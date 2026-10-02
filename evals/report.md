# Genlingo — evaluación

Generado por `make eval` el 2026-10-02 07:25. 403 pares de prueba (web; nunca sintéticos), 403 auto_validated. `auto_validated` = validada automáticamente contra el banco de términos (`scripts/validate_test_set.py`).

## Resumen

chrF++ de corpus (0–100, más es mejor) contra la referencia humana. Latencia de extremo a extremo con el modelo ya cargado; los modelos locales corren uno a la vez en la laptop del escenario.

| modelo | rol | prompt | chrF++ | p50 | p95 | costo total | costo / 1,000 frases | tamaño | errores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma4:e2b-it-qat | base (sin ajuste) | v2 | 50.1 | 363 ms | 490 ms | $0 | $0 | 4.34 GB | 0 |
| gemma4:e2b-it-qat + glosario | base (sin ajuste) | v2 + glosario | 54.7 | 451 ms | 582 ms | $0 | $0 | 4.34 GB | 0 |
| gemma4:e4b | base (sin ajuste) | v2 | 48.0 | 747 ms | 1.05 s | $0 | $0 | 6.58 GB | 0 |
| genlingo-2026-10-e2b-q5_k_m + glosario | David candidato (LoRA, Q5_K_M) | v2 + glosario | 55.2 | 567 ms | 742 ms | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10-e2b + glosario | David candidato (LoRA, Q4_K_M) | v2 + glosario | 55.5 | 512 ms | 696 ms | $0 | $0 | 3.42 GB | 0 |
| genlingo-2026-10-e2b-f16 + glosario | David candidato (LoRA, f16) | v2 + glosario | 56.1 | 567 ms | 809 ms | $0 | $0 | 9.27 GB | 0 |
| genlingo-2026-09 | David candidato (LoRA, Q4_K_M) | v1 | 54.8 | 395 ms | 555 ms | $0 | $0 | 3.42 GB | 0 |
| genlingo-2026-09-f16 | David candidato (LoRA, f16) | v1 | 55.2 | 444 ms | 651 ms | $0 | $0 | 9.27 GB | 0 |
| gemini-3.8-flash | Goliath | v2 | 52.8 | 3.40 s | 8.78 s | $0.47 | $1.17 | — | 3 |
| gemini-3.8-flash + glosario | Goliath con el glosario de David | v2 + glosario | 57.6 | 3.42 s | 8.32 s | $0.49 | $1.23 | — | 1 |
| genlingo-2026-11-e2b + glosario | David (LoRA, Q5_K_M) | v2 + glosario | 56.6 | 557 ms | 753 ms | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-11-e2b-f16 + glosario | David (LoRA, f16) | v2 + glosario | 56.6 | 557 ms | 802 ms | $0 | $0 | 9.27 GB | 0 |

Costo de Goliath con la tarifa del día del eval: $0.75 entrada / $3.75 salida por millón de tokens (vigente desde 2026-09-30).
Con la tarifa desde 2027-01-01 ($1.50 / $7.50), este mismo eval costaría $0.93 ($2.34 por 1,000 frases).

**Línea base "copiar la frase"** (devolver el texto original sin traducir): chrF++ 53.1. Un modelo que no supera esta línea no está traduciendo mejor que no hacer nada; mide cuánto del puntaje viene de palabras que la referencia comparte con el original.

## ¿Tradujo la jerga?

chrF++ premia parecerse a la referencia, y una reescritura de registro conserva casi todas las palabras: por eso copiar la frase ya saca ~50. Estas dos métricas miran solo lo que tenía que cambiar (detalle en `evals/term_accuracy.py`):

- **Jerga resuelta**: Gen Z → papás, no queda en la salida ningún término Gen Z del banco que tenía la frase; papás → Gen Z, la salida usa al menos un término Gen Z del banco del país. Mide que cambió el registro, no que el significado sea correcto.
- **Cambios acertados**: de las palabras que la referencia humana cambió respecto al original, cuántas aparecen en la salida. Mide significado, pero solo con palabras exactas: un sinónimo válido cuenta como fallo para todos.

