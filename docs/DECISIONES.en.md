# Technical decisions

Why Genlingo is built this way: the full result, the detail behind what the demo teaches, each technical decision with what was ruled out, the eval table and the cost of every training run. Back to the [README](../README.en.md). [Versión en español](DECISIONES.md).

## The result

The result is mixed, and the talk tells it that way:

- **Real data moved the needle.** The on-stage David (`genlingo-2026-10b-e2b`) was trained on the second research round: 334 pairs anchored in real sentences, the term bank grown to 406 terms in the glossary, and the synthetic pairs re-filtered against that bank. It handles the slang in **82%** of the 399 test phrases, against **74%** for the previous David at the same compression. Almost all of the gain is in the hard direction, parents → Gen Z: from 43% to **59%**. It is one run per David, without isolating how much each change contributes.
- **David now beats plain Gemini on slang:** 82% against **78%**, and 56.6 against 53.1 on chrF++. He answers in **~0.6 s** (p50 557 ms) and costs **$0** per phrase; Goliath takes **~3.3 s** and costs **$1.08 per 1,000 phrases**.
- **With the same glossary, they tie on slang (82%)**, and Goliath matches more of the reference's words (30% against 22%). David's advantage is not being a better model: it is **his data** (the term bank and the real sentences, sourced and dated).
- **Compression no longer costs slang:** the on-stage David is the Q5_K_M (3.62 GB), one point from the f16 (9.27 GB), at the same latency.
- **chrF++ barely tells anyone apart:** returning the phrase untranslated already scores **53.2**; David 56.6, Goliath 53.1, Goliath with glossary 56.5. That is why the term-level metric exists.
- **Retraining every month costs under $1, all in the cloud:** $0.71 end to end (L4 to train + CPU to merge and quantize).
- **Big models age:** with the `M` key, the previous David (`genlingo-2026-10-e2b-q5_k_m`, 74%) faces the on-stage one (82%) live.

The full story, iteration by iteration (dead ends included), is in [BITACORA.md](BITACORA.md) (Spanish); the niches where David is measured against Goliath, defined before looking at results, in [evals/niche.md](../evals/niche.md).

> The test-set references are validated automatically against the term bank (`auto_validated`); no person reviewed them. No test pair appears in the training data, not even inside a longer sentence. The test sentences and the real training pairs come from the same research round (disjoint halves by hash), so part of the gain may be closeness to those sources. Full details in [evals/report.md](../evals/report.md).

![Slang handled per variant](diagrams/resultados-jerga.png)

## What you'll learn, in detail

