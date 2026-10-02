# Bitácora de David

La historia de David, iteración por iteración: qué cambió, por qué, qué salió, cuánto costó y cuándo.
Incluye los callejones sin salida, porque explican las decisiones que quedaron.

Los números de jerga resuelta son todos del **mismo set de prueba** (399 frases web `auto_validated`,
eval del 2026-10-02), así que se pueden comparar entre sí. Las corridas viejas se reevaluaron sobre ese
set; los números de su momento (sobre sets anteriores) están en el historial de `evals/report.md`.

![Jerga resuelta por iteración](diagrams/bitacora-jerga.svg)

## Resumen

| Fecha | Iteración | Qué cambió | Jerga resuelta | Costo |
| --- | --- | --- | --- | --- |
| 2026-09-30 | Base sin afinar | Gemma 4 E2B tal cual | 58 % | $0 |
| 2026-09-30 | `pairs-v1` (descartado) | Paráfrasis libres generadas por Gemini | chrF++ 39.1, por debajo de la base | $0 (laptop) |
| 2026-10-01 | `genlingo-2026-09` | Pares de edición mínima (`pairs-v2`) | 62 % | $0.41 |
| 2026-10-01 | `genlingo-2026-10-e2b` | Pares anclados en el banco (`pairs-v3`) + prompt con glosario | 67 % (Q4) | $0.67 |
| 2026-10-01 | `genlingo-2026-10-e4b` (descartado) | Base más grande, E4B | 67 %, p50 836 ms | $0.98 |
| 2026-10-01 | Barrido de cuantización | Q5_K_M en vez de Q4_K_M | 74 % | $0 (laptop) |
| 2026-10-02 | `genlingo-2026-10b-e2b` | Oraciones reales + banco de 406 términos | **82 %** | $0.71 |
| | Goliath (referencia) | `gemini-3.8-flash`, sin glosario | 78 % | $1.08 / 1,000 frases |
| | Goliath + el mismo glosario | El banco de David en el prompt de Gemini | 82 % | $1.24 / 1,000 frases |

## 1 · Paráfrasis libres (`pairs-v1`): el primer callejón sin salida

- **Qué:** 1,000 pares sintéticos donde Gemini reescribía la frase entera «como lo diría la otra
  generación». LoRA en la Mac (MPS), 36.9 min.
- **Resultado:** chrF++ **39.1**, por debajo de la base sin afinar (47.1) y de copiar la frase (50.0).
  David aprendió a parafrasear todo, no a cambiar la jerga.
- **Lección:** una reescritura de registro cambia pocas palabras. Si el dato cambia todo, el modelo
  cambia todo. Detalle en [evals/experiments/2026-09-pairs-v1.md](../evals/experiments/2026-09-pairs-v1.md).

## 2 · Pares de edición mínima (`genlingo-2026-09`)

- **Qué:** `pairs-v2`, la misma frase con solo los términos de jerga cambiados. Primer entrenamiento en
  la nube (Cloud Run Job con una L4), 17.4 min.
- **Resultado:** **62 %** de jerga resuelta, chrF++ 55.0. Arriba de la base (58 %), pero casi todo el
  avance está en Gen Z → papás; en papás → Gen Z resuelve solo el 20 %.
- **Costo:** $0.41. Antes hubo tres corridas fallidas que también se pagaron: sin `gcc` para Triton
  ($0.26), y dos donde el GGUF se escribía en el bucket montado a ~3 MB/s ($0.74 y una sin registro).

## 3 · Pares anclados en el banco + glosario (`genlingo-2026-10-e2b`)

- **Qué:** `pairs-v3`. Cada par nombra un término del banco y su contraparte de la otra generación del
  mismo país, con trampas de otro país como negativos difíciles; 60 % papás → Gen Z. El prompt empieza
  por el país y lleva un glosario de cuatro entradas recuperadas con EmbeddingGemma. David se entrena con
  ese mismo prompt.
- **Resultado:** **67 %** en Q4_K_M; papás → Gen Z sube de 20 % a 31 %.
- **Costo:** $0.67 (28.2 min). Generar los 1,500 pares con Gemini costó $0.80.

## 4 · Un modelo más grande no era la respuesta (E4B)

- **Qué:** la misma receta sobre Gemma 4 E4B.
- **Resultado:** **67 %**, igual que E2B, con p50 de 836 ms (al límite del segundo) y 5.3 GB. Fusionarlo
  no cupo en los 32 GiB del job; terminó en la laptop con `make train-finish`.
- **Costo:** $0.98. Quedó fuera de escena: más modelo no compró más jerga.

## 5 · Q4 perdía jerga: barrido de cuantización

