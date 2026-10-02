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
make test                                 # 55 pruebas de Python, 12 de Vitest, tsc, ESLint y 4 de reglas
```

`.env` trae los valores reales del proyecto (`GOOGLE_CLOUD_PROJECT=ai-experiments-487722`, modelos, tarifas, buckets). No lleva secretos: la autenticación es ADC. `web/.env.local` sí lleva valores locales que no van al repo (token de depuración de App Check, credenciales de e2e).

### Modelos de Ollama

| Modelo | Cómo se obtiene | Para qué |
| --- | --- | --- |
| `embeddinggemma` | `ollama pull embeddinggemma` | Glosario del banco de términos (`EMBEDDING_MODEL`). Necesario en escena. |
| `genlingo-2026-10-e2b-q5_k_m` | `make pull-model TAG=genlingo-2026-10-e2b-q5_k_m` | David de escena (`LOCAL_MODEL_TAG`): Q5_K_M, 3.62 GB, elegido por el barrido de cuantización. |
| `genlingo-2026-10-e2b` y `-e2b-f16` | `make pull-model TAG=genlingo-2026-10-e2b FP16=1` | El mismo David en Q4 y f16, para el eval de compresión (`make quant-sweep` parte del f16). |
| `genlingo-2026-09` | `make pull-model TAG=genlingo-2026-09` (agrega `FP16=1` para el eval de compresión) | David del mes pasado (`DAVID_PREVIOUS_TAG`, tecla `M`). |
| `genlingo-2026-10-e4b` | `make pull-model TAG=genlingo-2026-10-e4b` (sin `FP16`: `make train-finish` publica solo el Q4) | Candidato E4B para `make eval`. |
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
| 02 | `bash infra/02-train-image.sh` | Construye la imagen de entrenamiento con Cloud Build (`e2-highcpu-8`, ~15 min la primera vez). El tag es un hash de `Dockerfile` + `requirements.txt` + `train_lora.py`: si no cambiaron, no reconstruye. Imprime la URI. | Lo llama `make train`. |
| 03 | `bash infra/03-train-job.sh` | Crea o actualiza el Cloud Run Job `genlingo-train` en `europe-west4`: 1× L4, 8 vCPU, 32 GiB, tope de 1 h, sin reintentos, volumen del bucket de staging en `/mnt/work`, salidas en el disco en memoria. | Lo llama `make train`. |
| 04 | `bash infra/04-web-service-account.sh` | Cuenta `genlingo-web` con `datastore.user` limitado por condición de IAM a la base `genlingo`. | Lo llama `make deploy`. |
| 05 | `bash infra/05-deploy-web.sh` | Construye `web/` con Cloud Build y despliega el servicio `genlingo` (público, `min-instances=1`, `max-instances=10`, 1 vCPU, 512 MiB, concurrencia 200). Exige `FIREBASE_API_KEY` y `FIREBASE_APP_ID`; con `RECAPTCHA_SITE_KEY` activa `APP_CHECK_ENFORCE=1`. | Lo llama `make deploy`. |
| 06 | `bash infra/06-app-check.sh` | Llave de reCAPTCHA Enterprise para el dominio de Cloud Run + `localhost`, proveedor de App Check de la app web, token de depuración `e2e` y, con `ENFORCE_FIRESTORE=1`, App Check obligatorio en Firestore. | Una vez (antes de desplegar con App Check). |

Despliegue de un evento:

```bash
export FIREBASE_API_KEY=... FIREBASE_APP_ID=...          # config web pública de «Genlingo audiencia»
FIREBASE_APP_ID=$FIREBASE_APP_ID bash infra/06-app-check.sh   # imprime site key y, la primera vez, el token de depuración
EVENT_ID=gdg-guate-2027-03 EVENT_COUNTRY=GT RECAPTCHA_SITE_KEY=<site key> make deploy
```

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
make export                   # 2. pares del público aprobados en /admin -> data/pairs/human.jsonl (+ datasheet)
make pairs                    # 3. (opcional) regenerar los pares sintéticos con Gemini (~$0.80, 6 min)
make train TAG=genlingo-2026-11-e2b                        # 4. LoRA en Cloud Run (L4) -> train/runs/<tag>.json
make train TAG=genlingo-2026-11-e4b GEMMA_BASE_MODEL=gemma-4-E4B-it TRAIN_ARGS=--adapter-only
make train-finish TAG=genlingo-2026-11-e4b                 # 5. E4B: merge + GGUF en la laptop
make pull-model TAG=genlingo-2026-11-e2b FP16=1            # 6. a Ollama
make eval                     # 7. evals/report.md (con DAVID_TAGS que incluya los tags nuevos)
```

