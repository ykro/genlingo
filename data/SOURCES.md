# Sources

Every term and usage example in `terms.jsonl` and `raw/web_usage.jsonl` cites one of these
sources by `source_id` (exact per-entry URL in the record). Accessed 2026-09-30.

## Policy

- **What we take:** facts (a term and what it means, paraphrased in our own words) and at most
  one short usage example per entry (≤ ~20 words), always attributed with its URL. We never
  copy a glossary wholesale.
- **Openly licensed sources** (Wikcionario and WikiLengua: CC BY-SA; diccionario-chapin: MIT)
  are reused under their licenses; attribution is the per-record URL. Derived pairs that quote
  CC BY-SA examples inherit share-alike for that text.
- **All-rights-reserved sources** (news, magazines, blogs): only facts and short attributed
  quotations for research and education. Nothing is republished beyond that.
- **What is in this repo and what isn't** (2026-10-07). The repo keeps every record: the term, the
  meaning in our words, the URL and the curator's rewrite, plus the full text of the open sources
  (S01–S05, S62, S70: WikiLengua and Wikcionario under CC BY-SA, so pairs that quote them inherit
  share-alike; diccionario-chapin under MIT; Guate Inmortal under CC BY 4.0). The sentences quoted
  from every other source (some, like S83 and S85, forbid any reproduction) are **not** in the repo:
  their field is `null` and listed in `"redacted"`, and the full files live in a private bucket
  (`PRIVATE_DATA_URI`), which `make data-pull` downloads to `data/.private/` (git-ignored) with the
  project's credentials. The scripts read the private copy when it is there
  (`genlingo_duel.dataset.read_jsonl`) and write both versions (`write_jsonl`). The eval job image
  carries the private copy and stays in the project's private Artifact Registry. Files affected:
  `pairs/test_web.jsonl`, `pairs/real_train.jsonl`, `pairs/dev_real.jsonl`, `raw/web_usage*.jsonl`,
  `terms.jsonl`, `raw/terms_*.jsonl`, `eval/terms_test.jsonl`, `eval/probe_genz.jsonl`. The page's
  example phrases come only from open sources.
- **Curator-written sentences:** where a source gives a term but no usable example, the curator
  wrote a minimal example and marked it `example_origin=curator` (under 30% of test candidates).
- **Test references** (`rewrite`) are written by the dataset curator from the meaning the source
  gives, never by Gemini. They are validated automatically against the term bank (`auto_validated`,
  `scripts/validate_test_set.py`).

## Sources

