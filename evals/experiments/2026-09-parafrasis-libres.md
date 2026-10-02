> Experimento descartado: pares de **paráfrasis libre** (el primer intento de datos sintéticos). El modelo se llamaba `genlingo-2026-09-pairs-v1`.

# Genlingo — evaluación

Generado por `make eval` el 2026-09-30 15:30. 319 pares de prueba (web; nunca sintéticos).

> **Ensayo:** las referencias de prueba aún están en `pending_review` (sin revisión del presentador). Los números cambiarán al aprobar/corregir el set con `make review-test`.

## Resumen

chrF++ de corpus (0–100, más es mejor) contra la referencia humana. Latencia de extremo a extremo con el modelo ya cargado; los modelos locales corren uno a la vez en la laptop del escenario.

| modelo | rol | chrF++ | p50 | p95 | costo total | costo / 1,000 frases | tamaño | errores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma4:e2b-it-qat | base (sin ajuste) | 47.1 | 334 ms | 486 ms | $0 | $0 | 4.34 GB | 0 |
| gemma4:e4b | base (sin ajuste) | 47.0 | 687 ms | 926 ms | $0 | $0 | 6.58 GB | 0 |
| genlingo-2026-09-parafrasis | David (LoRA, Q4) | 39.1 | 412 ms | 564 ms | $0 | $0 | 3.42 GB | 0 |
| genlingo-2026-09-parafrasis-f16 | David (LoRA, f16) | 40.1 | 491 ms | 684 ms | $0 | $0 | 9.27 GB | 1 |
| gemini-3.8-flash | Goliath | 48.8 | 1.42 s | 6.14 s | $0.1284 | $0.4036 | — | 1 |

**Línea base "copiar la frase"** (devolver el texto original sin traducir): chrF++ 50.0. Un modelo que no supera esta línea no está traduciendo mejor que no hacer nada; mide cuánto del puntaje viene de palabras que la referencia comparte con el original.

### chrF++ por origen

| modelo | web |
| --- | --- |
| gemma4:e2b-it-qat | 47.1 (n=319) |
| gemma4:e4b | 47.0 (n=319) |
| genlingo-2026-09-parafrasis | 39.1 (n=319) |
| genlingo-2026-09-parafrasis-f16 | 40.1 (n=318) |
| gemini-3.8-flash | 48.8 (n=318) |

### chrF++ por dirección

| modelo | genz_to_parent | parent_to_genz |
| --- | --- | --- |
| gemma4:e2b-it-qat | 52.5 (n=164) | 40.7 (n=155) |
| gemma4:e4b | 54.4 (n=164) | 38.3 (n=155) |
| genlingo-2026-09-parafrasis | 42.7 (n=164) | 34.8 (n=155) |
| genlingo-2026-09-parafrasis-f16 | 43.9 (n=164) | 35.6 (n=154) |
| gemini-3.8-flash | 56.0 (n=164) | 40.3 (n=154) |

### chrF++ por país

| modelo | CO | GT | LATAM | MX |
| --- | --- | --- | --- | --- |
| gemma4:e2b-it-qat | 46.2 (n=88) | 48.7 (n=73) | 47.4 (n=70) | 46.3 (n=88) |
| gemma4:e4b | 48.8 (n=88) | 48.1 (n=73) | 45.1 (n=70) | 45.3 (n=88) |
| genlingo-2026-09-parafrasis | 38.2 (n=88) | 41.2 (n=73) | 40.1 (n=70) | 37.3 (n=88) |
| genlingo-2026-09-parafrasis-f16 | 39.5 (n=88) | 42.5 (n=73) | 39.9 (n=70) | 39.0 (n=87) |
| gemini-3.8-flash | 49.5 (n=88) | 44.8 (n=73) | 53.4 (n=70) | 46.9 (n=87) |

## Modelo base: E2B vs E4B

Regla: el más pequeño que cumpla p50 < 1 s con el mejor chrF++.

**gemma4:e2b-it-qat**: mejor chrF++ (47.1) entre los que cumplen p50 < 1 s (p50 334 ms, 4.34 GB).

## Compresión: f16 vs Q4

| versión | tamaño | p50 | chrF++ |
| --- | --- | --- | --- |
| f16 | 9.27 GB | 491 ms | 40.1 |
| Q4_K_M | 3.42 GB | 412 ms | 39.1 |

## Entrenamiento

| tag | máquina | región | ejemplos | duración | costo estimado | loss inicial → final |
| --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-09-parafrasis | Apple M1 Max 64 GB (local, MPS) | laptop | 1000 | 36.9 min | $0 | 4.85 → 0.75 |

Costo = duración × tarifa por hora estimada ($0.0/h). La inferencia de David cuesta $0: corre en la laptop.

## Dónde pierde David

David gana 104 de 318 frases por chrF++ de oración. Las 10 peores derrotas:

| frase | referencia | David | Goliath | Δ chrF++ |
| --- | --- | --- | --- | --- |
| […] | Eres un as en ese juego | Eres muy bueno jugando ese videojuego. | Eres un as en ese juego | -72.7 |
| […] | Me gusta el ambiente de ese lugar, es muy tranquilo. | Me parece muy agradable ese sitio, tiene un ambiente muy relajado. | Me gusta el ambiente de ese lugar, es muy tranquilo. | -71.3 |
| […] | Se me antojan unas cervecitas. | Tengo muchas ganas de tomar una cerveza. | Se me antojan unas cervecitas bien frías. | -68.4 |
| […] | Hermano, no puedo ir con ustedes a cine. Estoy sin un peso. | Mijo, no me apetece ir al cine hoy, prefiero quedarme a descansar. | Hombre, no puedo ir con ustedes a cine. Estoy sin un peso. | -67.0 |
| Subieron fotos del cumple y yo ni sabía, GPI. | Subieron fotos del cumpleaños y yo ni enterada, gracias por invitar, ¿eh? | No me enteré de la fiesta de cumpleaños hasta después, qué sorpresa tan grande. | Publicaron fotos del cumpleaños y yo ni enterado, gracias por invitarme, ¿eh? | -57.3 |
| […] | ¿Usted cree que yo soy boba o qué? | ¿En serio crees que soy de ayer? | ¿Usted cree que yo soy huevón o qué? | -55.7 |
| Anoche nos fuimos de reven y estuvo de pelos. | Anoche nos fuimos de peda y estuvo buenísima. | Ayer nos pusimos a andar de fiesta y nos la pasamos un chorro. | Anoche nos fuimos de peda y estuvo épico. | -54.9 |
| Yo me foquié y cuando desperté tenía casi cien llamadas perdidas | Me quedé profundo y cuando me desperté tenía casi cien llamadas perdidas | Me desperté con el teléfono lleno de llamadas perdidas, qué situación tan rara. | Me quedé profundamente dormido y cuando me desperté tenía casi cien llamadas perdidas | -53.7 |
| […] | Sí, yo le aviso. | Sí, es verdad. | Sale y vale, yo le aviso. | -53.0 |
| Qué cuerudo sos, no te da vergüenza nada. | Qué descarado sos, maje, cero pena. | Qué molleja, no te da pena nada. | Qué descarado sos, cero pena te da todo. | -51.9 |

## Metodología

- Mismo prompt para todos (`duel/genlingo_duel/prompts.py`), temperatura 0.
- chrF++ = sacrebleu CHRF con `word_order=2`, a nivel de corpus.
- Costo de Goliath = tokens × precio por millón configurado (`GEMINI_*_USD_PER_M`); los tokens de razonamiento se cobran como salida.
- Resultados por frase en `evals/results/`.