Qué pasa en cada paso:

1. **Set de prueba sin humanos.** `scripts/validate_test_set.py` valida cada par contra el banco de términos (la jerga del origen existe y se reemplaza, o la referencia usa jerga Gen Z del país; nada de otro país; longitud; sin solapes con entrenamiento) y lo marca `auto_validated` o `rejected` con el motivo. Las rondas `E` y el eval usan los `auto_validated`. `make review-test` queda como pasada humana opcional, y sus decisiones mandan sobre las automáticas. `make real-pairs` arma pares de entrenamiento con la otra mitad de las oraciones reales de la segunda ronda de investigación.
2. **`make export`** lee `pairs` con `status == approved` de Firestore, los convierte en pares `origin=human` (procedencia: evento e id) y manda 20 % al split de prueba con un hash estable del id.
3. **`make pairs`** (`scripts/generate_pairs.py`, `pairs-v3`): cada llamada nombra un término y su contraparte de la otra generación, del mismo país (contrapartes encontradas con EmbeddingGemma), con trampas de otro país como negativos difíciles. Cada par se valida contra el banco y los rechazos se cuentan por motivo en `data/pairs/synthetic.meta.json`.
4. **`make train`** primero corre `make train-data` (`scripts/build_train_set.py`): renderiza los pares aprobados con el prompt del duelo (`v2+glossary` por defecto) a `data/train/chat.jsonl` y anota el estilo en `chat.meta.json`. Después `train/submit_job.py` sube el JSONL al bucket de staging, asegura la imagen (02) y el job (03), lanza `gcloud run jobs execute` con los argumentos de `train_lora.py`, espera, calcula el costo y escribe `train/runs/<tag>.json` con duración, máquina, costo, métricas y `prompt_style`. `TAG` por defecto es `genlingo-<año>-<mes>`; usa el sufijo de la base (`-e2b`, `-e4b`) cuando compares bases.
5. **`make train-finish`** (`train/finish_local.py`) baja el adaptador de `gs://…-train-eu/genlingo/runs/<tag>/adapter`, fusiona en bf16, convierte con llama.cpp `b11292` (`train/setup_llama_cpp.sh` lo descarga en `train/.llama.cpp`), cuantiza a Q4_K_M, publica en el bucket de modelos y agrega un bloque `finish` al run file. Hace falta porque fusionar E4B no cabe en los 32 GiB del job.
6. **`make pull-model`**: ver la tabla de modelos de Ollama.
7. **`make eval`** (`evals/run_eval.py`): modelos base (`BASE_MODEL_TAGS`, el primero también con glosario), cada David de `DAVID_TAGS` con el prompt con que se entrenó (más su `-f16` si está en Ollama), y Goliath con y sin glosario. Los modelos locales se precalientan y corren de a uno, a temperatura 0. Los resultados por frase quedan en `evals/results/<fecha>.json` y el reporte en `evals/report.md`. El reporte elige al David de escena: el archivo más pequeño a ≤ 2 puntos del f16 en jerga resuelta, con p50 < 1 s (sección «Compresión»). `make quant-sweep TAG=…` construye Q5_K_M, Q6_K, Q8_0 y Q4/Q5 calibrados con imatrix (sobre pares de entrenamiento) para ese barrido.

Después del eval, actualiza `.env`: `LOCAL_MODEL_TAG` (David de escena), `DAVID_PREVIOUS_TAG` (el del mes anterior) y `DAVID_TAGS`.

