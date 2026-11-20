# smt-optim-data

Data used by the examples and tutorials of [smt-optim](https://github.com/SMTorg/smt-optim): optimization logs, results and any other data needed to demonstrate the package.

The data is **not** stored in the `smt-optim` repository. It is published here as release archives (one zip file per dataset), which the examples download on demand.

## Repository structure

```
smt-optim-data/
├── datasets/
│   ├── _template/
│   │   └── dataset.toml        # template for new datasets (not released)
│   └── postprocessing/         # one directory = one dataset = one archive
│       ├── dataset.toml        # metadata of the dataset
│       ├── unconstrained/...
│       └── multifidelity/...
├── scripts/
│   └── build_release.py        # packs every dataset into a zip archive
└── .github/workflows/
    └── release.yml             # builds the archives and publishes a GitHub release
```

- Each directory in `datasets/` is a self-contained **dataset**. It is released as `<name>-<version>.zip`, and the archive is rooted at `<name>/`.
- Directories whose name starts with `_` or `.` are ignored by the release, as are hidden files and `*:Zone.Identifier` files (created by Windows when copying files from WSL).
- The layout inside a dataset is free. It should be the one expected by the code that reads it.

### `dataset.toml`

Every dataset has a short `dataset.toml`:

```toml
description = "One sentence: what the data is and which example uses it."
license = "CC-BY-4.0"
source = "optional: script or smt-optim version that generated the data"
```

Only `description` is used by the build (it is copied into `manifest.json`). Longer explanations (columns, how the data was generated) belong in a `README.md` inside the dataset directory, which is shipped in the archive.

### Current datasets

| Dataset | Content | Used by |
|---|---|---|
| `postprocessing` | Optimization runs of two acquisition functions (expected improvement and probability of improvement), single-fidelity (`unconstrained/`) and two-fidelity with a constraint (`multifidelity/`). One `doe.csv` per run: `<group>/<algorithm>/<problem>/<instance>/doe.csv`. | `smt-optim/examples/postprocessing.ipynb` |

## Using the data

Each release has one archive per dataset, and two files describing them:

| Release asset | Content |
|---|---|
| `<name>-<version>.zip` | the dataset, rooted at `<name>/` |
| `checksums.txt` | SHA-256 of every archive (`sha256sum` format) |
| `manifest.json` | for each dataset: file name, SHA-256, size, number of files and description |

The download URL of a dataset is:

```
https://github.com/oihanc/smt-optim-data/releases/download/<version>/<name>-<version>.zip
```

For example, with the standard library only:

```python
import io, urllib.request, zipfile

version = "v0.1.0"
url = f"https://github.com/oihanc/smt-optim-data/releases/download/{version}/postprocessing-{version}.zip"

with urllib.request.urlopen(url) as response:
    zipfile.ZipFile(io.BytesIO(response.read())).extractall("data")

# data/postprocessing/unconstrained/...
```

**Always pin a version** (a tag such as `v0.1.0`), never a branch. A published version never changes, so an example keeps giving the same results.

## Adding or changing data

1. Create `datasets/<name>/` and copy the data in it. Use a short, lowercase name, since it becomes the archive name.
2. Copy `datasets/_template/dataset.toml` to `datasets/<name>/dataset.toml` and fill it.
3. Check the archives build (see below), then open a pull request. Pull requests that touch `datasets/`, `scripts/` or the workflow run the build automatically, without publishing anything.
4. Release a new version once the change is merged.

Data that was already released must not be edited. Publish a new version instead, so older versions of `smt-optim` can still download the data they expect.

Keep the repository small. Prefer plain text files (CSV, JSON), commit only what an example needs, and do not use Git LFS: the archives are built from the files in the repository, and LFS files would not be included.

## Building the archives locally

No dependency is needed beyond Python 3.11 or later (the standard library only):

```bash
python scripts/build_release.py --version v0.0.1 --out dist
```

This writes `dist/<name>-v0.0.1.zip` for each dataset, plus `dist/checksums.txt` and `dist/manifest.json`. The version must look like `vMAJOR.MINOR.PATCH` (an optional suffix such as `-rc1` is allowed). The archives are reproducible: the same data always gives the same checksums. `dist/` is ignored by git.

## Releasing

Releases are created by the GitHub workflow `.github/workflows/release.yml`, which builds the archives and attaches them to a GitHub release. There are two ways to trigger it:

**From the command line**, by pushing a tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

**From GitHub**: open *Actions → Release → Run workflow*, and enter the version (for example `v0.1.0`). The tag is created on the latest commit of the default branch. Two options are available: *draft* (review the release before publishing it) and *pre-release*.

Rules enforced by the workflow:

- A manual run must be started from the default branch.
- If a release with the same version already exists, the workflow fails. Choose a new version.
- A version with a suffix (`v0.2.0-rc1`) is marked as a pre-release automatically.

## License

The data is released under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/), as stated in the `dataset.toml` of each dataset. A different license can be set per dataset.
