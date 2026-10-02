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

## Enmienda 1 · métricas nuevas (registrada el 2026-10-02 10:50, antes de calcularlas)

Se agregan tres medidas. Ninguna se ha calculado sobre el set de prueba ni sobre los nichos al escribir esto;
las métricas viejas (jerga resuelta, cambios acertados, chrF++) se siguen reportando igual. Las definiciones
dependen de la tabla de contrapartes validadas por significado (`data/counterparts.jsonl`, construida
sin mirar el set de prueba) y del banco congelado `data/eval/terms_test.jsonl`.

### Jerga correcta

Jerga resuelta mide que cambió el registro; jerga correcta mide que el término producido **significa lo
mismo**.

- **Papás → Gen Z:** correcta si la salida contiene al menos un término Gen Z del banco (del país o LATAM)
  que es el mismo término Gen Z de la referencia, o que está enlazado en la tabla de contrapartes con un
  término de papás de la frase original o con un término Gen Z de la referencia.
- **Gen Z → papás:** correcta si no queda ningún término Gen Z de la frase original y, para cada uno de
  ellos, la salida contiene su contraparte validada **o** al menos una palabra de contenido de su
  significado en el banco (comparación por raíz de 5 letras, sin acentos).
- Frases no juzgables (sin término del banco donde hace falta, o sin contraparte ni significado): fuera.

### Cambios acertados con sinónimos

Igual que «cambios acertados», pero una palabra que la referencia cambió cuenta como acertada si la salida
tiene la misma palabra, otra con la misma raíz de 5 letras, o un término del banco enlazado a ella en la
tabla de contrapartes.

### Nicho 3 · términos nuevos para Goliath

- **Frases:** pares del set de prueba (`auto_validated` o `approved`) cuyo término de jerga tiene su primera
  fecha de publicación registrada (en `SOURCES.md` o en el término) **posterior** al corte de conocimiento
  publicado para `GEMINI_MODEL` en su ficha del modelo. El corte y la fuente se anotan aquí al calcular el
  nicho por primera vez, sin cambiar la regla.
- Si califican menos de 30 frases, el nicho se reporta como «n insuficiente», sin veredicto.

### Regla de victoria

La misma: IC 95 % por bootstrap pareado (10,000 remuestreos, semilla 2027) de la diferencia David − Goliath;
gana David si el límite inferior es mayor que 0. Para jerga correcta y nicho 3 el rival también es Goliath
como en escena, y Goliath + glosario se reporta al lado.

### Set de desarrollo

Las decisiones de las rondas de datos se toman en `data/pairs/dev_real.jsonl` (20 % de los pares reales de
entrenamiento, por hash estable de la oración, más oraciones nuevas de investigación separadas igual),
nunca en el set de prueba ni en los nichos. El set de prueba se evalúa una sola vez al final de cada ronda.
