# Technical decisions

Why Genlingo is built this way: the full result, the detail behind what the demo teaches, each technical decision with what was ruled out, the eval table and the cost of every training run. Back to the [README](../README.en.md). [Versión en español](DECISIONES.md).

## The result

The result is mixed, and the talk tells it that way:

- **Data with meaning moved the needle.** The round-3 David (`genlingo-2026-10c-e2b-nomulti`) was trained with counterparts validated by meaning, a lexicon prompt (each term with its counterpart, nearby terms and one from another country marked "NO de aquí", not from here), 1,715 synthetic pairs regenerated with those counterparts and 556 pairs anchored in real sentences, with more Guatemala and Colombia. It produces slang with the correct meaning in **42%** of the 399 test phrases, against **34%** for the round-2 David (`genlingo-2026-10b-e2b`), and chrF++ goes from 56.6 to **59.7**. The round was decided on a separate dev set; the test set only confirmed it.
- **Round 4 brought the Gen Z slang of Mexico and neutral Spanish** (2026-10-06). The page's David today is `genlingo-2026-10d-e2b`: the same data plus 1,600 pairs anchored in Gen Z slang of those two cases and 17 real sentences. In the 2026-10-07 eval (in the cloud) it gets the meaning right in **44%** of the test phrases against **24%** for Goliath (+19.5 [+13.5, +25.6]); neutral Spanish goes from 32% to 43%. With general Gen Z slang (cringe, random, crush…) David and Goliath tie ([evals/report_probe.md](../evals/report_probe.md)): David's edge is local slang.
- **David beats Gemini on correct slang:** 42% against **26%** (+16.3 points, 95% CI [+10.8, +21.8]; 101 phrases only David gets right, 36 only Goliath). He wins on Guatemalan slang (52% against 23%), on parents → Gen Z for Guatemala and Colombia (44% against 20%) and in Colombia; Mexico is a tie. On *slang handled*, which ignores meaning, they tie (82% against 77%). In the eval he answered in **~0.7 s** (p50 670 ms, on a Mac); Goliath took **~2.6 s** and cost **$1.13 per 1,000 phrases**. In the cloud David answers in **~0.5 s** ([David in the cloud](#david-in-the-cloud)).
- **With the same glossary, Goliath ties on the whole set** (42% against 38%), but David still wins on Guatemalan slang (+17.4) and parents → Gen Z (+16.0); on neutral Spanish (LATAM) Goliath wins (55% against 32%). On reference-change recall they are close (28% David, 25% Goliath, 29% Goliath with glossary). David's advantage is **his data** (the term bank, the counterparts and the real sentences, sourced and dated) and having been trained on it.
- **Compression doesn't cost slang:** the page's David is the Q5_K_M (3.62 GB); with the round-2 David, the Q5_K_M landed one point from the f16 (9.27 GB) at the same latency.
- **chrF++ barely tells anyone apart:** returning the phrase untranslated already scores **53.2**; David 59.7, Goliath 53.5, Goliath with glossary 57.0. That is why the term-level metrics exist.
- **Retraining every month costs under $1, all in the cloud:** $0.97 end to end (L4 to train + CPU to merge and quantize).
- **Retraining on new data buys slang:** the David from two data rounds ago (`genlingo-2026-10-e2b-q5_k_m`) got 27% of the slang right; today's, 42%.

The full story, iteration by iteration (dead ends included), is in [BITACORA.md](BITACORA.md) (Spanish); the niches where David is measured against Goliath, defined before looking at results, in [evals/niche.md](../evals/niche.md).

> The test-set references are validated automatically against the term bank (`auto_validated`); no person reviewed them. No test pair appears in the training data, not even inside a longer sentence. The test sentences and the real training pairs come from the same research round (disjoint halves by hash), so part of the gain may be closeness to those sources. Full details in [evals/report.md](../evals/report.md).

![Correct slang per variant](diagrams/resultados-jerga.png)

## What you'll learn, in detail

| Lesson | Where it lives in the code |
| --- | --- |
| **Own data with `origin`.** Every pair says where it came from: `web` (URL + license), `synthetic` (model + prompt version + seed) or `human` (event). Without that you can neither trust the evaluation nor retrain every month. | `duel/genlingo_duel/dataset.py` (the `Pair` schema validates provenance), [data/SOURCES.md](../data/SOURCES.md), [data/DATASHEET.md](../data/DATASHEET.md) |
| **Term bank, real sentences and validated synthetic pairs.** 532 terms from 92 sources and a table of counterparts validated by meaning; Gemini generates *term-substitution* pairs anchored on the bank, and every pair is validated against the bank (expected term present, no slang from another country, the source slang is gone): the page's David uses 1,715 plus 1,600 from round 4 (Gen Z of Mexico and neutral Spanish). On top of that, 565 pairs anchored in real web sentences. Sentences quoted from all-rights-reserved sources live in a private bucket, not in the repo ([data/SOURCES.md](../data/SOURCES.md)). | `data/terms.jsonl`, `data/counterparts.jsonl`, `scripts/generate_pairs.py`, `duel/genlingo_duel/terms.py` |
| **LoRA on Cloud Run Jobs.** One image trains on an L4 (TRL + PEFT, r=32, alpha=16 with rsLoRA, lr 2e-4, 3 epochs) and, on a CPU job, merges, exports GGUF with llama.cpp and publishes an Ollama Modelfile. Every run records its duration and cost per stage in a file. | `train/train_lora.py`, `train/finish.py`, `train/submit_job.py`, `infra/03-train-job.sh`, `train/runs/` |
| **The compression trade-off.** f16 vs Q4_K_M, Q5_K_M, Q6_K, Q8_0 and imatrix: size, latency and how much slang is lost. | `train_lora.to_gguf`, `evals/quant_sweep.json`, [Quantization: why Q5_K_M](#quantization-why-q5_k_m) |
| **Evals with term metrics.** chrF++ plus a "copy the phrase" baseline, *correct slang*, *slang handled* and *reference-change recall* against the bank; data decisions are made on a separate dev set and David's losses are published. No model judges another. | `evals/run_eval.py`, `evals/term_accuracy.py`, `evals/report.py` |
| **Monthly retrain.** Models carry the date of their data (`genlingo-YYYY-MM`, with a letter when a month has two data versions: `genlingo-2026-10b-e2b` is October's second research round `genlingo-2026-10c-e2b-nomulti` the third, without the multi-term pairs, and `genlingo-2026-10d-e2b` the fourth); the page uses the one in `DAVID_MODEL_TAG`. | `Makefile` (`TAG`), `.env.example` (`DAVID_MODEL_TAG`), `train/runs/` |
| **Side-by-side comparison.** A public page where David and Goliath translate the same phrase with their time, and a ✓/✗ check per term on the verified examples. | `duel/genlingo_duel/static/index.html`, `duel/genlingo_duel/main.py`, `duel/genlingo_duel/translate_page.py`, `duel/genlingo_duel/term_check.py`, `data/translate_examples.json` |
| **Your model on your own GPU.** David runs with Ollama on Cloud Run with an L4, the model and the compiled CUDA kernels inside the image; private (identity token) and scaling to zero. The page wakes him when it opens and keeps him on while it stays open. | `david/Dockerfile`, `infra/04-david.sh`, `duel/genlingo_duel/cloud_auth.py`, `duel/genlingo_duel/main.py` |

## Decisions

### David in the cloud

Everything runs on Google Cloud (`ai-experiments-487722`); the stage laptop only opens the page.

| Component | Where | Why |
| --- | --- | --- |
| **The page** (FastAPI + one HTML page) | Cloud Run, `us-central1`, public, `min-instances=0` | A URL any browser opens, nothing to install. It serves its own fonts: nothing is fetched from another site. Its service account (`genlingo-page`) may only call Vertex AI and David. |
| **David** (Ollama with the fine-tuned Gemma and EmbeddingGemma) | Cloud Run with 1 NVIDIA L4, 4 vCPU and 16 GiB, `europe-west4`, private, `min-instances=0`, `max-instances=1` | The small model of our own: a server that runs only him. `europe-west4` because that's where the project has L4 quota (the same region as training). The model, the embedding model and the already compiled CUDA kernels are inside the image (`david/Dockerfile`), so starting downloads and compiles nothing. He serves up to 16 translations at a time. Only the page can call him (`roles/run.invoker`, identity token). |
| **Goliath** (Gemini) | Vertex AI, `GOOGLE_CLOUD_LOCATION=global`, `low` thinking | As anyone would use it: without David's glossary. |

**Measured on 2026-10-06 and 2026-10-07:**

- **With the GPU on**, David answers in ~0.6 s through the page, glossary included (median 0.6 s and p95 0.8 s, one at a time; [Time and cost in the cloud](../README.en.md#time-and-cost-in-the-cloud)). Goliath took a median of 3.2 s and up to 13 s, and sometimes Vertex AI answered «429 resource exhausted»: the page retries up to 3 times with a short wait and gives it up to 30 s.
- **Starting the GPU from zero** and getting him fast takes **about 35 seconds**: with the page and David off, `POST /api/david/wake` answered «ready» after 35 s (2026-10-07). It used to take 214–224 s. We measured where the time went:
  - **Compiling CUDA kernels (most of it).** Ollama ships its kernels as PTX for the L4, and the driver compiled them on every start: 60 s for the model's warm-up, 22–28 s for EmbeddingGemma's, and 3 to 9 s for the first phrase of each new shape (the slow phrases seen in the first minutes). Now they're compiled once on an L4 (`infra/07-david-jit-cache.sh`, 138 MB) and ship inside the image (`CUDA_CACHE_PATH`): both warm-ups dropped to 0.3 s and one translation's p95 from 3.6 s to 0.8 s.
  - **Reading the model in pieces.** Cloud Run pulls the image as it's read, and llama.cpp touched the GGUF piece by piece. `david/start.sh` reads the GPU libraries and the 4.2 GB of models in one go, in parallel, while Ollama starts (16–18 s), and loads both models before the first call.
  - **What's left:** ~2 s for Cloud Run to start the container, ~10 s of Ollama looking for the GPU, ~17 s reading the models and a few seconds of the page. The instance is ready 26–28 s after it starts.

  That's why the page wakes him when it opens, shows «Preparando a David…» with a clock and keeps him on with one call a minute while it's open, visible and used in the last 45 minutes.
- **Spending limits.** The page is public and every translation costs money: per connection, up to 60 translations and 12 wake-ups per minute; for the whole page, up to 1,500 Gemini calls and 24 starts of David per day (`duel/genlingo_duel/limits.py`, `LIMIT_*` in `.env`). Past them it answers 429 with a Spanish message the page shows. A talk stays far below. The counters live in each page instance's memory (up to 3), so the real ceiling is three times that. No reCAPTCHA or App Check: with these caps the most a day can cost is about $5 of Gemini and a few hours of GPU.
- **Cost:** the GPU costs about **$1.05 per hour** while the instance is on (L4 $0.0001867/s + 4 vCPU + 16 GiB, with CPU always allocated, which Cloud Run requires with a GPU), and Cloud Run stops it about 15 minutes after the last call. One David translation takes ~0.5 s of that GPU (~$0.00015), and one Gemini translation cost between $0.00015 and $0.0035 that day; but at a talk's volume (tens of phrases) the hour it's on costs more than everything Gemini charges for the same phrases. At volume it flips: one GPU serves tens of thousands of translations per hour. The page shows both sides' cost per translation, and the measured projections (when each one pays off) are in the README, [Time and cost in the cloud](../README.en.md#time-and-cost-in-the-cloud).

Ruled out: keeping David always on (`min-instances=1`) so there's no wait. That's ~$750 a month for a demo used a few hours.

### What else runs in the cloud

- **Training**: two Cloud Run Jobs in `europe-west4` (L4 to train, CPU to merge and convert to GGUF); image built with Cloud Build into Artifact Registry `charlas2027`.
- **Eval**: a Cloud Run Job with an L4 in `europe-west4` (`infra/06-eval-job.sh`, `evals/Dockerfile`). It runs Ollama inside the job, loads each model from the models bucket (mounted read-only) one at a time, warms it up with translations that don't count until three in a row take under 1.5 s, and deletes it before the next (the job's disk lives in its memory), calls Gemini and leaves the report in the staging bucket; `make eval` copies it into `evals/`.
- **Latency in the cloud eval:** in a 30-phrase test with the page's David in the job, most took 0.2–0.3 s, but 12 took 3 to 13 s, always the same phrases on every repeat. So the README's latencies are still those of the Mac eval (2026-10-04) and there is no new full eval in the cloud. The likely cause is the same one David had at start (CUDA kernels compiled the first time they're used, see above): the eval job doesn't carry the compiled kernels.
- **Models bucket** (`ai-experiments-487722-genlingo-models`): one GGUF per David, with its Modelfile and `metrics.json`. David's image and the eval's models come from there.

### Why two Cloud Run Jobs

One retrain a month doesn't justify anything running between runs. Cloud Run Jobs are serverless, billed per second while the task runs, and use the same kind of image as everything else. `make train` chains two jobs from the same image (`infra/03-train-job.sh`):

| Job | Machine | What it does |
| --- | --- | --- |
| `genlingo-train` | 1× L4, 8 vCPU, 32 GiB | Trains the LoRA adapter and saves it to the bucket volume (`ADAPTER_ONLY=1`). |
| `genlingo-finish` | CPU only, 8 vCPU, 32 GiB, 10 GiB ephemeral disk | Merges the adapter, converts to GGUF f16, quantizes to `QUANT` (Q5_K_M) and publishes to the models bucket (`train/finish.py`). |

`train/submit_job.py` waits for both, computes each one's cost from the per-second GPU, vCPU and memory rates, and writes the per-stage detail and the total to `train/runs/<tag>.json`.

Why split it: Cloud Run's filesystem lives in the instance's memory. Training, saving a 10 GB merged checkpoint and writing a 9 GB f16 GGUF don't fit together in 32 GiB: run `genlingo-2026-10b-e2b` (`zct96`) died of memory while converting to f16, and E4B had already failed the same way while merging. The CPU job holds nothing from training: the base weights are copied from the bucket with one sequential read (memory-mapping them from the bucket mount ran at ~5 MB/s), the merge runs in a child process (its ~10 GB go back when it exits), the merged checkpoint goes to the in-memory disk, the f16 GGUF goes to the ephemeral disk (disk-backed, not memory) and the checkpoint is deleted before quantizing. And the GPU isn't billed while merging and converting. Base weights are cached on a Cloud Storage volume shared by both jobs; the GGUFs don't go there because the converter writes out of order and the bucket mount ran at ~3 MB/s (cancelled runs `kcwqz` and `kqlxv` in `train/runs/failed/`).

Ruled out: Google Cloud Batch with one L4 and a persistent disk. It solved memory in a single step, but adds another API, a VM image with drivers and another set of permissions, while two jobs reuse the image, the service account and the bucket that already existed.

Available alternatives: a Vertex AI Custom Job with the same container and a 200 GB disk (`TRAIN_RUNTIME=vertex`, all in one step), and the `train/genlingo.ipynb` notebook for Colab. Early on, training also ran on the Mac (36.9 min for 1,000 pairs on MPS; on the L4, the training phase for the same size took 5.8 min); that path was removed on 2026-10-06, when everything moved to the cloud.

The monthly cycle, from data to the page and back (labels in Spanish):

![Monthly cycle](diagrams/ciclo-mensual.png)

### E4B didn't fit the CPU job

E4B's merged checkpoint (16 GB) plus the model in memory don't fit in the CPU job's 32 GiB. On 2026-10-01 that merge was finished on the 64 GB Mac with the same `train/finish.py`; that laptop fallback was removed on 2026-10-06. If it's ever needed again, `TRAIN_RUNTIME=vertex` runs training and merge in a single Vertex AI Custom Job with a 200 GB disk. E4B never reached the page: with 67% slang handled and a p50 of 836 ms it doesn't beat the E2B f16.

### Quantization: why Q5_K_M

Sweep of 2026-10-01 over the exports of `genlingo-2026-10-e2b`, all with the same glossary prompt, on that day's test set (319 pairs). imatrix was calibrated on training pairs, never on the test set. It ran on the Mac with llama.cpp (the script, `train/quant_sweep.py`, was removed on 2026-10-06 and is in the git history; the summary stayed in `evals/quant_sweep.json`). Per-phrase results in `evals/results/20261001-152529.json` (not in the repo); the full table is in the history of `evals/report.md` (commit `bb3f9fb`).

| Quantization | imatrix | Size | Slang handled | Reference-change recall | chrF++ | p50 |
| --- | --- | --- | --- | --- | --- | --- |
| Q4_K_M | no | 3.42 GB | 67% | 13% | 51.2 | 496 ms |
| Q4_K_M | yes | 3.42 GB | 72% | 14% | 51.6 | 539 ms |
| **Q5_K_M** | no | 3.62 GB | **76%** | 14% | 51.5 | 587 ms |
| Q5_K_M | yes | 3.62 GB | 75% | 15% | 52.2 | 624 ms |
| Q6_K | no | 3.83 GB | 74% | 15% | 51.9 | 527 ms |
| Q8_0 | no | 4.95 GB | 75% | 14% | 51.9 | 532 ms |
| f16 | — | 9.27 GB | 75% | 15% | 51.9 | 534 ms |

The rule (the same as in `evals/report.py`): the smallest file within 2 points of the f16 on slang handled, with p50 < 1 s. Q4_K_M loses 8 points against the f16; imatrix wins back 5 (72%) but is still 3 below. Q5_K_M is the smallest that loses no slang, for 0.2 GB more than Q4_K_M; Q6_K and Q8_0 are bigger without being better. That is why `.env` sets `QUANT=Q5_K_M` for `make train` and the page's David is Q5_K_M. The 2026-10-04 eval (399 phrases) repeats the result: Q4_K_M 67%, Q5_K_M 74% and f16 74% with `genlingo-2026-10-e2b`; Q5_K_M 82% and f16 81% with `genlingo-2026-10b-e2b`.

### The glossary prompt

The country prompt starts with the country ("Variante: español de Guatemala. Usa solo expresiones de Guatemala…") because "chido" and "chilero" are the same word in different places. It ends with a glossary from the term bank, country-specific or neutral. The page's David uses the `lexicon` style: six entries, each source-generation term that appears in the phrase with its counterpart validated by meaning (`data/counterparts.jsonl`; with no counterpart, its meaning), the closest other-generation terms according to EmbeddingGemma and one from another country marked "NO de aquí" (not from here). Davids from earlier rounds use the `glossary` style: four entries without counterparts, first the terms that appear verbatim in the phrase, then the closest ones. Retrieval time is added to David's latency.

David is trained on exactly that format (`make train-data` uses the `lexicon` style by default) and the page reads from `train/runs/<tag>.json` which prompt each David was trained with: there is no gap between training and the page. Goliath gets the country prompt, without a glossary, by default (`GOLIATH_PROMPT_STYLE`), because the bank is David's data; `make eval` also runs Goliath with the same glossary, which shows how much of the result is the model and how much is the data.

### The test set is web-only, never synthetic

A reference written by Gemini would reward Goliath for sounding like itself. The test pairs come from real sentences found on the web (two research rounds, 522 candidates); the reference is written by the curator from the meaning the source gives, and `scripts/validate_test_set.py` validates it against the term bank with no human involved: 399 are `auto_validated`. It also rejects any test pair that appears in a training file (synthetic, real or audience), even inside a longer sentence: raw and normalized substring matching (`duel/genlingo_duel/overlap.py`). The second round is split by a stable hash of the id: half goes to test and half to training pairs anchored in real sentences (`make real-pairs`), with no sentence shared. The `Pair` schema rejects any synthetic pair in the test split. The schema accepts `origin=human` pairs (sent by the audience app of an earlier version of the demo, which no longer exists; none are left in the data): they would be split 80/20 between training and test by a stable hash of the id.

### EmbeddingGemma: where it's used and why version 1 stays

**Where it's used:** only for the lexicon in David's prompt. For each phrase, EmbeddingGemma turns the phrase and every slang term in the bank into vectors and picks the closest terms; those go into David's prompt as hints (`duel/genlingo_duel/glossary.py`, `lex_entries`). Terms that appear verbatim in the phrase are found by text, without embeddings. It runs on David's own service, in the cloud; nothing runs on the laptop. Goliath doesn't use it.

**Why version 1 stays** (`embeddinggemma`, 300M):

- **It works better.** In Tzij, the talk's other demo, EmbeddingGemma 2 gave worse translations than version 1 on the same retrieval task: chrF++ 38.8 vs 39.9 on dev and 23.9 vs 25.8 on general translation.
- **In Genlingo it can't be used yet.** Tried on 2026-10-07 with the same dev eval: Ollama 0.35 (David's) doesn't know its architecture (`unknown model architecture: 'gemma-embedding2'`), and Ollama 0.40, the first one that ships it (`embeddinggemma-2:270m` to `:740m`), only runs it on Apple Silicon (MLX); on Cloud Run's GPU it fails (`MLX not available`).
- **David was trained with version 1's lexicon.** Changing the model changes what David receives, so it would only change if an eval showed it equal or better. Dev baseline with version 1 (146 pairs, 2026-10-07): correct slang 33 %, slang handled 85 %, chrF++ 63.3.

### Dated Gemini price schedule

Prices change, and that is part of the story. `GEMINI_PRICE_SCHEDULE=2026-09-30:0.75/3.75,2027-01-01:1.50/7.50` is a list of prices by date: every translation and every eval uses the price in force that day and records which one it used. The report also shows what the same eval would cost at the 2027 price ($2.26 per 1,000 phrases instead of $1.13). Thinking tokens are billed as output. The page shows each translation's cost: Gemini's at the day's price and David's as the GPU seconds it used ([David in the cloud](#david-in-the-cloud)). Exports of one training run (`-f16`, `-q5_k_m`) share its `train/runs/<tag>.json`.

### How the page compares

- **Temperature 0 on both sides**, as in `make eval`: the page shows what the eval measured and the same phrase always gets the same answer. At temperature 0.2, in one test David turned «chafa» into «muy regular» (wrong).
- **Side by side, no winner.** Both get the same phrase at the same time (`POST /api/translate/david` and `/api/translate/goliath`); each column fills when it answers and shows its time and cost. No rounds, scoreboard or votes. Goliath gets the country prompt, without David's glossary, as anyone would use it.
- **The term-by-term check** (`duel/genlingo_duel/term_check.py`) uses the eval's *correct slang* rules, one term at a time. Gen Z → parents: the Gen Z term is gone and its meaning (or its counterpart, or the word the human reference used) is in the translation. Parents → Gen Z: the parents' term was replaced by its validated Gen Z counterpart or an equivalent. It applies to any phrase: for the examples the word the human reference used also counts; for a typed phrase, only the bank. If a typed phrase has no slang the bank knows, the page says so instead of grading.
- **The examples** (`data/translate_examples.json`) are Guatemalan phrases from the test set. The 51 the check can judge were run live, 3 times with each model; the ones kept are those David got right and Goliath wrong all 3 times, where a person sees the same as the check. With David already in the cloud they were run 3 more times: 12 of 12 for David, 0 for Goliath. `make check` translates them again with both on the live page.
- **David wakes on his own.** `POST /api/david/wake` starts David's instance (the first call waits for it), loads both models and answers once they're ready; `GET /api/status` gives the state and the seconds so far, for the page's clock.

## Results

Eval of 2026-10-04 on 399 `auto_validated` web test pairs (out of 522 candidates; 123 rejected by the automatic validation, 4 of them for appearing inside a training pair). Every Ollama model with the prompt it was trained on, one at a time on an M1 Max (the eval now runs in a Cloud Run Job with an L4: `make eval`); Goliath at temperature 0 (2 errors with glossary). *Correct slang* (amendment 1 of [evals/niche.md](../evals/niche.md)): the term produced means the same, according to the counterpart table validated by meaning.

| Variant | Correct slang | Slang handled | Gen Z → parents | parents → Gen Z | Reference-change recall | chrF++ | p50 | Cost / 1,000 phrases (eval) | Size |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Copy the phrase (baseline) | 1% | 1% | 0% | 3% | 0% | 53.2 | — | — | — |
| `gemma4:e2b-it-qat` (base) | 14% | 58% | 95% | 10% | 14% | 50.2 | 364 ms | $0 | 4.34 GB |
| `gemma4:e2b-it-qat` + glossary | 38% | 62% | 94% | 20% | 23% | 55.0 | 452 ms | $0 | 4.34 GB |
| `gemma4:e4b` (base) | 19% | 68% | 97% | 31% | 17% | 48.2 | 802 ms | $0 | 6.58 GB |
| `genlingo-2026-09` (Q4, plain prompt) | 18% | 62% | 94% | 20% | 14% | 55.0 | 391 ms | $0 | 3.42 GB |
| `genlingo-2026-10-e2b` + glossary (Q4) | 25% | 67% | 95% | 31% | 16% | 55.7 | 512 ms | $0 | 3.42 GB |
| `genlingo-2026-10-e2b-q5_k_m` + glossary (previous David) | 27% | 74% | 97% | 43% | 18% | 55.4 | 564 ms | $0 | 3.62 GB |
| `genlingo-2026-10-e2b-f16` + glossary | 28% | 74% | 99% | 42% | 19% | 56.3 | 566 ms | $0 | 9.27 GB |
| `genlingo-2026-10b-e2b` + glossary (Q5_K_M, round 2) | 34% | 82% | 99% | 59% | 22% | 56.6 | 557 ms | $0 | 3.62 GB |
| `genlingo-2026-10b-e2b-f16` + glossary | 34% | 81% | 98% | 59% | 22% | 56.7 | 543 ms | $0 | 9.27 GB |
| `genlingo-2026-10c-e2b-nomulti` + lexicon (Q5_K_M, round 3) | 42% | 82% | 100% | 58% | 28% | 59.7 | 670 ms | $0 | 3.62 GB |
| **`genlingo-2026-10d-e2b` + lexicon (Q5_K_M, on the page; 2026-10-07 eval in the cloud)** | **44%** | **80%** | 100% | 54% | 28% | **60.0** | 237 ms | **$0** | 3.62 GB |
| Goliath `gemini-3.8-flash` | 26% | 77% | 97% | 51% | 25% | 53.5 | 2.60 s | $1.13 | — |
| Goliath + the same glossary | 38% | 82% | 100% | 58% | 29% | 57.0 | 3.05 s | $1.27 | — |

**Reading the results** (2026-10-04 eval, round 3; round 4's is in [evals/report.md](../evals/report.md)). Phrase by phrase, David produces the correct slang and Goliath doesn't in 101 phrases; the other way round, in 36. Against Goliath with the glossary the count narrows (79 against 63) and the whole set is a tie; David still wins on Guatemalan slang and parents → Gen Z, and Goliath wins on neutral Spanish (LATAM). On *slang handled* (the register changed, regardless of meaning) David and Goliath tie, and David still slips in another country's slang in 16 of 173 parents → Gen Z phrases (Goliath: 3). This round's jump is in meaning: the round-2 David already handled 82%, but got the term right in 34%. David wins on speed and wins on correct slang as long as the term bank, the counterparts and the real sentences are his alone. chrF++ stays close to the copy baseline (53.2) because a register rewrite keeps almost every word: it can't decide who translated the slang. The per-niche CIs are in [evals/niche_report.md](../evals/niche_report.md).

David's ten worst losses (among open-source phrases) and the per-country and per-direction breakdowns are in [evals/report.md](../evals/report.md). The first version of the data (free paraphrase) left David *below* the base model (chrF++ 39.1): it is documented in [evals/experiments/2026-09-parafrasis-libres.md](../evals/experiments/2026-09-parafrasis-libres.md).

![The comparison page with «Voy a comprar algo de refacción para media mañana»](demo/03-comparar-papas-a-genz.png)

David says «refa», as Gen Z says it in Guatemala, and gets the term right; Goliath writes «munchies para el bajón» and doesn't.

## Training cost per run

Cloud Run Jobs in `europe-west4`: training on 1× NVIDIA L4 without zonal redundancy, 8 vCPU, 32 GiB; since `genlingo-2026-10b-e2b`, merge + GGUF on a separate CPU job (8 vCPU, 32 GiB). Cost = billed seconds × per-second rates (`CLOUD_RUN_*_USD_PER_S` in `.env`), per stage.

| Run | Base | Pairs | Outcome | Duration | Cost |
| --- | --- | --- | --- | --- | --- |
| `genlingo-2026-09` | E2B | 1,000 (minimal edits) | done (loss 2.33 → 0.14) | 17.4 min | $0.41 |
| `genlingo-2026-10-e2b` | E2B | 1,500 (anchored on the bank) | done (loss 2.26 → 0.12) | 28.2 min | $0.67 |
| `genlingo-2026-10-e4b` | E4B | 1,500 (anchored on the bank) | trained; out of memory while merging → merge finished on the Mac | 41.3 min | $0.98 |
| `genlingo-2026-10b-e2b` | E2B | 1,709 (1,375 synthetic + 334 anchored in real sentences) | done in the cloud, two jobs (loss 2.62 → 0.16): train 25.3 min $0.60 + merge/GGUF Q5_K_M and f16 9.0 min $0.11 | 34.3 min | $0.71 |
| `genlingo-2026-10c-e2b` | E2B | 2,972 (2,416 synthetic, 701 of them with 2–3 terms, + 556 anchored in real sentences) | done (loss 2.19 → 0.04): train 54.0 min $1.28 + merge/GGUF 10.3 min $0.13; left out for latency (p50 1.99 s on dev) | 64.2 min | $1.41 |
| `genlingo-2026-10c-e2b-nomulti` | E2B | 2,271 (1,715 synthetic + 556 anchored in real sentences) | done, round 3 (loss 1.97 → 0.06): train 35.7 min $0.85 + merge/GGUF 10.2 min $0.13 | 45.9 min | $0.97 |
| `genlingo-2026-10d-e2b` | E2B | 3,880 (3,315 synthetic, 1,600 of them Gen Z of Mexico and neutral Spanish, + 565 anchored in real sentences) | done, **on the page**: training and merge/GGUF in two jobs | 67.5 min | $1.49 |
| `genlingo-2026-10c-e2b-nomulti-orpo` | E2B | 264 preference pairs on the nomulti adapter | done: sampling + ORPO 18.4 min $0.44 + merge/GGUF 9.9 min $0.12; left out (parents → Gen Z slang dropped on dev) | 28.3 min | $0.56 |
| `failed/genlingo-2026-10b-e2b-zct96` | E2B | 1,709 | trained; killed for memory converting to GGUF f16 in the single job → led to the split into two jobs | 26.8 min | $0.63 |
| `failed/genlingo-2026-10c-e2b-nomulti-orpo-8995k` | E2B | 2,271 | timed out: the model was loaded on the CPU for sampling | 60.4 min | $1.43 |
| `failed/genlingo-2026-10c-e2b-nomulti-orpo-jwt8d` | E2B | 2,271 | out of memory on the L4: with batch 4 Gemma's logits didn't fit (now batch 1 × 16) | 16.2 min | $0.38 |
| `failed/genlingo-2026-09-nv5r5` | E2B | 1,000 | failed at start (`gcc` missing for Triton) | 10.9 min | $0.26 |
| `failed/genlingo-2026-09-kcwqz` | E2B | 1,000 | cancelled: GGUF written to the bucket mount, too slow | 31.2 min | $0.74 |
| `failed/genlingo-2026-09-kqlxv` | E2B | 1,000 | cancelled at ~28 min (same cause, on read) | — | not recorded |
| `experiments/genlingo-2026-09-parafrasis` | E2B | 1,000 (free paraphrase) | laptop, MPS | 36.9 min | $0 |

Generating 1,500 synthetic pairs with Gemini costs under $1 ($0.71 and about 10 min in round 3, `data/pairs/synthetic.meta.json`). A monthly E2B retrain, train → GGUF all in the cloud, costs under $1. Serving David costs whatever time his GPU is on (~$1.05 per hour, [David in the cloud](#david-in-the-cloud)).
