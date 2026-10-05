# Technical decisions

Why Genlingo is built this way: the full result, the detail behind what the demo teaches, each technical decision with what was ruled out, the eval table and the cost of every training run. Back to the [README](../README.en.md). [Versión en español](DECISIONES.md).

## The result

The result is mixed, and the talk tells it that way:

- **Data with meaning moved the needle.** The on-stage David (`genlingo-2026-10c-e2b-nomulti`) was trained with counterparts validated by meaning, a lexicon prompt (each term with its counterpart, nearby terms and one from another country marked "NO de aquí", not from here), 1,715 synthetic pairs regenerated with those counterparts and 556 pairs anchored in real sentences, with more Guatemala and Colombia. It produces slang with the correct meaning in **42%** of the 399 test phrases, against **34%** for the round-2 David (`genlingo-2026-10b-e2b`), and chrF++ goes from 56.6 to **59.7**. The round was decided on a separate dev set; the test set only confirmed it.
- **David beats Gemini on correct slang:** 42% against **26%** (+16.3 points, 95% CI [+10.8, +21.8]; 101 phrases only David gets right, 36 only Goliath). He wins on Guatemalan slang (52% against 23%), on parents → Gen Z for Guatemala and Colombia (44% against 20%) and in Colombia; Mexico is a tie. On *slang handled*, which ignores meaning, they tie (82% against 77%). He answers in **~0.7 s** (p50 670 ms) and costs **$0** per phrase; Goliath takes **~2.6 s** and costs **$1.13 per 1,000 phrases**.
- **With the same glossary, Goliath ties on the whole set** (42% against 38%), but David still wins on Guatemalan slang (+17.4) and parents → Gen Z (+16.0); on neutral Spanish (LATAM) Goliath wins (55% against 32%). On reference-change recall they are close (28% David, 25% Goliath, 29% Goliath with glossary). David's advantage is **his data** (the term bank, the counterparts and the real sentences, sourced and dated) and having been trained on it.
- **Compression doesn't cost slang:** the on-stage David is the Q5_K_M (3.62 GB); with the round-2 David, the Q5_K_M landed one point from the f16 (9.27 GB) at the same latency.
- **chrF++ barely tells anyone apart:** returning the phrase untranslated already scores **53.2**; David 59.7, Goliath 53.5, Goliath with glossary 57.0. That is why the term-level metrics exist.
- **Retraining every month costs under $1, all in the cloud:** $0.97 end to end (L4 to train + CPU to merge and quantize).
- **Big models age:** with the `M` key, the previous David (`genlingo-2026-10-e2b-q5_k_m`, from two rounds ago, 27% correct slang) faces the on-stage one (42%) live.

The full story, iteration by iteration (dead ends included), is in [BITACORA.md](BITACORA.md) (Spanish); the niches where David is measured against Goliath, defined before looking at results, in [evals/niche.md](../evals/niche.md).

> The test-set references are validated automatically against the term bank (`auto_validated`); no person reviewed them. No test pair appears in the training data, not even inside a longer sentence. The test sentences and the real training pairs come from the same research round (disjoint halves by hash), so part of the gain may be closeness to those sources. Full details in [evals/report.md](../evals/report.md).

![Correct slang per variant](diagrams/resultados-jerga.png)

## What you'll learn, in detail

