"""Setup every eval in this directory shares - written ONCE, by /oryxflow:eval-init.

Each eval imports this before it imports production code, so the two facts no
eval can run without live in one place instead of being re-derived per eval:

1. where the production code is importable from, and
2. how credentials are loaded.

Run every eval from THIS directory (evals/). The cache (data/) is created
relative to the working directory, so a run launched from anywhere else builds a
second, empty cache - and a credential loader that resolves relative to the
working directory finds nothing and every case raises.
"""
import pathlib
import sys  # noqa: F401 - used once the import-path placeholder below is filled

EVALS = pathlib.Path(__file__).resolve().parent
ROOT = EVALS.parent        # the repository root: every eval's paths are relative to it

# PLACEHOLDER SCAFFOLD - where production code is importable from; delete this line when filled.
# Prefer installing the package that owns it (`pip install -e <dir holding its
# pyproject.toml>`), which needs nothing here. Only when that is not possible:
# sys.path.insert(0, str(ROOT / 'backend'))

# PLACEHOLDER SCAFFOLD - how credentials load; delete this line when filled.
# Load them by ABSOLUTE path, anchored on ROOT, never relative to the working
# directory. Never write a key here - point at where it is stored.
# load_credentials(ROOT / 'backend' / '.creds.yaml')
