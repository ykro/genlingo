"""Shared bootstrap for scripts: make the duel package importable and expose repo paths."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
if str(ROOT / "duel") not in sys.path:
    sys.path.insert(0, str(ROOT / "duel"))
