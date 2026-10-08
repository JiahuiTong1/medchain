# MedChain v0.1.35 — GitHub upload instructions

Zenodo record: https://doi.org/10.5281/zenodo.23230470 (version v0.1.35, released 2026-10-08).
All-version DOI: https://doi.org/10.5281/zenodo.23230469.

Upload these files into the **same paths** in the repository main branch:

- `pyproject.toml`
- `src/medchain/__init__.py`
- `CITATION.cff`
- `README.md`
- `CHANGELOG.md`
- `RELEASE_UPDATE_NOTES.md` (optional explanatory document)

The README now includes Zenodo's official all-version badge; CITATION.cff points to the archived v0.1.35 DOI and includes the release date.

**Important:** This patch is based on the previously supplied corrected software package, not a fresh checkout of the current GitHub release. Review differences before overwriting any file that has since changed. Uploading to main does not change the already published GitHub Release or Zenodo archive.

After uploading, run:

```bash
python -m pip install -e ".[dev]"
python -m pytest tests/ -q
```