| id | url | owner | license / terms | country | what was taken | accessed |
| --- | --- | --- | --- | --- | --- | --- |
| S01 | https://www.wikilengua.org/index.php/Jerga_juvenil/Guatemala | WikiLengua del español | CC BY-SA 3.0 | GT | 10 terms + meanings (paraphrased), 10 generator examples; 10 usage examples (test candidates) | 2026-09-30 |
| S02 | https://www.wikilengua.org/index.php/Jerga_juvenil/Colombia | WikiLengua del español | CC BY-SA 3.0 | CO | 14 terms + meanings (paraphrased), 14 generator examples; 4 usage examples (test candidates) | 2026-09-30 |
| S03 | https://www.wikilengua.org/index.php/Jerga_juvenil/M%C3%A9xico | WikiLengua del español | CC BY-SA 3.0 | MX | 1 terms + meanings (paraphrased), 1 generator examples; 0 usage examples (test candidates) | 2026-09-30 |
| S04 | https://github.com/abisai7/diccionario-chapin/blob/main/src/content/words-es/ (43 pages) | abisai7 / diccionario-chapin (GitHub) | MIT License | GT | 42 terms + meanings (paraphrased), 42 generator examples; 46 usage examples (test candidates) | 2026-09-30 |
| S05 | https://es.wiktionary.org/wiki/ (26 pages) | Wikcionario (Wikimedia Foundation) | CC BY-SA 4.0 | MX, GT, CO, LATAM | 15 terms + meanings (paraphrased), 15 generator examples; 21 usage examples (test candidates) | 2026-09-30 |
| S06 | https://www.infobae.com/mexico/2024/12/04/cuales-son-las-frases-y-palabras-que-solo-la-generacion-z-entiende/ | Infobae | © Infobae, all rights reserved; facts + short attributed quotation (research/education) | MX | 2 terms + meanings (paraphrased), 2 generator examples; 2 usage examples (test candidates) | 2026-09-30 |
| S07 | https://guiauniversitaria.mx/diccionario-gen-z-gen-alfa-para-enteneder-a-los-jovenes/ | Guía Universitaria | © Guía Universitaria, all rights reserved; facts + short attributed quotation (research/education) | MX | 5 terms + meanings (paraphrased), 5 generator examples; 6 usage examples (test candidates) | 2026-09-30 |
| S08 | https://guiauniversitaria.mx/10-frases-tipicas-de-los-papas-mexicanos/ | Guía Universitaria | © Guía Universitaria, all rights reserved; facts + short attributed quotation (research/education) | MX | 1 terms + meanings (paraphrased), 1 generator examples; 2 usage examples (test candidates) | 2026-09-30 |
| S09 | https://vanguardia.com.mx/vida/sabias-que-la-generacion-z-tiene-su-propio-lenguaje-BH12374104 | Vanguardia MX | © Vanguardia MX, all rights reserved; facts + short attributed quotation (research/education) | MX | 8 terms + meanings (paraphrased), 8 generator examples; 6 usage examples (test candidates) | 2026-09-30 |
| S10 | https://www.informador.mx/mexico/Cuales-son-las-palabras-favoritas-de-la-Generacion-Z-y-para-que-las-usan-20240503-0092.html | El Informador | © El Informador, all rights reserved; facts + short attributed quotation (research/education) | MX | 2 terms + meanings (paraphrased), 2 generator examples; 0 usage examples (test candidates) | 2026-09-30 |
| S11 | https://www.univision.com/entretenimiento/cultura-pop/como-expresa-generacion-z-palabras-frases-centennials-millennials-generacion-x-no-entienden | Univision | © Univision, all rights reserved; facts + short attributed quotation (research/education) | LATAM | 2 terms + meanings (paraphrased), 2 generator examples; 2 usage examples (test candidates) | 2026-09-30 |
| S12 | https://www.univision.com/entretenimiento/cultura-pop/frases-delatan-senor-o-senora-pero-se-siguen-usando | Univision | © Univision, all rights reserved; facts + short attributed quotation (research/education) | MX, LATAM | 1 terms + meanings (paraphrased), 1 generator examples; 1 usage examples (test candidates) | 2026-09-30 |
| S13 | https://noro.mx/cultura/frases-palabras-populares-de-los-gen-z/ | Noro | © Noro, all rights reserved; facts + short attributed quotation (research/education) | MX | 1 terms + meanings (paraphrased), 1 generator examples; 2 usage examples (test candidates) | 2026-09-30 |
| S14 | https://www.gentedesalta.com/sociedad/gen-z-o-centennials-diccionario-urgente-entender-su-idioma-n870 | Gente de Salta | © Gente de Salta, all rights reserved; facts + short attributed quotation (research/education) | LATAM | 9 terms + meanings (paraphrased), 9 generator examples; 13 usage examples (test candidates) | 2026-09-30 |
| S15 | https://trykaiwa.com/blog/spanish-gen-z-slang-phrases-2026 | Kaiwa | © Kaiwa, all rights reserved; facts + short attributed quotation (research/education) | LATAM | 9 terms + meanings (paraphrased), 9 generator examples; 5 usage examples (test candidates) | 2026-09-30 |
| S16 | https://www.fluentu.com/blog/spanish/guatemalan-slang/ | FluentU | © FluentU, all rights reserved; facts + short attributed quotation (research/education) | GT | 3 terms + meanings (paraphrased), 3 generator examples; 3 usage examples (test candidates) | 2026-09-30 |
| S17 | https://www.fluentu.com/blog/spanish/colombian-slang/ | FluentU | © FluentU, all rights reserved; facts + short attributed quotation (research/education) | CO | 13 terms + meanings (paraphrased), 13 generator examples; 10 usage examples (test candidates) | 2026-09-30 |
| S18 | https://www.fluentu.com/blog/spanish/mexican-slang/ | FluentU | © FluentU, all rights reserved; facts + short attributed quotation (research/education) | MX | 30 terms + meanings (paraphrased), 30 generator examples; 23 usage examples (test candidates) | 2026-09-30 |
| S19 | https://www.tellmeinspanish.com/mexico/mexican-slang/words/ | Tell Me In Spanish | © Tell Me In Spanish, all rights reserved; facts + short attributed quotation (research/education) | MX | 21 terms + meanings (paraphrased), 21 generator examples; 31 usage examples (test candidates) | 2026-09-30 |
| S20 | https://medellinjoven-production.s3.us-west-2.amazonaws.com/biblioteca/DOC4.pdf | Alcaldía de Medellín — Medellín Joven | © Alcaldía de Medellín — Medellín Joven, all rights reserved; facts + short attributed quotation (research/education) | CO | 28 terms + meanings (paraphrased), 28 generator examples; 38 usage examples (test candidates) | 2026-09-30 |
| S22 | https://www.prensalibre.com/vida/salud-y-familia/dia-de-la-madre-las-frases-mas-reconocidas-de-las-madres-chapinas/ | Prensa Libre | © Prensa Libre, all rights reserved; facts + short attributed quotation (research/education) | GT | 3 terms + meanings (paraphrased), 3 generator examples; 6 usage examples (test candidates) | 2026-09-30 |
| S23 | https://www.guatemala.com/noticias/entretenimiento/las-tipicas-frases-que-toda-madre-guatemalteca-ha-dicho-alguna-vez.html | Guatemala.com | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 1 terms + meanings (paraphrased), 1 generator examples; 6 usage examples (test candidates) | 2026-09-30 |
| S24 | https://nuevalengua.com/19-expresiones-tipicas-de-una-mama-colombiana/ | Nueva Lengua | © Nueva Lengua, all rights reserved; facts + short attributed quotation (research/education) | CO | 1 terms + meanings (paraphrased), 1 generator examples; 15 usage examples (test candidates) | 2026-09-30 |
| S25 | https://www.minuto30.com/frases-tipicas-mamas-colombianas/1439293/ | Minuto30 | © Minuto30, all rights reserved; facts + short attributed quotation (research/education) | CO | 3 terms + meanings (paraphrased), 3 generator examples; 13 usage examples (test candidates) | 2026-09-30 |
| S26 | https://edomexaldia.com/las-10-frases-mas-emblematicas-de-los-papas-mexicanos/ | Edomex al Día | © Edomex al Día, all rights reserved; facts + short attributed quotation (research/education) | MX | 0 terms + meanings (paraphrased), 0 generator examples; 4 usage examples (test candidates) | 2026-09-30 |
| S27 | https://webadictos.com/frases-tipicas-de-las-madres/ | Webadictos | © Webadictos, all rights reserved; facts + short attributed quotation (research/education) | MX, LATAM | 3 terms + meanings (paraphrased), 3 generator examples; 8 usage examples (test candidates) | 2026-09-30 |
| S28 | https://www.chilango.com/cultura/frases-de-chavorrucos/ | Chilango | © Chilango, all rights reserved; facts + short attributed quotation (research/education) | MX | 5 terms + meanings (paraphrased), 5 generator examples; 5 usage examples (test candidates) | 2026-09-30 |
| S29 | https://www.adn40.mx/es-tendencia/en-mis-tiempos-15-frases-tipicas-chistosas-dicen-los-abuelos/ | ADN40 | © ADN40, all rights reserved; facts + short attributed quotation (research/education) | MX | 2 terms + meanings (paraphrased), 2 generator examples; 7 usage examples (test candidates) | 2026-09-30 |
| S30 | https://genial.guru/articles/30-palabras-que-usaban-nuestros-abuelos-y-que-ahora-nos-invitan-a-viajar-al-pasado-1454259/ | Genial.guru | © Genial.guru, all rights reserved; facts + short attributed quotation (research/education) | LATAM | 16 terms + meanings (paraphrased), 16 generator examples; 21 usage examples (test candidates) | 2026-09-30 |
| S31 | https://www.elgrafico.mx/al-dia/2025/09/25/glosario-para-entender-a-los-jovenes-en-redes-que-tan-perdido-estas/ | El Gráfico | © El Gráfico, all rights reserved; facts + short attributed quotation (research/education) | MX | 2 terms + meanings (paraphrased), 2 generator examples; 2 usage examples (test candidates) | 2026-09-30 |
| S33 | https://www.telediario.mx/tendencias/que-significa-cringe-facto-rizz-funa-palabras-de-redes-sociales | Telediario | © Telediario, all rights reserved; facts + short attributed quotation (research/education) | MX | 3 terms + meanings (paraphrased), 3 generator examples; 2 usage examples (test candidates) | 2026-09-30 |
| S37 | https://www.asale.org/damer/dar | Asociación de Academias de la Lengua Española (DAMER) | © Asociación de Academias de la Lengua Española (DAMER), all rights reserved; facts + short attributed quotation (research/education) | LATAM | 1 terms + meanings (paraphrased), 1 generator examples; 1 usage examples (test candidates) | 2026-09-30 |
| S38 | https://blog.openl.io/es/30-slang-words-gen-zers-are-using-in-2025/ | OpenL blog | © OpenL blog, all rights reserved; facts + short attributed quotation (research/education) | LATAM | 1 terms + meanings (paraphrased), 1 generator examples; 2 usage examples (test candidates) | 2026-09-30 |
| S39 | https://www.univision.com/entretenimiento/cultura-pop/palabras-generacion-x-millennial-centennials-no-entienden | Univision | © Univision, all rights reserved; facts + short attributed quotation (research/education) | LATAM | 1 terms + meanings (paraphrased), 1 generator examples; 1 usage examples (test candidates) | 2026-09-30 |
| S40 | https://www.buzzfeed.com/mx/luisdelvalle/frases-de-senora-mexicana-quiz-lista | BuzzFeed México | © BuzzFeed México, all rights reserved; facts + short attributed quotation (research/education) | MX | 1 terms + meanings (paraphrased), 1 generator examples; 1 usage examples (test candidates) | 2026-09-30 |
| S41 | https://spanish.yabla.com/lesson-Colombian-Slang-100-Words-and-Phrases-to-Sound-like-a-True-Colombian-1675 | Yabla Spanish | © Yabla, all rights reserved; facts + short attributed quotation (research/education) | CO | 10 terms + meanings (paraphrased), 10 term examples; 33 usage examples (real); cited by 4 curator-written sentences | 2026-10-01 |
| S42 | https://www.italki.com/en/blog/colombian-slang | italki | © italki, all rights reserved; facts + short attributed quotation (research/education) | CO | 1 terms + meanings (paraphrased), 1 term examples; 12 usage examples (real); cited by 1 curator-written sentences | 2026-10-01 |
| S43 | https://latinamericanspanishcafe.com/colombian-slang/ | Latin American Spanish Café | © Latin American Spanish Café, all rights reserved; facts + short attributed quotation (research/education) | CO | 3 terms + meanings (paraphrased), 2 term examples; 4 usage examples (real); cited by 2 curator-written sentences | 2026-10-01 |
| S44 | https://learnmorethanspanish.com/blog/colombian-spanish-slangs-meaning/ | Learn More Than Spanish | © Learn More Than Spanish, all rights reserved; facts + short attributed quotation (research/education) | CO | 5 terms + meanings (paraphrased), 5 term examples; 22 usage examples (real); cited by 2 curator-written sentences | 2026-10-01 |
| S45 | https://learnmorethanspanish.com/blog/colombian-slang-bogota/ | Learn More Than Spanish | © Learn More Than Spanish, all rights reserved; facts + short attributed quotation (research/education) | CO | 2 terms + meanings (paraphrased), 2 term examples; 7 usage examples (real); cited by 1 curator-written sentences | 2026-10-01 |
| S46 | https://www.tomplanmytrip.com/colombian-slang-words-expressions/ | Tom Plan My Trip | © Tom Plan My Trip, all rights reserved; facts + short attributed quotation (research/education) | CO | 6 terms + meanings (paraphrased), 6 term examples; 18 usage examples (real); cited by 2 curator-written sentences | 2026-10-01 |
| S47 | https://lingopie.com/blog/21-best-colombian-slang-words-to-learn-this-year/ | Lingopie | © Lingopie, all rights reserved; facts + short attributed quotation (research/education) | CO | 1 terms + meanings (paraphrased), 1 term examples; 15 usage examples (real); cited by 1 curator-written sentences | 2026-10-01 |
| S48 | https://lingopie.com/blog/guatemalan-slang/ | Lingopie | © Lingopie, all rights reserved; facts + short attributed quotation (research/education) | GT | 2 terms + meanings (paraphrased), 2 term examples; 8 usage examples (real); cited by 2 curator-written sentences | 2026-10-01 |
| S49 | https://baselang.com/blog/vocabulary/guatemalan-slang/ | BaseLang | © BaseLang, all rights reserved; facts + short attributed quotation (research/education) | GT | 5 terms + meanings (paraphrased), 5 term examples; 18 usage examples (real); cited by 2 curator-written sentences | 2026-10-01 |
| S50 | https://www.spanish.academy/blog/top-20-guatemalan-words-and-slang-expressions-you-should-know/ | Spanish Academy (Mar Z. Luna) | © Spanish Academy, all rights reserved; facts + short attributed quotation (research/education) | GT | 1 terms + meanings (paraphrased), 1 term examples; 11 usage examples (real) | 2026-10-01 |
| S51 | https://spanishvip.com/vocabulary/guatemalan-slang/ | SpanishVIP | © SpanishVIP, all rights reserved; facts + short attributed quotation (research/education) | GT | 0 terms + meanings (paraphrased), 0 term examples; 3 usage examples (real) | 2026-10-01 |
| S52 | https://www.guatemala.com/noticias/vida/palabras-que-usamos-los-guatemaltecos-para-casaquear.html | Guatemala.com | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 5 terms + meanings (paraphrased), 5 term examples; 1 usage examples (real); cited by 5 curator-written sentences | 2026-10-01 |
| S53 | https://www.guatemala.com/aprende/cultura-guatemalteca/chapinismos-positivos-que-usan-los-guatemaltecos | Guatemala.com | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 1 terms + meanings (paraphrased), 0 term examples; 0 usage examples (real); cited by 1 curator-written sentences | 2026-10-01 |
| S54 | https://mochilerostv.com/guaterminos-91-expresiones-guatemaltecas/ | Mochileros TV | © Mochileros TV, all rights reserved; facts + short attributed quotation (research/education) | GT | 6 terms + meanings (paraphrased), 5 term examples; 2 usage examples (real); cited by 6 curator-written sentences | 2026-10-01 |
| S55 | https://www.publinews.gt/noticias/2026/09/30/que-es-un-chapinismo-las-expresiones-que-dan-identidad-al-espanol-en-guatemala/ | Publinews Guatemala | © Publinews, all rights reserved; facts + short attributed quotation (research/education) | GT | 1 terms + meanings (paraphrased), 0 term examples; 0 usage examples (real); cited by 1 curator-written sentences | 2026-10-01 |
| S56 | https://www.elespectador.com/actualidad/el-diccionario-de-los-jovenes-article-136720/ | El Espectador (glossary by Universidad Santo Tomás students) | © El Espectador, all rights reserved; facts + short attributed quotation (research/education) | CO | 2 terms + meanings (paraphrased), 0 term examples; 0 usage examples (real); cited by 2 curator-written sentences | 2026-10-01 |
| S57 | https://www.colombia.com/vida-y-estilo/pareja/sdi/116577/top-de-frases-tipicas-de-papa | Colombia.com | © Colombia.com, all rights reserved; facts + short attributed quotation (research/education) | CO | 4 terms + meanings (paraphrased), 4 term examples; 4 usage examples (real) | 2026-10-01 |
| S58 | https://www.diariodelsur.com.co/dia-del-padre-estas-son-las-siete-frases-mas-tipicas-de-los-papas-colombianos/ | Diario del Sur | © Diario del Sur, all rights reserved; facts + short attributed quotation (research/education) | CO | 2 terms + meanings (paraphrased), 2 term examples; 1 usage examples (real) | 2026-10-01 |
| S59 | https://alternativo.mx/el-diccionario-de-las-expresiones-que-usan-los-jovenes-en-2025/ | Alternativo.mx | © Alternativo.mx, all rights reserved; facts + short attributed quotation (research/education) | LATAM | 4 terms + meanings (paraphrased), 4 term examples; 6 usage examples (real); cited by 3 curator-written sentences | 2026-10-01 |
| S60 | https://www.telemetro.com/actualidad/que-significan-las-palabras-la-generacion-z-asi-hablan-ahora-n6079373 | Telemetro | © Telemetro, all rights reserved; facts + short attributed quotation (research/education) | LATAM | 0 terms + meanings (paraphrased), 0 term examples; 3 usage examples (real) | 2026-10-01 |
| S61 | https://quillbot.com/es/blog/vocabulario/expresiones-generacion-z/ | QuillBot (blog en español) | © QuillBot, all rights reserved; facts + short attributed quotation (research/education) | LATAM | 1 terms + meanings (paraphrased), 1 term examples; 8 usage examples (real); cited by 10 curator-written sentences | 2026-10-01 |
| S62 | https://es.wiktionary.org/wiki/ (additional pages, see per-record URL) | Wikcionario (Wikimedia Foundation) | CC BY-SA 4.0 | MX, GT, CO | 27 terms + meanings (paraphrased), 27 term examples; 27 usage examples (real); cited by 16 curator-written sentences | 2026-10-01 |
| S63 | https://huggingface.co/datasets/shraavb/spanish-slang-stt-data | shraavb (Hugging Face; repackages CIEMPIESS, Common Voice, OpenSLR) | dataset card: CC BY 4.0; upstream corpora under their own licenses | MX, LATAM | **No text taken.** Only per-term match counts over ~39k general-speech transcripts, to flag ambiguous term-bank entries (`scripts/flag_ambiguous_terms.py`). | 2026-10-01 |
| S64 | https://soymigrante.com/revista/otras-20-palabras-chapinas-que-solo-un-guatemalteco-reconoce/ | SoyMigrante.com (Revista) | © SoyMigrante.com Revista, all rights reserved; facts + short attributed quotation (research/education) | GT | 12 terms + meanings (paraphrased), 12 term examples; 32 usage examples (real) | 2026-10-02 |
| S65 | https://soymigrante.com/revista/guatemaltequismos-que-superan-fronteras/ | SoyMigrante.com (Revista) | © SoyMigrante.com Revista, all rights reserved; facts + short attributed quotation (research/education) | GT | 6 terms + meanings (paraphrased), 6 term examples; 27 usage examples (real) | 2026-10-02 |
| S66 | https://soymigrante.com/revista/10-verbos-super-chapines-que-solo-un-guatemalteco-entiende/ | SoyMigrante.com (Revista) | © SoyMigrante.com Revista, all rights reserved; facts + short attributed quotation (research/education) | GT | 5 terms + meanings (paraphrased), 5 term examples; 5 usage examples (real) | 2026-10-02 |
| S67 | https://soymigrante.com/revista/todo-chapin-conoce-estas-palabras-guatemaltecas-cuales-usas/ | SoyMigrante.com (Revista) | © SoyMigrante.com Revista, all rights reserved; facts + short attributed quotation (research/education) | GT | 5 terms + meanings (paraphrased), 5 term examples; 5 usage examples (real) | 2026-10-02 |
| S68 | https://www.guatemala.com/noticias/entretenimiento/asi-es-como-nos-expresamos-los-guatemaltecos.html | Guatemala.com | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 6 terms + meanings (paraphrased), 6 term examples; 8 usage examples (real) | 2026-10-02 |
| S69 | https://www.guatemala.com/noticias/sociedad/las-frases-toda-abuelita-guatemalteca-ha-mencionado-alguna-vez.html | Guatemala.com | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 0 terms + meanings (paraphrased), 0 term examples; 3 usage examples (real) | 2026-10-02 |
| S70 | https://guateinmortal.wordpress.com/2016/10/25/las-tipicas-frases-del-chapin/ | Guate Inmortal (blog on WordPress.com) | CC BY 4.0 (Creative Commons Reconocimiento 4.0 Internacional, per the blog footer) | GT | 0 terms + meanings (paraphrased), 0 term examples; 1 usage examples (real) | 2026-10-02 |
| S71 | https://www.guatemala.com/aprende/cultura-guatemalteca/frases-guatemaltecas-que-empiezan-con-a | Aprende Guatemala (Guatemala.com) | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 5 terms + meanings (paraphrased), 5 term examples; 5 usage examples (real) | 2026-10-02 |
| S72 | https://www.guatemala.com/aprende/cultura-guatemalteca/guatemaltequismos-que-inician-con-m | Aprende Guatemala (Guatemala.com) | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 2 terms + meanings (paraphrased), 2 term examples; 2 usage examples (real) | 2026-10-02 |
| S73 | https://www.guatemala.com/aprende/cultura-guatemalteca/guatemaltequismos-que-empiezan-con-ch | Aprende Guatemala (Guatemala.com) | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 2 terms + meanings (paraphrased), 2 term examples; 2 usage examples (real) | 2026-10-02 |
| S74 | https://www.guatemala.com/aprende/cultura-guatemalteca/general/expresiones-guatemaltecas-que-se-usan-en-la-cotidianidad | Aprende Guatemala (Guatemala.com) | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 1 terms + meanings (paraphrased), 1 term examples; 2 usage examples (real) | 2026-10-02 |
| S75 | https://www.guatemala.com/aprende/cultura-guatemalteca/general/significado-de-la-palabra-yuca-en-guatemala | Aprende Guatemala (Guatemala.com) | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 1 terms + meanings (paraphrased), 1 term examples; 2 usage examples (real) | 2026-10-02 |
| S76 | https://www.guatemala.com/aprende/cultura-guatemalteca/general/significado-de-la-expresion-vaa-en-guatemala | Aprende Guatemala (Guatemala.com) | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 0 terms + meanings (paraphrased), 0 term examples; 2 usage examples (real) | 2026-10-02 |
| S77 | https://www.guatemala.com/aprende/cultura-guatemalteca/general/origen-palabra-chucho-guatemala | Aprende Guatemala (Guatemala.com) | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 0 terms + meanings (paraphrased), 0 term examples; 1 usage examples (real) | 2026-10-02 |
| S78 | https://www.guatemala.com/aprende/cultura-guatemalteca/general/que-significa-palabra-chulo-guatemala | Aprende Guatemala (Guatemala.com) | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 0 terms + meanings (paraphrased), 0 term examples; 2 usage examples (real) | 2026-10-02 |
| S79 | https://www.guatemala.com/aprende/cultura-guatemalteca/general/significado-de-la-palabra-mucha-en-guatemala | Aprende Guatemala (Guatemala.com) | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 2 terms + meanings (paraphrased), 2 term examples; 2 usage examples (real) | 2026-10-02 |
| S80 | https://www.guatemala.com/aprende/cultura-guatemalteca/general/que-son-los-guatemaltequismos | Aprende Guatemala (Guatemala.com) | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 0 terms + meanings (paraphrased), 0 term examples; 3 usage examples (real) | 2026-10-02 |
| S81 | https://www.guatemala.com/aprende/cultura-guatemalteca/guatemaltequismos-para-decirle-a-alguien-que-es-inteligente | Aprende Guatemala (Guatemala.com) | © Guatemala.com, all rights reserved; facts + short attributed quotation (research/education) | GT | 1 terms + meanings (paraphrased), 1 term examples; 1 usage examples (real) | 2026-10-02 |
| S82 | https://www.soy502.com/articulo/buzzfeed-viraliza-diez-frases-guatemaltecas-ilustradas-emojis | Soy502 | © Soy502, all rights reserved; facts + short attributed quotation (research/education) | GT | 2 terms + meanings (paraphrased), 2 term examples; 3 usage examples (real) | 2026-10-02 |
| S83 | https://www.todacolombia.com/informacion-de-colombia/frases-colombianas.html | TodaColombia (Andrés G. Martínez) | © TodaColombia, all rights reserved ("se prohíbe la reproducción parcial o total"); facts + short attributed quotation (research/education) | CO | 15 terms + meanings (paraphrased), 15 term examples; 20 usage examples (real) | 2026-10-02 |
| S84 | https://getvico.com/blog/en/palabras-paisas-vocababulary-complete-list-1/ | VICO blog (getvico.com) | © VICO Rooms, Inc., all rights reserved; facts + short attributed quotation (research/education) | CO | 3 terms + meanings (paraphrased), 3 term examples; 13 usage examples (real) | 2026-10-02 |
| S85 | https://www.elnuevosiglo.com.co/cultura-y-sociedad/10-expresiones-tipicas-que-solo-los-colombianos-reconocen | El Nuevo Siglo (glossary by Babbel linguists) | © El Nuevo Siglo, reproduction prohibited without permission; facts + short attributed quotation (research/education) | CO | 6 terms + meanings (paraphrased), 6 term examples; 10 usage examples (real) | 2026-10-02 |
| S86 | https://www.inravision.gov.co/dia-de-la-madre-frases-tipicas-mama-origen | Inravisión / RTVC Sistema de Medios Públicos (Señal Memoria) | © RTVC, protected by copyright per site terms; facts + short attributed quotation (research/education) | CO | 3 terms + meanings (paraphrased), 3 term examples; 3 usage examples (real) | 2026-10-02 |
| S87 | https://locombianos.com/51-frases-tipicas-de-la-mama-colombiana/ | Locombianos | © Locombianos, all rights reserved; facts + short attributed quotation (research/education) | CO | 4 terms + meanings (paraphrased), 4 term examples; 3 usage examples (real) | 2026-10-02 |
| S88 | https://interimage.es/20-dichos-tipicos-de-las-mamas-colombianas/ | Inter-Image (blog) | © Inter Image, todos los derechos reservados; facts + short attributed quotation (research/education) | CO | 1 terms + meanings (paraphrased), 1 term examples; 1 usage examples (real) | 2026-10-02 |
| S89 | https://www.infobae.com/colombia/2026/04/28/colombiana-explico-cuales-son-las-expresiones-mas-neas-del-parlache-y-y-su-vinculo-con-medellin/ | Infobae Colombia (quoting the creator of the public account @elparche.ilustrado) | © Infobae, all rights reserved; facts + short attributed quotation (research/education) | CO | 0 terms + meanings (paraphrased), 0 term examples; 1 usage examples (real) | 2026-10-02 |

