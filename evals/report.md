# Genlingo — evaluación

Generado por `make eval` el 2026-10-04 19:28. 399 pares de prueba (web; nunca sintéticos), 399 auto_validated. `auto_validated` = validada automáticamente contra el banco de términos (`scripts/validate_test_set.py`).

## Resumen

chrF++ de corpus (0–100, más es mejor) contra la referencia humana. Latencia de extremo a extremo con el modelo ya cargado; los modelos locales corren uno a la vez en la laptop del escenario.

| modelo | rol | prompt | chrF++ | p50 | p95 | costo total | costo / 1,000 frases | tamaño | errores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma4:e2b-it-qat | base (sin ajuste) | país | 50.2 | 364 ms | 490 ms | $0 | $0 | 4.34 GB | 0 |
| gemma4:e2b-it-qat + glosario | base (sin ajuste) | país + glosario | 55.0 | 452 ms | 592 ms | $0 | $0 | 4.34 GB | 0 |
| gemma4:e4b | base (sin ajuste) | país | 48.2 | 802 ms | 1.10 s | $0 | $0 | 6.58 GB | 0 |
| genlingo-2026-10b-e2b + glosario | David candidato (LoRA, Q5_K_M) | país + glosario | 56.6 | 557 ms | 751 ms | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10b-e2b-f16 + glosario | David candidato (LoRA, f16) | país + glosario | 56.7 | 543 ms | 786 ms | $0 | $0 | 9.27 GB | 0 |
| genlingo-2026-10-e2b-q5_k_m + glosario | David candidato (LoRA, Q5_K_M) | país + glosario | 55.4 | 564 ms | 744 ms | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10-e2b + glosario | David candidato (LoRA, Q4_K_M) | país + glosario | 55.7 | 512 ms | 696 ms | $0 | $0 | 3.42 GB | 0 |
| genlingo-2026-10-e2b-f16 + glosario | David candidato (LoRA, f16) | país + glosario | 56.3 | 566 ms | 807 ms | $0 | $0 | 9.27 GB | 0 |
| genlingo-2026-09 | David candidato (LoRA, Q4_K_M) | básico | 55.0 | 391 ms | 545 ms | $0 | $0 | 3.42 GB | 0 |
| genlingo-2026-09-f16 | David candidato (LoRA, f16) | básico | 55.4 | 435 ms | 639 ms | $0 | $0 | 9.27 GB | 0 |
| genlingo-2026-10c-e2b-nomulti + léxico | David (LoRA, Q5_K_M) | país + léxico | 59.7 | 670 ms | 954 ms | $0 | $0 | 3.62 GB | 0 |
| gemini-3.8-flash | Goliath | país | 53.5 | 2.60 s | 7.64 s | $0.45 | $1.13 | — | 0 |
| gemini-3.8-flash + glosario | Goliath con el glosario de David | país + glosario | 57.0 | 3.05 s | 7.37 s | $0.51 | $1.27 | — | 2 |

Costo de Goliath con la tarifa del día del eval: $0.75 entrada / $3.75 salida por millón de tokens (vigente desde 2026-09-30).
Con la tarifa desde 2027-01-01 ($1.50 / $7.50), este mismo eval costaría $0.90 ($2.26 por 1,000 frases).

**Línea base "copiar la frase"** (devolver el texto original sin traducir): chrF++ 53.2. Un modelo que no supera esta línea no está traduciendo mejor que no hacer nada; mide cuánto del puntaje viene de palabras que la referencia comparte con el original.

## ¿Tradujo la jerga?

chrF++ premia parecerse a la referencia, y una reescritura de registro conserva casi todas las palabras: por eso copiar la frase ya saca ~50. Estas dos métricas miran solo lo que tenía que cambiar (detalle en `evals/term_accuracy.py`):

