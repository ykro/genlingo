# Ronda 5 · frases con varios términos de jerga (2026-10-07)

**Pregunta.** El modelo grande conoce muchos términos sueltos; ¿gana el pequeño cuando una frase junta 2–4
términos de jerga del mismo país? El nicho «Combinaciones» se registró antes de buscar datos, entrenar o
calcular nada ([niche.md](../niche.md), enmienda 2, commit `7760c3f`).

## Datos nuevos

- **Oraciones reales de la web** (`raw/web_usage_2026-10-07.jsonl`, fuentes S93–S133 en `data/SOURCES.md`): 422,
  cada una descargada de nuevo y comprobada palabra por palabra contra su página.
  - Habla real: México 89 (casi todo publicaciones de X), español neutro 130 (Bluesky, reseñas de Steam en
    «Español-Latinoamérica», X, títulos de YouTube, ejemplos de medios), Colombia 78 (comentarios de blogs y
    foros, Wattpad, X citados en Infobae), Guatemala 5 (comentarios de blogs).
  - Ejemplos escritos por los editores de Magikitos (España, mismo editor para todos los países): Colombia 72,
    Guatemala 48. Solo para entrenar, nunca en el nicho (aclaración registrada antes de calcular nada).
  - De Argentina, Chile, Perú, Venezuela y España solo se tomaron frases con jerga Gen Z panhispana (etiqueta
    LATAM); la página solo conoce MX, GT, CO y LATAM.
  - 43 oraciones con 2 o más términos del banco congelado quedaron apartadas para el nicho (México 23, español
    neutro 15, Colombia 5); el resto dio 567 pares de entrenamiento y 126 de desarrollo, en las dos direcciones.
- **Banco de términos:** 202 términos Gen Z nuevos (CO 104, GT 35, LATAM 32, MX 31), con contrapartes validadas por
  significado solo para los nuevos (`build_counterparts.py --only-new`: los enlaces existentes, que usa el juicio,
  no se movieron). Una primera versión tenía 323; se quitaron 121 que eran palabras normales («pues», «video»,
  «profe»), préstamos genéricos («ok», «look») o duplicados.
- **Sintéticos** (solo entrenamiento, `gemini-3.8-flash`, versión de prompt y semilla en cada par):
  - `synthetic_combo` (`synthetic-combo-2026-10e`, semilla 6067, $0.42): frases naturales de 5–22 palabras con 2–3
    términos de un país, cada término comprobado por significado en la versión de papás. Dan los dos sentidos.
    Generadas 1,252, válidas 324 frases (648 pares); 261 frases (522 pares) siguen siendo válidas con el banco curado.
  - `synthetic_p2g` (`synthetic-2026-10b`, semilla 5051, $0.30): papás → Gen Z de un término, solo MX, CO y
    LATAM. 600 generados, 462 válidos con el banco curado.
- **Por qué no se repite el error de la ronda 3** (pares de 2–3 términos que bajaron chrF++ y alargaron las
  respuestas): frases cortas y naturales en vez de términos forzados, cada término validado por significado, las
  dos direcciones y una parte menor del entrenamiento (15 %). El p50 del ganador quedó en 253 ms.

## Variantes (todas E2B, LoRA igual que 10d, decididas en desarrollo)

Desarrollo: 280 pares (241 juzgables), 69 de ellos «combinaciones». Jerga correcta con la regla de la revisión
término por término (`term_check.py`), igual para todos.

| variante | qué prueba | ejemplos | épocas | dev | dev combinaciones | p50 | costo |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **`genlingo-2026-10e-e2b`** | todo, sintéticos viejos al 60 % | 4,321 | 2.5 | 58.1 % | **56.5 %** | 275 ms | $1.44 |
| `…-all` | todo, sin recortar | 5,670 | 1.9 | 57.3 % | 49.3 % | 272 ms | $1.39 |
| `…-webonly` | solo las oraciones reales nuevas | 3,073 | 3 | 56.4 % | 47.8 % | 271 ms | $1.24 |
| `…-nocombo` | sin las combinaciones sintéticas | 3,673 | 3 | 53.1 % | 46.4 % | 273 ms | $1.44 |
| `…-v2` | como el ganador, con el banco curado | 4,042 | 2.7 | 59.3 % | 52.2 % | 270 ms | $1.39 |
| `…-v2-nocombo` | `-v2` sin combinaciones sintéticas | 3,520 | 3 | 54.4 % | 40.6 % | 270 ms | $1.33 |
| `genlingo-2026-10d-e2b` | el David de la página | — | — | 49.0 % | 34.8 % | 278 ms | — |
| Goliath (`gemini-3.8-flash`) | rival | — | — | 39.6 % | 35.3 % | 3.38 s | — |
| Goliath + léxico | referencia | — | — | 58.9 % | 59.4 % | 3.40 s | — |

