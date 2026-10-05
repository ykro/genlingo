# Genlingo — evaluación en desarrollo

> **Set de desarrollo** (`data/pairs/dev_real.jsonl`): para decidir rondas de datos. Los Davids entrenados antes del 2026-10-02 vieron estos pares al entrenar, así que su número aquí es optimista.

Generado por `make eval` el 2026-10-04 19:11. 146 pares de desarrollo (web; nunca sintéticos), 146 auto_validated. `auto_validated` = validada automáticamente contra el banco de términos (`scripts/validate_test_set.py`).

## Resumen

chrF++ de corpus (0–100, más es mejor) contra la referencia humana. Latencia de extremo a extremo con el modelo ya cargado; los modelos locales corren uno a la vez en la laptop del escenario.

| modelo | rol | prompt | chrF++ | p50 | p95 | costo total | costo / 1,000 frases | tamaño | errores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-10b-e2b + glosario | David candidato (LoRA, Q5_K_M) | país + glosario | 65.3 | 592 ms | 854 ms | $0 | $0 | 3.62 GB | 0 |
| gemini-3.8-flash + glosario | Goliath con el glosario de David | país + glosario | 55.4 | 3.51 s | 9.93 s | $0.18 | $1.22 | — | 0 |
| genlingo-2026-10c-e2b + léxico | David (LoRA, Q5_K_M) | país + léxico | 61.9 | 1.99 s | 3.45 s | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10c-e2b + léxico · N-best 4 | david_nbest | país + léxico | 61.9 | 4.40 s | 6.51 s | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10c-e2b-f16 + léxico | David (LoRA, f16) | país + léxico | 62.5 | 1.33 s | 1.96 s | $0 | $0 | 9.27 GB | 0 |
| gemini-3.8-flash | Goliath | país | 51.1 | 3.60 s | 7.68 s | $0.21 | $1.43 | — | 0 |
| gemini-3.8-flash + léxico | Goliath con el glosario de David | país + léxico | 58.4 | 3.10 s | 7.71 s | $0.20 | $1.38 | — | 0 |
| genlingo-2026-10c-e2b-nomulti + léxico | David candidato (LoRA, Q5_K_M) | país + léxico | 63.2 | 809 ms | 1.14 s | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10c-e2b-nomulti-orpo + léxico | David candidato (LoRA, Q5_K_M) | país + léxico | 63.7 | 866 ms | 1.20 s | $0 | $0 | 3.62 GB | 0 |

Costo de Goliath con la tarifa del día del eval: $0.75 entrada / $3.75 salida por millón de tokens (vigente desde 2026-09-30).
Con la tarifa desde 2027-01-01 ($1.50 / $7.50), este mismo eval costaría $0.42 ($2.87 por 1,000 frases).

**Línea base "copiar la frase"** (devolver el texto original sin traducir): chrF++ 58.3. Un modelo que no supera esta línea no está traduciendo mejor que no hacer nada; mide cuánto del puntaje viene de palabras que la referencia comparte con el original.

## ¿Tradujo la jerga?

chrF++ premia parecerse a la referencia, y una reescritura de registro conserva casi todas las palabras: por eso copiar la frase ya saca ~50. Estas dos métricas miran solo lo que tenía que cambiar (detalle en `evals/term_accuracy.py`):

- **Jerga resuelta**: Gen Z → papás, no queda en la salida ningún término Gen Z del banco que tenía la frase; papás → Gen Z, la salida usa al menos un término Gen Z del banco del país. Mide que cambió el registro, no que el significado sea correcto.
- **Cambios acertados**: de las palabras que la referencia humana cambió respecto al original, cuántas aparecen en la salida. Mide significado, pero solo con palabras exactas: un sinónimo válido cuenta como fallo para todos.

- **Jerga correcta** y **cambios acertados con sinónimos** (enmienda 1 de `evals/niche.md`): el término producido tiene que significar lo mismo, según la tabla de contrapartes validada por significado (`data/counterparts.jsonl`); con sinónimos, una palabra cuenta si coincide la raíz o es un término enlazado.

