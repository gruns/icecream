# Icecream (Forked) - My Contribution

I used this repository to modernise the build infrastructure of the `icecream` library.

### What I Accomplished:
- Migrated static metadata from `setup.py` to a PEP 621-compliant `pyproject.toml` file.
- Preserved custom `cmdclass` handlers for testing/publishing to maintain full backwards compatibility.
- Verified the build locally via editable installation (`pip install -e .`).

**View my official, live Pull Request here:** https://github.com/gruns/icecream/pull/237