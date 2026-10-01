# Genlingo

**Traductor generacional: Gen Z ↔ papás.** Demo de la charla *«David vs. Goliath: cómo un modelo pequeño le gana a un modelo frontier»*.

«no manches, la peli estuvo bien chilera pero el final me dio cringe» ↔ «la película estuvo bien chévere pero el final me dio pena ajena».

- **David** es Gemma 4 E2B afinado con LoRA sobre pares propios. Corre en la laptop del escenario con Ollama, **sin internet**.
- **Goliath** es Gemini (`GEMINI_MODEL`, hoy `gemini-3.8-flash`) en Vertex AI.
- El público entra con un QR, manda frases desde el teléfono y vota quién tradujo mejor. Una métrica objetiva compara a los dos contra referencias humanas.

English version: [README.en.md](README.en.md) · Guía de puesta en marcha: [docs/ONBOARDING.md](docs/ONBOARDING.md)

App del público (Cloud Run): **https://genlingo-611681112050.us-central1.run.app**

![Vista del presentador: David y Goliath traducen la misma frase](docs/screenshots/presentador-ronda.png)

## El resultado, sin maquillaje

El resultado es mixto, y la charla lo cuenta así:

- **En jerga resuelta, David gana a Gemini solo:** el David de escena (`genlingo-2026-10-e2b-f16` + glosario) resuelve la jerga en el **75 %** de las frases de prueba; Gemini sin ayuda, en el **66 %**. David responde en **~0.5 s** (p50 534 ms) y cuesta **$0** por frase; Goliath tarda **~5 s** (p50 5.22 s) y cuesta **~$1.10 por 1,000 frases**.
- **Con el mismo glosario, gana Goliath (82 %).** La ventaja de David no es ser mejor modelo: son **sus datos** (el banco de términos investigado, con fuentes y fecha), que Goliath no tiene.
- **Comprimir cuesta jerga:** el mismo David en Q4 (3.42 GB) resuelve 67 % contra 75 % en f16 (9.27 GB).
- **chrF++ casi no distingue a nadie:** devolver la frase sin traducir ya saca **50.0**; David f16 saca 51.9 y Goliath 52.1. Por eso existe la métrica a nivel de término.
- **Reentrenar cada mes cuesta menos de $1** en una GPU L4 de Cloud Run ($0.41 y $0.67 en las dos corridas de E2B).
- **Los modelos grandes envejecen:** con la tecla `M` el David del mes pasado (`genlingo-2026-09`, 55 %) se enfrenta en vivo al de este mes (75 %).

> Las referencias del set de prueba todavía están en `pending_review`: estos números son de ensayo y cambiarán cuando el presentador apruebe o corrija el set (`make review-test`). Detalle completo en [evals/report.md](evals/report.md).

![Jerga resuelta por variante](docs/diagrams/resultados-jerga.png)

## Qué vas a aprender

