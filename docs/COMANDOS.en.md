# Commands

Every `Makefile` command. `make help` lists them with their description. Back to the [README](../README.en.md). [Versión en español](COMANDOS.md).

| Command | What it does |
| --- | --- |
| `make help` | Lists the commands with their description. |
| `make up` | Starts Ollama (with `OLLAMA_MAX_LOADED_MODELS=4`), preloads the three stage models (David, the previous David, EmbeddingGemma), brings up the duel service and the presenter view (rebuilt if its code changed). Works with Wi-Fi off and without an audience. |
| `make reset` | Zeroes local rounds, votes, queue and scoreboard; with `AUDIENCE_FEED=1`, also deletes the event's rounds in Firestore (up to 3 attempts). If Firestore fails (e.g. offline), it says so with the cause and exits with an error; the local scoreboard is zeroed anyway. |
| `make stage-on` | Talk day: `min-instances=1` on the audience app (`infra/60-stage.sh on`), so the QR code doesn't wait for a cold start. Prints the value Cloud Run now shows. |
| `make stage-off` | After the talk: `min-instances=0` (scales to zero, nothing bills at rest). |
| `make warmup` | Wakes the audience app (200 on `/` and `/api/config`), loads both Davids and EmbeddingGemma in Ollama, and makes one David call and one Goliath call: through the duel service if it is running (`POST /warmup`, not recorded as a round), otherwise directly. |
| `make preflight` | Pre-stage check: Ollama with both Davids and EmbeddingGemma, the duel's `/health`, the presenter view's `/api/config`, term bank, lexicon, test set and David's run file, 10 GB free disk, audience app answering 200 with `min-instances` ≥ 1 and the same `EVENT_ID`, Gemini (one tiny call) and the event's Firestore. One `[ok]` or `[FALLA]` line per check, with the fix; the exit code is the number of failures. |
| `make test` | Python tests (`MOCK_AI=1`), Vitest, `tsc`, ESLint and, with JDK 21, the Firestore rules on the emulator. |
| `make eval` | Runs the test set through the base models, every David and Goliath (with and without glossary) and writes `evals/report.md`. Accepts `EVAL_ARGS="--limit 50 --no-goliath"`. |
| `make eval-dev` | Runs the dev set (data decisions, ablations) and writes `evals/report_dev.md`: `make eval-dev [EVAL_ARGS="--nbest 4"]`. |
| `make niches` | Computes the pre-registered niches ([evals/niche.md](../evals/niche.md)) from the latest test eval and writes `evals/niche_report.md`. |
| `make test-set` | Builds the test pairs from real web sentences and validates them against the term bank (`auto_validated` or `rejected`, no human involved). |
| `make real-pairs` | Training pairs anchored in real sentences (both directions), validated against the term bank. |
| `make ambiguous-terms` | Flags term-bank entries that are also ordinary words («cámara», «servir») so metrics ignore them. |
| `make counterparts` | Term → counterpart table validated by meaning (mutual nearest neighbours + a Gemini check of the top 5) in `data/counterparts.jsonl`. |
| `make pairs` | Generates the single-term synthetic training pairs with `GEMINI_MODEL` (paid; `SYNTHETIC_PAIRS_TARGET`, currently 1,500). The 2–3-term pairs (`scripts/generate_multi_pairs.py`, `data/pairs/synthetic_multi.jsonl`) are not part of the stage recipe and are not regenerated here. |
| `make datasheet` | Recounts `data/DATASHEET.md`. |
| `make data` | `test-set` + `real-pairs` + `pairs` + `datasheet`. |
| `make export` | Pulls the audience pairs approved in `/admin` from Firestore into `data/pairs/human.jsonl` and recounts the datasheet. |
| `make train-data` | Renders the training pairs into chat JSONL with the duel's exact prompt (and lexicon), following the on-stage David's recipe: no 2–3-term pairs and no ORPO stage. `MULTI=1` includes those pairs and `ORPO=1` also builds `data/train/pref.jsonl` (rejected variants, for ablations). |
| `make train` | Trains on a Cloud Run Job with one L4, then merges and converts to GGUF on a CPU job: `make train [TAG=…] [QUANT=Q5_K_M] [TRAIN_ARGS=…]`; `TAG` defaults to `genlingo-<year>-<month>` of the day. Runs `make train-data` first (accepts `MULTI=1` and `ORPO=1`; with `ORPO=1` the job adds the preference stage). Writes `train/runs/<tag>.json`. |
| `make train-finish` | Fallback: merges and exports to GGUF on the laptop an adapter trained in the cloud, and publishes it: `make train-finish` with the job's same `TAG`. |
| `make train-local` | The same training on the Mac (MPS), for experiments. |
| `make quant-sweep` | From a David's f16 GGUF: Q5_K_M, Q6_K, Q8_0 and imatrix-calibrated Q4/Q5 (calibrated on training pairs), registered in Ollama. |
| `make pull-model` | Downloads a David from the bucket and registers it in Ollama: `make pull-model TAG=genlingo-2026-10c-e2b-nomulti [FP16=1]`. |
| `make deploy` | Creates the web service account and deploys the audience app to Cloud Run (`min-instances=0`; `make stage-on` keeps it warm on talk days). |

## Quickstart

Requirements (versions in [ONBOARDING.md](ONBOARDING.md), Spanish): macOS on Apple Silicon, `uv`, Node 24, Ollama, `gcloud` with ADC.

```bash
cp .env.example .env                                  # models, prices and paths
(cd duel && uv sync)                                  # duel service (Python 3.12)
(cd web && npm install && cp .env.example .env.local) # presenter view and audience app
gcloud auth application-default login                 # Goliath (Vertex AI) and model downloads

ollama pull embeddinggemma                            # lexicon retrieval
make pull-model TAG=genlingo-2026-10c-e2b-nomulti     # on-stage David (Q5_K_M, 3.62 GB)
make pull-model TAG=genlingo-2026-10-e2b-q5_k_m      # previous David (M key)

make up       # Ollama + warmed-up David + duel (:8787) + presenter view (:3000/presenter)
```

Rehearsal with no network or GPU: set `MOCK_AI=1` in `.env` and run `make up` (simulated, deterministic models).

## Talk day

```bash
make up                                          # terminal 1: keeps running
make stage-on && make warmup && make preflight   # terminal 2: warm app, models loaded, everything [ok]
make reset                                       # scoreboard to zero
# … the talk …
make stage-off                                   # afterwards: the audience app scales to zero again
```

The on-stage demo script, screen by screen (keys, phrases, talking points, timings and what to do if something fails), is in [DEMO.md](DEMO.md) (Spanish).
