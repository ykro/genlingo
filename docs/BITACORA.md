# Bitácora de David

La historia de David, iteración por iteración: qué cambió, por qué, qué salió, cuánto costó y cuándo.
Incluye los callejones sin salida, porque explican las decisiones que quedaron.

Los números de jerga resuelta y jerga correcta son todos del **mismo set de prueba** (399 frases web
`auto_validated`) en el eval del 2026-10-04 ([evals/report.md](../evals/report.md)), así que se pueden comparar
entre sí. La jerga correcta (el término producido significa lo mismo) nació con la ronda 3. Las ejecuciones
viejas se reevaluaron sobre ese set; los números de su momento (sobre sets anteriores) están en el historial
de `evals/report.md`.

![Jerga resuelta por iteración](diagrams/bitacora-jerga.svg)

## Resumen

| Fecha | Iteración | Qué cambió | Jerga resuelta | Jerga correcta | Costo |
| --- | --- | --- | --- | --- | --- |
| 2026-09-30 | Base sin afinar | Gemma 4 E2B tal cual | 58 % | 14 % | $0 |
| 2026-10-01 | `genlingo-2026-09` | Pares de edición mínima | 62 % | 18 % | $0.41 |
| 2026-10-01 | `genlingo-2026-10-e2b` | Pares anclados en el banco + prompt con glosario | 67 % (Q4) | 25 % | $0.67 |
| 2026-10-01 | Barrido de cuantización | Q5_K_M en vez de Q4_K_M | 74 % | 27 % | $0 (en la Mac) |
| 2026-10-02 | `genlingo-2026-10b-e2b` | Oraciones reales + banco de 406 términos | 82 % | 34 % | $0.71 |
| 2026-10-04 | `genlingo-2026-10c-e2b-nomulti` | Contrapartes por significado + prompt de léxico + ronda 3 de oraciones reales | **82 %** | **42 %** | $0.97 |
| | Goliath (referencia) | `gemini-3.8-flash`, sin glosario | 77 % | 26 % | $1.13 / 1,000 frases |
| | Goliath + el mismo glosario | El banco de David en el prompt de Gemini | 82 % | 38 % | $1.27 / 1,000 frases |

## Callejones sin salida, en una línea

- **Paráfrasis libres** (2026-09-30): David aprendió a reescribir todo y quedó por debajo de no hacer nada (chrF++ 39.1 contra 50.0 de copiar la frase; [detalle](../evals/experiments/2026-09-parafrasis-libres.md)).
- **Un modelo más grande** (E4B, 2026-10-01, $0.98): la misma jerga resuelta que E2B (67 %) con p50 de 836 ms; más modelo no compró más jerga.
- **Q4_K_M**: perdía 7 puntos de jerga contra f16; Q5_K_M no pierde nada y pesa 3.62 GB.
- **Entrenar, fusionar y convertir en un solo job** (`zct96`, $0.63): murió por memoria, porque en Cloud Run el disco vive en la memoria; ahora son dos jobs.
- **Contrapartes por *embedding***: 175 de 217 enlaces significaban otra cosa («brainrot → patatús») y estaban en 1,065 de 1,375 pares sintéticos; quedan archivados solo como respuestas rechazadas.
- **Pares con 2–3 términos a la vez** (2026-10-02, $1.41): en dev, chrF++ 1.3 puntos más bajo y p50 de 1.99 s (809 ms sin ellos); el David de escena se entrenó sin ellos.
- **Preferencias ORPO** (2026-10-04, $0.56 más $1.81 en dos intentos fallidos): +0.5 de chrF++ en dev, pero la jerga resuelta papás → Gen Z bajó de 70 % a 57 %.

## 1 · Pares de edición mínima (`genlingo-2026-09`)

La misma frase con solo los términos de jerga cambiados, generada por Gemini; primer entrenamiento en la
nube (Cloud Run con una L4, 17.4 min, $0.41). **62 %** de jerga resuelta, arriba de la base (58 %), pero
casi todo en Gen Z → papás: en papás → Gen Z resolvía el 20 %. Antes hubo tres ejecuciones fallidas que
también se pagaron (sin `gcc` para Triton, y el GGUF escrito en el bucket montado a ~3 MB/s).

