# Genlingo — evaluación en desarrollo

> **Set de desarrollo** (`data/pairs/dev_real.jsonl`): para decidir rondas de datos. Los Davids entrenados antes del 2026-10-02 vieron estos pares al entrenar, así que su número aquí es optimista.

Generado por `make eval` el 2026-10-02 11:55. 146 pares de desarrollo (web; nunca sintéticos), 146 auto_validated. `auto_validated` = validada automáticamente contra el banco de términos (`scripts/validate_test_set.py`).

## Resumen

chrF++ de corpus (0–100, más es mejor) contra la referencia humana. Latencia de extremo a extremo con el modelo ya cargado; los modelos locales corren uno a la vez en la laptop del escenario.

| modelo | rol | prompt | chrF++ | p50 | p95 | costo total | costo / 1,000 frases | tamaño | errores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-10b-e2b + glosario | David (LoRA, Q5_K_M) | país + glosario | 65.3 | 592 ms | 854 ms | $0 | $0 | 3.62 GB | 0 |
| gemini-3.8-flash | Goliath | país | 49.7 | 4.00 s | 8.39 s | $0.20 | $1.35 | — | 1 |
| gemini-3.8-flash + glosario | Goliath con el glosario de David | país + glosario | 55.4 | 3.51 s | 9.93 s | $0.18 | $1.22 | — | 0 |

Costo de Goliath con la tarifa del día del eval: $0.75 entrada / $3.75 salida por millón de tokens (vigente desde 2026-09-30).
Con la tarifa desde 2027-01-01 ($1.50 / $7.50), este mismo eval costaría $0.39 ($2.70 por 1,000 frases).

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
| gemini-3.8-flash | 96 % (n=69) | 56 % (n=70) | 76 % (n=139) | 18 % | 14 % (n=132) | 21 % |
| gemini-3.8-flash + glosario | 99 % (n=69) | 74 % (n=70) | 86 % (n=139) | 31 % | 27 % (n=132) | 36 % |

**David en escena:** `genlingo-2026-10b-e2b + glosario` (3.62 GB, p50 592 ms): el archivo más pequeño a ≤ 2 puntos de `genlingo-2026-10b-e2b + glosario` (91 % de jerga resuelta), con p50 < 1 s. Resuelve 91 %.

Cara a cara con `gemini-3.8-flash` en jerga resuelta: David la resuelve y Goliath no en **27** frases; al revés en **6**.

Cara a cara con `gemini-3.8-flash + glosario` en jerga resuelta: David la resuelve y Goliath no en **13** frases; al revés en **7**.

Jerga de otro país en papás → Gen Z (p. ej. «pisto» guatemalteco en una frase mexicana): genlingo-2026-10b-e2b + glosario 1, gemini-3.8-flash 3, gemini-3.8-flash + glosario 4 (de 70).

**Lectura honesta:** David gana también en jerga, no solo en parecido de superficie, frente a Goliath sin glosario. Compáralo con Goliath + glosario para separar lo que aporta el modelo de lo que aporta el dato.

Con el mismo glosario, Goliath resuelve 86 % de la jerga frente al 91 % de David: David sigue por delante incluso con el glosario compartido.

### chrF++ por origen

| modelo | web |
| --- | --- |
| genlingo-2026-10b-e2b + glosario | 65.3 (n=146) |
| gemini-3.8-flash | 49.7 (n=145) |
| gemini-3.8-flash + glosario | 55.4 (n=146) |

### chrF++ por dirección

| modelo | genz_to_parent | parent_to_genz |
| --- | --- | --- |
| genlingo-2026-10b-e2b + glosario | 64.3 (n=76) | 66.3 (n=70) |
| gemini-3.8-flash | 55.2 (n=75) | 43.9 (n=70) |
| gemini-3.8-flash + glosario | 59.7 (n=76) | 50.8 (n=70) |

### chrF++ por país