| Lección | Dónde está en el código |
| --- | --- |
| **Datos propios con `origin`.** Cada par dice de dónde salió: `web` (URL + licencia), `synthetic` (modelo + versión de prompt + semilla) o `human` (evento). Sin eso no se puede evaluar con honestidad ni reentrenar cada mes. | `duel/genlingo_duel/dataset.py` (esquema `Pair` que valida la procedencia), [data/SOURCES.md](data/SOURCES.md), [data/DATASHEET.md](data/DATASHEET.md) |
| **Banco de términos y pares sintéticos validados.** 260 términos de 35 fuentes; Gemini genera pares de *sustitución de término* anclados en el banco, y cada par se valida contra el banco (término esperado presente, nada de jerga de otro país, la jerga del origen desaparece). De 2,700 generados quedaron 1,848 válidos; se usan 1,500. | `data/terms.jsonl`, `scripts/generate_pairs.py`, `duel/genlingo_duel/terms.py` |
| **LoRA en un Cloud Run GPU Job.** El mismo contenedor entrena (TRL + PEFT, r=16, alpha=32, lr 2e-4, 3 épocas), fusiona, exporta GGUF con llama.cpp y publica un Modelfile para Ollama. Cada corrida deja su duración y costo en un archivo. | `train/train_lora.py`, `train/submit_job.py`, `infra/03-train-job.sh`, `train/runs/` |
| **El costo de comprimir.** f16 contra Q4_K_M: tamaño, latencia y cuánta jerga se pierde. | `train_lora.to_gguf`, sección «Compresión» de `evals/report.md` |
| **Evals honestos con métricas de término.** chrF++ más una línea base de «copiar la frase», *jerga resuelta* y *cambios acertados* contra el banco; las derrotas de David se publican. Ningún modelo juzga a otro. | `evals/run_eval.py`, `evals/term_accuracy.py`, `evals/report.py` |
| **Reentrenamiento mensual y `david_tag`.** Los modelos llevan la fecha de sus datos (`genlingo-AAAA-MM`); el duelo acepta `david_tag` para enfrentar al David del mes pasado con el de este mes. | `Makefile` (`TAG`), `DuelRequest.david_tag` en `duel/genlingo_duel/main.py`, tecla `M` en `web/components/presenter/PresenterApp.tsx` |
| **Offline por diseño.** El chequeo de red es una conexión TCP de 0.8 s; sin red, Goliath aparece «sin conexión» y David sigue. El glosario se recupera con EmbeddingGemma local y embeddings en caché. | `duel/duel_core/connectivity.py`, `duel/duel_core/duel.py`, `duel/genlingo_duel/glossary.py` |

## Arquitectura

![Qué corre en la laptop y qué en la nube](docs/diagrams/arquitectura.png)

Fuente editable: [docs/diagrams/arquitectura.html](docs/diagrams/arquitectura.html) (también en `.svg`).

El ciclo de cada mes, de los datos al escenario y de vuelta:

![Ciclo mensual](docs/diagrams/ciclo-mensual.png)

## Inicio rápido

Requisitos (versiones en [docs/ONBOARDING.md](docs/ONBOARDING.md)): macOS con Apple Silicon, `uv`, Node 24, Ollama, `gcloud` con ADC.

```bash
cp .env.example .env                                  # modelos, precios y rutas
(cd duel && uv sync)                                  # servicio del duelo (Python 3.12)
(cd web && npm install && cp .env.example .env.local) # vista del presentador y app del público
gcloud auth application-default login                 # Goliath (Vertex AI) y descarga de modelos

ollama pull embeddinggemma                            # recuperación del glosario
make pull-model TAG=genlingo-2026-10-e2b FP16=1       # David de escena (crea -e2b y -e2b-f16)
make pull-model TAG=genlingo-2026-09                  # David del mes pasado (tecla M)

make up       # Ollama + David precalentado + duelo (:8787) + vista del presentador (:3000/presenter)
```

Ensayo sin red ni GPU: pon `MOCK_AI=1` en `.env` y corre `make up` (modelos simulados y deterministas).

## Comandos `make`

