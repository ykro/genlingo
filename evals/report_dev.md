# Genlingo — evaluación en desarrollo

> **Set de desarrollo** (`data/pairs/dev_real.jsonl`): para decidir rondas de datos. Los Davids entrenados antes del 2026-10-02 vieron estos pares al entrenar, así que su número aquí es optimista.

Generado por `make eval` el 2026-10-07 20:46. 280 pares de desarrollo (web; nunca sintéticos), 280 auto_validated. `auto_validated` = validada automáticamente contra el banco de términos (`scripts/validate_test_set.py`).

## Resumen

chrF++ de corpus (0–100, más es mejor) contra la referencia humana. Latencia de extremo a extremo con el modelo ya cargado; los modelos de Ollama corren uno a la vez en la GPU del job del eval.

| modelo | rol | prompt | chrF++ | p50 | p95 | costo total | costo / 1,000 frases | tamaño | errores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-10d-e2b + léxico | David (LoRA, Q5_K_M) | país + léxico | 66.1 | 278 ms | 486 ms | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10e-e2b + léxico | David candidato (LoRA, Q5_K_M) | país + léxico | 69.8 | 275 ms | 503 ms | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10e-e2b-nocombo + léxico | David candidato (LoRA, Q5_K_M) | país + léxico | 69.4 | 273 ms | 504 ms | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10e-e2b-webonly + léxico | David candidato (LoRA, Q5_K_M) | país + léxico | 69.5 | 271 ms | 502 ms | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10e-e2b-all + léxico | David candidato (LoRA, Q5_K_M) | país + léxico | 69.9 | 272 ms | 502 ms | $0 | $0 | 3.62 GB | 0 |
| gemini-3.8-flash | Goliath | país | 53.0 | 3.38 s | 8.72 s | $0.31 | $1.11 | — | 1 |
| gemini-3.8-flash + léxico | Goliath con el glosario de David | país + léxico | 60.6 | 3.40 s | 10.19 s | $0.37 | $1.33 | — | 0 |
| genlingo-2026-10e-e2b-v2 + léxico | David candidato (LoRA, Q5_K_M) | país + léxico | 68.3 | 270 ms | 497 ms | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10e-e2b-v2-nocombo + léxico | David candidato (LoRA, Q5_K_M) | país + léxico | 69.6 | 270 ms | 492 ms | $0 | $0 | 3.62 GB | 0 |

Costo de Goliath con la tarifa del día del eval: $0.75 entrada / $3.75 salida por millón de tokens (vigente desde 2026-09-30).
Con la tarifa desde 2027-01-01 ($1.50 / $7.50), este mismo eval costaría $0.62 ($2.23 por 1,000 frases).

**Línea base "copiar la frase"** (devolver el texto original sin traducir): chrF++ 61.3. Un modelo que no supera esta línea no está traduciendo mejor que no hacer nada; mide cuánto del puntaje viene de palabras que la referencia comparte con el original.

## ¿Tradujo la jerga?

chrF++ premia parecerse a la referencia, y una reescritura de registro conserva casi todas las palabras: por eso copiar la frase ya saca ~50. Estas dos métricas miran solo lo que tenía que cambiar (detalle en `evals/term_accuracy.py`):

- **Jerga resuelta**: Gen Z → papás, no queda en la salida ningún término Gen Z del banco que tenía la frase; papás → Gen Z, la salida usa al menos un término Gen Z del banco del país. Mide que cambió el registro, no que el significado sea correcto.
- **Cambios acertados**: de las palabras que la referencia humana cambió respecto al original, cuántas aparecen en la salida. Mide significado, pero solo con palabras exactas: un sinónimo válido cuenta como fallo para todos.

- **Jerga correcta** (enmienda 1 de `evals/niche.md`, la misma revisión ✓/✗ de la página, `duel/genlingo_duel/term_check.py`): la frase cuenta si cada término de jerga sale bien. Gen Z → papás: la jerga desaparece y en su lugar queda el significado llano (su significado en el banco, su contraparte de papás o lo que puso ahí la referencia humana), sin otra jerga de ningún país. Papás → Gen Z: la salida usa jerga válida para el país de la frase (la contraparte validada por significado, `data/counterparts.jsonl`, o lo que usó la referencia); la misma idea con jerga de otro país no cuenta.
- **Cambios acertados con sinónimos**: una palabra cuenta si coincide la raíz o es un término enlazado.