| Lesson | Where it lives in the code |
| --- | --- |
| **Own data with `origin`.** Every pair says where it came from: `web` (URL + license), `synthetic` (model + prompt version + seed) or `human` (event). Without that you can neither trust the evaluation nor retrain every month. | `duel/genlingo_duel/dataset.py` (the `Pair` schema validates provenance), [data/SOURCES.md](../data/SOURCES.md), [data/DATASHEET.md](../data/DATASHEET.md) |
| **Term bank, real sentences and validated synthetic pairs.** 406 terms from 57 sources; Gemini generates *term-substitution* pairs anchored on the bank, and every pair is validated against the bank (expected term present, no slang from another country, the source slang is gone): 1,375 remain. On top of that, 334 pairs anchored in real web sentences. | `data/terms.jsonl`, `scripts/generate_pairs.py`, `duel/genlingo_duel/terms.py` |
| **LoRA on Cloud Run Jobs.** One image trains on an L4 (TRL + PEFT, r=16, alpha=32, lr 2e-4, 3 epochs) and, on a CPU job, merges, exports GGUF with llama.cpp and publishes an Ollama Modelfile. Every run records its duration and cost per stage in a file. | `train/train_lora.py`, `train/finish.py`, `train/submit_job.py`, `infra/03-train-job.sh`, `train/runs/` |
| **The compression trade-off.** f16 vs Q4_K_M, Q5_K_M, Q6_K, Q8_0 and imatrix: size, latency and how much slang is lost. | `train_lora.to_gguf`, "Compresión" section of `evals/report.md` |
| **Evals with term metrics.** chrF++ plus a "copy the phrase" baseline, *slang handled* and *reference-change recall* against the bank; David's losses are published. No model judges another. | `evals/run_eval.py`, `evals/term_accuracy.py`, `evals/report.py` |
| **Monthly retrain and `david_tag`.** Models carry the date of their data (`genlingo-YYYY-MM`, with a letter when a month has two data versions: `genlingo-2026-10b-e2b` is October's second research round); the duel accepts `david_tag` to pit last month's David against this month's. | `Makefile` (`TAG`), `DuelRequest.david_tag` in `duel/genlingo_duel/main.py`, `M` key in `web/components/presenter/PresenterApp.tsx` |
| **Offline by design.** The network check is a 0.8 s TCP connect; with no network, Goliath shows as "sin conexión" (offline) and David keeps going. The glossary is retrieved with a local EmbeddingGemma and cached embeddings. | `duel/duel_core/connectivity.py`, `duel/duel_core/duel.py`, `duel/genlingo_duel/glossary.py` |

## Decisions

### What runs on the laptop, and why

| Component | Why on the laptop |
| --- | --- |
| **David** (fine-tuned Gemma, Ollama) | It is the thesis: a small model runs on your laptop, without internet and with no per-phrase cost. The latency that matters is the stage hardware's (M1 Max 64 GB), not a server's. |
| **EmbeddingGemma** (Ollama) | Retrieves the term-bank glossary with no network. The bank's embeddings are computed once and kept in `data/.cache/term_embeddings.json`. |
| **Duel service** (FastAPI + SQLite) | It must work with Wi-Fi off and measure latency on the stage machine. The local SQLite scoreboard makes `make reset` take under a second. |
| **Presenter view** (Next.js, local production build) | Offline mode: self-hosted fonts and a QR code generated in the browser, nothing is downloaded during the talk. |

When there is network, the duel also calls Goliath and, with `AUDIENCE_FEED=1`, receives approved phrases and publishes rounds to Firestore. With no network, all of that goes quiet and David keeps going.

### What runs in the cloud

- **Audience app** on Cloud Run (`us-central1`, `min-instances=1` so the QR code doesn't greet the room with a cold start). Firebase anonymous Auth (no sign-up), App Check with reCAPTCHA Enterprise, one phrase every 20 s enforced in a server-side transaction, a blocklist and presenter moderation in `/admin`.
- **Firestore**, database `genlingo`: phrases, rounds, votes (one per person) and audience pairs. The rules deny every client write; the `genlingo-web` service account can only touch that database (IAM condition).
- **Goliath**: Gemini on Vertex AI with ADC, `GOOGLE_CLOUD_LOCATION=global`, thinking level `low`.
- **Training**: two Cloud Run Jobs in `europe-west4` (L4 to train, CPU to merge and convert to GGUF); image built with Cloud Build into Artifact Registry `charlas2027`.

### Why two Cloud Run Jobs

One retrain a month doesn't justify anything running between runs. Cloud Run Jobs are serverless, billed per second while the task runs, and use the same kind of image as everything else. `make train` chains two jobs from the same image (`infra/03-train-job.sh`):

| Job | Machine | What it does |
| --- | --- | --- |
| `genlingo-train` | 1× L4, 8 vCPU, 32 GiB | Trains the LoRA adapter and saves it to the bucket volume (`ADAPTER_ONLY=1`). |
| `genlingo-finish` | CPU only, 8 vCPU, 32 GiB, 10 GiB ephemeral disk | Merges the adapter, converts to GGUF f16, quantizes to `QUANT` (Q5_K_M) and publishes to the models bucket (`train/finish.py`). |

`train/submit_job.py` waits for both, computes each one's cost from the per-second GPU, vCPU and memory rates, and writes the per-stage detail and the total to `train/runs/<tag>.json`.

Why split it: Cloud Run's filesystem lives in the instance's memory. Training, saving a 10 GB merged checkpoint and writing a 9 GB f16 GGUF don't fit together in 32 GiB: run `genlingo-2026-10b-e2b` (`zct96`) died of memory while converting to f16, and E4B had already failed the same way while merging. The CPU job holds nothing from training: the base weights are copied from the bucket with one sequential read (memory-mapping them from the bucket mount ran at ~5 MB/s), the merge runs in a child process (its ~10 GB go back when it exits), the merged checkpoint goes to the in-memory disk, the f16 GGUF goes to the ephemeral disk (disk-backed, not memory) and the checkpoint is deleted before quantizing. And the GPU isn't billed while merging and converting. Base weights are cached on a Cloud Storage volume shared by both jobs; the GGUFs don't go there because the converter writes out of order and the bucket mount ran at ~3 MB/s (cancelled runs `kcwqz` and `kqlxv` in `train/runs/failed/`).

Ruled out: Google Cloud Batch with one L4 and a persistent disk. It solved memory in a single step, but adds another API, a VM image with drivers and another set of permissions, while two jobs reuse the image, the service account and the bucket that already existed.

Available alternatives: a Vertex AI Custom Job with the same container and a 200 GB disk (`TRAIN_RUNTIME=vertex`, all in one step), the `train/genlingo.ipynb` notebook for Colab, and `make train-local` on the Mac (36.9 min for 1,000 pairs on MPS; on the L4, the training phase for the same size took 5.8 min).

The monthly cycle, from data to stage and back (labels in Spanish):

![Monthly cycle](diagrams/ciclo-mensual.png)

### `make train-finish`: the laptop fallback

`make train-finish TAG=…` runs the same `train/finish.py` on the 64 GB Mac: it downloads the adapter from the bucket, merges, converts, quantizes (`QUANT`, `KEEP_F16=1` to publish the f16 too) and publishes to the same bucket, so `make pull-model` doesn't care where the merge happened. Use it when the CPU job can't run, and for E4B: its 16 GB merged checkpoint plus the model in memory don't fit in 32 GiB, not even in the CPU job. E4B did not go on stage: with 67% slang handled and a p50 of 836 ms it doesn't beat the E2B f16.

### The glossary prompt

The country prompt starts with the country ("Variante: español de Guatemala. Usa solo expresiones de Guatemala…") because "chido" and "chilero" are the same word in different places. It ends with a four-entry glossary from the term bank, country-specific or neutral: first the source-generation terms that appear verbatim in the phrase, then the closest ones by meaning according to EmbeddingGemma. Retrieval time is added to David's latency.

David is trained on exactly that format (`make train-data` uses the glossary style by default) and the duel reads from `train/runs/<tag>.json` which prompt each David was trained with: there is no gap between training and stage. Goliath gets the country prompt, without a glossary, by default (`GOLIATH_PROMPT_STYLE`), because the bank is David's data; `make eval` also runs Goliath with the same glossary, which shows how much of the result is the model and how much is the data.

### The test set is web-only, never synthetic

A reference written by Gemini would reward Goliath for sounding like itself. The test pairs come from real sentences found on the web (two research rounds, 522 candidates); the reference is written by the curator from the meaning the source gives, and `scripts/validate_test_set.py` validates it against the term bank with no human involved: 399 are `auto_validated`. It also rejects any test pair that appears in a training file (synthetic, real or audience), even inside a longer sentence: raw and normalized substring matching (`duel/genlingo_duel/overlap.py`). The second round is split by a stable hash of the id: half goes to test and half to training pairs anchored in real sentences (`make real-pairs`), with no sentence shared. The `Pair` schema rejects any synthetic pair in the test split. Audience pairs (`origin=human`) are split 80/20 between training and test by a stable hash of the id.

### Dated Gemini price schedule

Prices change, and that is part of the story. `GEMINI_PRICE_SCHEDULE=2026-09-30:0.75/3.75,2027-01-01:1.50/7.50` is a list of prices by date: every round and every eval uses the price in force that day and records which one it used. The report also shows what the same eval would cost at the 2027 price ($2.17 per 1,000 phrases instead of $1.08). Thinking tokens are billed as output. David's inference costs $0; the presenter view shows his training cost amortized per round. Exports of one training run (`-f16`, `-q5_k_m`, `-iq-q4_k_m`…) share its `train/runs/<tag>.json`.

### App Check enforcement is project-wide

`infra/06-app-check.sh` registers reCAPTCHA Enterprise as the App Check provider and, with `ENFORCE_FIRESTORE=1`, enforces App Check on Cloud Firestore. That enforcement is **per project**: App Check has no per-database policy, so any web or mobile client of any database in `ai-experiments-487722` will have to send App Check tokens. Server code (Admin SDK, IAM) is not affected. The API routes enforce it on their own with `APP_CHECK_ENFORCE=1`, which `infra/05-deploy-web.sh` turns on when `RECAPTCHA_SITE_KEY` is set. Automated tests and the emulator use a registered debug token.

### Who wins a round

- **Evaluation round** (test-set phrase, `E` key): the higher chrF++ wins; gaps under 0.5 are a draw. It uses `auto_validated` pairs (or ones a person approved), ready with no human review.
- **Specialty round: chapín slang** (`G` key): the same, but with the next Guatemalan test phrase in a fixed seeded order (`SPECIALTY_SEED`), the «slang chapín» niche of [evals/niche.md](../evals/niche.md). Nobody picks the phrase. The stage's default country is `GT`.
- **Live phrase** (typed with `/`) or **audience phrase** (from a phone): with the audience app connected (`AUDIENCE_FEED=1`) the vote decides (`V` closes voting); without an audience the round shows both translations with no winner. The whole talk works without an audience: `E` rounds and typed phrases.
- Audience phrases that pass the blocklist go straight to the screen queue (`AUTO_APPROVE_PHRASES=1`, the default); with `0` the presenter approves them in `/admin`.
- If Goliath has no network or fails, David wins by showing up.

## Results

Eval of 2026-10-02 on 399 `auto_validated` web test pairs (out of 522 candidates; 123 rejected by the automatic validation, 4 of them for appearing inside a training pair). Every local model with the prompt it was trained on, one at a time on the M1 Max; Goliath at temperature 0 (1 error without glossary).

| Variant | Slang handled | Gen Z → parents | parents → Gen Z | Reference-change recall | chrF++ | p50 | Cost / 1,000 phrases | Size |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Copy the phrase (baseline) | 1% | 0% | 3% | 0% | 53.2 | — | — | — |
| `gemma4:e2b-it-qat` (base) | 58% | 95% | 10% | 14% | 50.2 | 364 ms | $0 | 4.34 GB |
| `gemma4:e2b-it-qat` + glossary | 62% | 94% | 20% | 23% | 55.0 | 452 ms | $0 | 4.34 GB |
| `gemma4:e4b` (base) | 68% | 97% | 31% | 17% | 48.2 | 802 ms | $0 | 6.58 GB |
| `genlingo-2026-09` (Q4, plain prompt) | 62% | 94% | 20% | 14% | 55.0 | 391 ms | $0 | 3.42 GB |
| `genlingo-2026-10-e2b` + glossary (Q4) | 67% | 95% | 31% | 16% | 55.7 | 512 ms | $0 | 3.42 GB |
| `genlingo-2026-10-e2b-q5_k_m` + glossary (previous) | 74% | 97% | 43% | 18% | 55.4 | 564 ms | $0 | 3.62 GB |
| `genlingo-2026-10-e2b-f16` + glossary | 74% | 99% | 42% | 19% | 56.3 | 566 ms | $0 | 9.27 GB |
| **`genlingo-2026-10b-e2b` + glossary (Q5_K_M, on stage)** | **82%** | 99% | **59%** | 22% | **56.6** | **557 ms** | **$0** | 3.62 GB |
| `genlingo-2026-10b-e2b-f16` + glossary | 81% | 98% | 59% | 22% | 56.7 | 543 ms | $0 | 9.27 GB |
| Goliath `gemini-3.8-flash` | 78% | 99% | 51% | 25% | 53.1 | 3.26 s | $1.08 | — |
| Goliath + the same glossary | 82% | 98% | 62% | 30% | 56.5 | 3.84 s | $1.24 | — |

**Reading the results.** Phrase by phrase, David handles the slang and Goliath doesn't in 46 phrases; the other way round, in 31. Against Goliath with the glossary the count flips: 36 against 39. On *reference-change recall* (exact words of the reference) Goliath beats David with and without the glossary, and David still slips in another country's slang in 14 of 173 parents → Gen Z phrases (Goliath: 2). The second-round data gave David 8 points of slang handled, almost all in parents → Gen Z, which is what the real pairs teach in that direction (a real Gen Z sentence as the output). David wins on speed, cost and privacy, and wins on slang as long as the term bank and the real sentences are his alone. chrF++ stays glued to the copy baseline (53.2) because a register rewrite keeps almost every word: it can't decide who translated the slang.

David's ten worst losses and the per-country and per-direction breakdowns are in [evals/report.md](../evals/report.md). The first version of the data (free paraphrase) left David *below* the base model (chrF++ 39.1): it is documented in [evals/experiments/2026-09-parafrasis-libres.md](../evals/experiments/2026-09-parafrasis-libres.md).

| `M` key: last month's David | Wi-Fi off |
| --- | --- |
| ![Last month's David (M key)](screenshots/presentador-mes-pasado.png) | ![No internet: Goliath offline, David keeps going](screenshots/presentador-sin-internet.png) |
| `M` key: the previous David (`genlingo-2026-10-e2b-q5_k_m`) against Goliath on the same phrase; the scoreboard counts only his rounds. | No network: Goliath shows as "sin conexión" and David answers in 0.53 s ("bolo" → "borrachín"; "chupando" becomes "de fiesta", close but not exact: it means drinking). |

## Training cost per run

Cloud Run Jobs in `europe-west4`: training on 1× NVIDIA L4 without zonal redundancy, 8 vCPU, 32 GiB; since `genlingo-2026-10b-e2b`, merge + GGUF on a separate CPU job (8 vCPU, 32 GiB). Cost = billed seconds × per-second rates (`CLOUD_RUN_*_USD_PER_S` in `.env`), per stage.

| Run | Base | Pairs | Outcome | Duration | Cost |
| --- | --- | --- | --- | --- | --- |
| `genlingo-2026-09` | E2B | 1,000 (minimal edits) | done (loss 2.33 → 0.14) | 17.4 min | $0.41 |
| `genlingo-2026-10-e2b` | E2B | 1,500 (anchored on the bank) | done (loss 2.26 → 0.12) | 28.2 min | $0.67 |
| `genlingo-2026-10-e4b` | E4B | 1,500 (anchored on the bank) | trained; out of memory while merging → `make train-finish` | 41.3 min | $0.98 |
| `genlingo-2026-10b-e2b` | E2B | 1,709 (1,375 synthetic + 334 anchored in real sentences) | done in the cloud, two jobs (loss 2.62 → 0.16): train 25.3 min $0.60 + merge/GGUF Q5_K_M and f16 9.0 min $0.11 | 34.3 min | $0.71 |
| `failed/genlingo-2026-10b-e2b-zct96` | E2B | 1,709 | trained; killed for memory converting to GGUF f16 in the single job → led to the split into two jobs | 26.8 min | $0.63 |
| `failed/genlingo-2026-09-nv5r5` | E2B | 1,000 | failed at start (`gcc` missing for Triton) | 10.9 min | $0.26 |
| `failed/genlingo-2026-09-kcwqz` | E2B | 1,000 | cancelled: GGUF written to the bucket mount, too slow | 31.2 min | $0.74 |
| `failed/genlingo-2026-09-kqlxv` | E2B | 1,000 | cancelled at ~28 min (same cause, on read) | — | not recorded |
| `experiments/genlingo-2026-09-parafrasis` | E2B | 1,000 (free paraphrase) | laptop, MPS | 36.9 min | $0 |

Generating 1,500 synthetic pairs with Gemini costs under $1 (about 6 min). A monthly E2B retrain, train → GGUF all in the cloud, costs under $1; David's inference, $0.
