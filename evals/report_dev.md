# Genlingo — evaluación en desarrollo

> **Set de desarrollo** (`data/pairs/dev_real.jsonl`): para decidir rondas de datos. Los Davids entrenados antes del 2026-10-02 vieron estos pares al entrenar, así que su número aquí es optimista.

Generado por `make eval` el 2026-10-07 07:21. 151 pares de desarrollo (web; nunca sintéticos), 151 auto_validated. `auto_validated` = validada automáticamente contra el banco de términos (`scripts/validate_test_set.py`).

## Resumen

chrF++ de corpus (0–100, más es mejor) contra la referencia humana. Latencia de extremo a extremo con el modelo ya cargado; los modelos de Ollama corren uno a la vez en la GPU del job del eval.

| modelo | rol | prompt | chrF++ | p50 | p95 | costo total | costo / 1,000 frases | tamaño | errores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-10d-e2b + léxico | David candidato (LoRA, Q5_K_M) | país + léxico | 63.9 | 237 ms | 346 ms | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10c-e2b-nomulti + léxico | David (LoRA, Q5_K_M) | país + léxico | 63.6 | 239 ms | 343 ms | $0 | $0 | 3.62 GB | 0 |

**Línea base "copiar la frase"** (devolver el texto original sin traducir): chrF++ 58.4. Un modelo que no supera esta línea no está traduciendo mejor que no hacer nada; mide cuánto del puntaje viene de palabras que la referencia comparte con el original.

## ¿Tradujo la jerga?

chrF++ premia parecerse a la referencia, y una reescritura de registro conserva casi todas las palabras: por eso copiar la frase ya saca ~50. Estas dos métricas miran solo lo que tenía que cambiar (detalle en `evals/term_accuracy.py`):

- **Jerga resuelta**: Gen Z → papás, no queda en la salida ningún término Gen Z del banco que tenía la frase; papás → Gen Z, la salida usa al menos un término Gen Z del banco del país. Mide que cambió el registro, no que el significado sea correcto.
- **Cambios acertados**: de las palabras que la referencia humana cambió respecto al original, cuántas aparecen en la salida. Mide significado, pero solo con palabras exactas: un sinónimo válido cuenta como fallo para todos.

- **Jerga correcta** y **cambios acertados con sinónimos** (enmienda 1 de `evals/niche.md`): el término producido tiene que significar lo mismo, según la tabla de contrapartes validada por significado (`data/counterparts.jsonl`); con sinónimos, una palabra cuenta si coincide la raíz o es un término enlazado.

| modelo | jerga resuelta Gen Z → papás | jerga resuelta papás → Gen Z | jerga resuelta total | cambios acertados | jerga correcta | cambios acertados (sinónimos) |
| --- | --- | --- | --- | --- | --- | --- |
| copiar la frase (línea base) | 0 % (n=72) | 0 % (n=72) | 0 % (n=144) | 0 % | 0 % (n=137) | 5 % |
| genlingo-2026-10d-e2b + léxico | 100 % (n=72) | 75 % (n=72) | 88 % (n=144) | 29 % | 39 % (n=137) | 33 % |
| genlingo-2026-10c-e2b-nomulti + léxico | 100 % (n=72) | 71 % (n=72) | 85 % (n=144) | 26 % | 35 % (n=137) | 31 % |

**Mejor David en desarrollo:** `genlingo-2026-10d-e2b + léxico` (3.62 GB, p50 237 ms): el archivo más pequeño a ≤ 2 puntos de `genlingo-2026-10d-e2b + léxico` (88 % de jerga resuelta), con p50 < 1 s (empate de tamaño: gana el mayor chrF++). Resuelve 88 %.

### chrF++ por origen

| modelo | web |
| --- | --- |
| genlingo-2026-10d-e2b + léxico | 63.9 (n=151) |
| genlingo-2026-10c-e2b-nomulti + léxico | 63.6 (n=151) |

### chrF++ por dirección

| modelo | genz_to_parent | parent_to_genz |
| --- | --- | --- |
| genlingo-2026-10d-e2b + léxico | 64.4 (n=79) | 63.4 (n=72) |
| genlingo-2026-10c-e2b-nomulti + léxico | 63.6 (n=79) | 63.6 (n=72) |

### chrF++ por país

| modelo | CO | GT | LATAM | MX |
| --- | --- | --- | --- | --- |
| genlingo-2026-10d-e2b + léxico | 61.4 (n=67) | 65.7 (n=69) | 69.9 (n=2) | 69.7 (n=13) |
| genlingo-2026-10c-e2b-nomulti + léxico | 60.1 (n=67) | 66.7 (n=69) | 68.0 (n=2) | 69.4 (n=13) |

## Modelo base: E2B vs E4B

Regla: el más pequeño que cumpla p50 < 1 s con el mejor chrF++.

Ningún modelo base cumple p50 < 1 s.

## Compresión: f16 vs Q5_K_M

Esta ejecución no incluyó ningún David en f16; para compararlo, publica su f16 (`KEEP_F16=1` en `make train`) antes de `make eval`.

## Entrenamiento

| tag | máquina | región | ejemplos | duración | costo estimado | loss inicial → final |
| --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-10c-e2b-nomulti | Cloud Run Jobs: 1x NVIDIA L4 + 8 vCPU/32 GiB (train), 8 vCPU/32 GiB (merge + GGUF) | europe-west4 | 2271 | 45.9 min | $0.97 | 1.97 → 0.06 |

Costo = segundos facturados × tarifas por segundo de Cloud Run (GPU L4 sin redundancia zonal + vCPU + memoria; entrenamiento en la L4 + fusión y GGUF en un job de CPU). Un reentrenamiento mensual cuesta eso.

## Metodología

- Prompts en `duel/genlingo_duel/prompts.py`, temperatura 0. Cada variante declara su prompt en la tabla: cada David con el prompt con el que se entrenó; los modelos base y Goliath con el prompt con país, y también con el glosario de David («+ glosario») para que la comparación con los datos de David sea justa y visible.
- Glosario: entradas del banco de términos recuperadas con EmbeddingGemma local; su tiempo cuenta en la latencia.
- chrF++ = sacrebleu CHRF con `word_order=2`, a nivel de corpus.
- Costo de Goliath = tokens × precio por millón vigente el día del eval (`GEMINI_PRICE_SCHEDULE`); los tokens de razonamiento se cobran como salida.
- Resultados por frase en `evals/results/`.
