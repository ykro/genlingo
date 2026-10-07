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
    "synthetic_genz": "pairs/synthetic_genz.jsonl",  # pan-Hispanic Gen Z round (2026-10-06): LATAM + MX
    # round 5 (2026-10-07): natural 2–3-term combinations per country, each term checked by meaning, both directions
    "synthetic_combo": "pairs/synthetic_combo.jsonl",
    # round 5: papás -> Gen Z outside Guatemala (MX, CO, LATAM), single-term
    "synthetic_p2g": "pairs/synthetic_p2g.jsonl",
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


# ---------------------------------------------------------------------------------------------
# Verbatim text from sources that don't allow redistribution stays out of the public repo.
# Open sources (their text may be in the repo, with attribution; WikiLengua and Wikcionario pairs inherit
# CC BY-SA): S01–S03 WikiLengua (CC BY-SA 3.0), S04 diccionario-chapin (MIT), S05/S62 Wikcionario
# (CC BY-SA 4.0), S70 Guate Inmortal (CC BY 4.0). Every other source is "all rights reserved": its verbatim
# sentences live in a private bucket (PRIVATE_DATA_URI, `make data-pull` -> data/.private/) and the repo
# keeps the term, the paraphrased meaning, the URL and our own rewrite, with the quoted field set to null
# and listed in "redacted". read_jsonl reads the private copy when it is there; write_jsonl writes both.
# ---------------------------------------------------------------------------------------------
OPEN_SOURCES = frozenset({"S01", "S02", "S03", "S04", "S05", "S62", "S70"})
PRIVATE_DIRNAME = ".private"


def _data_rel(path: Path) -> tuple[Path, str] | None:
    """(data dir, path relative to it) when `path` is inside a `data/` directory."""
    parts = path.resolve().parts
    if "data" not in parts:
        return None
    i = len(parts) - 1 - parts[::-1].index("data")
    rest = parts[i + 1:]
    if not rest or rest[0] == PRIVATE_DIRNAME:
        return None
    return Path(*parts[: i + 1]), "/".join(rest)


def _source_id(row: dict) -> str | None:
    return row.get("source_id") or (row.get("provenance") or {}).get("source_id")


def _quoted_fields(rel: str, row: dict) -> list[str]:
    """The fields of `row` that quote a source verbatim (empty for open sources and our own text)."""
    if rel.startswith("raw/web_usage"):
        return ["example"] if row.get("example_origin", "source") == "source" else []
    if rel in ("terms.jsonl", "eval/terms_test.jsonl") or rel.startswith("raw/terms_"):
        return ["example"] if row.get("example") and row.get("example_origin", "source") == "source" else []
    if rel in ("pairs/test_web.jsonl", "pairs/real_train.jsonl", "pairs/dev_real.jsonl", "eval/probe_genz.jsonl",
               "eval/combos.jsonl"):
        prov = row.get("provenance") or {}
        if prov.get("example_origin", "source") != "source":
            return []
        return ["target"] if prov.get("kind") == "real_target" else ["source"]
    return []


PRIVATE_FILES = ("raw/web_usage", "raw/terms_", "terms.jsonl", "eval/terms_test.jsonl", "pairs/test_web.jsonl",
                 "pairs/real_train.jsonl", "pairs/dev_real.jsonl", "eval/probe_genz.jsonl", "eval/combos.jsonl")


def is_private_file(rel: str) -> bool:
    return any(rel == f or (f.endswith("_") or f.endswith("usage")) and rel.startswith(f) for f in PRIVATE_FILES)


def redact(rel: str, row: dict) -> dict:
    """The public version of a row: quoted text of a closed source set to null and listed in "redacted"."""
    if _source_id(row) in OPEN_SOURCES:
        return row
    fields = [f for f in _quoted_fields(rel, row) if row.get(f)]
    if not fields:
        return row
    return {**row, **{f: None for f in fields}, "redacted": fields}


class PrivateTextMissing(RuntimeError):
    pass


def read_jsonl(path: Path) -> Iterator[dict]:
    loc = _data_rel(path)
    if loc is not None:
        private = loc[0] / PRIVATE_DIRNAME / loc[1]
        if private.exists():
            path = private
    if not path.exists():
        return
    with path.open(encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if line.strip():
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{n}: {exc}") from exc
                # A term's example is reference only (nothing reads it); a pair or usage sentence without its
                # text can't be used, so that is an error with the fix.
                if row.get("redacted") and (set(row["redacted"]) & {"source", "target"} or "web_usage" in path.name):
                    raise PrivateTextMissing(
                        f"{path}:{n} quotes a source that can't be redistributed; its text is in the private "
                        "bucket: run `make data-pull` (needs access to the project).")
                yield row


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    """Write rows; for a file that quotes closed sources, the full rows go to data/.private/ and the repo
    file gets the redacted version (see OPEN_SOURCES)."""
    rows = list(rows)
    loc = _data_rel(path)
    if loc is not None and is_private_file(loc[1]):
        _write(loc[0] / PRIVATE_DIRNAME / loc[1], rows)
        rows = [redact(loc[1], r) for r in rows]
    return _write(path, rows)


def _write(path: Path, rows: list[dict]) -> int:
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