| modelo | jerga resuelta Gen Z → papás | jerga resuelta papás → Gen Z | jerga resuelta total | cambios acertados | jerga correcta | cambios acertados (sinónimos) |
| --- | --- | --- | --- | --- | --- | --- |
| copiar la frase (línea base) | 0 % (n=123) | 1 % (n=135) | 0 % (n=258) | 0 % | 0 % (n=241) | 3 % |
| genlingo-2026-10d-e2b + léxico | 100 % (n=123) | 70 % (n=135) | 84 % (n=258) | 28 % | 49 % (n=241) | 32 % |
| genlingo-2026-10e-e2b + léxico | 99 % (n=123) | 68 % (n=135) | 83 % (n=258) | 36 % | 58 % (n=241) | 39 % |
| genlingo-2026-10e-e2b-nocombo + léxico | 100 % (n=123) | 67 % (n=135) | 83 % (n=258) | 35 % | 53 % (n=241) | 39 % |
| genlingo-2026-10e-e2b-webonly + léxico | 99 % (n=123) | 70 % (n=135) | 84 % (n=258) | 35 % | 56 % (n=241) | 38 % |
| genlingo-2026-10e-e2b-all + léxico | 100 % (n=123) | 66 % (n=135) | 82 % (n=258) | 36 % | 57 % (n=241) | 39 % |
| gemini-3.8-flash | 97 % (n=122) | 64 % (n=135) | 79 % (n=257) | 28 % | 40 % (n=240) | 31 % |
| gemini-3.8-flash + léxico | 98 % (n=123) | 73 % (n=135) | 85 % (n=258) | 35 % | 59 % (n=241) | 38 % |
| genlingo-2026-10e-e2b-v2 + léxico | 99 % (n=123) | 73 % (n=135) | 85 % (n=258) | 36 % | 59 % (n=241) | 39 % |
| genlingo-2026-10e-e2b-v2-nocombo + léxico | 97 % (n=123) | 68 % (n=135) | 82 % (n=258) | 35 % | 54 % (n=241) | 39 % |

**Mejor David en desarrollo:** `genlingo-2026-10e-e2b-webonly + léxico` (3.62 GB, p50 271 ms): el archivo más pequeño a ≤ 2 puntos de `genlingo-2026-10e-e2b-v2 + léxico` (85 % de jerga resuelta), con p50 < 1 s (empate de tamaño: gana el mayor chrF++). Resuelve 84 %.

Cara a cara con `gemini-3.8-flash` en jerga resuelta: David la resuelve y Goliath no en **32** frases; al revés en **20**.

Cara a cara con `gemini-3.8-flash + léxico` en jerga resuelta: David la resuelve y Goliath no en **16** frases; al revés en **18**.

Jerga de otro país en papás → Gen Z (p. ej. «pisto» guatemalteco en una frase mexicana): genlingo-2026-10d-e2b + léxico 3, genlingo-2026-10e-e2b + léxico 2, genlingo-2026-10e-e2b-nocombo + léxico 1, genlingo-2026-10e-e2b-webonly + léxico 1, genlingo-2026-10e-e2b-all + léxico 1, gemini-3.8-flash 4, gemini-3.8-flash + léxico 0, genlingo-2026-10e-e2b-v2 + léxico 3, genlingo-2026-10e-e2b-v2-nocombo + léxico 1 (de 135).

**Lectura:** David gana también en jerga, no solo en parecido de superficie, frente a Goliath sin glosario. Compáralo con Goliath + glosario para separar lo que aporta el modelo de lo que aporta el dato.

Con el mismo glosario, Goliath resuelve 85 % de la jerga frente al 84 % de David: la ventaja de David viene de **sus datos** (el banco de términos), no de ser mejor modelo; y esos datos los tiene él, no Goliath.