| modelo | jerga resuelta Gen Z → papás | jerga resuelta papás → Gen Z | jerga resuelta total | cambios acertados | jerga correcta | cambios acertados (sinónimos) |
| --- | --- | --- | --- | --- | --- | --- |
| copiar la frase (línea base) | 0 % (n=69) | 0 % (n=70) | 0 % (n=139) | 0 % | 0 % (n=132) | 5 % |
| genlingo-2026-10b-e2b + glosario | 100 % (n=69) | 81 % (n=70) | 91 % (n=139) | 34 % | 41 % (n=132) | 38 % |
| gemini-3.8-flash + glosario | 99 % (n=69) | 74 % (n=70) | 86 % (n=139) | 31 % | 27 % (n=132) | 36 % |
| genlingo-2026-10c-e2b + léxico | 100 % (n=69) | 71 % (n=70) | 86 % (n=139) | 27 % | 36 % (n=132) | 30 % |
| genlingo-2026-10c-e2b + léxico · N-best 4 | 100 % (n=69) | 89 % (n=70) | 94 % (n=139) | 26 % | 39 % (n=132) | 30 % |
| genlingo-2026-10c-e2b-f16 + léxico | 100 % (n=69) | 76 % (n=70) | 88 % (n=139) | 26 % | 37 % (n=132) | 30 % |
| gemini-3.8-flash | 96 % (n=69) | 57 % (n=70) | 76 % (n=139) | 18 % | 14 % (n=132) | 23 % |
| gemini-3.8-flash + léxico | 100 % (n=69) | 76 % (n=70) | 88 % (n=139) | 33 % | 42 % (n=132) | 38 % |
| genlingo-2026-10c-e2b-nomulti + léxico | 100 % (n=69) | 70 % (n=70) | 85 % (n=139) | 25 % | 33 % (n=132) | 30 % |
| genlingo-2026-10c-e2b-nomulti-orpo + léxico | 100 % (n=69) | 57 % (n=70) | 78 % (n=139) | 26 % | 31 % (n=132) | 30 % |

**Mejor David en desarrollo:** `genlingo-2026-10b-e2b + glosario` (3.62 GB, p50 592 ms): el archivo más pequeño a ≤ 2 puntos de `genlingo-2026-10b-e2b + glosario` (91 % de jerga resuelta), con p50 < 1 s (empate de tamaño: gana el mayor chrF++). Resuelve 91 %.

Cara a cara con `gemini-3.8-flash + glosario` en jerga resuelta: David la resuelve y Goliath no en **13** frases; al revés en **7**.

Cara a cara con `gemini-3.8-flash` en jerga resuelta: David la resuelve y Goliath no en **27** frases; al revés en **7**.

Cara a cara con `gemini-3.8-flash + léxico` en jerga resuelta: David la resuelve y Goliath no en **11** frases; al revés en **7**.

Jerga de otro país en papás → Gen Z (p. ej. «pisto» guatemalteco en una frase mexicana): genlingo-2026-10b-e2b + glosario 1, gemini-3.8-flash + glosario 4, genlingo-2026-10c-e2b + léxico 3, gemini-3.8-flash 2, gemini-3.8-flash + léxico 2, genlingo-2026-10c-e2b-nomulti + léxico 1, genlingo-2026-10c-e2b-nomulti-orpo + léxico 1 (de 70).

**Lectura:** David gana también en jerga, no solo en parecido de superficie, frente a Goliath sin glosario. Compáralo con Goliath + glosario para separar lo que aporta el modelo de lo que aporta el dato.

Con el mismo glosario, Goliath resuelve 86 % de la jerga frente al 91 % de David: David sigue por delante incluso con el glosario compartido.

### chrF++ por origen

| modelo | web |
| --- | --- |
| genlingo-2026-10b-e2b + glosario | 65.3 (n=146) |
| gemini-3.8-flash + glosario | 55.4 (n=146) |
| genlingo-2026-10c-e2b + léxico | 61.9 (n=146) |
| genlingo-2026-10c-e2b + léxico · N-best 4 | 61.9 (n=146) |
| genlingo-2026-10c-e2b-f16 + léxico | 62.5 (n=146) |
| gemini-3.8-flash | 51.1 (n=146) |
| gemini-3.8-flash + léxico | 58.4 (n=146) |
| genlingo-2026-10c-e2b-nomulti + léxico | 63.2 (n=146) |
| genlingo-2026-10c-e2b-nomulti-orpo + léxico | 63.7 (n=146) |

### chrF++ por dirección

| modelo | genz_to_parent | parent_to_genz |
| --- | --- | --- |
| genlingo-2026-10b-e2b + glosario | 64.3 (n=76) | 66.3 (n=70) |
| gemini-3.8-flash + glosario | 59.7 (n=76) | 50.8 (n=70) |
| genlingo-2026-10c-e2b + léxico | 61.5 (n=76) | 62.3 (n=70) |
| genlingo-2026-10c-e2b + léxico · N-best 4 | 60.9 (n=76) | 63.0 (n=70) |
| genlingo-2026-10c-e2b-f16 + léxico | 62.4 (n=76) | 62.6 (n=70) |
| gemini-3.8-flash | 56.8 (n=76) | 45.0 (n=70) |
| gemini-3.8-flash + léxico | 61.7 (n=76) | 54.9 (n=70) |
| genlingo-2026-10c-e2b-nomulti + léxico | 62.8 (n=76) | 63.6 (n=70) |
| genlingo-2026-10c-e2b-nomulti-orpo + léxico | 64.1 (n=76) | 63.4 (n=70) |

### chrF++ por país