## 5. Correr el duelo sin internet

```bash
make up
```

`scripts/up.sh` arranca `ollama serve` (con `OLLAMA_MAX_LOADED_MODELS=4`) si no está corriendo, comprueba que `LOCAL_MODEL_TAG` y `DAVID_PREVIOUS_TAG` existan en Ollama, precarga exactamente los tres modelos de escena (los dos Davids y EmbeddingGemma, `keep_alive` 2 h), levanta el servicio del duelo en `127.0.0.1:8787` y la vista del presentador (`next start` en `127.0.0.1:3000`, recompilada si cambió algo en `web/` desde el último build) y abre `http://127.0.0.1:3000/presenter`. La charla entera funciona sin público: rondas `E` (set de prueba) y frases escritas con `/`.

Teclas de la vista del presentador:

| Tecla | Acción |
| --- | --- |
| `E` | Ronda de evaluación: frase del set de prueba sin usar, con referencia y chrF++ en vivo. |
| `Enter` / `N` / `AvPág` | Siguiente frase aprobada del público. |
| `/` | Escribir una frase (el botón alterna la dirección; `Esc` cancela). Usa el país `EVENT_COUNTRY`. |
| `V` | Cerrar la votación de la ronda del público. |
| `M` | Alternar entre el David de este mes y el del mes pasado (`DAVID_PREVIOUS_TAG`). |
| `F` | Pantalla completa. |

Para ensayar «Wi-Fi apagado» sin tocar el sistema operativo, pon `FORCE_OFFLINE=1` en `.env` y reinicia `make up`: el indicador pasa a «Sin conexión», Goliath aparece desconectado y David sigue respondiendo. Con `MOCK_AI=1` no hacen falta ni Ollama ni red.

`scripts/up.sh` carga `.env` con `set -a; source .env`, así que una variable que esté en `.env` gana sobre la que pongas delante de `make up`. Cambia las opciones de escena (`FORCE_OFFLINE`, `AUDIENCE_FEED`, `ALLOW_UNREVIEWED_TEST`, `EVENT_ID`) en `.env`.

## 6. El flujo del público en el Chrome del emulador

1. En `.env`: `AUDIENCE_FEED=1` y el mismo `EVENT_ID` que tiene desplegado Cloud Run (hoy `ensayo`). Luego `make up`.
2. En el emulador, abre la app con el token de depuración: `https://genlingo-611681112050.us-central1.run.app/#appcheck-debug=<token>`.
3. En el teléfono: «Reta a los modelos» → dirección → frase → «Enviar». La frase queda pendiente (una cada 20 s por persona, máximo 30 palabras, blocklist).
4. En `/admin` (cuenta del presentador): «Aprobar». `audience_feed.py` la recibe por un listener de Firestore (con sondeo cada 2 s de respaldo) y aparece como «Siguiente del público» en la vista del presentador; el presupuesto es menos de 3 s.
5. En la vista del presentador: `Enter`. El duelo publica la ronda en Firestore (`rounds/{id}`, `status: voting`); el teléfono muestra «Votar por David» / «Votar por Goliath».
6. Vota en el teléfono; la vista del presentador muestra «Votos en vivo». `V` cierra la ronda, lee el conteo de `rounds/{id}/votes` y decide al ganador.

Para automatizar el lado del presentador mientras el emulador hace de público:

```bash
cd web && set -a && source .env.local && set +a
node e2e/emulator-round.mjs https://genlingo-611681112050.us-central1.run.app http://127.0.0.1:3000 "la frase que mandaste desde el emulador"
```

El script entra a `/admin` con `E2E_ADMIN_EMAIL` / `E2E_ADMIN_PASSWORD`, aprueba la frase, mide aprobación → pantalla, abre la ronda y espera el voto del emulador. Con varios teléfonos simulados: `node e2e/audience-flow.mjs <webUrl> <presenterUrl>`.

## 7. Recorrido por el código: una ronda del duelo

