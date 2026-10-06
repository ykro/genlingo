# Commands

Every `Makefile` command. `make help` lists them with their description. Back to the [README](../README.en.md). [Versión en español](COMANDOS.md).

Using the demo needs none of them: the page is at **https://genlingo-611681112050.us-central1.run.app** ([DEMO.en.md](DEMO.en.md)). These commands rebuild it, train David and evaluate him. Everything runs on Google Cloud; the laptop only submits the work.

| Command | What it does |
| --- | --- |
| `make help` | Lists the commands with their description. |
| `make deploy` | Deploys David (`infra/04-david.sh`: an Ollama image with the `DAVID_MODEL_TAG` David and EmbeddingGemma inside, a private Cloud Run service with an L4 GPU in `europe-west4`, `min-instances=0`, `max-instances=1`) and the page (`infra/05-page.sh`: a public service in `us-central1` whose service account may only call Gemini and David). David's image is only rebuilt when its recipe or the model changed. |
| `make check` | Checks the live page the way the browser uses it: opens it, wakes David (says how long it took) and translates every example with both. Fails if David misses any slang term of an example or if Goliath gets them all. |
| `make screenshots` | Screenshots of the live page in a real browser (1920×1080 and 1280×800, light theme) in `docs/demo/`. |
| `make test` | Python tests without network (`MOCK_AI=1`): the page, the per-term check, the data, the eval and the report. |
| `make eval` | Runs the test set through the base models, every David and Goliath (with and without the glossary) in a Cloud Run Job with an L4 GPU (`infra/06-eval-job.sh`): the job runs Ollama inside, loads each model from the models bucket one at a time and leaves the report in the bucket; the command copies it to `evals/report.md` and `evals/results/`. Accepts `EVAL_ARGS="--limit 50 --no-goliath"`. |
| `make eval-dev` | The same on the dev set (data decisions, ablations): `evals/report_dev.md`. `make eval-dev [EVAL_ARGS="--nbest 4"]`. |
| `make niches` | Computes the pre-registered niches ([evals/niche.md](../evals/niche.md)) from the latest test eval and writes `evals/niche_report.md`. |
| `make test-set` | Builds test pairs from real web sentences and validates them against the term bank (`auto_validated` or `rejected`, no human in the loop). |
| `make real-pairs` | Training pairs anchored in real sentences (both directions), validated against the bank. |
| `make ambiguous-terms` | Flags bank terms that are also ordinary words («cámara», «servir») so the metrics don't count them. |
| `make counterparts` | Term → counterpart table validated by meaning (mutual nearest neighbours + a Gemini top-5 check) in `data/counterparts.jsonl`. |
| `make pairs` | Generates the one-term synthetic pairs with `GEMINI_MODEL` (paid; `SYNTHETIC_PAIRS_TARGET`, today 1,500). The 2–3-term pairs (`scripts/generate_multi_pairs.py`, `data/pairs/synthetic_multi.jsonl`) aren't in David's recipe and aren't regenerated here. |
| `make datasheet` | Recounts `data/DATASHEET.md`. |
| `make data` | `test-set` + `real-pairs` + `pairs` + `datasheet`. |
| `make train-data` | Renders the training pairs into chat JSONL with the same prompt (and lexicon) the page uses, with David's recipe: no 2–3-term pairs, no ORPO stage. The lexicon uses the embedding model on David's service (`DAVID_URL`). `MULTI=1` includes those pairs and `ORPO=1` also builds `data/train/pref.jsonl` (discarded variants, for ablations). |
| `make train` | Trains in a Cloud Run Job with an L4, then merges and converts to GGUF in a CPU job: `make train [TAG=…] [QUANT=Q5_K_M] [TRAIN_ARGS=…]`; `TAG` defaults to today's `genlingo-<year>-<month>`. Runs `make train-data` first (accepts `MULTI=1` and `ORPO=1`). Writes `train/runs/<tag>.json`. To put the new model on the page: `DAVID_MODEL_TAG=<tag>` in `.env` and `make deploy`. |

## Quickstart

Requirements (versions in [ONBOARDING.md](ONBOARDING.md)): `uv` and `gcloud` with ADC on project `ai-experiments-487722`.

```bash
cp .env.example .env                  # models, prices and buckets
(cd duel && uv sync)                  # page and eval code (Python 3.12)
gcloud auth application-default login
make deploy                           # David (GPU) + the page
make check                            # the live page, end to end
```

## Talk day

Nothing to run: open the page about ten minutes before ([DEMO.en.md](DEMO.en.md)).
