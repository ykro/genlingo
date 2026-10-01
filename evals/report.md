# Genlingo — evaluación

Generado por `make eval` el 2026-10-01 11:41. 319 pares de prueba (web; nunca sintéticos).

> **Ensayo:** las referencias de prueba aún están en `pending_review` (sin revisión del presentador). Los números cambiarán al aprobar/corregir el set con `make review-test`.

## Resumen

chrF++ de corpus (0–100, más es mejor) contra la referencia humana. Latencia de extremo a extremo con el modelo ya cargado; los modelos locales corren uno a la vez en la laptop del escenario.

| modelo | rol | prompt | chrF++ | p50 | p95 | costo total | costo / 1,000 frases | tamaño | errores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma4:e2b-it-qat | base (sin ajuste) | v2 | 48.7 | 370 ms | 495 ms | $0 | $0 | 4.34 GB | 0 |
| gemma4:e2b-it-qat + glosario | base (sin ajuste) | v2 + glosario | 52.0 | 501 ms | 713 ms | $0 | $0 | 4.34 GB | 0 |
| gemma4:e4b | base (sin ajuste) | v2 | 47.1 | 775 ms | 1.07 s | $0 | $0 | 6.58 GB | 0 |
| genlingo-2026-10-e2b + glosario | David (LoRA, Q4) | v2 + glosario | 51.2 | 496 ms | 683 ms | $0 | $0 | 3.42 GB | 0 |
| genlingo-2026-10-e2b-f16 + glosario | David (LoRA, f16) | v2 + glosario | 51.9 | 534 ms | 776 ms | $0 | $0 | 9.27 GB | 0 |
| genlingo-2026-10-e4b + glosario | David candidato (LoRA, Q4) | v2 + glosario | 52.4 | 836 ms | 1.12 s | $0 | $0 | 5.30 GB | 0 |
| genlingo-2026-09 | David candidato (LoRA, Q4) | v1 | 52.1 | 386 ms | 548 ms | $0 | $0 | 3.42 GB | 0 |
| genlingo-2026-09-f16 | David candidato (LoRA, f16) | v1 | 52.0 | 432 ms | 636 ms | $0 | $0 | 9.27 GB | 0 |
| gemini-3.8-flash | Goliath | v2 | 52.1 | 5.22 s | 14.68 s | $0.35 | $1.10 | — | 6 |
| gemini-3.8-flash + glosario | Goliath con el glosario de David | v2 + glosario | 55.0 | 5.09 s | 15.97 s | $0.37 | $1.17 | — | 1 |

Costo de Goliath con la tarifa del día del eval: $0.75 entrada / $3.75 salida por millón de tokens (vigente desde 2026-09-30).
Con la tarifa desde 2027-01-01 ($1.50 / $7.50), este mismo eval costaría $0.69 ($2.21 por 1,000 frases).

**Línea base "copiar la frase"** (devolver el texto original sin traducir): chrF++ 50.0. Un modelo que no supera esta línea no está traduciendo mejor que no hacer nada; mide cuánto del puntaje viene de palabras que la referencia comparte con el original.

Sin evaluar: `genlingo-2026-10-e4b-f16 + glosario` (no está en Ollama (make pull-model)).

## ¿Tradujo la jerga?

chrF++ premia parecerse a la referencia, y una reescritura de registro conserva casi todas las palabras: por eso copiar la frase ya saca ~50. Estas dos métricas miran solo lo que tenía que cambiar (detalle en `evals/term_accuracy.py`):

- **Jerga resuelta**: Gen Z → papás, no queda en la salida ningún término Gen Z del banco que tenía la frase; papás → Gen Z, la salida usa al menos un término Gen Z del banco del país. Mide que cambió el registro, no que el significado sea correcto.
- **Cambios acertados**: de las palabras que la referencia humana cambió respecto al original, cuántas aparecen en la salida. Mide significado, pero solo con palabras exactas: un sinónimo válido cuenta como fallo para todos.

