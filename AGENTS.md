# Genlingo — generational translator

Talk: **David vs. Goliath: cómo un modelo pequeño le gana a un modelo frontier.**

A small Gemma model (David), fine-tuned on Gen Z ↔ parent phrase pairs, translates between Gen Z speech and their parents' speech ("no manches, está bien mid, me dio cringe" ↔ "estuvo regular y me dio pena ajena"). It runs on the presenter's laptop with no internet and competes live against Gemini (Goliath). The audience submits phrases from their phones and votes; an objective score (chrF++) measures both models against reference translations.

## What the talk teaches (make each one visible in code and reports)

| Principle | Where |
| --- | --- |
| Own, quality data | `origin` per pair, `data/DATASHEET.md`, manual approval, non-synthetic test set |
| Efficient fine-tuning in the cloud | `train/` (commented LoRA), Vertex AI Custom Job, cost and duration in `evals/report.md` |
| Compress to run on a laptop | report compares fp16 vs Q4 size and latency |
| Honest evals | chrF++, results per `origin`, David's losses shown |
| Big models age | model tags by data date (`genlingo-2027-03`), `david_tag` duel last month vs this month |

## Components

| Component | Stack | Runs on | Why |
| --- | --- | --- | --- |
| Audience web app (`web/`) | Next.js, Firebase Auth (anonymous), Firestore db `genlingo`, App Check | Cloud Run | Phones must reach it |
| Admin (`web/` route `/admin`) | Same app, email auth for the presenter | Cloud Run | Approve contributed pairs and live phrases |
| Training (`train/`) | TRL + PEFT LoRA, merge, llama.cpp GGUF Q4 + Modelfile | Vertex AI Custom Job (L4, europe-west4); notebook for Colab | CUDA stack, real billed cost, reproducible |
| David | Ollama with custom Modelfile | Laptop | The thesis: runs offline on your laptop |
| Duel service (`duel/`) | Python, FastAPI, Ollama client, `google-genai`, `sacrebleu` | Laptop | Must work with Wi-Fi off; latency measured on stage hardware |
| Presenter view (`presenter/` or `web/` route served locally) | Next.js calling the duel service | Laptop | Offline mode |

## Data

- JSONL, one pair per line: `id`, `direction` (`genz_to_parent` | `parent_to_genz`), `source`, `target`, `country`, `age_range`, `split` (`train` | `test`), `status`, `origin` (`web` | `synthetic` | `human`), `provenance` (URL + license for web; model + prompt id + seed for synthetic; event for human).
- Build path:
  1. Web research of real Gen Z slang and parent speech (MX, GT, CO and neutral LatAm): glossaries, slang dictionaries, articles with usage examples. Respect licenses; record every source in `data/SOURCES.md`.
  2. Build a **term bank** (`data/terms.jsonl`): term, meaning, country, example, source URL.
  3. Generate synthetic pairs with `GEMINI_MODEL` **anchored on the term bank** (the prompt receives term, meaning, source example and country). Record model, prompt version and seed. Target ~1,000 training pairs balanced by direction.
  4. Test set: ~300 pairs, `origin=web` only (real usage examples with their meaning rewritten as reference), never synthetic — synthetic references written by Gemini would bias chrF++ toward Goliath. Mark `status=pending_review`; the presenter reviews them (`make review-test` exports a CSV).
- The audience app adds `origin=human` pairs at every event; approved in `/admin`; `make export` pulls approved pairs from Firestore into `data/`.
- The prompt receives `country` so each event can use its local variant.

## Training

- `train/train_lora.py` runs end to end: load approved pairs, LoRA fine-tune `GEMMA_BASE_MODEL` (r=16, alpha=32, lr 2e-4, 3 epochs), merge, quantize to Q4_K_M GGUF with llama.cpp, write Modelfile, upload to `gs://ai-experiments-487722-genlingo-models/<tag>/`.
- `train/genlingo.ipynb` wraps the same script for Colab / Colab Enterprise.
- `make train` submits a Vertex AI Custom Job (container built with Cloud Build) on an L4 in `europe-west4`, staging bucket `gs://ai-experiments-487722-train-eu`. Writes `train/runs/<tag>.json` with duration, machine, and estimated cost.
- `make pull-model TAG=…` downloads the GGUF and runs `ollama create`.
- Each model is tagged with its data date (`genlingo-2027-03`) so the talk can show a monthly retrain and its cost.
- Base candidates: Gemma 4 E2B and E4B. `make eval` picks the smallest one meeting p50 < 1 s and best chrF++.

## Duel service

- `POST /duel` with `phrase`, `direction`, `country`, optional `david_tag`: calls David and Goliath (`GEMINI_MODEL`) in parallel with the same prompt; returns translation, latency ms, tokens and cost for each.
- Cost from per-million-token prices in config. David's inference cost is zero; the presenter view shows his training cost amortized.
- Round types: **evaluation rounds** use test-set phrases and show chrF++ live; **audience rounds** use submitted phrases, no reference, decided by vote.
- Offline: with no internet, Goliath shows as offline and David keeps working.
- `david_tag` lets two versions of David compete.

## Audience flow