### chrF++ por origen

| modelo | web |
| --- | --- |
| genlingo-2026-10d-e2b + léxico | 66.1 (n=280) |
| genlingo-2026-10e-e2b + léxico | 69.8 (n=280) |
| genlingo-2026-10e-e2b-nocombo + léxico | 69.4 (n=280) |
| genlingo-2026-10e-e2b-webonly + léxico | 69.5 (n=280) |
| genlingo-2026-10e-e2b-all + léxico | 69.9 (n=280) |
| gemini-3.8-flash | 53.0 (n=279) |
| gemini-3.8-flash + léxico | 60.6 (n=280) |
| genlingo-2026-10e-e2b-v2 + léxico | 68.3 (n=280) |
| genlingo-2026-10e-e2b-v2-nocombo + léxico | 69.6 (n=280) |

### chrF++ por dirección

| modelo | genz_to_parent | parent_to_genz |
| --- | --- | --- |
| genlingo-2026-10d-e2b + léxico | 67.2 (n=145) | 65.0 (n=135) |
| genlingo-2026-10e-e2b + léxico | 72.4 (n=145) | 66.8 (n=135) |
| genlingo-2026-10e-e2b-nocombo + léxico | 70.5 (n=145) | 68.2 (n=135) |
| genlingo-2026-10e-e2b-webonly + léxico | 70.9 (n=145) | 67.8 (n=135) |
| genlingo-2026-10e-e2b-all + léxico | 71.5 (n=145) | 68.0 (n=135) |
| gemini-3.8-flash | 57.0 (n=144) | 48.6 (n=135) |
| gemini-3.8-flash + léxico | 61.6 (n=145) | 59.5 (n=135) |
| genlingo-2026-10e-e2b-v2 + léxico | 70.8 (n=145) | 65.4 (n=135) |
| genlingo-2026-10e-e2b-v2-nocombo + léxico | 71.5 (n=145) | 67.3 (n=135) |

### chrF++ por país

| modelo | CO | GT | LATAM | MX |
| --- | --- | --- | --- | --- |
| genlingo-2026-10d-e2b + léxico | 65.9 (n=110) | 71.7 (n=85) | 61.5 (n=48) | 63.0 (n=37) |
| genlingo-2026-10e-e2b + léxico | 68.1 (n=110) | 72.5 (n=85) | 68.7 (n=48) | 72.7 (n=37) |
| genlingo-2026-10e-e2b-nocombo + léxico | 66.6 (n=110) | 72.0 (n=85) | 71.4 (n=48) | 69.9 (n=37) |
| genlingo-2026-10e-e2b-webonly + léxico | 67.5 (n=110) | 72.1 (n=85) | 69.7 (n=48) | 70.2 (n=37) |
| genlingo-2026-10e-e2b-all + léxico | 68.8 (n=110) | 71.9 (n=85) | 69.9 (n=48) | 68.8 (n=37) |
| gemini-3.8-flash | 51.1 (n=110) | 55.0 (n=84) | 55.6 (n=48) | 49.9 (n=37) |
| gemini-3.8-flash + léxico | 59.1 (n=110) | 63.5 (n=85) | 62.8 (n=48) | 54.1 (n=37) |
| genlingo-2026-10e-e2b-v2 + léxico | 66.4 (n=110) | 71.7 (n=85) | 68.0 (n=48) | 67.6 (n=37) |
| genlingo-2026-10e-e2b-v2-nocombo + léxico | 67.5 (n=110) | 72.2 (n=85) | 69.4 (n=48) | 71.9 (n=37) |

## Modelo base: E2B vs E4B

Regla: el más pequeño que cumpla p50 < 1 s con el mejor chrF++.

Ningún modelo base cumple p50 < 1 s.

## Compresión: f16 vs Q5_K_M

Esta ejecución no incluyó ningún David en f16; para compararlo, publica su f16 (`KEEP_F16=1` en `make train`) antes de `make eval`.

## Entrenamiento