| modelo | jerga resuelta Gen Z → papás | jerga resuelta papás → Gen Z | jerga resuelta total | cambios acertados |
| --- | --- | --- | --- | --- |
| copiar la frase (línea base) | 0 % (n=149) | 1 % (n=155) | 0 % (n=304) | 0 % |
| gemma4:e2b-it-qat | 92 % (n=149) | 10 % (n=155) | 50 % (n=304) | 15 % |
| gemma4:e2b-it-qat + glosario | 93 % (n=149) | 21 % (n=155) | 57 % (n=304) | 20 % |
| gemma4:e4b | 94 % (n=149) | 30 % (n=155) | 61 % (n=304) | 16 % |
| genlingo-2026-10-e2b + glosario | 95 % (n=149) | 40 % (n=155) | 67 % (n=304) | 13 % |
| genlingo-2026-10-e2b-f16 + glosario | 97 % (n=149) | 54 % (n=155) | 75 % (n=304) | 15 % |
| genlingo-2026-10-e4b + glosario | 94 % (n=149) | 41 % (n=155) | 67 % (n=304) | 15 % |
| genlingo-2026-09 | 90 % (n=149) | 21 % (n=155) | 55 % (n=304) | 15 % |
| genlingo-2026-09-f16 | 90 % (n=149) | 28 % (n=155) | 58 % (n=304) | 13 % |
| gemini-3.8-flash | 98 % (n=145) | 37 % (n=153) | 66 % (n=298) | 25 % |
| gemini-3.8-flash + glosario | 99 % (n=149) | 65 % (n=155) | 82 % (n=304) | 30 % |

**David en escena:** `genlingo-2026-10-e2b-f16 + glosario` — la variante de David con más jerga resuelta (75 %) que cumple p50 < 1 s (p50 534 ms).

Cara a cara con `gemini-3.8-flash` en jerga resuelta: David la resuelve y Goliath no en **51** frases; al revés en **26**.

Cara a cara con `gemini-3.8-flash + glosario` en jerga resuelta: David la resuelve y Goliath no en **27** frases; al revés en **48**.

Jerga de otro país en papás → Gen Z (p. ej. «pisto» guatemalteco en una frase mexicana): gemma4:e2b-it-qat 7, gemma4:e2b-it-qat + glosario 6, gemma4:e4b 14, genlingo-2026-10-e2b + glosario 13, genlingo-2026-10-e4b + glosario 10, genlingo-2026-09 16, gemini-3.8-flash 8, gemini-3.8-flash + glosario 2 (de 155).

**Lectura honesta:** resultado mixto: cada uno gana en una de las dos métricas de jerga.

Con el mismo glosario, Goliath resuelve 82 % de la jerga frente al 75 % de David: la ventaja de David viene de **sus datos** (el banco de términos), no de ser mejor modelo; y esos datos los tiene él, no Goliath.

Compresión y jerga: `genlingo-2026-10-e2b + glosario` (Q4, 3.42 GB) resuelve 67 % frente al 75 % de `genlingo-2026-10-e2b-f16 + glosario` (9.27 GB). Cuantizar cuesta jerga, no solo chrF++.

### chrF++ por origen

| modelo | web |
| --- | --- |
| gemma4:e2b-it-qat | 48.7 (n=319) |
| gemma4:e2b-it-qat + glosario | 52.0 (n=319) |
| gemma4:e4b | 47.1 (n=319) |
| genlingo-2026-10-e2b + glosario | 51.2 (n=319) |
| genlingo-2026-10-e2b-f16 + glosario | 51.9 (n=319) |
| genlingo-2026-10-e4b + glosario | 52.4 (n=319) |
| genlingo-2026-09 | 52.1 (n=319) |
| genlingo-2026-09-f16 | 52.0 (n=319) |
| gemini-3.8-flash | 52.1 (n=313) |
| gemini-3.8-flash + glosario | 55.0 (n=318) |

### chrF++ por dirección

| modelo | genz_to_parent | parent_to_genz |
| --- | --- | --- |
| gemma4:e2b-it-qat | 55.6 (n=164) | 40.7 (n=155) |
| gemma4:e2b-it-qat + glosario | 60.8 (n=164) | 41.7 (n=155) |
| gemma4:e4b | 54.2 (n=164) | 38.7 (n=155) |
| genlingo-2026-10-e2b + glosario | 57.7 (n=164) | 43.6 (n=155) |
| genlingo-2026-10-e2b-f16 + glosario | 58.6 (n=164) | 44.0 (n=155) |
| genlingo-2026-10-e4b + glosario | 58.9 (n=164) | 44.7 (n=155) |
| genlingo-2026-09 | 59.5 (n=164) | 43.5 (n=155) |
| genlingo-2026-09-f16 | 59.0 (n=164) | 43.9 (n=155) |
| gemini-3.8-flash | 58.9 (n=160) | 44.3 (n=153) |
| gemini-3.8-flash + glosario | 61.7 (n=163) | 47.3 (n=155) |

### chrF++ por país