1. **Vista del presentador** (`web/components/presenter/PresenterApp.tsx`). `Enter` toma la primera frase de la cola (la vista consulta `GET /queue` cada segundo) y llama `DuelClient.duel()` (`duelClient.ts`) con frase, dirección, país, `phrase_id` y el `david_tag` activo (el de `M`).
2. **API** (`duel/genlingo_duel/main.py`). `POST /duel` valida el país y llama `run_round`, que decide el tipo de ronda (con referencia es evaluación; sin ella, del público) y llama `arena.duel(...)`.
3. **Prompt por contendiente** (`arena.py`). `prompt_style_for` lee `train/runs/<tag>.json` (sin el sufijo `-f16`) para saber con qué prompt se entrenó ese David; Goliath usa `GOLIATH_PROMPT_STYLE` (`v2`). Si alguno usa `v2+glossary`, `glossary.py` recupera 4 entradas del banco del país y LATAM: términos de la generación de origen que aparecen en la frase (`terms.py`, coincidencia tolerante a inflexiones) y, si faltan, los de la otra generación más cercanos por coseno con EmbeddingGemma. `prompts.py` arma los mensajes.
4. **¿Hay red?** (`duel_core/connectivity.py`). Una conexión TCP a `aiplatform.googleapis.com:443` con 0.8 s de tope, en caché 3 s. Esperar un timeout HTTP congelaría el escenario.
5. **Duelo en paralelo** (`duel_core/duel.py`). `run_duel` lanza ambos contendientes con `asyncio.gather`. A Goliath sin red se le marca `offline` sin llamarlo; un error de red se convierte en `offline` y cualquier otro error en `error`, sin tumbar la ronda. David va por `ollama_client.py` (`/api/chat`, sin streaming, `think: false`, temperatura 0.2); Goliath por `gemini_client.py` (Vertex AI, ADC, timeout 20 s; los tokens de razonamiento cuentan como salida).
6. **Medición** (`duel.py`, `cost.py`, `metrics.py`). `clean_translation` deja la primera línea sin etiquetas ni comillas; el costo usa `PriceSchedule.at()` (tarifa vigente hoy) y guarda qué tarifa usó; si hay referencia, se calcula chrF++ de oración. La arena suma el tiempo de recuperación del glosario a la latencia de quien lo usó y registra el prompt y los términos del glosario.
7. **Marcador** (`scoreboard.py`). `record_round` guarda la ronda en SQLite. En evaluación gana el chrF++ más alto (empate si la diferencia es menor a 0.5); si un lado no respondió, gana el otro; en rondas del público el ganador queda pendiente del voto.
8. **Hacia los teléfonos** (`audience_feed.py`). Con `AUDIENCE_FEED=1`, `publish_round` escribe `rounds/{id}` en Firestore y `mark_shown` marca la frase como mostrada. La vista consulta `GET /rounds/{id}/votes` cada 1.5 s; `V` llama `POST /rounds/{id}/close`, que cuenta los votos, cierra la ronda en Firestore y fija el ganador.

## 8. Ensayar y probar

- `make test`: todo sin red (`MOCK_AI=1`).
- `web/e2e/shots.mjs [baseUrl] [outDir]`: capturas del presentador, del teléfono y de `/admin`.
- `web/e2e/audience-flow.mjs`: cuatro teléfonos simulados, moderación, ronda, votos y cierre.
- `web/e2e/appcheck-firestore.sh`: prueba la exigencia de App Check en Firestore.

## 9. Problemas frecuentes