- Join by QR code, no sign-up (anonymous auth). Submit a phrase (one every 20 s per person, enforced server side) and vote each round.
- Submitted phrases wait in a queue the presenter approves from the laptop before they reach the screen; blocklist as a first filter.

## Presenter view

- Phrase and direction; David and Goliath side by side with translation, latency and cost.
- Persistent scoreboard: rounds won, average chrF++, p50 latency, cumulative cost per model, live vote results.
- Indicators for offline mode and David's model tag.

## Acceptance criteria

- `make up` starts Ollama, the duel service and the presenter view; the duel works with Wi-Fi off.
- David's p50 latency < 1 s for phrases up to 30 words on the M1 Max 64 GB laptop.
- `make eval` runs the test pairs against both models and writes `evals/report.md` (chrF++, per-origin, latency p50/p95, cost, fp16 vs Q4).
- An approved audience phrase reaches the screen in < 3 s.
- `make reset` clears rounds, votes and scoreboard.
- `make test` passes.

## Shared rules (all four demo repos)

These demos are teaching material for a talk. The code, folder names, reports and docs must make the talk's ideas visible. Prefer small files named after the concept they teach, and comments that explain *why*, not *what*.

### Stack

| Layer | Choice |
| --- | --- |
| Web | Next.js (App Router, TypeScript), React |
| Android | Kotlin, Jetpack Compose, Material 3 |
| Cloud models | Gemini via Vertex AI with the Google Gen AI SDK (`@google/genai` / `google-genai`), ADC, `GOOGLE_CLOUD_LOCATION=global` |
| Images | Nano Banana 2 Lite (`IMAGE_MODEL`) via Vertex AI |
| Local models | Gemma served with Ollama; EmbeddingGemma where retrieval is needed |
| Fine-tuning | LoRA with Hugging Face TRL + PEFT as a Vertex AI Custom Job (L4, `europe-west4`); same script wrapped in a Colab notebook; exported to quantized GGUF for Ollama |
| Agents | Agent Development Kit (ADK, Python); MCP for tools; A2A for agent-to-agent |
| Cloud | Google Cloud project `ai-experiments-487722`. Every web app or API runs on **Cloud Run** (`us-central1`, Dockerfile + Cloud Build + Artifact Registry repo `charlas2027`). Firebase services (Auth, Firestore named database per app, FCM, Storage, App Check) are used as SDKs, never Firebase Hosting |
| Local data | JSON/JSONL files or SQLite in the repo |

### Cloud first

Everything runs in the cloud unless the talk requires the laptop (offline model, latency measured on the stage hardware). Every component that runs on the laptop is listed in the README's "Decisiones técnicas" section with the reason.

### Rules

- No model name or version is hard-coded. Models come from env vars (`GEMINI_MODEL`, `GEMINI_LIVE_MODEL`, `IMAGE_MODEL`, `GEMMA_BASE_MODEL`, `LOCAL_MODEL_TAG`, `EMBEDDING_MODEL`) documented in `.env.example`.
- Preview APIs (AppFunctions with Gemini, WebMCP, UCP, AP2, A2A, MCP SDK, ADK): check the current official docs before implementing (context7 or the web) and record the version used in the README.
- `Makefile` targets: `make up` (start everything needed locally), `make reset` (back to the initial state in under 10 seconds), `make test`, `make deploy`, and where it applies `make eval`, `make train`.
- Data: every record carries `origin` (`web` with URL + license, `synthetic` with model + prompt + seed, `human`). Documented in `data/SOURCES.md` and `data/DATASHEET.md`. Fictional seed data is generated by scripts. No secrets in the repo.
- Python uses `uv`. Node uses npm. Code in English; UI in Spanish (Guatemala/LatAm neutral).
- Tests must pass before a task is done (`make test`). Anything that needs the cloud also has a mock mode (`MOCK_AI=1`) so tests and rehearsals run without network.
- No `CLAUDE.md` in the repo.

### UI/UX bar

- Light theme only. No dark mode. Not overloaded: each screen shows what matters and nothing else.
- Production-grade: own brand identity (name, logo mark, palette, typography), consistent components, designed empty/loading/error states, no placeholder text.
- Web: responsive, keyboard accessible, WCAG 2.2 AA contrast, purposeful motion only. Android: Material 3 and platform conventions.
- Every app on stage has a presenter view: a separate route readable from the back of an auditorium (large type, high contrast, 16:9 at 1920×1080), no logins or manual steps during the talk.
- Visual assets (logos, product photos, sample photos) are generated with `IMAGE_MODEL` by a script in `scripts/` and committed; the prompt is kept next to the asset.

### Docs (written at the end, from the finished code)

- `README.md` (Spanish) and `README.en.md`: what you'll learn, architecture diagram, quickstart, `make` commands, repo map, **technical decisions** (what, why, discarded alternatives, where each component runs and why), preview API versions.
- `docs/ONBOARDING.md`: prerequisites with versions, local setup, credentials/ADC, GCP setup with `infra/NN-*.sh`, run/test/rehearse, code walkthrough, troubleshooting, talk-day checklist.
- `docs/diagrams/`: made with the `diagram-design` skill, exported to SVG and PNG.
- Never describe the project as a deviation from a spec; the docs describe what the project is.
