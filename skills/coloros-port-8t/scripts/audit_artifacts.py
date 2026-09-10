"""Read-only structural checks, not signature or dependency verification."""
import argparse
import os
import zipfile
from pathlib import Path

DEX_VERSIONS = {"035", "037", "038", "039", "040", "041"}

def dex_error(header, required=None):
    version = header[4:7].decode("ascii", errors="replace")
    if len(header) < 8 or header[:4] != b"dex\n" or header[7:8] != b"\0" or version not in DEX_VERSIONS:
        return "invalid or unsupported DEX header"
    if required and version != required:
        return "DEX version differs from required " + required

def audit(root, dex_version=None):
    root = Path(root)
    errors = []
    if root.is_symlink() or not root.is_dir():
        return ["root must be a real directory"]
    for folder, dirs, files in os.walk(root, followlinks=False):
        for name in list(dirs):
            if (Path(folder) / name).is_symlink():
                errors.append(str(Path(folder) / name) + ": symlink not inspected")
                dirs.remove(name)
        for name in files:
            path = Path(folder) / name
            try:
                if path.is_symlink():
                    errors.append(str(path) + ": symlink not inspected")
                    continue
                with path.open("rb") as stream:
                    header = stream.read(32)
                if header.startswith(b"!<symlink>"):
                    errors.append(str(path) + ": extracted symlink placeholder")
                if path.suffix == ".so" and header[:4] != b"\x7fELF":
                    errors.append(str(path) + ": not ELF")
                if path.suffix == ".dex":
                    error = dex_error(header, dex_version)
                    if error:
                        errors.append(str(path) + ": " + error)
                if path.suffix.lower() == ".apk":
                    with zipfile.ZipFile(path) as archive:
                        names = archive.namelist()
                        if len(names) != len(set(names)):
                            errors.append(str(path) + ": duplicate ZIP entries")
                        bad = archive.testzip()
                        if bad:
                            errors.append(str(path) + ": CRC failed: " + bad)
                        for item in archive.infolist():
                            if item.filename.endswith(".dex"):
                                with archive.open(item) as stream:
                                    error = dex_error(stream.read(8), dex_version)
                                if error:
                                    errors.append(str(path) + "!" + item.filename + ": " + error)
            except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, NotImplementedError) as error:
                errors.append(str(path) + ": " + str(error))
    return errors

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--dex-version", choices=sorted(DEX_VERSIONS))
    args = parser.parse_args()
    errors = audit(args.root, args.dex_version)
    if errors:
        parser.exit(1, "\n".join(errors) + "\n")
    print("PASS (structural checks only; signatures and dependencies not verified)")

if __name__ == "__main__":
    main()