| modelo | jerga resuelta Gen Z → papás | jerga resuelta papás → Gen Z | jerga resuelta total | cambios acertados |
| --- | --- | --- | --- | --- |
| copiar la frase (línea base) | 0 % (n=227) | 3 % (n=176) | 1 % (n=403) | 0 % |
| gemma4:e2b-it-qat | 94 % (n=227) | 10 % (n=176) | 58 % (n=403) | 14 % |
| gemma4:e2b-it-qat + glosario | 94 % (n=227) | 20 % (n=176) | 62 % (n=403) | 23 % |
| gemma4:e4b | 97 % (n=227) | 30 % (n=176) | 68 % (n=403) | 17 % |
| genlingo-2026-10-e2b-q5_k_m + glosario | 97 % (n=227) | 44 % (n=176) | 74 % (n=403) | 17 % |
| genlingo-2026-10-e2b + glosario | 95 % (n=227) | 31 % (n=176) | 67 % (n=403) | 16 % |
| genlingo-2026-10-e2b-f16 + glosario | 99 % (n=227) | 43 % (n=176) | 74 % (n=403) | 18 % |
| genlingo-2026-09 | 94 % (n=227) | 20 % (n=176) | 62 % (n=403) | 14 % |
| genlingo-2026-09-f16 | 93 % (n=227) | 27 % (n=176) | 64 % (n=403) | 14 % |
| gemini-3.8-flash | 99 % (n=225) | 48 % (n=175) | 76 % (n=400) | 24 % |
| gemini-3.8-flash + glosario | 100 % (n=226) | 64 % (n=176) | 84 % (n=402) | 31 % |
| genlingo-2026-11-e2b + glosario | 99 % (n=227) | 60 % (n=176) | 82 % (n=403) | 22 % |
| genlingo-2026-11-e2b-f16 + glosario | 98 % (n=227) | 60 % (n=176) | 81 % (n=403) | 22 % |

**David en escena:** `genlingo-2026-11-e2b + glosario` (3.62 GB, p50 557 ms): el archivo más pequeño a ≤ 2 puntos de `genlingo-2026-11-e2b-f16 + glosario` (81 % de jerga resuelta), con p50 < 1 s. Resuelve 82 %.

Cara a cara con `gemini-3.8-flash` en jerga resuelta: David la resuelve y Goliath no en **53** frases; al revés en **31**.

Cara a cara con `gemini-3.8-flash + glosario` en jerga resuelta: David la resuelve y Goliath no en **27** frases; al revés en **36**.

Jerga de otro país en papás → Gen Z (p. ej. «pisto» guatemalteco en una frase mexicana): gemma4:e2b-it-qat 9, gemma4:e2b-it-qat + glosario 7, gemma4:e4b 18, genlingo-2026-10-e2b-q5_k_m + glosario 19, genlingo-2026-10-e2b + glosario 21, genlingo-2026-09 22, gemini-3.8-flash 5, gemini-3.8-flash + glosario 1, genlingo-2026-11-e2b + glosario 14 (de 176).

**Lectura honesta:** resultado mixto: cada uno gana en una de las dos métricas de jerga.

Con el mismo glosario, Goliath resuelve 84 % de la jerga frente al 82 % de David: la ventaja de David viene de **sus datos** (el banco de términos), no de ser mejor modelo; y esos datos los tiene él, no Goliath.

## Compresión: tamaño vs jerga

Las exportaciones de `genlingo-2026-10-e2b` con el mismo prompt y glosario. La curva muestra cuánta jerga se pierde al comprimir.

![Tamaño vs jerga resuelta](compression.svg)

| variante | cuantización | imatrix | tamaño | jerga resuelta | cambios acertados | chrF++ | p50 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `genlingo-2026-10-e2b + glosario` | Q4_K_M | no | 3.42 GB | 67 % | 16 % | 55.5 | 512 ms |
| `genlingo-2026-10-e2b-q5_k_m + glosario` | Q5_K_M | no | 3.62 GB | 74 % | 17 % | 55.2 | 567 ms |
| `genlingo-2026-10-e2b-f16 + glosario` | F16 | no | 9.27 GB | 74 % | 18 % | 56.1 | 567 ms |

**imatrix (importance matrix):** antes de cuantizar, llama.cpp pasa el modelo f16 por texto de calibración y mide qué pesos influyen más; la cuantización gasta los bits ahí. Calibramos con **pares de entrenamiento** renderizados con el prompt de David (`train/quant_sweep.py`), nunca con el set de prueba: eso inflaría el eval.

