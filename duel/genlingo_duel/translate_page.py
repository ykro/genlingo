"""The translation page (/traducir): David alone, Gen Z ↔ papás, on the laptop and without internet.

A text box, a direction switch and example buttons. The examples (data/translate_examples.json)
are Guatemalan slang from the test set, the use case David wins, each one checked live.
"""

from __future__ import annotations

import json
from pathlib import Path

PAGE = Path(__file__).with_name("static") / "traducir.html"


def examples_path(data_dir: Path) -> Path:
    return data_dir / "translate_examples.json"


def load_examples(data_dir: Path) -> list[dict]:
    path = examples_path(data_dir)
    if not path.exists():
        return []
    return [
        {"text": e["text"], "direction": e["direction"]}
        for e in json.loads(path.read_text(encoding="utf-8")).get("examples", [])
    ]
