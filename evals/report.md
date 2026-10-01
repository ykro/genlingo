# Genlingo — evaluación

Generado por `make eval` el 2026-09-30 21:52. 319 pares de prueba (web; nunca sintéticos).

> **Ensayo:** las referencias de prueba aún están en `pending_review` (sin revisión del presentador). Los números cambiarán al aprobar/corregir el set con `make review-test`.

## Resumen

chrF++ de corpus (0–100, más es mejor) contra la referencia humana. Latencia de extremo a extremo con el modelo ya cargado; los modelos locales corren uno a la vez en la laptop del escenario.

| modelo | rol | chrF++ | p50 | p95 | costo total | costo / 1,000 frases | tamaño | errores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma4:e2b-it-qat | base (sin ajuste) | 47.1 | 328 ms | 453 ms | $0 | $0 | 4.34 GB | 0 |
| gemma4:e4b | base (sin ajuste) | 47.0 | 685 ms | 890 ms | $0 | $0 | 6.58 GB | 0 |
| genlingo-2026-09 | David (LoRA, Q4) | 52.1 | 388 ms | 561 ms | $0 | $0 | 3.42 GB | 0 |
| genlingo-2026-09-f16 | David (LoRA, f16) | 52.0 | 439 ms | 643 ms | $0 | $0 | 9.27 GB | 0 |
| gemini-3.8-flash | Goliath | 48.2 | 1.28 s | 5.82 s | $0.13 | $0.41 | — | 0 |

**Línea base "copiar la frase"** (devolver el texto original sin traducir): chrF++ 50.0. Un modelo que no supera esta línea no está traduciendo mejor que no hacer nada; mide cuánto del puntaje viene de palabras que la referencia comparte con el original.

### chrF++ por origen

| modelo | web |
| --- | --- |
| gemma4:e2b-it-qat | 47.1 (n=319) |
| gemma4:e4b | 47.0 (n=319) |
| genlingo-2026-09 | 52.1 (n=319) |
| genlingo-2026-09-f16 | 52.0 (n=319) |
| gemini-3.8-flash | 48.2 (n=319) |

### chrF++ por dirección

| modelo | genz_to_parent | parent_to_genz |
| --- | --- | --- |
| gemma4:e2b-it-qat | 52.5 (n=164) | 40.7 (n=155) |
| gemma4:e4b | 54.4 (n=164) | 38.3 (n=155) |
| genlingo-2026-09 | 59.5 (n=164) | 43.5 (n=155) |
| genlingo-2026-09-f16 | 59.0 (n=164) | 43.9 (n=155) |
| gemini-3.8-flash | 55.6 (n=164) | 39.6 (n=155) |

### chrF++ por país

| modelo | CO | GT | LATAM | MX |
| --- | --- | --- | --- | --- |
| gemma4:e2b-it-qat | 46.2 (n=88) | 48.7 (n=73) | 47.4 (n=70) | 46.3 (n=88) |
| gemma4:e4b | 48.8 (n=88) | 48.1 (n=73) | 45.1 (n=70) | 45.3 (n=88) |
| genlingo-2026-09 | 51.7 (n=88) | 56.4 (n=73) | 51.1 (n=70) | 49.5 (n=88) |
| genlingo-2026-09-f16 | 52.5 (n=88) | 56.3 (n=73) | 50.9 (n=70) | 48.5 (n=88) |
| gemini-3.8-flash | 47.6 (n=88) | 43.0 (n=73) | 55.3 (n=70) | 47.2 (n=88) |

## Modelo base: E2B vs E4B

Regla: el más pequeño que cumpla p50 < 1 s con el mejor chrF++.

**gemma4:e2b-it-qat**: mejor chrF++ (47.1) entre los que cumplen p50 < 1 s (p50 328 ms, 4.34 GB).

## Compresión: f16 vs Q4

| versión | tamaño | p50 | chrF++ |
| --- | --- | --- | --- |
| f16 | 9.27 GB | 439 ms | 52.0 |
| Q4_K_M | 3.42 GB | 388 ms | 52.1 |

## Entrenamiento

| tag | máquina | región | ejemplos | duración | costo estimado | loss inicial → final |
| --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-09 | Cloud Run Job: 1x NVIDIA L4 (no zonal redundancy), 8 vCPU, 32 GiB | europe-west4 | 1000 | 17.4 min | $0.41 | 2.33 → 0.14 |

Costo = segundos facturados × tarifas por segundo de Cloud Run (GPU L4 sin redundancia zonal + vCPU + memoria). Un reentrenamiento mensual cuesta eso; la inferencia de David cuesta $0 porque corre en la laptop.

## Dónde pierde David

David gana 178 de 319 frases por chrF++ de oración. Las 10 peores derrotas:

| frase | referencia | David | Goliath | Δ chrF++ |
| --- | --- | --- | --- | --- |
| […] | Shakira se lució en la gala del MET | Shakira fue la sensación en la gala. | Shakira se lució en la gala del MET | -55.0 |
| […] | La película estuvo regular, nada del otro mundo. | La película fue nada especial. | La película estuvo regular—nada del otro mundo. | -54.8 |
| […] | ¿Por qué me deja en visto, parce? | […] ¿Por qué no me llega el mensaje? | ¿Por qué me deja en visto, mk? | -53.3 |
| […] | Esa morra es red flag, bro. | Esa chava no te conviene. | Esa morra es pura red flag, no te conviene. | -51.0 |
| […] | ¿Qué onda? Te quedaste en modo NPC | ¿Qué te pasa? Andai re bugueado. | ¿Qué onda? Te quedaste tieso | -49.3 |
| […] | Sí, yo le aviso. | Claro que sí, yo te digo. | Sale y vale, yo le aviso. | -48.6 |
| Qué hueva ir a la chamba hoy. | Qué flojera me da ir a trabajar hoy. | Qué pereza ir al trabajo hoy. | Qué flojera ir a trabajar hoy. | -46.7 |
| Qué cuerudo sos, no te da vergüenza nada. | Qué descarado sos, maje, cero pena. | Qué chévere sos, no te da pena nada. | Qué descarado sos, cero pena te da todo. | -44.6 |
| […] | ¿De veras? Pero ¿qué fue lo que pasó? | ¿En serio? Pero, ¿qué pasó? | ¿En serio? Pero ¿qué fue lo que pasó? | -44.5 |
| […] | Eres un as en ese juego | Eres muy bueno en ese juego | Eres un as en ese juego | -44.1 |

## Metodología

- Mismo prompt para todos (`duel/genlingo_duel/prompts.py`), temperatura 0.
- chrF++ = sacrebleu CHRF con `word_order=2`, a nivel de corpus.
- Costo de Goliath = tokens × precio por millón configurado (`GEMINI_*_USD_PER_M`); los tokens de razonamiento se cobran como salida.
- Resultados por frase en `evals/results/`.
