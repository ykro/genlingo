# Genlingo — traductor generacional: Gen Z ↔ papás

Demo de la charla *«David vs. Goliath: cómo un modelo pequeño le gana a un modelo frontier»*. «no manches, la peli estuvo bien chilera pero el final me dio cringe» ↔ «la película estuvo bien chévere pero el final me dio pena ajena». **David** es Gemma 4 E2B afinado con LoRA sobre pares propios y corre en la laptop con Ollama, **sin internet**. **Goliath** es Gemini (`GEMINI_MODEL`, hoy `gemini-3.8-flash`) en Vertex AI.

[English version](README.en.md)

## La demo: David y Goliath lado a lado

Una sola página, `http://127.0.0.1:8787/traducir` (la abre `make up`). Se elige la dirección (Gen Z → papás o papás → Gen Z), se escribe una frase o se toca un ejemplo, y los dos traducen la misma frase al mismo tiempo. Cada columna muestra su traducción, cuánto tardó y cuánto costó. En los ejemplos, la página muestra además la traducción de referencia hecha por personas y, debajo de cada columna, si acertó cada término de jerga (✓ o ✗). Sin internet, Goliath dice «Sin conexión» y David sigue traduciendo.

![La página de comparación: David y Goliath traducen «esa tu tarea te quedó bien chafa»](docs/demo/10-comparar-genz-a-papas.png)

Los cuatro ejemplos son jerga chapina del set de prueba, el caso donde David gana. Probé en vivo las 51 frases chapinas cortas que la revisión término por término puede juzgar, 3 veces con cada modelo. Quedaron solo las que David tradujo bien y Goliath mal las 3 veces ([`data/translate_examples.json`](data/translate_examples.json), con la fuente y la razón de cada una). El guion está en [docs/DEMO.md](docs/DEMO.md).

![Qué corre en la laptop y qué en la nube](docs/diagrams/arquitectura.png)

## Qué vas a aprender

1. **Datos propios con `origin`:** cada par dice de dónde salió (`web`, `synthetic` o `human`); sin eso no se puede evaluar ni reentrenar cada mes.
2. **Banco de términos y oraciones reales:** 532 términos de 76 fuentes, contrapartes validadas por significado y 556 pares anclados en oraciones reales; la ventaja de David son sus datos.
3. **LoRA en Cloud Run Jobs:** una L4 entrena y un job de CPU fusiona y exporta GGUF; cada ejecución registra su duración y costo.
4. **El costo de comprimir:** f16 contra Q4_K_M, Q5_K_M, Q6_K, Q8_0 e imatrix, en tamaño, latencia y jerga perdida.
5. **Evals con métricas de término:** chrF++ más *jerga correcta*, *jerga resuelta* y *cambios acertados*, con un set de desarrollo aparte para decidir y nichos definidos antes de mirar resultados.
6. **Offline por diseño:** el modelo, el glosario y la página viven en la laptop; la nube solo entrena una vez al mes.

## Las métricas

- **Jerga correcta:** la jerga que produce el modelo significa lo mismo que el original, según la tabla de contrapartes validadas por significado (`data/counterparts.jsonl`). Es la métrica principal.
- **Jerga resuelta:** el registro cambió. En Gen Z → papás no queda jerga Gen Z del banco; en papás → Gen Z la salida usa al menos un término Gen Z del país. No mira el significado.
- **Cambios acertados:** de las palabras que cambió la referencia humana, cuántas aparecen en la salida.
- **chrF++:** parecido de caracteres con la referencia. Una reescritura de registro conserva casi todas las palabras, así que copiar la frase sin traducir ya saca 53.2; por eso no decide por sí sola.

Todo es determinista: ningún modelo juzga a otro. Los números del set de prueba son del eval del 2026-10-04 sobre 399 frases web `auto_validated` que David nunca vio ([evals/report.md](evals/report.md)), salvo donde se indica otra fecha.

## Resultado final

| | Jerga correcta | Jerga resuelta | chrF++ | p50 | Costo / 1,000 frases |
| --- | ---: | ---: | ---: | ---: | ---: |
| **David** (`genlingo-2026-10c-e2b-nomulti`, Q5_K_M, 3.62 GB) | **42 %** | **82 %** | **59.7** | **670 ms** | **$0** |
| Goliath `gemini-3.8-flash` | 26 % | 77 % | 53.5 | 2.60 s | $1.13 |
| Goliath con el glosario de David (referencia) | 38 % | 82 % | 57.0 | 3.05 s | $1.27 |
| Copiar la frase (línea base) | 1 % | 1 % | 53.2 | — | — |

