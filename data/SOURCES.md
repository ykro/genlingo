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
- **Curator-written sentences:** where a source gives a term but no usable example, the curator
  wrote a minimal example and marked it `example_origin=curator` (under 30% of test candidates).
- **Test references** (`rewrite`) are written by the dataset curator from the meaning the source
  gives, never by Gemini, and are reviewed by the presenter (`make review-test`).

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

Ids S21, S32, S34–S36 were consulted but nothing was taken from them.