- **Jerga resuelta**: Gen Z → papás, no queda en la salida ningún término Gen Z del banco que tenía la frase; papás → Gen Z, la salida usa al menos un término Gen Z del banco del país. Mide que cambió el registro, no que el significado sea correcto.
- **Cambios acertados**: de las palabras que la referencia humana cambió respecto al original, cuántas aparecen en la salida. Mide significado, pero solo con palabras exactas: un sinónimo válido cuenta como fallo para todos.

- **Jerga correcta** y **cambios acertados con sinónimos** (enmienda 1 de `evals/niche.md`): el término producido tiene que significar lo mismo, según la tabla de contrapartes validada por significado (`data/counterparts.jsonl`); con sinónimos, una palabra cuenta si coincide la raíz o es un término enlazado.

| modelo | jerga resuelta Gen Z → papás | jerga resuelta papás → Gen Z | jerga resuelta total | cambios acertados | jerga correcta | cambios acertados (sinónimos) |
| --- | --- | --- | --- | --- | --- | --- |
| copiar la frase (línea base) | 0 % (n=226) | 3 % (n=173) | 1 % (n=399) | 0 % | 1 % (n=399) | 4 % |
| gemma4:e2b-it-qat | 95 % (n=226) | 10 % (n=173) | 58 % (n=399) | 14 % | 14 % (n=399) | 17 % |
| gemma4:e2b-it-qat + glosario | 94 % (n=226) | 20 % (n=173) | 62 % (n=399) | 23 % | 38 % (n=399) | 27 % |
| gemma4:e4b | 97 % (n=226) | 31 % (n=173) | 68 % (n=399) | 17 % | 19 % (n=399) | 21 % |
| genlingo-2026-10b-e2b + glosario | 99 % (n=226) | 59 % (n=173) | 82 % (n=399) | 22 % | 34 % (n=399) | 26 % |
| genlingo-2026-10b-e2b-f16 + glosario | 98 % (n=226) | 59 % (n=173) | 81 % (n=399) | 22 % | 34 % (n=399) | 27 % |
| genlingo-2026-10-e2b-q5_k_m + glosario | 97 % (n=226) | 43 % (n=173) | 74 % (n=399) | 18 % | 27 % (n=399) | 20 % |
| genlingo-2026-10-e2b + glosario | 95 % (n=226) | 31 % (n=173) | 67 % (n=399) | 16 % | 25 % (n=399) | 19 % |
| genlingo-2026-10-e2b-f16 + glosario | 99 % (n=226) | 42 % (n=173) | 74 % (n=399) | 19 % | 28 % (n=399) | 22 % |
| genlingo-2026-09 | 94 % (n=226) | 20 % (n=173) | 62 % (n=399) | 14 % | 18 % (n=399) | 18 % |
| genlingo-2026-09-f16 | 93 % (n=226) | 27 % (n=173) | 64 % (n=399) | 14 % | 18 % (n=399) | 18 % |
| genlingo-2026-10c-e2b-nomulti + léxico | 100 % (n=226) | 58 % (n=173) | 82 % (n=399) | 28 % | 42 % (n=399) | 32 % |
| gemini-3.8-flash | 97 % (n=226) | 51 % (n=173) | 77 % (n=399) | 25 % | 26 % (n=399) | 27 % |
| gemini-3.8-flash + glosario | 100 % (n=226) | 58 % (n=171) | 82 % (n=397) | 29 % | 38 % (n=397) | 31 % |

**David en escena:** `genlingo-2026-10c-e2b-nomulti + léxico` (3.62 GB, p50 670 ms): el archivo más pequeño a ≤ 2 puntos de `genlingo-2026-10c-e2b-nomulti + léxico` (82 % de jerga resuelta), con p50 < 1 s (empate de tamaño: gana el mayor chrF++). Resuelve 82 %.

Cara a cara con `gemini-3.8-flash` en jerga resuelta: David la resuelve y Goliath no en **49** frases; al revés en **31**.

Cara a cara con `gemini-3.8-flash + glosario` en jerga resuelta: David la resuelve y Goliath no en **36** frases; al revés en **36**.

