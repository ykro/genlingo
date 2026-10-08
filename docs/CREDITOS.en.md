# Credits and provenance

Where Genlingo's data comes from and under which license it is used. Back to the [README](../README.en.md). [Versión en español](CREDITOS.md).

## Data provenance and licenses

| Data | Origin | License / use |
| --- | --- | --- |
| `data/terms.jsonl` (734 terms) and `data/raw/web_usage*.jsonl` (1,435 sentences) | 133 web sources from MX, GT, CO and Latin America (plus pan-Hispanic slang phrases from Argentina, Chile, Peru, Venezuela and Spain, labelled as neutral Spanish), accessed 2026-09-30 to 2026-10-07 ([SOURCES.md](../data/SOURCES.md)); a general-speech corpus (S63) only to count ambiguous terms | WikiLengua (CC BY-SA 3.0), Wiktionary (CC BY-SA 4.0) and diccionario-chapin (MIT) are reused under their licenses with per-record attribution. From all-rights-reserved sources only facts (a term and its meaning, paraphrased) and one short attributed quotation per entry are taken, for research and education; those quotations aren't in the repo, they live in a private bucket (`make data-pull`). |
| `data/pairs/test_web.jsonl` (522 pairs, 399 `auto_validated`) and `data/pairs/real_train.jsonl` (334 pairs) | Real sentences from those sources; the reference is the curator's rewrite (under 30% are curator-written sentences, marked `example_origin=curator`) | Same as the source; pairs quoting CC BY-SA examples inherit share-alike for that text. |
| `data/pairs/synthetic.jsonl` and `synthetic_multi.jsonl` (synthetic pairs) | `gemini-3.8-flash`, meaning-validated counterparts (`data/counterparts.jsonl`), base seed 2027; training only | Every pair records model, prompt version, seed and the term ids it was built from. |
| `data/eval/combos.jsonl` (174 pairs) | Combinations niche: test-set phrases with 2 or more terms and real round-5 sentences (posts on X, Bluesky, Steam reviews, blog and forum comments), set aside before training; the reference is the curator's | Like the test set: quotations from closed sources live in the private bucket; never used for training or on the page. |
| `data/pairs/synthetic_combo.jsonl` and `synthetic_p2g.jsonl` (round 5) | `gemini-3.8-flash`, prompt versions `synthetic-combo-2026-10e` (seed 6067) and `synthetic-2026-10b` (seed 5051); training only | Every pair records model, prompt version and seed; every term is validated by meaning against the bank. |

Known limitations (from the datasheet): Guatemalan youth slang is thinly documented online; slang ages fast; references are one person's, so chrF++ underestimates valid alternative translations.

Per-source details and counts: [data/SOURCES.md](../data/SOURCES.md) and [data/DATASHEET.md](../data/DATASHEET.md).