| Comando | Qué hace |
| --- | --- |
| `make help` | Lista los comandos con su descripción. |
| `make up` | Arranca Ollama, precalienta a David, levanta el servicio del duelo y la vista del presentador. Funciona sin Wi-Fi. |
| `make reset` | Pone en cero rondas, votos, cola y marcador locales; con `AUDIENCE_FEED=1` y red, también borra las rondas del evento en Firestore. |
| `make test` | Pruebas de Python (`MOCK_AI=1`), Vitest, `tsc`, ESLint y, con JDK 21, las reglas de Firestore en el emulador. |
| `make eval` | Pasa el set de prueba por los modelos base, cada David y Goliath (con y sin glosario) y escribe `evals/report.md`. Acepta `EVAL_ARGS="--limit 50 --no-goliath"`. |
| `make test-set` | Construye los pares de prueba (`pending_review`) a partir de ejemplos reales de la web. |
| `make pairs` | Genera los pares sintéticos de entrenamiento con `GEMINI_MODEL` (de pago; `SYNTHETIC_PAIRS_TARGET`, hoy 1,500). |
| `make datasheet` | Recuenta `data/DATASHEET.md`. |
| `make data` | `test-set` + `pairs` + `datasheet`. |
| `make review-test` | Exporta el set de prueba a `data/review/test_review.csv` para que lo revise el presentador. |
| `make review-test-apply` | Aplica las decisiones del CSV (`a` aprobar, `r` rechazar, referencia corregida opcional). |
| `make export` | Baja de Firestore los pares del público aprobados en `/admin` a `data/pairs/human.jsonl` y recuenta el datasheet. |
| `make train-data` | Renderiza los pares aprobados al JSONL de chat con el mismo prompt (y glosario) del duelo. |
| `make train` | Entrena en un Cloud Run Job con una L4: `make train TAG=genlingo-2027-03 [GEMMA_BASE_MODEL=…] [TRAIN_ARGS=…]`. Escribe `train/runs/<tag>.json`. |
| `make train-finish` | Fusiona y exporta a GGUF en la laptop un adaptador entrenado en la nube y lo publica: `make train-finish TAG=…`. |
| `make train-local` | El mismo entrenamiento en la Mac (MPS), para experimentos. |
| `make pull-model` | Descarga un David del bucket y lo registra en Ollama: `make pull-model TAG=… [FP16=1]`. |
| `make deploy` | Crea la cuenta de servicio web y despliega la app del público en Cloud Run (`min-instances=1`). |

## Mapa del repo

```
duel/                 Servicio del duelo (FastAPI) — corre en la laptop
  duel_core/          Núcleo reutilizable: duelo en paralelo, clientes Ollama/Gemini/mock,
                      conectividad, costo con tarifas fechadas, chrF++, percentiles
  genlingo_duel/      La app: prompts, glosario, banco de términos, arena, marcador (SQLite),
                      puente con Firestore (audience_feed.py), API (main.py)
  tests/              Pruebas del servicio (MOCK_AI=1)
web/                  Next.js: app del público (/), moderación (/admin), vista del presentador (/presenter)
  app/api/            Rutas del público (frases, pares, votos, config) y de admin
  lib/server/         Auth + App Check, límite de 20 s, blocklist, validación, Firestore
  e2e/                Ensayos con Playwright y con el emulador de Android
  firestore.rules     Ningún cliente escribe directo; todo pasa por la API
data/                 terms.jsonl, raw/web_usage.jsonl, pairs/, review/, SOURCES.md, DATASHEET.md
scripts/              Construcción de datos, revisión, export, reset, make up
train/                train_lora.py, submit_job.py, finish_local.py, train_local.py, notebook, runs/
evals/                run_eval.py, term_accuracy.py, report.py, report.md, experiments/
infra/                Scripts gcloud numerados (01–06) y env.sh compartido
docs/                 ONBOARDING.md, diagrams/ (HTML + SVG + PNG), screenshots/
```

## Decisiones técnicas

### Qué corre en la laptop y por qué

| Componente | Por qué en la laptop |
| --- | --- |
| **David** (Gemma afinado, Ollama) | Es la tesis: un modelo pequeño corre en tu laptop, sin internet y sin costo por frase. La latencia que importa es la del hardware del escenario (M1 Max 64 GB), no la de un servidor. |
| **EmbeddingGemma** (Ollama) | Recupera el glosario del banco de términos sin red. Los embeddings del banco se calculan una vez y quedan en `data/.cache/term_embeddings.json`. |
| **Servicio del duelo** (FastAPI + SQLite) | Tiene que funcionar con el Wi-Fi apagado y medir la latencia en la máquina del escenario. El marcador en SQLite local hace que `make reset` tarde menos de un segundo. |
| **Vista del presentador** (Next.js, build de producción local) | Modo offline: tipografías propias y QR generado en el navegador, nada se descarga durante la charla. |

