# Genlingo — generational translator: Gen Z ↔ parents

Demo for the talk *"David vs. Goliath: how a small model beats a frontier model"*. «no manches, la peli estuvo bien chilera pero el final me dio cringe» ↔ «la película estuvo bien chévere pero el final me dio pena ajena». **David** is Gemma 4 E2B fine-tuned with LoRA on our own pairs and runs with Ollama on a GPU server of his own (Cloud Run, NVIDIA L4). **Goliath** is Gemini (`GEMINI_MODEL`, today `gemini-3.8-flash`) on Vertex AI. Everything runs in the cloud: the laptop only opens a page.

[Versión en español](README.md)

## The demo: David and Goliath side by side

One public page on Cloud Run: **https://genlingo-611681112050.us-central1.run.app**. Nothing to install or run on talk day: open the page a few minutes before and that's it.

- Pick the direction (Gen Z → parents or parents → Gen Z), type a phrase or tap an example, and both translate the same phrase at the same time. Each column shows its translation, how long it took and what it cost ([how it's computed and when each one pays off](#time-and-cost-in-the-cloud)).
- Under each column, each slang word in the phrase with ✓ (translated with its meaning) or ✗, per our slang bank. For the examples, also the human reference translation. If a typed phrase has no slang the bank knows, the page says so instead of grading.
- At the bottom, «¿Cómo se lee esta página?» explains ✓/✗, time and cost in plain words. The page works on a projector, a laptop and a phone.
- David shuts down on his own when nobody uses him, so nothing bills between talks. When the page opens, the top right says «Preparando a David…» with a clock while his GPU starts; from zero it takes about 35 seconds ([measured](docs/DECISIONES.en.md#david-in-the-cloud); it used to be almost 4 minutes). Once it says «David listo» everything answers right away, and the page keeps him on while it stays open.

![The comparison page: David and Goliath translate «No tengo pisto, préstame unas baras»](docs/demo/02-comparar-genz-a-papas.png)

The five examples are test-set phrases (David never saw them in training), from openly licensed sources: three combine two Guatemalan terms («No tengo **pisto**, préstame unas **baras**»), one is from Mexico («de **partir la madre**») and one goes parents → Gen Z. They were run live, 3 times with each model, with the page's David (`genlingo-2026-10e-e2b`): of the 96 showable test phrases, 18 passed the automatic check and, read one by one, 5 hold up. Colombia and neutral Spanish have no example: in the ones that passed, Goliath said something correct that the bank doesn't recognize ([details](evals/experiments/2026-10-07-ejemplos-ronda5.md), Spanish). Each example, with its source, license and the answers of every run, is in [`data/translate_examples.json`](data/translate_examples.json). The script is in [docs/DEMO.en.md](docs/DEMO.en.md): first a slang word from all over the internet («cringe»), where they tie, then local slang and combinations, where David wins.

![What runs where: the page, David and Goliath in the cloud](docs/diagrams/arquitectura.png)

## What you'll learn

1. **Your own data with `origin`:** every pair says where it came from (`web`, `synthetic` or `human`); without that you can't evaluate or retrain monthly.
2. **Term bank and real sentences:** 734 terms from 133 sources, meaning-validated counterparts and 1,138 pairs anchored in real sentences; David's edge is his data. Sentences from sources that can't be redistributed live in a private bucket, not in the repo ([data/SOURCES.md](data/SOURCES.md)).
3. **LoRA on Cloud Run Jobs:** an L4 trains and a CPU job merges and exports GGUF; each run records its duration and cost.
4. **The cost of compression:** f16 vs Q4_K_M, Q5_K_M, Q6_K, Q8_0 and imatrix, in size, latency and lost slang.
5. **Evals with term metrics:** chrF++ plus *correct slang*, *slang handled* and *reference changes*, with a separate dev set for decisions and niches defined before looking at results.
6. **Your model on your own GPU:** David runs with Ollama on Cloud Run with an L4, private, and scales to zero between talks; the page wakes him when it opens. Training, evaluating and serving: all in the cloud, nothing on the laptop.

## The metrics, in plain words

No model grades another: every metric is computed by a program with fixed rules.

- **Correct slang** (*jerga correcta*; the main one, and what the page shows as ✓ Bien and ✗ Mal): for each slang word in the phrase, did the translation replace it with something that means the same? The program uses our slang bank (734 terms, each with its meaning, country and source) and a meaning-validated counterpart table (`data/counterparts.jsonl`).
  *Example:* «esa tu tarea te quedó bien **chafa**» (chafa = poor quality). «Esa tarea tuya te quedó muy mala» → ✓. «Esa tu tarea te quedó bien pura lata» → ✗: it swapped one slang word for another that doesn't mean the same.
- **Slang handled** (*jerga resuelta*): did the register change? Gen Z → parents: no Gen Z bank slang is left; parents → Gen Z: the translation uses at least one Gen Z term of the country. It doesn't check whether the meaning is right, so it isn't the main one.
- **Reference changes** (*cambios acertados*): of the words the person changed when translating, how many appear unchanged in the model's translation.
- **chrF++:** how similar the translation is to the one a person wrote, counting the chunks of letters and words they share: 0 is nothing in common and 100 is identical.
  *Example:* if the person wrote «esa tarea te quedó muy mal hecha», «esa tarea tuya te quedó muy mala» shares almost everything and scores high; «te quedó pura lata» shares little and scores low. In this task most words stay the same, so copying the phrase untranslated already scores 53.2: that's why chrF++ doesn't decide on its own.

Test-set numbers come from the eval of the night of 2026-10-07 (every model with the round-5 bank and the term-by-term check) on 399 `auto_validated` web phrases David never saw, run in the cloud (Cloud Run with an L4, the same GPU as the page; [evals/report.md](evals/report.md)), unless another date is given. The page's time and cost are measured separately ([Time and cost in the cloud](#time-and-cost-in-the-cloud)).

## Final result

| | Correct slang | Slang handled | chrF++ | p50 (eval) |
| --- | ---: | ---: | ---: | ---: |
| **David** (`genlingo-2026-10e-e2b`, Q5_K_M, 3.62 GB) | **58 %** | **81 %** | **60.7** | **253 ms** |
| Previous David (`genlingo-2026-10d-e2b`) | 54 % | 78 % | 59.8 | 256 ms |
| Goliath `gemini-3.8-flash` | 34 % | 77 % | 53.2 | 3.49 s |
| Goliath with David's lexicon (reference) | 48 % | 81 % | 56.9 | 3.28 s |
| Copy the phrase (baseline) | 1 % | 1 % | 53.2 | — |

- **Correct slang:** +24.1 points over Goliath (95 % CI [+18.6, +29.6]). 126 phrases only David gets right and 30 only Goliath.
- **Slang handled:** +4.0 [−0.3, +8.3], a statistical tie.
- **chrF++:** 60.7 against 53.2 for Goliath and 56.9 for Goliath with the lexicon.
- **Goliath's cost:** $1.22 per 1,000 phrases in that eval; $2.43 at the price from 2027-01-01.

### Phrases with several slang terms (round 5)

The hypothesis: Goliath knows many terms on their own, but when a phrase combines several from the same country, David, trained on that country, can win. The «Combinations» niche was registered before gathering data and training ([evals/niche.md](evals/niche.md), amendment 2): 174 real web phrases with 2 or more terms from the frozen bank, in both directions (91 from the test set and 83 from new sentences set aside before running any model). Correct slang, 95 % CI by paired bootstrap ([evals/report_combos.md](evals/report_combos.md)).

| Slice | n | David | Goliath | Δ | 95 % CI | Verdict |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| **Combinations** | 174 | **62 %** | 45 % | +16.7 | [+7.5, +25.9] | **David wins** |
| Gen Z → parents | 78 | 63 % | 33 % | +29.5 | [+15.4, +43.6] | David wins |
| Parents → Gen Z | 96 | 61 % | 55 % | +6.2 | [−5.2, +17.7] | tie |
| Mexico | 67 | 66 % | 52 % | +13.4 | [−1.5, +26.9] | tie |
| Colombia | 46 | 52 % | 33 % | +19.6 | [+0.0, +39.1] | tie (bound at 0) |
| Neutral Spanish | 39 | 72 % | 64 % | +7.7 | [−10.3, +25.6] | tie |
| Guatemala | 22 | 55 % | 18 % | +36.4 | [+9.1, +63.6] | n < 30, no verdict |

- **The previous David lost here:** `10d` scored 39 % against 45 % for Goliath (−6.3 [−16.7, +3.4]); it lost in Mexico and neutral Spanish. Round 5 added 23 points.
- **Against Goliath with the same lexicon:** 62 % vs 61 %, a tie. With the same data the big model catches up with David on combinations; without it, it doesn't.

### By country and direction (correct slang, David vs Goliath without glossary)

Niches from [evals/niche.md](evals/niche.md); 95 % CI by paired bootstrap ([evals/niche_report.md](evals/niche_report.md), [evals/report_combos.md](evals/report_combos.md)).

| Slice | n | David | Goliath | Δ | 95 % CI | Verdict |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Guatemalan slang (GT) | 115 | 61 % | 18 % | +42.6 | [+32.2, +53.0] | David wins |
| Parents → Gen Z (GT/CO) | 107 | 33 % | 15 % | +17.8 | [+6.5, +29.0] | David wins |
| Country CO | 131 | 53 % | 28 % | +24.4 | [+14.5, +34.4] | David wins |
| Country MX | 77 | 65 % | 48 % | +16.9 | [+5.2, +28.6] | David wins (with `10d`, a tie) |
| Country LATAM (neutral Spanish) | 75 | 55 % | 52 % | +2.7 | [−9.3, +14.7] | statistical tie |
| Gen Z → parents | 226 | 77 % | 41 % | +36.3 | [+29.2, +43.4] | David wins |
| Parents → Gen Z | 172 | 32 % | 24 % | +8.1 | [−1.2, +16.9] | statistical tie |
| Whole set | 398 | 58 % | 34 % | +24.1 | [+18.6, +29.6] | David wins |

- **Gen Z → parents, David wins in all four countries:** Mexico 84 % vs 51 %, Colombia 71 % vs 37 %, neutral Spanish 80 % vs 64 % and Guatemala 80 % vs 22 %.
- **Parents → Gen Z:** he wins in Guatemala (37 % vs 14 %); ties in Mexico (48 % vs 45 %) and Colombia (29 % vs 16 %); in neutral Spanish he loses (4 % vs 28 %, 25 phrases).
- **Against Goliath with the same lexicon:** David wins on the whole set (58 % vs 48 %, +9.8 [+4.3, +15.5]), in Guatemala and in Colombia; ties in Mexico and neutral Spanish.

### Slang from all over the internet: a tie

With general Gen Z slang (cringe, random, crush, stalkear, funar, mid, delulu…) David and Goliath tie. It's measured with a separate probe ([evals/report_probe.md](evals/report_probe.md), `make eval-probe`): 32 real sentences from 14 pages never used for training, in both directions.

| | As neutral Spanish | As Guatemala |
| --- | ---: | ---: |
| `10c` (round 3) | 91 % | 69 % |
| `10d` (round 4) | 91 % | 73 % |
| **`10e` (round 5, on the page)** | **88 %** | **69 %** |
| Goliath | 94 % | 69 % |

Any big model already knows that slang. David's edge is in the slang of a country the big model knows little about and in phrases that combine several terms from that country. The demo starts there: «cringe» is a tie, «pisto» and «baras» in the same phrase are not.

### chrF++ by country and by direction

| | CO | GT | LATAM | MX | Gen Z → parents | Parents → Gen Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| David | 61.0 | 66.7 | 57.9 | 54.4 | 69.5 | 48.5 |
| Goliath | 52.4 | 52.5 | 57.4 | 51.0 | 60.1 | 43.4 |
| Goliath + lexicon | 55.0 | 60.4 | 58.8 | 53.2 | 63.1 | 48.2 |

## Time and cost in the cloud

<!-- projections: make projections -->
Measured on 2026-10-07 with `make capacity` ([`scripts/bench_capacity.py`](scripts/bench_capacity.py) → [`docs/data/capacity.json`](docs/data/capacity.json)): 48 test-set phrases, with the page's own code, against the Cloud Run David (1 NVIDIA L4) and against Gemini. `make projections` writes the tables from that file.

**Time per translation** (from the request to the answer)

| | Median | p95 | Translations per hour |
| --- | ---: | ---: | ---: |
| David, 1 at a time | 0.6 s | 0.8 s | 4,114 |
| David, 4 at a time | 0.8 s | 1.1 s | 16,499 |
| David, 8 at a time | 1.0 s | 1.3 s | 25,984 |
| David, 16 at a time | 1.7 s | 2.3 s | 29,586 |
| Goliath (Gemini) | 3.2 s | 12.9 s | no limit of its own |

David is faster in every case measured: his median with 16 translations at a time (1.7 s) is still below Goliath's (3.2 s). Of the 48 Gemini calls, 2 failed because Vertex AI was saturated (429); the page retries on its own.

**Cost.** David's GPU is billed by the second while it's on, whatever it does: R = L4 + 4 vCPU + 16 GiB ≈ **$1.05 per hour**. Gemini bills by token: in the measurement each translation used 125 input and 298 output tokens on average (its reasoning included), so g ≈ **$0.0012** at today's price ($0.75 / $3.75 per million) and **$0.0024** from 2027-01-01 ($1.50 / $7.50).

- David per translation = R ÷ V, for V translations per hour. One GPU handles up to C = 29,586 per hour (the best measured, 16 at a time); beyond that, add GPUs: ⌈V ÷ C⌉ × R ÷ V.
- Goliath per translation = g, the same at any volume.
- Break-even: V = R ÷ g. Per month: 730 hours at that volume.

| Translations per hour | David's GPUs | David per translation | Goliath per translation (today) | Goliath (from 2027-01-01) | David per month | Goliath per month (today) | Goliath per month (from 2027-01-01) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 1 | $0.021 | **$0.0012** | **$0.0024** | $764 | **$44.26** | $88.51 |
| 500 | 1 | $0.0021 | **$0.0012** | $0.0024 | $764 | **$443** | $885 |
| 1,000 | 1 | **$0.0010** | $0.0012 | $0.0024 | **$764** | $885 | $1,770 |
| 5,000 | 1 | **$0.00021** | $0.0012 | $0.0024 | **$764** | $4,426 | $8,851 |
| 20,000 | 1 | **$0.000052** | $0.0012 | $0.0024 | **$764** | $17,702 | $35,404 |
| 50,000 | 2 | **$0.000042** | $0.0012 | $0.0024 | **$1,528** | $44,256 | $88,509 |

**Where David wins:** from about **863 translations per hour** at today's price and **432** at the 2027-01-01 one. With his GPU full, each translation costs **$0.000035**: 34 times less than Gemini today and 69 times less from 2027-01-01. A translator serving an organization all day is in that zone.

**Where Goliath wins:** at low volume. At a talk (about 50 phrases in an hour) the GPU costs ~$1.05 for that hour and Gemini ~$0.061 for the 50 phrases. That's why David shuts down on his own between talks: he costs nothing while nobody uses him.

On the page, David's cost is the GPU seconds that translation used (serving one at a time), and Goliath's is what Gemini billed for its tokens.
<!-- /projections -->

This measurement was made with `genlingo-2026-10d-e2b`, the previous David. `genlingo-2026-10e-e2b` is the same size (3.62 GB, Q5_K_M), runs on the same service and answers just as fast in the eval (p50 of 253 ms vs 256 ms), so it wasn't measured again.

## All the experiments

### Every variant on the test set (399 phrases, eval of the night of 2026-10-07 in the cloud)

Every model with the round-5 bank (734 terms) and the term-by-term check; that's why the earlier Davids' numbers don't match the ones published in their round.

| Variant | Correct slang | Slang handled (Gen Z → parents / parents → Gen Z / total) | Changes matched | chrF++ | p50 | Size | Training |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| Base `gemma4:e2b-it-qat` | 21 % | 94 % / 10 % / 58 % | 14 % | 50.3 | 152 ms | 4.34 GB | — |
| Base E2B + lexicon | 47 % | 98 % / 16 % / 62 % | 25 % | 55.0 | 228 ms | 4.34 GB | — |
| Base `gemma4:e4b` | 27 % | 98 % / 31 % / 69 % | 17 % | 48.2 | 222 ms | 6.58 GB | — |
| `genlingo-2026-09` (minimal edits, Q4_K_M) | 23 % | 93 % / 21 % / 62 % | 14 % | 54.9 | 155 ms | 3.42 GB | $0.41 |
| `genlingo-2026-10-e2b` + glossary (Q4_K_M) | 33 % | 96 % / 29 % / 67 % | 17 % | 55.9 | 199 ms | 3.42 GB | $0.67 |
| `genlingo-2026-10-e2b-q5_k_m` + glossary | 33 % | 97 % / 36 % / 71 % | 17 % | 55.6 | 216 ms | 3.62 GB | — |
| `genlingo-2026-10-e2b-f16` + glossary | 35 % | 98 % / 34 % / 70 % | 18 % | 56.3 | 360 ms | 9.27 GB | — |
| `genlingo-2026-10b-e2b` + glossary (Q5_K_M) | 41 % | 99 % / 53 % / 79 % | 23 % | 56.5 | 214 ms | 3.62 GB | $0.71 |
| `genlingo-2026-10c-e2b-nomulti` + lexicon (Q5_K_M) | 49 % | 100 % / 50 % / 78 % | 26 % | 59.0 | 249 ms | 3.62 GB | $0.97 |
| `genlingo-2026-10c-e2b-nomulti-f16` + lexicon | 49 % | 99 % / 54 % / 80 % | 28 % | 59.2 | 387 ms | 9.27 GB | — |
| `genlingo-2026-10d-e2b` + lexicon (Q5_K_M) | 54 % | 100 % / 50 % / 78 % | 28 % | 59.8 | 256 ms | 3.62 GB | $1.49 |
| `genlingo-2026-10d-e2b-f16` + lexicon | 53 % | 100 % / 53 % / 80 % | 27 % | 59.4 | 402 ms | 9.27 GB | — |
| **`genlingo-2026-10e-e2b` + lexicon (Q5_K_M)** | **58 %** | 100 % / 57 % / 81 % | 29 % | **60.7** | 253 ms | 3.62 GB | $1.44 |
| `genlingo-2026-10e-e2b-f16` + lexicon | 56 % | 100 % / 54 % / 80 % | 30 % | 60.9 | 394 ms | 9.27 GB | — |
| Goliath `gemini-3.8-flash` | 34 % | 97 % / 51 % / 77 % | 25 % | 53.2 | 3.49 s | — | — |
| Goliath + lexicon | 48 % | 100 % / 57 % / 81 % | 25 % | 56.9 | 3.28 s | — | — |
| Copy the phrase | 1 % | 0 % / 3 % / 1 % | 0 % | 53.2 | — | — | — |

Latencies are from an L4 in the cloud with Ollama (David answers one phrase at a time; Goliath four at a time). Earlier versions of this table are in `evals/report.md`'s history.

### Round 5 on the dev set (280 pairs, 69 of them with several terms; 2026-10-07)

Round 5 was decided here, with the rule registered before training: more correct slang on the dev combinations, without dropping more than 2 points on the whole dev set against `10d` and with p50 < 1 s ([evals/report_dev.md](evals/report_dev.md), [note](evals/experiments/2026-10-07-ronda5-combinaciones.md), Spanish).

| Variant | What it tests | Examples | Correct slang (dev) | On combinations (dev) | p50 | Training |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **`genlingo-2026-10e-e2b`** | all the new data, old synthetic pairs at 60 % | 4,321 | 58.1 % | **56.5 %** | 275 ms | $1.44 |
| `…-all` | everything, untrimmed (1.9 epochs) | 5,670 | 57.3 % | 49.3 % | 272 ms | $1.39 |
| `…-webonly` | only the new real sentences | 3,073 | 56.4 % | 47.8 % | 271 ms | $1.24 |
| `…-nocombo` | without the synthetic combinations | 3,673 | 53.1 % | 46.4 % | 273 ms | $1.44 |
| `…-v2` | like the winner, with the cleaned bank | 4,042 | 59.3 % | 52.2 % | 270 ms | $1.39 |
| `…-v2-nocombo` | `-v2` without synthetic combinations | 3,520 | 54.4 % | 40.6 % | 270 ms | $1.33 |
| `genlingo-2026-10d-e2b` | the previous David | — | 49.0 % | 34.8 % | 278 ms | — |
| Goliath | rival | — | 39.6 % | 35.3 % | 3.38 s | — |
| Goliath + lexicon | reference | — | 58.9 % | 59.4 % | 3.40 s | — |

### Round 3 on the dev set (146 pairs, 2026-10-04 eval)

Round 3 data decisions were made here, without looking at the test set ([evals/report_dev.md](evals/report_dev.md)). `10b` saw 70 of these pairs in training, so its number is optimistic.

| Variant | chrF++ | Slang handled | Ref. changes | Correct slang | p50 | Training |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `genlingo-2026-10b-e2b` (glossary; saw 70 of the 146) | 65.3 | 91 % | 34 % | 41 % | 592 ms | $0.71 |
| `genlingo-2026-10c-e2b` (lexicon, with 2–3-term pairs) | 61.9 | 86 % | 27 % | 36 % | 1.99 s | $1.41 |
| **`genlingo-2026-10c-e2b-nomulti`** (lexicon, without them) | **63.2** | 85 % | 25 % | 33 % | 809 ms | $0.97 |
| `genlingo-2026-10c-e2b-nomulti-orpo` (+ ORPO preferences) | 63.7 | 78 % | 26 % | 31 % | 866 ms | $0.56 |
| Goliath | 51.1 | 76 % | 18 % | 14 % | 3.60 s | — |
| Goliath + David's lexicon | 58.4 | 88 % | 33 % | 42 % | 3.10 s | — |

### Quantization sweep (2026-10-01, that day's 319 pairs, `genlingo-2026-10-e2b` with glossary)

| Quantization | imatrix | Size | Slang handled | Ref. changes | chrF++ | p50 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Q4_K_M | no | 3.42 GB | 67 % | 13 % | 51.2 | 496 ms |
| Q4_K_M | yes | 3.42 GB | 72 % | 14 % | 51.6 | 539 ms |
| **Q5_K_M** | no | 3.62 GB | **76 %** | 14 % | 51.5 | 587 ms |
| Q5_K_M | yes | 3.62 GB | 75 % | 15 % | 52.2 | 624 ms |
| Q6_K | no | 3.83 GB | 74 % | 15 % | 51.9 | 527 ms |
| Q8_0 | no | 4.95 GB | 75 % | 14 % | 51.9 | 532 ms |
| f16 | — | 9.27 GB | 75 % | 15 % | 51.9 | 534 ms |

### Each experiment, briefly

Details and dates in [docs/BITACORA.md](docs/BITACORA.md) (Spanish); technical decisions in [docs/DECISIONES.en.md](docs/DECISIONES.en.md).

1. **Base model: E2B vs E4B.**
   - *Tested:* which Gemma works untuned.
   - *Result:* E4B handles more slang (68 % vs 58 %; correct 19 % vs 14 %), but scores lower chrF++ (48.2 vs 50.2), is over twice as slow (802 ms vs 364 ms) and weighs 6.58 GB.
   - *Learned:* the rule picks the smallest with p50 < 1 s and the best chrF++: E2B. E4B's untuned edge was gone once fine-tuned (experiment 6).
2. **Glossary without fine-tuning.**
   - *Tested:* giving the E2B base the term-bank glossary in the prompt.
   - *Result:* correct slang goes from 14 % to 38 % and chrF++ from 50.2 to 55.0.
   - *Learned:* data matters before tuning.
3. **Free paraphrases** (2026-09-30, `genlingo-2026-09-parafrasis`).
   - *Tested:* training on synthetic pairs that rewrote the whole phrase.
   - *Result:* chrF++ 39.1, below the base (47.1) and below copying the phrase (50.0), on that day's 319-pair set.
   - *Learned:* David learned to rewrite everything; a pair must change only the slang ([details](evals/experiments/2026-09-parafrasis-libres.md), Spanish).
4. **Minimal-edit pairs** (`genlingo-2026-09`).
   - *Tested:* the same phrase with only the terms swapped.
   - *Result:* 62 % slang handled vs 58 % for the base, but parents → Gen Z only 20 %. Cost $0.41 (17.4 min of L4).
   - *Learned:* the hard direction needed teaching.
5. **Bank-anchored pairs + glossary in the prompt** (`genlingo-2026-10-e2b`).
   - *Tested:* each pair names a term and its same-country counterpart, with other-country traps and 60 % parents → Gen Z; David trains with the same glossary prompt.
   - *Result:* parents → Gen Z rises from 20 % to 43 % (Q5_K_M). Cost $0.67, plus $0.80 for pairs.
6. **Fine-tuned E4B** (`genlingo-2026-10-e4b`).
   - *Tested:* the same 1,500 pairs on the bigger base.
   - *Result:* 67 % slang handled and 836 ms p50 in the 2026-10-01 eval. Cost $0.98; it ran out of memory while merging and was finished on the laptop.
   - *Learned:* it doesn't beat E2B; more model didn't buy more slang.
7. **Quantization** (table above).
   - *Result:* Q4_K_M loses 8 slang points vs f16; imatrix recovers 5 and is still 3 below. Q5_K_M loses nothing for 0.2 GB more. Q6_K and Q8_0 weigh more without improving.
   - *Learned:* the rule is the smallest file within 2 points of f16 with p50 < 1 s, and that's Q5_K_M. The 2026-10-04 eval repeats it: Q4 67 %, Q5 74 %, f16 74 %.
8. **Training, merging and converting in a single job** (`zct96`).
   - *Result:* it died out of memory ($0.63), because Cloud Run's disk lives in memory.
   - *Learned:* now there are two jobs, an L4 that trains and a CPU job that merges and converts.
9. **Real sentences** (`genlingo-2026-10b-e2b`).
   - *Tested:* 22 sources, 146 terms and 420 real sentences; half to the test set, the other half to 334 training pairs anchored in the sentence.
   - *Result:* slang handled from 74 % to 82 %, almost all in parents → Gen Z (43 % → 59 %); correct slang 34 %. Cost $0.71.
10. **Embedding counterparts.**
    - *Tested:* linking each term to its other-generation equivalent by vector similarity.
    - *Result:* 175 of 217 links meant something else («brainrot → patatús») and were in 1,065 of 1,375 synthetic pairs.
    - *Learned:* counterparts are validated by meaning; the bad links are archived only as rejected answers.
11. **Meaning counterparts + lexicon prompt + round 3 of real sentences** (`genlingo-2026-10c-e2b-nomulti`).
    - *Tested:*
      - meaning-validated counterparts;
      - 1,715 synthetic pairs regenerated with them ($0.71 + $0.15);
      - a lexicon glossary with the answer in 85 % of examples;
      - more real sentences from Guatemala and Colombia (532 terms from 26 sources).
    - *Result:* on dev, chrF++ 63.2 with 809 ms p50. On test, correct slang 42 % (vs 34 % for 10b) and chrF++ 59.7 (+3.1 [+1.7, +4.4] over 10b). Cost $0.97.
12. **Pairs with 2–3 terms at once** (`genlingo-2026-10c-e2b`).
    - *Result:* on dev, chrF++ 61.9 vs 63.2 without them and 1.99 s p50 vs 809 ms. Slang stayed the same (86 % vs 85 % handled, 36 % vs 33 % correct). Cost $1.41.
    - *Learned:* the model lengthens its answers and doesn't fit the 1 s budget; they were dropped.
13. **ORPO preferences** (`…-nomulti-orpo`).
    - *Result:* +0.5 chrF++ on dev, but parents → Gen Z slang handled dropped from 70 % to 57 % and correct slang from 33 % to 31 %. Cost $0.56, plus $1.81 for two failed attempts (the model was loaded on the CPU for sampling and, at batch 4, the logits didn't fit the L4).
    - *Learned:* it didn't help; dropped.
14. **Goliath with David's glossary.**
    - *Tested:* giving Gemini the same bank in the prompt.
    - *Result:* correct slang from 26 % to 38 % and chrF++ from 53.5 to 57.0, at 3.05 s p50.
    - *Learned:* with the same data the big model gets closer; David's edge is his data and having been trained on it. In the demo Goliath runs without the glossary, as anyone would use it.
15. **Picking among several answers.**
    - *Tested:* generating 4 answers and keeping the one with the most expected counterparts from the bank.
    - *Result:* on dev, 10c's slang handled rose from 86 % to 94 %, but p50 reached 4.40 s.
    - *Learned:* it doesn't fit the 1 s budget; it's off (`DAVID_NBEST=1`).
16. **David in the cloud** (2026-10-06).
    - *Tested:* serving the same David with Ollama on Cloud Run with an L4 GPU (europe-west4), private and scaling to zero, with the public page calling him with an identity token.
    - *Result:* with the GPU on, David answers in ~0.5 s through the page (Goliath, between 0.8 and 18.6 s that day). Starting the GPU from zero, loading the model and warming it took almost four minutes; reading the files in one go and shipping the CUDA kernels already compiled in the image brought it down to about 35 seconds. The 4 examples came out as on the Mac: David 12 of 12 right, Goliath 0.
    - *Learned:* in the cloud David is still faster, but no longer free: the GPU costs about $1.05 per hour while it's on, and at a talk's volume that's more than what Gemini charges for the same phrases. The page first showed only the time; with the GPU's capacity measured, it shows both, and the README has the projections: at volume, David costs a fraction of Gemini ([Time and cost in the cloud](#time-and-cost-in-the-cloud)).

17. **Round 4: Gen Z slang of Mexico and neutral Spanish** (`genlingo-2026-10d-e2b`, 2026-10-06).
    - *Tested:* fixing with data that David failed on Gen Z slang that isn't Guatemalan: 1,600 training pairs anchored in Gen Z terms of Mexico and neutral Spanish (Gemini, $1.02, validated against the bank), 17 more real sentences from those countries, 3,880 examples in total.
    - *Result:* on dev, correct slang 46 % vs 40 % for `10c`. On test, 44 % vs 41 % and chrF++ 60.0 vs 59.5; neutral Spanish from 32 % to 43 %, Mexico unchanged (46 %), Guatemala from 52 % to 50 % and parents → Gen Z in Guatemala and Colombia from 44 % to 33 %. Cost $1.49 (68 min in the cloud).
    - *Learned:* a country's data moves that country. With more general data David improves in neutral Spanish, but not enough to beat Goliath there.
18. **General Gen Z slang probe** ([evals/report_probe.md](evals/report_probe.md)).
    - *Tested:* 32 real sentences of Gen Z slang used everywhere (cringe, random, crush, stalkear, funar, mid, delulu…), from 14 pages never used for training, both directions.
    - *Result:* as neutral Spanish, David 91 % (before and after round 4) vs 94 % for Goliath; as Guatemala, David 77 % (before 69 %) vs 77 %.
    - *Learned:* any big model already knows that slang; there David ties. His edge is local slang.
19. **The lexicon without fine-tuning, measured again** (2026-10-07 eval).
    - *Result:* base E2B with David's same lexicon reaches 42 % correct slang vs 44 % for the fine-tuned David; but it stays at 16 % slang handled parents → Gen Z (David 54 %) and chrF++ 54.9 (David 60.0).
    - *Learned:* the slang bank does most of the work of understanding slang; fine-tuning is what teaches David to *produce* it, the parents → Gen Z direction.
20. **The eval in the cloud too** (2026-10-07).
    - *Tested:* running the eval in a Cloud Run Job with the same L4 and David's precompiled CUDA kernels.
    - *Result:* each model answers the 399 phrases in ~80 s, with p50 of 237 ms for David. A GPU job lasts at most an hour, so `make eval` runs the models in four jobs in a row and merges them.

21. **Round 5: phrases with several slang terms** (`genlingo-2026-10e-e2b`, 2026-10-07).
    - *Tested:* whether David wins when a phrase combines 2–4 terms from the same country. Data: 422 new real sentences checked word by word (Mexico 89, neutral Spanish 130, Colombia 150, Guatemala 53; 120 are editor-written examples and only serve for training), 202 new terms, 324 natural synthetic phrases with 2–3 terms validated one at a time by meaning ($0.42) and 600 synthetic parents → Gen Z pairs outside Guatemala ($0.30).
    - *Why it doesn't repeat experiment 12's mistake:* short (5–22 words), natural phrases instead of forced terms, each term checked by meaning, both directions and 15 % of training. p50 stayed at 253 ms.
    - *Result:* on the combinations niche, 62 % vs 45 % for Goliath (+16.7 [+7.5, +25.9]); on the whole set, 58 % vs 34 %; Mexico flips to a win (65 % vs 48 %). Cost $1.44 (66 min in the cloud).
    - *Learned:* the validated synthetic combinations added the most (without them, 46 % on the dev combinations). Neutral Spanish, parents → Gen Z and slang from all over the internet are still ties.
22. **Only the new real sentences** (`…-webonly`).
    - *Result:* 47.8 % on the dev combinations vs 56.5 % for the winner; 3,073 examples, $1.24.
    - *Learned:* real sentences with several terms are scarce on the web (pages that explain slang almost never give a phrase with more than one term); the validated synthetic ones multiply them.
23. **All the data, untrimmed** (`…-all`).
    - *Result:* 49.3 % on the dev combinations; with 5,670 examples only 1.9 epochs fit in the hour a GPU job lasts.
    - *Learned:* trimming the old synthetic pairs to 60 % leaves room for 2.5 epochs and performs better.
24. **The cleaned bank** (`…-v2`, `…-v2-nocombo`).
    - *Tested:* retraining after removing 121 terms that were ordinary words («pues», «video») or duplicates.
    - *Result:* 52.2 % on the dev combinations vs 56.5 % for the winner (which was trained before the cleanup and uses the cleaned bank in the eval); without combinations, 40.6 %.
    - *Learned:* the registered rule picked `10e`; the difference between the two is 3 phrases out of 69. The `-v2-all` variant never trained (uploading its data failed).

**Total cost:** the logged training runs cost $18.87 ($9.15 through round 3, $1.49 for round 4 and $8.23 for the six round-5 variants), including five of the six failed ones ($3.44; the sixth left no cost record).

## Why the demo uses only the final model

The page uses `genlingo-2026-10e-e2b` in Q5_K_M with the lexicon prompt, and no other David:

- **It's the best at what the demo shows.** It has the highest correct slang on the test set: 58 %, vs 54 % for `10d`, 49 % for `10c`, 41 % for `10b`, 33 % for `10-e2b` and 23 % for `2026-09`, and the highest chrF++ (60.7). On the combinations niche it beats Goliath (62 % vs 45 %), where `10d` didn't. It was chosen on the dev set, not on the test set.
- **It fits the 1 s budget.** p50 of 253 ms in the cloud eval and ~0.5 s through the page, at 3.62 GB.
- **Q5_K_M loses no slang vs f16** (58 % vs 56 %) and is 2.6 times smaller.
- **The earlier ones teach nothing new on the page.** Their story (from 21 % to 58 % correct slang, at $0.41–$1.49 per training round) is in the tables above and in the logbook. `genlingo-2026-10d-e2b` stays in the bucket to roll back.
- **The page's examples are from what he wins:** Guatemalan slang, two-term phrases and a Mexican one. Slang from all over the internet, where he ties, is typed live so the tie shows; Colombia and neutral Spanish are documented here.

## Quick start

Using the demo takes nothing: open the page. To try the code without the cloud: `make test` (simulated models, `MOCK_AI=1`).

## Reproduce it in your own project

The models (David's GGUFs and the compiled CUDA kernels) and the training data live in **private buckets** of the talk's Google Cloud project; they don't come with the repo. To reproduce everything you need your own Google Cloud project (with L4 GPU quota) and your own buckets:

1. **Configuration:** `cp .env.example .env` and change `GOOGLE_CLOUD_PROJECT`, `MODELS_BUCKET` (the models), `STAGING_BUCKET` (training and evals, in the GPU's region) and `DAVID_URL` (filled in after the first `make deploy`). The `infra/` scripts create the service accounts and the image repository ([docs/ONBOARDING.md](docs/ONBOARDING.md), section 3).
2. **Data:** sentences quoted from all-rights-reserved sources are not in the repo (see [data/SOURCES.md](data/SOURCES.md)): in the talk's project `make data-pull` downloads them from the private bucket (`PRIVATE_DATA_URI`); in yours, `make data` rebuilds the test set, the pairs anchored in real sentences and the synthetic ones from the sources in [data/SOURCES.md](data/SOURCES.md) (Gemini writes the synthetic ones, at a cost).
3. **Train:** `make train` (an L4 trains and a CPU job merges and publishes the GGUF to your `MODELS_BUCKET`).
4. **Measure:** `make eval` and `make eval-dev` (a GPU job in the cloud).
5. **Publish:** `bash infra/04-david.sh` (David on Cloud Run with a GPU), `bash infra/07-david-jit-cache.sh` and `infra/04-david.sh` again (compiled CUDA kernels, so he starts in ~35 s) and `bash infra/05-page.sh` (the page). `make check` tests it live.

```bash
cp .env.example .env && (cd duel && uv sync)   # and edit .env with your project and buckets
gcloud auth application-default login
make data-pull   # only in the talk's project; elsewhere, make data
make train TAG=genlingo-YYYY-MM && make eval
make deploy && make check
```

Full command list in [docs/COMANDOS.en.md](docs/COMANDOS.en.md).

## License

The code is Apache 2.0 ([LICENSE](LICENSE)). The data cites its source and license in every record, and David, as a Gemma fine-tune, follows the Gemma terms of use: details in [THIRD_PARTY.md](THIRD_PARTY.md).

## Documentation

- [docs/DEMO.en.md](docs/DEMO.en.md): the demo script (what to open, which examples to tap, talking points and what to do if something fails).
- [docs/BITACORA.md](docs/BITACORA.md) (Spanish): David's story, iteration by iteration.
- [docs/DECISIONES.en.md](docs/DECISIONES.en.md): every technical decision, full results and training cost.
- [docs/ONBOARDING.md](docs/ONBOARDING.md) (Spanish): the cloud, the data and training pipeline, code walkthrough and common problems.
- [docs/COMANDOS.en.md](docs/COMANDOS.en.md): every `make` command.
- [docs/ESTRUCTURA.en.md](docs/ESTRUCTURA.en.md): architecture, monthly cycle, repository map and versions.
- [docs/CREDITOS.en.md](docs/CREDITOS.en.md): data provenance and licenses.
- [evals/report.md](evals/report.md), [evals/report_dev.md](evals/report_dev.md) and [evals/niche_report.md](evals/niche_report.md): the eval reports; [evals/niche.md](evals/niche.md): niches defined before looking at results.
- [data/SOURCES.md](data/SOURCES.md) and [data/DATASHEET.md](data/DATASHEET.md): data sources and datasheet.
