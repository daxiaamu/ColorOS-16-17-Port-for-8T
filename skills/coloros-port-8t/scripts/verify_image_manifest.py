"""Read-only integrity and allocation checks for explicitly listed raw images."""
import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath

PARTITIONS = set("system system_ext product vendor odm my_product my_stock my_heytap my_region my_carrier my_preload my_engineering my_company my_manifest my_bigball".split())

def positive(value, name):
    if type(value) is not int or value <= 0:
        raise ValueError(name + " must be a positive integer")
    return value

def verify(manifest, root):
    root = Path(root).resolve(strict=True)
    alignment = positive(manifest["alignment"], "alignment")
    if alignment & (alignment - 1):
        raise ValueError("alignment must be a power of two")
    limit = positive(manifest["group_limit"], "group_limit")
    rows = manifest["partitions"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("partitions must be a nonempty list")
    seen, allocated = set(), 0
    for row in rows:
        name = row["partition"]
        if name not in PARTITIONS or name in seen:
            raise ValueError("unknown or duplicate partition: " + str(name))
        seen.add(name)
        raw = row["path"]
        path, win = Path(raw), PureWindowsPath(raw)
        if not raw or path.is_absolute() or win.drive or win.root or ".." in path.parts or ".." in win.parts:
            raise ValueError("path must be relative and contained")
        path = (root / path).resolve(strict=True)
        try:
            path.relative_to(root)
        except ValueError:
            raise ValueError("resolved path escapes root")
        size = positive(row["bytes"], "bytes")
        if not path.is_file() or path.stat().st_size != size:
            raise ValueError("file length mismatch: " + name)
        expected = row["sha256"]
        if not isinstance(expected, str) or len(expected) != 64 or any(c not in "0123456789abcdefABCDEF" for c in expected):
            raise ValueError("invalid SHA256: " + name)
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            if stream.read(4) == bytes.fromhex("3aff26ed"):
                raise ValueError("sparse input unsupported; use expanded raw image")
            stream.seek(0)
            for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected.lower():
            raise ValueError("SHA256 mismatch: " + name)
        allocated += (size + alignment - 1) // alignment * alignment
    if allocated > limit:
        raise ValueError("aligned allocation exceeds group limit")
    return dict(checked_partitions=len(seen), allocated_bytes=allocated, remaining_bytes=limit-allocated)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = verify(json.loads(args.manifest.read_text(encoding="utf-8-sig")), args.root)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, "FAIL: " + str(error) + "\n")
    print("PASS (listed images only): " + json.dumps(result))

if __name__ == "__main__":
    main()