- **Jerga correcta:** +16.3 puntos sobre Goliath (IC 95 % [+10.8, +21.8]). 101 frases las acierta solo David y 36 solo Goliath.
- **chrF++:** +6.2 [+4.3, +8.1] sobre Goliath y +2.7 [+0.8, +4.7] sobre Goliath con el glosario.
- **Jerga resuelta:** +4.5 [+0.0, +8.8], empate estadístico.
- **Costo de Goliath:** con la tarifa desde el 2027-01-01 sería $2.26 por 1,000 frases.

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

**Costo total:** las ejecuciones de entrenamiento con registro costaron $9.15, incluidas cinco de las seis fallidas ($3.44; la sexta no dejó registro de costo). La inferencia de David cuesta $0.

## Por qué la demo usa solo el modelo final

La página usa `genlingo-2026-10c-e2b-nomulti` en Q5_K_M con el prompt de léxico, y ningún otro David:

- **Es el mejor en lo que la demo enseña.** Tiene la jerga correcta más alta de todas las variantes: 42 %, contra 34 % de `10b`, 27 % de `10-e2b` y 18 % de `2026-09`. También tiene el chrF++ más alto (59.7).
- **Cabe en el presupuesto de la laptop.** p50 de 670 ms y 3.62 GB. La variante con pares de varios términos rondaba los 2 s en dev, y la selección entre 4 respuestas los 4.4 s.
- **Q5_K_M no pierde jerga contra f16** y pesa 2.6 veces menos. Q4_K_M sí perdía jerga.
- **Los anteriores ya no enseñan nada nuevo en escena.** Su historia (de 14 % a 42 % de jerga correcta, a $0.41–$0.97 por ronda) está en las tablas de arriba y en la bitácora. En escena solo se compara el David de hoy con Goliath.
- **Los ejemplos de la página son del nicho donde gana** (slang chapín, +29.6 puntos de jerga correcta). México y el español neutro, donde David empata o donde Goliath con glosario le gana, quedan documentados aquí y no se muestran en la demo.

## Arranque rápido

```bash
cp .env.example .env && (cd duel && uv sync) && (cd web && npm install && cp .env.example .env.local)
gcloud auth application-default login                 # Goliath (Vertex AI) y descarga de modelos
ollama pull embeddinggemma && make pull-model TAG=genlingo-2026-10c-e2b-nomulti   # léxico + David
make up       # Ollama + David precalentado + servicio (:8787); abre la página de comparación
make test     # pruebas sin red (MOCK_AI=1)
```

Ensayo sin red ni GPU: `MOCK_AI=1` en `.env` y `make up`. Requisitos y la versión completa en [docs/COMANDOS.md](docs/COMANDOS.md#arranque-rápido).

## Documentación

- [docs/DEMO.md](docs/DEMO.md): el guion de la demo (cómo abrir la página, qué ejemplos tocar, qué decir y qué hacer si algo falla).
- [docs/BITACORA.md](docs/BITACORA.md): la historia de David iteración por iteración.
- [docs/DECISIONES.md](docs/DECISIONES.md): cada decisión técnica, los resultados completos y el costo de entrenamiento.
- [docs/ONBOARDING.md](docs/ONBOARDING.md): instalación, nube, cadena de datos y entrenamiento, recorrido del código y problemas frecuentes.
- [docs/COMANDOS.md](docs/COMANDOS.md): todos los comandos `make`.
- [docs/ESTRUCTURA.md](docs/ESTRUCTURA.md): arquitectura, ciclo mensual, mapa del repositorio y versiones.
- [docs/CREDITOS.md](docs/CREDITOS.md): procedencia de los datos y licencias.
- [evals/report.md](evals/report.md), [evals/report_dev.md](evals/report_dev.md) y [evals/niche_report.md](evals/niche_report.md): los reportes de los evals; [evals/niche.md](evals/niche.md): los nichos definidos antes de mirar resultados.
- [data/SOURCES.md](data/SOURCES.md) y [data/DATASHEET.md](data/DATASHEET.md): fuentes y datasheet de los datos.
