# Nichos pre-registrados

> Los nichos se numeraban (1, 2, 3) cuando se registraron; el 2026-10-02 se les dio nombre descriptivo.
> Solo cambió el nombre: las definiciones de abajo son las registradas.

Escrito el 2026-10-02 **antes** de calcular cualquier corte por nicho de David contra Goliath. La definición
no cambia después de ver resultados; si un nicho sale mal, se reporta tal cual (`docs/BITACORA.md`).

Transparencia: reportes anteriores (`evals/report.md`) ya traían una tabla de chrF++ por país solo de los
Davids, sin Goliath y sin jerga resuelta. Los nichos no salen de esa tabla: el primero es la sugerencia de
la presentadora (la charla es en Guatemala y es donde Gemini tiene menos datos) y el segundo es la
dirección que los datos reales vinieron a reforzar.

## «Slang chapín»

- **Frases:** pares del set de prueba con `country = GT` y `status` en (`auto_validated`, `approved`).
- **Cómo se evalúan:** con `country = GT` en el prompt de los dos (el país del par), como en escena.
- **Dirección:** las dos.

## «Papás → Gen Z (GT/CO)»

- **Frases:** pares del set de prueba con `direction = parent_to_genz`, `country` en (`GT`, `CO`) y
  `status` en (`auto_validated`, `approved`).
- **Por qué:** es la dirección difícil (producir jerga real, no quitarla) y la que los pares anclados en
  oraciones reales de GT y CO buscan enseñar.

## Quién compite

- **David:** el David de la página (`DAVID_MODEL_TAG`; se llamaba `LOCAL_MODEL_TAG` cuando se registró este nicho), con el prompt con que se entrenó (`país + glosario`).
- **Goliath:** `GEMINI_MODEL` como en escena (`GOLIATH_PROMPT_STYLE = country`, sin glosario). Es el rival del nicho.
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

### «Slang reciente»: términos nuevos para Goliath

- **Frases:** pares del set de prueba (`auto_validated` o `approved`) cuyo término de jerga tiene su primera
  fecha de publicación registrada (en `SOURCES.md` o en el término) **posterior** al corte de conocimiento
  publicado para `GEMINI_MODEL` en su ficha del modelo. El corte y la fuente se anotan aquí al calcular el
  nicho por primera vez, sin cambiar la regla.
- Si califican menos de 30 frases, el nicho se reporta como «n insuficiente», sin veredicto.
- **Resultado (2026-10-02):** ni `SOURCES.md` ni el banco registran la primera fecha de publicación de los
  términos (solo la fecha de consulta), así que califican 0 frases: n insuficiente. El nicho se deja de reportar.

### Regla de victoria

La misma: IC 95 % por bootstrap pareado (10,000 remuestreos, semilla 2027) de la diferencia David − Goliath;
gana David si el límite inferior es mayor que 0. Para jerga correcta y «slang reciente» el rival también es Goliath
como en escena, y Goliath + glosario se reporta al lado.

### Set de desarrollo

Las decisiones de las rondas de datos se toman en `data/pairs/dev_real.jsonl` (20 % de los pares reales de
entrenamiento, por hash estable de la oración, más oraciones nuevas de investigación separadas igual),
nunca en el set de prueba ni en los nichos. El set de prueba se evalúa una sola vez al final de cada ronda.

## Enmienda 2 · «Combinaciones» (registrada el 2026-10-07 10:55 CST, antes de calcularla)

Escrita antes de buscar las oraciones nuevas, antes de entrenar la ronda 5 y antes de calcular ningún corte por
número de términos (de ningún modelo, en ningún set). La definición no cambia después de ver resultados.

**Hipótesis.** El modelo grande conoce muchos términos sueltos y algunas frases hechas, pero en una frase que junta
varios términos de jerga del mismo país (p. ej. «no manches güey, el profe está bien mamón y la tarea está cañona»)
el modelo pequeño, entrenado con los datos de ese país, puede ganar.

### Frases

- **Regla de la combinación:** el lado Gen Z del par (la fuente en Gen Z → papás; la referencia en papás → Gen Z)
  contiene **al menos 2 términos Gen Z distintos** del banco congelado (`data/eval/terms_test.jsonl`, sin los
  marcados `ambiguous`) del país del par o de LATAM. Dos términos cuentan como uno si una forma de uno está
  contenida en una forma del otro («chido» y «bien chido»).