| tag | máquina | región | ejemplos | duración | costo estimado | loss inicial → final |
| --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-10d-e2b | Cloud Run Jobs: 1x NVIDIA L4 + 8 vCPU/32 GiB (train), 8 vCPU/32 GiB (merge + GGUF) | europe-west4 | 3880 | 67.5 min | $1.49 | 2.08 → 0.05 |

Costo = segundos facturados × tarifas por segundo de Cloud Run (GPU L4 sin redundancia zonal + vCPU + memoria; entrenamiento en la L4 + fusión y GGUF en un job de CPU). Un reentrenamiento mensual cuesta eso.

## Dónde pierde David

David gana 199 de 279 frases por chrF++ de oración. Las 10 peores derrotas entre las frases de fuentes abiertas (las demás no se pueden reproducir aquí):

| frase | referencia | David | Goliath | Δ chrF++ |
| --- | --- | --- | --- | --- |
| Qué nítido tu cel | Qué chilero tu teléfono | Qué chulo tu celular | Qué chilero tu teléfono | -76.0 |
| Hágame un favorcito, parce, présteme mil pesos. | Hágame una parada, hermano, présteme mil pesos. | Hágame un favor, por favor, présteme mil pesos. | Hágame un favorcito, hermano, présteme mil pesos. | -17.6 |
| ¡No manches! Ya se nos hizo tarde para la misa. | ¡Újule! Ya se nos hizo tarde para la misa. | ¡Qué barbaridad! Ya se nos hizo tarde para la misa. | ¡Híjole! Ya se nos hizo tarde para la misa. | -7.7 |
| No me estés dando lata, güey, que tengo que acabar la comida. | No me estés enchinchando, que tengo que terminar la comida. | No me estés molestando, que tengo que acabar la comida. | No me estés molestando, mano, que tengo que terminar de hacer la comida. | -7.3 |
| De ley que va a llover hoy | Seguro que va a llover hoy. | Cabal que va a llover hoy | De plano que va a llover hoy | -2.9 |
| Mire cómo quedó de peye esa camiseta de tanto lavarla. | Mire cómo se jetió esa camiseta de tanto lavarla | Mire cómo quedó de muy mala calidad esa camiseta de tanto lavarla. | Mire cómo quedó de vuelta nada esa camiseta de tanto lavarla. | -1.4 |
| Desde que se cambió de colegio anda bien caquero. | Desde que se cambió de colegio anda muy presumido. | Desde que se cambió de colegio anda bien agarrado. | Desde que se cambió de colegio anda bien creído. | -0.9 |
| Ya ni salgo, la rodilla me tiene bien gacho. | Ya ni salgo, ando muy malito de la rodilla. | Ya ni salgo, la rodilla me está dando un dolor terrible. | Ya ni salgo, la rodilla me trae bien amolado. | -0.6 |
| No me estés enchinchando, que tengo que terminar la comida. | No me estés dando lata, güey, que tengo que acabar la comida. | No me estés distraiendo, que tengo que terminar la comida. | No me estés castrando, que tengo que terminar la comida. | -0.3 |
| Toca ponerse las pilas en matemáticas porque nos fue chimbo en el parcial. | Hay que apretar en matemáticas porque la previa fue floja. | Toca esforzarse en matemáticas porque nos fue mal en el examen. | Toca ponerse juiciosos con matemáticas porque nos fue de la patada en el parcial. | -0.2 |

## Metodología

- Prompts en `duel/genlingo_duel/prompts.py`, temperatura 0. Cada variante declara su prompt en la tabla: cada David con el prompt con el que se entrenó; los modelos base y Goliath con el prompt con país, y también con el glosario de David («+ glosario») para que la comparación con los datos de David sea justa y visible.
- Glosario: entradas del banco de términos recuperadas con EmbeddingGemma local; su tiempo cuenta en la latencia.
- chrF++ = sacrebleu CHRF con `word_order=2`, a nivel de corpus.
- Costo de Goliath = tokens × precio por millón vigente el día del eval (`GEMINI_PRICE_SCHEDULE`); los tokens de razonamiento se cobran como salida.
- Resultados por frase en `evals/results/`.
