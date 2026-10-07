# Genlingo — traductor generacional: Gen Z ↔ papás

Demo de la charla *«David vs. Goliath: cómo un modelo pequeño le gana a un modelo frontier»*. «no manches, la peli estuvo bien chilera pero el final me dio cringe» ↔ «la película estuvo bien chévere pero el final me dio pena ajena». **David** es Gemma 4 E2B afinado con LoRA sobre pares propios y corre con Ollama en un servidor con GPU (Cloud Run, NVIDIA L4) que es solo suyo. **Goliath** es Gemini (`GEMINI_MODEL`, hoy `gemini-3.8-flash`) en Vertex AI. Todo corre en la nube: la laptop solo abre una página.

[English version](README.en.md)

## La demo: David y Goliath lado a lado

Una sola página pública en Cloud Run: **https://genlingo-611681112050.us-central1.run.app**. No hay nada que instalar ni que ejecutar el día de la charla: se abre la página unos minutos antes y listo.

- Se elige la dirección (Gen Z → papás o papás → Gen Z), se escribe una frase o se toca un ejemplo, y los dos traducen la misma frase al mismo tiempo. Cada columna muestra su traducción, cuánto tardó y cuánto costó ([cómo se calcula y cuándo conviene cada uno](#tiempo-y-costo-en-la-nube)).
- Debajo de cada columna, cada palabra de jerga de la frase con ✓ (la tradujo con su significado) o ✗, según nuestro banco de jerga. En los ejemplos, además, la traducción de referencia hecha por personas. Si una frase escrita no tiene jerga que el banco conozca, la página lo dice en vez de calificar.
- Al final, «¿Cómo se lee esta página?» explica en palabras simples qué es ✓/✗, el tiempo y el costo. La página se ve bien en el proyector, en una laptop y en el teléfono.
- David se apaga solo cuando nadie lo usa, para no cobrar entre charlas. Al abrir la página, arriba a la derecha dice «Preparando a David…» con un reloj mientras se enciende su GPU; tarda unos 35 segundos desde cero ([medido](docs/DECISIONES.md#david-en-la-nube); antes eran casi 4 minutos). Cuando dice «David listo», todo responde al instante, y la página lo mantiene encendido mientras esté abierta.

![La página de comparación: David y Goliath traducen «esa tu tarea te quedó bien chafa»](docs/demo/02-comparar-genz-a-papas.png)

Los tres ejemplos son jerga chapina del set de prueba (David nunca los vio al entrenar), de fuentes con licencia abierta. Se probaron en vivo, 3 veces con cada modelo, contra el David de la nube: David acertó las 9 veces y Goliath ninguna. Fuera de Guatemala también se probaron las 38 frases de fuentes abiertas de México, Colombia y español neutro, y ninguna pasó todas las pruebas ([por qué](#y-la-jerga-gen-z-que-no-es-chapina)). Cada ejemplo, con su fuente, su licencia y las respuestas de cada prueba, está en [`data/translate_examples.json`](data/translate_examples.json). El guion está en [docs/DEMO.md](docs/DEMO.md).

![Qué corre dónde: la página, David y Goliath en la nube](docs/diagrams/arquitectura.png)

## Qué vas a aprender

1. **Datos propios con `origin`:** cada par dice de dónde salió (`web`, `synthetic` o `human`); sin eso no se puede evaluar ni reentrenar cada mes.
2. **Banco de términos y oraciones reales:** 532 términos de 92 fuentes, contrapartes validadas por significado y 565 pares anclados en oraciones reales; la ventaja de David son sus datos. Las oraciones de fuentes que no se pueden redistribuir viven en un bucket privado, no en el repo ([data/SOURCES.md](data/SOURCES.md)).
3. **LoRA en Cloud Run Jobs:** una L4 entrena y un job de CPU fusiona y exporta GGUF; cada ejecución registra su duración y costo.
4. **El costo de comprimir:** f16 contra Q4_K_M, Q5_K_M, Q6_K, Q8_0 e imatrix, en tamaño, latencia y jerga perdida.
5. **Evals con métricas de término:** chrF++ más *jerga correcta*, *jerga resuelta* y *cambios acertados*, con un set de desarrollo aparte para decidir y nichos definidos antes de mirar resultados.
6. **Tu modelo en tu propia GPU:** David corre con Ollama en Cloud Run con una L4, privado, y escala a cero entre charlas; la página lo despierta al abrirse. Entrenar, evaluar y servir: todo en la nube, nada en la laptop.

## Las métricas, en palabras simples

Ningún modelo califica a otro: todas las métricas las calcula un programa con reglas fijas.

- **Jerga correcta** (la principal, y la que la página muestra con ✓ Bien y ✗ Mal): por cada palabra de jerga de la frase, ¿la traducción la cambió por algo que significa lo mismo? El programa usa nuestro banco de jerga (532 términos, cada uno con su significado, su país y su fuente) y una tabla de equivalencias validada por significado (`data/counterparts.jsonl`).
  *Ejemplo:* «esa tu tarea te quedó bien **chafa**» (chafa = de mala calidad). «Esa tarea tuya te quedó muy mala» → ✓. «Esa tu tarea te quedó bien pura lata» → ✗: cambió una jerga por otra que no dice lo mismo.
- **Jerga resuelta:** ¿cambió el registro? En Gen Z → papás, que no quede jerga Gen Z del banco; en papás → Gen Z, que la traducción use al menos una jerga Gen Z del país. No mira si el significado es el correcto, por eso no es la principal.
- **Cambios acertados:** de las palabras que la persona cambió al traducir, cuántas aparecen igual en la traducción del modelo.
- **chrF++:** qué tanto se parece la traducción a la que escribió una persona, contando los pedazos de letras y de palabras que tienen en común: 0 es nada en común y 100 es idéntica.
  *Ejemplo:* si la persona escribió «esa tarea te quedó muy mal hecha», «esa tarea tuya te quedó muy mala» comparte casi todo y saca un número alto; «te quedó pura lata» comparte poco y saca uno bajo. En esta tarea casi todas las palabras se quedan iguales, así que copiar la frase sin traducir ya saca 53.2: por eso chrF++ no decide solo.

Los números del set de prueba son del eval del 2026-10-07 sobre 399 frases web `auto_validated` que David nunca vio, corrido en la nube (Cloud Run con una L4, la misma GPU que la página; [evals/report.md](evals/report.md)), salvo donde se indica otra fecha. El tiempo y el costo de la página están medidos aparte ([Tiempo y costo en la nube](#tiempo-y-costo-en-la-nube)).

## Resultado final

| | Jerga correcta | Jerga resuelta | chrF++ | p50 (eval) |
| --- | ---: | ---: | ---: | ---: |
| **David** (`genlingo-2026-10d-e2b`, Q5_K_M, 3.62 GB) | **44 %** | **80 %** | **60.0** | **237 ms** |
| Goliath `gemini-3.8-flash` | 24 % | 77 % | 53.7 | 3.06 s |
| Goliath con el léxico de David (referencia) | 41 % | 83 % | 56.4 | 3.20 s |
| Copiar la frase (línea base) | 1 % | 1 % | 53.2 | — |

- **Jerga correcta:** +19.5 puntos sobre Goliath (IC 95 % [+13.5, +25.6]). 120 frases las acierta solo David y 42 solo Goliath.
- **Jerga resuelta:** +3.3 [−1.3, +7.8], empate estadístico.
- **chrF++:** 60.0 contra 53.7 de Goliath y 56.4 de Goliath con el léxico.
- **Costo de Goliath:** $1.14 por 1,000 frases en ese eval; con la tarifa desde el 2027-01-01 serían $2.28.

### Por nicho (jerga correcta, David contra Goliath sin glosario)

Nichos definidos antes de mirar resultados ([evals/niche.md](evals/niche.md)); IC 95 % por bootstrap pareado ([evals/niche_report.md](evals/niche_report.md)).

| Nicho | n | David | Goliath | Δ | IC 95 % | Veredicto |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Slang chapín (GT) | 115 | 50 % | 20 % | +30.4 | [+19.1, +41.7] | gana David |
| Papás → Gen Z (GT/CO) | 107 | 33 % | 20 % | +13.1 | [+1.9, +25.2] | gana David |
| País CO | 131 | 37 % | 18 % | +19.1 | [+8.4, +29.8] | gana David |
| País MX | 78 | 46 % | 33 % | +12.8 | [−1.3, +26.9] | empate estadístico |
| País LATAM (español neutro) | 75 | 43 % | 32 % | +10.7 | [−1.3, +22.7] | empate estadístico |
| Todo el set | 399 | 44 % | 24 % | +19.5 | [+13.5, +25.6] | gana David |

Por país y dirección (no pre-registrado; mismo bootstrap): David gana de Gen Z a papás en México (51 % contra 22 %) y en Colombia (43 % contra 15 %); en español neutro de Gen Z a papás queda 50 % contra 36 %, en el borde del empate. De papás a Gen Z fuera de Guatemala es empate en los tres.

- **Contra Goliath con el mismo léxico:** David gana en slang chapín (+13.9 [+3.5, +24.3]); empata en el set completo (+2.5), en papás → Gen Z y en Colombia; en México (46 % contra 58 %) y en español neutro (43 % contra 51 %) Goliath queda arriba sin que la diferencia sea significativa.

### ¿Y la jerga Gen Z que no es chapina?

La primera versión del banco y de las oraciones reales venía casi toda de Guatemala y Colombia (268 y 255 de 556 pares reales; México 9, español neutro 24), y la página traduce siempre con la jerga de Guatemala. Por eso con «cringe», «random» o «crush» David respondía a la chapina. Se midió y se trabajó en dos frentes:

- **Una sonda aparte** ([evals/report_probe.md](evals/report_probe.md), `make eval-probe`): 32 oraciones reales de jerga Gen Z general (cringe, random, crush, stalkear, funar, ghostear, shippear, mid, mood, delulu, basado, rizz, slay, red flag, prime…) sacadas de 14 páginas que nunca se usan para entrenar, en las dos direcciones.

  | | Como español neutro | Como Guatemala |
  | --- | ---: | ---: |
  | David antes (`10c`) | 91 % | 69 % |
  | **David hoy (`10d`)** | **91 %** | **77 %** |
  | Goliath | 94 % | 77 % |

- **La ronda 4 de datos:** 1,600 pares para entrenar anclados en jerga Gen Z de México y del español neutro, más 17 oraciones reales; `10d` ganó en desarrollo (46 % contra 40 % de jerga correcta) y es el David de la página.

**Respuesta corta:** David sí traduce jerga Gen Z general (91 % en la sonda), pero ahí no le gana a Goliath: empatan. Donde gana es con jerga de un país que el modelo grande conoce poco: Guatemala, Colombia y, de Gen Z a papás, México. Por eso los ejemplos de la página son chapines.

### chrF++ por país y por dirección

| | CO | GT | LATAM | MX | Gen Z → papás | Papás → Gen Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| David | 60.9 | 66.1 | 56.1 | 53.6 | 68.3 | 48.6 |
| Goliath | 52.9 | 53.0 | 59.7 | 49.7 | 61.4 | 43.1 |
| Goliath + léxico | 54.0 | 59.8 | 60.1 | 52.2 | 62.7 | 47.7 |

## Tiempo y costo en la nube

<!-- projections: make projections -->
Medido el 2026-10-07 con `make capacity` ([`scripts/bench_capacity.py`](scripts/bench_capacity.py) → [`docs/data/capacity.json`](docs/data/capacity.json)): 48 frases del set de prueba, con el mismo código de la página, contra el David de Cloud Run (1 NVIDIA L4) y contra Gemini. Las tablas las escribe `make projections` a partir de ese archivo.

**Tiempo por traducción** (de que se pide a que llega la respuesta)

| | Mediana | p95 | Traducciones por hora |
| --- | ---: | ---: | ---: |
| David, 1 a la vez | 0.6 s | 0.8 s | 4,114 |
| David, 4 a la vez | 0.8 s | 1.1 s | 16,499 |
| David, 8 a la vez | 1.0 s | 1.3 s | 25,984 |
| David, 16 a la vez | 1.7 s | 2.3 s | 29,586 |
| Goliath (Gemini) | 3.2 s | 12.9 s | sin límite propio |

David es más rápido en todos los casos medidos: su mediana con 16 traducciones a la vez (1.7 s) sigue debajo de la de Goliath (3.2 s). De las 48 llamadas a Gemini, 2 fallaron por saturación de Vertex AI (429); la página reintenta sola.

**Costo.** La GPU de David se cobra por segundo mientras está encendida, haga lo que haga: R = L4 + 4 vCPU + 16 GiB ≈ **$1.05 por hora**. Gemini cobra por token: en la medición cada traducción usó en promedio 125 tokens de entrada y 298 de salida (incluye su razonamiento), o sea g ≈ **$0.0012** con la tarifa de hoy ($0.75 / $3.75 por millón) y **$0.0024** desde el 2027-01-01 ($1.50 / $7.50).

- David por traducción = R ÷ V, con V traducciones por hora. Una GPU aguanta hasta C = 29,586 por hora (lo mejor medido, 16 a la vez); con más, se suman GPUs: ⌈V ÷ C⌉ × R ÷ V.
- Goliath por traducción = g, igual a cualquier volumen.
- Equilibrio: V = R ÷ g. Al mes: 730 horas a ese volumen.

| Traducciones por hora | GPUs de David | David por traducción | Goliath por traducción (hoy) | Goliath (desde 2027-01-01) | David al mes | Goliath al mes (hoy) | Goliath al mes (desde 2027-01-01) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 1 | $0.021 | **$0.0012** | **$0.0024** | $764 | **$44.26** | $88.51 |
| 500 | 1 | $0.0021 | **$0.0012** | $0.0024 | $764 | **$443** | $885 |
| 1,000 | 1 | **$0.0010** | $0.0012 | $0.0024 | **$764** | $885 | $1,770 |
| 5,000 | 1 | **$0.00021** | $0.0012 | $0.0024 | **$764** | $4,426 | $8,851 |
| 20,000 | 1 | **$0.000052** | $0.0012 | $0.0024 | **$764** | $17,702 | $35,404 |
| 50,000 | 2 | **$0.000042** | $0.0012 | $0.0024 | **$1,528** | $44,256 | $88,509 |

**Dónde gana David:** desde unas **863 traducciones por hora** con la tarifa de hoy y **432** con la de 2027-01-01. Con su GPU llena, cada traducción cuesta **$0.000035**: 34 veces menos que Gemini hoy y 69 veces menos desde 2027-01-01. Un traductor que atiende a una organización todo el día está en esa zona.

**Dónde gana Goliath:** con poco volumen. En una charla (unas 50 frases en una hora) la GPU cuesta ~$1.05 por esa hora y Gemini ~$0.061 por las 50 frases. Por eso David se apaga solo entre charlas: así no cuesta nada mientras nadie lo usa.

En la página, el costo de David es el de los segundos de GPU que usó esa traducción (atendiendo una a la vez), y el de Goliath, lo que Gemini cobró por sus tokens.
<!-- /projections -->

## Todos los experimentos

### Todas las variantes en el set de prueba (399 frases, eval del 2026-10-07 en la nube)

| Variante | Jerga correcta | Jerga resuelta (Gen Z → papás / papás → Gen Z / total) | Cambios acertados | chrF++ | p50 | Tamaño | Entrenar |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| Base `gemma4:e2b-it-qat` | 14 % | 94 % / 10 % / 58 % | 14 % | 50.3 | 151 ms | 4.34 GB | — |
| Base E2B + léxico | 42 % | 98 % / 16 % / 62 % | 24 % | 54.9 | 213 ms | 4.34 GB | — |
| Base `gemma4:e4b` | 18 % | 98 % / 31 % / 69 % | 17 % | 48.2 | 224 ms | 6.58 GB | — |
| `genlingo-2026-09` (edición mínima, Q4_K_M) | 17 % | 93 % / 21 % / 62 % | 14 % | 54.9 | 157 ms | 3.42 GB | $0.41 |
| `genlingo-2026-10-e2b` + glosario (Q4_K_M) | 26 % | 96 % / 30 % / 67 % | 16 % | 55.7 | 196 ms | 3.42 GB | $0.67 |
| `genlingo-2026-10-e2b-q5_k_m` + glosario | 26 % | 97 % / 42 % / 73 % | 18 % | 55.4 | 212 ms | 3.62 GB | — |
| `genlingo-2026-10-e2b-f16` + glosario | 28 % | 98 % / 41 % / 73 % | 19 % | 56.2 | 358 ms | 9.27 GB | — |
| `genlingo-2026-10b-e2b` + glosario (Q5_K_M) | 33 % | 99 % / 57 % / 81 % | 22 % | 56.4 | 206 ms | 3.62 GB | $0.71 |
| `genlingo-2026-10c-e2b-nomulti` + léxico (Q5_K_M) | 41 % | 100 % / 59 % / 82 % | 28 % | 59.5 | 236 ms | 3.62 GB | $0.97 |
| `genlingo-2026-10c-e2b-nomulti-f16` + léxico | 43 % | 99 % / 58 % / 81 % | 28 % | 59.5 | 377 ms | 9.27 GB | — |
| **`genlingo-2026-10d-e2b` + léxico (Q5_K_M)** | 44 % | 100 % / 54 % / 80 % | 28 % | 60.0 | 237 ms | 3.62 GB | $1.49 |
| `genlingo-2026-10d-e2b-f16` + léxico | 43 % | 100 % / 62 % / 84 % | 28 % | 59.7 | 378 ms | 9.27 GB | — |
| Goliath `gemini-3.8-flash` | 24 % | 96 % / 51 % / 77 % | 25 % | 53.7 | 3.06 s | — | — |
| Goliath + léxico | 41 % | 99 % / 63 % / 83 % | 28 % | 56.4 | 3.20 s | — | — |
| Copiar la frase | 1 % | 0 % / 3 % / 1 % | 0 % | 53.2 | — | — | — |

Las latencias son de una L4 en la nube con Ollama (David responde una frase a la vez; Goliath cuatro a la vez). La versión del 2026-10-04, corrida en una Mac, está en el historial de `evals/report.md`.

### Ronda 3 en el set de desarrollo (146 pares, eval del 2026-10-04)

Las decisiones de datos de la ronda 3 se tomaron aquí, sin mirar el set de prueba ([evals/report_dev.md](evals/report_dev.md)). `10b` vio 70 de estos pares al entrenar, así que su número es optimista.

| Variante | chrF++ | Jerga resuelta | Cambios acertados | Jerga correcta | p50 | Entrenar |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `genlingo-2026-10b-e2b` (glosario; vio 70 de los 146) | 65.3 | 91 % | 34 % | 41 % | 592 ms | $0.71 |
| `genlingo-2026-10c-e2b` (léxico, con pares de 2–3 términos) | 61.9 | 86 % | 27 % | 36 % | 1.99 s | $1.41 |
| **`genlingo-2026-10c-e2b-nomulti`** (léxico, sin esos pares) | **63.2** | 85 % | 25 % | 33 % | 809 ms | $0.97 |
| `genlingo-2026-10c-e2b-nomulti-orpo` (+ preferencias ORPO) | 63.7 | 78 % | 26 % | 31 % | 866 ms | $0.56 |
| Goliath | 51.1 | 76 % | 18 % | 14 % | 3.60 s | — |
| Goliath + el léxico de David | 58.4 | 88 % | 33 % | 42 % | 3.10 s | — |

### Barrido de cuantización (2026-10-01, 319 pares de ese día, `genlingo-2026-10-e2b` con glosario)

| Cuantización | imatrix | Tamaño | Jerga resuelta | Cambios acertados | chrF++ | p50 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Q4_K_M | no | 3.42 GB | 67 % | 13 % | 51.2 | 496 ms |
| Q4_K_M | sí | 3.42 GB | 72 % | 14 % | 51.6 | 539 ms |
| **Q5_K_M** | no | 3.62 GB | **76 %** | 14 % | 51.5 | 587 ms |
| Q5_K_M | sí | 3.62 GB | 75 % | 15 % | 52.2 | 624 ms |
| Q6_K | no | 3.83 GB | 74 % | 15 % | 51.9 | 527 ms |
| Q8_0 | no | 4.95 GB | 75 % | 14 % | 51.9 | 532 ms |
| f16 | — | 9.27 GB | 75 % | 15 % | 51.9 | 534 ms |

### Cada experimento, en corto

Detalle y fechas en [docs/BITACORA.md](docs/BITACORA.md); decisiones técnicas en [docs/DECISIONES.md](docs/DECISIONES.md).

1. **Modelo base: E2B contra E4B.**
   - *Qué probó:* qué Gemma sirve sin afinar.
   - *Resultado:* E4B resuelve más jerga (68 % contra 58 %; correcta 19 % contra 14 %), pero saca menos chrF++ (48.2 contra 50.2), tarda más del doble (802 ms contra 364 ms) y pesa 6.58 GB.
   - *Qué aprendimos:* la regla elige el más pequeño con p50 < 1 s y el mejor chrF++: E2B. La ventaja de E4B sin afinar desapareció al afinar (experimento 6).
2. **Glosario sin afinar.**
   - *Qué probó:* darle a la base E2B el glosario del banco de términos en el prompt.
   - *Resultado:* la jerga correcta sube de 14 % a 38 % y chrF++ de 50.2 a 55.0.
   - *Qué aprendimos:* el dato importa antes que el ajuste.
3. **Paráfrasis libres** (2026-09-30, `genlingo-2026-09-parafrasis`).
   - *Qué probó:* entrenar con pares sintéticos que reescribían la frase completa.
   - *Resultado:* chrF++ 39.1, por debajo de la base (47.1) y de copiar la frase (50.0), en el set de 319 pares de ese día.
   - *Qué aprendimos:* David aprendió a reescribir todo; el par tiene que cambiar solo la jerga ([detalle](evals/experiments/2026-09-parafrasis-libres.md)).
4. **Pares de edición mínima** (`genlingo-2026-09`).
   - *Qué probó:* la misma frase con solo los términos cambiados.
   - *Resultado:* 62 % de jerga resuelta contra 58 % de la base, pero en papás → Gen Z solo 20 %. Costó $0.41 (17.4 min de L4).
   - *Qué aprendimos:* faltaba enseñar la dirección difícil.
5. **Pares anclados en el banco + glosario en el prompt** (`genlingo-2026-10-e2b`).
   - *Qué probó:* cada par nombra un término y su contraparte del mismo país, con trampas de otro país y 60 % papás → Gen Z; David se entrena con el mismo prompt con glosario.
   - *Resultado:* papás → Gen Z sube de 20 % a 43 % (Q5_K_M). Costó $0.67, más $0.80 de pares.
6. **E4B afinado** (`genlingo-2026-10-e4b`).
   - *Qué probó:* los mismos 1,500 pares sobre la base grande.
   - *Resultado:* 67 % de jerga resuelta y p50 de 836 ms en el eval del 2026-10-01. Costó $0.98; se quedó sin memoria al fusionar y se terminó en la laptop.
   - *Qué aprendimos:* no supera al E2B; más modelo no compró más jerga.
7. **Cuantización** (tabla arriba).
   - *Resultado:* Q4_K_M pierde 8 puntos de jerga contra f16; imatrix recupera 5 y sigue 3 abajo. Q5_K_M no pierde nada con 0.2 GB más. Q6_K y Q8_0 pesan más sin mejorar.
   - *Qué aprendimos:* la regla es el archivo más pequeño a ≤ 2 puntos del f16 con p50 < 1 s, y eso es Q5_K_M. El eval del 2026-10-04 lo repite: Q4 67 %, Q5 74 %, f16 74 %.
8. **Entrenar, fusionar y convertir en un solo job** (`zct96`).
   - *Resultado:* murió por memoria ($0.63), porque en Cloud Run el disco vive en la memoria.
   - *Qué aprendimos:* ahora son dos jobs, una L4 que entrena y un job de CPU que fusiona y convierte.
9. **Oraciones reales** (`genlingo-2026-10b-e2b`).
   - *Qué probó:* 22 fuentes, 146 términos y 420 oraciones reales; la mitad al set de prueba y la otra mitad a 334 pares de entrenamiento anclados en la oración.
   - *Resultado:* jerga resuelta de 74 % a 82 %, casi todo en papás → Gen Z (43 % → 59 %); jerga correcta 34 %. Costó $0.71.
10. **Contrapartes por *embedding*.**
    - *Qué probó:* enlazar cada término con su equivalente de la otra generación por similitud de vectores.
    - *Resultado:* 175 de 217 enlaces significaban otra cosa («brainrot → patatús») y estaban en 1,065 de 1,375 pares sintéticos.
    - *Qué aprendimos:* las contrapartes se validan por significado; los enlaces malos quedaron archivados solo como respuestas rechazadas.
11. **Contrapartes por significado + prompt de léxico + ronda 3 de oraciones reales** (`genlingo-2026-10c-e2b-nomulti`).
    - *Qué probó:*
      - contrapartes validadas por significado;
      - 1,715 pares sintéticos regenerados con ellas ($0.71 + $0.15);
      - un glosario de léxico con la respuesta en el 85 % de los ejemplos;
      - más oraciones reales de Guatemala y Colombia (532 términos de 26 fuentes).
    - *Resultado:* en dev, chrF++ 63.2 con p50 de 809 ms. En prueba, jerga correcta 42 % (contra 34 % de 10b) y chrF++ 59.7 (+3.1 [+1.7, +4.4] sobre 10b). Costó $0.97.
12. **Pares con 2–3 términos a la vez** (`genlingo-2026-10c-e2b`).
    - *Resultado:* en dev, chrF++ 61.9 contra 63.2 sin ellos y p50 de 1.99 s contra 809 ms. La jerga quedó igual (86 % contra 85 % resuelta, 36 % contra 33 % correcta). Costó $1.41.
    - *Qué aprendimos:* el modelo alarga las respuestas y no cabe en el presupuesto de 1 s; quedaron fuera.
13. **Preferencias ORPO** (`…-nomulti-orpo`).
    - *Resultado:* +0.5 de chrF++ en dev, pero la jerga resuelta papás → Gen Z bajó de 70 % a 57 % y la jerga correcta de 33 % a 31 %. Costó $0.56, más $1.81 de dos intentos fallidos (el modelo se cargaba en la CPU para muestrear y, con lote 4, los logits no cabían en la L4).
    - *Qué aprendimos:* no ayudó; quedó fuera.
14. **Goliath con el glosario de David.**
    - *Qué probó:* darle a Gemini el mismo banco en el prompt.
    - *Resultado:* jerga correcta de 26 % a 38 % y chrF++ de 53.5 a 57.0, con p50 de 3.05 s.
    - *Qué aprendimos:* con los mismos datos el modelo grande se acerca; la ventaja de David está en sus datos y en haberse entrenado con ellos. En la demo Goliath va sin glosario, como lo usaría cualquiera.
15. **Selección entre varias respuestas.**
    - *Qué probó:* generar 4 respuestas y quedarse con la que tiene más contrapartes esperadas del banco.
    - *Resultado:* en dev, la jerga resuelta de 10c subió de 86 % a 94 %, pero el p50 llegó a 4.40 s.
    - *Qué aprendimos:* no entra en el presupuesto de 1 s; está apagado (`DAVID_NBEST=1`).
16. **David en la nube** (2026-10-06).
    - *Qué probó:* servir el mismo David con Ollama en Cloud Run con una GPU L4 (europe-west4), privado y con escala a cero, y que la página pública lo llame con un token de identidad.
    - *Resultado:* con la GPU encendida, David responde en ~0.5 s a través de la página (Goliath, entre 0.8 y 18.6 s ese día). Encender la GPU desde cero, cargar el modelo y calentarlo tardaba casi cuatro minutos; leer los archivos de una vez y llevar los kernels de CUDA ya compilados en la imagen lo bajó a unos 35 segundos. Los 4 ejemplos dieron lo mismo que en la Mac: 12 de 12 aciertos de David, 0 de Goliath.
    - *Qué aprendimos:* en la nube David sigue siendo más rápido, pero ya no es gratis: la GPU cuesta unos $1.05 por hora mientras está encendida, y con el uso de una charla eso es más que lo que cobra Gemini por las mismas frases. La página mostró primero solo el tiempo; con la capacidad de la GPU medida, muestra los dos, y el README tiene las proyecciones: con volumen, David cuesta una fracción de Gemini ([Tiempo y costo en la nube](#tiempo-y-costo-en-la-nube)).

17. **Ronda 4: jerga Gen Z de México y del español neutro** (`genlingo-2026-10d-e2b`, 2026-10-06).
    - *Qué probó:* corregir con datos que David fallara con jerga Gen Z que no es chapina: 1,600 pares para entrenar anclados en términos Gen Z de México y del español neutro (Gemini, $1.02, validados contra el banco), 17 oraciones reales más de esos países, 3,880 ejemplos en total.
    - *Resultado:* en desarrollo, jerga correcta 46 % contra 40 % de `10c`. En prueba, 44 % contra 41 % y chrF++ 60.0 contra 59.5; español neutro de 32 % a 43 %, México igual (46 %), Guatemala de 52 % a 50 % y papás → Gen Z de Guatemala y Colombia de 44 % a 33 %. Costó $1.49 (68 min en la nube).
    - *Qué aprendimos:* los datos de un país mueven ese país. Con más datos generales David mejora en español neutro, pero no lo bastante para ganarle a Goliath ahí.
18. **Sonda de jerga Gen Z general** ([evals/report_probe.md](evals/report_probe.md)).
    - *Qué probó:* 32 oraciones reales de jerga Gen Z que se usa en todos lados (cringe, random, crush, stalkear, funar, mid, delulu…), de 14 páginas que nunca se usan para entrenar, en las dos direcciones.
    - *Resultado:* como español neutro, David 91 % (antes y después de la ronda 4) contra 94 % de Goliath; como Guatemala, David 77 % (antes 69 %) contra 77 %.
    - *Qué aprendimos:* esa jerga ya la conoce cualquier modelo grande; ahí David empata. Su ventaja está en la jerga local.
19. **El léxico sin afinar, medido otra vez** (eval del 2026-10-07).
    - *Resultado:* la base E2B con el mismo léxico de David llega a 42 % de jerga correcta, contra 44 % de David afinado; pero se queda en 16 % de jerga resuelta de papás a Gen Z (David 54 %) y en chrF++ 54.9 (David 60.0).
    - *Qué aprendimos:* el banco de jerga hace casi todo el trabajo de entender jerga; afinar es lo que enseña a *producirla*, la dirección papás → Gen Z.
20. **El eval también en la nube** (2026-10-07).
    - *Qué probó:* correr el eval en un Cloud Run Job con la misma L4 y los kernels de CUDA ya compilados de David.
    - *Resultado:* cada modelo responde las 399 frases en ~80 s, con p50 de 237 ms para David. Un job con GPU dura como máximo una hora, así que `make eval` corre los modelos en cuatro jobs seguidos y los junta.

**Costo total:** las ejecuciones de entrenamiento con registro costaron $10.64 ($9.15 hasta la ronda 3 más $1.49 de la ronda 4), incluidas cinco de las seis fallidas ($3.44; la sexta no dejó registro de costo).

## Por qué la demo usa solo el modelo final

La página usa `genlingo-2026-10d-e2b` en Q5_K_M con el prompt de léxico, y ningún otro David:

- **Es el mejor en lo que la demo enseña.** Tiene la jerga correcta más alta del set de prueba: 44 %, contra 41 % de `10c`, 33 % de `10b`, 26 % de `10-e2b` y 17 % de `2026-09`, y el chrF++ más alto (60.0). Se eligió en el set de desarrollo (46 % contra 40 % de `10c`), no en el de prueba.
- **Cabe en el presupuesto de 1 s.** p50 de 237 ms en el eval en la nube y ~0.6 s a través de la página, con 3.62 GB. La variante con pares de varios términos rondaba los 2 s en dev, y la selección entre 4 respuestas los 4.4 s.
- **Q5_K_M no pierde jerga contra f16** (44 % contra 43 %) y pesa 2.6 veces menos. Q4_K_M sí perdía jerga.
- **Los anteriores ya no enseñan nada nuevo en la página.** Su historia (de 14 % a 44 % de jerga correcta, a $0.41–$1.49 por ronda de entrenamiento) está en las tablas de arriba y en la bitácora.
- **Los ejemplos de la página son del caso donde gana:** slang chapín (+30.4 puntos de jerga correcta). México, Colombia de papás a Gen Z, el español neutro y la jerga Gen Z general, donde David empata, quedan documentados aquí y no se muestran como ejemplo.

## Arranque rápido

Para usar la demo no hace falta nada: abre la página. Para probar el código sin nube: `make test` (modelos simulados, `MOCK_AI=1`).

## Reproducirlo en tu propio proyecto

Los modelos (los GGUF de David y los kernels de CUDA compilados) y los datos de entrenamiento viven en **buckets privados** del proyecto de Google Cloud de la charla; al clonar el repo no vienen. Para reproducir todo necesitas tu propio proyecto de Google Cloud (con cuota de GPU L4) y tus buckets:

1. **Configuración:** `cp .env.example .env` y cambia `GOOGLE_CLOUD_PROJECT`, `MODELS_BUCKET` (los modelos), `STAGING_BUCKET` (entrenamiento y evals, en la región de la GPU) y `DAVID_URL` (se llena después del primer `make deploy`). Las cuentas de servicio y el repositorio de imágenes los crean los scripts de `infra/` ([docs/ONBOARDING.md](docs/ONBOARDING.md), sección 3).
2. **Datos:** las oraciones citadas de fuentes con todos los derechos reservados no están en el repo (ver [data/SOURCES.md](data/SOURCES.md)): en el proyecto de la charla las baja `make data-pull` del bucket privado (`PRIVATE_DATA_URI`); en el tuyo, `make data` vuelve a construir el set de prueba, los pares anclados en oraciones reales y los sintéticos desde las fuentes de [data/SOURCES.md](data/SOURCES.md) (los sintéticos los escribe Gemini, con costo).
3. **Entrenar:** `make train` (una L4 entrena y un job de CPU fusiona y publica el GGUF en tu `MODELS_BUCKET`).
4. **Medir:** `make eval` y `make eval-dev` (un job con GPU en la nube).
5. **Publicar:** `bash infra/04-david.sh` (David en Cloud Run con GPU), `bash infra/07-david-jit-cache.sh` y otra vez `infra/04-david.sh` (kernels de CUDA compilados, para que arranque en ~35 s) y `bash infra/05-page.sh` (la página). `make check` la prueba en vivo.

```bash
cp .env.example .env && (cd duel && uv sync)   # y edita .env con tu proyecto y tus buckets
gcloud auth application-default login
make data-pull   # solo en el proyecto de la charla; en otro, make data
make train TAG=genlingo-YYYY-MM && make eval
make deploy && make check
```

Comandos completos en [docs/COMANDOS.md](docs/COMANDOS.md).

## Licencia

El código está bajo Apache 2.0 ([LICENSE](LICENSE)). Los datos citan su fuente y su licencia en cada registro, y David, como ajuste de Gemma, sigue los términos de uso de Gemma: el detalle está en [THIRD_PARTY.md](THIRD_PARTY.md).

## Documentación

- [docs/DEMO.md](docs/DEMO.md): el guion de la demo (qué abrir, qué ejemplos tocar, qué decir y qué hacer si algo falla).
- [docs/BITACORA.md](docs/BITACORA.md): la historia de David iteración por iteración.
- [docs/DECISIONES.md](docs/DECISIONES.md): cada decisión técnica, los resultados completos y el costo de entrenamiento.
- [docs/ONBOARDING.md](docs/ONBOARDING.md): la nube, la cadena de datos y el entrenamiento, recorrido del código y problemas frecuentes.
- [docs/COMANDOS.md](docs/COMANDOS.md): todos los comandos `make`.
- [docs/ESTRUCTURA.md](docs/ESTRUCTURA.md): arquitectura, ciclo mensual, mapa del repositorio y versiones.
- [docs/CREDITOS.md](docs/CREDITOS.md): procedencia de los datos y licencias.
- [evals/report.md](evals/report.md), [evals/report_dev.md](evals/report_dev.md) y [evals/niche_report.md](evals/niche_report.md): los reportes de los evals; [evals/niche.md](evals/niche.md): los nichos definidos antes de mirar resultados.
- [data/SOURCES.md](data/SOURCES.md) y [data/DATASHEET.md](data/DATASHEET.md): fuentes y datasheet de los datos.