| modelo | CO | GT | LATAM | MX |
| --- | --- | --- | --- | --- |
| gemma4:e2b-it-qat | 47.6 (n=88) | 50.8 (n=73) | 49.0 (n=70) | 48.0 (n=88) |
| gemma4:e2b-it-qat + glosario | 49.9 (n=88) | 56.7 (n=73) | 53.6 (n=70) | 49.0 (n=88) |
| gemma4:e4b | 47.4 (n=88) | 49.7 (n=73) | 46.7 (n=70) | 44.5 (n=88) |
| genlingo-2026-10-e2b + glosario | 51.1 (n=88) | 54.6 (n=73) | 50.9 (n=70) | 48.5 (n=88) |
| genlingo-2026-10-e2b-f16 + glosario | 51.3 (n=88) | 56.4 (n=73) | 52.0 (n=70) | 48.3 (n=88) |
| genlingo-2026-10-e4b + glosario | 52.1 (n=88) | 56.7 (n=73) | 52.4 (n=70) | 48.6 (n=88) |
| genlingo-2026-09 | 51.7 (n=88) | 56.4 (n=73) | 51.1 (n=70) | 49.5 (n=88) |
| genlingo-2026-09-f16 | 52.5 (n=88) | 56.3 (n=73) | 50.9 (n=70) | 48.5 (n=88) |
| gemini-3.8-flash | 52.4 (n=87) | 49.4 (n=71) | 55.9 (n=68) | 50.6 (n=87) |
| gemini-3.8-flash + glosario | 54.1 (n=88) | 55.0 (n=73) | 59.6 (n=70) | 51.8 (n=87) |

## Modelo base: E2B vs E4B

Regla: el más pequeño que cumpla p50 < 1 s con el mejor chrF++.

**gemma4:e2b-it-qat**: mejor chrF++ (48.7) entre los que cumplen p50 < 1 s (p50 370 ms, 4.34 GB).

## Compresión: f16 vs Q4

| versión | tamaño | p50 | chrF++ |
| --- | --- | --- | --- |
| f16 | 9.27 GB | 534 ms | 51.9 |
| Q4_K_M | 3.42 GB | 496 ms | 51.2 |

## Entrenamiento

| tag | máquina | región | ejemplos | duración | costo estimado | loss inicial → final |
| --- | --- | --- | --- | --- | --- | --- |
| genlingo-2026-10-e2b | Cloud Run Job: 1x NVIDIA L4 (no zonal redundancy), 8 vCPU, 32 GiB | europe-west4 | 1500 | 28.2 min | $0.67 | 2.26 → 0.12 |

Costo = segundos facturados × tarifas por segundo de Cloud Run (GPU L4 sin redundancia zonal + vCPU + memoria). Un reentrenamiento mensual cuesta eso; la inferencia de David cuesta $0 porque corre en la laptop.

## Dónde pierde David

David gana 136 de 313 frases por chrF++ de oración. Las 10 peores derrotas:

| frase | referencia | David | Goliath | Δ chrF++ |
| --- | --- | --- | --- | --- |
| […] | ¿Usted cree que yo soy boba o qué? | Nadie es delulu del todo, vive en la realidad. | ¿Usted cree que yo soy güevón o qué? | -67.8 |
| […] | Qué fiestón el de anoche | Hubo tremendo mitote anoche. | Qué buen fiestón el de anoche | -59.5 |
| […] | La película estuvo regular, nada del otro mundo. | La película fue aburrida y nada especial. | La película estuvo regular—nada del otro mundo. | -54.9 |
| Usted qué cree ¿que esto es un hotel? | ¿Qué, cree que esto es un Airbnb o qué, parce? | Qué lache que lleguemos tan tarde. | ¿Usted qué se cree, que esto es un Airbnb o qué, mk? | -52.9 |
| […] | Esa morra es red flag, bro. | Esa chava no te conviene. | Esa morra es pura red flag. | -50.8 |
| […] | No te preocupes, yo me encargo | ¡Sosiégate!, yo me encargo. | No te preocupes, yo me encargo. | -50.5 |
| […] | ¿Qué te pasó que hoy andas con tan buena vibra? | ¿Qué te ha pasado que hoy estás tan shadeando? | ¿Qué te pasó que hoy andas con tanta vibra? | -49.1 |
| […] | ¿Qué onda, tus compas no tienen casa o qué? | ¿Qué, tus amigos no tienen depa? | ¿Qué onda, tus compas no tienen cantón o qué? | -48.0 |
| […] | Esto no es Airbnb, eh. | Aquí no nacimos durmiendo en la calle. | Esto no es un Airbnb. | -44.9 |
| ¡Malaya fuera rico para comprarme esa casa! | ¡Ojalá tuviera un montón de pisto para comprarme esa casa! | Espero que me llegue esa casa. | ¡Manifestando tener pisto para comprarme esa casa! | -39.8 |

## Metodología

- Mismo prompt para todos (`duel/genlingo_duel/prompts.py`), temperatura 0.
- chrF++ = sacrebleu CHRF con `word_order=2`, a nivel de corpus.
- Costo de Goliath = tokens × precio por millón configurado (`GEMINI_*_USD_PER_M`); los tokens de razonamiento se cobran como salida.
- Resultados por frase en `evals/results/`.