Si hay red, el duelo también llama a Goliath y, con `AUDIENCE_FEED=1`, recibe frases aprobadas y publica rondas en Firestore. Sin red, todo eso se calla y David sigue.

### Qué corre en la nube

- **App del público** en Cloud Run (`us-central1`, `min-instances=1` para que el QR no reciba a la sala con un arranque en frío). Auth anónima de Firebase (sin registro), App Check con reCAPTCHA Enterprise, límite de una frase cada 20 s aplicado en una transacción del servidor, blocklist y moderación del presentador en `/admin`.
- **Firestore**, base de datos `genlingo`: frases, rondas, votos (uno por persona) y pares del público. Las reglas niegan toda escritura de clientes; la cuenta de servicio `genlingo-web` solo puede tocar esa base (condición de IAM).
- **Goliath**: Gemini en Vertex AI con ADC, `GOOGLE_CLOUD_LOCATION=global`, razonamiento `low`.
- **Entrenamiento**: Cloud Run Job con GPU en `europe-west4`; imagen construida con Cloud Build en Artifact Registry `charlas2027`.

### Por qué Cloud Run GPU Jobs

Un reentrenamiento al mes no justifica nada encendido entre corridas. Un Cloud Run Job con una L4 es serverless, se cobra por segundo mientras la tarea corre y usa el mismo tipo de imagen que el resto. `train/submit_job.py` calcula el costo con las tarifas por segundo de GPU, vCPU y memoria, y lo deja en `train/runs/<tag>.json`.

Dos límites dieron forma al job (`infra/03-train-job.sh`): las tareas con GPU duran como máximo 1 h, y el sistema de archivos de Cloud Run vive en memoria (32 GiB en total). Por eso los pesos base se cachean en un volumen de Cloud Storage, mientras el modelo fusionado y los GGUF van al disco en memoria: leer y escribir el GGUF sobre el bucket montado iba a ~3 MB/s (corridas canceladas `kcwqz` y `kqlxv` en `train/runs/failed/`).

Alternativas descartadas como camino principal, pero disponibles: un Vertex AI Custom Job con el mismo contenedor (`TRAIN_RUNTIME=vertex`), el notebook `train/genlingo.ipynb` para Colab, y `make train-local` en la Mac (36.9 min para 1,000 pares en MPS; en la L4, la fase de entrenamiento de ese mismo tamaño tomó 5.8 min).

### Por qué E4B termina en la laptop (`make train-finish`)

Gemma 4 E4B entrena bien en la L4 (282 pasos, 24.7 min) y el adaptador LoRA se guarda en el bucket. Pero fusionar un checkpoint de 16 GB y convertirlo a GGUF no cabe en los 32 GiB del job: la corrida `genlingo-2026-10-e4b` terminó con «The configured memory limit was reached». La parte que necesita GPU se queda en la nube y la que necesita RAM se hace en la laptop de 64 GB: `make train-finish TAG=genlingo-2026-10-e4b` descarga el adaptador, fusiona, cuantiza a Q4_K_M y publica en el mismo bucket, así que `make pull-model` no distingue dónde se hizo la fusión. Para bases grandes, `TRAIN_ARGS=--adapter-only` detiene el job después de guardar el adaptador. E4B no salió a escena: con 67 % de jerga resuelta y p50 de 836 ms no supera al E2B f16.

### El prompt con glosario

El prompt `translate-v2` empieza por el país («Variante: español de Guatemala. Usa solo expresiones de Guatemala…») porque «chido» y «chilero» son la misma palabra en lugares distintos. Al final lleva un glosario de cuatro entradas del banco de términos, del país o neutras: primero los términos de la generación de origen que aparecen literalmente en la frase y después los más cercanos por significado según EmbeddingGemma. El tiempo de recuperación se suma a la latencia de David.