## 2 · Pares anclados en el banco + glosario (`genlingo-2026-10-e2b`)

Cada par nombra un término del banco y su contraparte de la otra generación del mismo país, con trampas
de otro país como negativos difíciles y 60 % papás → Gen Z. El prompt empieza por el país y lleva un
glosario de cuatro entradas recuperadas con EmbeddingGemma; David se entrena con ese mismo prompt.
**67 %** en Q4_K_M y **74 %** en Q5_K_M tras el barrido de cuantización; papás → Gen Z sube de 20 % a 43 %.
$0.67 de entrenamiento y $0.80 de pares.

## 3 · Oraciones reales (`genlingo-2026-10b-e2b`)

Segunda ronda de investigación web: 22 fuentes, 146 términos y 420 oraciones reales. La mitad fue al set
de prueba; la otra mitad, a 334 pares de entrenamiento anclados en la oración real, en las dos
direcciones. **82 %**, +8 puntos, casi todo en papás → Gen Z (43 % → 59 %): supera a Goliath sin glosario
(77 %) y empata con Goliath + glosario (82 %). Entrenar, fusionar y cuantizar de punta a punta en la nube
costó **$0.71**. Se entrenó como `genlingo-2026-11-e2b` y se renombró: los tags llevan la fecha de los
datos (segunda versión de octubre).

## 4 · Set de prueba limpio

Dos frases de prueba estaban citadas dentro de pares de entrenamiento más largos. La validación ahora
compara subcadenas, crudas y normalizadas, contra todos los archivos de entrenamiento: 4 pares de prueba
fuera (403 → 399), quitados del set de prueba y no del entrenamiento porque David ya estaba entrenado.

## 5 · Contrapartes por significado (`genlingo-2026-10c-e2b-nomulti`, en escena)

La revisión de datos encontró el error de las contrapartes (arriba) y que, al entrenar, el término
correcto estaba en el glosario solo el 45 % de las veces. Esta ronda cambió los datos: contrapartes
validadas por significado (`data/counterparts.jsonl`; sin contraparte se dice el significado), 1,715
pares sintéticos regenerados con ellas (1,431 de los 1,500 generados pasaron el filtro con el banco de la
ronda 3, más 284 para los términos nuevos; $0.71 + $0.15, `data/pairs/synthetic.meta.json`), un glosario de léxico con cada término, su contraparte,
términos cercanos y uno de otro país marcado «NO de aquí» (la respuesta está en el 85 % de los ejemplos),
más oraciones reales de Guatemala y Colombia (ronda 3: 532 términos de 26 fuentes) y un set de desarrollo
con métricas de significado registradas antes de calcularlas.

**Dev, 146 pares** (eval del 2026-10-04, [evals/report_dev.md](../evals/report_dev.md)). 10b entrenó con 70
de estos pares (estaban en sus pares reales antes de que existiera el split de dev), así que su número es
optimista; los Davids de la ronda 3 no vieron ninguno.

| | chrF++ | Jerga resuelta | Cambios acertados | Jerga correcta | p50 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `genlingo-2026-10b-e2b` (glosario; vio 70 de los 146) | 65.3 | 91 % | 34 % | 41 % | 592 ms |
| `genlingo-2026-10c-e2b` (léxico, con pares de 2–3 términos) | 61.9 | 86 % | 27 % | 36 % | 1.99 s |
| **`genlingo-2026-10c-e2b-nomulti`** (léxico, sin esos pares) | **63.2** | 85 % | 25 % | 33 % | 809 ms |
| `…-nomulti-orpo` (+ preferencias ORPO) | 63.7 | 78 % | 26 % | 31 % | 866 ms |
| Goliath (`gemini-3.8-flash`) | 51.1 | 76 % | 18 % | 14 % | 3.60 s |
| Goliath + el léxico de David | 58.4 | 88 % | 33 % | 42 % | 3.10 s |

- **Los pares de 2–3 términos no ayudaron:** sin ellos, chrF++ sube 1.3, la jerga queda igual (85 % contra
  86 % resuelta, 33 % contra 36 % correcta) y la latencia baja de 1.99 s a 809 ms (el modelo dejó de alargar
  las respuestas): con ellos, David no cabe en el presupuesto de 1 s.
