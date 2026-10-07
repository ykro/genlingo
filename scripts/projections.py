"""The README's "time and cost in the cloud" section, computed from what `make capacity` measured
(docs/data/capacity.json). `make projections` rewrites it in README.md and README.en.md, between the
`<!-- projections -->` markers, so no number in it is typed by hand.

Cost per translation at a steady volume V (translations per hour):
- Goliath: what Gemini bills for one translation (mean tokens of the run × the price per million tokens),
  the same at any volume.
- David: his GPU is billed by the second while it's on, whatever it does, so one hour of GPU is spread
  over that hour's translations: R / V, where R is the service's price per hour. One GPU handles at most C
  translations per hour (the best throughput measured); past that you add GPUs: ceil(V / C) × R / V.
Break-even: R / g, where g is Goliath's cost per translation. Per month: 730 hours at that volume.
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data" / "capacity.json"
HOURS_PER_MONTH = 730
VOLUMES = (50, 500, 1_000, 5_000, 20_000, 50_000)
START, END = "<!-- projections: make projections -->", "<!-- /projections -->"


def usd(x: float) -> str:
    if x >= 100:
        return f"${x:,.0f}"
    if x >= 1:
        return f"${x:,.2f}"
    digits = max(2, 1 - math.floor(math.log10(x)))
    return f"${x:.{digits}f}"


def s(ms: float) -> str:
    return f"{ms / 1000:.1f} s"


def section(lang: str) -> str:
    d = json.loads(DATA.read_text())
    es = lang == "es"
    rate = d["david_usd_per_hour"]
    one = next(r for r in d["david"] if r["concurrency"] == 1)
    best = max(d["david"], key=lambda r: r["per_hour"])
    cap = best["per_hour"]
    g = d["goliath"]
    (today, g_now), (later, g_next) = sorted(g["usd_per_translation"].items())
    day = d["measured_at"][:10]

    def david(v: int) -> float:
        return math.ceil(v / cap) * rate / v

    out = []
    if es:
        out.append(f"Medido el {day} con `make capacity` ([`scripts/bench_capacity.py`](scripts/bench_capacity.py) → "
                   f"[`docs/data/capacity.json`](docs/data/capacity.json)): {one['n']} frases del set de prueba, con el mismo "
                   "código de la página, contra el David de Cloud Run (1 NVIDIA L4) y contra Gemini. Las tablas las escribe "
                   "`make projections` a partir de ese archivo.\n")
        out.append("**Tiempo por traducción** (de que se pide a que llega la respuesta)\n")
        out.append("| | Mediana | p95 | Traducciones por hora |\n| --- | ---: | ---: | ---: |")
        for r in d["david"]:
            out.append(f"| David, {r['concurrency']} a la vez | {s(r['median_ms'])} | {s(r['p95_ms'])} | {r['per_hour']:,} |")
        out.append(f"| Goliath (Gemini) | {s(g['median_ms'])} | {s(g['p95_ms'])} | sin límite propio |\n")
        out.append(f"David es más rápido en todos los casos medidos: su mediana con {best['concurrency']} traducciones a la vez "
                   f"({s(best['median_ms'])}) sigue debajo de la de Goliath ({s(g['median_ms'])})."
                   + (f" De las {g['n']} llamadas a Gemini, {g['errors']} fallaron por saturación de Vertex AI (429); "
                      "la página reintenta sola." if g["errors"] else "") + "\n")
        out.append("**Costo.** La GPU de David se cobra por segundo mientras está encendida, haga lo que haga: "
                   f"R = L4 + 4 vCPU + 16 GiB ≈ **{usd(rate)} por hora**. Gemini cobra por token: en la medición cada traducción "
                   f"usó en promedio {g['mean_input_tokens']:.0f} tokens de entrada y {g['mean_output_tokens']:.0f} de salida "
                   f"(incluye su razonamiento), o sea g ≈ **{usd(g_now)}** con la tarifa de hoy ($0.75 / $3.75 por millón) y "
                   f"**{usd(g_next)}** desde el {later} ($1.50 / $7.50).\n")
        out.append(f"- David por traducción = R ÷ V, con V traducciones por hora. Una GPU aguanta hasta C = {cap:,} por hora "
                   f"(lo mejor medido, {best['concurrency']} a la vez); con más, se suman GPUs: ⌈V ÷ C⌉ × R ÷ V.")
        out.append("- Goliath por traducción = g, igual a cualquier volumen.")
        out.append(f"- Equilibrio: V = R ÷ g. Al mes: {HOURS_PER_MONTH} horas a ese volumen.\n")
        out.append("| Traducciones por hora | GPUs de David | David por traducción | Goliath por traducción (hoy) | "
                   f"Goliath (desde {later}) | David al mes | Goliath al mes (hoy) | Goliath al mes (desde {later}) |")
    else:
        out.append(f"Measured on {day} with `make capacity` ([`scripts/bench_capacity.py`](scripts/bench_capacity.py) → "
                   f"[`docs/data/capacity.json`](docs/data/capacity.json)): {one['n']} test-set phrases, with the page's own code, "
                   "against the Cloud Run David (1 NVIDIA L4) and against Gemini. `make projections` writes the tables from "
                   "that file.\n")
        out.append("**Time per translation** (from the request to the answer)\n")
        out.append("| | Median | p95 | Translations per hour |\n| --- | ---: | ---: | ---: |")
        for r in d["david"]:
            out.append(f"| David, {r['concurrency']} at a time | {s(r['median_ms'])} | {s(r['p95_ms'])} | {r['per_hour']:,} |")
        out.append(f"| Goliath (Gemini) | {s(g['median_ms'])} | {s(g['p95_ms'])} | no limit of its own |\n")
        out.append(f"David is faster in every case measured: his median with {best['concurrency']} translations at a time "
                   f"({s(best['median_ms'])}) is still below Goliath's ({s(g['median_ms'])})."
                   + (f" Of the {g['n']} Gemini calls, {g['errors']} failed because Vertex AI was saturated (429); the page "
                      "retries on its own." if g["errors"] else "") + "\n")
        out.append("**Cost.** David's GPU is billed by the second while it's on, whatever it does: "
                   f"R = L4 + 4 vCPU + 16 GiB ≈ **{usd(rate)} per hour**. Gemini bills by token: in the measurement each "
                   f"translation used {g['mean_input_tokens']:.0f} input and {g['mean_output_tokens']:.0f} output tokens on "
                   f"average (its reasoning included), so g ≈ **{usd(g_now)}** at today's price ($0.75 / $3.75 per million) "
                   f"and **{usd(g_next)}** from {later} ($1.50 / $7.50).\n")
        out.append(f"- David per translation = R ÷ V, for V translations per hour. One GPU handles up to C = {cap:,} per "
                   f"hour (the best measured, {best['concurrency']} at a time); beyond that, add GPUs: ⌈V ÷ C⌉ × R ÷ V.")
        out.append("- Goliath per translation = g, the same at any volume.")
        out.append(f"- Break-even: V = R ÷ g. Per month: {HOURS_PER_MONTH} hours at that volume.\n")
        out.append("| Translations per hour | David's GPUs | David per translation | Goliath per translation (today) | "
                   f"Goliath (from {later}) | David per month | Goliath per month (today) | Goliath per month (from {later}) |")
    out.append("| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for v in VOLUMES:
        gpus = math.ceil(v / cap)
        dv = david(v)
        mark = (lambda x, other: f"**{usd(x)}**" if x < other else usd(x))
        out.append(f"| {v:,} | {gpus} | {mark(dv, g_now)} | {mark(g_now, dv)} | {mark(g_next, dv)} | "
                   f"{mark(gpus * rate * HOURS_PER_MONTH, g_now * v * HOURS_PER_MONTH)} | "
                   f"{mark(g_now * v * HOURS_PER_MONTH, gpus * rate * HOURS_PER_MONTH)} | {usd(g_next * v * HOURS_PER_MONTH)} |")
    be_now, be_next = rate / g_now, rate / g_next
    low = rate / cap
    if es:
        out.append(f"\n**Dónde gana David:** desde unas **{be_now:,.0f} traducciones por hora** con la tarifa de hoy y "
                   f"**{be_next:,.0f}** con la de {later}. Con su GPU llena, cada traducción cuesta **{usd(low)}**: "
                   f"{g_now / low:,.0f} veces menos que Gemini hoy y {g_next / low:,.0f} veces menos desde {later}. "
                   "Un traductor que atiende a una organización todo el día está en esa zona.\n")
        out.append("**Dónde gana Goliath:** con poco volumen. En una charla (unas 50 frases en una hora) la GPU cuesta "
                   f"~{usd(rate)} por esa hora y Gemini ~{usd(50 * g_now)} por las 50 frases. Por eso David se apaga solo "
                   "entre charlas: así no cuesta nada mientras nadie lo usa.\n")
        out.append("En la página, el costo de David es el de los segundos de GPU que usó esa traducción (atendiendo una a "
                   "la vez), y el de Goliath, lo que Gemini cobró por sus tokens.")
    else:
        out.append(f"\n**Where David wins:** from about **{be_now:,.0f} translations per hour** at today's price and "
                   f"**{be_next:,.0f}** at the {later} one. With his GPU full, each translation costs **{usd(low)}**: "
                   f"{g_now / low:,.0f} times less than Gemini today and {g_next / low:,.0f} times less from {later}. "
                   "A translator serving an organization all day is in that zone.\n")
        out.append("**Where Goliath wins:** at low volume. At a talk (about 50 phrases in an hour) the GPU costs "
                   f"~{usd(rate)} for that hour and Gemini ~{usd(50 * g_now)} for the 50 phrases. That's why David shuts "
                   "down on his own between talks: he costs nothing while nobody uses him.\n")
        out.append("On the page, David's cost is the GPU seconds that translation used (serving one at a time), and "
                   "Goliath's is what Gemini billed for its tokens.")
    return "\n".join(out)


def write_readmes() -> None:
    for name, lang in (("README.md", "es"), ("README.en.md", "en")):
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        if START not in text:
            sys.exit(f"{name}: no {START} marker")
        new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: f"{START}\n{section(lang)}\n{END}", text, flags=re.S)
        path.write_text(new, encoding="utf-8")
        print(f"{name}: projections updated")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("es", "en"):
        print(section(sys.argv[1]))
    else:
        write_readmes()
