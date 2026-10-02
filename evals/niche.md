# Nichos pre-registrados

Escrito el 2026-10-02 **antes** de calcular cualquier corte por nicho de David contra Goliath. La definición
no cambia después de ver resultados; si un nicho sale mal, se reporta tal cual (`docs/BITACORA.md`).

Transparencia: reportes anteriores (`evals/report.md`) ya traían una tabla de chrF++ por país solo de los
Davids, sin Goliath y sin jerga resuelta. Los nichos no salen de esa tabla: el primero es la sugerencia de
la presentadora (la charla es en Guatemala y es donde Gemini tiene menos datos) y el segundo es la
dirección que los datos reales vinieron a reforzar.

## Nicho 1 · «Slang chapín»

- **Frases:** pares del set de prueba con `country = GT` y `status` en (`auto_validated`, `approved`).
- **Cómo se evalúan:** con `country = GT` en el prompt de los dos (el país del par), como en escena.
- **Dirección:** las dos.

## Nicho 2 · «Papás → Gen Z en Guatemala y Colombia»

- **Frases:** pares del set de prueba con `direction = parent_to_genz`, `country` en (`GT`, `CO`) y
  `status` en (`auto_validated`, `approved`).
- **Por qué:** es la dirección difícil (producir jerga real, no quitarla) y la que los pares anclados en
  oraciones reales de GT y CO buscan enseñar.

## Quién compite

- **David:** el David de escena (`LOCAL_MODEL_TAG`), con el prompt con que se entrenó (`v2 + glosario`).
- **Goliath:** `GEMINI_MODEL` como en escena (`GOLIATH_PROMPT_STYLE = v2`, sin glosario). Es el rival del nicho.
- **Goliath + el mismo glosario:** se reporta siempre al lado, para separar modelo de datos, pero no
  decide el nicho.

## Métricas

- **Jerga resuelta** (métrica principal, `evals/term_accuracy.py`), chrF++ de corpus y p50.
- **Tasa de victorias:** frases donde David resuelve la jerga y Goliath no, sobre las frases donde
  exactamente uno de los dos la resuelve.
- **Intervalo de confianza:** bootstrap pareado de la diferencia de jerga resuelta (David − Goliath),
  10,000 remuestreos por frase con semilla 2027, percentiles 2.5 y 97.5.

## Regla de victoria

David **gana** un nicho si el límite inferior del IC 95 % de la diferencia es mayor que 0. Si el
intervalo cruza el 0 es empate estadístico; si el límite superior es menor que 0, gana Goliath.
También se reportan todos los países y el set completo, con la misma tabla.

## Lo que nunca entra al nicho

Pares sintéticos (el set de prueba solo tiene `origin = web`), pares de entrenamiento y pares de
desarrollo. Las rondas de mejora con datos se deciden con un set de desarrollo aparte, nunca mirando el
nicho ni el set de prueba.