- **ORPO no ayudó:** +0.5 de chrF++, pero la jerga resuelta en papás → Gen Z baja de 70 % a 57 % y la jerga
  correcta de 33 % a 31 %. Queda fuera. Antes de llegar a entrenar falló dos veces: el modelo se cargaba en la CPU para muestrear y,
  con lote 4, los logits de Gemma no cabían en la L4 (ahora lote 1 × 16).
- **Costo:** 10c $1.41, nomulti $0.97, ORPO $0.56 (más $1.81 de los dos intentos fallidos).

**Prueba, 399 frases (eval del 2026-10-04).** Con el mejor del dev elegido, el set de prueba se corrió una
sola vez. Contra Goliath sin glosario, como en escena, con IC 95 % por bootstrap pareado:

- **chrF++:** 59.7 contra 53.5 (+6.2 [+4.3, +8.1]); contra Goliath con el mismo glosario, 57.0 (+2.7
  [+0.8, +4.7]); contra el David de la ronda 2 (10b), 56.6 (+3.1 [+1.7, +4.4]).
- **Jerga correcta:** 42 % contra 26 % (+16.3 [+10.8, +21.8]); 101 frases las acierta solo David y 36 solo
  Goliath. El David de la ronda 2 acertaba el 34 %.
- **Jerga resuelta:** 82 % contra 77 % (+4.5 [+0.0, +8.8]), empate. **Cambios acertados:** 28 % contra 25 %.
- **p50** 670 ms contra 2.60 s; **costo** $0 contra $1.13 por 1,000 frases.

**Decisión:** `genlingo-2026-10c-e2b-nomulti` pasa a escena (`LOCAL_MODEL_TAG`). Es el mejor de la ronda 3 en
dev dentro del presupuesto de p50 < 1 s, y la prueba lo confirma contra 10b en chrF++ y jerga correcta, con el
mismo tamaño (3.62 GB). `genlingo-2026-10b-e2b` quedó en `DAVID_TAGS` para comparar rondas, y el David anterior
(`DAVID_PREVIOUS_TAG`) siguió siendo `genlingo-2026-10-e2b-q5_k_m`.

## Dónde gana David hoy, y dónde no

Nichos definidos antes de mirar resultados ([evals/niche.md](../evals/niche.md)); métrica: jerga correcta
(enmienda 1, registrada antes de calcularla); IC 95 % por bootstrap pareado
([evals/niche_report.md](../evals/niche_report.md)). David en escena contra Goliath sin glosario:

| Nicho | n | David | Goliath | Δ | IC 95 % | Veredicto |
| --- | --- | --- | --- | --- | --- | --- |
| Slang chapín (GT) | 115 | 52 % | 23 % | +29.6 | [+19.1, +40.0] | **gana David** |
| Papás → Gen Z (GT/CO) | 107 | 44 % | 20 % | +24.3 | [+12.1, +36.4] | **gana David** |
| País CO | 131 | 37 % | 19 % | +17.6 | [+8.4, +27.5] | **gana David** |
| País MX | 78 | 46 % | 37 % | +9.0 | [−2.6, +21.8] | empate estadístico |
| País LATAM | 75 | 32 % | 31 % | +1.3 | [−9.3, +12.0] | empate estadístico |
| Todo el set | 399 | 42 % | 26 % | +16.3 | [+10.8, +21.8] | **gana David** |

- **Gana** en slang chapín, en papás → Gen Z, en Colombia y en el set completo; empata en México y en el
  español neutro (LATAM).
- **En jerga resuelta**, que no mira el significado, gana solo en papás → Gen Z (67 % contra 52 %, +15.0
  [+2.8, +27.1]); en Guatemala y en el set completo el límite inferior queda en 0: empate.
- **Contra Goliath con el mismo glosario** (referencia, no decide): David gana en slang chapín (+17.4
  [+7.0, +28.7]) y en papás → Gen Z (+16.0 [+3.8, +28.3]), empata en el set completo (+4.0) y pierde en el
  español neutro (32 % contra 55 %). Con los mismos datos el modelo grande se acerca, pero no alcanza a David
  en lo que David estudió.

## Costo de reentrenar cada mes

