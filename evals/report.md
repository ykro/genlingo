# Genlingo — evaluación

Generado por `make eval` el 2026-10-07 21:54. 399 pares de prueba (web; nunca sintéticos), 399 auto_validated. `auto_validated` = validada automáticamente contra el banco de términos (`scripts/validate_test_set.py`).

## Resumen

chrF++ de corpus (0–100, más es mejor) contra la referencia humana. Latencia de extremo a extremo con el modelo ya cargado; los modelos de Ollama corren uno a la vez en la GPU del job del eval.

| modelo | rol | prompt | chrF++ | p50 | p95 | costo total | costo / 1,000 frases | tamaño | errores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-10-e2b + glosario | David candidato (LoRA, Q4_K_M) | país + glosario | 55.9 | 199 ms | 296 ms | $0 | $0 | 3.42 GB | 0 |
| genlingo-2026-10-e2b-f16 + glosario | David candidato (LoRA, f16) | país + glosario | 56.3 | 360 ms | 558 ms | $0 | $0 | 9.27 GB | 0 |
| genlingo-2026-09 | David candidato (LoRA, Q4_K_M) | básico | 54.9 | 155 ms | 232 ms | $0 | $0 | 3.42 GB | 0 |
| genlingo-2026-10c-e2b-nomulti + léxico | David candidato (LoRA, Q5_K_M) | país + léxico | 59.0 | 249 ms | 332 ms | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10c-e2b-nomulti-f16 + léxico | David candidato (LoRA, f16) | país + léxico | 59.2 | 387 ms | 570 ms | $0 | $0 | 9.27 GB | 0 |
| genlingo-2026-10b-e2b + glosario | David candidato (LoRA, Q5_K_M) | país + glosario | 56.5 | 214 ms | 313 ms | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10-e2b-q5_k_m + glosario | David candidato (LoRA, Q5_K_M) | país + glosario | 55.6 | 216 ms | 305 ms | $0 | $0 | 3.62 GB | 0 |
| gemma4:e2b-it-qat | base (sin ajuste) | país | 50.3 | 152 ms | 222 ms | $0 | $0 | 4.34 GB | 0 |
| gemma4:e2b-it-qat + léxico | base (sin ajuste) | país + léxico | 55.0 | 228 ms | 298 ms | $0 | $0 | 4.34 GB | 0 |
| gemma4:e4b | base (sin ajuste) | país | 48.2 | 222 ms | 323 ms | $0 | $0 | 6.58 GB | 0 |
| gemini-3.8-flash | Goliath | país | 53.2 | 3.49 s | 9.90 s | $0.48 | $1.22 | — | 1 |
| gemini-3.8-flash + léxico | Goliath con el glosario de David | país + léxico | 56.9 | 3.28 s | 9.57 s | $0.54 | $1.34 | — | 0 |
| genlingo-2026-10e-e2b + léxico | David (LoRA, Q5_K_M) | país + léxico | 60.7 | 253 ms | 344 ms | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10e-e2b-f16 + léxico | David (LoRA, f16) | país + léxico | 60.9 | 394 ms | 587 ms | $0 | $0 | 9.27 GB | 0 |
| genlingo-2026-10d-e2b + léxico | David candidato (LoRA, Q5_K_M) | país + léxico | 59.8 | 256 ms | 344 ms | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10d-e2b-f16 + léxico | David candidato (LoRA, f16) | país + léxico | 59.4 | 402 ms | 583 ms | $0 | $0 | 9.27 GB | 0 |

Costo de Goliath con la tarifa del día del eval: $0.75 entrada / $3.75 salida por millón de tokens (vigente desde 2026-09-30).
Con la tarifa desde 2027-01-01 ($1.50 / $7.50), este mismo eval costaría $0.97 ($2.43 por 1,000 frases).

**Línea base "copiar la frase"** (devolver el texto original sin traducir): chrF++ 53.2. Un modelo que no supera esta línea no está traduciendo mejor que no hacer nada; mide cuánto del puntaje viene de palabras que la referencia comparte con el original.

## ¿Tradujo la jerga?

chrF++ premia parecerse a la referencia, y una reescritura de registro conserva casi todas las palabras: por eso copiar la frase ya saca ~50. Estas dos métricas miran solo lo que tenía que cambiar (detalle en `evals/term_accuracy.py`):

