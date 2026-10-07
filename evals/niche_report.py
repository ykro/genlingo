"""Pre-registered niches (evals/niche.md): the page's David against Goliath, with bootstrap CIs.

    uv run --project duel python evals/niche_report.py [evals/results/<run>.json]

Reads the per-phrase results of a `make eval` run (latest by default), slices them exactly as
evals/niche.md defines, and writes evals/niche_report.md. The niche definitions live in NICHES
and must match niche.md; they are never tuned after looking at results.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "duel"))
sys.path.insert(0, str(ROOT / "evals"))

from duel_core import corpus_chrf_pp, percentile  # noqa: E402
from report import eval_terms_path  # noqa: E402
from term_accuracy import TermBank, correct_slang, slang_handled  # noqa: E402
from genlingo_duel.glossary import load_counterparts  # noqa: E402

DATA = ROOT / "data"
RESAMPLES, SEED = 10_000, 2027
USABLE = {"auto_validated", "approved"}

# As registered in evals/niche.md (2026-10-02).
NICHES = {
    "Slang chapín (GT)": lambda p: p["country"] == "GT",
    "Papás → Gen Z (GT/CO)": lambda p: p["direction"] == "parent_to_genz" and p["country"] in ("GT", "CO"),
}
CONTEXT = {
    "Todo el set": lambda p: True,
    **{f"País {c}": (lambda c: lambda p: p["country"] == c)(c) for c in ("GT", "MX", "CO", "LATAM")},
}


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []


def bootstrap_diff(d: list[int], g: list[int], seed: int = SEED, n: int = RESAMPLES) -> tuple[float, float]:
    """Paired bootstrap of mean(d) - mean(g): resample phrases, keep each phrase's pair together."""
    rng = random.Random(seed)
    k = len(d)
    diffs = []
    for _ in range(n):
        idx = [rng.randrange(k) for _ in range(k)]
        diffs.append(sum(d[i] - g[i] for i in idx) / k)
    diffs.sort()
    return diffs[int(0.025 * n)], diffs[int(0.975 * n) - 1]


def verdict(lo: float, hi: float) -> str:
    if lo > 0:
        return "**gana David**"
    if hi < 0:
        return "**gana Goliath**"
    return "**empate estadístico**"


def compare(pairs: dict, rows: dict, bank: TermBank, linked: dict, david: str, rival: str, keep, metric=None) -> dict | None:
    """metric(pair, hypothesis) -> bool | None; default: jerga resuelta (slang handled)."""
    d_ok, g_ok, d_txt, g_txt, refs, d_lat, g_lat = [], [], [], [], [], [], []
    for pid, p in pairs.items():
        if not keep(p) or pid not in rows[david] or pid not in rows[rival]:
            continue
        dr, gr = rows[david][pid], rows[rival][pid]
        if "error" in dr or "error" in gr:
            continue
        ids = linked.get(p["provenance"].get("usage_id"), [])
        if metric is None:
            ds, gs = slang_handled(bank, p, ids, dr["text"]), slang_handled(bank, p, ids, gr["text"])
        else:
            ds, gs = metric(p, dr["text"]), metric(p, gr["text"])
        d_txt.append(dr["text"])
        g_txt.append(gr["text"])
        refs.append(p["target"])
        d_lat.append(dr.get("latency_ms"))
        g_lat.append(gr.get("latency_ms"))
        if ds is not None and gs is not None:
            d_ok.append(int(ds))
            g_ok.append(int(gs))
    if not d_ok:
        return None
    only_d = sum(1 for a, b in zip(d_ok, g_ok) if a and not b)
    only_g = sum(1 for a, b in zip(d_ok, g_ok) if b and not a)
    lo, hi = bootstrap_diff(d_ok, g_ok)
    return {
        "n": len(d_ok), "n_phrases": len(refs),
        "david": sum(d_ok) / len(d_ok), "rival": sum(g_ok) / len(g_ok),
        "diff": (sum(d_ok) - sum(g_ok)) / len(d_ok), "ci": (lo, hi),
        "win_rate": only_d / (only_d + only_g) if only_d + only_g else None, "only_david": only_d, "only_rival": only_g,
        "chrf_david": corpus_chrf_pp(d_txt, refs), "chrf_rival": corpus_chrf_pp(g_txt, refs),
        "p50_david": percentile(d_lat, 50), "p50_rival": percentile(g_lat, 50),
    }


