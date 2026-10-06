# Credits and provenance

Where Genlingo's data comes from and under which license it is used. Back to the [README](../README.en.md). [Versión en español](CREDITOS.md).

## Data provenance and licenses

| Data | Origin | License / use |
| --- | --- | --- |
| `data/terms.jsonl` (532 terms) and `data/raw/web_usage*.jsonl` (996 sentences) | 76 web sources from MX, GT, CO and Latin America, accessed 2026-09-30 to 2026-10-02 ([SOURCES.md](../data/SOURCES.md)); a general-speech corpus (S63) only to count ambiguous terms | WikiLengua (CC BY-SA 3.0), Wiktionary (CC BY-SA 4.0) and diccionario-chapin (MIT) are reused under their licenses with per-record attribution. From all-rights-reserved sources only facts (a term and its meaning, paraphrased) and one short attributed quotation per entry are taken, for research and education. |
| `data/pairs/test_web.jsonl` (522 pairs, 399 `auto_validated`) and `data/pairs/real_train.jsonl` (334 pairs) | Real sentences from those sources; the reference is the curator's rewrite (under 30% are curator-written sentences, marked `example_origin=curator`) | Same as the source; pairs quoting CC BY-SA examples inherit share-alike for that text. |
| `data/pairs/synthetic.jsonl` and `synthetic_multi.jsonl` (synthetic pairs) | `gemini-3.8-flash`, meaning-validated counterparts (`data/counterparts.jsonl`), base seed 2027; training only | Every pair records model, prompt version, seed and the term ids it was built from. |

Known limitations (from the datasheet): Guatemalan youth slang is thinly documented online; slang ages fast; references are one person's, so chrF++ underestimates valid alternative translations.

Per-source details and counts: [data/SOURCES.md](../data/SOURCES.md) and [data/DATASHEET.md](../data/DATASHEET.md).