- **Jerga resuelta**: Gen Z → papás, no queda en la salida ningún término Gen Z del banco que tenía la frase; papás → Gen Z, la salida usa al menos un término Gen Z del banco del país. Mide que cambió el registro, no que el significado sea correcto.
- **Cambios acertados**: de las palabras que la referencia humana cambió respecto al original, cuántas aparecen en la salida. Mide significado, pero solo con palabras exactas: un sinónimo válido cuenta como fallo para todos.

- **Jerga correcta** (enmienda 1 de `evals/niche.md`, la misma revisión ✓/✗ de la página, `duel/genlingo_duel/term_check.py`): la frase cuenta si cada término de jerga sale bien. Gen Z → papás: la jerga desaparece y en su lugar queda el significado llano (su significado en el banco, su contraparte de papás o lo que puso ahí la referencia humana), sin otra jerga de ningún país. Papás → Gen Z: la salida usa jerga válida para el país de la frase (la contraparte validada por significado, `data/counterparts.jsonl`, o lo que usó la referencia); la misma idea con jerga de otro país no cuenta.
- **Cambios acertados con sinónimos**: una palabra cuenta si coincide la raíz o es un término enlazado.

| modelo | jerga resuelta Gen Z → papás | jerga resuelta papás → Gen Z | jerga resuelta total | cambios acertados | jerga correcta | cambios acertados (sinónimos) |
| --- | --- | --- | --- | --- | --- | --- |
| copiar la frase (línea base) | 0 % (n=226) | 3 % (n=173) | 1 % (n=399) | 0 % | 1 % (n=399) | 4 % |
| genlingo-2026-10-e2b + glosario | 96 % (n=226) | 29 % (n=173) | 67 % (n=399) | 17 % | 33 % (n=399) | 20 % |
| genlingo-2026-10-e2b-f16 + glosario | 98 % (n=226) | 34 % (n=173) | 70 % (n=399) | 18 % | 35 % (n=399) | 22 % |
| genlingo-2026-09 | 93 % (n=226) | 21 % (n=173) | 62 % (n=399) | 14 % | 23 % (n=399) | 18 % |
| genlingo-2026-10c-e2b-nomulti + léxico | 100 % (n=226) | 50 % (n=173) | 78 % (n=399) | 26 % | 49 % (n=399) | 30 % |
| genlingo-2026-10c-e2b-nomulti-f16 + léxico | 99 % (n=226) | 54 % (n=173) | 80 % (n=399) | 28 % | 49 % (n=399) | 32 % |
| genlingo-2026-10b-e2b + glosario | 99 % (n=226) | 53 % (n=173) | 79 % (n=399) | 23 % | 41 % (n=399) | 27 % |
| genlingo-2026-10-e2b-q5_k_m + glosario | 97 % (n=226) | 36 % (n=173) | 71 % (n=399) | 17 % | 33 % (n=399) | 21 % |
| gemma4:e2b-it-qat | 94 % (n=226) | 10 % (n=173) | 58 % (n=399) | 14 % | 21 % (n=399) | 17 % |
| gemma4:e2b-it-qat + léxico | 98 % (n=226) | 16 % (n=173) | 62 % (n=399) | 25 % | 47 % (n=399) | 29 % |
| gemma4:e4b | 98 % (n=226) | 31 % (n=173) | 69 % (n=399) | 17 % | 27 % (n=399) | 21 % |
| gemini-3.8-flash | 97 % (n=226) | 51 % (n=172) | 77 % (n=398) | 25 % | 34 % (n=398) | 27 % |
| gemini-3.8-flash + léxico | 100 % (n=226) | 57 % (n=173) | 81 % (n=399) | 25 % | 48 % (n=399) | 28 % |
| genlingo-2026-10e-e2b + léxico | 100 % (n=226) | 57 % (n=173) | 81 % (n=399) | 29 % | 58 % (n=399) | 33 % |
| genlingo-2026-10e-e2b-f16 + léxico | 100 % (n=226) | 54 % (n=173) | 80 % (n=399) | 30 % | 56 % (n=399) | 34 % |
| genlingo-2026-10d-e2b + léxico | 100 % (n=226) | 50 % (n=173) | 78 % (n=399) | 28 % | 54 % (n=399) | 32 % |
| genlingo-2026-10d-e2b-f16 + léxico | 100 % (n=226) | 53 % (n=173) | 80 % (n=399) | 27 % | 53 % (n=399) | 30 % |