- **Regla registrada:** gana la de más jerga correcta en combinaciones de desarrollo, sin bajar más de 2 puntos en
  todo el desarrollo contra 10d y con p50 < 1 s → `genlingo-2026-10e-e2b`.
- Las combinaciones sintéticas son lo que más suma: sin ellas, 46.4 % y 40.6 %; con ellas, 56.5 % y 52.2 %.
- `genlingo-2026-10e-e2b` se entrenó con los datos antes de curar el banco (su léxico de entrenamiento tenía los
  121 términos que luego se quitaron); el archivo exacto está en
  `gs://ai-experiments-487722-train-eu/genlingo/data/genlingo-2026-10e-e2b/train.jsonl`. En el eval usa el banco curado.
- `…-v2-all` no llegó a entrenar (falló la subida de sus datos); no se repitió porque `-all` ya había quedado abajo.
- Costo de la ronda: entrenamientos $8.23 (6 corridas), Gemini $0.72 de sintéticos, más los evals en la nube.

## Resultado final (eval del 2026-10-07 en la nube; `report.md`, `report_combos.md`, `report_probe.md`)

Jerga correcta, David `genlingo-2026-10e-e2b` contra Goliath sin glosario, IC 95 % por bootstrap pareado.

| corte | n | David | Goliath | Δ | IC 95 % | veredicto |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| **Combinaciones (nicho)** | 174 | 62 % | 45 % | +16.7 | [+7.5, +25.9] | **gana David** |
| Combinaciones · Gen Z → papás | 78 | 63 % | 33 % | +29.5 | [+15.4, +43.6] | gana David |
| Combinaciones · papás → Gen Z | 96 | 61 % | 55 % | +6.2 | [−5.2, +17.7] | empate |
| Combinaciones · México | 67 | 66 % | 52 % | +13.4 | [−1.5, +26.9] | empate |
| Combinaciones · Colombia | 46 | 52 % | 33 % | +19.6 | [+0.0, +39.1] | empate (límite en 0) |
| Combinaciones · español neutro | 39 | 72 % | 64 % | +7.7 | [−10.3, +25.6] | empate |
| Set de prueba completo | 398 | 58 % | 34 % | +24.1 | [+18.6, +29.6] | gana David |
| Prueba · México | 77 | 65 % | 48 % | +16.9 | [+5.2, +28.6] | gana David (10d empataba) |
| Prueba · Colombia | 131 | 53 % | 28 % | +24.4 | [+14.5, +34.4] | gana David |
| Prueba · español neutro | 75 | 55 % | 52 % | +2.7 | [−9.3, +14.7] | empate |
| Prueba · Guatemala | 115 | 61 % | 18 % | +42.6 | [+32.2, +53.0] | gana David |
| Prueba · papás → Gen Z | 172 | 32 % | 24 % | +8.1 | [−1.2, +16.9] | empate |

- **El David de antes (10d) en el mismo nicho:** 39 % contra 45 % de Goliath (−6.3 [−16.7, +3.4]); perdía en México
  (−17.9) y en el español neutro (−23.1). La ronda le dio +23 puntos en combinaciones.
- **Contra Goliath con el mismo léxico** (no decide): 62 % contra 61 % en combinaciones, empate; en todo el set
  58 % contra 48 % (+9.8 [+4.3, +15.5]).
- **Lo que sigue perdido o empatado:** papás → Gen Z en español neutro (4 % contra 28 %, n = 25, pierde David) y en
  México (48 % contra 45 %, empate); la sonda de jerga Gen Z general: 88 % contra 94 % de Goliath como español
  neutro (10d: 91 %), empate.
- chrF++ 60.7 (10d 59.8, Goliath 53.2); p50 253 ms; 3.62 GB en Q5_K_M (f16: 60.9 de chrF++, 9.27 GB).