Jerga de otro país en papás → Gen Z (p. ej. «pisto» guatemalteco en una frase mexicana): gemma4:e2b-it-qat 8, gemma4:e2b-it-qat + glosario 7, gemma4:e4b 18, genlingo-2026-10b-e2b + glosario 14, genlingo-2026-10-e2b-q5_k_m + glosario 19, genlingo-2026-10-e2b + glosario 21, genlingo-2026-09 22, genlingo-2026-10c-e2b-nomulti + léxico 16, gemini-3.8-flash 3, gemini-3.8-flash + glosario 1 (de 173).

**Lectura:** David gana también en jerga, no solo en parecido de superficie, frente a Goliath sin glosario. Compáralo con Goliath + glosario para separar lo que aporta el modelo de lo que aporta el dato.

Con el mismo glosario, Goliath resuelve 82 % de la jerga frente al 82 % de David: la ventaja de David viene de **sus datos** (el banco de términos), no de ser mejor modelo; y esos datos los tiene él, no Goliath.

## Compresión: tamaño vs jerga

Las exportaciones de `genlingo-2026-10-e2b` con el mismo prompt y glosario. La curva muestra cuánta jerga se pierde al comprimir.

![Tamaño vs jerga resuelta](compression.svg)

| variante | cuantización | imatrix | tamaño | jerga resuelta | cambios acertados | chrF++ | p50 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `genlingo-2026-10-e2b + glosario` | Q4_K_M | no | 3.42 GB | 67 % | 16 % | 55.7 | 512 ms |
| `genlingo-2026-10-e2b-q5_k_m + glosario` | Q5_K_M | no | 3.62 GB | 74 % | 18 % | 55.4 | 564 ms |
| `genlingo-2026-10-e2b-f16 + glosario` | F16 | no | 9.27 GB | 74 % | 19 % | 56.3 | 566 ms |

**imatrix (importance matrix):** antes de cuantizar, llama.cpp pasa el modelo f16 por texto de calibración y mide qué pesos influyen más; la cuantización gasta los bits ahí. Calibramos con **pares de entrenamiento** renderizados con el prompt de David (`train/quant_sweep.py`), nunca con el set de prueba: eso inflaría el eval.

### chrF++ por origen

| modelo | web |
| --- | --- |
| gemma4:e2b-it-qat | 50.2 (n=399) |
| gemma4:e2b-it-qat + glosario | 55.0 (n=399) |
| gemma4:e4b | 48.2 (n=399) |
| genlingo-2026-10b-e2b + glosario | 56.6 (n=399) |
| genlingo-2026-10b-e2b-f16 + glosario | 56.7 (n=399) |
| genlingo-2026-10-e2b-q5_k_m + glosario | 55.4 (n=399) |
| genlingo-2026-10-e2b + glosario | 55.7 (n=399) |
| genlingo-2026-10-e2b-f16 + glosario | 56.3 (n=399) |
| genlingo-2026-09 | 55.0 (n=399) |
| genlingo-2026-09-f16 | 55.4 (n=399) |
| genlingo-2026-10c-e2b-nomulti + léxico | 59.7 (n=399) |
| gemini-3.8-flash | 53.5 (n=399) |
| gemini-3.8-flash + glosario | 57.0 (n=397) |

### chrF++ por dirección

