"""Render evals/report.md (Spanish, it goes on the slides) from a raw eval run."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "duel"))

from duel_core import chrf_pp, corpus_chrf_pp, percentile  # noqa: E402

sys.path.insert(0, str(ROOT / "evals"))
from term_accuracy import (  # noqa: E402
    TermBank,
    change_recall,
    change_recall_synonyms,
    correct_slang,
    foreign_slang,
    slang_handled,
)
from genlingo_duel.glossary import load_counterparts  # noqa: E402

DATA = ROOT / "data"


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []


def eval_terms_path(data_dir: Path) -> Path:
    """Term metrics on the test set use the bank as it was when the test set and the niches were frozen
    (data/eval/terms_test.jsonl), so a growing bank can't move the goalposts between rounds."""
    frozen = data_dir / "eval" / "terms_test.jsonl"
    return frozen if frozen.exists() else data_dir / "terms.jsonl"


def term_section(raw: dict, summary: dict[str, dict], data_dir: Path, rates: dict | None = None) -> list[str]:
    """Slang-level metrics, so a win is about meaning and not surface overlap (see term_accuracy)."""
    terms = _jsonl(eval_terms_path(data_dir))
    if not terms:
        return []
    bank = TermBank(terms, ignore_ambiguous=True)  # ordinary-word terms would inflate the metric
    linked = {u["id"]: u.get("term_ids", []) for u in _jsonl(data_dir / "raw" / "web_usage.jsonl")}
    pairs = {p["id"]: p for p in raw["pairs"]}
    outputs = {"copiar la frase (línea base)": {pid: p["source"] for pid, p in pairs.items()}}
    for name, sm in summary.items():
        outputs[name] = {pid: text for pid, (_, text) in sm["sentence"].items()}

    cps = load_counterparts(data_dir / "counterparts.jsonl")

    def scores(hyps: dict[str, str]) -> dict:
        res = {"genz_to_parent": [], "parent_to_genz": [], "recall": [], "correct": [], "recall_syn": []}
        for pid, hyp in hyps.items():
            p = pairs[pid]
            ok = slang_handled(bank, p, linked.get(p["provenance"].get("usage_id"), []), hyp)
            if ok is not None:
                res[p["direction"]].append(ok)
            r = change_recall(p["source"], p["target"], hyp)
            if r is not None:
                res["recall"].append(r)
            if cps:  # Amendment 1 (niche.md): meaning-aware metrics
                c = correct_slang(bank, cps, p, hyp)
                if c is not None:
                    res["correct"].append(c)
                rs = change_recall_synonyms(bank, cps, p, hyp)
                if rs is not None:
                    res["recall_syn"].append(rs)
        return res

    def pct(xs):
        return f"{100 * sum(xs) / len(xs):.0f} % (n={len(xs)})" if xs else "—"

    computed = {name: scores(h) for name, h in outputs.items()}
    mean = lambda xs: f"{100 * sum(xs) / len(xs):.0f} %" if xs else "—"  # noqa: E731
    rows = [
        [name, pct(c["genz_to_parent"]), pct(c["parent_to_genz"]), pct(c["genz_to_parent"] + c["parent_to_genz"]),
         mean(c["recall"]), pct(c["correct"]), mean(c["recall_syn"])]
        for name, c in computed.items()
    ]
    lines = [
        "## ¿Tradujo la jerga?",
        "",
        "chrF++ premia parecerse a la referencia, y una reescritura de registro conserva casi todas las palabras: "
        "por eso copiar la frase ya saca ~50. Estas dos métricas miran solo lo que tenía que cambiar "
        "(detalle en `evals/term_accuracy.py`):",
        "",
        "- **Jerga resuelta**: Gen Z → papás, no queda en la salida ningún término Gen Z del banco que tenía la frase; "
        "papás → Gen Z, la salida usa al menos un término Gen Z del banco del país. Mide que cambió el registro, no que el significado sea correcto.",
        "- **Cambios acertados**: de las palabras que la referencia humana cambió respecto al original, cuántas aparecen en la salida. "
        "Mide significado, pero solo con palabras exactas: un sinónimo válido cuenta como fallo para todos.",
        "",
        "- **Jerga correcta** y **cambios acertados con sinónimos** (enmienda 1 de `evals/niche.md`): el término "
        "producido tiene que significar lo mismo, según la tabla de contrapartes validada por significado "
        "(`data/counterparts.jsonl`); con sinónimos, una palabra cuenta si coincide la raíz o es un término enlazado.",
        "",
        table(["modelo", "jerga resuelta Gen Z → papás", "jerga resuelta papás → Gen Z", "jerga resuelta total", "cambios acertados",
               "jerga correcta", "cambios acertados (sinónimos)"], rows),
        "",
    ]
    def handled_total(c):
        xs = c["genz_to_parent"] + c["parent_to_genz"]
        return sum(xs) / len(xs) if xs else 0.0

    # On-stage David. Rule: the best slang handling among Davids within the latency budget; if a
    # quantization sweep exists, the SMALLEST file within 2 points of that best (compression wins
    # unless it costs slang).
    candidates = [n for n, sm in summary.items() if sm["role"] in ("david", "david_alt", "david_f16", "david_alt_f16")
                  and sm["p50"] is not None and sm["p50"] < P50_BUDGET_MS]
    best = max(candidates, key=lambda n: (round(handled_total(computed[n]), 3), summary[n]["chrf"] or 0), default=None)
    david = best
    if best:
        # Reference: the unquantized f16 of the best family when it was evaluated, else the best.
        family = best.removesuffix(" + glosario").split("-q")[0].split("-iq")[0].removesuffix("-f16")
        ref = next((n for n in candidates if n.removesuffix(" + glosario") == f"{family}-f16"), best)
        near = [n for n in candidates if handled_total(computed[n]) >= handled_total(computed[ref]) - 0.02
                and summary[n].get("size_bytes")]
        david = min(near, key=lambda n: summary[n]["size_bytes"], default=best)
        lines += [
            f"**David en escena:** `{david}` ({_gb(summary[david].get('size_bytes'))}, p50 {_ms(summary[david]['p50'])}): "
            f"el archivo más pequeño a ≤ 2 puntos de `{ref}` ({100 * handled_total(computed[ref]):.0f} % de jerga resuelta), "
            f"con p50 < 1 s. Resuelve {100 * handled_total(computed[david]):.0f} %.",
            "",
        ]
    if rates is not None:  # read by compression_section
        rates.update({n: {"handled": handled_total(c), "recall": sum(c["recall"]) / max(1, len(c["recall"]))}
                      for n, c in computed.items()})
    for gname in [n for n, sm in summary.items() if sm["role"] in ("goliath", "goliath_glossary")]:
        if not david:
            break
        only_d = only_g = 0
        for pid in set(outputs[david]) & set(outputs[gname]):
            p = pairs[pid]
            ids = linked.get(p["provenance"].get("usage_id"), [])
            d, g = slang_handled(bank, p, ids, outputs[david][pid]), slang_handled(bank, p, ids, outputs[gname][pid])
            if d is None or g is None:
                continue
            only_d += d and not g
            only_g += g and not d
        lines += [f"Cara a cara con `{gname}` en jerga resuelta: David la resuelve y Goliath no en **{only_d}** frases; al revés en **{only_g}**.", ""]

    goliath = next((n for n, sm in summary.items() if sm["role"] == "goliath"), None)
    if david and goliath:
        cd, cg = computed[david], computed[goliath]
        recall = lambda c: sum(c["recall"]) / max(1, len(c["recall"]))  # noqa: E731
        p2g = [pid for pid, p in pairs.items() if p["direction"] == "parent_to_genz"]
        names = [n for n in summary if summary[n]["role"] in ("david", "david_alt", "goliath", "goliath_glossary", "base")]
        foreign = {n: sum(foreign_slang(bank, pairs[pid], outputs[n].get(pid, "")) for pid in p2g) for n in names}
        lines += [
            "Jerga de otro país en papás → Gen Z (p. ej. «pisto» guatemalteco en una frase mexicana): "
            + ", ".join(f"{n} {foreign[n]}" for n in names) + f" (de {len(p2g)}).",
            "",
        ]
        if handled_total(cg) > handled_total(cd) and recall(cg) > recall(cd):
            lines += ["**Lectura honesta:** en jerga gana Goliath, incluso frente al mejor David. La ventaja de David en chrF++ "
                      "viene sobre todo de quedarse cerca de la frase original, no de traducir mejor el término.", ""]
        elif handled_total(cd) >= handled_total(cg) and recall(cd) >= recall(cg):
            lines += ["**Lectura honesta:** David gana también en jerga, no solo en parecido de superficie, frente a Goliath sin glosario. "
                      "Compáralo con Goliath + glosario para separar lo que aporta el modelo de lo que aporta el dato.", ""]
        else:
            lines += ["**Lectura honesta:** resultado mixto: cada uno gana en una de las dos métricas de jerga.", ""]
        gg = next((n for n, sm in summary.items() if sm["role"] == "goliath_glossary"), None)
        if gg:
            better = handled_total(computed[gg]) > handled_total(cd)
            lines += [
                f"Con el mismo glosario, Goliath resuelve {100 * handled_total(computed[gg]):.0f} % de la jerga frente al "
                f"{100 * handled_total(cd):.0f} % de David: "
                + ("la ventaja de David viene de **sus datos** (el banco de términos), no de ser mejor modelo; "
                   "y esos datos los tiene él, no Goliath." if better else "David sigue por delante incluso con el glosario compartido."),
                "",
            ]
        q4 = david.removesuffix(" + glosario").removesuffix("-f16")
        q4 = next((n for n in summary if n.startswith(q4) and "-f16" not in n), None)
        if q4 and q4 != david and david in computed and q4 in computed:
            lines += [
                f"Compresión y jerga: `{q4}` (Q4, {_gb(summary[q4].get('size_bytes'))}) resuelve "
                f"{100 * handled_total(computed[q4]):.0f} % frente al {100 * handled_total(computed[david]):.0f} % de `{david}` "
                f"({_gb(summary[david].get('size_bytes'))}). Cuantizar cuesta jerga, no solo chrF++.",
                "",
            ]
    return lines

