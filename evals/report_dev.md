# Genlingo — evaluación en desarrollo

> **Set de desarrollo** (`data/pairs/dev_real.jsonl`): para decidir rondas de datos. Los Davids entrenados antes del 2026-10-02 vieron estos pares al entrenar, así que su número aquí es optimista.

Generado por `make eval` el 2026-10-07 21:29. 280 pares de desarrollo (web; nunca sintéticos), 280 auto_validated. `auto_validated` = validada automáticamente contra el banco de términos (`scripts/validate_test_set.py`).

## Resumen

chrF++ de corpus (0–100, más es mejor) contra la referencia humana. Latencia de extremo a extremo con el modelo ya cargado; los modelos de Ollama corren uno a la vez en la GPU del job del eval.

| modelo | rol | prompt | chrF++ | p50 | p95 | costo total | costo / 1,000 frases | tamaño | errores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-10e-e2b-v2 + léxico | David candidato (LoRA, Q5_K_M) | país + léxico | 68.3 | 270 ms | 497 ms | $0 | $0 | 3.62 GB | 0 |
| genlingo-2026-10e-e2b-v2-nocombo + léxico | David candidato (LoRA, Q5_K_M) | país + léxico | 69.6 | 270 ms | 492 ms | $0 | $0 | 3.62 GB | 0 |

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
| genlingo-2026-10e-e2b-v2 + léxico | 99 % (n=123) | 73 % (n=135) | 85 % (n=258) | 36 % | 59 % (n=241) | 39 % |
| genlingo-2026-10e-e2b-v2-nocombo + léxico | 97 % (n=123) | 68 % (n=135) | 82 % (n=258) | 35 % | 54 % (n=241) | 39 % |

**Mejor David en desarrollo:** `genlingo-2026-10e-e2b-v2 + léxico` (3.62 GB, p50 270 ms): el archivo más pequeño a ≤ 2 puntos de `genlingo-2026-10e-e2b-v2 + léxico` (85 % de jerga resuelta), con p50 < 1 s (empate de tamaño: gana el mayor chrF++). Resuelve 85 %.

### chrF++ por origen

| modelo | web |
| --- | --- |
| genlingo-2026-10e-e2b-v2 + léxico | 68.3 (n=280) |
| genlingo-2026-10e-e2b-v2-nocombo + léxico | 69.6 (n=280) |

### chrF++ por dirección

| modelo | genz_to_parent | parent_to_genz |
| --- | --- | --- |
| genlingo-2026-10e-e2b-v2 + léxico | 70.8 (n=145) | 65.4 (n=135) |
| genlingo-2026-10e-e2b-v2-nocombo + léxico | 71.5 (n=145) | 67.3 (n=135) |

### chrF++ por país

| modelo | CO | GT | LATAM | MX |
| --- | --- | --- | --- | --- |
| genlingo-2026-10e-e2b-v2 + léxico | 66.4 (n=110) | 71.7 (n=85) | 68.0 (n=48) | 67.6 (n=37) |
| genlingo-2026-10e-e2b-v2-nocombo + léxico | 67.5 (n=110) | 72.2 (n=85) | 69.4 (n=48) | 71.9 (n=37) |

## Modelo base: E2B vs E4B

Regla: el más pequeño que cumpla p50 < 1 s con el mejor chrF++.

Ningún modelo base cumple p50 < 1 s.

## Compresión: f16 vs Q4_K_M

Esta ejecución no incluyó ningún David en f16; para compararlo, publica su f16 (`KEEP_F16=1` en `make train`) antes de `make eval`.

## Entrenamiento

| tag | máquina | región | ejemplos | duración | costo estimado | loss inicial → final |
| --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-10d-e2b | Cloud Run Jobs: 1x NVIDIA L4 + 8 vCPU/32 GiB (train), 8 vCPU/32 GiB (merge + GGUF) | europe-west4 | 3880 | 67.5 min | $1.49 | 2.08 → 0.05 |

Costo = segundos facturados × tarifas por segundo de Cloud Run (GPU L4 sin redundancia zonal + vCPU + memoria; entrenamiento en la L4 + fusión y GGUF en un job de CPU). Un reentrenamiento mensual cuesta eso.

## Metodología

- Prompts en `duel/genlingo_duel/prompts.py`, temperatura 0. Cada variante declara su prompt en la tabla: cada David con el prompt con el que se entrenó; los modelos base y Goliath con el prompt con país, y también con el glosario de David («+ glosario») para que la comparación con los datos de David sea justa y visible.
- Glosario: entradas del banco de términos recuperadas con EmbeddingGemma local; su tiempo cuenta en la latencia.
- chrF++ = sacrebleu CHRF con `word_order=2`, a nivel de corpus.
- Costo de Goliath = tokens × precio por millón vigente el día del eval (`GEMINI_PRICE_SCHEDULE`); los tokens de razonamiento se cobran como salida.
- Resultados por frase en `evals/results/`.