| Lesson | Where it lives in the code |
| --- | --- |
| **Own data with `origin`.** Every pair says where it came from: `web` (URL + license), `synthetic` (model + prompt version + seed) or `human` (event). Without that you can neither trust the evaluation nor retrain every month. | `duel/genlingo_duel/dataset.py` (the `Pair` schema validates provenance), [data/SOURCES.md](../data/SOURCES.md), [data/DATASHEET.md](../data/DATASHEET.md) |
| **Term bank, real sentences and validated synthetic pairs.** 532 terms from 76 sources and a table of counterparts validated by meaning; Gemini generates *term-substitution* pairs anchored on the bank, and every pair is validated against the bank (expected term present, no slang from another country, the source slang is gone): the on-stage David uses 1,715. On top of that, 556 pairs anchored in real web sentences. | `data/terms.jsonl`, `data/counterparts.jsonl`, `scripts/generate_pairs.py`, `duel/genlingo_duel/terms.py` |
| **LoRA on Cloud Run Jobs.** One image trains on an L4 (TRL + PEFT, r=32, alpha=16 with rsLoRA, lr 2e-4, 3 epochs) and, on a CPU job, merges, exports GGUF with llama.cpp and publishes an Ollama Modelfile. Every run records its duration and cost per stage in a file. | `train/train_lora.py`, `train/finish.py`, `train/submit_job.py`, `infra/03-train-job.sh`, `train/runs/` |
| **The compression trade-off.** f16 vs Q4_K_M, Q5_K_M, Q6_K, Q8_0 and imatrix: size, latency and how much slang is lost. | `train/quant_sweep.py`, `train_lora.to_gguf`, [Quantization: why Q5_K_M](#quantization-why-q5_k_m) |
| **Evals with term metrics.** chrF++ plus a "copy the phrase" baseline, *correct slang*, *slang handled* and *reference-change recall* against the bank; data decisions are made on a separate dev set and David's losses are published. No model judges another. | `evals/run_eval.py`, `evals/term_accuracy.py`, `evals/report.py` |
| **Monthly retrain and `david_tag`.** Models carry the date of their data (`genlingo-YYYY-MM`, with a letter when a month has two data versions: `genlingo-2026-10b-e2b` is October's second research round and `genlingo-2026-10c-e2b-nomulti` the third, without the multi-term pairs); the duel accepts `david_tag` to pit the previous David (`DAVID_PREVIOUS_TAG`) against the on-stage one. | `Makefile` (`TAG`), `DuelRequest.david_tag` in `duel/genlingo_duel/main.py`, `M` key in `web/components/presenter/PresenterApp.tsx` |
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

- **Audience app** on Cloud Run (`us-central1`, `min-instances=0` outside talks; on talk day `make stage-on` raises it to 1 so the QR code doesn't greet the room with a cold start, and `make stage-off` lowers it afterwards). Firebase anonymous Auth (no sign-up), App Check with reCAPTCHA Enterprise, one phrase every 20 s enforced in a server-side transaction, a blocklist and presenter moderation in `/admin`.
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

### Quantization: why Q5_K_M

Sweep of 2026-10-01 (`make quant-sweep`, `train/quant_sweep.py`) over the exports of `genlingo-2026-10-e2b`, all with the same glossary prompt, on that day's test set (319 pairs). imatrix was calibrated on training pairs, never on the test set. Per-phrase results in `evals/results/20261001-152529.json` (not in the repo); the full table is in the history of `evals/report.md` (commit `bb3f9fb`).

| Quantization | imatrix | Size | Slang handled | Reference-change recall | chrF++ | p50 |
| --- | --- | --- | --- | --- | --- | --- |
| Q4_K_M | no | 3.42 GB | 67% | 13% | 51.2 | 496 ms |
| Q4_K_M | yes | 3.42 GB | 72% | 14% | 51.6 | 539 ms |
| **Q5_K_M** | no | 3.62 GB | **76%** | 14% | 51.5 | 587 ms |
| Q5_K_M | yes | 3.62 GB | 75% | 15% | 52.2 | 624 ms |
| Q6_K | no | 3.83 GB | 74% | 15% | 51.9 | 527 ms |
| Q8_0 | no | 4.95 GB | 75% | 14% | 51.9 | 532 ms |
| f16 | — | 9.27 GB | 75% | 15% | 51.9 | 534 ms |

The rule (the same as in `evals/report.py`): the smallest file within 2 points of the f16 on slang handled, with p50 < 1 s. Q4_K_M loses 8 points against the f16; imatrix wins back 5 (72%) but is still 3 below. Q5_K_M is the smallest that loses no slang, for 0.2 GB more than Q4_K_M; Q6_K and Q8_0 are bigger without being better. That is why `.env` sets `QUANT=Q5_K_M` for `make train` and the on-stage David is Q5_K_M. The 2026-10-04 eval (399 phrases) repeats the result: Q4_K_M 67%, Q5_K_M 74% and f16 74% with `genlingo-2026-10-e2b`; Q5_K_M 82% and f16 81% with `genlingo-2026-10b-e2b`.

### The glossary prompt

The country prompt starts with the country ("Variante: español de Guatemala. Usa solo expresiones de Guatemala…") because "chido" and "chilero" are the same word in different places. It ends with a glossary from the term bank, country-specific or neutral. The on-stage David uses the `lexicon` style: six entries, each source-generation term that appears in the phrase with its counterpart validated by meaning (`data/counterparts.jsonl`; with no counterpart, its meaning), the closest other-generation terms according to EmbeddingGemma and one from another country marked "NO de aquí" (not from here). Davids from earlier rounds use the `glossary` style: four entries without counterparts, first the terms that appear verbatim in the phrase, then the closest ones. Retrieval time is added to David's latency.

David is trained on exactly that format (`make train-data` uses the `lexicon` style by default) and the duel reads from `train/runs/<tag>.json` which prompt each David was trained with: there is no gap between training and stage. Goliath gets the country prompt, without a glossary, by default (`GOLIATH_PROMPT_STYLE`), because the bank is David's data; `make eval` also runs Goliath with the same glossary, which shows how much of the result is the model and how much is the data.

### The test set is web-only, never synthetic

A reference written by Gemini would reward Goliath for sounding like itself. The test pairs come from real sentences found on the web (two research rounds, 522 candidates); the reference is written by the curator from the meaning the source gives, and `scripts/validate_test_set.py` validates it against the term bank with no human involved: 399 are `auto_validated`. It also rejects any test pair that appears in a training file (synthetic, real or audience), even inside a longer sentence: raw and normalized substring matching (`duel/genlingo_duel/overlap.py`). The second round is split by a stable hash of the id: half goes to test and half to training pairs anchored in real sentences (`make real-pairs`), with no sentence shared. The `Pair` schema rejects any synthetic pair in the test split. Audience pairs (`origin=human`) are split 80/20 between training and test by a stable hash of the id.

### Dated Gemini price schedule

Prices change, and that is part of the story. `GEMINI_PRICE_SCHEDULE=2026-09-30:0.75/3.75,2027-01-01:1.50/7.50` is a list of prices by date: every round and every eval uses the price in force that day and records which one it used. The report also shows what the same eval would cost at the 2027 price ($2.26 per 1,000 phrases instead of $1.13). Thinking tokens are billed as output. David's inference costs $0; the presenter view shows his training cost amortized per round. Exports of one training run (`-f16`, `-q5_k_m`, `-iq-q4_k_m`…) share its `train/runs/<tag>.json`.

### App Check enforcement is project-wide

`infra/06-app-check.sh` registers reCAPTCHA Enterprise as the App Check provider and, with `ENFORCE_FIRESTORE=1`, enforces App Check on Cloud Firestore. That enforcement is **per project**: App Check has no per-database policy, so any web or mobile client of any database in `ai-experiments-487722` will have to send App Check tokens. Server code (Admin SDK, IAM) is not affected. The API routes enforce it on their own with `APP_CHECK_ENFORCE=1`, which `infra/05-deploy-web.sh` turns on when `RECAPTCHA_SITE_KEY` is set. Automated tests and the emulator use a registered debug token.

### Who wins a round

- **Evaluation round** (test-set phrase, `E` key): the higher chrF++ wins; gaps under 0.5 are a draw. It uses `auto_validated` pairs (or ones a person approved), ready with no human review.
- **Specialty round: chapín slang** (`G` key): the same, but with the next Guatemalan test phrase in a fixed seeded order (`SPECIALTY_SEED`), the «slang chapín» niche of [evals/niche.md](../evals/niche.md). Nobody picks the phrase. The stage's default country is `GT`.
- **Live phrase** (typed with `/`) or **audience phrase** (from a phone): with the audience app connected (`AUDIENCE_FEED=1`) the vote decides (`V` closes voting); without an audience the round shows both translations with no winner. The whole talk works without an audience: `E` rounds and typed phrases.
- Audience phrases that pass the blocklist go straight to the screen queue (`AUTO_APPROVE_PHRASES=1`, the default); with `0` the presenter approves them in `/admin`.
- If Goliath has no network or fails, David wins by showing up.

## Results

Eval of 2026-10-04 on 399 `auto_validated` web test pairs (out of 522 candidates; 123 rejected by the automatic validation, 4 of them for appearing inside a training pair). Every local model with the prompt it was trained on, one at a time on the M1 Max; Goliath at temperature 0 (2 errors with glossary). *Correct slang* (amendment 1 of [evals/niche.md](../evals/niche.md)): the term produced means the same, according to the counterpart table validated by meaning.

| Variant | Correct slang | Slang handled | Gen Z → parents | parents → Gen Z | Reference-change recall | chrF++ | p50 | Cost / 1,000 phrases | Size |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Copy the phrase (baseline) | 1% | 1% | 0% | 3% | 0% | 53.2 | — | — | — |
| `gemma4:e2b-it-qat` (base) | 14% | 58% | 95% | 10% | 14% | 50.2 | 364 ms | $0 | 4.34 GB |
| `gemma4:e2b-it-qat` + glossary | 38% | 62% | 94% | 20% | 23% | 55.0 | 452 ms | $0 | 4.34 GB |
| `gemma4:e4b` (base) | 19% | 68% | 97% | 31% | 17% | 48.2 | 802 ms | $0 | 6.58 GB |
| `genlingo-2026-09` (Q4, plain prompt) | 18% | 62% | 94% | 20% | 14% | 55.0 | 391 ms | $0 | 3.42 GB |
| `genlingo-2026-10-e2b` + glossary (Q4) | 25% | 67% | 95% | 31% | 16% | 55.7 | 512 ms | $0 | 3.42 GB |
| `genlingo-2026-10-e2b-q5_k_m` + glossary (`M` key) | 27% | 74% | 97% | 43% | 18% | 55.4 | 564 ms | $0 | 3.62 GB |
| `genlingo-2026-10-e2b-f16` + glossary | 28% | 74% | 99% | 42% | 19% | 56.3 | 566 ms | $0 | 9.27 GB |
| `genlingo-2026-10b-e2b` + glossary (Q5_K_M, round 2) | 34% | 82% | 99% | 59% | 22% | 56.6 | 557 ms | $0 | 3.62 GB |
| `genlingo-2026-10b-e2b-f16` + glossary | 34% | 81% | 98% | 59% | 22% | 56.7 | 543 ms | $0 | 9.27 GB |
| **`genlingo-2026-10c-e2b-nomulti` + lexicon (Q5_K_M, on stage)** | **42%** | **82%** | 100% | 58% | 28% | **59.7** | 670 ms | **$0** | 3.62 GB |
| Goliath `gemini-3.8-flash` | 26% | 77% | 97% | 51% | 25% | 53.5 | 2.60 s | $1.13 | — |
| Goliath + the same glossary | 38% | 82% | 100% | 58% | 29% | 57.0 | 3.05 s | $1.27 | — |

**Reading the results.** Phrase by phrase, David produces the correct slang and Goliath doesn't in 101 phrases; the other way round, in 36. Against Goliath with the glossary the count narrows (79 against 63) and the whole set is a tie; David still wins on Guatemalan slang and parents → Gen Z, and Goliath wins on neutral Spanish (LATAM). On *slang handled* (the register changed, regardless of meaning) David and Goliath tie, and David still slips in another country's slang in 16 of 173 parents → Gen Z phrases (Goliath: 3). This round's jump is in meaning: the round-2 David already handled 82%, but got the term right in 34%. David wins on speed, cost and privacy, and wins on correct slang as long as the term bank, the counterparts and the real sentences are his alone. chrF++ stays close to the copy baseline (53.2) because a register rewrite keeps almost every word: it can't decide who translated the slang. The per-niche CIs are in [evals/niche_report.md](../evals/niche_report.md).

David's ten worst losses and the per-country and per-direction breakdowns are in [evals/report.md](../evals/report.md). The first version of the data (free paraphrase) left David *below* the base model (chrF++ 39.1): it is documented in [evals/experiments/2026-09-parafrasis-libres.md](../evals/experiments/2026-09-parafrasis-libres.md).

| `M` key: the previous David | Wi-Fi off |
| --- | --- |
| ![The previous David (M key)](demo/08-mes-anterior.png) | ![No internet: Goliath offline, David keeps going](demo/09-sin-internet.png) |
| `M` key: the previous David (`genlingo-2026-10-e2b-q5_k_m`) against Goliath on the same phrase ("no manches, la peli estuvo bien mid y me dio cringe"); the scoreboard counts only his rounds. | No network: Goliath shows as "sin conexión" (offline) and the on-stage David answers in 0.81 s ("ese bolo anda chupando desde la tarde…" → "Ese muchacho anda borrachísimo desde la tarde…", that guy has been very drunk since the afternoon). |

## Training cost per run

Cloud Run Jobs in `europe-west4`: training on 1× NVIDIA L4 without zonal redundancy, 8 vCPU, 32 GiB; since `genlingo-2026-10b-e2b`, merge + GGUF on a separate CPU job (8 vCPU, 32 GiB). Cost = billed seconds × per-second rates (`CLOUD_RUN_*_USD_PER_S` in `.env`), per stage.

| Run | Base | Pairs | Outcome | Duration | Cost |
| --- | --- | --- | --- | --- | --- |
| `genlingo-2026-09` | E2B | 1,000 (minimal edits) | done (loss 2.33 → 0.14) | 17.4 min | $0.41 |
| `genlingo-2026-10-e2b` | E2B | 1,500 (anchored on the bank) | done (loss 2.26 → 0.12) | 28.2 min | $0.67 |
| `genlingo-2026-10-e4b` | E4B | 1,500 (anchored on the bank) | trained; out of memory while merging → `make train-finish` | 41.3 min | $0.98 |
| `genlingo-2026-10b-e2b` | E2B | 1,709 (1,375 synthetic + 334 anchored in real sentences) | done in the cloud, two jobs (loss 2.62 → 0.16): train 25.3 min $0.60 + merge/GGUF Q5_K_M and f16 9.0 min $0.11 | 34.3 min | $0.71 |
| `genlingo-2026-10c-e2b` | E2B | 2,972 (2,416 synthetic, 701 of them with 2–3 terms, + 556 anchored in real sentences) | done (loss 2.19 → 0.04): train 54.0 min $1.28 + merge/GGUF 10.3 min $0.13; left out for latency (p50 1.99 s on dev) | 64.2 min | $1.41 |
| `genlingo-2026-10c-e2b-nomulti` | E2B | 2,271 (1,715 synthetic + 556 anchored in real sentences) | done, **on stage** (loss 1.97 → 0.06): train 35.7 min $0.85 + merge/GGUF 10.2 min $0.13 | 45.9 min | $0.97 |
| `genlingo-2026-10c-e2b-nomulti-orpo` | E2B | 264 preference pairs on the nomulti adapter | done: sampling + ORPO 18.4 min $0.44 + merge/GGUF 9.9 min $0.12; left out (parents → Gen Z slang dropped on dev) | 28.3 min | $0.56 |
| `failed/genlingo-2026-10b-e2b-zct96` | E2B | 1,709 | trained; killed for memory converting to GGUF f16 in the single job → led to the split into two jobs | 26.8 min | $0.63 |
| `failed/genlingo-2026-10c-e2b-nomulti-orpo-8995k` | E2B | 2,271 | timed out: the model was loaded on the CPU for sampling | 60.4 min | $1.43 |
| `failed/genlingo-2026-10c-e2b-nomulti-orpo-jwt8d` | E2B | 2,271 | out of memory on the L4: with batch 4 Gemma's logits didn't fit (now batch 1 × 16) | 16.2 min | $0.38 |
| `failed/genlingo-2026-09-nv5r5` | E2B | 1,000 | failed at start (`gcc` missing for Triton) | 10.9 min | $0.26 |
| `failed/genlingo-2026-09-kcwqz` | E2B | 1,000 | cancelled: GGUF written to the bucket mount, too slow | 31.2 min | $0.74 |
| `failed/genlingo-2026-09-kqlxv` | E2B | 1,000 | cancelled at ~28 min (same cause, on read) | — | not recorded |
| `experiments/genlingo-2026-09-parafrasis` | E2B | 1,000 (free paraphrase) | laptop, MPS | 36.9 min | $0 |

Generating 1,500 synthetic pairs with Gemini costs under $1 ($0.71 and about 10 min in round 3, `data/pairs/synthetic.meta.json`). A monthly E2B retrain, train → GGUF all in the cloud, costs under $1; David's inference, $0.
