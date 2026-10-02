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

- **Los datos reales movieron la aguja.** El David de escena (`genlingo-2026-10b-e2b`) se entrenó con la segunda ronda de investigación: 334 pares anclados en oraciones reales, el banco crecido a 406 términos en el glosario y los sintéticos refiltrados contra ese banco. Resuelve la jerga en el **82 %** de las 399 frases de prueba, contra **74 %** del David anterior con la misma compresión. Casi toda la mejora está en la dirección difícil, papás → Gen Z: de 43 % a **59 %**. Es una sola corrida por David, sin separar cuánto aporta cada cambio.
- **David ya gana a Gemini solo en jerga:** 82 % contra **78 %**, y 56.6 contra 53.1 en chrF++. Responde en **~0.6 s** (p50 557 ms) y cuesta **$0** por frase; Goliath tarda **~3.3 s** y cuesta **$1.08 por 1,000 frases**.
- **Con el mismo glosario, empatan en jerga (82 %)**, y Goliath acierta más palabras de la referencia (30 % contra 22 %). La ventaja de David no es ser mejor modelo: son **sus datos** (el banco de términos y las oraciones reales, con fuentes y fecha).
- **Comprimir ya no cuesta jerga:** el David de escena es el Q5_K_M (3.62 GB), a un punto del f16 (9.27 GB), con la misma latencia.
- **chrF++ casi no distingue a nadie:** devolver la frase sin traducir ya saca **53.2**; David 56.6, Goliath 53.1, Goliath con glosario 56.5. Por eso existe la métrica a nivel de término.
- **Reentrenar cada mes cuesta menos de $1, todo en la nube:** $0.71 de punta a punta (L4 para entrenar + CPU para fusionar y cuantizar).
- **Los modelos grandes envejecen:** con la tecla `M` el David anterior (`genlingo-2026-10-e2b-q5_k_m`, 74 %) se enfrenta en vivo al de escena (82 %).

La historia completa, iteración por iteración (callejones sin salida incluidos), está en [docs/BITACORA.md](docs/BITACORA.md); los nichos donde David se mide contra Goliath, definidos antes de mirar resultados, en [evals/niche.md](evals/niche.md).

> Las referencias del set de prueba se validan automáticamente contra el banco de términos (`auto_validated`); ninguna persona las revisó. Ningún par de prueba aparece en los datos de entrenamiento, ni siquiera dentro de una oración más larga. Las oraciones de prueba y los pares reales de entrenamiento vienen de la misma ronda de investigación (mitades disjuntas por hash), así que parte de la mejora puede ser cercanía a esas fuentes. Detalle completo en [evals/report.md](evals/report.md).

![Jerga resuelta por variante](docs/diagrams/resultados-jerga.png)

## Qué vas a aprender

| Lección | Dónde está en el código |
| --- | --- |
| **Datos propios con `origin`.** Cada par dice de dónde salió: `web` (URL + licencia), `synthetic` (modelo + versión de prompt + semilla) o `human` (evento). Sin eso no se puede evaluar con honestidad ni reentrenar cada mes. | `duel/genlingo_duel/dataset.py` (esquema `Pair` que valida la procedencia), [data/SOURCES.md](data/SOURCES.md), [data/DATASHEET.md](data/DATASHEET.md) |
| **Banco de términos, oraciones reales y pares sintéticos validados.** 406 términos de 57 fuentes; Gemini genera pares de *sustitución de término* anclados en el banco, y cada par se valida contra el banco (término esperado presente, nada de jerga de otro país, la jerga del origen desaparece): quedan 1,375. A eso se suman 334 pares anclados en oraciones reales de la web. | `data/terms.jsonl`, `scripts/generate_pairs.py`, `duel/genlingo_duel/terms.py` |
| **LoRA en Cloud Run Jobs.** La misma imagen entrena en una L4 (TRL + PEFT, r=16, alpha=32, lr 2e-4, 3 épocas) y, en un job de CPU, fusiona, exporta GGUF con llama.cpp y publica un Modelfile para Ollama. Cada corrida deja su duración y costo por etapa en un archivo. | `train/train_lora.py`, `train/finish.py`, `train/submit_job.py`, `infra/03-train-job.sh`, `train/runs/` |
| **El costo de comprimir.** f16 contra Q4_K_M, Q5_K_M, Q6_K, Q8_0 e imatrix: tamaño, latencia y cuánta jerga se pierde. | `train_lora.to_gguf`, sección «Compresión» de `evals/report.md` |
| **Evals honestos con métricas de término.** chrF++ más una línea base de «copiar la frase», *jerga resuelta* y *cambios acertados* contra el banco; las derrotas de David se publican. Ningún modelo juzga a otro. | `evals/run_eval.py`, `evals/term_accuracy.py`, `evals/report.py` |
| **Reentrenamiento mensual y `david_tag`.** Los modelos llevan la fecha de sus datos (`genlingo-AAAA-MM`, con una letra si hay dos versiones de datos en el mes: `genlingo-2026-10b-e2b` es la segunda ronda de investigación de octubre); el duelo acepta `david_tag` para enfrentar al David del mes pasado con el de este mes. | `Makefile` (`TAG`), `DuelRequest.david_tag` en `duel/genlingo_duel/main.py`, tecla `M` en `web/components/presenter/PresenterApp.tsx` |
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
make pull-model TAG=genlingo-2026-10b-e2b             # David de escena (Q5_K_M, 3.62 GB)
make pull-model TAG=genlingo-2026-10-e2b-q5_k_m      # David del mes pasado (tecla M)

