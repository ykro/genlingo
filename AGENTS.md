# Genlingo — generational translator

Talk: **David vs. Goliath: cómo un modelo pequeño le gana a un modelo frontier.**

A small Gemma model (David), fine-tuned on Gen Z ↔ parent phrase pairs, translates between Gen Z speech and their parents' speech ("no manches, está bien mid, me dio cringe" ↔ "estuvo regular y me dio pena ajena"). It runs on the presenter's laptop with no internet. The demo is one comparison page (`/traducir`, served by the duel service): David and Goliath (Gemini) translate the same phrase side by side, each column with its translation, time and cost; verified example buttons also show the human reference and a ✓/✗ per slang term. No rounds, scoreboard or votes in the talk.

## What the talk teaches (make each one visible in code and reports)

| Principle | Where |
| --- | --- |
| Own, quality data | `origin` per pair, `data/DATASHEET.md`, term bank, real sentences, automatic validation against the bank, non-synthetic test set |
| Efficient fine-tuning in the cloud | `train/` (commented LoRA), two Cloud Run Jobs (L4 trains, CPU merges + GGUF), cost and duration per stage in `train/runs/<tag>.json` and `evals/report.md` |
| Compress to run on a laptop | quantization sweep (Q4_K_M, Q5_K_M, Q6_K, Q8_0, imatrix) vs f16: size, latency and slang lost |
| Term-level evals | chrF++ plus a copy-the-phrase baseline, correct slang (meaning-validated), slang handled and reference-change recall, a separate dev set for data decisions, Goliath with and without David's glossary, David's losses shown |
| Retraining on new data | model tags by data date (on stage: `genlingo-2026-10c-e2b-nomulti`); the README's experiments section shows every round's numbers |
| Show only what David wins | comparison page examples from the niche David wins (Guatemalan slang), each verified live 3× with both models (`data/translate_examples.json`); losses stay documented in the README, BITACORA and evals, never on the page |

## Components

| Component | Stack | Runs on | Why |
| --- | --- | --- | --- |
| Comparison page (`duel/genlingo_duel/static/traducir.html`, route `/traducir`) | Plain HTML/JS served by the duel service, brand fonts served locally | Laptop | The talk demo; works offline |
| Audience web app (`web/`, earlier version of the demo, not used in the talk) | Next.js, Firebase Auth (anonymous), Firestore db `genlingo`, App Check (reCAPTCHA Enterprise) | Cloud Run | Phones must reach it |
| Admin (`web/` route `/admin`) | Same app, email auth for the presenter | Cloud Run | Optional: moderate phrases when auto-approve is off, approve contributed pairs |
| Training (`train/`) | TRL + PEFT LoRA (`train_lora.py`), merge + llama.cpp GGUF `QUANT` (Q5_K_M) + f16 + Modelfile (`finish.py`) | Cloud Run Jobs in europe-west4: `genlingo-train` (1× L4) then `genlingo-finish` (CPU); notebook for Colab; `make train-finish` on the laptop as fallback | Serverless GPU billed per second; the split keeps each job within 32 GiB |
| David | Ollama with custom Modelfile, EmbeddingGemma lexicon (term bank + meaning-validated counterparts) | Laptop | The thesis: runs offline on your laptop |
| Duel service (`duel/`) | Python, FastAPI, Ollama client, `google-genai`, `sacrebleu`, SQLite scoreboard | Laptop | Must work with Wi-Fi off; latency measured on stage hardware |
| Presenter view (`web/` route `/presenter`, earlier version of the demo, not used in the talk) | Next.js calling the duel service | Laptop | Offline mode |

## Data

- JSONL, one pair per line: `id`, `direction` (`genz_to_parent` | `parent_to_genz`), `source`, `target`, `country`, `age_range`, `split` (`train` | `test`), `status` (`pending_review` | `auto_validated` | `approved` | `rejected`), `origin` (`web` | `synthetic` | `human`), `provenance` (URL + license for web; model + prompt version + seed for synthetic; event for human).
- Build path, with **no human in the loop**:
  1. Web research of real Gen Z slang and parent speech (MX, GT, CO and neutral LatAm): glossaries, slang dictionaries, articles with usage examples. Respect licenses; record every source in `data/SOURCES.md`.
  2. **Term bank** (`data/terms.jsonl`): term, meaning, country, generation, example, source; terms that are also ordinary words are flagged `ambiguous` from general-speech counts.
  3. **Real sentences** (`data/raw/web_usage*.jsonl`): round 1 goes to test; round 2 is split by a stable hash of the id, half test, half training pairs anchored in the real sentence (`make real-pairs`).
  4. **Synthetic pairs** from `GEMINI_MODEL` anchored on the term bank (`make pairs`), validated against the bank; model, prompt version and seed recorded.
  5. **Test set**: `origin=web` only, never synthetic (a Gemini reference would bias chrF++ toward Goliath). `make test-set` validates every pair against the term bank and marks it `auto_validated` or `rejected` with the reason, including any overlap with training (also as a substring).
- The audience app can add `origin=human` pairs at an event (approved in `/admin`; `make export`).
- The prompt receives `country` and a glossary from the term bank, so each event can use its local variant.

## Training

