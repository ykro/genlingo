"""The combinations niche (evals/niche.md, amendment 2) and the per-country, per-direction cuts, with bootstrap CIs.

    uv run --project duel python evals/combos_report.py --david <tag> [--combos evals/results/combos-….json]
                                                         [--test evals/results/<merged>.json] [--out evals/report_combos.md]

Reads per-sentence results (`make eval-combos` for the niche, `make eval` for the full test set) and writes
evals/report_combos.md: the niche's cuts as registered (all, per country, per direction, country × direction), each
David − Goliath with a paired bootstrap CI, and the same cuts on the whole test set as context. Metric: jerga
correcta (evals/term_accuracy.py: correct_slang, the rule in force); jerga resuelta and chrF++ alongside.
Cuts with fewer than MIN_N judged sentences get no verdict ("n insuficiente").
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "duel"))
sys.path.insert(0, str(ROOT / "evals"))

from genlingo_duel.glossary import load_counterparts  # noqa: E402
from niche_report import RESAMPLES, SEED, compare, table, verdict  # noqa: E402
from report import eval_terms_path  # noqa: E402
from term_accuracy import TermBank, correct_slang  # noqa: E402

DATA = ROOT / "data"
MIN_N = 30
USABLE = {"auto_validated", "approved"}
COUNTRIES = ("MX", "CO", "LATAM", "GT")
DIRS = {"genz_to_parent": "Gen Z → papás", "parent_to_genz": "papás → Gen Z"}


def cuts() -> dict:
    out = {"Todo": lambda p: True}
    out |= {f"País {c}": (lambda c: lambda p: p["country"] == c)(c) for c in COUNTRIES}
    out |= {d: (lambda d: lambda p: p["direction"] == d)(k) for k, d in DIRS.items()}
    out |= {f"{c} · {d}": (lambda c, k: lambda p: p["country"] == c and p["direction"] == k)(c, k)
            for c in COUNTRIES for k, d in DIRS.items()}
    return out


def fmt(name: str, c: dict | None) -> list[str]:
    if c is None:
        return [name, "0", "—", "—", "—", "—", "—", "—", "—"]
    pct = lambda x: f"{100 * x:.0f} %"  # noqa: E731
    lo, hi = c["ci"]
    wr = f"{c['only_david']}–{c['only_rival']}"
    v = verdict(lo, hi) if c["n"] >= MIN_N else "n insuficiente"
    return [name, str(c["n"]), pct(c["david"]), pct(c["rival"]), f"{100 * c['diff']:+.1f}",
            f"[{100 * lo:+.1f}, {100 * hi:+.1f}]", wr, f"{c['chrf_david']:.1f} / {c['chrf_rival']:.1f}", v]


HEAD = ["corte", "n", "David", "rival", "Δ (puntos)", "IC 95 %", "solo David – solo rival", "chrF++ David / rival", "veredicto"]


def labels(raw: dict) -> dict[str, str]:
    """name -> label of every model that ran, plus the roles of Goliath."""
    out = {}
    for m in raw["models"]:
        if m.get("skip"):
            continue
        out[m["name"] if m.get("role") not in ("goliath_glossary",) else "goliath_glossary"] = m.get("label", m["name"])
        if m.get("role") == "goliath":
            out["goliath"] = m.get("label", m["name"])
    return out


def section(raw: dict, title: str, david_tags: list[str], summary: dict, key: str) -> list[str]:
    bank = TermBank([json.loads(l) for l in eval_terms_path(DATA).read_text(encoding="utf-8").splitlines() if l.strip()],
                    ignore_ambiguous=True)
    cps = load_counterparts(DATA / "counterparts.jsonl")
    pairs = {p["id"]: p for p in raw["pairs"] if p.get("status") in USABLE}
    rows: dict[str, dict] = {}
    for r in raw["results"]:
        rows.setdefault(r["model"], {})[r["pair_id"]] = r
    lab = labels(raw)
    linked: dict = {}
    correct = lambda p, hyp: correct_slang(bank, cps, p, hyp)  # noqa: E731
    out = [f"## {title}", ""]
    rivals = [("goliath", "Goliath (rival, como en la página, sin glosario)"),
              ("goliath_glossary", "Goliath con el mismo glosario (referencia, no decide)")]
    for tag in david_tags:
        if tag not in lab:
            out += [f"_{tag}: no está en estos resultados._", ""]
            continue
        david = lab[tag]
        for rkey, rtitle in rivals:
            if rkey not in lab:
                continue
            for mname, metric in (("Jerga correcta", correct), ("Jerga resuelta", None)):
                rws = []
                for name, keep in cuts().items():
                    c = compare(pairs, rows, bank, linked, david, lab[rkey], keep, metric)
                    rws.append(fmt(name, c))
                    if c:
                        summary[f"{key} | {tag} | {rkey} | {mname} | {name}"] = {
                            k: (list(v) if isinstance(v, tuple) else v) for k, v in c.items()}
                out += [f"### {mname}: `{david}` contra {rtitle}", "", table(HEAD, rws), ""]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--david", required=True, help="tag of the round's David (chosen on dev)")
    ap.add_argument("--ref-david", default="genlingo-2026-10d-e2b", help="the page's David before the round")
    ap.add_argument("--combos", default="", help="results of make eval-combos (default: latest combos-*.json)")
    ap.add_argument("--test", default="", help="results of make eval (merged) for the context cuts")
    ap.add_argument("--out", default=str(ROOT / "evals" / "report_combos.md"))
    args = ap.parse_args()
    res = ROOT / "evals" / "results"
    combos = Path(args.combos) if args.combos else sorted(res.glob("combos-*.json"))[-1]
    raw = json.loads(combos.read_text())
    tags = [args.david, args.ref_david]
    summary: dict = {}
    n_ok = sum(1 for p in raw["pairs"] if p.get("status") in USABLE)
    out = [
        "# Combinaciones: frases con varios términos de jerga",
        "",
        f"Generado desde `evals/results/{combos.name}` ({raw.get('created_at')}). Nicho pre-registrado en "
        "[niche.md](niche.md) (enmienda 2, 2026-10-07): oraciones reales de la web cuyo lado Gen Z tiene 2 o más "
        f"términos Gen Z distintos del banco congelado; {n_ok} pares. Métrica que decide: jerga correcta. IC 95 % por "
        f"bootstrap pareado de la diferencia David − rival ({RESAMPLES:,} remuestreos, semilla {SEED}); gana David si "
        f"el límite inferior es mayor que 0. Cortes con menos de {MIN_N} frases juzgables: sin veredicto.",
        "",
    ]
    out += section(raw, "El nicho de combinaciones", tags, summary, "combos")
    if args.test:
        traw = json.loads(Path(args.test).read_text())
        out += [
            "---",
            "",
            f"Contexto (no es el nicho): el set de prueba completo (`evals/results/{Path(args.test).name}`), con los "
            "mismos cortes por país y dirección.",
            "",
        ]
        out += section(traw, "El set de prueba completo, por país y dirección", tags, summary, "test")
    Path(args.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    (Path(args.out).with_suffix(".json")).write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    print(f"report -> {Path(args.out).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
