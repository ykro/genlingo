# Genlingo — generational translator: Gen Z ↔ parents

Demo for the talk *"David vs. Goliath: cómo un modelo pequeño le gana a un modelo frontier"* (David vs. Goliath: how a small model beats a frontier model). "no manches, la peli estuvo bien chilera pero el final me dio cringe" ↔ "la película estuvo bien chévere pero el final me dio pena ajena". **David** is Gemma 4 E2B fine-tuned with LoRA on our own pairs and runs on the stage laptop with Ollama, **without internet**. **Goliath** is Gemini (`GEMINI_MODEL`, currently `gemini-3.8-flash`) on Vertex AI. The audience joins with a QR code, sends phrases from their phones and votes on who translated better; an objective metric compares both against human references.

[Versión en español](README.md)

## What you'll learn

1. **Own data with `origin`:** every pair says where it came from (`web`, `synthetic` or `human`); without that you can neither evaluate nor retrain every month.
2. **Term bank and real sentences:** 532 terms from 76 sources, counterparts validated by meaning and 556 pairs anchored in real sentences; David's advantage is his data.
3. **LoRA on Cloud Run Jobs:** an L4 trains and a CPU job merges and exports GGUF; every run records its duration and cost.
4. **The compression trade-off:** f16 vs Q4_K_M, Q5_K_M, Q6_K, Q8_0 and imatrix, in size, latency and slang lost ([sweep and why Q5_K_M](docs/DECISIONES.en.md#quantization-why-q5_k_m)).
5. **Evals with term metrics:** chrF++ plus *correct slang*, *slang handled* and *reference-change recall*, with a separate dev set for decisions; David's losses are published.
6. **Monthly retrain and offline by design:** the `M` key brings in the previous David against the on-stage one; with no network, Goliath shows as "sin conexión" (offline) and David keeps going.

![What runs on the laptop and what runs in the cloud](docs/diagrams/arquitectura.png)

![What the demo tests](docs/diagrams/que-se-prueba.png)

Diagram labels are in Spanish.

## Result

Eval of 2026-10-04 on 399 `auto_validated` web test phrases ([full table and caveats](docs/DECISIONES.en.md#results)):

| Variant | Correct slang | Slang handled | chrF++ | p50 | Cost / 1,000 phrases |
| --- | --- | --- | --- | --- | --- |
| **On-stage David** (`genlingo-2026-10c-e2b-nomulti`, Q5_K_M, 3.62 GB) | **42%** | **82%** | **59.7** | 670 ms | **$0** |
| Round-2 David (`genlingo-2026-10b-e2b`) | 34% | 82% | 56.6 | 557 ms | $0 |
| Previous David, `M` key (`genlingo-2026-10-e2b-q5_k_m`) | 27% | 74% | 55.4 | 564 ms | $0 |
| Goliath `gemini-3.8-flash` | 26% | 77% | 53.5 | 2.60 s | $1.13 |
| Goliath + the same glossary | 38% | 82% | 57.0 | 3.05 s | $1.27 |
| Copy the phrase (baseline) | 1% | 1% | 53.2 | — | — |

*Correct slang*: the slang produced means what the original said. David beats Goliath by 16 points (95% CI [+10.8, +21.8]) and by 30 on Guatemalan slang. With the same glossary Goliath ties on the whole set, but David still wins in Guatemala and in parents → Gen Z: David's advantage is his data. Retraining costs $0.97 end to end in the cloud ([cost per run](docs/DECISIONES.en.md#training-cost-per-run)).

## What didn't work

One line per dead end; the details are in [docs/BITACORA.md](docs/BITACORA.md) (Spanish).

- **Free paraphrases:** David ended up below copying the phrase.
- **A bigger model (E4B):** the same slang handled as E2B, and slower.
- **Q4_K_M:** lost 7 points of slang against f16.
- **Training, merging and converting in a single job:** died of memory; now it is two jobs.
- **Counterparts by *embedding*:** most of the links meant something else.
- **Pairs with 2–3 terms at once and ORPO preferences:** neither improved the dev set; both left out.

## Quickstart

```bash
cp .env.example .env && (cd duel && uv sync) && (cd web && npm install && cp .env.example .env.local)
gcloud auth application-default login                 # Goliath (Vertex AI) and model downloads
ollama pull embeddinggemma && make pull-model TAG=genlingo-2026-10c-e2b-nomulti   # lexicon + on-stage David
make up       # Ollama + warmed-up David + duel (:8787) + presenter view (:3000/presenter)
make test     # tests with no network (MOCK_AI=1)
```

Rehearsal with no network or GPU: `MOCK_AI=1` in `.env` and `make up`. Requirements, the previous David and the full version in [docs/COMANDOS.en.md](docs/COMANDOS.en.md#quickstart).

## Deployed app

- Audience: **https://genlingo-611681112050.us-central1.run.app** (event `ensayo`, country `GT`); moderation at `/admin` (account with `admin=true`).
- Presenter view: local, `http://127.0.0.1:3000/presenter` with `make up`.

## Documentation

- [docs/DEMO.md](docs/DEMO.md) (Spanish): the demo script, screen by screen (keys, phrases, talking points, timings and what to do if something fails).
- [docs/ONBOARDING.md](docs/ONBOARDING.md) (Spanish): setup, cloud, data and training chain, code walkthrough, common problems and talk-day checklist.
- [docs/BITACORA.md](docs/BITACORA.md) (Spanish): David's story iteration by iteration, with the dead ends and the niches.
- [docs/DECISIONES.en.md](docs/DECISIONES.en.md): what the demo teaches in detail, every technical decision, full results and training cost.
- [docs/COMANDOS.en.md](docs/COMANDOS.en.md): every `make` command and the full quickstart.
- [docs/ESTRUCTURA.en.md](docs/ESTRUCTURA.en.md): architecture, monthly cycle, screens, repo map and versions.
- [docs/CREDITOS.en.md](docs/CREDITOS.en.md): data provenance and licenses.
- [evals/report.md](evals/report.md) and [evals/niche.md](evals/niche.md): the eval report and the niches defined before looking at results.
- [docs/diagrams/](docs/diagrams/): architecture, what the demo tests, monthly cycle, results and log (HTML, SVG and PNG).
- [data/SOURCES.md](data/SOURCES.md) and [data/DATASHEET.md](data/DATASHEET.md): data sources and datasheet.