### chrF++ por origen

| modelo | web |
| --- | --- |
| gemma4:e2b-it-qat | 50.1 (n=403) |
| gemma4:e2b-it-qat + glosario | 54.7 (n=403) |
| gemma4:e4b | 48.0 (n=403) |
| genlingo-2026-10-e2b-q5_k_m + glosario | 55.2 (n=403) |
| genlingo-2026-10-e2b + glosario | 55.5 (n=403) |
| genlingo-2026-10-e2b-f16 + glosario | 56.1 (n=403) |
| genlingo-2026-09 | 54.8 (n=403) |
| genlingo-2026-09-f16 | 55.2 (n=403) |
| gemini-3.8-flash | 52.8 (n=400) |
| gemini-3.8-flash + glosario | 57.6 (n=402) |
| genlingo-2026-11-e2b + glosario | 56.6 (n=403) |
| genlingo-2026-11-e2b-f16 + glosario | 56.6 (n=403) |

### chrF++ por dirección

| modelo | genz_to_parent | parent_to_genz |
| --- | --- | --- |
| gemma4:e2b-it-qat | 56.9 (n=227) | 40.8 (n=176) |
| gemma4:e2b-it-qat + glosario | 64.3 (n=227) | 41.5 (n=176) |
| gemma4:e4b | 55.0 (n=227) | 38.5 (n=176) |
| genlingo-2026-10-e2b-q5_k_m + glosario | 62.5 (n=227) | 45.0 (n=176) |
| genlingo-2026-10-e2b + glosario | 62.3 (n=227) | 46.1 (n=176) |
| genlingo-2026-10-e2b-f16 + glosario | 63.2 (n=227) | 46.2 (n=176) |
| genlingo-2026-09 | 62.2 (n=227) | 44.7 (n=176) |
| genlingo-2026-09-f16 | 62.7 (n=227) | 44.9 (n=176) |
| gemini-3.8-flash | 59.6 (n=225) | 43.4 (n=175) |
| gemini-3.8-flash + glosario | 65.3 (n=226) | 47.1 (n=176) |
| genlingo-2026-11-e2b + glosario | 63.7 (n=227) | 46.7 (n=176) |
| genlingo-2026-11-e2b-f16 + glosario | 64.0 (n=227) | 46.4 (n=176) |

### chrF++ por país

| modelo | CO | GT | LATAM | MX |
| --- | --- | --- | --- | --- |
| gemma4:e2b-it-qat | 48.1 (n=134) | 53.1 (n=116) | 51.1 (n=75) | 48.6 (n=78) |
| gemma4:e2b-it-qat + glosario | 52.0 (n=134) | 59.8 (n=116) | 56.5 (n=75) | 50.8 (n=78) |
| gemma4:e4b | 47.6 (n=134) | 50.1 (n=116) | 48.1 (n=75) | 45.7 (n=78) |
| genlingo-2026-10-e2b-q5_k_m + glosario | 55.8 (n=134) | 61.1 (n=116) | 51.3 (n=75) | 49.2 (n=78) |
| genlingo-2026-10-e2b + glosario | 55.6 (n=134) | 60.9 (n=116) | 52.7 (n=75) | 50.0 (n=78) |
| genlingo-2026-10-e2b-f16 + glosario | 56.2 (n=134) | 61.5 (n=116) | 53.1 (n=75) | 50.7 (n=78) |
| genlingo-2026-09 | 54.1 (n=134) | 58.1 (n=116) | 54.3 (n=75) | 51.6 (n=78) |
| genlingo-2026-09-f16 | 55.4 (n=134) | 59.0 (n=116) | 54.0 (n=75) | 50.5 (n=78) |
| gemini-3.8-flash | 52.7 (n=134) | 51.6 (n=115) | 57.0 (n=73) | 50.4 (n=78) |
| gemini-3.8-flash + glosario | 54.9 (n=134) | 59.9 (n=116) | 62.1 (n=75) | 54.8 (n=77) |
| genlingo-2026-11-e2b + glosario | 58.4 (n=134) | 61.1 (n=116) | 52.0 (n=75) | 50.9 (n=78) |
| genlingo-2026-11-e2b-f16 + glosario | 58.0 (n=134) | 61.0 (n=116) | 52.6 (n=75) | 51.2 (n=78) |

