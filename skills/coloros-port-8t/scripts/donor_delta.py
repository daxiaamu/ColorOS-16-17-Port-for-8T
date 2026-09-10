"""Read-only donor inventories and patch impact planning. Python 3.8+."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath

def relative_name(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("Expected a normalized relative POSIX path")
    p = PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts or p.as_posix() != value or value == ".":
        raise ValueError("Unsafe or non-normalized path: " + value)
    return value

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def snapshot(root, label):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Snapshot root must be an extracted directory")
    entries = {}
    def visit(folder):
        for p in sorted(folder.iterdir()):
            name = relative_name(p.relative_to(root).as_posix())
            # Never follow Android symlinks or host directory junctions.
            if p.is_symlink():
                entries[name] = {"kind": "symlink", "target": os.readlink(str(p))}
            elif getattr(p.lstat(), "st_file_attributes", 0) & 0x400:
                raise ValueError("Unsupported reparse point: " + name)
            elif p.is_dir():
                entries[name] = {"kind": "directory"}
                visit(p)
            elif p.is_file():
                before = p.stat()
                sha = digest(p)
                after = p.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    raise ValueError("Input changed while hashing: " + name)
                entries[name] = {"kind": "file", "bytes": after.st_size, "sha256": sha}
            else:
                raise ValueError("Unsupported filesystem entry: " + name)
    visit(root)
    return {"schema": 1, "label": label, "entries": entries}

def validate_inventory(data):
    if data.get("schema") != 1 or not isinstance(data.get("entries"), dict):
        raise ValueError("Expected schema 1 inventory")
    for name, item in data["entries"].items():
        relative_name(name)
        if not isinstance(item, dict):
            raise ValueError("Invalid inventory entry")
        kind = item.get("kind")
        if kind == "file":
            if type(item.get("bytes")) is not int or item["bytes"] < 0:
                raise ValueError("Invalid byte length")
            if not isinstance(item.get("sha256"), str) or not re.fullmatch("[0-9a-f]{64}", item["sha256"]):
                raise ValueError("Invalid SHA256")
        elif kind == "symlink":
            if not isinstance(item.get("target"), str) or not item["target"]:
                raise ValueError("Invalid symlink target")
        elif kind != "directory":
            raise ValueError("Unknown entry kind")
    return data["entries"]

def strings(value, field, nonempty=False):
    if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
        raise ValueError("Expected string list: " + field)
    if len(value) != len(set(value)) or (nonempty and not value):
        raise ValueError("Empty or repeated values: " + field)
    return value

def plan(old, new, catalog):
    a, b = validate_inventory(old), validate_inventory(new)
    delta = {"added": sorted(b.keys() - a.keys()), "removed": sorted(a.keys() - b.keys()),
             "changed": sorted(k for k in a.keys() & b.keys() if a[k] != b[k])}
    rows = catalog.get("patches")
    if not isinstance(rows, list):
        raise ValueError("Expected patches list")
    patches = {}
    for row in rows:
        ident = row.get("id")
        if not isinstance(ident, str) or not re.fullmatch("[a-z0-9][a-z0-9-]*", ident) or ident in patches:
            raise ValueError("Invalid or duplicate patch ID")
        if row.get("state") not in {"verified", "experimental", "reverted"}:
            raise ValueError("Unknown patch state: " + ident)
        for name in strings(row.get("inputs"), "inputs", True):
            relative_name(name)
        strings(row.get("depends_on", []), "depends_on")
        strings(row.get("tests", []), "tests")
        patches[ident] = row
    results, visiting = {}, set()
    def classify(ident):
        if ident in results:
            return results[ident]
        if ident not in patches:
            raise ValueError("Unknown dependency: " + ident)
        if ident in visiting:
            raise ValueError("Patch dependency cycle: " + ident)
        visiting.add(ident)
        row = patches[ident]
        deps = [classify(x) for x in row.get("depends_on", [])]
        missing_old = [x for x in row["inputs"] if x not in a]
        missing_new = [x for x in row["inputs"] if x not in b]
        changed = [x for x in row["inputs"] if x in a and x in b and a[x] != b[x]]
        # Directory hashes are not recursive: require explicit file/link inputs.
        directory_inputs = [x for x in row["inputs"] if a.get(x, {}).get("kind") == "directory"
                            or b.get(x, {}).get("kind") == "directory"]
        if directory_inputs:
            raise ValueError("Patch inputs must list files/links, not directories: " + ident)
        reasons = []
        if missing_old: reasons.append("baseline-input-missing")
        if missing_new: reasons.append("new-input-missing")
        if changed: reasons.append("input-changed")
        if any(d["decision"] != "candidate-reuse" for d in deps): reasons.append("dependency-needs-review")
        if row["state"] != "verified":
            decision = "excluded"
        elif missing_old or missing_new:
            decision = "blocked"
        elif reasons:
            decision = "review"
        else:
            decision = "candidate-reuse"
        result = {"id": ident, "decision": decision, "reasons": reasons,
                  "missing_old": missing_old, "missing_new": missing_new, "changed_inputs": changed,
                  "tests": row.get("tests", [])}
        visiting.remove(ident)
        results[ident] = result
        return result
    for ident in patches:
        classify(ident)
    tests = sorted({t for r in results.values() if r["decision"] != "excluded" for t in r["tests"]})
    return {"schema": 1, "old": old.get("label"), "new": new.get("label"), "files": delta,
            "patches": list(results.values()), "required_tests": tests,
            "ready_for_candidate_reuse": bool(results) and all(r["decision"] == "candidate-reuse" for r in results.values()),
            "scope": "Declared file inputs only; no patch applied or runtime compatibility proven"}

def read_json(path):
    def unique(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                raise ValueError("Duplicate JSON key: " + k)
            out[k] = v
        return out
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=unique)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    subs = ap.add_subparsers(dest="command", required=True)
    snap = subs.add_parser("snapshot")
    snap.add_argument("root", type=Path)
    snap.add_argument("--label", required=True)
    snap.add_argument("--output", type=Path, required=True)
    diff = subs.add_parser("plan")
    diff.add_argument("old", type=Path)
    diff.add_argument("new", type=Path)
    diff.add_argument("--patches", type=Path, required=True)
    diff.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.command == "snapshot":
        # Keep generated inventory out of its own input tree.
        try:
            args.output.resolve().relative_to(args.root.resolve())
        except ValueError:
            pass
        else:
            ap.error("Output must be outside the snapshot root")
    try:
        result = snapshot(args.root, args.label) if args.command == "snapshot" else plan(
            read_json(args.old), read_json(args.new), read_json(args.patches))
        with args.output.open("x", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        ap.exit(2, str(exc) + "\n")
    print("Wrote", args.output)

if __name__ == "__main__":
    main()