def fmt_row(name: str, c: dict | None) -> list[str]:
    if c is None:
        return [name, "—", "—", "—", "—", "—", "—", "—", "—"]
    pct = lambda x: f"{100 * x:.0f} %"  # noqa: E731
    lo, hi = c["ci"]
    wr = f"{100 * c['win_rate']:.0f} % ({c['only_david']}–{c['only_rival']})" if c["win_rate"] is not None else "—"
    return [name, str(c["n"]), pct(c["david"]), pct(c["rival"]), f"{100 * c['diff']:+.1f}",
            f"[{100 * lo:+.1f}, {100 * hi:+.1f}]", wr, f"{c['chrf_david']:.1f} / {c['chrf_rival']:.1f}", verdict(lo, hi)]


HEAD = ["corte", "n", "David", "rival", "Δ (puntos)", "IC 95 %", "victorias de David", "chrF++ David / rival", "veredicto"]


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |"]
    return "\n".join(out + ["| " + " | ".join(str(x) for x in r) + " |" for r in rows])


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted((ROOT / "evals" / "results").glob("2*.json"))[-1]  # test runs only (never dev-* or probe-*); a merged run sorts after its parts
    raw = json.loads(path.read_text())
    bank = TermBank(_jsonl(eval_terms_path(DATA)), ignore_ambiguous=True)  # frozen with the test set
    linked = {u["id"]: u.get("term_ids", []) for u in _jsonl(DATA / "raw" / "web_usage.jsonl")}
    pairs = {p["id"]: p for p in raw["pairs"] if p.get("status") in USABLE}
    rows: dict[str, dict] = {}
    for r in raw["results"]:
        rows.setdefault(r["model"], {})[r["pair_id"]] = r
    role = {m.get("role"): m.get("label", m["name"]) for m in raw["models"] if not m.get("skip")}
    david_role = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--david-role=")), "david")
    david, goliath, gg = role[david_role], role["goliath"], role.get("goliath_glossary")
    cps = load_counterparts(DATA / "counterparts.jsonl")
    correct = lambda p, hyp: correct_slang(bank, cps, p, hyp)  # noqa: E731  (Amendment 1 of niche.md)

    out = [
        "# Nichos: David contra Goliath",
        "",
        f"Generado desde `evals/results/{path.name}` ({raw.get('created_at')}). Definiciones pre-registradas en "
        "[niche.md](niche.md). Métrica principal: jerga resuelta (`evals/term_accuracy.py`); IC 95 % por bootstrap "
        f"pareado de la diferencia ({RESAMPLES:,} remuestreos, semilla {SEED}). «Victorias de David»: frases donde solo "
        "David resuelve la jerga, sobre las frases donde la resuelve exactamente uno (entre paréntesis, solo David – solo el rival).",
        "",
        f"David: `{david}`. Rival del nicho: `{goliath}` (como en la página, sin glosario).",
        "",
    ]
    summary = {}
    for mname, metric in (("jerga resuelta", None), ("jerga correcta", correct)):
        for rival, title in ((goliath, "contra Goliath (rival del nicho)"), (gg, "contra Goliath con el mismo glosario (referencia, no decide)")):
            if not rival:
                continue
            rws = []
            for name, keep in {**NICHES, **CONTEXT}.items():
                c = compare(pairs, rows, bank, linked, david, rival, keep, metric)
                rws.append(fmt_row(name, c))
                if c:
                    summary[f"{mname} | {name} | {rival}"] = {k: (list(v) if isinstance(v, tuple) else v) for k, v in c.items()}
            out += [f"## {mname.capitalize()}, {title}", "", table(HEAD, rws), ""]
    out += [
        "## Slang reciente",
        "",
        "Sin veredicto: el nicho pide la primera fecha de publicación de cada término, y ni `SOURCES.md` ni el banco "
        "la registran (solo la fecha de consulta). Califican 0 frases, menos de las 30 que exige la regla: "
        "n insuficiente, y el nicho se deja de reportar.",
        "",
    ]
    (ROOT / "evals" / "niche_report.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
