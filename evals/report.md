# Genlingo — evaluación

Generado por `make eval` el 2026-10-01 00:50. 319 pares de prueba (web; nunca sintéticos).

> **Ensayo:** las referencias de prueba aún están en `pending_review` (sin revisión del presentador). Los números cambiarán al aprobar/corregir el set con `make review-test`.

## Resumen

chrF++ de corpus (0–100, más es mejor) contra la referencia humana. Latencia de extremo a extremo con el modelo ya cargado; los modelos locales corren uno a la vez en la laptop del escenario.

| modelo | rol | chrF++ | p50 | p95 | costo total | costo / 1,000 frases | tamaño | errores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma4:e2b-it-qat | base (sin ajuste) | 47.1 | 329 ms | 451 ms | $0 | $0 | 4.34 GB | 0 |
| gemma4:e4b | base (sin ajuste) | 47.0 | 689 ms | 934 ms | $0 | $0 | 6.58 GB | 0 |
| genlingo-2026-09 | David (LoRA, Q4) | 52.1 | 388 ms | 568 ms | $0 | $0 | 3.42 GB | 0 |
| genlingo-2026-09-f16 | David (LoRA, f16) | 52.0 | 447 ms | 683 ms | $0 | $0 | 9.27 GB | 0 |
| gemini-3.8-flash | Goliath | 48.7 | 1.71 s | 6.51 s | $0.13 | $0.40 | — | 0 |

Costo de Goliath con la tarifa del día del eval: $0.75 entrada / $3.75 salida por millón de tokens (vigente desde 2026-09-30).
Con la tarifa desde 2027-01-01 ($1.50 / $7.50), este mismo eval costaría $0.25 ($0.80 por 1,000 frases).

**Línea base "copiar la frase"** (devolver el texto original sin traducir): chrF++ 50.0. Un modelo que no supera esta línea no está traduciendo mejor que no hacer nada; mide cuánto del puntaje viene de palabras que la referencia comparte con el original.

## ¿Tradujo la jerga?

chrF++ premia parecerse a la referencia, y una reescritura de registro conserva casi todas las palabras: por eso copiar la frase ya saca ~50. Estas dos métricas miran solo lo que tenía que cambiar (detalle en `evals/term_accuracy.py`):

- **Jerga resuelta**: Gen Z → papás, no queda en la salida ningún término Gen Z del banco que tenía la frase; papás → Gen Z, la salida usa al menos un término Gen Z del banco del país. Mide que cambió el registro, no que el significado sea correcto.
- **Cambios acertados**: de las palabras que la referencia humana cambió respecto al original, cuántas aparecen en la salida. Mide significado, pero solo con palabras exactas: un sinónimo válido cuenta como fallo para todos.

| modelo | jerga resuelta Gen Z → papás | jerga resuelta papás → Gen Z | jerga resuelta total | cambios acertados |
| --- | --- | --- | --- | --- |
| copiar la frase (línea base) | 0 % (n=149) | 1 % (n=155) | 0 % (n=304) | 0 % |
| gemma4:e2b-it-qat | 96 % (n=149) | 10 % (n=155) | 52 % (n=304) | 12 % |
| gemma4:e4b | 97 % (n=149) | 17 % (n=155) | 56 % (n=304) | 16 % |
| genlingo-2026-09 | 90 % (n=149) | 21 % (n=155) | 55 % (n=304) | 15 % |
| genlingo-2026-09-f16 | 90 % (n=149) | 28 % (n=155) | 58 % (n=304) | 13 % |
| gemini-3.8-flash | 99 % (n=149) | 39 % (n=155) | 68 % (n=304) | 29 % |

Cara a cara en jerga resuelta: David la resuelve y Goliath no en **19** frases; al revés en **61**.

Jerga de otro país en papás → Gen Z (p. ej. «pisto» guatemalteco en una frase mexicana): David 16 de 155, Goliath 7 de 155.

**Lectura honesta:** en jerga gana Goliath. La ventaja de David en chrF++ viene sobre todo de quedarse cerca de la frase original, como la referencia, no de traducir mejor el término. El próximo David necesita datos que cambien la jerga de verdad (sobre todo papás → Gen Z) y del país correcto.

### chrF++ por origen

| modelo | web |
| --- | --- |
| gemma4:e2b-it-qat | 47.1 (n=319) |
| gemma4:e4b | 47.0 (n=319) |
| genlingo-2026-09 | 52.1 (n=319) |
| genlingo-2026-09-f16 | 52.0 (n=319) |
| gemini-3.8-flash | 48.7 (n=319) |

### chrF++ por dirección