- `train/train_lora.py` fine-tunes `GEMMA_BASE_MODEL` with LoRA (r=32, alpha=16, rsLoRA, lr 2e-4, 3 epochs) on the chat JSONL rendered with the duel's prompt (`make train-data`, style `lexicon`: country + lexicon).
- `train/finish.py` merges the adapter, writes the f16 and `QUANT` (Q5_K_M) GGUFs and the Modelfile, and uploads to `gs://ai-experiments-487722-genlingo-models/<tag>/`.
- `make train` runs both as Cloud Run Jobs from one image (`infra/03-train-job.sh`) and writes `train/runs/<tag>.json` with duration and estimated cost per stage. `TRAIN_RUNTIME=vertex` runs everything as one Vertex AI Custom Job; `train/genlingo.ipynb` wraps it for Colab; `make train-finish` redoes the merge on the laptop.
- `make pull-model TAG=genlingo-2026-10c-e2b-nomulti` downloads the GGUF and runs `ollama create`.
- Tags carry the data date (`genlingo-YYYY-MM`, plus a letter for a second data version in the same month, e.g. `genlingo-2026-10c-e2b-nomulti`, the third data version of October without the multi-term pairs).
- `make eval` picks the on-stage David: the smallest export within 2 points of its f16 on slang handled, with p50 < 1 s.

## Duel service

- Comparison page: `GET /traducir`; `POST /translate/david` and `POST /translate/goliath` (one side each, so each column fills as it answers; nothing recorded); `GET /translate/examples`. With an example's `example_id`, the answer carries a per-term check (`term_check.py`, the eval's correct-slang rules).

- `POST /duel` with `phrase`, `direction`, `country`, optional `david_tag`: calls David and Goliath (`GEMINI_MODEL`) in parallel, each with the prompt it was trained or configured for; returns translation, latency ms, tokens and cost for each.
- Cost from a dated price schedule (`GEMINI_PRICE_SCHEDULE`). David's inference cost is zero; the presenter view shows his training cost amortized over the rounds he played.
- Round types: **evaluation rounds** use auto-validated test-set phrases and show chrF++ live; **audience rounds** use submitted phrases, no reference, decided by vote when the audience is connected.
- Offline: with no internet, Goliath shows as offline, Firestore is skipped and David keeps working.
- `david_tag` lets two versions of David compete; the scoreboard is per David.

## Audience flow (earlier version of the demo, not used in the talk)

- Join by QR code, no sign-up (anonymous auth). Submit a phrase (one every 20 s per person, enforced server side) and vote each round.
- Phrases that pass the blocklist go straight to the screen queue (`AUTO_APPROVE_PHRASES=1`, the default); with `0` the presenter approves them in `/admin`. The talk also works with no audience at all.

## Presenter view (earlier version of the demo, not used in the talk)

- Phrase and direction; David and Goliath side by side with translation, latency and cost.
- Persistent scoreboard per David: rounds won, average chrF++, p50 latency, cumulative cost, live vote results.
- Indicators for offline mode and David's model tag, quantization and size.

## Acceptance criteria

- `make up` starts Ollama, the duel service (with the comparison page) and the presenter view, and opens the comparison page; David works with Wi-Fi off.
- `make preflight` translates every comparison-page example live with both models: David gets the slang right and Goliath doesn't.
- David's p50 latency < 1 s for phrases up to 30 words on the M1 Max 64 GB laptop.
- `make eval` runs the test pairs against both models and writes `evals/report.md` (chrF++, term metrics, per-origin, latency p50/p95, cost, compression).
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
| Fine-tuning | LoRA with Hugging Face TRL + PEFT on serverless GPUs (Genlingo: Cloud Run Jobs, L4, `europe-west4`; Vertex AI Custom Job as alternative); same script wrapped in a Colab notebook; exported to quantized GGUF for Ollama |
| Agents | Agent Development Kit (ADK, Python); MCP for tools; A2A for agent-to-agent |
| Cloud | Google Cloud project `ai-experiments-487722`. Every web app or API runs on **Cloud Run** (`us-central1`, Dockerfile + Cloud Build + Artifact Registry repo `charlas2027`). Firebase services (Auth, Firestore named database per app, FCM, Storage, App Check) are used as SDKs, never Firebase Hosting |
| Local data | JSON/JSONL files or SQLite in the repo |

### Cloud first

Everything runs in the cloud unless the talk requires the laptop (offline model, latency measured on the stage hardware). Every component that runs on the laptop is listed in `docs/DECISIONES.md` with the reason.

### Rules

- No model name or version is hard-coded. Models come from env vars (`GEMINI_MODEL`, `GEMINI_LIVE_MODEL`, `IMAGE_MODEL`, `GEMMA_BASE_MODEL`, `LOCAL_MODEL_TAG`, `EMBEDDING_MODEL`) documented in `.env.example`.
- Preview APIs (AppFunctions with Gemini, WebMCP, UCP, AP2, A2A, MCP SDK, ADK): check the current official docs before implementing (context7 or the web) and record the version used in `docs/DECISIONES.md`.
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

- `README.md` (Spanish) and `README.en.md`: what it is, what you'll learn, the result, diagrams, quickstart and links. Genlingo's README also carries every experiment with its statistics and why the demo uses only the final model. Everything else lives in `docs/` (es + en): `DECISIONES` (**technical decisions**: what, why, discarded alternatives, where each component runs and why; preview API versions), `COMANDOS` (`make` commands), `ESTRUCTURA` (repo map), `CREDITOS` (data and licenses).
- `docs/ONBOARDING.md`: prerequisites with versions, local setup, credentials/ADC, GCP setup with `infra/NN-*.sh`, run/test/rehearse, code walkthrough, troubleshooting, talk-day checklist.
- `docs/diagrams/`: made with the `diagram-design` skill, exported to SVG and PNG.
- Never describe the project as a deviation from a spec; the docs describe what the project is.
