"""Render evals/report.md (Spanish, it goes on the slides) from a raw eval run."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "duel"))

from duel_core import chrf_pp, corpus_chrf_pp, percentile  # noqa: E402

sys.path.insert(0, str(ROOT / "evals"))
from term_accuracy import TermBank, change_recall, foreign_slang, slang_handled  # noqa: E402

DATA = ROOT / "data"


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []


def term_section(raw: dict, summary: dict[str, dict], data_dir: Path) -> list[str]:
    """Slang-level metrics, so a win is about meaning and not surface overlap (see term_accuracy)."""
    terms = _jsonl(data_dir / "terms.jsonl")
    if not terms:
        return []
    bank = TermBank(terms)
    linked = {u["id"]: u.get("term_ids", []) for u in _jsonl(data_dir / "raw" / "web_usage.jsonl")}
    pairs = {p["id"]: p for p in raw["pairs"]}
    outputs = {"copiar la frase (línea base)": {pid: p["source"] for pid, p in pairs.items()}}
    for name, sm in summary.items():
        outputs[name] = {pid: text for pid, (_, text) in sm["sentence"].items()}

    def scores(hyps: dict[str, str]) -> dict:
        res = {"genz_to_parent": [], "parent_to_genz": [], "recall": []}
        for pid, hyp in hyps.items():
            p = pairs[pid]
            ok = slang_handled(bank, p, linked.get(p["provenance"].get("usage_id"), []), hyp)
            if ok is not None:
                res[p["direction"]].append(ok)
            r = change_recall(p["source"], p["target"], hyp)
            if r is not None:
                res["recall"].append(r)
        return res

    def pct(xs):
        return f"{100 * sum(xs) / len(xs):.0f} % (n={len(xs)})" if xs else "—"

    computed = {name: scores(h) for name, h in outputs.items()}
    rows = [
        [name, pct(c["genz_to_parent"]), pct(c["parent_to_genz"]), pct(c["genz_to_parent"] + c["parent_to_genz"]),
         f"{100 * sum(c['recall']) / len(c['recall']):.0f} %" if c["recall"] else "—"]
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
        table(["modelo", "jerga resuelta Gen Z → papás", "jerga resuelta papás → Gen Z", "jerga resuelta total", "cambios acertados"], rows),
        "",
    ]
    david = next((n for n, sm in summary.items() if sm["role"] == "david"), None)
    goliath = next((n for n, sm in summary.items() if sm["role"] == "goliath"), None)
    if david and goliath:
        only_d = only_g = 0
        for pid in set(outputs[david]) & set(outputs[goliath]):
            p = pairs[pid]
            ids = linked.get(p["provenance"].get("usage_id"), [])
            d, g = slang_handled(bank, p, ids, outputs[david][pid]), slang_handled(bank, p, ids, outputs[goliath][pid])
            if d is None or g is None:
                continue
            only_d += d and not g
            only_g += g and not d
        cd, cg = computed[david], computed[goliath]
        rate = lambda c: sum(c["genz_to_parent"] + c["parent_to_genz"]) / max(1, len(c["genz_to_parent"] + c["parent_to_genz"]))  # noqa: E731
        recall = lambda c: sum(c["recall"]) / max(1, len(c["recall"]))  # noqa: E731
        p2g = [pid for pid, p in pairs.items() if p["direction"] == "parent_to_genz"]
        foreign = {n: sum(foreign_slang(bank, pairs[pid], outputs[n].get(pid, "")) for pid in p2g) for n in (david, goliath)}
        lines += [
            f"Cara a cara en jerga resuelta: David la resuelve y Goliath no en **{only_d}** frases; al revés en **{only_g}**.",
            "",
            f"Jerga de otro país en papás → Gen Z (p. ej. «pisto» guatemalteco en una frase mexicana): "
            f"David {foreign[david]} de {len(p2g)}, Goliath {foreign[goliath]} de {len(p2g)}.",
            "",
        ]
        if rate(cg) > rate(cd) and recall(cg) > recall(cd):
            lines += [
                "**Lectura honesta:** en jerga gana Goliath. La ventaja de David en chrF++ viene sobre todo de quedarse "
                "cerca de la frase original, como la referencia, no de traducir mejor el término. El próximo David necesita "
                "datos que cambien la jerga de verdad (sobre todo papás → Gen Z) y del país correcto.",
                "",
            ]
        elif rate(cd) >= rate(cg) and recall(cd) >= recall(cg):
            lines += ["**Lectura honesta:** David también gana en jerga, no solo en parecido de superficie.", ""]
        else:
            lines += ["**Lectura honesta:** resultado mixto: cada modelo gana en una de las dos métricas de jerga.", ""]
    return lines

P50_BUDGET_MS = 1000  # David must answer in under a second on the stage laptop
ROLE_LABEL = {"base": "base (sin ajuste)", "david": "David (LoRA, Q4)", "david_f16": "David (LoRA, f16)", "goliath": "Goliath"}


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
        rows = by_model[m["name"]]
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
        out[m["name"]] = {
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
    bases = [s for s in summary.values() if s["role"] == "base" and s["chrf"] is not None]
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
    rows = [[s["name"], *[f"{_n(s[key][g][0])} (n={s[key][g][1]})" if g in s[key] else "—" for g in groups]] for s in summary.values()]
    return f"### chrF++ por {title}\n\n" + table(["modelo", *groups], rows)


def write_report(raw: dict, path: Path, runs_dir: Path | None = None, data_dir: Path = DATA) -> str:
    summary = summarize(raw)
    pairs = {p["id"]: p for p in raw["pairs"]}
    n_pairs = len(raw["pairs"])
    lines = [
        "# Genlingo — evaluación",
        "",
        f"Generado por `make eval` el {raw['created_at']}. {n_pairs} pares de prueba "
        f"({', '.join(sorted({p['origin'] for p in raw['pairs']}))}; nunca sintéticos).",
        "",
    ]
    if raw.get("mock"):
        lines += ["> **MOCK_AI=1**: números de ensayo con modelos simulados, no reales.", ""]
    if not raw["reviewed"]:
        lines += [
            "> **Ensayo:** las referencias de prueba aún están en `pending_review` (sin revisión del "
            "presentador). Los números cambiarán al aprobar/corregir el set con `make review-test`.",
            "",
        ]
    lines += [
        "## Resumen",
        "",
        "chrF++ de corpus (0–100, más es mejor) contra la referencia humana. Latencia de extremo a extremo "
        "con el modelo ya cargado; los modelos locales corren uno a la vez en la laptop del escenario.",
        "",
        table(
            ["modelo", "rol", "chrF++", "p50", "p95", "costo total", "costo / 1,000 frases", "tamaño", "errores"],
            [
                [s["name"], ROLE_LABEL.get(s["role"], s["role"]), _n(s["chrf"]), _ms(s["p50"]), _ms(s["p95"]),
                 _usd(s["cost"]), _usd(s["cost_per_1k"]), _gb(s.get("size_bytes")), s["errors"]]
                for s in summary.values()
            ],
        ),
        "",
    ]
    goliath_meta = next((m for m in raw["models"] if m.get("role") == "goliath" and m.get("price")), None)
    if goliath_meta:
        pr = goliath_meta["price"]
        since = f" (vigente desde {pr['effective_from']})" if pr.get("effective_from") else ""
        lines += [f"Costo de Goliath con la tarifa del día del eval: ${pr['input_per_million']:.2f} entrada / "
                  f"${pr['output_per_million']:.2f} salida por millón de tokens{since}."]
        nxt = goliath_meta.get("next_price")
        if nxt:
            rows = [r for r in raw["results"] if r["model"] == goliath_meta["name"] and "error" not in r]
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
        lines += ["Sin evaluar: " + "; ".join(f"`{m['name']}` ({m['skip']})" for m in skipped) + ".", ""]

    lines += term_section(raw, summary, data_dir)

    lines += [slice_table(summary, "by_origin", "origen"), "", slice_table(summary, "by_direction", "dirección"), "",
              slice_table(summary, "by_country", "país"), ""]

    base_name, why = pick_base(summary)
    lines += ["## Modelo base: E2B vs E4B", "", "Regla: el más pequeño que cumpla p50 < 1 s con el mejor chrF++.", "", why, ""]

    david = next((s for s in summary.values() if s["role"] == "david"), None)
    f16 = next((s for s in summary.values() if s["role"] == "david_f16"), None)
    lines += ["## Compresión: f16 vs Q4", ""]
    if david and f16:
        lines += [
            table(
                ["versión", "tamaño", "p50", "chrF++"],
                [["f16", _gb(f16.get("size_bytes")), _ms(f16["p50"]), _n(f16["chrf"])],
                 ["Q4_K_M", _gb(david.get("size_bytes")), _ms(david["p50"]), _n(david["chrf"])]],
            ),
            "",
        ]
    else:
        lines += ["Pendiente: se necesita David en f16 y en Q4 en Ollama (`make pull-model FP16=1`).", ""]

    lines += ["## Entrenamiento", ""]
    run = None
    if runs_dir and raw.get("david_tag") and (runs_dir / f"{raw['david_tag']}.json").exists():
        run = json.loads((runs_dir / f"{raw['david_tag']}.json").read_text())
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
                "Costo = segundos facturados × tarifas por segundo de Cloud Run (GPU L4 sin redundancia zonal + vCPU + memoria)."
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
        "- Mismo prompt para todos (`duel/genlingo_duel/prompts.py`), temperatura 0.",
        "- chrF++ = sacrebleu CHRF con `word_order=2`, a nivel de corpus.",
        "- Costo de Goliath = tokens × precio por millón configurado (`GEMINI_*_USD_PER_M`); los tokens de razonamiento se cobran como salida.",
        "- Resultados por frase en `evals/results/`.",
        "",
    ]
    text = "\n".join(lines)
    path.write_text(text, encoding="utf-8")
    return text
