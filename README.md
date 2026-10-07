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

Los cuatro ejemplos son jerga chapina del set de prueba, el caso donde David gana. Probé en vivo las 51 frases chapinas cortas que la revisión término por término puede juzgar, 3 veces con cada modelo, y quedaron solo las que David tradujo bien y Goliath mal las 3 veces. Después de pasar a David a la nube los volví a probar 3 veces contra el David de Cloud Run: David acertó las 12 veces y Goliath ninguna ([`data/translate_examples.json`](data/translate_examples.json), con la fuente y la razón de cada uno). El guion está en [docs/DEMO.md](docs/DEMO.md).

![Qué corre dónde: la página, David y Goliath en la nube](docs/diagrams/arquitectura.png)

## Qué vas a aprender

1. **Datos propios con `origin`:** cada par dice de dónde salió (`web`, `synthetic` o `human`); sin eso no se puede evaluar ni reentrenar cada mes.
2. **Banco de términos y oraciones reales:** 532 términos de 76 fuentes, contrapartes validadas por significado y 556 pares anclados en oraciones reales; la ventaja de David son sus datos.
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

Los números del set de prueba son del eval del 2026-10-04 sobre 399 frases web `auto_validated` que David nunca vio ([evals/report.md](evals/report.md)), salvo donde se indica otra fecha. Ese eval corrió a David en Ollama en una Mac (antes de pasarlo a la nube): las latencias y costos de esas tablas son de ahí. El tiempo y el costo de David en la nube están medidos aparte ([Tiempo y costo en la nube](#tiempo-y-costo-en-la-nube)).

## Resultado final

| | Jerga correcta | Jerga resuelta | chrF++ | p50 (eval) |
| --- | ---: | ---: | ---: | ---: |
| **David** (`genlingo-2026-10c-e2b-nomulti`, Q5_K_M, 3.62 GB) | **42 %** | **82 %** | **59.7** | **670 ms** |
| Goliath `gemini-3.8-flash` | 26 % | 77 % | 53.5 | 2.60 s |
| Goliath con el glosario de David (referencia) | 38 % | 82 % | 57.0 | 3.05 s |
| Copiar la frase (línea base) | 1 % | 1 % | 53.2 | — |

- **Jerga correcta:** +16.3 puntos sobre Goliath (IC 95 % [+10.8, +21.8]). 101 frases las acierta solo David y 36 solo Goliath.
- **chrF++:** +6.2 [+4.3, +8.1] sobre Goliath y +2.7 [+0.8, +4.7] sobre Goliath con el glosario.
- **Jerga resuelta:** +4.5 [+0.0, +8.8], empate estadístico.
- **Costo de Goliath:** $1.13 por 1,000 frases en ese eval; con la tarifa desde el 2027-01-01 serían $2.26.

### Por nicho (jerga correcta, David contra Goliath sin glosario)

Nichos definidos antes de mirar resultados ([evals/niche.md](evals/niche.md)); IC 95 % por bootstrap pareado ([evals/niche_report.md](evals/niche_report.md)).

| Nicho | n | David | Goliath | Δ | IC 95 % | Veredicto |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Slang chapín (GT) | 115 | 52 % | 23 % | +29.6 | [+19.1, +40.0] | gana David |
| Papás → Gen Z (GT/CO) | 107 | 44 % | 20 % | +24.3 | [+12.1, +36.4] | gana David |
| País CO | 131 | 37 % | 19 % | +17.6 | [+8.4, +27.5] | gana David |
| País MX | 78 | 46 % | 37 % | +9.0 | [−2.6, +21.8] | empate estadístico |
| País LATAM (español neutro) | 75 | 32 % | 31 % | +1.3 | [−9.3, +12.0] | empate estadístico |
| Todo el set | 399 | 42 % | 26 % | +16.3 | [+10.8, +21.8] | gana David |

- **En jerga resuelta**, que no mira el significado, David gana en papás → Gen Z (67 % contra 52 %, +15.0 [+2.8, +27.1]) y en Colombia (+8.4 [+0.8, +16.0]). En Guatemala (85 % contra 76 %), México, LATAM y el set completo es empate estadístico.
- **Contra Goliath con el mismo glosario:**
  - David gana en slang chapín (+17.4 [+7.0, +28.7]) y en papás → Gen Z (+16.0 [+3.8, +28.3]).
  - Empata en el set completo (+4.0).
  - Pierde en el español neutro: 32 % contra 55 %.

### chrF++ por país y por dirección

| | CO | GT | LATAM | MX | Gen Z → papás | Papás → Gen Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| David | 60.4 | 65.3 | 56.5 | 53.6 | 67.4 | 49.1 |
| Goliath | 53.8 | 52.9 | 55.4 | 51.5 | 61.0 | 43.0 |
| Goliath + glosario | 54.3 | 60.1 | 58.9 | 56.0 | 63.8 | 47.6 |

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

### Todas las variantes en el set de prueba (399 frases)

| Variante | Jerga correcta | Jerga resuelta (Gen Z → papás / papás → Gen Z / total) | Cambios acertados | chrF++ | p50 | Tamaño | Entrenar |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| Base `gemma4:e2b-it-qat` | 14 % | 95 % / 10 % / 58 % | 14 % | 50.2 | 364 ms | 4.34 GB | — |
| Base E2B + glosario | 38 % | 94 % / 20 % / 62 % | 23 % | 55.0 | 452 ms | 4.34 GB | — |
| Base `gemma4:e4b` | 19 % | 97 % / 31 % / 68 % | 17 % | 48.2 | 802 ms | 6.58 GB | — |
| `genlingo-2026-09` (edición mínima, Q4_K_M) | 18 % | 94 % / 20 % / 62 % | 14 % | 55.0 | 391 ms | 3.42 GB | $0.41 |
| `genlingo-2026-09-f16` | 18 % | 93 % / 27 % / 64 % | 14 % | 55.4 | 435 ms | 9.27 GB | — |
| `genlingo-2026-10-e2b` + glosario (Q4_K_M) | 25 % | 95 % / 31 % / 67 % | 16 % | 55.7 | 512 ms | 3.42 GB | $0.67 |
| `genlingo-2026-10-e2b-q5_k_m` + glosario | 27 % | 97 % / 43 % / 74 % | 18 % | 55.4 | 564 ms | 3.62 GB | — |
| `genlingo-2026-10-e2b-f16` + glosario | 28 % | 99 % / 42 % / 74 % | 19 % | 56.3 | 566 ms | 9.27 GB | — |
| `genlingo-2026-10b-e2b` + glosario (Q5_K_M) | 34 % | 99 % / 59 % / 82 % | 22 % | 56.6 | 557 ms | 3.62 GB | $0.71 |
| `genlingo-2026-10b-e2b-f16` + glosario | 34 % | 98 % / 59 % / 81 % | 22 % | 56.7 | 543 ms | 9.27 GB | — |
| **`genlingo-2026-10c-e2b-nomulti` + léxico (Q5_K_M)** | **42 %** | 100 % / 58 % / **82 %** | **28 %** | **59.7** | 670 ms | 3.62 GB | $0.97 |
| Goliath `gemini-3.8-flash` | 26 % | 97 % / 51 % / 77 % | 25 % | 53.5 | 2.60 s | — | — |
| Goliath + glosario | 38 % | 100 % / 58 % / 82 % | 29 % | 57.0 | 3.05 s | — | — |
| Copiar la frase | 1 % | 0 % / 3 % / 1 % | 0 % | 53.2 | — | — | — |

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

**Costo total:** las ejecuciones de entrenamiento con registro costaron $9.15, incluidas cinco de las seis fallidas ($3.44; la sexta no dejó registro de costo).

## Por qué la demo usa solo el modelo final

La página usa `genlingo-2026-10c-e2b-nomulti` en Q5_K_M con el prompt de léxico, y ningún otro David:

- **Es el mejor en lo que la demo enseña.** Tiene la jerga correcta más alta de todas las variantes: 42 %, contra 34 % de `10b`, 27 % de `10-e2b` y 18 % de `2026-09`. También tiene el chrF++ más alto (59.7).
- **Cabe en el presupuesto de 1 s.** p50 de 670 ms en el eval y ~0.5 s en la GPU de la nube, con 3.62 GB. La variante con pares de varios términos rondaba los 2 s en dev, y la selección entre 4 respuestas los 4.4 s.
- **Q5_K_M no pierde jerga contra f16** y pesa 2.6 veces menos. Q4_K_M sí perdía jerga.
- **Los anteriores ya no enseñan nada nuevo en la página.** Su historia (de 14 % a 42 % de jerga correcta, a $0.41–$0.97 por ronda de entrenamiento) está en las tablas de arriba y en la bitácora. En la página solo se compara el David de hoy con Goliath.
- **Los ejemplos de la página son del nicho donde gana** (slang chapín, +29.6 puntos de jerga correcta). México y el español neutro, donde David empata o donde Goliath con glosario le gana, quedan documentados aquí y no se muestran en la demo.

## Arranque rápido

Para usar la demo no hace falta nada: abre la página. Para probar el código sin nube: `make test` (modelos simulados, `MOCK_AI=1`).

## Reproducirlo en tu propio proyecto

Los modelos (los GGUF de David y los kernels de CUDA compilados) y los datos de entrenamiento viven en **buckets privados** del proyecto de Google Cloud de la charla; al clonar el repo no vienen. Para reproducir todo necesitas tu propio proyecto de Google Cloud (con cuota de GPU L4) y tus buckets:

1. **Configuración:** `cp .env.example .env` y cambia `GOOGLE_CLOUD_PROJECT`, `MODELS_BUCKET` (los modelos), `STAGING_BUCKET` (entrenamiento y evals, en la región de la GPU) y `DAVID_URL` (se llena después del primer `make deploy`). Las cuentas de servicio y el repositorio de imágenes los crean los scripts de `infra/` ([docs/ONBOARDING.md](docs/ONBOARDING.md), sección 3).
2. **Datos:** `make data` vuelve a construir el set de prueba, los pares anclados en oraciones reales y los sintéticos desde las fuentes de [data/SOURCES.md](data/SOURCES.md) (los sintéticos los escribe Gemini, con costo).
3. **Entrenar:** `make train` (una L4 entrena y un job de CPU fusiona y publica el GGUF en tu `MODELS_BUCKET`).
4. **Medir:** `make eval` y `make eval-dev` (un job con GPU en la nube).
5. **Publicar:** `bash infra/04-david.sh` (David en Cloud Run con GPU), `bash infra/07-david-jit-cache.sh` y otra vez `infra/04-david.sh` (kernels de CUDA compilados, para que arranque en ~35 s) y `bash infra/05-page.sh` (la página). `make check` la prueba en vivo.

```bash
cp .env.example .env && (cd duel && uv sync)   # y edita .env con tu proyecto y tus buckets
gcloud auth application-default login
make data && make train TAG=genlingo-YYYY-MM && make eval
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