| modelo | CO | GT | LATAM | MX |
| --- | --- | --- | --- | --- |
| genlingo-2026-10b-e2b + glosario | 61.4 (n=67) | 66.5 (n=69) | 77.8 (n=2) | 86.7 (n=8) |
| gemini-3.8-flash | 44.7 (n=66) | 54.1 (n=69) | 74.2 (n=2) | 54.8 (n=8) |
| gemini-3.8-flash + glosario | 53.1 (n=67) | 58.1 (n=69) | 65.3 (n=2) | 55.0 (n=8) |

## Modelo base: E2B vs E4B

Regla: el más pequeño que cumpla p50 < 1 s con el mejor chrF++.

Ningún modelo base cumple p50 < 1 s.

## Compresión: f16 vs Q5_K_M

Pendiente: se necesita David en f16 y cuantizado en Ollama (`make pull-model FP16=1`).

## Entrenamiento

| tag | máquina | región | ejemplos | duración | costo estimado | loss inicial → final |
| --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-10b-e2b | Cloud Run Jobs: 1x NVIDIA L4 + 8 vCPU/32 GiB (train), 8 vCPU/32 GiB (merge + GGUF) | europe-west4 | 1709 | 34.3 min | $0.71 | 2.62 → 0.16 |

Costo = segundos facturados × tarifas por segundo de Cloud Run (GPU L4 sin redundancia zonal + vCPU + memoria; entrenamiento en la L4 + fusión y GGUF en un job de CPU). Un reentrenamiento mensual cuesta eso; la inferencia de David cuesta $0 porque corre en la laptop.

## Dónde pierde David

David gana 95 de 145 frases por chrF++ de oración. Las 10 peores derrotas:

| frase | referencia | David | Goliath | Δ chrF++ |
| --- | --- | --- | --- | --- |
| ¡Puchis! ¿Y esta qué onda? | […] | ¡Púchica! ¿Y cómo le va? | ¡Púchica! ¿Y a esta qué le pasa pues? | -50.9 |
| […] | Le dije que pasara todas sus chivas al nuevo cuarto | Le dije que pasara todos sus chistes a la nueva habitación. | Le dije que pasara todas sus chivas al nuevo cuarto | -46.8 |
| Dame una bara para el bus. | Dame un quetzal para el bus. | Paga la boleta del bus. | Dame un quetzal para la camioneta. | -43.0 |
| ¡No sea avión, parce! | ¡No sea vivo, hombre! | ¡No sea tan confianzudo! | ¡No se las dé de vivo, hombre! | -42.2 |
| Qué nítido tu cel | Qué chilero tu teléfono | Qué chulo tu cel | Qué chilero tu celular | -36.3 |
| Hágame un favorcito, parce, présteme mil pesos. | Hágame una parada, hermano, présteme mil pesos. | Hágame un favor, por favor, pídeme mil baras. | Hágame un favorcito, hermano, présteme mil pesitos. | -35.9 |
| ¡Casi me muero del susto, maje! | […] | ¡Qué barbaridad el susto que me llevé! | ¡Casi me da el patatús, vos! | -34.5 |
| ¡Qué cuca tu camiseta nueva! | […] | ¡Qué bonita tu camiseta nueva! | ¡Qué chévere tu camiseta nueva! | -33.0 |
| […] | Vos, ¿por qué sos tan metido, maje? | Vos ¿por qué sos tan clavado? | Vos, ¿por qué sos tan metido? | -31.7 |
| ¡Está muy bonito, hombre! | […] | ¡Está bien calidá, maje! | ¡Está bien de ahuevo, va! | -31.1 |

## Metodología

- Prompts en `duel/genlingo_duel/prompts.py`, temperatura 0. Cada variante declara su prompt en la tabla: cada David con el prompt con el que se entrenó; los modelos base y Goliath con el prompt con país, y también con el glosario de David («+ glosario») para que la comparación con los datos de David sea justa y visible.
- Glosario: entradas del banco de términos recuperadas con EmbeddingGemma local; su tiempo cuenta en la latencia.
- chrF++ = sacrebleu CHRF con `word_order=2`, a nivel de corpus.
- Costo de Goliath = tokens × precio por millón vigente el día del eval (`GEMINI_PRICE_SCHEDULE`); los tokens de razonamiento se cobran como salida.
- Resultados por frase en `evals/results/`.
