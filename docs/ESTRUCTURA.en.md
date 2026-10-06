# Repository structure

What runs where, what it looks like and where each thing lives in the code. Back to the [README](../README.en.md). [Versión en español](ESTRUCTURA.md).

## Architecture

![What runs on the laptop and what runs in the cloud](diagrams/arquitectura.png)

Editable source: [diagrams/arquitectura.html](diagrams/arquitectura.html) (also as `.svg`). Diagram labels are in Spanish. Why each piece runs on the laptop or in the cloud: [DECISIONES.en.md](DECISIONES.en.md#what-runs-on-the-laptop-and-why).

The monthly cycle, from data to stage and back:

![Monthly cycle](diagrams/ciclo-mensual.png)

## Screens

![The comparison page: David and Goliath translate the same phrase from Gen Z to parents](demo/10-comparar-genz-a-papas.png)

![No internet: Goliath says «Sin conexión» and David keeps translating](demo/12-sin-internet.png)

The talk demo is that page (`/traducir`); the script is in [DEMO.en.md](DEMO.en.md). The repo also has a presenter view (`/presenter`) and an audience app with votes, from an earlier version of the demo; they still work, but the talk doesn't use them.

## Repo map

```
duel/                 Duel service (FastAPI) — runs on the laptop
  duel_core/          Reusable core: parallel duel, Ollama/Gemini/mock clients,
                      connectivity, cost with dated prices, chrF++, percentiles
  genlingo_duel/      The app: prompts, glossary, term bank, arena, API (main.py), the comparison
                      page (translate_page.py, term_check.py, static/traducir.html), scoreboard
                      (SQLite) and Firestore bridge (audience_feed.py) of the earlier view
  tests/              Service tests (MOCK_AI=1)
web/                  Next.js: audience app (/), moderation (/admin), presenter view (/presenter)
  app/api/            Audience routes (phrases, pairs, votes, config) and admin routes
  lib/server/         Auth + App Check, 20 s limit, blocklist, validation, Firestore
  e2e/                Playwright rehearsals, script screenshots (demo-shots.mjs) and Android emulator
  firestore.rules     No client writes directly; everything goes through the API
data/                 terms.jsonl, raw/web_usage.jsonl, pairs/, review/, SOURCES.md, DATASHEET.md,
                      translate_examples.json (the /traducir examples, verified live)
scripts/              Data building, review, export, reset, make up, warmup, preflight
train/                train_lora.py, finish.py, submit_job.py, finish_local.py, train_local.py, notebook, runs/
evals/                run_eval.py, term_accuracy.py, report.py, report.md, experiments/
infra/                Numbered gcloud scripts (01–06, 60 stage on/off) and shared env.sh
docs/                 DEMO, ONBOARDING, BITACORA, DECISIONES, COMANDOS, ESTRUCTURA, CREDITOS,
                      diagrams/ (HTML + SVG + PNG), demo/ (demo-script screenshots)
```

## Versions

| Piece | Version |
| --- | --- |
| David's base model | Gemma 4 E2B (`gemma-4-E2B-it`, Hugging Face weights `hf://google`); compared with E4B |
| Goliath | `gemini-3.8-flash` (`GEMINI_THINKING_LEVEL=low`) on Vertex AI |
| Local embeddings | EmbeddingGemma (`embeddinggemma` in Ollama) |
| Ollama | 0.35.0 |
| Training | torch 2.14.0 (CUDA 12.6), transformers 5.17.0, peft 0.21.1, trl 1.14.1, accelerate 1.15.0, datasets 5.0.1, llama.cpp `b11292` |
| Duel service | Python 3.12, fastapi 0.142.2, uvicorn 0.54.0, google-genai 2.25.0, sacrebleu 2.6.0, google-cloud-firestore 2.33.0 |
| Web | Next.js 16.3.8, React 19.2.8, firebase 12.19.0, firebase-admin 14.5.0, Node 24 |

Models come from environment variables (`GEMINI_MODEL`, `GEMMA_BASE_MODEL`, `LOCAL_MODEL_TAG`, `DAVID_PREVIOUS_TAG`, `DAVID_TAGS`, `BASE_MODEL_TAGS`, `EMBEDDING_MODEL`), documented in `.env.example`. The project uses no preview APIs (ADK, MCP, A2A).