| modelo | genz_to_parent | parent_to_genz |
| --- | --- | --- |
| gemma4:e2b-it-qat | 57.0 (n=226) | 40.9 (n=173) |
| gemma4:e2b-it-qat + glosario | 64.4 (n=226) | 41.7 (n=173) |
| gemma4:e4b | 55.1 (n=226) | 38.5 (n=173) |
| genlingo-2026-10b-e2b + glosario | 63.7 (n=226) | 46.8 (n=173) |
| genlingo-2026-10b-e2b-f16 + glosario | 64.0 (n=226) | 46.5 (n=173) |
| genlingo-2026-10-e2b-q5_k_m + glosario | 62.7 (n=226) | 45.2 (n=173) |
| genlingo-2026-10-e2b + glosario | 62.4 (n=226) | 46.3 (n=173) |
| genlingo-2026-10-e2b-f16 + glosario | 63.3 (n=226) | 46.4 (n=173) |
| genlingo-2026-09 | 62.3 (n=226) | 44.8 (n=173) |
| genlingo-2026-09-f16 | 62.8 (n=226) | 45.0 (n=173) |
| genlingo-2026-10c-e2b-nomulti + léxico | 67.4 (n=226) | 49.1 (n=173) |
| gemini-3.8-flash | 61.0 (n=226) | 43.0 (n=173) |
| gemini-3.8-flash + glosario | 63.8 (n=226) | 47.6 (n=171) |

### chrF++ por país

| modelo | CO | GT | LATAM | MX |
| --- | --- | --- | --- | --- |
| gemma4:e2b-it-qat | 48.5 (n=131) | 53.1 (n=115) | 51.1 (n=75) | 48.6 (n=78) |
| gemma4:e2b-it-qat + glosario | 52.5 (n=131) | 60.0 (n=115) | 56.5 (n=75) | 50.8 (n=78) |
| gemma4:e4b | 48.0 (n=131) | 50.1 (n=115) | 48.1 (n=75) | 45.7 (n=78) |
| genlingo-2026-10b-e2b + glosario | 58.7 (n=131) | 61.2 (n=115) | 52.0 (n=75) | 50.9 (n=78) |
| genlingo-2026-10b-e2b-f16 + glosario | 58.3 (n=131) | 61.2 (n=115) | 52.6 (n=75) | 51.2 (n=78) |
| genlingo-2026-10-e2b-q5_k_m + glosario | 56.3 (n=131) | 61.2 (n=115) | 51.3 (n=75) | 49.2 (n=78) |
| genlingo-2026-10-e2b + glosario | 56.1 (n=131) | 61.0 (n=115) | 52.7 (n=75) | 50.0 (n=78) |
| genlingo-2026-10-e2b-f16 + glosario | 56.7 (n=131) | 61.7 (n=115) | 53.1 (n=75) | 50.7 (n=78) |
| genlingo-2026-09 | 54.5 (n=131) | 58.2 (n=115) | 54.3 (n=75) | 51.6 (n=78) |
| genlingo-2026-09-f16 | 55.7 (n=131) | 59.0 (n=115) | 54.0 (n=75) | 50.5 (n=78) |
| genlingo-2026-10c-e2b-nomulti + léxico | 60.4 (n=131) | 65.3 (n=115) | 56.5 (n=75) | 53.6 (n=78) |
| gemini-3.8-flash | 53.8 (n=131) | 52.9 (n=115) | 55.4 (n=75) | 51.5 (n=78) |
| gemini-3.8-flash + glosario | 54.3 (n=130) | 60.1 (n=115) | 58.9 (n=75) | 56.0 (n=77) |

## Modelo base: E2B vs E4B

Regla: el más pequeño que cumpla p50 < 1 s con el mejor chrF++.

**gemma4:e2b-it-qat**: mejor chrF++ (50.2) entre los que cumplen p50 < 1 s (p50 364 ms, 4.34 GB).

## Compresión: f16 vs cuantizado

El David de escena no se evaluó en f16 en esta corrida; estas son las comparaciones que sí tiene, cada David con su propio f16 y el mismo prompt.

