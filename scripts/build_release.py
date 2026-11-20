"""
Build the release assets of smt-optim-data.

Every directory ``datasets/<name>/`` is packed into ``<name>-<version>.zip``. Besides the archives, two files are
written to the output directory:

- ``checksums.txt``: SHA-256 of every archive, in ``sha256sum`` format.
- ``manifest.json``: dataset name -> archive file name, SHA-256, size and description (from ``dataset.toml``).

The archives are reproducible: the same data always gives the same bytes, so the checksums only change when the
data does. Each archive is rooted at ``<name>/``.

Usage::

    python scripts/build_release.py --version v0.1.0 --out dist
"""

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

try:  # Python >= 3.11
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?$")

# fixed timestamp and permissions so that archives do not depend on when or where they were built
ZIP_DATE = (1980, 1, 1, 0, 0, 0)
FILE_MODE = 0o644 << 16


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dataset_files(dataset_dir: Path) -> list[Path]:
    """
    Files of a dataset, sorted.

    Hidden files and directories (``.DS_Store``, ``.gitkeep``, ...) and the ``*:Zone.Identifier`` files created
    by Windows when copying files from WSL are ignored.
    """
    files = [
        p for p in dataset_dir.rglob("*")
        if p.is_file()
        and not p.name.endswith(":Zone.Identifier")
        and not any(part.startswith(".") for part in p.relative_to(dataset_dir).parts)
    ]
    return sorted(files, key=lambda p: p.relative_to(dataset_dir).as_posix())


def build_archive(dataset_dir: Path, archive: Path) -> int:
    """Zip `dataset_dir` into `archive`, rooted at ``<dataset name>/``. Returns the number of files."""
    files = dataset_files(dataset_dir)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            arcname = f"{dataset_dir.name}/{path.relative_to(dataset_dir).as_posix()}"
            info = zipfile.ZipInfo(arcname, date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = FILE_MODE
            zf.writestr(info, path.read_bytes())
    return len(files)


def read_description(dataset_dir: Path) -> str:
    meta = dataset_dir / "dataset.toml"
    if tomllib is None or not meta.is_file():
        return ""
    with open(meta, "rb") as f:
        return str(tomllib.load(f).get("description", ""))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", required=True, help="release version, e.g. v0.1.0 or v0.2.0-rc1")
    parser.add_argument("--datasets-dir", type=Path, default=Path("datasets"), help="default: datasets")
    parser.add_argument("--out", type=Path, default=Path("dist"), help="output directory, default: dist")
    args = parser.parse_args()

    if not VERSION_RE.match(args.version):
        parser.error(f"invalid version '{args.version}': expected vMAJOR.MINOR.PATCH[-suffix], e.g. v0.1.0")
    if not args.datasets_dir.is_dir():
        parser.error(f"datasets directory '{args.datasets_dir}' not found")

    # directories starting with "_" or "." are not released (drafts, templates, ...)
    datasets = sorted(
        d for d in args.datasets_dir.iterdir() if d.is_dir() and not d.name.startswith(("_", "."))
    )
    if not datasets:
        parser.error(f"no dataset found in '{args.datasets_dir}'")

    args.out.mkdir(parents=True, exist_ok=True)

    manifest = {"version": args.version, "datasets": {}}
    checksum_lines = []

    for dataset_dir in datasets:
        if not dataset_files(dataset_dir):
            parser.error(f"dataset '{dataset_dir.name}' has no files")

        archive = args.out / f"{dataset_dir.name}-{args.version}.zip"
        n_files = build_archive(dataset_dir, archive)
        digest = sha256(archive)

        manifest["datasets"][dataset_dir.name] = {
            "file": archive.name,
            "sha256": digest,
            "size": archive.stat().st_size,
            "n_files": n_files,
            "description": read_description(dataset_dir),
        }
        checksum_lines.append(f"{digest}  {archive.name}")
        print(f"{archive.name}: {n_files} files, {archive.stat().st_size / 1e6:.2f} MB, sha256={digest[:12]}...")

    (args.out / "checksums.txt").write_text("\n".join(checksum_lines) + "\n")
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