- **Qué:** el mismo David 2026-10 exportado en Q4_K_M, Q5_K_M, Q6_K, Q8_0 y Q4/Q5 calibrados con imatrix.
- **Resultado:** Q4_K_M perdía **7 puntos** contra f16 (67 % contra 74 %). Q5_K_M (3.62 GB) queda a la
  par del f16 (9.27 GB) con la misma latencia. Regla desde entonces: el archivo más pequeño a ≤ 2 puntos
  del f16, con p50 < 1 s.
- **Costo:** $0, todo en la laptop.

## 6 · Oraciones reales (`genlingo-2026-10b-e2b`)

- **Qué:** una segunda ronda de investigación web (22 fuentes nuevas, 146 términos, 420 oraciones reales).
  La mitad de las oraciones fue al set de prueba; la otra mitad se convirtió en 334 pares de entrenamiento
  anclados en la oración real, en las dos direcciones. El banco creció a 406 términos y los sintéticos se
  refiltraron contra él (1,375).
- **Resultado:** **82 %**, +8 puntos sobre el David anterior en la misma compresión, casi todo en
  papás → Gen Z (43 % → 59 %). Supera a Goliath sin glosario (78 %) y empata con Goliath + glosario (82 %).
- **Tropiezo:** el job único (entrenar + fusionar + GGUF) murió por memoria al convertir a f16 (`zct96`,
  $0.63): en Cloud Run el disco vive en la memoria. Se dividió en dos jobs (L4 entrena, CPU fusiona y
  cuantiza), y la primera corrida de punta a punta costó **$0.71**.
- **Nombre:** se entrenó como `genlingo-2026-11-e2b` y se renombró: los tags llevan la fecha de los datos
  (segunda versión de octubre), no la del entrenamiento.

## 7 · Limpieza del set de prueba

- **Qué:** la revisión encontró dos frases de prueba citadas dentro de pares de entrenamiento más largos.
  La validación ahora compara subcadenas, crudas y normalizadas, contra todos los archivos de entrenamiento.
- **Resultado:** 4 pares de prueba fuera (403 → 399). Se quitaron del set de prueba, no del entrenamiento,
  porque David ya estaba entrenado. Todos los números de esta bitácora son del set limpio.

## Dónde gana David hoy, y dónde no

Nichos definidos antes de mirar resultados ([evals/niche.md](../evals/niche.md)); IC 95 % por bootstrap
pareado ([evals/niche_report.md](../evals/niche_report.md)).

| Nicho | n | David | Goliath | Δ | IC 95 % | Veredicto |
| --- | --- | --- | --- | --- | --- | --- |
| 1 · Slang chapín (GT) | 115 | 78 % | 70 % | +7.8 | [+0.0, +15.7] | empate estadístico |
| 2 · Papás → Gen Z en GT y CO | 106 | 65 % | 49 % | +16.0 | [+3.8, +28.3] | **gana David** |
| Todo el set | 398 | 82 % | 78 % | +3.8 | [−0.5, +8.0] | empate estadístico |

- **Gana** en papás → Gen Z para Guatemala y Colombia: es justo lo que enseñan los pares reales.
- **En Guatemala** el límite inferior queda exactamente en 0: no alcanza para declarar victoria, aunque
  resuelve la jerga donde Goliath no en 16 frases contra 7 (chrF++ 61.2 contra 51.4).
- **Pierde o empata** contra Goliath con el mismo glosario en todos los cortes, y Goliath acierta más
  palabras de la referencia (30 % contra 22 %). Con los mismos datos, el modelo grande alcanza al pequeño:
  la ventaja de David son sus datos.

## Costo de reentrenar cada mes

Un reentrenamiento de E2B, de punta a punta en la nube, cuesta **$0.71** (25 min de L4 + 9 min de CPU).
En total, las corridas con registro costaron $4.40, incluidas tres de las cuatro fallidas ($1.63; la cuarta, `kqlxv`, no dejó registro). La
inferencia de David cuesta $0; Goliath, $1.08 por 1,000 frases con la tarifa de hoy y $2.17 con la de 2027.

## Qué haríamos después

- **Más datos reales de Guatemala.** Es el nicho que todavía empata, y donde la web tiene menos.
- **Pares con varios términos a la vez.** David cambia menos palabras de la referencia que Goliath (22 %
  contra 30 %); los pares de un solo término le enseñan a cambiar uno.
- **Selección con el glosario.** Generar varias respuestas y quedarse con la que contiene más
  contrapartes esperadas del banco, sin pasarse de 1 s.
- **Un set de desarrollo propio**, para que las decisiones de datos nunca miren el set de prueba.