P50_BUDGET_MS = 1000  # David must answer in under a second on the stage laptop
ROLE_LABEL = {
    "base": "base (sin ajuste)",
    "david": "David (LoRA, {quant})",
    "david_f16": "David (LoRA, f16)",
    "david_alt": "David candidato (LoRA, {quant})",
    "david_alt_f16": "David candidato (LoRA, f16)",
    "goliath": "Goliath",
    "goliath_glossary": "Goliath con el glosario de David",
}
PROMPT_LABEL = {"v1": "v1", "v2": "v2", "v2+glossary": "v2 + glosario"}


def quant_label(name: str, meta: dict | None) -> str:
    """Quantization of a local variant: the tag suffix wins (-q5_k_m, -iq-q4_k_m, -f16), else what the eval recorded."""
    import re

    tag = name.removesuffix(" + glosario")
    m = re.search(r"-(?:iq-)?(q\d_k_m|q\d_k|q8_0|f16)$", tag)
    return m.group(1).upper() if m else ((meta or {}).get("quant") or "Q4_K_M")


def _n(x, d=1):
    return "—" if x is None else f"{x:,.{d}f}"


def _ms(x):
    return "—" if x is None else (f"{x / 1000:.2f} s" if x >= 1000 else f"{x:.0f} ms")