Ids S21, S32, S34–S36 were consulted but nothing was taken from them.

## Round 2 (2026-10-01): sources checked

New sources used by `raw/terms_2026-10-01.jsonl` and `raw/web_usage_2026-10-01.jsonl` (ids continue after S40 in
`../SOURCES.md`; same policy: facts paraphrased, short attributed quotations ≤ 30 words, exact per-record URL in
each record). Accessed 2026-10-01.
Notes:
- S62 (Wikcionario) examples are mostly quotations from published books, press and songs that the
  Wikcionario page itself cites; they are real usage but often older/literary, so most were used as
  *parent* sentences. Text reused under CC BY-SA 4.0 (share-alike applies to derived pairs).
- S41 (Yabla) examples marked "Caption" are real dialogue lines from Colombian TV series shown on Yabla.
- S20 (Medellín Joven) examples were written by the youth participants of the dictionary (ages 14–28).
- Learner blogs (S41–S51) and press (S52–S61) are all-rights-reserved: only facts and short attributed
  quotations for research/education.
- Existing sources reused with their original ids (new pages or previously unused examples):
- **S04** (abisai7 / diccionario-chapin): 29 new terms, 73 new usage examples, 11 curator sentences citing it.
- **S16** (FluentU): 0 new terms, 14 new usage examples, 0 curator sentences citing it.
- **S17** (FluentU): 2 new terms, 9 new usage examples, 0 curator sentences citing it.
- **S20** (Alcaldía de Medellín — Medellín Joven): 26 new terms, 45 new usage examples, 4 curator sentences citing it.

