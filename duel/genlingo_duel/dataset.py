"""The pair schema and loaders. Every pair says where it came from (`origin` + `provenance`):
you can't trust an evaluation, or retrain monthly, on data whose origin you don't know."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .prompts import COUNTRIES

Origin = Literal["web", "synthetic", "human"]
# dev: real pairs held out from training to make data decisions, so the test set is touched once per round.
Split = Literal["train", "dev", "test"]
# auto_validated: passed the automatic term-bank checks (scripts/validate_test_set.py); no human needed.
Status = Literal["pending_review", "auto_validated", "approved", "rejected"]

PAIR_FILES = {
    "synthetic": "pairs/synthetic.jsonl",
    "test_web": "pairs/test_web.jsonl",
    "human": "pairs/human.jsonl",
    "real_train": "pairs/real_train.jsonl",
    "dev_real": "pairs/dev_real.jsonl",
    "synthetic_multi": "pairs/synthetic_multi.jsonl",
}


class Pair(BaseModel):
    id: str = Field(min_length=1)
    direction: Literal["genz_to_parent", "parent_to_genz"]
    source: str = Field(min_length=1, max_length=400)
    target: str = Field(min_length=1, max_length=400)
    country: str
    age_range: str
    split: Split
    status: Status
    origin: Origin
    provenance: dict

    @model_validator(mode="after")
    def _check(self) -> "Pair":
        if self.country not in COUNTRIES:
            raise ValueError(f"country {self.country!r} not in {sorted(COUNTRIES)}")
        p = self.provenance
        required = {
            "web": ("url", "license"),
            "synthetic": ("model", "prompt_version", "seed"),
            "human": ("event",),
        }[self.origin]
        missing = [k for k in required if k not in p or p[k] in (None, "")]
        if missing:
            raise ValueError(f"{self.origin} pair {self.id} missing provenance {missing}")
        # Synthetic references written by Gemini would bias chrF++ toward Gemini (Goliath).
        if self.split in ("test", "dev") and self.origin == "synthetic":
            raise ValueError(f"synthetic pair {self.id} cannot be in the {self.split} split")
        if self.source.strip() == self.target.strip():
            raise ValueError(f"pair {self.id}: source equals target")
        return self


def read_jsonl(path: Path) -> Iterator[dict]:
    if not path.exists():
        return
    with path.open(encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{n}: {exc}") from exc


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def load_pairs(data_dir: Path, files: Iterable[str] | None = None) -> list[Pair]:
    rels = list(files) if files is not None else list(PAIR_FILES.values())
    return [Pair.model_validate(row) for rel in rels for row in read_jsonl(data_dir / rel)]


def test_pairs(data_dir: Path, *, include_pending: bool = False) -> list[Pair]:
    """Test pairs for evaluation rounds and `make eval`: web + human only, never synthetic."""
    ok = {"approved", "auto_validated", "pending_review"} if include_pending else {"approved", "auto_validated"}
    return [p for p in load_pairs(data_dir) if p.split == "test" and p.status in ok]


def train_pairs(data_dir: Path) -> list[Pair]:
    return [p for p in load_pairs(data_dir) if p.split == "train" and p.status in ("approved", "auto_validated")]