El David de la página costó **$0.97** de punta a punta en la nube (36 min de L4 + 10 min de CPU).
En total, las ejecuciones con registro costaron $9.15, incluidas cinco de las seis fallidas ($3.44; la sexta, `kqlxv`, no dejó registro de costo). Goliath
cuesta $1.13 por 1,000 frases con la tarifa de hoy y $2.26 con la de 2027. Servir a David en la nube cuesta lo
que está encendida su GPU, ~$1.05 por hora (sección 7).

## Qué haríamos después

- **Más datos reales de Guatemala.** Con la ronda 3, David gana el nicho chapín en jerga correcta, pero en
  jerga resuelta sigue en empate, y la web tiene menos de Guatemala que de los demás países.
- **El español neutro (LATAM).** Es donde Goliath con el mismo glosario le gana a David (55 % contra 32 %
  de jerga correcta): faltan pares reales sin país.
- **Selección con el glosario.** Generar varias respuestas y quedarse con la que contiene más
  contrapartes esperadas del banco, sin pasarse de 1 s: en dev, con 4 respuestas, la jerga resuelta de 10c subió de 86 % a 94 %, pero
  el p50 llegó a 4.40 s.
- Ya hecho en la ronda 3: el set de desarrollo propio (las decisiones de datos ya no miran el set de prueba)
  y los pares con varios términos a la vez (no ayudaron: quedaron fuera).

## 6 · La demo pasa a ser la página de comparación (2026-10-06)

La demo de la charla dejó las rondas, el marcador, los votos del público y la tecla `M`. Ahora es una sola
página donde David y Goliath traducen la misma frase lado a lado con su tiempo y su costo. Los
ejemplos son jerga chapina del set de prueba: se probaron en vivo las 51 frases chapinas cortas que la revisión
término por término puede juzgar, 3 veces con cada modelo, y quedaron 4, las que David tradujo bien y Goliath
mal las 3 veces. Se descartaron las frases donde Goliath acertó alguna vez o dijo algo razonable con otras
palabras («échale un ojo» por «chotea», «qué tufo» por «chish», «emocionado» por «engasado»): la revisión las
marcaba mal y la página habría dicho algo falso. La vista del presentador y la app del público quedaron sin uso (se
quitaron el mismo día, sección 7).

## 7 · Todo pasa a la nube (2026-10-06)

David dejó la laptop. Ahora corre con Ollama en un servicio privado de Cloud Run con una GPU L4 en
`europe-west4`, con el modelo y EmbeddingGemma dentro de la imagen, y escala a cero cuando nadie lo usa. La
página de comparación también está en Cloud Run, pública, y es lo único que se abre el día de la charla: al
abrirse despierta a David y lo mantiene encendido mientras sigue abierta. El eval pasó a un Cloud Run Job con
una L4 que carga cada modelo desde el bucket de uno en uno. En la laptop no queda ningún modelo.

- **Tiempo:** con la GPU encendida, David responde en ~0.5 s a través de la página (en la Mac eran 670 ms de
  p50); Goliath tardó entre 0.8 y 18.6 s ese día. Encender la GPU desde cero, cargar el modelo y calentarlo tarda unos
  cuatro minutos.
- **Los ejemplos:** los 4 se volvieron a probar 3 veces cada uno contra el David de la nube: 12 de 12 aciertos
  de David, 0 de Goliath. En una prueba a temperatura 0.2 David dijo «muy regular» en vez de «muy mala» (mal); la página pasó a temperatura 0, como el eval, y con eso da siempre la misma respuesta: 12 de 12 bien.
- **Costo:** en la nube David ya no es gratis. La GPU cuesta ~$1.05 por hora encendida, y con el uso de una
  charla eso es más que lo que cobra Gemini por las mismas frases. La página dejó de mostrar el costo y muestra
  solo el tiempo.
- **Lo que se quitó:** la app del público (QR, frases y votos; servicio de Cloud Run, código, cuenta de
  servicio, app web de Firebase y su llave de reCAPTCHA), la vista del presentador con rondas y marcador, el
  modo sin internet, `make up`, `make stage-on/off`, `make warmup`, `make preflight`, `make reset`,
  `make pull-model`, `make train-local`, `make train-finish` y `make quant-sweep`. Todo sigue en el historial
  de git.