**David de la página:** `genlingo-2026-10e-e2b + léxico` (3.62 GB, p50 253 ms): el archivo más pequeño a ≤ 2 puntos de `genlingo-2026-10e-e2b + léxico` (81 % de jerga resuelta), con p50 < 1 s (empate de tamaño: gana el mayor chrF++). Resuelve 81 %.

Cara a cara con `gemini-3.8-flash` en jerga resuelta: David la resuelve y Goliath no en **46** frases; al revés en **30**.

Cara a cara con `gemini-3.8-flash + léxico` en jerga resuelta: David la resuelve y Goliath no en **32** frases; al revés en **33**.

Jerga de otro país en papás → Gen Z (p. ej. «pisto» guatemalteco en una frase mexicana): genlingo-2026-10-e2b + glosario 13, genlingo-2026-09 20, genlingo-2026-10c-e2b-nomulti + léxico 10, genlingo-2026-10b-e2b + glosario 14, genlingo-2026-10-e2b-q5_k_m + glosario 16, gemma4:e2b-it-qat 7, gemma4:e2b-it-qat + léxico 3, gemma4:e4b 16, gemini-3.8-flash 4, gemini-3.8-flash + léxico 1, genlingo-2026-10e-e2b + léxico 4, genlingo-2026-10d-e2b + léxico 6 (de 173).

**Lectura:** David gana también en jerga, no solo en parecido de superficie, frente a Goliath sin glosario. Compáralo con Goliath + glosario para separar lo que aporta el modelo de lo que aporta el dato.

Con el mismo glosario, Goliath resuelve 81 % de la jerga frente al 81 % de David: la ventaja de David viene de **sus datos** (el banco de términos), no de ser mejor modelo; y esos datos los tiene él, no Goliath.

## Compresión: tamaño vs jerga

Las exportaciones de `genlingo-2026-10-e2b` con el mismo prompt y glosario. La curva muestra cuánta jerga se pierde al comprimir.

![Tamaño vs jerga resuelta](compression.svg)

| variante | cuantización | imatrix | tamaño | jerga resuelta | cambios acertados | chrF++ | p50 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `genlingo-2026-10-e2b + glosario` | Q4_K_M | no | 3.42 GB | 67 % | 17 % | 55.9 | 199 ms |
| `genlingo-2026-10-e2b-q5_k_m + glosario` | Q5_K_M | no | 3.62 GB | 71 % | 17 % | 55.6 | 216 ms |
| `genlingo-2026-10-e2b-f16 + glosario` | F16 | no | 9.27 GB | 70 % | 18 % | 56.3 | 360 ms |

**imatrix (importance matrix):** antes de cuantizar, llama.cpp pasa el modelo f16 por texto de calibración y mide qué pesos influyen más; la cuantización gasta los bits ahí. Calibramos con **pares de entrenamiento** renderizados con el prompt de David (`train/quant_sweep.py`), nunca con el set de prueba: eso inflaría el eval.

### chrF++ por origen

| modelo | web |
| --- | --- |
| genlingo-2026-10-e2b + glosario | 55.9 (n=399) |
| genlingo-2026-10-e2b-f16 + glosario | 56.3 (n=399) |
| genlingo-2026-09 | 54.9 (n=399) |
| genlingo-2026-10c-e2b-nomulti + léxico | 59.0 (n=399) |
| genlingo-2026-10c-e2b-nomulti-f16 + léxico | 59.2 (n=399) |
| genlingo-2026-10b-e2b + glosario | 56.5 (n=399) |
| genlingo-2026-10-e2b-q5_k_m + glosario | 55.6 (n=399) |
| gemma4:e2b-it-qat | 50.3 (n=399) |
| gemma4:e2b-it-qat + léxico | 55.0 (n=399) |
| gemma4:e4b | 48.2 (n=399) |
| gemini-3.8-flash | 53.2 (n=398) |
| gemini-3.8-flash + léxico | 56.9 (n=399) |
| genlingo-2026-10e-e2b + léxico | 60.7 (n=399) |
| genlingo-2026-10e-e2b-f16 + léxico | 60.9 (n=399) |
| genlingo-2026-10d-e2b + léxico | 59.8 (n=399) |
| genlingo-2026-10d-e2b-f16 + léxico | 59.4 (n=399) |

### chrF++ por dirección

