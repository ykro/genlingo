"""The comparison page: David and Goliath translate Gen Z ↔ papás side by side.

A text box, a direction switch and example buttons; each column shows its translation and how long
it took. No scores, rounds or votes. The examples (data/translate_examples.json) are
Guatemalan slang from the test set, the use case David wins; each one was checked live with both
models. For an example the page also shows the human reference and a ✓/✗ per slang term
(term_check.py, the same rules as the eval's *jerga correcta*).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .dataset import read_jsonl
from .glossary import load_counterparts
from .term_check import term_checks
from .terms import TermBank

PAGE = Path(__file__).with_name("static") / "index.html"
# The brand fonts (OFL, static/fonts/README.txt), served by the page itself.
FONTS = {name: Path(__file__).with_name("static") / "fonts" / name for name in ("BigShoulders-latin.woff2", "Figtree-latin.woff2")}


def examples_path(data_dir: Path) -> Path:
    return data_dir / "translate_examples.json"


def _examples(data_dir: Path) -> list[dict]:
    path = examples_path(data_dir)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("examples", [])


def load_examples(data_dir: Path) -> list[dict]:
    """What the page needs for each example button (not the verification record), with the slang
    terms of the phrase so the button can show them."""
    keys = ("text", "direction", "reference", "source", "license")
    out = []
    for n, e in enumerate(_examples(data_dir)):
        item = {"id": e.get("pair_id") or str(n), **{k: e.get(k) for k in keys}}
        item["slang"] = [t["term"] for t in check_terms(data_dir, item, "GT", "")]
        out.append(item)
    return out


def find_example(data_dir: Path, example_id: str | None) -> dict | None:
    return next((e for e in load_examples(data_dir) if e["id"] == example_id), None) if example_id else None


@lru_cache(maxsize=4)
def _bank(data_dir: Path) -> tuple[TermBank, dict[str, str | None]]:
    # The bank frozen with the test set (like the eval), without ordinary-word entries.
    frozen = data_dir / "eval" / "terms_test.jsonl"
    terms = read_jsonl(frozen if frozen.exists() else data_dir / "terms.jsonl")
    return TermBank(terms, ignore_ambiguous=True), load_counterparts(data_dir / "counterparts.jsonl")


def check_terms(data_dir: Path, example: dict, country: str, hypothesis: str) -> list[dict]:
    bank, cps = _bank(data_dir)
    return term_checks(bank, cps, example["text"], example["direction"], country, hypothesis, example.get("reference"))