| modelo | versión | tamaño | p50 | chrF++ | jerga resuelta |
| --- | --- | --- | --- | --- | --- |
| `genlingo-2026-10b-e2b + glosario` | Q5_K_M | 3.62 GB | 557 ms | 56.6 | 82 % |
| `genlingo-2026-10b-e2b-f16 + glosario` | F16 | 9.27 GB | 543 ms | 56.7 | 81 % |
| `genlingo-2026-10-e2b + glosario` | Q4_K_M | 3.42 GB | 512 ms | 55.7 | 67 % |
| `genlingo-2026-10-e2b-q5_k_m + glosario` | Q5_K_M | 3.62 GB | 564 ms | 55.4 | 74 % |
| `genlingo-2026-10-e2b-f16 + glosario` | F16 | 9.27 GB | 566 ms | 56.3 | 74 % |
| `genlingo-2026-09` | Q4_K_M | 3.42 GB | 391 ms | 55.0 | 62 % |
| `genlingo-2026-09-f16` | F16 | 9.27 GB | 435 ms | 55.4 | 64 % |

## Entrenamiento

| tag | máquina | región | ejemplos | duración | costo estimado | loss inicial → final |
| --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-10c-e2b-nomulti | Cloud Run Jobs: 1x NVIDIA L4 + 8 vCPU/32 GiB (train), 8 vCPU/32 GiB (merge + GGUF) | europe-west4 | 2271 | 45.9 min | $0.97 | 1.97 → 0.06 |

Costo = segundos facturados × tarifas por segundo de Cloud Run (GPU L4 sin redundancia zonal + vCPU + memoria; entrenamiento en la L4 + fusión y GGUF en un job de CPU). Un reentrenamiento mensual cuesta eso; la inferencia de David cuesta $0 porque corre en la laptop.

## Dónde pierde David

David gana 231 de 399 frases por chrF++ de oración. Las 10 peores derrotas:

| frase | referencia | David | Goliath | Δ chrF++ |
| --- | --- | --- | --- | --- |
| […] | se te trabó la aplicación | Tu aplicación se congeló. | Se te trabó la aplicación. | -50.5 |
| […] | ¿Qué te pasó que hoy andas con tan buena vibra? | ¿Qué te ha pasado que hoy estás tan linda? | ¿Qué te pasó que hoy andas con tanta vibra? | -48.3 |
| […] | Eres un as en ese juego | Eres el mejor en ese juego | Eres un as en ese juego | -44.3 |
| Ya andate, maje, me estás haciendo tierra con ella. | Ya andate, me estás estorbando con ella. | Ya hacéte sho, me estás haciendo perder el tiempo. | Ya andate, mano, me estás quemando con ella. | -39.8 |
| […] | Neta ya no quiero más desmadre en la casa, ¿eh? | No quiero más drama en casa. | Ya no quiero más desmadre en la casa. | -38.7 |
| […] | ¡Ese es mi morro! | ¡No manches, maje! | ¡Ese es mi gallo, la neta! | -36.8 |
| […] | Porque yo lo digo y ya, bro | Porque yo digo y pa' de una | Porque yo lo digo y ya, soporte. | -36.4 |
| […] | ¿Por qué me deja en visto, parce? | ¿Por qué no me contesta el celular, parce? | ¿Por qué me deja en visto, marica? | -35.5 |
| Mi jefa no me deja salir, la neta. | La verdad, mi mamá no me da permiso de salir. | Mi mamá no me deja salir, de verdad. | Mi mamá no me da permiso de salir, la verdad. | -33.6 |
| […] | Muy bien hecho, muchachos, se lucieron. | Se la rifaron, muchachos, qué chidos. | Muy bien hecho, muchachos, qué padre. | -32.6 |

## Metodología

- Prompts en `duel/genlingo_duel/prompts.py`, temperatura 0. Cada variante declara su prompt en la tabla: cada David con el prompt con el que se entrenó; los modelos base y Goliath con el prompt con país, y también con el glosario de David («+ glosario») para que la comparación con los datos de David sea justa y visible.
- Glosario: entradas del banco de términos recuperadas con EmbeddingGemma local; su tiempo cuenta en la latencia.
- chrF++ = sacrebleu CHRF con `word_order=2`, a nivel de corpus.
- Costo de Goliath = tokens × precio por millón vigente el día del eval (`GEMINI_PRICE_SCHEDULE`); los tokens de razonamiento se cobran como salida.
- Resultados por frase en `evals/results/`.