| modelo | genz_to_parent | parent_to_genz |
| --- | --- | --- |
| genlingo-2026-10-e2b + glosario | 62.7 (n=226) | 46.5 (n=173) |
| genlingo-2026-10-e2b-f16 + glosario | 63.4 (n=226) | 46.5 (n=173) |
| genlingo-2026-09 | 62.3 (n=226) | 44.6 (n=173) |
| genlingo-2026-10c-e2b-nomulti + léxico | 67.1 (n=226) | 47.9 (n=173) |
| genlingo-2026-10c-e2b-nomulti-f16 + léxico | 67.2 (n=226) | 48.2 (n=173) |
| genlingo-2026-10b-e2b + glosario | 63.8 (n=226) | 46.3 (n=173) |
| genlingo-2026-10-e2b-q5_k_m + glosario | 62.7 (n=226) | 45.8 (n=173) |
| gemma4:e2b-it-qat | 56.8 (n=226) | 41.2 (n=173) |
| gemma4:e2b-it-qat + léxico | 64.3 (n=226) | 41.9 (n=173) |
| gemma4:e4b | 54.9 (n=226) | 38.9 (n=173) |
| gemini-3.8-flash | 60.1 (n=226) | 43.4 (n=172) |
| gemini-3.8-flash + léxico | 63.1 (n=226) | 48.2 (n=173) |
| genlingo-2026-10e-e2b + léxico | 69.5 (n=226) | 48.5 (n=173) |
| genlingo-2026-10e-e2b-f16 + léxico | 70.0 (n=226) | 48.3 (n=173) |
| genlingo-2026-10d-e2b + léxico | 68.4 (n=226) | 47.9 (n=173) |
| genlingo-2026-10d-e2b-f16 + léxico | 67.8 (n=226) | 47.8 (n=173) |

### chrF++ por país

| modelo | CO | GT | LATAM | MX |
| --- | --- | --- | --- | --- |
| genlingo-2026-10-e2b + glosario | 56.1 (n=131) | 61.2 (n=115) | 53.0 (n=75) | 50.8 (n=78) |
| genlingo-2026-10-e2b-f16 + glosario | 56.6 (n=131) | 61.4 (n=115) | 54.1 (n=75) | 50.8 (n=78) |
| genlingo-2026-09 | 54.2 (n=131) | 58.1 (n=115) | 54.5 (n=75) | 51.7 (n=78) |
| genlingo-2026-10c-e2b-nomulti + léxico | 59.3 (n=131) | 64.6 (n=115) | 55.9 (n=75) | 53.5 (n=78) |
| genlingo-2026-10c-e2b-nomulti-f16 + léxico | 59.0 (n=131) | 65.3 (n=115) | 56.5 (n=75) | 53.6 (n=78) |
| genlingo-2026-10b-e2b + glosario | 57.6 (n=131) | 61.8 (n=115) | 52.4 (n=75) | 50.8 (n=78) |
| genlingo-2026-10-e2b-q5_k_m + glosario | 56.4 (n=131) | 60.5 (n=115) | 52.4 (n=75) | 50.1 (n=78) |
| gemma4:e2b-it-qat | 48.6 (n=131) | 53.6 (n=115) | 50.5 (n=75) | 48.5 (n=78) |
| gemma4:e2b-it-qat + léxico | 51.8 (n=131) | 61.1 (n=115) | 57.0 (n=75) | 49.8 (n=78) |
| gemma4:e4b | 48.0 (n=131) | 49.4 (n=115) | 48.0 (n=75) | 46.7 (n=78) |
| gemini-3.8-flash | 52.4 (n=131) | 52.5 (n=115) | 57.4 (n=75) | 51.0 (n=77) |
| gemini-3.8-flash + léxico | 55.0 (n=131) | 60.4 (n=115) | 58.8 (n=75) | 53.2 (n=78) |
| genlingo-2026-10e-e2b + léxico | 61.0 (n=131) | 66.7 (n=115) | 57.9 (n=75) | 54.4 (n=78) |
| genlingo-2026-10e-e2b-f16 + léxico | 61.1 (n=131) | 67.5 (n=115) | 58.5 (n=75) | 53.4 (n=78) |
| genlingo-2026-10d-e2b + léxico | 61.3 (n=131) | 65.4 (n=115) | 55.3 (n=75) | 53.5 (n=78) |
| genlingo-2026-10d-e2b-f16 + léxico | 60.8 (n=131) | 65.5 (n=115) | 55.2 (n=75) | 52.0 (n=78) |

## Modelo base: E2B vs E4B

Regla: el más pequeño que cumpla p50 < 1 s con el mejor chrF++.

**gemma4:e2b-it-qat**: mejor chrF++ (50.3) entre los que cumplen p50 < 1 s (p50 152 ms, 4.34 GB).