## Round 3 (2026-10-02): sources checked

New sources used by `raw/terms_2026-10-02.jsonl` and `raw/web_usage_2026-10-02.jsonl` (ids continue after S63 in
`../SOURCES.md`; same policy: facts paraphrased, short attributed quotations ≤ 30 words, exact per-record URL in
each record). Accessed 2026-10-02.
Notes:
- Every usage `example` and every term `example` is verbatim from the page at the record's `source_url`
  (checked against the fetched page text, whitespace-normalized); all records are `example_origin: "source"`.
  Rewrites are the curator's; meanings are paraphrased.
- S64–S67 (SoyMigrante.com Revista), S68–S69 (Guatemala.com), S71–S81 (Aprende Guatemala, Guatemala.com's
  explainer section) and S82 (Soy502) are all-rights-reserved press: only facts and short attributed quotations
  for research/education. Many of their examples are the outlet's own illustrative sentences for each word, so
  they read as older/general GT speech and were mostly used as *parent* sentences.
- S70 (Guate Inmortal) is a WordPress.com blog licensed CC BY 4.0 (footer: "Creative Commons Reconocimiento 4.0
  Internacional"); attribution is the per-record URL.
- Aprende Guatemala moved from `aprende.guatemala.com` to `www.guatemala.com/aprende/…`; the URLs above are the
  current canonical ones (resolved through the site's own API on 2026-10-02).
- The term `cuate` (t3-gt-021) cites S66, where it is used; its meaning was also checked against Aprende
  Guatemala's "Origen de la palabra Cuate en Guatemala"
  (https://www.guatemala.com/aprende/cultura-guatemalteca/general/origen-palabra-cuate-guatemala).
- S83–S89 (CO) are all-rights-reserved: facts + short attributed quotations only. S83 TodaColombia and
  S86–S88 are mostly sayings of parents/mothers (used as *parent* sentences); S85 El Nuevo Siglo terms are
  regional (Costa, Santander, Boyacá, Nariño).
- Term examples were taken from the same page as the usage rows, so most new-term examples are also a w3 usage
  sentence (or part of one). Assign those rows with their term in mind when splitting train/dev/test.
- Existing sources reused with their original ids (new pages or previously unused examples):
- **S04** (abisai7 / diccionario-chapin (MIT)): 4 new terms, 46 new usage examples.
- **S20** (Alcaldía de Medellín — Medellín Joven): 20 new terms, 27 new usage examples.
- **S62** (Wikcionario (Wikimedia Foundation), CC BY-SA 4.0): 20 new terms, 25 new usage examples.

## Round 4 (2026-10-06): pan-Hispanic Gen Z and Mexico

Why: on the test set David tied Goliath in Mexico and in neutral Latin American Spanish (LATAM), and the people
who tried the page with ordinary Gen Z slang (cringe, random, crush, stalkear…) saw it fail. Only 24 LATAM and 9
MX training pairs were anchored in real sentences (GT: 268, CO: 255). Same policy as before: facts paraphrased,
short attributed quotations, exact URL per record. Accessed 2026-10-06.

**Training sources** (`raw/web_usage_2026-10-06.jsonl`, all `example_origin: "source"`, rewrites by the curator):

| id | url | owner | license | country | taken |
| --- | --- | --- | --- | --- | --- |
| S90 | https://es.lingopie.com/blog/el-colorido-lenguaje-mexicano/ | Lingopie (blog en español) | © Lingopie, all rights reserved; facts + short attributed quotation (research/education) | MX | 15 usage examples (real) |
| S91 | https://www.elcorreogallego.es/sociedad/2026/07/31/cringe-shippear-diccionario-expresiones-juveniles-132965245.html | El Correo Gallego | © El Correo Gallego, all rights reserved; short attributed quotation (research/education) | LATAM | 1 usage example (real) |
| S92 | https://www.planeta.pe/noticias/actualidad/que-significa-estar-en-tu-prime-la-expresion-viral-que-todos-usan-en-redes/ | Radio Planeta (Perú) | © Radio Planeta, all rights reserved; short attributed quotation (research/education) | LATAM | 1 usage example (real) |

Real Gen Z sentences are scarce on the web pages that explain slang (most give a definition, few a sentence), so
this round's training data is mostly synthetic: `pairs/synthetic_genz.jsonl` (Gemini, LATAM + MX Gen Z terms,
validated against the term bank like every synthetic pair, never in dev, test or the probe).

**Probe sources** (`eval/probe_genz.jsonl`, held out: no page below is used for training; every sentence is
verbatim from its page, the parents' version is the curator's):

| page | owner | country of the outlet |
| --- | --- | --- |
| https://www.elespectador.com/zona-z/que-significa-aesthetic-funar-cringe-y-glow-up-este-es-el-glosario-de-la-gen-z/ | El Espectador (Zona Z) | CO |
| https://www.acis.org.co/blog/noticias-2/que-significa-dar-cringe-las-expresiones-en-ingles-que-se-estan-tomando-las-nuevas-generaciones-en-colombia-8772 | ACIS | CO |
| https://gullon.es/blog/bienestar-y-ocio/que-dice-la-gen-z/ | Gullón (blog) | ES |
| https://fad.es/planetajoven/glosario-para-entender-como-hablan-los-y-las-jovenes-de-la-generacion-z/ | Fad Juventud | ES |
| https://educayaprende.com/diccionario-generacion-z-para-padres/ | Educa y Aprende | ES |
| https://www.telediario.mx/tendencias/guia-amor-redes-sociales-que-es-shippear-ghostear-love-bombing | Telediario México | MX |
| https://androidphoria.com/curiosidades/que-significar-estar-en-su-prime | Androidphoria | ES |
| https://www.elmostrador.cl/agenda-pais/agenda-digital/2025/07/01/me-dio-cringe-el-modismo-que-define-la-incomodidad-en-la-era-digital/ | El Mostrador | CL |
| https://www.tiktok.com/@burbujadelespanol/video/7602259913288584481 | @burbujadelespanol (TikTok, video description) | — |
| https://www.elnacional.com/2024/02/delulu-es-la-solulu-lo-que-revela-sobre-la-generacion-z-esta-extrana-frase-que-utilizan-algunos-jovenes/ | El Nacional (BBC Mundo) | VE |
| https://sonilec.mx/que-significa-mid-y-como-se-usa-en-el-lenguaje-actual/ | Sonilec | MX |
| https://literalbro.com/que-significa/mood/ | LiteralBro | — |
| https://www.smythsys.es/21468/significado-de-basado-en-internet-%F0%9F%A4%94-de-donde-viene/ | SmythSys | ES |
| https://bloygo.yoigo.com/glosario/definicion-rizz/ | Bloygo (Yoigo) | ES |

All are all-rights-reserved pages: only the short example sentence is quoted, with its URL, for evaluation.
