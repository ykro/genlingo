# Genlingo — guía de puesta en marcha

Todo lo necesario para desplegar la demo, rehacer los datos, reentrenar a David y evaluarlo. Todo corre en Google Cloud: la laptop solo manda los trabajos y abre la página. Para la visión general y los resultados, ver el [README](../README.md).

## 1. Requisitos

| Herramienta | Versión probada | Para qué |
| --- | --- | --- |
| [uv](https://docs.astral.sh/uv/) | 0.8.22 | Python 3.12 de la página, los scripts de datos y el eval (`duel/.python-version`). |
| Google Cloud SDK (`gcloud`) | 587.0.0 | ADC, buckets, Cloud Build, Cloud Run, Secret Manager. |
| Chromium de Playwright (opcional) | el que instala `uv run --with playwright` | Solo para `make screenshots`. |

No hace falta Ollama, Docker ni GPU en la laptop: las imágenes se construyen con Cloud Build y los modelos corren en Cloud Run.

## 2. Instalación

```bash
git clone <este repo> genlingo && cd genlingo
cp .env.example .env              # el Makefile lee este archivo
(cd duel && uv sync)              # crea duel/.venv con las dependencias de duel/uv.lock
make test                         # pruebas sin red (MOCK_AI=1)
```

`.env` trae los valores reales del proyecto (`GOOGLE_CLOUD_PROJECT=ai-experiments-487722`, modelos, tarifas, buckets). No lleva secretos: la autenticación es ADC.

### Credenciales: ADC

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project ai-experiments-487722   # opcional: infra/env.sh ya fija CLOUDSDK_CORE_PROJECT
```

Con ADC funcionan los despliegues, los jobs y los scripts de datos que llaman a Gemini. Los scripts que usan el modelo de embeddings (`make train-data`) llaman al servicio privado de David con `gcloud auth print-identity-token`: tu cuenta necesita `roles/run.invoker` en `genlingo-david` (la tiene quien es dueño del proyecto) y `DAVID_URL` en `.env`. No hay claves de API en el repo.

## 3. Google Cloud

Proyecto `ai-experiments-487722`. La página corre en `us-central1`; David, el entrenamiento y el eval, en `europe-west4` (ahí está la cuota de GPU L4).

### Recursos que los scripts dan por hechos

| Recurso | Valor actual |
| --- | --- |
| Artifact Registry (Docker) | `charlas2027` en `us-central1` (página, entrenamiento) y en `europe-west4` (David y eval; `infra/04-david.sh` lo crea si falta) |
| Bucket de staging (datos de entrenamiento, caché de pesos, adaptadores, reportes del eval) | `gs://ai-experiments-487722-train-eu`, `EUROPE-WEST4` |
| Bucket de modelos (GGUF + Modelfile por tag) | `gs://ai-experiments-487722-genlingo-models`, `US-CENTRAL1` |
| Cuota de GPU de Cloud Run | NVIDIA L4 sin redundancia zonal en `europe-west4` (4 en el proyecto, compartidas con otras demos) |

### Token de Hugging Face en Secret Manager (`hf-token`)

Gemma 4 no es un modelo restringido, pero las descargas anónimas desde IPs de la nube pueden recibir 429. Si existe el secreto `hf-token`, el job de entrenamiento lo lee al arrancar (`hf_token_from_secret_manager` en `train/train_lora.py`); si no existe, descarga de forma anónima. El token nunca vive en la imagen, en la definición del job ni en el repo.

```bash
printf '%s' "hf_..." | gcloud secrets create hf-token --data-file=- --replication-policy=automatic
# o, si ya existe:  printf '%s' "hf_..." | gcloud secrets versions add hf-token --data-file=-
```

Créalo **antes** de `infra/01-train-service-account.sh`: ese script le da acceso a la cuenta del job solo si el secreto ya existe. Alternativa sin Hugging Face: `GEMMA_WEIGHTS_URI=gs://vertex-model-garden-public-us/gemma4`.

### Scripts `infra/` en orden

Todos cargan `infra/env.sh` (proyecto, regiones, Artifact Registry) y `infra/app.env` (`APP=genlingo`). Son idempotentes.

| # | Script | Qué hace | Cuándo |
| --- | --- | --- | --- |
| 01 | `bash infra/01-train-service-account.sh` | Cuenta `genlingo-train`: `storage.objectAdmin` en los dos buckets, lectura de Artifact Registry y acceso a `hf-token` si existe. | Una vez. |
| 02 | `bash infra/02-train-image.sh` | Construye la imagen de entrenamiento con Cloud Build (`e2-highcpu-8`, ~15 min la primera vez). El tag es un hash de sus archivos: si no cambiaron, no reconstruye. | Lo llama `make train`. |
| 03 | `bash infra/03-train-job.sh` | Crea o actualiza dos Cloud Run Jobs en `europe-west4`: `genlingo-train` (1× L4, 8 vCPU, 32 GiB, tope de 1 h, `ADAPTER_ONLY=1`) y `genlingo-finish` (solo CPU, 8 vCPU, 32 GiB, `python /app/finish.py`, disco efímero de 10 GiB para el GGUF f16). Los dos montan el bucket de staging en `/mnt/work`. | Lo llama `make train`. |
| 04 | `bash infra/04-david.sh` | Cuenta `genlingo-david` (sin roles). Construye con Cloud Build la imagen de David (`david/Dockerfile`: Ollama 0.35.0 con el GGUF de `DAVID_MODEL_TAG` y `EMBEDDING_MODEL` adentro; el tag es un hash de la receta y del GGUF) y la despliega como servicio privado `genlingo-david` en `europe-west4`: 1× L4, 4 vCPU, 16 GiB, CPU siempre asignada, `min-instances=0`, `max-instances=1`, concurrencia 8, tiempo máximo 600 s. | Lo llama `make deploy`. |
| 05 | `bash infra/05-page.sh` | Cuenta `genlingo-page` con `aiplatform.user` y `run.invoker` sobre `genlingo-david`. Construye la página (`duel/Dockerfile`, desde la raíz del repo) y la despliega como servicio público `genlingo` en `us-central1`: `min-instances=0`, `max-instances=3`, 1 vCPU, 1 GiB, tiempo máximo 900 s (la primera llamada espera a que David encienda). | Lo llama `make deploy`. |
| 06 | `bash infra/06-eval-job.sh [args de run_eval.py]` | Cuenta `genlingo-eval` (lectura del bucket de modelos, escritura en staging, Vertex AI). Construye la imagen del eval (`evals/Dockerfile`), crea o actualiza el job `genlingo-eval` (1× L4, 8 vCPU, 32 GiB, bucket de modelos montado de solo lectura en `/mnt/models`, staging en `/mnt/staging`), lo ejecuta y copia el reporte a `evals/`. | Lo llaman `make eval` y `make eval-dev`. |

## 4. Datos, entrenamiento y eval: la cadena completa

```bash
make test-set                 # 1. set de prueba desde oraciones reales, validado contra el banco (sin humanos)
make real-pairs               #    pares de entrenamiento anclados en oraciones reales
make pairs                    # 2. (opcional) regenerar los pares sintéticos con Gemini (~$0.71, ~10 min)
make train                    # 3. LoRA (L4) + merge y GGUF (CPU) en Cloud Run -> train/runs/genlingo-<año>-<mes>.json
make eval                     # 4. evals/report.md, en un job con GPU (con DAVID_TAGS que incluya el tag nuevo)
make deploy                   # 5. con DAVID_MODEL_TAG=<tag nuevo> en .env: David nuevo en la página
make check                    # 6. la página en vivo con los ejemplos
```

`make train` sigue la receta del David de la página (`genlingo-2026-10c-e2b-nomulti`): sin los pares de varios términos (`--exclude synthetic_multi`) y sin la etapa ORPO, porque ninguno de los dos mejoró el set de desarrollo. Con los datos de hoy, `make train-data` da los mismos 2,271 ejemplos (1,715 sintéticos + 556 anclados en oraciones reales) que registra `train/runs/genlingo-2026-10c-e2b-nomulti.json`. Para repetir una variante descartada en una ablación: `MULTI=1` incluye `data/pairs/synthetic_multi.jsonl` y `ORPO=1` arma `data/train/pref.jsonl` y agrega la etapa de preferencias al job.

Qué pasa en cada paso:

1. **Set de prueba sin humanos.** `scripts/validate_test_set.py` valida cada par contra el banco de términos (la jerga del origen existe y se reemplaza, o la referencia usa jerga Gen Z del país; nada de otro país; longitud; sin solapes con entrenamiento) y lo marca `auto_validated` o `rejected` con el motivo. El eval y los ejemplos de la página usan los `auto_validated`. `make real-pairs` arma pares de entrenamiento con la otra mitad de las oraciones reales de la segunda ronda de investigación.
2. **`make counterparts`** y **`make pairs`**: `scripts/build_counterparts.py` arma la tabla de contrapartes validadas por significado (`data/counterparts.jsonl`: vecinos mutuos con coseno ≥ 0.65, o la elección de Gemini entre 5 candidatos confirmada por una palabra de significado compartida). `scripts/generate_pairs.py` genera los pares sintéticos: cada llamada nombra un término y, solo si la tabla la tiene, su contraparte; sin contraparte, el lado de papás dice el significado. Los pares llevan trampas de otro país como negativos difíciles; cada par se valida contra el banco y los rechazos se cuentan por motivo en `data/pairs/synthetic.meta.json`. `scripts/generate_multi_pairs.py` (pares que cambian 2–3 términos a la vez) no entra en la receta de David ni en `make pairs`: sus pares solo se usan en ablaciones con `MULTI=1`.
3. **`make train`** primero corre `make train-data` (`scripts/build_train_set.py`): renderiza los pares con el prompt de la página (estilo `lexicon`: país + léxico, con la respuesta en el glosario en el 85 % de los ejemplos) a `data/train/chat.jsonl`. El léxico necesita los embeddings de las frases: los pide al servicio de David (`DAVID_URL`); los del banco ya están en `data/.cache/term_embeddings.json`. Después `train/submit_job.py` sube el JSONL al bucket de staging, asegura la imagen (02) y los jobs (03), ejecuta `genlingo-train` (L4: entrena y guarda el adaptador en `gs://…-train-eu/genlingo/runs/<tag>/adapter`) y, si termina bien, `genlingo-finish` (CPU: `train/finish.py` fusiona, convierte a GGUF f16, cuantiza a `QUANT` y publica en el bucket de modelos con su `Modelfile`). Espera a los dos, calcula el costo de cada etapa y escribe `train/runs/<tag>.json`. `TAG` lleva la fecha de los datos: por defecto `genlingo-<año>-<mes>` del día; si el mes ya tiene una versión de datos, agrega una letra (`genlingo-2026-10b`).
4. **`make eval`** (`infra/06-eval-job.sh`, `evals/run_eval.py`): modelos base (`BASE_MODEL_TAGS`, el primero también con glosario), cada David de `DAVID_TAGS` con el prompt con que se entrenó (más su `-f16` si está publicado) y Goliath con y sin glosario. En el job, `run_eval.py` carga cada modelo desde el bucket montado (o desde la biblioteca de Ollama, para los base), lo precalienta (traducciones que no cuentan hasta que tres seguidas tardan menos de 1.5 s: los primeros minutos en una GPU recién encendida son lentos), lo corre a temperatura 0 de a una frase y lo borra antes del siguiente. Los resultados por frase quedan en `evals/results/<fecha>.json` y el reporte en `evals/report.md`. El reporte elige al David de la página: el archivo más pequeño a ≤ 2 puntos del f16 en jerga resuelta, con p50 < 1 s.
5. **`make deploy`** con el tag nuevo en `DAVID_MODEL_TAG`: `infra/04-david.sh` construye la imagen nueva de David (el GGUF cambió, el hash también) y la despliega; `infra/05-page.sh` vuelve a desplegar la página con el tag nuevo.
6. **`make check`**: si cambió David, vuelve a verificar los ejemplos de `data/translate_examples.json` (3 veces en vivo con los dos) y corre `make check`; un ejemplo que ya no muestra la diferencia se quita.

## 5. La página de comparación

**https://genlingo-611681112050.us-central1.run.app**

Se elige la dirección, se escribe una frase o se toca un ejemplo, y David y Goliath traducen al mismo tiempo; cada columna muestra su traducción y su tiempo. En los ejemplos aparece también la traducción de referencia y un ✓/✗ por término de jerga. `Enter` en el cuadro de texto traduce. El país es `EVENT_COUNTRY` (`GT` por defecto: la charla es en Guatemala).

David escala a cero cuando nadie lo usa. Al abrir la página:

1. La página llama `POST /api/david/wake`. Esa llamada enciende la instancia de David (Cloud Run la retiene hasta que arranca), carga David y EmbeddingGemma si no están en memoria (`/api/ps`, `/api/chat` vacío, `/api/embed`), traduce frases de calentamiento (los ejemplos, en las dos direcciones) hasta que tres seguidas tardan menos de 1 s, y responde. Los primeros minutos de una instancia recién encendida son lentos (la imagen todavía se descarga por partes); así «David listo» significa rápido. Mientras tanto la página consulta `GET /api/status` cada segundo para mostrar el reloj de «Preparando a David…».
2. Con «David listo», los botones se activan.
3. Cada minuto, mientras la página está abierta y visible (hasta tres horas), vuelve a llamar `POST /api/david/wake`: una consulta barata que mantiene encendida la instancia. Si David se apagó, lo vuelve a encender.

Ensayo sin nube: `MOCK_AI=1 uv run --project duel uvicorn genlingo_duel.main:create_app --factory --port 8080` levanta la página con modelos simulados en `http://127.0.0.1:8080`.

## 6. Recorrido por el código: una traducción en la página

1. **La página** (`duel/genlingo_duel/static/index.html`, servida en `GET /` con sus tipografías en `/fonts/`). Al pulsar **Traducir** o un ejemplo, llama a la vez `POST /api/translate/david` y `POST /api/translate/goliath` con frase, dirección y, si es un ejemplo, su `example_id`; cada columna se llena cuando llega su respuesta, con un cronómetro mientras espera.
2. **API** (`duel/genlingo_duel/main.py`). Cada ruta llama `arena.translate_one(side, ...)`; nada se registra. Los ejemplos salen de `GET /api/examples` (`translate_page.py`, que lee `data/translate_examples.json`).
3. **Prompt por lado** (`arena.py`). `prompt_style_for` lee el run file del tag (`runs.py` quita sufijos como `-f16` o `-q5_k_m` hasta encontrarlo) para saber con qué prompt se entrenó David; Goliath usa `GOLIATH_PROMPT_STYLE` (`country`, sin glosario). Con el estilo `lexicon`, `glossary.py` arma 6 entradas: cada término de la generación de origen que aparece en la frase con su contraparte validada (`terms.py`; `data/counterparts.jsonl`), los de la otra generación más cercanos por coseno con EmbeddingGemma y uno de otro país marcado «NO de aquí». Con `DAVID_NBEST` > 1, `rerank.py` pide N respuestas en paralelo y el banco elige. `prompts.py` arma los mensajes.
4. **La llamada** (`duel_core/duel.py`). David va por `ollama_client.py` al servicio privado de David (`/api/chat`, sin streaming, `think: false`, temperatura 0) con un token de identidad (`cloud_auth.py`: en Cloud Run lo emite la cuenta de la página; fuera, `gcloud auth print-identity-token`); Goliath por `gemini_client.py` (Vertex AI, ADC, timeout 30 s, reintenta los 429; los tokens de razonamiento cuentan como salida). Los dos lados van a temperatura 0, como en `make eval`. Un error no tumba la página: el lado que falla dice «No respondió».
5. **Medición** (`duel.py`). `clean_translation` deja la primera línea sin etiquetas ni comillas. El tiempo de recuperación del glosario se suma a la latencia de David.
6. **Revisión por término** (`term_check.py`). Solo para ejemplos: las reglas de la *jerga correcta* del eval, un término a la vez, con la referencia del ejemplo; la página muestra ✓ o ✗ por término.

## 7. Ensayar y probar

- `make test`: todo sin red (`MOCK_AI=1`).
- `make check`: la página en vivo, de punta a punta: despierta a David (dice cuánto tardó) y traduce cada ejemplo con los dos (David tiene que acertar la jerga y Goliath no).
- `make screenshots`: las capturas de `docs/demo/` desde la página en vivo, en un navegador real.

## 8. Problemas frecuentes

| Síntoma | Causa y solución |
| --- | --- |
| La página se queda en «Preparando a David…» más de 5 minutos | Cloud Run no consiguió una GPU (la cuota de L4 de `europe-west4` es compartida con otras demos y jobs) o la instancia no arrancó. Revisa `gcloud run services logs read genlingo-david --region europe-west4` y recarga la página. |
| La página dice «David no respondió · reintentando» | La llamada de encendido falló (tiempo agotado o error de David); la página reintenta cada 5 s. Si sigue, mira los registros de `genlingo-david`. |
| La columna de David dice «No respondió» | David se apagó entre la última llamada y esta (más de ~15 min sin uso) o tardó más de 120 s. Pulsa **Traducir** otra vez. |
| Goliath dice «No respondió» | Gemini tardó más de 30 s o falló. Vuelve a intentar. |
| `make check` dice que Goliath también acertó un ejemplo | Goliath varía de una llamada a otra. Repite `make check`; si vuelve a pasar, ese ejemplo ya no muestra la diferencia: quítalo de `data/translate_examples.json`. |
| `make train-data` falla con «no ID token» | Falta `DAVID_URL` en `.env` o tu cuenta no puede invocar `genlingo-david`: `gcloud run services add-iam-policy-binding genlingo-david --region europe-west4 --member=user:<tu correo> --role=roles/run.invoker`. |
| `genlingo-finish` muere con «memory limit was reached» | Base demasiado grande para fusionar en 32 GiB (E4B). Corre entrenamiento y fusión juntos en Vertex AI: `TRAIN_RUNTIME=vertex make train`. |
| `make train` falla al descargar pesos con 429 | Descargas anónimas de Hugging Face desde la nube. Crea `hf-token` en Secret Manager y vuelve a correr `infra/01-train-service-account.sh`. |
| `make eval` termina sin reporte | El job falló antes de copiar: `gcloud run jobs executions list --job genlingo-eval --region europe-west4` y sus registros. |

## 9. Día de la charla

- [ ] Abrir **https://genlingo-611681112050.us-central1.run.app** en Chrome unos diez minutos antes y esperar «David listo».
- [ ] Pantalla completa y comprobar desde el fondo de la sala que se lea.

Nada que ejecutar antes ni después: David se apaga solo unos 15 minutos después de cerrar la página.
