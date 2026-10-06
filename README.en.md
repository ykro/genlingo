# Genlingo — generational translator: Gen Z ↔ parents

Demo for the talk *"David vs. Goliath: how a small model beats a frontier model"*. «no manches, la peli estuvo bien chilera pero el final me dio cringe» ↔ «la película estuvo bien chévere pero el final me dio pena ajena». **David** is Gemma 4 E2B fine-tuned with LoRA on our own pairs and runs with Ollama on a GPU server of his own (Cloud Run, NVIDIA L4). **Goliath** is Gemini (`GEMINI_MODEL`, today `gemini-3.8-flash`) on Vertex AI. Everything runs in the cloud: the laptop only opens a page.

[Versión en español](README.md)

## The demo: David and Goliath side by side

One public page on Cloud Run: **https://genlingo-611681112050.us-central1.run.app**. Nothing to install or run on talk day: open the page a few minutes before and that's it.

- Pick the direction (Gen Z → parents or parents → Gen Z), type a phrase or tap an example, and both translate the same phrase at the same time. Each column shows its translation and how long it took.
- For the examples, the page also shows the human reference translation and, under each column, whether it got each slang term right (✓ or ✗).
- David shuts down on his own when nobody uses him, so nothing bills between talks. When the page opens, the top right says «Preparando a David…» with a clock while his GPU starts; from zero it takes about four minutes ([measured](docs/DECISIONES.en.md#david-in-the-cloud)). Once it says «David listo» everything answers right away, and the page keeps him on while it stays open.

![The comparison page: David and Goliath translate «esa tu tarea te quedó bien chafa»](docs/demo/02-comparar-genz-a-papas.png)

The four examples are Guatemalan slang from the test set, the case where David wins. I ran live the 51 short Guatemalan phrases the term-by-term check can judge, 3 times with each model, and kept only the ones David got right and Goliath got wrong all 3 times. After moving David to the cloud I ran them 3 more times against the Cloud Run David: David got all 12 right and Goliath none ([`data/translate_examples.json`](data/translate_examples.json), with the source and the reason for each one). The script is in [docs/DEMO.en.md](docs/DEMO.en.md).

![What runs where: the page, David and Goliath in the cloud](docs/diagrams/arquitectura.png)

## What you'll learn

1. **Your own data with `origin`:** every pair says where it came from (`web`, `synthetic` or `human`); without that you can't evaluate or retrain monthly.
2. **Term bank and real sentences:** 532 terms from 76 sources, meaning-validated counterparts and 556 pairs anchored in real sentences; David's edge is his data.
3. **LoRA on Cloud Run Jobs:** an L4 trains and a CPU job merges and exports GGUF; each run records its duration and cost.
4. **The cost of compression:** f16 vs Q4_K_M, Q5_K_M, Q6_K, Q8_0 and imatrix, in size, latency and lost slang.
5. **Evals with term metrics:** chrF++ plus *correct slang*, *slang handled* and *reference changes*, with a separate dev set for decisions and niches defined before looking at results.
6. **Your model on your own GPU:** David runs with Ollama on Cloud Run with an L4, private, and scales to zero between talks; the page wakes him when it opens. Training, evaluating and serving: all in the cloud, nothing on the laptop.

## The metrics

- **Correct slang** (*jerga correcta*): the slang the model produces means the same as the original, per the meaning-validated counterpart table (`data/counterparts.jsonl`). The main metric.
- **Slang handled** (*jerga resuelta*): the register changed. Gen Z → parents: no Gen Z bank slang is left; parents → Gen Z: the output uses at least one Gen Z term of the country. It doesn't check meaning.
- **Reference changes** (*cambios acertados*): of the words the human reference changed, how many appear in the output.
- **chrF++:** character overlap with the reference. A register rewrite keeps most words, so copying the phrase untranslated already scores 53.2; that's why it doesn't decide on its own.

All deterministic: no model judges another. Test-set numbers come from the 2026-10-04 eval on 399 `auto_validated` web phrases David never saw ([evals/report.md](evals/report.md)), unless another date is given. That eval ran David in Ollama on a Mac (before he moved to the cloud): the latencies in the tables are from there. In the cloud David answers in ~0.5 s and his cost is the GPU's ([David in the cloud](#david-in-the-cloud)).

## Final result

| | Correct slang | Slang handled | chrF++ | p50 (eval) |
| --- | ---: | ---: | ---: | ---: |
| **David** (`genlingo-2026-10c-e2b-nomulti`, Q5_K_M, 3.62 GB) | **42 %** | **82 %** | **59.7** | **670 ms** |
| Goliath `gemini-3.8-flash` | 26 % | 77 % | 53.5 | 2.60 s |
| Goliath with David's glossary (reference) | 38 % | 82 % | 57.0 | 3.05 s |
| Copy the phrase (baseline) | 1 % | 1 % | 53.2 | — |

- **Correct slang:** +16.3 points over Goliath (95 % CI [+10.8, +21.8]). 101 phrases only David gets right; 36 only Goliath.
- **chrF++:** +6.2 [+4.3, +8.1] over Goliath and +2.7 [+0.8, +4.7] over Goliath with the glossary.
- **Slang handled:** +4.5 [+0.0, +8.8], a statistical tie.
- **Goliath's cost:** $1.13 per 1,000 phrases in that eval; at the price from 2027-01-01, $2.26.

### By niche (correct slang, David vs Goliath without glossary)

Niches defined before looking at results ([evals/niche.md](evals/niche.md)); 95 % CI by paired bootstrap ([evals/niche_report.md](evals/niche_report.md)).

| Niche | n | David | Goliath | Δ | 95 % CI | Verdict |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Guatemalan slang (GT) | 115 | 52 % | 23 % | +29.6 | [+19.1, +40.0] | David wins |
| Parents → Gen Z (GT/CO) | 107 | 44 % | 20 % | +24.3 | [+12.1, +36.4] | David wins |
| Country CO | 131 | 37 % | 19 % | +17.6 | [+8.4, +27.5] | David wins |
| Country MX | 78 | 46 % | 37 % | +9.0 | [−2.6, +21.8] | statistical tie |
| Country LATAM (neutral Spanish) | 75 | 32 % | 31 % | +1.3 | [−9.3, +12.0] | statistical tie |
| Whole set | 399 | 42 % | 26 % | +16.3 | [+10.8, +21.8] | David wins |

- **On slang handled**, which ignores meaning, David wins on parents → Gen Z (67 % vs 52 %, +15.0 [+2.8, +27.1]) and in Colombia (+8.4 [+0.8, +16.0]). In Guatemala (85 % vs 76 %), Mexico, LATAM and the whole set it's a statistical tie.
- **Against Goliath with the same glossary:**
  - David wins on Guatemalan slang (+17.4 [+7.0, +28.7]) and on parents → Gen Z (+16.0 [+3.8, +28.3]).
  - It ties on the whole set (+4.0).
  - It loses on neutral Spanish: 32 % vs 55 %.

### chrF++ by country and by direction

| | CO | GT | LATAM | MX | Gen Z → parents | Parents → Gen Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| David | 60.4 | 65.3 | 56.5 | 53.6 | 67.4 | 49.1 |
| Goliath | 53.8 | 52.9 | 55.4 | 51.5 | 61.0 | 43.0 |
| Goliath + glossary | 54.3 | 60.1 | 58.9 | 56.0 | 63.8 | 47.6 |

## All the experiments

### Every variant on the test set (399 phrases)

| Variant | Correct slang | Slang handled (Gen Z → parents / parents → Gen Z / total) | Ref. changes | chrF++ | p50 | Size | Training |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| Base `gemma4:e2b-it-qat` | 14 % | 95 % / 10 % / 58 % | 14 % | 50.2 | 364 ms | 4.34 GB | — |
| Base E2B + glossary | 38 % | 94 % / 20 % / 62 % | 23 % | 55.0 | 452 ms | 4.34 GB | — |
| Base `gemma4:e4b` | 19 % | 97 % / 31 % / 68 % | 17 % | 48.2 | 802 ms | 6.58 GB | — |
| `genlingo-2026-09` (minimal edit, Q4_K_M) | 18 % | 94 % / 20 % / 62 % | 14 % | 55.0 | 391 ms | 3.42 GB | $0.41 |
| `genlingo-2026-09-f16` | 18 % | 93 % / 27 % / 64 % | 14 % | 55.4 | 435 ms | 9.27 GB | — |
| `genlingo-2026-10-e2b` + glossary (Q4_K_M) | 25 % | 95 % / 31 % / 67 % | 16 % | 55.7 | 512 ms | 3.42 GB | $0.67 |
| `genlingo-2026-10-e2b-q5_k_m` + glossary | 27 % | 97 % / 43 % / 74 % | 18 % | 55.4 | 564 ms | 3.62 GB | — |
| `genlingo-2026-10-e2b-f16` + glossary | 28 % | 99 % / 42 % / 74 % | 19 % | 56.3 | 566 ms | 9.27 GB | — |
| `genlingo-2026-10b-e2b` + glossary (Q5_K_M) | 34 % | 99 % / 59 % / 82 % | 22 % | 56.6 | 557 ms | 3.62 GB | $0.71 |
| `genlingo-2026-10b-e2b-f16` + glossary | 34 % | 98 % / 59 % / 81 % | 22 % | 56.7 | 543 ms | 9.27 GB | — |
| **`genlingo-2026-10c-e2b-nomulti` + lexicon (Q5_K_M)** | **42 %** | 100 % / 58 % / **82 %** | **28 %** | **59.7** | 670 ms | 3.62 GB | $0.97 |
| Goliath `gemini-3.8-flash` | 26 % | 97 % / 51 % / 77 % | 25 % | 53.5 | 2.60 s | — | — |
| Goliath + glossary | 38 % | 100 % / 58 % / 82 % | 29 % | 57.0 | 3.05 s | — | — |
| Copy the phrase | 1 % | 0 % / 3 % / 1 % | 0 % | 53.2 | — | — | — |

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
    - *Result:* with the GPU on, David answers in ~0.5 s through the page (Goliath, between 0.8 and 18.6 s that day). Starting the GPU from zero, loading the model and warming it takes about four minutes. The 4 examples came out as on the Mac: David 12 of 12 right, Goliath 0.
    - *Learned:* in the cloud David is still faster, but no longer free: the GPU costs about $1.05 per hour while it's on, and at a talk's volume that's more than what Gemini charges for the same phrases. So the page shows time, not cost ([details](docs/DECISIONES.en.md#david-in-the-cloud)).

**Total cost:** the logged training runs cost $9.15, including five of the six failed ones ($3.44; the sixth left no cost record).

## Why the demo uses only the final model

The page uses `genlingo-2026-10c-e2b-nomulti` in Q5_K_M with the lexicon prompt, and no other David:

- **It's the best at what the demo shows.** It has the highest correct slang of all variants: 42 %, vs 34 % for `10b`, 27 % for `10-e2b` and 18 % for `2026-09`. It also has the highest chrF++ (59.7).
- **It fits the 1 s budget.** 670 ms p50 in the eval and ~0.5 s on the cloud GPU, with 3.62 GB. The multi-term variant was around 2 s on dev, and picking among 4 answers around 4.4 s.
- **Q5_K_M loses no slang vs f16** and is 2.6 times smaller. Q4_K_M did lose slang.
- **The earlier ones teach nothing new on the page.** Their story (from 14 % to 42 % correct slang, at $0.41–$0.97 per training round) is in the tables above and in the logbook. The page only compares today's David with Goliath.
- **The page's examples come from the niche where it wins** (Guatemalan slang, +29.6 correct-slang points). Mexico and neutral Spanish, where David ties or where Goliath with the glossary beats him, stay documented here and are not shown in the demo.

## Quick start

To use the demo you need nothing: open the page. To rebuild it (Google Cloud with `gcloud` and ADC, `uv`):

```bash
cp .env.example .env && (cd duel && uv sync)
gcloud auth application-default login
make deploy   # David on Cloud Run with a GPU (europe-west4) + the public page (us-central1)
make check    # the live page: wakes David and translates every example with both
make test     # tests without network (MOCK_AI=1)
```

All commands in [docs/COMANDOS.en.md](docs/COMANDOS.en.md).

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
