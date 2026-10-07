"""Round 5's decision on dev (evals/niche.md, amendment 2): jerga correcta on the whole dev set and on its combinations.

    uv run --project duel python evals/dev_decision.py evals/results/dev-<run>.json [more dev runs…]

Every David in the runs (and Goliath, for reference) is scored with the same code: jerga correcta
(evals/term_accuracy.py, the rule in force), jerga resuelta, chrF++ and p50, on all dev pairs and on the dev pairs
that meet the combinations rule (evals/combos.py). The rule registered before training: the variant with the most
jerga correcta on dev combinations wins, if on all of dev it doesn't drop more than 2 points against
genlingo-2026-10d-e2b and its p50 is under 1 s; ties (≤ 1 point) go to the most jerga correcta on all of dev.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "duel"))
sys.path.insert(0, str(ROOT / "evals"))

from combos import frozen_bank, is_combo  # noqa: E402
from duel_core import corpus_chrf_pp, percentile  # noqa: E402
from genlingo_duel.glossary import load_counterparts  # noqa: E402
from term_accuracy import correct_slang, slang_handled  # noqa: E402

DATA = ROOT / "data"


def score(pairs: list[dict], rows: dict, bank, cps) -> dict:
    ok, handled, hyps, refs, lat = [], [], [], [], []
    for p in pairs:
        r = rows.get(p["id"])
        if not r or "error" in r:
            continue
        c = correct_slang(bank, cps, p, r["text"])
        h = slang_handled(bank, p, [], r["text"])
        if c is not None:
            ok.append(int(c))
        if h is not None:
            handled.append(int(h))
        hyps.append(r["text"])
        refs.append(p["target"])
        lat.append(r.get("latency_ms"))
    pct = lambda xs: round(100 * sum(xs) / len(xs), 1) if xs else None  # noqa: E731
    return {"n": len(ok), "correcta": pct(ok), "resuelta": pct(handled),
            "chrf": round(corpus_chrf_pp(hyps, refs), 1) if hyps else None, "p50_ms": percentile(lat, 50)}


def main() -> None:
    bank = frozen_bank(DATA)
    cps = load_counterparts(DATA / "counterparts.jsonl")
    table = {}
    for f in sys.argv[1:]:
        raw = json.loads(Path(f).read_text())
        pairs = [p for p in raw["pairs"] if p.get("status") in ("auto_validated", "approved")]
        combos = [p for p in pairs if is_combo(bank, p)]
        by: dict[str, dict] = {}
        for r in raw["results"]:
            by.setdefault(r["model"], {})[r["pair_id"]] = r
        for model, rows in by.items():
            table[model] = {"dev": score(pairs, rows, bank, cps), "dev_combos": score(combos, rows, bank, cps),
                            "file": Path(f).name}
    print(f"{'modelo':58} {'dev n':>5} {'correcta':>8} {'resuelta':>8} {'chrF++':>6} {'p50':>6} | {'comb n':>6} {'correcta':>8} {'resuelta':>8}")
    for m, t in sorted(table.items(), key=lambda kv: -(kv[1]["dev_combos"]["correcta"] or 0)):
        d, c = t["dev"], t["dev_combos"]
        print(f"{m[:58]:58} {d['n']:>5} {d['correcta']:>8} {d['resuelta']:>8} {d['chrf']:>6} {d['p50_ms'] or 0:>6.0f} | "
              f"{c['n']:>6} {c['correcta']:>8} {c['resuelta']:>8}")
    out = ROOT / "evals" / "experiments" / "2026-10-07-ronda5-dev.json"
    out.write_text(json.dumps(table, indent=1, ensure_ascii=False) + "\n")
    print(f"-> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