David se entrena con exactamente ese formato (`make train-data` usa `v2+glossary` por defecto) y el duelo lee de `train/runs/<tag>.json` con qué prompt se entrenó cada David: no hay diferencia entre entrenamiento y escena. Goliath recibe `v2` sin glosario por defecto (`GOLIATH_PROMPT_STYLE`), porque el banco es dato de David; `make eval` corre además a Goliath con el mismo glosario, y así se ve cuánto del resultado es modelo y cuánto es dato.

### El set de prueba es solo web, nunca sintético

Una referencia escrita por Gemini premiaría a Goliath por sonar como él mismo. Los 319 pares de prueba salen de oraciones reales encontradas en la web; la referencia la escribe el curador a partir del significado que da la fuente y la revisa el presentador. El esquema `Pair` rechaza cualquier par sintético en el split de prueba. Los pares del público (`origin=human`) se reparten 80/20 entre entrenamiento y prueba con un hash estable del id.

### Tarifas de Gemini con fecha

Los precios cambian, y eso es parte de la historia. `GEMINI_PRICE_SCHEDULE=2026-09-30:0.75/3.75,2027-01-01:1.50/7.50` es una lista de tarifas por fecha: cada ronda y cada eval usan la tarifa vigente ese día y registran cuál usaron. El reporte muestra además lo que costaría el mismo eval con la tarifa de 2027 ($2.21 por 1,000 frases en vez de $1.10). Los tokens de razonamiento se cobran como salida. La inferencia de David cuesta $0; el presentador muestra su costo de entrenamiento amortizado por ronda cuando encuentra `train/runs/<tag>.json` para el tag activo (hoy lo encuentra para `genlingo-2026-09`, pero no para el tag `-f16` de escena).

### App Check se aplica a todo el proyecto

`infra/06-app-check.sh` registra reCAPTCHA Enterprise como proveedor de App Check y, con `ENFORCE_FIRESTORE=1`, exige App Check en Cloud Firestore. Esa exigencia es **por proyecto**: App Check no tiene política por base de datos, así que cualquier cliente web o móvil de cualquier base de `ai-experiments-487722` tendrá que mandar tokens de App Check. El código de servidor (Admin SDK, IAM) no se ve afectado. Las rutas de la API lo exigen por su cuenta con `APP_CHECK_ENFORCE=1`, que `infra/05-deploy-web.sh` activa cuando hay `RECAPTCHA_SITE_KEY`. Las pruebas automatizadas y el emulador usan un token de depuración registrado.

### Quién gana una ronda

- **Ronda de evaluación** (frase del set de prueba, tecla `E`): gana el chrF++ más alto; diferencias menores a 0.5 son empate. Solo usa pares aprobados, salvo con `ALLOW_UNREVIEWED_TEST=1`.
- **Ronda del público** (frase de un teléfono o escrita con `/`): decide el voto del público (`V` cierra la votación).
- Si Goliath no tiene red o falla, David gana por presentarse.

## Resultados

Eval del 2026-10-01 sobre 319 pares de prueba web (referencias aún en `pending_review`). Jerga resuelta: n = 304 frases juzgables (298 para Goliath sin glosario, que tuvo 6 errores).

