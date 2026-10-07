"""Report for the held-out pan-Hispanic Gen Z probe (data/eval/probe_genz.jsonl).

    uv run --project duel python evals/probe_report.py evals/results/probe-<stamp>.json

The probe answers one question the test set can't: does David handle the Gen Z slang every Spanish-
speaking teenager uses (cringe, random, crush, stalkear, funar, mid, delulu, mood…), not only the
Guatemalan and Colombian slang most of his real-sentence training came from? Every source sentence
is real (quoted from the web page in its provenance) and no source page of the probe is used for
training (data/SOURCES.md, round 4).

Judgment is deterministic and the same for every model (no model judges another). Each item lists
the slang forms of its sentence and plain-meaning stems (provenance.judge):
- Gen Z -> papás: correct when no slang form is left AND the output says the meaning (one stem).
- papás -> Gen Z: correct when the output uses one of the item's slang forms or an equally valid Gen Z
  synonym listed for it (provenance.judge.genz_ok: e.g. «lache» for «cringe», «devoraste» for «slay»).
Every item is asked twice: with the country set to LATAM (neutral Spanish) and to GT (what the
page uses on stage in Guatemala).
"""

from __future__ import annotations

import json
import math
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "duel"))
from genlingo_duel.dataset import read_jsonl  # noqa: E402


def _low(text: str) -> str:
    return unicodedata.normalize("NFC", text).lower()


def has_form(form: str, text: str) -> bool:
    """A slang form as a word prefix ("funar" matches "funaron"); short forms (bro, mid, F) as whole words."""
    tail = r"\b" if len(form) <= 4 else ""
    return re.search(r"\b" + re.escape(_low(form)) + tail, _low(text)) is not None


def judge(pair: dict, hypothesis: str | None) -> bool:
    if not hypothesis or not hypothesis.strip():
        return False
    j = pair["provenance"]["judge"]
    if pair["direction"] == "genz_to_parent":
        if any(has_form(f, hypothesis) for f in j["slang"]):
            return False
        return any(m in _low(hypothesis) for m in j["meaning"])
    return any(has_form(f, hypothesis) for f in j.get("genz_ok", j["slang"]))


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


PROBE = Path(__file__).resolve().parents[1] / "data" / "eval" / "probe_genz.jsonl"


def current_pairs(raw: dict) -> dict[str, dict]:
    """The run's pairs, with the judge lists of the current probe file (one rule for every run)."""
    pairs = {p["id"]: p for p in raw["pairs"]}
    for row in read_jsonl(PROBE):  # the private copy (make data-pull): the probe quotes closed sources
        if row["id"] in pairs:
            pairs[row["id"]] = row
    return pairs


def scores(raw: dict) -> dict:
    pairs = current_pairs(raw)
    out: dict = {}
    for r in raw["results"]:
        p = pairs[r["pair_id"]]
        ok = judge(p, r.get("text")) if "error" not in r else False
        key = (r["model"], p["country"], p["direction"])
        out.setdefault(key, {})[p["id"]] = ok
    return out


def write_probe_report(raw: dict, path: Path) -> str:
    sc = scores(raw)
    models = [m.get("label", m["name"]) for m in raw["models"] if not m.get("skip")]
    lines = [
        "# Sonda Gen Z general (fuera de Guatemala)",
        "",
        f"Generado por `make eval-probe` el {raw['created_at']}. {len(raw['pairs']) // 2} frases reales de la web"
        " (32 oraciones, cada una en las dos direcciones), preguntadas con el país en LATAM y en GT."
        " Juicio determinista, igual para todos los modelos (`evals/probe_report.py`): de Gen Z a papás, la jerga"
        " desaparece y la salida dice el significado; de papás a Gen Z, la salida usa la jerga de la frase.",
        "",
        "| modelo | país | Gen Z → papás | papás → Gen Z | total | IC 95 % (total) |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for m in models:
        for country in ("LATAM", "GT"):
            g = sc.get((m, country, "genz_to_parent"), {})
            p = sc.get((m, country, "parent_to_genz"), {})
            k, n = sum(g.values()) + sum(p.values()), len(g) + len(p)
            if not n:
                continue
            lo, hi = wilson(k, n)
            lines.append(f"| {m} | {country} | {sum(g.values())}/{len(g)} | {sum(p.values())}/{len(p)} | "
                         f"**{100 * k / n:.0f} %** | [{100 * lo:.0f}, {100 * hi:.0f}] |")
    # Per item: the slang it tests and ✓/✗ per model (the sentences quote pages that can't be redistributed;
    # they are in the private bucket, data/.private/eval/probe_genz.jsonl).
    lines += ["", "## Frase por frase (país LATAM)", "", "| # | jerga | dirección | " + " | ".join(models) + " |",
              "| --- | --- | --- | " + " | ".join("---" for _ in models) + " |"]
    by_pair = {(r["model"], r["pair_id"]): r.get("text") for r in raw["results"]}
    for p in current_pairs(raw).values():
        if p["country"] != "LATAM":
            continue
        n = p["id"].split("-")[1]
        arrow = "Gen Z → papás" if p["direction"] == "genz_to_parent" else "papás → Gen Z"
        marks = ["✓" if judge(p, by_pair.get((m, p["id"]))) else "✗" for m in models]
        lines.append(f"| {n} | {', '.join(p['provenance']['judge']['slang'])} | {arrow} | " + " | ".join(marks) + " |")
    text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")
    return text


if __name__ == "__main__":
    src = Path(sys.argv[1])
    raw = json.loads(src.read_text())
    out = Path(__file__).resolve().parent / "report_probe.md"
    print(write_probe_report(raw, out))
