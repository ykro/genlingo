# Repository structure

What runs where, what it looks like and where everything is in the code. Back to the [README](../README.en.md). [Versión en español](ESTRUCTURA.md).

## Architecture

![Everything runs in the cloud: the page, David and Goliath](diagrams/arquitectura.png)

Editable source: [diagrams/arquitectura.html](diagrams/arquitectura.html) (also as `.svg`). Diagram labels are in Spanish. Why each piece runs where it runs: [DECISIONES.en.md](DECISIONES.en.md#david-in-the-cloud).

- **The page** is a public Cloud Run service in `us-central1`. The browser only talks to it; it calls both models and returns each answer as soon as it arrives.
- **David** is a private Cloud Run service in `europe-west4` with an NVIDIA L4 GPU: Ollama with the `DAVID_MODEL_TAG` David and EmbeddingGemma inside the image. Only the page's service account may call it (identity token). It scales to zero when nobody uses it; the page wakes it when it opens.
- **Goliath** is Gemini on Vertex AI, called from the page.
- **Training and evaluating** are Cloud Run Jobs with an L4 in `europe-west4`. Training publishes the GGUF to the models bucket; David's image and the eval's models come from there.

The monthly cycle, from the data to the page and back:

![Monthly cycle](diagrams/ciclo-mensual.png)

## Screens

![The comparison page: David and Goliath translate the same phrase from Gen Z to parents](demo/02-comparar-genz-a-papas.png)

![Parents → Gen Z: David says «refa», Goliath «munchies»](demo/03-comparar-papas-a-genz.png)

The talk's demo is that page; the script is in [DEMO.en.md](DEMO.en.md).

## Repository map

```
duel/                 The comparison page (FastAPI) — runs on Cloud Run
  duel_core/          Reusable core: both calls in parallel, Ollama/Gemini/mock clients,
                      cost with dated prices, chrF++, percentiles
  genlingo_duel/      The app: prompts, lexicon glossary, term bank, arena (David and Goliath),
                      API (main.py), per-term check (term_check.py), examples (translate_page.py),
                      identity token for David (cloud_auth.py) and the page (static/index.html)
  tests/              Tests (MOCK_AI=1)
  Dockerfile          The page's image
david/                David's image: Ollama with the model, EmbeddingGemma and the compiled CUDA kernels (Dockerfile, start.sh,
                      fill-jit-cache.sh, cloudbuild.yaml)
data/                 terms.jsonl, raw/, pairs/, eval/, counterparts.jsonl, SOURCES.md, DATASHEET.md,
                      translate_examples.json (the page's examples, verified live)
scripts/              Data building, check_page.py (make check), check_candidates.py (make check-candidates), screenshots.py (make screenshots), bench_capacity.py (make capacity)
train/                train_lora.py, finish.py, preference.py, submit_job.py, notebook, runs/
evals/                run_eval.py, term_accuracy.py, report.py, report.md, experiments/,
                      Dockerfile + cloud_eval.sh (the eval job)
infra/                Numbered gcloud scripts: 01–03 training, 04 David, 05 the page, 06 the eval,
                      07 David's CUDA kernels
docs/                 DEMO, ONBOARDING, BITACORA, DECISIONES, COMANDOS, ESTRUCTURA, CREDITOS,
                      diagrams/ (HTML + SVG + PNG), demo/ (screenshots of the page), data/capacity.json (make capacity)
```

## Versions

| Piece | Version |
| --- | --- |
| David's base model | Gemma 4 E2B (`gemma-4-E2B-it`, Hugging Face weights `hf://google`); compared with E4B |
| Goliath | `gemini-3.8-flash` (`GEMINI_THINKING_LEVEL=low`) on Vertex AI |
| Lexicon embeddings | EmbeddingGemma (`embeddinggemma` in Ollama) |
| Ollama | 0.35.0 (`ollama/ollama` image), on Cloud Run with 1 NVIDIA L4, 4 vCPU and 16 GiB |
| Training | torch 2.14.0 (CUDA 12.6), transformers 5.17.0, peft 0.21.1, trl 1.14.1, accelerate 1.15.0, datasets 5.0.1, llama.cpp `b11292` |
| The page | Python 3.12, fastapi 0.142.2, uvicorn 0.54.0, google-genai 2.25.0, google-auth 2.59.0, httpx 0.28.1, sacrebleu 2.6.0 |

Models come from environment variables (`GEMINI_MODEL`, `GEMMA_BASE_MODEL`, `DAVID_MODEL_TAG`, `DAVID_TAGS`, `BASE_MODEL_TAGS`, `EMBEDDING_MODEL`), documented in `.env.example`. The project uses no preview APIs (ADK, MCP, A2A).