| Variante | Jerga resuelta | Gen Z → papás | papás → Gen Z | chrF++ | p50 | Costo / 1,000 frases | Tamaño |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Copiar la frase (línea base) | 0 % | 0 % | 1 % | 50.0 | — | — | — |
| `gemma4:e2b-it-qat` (base) | 50 % | 92 % | 10 % | 48.7 | 370 ms | $0 | 4.34 GB |
| `gemma4:e2b-it-qat` + glosario | 57 % | 93 % | 21 % | 52.0 | 501 ms | $0 | 4.34 GB |
| `genlingo-2026-09` (mes pasado, Q4) | 55 % | 90 % | 21 % | 52.1 | 386 ms | $0 | 3.42 GB |
| `genlingo-2026-10-e2b` + glosario (Q4) | 67 % | 95 % | 40 % | 51.2 | 496 ms | $0 | 3.42 GB |
| **`genlingo-2026-10-e2b-f16` + glosario (en escena)** | **75 %** | 97 % | 54 % | 51.9 | **534 ms** | **$0** | 9.27 GB |
| `genlingo-2026-10-e4b` + glosario (Q4) | 67 % | 94 % | 41 % | 52.4 | 836 ms | $0 | 5.30 GB |
| Goliath `gemini-3.8-flash` | 66 % | 98 % | 37 % | 52.1 | 5.22 s | $1.10 | — |
| Goliath + el mismo glosario | 82 % | 99 % | 65 % | 55.0 | 5.09 s | $1.17 | — |

**Lectura honesta.** Frase por frase, David resuelve la jerga y Goliath no en 51 frases; al revés, en 26. Contra Goliath con glosario, la cuenta se invierte: 27 contra 48. La dirección difícil es papás → Gen Z, y ahí es donde el glosario y los datos rebalanceados (60 % papás → Gen Z) más ayudan. David gana en velocidad, costo y privacidad, y gana en jerga mientras el banco de términos sea solo suyo. chrF++ queda pegado a la línea base de copiar (50.0) porque una reescritura de registro conserva casi todas las palabras: no sirve para decidir quién tradujo la jerga.

Las diez peores derrotas de David y los cortes por país y dirección están en [evals/report.md](evals/report.md). La primera versión de los datos (`pairs-v1`, paráfrasis libre) dejó a David *por debajo* de la base (chrF++ 39.1): está documentado en [evals/experiments/2026-09-pairs-v1.md](evals/experiments/2026-09-pairs-v1.md).

| Tecla `M`: el David del mes pasado | Wi-Fi apagado |
| --- | --- |
| ![El David del mes pasado (tecla M)](docs/screenshots/presentador-mes-pasado.png) | ![Sin internet: Goliath sin conexión, David sigue](docs/screenshots/presentador-sin-internet.png) |
| Tecla `M`: `genlingo-2026-09` contra Goliath con la misma frase. | Sin red: Goliath aparece «sin conexión» y David responde en 0.59 s (aunque aquí se equivoca: en Guatemala «bolo» es borracho y «chupando» es bebiendo). |

## Costo de entrenamiento por corrida

Cloud Run Job, 1× NVIDIA L4 sin redundancia zonal, 8 vCPU, 32 GiB, `europe-west4`. Costo = segundos facturados × tarifas por segundo (`CLOUD_RUN_*_USD_PER_S` en `.env`).

| Corrida | Base | Pares | Resultado | Duración | Costo |
| --- | --- | --- | --- | --- | --- |
| `genlingo-2026-09` | E2B | 1,000 (`pairs-v2`) | listo (loss 2.33 → 0.14) | 17.4 min | $0.41 |
| `genlingo-2026-10-e2b` | E2B | 1,500 (`pairs-v3`) | listo (loss 2.26 → 0.12) | 28.2 min | $0.67 |
| `genlingo-2026-10-e4b` | E4B | 1,500 (`pairs-v3`) | entrenó; sin memoria al fusionar → `make train-finish` | 41.3 min | $0.98 |
| `failed/genlingo-2026-09-nv5r5` | E2B | 1,000 | falló al arrancar (faltaba `gcc` para Triton) | 10.9 min | $0.26 |
| `failed/genlingo-2026-09-kcwqz` | E2B | 1,000 | cancelada: GGUF escrito en el bucket montado, demasiado lento | 31.2 min | $0.74 |
| `failed/genlingo-2026-09-kqlxv` | E2B | 1,000 | cancelada a ~28 min (misma causa, al leer) | — | sin registro |
| `experiments/genlingo-2026-09-pairs-v1` | E2B | 1,000 (`pairs-v1`) | laptop, MPS | 36.9 min | $0 |