| modelo | genz_to_parent | parent_to_genz |
| --- | --- | --- |
| gemma4:e2b-it-qat | 52.5 (n=164) | 40.7 (n=155) |
| gemma4:e4b | 54.4 (n=164) | 38.3 (n=155) |
| genlingo-2026-09 | 59.5 (n=164) | 43.5 (n=155) |
| genlingo-2026-09-f16 | 59.0 (n=164) | 43.9 (n=155) |
| gemini-3.8-flash | 54.3 (n=164) | 42.1 (n=155) |

### chrF++ por país

| modelo | CO | GT | LATAM | MX |
| --- | --- | --- | --- | --- |
| gemma4:e2b-it-qat | 46.2 (n=88) | 48.7 (n=73) | 47.4 (n=70) | 46.3 (n=88) |
| gemma4:e4b | 48.8 (n=88) | 48.1 (n=73) | 45.1 (n=70) | 45.3 (n=88) |
| genlingo-2026-09 | 51.7 (n=88) | 56.4 (n=73) | 51.1 (n=70) | 49.5 (n=88) |
| genlingo-2026-09-f16 | 52.5 (n=88) | 56.3 (n=73) | 50.9 (n=70) | 48.5 (n=88) |
| gemini-3.8-flash | 49.0 (n=88) | 44.2 (n=73) | 53.1 (n=70) | 48.2 (n=88) |

## Modelo base: E2B vs E4B

Regla: el más pequeño que cumpla p50 < 1 s con el mejor chrF++.

**gemma4:e2b-it-qat**: mejor chrF++ (47.1) entre los que cumplen p50 < 1 s (p50 329 ms, 4.34 GB).

## Compresión: f16 vs Q4

| versión | tamaño | p50 | chrF++ |
| --- | --- | --- | --- |
| f16 | 9.27 GB | 447 ms | 52.0 |
| Q4_K_M | 3.42 GB | 388 ms | 52.1 |

## Entrenamiento

| tag | máquina | región | ejemplos | duración | costo estimado | loss inicial → final |
| --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-09 | Cloud Run Job: 1x NVIDIA L4 (no zonal redundancy), 8 vCPU, 32 GiB | europe-west4 | 1000 | 17.4 min | $0.41 | 2.33 → 0.14 |

Costo = segundos facturados × tarifas por segundo de Cloud Run (GPU L4 sin redundancia zonal + vCPU + memoria). Un reentrenamiento mensual cuesta eso; la inferencia de David cuesta $0 porque corre en la laptop.

## Dónde pierde David

David gana 180 de 319 frases por chrF++ de oración. Las 10 peores derrotas:

| frase | referencia | David | Goliath | Δ chrF++ |
| --- | --- | --- | --- | --- |
| […] | ¿Usted cree que yo soy boba o qué? | ¿A que nací ayer, no? | ¿Usted cree que yo soy marica o qué? | -67.3 |
| […] | La película estuvo regular, nada del otro mundo. | La película fue nada especial. | La película estuvo regular—nada del otro mundo. | -54.8 |
| […] | ¡Quiubo, mijo! ¿Cómo le va? | ¡Qué hubo pues compañero! ¿Todo bien o no? | ¡Quiubo mijo! ¿Cómo me le va? | -54.4 |
| […] | ¿Qué, creen que soy su chacha o qué onda? | ¿Qué onda que soy tu sirvienta? | ¿Qué onda, creen que soy su chacha o qué? | -54.0 |
| Qué hueva ir a la chamba hoy. | Qué flojera me da ir a trabajar hoy. | Qué pereza ir al trabajo hoy. | Qué flojera me da tener que ir a trabajar hoy. | -54.0 |
| […] | ¡Qué chido que ganaste, te la rifaste! | ¡Qué chido que ganaras! | ¡Qué chido que ganaste, te la rifaste! | -50.6 |
| […] | Sí, yo le aviso. | Claro que sí, yo te digo. | Sale y vale, yo le aviso. | -48.6 |
| […] | Esa morra es red flag, bro. | Esa chava no te conviene. | Esa morra es una red flag andante. | -47.3 |
| […] | Ese parche no me cuadra | Esa amistad no me llega. | Ese parche no me da buena vibra | -45.1 |
| […] | ¿Por qué tan decaído, mijo? —Es que perdí la materia, hermano. | ¿Por qué tan descorazonado, amigo? —Es que me cargó el payaso, parce. | ¿Por qué tan achicopalado, mijo? —Es que perdí la materia, hermano. | -44.6 |

## Metodología

- Mismo prompt para todos (`duel/genlingo_duel/prompts.py`), temperatura 0.
- chrF++ = sacrebleu CHRF con `word_order=2`, a nivel de corpus.
- Costo de Goliath = tokens × precio por millón configurado (`GEMINI_*_USD_PER_M`); los tokens de razonamiento se cobran como salida.
- Resultados por frase en `evals/results/`.
