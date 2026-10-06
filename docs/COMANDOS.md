# Comandos

Todos los comandos del `Makefile`. `make help` los lista con su descripción. Volver al [README](../README.md). [English version](COMANDOS.en.md).

| Comando | Qué hace |
| --- | --- |
| `make help` | Lista los comandos con su descripción. |
| `make up` | Arranca Ollama (con `OLLAMA_MAX_LOADED_MODELS=4`), precarga David, el David anterior (`DAVID_PREVIOUS_TAG`) y EmbeddingGemma, levanta el servicio del duelo (`:8787`, que sirve la página de comparación `/traducir`) y la vista del presentador (`:3000`, la recompila si cambió su código), y abre la página de comparación. Funciona sin Wi-Fi. |
| `make reset` | Pone en cero el historial del servicio del duelo (rondas, votos, cola y marcador; la página de comparación no los usa); con `AUDIENCE_FEED=1`, también borra las rondas del evento en Firestore (hasta 3 intentos). Si Firestore falla (por ejemplo, sin red), lo dice con la causa y termina con error; el marcador local queda en cero igual. |
| `make stage-on` | `min-instances=1` en la app del público de Cloud Run (`infra/60-stage.sh on`). La demo no la usa, pero `make preflight` revisa que esté tibia. Muestra el valor que quedó en Cloud Run. |
| `make stage-off` | Después de la charla: `min-instances=0` (escala a cero, nada cobra en reposo). |
| `make warmup` | Despierta la app del público (200 en `/` y `/api/config`), carga en Ollama los dos Davids y EmbeddingGemma, y hace una llamada a David y otra a Goliath: por el servicio si está corriendo (`POST /warmup`, no se registra) o directo si no. |
| `make preflight` | Revisión antes de subir: Ollama con los dos Davids y EmbeddingGemma, `/health` del duelo, `/api/config` de la vista del presentador, banco de términos, léxico, set de prueba y ficha de entrenamiento de David, 10 GB libres en disco, la página de comparación y cada ejemplo traducido en vivo por los dos (David acierta la jerga y Goliath no), app del público con 200, `min-instances` ≥ 1 y el mismo `EVENT_ID`, Gemini (una llamada mínima) y Firestore del evento. Una línea `[ok]` o `[FALLA]` por revisión, con el arreglo; el código de salida es el número de fallas. |
| `make test` | Pruebas de Python (`MOCK_AI=1`), Vitest, `tsc`, ESLint y, con JDK 21, las reglas de Firestore en el emulador. |
| `make eval` | Pasa el set de prueba por los modelos base, cada David y Goliath (con y sin glosario) y escribe `evals/report.md`. Acepta `EVAL_ARGS="--limit 50 --no-goliath"`. |
| `make eval-dev` | Pasa el set de desarrollo (decisiones de datos, ablaciones) y escribe `evals/report_dev.md`: `make eval-dev [EVAL_ARGS="--nbest 4"]`. |
| `make niches` | Calcula los nichos registrados de antemano ([evals/niche.md](../evals/niche.md)) a partir del último eval de prueba y escribe `evals/niche_report.md`. |
| `make test-set` | Construye los pares de prueba a partir de oraciones reales de la web y los valida contra el banco de términos (`auto_validated` o `rejected`, sin intervención humana). |
| `make real-pairs` | Pares de entrenamiento anclados en oraciones reales (las dos direcciones), validados contra el banco. |
| `make ambiguous-terms` | Marca los términos del banco que también son palabras comunes («cámara», «servir»), para que las métricas no los cuenten. |
| `make counterparts` | Tabla término → contraparte validada por significado (vecinos más cercanos mutuos + revisión del top 5 con Gemini) en `data/counterparts.jsonl`. |
| `make pairs` | Genera los pares sintéticos de un término con `GEMINI_MODEL` (de pago; `SYNTHETIC_PAIRS_TARGET`, hoy 1,500). Los pares de 2–3 términos (`scripts/generate_multi_pairs.py`, `data/pairs/synthetic_multi.jsonl`) no entran en la receta de escena y no se regeneran aquí. |
| `make datasheet` | Recuenta `data/DATASHEET.md`. |
| `make data` | `test-set` + `real-pairs` + `pairs` + `datasheet`. |
| `make export` | Baja de Firestore los pares del público aprobados en `/admin` a `data/pairs/human.jsonl` y recuenta el datasheet. |
| `make train-data` | Renderiza los pares de entrenamiento al JSONL de chat con el mismo prompt (y léxico) del duelo, con la receta del David de escena: sin los pares de 2–3 términos y sin etapa ORPO. `MULTI=1` incluye esos pares y `ORPO=1` arma también `data/train/pref.jsonl` (variantes descartadas, para ablaciones). |
| `make train` | Entrena en un Cloud Run Job con una L4 y después fusiona y convierte a GGUF en un job de CPU: `make train [TAG=…] [QUANT=Q5_K_M] [TRAIN_ARGS=…]`; `TAG` vale por defecto `genlingo-<año>-<mes>` del día. Corre `make train-data` antes (acepta `MULTI=1` y `ORPO=1`; con `ORPO=1` agrega la etapa de preferencias al job). Escribe `train/runs/<tag>.json`. |
| `make train-finish` | Respaldo: fusiona y exporta a GGUF en la laptop un adaptador entrenado en la nube y lo publica: `make train-finish` con el mismo `TAG` del job. |
| `make train-local` | El mismo entrenamiento en la Mac (MPS), para experimentos. |
| `make quant-sweep` | Desde el GGUF f16 de un David: Q5_K_M, Q6_K, Q8_0 y Q4/Q5 calibrados con imatrix (pares de entrenamiento), registrados en Ollama. |
| `make pull-model` | Descarga un David del bucket y lo registra en Ollama: `make pull-model TAG=genlingo-2026-10c-e2b-nomulti [FP16=1]`. |
| `make deploy` | Crea la cuenta de servicio web y despliega la app del público en Cloud Run (`min-instances=0`; `make stage-on` la mantiene tibia el día de la charla). |

## Arranque rápido

Requisitos (versiones en [ONBOARDING.md](ONBOARDING.md)): macOS con Apple Silicon, `uv`, Node 24, Ollama, `gcloud` con ADC.

```bash
cp .env.example .env                                  # modelos, precios y rutas
(cd duel && uv sync)                                  # servicio del duelo (Python 3.12)
(cd web && npm install && cp .env.example .env.local) # vista del presentador, app del público y capturas
gcloud auth application-default login                 # Goliath (Vertex AI) y descarga de modelos

ollama pull embeddinggemma                            # recuperación del léxico
make pull-model TAG=genlingo-2026-10c-e2b-nomulti     # David de escena (Q5_K_M, 3.62 GB)
make pull-model TAG=genlingo-2026-10-e2b-q5_k_m      # David anterior (make up y make preflight lo esperan)

make up       # Ollama + David precalentado + servicio (:8787); abre la página de comparación
```

Ensayo sin red ni GPU: pon `MOCK_AI=1` en `.env` y corre `make up` (modelos simulados y deterministas).

## Día de la charla

```bash
make up                                          # terminal 1: se queda corriendo
make stage-on && make warmup && make preflight   # terminal 2: modelos cargados, ejemplos verificados, todo en [ok]
# … la charla …
make stage-off                                   # después: la app del público vuelve a escalar a cero
```

El guion de la demo (la página de comparación: cómo abrirla, qué ejemplos tocar, qué decir y qué hacer si algo falla) está en [DEMO.md](DEMO.md).