## Modelo base: E2B vs E4B

Regla: el más pequeño que cumpla p50 < 1 s con el mejor chrF++.

**gemma4:e2b-it-qat**: mejor chrF++ (50.1) entre los que cumplen p50 < 1 s (p50 363 ms, 4.34 GB).

## Compresión: f16 vs Q5_K_M

| versión | tamaño | p50 | chrF++ |
| --- | --- | --- | --- |
| f16 | 9.27 GB | 557 ms | 56.6 |
| Q5_K_M | 3.62 GB | 557 ms | 56.6 |

## Entrenamiento

| tag | máquina | región | ejemplos | duración | costo estimado | loss inicial → final |
| --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-11-e2b | Cloud Run Jobs: 1x NVIDIA L4 + 8 vCPU/32 GiB (train), 8 vCPU/32 GiB (merge + GGUF) | europe-west4 | 1709 | 34.3 min | $0.71 | 2.62 → 0.16 |

Costo = segundos facturados × tarifas por segundo de Cloud Run (GPU L4 sin redundancia zonal + vCPU + memoria; entrenamiento en la L4 + fusión y GGUF en un job de CPU). Un reentrenamiento mensual cuesta eso; la inferencia de David cuesta $0 porque corre en la laptop.

## Dónde pierde David

David gana 214 de 400 frases por chrF++ de oración. Las 10 peores derrotas:

| frase | referencia | David | Goliath | Δ chrF++ |
| --- | --- | --- | --- | --- |
| […] | Se me antojan unas cervecitas. | Se me antoja una cerveza. | Se me antojan unas cervecitas. | -54.5 |
| Mi jefa no me deja salir, la neta. | La verdad, mi mamá no me da permiso de salir. | Yo a tu edad no salía a ningún lado sin permiso de mis papás. | Mi mamá no me da permiso de salir, la verdad. | -50.1 |
| […] | ¿Qué te pasó que hoy andas con tan buena vibra? | ¿Qué te pasó que hoy estás tan bajoneada? | ¿Qué te pasó que hoy andas con tan buena vibra? | -49.9 |
| […] | Esa morra es red flag, bro. | Esa chava no te conviene, güey. | Esa morra es una red flag. | -48.5 |
| […] | Tengo la cabeza tan atontada que solo pienso en las grabaciones chistosas de internet | Tengo tanta racha de ver videos absurdos que ando turulato de la risa. | Tengo la cabeza tan quemada que solo pienso en chistes de internet | -43.4 |
| […] | Ese examen estuvo dificilísimo, de verdad. | Ese examen fue imposible, en serio. | Ese examen estuvo dificilísimo, te lo juro. | -42.8 |
| Se pegó en la shola con la puerta. | Se pegó en la cabeza con la puerta. | Se cayó de lleno contra la puerta. | Se dio un buen golpe en la cabeza con la puerta. | -38.8 |
| […] | ¡No me digas eso que me da algo, literal! | No me digas esas cosas que me van a hacer flashear. | ¡No me digas eso que me da algo y colapso! | -37.7 |
| […] | Publicaron sus datos personales por los comentarios tan polémicos que hizo | Se armó un escándalo por sus comentarios polémicos. | Publicaron sus datos personales por sus comentarios polémicos | -37.5 |
| ¡Malaya fuera rico para comprarme esa casa! | ¡Ojalá tuviera un montón de pisto para comprarme esa casa! | F que me compre esa casa | ¡Quién pudiera tener pisto para comprarme esa casa! | -37.1 |

## Metodología

- Prompts en `duel/genlingo_duel/prompts.py`, temperatura 0. Cada variante declara su prompt en la tabla: cada David con el prompt con el que se entrenó; los modelos base y Goliath con v2, y también con el glosario de David («+ glosario») para que la comparación con los datos de David sea justa y visible.
- Glosario: entradas del banco de términos recuperadas con EmbeddingGemma local; su tiempo cuenta en la latencia.
- chrF++ = sacrebleu CHRF con `word_order=2`, a nivel de corpus.
- Costo de Goliath = tokens × precio por millón vigente el día del eval (`GEMINI_PRICE_SCHEDULE`); los tokens de razonamiento se cobran como salida.
- Resultados por frase en `evals/results/`.