| modelo | CO | GT | LATAM | MX |
| --- | --- | --- | --- | --- |
| genlingo-2026-10b-e2b + glosario | 61.4 (n=67) | 66.5 (n=69) | 77.8 (n=2) | 86.7 (n=8) |
| gemini-3.8-flash + glosario | 53.1 (n=67) | 58.1 (n=69) | 65.3 (n=2) | 55.0 (n=8) |
| genlingo-2026-10c-e2b + léxico | 58.6 (n=67) | 64.8 (n=69) | 68.0 (n=2) | 68.6 (n=8) |
| genlingo-2026-10c-e2b + léxico · N-best 4 | 58.7 (n=67) | 64.7 (n=69) | 68.0 (n=2) | 69.1 (n=8) |
| genlingo-2026-10c-e2b-f16 + léxico | 58.9 (n=67) | 66.0 (n=69) | 68.0 (n=2) | 68.6 (n=8) |
| gemini-3.8-flash | 47.6 (n=67) | 54.1 (n=69) | 69.6 (n=2) | 56.3 (n=8) |
| gemini-3.8-flash + léxico | 54.8 (n=67) | 61.9 (n=69) | 74.7 (n=2) | 61.6 (n=8) |
| genlingo-2026-10c-e2b-nomulti + léxico | 60.2 (n=67) | 66.8 (n=69) | 68.0 (n=2) | 64.1 (n=8) |
| genlingo-2026-10c-e2b-nomulti-orpo + léxico | 61.4 (n=67) | 65.6 (n=69) | 71.3 (n=2) | 68.8 (n=8) |

## Modelo base: E2B vs E4B

Regla: el más pequeño que cumpla p50 < 1 s con el mejor chrF++.

Ningún modelo base cumple p50 < 1 s.

## Compresión: f16 vs Q5_K_M

| versión | tamaño | p50 | chrF++ |
| --- | --- | --- | --- |
| f16 | 9.27 GB | 1.33 s | 62.5 |
| Q5_K_M | 3.62 GB | 1.99 s | 61.9 |

## Entrenamiento

| tag | máquina | región | ejemplos | duración | costo estimado | loss inicial → final |
| --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-10c-e2b | Cloud Run Jobs: 1x NVIDIA L4 + 8 vCPU/32 GiB (train), 8 vCPU/32 GiB (merge + GGUF) | europe-west4 | 2972 | 64.2 min | $1.41 | 2.19 → 0.04 |

Costo = segundos facturados × tarifas por segundo de Cloud Run (GPU L4 sin redundancia zonal + vCPU + memoria; entrenamiento en la L4 + fusión y GGUF en un job de CPU). Un reentrenamiento mensual cuesta eso; la inferencia de David cuesta $0 porque corre en la laptop.

## Dónde pierde David

David gana 84 de 146 frases por chrF++ de oración. Las 10 peores derrotas:

| frase | referencia | David | Goliath | Δ chrF++ |
| --- | --- | --- | --- | --- |
| ¡Puchis! ¿Y esta qué onda? | […] | ¡Púchica! ¿Y cómo está? | ¡Púchica! ¿Y a esta qué le picó? | -41.9 |
| ¡Casi me muero del susto, maje! | […] | ¡Me voy a ahogar del miedo! | ¡Casi me da el patatús, vos! | -41.6 |
| Este maje no suelta el pisto ni a palos | […] | Este muchacho no suelta los lenes ni a palos | Ese tipo es bien agarrado, no gasta pero ni a la fuerza | -38.0 |
| Es un tipo chilero | Es un maje bien calidá | Es un vato, maje | Es un maje bien de ahuevo | -37.2 |
| Qué nítido tu cel | Qué chilero tu teléfono | Qué chulo tu celular | Qué chilero tu celular | -36.5 |
| ¡Qué cuca tu camiseta nueva! | […] | ¡Qué bonita tu camiseta nueva! | ¡Qué chévere tu camiseta nueva! | -33.0 |
| ¡Está muy bonito, hombre! | […] | ¡Está bien aesthetic, maje! | ¡Está bien de ahuevo, vos! | -31.1 |
| Le traje un detallito y tengo un camello pa' usted, parce. | […] | Le traje un detalle y tengo un trabajo para usted. | Le traje un regalito y le tengo un trabajito, mi hermano. | -30.3 |
| ¡Porque soy tu cucho y ya, parce! | […] | ¡Porque soy tu papá y ya! | ¡Porque soy su papá y punto, mijo! | -28.0 |
| […] | Vos, ¿por qué sos tan metido, maje? | Vos por qué sos tan chive? | Maje, ¿por qué sos tan metido? | -27.9 |

## Metodología

- Prompts en `duel/genlingo_duel/prompts.py`, temperatura 0. Cada variante declara su prompt en la tabla: cada David con el prompt con el que se entrenó; los modelos base y Goliath con el prompt con país, y también con el glosario de David («+ glosario») para que la comparación con los datos de David sea justa y visible.
- Glosario: entradas del banco de términos recuperadas con EmbeddingGemma local; su tiempo cuenta en la latencia.
- chrF++ = sacrebleu CHRF con `word_order=2`, a nivel de corpus.
- Costo de Goliath = tokens × precio por millón vigente el día del eval (`GEMINI_PRICE_SCHEDULE`); los tokens de razonamiento se cobran como salida.
- Resultados por frase en `evals/results/`.