## Compresión: f16 vs Q5_K_M

| versión | tamaño | p50 | chrF++ |
| --- | --- | --- | --- |
| f16 | 9.27 GB | 394 ms | 60.9 |
| Q5_K_M | 3.62 GB | 253 ms | 60.7 |

## Entrenamiento

| tag | máquina | región | ejemplos | duración | costo estimado | loss inicial → final |
| --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-10e-e2b | Cloud Run Jobs: 1x NVIDIA L4 + 8 vCPU/32 GiB (train), 8 vCPU/32 GiB (merge + GGUF) | europe-west4 | 4321 | 65.8 min | $1.44 | 2.17 → 0.05 |

Costo = segundos facturados × tarifas por segundo de Cloud Run (GPU L4 sin redundancia zonal + vCPU + memoria; entrenamiento en la L4 + fusión y GGUF en un job de CPU). Un reentrenamiento mensual cuesta eso.

## Dónde pierde David

David gana 236 de 398 frases por chrF++ de oración. Las 10 peores derrotas entre las frases de fuentes abiertas (las demás no se pueden reproducir aquí):

| frase | referencia | David | Goliath | Δ chrF++ |
| --- | --- | --- | --- | --- |
| Vieras que me pasó algo bien curioso. | Maje, no sabés lo que me pasó, bien random. | Vieras que me pasó algo bien chistoso. | Maje, no sabés lo random que me pasó algo. | -35.6 |
| jovencita no siga ahí acostada, pongase las pilas | Amiga, no se quede ahí tirada, pilas pues | nena no siga ahí acostada, ¡pílas! | Mor, no se quede ahí echada, actívese. | -25.7 |
| Mi abuelo cría coches en su finca. | Mi abuelo cría cerdos en su finca, maje. | Mi abuelo cría burras en su finca. | Mi abuelo cría cerdos en su finca. | -22.8 |
| Oí en las noticias quesque van a bajar los precios de la fruta. | Neta, dijeron en las noticias que según ya va a bajar la fruta. | Oí en las noticias que dicen que van a bajar los precios de la fruta. | Vi en las noticias que según va a bajar la fruta. | -18.8 |
| Se pegó en la shola con la puerta. | Se pegó en la cabeza con la puerta. | Se dio un talegazo con la puerta. | Se pegó en el coco con la puerta. | -18.4 |
| En suma, no me es posible encontrar un solo defecto en La llegada. Es la neta del planeta. | No le encuentro ni un defecto a La llegada. Está bien chingona, neta. | En resumen, no me es posible encontrar un solo defecto en La llegada. Es god. | En resumen, literal no le encuentro ni un solo pero a La llegada. Está god. | -18.4 |
| Qué cuerudo sos, no te da vergüenza nada. | Qué descarado sos, maje, cero pena. | Qué descarado sos, no te da pena nada. | Qué descarado sos, cero pena te da nada. | -15.9 |
| Deja de tanto güirigüiri y mejor ponte a trabajar. | Ya dejá de tanta paja y ponete a trabajar, maje. | Deja de tanto cháchara y mejor ponte a jalar. | Dejá de tanta casaca y mejor ponete a chambear. | -14.1 |
| No soportamos ese hueso y nos salimos del teatro. | Esa obra estaba muy caspa y nos abrimos. | No soportamos ese hueso y nos caemos del teatro. | Literal no soportamos tremendo flop y nos abrimos del teatro. | -13.0 |
| No le hagas caso, es puro güirigüiri lo que dice. | No le parés bola, es pura paja lo que dice. | No le hagas caso, es puro paja lo que dice. | No le pongás coco, es pura paja lo que dice. | -12.4 |

## Metodología

- Prompts en `duel/genlingo_duel/prompts.py`, temperatura 0. Cada variante declara su prompt en la tabla: cada David con el prompt con el que se entrenó; los modelos base y Goliath con el prompt con país, y también con el glosario de David («+ glosario») para que la comparación con los datos de David sea justa y visible.
- Glosario: entradas del banco de términos recuperadas con EmbeddingGemma local; su tiempo cuenta en la latencia.
- chrF++ = sacrebleu CHRF con `word_order=2`, a nivel de corpus.
- Costo de Goliath = tokens × precio por millón vigente el día del eval (`GEMINI_PRICE_SCHEDULE`); los tokens de razonamiento se cobran como salida.
- Resultados por frase en `evals/results/`.