Generar los 1,500 pares sintéticos de `pairs-v3` con Gemini costó $0.80 (6 min). Un reentrenamiento mensual de E2B cuesta menos de $1; la inferencia de David, $0.

## Versiones

| Pieza | Versión |
| --- | --- |
| Modelo base de David | Gemma 4 E2B (`gemma-4-E2B-it`, pesos de Hugging Face `hf://google`); comparado con E4B |
| Goliath | `gemini-3.8-flash` (`GEMINI_THINKING_LEVEL=low`) en Vertex AI |
| Embeddings locales | EmbeddingGemma (`embeddinggemma` en Ollama) |
| Ollama | 0.35.0 |
| Entrenamiento | torch 2.14.0 (CUDA 12.6), transformers 5.17.0, peft 0.21.1, trl 1.14.1, accelerate 1.15.0, datasets 5.0.1, llama.cpp `b11292` |
| Servicio del duelo | Python 3.12, fastapi 0.142.2, uvicorn 0.54.0, google-genai 2.25.0, sacrebleu 2.6.0, google-cloud-firestore 2.33.0 |
| Web | Next.js 16.3.8, React 19.2.8, firebase 12.19.0, firebase-admin 14.5.0, Node 24 |

Los modelos vienen de variables de entorno (`GEMINI_MODEL`, `GEMMA_BASE_MODEL`, `LOCAL_MODEL_TAG`, `DAVID_PREVIOUS_TAG`, `DAVID_TAGS`, `BASE_MODEL_TAGS`, `EMBEDDING_MODEL`), documentadas en `.env.example`. El proyecto no usa APIs en preview (ADK, MCP, A2A).

## Procedencia de los datos y licencias

| Datos | Origen | Licencia / uso |
| --- | --- | --- |
| `data/terms.jsonl` (260 términos) y `data/raw/web_usage.jsonl` | 35 fuentes web de MX, GT, CO y Latinoamérica, consultadas el 2026-09-30 ([SOURCES.md](data/SOURCES.md)) | WikiLengua (CC BY-SA 3.0), Wikcionario (CC BY-SA 4.0) y diccionario-chapin (MIT) se reutilizan bajo su licencia con atribución por registro. De las fuentes con todos los derechos reservados solo se toman hechos (término y significado, parafraseado) y una cita breve atribuida por entrada, con fines de investigación y educación. |
| `data/pairs/test_web.jsonl` (319 pares) | Oraciones reales de esas fuentes; la referencia es reescritura del curador (menos de 30 % son oraciones escritas por el curador, marcadas `example_origin=curator`) | Igual que la fuente; los pares que citan ejemplos CC BY-SA heredan share-alike para ese texto. |
| `data/pairs/synthetic.jsonl` (1,500 pares) | `gemini-3.8-flash`, prompt `pairs-v3`, semilla base 2027; solo entrenamiento | Cada par registra modelo, versión de prompt, semilla y los ids de término de los que salió. |
| `data/pairs/human.jsonl` | Público de cada evento, aprobado en `/admin` (`make export`) | Procedencia: evento e id de Firestore. |

Limitaciones conocidas (del datasheet): la jerga juvenil guatemalteca está poco documentada en línea; la jerga envejece rápido; las referencias son de una sola persona, así que chrF++ subestima traducciones alternativas válidas.

## App desplegada

- Público: **https://genlingo-611681112050.us-central1.run.app** (evento `ensayo`, país `GT`)
- Moderación: `/admin` en la misma URL (cuenta del presentador con `admin=true`)
- Vista del presentador: local, `http://127.0.0.1:3000/presenter` con `make up`

![App del público en un teléfono](docs/screenshots/audiencia.png)