make up       # Ollama + David precalentado + duelo (:8787) + vista del presentador (:3000/presenter)
```

Ensayo sin red ni GPU: pon `MOCK_AI=1` en `.env` y corre `make up` (modelos simulados y deterministas).

## Comandos `make`

| Comando | Qué hace |
| --- | --- |
| `make help` | Lista los comandos con su descripción. |
| `make up` | Arranca Ollama (con `OLLAMA_MAX_LOADED_MODELS=4`), precarga los tres modelos de escena (David, el del mes pasado y EmbeddingGemma), levanta el duelo y la vista del presentador (la recompila si cambió su código). Funciona sin Wi-Fi y sin público. |
| `make reset` | Pone en cero rondas, votos, cola y marcador locales; con `AUDIENCE_FEED=1` y red, también borra las rondas del evento en Firestore. |
| `make test` | Pruebas de Python (`MOCK_AI=1`), Vitest, `tsc`, ESLint y, con JDK 21, las reglas de Firestore en el emulador. |
| `make eval` | Pasa el set de prueba por los modelos base, cada David y Goliath (con y sin glosario) y escribe `evals/report.md`. Acepta `EVAL_ARGS="--limit 50 --no-goliath"`. |
| `make test-set` | Construye los pares de prueba a partir de oraciones reales de la web y los valida contra el banco de términos (`auto_validated` o `rejected`, sin intervención humana). |
| `make real-pairs` | Pares de entrenamiento anclados en oraciones reales (las dos direcciones), validados contra el banco. |
| `make ambiguous-terms` | Marca los términos del banco que también son palabras comunes («cámara», «servir»), para que las métricas no los cuenten. |
| `make pairs` | Genera los pares sintéticos de entrenamiento con `GEMINI_MODEL` (de pago; `SYNTHETIC_PAIRS_TARGET`, hoy 1,500). |
| `make datasheet` | Recuenta `data/DATASHEET.md`. |
| `make data` | `test-set` + `pairs` + `datasheet`. |
| `make review-test` | (Opcional) exporta el set de prueba a un CSV para una pasada humana sobre la validación automática. |
| `make review-test-apply` | Aplica las decisiones del CSV (`a` aprobar, `r` rechazar, referencia corregida opcional). |
| `make export` | Baja de Firestore los pares del público aprobados en `/admin` a `data/pairs/human.jsonl` y recuenta el datasheet. |
| `make train-data` | Renderiza los pares aprobados al JSONL de chat con el mismo prompt (y glosario) del duelo. |
| `make train` | Entrena en un Cloud Run Job con una L4 y después fusiona y convierte a GGUF en un job de CPU: `make train TAG=genlingo-2027-03 [QUANT=Q5_K_M] [GEMMA_BASE_MODEL=…] [TRAIN_ARGS=…]`. Escribe `train/runs/<tag>.json`. |
| `make train-finish` | Respaldo: fusiona y exporta a GGUF en la laptop un adaptador entrenado en la nube y lo publica: `make train-finish TAG=…`. |
| `make train-local` | El mismo entrenamiento en la Mac (MPS), para experimentos. |
| `make quant-sweep` | Desde el GGUF f16 de un David: Q5_K_M, Q6_K, Q8_0 y Q4/Q5 calibrados con imatrix (pares de entrenamiento), registrados en Ollama. |
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
train/                train_lora.py, finish.py, submit_job.py, finish_local.py, train_local.py, notebook, runs/
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
- **Entrenamiento**: dos Cloud Run Jobs en `europe-west4` (L4 para entrenar, CPU para fusionar y convertir a GGUF); imagen construida con Cloud Build en Artifact Registry `charlas2027`.

### Por qué dos Cloud Run Jobs

Un reentrenamiento al mes no justifica nada encendido entre corridas. Cloud Run Jobs es serverless, se cobra por segundo mientras la tarea corre y usa el mismo tipo de imagen que el resto. `make train` encadena dos jobs de la misma imagen (`infra/03-train-job.sh`):

| Job | Máquina | Qué hace |
| --- | --- | --- |
| `genlingo-train` | 1× L4, 8 vCPU, 32 GiB | Entrena el adaptador LoRA y lo guarda en el volumen del bucket (`ADAPTER_ONLY=1`). |
| `genlingo-finish` | solo CPU, 8 vCPU, 32 GiB, disco efímero de 10 GiB | Fusiona el adaptador, convierte a GGUF f16, cuantiza a `QUANT` (Q5_K_M) y publica en el bucket de modelos (`train/finish.py`). |

`train/submit_job.py` espera a los dos, calcula el costo de cada uno con las tarifas por segundo de GPU, vCPU y memoria, y deja el detalle por etapa y el total en `train/runs/<tag>.json`.

Por qué dividirlo: el sistema de archivos de Cloud Run vive en la memoria de la instancia. Entrenar, guardar un checkpoint fusionado de 10 GB y escribir un GGUF f16 de 9 GB no caben juntos en 32 GiB: la corrida `genlingo-2026-10b-e2b` (`zct96`) murió por memoria al convertir a f16, y E4B ya había fallado igual al fusionar. En el job de CPU no queda nada del entrenamiento en memoria: los pesos base se copian del bucket con una lectura secuencial (cargarlos con `mmap` desde el bucket montado iba a ~5 MB/s), la fusión corre en un proceso hijo (devuelve sus ~10 GB al terminar), el checkpoint fusionado va al disco en memoria, el GGUF f16 va al disco efímero (respaldado en disco, no en memoria) y el checkpoint se borra antes de cuantizar. Además la GPU no se cobra mientras se fusiona y convierte. Los pesos base se cachean en un volumen de Cloud Storage que comparten los dos jobs; los GGUF no van ahí porque el convertidor escribe a saltos y sobre el bucket montado iba a ~3 MB/s (corridas canceladas `kcwqz` y `kqlxv` en `train/runs/failed/`).

Descartado: Google Cloud Batch con una L4 y disco persistente. Resolvía la memoria en un solo paso, pero suma otra API, otra imagen de VM con drivers y otra cuenta de permisos, mientras que dos jobs reutilizan la imagen, la cuenta de servicio y el bucket que ya existían.

Alternativas disponibles: un Vertex AI Custom Job con el mismo contenedor y 200 GB de disco (`TRAIN_RUNTIME=vertex`, todo en un paso), el notebook `train/genlingo.ipynb` para Colab, y `make train-local` en la Mac (36.9 min para 1,000 pares en MPS; en la L4, la fase de entrenamiento de ese mismo tamaño tomó 5.8 min).

### `make train-finish`: el respaldo en la laptop

`make train-finish TAG=…` corre el mismo `train/finish.py` en la Mac de 64 GB: baja el adaptador del bucket, fusiona, convierte, cuantiza (`QUANT`, `KEEP_F16=1` para publicar también el f16) y publica en el mismo bucket, así que `make pull-model` no distingue dónde se hizo la fusión. Sirve cuando el job de CPU no puede correr, y para E4B: su checkpoint fusionado de 16 GB más el modelo en memoria no caben en 32 GiB ni en el job de CPU. E4B no salió a escena: con 67 % de jerga resuelta y p50 de 836 ms no supera al E2B f16.

### El prompt con glosario

El prompt `translate-v2` empieza por el país («Variante: español de Guatemala. Usa solo expresiones de Guatemala…») porque «chido» y «chilero» son la misma palabra en lugares distintos. Al final lleva un glosario de cuatro entradas del banco de términos, del país o neutras: primero los términos de la generación de origen que aparecen literalmente en la frase y después los más cercanos por significado según EmbeddingGemma. El tiempo de recuperación se suma a la latencia de David.

David se entrena con exactamente ese formato (`make train-data` usa `v2+glossary` por defecto) y el duelo lee de `train/runs/<tag>.json` con qué prompt se entrenó cada David: no hay diferencia entre entrenamiento y escena. Goliath recibe `v2` sin glosario por defecto (`GOLIATH_PROMPT_STYLE`), porque el banco es dato de David; `make eval` corre además a Goliath con el mismo glosario, y así se ve cuánto del resultado es modelo y cuánto es dato.

### El set de prueba es solo web, nunca sintético

Una referencia escrita por Gemini premiaría a Goliath por sonar como él mismo. Los pares de prueba salen de oraciones reales encontradas en la web (dos rondas de investigación, 522 candidatos); la referencia la escribe el curador a partir del significado que da la fuente, y `scripts/validate_test_set.py` la valida contra el banco de términos sin intervención humana: quedan 399 `auto_validated`. También rechaza cualquier par de prueba que aparezca en un archivo de entrenamiento (sintéticos, reales o del público), aunque sea dentro de una oración más larga: coincidencia de subcadenas cruda y normalizada (`duel/genlingo_duel/overlap.py`). La segunda ronda se parte por un hash estable del id: la mitad va a prueba y la otra mitad a pares de entrenamiento anclados en oraciones reales (`make real-pairs`), sin oraciones compartidas. El esquema `Pair` rechaza cualquier par sintético en el split de prueba. Los pares del público (`origin=human`) se reparten 80/20 entre entrenamiento y prueba con un hash estable del id.

### Tarifas de Gemini con fecha

Los precios cambian, y eso es parte de la historia. `GEMINI_PRICE_SCHEDULE=2026-09-30:0.75/3.75,2027-01-01:1.50/7.50` es una lista de tarifas por fecha: cada ronda y cada eval usan la tarifa vigente ese día y registran cuál usaron. El reporte muestra además lo que costaría el mismo eval con la tarifa de 2027 ($2.17 por 1,000 frases en vez de $1.08). Los tokens de razonamiento se cobran como salida. La inferencia de David cuesta $0; el presentador muestra su costo de entrenamiento amortizado por ronda. Las exportaciones de una misma corrida (`-f16`, `-q5_k_m`, `-iq-q4_k_m`…) comparten su `train/runs/<tag>.json`.

### App Check se aplica a todo el proyecto

`infra/06-app-check.sh` registra reCAPTCHA Enterprise como proveedor de App Check y, con `ENFORCE_FIRESTORE=1`, exige App Check en Cloud Firestore. Esa exigencia es **por proyecto**: App Check no tiene política por base de datos, así que cualquier cliente web o móvil de cualquier base de `ai-experiments-487722` tendrá que mandar tokens de App Check. El código de servidor (Admin SDK, IAM) no se ve afectado. Las rutas de la API lo exigen por su cuenta con `APP_CHECK_ENFORCE=1`, que `infra/05-deploy-web.sh` activa cuando hay `RECAPTCHA_SITE_KEY`. Las pruebas automatizadas y el emulador usan un token de depuración registrado.

### Quién gana una ronda

- **Ronda de evaluación** (frase del set de prueba, tecla `E`): gana el chrF++ más alto; diferencias menores a 0.5 son empate. Usa pares `auto_validated` (o aprobados por una persona), listos sin revisión humana.
- **Frase en vivo** (escrita con `/`) o **del público** (desde un teléfono): con la app del público conectada (`AUDIENCE_FEED=1`) decide el voto (`V` cierra la votación); sin público, la ronda muestra las dos traducciones sin ganador. La charla completa funciona sin público: rondas `E` y frases escritas.
- Las frases del público que pasan la blocklist van directo a la cola de la pantalla (`AUTO_APPROVE_PHRASES=1`, por defecto); con `0`, el presentador las aprueba en `/admin`.
- Si Goliath no tiene red o falla, David gana por presentarse.

## Resultados

Eval del 2026-10-02 sobre 399 pares de prueba web `auto_validated` (de 522 candidatos; 123 rechazados por la validación automática, 4 de ellos por aparecer dentro de un par de entrenamiento). Todos los modelos locales con el prompt con que se entrenaron, uno a la vez en la M1 Max; Goliath con temperatura 0 (1 error sin glosario).

| Variante | Jerga resuelta | Gen Z → papás | papás → Gen Z | Cambios acertados | chrF++ | p50 | Costo / 1,000 frases | Tamaño |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Copiar la frase (línea base) | 1 % | 0 % | 3 % | 0 % | 53.2 | — | — | — |
| `gemma4:e2b-it-qat` (base) | 58 % | 95 % | 10 % | 14 % | 50.2 | 364 ms | $0 | 4.34 GB |
| `gemma4:e2b-it-qat` + glosario | 62 % | 94 % | 20 % | 23 % | 55.0 | 452 ms | $0 | 4.34 GB |
| `gemma4:e4b` (base) | 68 % | 97 % | 31 % | 17 % | 48.2 | 802 ms | $0 | 6.58 GB |
| `genlingo-2026-09` (Q4, prompt v1) | 62 % | 94 % | 20 % | 14 % | 55.0 | 391 ms | $0 | 3.42 GB |
| `genlingo-2026-10-e2b` + glosario (Q4) | 67 % | 95 % | 31 % | 16 % | 55.7 | 512 ms | $0 | 3.42 GB |
| `genlingo-2026-10-e2b-q5_k_m` + glosario (anterior) | 74 % | 97 % | 43 % | 18 % | 55.4 | 564 ms | $0 | 3.62 GB |
| `genlingo-2026-10-e2b-f16` + glosario | 74 % | 99 % | 42 % | 19 % | 56.3 | 566 ms | $0 | 9.27 GB |
| **`genlingo-2026-10b-e2b` + glosario (Q5_K_M, en escena)** | **82 %** | 99 % | **59 %** | 22 % | **56.6** | **557 ms** | **$0** | 3.62 GB |
| `genlingo-2026-10b-e2b-f16` + glosario | 81 % | 98 % | 59 % | 22 % | 56.7 | 543 ms | $0 | 9.27 GB |
| Goliath `gemini-3.8-flash` | 78 % | 99 % | 51 % | 25 % | 53.1 | 3.26 s | $1.08 | — |
| Goliath + el mismo glosario | 82 % | 98 % | 62 % | 30 % | 56.5 | 3.84 s | $1.24 | — |

**Lectura honesta.** Frase por frase, David resuelve la jerga y Goliath no en 46 frases; al revés, en 31. Contra Goliath con glosario la cuenta se invierte: 36 contra 39. En *cambios acertados* (palabras exactas de la referencia) Goliath gana a David con y sin glosario, y David todavía mete jerga de otro país en 14 de 173 frases papás → Gen Z (Goliath: 2). Los datos de la segunda ronda le dieron a David 8 puntos de jerga resuelta, casi todos en papás → Gen Z, que es lo que enseñan los pares reales en esa dirección (una oración Gen Z real como salida). David gana en velocidad, costo y privacidad, y gana en jerga mientras el banco de términos y las oraciones reales sean solo suyos. chrF++ queda pegado a la línea base de copiar (53.2) porque una reescritura de registro conserva casi todas las palabras: no sirve para decidir quién tradujo la jerga.

Las diez peores derrotas de David y los cortes por país y dirección están en [evals/report.md](evals/report.md). La primera versión de los datos (`pairs-v1`, paráfrasis libre) dejó a David *por debajo* de la base (chrF++ 39.1): está documentado en [evals/experiments/2026-09-pairs-v1.md](evals/experiments/2026-09-pairs-v1.md).

| Tecla `M`: el David del mes pasado | Wi-Fi apagado |
| --- | --- |
| ![El David del mes pasado (tecla M)](docs/screenshots/presentador-mes-pasado.png) | ![Sin internet: Goliath sin conexión, David sigue](docs/screenshots/presentador-sin-internet.png) |
| Tecla `M`: el David anterior (`genlingo-2026-10-e2b-q5_k_m`) contra Goliath con la misma frase; el marcador cuenta solo sus rondas. | Sin red: Goliath aparece «sin conexión» y David responde en 0.53 s («bolo» → «borrachín»; «chupando» queda como «de fiesta», cerca pero no exacto: es bebiendo). |

## Costo de entrenamiento por corrida

Cloud Run Jobs en `europe-west4`: entrenamiento en 1× NVIDIA L4 sin redundancia zonal, 8 vCPU, 32 GiB; desde `genlingo-2026-10b-e2b`, fusión + GGUF en un job aparte de CPU (8 vCPU, 32 GiB). Costo = segundos facturados × tarifas por segundo (`CLOUD_RUN_*_USD_PER_S` en `.env`), por etapa.

| Corrida | Base | Pares | Resultado | Duración | Costo |
| --- | --- | --- | --- | --- | --- |
| `genlingo-2026-09` | E2B | 1,000 (`pairs-v2`) | listo (loss 2.33 → 0.14) | 17.4 min | $0.41 |
| `genlingo-2026-10-e2b` | E2B | 1,500 (`pairs-v3`) | listo (loss 2.26 → 0.12) | 28.2 min | $0.67 |
| `genlingo-2026-10-e4b` | E4B | 1,500 (`pairs-v3`) | entrenó; sin memoria al fusionar → `make train-finish` | 41.3 min | $0.98 |
| `genlingo-2026-10b-e2b` | E2B | 1,709 (1,375 sintéticos + 334 anclados en oraciones reales) | listo en la nube, dos jobs (loss 2.62 → 0.16): entrenamiento 25.3 min $0.60 + fusión/GGUF Q5_K_M y f16 9.0 min $0.11 | 34.3 min | $0.71 |
| `failed/genlingo-2026-10b-e2b-zct96` | E2B | 1,709 | entrenó; muerta por memoria al convertir a GGUF f16 en el job único → motivó la división en dos jobs | 26.8 min | $0.63 |
| `failed/genlingo-2026-09-nv5r5` | E2B | 1,000 | falló al arrancar (faltaba `gcc` para Triton) | 10.9 min | $0.26 |
| `failed/genlingo-2026-09-kcwqz` | E2B | 1,000 | cancelada: GGUF escrito en el bucket montado, demasiado lento | 31.2 min | $0.74 |
| `failed/genlingo-2026-09-kqlxv` | E2B | 1,000 | cancelada a ~28 min (misma causa, al leer) | — | sin registro |
| `experiments/genlingo-2026-09-pairs-v1` | E2B | 1,000 (`pairs-v1`) | laptop, MPS | 36.9 min | $0 |

Generar los 1,500 pares sintéticos de `pairs-v3` con Gemini costó $0.80 (6 min). Un reentrenamiento mensual de E2B, de punta a punta en la nube (entrenamiento → GGUF), cuesta menos de $1; la inferencia de David, $0.

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
| `data/terms.jsonl` (406 términos) y `data/raw/web_usage*.jsonl` (739 oraciones) | 57 fuentes web de MX, GT, CO y Latinoamérica, consultadas el 2026-09-30 y el 2026-10-01 ([SOURCES.md](data/SOURCES.md)); un corpus de habla general (S63) solo para contar términos ambiguos | WikiLengua (CC BY-SA 3.0), Wikcionario (CC BY-SA 4.0) y diccionario-chapin (MIT) se reutilizan bajo su licencia con atribución por registro. De las fuentes con todos los derechos reservados solo se toman hechos (término y significado, parafraseado) y una cita breve atribuida por entrada, con fines de investigación y educación. |
| `data/pairs/test_web.jsonl` (522 pares, 399 `auto_validated`) y `data/pairs/real_train.jsonl` (334 pares) | Oraciones reales de esas fuentes; la referencia es reescritura del curador (menos de 30 % son oraciones escritas por el curador, marcadas `example_origin=curator`) | Igual que la fuente; los pares que citan ejemplos CC BY-SA heredan share-alike para ese texto. |
| `data/pairs/synthetic.jsonl` (1,375 pares) | `gemini-3.8-flash`, prompt `pairs-v3`, semilla base 2027; solo entrenamiento | Cada par registra modelo, versión de prompt, semilla y los ids de término de los que salió. |
| `data/pairs/human.jsonl` | Público de cada evento, aprobado en `/admin` (`make export`) | Procedencia: evento e id de Firestore. |

Limitaciones conocidas (del datasheet): la jerga juvenil guatemalteca está poco documentada en línea; la jerga envejece rápido; las referencias son de una sola persona, así que chrF++ subestima traducciones alternativas válidas.

## App desplegada

- Público: **https://genlingo-611681112050.us-central1.run.app** (evento `ensayo`, país `GT`)
- Moderación: `/admin` en la misma URL (cuenta del presentador con `admin=true`)
- Vista del presentador: local, `http://127.0.0.1:3000/presenter` con `make up`

![App del público en un teléfono](docs/screenshots/audiencia.png)