def _gb(b):
    return "—" if not b else f"{b / 1e9:.2f} GB"


def _usd(x):
    if x is None:
        return "—"
    if x == 0:
        return "$0"
    return f"${x:,.2f}" if x >= 0.1 else f"${x:.4f}"


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |"]
    return "\n".join(out + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def summarize(raw: dict) -> dict[str, dict]:
    pairs = {p["id"]: p for p in raw["pairs"]}
    by_model: dict[str, list] = defaultdict(list)
    for r in raw["results"]:
        by_model[r["model"]].append(r)
    out = {}
    for m in raw["models"]:
        if m.get("skip"):
            continue
        key = m.get("label", m["name"])
        rows = by_model[key]
        ok = [r for r in rows if "error" not in r]
        hyps = [r["text"] for r in ok]
        refs = [pairs[r["pair_id"]]["target"] for r in ok]

        def sliced(key):
            groups = defaultdict(lambda: ([], []))
            for r in ok:
                g = pairs[r["pair_id"]][key]
                groups[g][0].append(r["text"])
                groups[g][1].append(pairs[r["pair_id"]]["target"])
            return {g: (corpus_chrf_pp(h, rf), len(h)) for g, (h, rf) in sorted(groups.items())}

        cost = sum(r["cost_usd"] for r in ok)
        out[key] = {
            **m,
            "n": len(rows),
            "errors": len(rows) - len(ok),
            "chrf": corpus_chrf_pp(hyps, refs) if ok else None,
            "by_origin": sliced("origin"),
            "by_direction": sliced("direction"),
            "by_country": sliced("country"),
            "p50": percentile([r["latency_ms"] for r in ok], 50),
            "p95": percentile([r["latency_ms"] for r in ok], 95),
            "cost": cost,
            "cost_per_1k": cost / len(ok) * 1000 if ok else None,
            "sentence": {r["pair_id"]: (chrf_pp(r["text"], pairs[r["pair_id"]]["target"]), r["text"]) for r in ok},
        }
    return out


def pick_base(summary: dict[str, dict]) -> tuple[str | None, str]:
    """Smallest base model with p50 < 1 s and the best chrF++ (ties -> smaller)."""
    bases = [s for s in summary.values() if s["role"] == "base" and s.get("style", "v2") != "v2+glossary" and s["chrf"] is not None]
    fast = [s for s in bases if s["p50"] is not None and s["p50"] < P50_BUDGET_MS]
    if not fast:
        return None, "Ningún modelo base cumple p50 < 1 s."
    best = max(fast, key=lambda s: (round(s["chrf"], 1), -(s.get("size_bytes") or 0)))
    return best["name"], (
        f"**{best['name']}**: mejor chrF++ ({best['chrf']:.1f}) entre los que cumplen p50 < 1 s "
        f"(p50 {_ms(best['p50'])}, {_gb(best.get('size_bytes'))})."
    )


def slice_table(summary, key, title):
    groups = sorted({g for s in summary.values() for g in s[key]})
    rows = [[name, *[f"{_n(s[key][g][0])} (n={s[key][g][1]})" if g in s[key] else "—" for g in groups]] for name, s in summary.items()]
    return f"### chrF++ por {title}\n\n" + table(["modelo", *groups], rows)


def compression_section(summary: dict, rates: dict, out_dir: Path) -> list[str]:
    """Size vs slang for the quantized exports of one David (quant sweep), with a small SVG chart."""
    sweep_path = ROOT / "evals" / "quant_sweep.json"
    if not sweep_path.exists() or not rates:
        return []
    sweep = json.loads(sweep_path.read_text())
    fam = sweep["tag"]
    rows = []
    for name, sm in summary.items():
        if not name.startswith(fam) or not sm.get("size_bytes") or name not in rates:
            continue
        variant = name.removesuffix(" + glosario")
        quant = "F16" if variant.endswith("-f16") else (variant[len(fam) + 1:].upper().replace("IQ-", "") if variant != fam else "Q4_K_M")
        rows.append({"name": name, "quant": quant, "imatrix": "-iq-" in variant, "gb": sm["size_bytes"] / 1e9,
                     "handled": rates[name]["handled"], "recall": rates[name]["recall"], "chrf": sm["chrf"], "p50": sm["p50"]})
    if len(rows) < 2:
        return []
    rows.sort(key=lambda r: r["gb"])
    svg = compression_svg(rows)
    (out_dir / "compression.svg").write_text(svg, encoding="utf-8")
    table_rows = [[f"`{r['name']}`", r["quant"], "sí" if r["imatrix"] else "no", f"{r['gb']:.2f} GB", f"{100 * r['handled']:.0f} %",
                   f"{100 * r['recall']:.0f} %", _n(r["chrf"]), _ms(r["p50"])] for r in rows]
    return [
        "## Compresión: tamaño vs jerga",
        "",
        f"Las exportaciones de `{fam}` con el mismo prompt y glosario. La curva muestra cuánta jerga se pierde al comprimir.",
        "",
        "![Tamaño vs jerga resuelta](compression.svg)",
        "",
        table(["variante", "cuantización", "imatrix", "tamaño", "jerga resuelta", "cambios acertados", "chrF++", "p50"], table_rows),
        "",
        "**imatrix (importance matrix):** antes de cuantizar, llama.cpp pasa el modelo f16 por texto de calibración y mide "
        "qué pesos influyen más; la cuantización gasta los bits ahí. Calibramos con **pares de entrenamiento** renderizados con "
        "el prompt de David (`train/quant_sweep.py`), nunca con el set de prueba: eso inflaría el eval.",
        "",
    ]


def compression_svg(rows: list[dict]) -> str:
    """Tiny dependency-free scatter: size (GB) vs slang handled (%), Marcador palette."""
    w, h, pad = 720, 360, 56
    xs = [r["gb"] for r in rows]
    ys = [100 * r["handled"] for r in rows]
    x0, x1 = 0, max(xs) * 1.08
    y0, y1 = max(0, min(ys) - 10), min(100, max(ys) + 6)
    px = lambda x: pad + (x - x0) / (x1 - x0) * (w - 2 * pad)  # noqa: E731
    py = lambda y: h - pad - (y - y0) / (y1 - y0) * (h - 2 * pad)  # noqa: E731
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" font-family="Figtree, sans-serif" font-size="13">',
             f'<rect width="{w}" height="{h}" fill="#F6F3EC"/>',
             f'<line x1="{pad}" y1="{h - pad}" x2="{w - pad}" y2="{h - pad}" stroke="#16181D"/>',
             f'<line x1="{pad}" y1="{pad / 2}" x2="{pad}" y2="{h - pad}" stroke="#16181D"/>',
             f'<text x="{w / 2}" y="{h - 14}" text-anchor="middle" fill="#5A5E66">tamaño del archivo (GB)</text>',
             f'<text x="16" y="{h / 2}" text-anchor="middle" fill="#5A5E66" transform="rotate(-90 16 {h / 2})">jerga resuelta (%)</text>']
    for gb in range(0, int(x1) + 1, 2):
        parts.append(f'<text x="{px(gb):.0f}" y="{h - pad + 18}" text-anchor="middle" fill="#5A5E66">{gb}</text>')
    for v in range(int(y0 // 5 * 5), int(y1) + 1, 5):
        if v >= y0:
            parts.append(f'<text x="{pad - 8}" y="{py(v) + 4:.0f}" text-anchor="end" fill="#5A5E66">{v}</text>')
    pts = " ".join(f"{px(r['gb']):.1f},{py(100 * r['handled']):.1f}" for r in rows)
    parts.append(f'<polyline points="{pts}" fill="none" stroke="#D9D4C7" stroke-width="2"/>')
    for r in rows:
        color = "#2B4ACB" if r["imatrix"] else "#C23D19"
        x, y = px(r["gb"]), py(100 * r["handled"])
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{color}"/>')
        label = r["quant"] + (" imatrix" if r["imatrix"] else "")
        parts.append(f'<text x="{x + 9:.1f}" y="{y - 8:.1f}" fill="#16181D">{label} · {100 * r["handled"]:.0f} %</text>')
    parts.append(f'<text x="{w - pad}" y="{pad / 2 + 4}" text-anchor="end" fill="#5A5E66">'
                 '<tspan fill="#C23D19">●</tspan> cuantización normal  <tspan fill="#2B4ACB">●</tspan> con imatrix</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def write_report(raw: dict, path: Path, runs_dir: Path | None = None, data_dir: Path = DATA) -> str:
    summary = summarize(raw)
    pairs = {p["id"]: p for p in raw["pairs"]}
    n_pairs = len(raw["pairs"])
    dev = raw.get("split") == "dev"
    lines = [
        "# Genlingo — evaluación" + (" en desarrollo" if dev else ""),
        "",
        *(["> **Set de desarrollo** (`data/pairs/dev_real.jsonl`): para decidir rondas de datos. Los Davids "
           "entrenados antes del 2026-10-02 vieron estos pares al entrenar, así que su número aquí es optimista.", ""]
          if dev else []),
        f"Generado por `make eval` el {raw['created_at']}. {n_pairs} pares de {'desarrollo' if dev else 'prueba'} "
        f"({', '.join(sorted({p['origin'] for p in raw['pairs']}))}; nunca sintéticos), "
        + ", ".join(f"{v} {k}" for k, v in sorted(Counter(p["status"] for p in raw["pairs"]).items())) + ". "
        "`auto_validated` = validada automáticamente contra el banco de términos (`scripts/validate_test_set.py`).",
        "",
    ]
    if raw.get("mock"):
        lines += ["> **MOCK_AI=1**: números de ensayo con modelos simulados, no reales.", ""]
    if not raw["reviewed"]:
        lines += [
            "> **Ensayo:** este eval incluyó referencias sin validar (`pending_review`); "
            "corre `make test-set` para validarlas automáticamente.",
            "",
        ]
    meta_by = {m.get("label", m["name"]): m for m in raw["models"]}
    lines += [
        "## Resumen",
        "",
        "chrF++ de corpus (0–100, más es mejor) contra la referencia humana. Latencia de extremo a extremo "
        "con el modelo ya cargado; los modelos locales corren uno a la vez en la laptop del escenario.",
        "",
        table(
            ["modelo", "rol", "prompt", "chrF++", "p50", "p95", "costo total", "costo / 1,000 frases", "tamaño", "errores"],
            [
                [name, ROLE_LABEL.get(s["role"], s["role"]).format(quant=quant_label(name, meta_by.get(name))), PROMPT_LABEL.get(s.get("style", "v1"), "v1"), _n(s["chrf"]), _ms(s["p50"]), _ms(s["p95"]),
                 _usd(s["cost"]), _usd(s["cost_per_1k"]), _gb(s.get("size_bytes")), s["errors"]]
                for name, s in summary.items()
            ],
        ),
        "",
    ]
    goliath_meta = next((m for m in raw["models"] if m.get("role") == "goliath" and m.get("price") and not m.get("skip")), None)
    if goliath_meta:
        pr = goliath_meta["price"]
        since = f" (vigente desde {pr['effective_from']})" if pr.get("effective_from") else ""
        lines += [f"Costo de Goliath con la tarifa del día del eval: ${pr['input_per_million']:.2f} entrada / "
                  f"${pr['output_per_million']:.2f} salida por millón de tokens{since}."]
        nxt = goliath_meta.get("next_price")
        if nxt:
            rows = [r for r in raw["results"] if r["model"] in (goliath_meta.get("label", goliath_meta["name"]), goliath_meta["name"]) and "error" not in r]
            later = sum((r["input_tokens"] * nxt["input_per_million"] + r["output_tokens"] * nxt["output_per_million"]) / 1e6 for r in rows)
            lines += [f"Con la tarifa desde {nxt['effective_from']} (${nxt['input_per_million']:.2f} / ${nxt['output_per_million']:.2f}), "
                      f"este mismo eval costaría {_usd(later)} ({_usd(later / len(rows) * 1000) if rows else '—'} por 1,000 frases)."]
        lines += [""]
    ids = [p["id"] for p in raw["pairs"]]
    copy = corpus_chrf_pp([pairs[i]["source"] for i in ids], [pairs[i]["target"] for i in ids])
    lines += [
        f"**Línea base \"copiar la frase\"** (devolver el texto original sin traducir): chrF++ {copy:.1f}. "
        "Un modelo que no supera esta línea no está traduciendo mejor que no hacer nada; mide cuánto del "
        "puntaje viene de palabras que la referencia comparte con el original.",
        "",
    ]
    skipped = [m for m in raw["models"] if m.get("skip")]
    if skipped:
        lines += ["Sin evaluar: " + "; ".join(f"`{m.get('label', m['name'])}` ({m['skip']})" for m in skipped) + ".", ""]

    rates: dict = {}
    lines += term_section(raw, summary, data_dir, rates)
    lines += compression_section(summary, rates, path.parent)

    lines += [slice_table(summary, "by_origin", "origen"), "", slice_table(summary, "by_direction", "dirección"), "",
              slice_table(summary, "by_country", "país"), ""]

    base_name, why = pick_base(summary)
    lines += ["## Modelo base: E2B vs E4B", "", "Regla: el más pequeño que cumpla p50 < 1 s con el mejor chrF++.", "", why, ""]

    david = next((s for s in summary.values() if s["role"] == "david"), None)
    f16 = next((s for s in summary.values() if s["role"] == "david_f16"), None)
    quant = next((quant_label(m.get("label", m["name"]), m) for m in raw["models"] if m.get("role") == "david"), "Q4_K_M")
    lines += [f"## Compresión: f16 vs {quant}", ""]
    if david and f16:
        lines += [
            table(
                ["versión", "tamaño", "p50", "chrF++"],
                [["f16", _gb(f16.get("size_bytes")), _ms(f16["p50"]), _n(f16["chrf"])],
                 [quant, _gb(david.get("size_bytes")), _ms(david["p50"]), _n(david["chrf"])]],
            ),
            "",
        ]
    else:
        lines += ["Pendiente: se necesita David en f16 y cuantizado en Ollama (`make pull-model FP16=1`).", ""]

    lines += ["## Entrenamiento", ""]
    run = None
    if runs_dir and raw.get("david_tag"):
        from genlingo_duel.runs import load_run

        run = load_run(runs_dir, raw["david_tag"])
    if run and run.get("duration_s"):
        met = run.get("metrics", {})
        lines += [
            table(
                ["tag", "máquina", "región", "ejemplos", "duración", "costo estimado", "loss inicial → final"],
                [[run["tag"], run["machine"], run["region"], run.get("examples"), f"{run['duration_s'] / 60:.1f} min",
                  _usd(run.get("estimated_cost_usd")), f"{_n(met.get('train_loss_first'), 2)} → {_n(met.get('train_loss_last'), 2)}"]],
            ),
            "",
            (
                "Costo = segundos facturados × tarifas por segundo de Cloud Run (GPU L4 sin redundancia zonal + vCPU + memoria"
                + ("; entrenamiento en la L4 + fusión y GGUF en un job de CPU)." if run.get("stages") else ").")
                if run.get("rates_usd_per_s")
                else f"Costo = duración × tarifa por hora estimada (${run.get('hourly_usd', 0)}/h)."
            )
            + " Un reentrenamiento mensual cuesta eso; la inferencia de David cuesta $0 porque corre en la laptop.",
            "",
        ]
    else:
        lines += ["Aún no hay una corrida de entrenamiento terminada para el tag actual de David.", ""]

    goliath = next((s for s in summary.values() if s["role"] == "goliath"), None)
    if david and goliath:
        common = set(david["sentence"]) & set(goliath["sentence"])
        wins = sum(1 for pid in common if david["sentence"][pid][0] > goliath["sentence"][pid][0] + 0.5)
        losses = sorted(common, key=lambda pid: david["sentence"][pid][0] - goliath["sentence"][pid][0])[:10]
        lines += [
            "## Dónde pierde David",
            "",
            f"David gana {wins} de {len(common)} frases por chrF++ de oración. Las 10 peores derrotas:",
            "",
            table(
                ["frase", "referencia", "David", "Goliath", "Δ chrF++"],
                [[pairs[pid]["source"], pairs[pid]["target"], david["sentence"][pid][1], goliath["sentence"][pid][1],
                  _n(david["sentence"][pid][0] - goliath["sentence"][pid][0])] for pid in losses],
            ),
            "",
        ]
    lines += [
        "## Metodología",
        "",
        "- Prompts en `duel/genlingo_duel/prompts.py`, temperatura 0. Cada variante declara su prompt en la tabla: cada David "
        "con el prompt con el que se entrenó; los modelos base y Goliath con v2, y también con el glosario de David "
        "(«+ glosario») para que la comparación con los datos de David sea justa y visible.",
        "- Glosario: entradas del banco de términos recuperadas con EmbeddingGemma local; su tiempo cuenta en la latencia.",
        "- chrF++ = sacrebleu CHRF con `word_order=2`, a nivel de corpus.",
        "- Costo de Goliath = tokens × precio por millón vigente el día del eval (`GEMINI_PRICE_SCHEDULE`); los tokens de razonamiento se cobran como salida.",
        "- Resultados por frase en `evals/results/`.",
        "",
    ]
    text = "\n".join(lines)
    path.write_text(text, encoding="utf-8")
    return text
