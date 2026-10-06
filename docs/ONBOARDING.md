# Genlingo — guía de puesta en marcha

Todo lo necesario para correr la demo, rehacer los datos, reentrenar a David y dar la charla. Para la visión general y los resultados, ver el [README](../README.md).

## 1. Requisitos

| Herramienta | Versión probada | Para qué |
| --- | --- | --- |
| macOS en Apple Silicon | macOS 26.6, M1 Max 64 GB | La laptop del escenario. 64 GB permiten `make train-finish` con E4B. |
| [uv](https://docs.astral.sh/uv/) | 0.8.22 | Python 3.12 del servicio del duelo, los scripts y los evals (`duel/.python-version`). |
| Node.js / npm | Node 24.21, npm 12 | Web (`web/`). La imagen de Cloud Run usa `node:24-slim`. |
| [Ollama](https://ollama.com) | 0.35.0 | David y EmbeddingGemma en la laptop. |
| Google Cloud SDK (`gcloud`) | 587.0.0 | ADC, buckets, Cloud Build, Cloud Run, Secret Manager. |
| Firebase CLI (`firebase`) | 15.6.0 | Emulador de Firestore para las pruebas de reglas y despliegue de reglas/índices. |
| JDK 21 | `brew install openjdk@21` | Solo para el emulador de Firestore. El `Makefile` lo busca en `$(brew --prefix openjdk@21)` y lo pone en `JAVA_HOME` solo dentro de `make test`; no hace falta cambiar el Java del sistema. |
| Chromium de Playwright | `@playwright/test` 1.63 | Ensayos `web/e2e/*.mjs`: `cd web && npx playwright install chromium`. |
| Android Studio + emulador (opcional) | Pixel con API 36 | Probar la app del público en Chrome de Android. |

## 2. Instalación local

```bash
git clone <este repo> genlingo && cd genlingo
cp .env.example .env                      # el Makefile y scripts/up.sh leen este archivo
(cd duel && uv sync)                      # crea duel/.venv con las dependencias de duel/uv.lock
(cd web && npm install && cp .env.example .env.local)
make test                                 # 85 pruebas de Python, 17 de Vitest, tsc, ESLint y 4 de reglas (falla si no puede correr web o reglas; SKIP_WEB=1 / SKIP_RULES=1 para omitirlas a propósito)
```

`.env` trae los valores reales del proyecto (`GOOGLE_CLOUD_PROJECT=ai-experiments-487722`, modelos, tarifas, buckets). No lleva secretos: la autenticación es ADC. `web/.env.local` sí lleva valores locales que no van al repo (token de depuración de App Check, credenciales de e2e).

### Modelos de Ollama

| Modelo | Cómo se obtiene | Para qué |
| --- | --- | --- |
| `embeddinggemma` | `ollama pull embeddinggemma` | Glosario del banco de términos (`EMBEDDING_MODEL`). Necesario en escena. |
| `genlingo-2026-10c-e2b-nomulti` y `-nomulti-f16` | `make pull-model TAG=genlingo-2026-10c-e2b-nomulti FP16=1` | David de escena (`LOCAL_MODEL_TAG`): Q5_K_M, 3.62 GB, prompt de léxico, entrenado y cuantizado en la nube (`make train` publica `QUANT` bajo el tag sin sufijo). El f16 es la referencia de compresión. |
| `genlingo-2026-10b-e2b` y `-e2b-f16` | `make pull-model TAG=genlingo-2026-10b-e2b FP16=1` | El David de la ronda 2 (prompt con glosario), en `DAVID_TAGS` para comparar las rondas de datos. |
| `genlingo-2026-10-e2b-q5_k_m` | `make pull-model TAG=genlingo-2026-10-e2b-q5_k_m` | David anterior (`DAVID_PREVIOUS_TAG`, lo precarga `make up`): Q5_K_M del barrido de cuantización de la ronda 1. |
| `genlingo-2026-10-e2b` y `-e2b-f16` | `make pull-model TAG=genlingo-2026-10-e2b FP16=1` | El David de 2026-10 en Q4 y f16, para el barrido de compresión (`make quant-sweep` parte del f16). |
| `genlingo-2026-09` | `make pull-model TAG=genlingo-2026-09` (agrega `FP16=1` para el eval de compresión) | David de 2026-09 (prompt básico), en `DAVID_TAGS` para mostrar la evolución. |
| `genlingo-2026-10-e4b` | `make pull-model TAG=genlingo-2026-10-e4b` (sin `FP16`: `make train-finish` publica solo el Q4) | Candidato E4B (agrégalo a `DAVID_TAGS` para evaluarlo; quedó fuera del eval final: 67 %, p50 836 ms). |
| `gemma4:e2b-it-qat`, `gemma4:e4b` | `ollama pull gemma4:e2b-it-qat`, `ollama pull gemma4:e4b` | Modelos base sin afinar (`BASE_MODEL_TAGS`) para `make eval`. |

`make pull-model` (`train/pull_model.sh`) copia de `gs://ai-experiments-487722-genlingo-models/<tag>/` el `Modelfile`, el GGUF que ese Modelfile nombra y `metrics.json` (más `Modelfile.f16` y el GGUF f16 con `FP16=1`) a `models/<tag>/` y corre `ollama create`. El Modelfile usa `RENDERER gemma4` / `PARSER gemma4` (`OLLAMA_RENDERER`), así que el modelo afinado recibe el prompt igual que su base.

### Credenciales: ADC

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project ai-experiments-487722   # opcional: infra/env.sh ya fija CLOUDSDK_CORE_PROJECT
```

Con ADC funcionan Goliath (Vertex AI, `google-genai`), la descarga de modelos, `make export`, `make reset` contra Firestore y el puente del público (`AUDIENCE_FEED=1`). No hay claves de API en el repo.

## 3. Google Cloud

Proyecto `ai-experiments-487722`. Las apps web corren en `us-central1`; el entrenamiento, en `europe-west4`.

### Recursos que los scripts dan por hechos

Los scripts de `infra/` no crean estos recursos; ya existen en el proyecto. Para montarlo en otro proyecto:

| Recurso | Valor actual |
| --- | --- |
| Artifact Registry (Docker) | `charlas2027` en `us-central1` |
| Bucket de staging (datos de entrenamiento, caché de pesos, adaptadores) | `gs://ai-experiments-487722-train-eu`, `EUROPE-WEST4` (misma región que la GPU) |
| Bucket de modelos (GGUF + Modelfile por tag) | `gs://ai-experiments-487722-genlingo-models`, `US-CENTRAL1` |
| Firestore | base `genlingo`, modo nativo, `nam5` |
| Firebase | app web «Genlingo audiencia»; proveedores de Auth anónimo y correo/contraseña habilitados |
| Cuota de GPU de Cloud Run | 1× NVIDIA L4 sin redundancia zonal en `europe-west4` |

Reglas e índices de Firestore (`web/firestore.rules`, `web/firestore.indexes.json`, base `genlingo` según `web/firebase.json`):

```bash
cd web && firebase deploy --only firestore --project ai-experiments-487722
```

### Token de Hugging Face en Secret Manager (`hf-token`)

Gemma 4 no es un modelo restringido, pero las descargas anónimas desde IPs de la nube pueden recibir 429. Si existe el secreto `hf-token`, el job lo lee al arrancar (`hf_token_from_secret_manager` en `train/train_lora.py`); si no existe, descarga de forma anónima. El token nunca vive en la imagen, en la definición del job ni en el repo.

```bash
printf '%s' "hf_..." | gcloud secrets create hf-token --data-file=- --replication-policy=automatic
# o, si ya existe:  printf '%s' "hf_..." | gcloud secrets versions add hf-token --data-file=-
```

Créalo **antes** de `infra/01-train-service-account.sh`: ese script le da acceso a la cuenta del job solo si el secreto ya existe. `make train-finish` usa el mismo secreto con tus credenciales. Alternativa sin Hugging Face: `GEMMA_WEIGHTS_URI=gs://vertex-model-garden-public-us/gemma4`.

### Scripts `infra/` en orden

Todos cargan `infra/env.sh` (proyecto, regiones, Artifact Registry) y `infra/app.env` (`APP=genlingo`). Son idempotentes.

| # | Script | Qué hace | Cuándo |
| --- | --- | --- | --- |
| 01 | `bash infra/01-train-service-account.sh` | Cuenta `genlingo-train`: `storage.objectAdmin` en los dos buckets, lectura de Artifact Registry y acceso a `hf-token` si existe. | Una vez. |
| 02 | `bash infra/02-train-image.sh` | Construye la imagen de entrenamiento con Cloud Build (`e2-highcpu-8`, ~15 min la primera vez). El tag es un hash de `Dockerfile` + `requirements.txt` + `train_lora.py` + `finish.py`: si no cambiaron, no reconstruye. Imprime la URI. | Lo llama `make train`. |
| 03 | `bash infra/03-train-job.sh` | Crea o actualiza dos Cloud Run Jobs en `europe-west4` con esa imagen: `genlingo-train` (1× L4, 8 vCPU, 32 GiB, tope de 1 h, `ADAPTER_ONLY=1`) y `genlingo-finish` (solo CPU, 8 vCPU, 32 GiB, comando `python /app/finish.py`, pesos base copiados del bucket a `/tmp/base` con una lectura secuencial, disco efímero de 10 GiB en `/mnt/scratch` para el GGUF f16). Los dos montan el bucket de staging en `/mnt/work` (caché de pesos base y adaptador). Sin reintentos. | Lo llama `make train`. |
| 04 | `bash infra/04-web-service-account.sh` | Cuenta `genlingo-web` con `datastore.user` limitado por condición de IAM a la base `genlingo`. | Lo llama `make deploy`. |
| 05 | `bash infra/05-deploy-web.sh` | Construye `web/` con Cloud Build y despliega el servicio `genlingo` (público, `min-instances=0`, `max-instances=10`, 1 vCPU, 512 MiB, concurrencia 200). Exige `FIREBASE_API_KEY` y `FIREBASE_APP_ID`; con `RECAPTCHA_SITE_KEY` activa `APP_CHECK_ENFORCE=1`. | Lo llama `make deploy`. |
| 06 | `bash infra/06-app-check.sh` | Llave de reCAPTCHA Enterprise para el dominio de Cloud Run + `localhost`, proveedor de App Check de la app web, token de depuración `e2e` y, con `ENFORCE_FIRESTORE=1`, App Check obligatorio en Firestore. | Una vez (antes de desplegar con App Check). |
| 60 | `bash infra/60-stage.sh on\|off` | `min-instances` 1 o 0 en el servicio `genlingo` y muestra el valor que quedó en Cloud Run. | Lo llaman `make stage-on` (día de charla) y `make stage-off` (después). |

Despliegue de un evento:

```bash
export FIREBASE_API_KEY=... FIREBASE_APP_ID=...          # config web pública de «Genlingo audiencia»
FIREBASE_APP_ID=$FIREBASE_APP_ID bash infra/06-app-check.sh   # imprime site key y, la primera vez, el token de depuración
EVENT_ID=gdg-guate-2027-03 EVENT_COUNTRY=GT RECAPTCHA_SITE_KEY=<site key> make deploy
```

> **La llave de navegador es solo de Genlingo.** La app web usa la llave `Browser key (auto created by Firebase)` (`FIREBASE_API_KEY`), restringida por referente HTTP a `https://genlingo-611681112050.us-central1.run.app/*`, `https://genlingo-z63pqhhmxq-uc.a.run.app/*`, `localhost`/`127.0.0.1` en los puertos 3000 y 3100, y a cinco APIs (Identity Toolkit, Secure Token, Firestore, App Check, Installations). Ninguna otra app del proyecto debe usarla: una app nueva crea su propia llave. Antes de cambiar llaves, App Check o IAM del proyecto, avisa a quien coordina las demos de `ai-experiments-487722`: son recursos compartidos. `web/e2e/appcheck-firestore.sh` manda el `Referer` de Cloud Run por esa restricción.

> **App Check en Firestore es por proyecto.** `ENFORCE_FIRESTORE=1` obliga a *todas* las apps cliente de *todas* las bases de Firestore de `ai-experiments-487722` a mandar tokens de App Check. El Admin SDK y el acceso por IAM no se ven afectados. Revisa las otras demos del proyecto antes de activarlo. `web/e2e/appcheck-firestore.sh` demuestra el efecto: sin token, 403; con token, 200.

### Tokens de depuración de App Check

Los navegadores automatizados y el Chrome del emulador no pasan reCAPTCHA, así que usan el token de depuración que `infra/06-app-check.sh` imprime una sola vez (`APPCHECK_DEBUG_TOKEN=...`). Guárdalo en `web/.env.local`. Nunca se despliega.

- **Playwright**: los scripts de `web/e2e/` leen `APPCHECK_DEBUG_TOKEN` del entorno y lo escriben en `localStorage` (`genlingo.appcheckDebug`) antes de cargar la página.

  ```bash
  cd web && set -a && source .env.local && set +a
  node e2e/audience-flow.mjs https://genlingo-611681112050.us-central1.run.app http://127.0.0.1:3000
  ```

- **Chrome del emulador de Android**: abre una vez `https://genlingo-611681112050.us-central1.run.app/#appcheck-debug=<token>`. `web/lib/client/firebase.ts` lo guarda en `localStorage`, limpia la URL y desde entonces ese navegador manda tokens válidos.

### Cuenta del presentador (`admin=true`)

`/admin` y `/api/admin/*` exigen el claim `admin=true` (o un correo verificado listado en `ADMIN_EMAILS`).

```bash
cd web
GOOGLE_CLOUD_PROJECT=ai-experiments-487722 node scripts/set-admin.mjs presentador@ejemplo.com
```

Si la cuenta no existe, la crea con una contraseña aleatoria que nadie ve; el presentador entra a `/admin`, pulsa «Olvidé mi contraseña» y define la suya. Para ensayos automatizados, `--password-out=.env.local` escribe `E2E_ADMIN_EMAIL` y `E2E_ADMIN_PASSWORD` en ese archivo.

## 4. Datos, entrenamiento y eval: la cadena completa

```bash
make test-set                 # 1. set de prueba desde oraciones reales, validado contra el banco (sin humanos)
make real-pairs               #    pares de entrenamiento anclados en oraciones reales
make export                   # 2. (si hubo público) pares aprobados en /admin -> data/pairs/human.jsonl
make pairs                    # 3. (opcional) regenerar los pares sintéticos con Gemini (~$0.71, ~10 min)
make train                    # 4. LoRA (L4) + merge y GGUF (CPU) en Cloud Run -> train/runs/genlingo-<año>-<mes>.json
make train-finish             # 5. (solo si falla el job de CPU) merge + GGUF en la laptop, mismo TAG
make pull-model TAG=genlingo-<año>-<mes> FP16=1   # 6. a Ollama
make eval                     # 7. evals/report.md (con DAVID_TAGS que incluya los tags nuevos)
```

`make train` sigue la receta del David de escena (`genlingo-2026-10c-e2b-nomulti`): sin los pares de varios términos (`--exclude synthetic_multi`) y sin la etapa ORPO, porque ninguno de los dos mejoró el set de desarrollo. Con los datos de hoy, `make train-data` da los mismos 2,271 ejemplos (1,715 sintéticos + 556 anclados en oraciones reales) que registra `train/runs/genlingo-2026-10c-e2b-nomulti.json`. Para repetir una variante descartada en una ablación: `MULTI=1` incluye `data/pairs/synthetic_multi.jsonl` y `ORPO=1` arma `data/train/pref.jsonl` y agrega la etapa de preferencias al job.

Qué pasa en cada paso:

1. **Set de prueba sin humanos.** `scripts/validate_test_set.py` valida cada par contra el banco de términos (la jerga del origen existe y se reemplaza, o la referencia usa jerga Gen Z del país; nada de otro país; longitud; sin solapes con entrenamiento) y lo marca `auto_validated` o `rejected` con el motivo. Las rondas `E` y el eval usan los `auto_validated`. `make real-pairs` arma pares de entrenamiento con la otra mitad de las oraciones reales de la segunda ronda de investigación.
2. **`make export`** lee `pairs` con `status == approved` de Firestore, los convierte en pares `origin=human` (procedencia: evento e id) y manda 20 % al split de prueba con un hash estable del id.
3. **`make counterparts`** y **`make pairs`**: `scripts/build_counterparts.py` arma la tabla de contrapartes validadas por significado (`data/counterparts.jsonl`: vecinos mutuos con coseno ≥ 0.65, o la elección de Gemini entre 5 candidatos confirmada por una palabra de significado compartida). `scripts/generate_pairs.py` genera los pares sintéticos: cada llamada nombra un término y, solo si la tabla la tiene, su contraparte; sin contraparte, el lado de papás dice el significado. Los pares llevan trampas de otro país como negativos difíciles; cada par se valida contra el banco y los rechazos se cuentan por motivo en `data/pairs/synthetic.meta.json`. `scripts/generate_multi_pairs.py` (pares que cambian 2–3 términos a la vez, `data/pairs/synthetic_multi.jsonl`) no entra en la receta de escena ni en `make pairs`: sus pares solo se usan en ablaciones con `MULTI=1`.
4. **`make train`** primero corre `make train-data` (`scripts/build_train_set.py`): renderiza los pares de entrenamiento con el prompt del duelo (estilo `lexicon` por defecto: país + léxico, con la respuesta en el glosario en el 85 % de los ejemplos) a `data/train/chat.jsonl`, sin los pares de varios términos, y anota el estilo y lo excluido en `chat.meta.json`; solo con `ORPO=1`, `scripts/build_pref_set.py` arma `data/train/pref.jsonl`, las frases de la etapa de preferencias (ORPO) del mismo job. Después `train/submit_job.py` sube el JSONL al bucket de staging, asegura la imagen (02) y el job (03), ejecuta `genlingo-train` (L4: entrena y guarda el adaptador en `gs://…-train-eu/genlingo/runs/<tag>/adapter`) y, si termina bien, `genlingo-finish` (CPU: `train/finish.py` fusiona, convierte a GGUF f16, cuantiza a `QUANT` y publica en el bucket de modelos con su `Modelfile`). Espera a los dos, calcula el costo de cada etapa y escribe `train/runs/<tag>.json` con duración, máquina, costo por etapa (`stages`) y total, métricas y `prompt_style`. `QUANT=Q5_K_M` y `KEEP_F16=1` vienen de `.env`. `TAG` lleva la fecha de los datos, no la del entrenamiento: por defecto `genlingo-<año>-<mes>` del día; si el mes ya tiene una versión de datos, agrega una letra (`genlingo-2026-10b`). Usa el sufijo de la base (`-e2b`, `-e4b`) cuando compares bases.
5. **`make train-finish`** (respaldo, `train/finish_local.py`) corre el mismo `train/finish.py` en la laptop: baja el adaptador de `gs://…-train-eu/genlingo/runs/<tag>/adapter`, fusiona en bf16, convierte con llama.cpp `b11292` (`train/setup_llama_cpp.sh` lo descarga en `train/.llama.cpp`), cuantiza a `QUANT` (y deja el f16 con `KEEP_F16=1`), publica en el bucket de modelos y agrega un bloque `finish` al run file. Úsalo si `genlingo-finish` falla (el adaptador ya está en el bucket, no hay que reentrenar) y para E4B, cuyo checkpoint fusionado de 16 GB no cabe en los 32 GiB del job de CPU. Necesita ~40 GB libres en disco.
6. **`make pull-model`**: ver la tabla de modelos de Ollama.
7. **`make eval`** (`evals/run_eval.py`): modelos base (`BASE_MODEL_TAGS`, el primero también con glosario), cada David de `DAVID_TAGS` con el prompt con que se entrenó (más su `-f16` si está en Ollama), y Goliath con y sin glosario. Los modelos locales se precalientan y corren de a uno, a temperatura 0. Los resultados por frase quedan en `evals/results/<fecha>.json` y el reporte en `evals/report.md`. El reporte elige al David de escena: el archivo más pequeño a ≤ 2 puntos del f16 en jerga resuelta, con p50 < 1 s (sección «Compresión»). `make quant-sweep TAG=…` construye Q5_K_M, Q6_K, Q8_0 y Q4/Q5 calibrados con imatrix (sobre pares de entrenamiento) para ese barrido.

Después del eval, actualiza `.env`: `LOCAL_MODEL_TAG` (el David de la página de comparación), `DAVID_PREVIOUS_TAG` (el David anterior, que `make up` precarga) y `DAVID_TAGS`. Si cambia el David, vuelve a verificar los ejemplos de `data/translate_examples.json` (3 veces en vivo con los dos modelos) y corre `make preflight`.

## 5. La página de comparación, sin internet

```bash
make up
```

`scripts/up.sh` (sin Ollama con `MOCK_AI=1`) arranca `ollama serve` (con `OLLAMA_MAX_LOADED_MODELS=4`) si no está corriendo, comprueba que `LOCAL_MODEL_TAG` y `DAVID_PREVIOUS_TAG` existan en Ollama, precarga los dos Davids y EmbeddingGemma (`keep_alive` 2 h), levanta el servicio del duelo en `127.0.0.1:8787` y la vista del presentador de la versión anterior (`127.0.0.1:3000`), y abre la página de comparación `http://127.0.0.1:8787/traducir`. Si algo falla, dice qué y en qué línea en vez de salir en silencio.

En la página se elige la dirección, se escribe una frase o se toca un ejemplo, y David y Goliath traducen al mismo tiempo; cada columna muestra su traducción, su tiempo y su costo. En los ejemplos aparece también la traducción de referencia y un ✓/✗ por término de jerga. `Enter` en el cuadro de texto traduce. El país es `EVENT_COUNTRY` (`GT` por defecto: la charla es en Guatemala).

Para ensayar «Wi-Fi apagado» sin tocar el sistema operativo, pon `FORCE_OFFLINE=1` en `.env` y reinicia `make up`: el indicador dice «Sin internet · David sigue», la columna de Goliath dice «Sin conexión» y David sigue respondiendo. Con `MOCK_AI=1` no hacen falta ni Ollama ni red.

`scripts/up.sh` carga `.env` con `set -a; source .env`, así que una variable que esté en `.env` gana sobre la que pongas delante de `make up`. Cambia las opciones (`FORCE_OFFLINE`, `EVENT_COUNTRY`) en `.env`.

## 6. La versión anterior de la demo: vista del presentador y app del público

La charla ya no las usa, pero siguen en el repositorio y funcionando: la vista del presentador (`http://127.0.0.1:3000/presenter`) con rondas, marcador y votos, y la app del público en Cloud Run (frases y votos desde el teléfono, moderación en `/admin`).

- **Teclas de la vista:** `E` ronda del set de prueba, `G` ronda de slang chapín (orden fijo con `SPECIALTY_SEED`), `Enter` siguiente frase del público, `/` escribir una frase, `V` cerrar la votación, `M` alternar con el David anterior, `F` pantalla completa.
- **El público:** con `AUDIENCE_FEED=1` y el mismo `EVENT_ID` que Cloud Run, `audience_feed.py` recibe las frases aprobadas por un listener de Firestore y publica cada ronda en `rounds/{id}`; los votos se cuentan en `rounds/{id}/votes`. En el emulador, la app se abre con el token de depuración: `https://genlingo-611681112050.us-central1.run.app/#appcheck-debug=<token>`.
- **Ensayos automatizados:** `node e2e/emulator-round.mjs <webUrl> <presenterUrl> "<frase>"` (aprueba una frase en `/admin`, abre la ronda y espera el voto del emulador) y `node e2e/audience-flow.mjs <webUrl> <presenterUrl>` (cuatro teléfonos simulados).

## 7. Recorrido por el código: una traducción en la página

1. **La página** (`duel/genlingo_duel/static/traducir.html`, servida en `GET /traducir` con sus tipografías en `/traducir/fonts/`). Al pulsar **Traducir** o un ejemplo, llama a la vez `POST /translate/david` y `POST /translate/goliath` con frase, dirección y, si es un ejemplo, su `example_id`; cada columna se llena cuando llega su respuesta, con un cronómetro mientras espera.
2. **API** (`duel/genlingo_duel/main.py`). Cada ruta llama `arena.translate_one(side, ...)`; nada se registra. Los ejemplos salen de `GET /translate/examples` (`translate_page.py`, que lee `data/translate_examples.json`).
3. **Prompt por lado** (`arena.py`). `prompt_style_for` lee el run file del tag (`runs.py` quita sufijos como `-f16` o `-q5_k_m` hasta encontrarlo) para saber con qué prompt se entrenó David; Goliath usa `GOLIATH_PROMPT_STYLE` (`country`, sin glosario). Con el estilo `lexicon`, `glossary.py` arma 6 entradas: cada término de la generación de origen que aparece en la frase con su contraparte validada (`terms.py`; `data/counterparts.jsonl`), los de la otra generación más cercanos por coseno con EmbeddingGemma y uno de otro país marcado «NO de aquí». Con `DAVID_NBEST` > 1, `rerank.py` pide N respuestas en paralelo y el banco elige. `prompts.py` arma los mensajes.
4. **¿Hay red?** (`duel_core/connectivity.py`). Solo para Goliath: una conexión TCP a `aiplatform.googleapis.com:443` con 0.8 s de tope, en caché 3 s. Sin red, Goliath vuelve `offline` sin llamarlo.
5. **La llamada** (`duel_core/duel.py`). David va por `ollama_client.py` (`/api/chat`, sin streaming, `think: false`, temperatura 0.2); Goliath por `gemini_client.py` (Vertex AI, ADC, timeout 20 s; los tokens de razonamiento cuentan como salida). Un error no tumba la página: el lado que falla dice «No respondió».
6. **Medición** (`duel.py`, `cost.py`). `clean_translation` deja la primera línea sin etiquetas ni comillas; el costo usa `PriceSchedule.at()` (tarifa vigente hoy). El tiempo de recuperación del glosario se suma a la latencia de David.
7. **Revisión por término** (`term_check.py`). Solo para ejemplos: las reglas de la *jerga correcta* del eval, un término a la vez, con la referencia del ejemplo; la página muestra ✓ o ✗ por término.

## 8. Ensayar y probar

- `make test`: todo sin red (`MOCK_AI=1`).
- `make preflight`: abre la página y traduce cada ejemplo en vivo con los dos modelos (David tiene que acertar la jerga y Goliath no).
- `web/e2e/demo-shots.mjs [duelBase] [outDir] [online|offline]`: las capturas de `docs/demo/` desde la página.
- `web/e2e/shots.mjs` y `web/e2e/audience-flow.mjs`: capturas y ensayos de la versión anterior (vista del presentador y app del público).
- `web/e2e/appcheck-firestore.sh`: prueba la exigencia de App Check en Firestore.

## 9. Problemas frecuentes

| Síntoma | Causa y solución |
| --- | --- |
| `make up` dice «… no está en Ollama» | Ese tag no está registrado: `make pull-model TAG=` con el tag que nombra el mensaje. |
| La latencia de David sube a 2–3 s y la del glosario a ~850 ms | Ollama está descargando y recargando modelos. `make up` pide `OLLAMA_MAX_LOADED_MODELS=4`, pero solo aplica si `make up` arrancó Ollama (si ya corría, configúralo allí); cualquier otro modelo (otra demo, un `make eval`) puede desalojar alguno. Revisa con `ollama ps` y descarga lo que sobre con `curl http://127.0.0.1:11434/api/generate -d '{"model":"<modelo>","keep_alive":0}'`. |
| La página dice «El servicio no responde» | El servicio del duelo no corre: `make up`. |
| La columna de David dice «No respondió» | Ollama no corre o no tiene a David: `ollama ps` y `make up` otra vez. |
| Goliath dice «Sin conexión» con internet | `FORCE_OFFLINE=1` en `.env`, o no hay salida TCP a `aiplatform.googleapis.com:443` (VPN, proxy, red del evento). |
| Goliath dice «No respondió» | ADC vencido (`gcloud auth application-default login`) o un timeout de 20 s. |
| `make preflight` dice que Goliath también acertó un ejemplo | Goliath varía de una llamada a otra. Repite `make preflight`; si vuelve a pasar, ese ejemplo ya no muestra la diferencia: quítalo de `data/translate_examples.json`. |
| `make test` falla con «Firestore rules tests can't run» | Falta JDK 21 (`brew install openjdk@21`) o `web/node_modules` (`cd web && npm install`). `SKIP_RULES=1` las omite a propósito. |
| `make test` falla con «Could not start Firestore Emulator, port taken» | Otro emulador de Firestore usa el puerto 8080; ciérralo o espera a que termine. |
| `genlingo-finish` muere con «memory limit was reached» | Base demasiado grande para fusionar en 32 GiB (E4B). El adaptador ya está en el bucket: termina con `make train-finish` y el mismo `TAG`. |
| `make train-finish` falla con «No space left on device» | Fusionar E2B ocupa ~10 GB y el GGUF f16 otros ~9 GB. Borra `models/.work/<tag>/merged` y GGUF viejos de `models/` (Ollama guarda su propia copia). |
| `make train` falla al descargar pesos con 429 | Descargas anónimas de Hugging Face desde la nube. Crea `hf-token` en Secret Manager y vuelve a correr `infra/01-train-service-account.sh`. |

## 10. Lista para el día de la charla

**El día anterior**

- [ ] `make test` en verde.
- [ ] `ollama list` muestra `LOCAL_MODEL_TAG`, `DAVID_PREVIOUS_TAG` y `embeddinggemma`.

**En el lugar, antes de abrir la sala**

- [ ] ADC vigente: `gcloud auth application-default print-access-token`.
- [ ] `make up` en una terminal; la página de comparación en el proyector, en Chrome a pantalla completa.
- [ ] En otra terminal, `make stage-on && make warmup && make preflight`. `warmup` carga los modelos y hace una llamada a cada uno; `preflight` traduce cada ejemplo con los dos y tiene que terminar en «preflight ok» (cada `[FALLA]` dice cómo arreglarlo). `stage-on` solo hace falta porque `preflight` también revisa la app del público. Cierra cualquier otro cliente de Ollama: `ollama ps` debe mostrar solo los dos Davids y EmbeddingGemma.
- [ ] Prueba con Wi-Fi apagado: apaga el Wi-Fi, espera «Sin internet · David sigue» (la página consulta cada 3 s), toca un ejemplo: David responde y Goliath dice «Sin conexión». Vuelve a encender el Wi-Fi y espera «En línea».
- [ ] La laptop no se duerme (`caffeinate -d` en otra terminal) y está conectada a la corriente.

**Después de la charla**

- [ ] `make stage-off`: la app del público vuelve a `min-instances=0` y deja de cobrar en reposo.