- **Solo oraciones reales** (`origin = web`), nunca sintéticas: una referencia escrita por Gemini sesga hacia Goliath.
- **De dónde salen**, en un archivo aparte (`data/eval/combos.jsonl`, `make eval-combos`):
  1. los pares del set de prueba congelado (`pairs/test_web.jsonl`, `auto_validated`) que cumplen la regla;
  2. oraciones reales nuevas de la ronda 5 de investigación (`raw/web_usage_2026-10-07.jsonl`) que cumplen la
     regla y que un hash estable del id (`sha1("combos|" + id)`, la mitad) aparta para este nicho **antes** de
     correr ningún modelo sobre ellas. Cada oración entra en las dos direcciones, como en la sonda: la oración
     real → la versión de papás del curador, y la versión del curador → la oración real.
- **Validación automática**, la misma del set de prueba (`scripts/validate_test_set.py: check`, con el banco
  congelado): largo, sin jerga de otro país en la referencia, la fuente Gen Z con su jerga y la referencia sin
  ella, y **sin solapamiento** (también como subcadena) con ningún archivo de entrenamiento ni de desarrollo,
  incluidos `synthetic_genz`, `synthetic_multi` y los de la ronda 5.
- Ninguna oración se elige ni se descarta mirando la salida de un modelo.

### Quién compite y cómo

- **David:** el ganador de la ronda 5 elegido en desarrollo (abajo), con su prompt de entrenamiento (país +
  léxico). Al lado, el David de la página antes de la ronda (`genlingo-2026-10d-e2b`).
- **Goliath:** `GEMINI_MODEL` como en la página (país, sin glosario): es el rival. Goliath con el mismo glosario se
  reporta al lado y no decide.
- El país del prompt es el del par.

### Métrica y regla de victoria

- **Jerga correcta** (`evals/term_accuracy.py: correct_slang`) en la versión vigente el día del eval final:
  incluye la corrección que se está haciendo en paralelo (Gen Z → papás solo es correcta si la salida no deja
  ninguna jerga, ni otra; papás → Gen Z solo con jerga del país del par). Al lado: jerga resuelta y chrF++.
- IC 95 % por bootstrap pareado de la diferencia David − Goliath (10,000 remuestreos por frase, semilla 2027).
  Gana David si el límite inferior es mayor que 0; empate si el intervalo cruza el 0; gana Goliath si el
  superior es menor que 0.
- **Cortes con veredicto** (si n ≥ 30): todo el nicho; por país (MX, CO, LATAM, GT); por dirección. País ×
  dirección se reporta siempre, con veredicto solo si n ≥ 30 (si no, «n insuficiente»).

### Cómo se elige el David de la ronda 5 (en desarrollo, nunca en prueba)

- Desarrollo: `pairs/dev_real.jsonl` (20 % de las oraciones reales de entrenamiento por hash estable, más el 20 % de
  las oraciones de la ronda 5 que no fueron al nicho). «Combinaciones en desarrollo» = los pares de dev que
  cumplen la misma regla.
- Gana la variante con más jerga correcta en combinaciones de desarrollo, siempre que en todo el desarrollo no
  baje más de 2 puntos de jerga correcta contra `genlingo-2026-10d-e2b` y su p50 quede bajo 1 s. Empate (≤ 1
  punto): la de más jerga correcta en todo el desarrollo.
- El nicho, el set de prueba y la sonda se corren una sola vez, con el ganador ya elegido.

**Aclaración (2026-10-07 11:45 CST, antes de calcular nada).** De la parte 2 (oraciones nuevas) quedan fuera, y
van solo a entrenamiento, las oraciones de páginas cuyos ejemplos escriben los editores de un sitio para muchos
países a la vez con la misma plantilla (p. ej. el «Castellanario» de magikitos.com, de España, con el mismo
editor para Guatemala, Colombia y México): no son habla real de jóvenes de ese país, y pueden estar generadas.
Esa marca se pone por fuente (`kind: "editorial example"` en `raw/web_usage_2026-10-07.jsonl`) antes de correr
ningún modelo y no depende de lo que diga ninguna salida.