| Síntoma | Causa y solución |
| --- | --- |
| `make up` dice «… no está en Ollama» | Ese tag no está registrado: `make pull-model TAG=…`. |
| La latencia de David sube a 2–3 s y la del glosario a ~850 ms | Ollama está descargando y recargando modelos. `make up` pide `OLLAMA_MAX_LOADED_MODELS=4`, pero solo aplica si `make up` arrancó Ollama (si ya corría, configúralo allí); cualquier otro modelo (otra demo, un `make eval`) puede desalojar alguno. Revisa con `ollama ps` y descarga lo que sobre con `curl http://127.0.0.1:11434/api/generate -d '{"model":"<modelo>","keep_alive":0}'`. |
| La primera ronda con `M` tarda varios segundos | El David del mes pasado no estaba cargado. Precaliéntalo (ver la lista del día de la charla). |
| `E` muestra «No quedan frases de prueba para esa combinación» | Ya se usaron todos los pares `auto_validated` de esa combinación (o falta `make test-set`). `make reset` libera las ya usadas. |
| Goliath aparece «sin conexión» con internet | `FORCE_OFFLINE=1` en `.env`, o no hay salida TCP a `aiplatform.googleapis.com:443` (VPN, proxy, red del evento). |
| Goliath da error en vez de traducir | ADC vencido: `gcloud auth application-default login`. Un timeout de 20 s se muestra como error, no como «sin conexión». |
| El teléfono dice «Falta la verificación de la app» o la API responde 401 | App Check: navegador sin reCAPTCHA válido. En automatización y emulador, usa el token de depuración (sección 3). |
| Una frase aprobada no llega a la pantalla | `AUDIENCE_FEED=0` o `EVENT_ID` distinto entre `.env` y Cloud Run. `GET http://127.0.0.1:8787/health` muestra `audience_feed`, `event` y `feed_last_sync`. |
| El teléfono muestra una ronda vieja de un ensayo | El teléfono muestra la última ronda del evento. `make reset` con `AUDIENCE_FEED=1` y red borra las rondas del evento; o usa un `EVENT_ID` nuevo por evento. |
| `make test` omite las reglas de Firestore | Falta JDK 21 (`brew install openjdk@21`) o `web/node_modules`. |
| El job de entrenamiento muere con «memory limit was reached» | Base demasiado grande para fusionar en 32 GiB. Usa `TRAIN_ARGS=--adapter-only` y termina con `make train-finish`. |
| `make train` falla al descargar pesos con 429 | Descargas anónimas de Hugging Face desde la nube. Crea `hf-token` en Secret Manager y vuelve a correr `infra/01-train-service-account.sh`. |

## 10. Lista para el día de la charla

**El día anterior**

- [ ] Set de prueba validado: `make test-set` (sin intervención humana).
- [ ] `make eval`; actualiza las cifras de la charla con `evals/report.md`.
- [ ] Evento: `EVENT_ID` y `EVENT_COUNTRY` nuevos en `.env` y desplegados (`EVENT_ID=… EVENT_COUNTRY=… RECAPTCHA_SITE_KEY=… make deploy`); `AUDIENCE_FEED=1`.
- [ ] `make test` en verde.
- [ ] `ollama list` muestra `LOCAL_MODEL_TAG`, `DAVID_PREVIOUS_TAG` y `embeddinggemma`.

**En el lugar, antes de abrir la sala**

- [ ] ADC vigente: `gcloud auth application-default print-access-token`.
- [ ] `make up`; la vista en el proyector a 1920×1080, `F` para pantalla completa.
- [ ] Precalentamiento: una ronda escrita (`/`) en cada dirección con el David de escena, `M` y una ronda con el del mes pasado, `M` de vuelta. `ollama ps` debe mostrar solo David, EmbeddingGemma y el David del mes pasado; cierra cualquier otro cliente de Ollama.
- [ ] Prueba con Wi-Fi apagado: apaga el Wi-Fi, espera «Sin conexión» (la vista consulta cada 3 s), escribe una frase: David responde en menos de 1 s y Goliath aparece desconectado. Vuelve a encender el Wi-Fi y espera «En línea».
- [ ] (Opcional, si hay público) escanea el QR, manda una frase y comprueba que llegue a la pantalla en menos de 3 s (con `AUTO_APPROVE_PHRASES=1` no hace falta aprobarla).
- [ ] `make reset` con red (pone en cero el marcador local y borra las rondas del evento en Firestore).
- [ ] La laptop no se duerme (`caffeinate -d` en otra terminal) y está conectada a la corriente.
