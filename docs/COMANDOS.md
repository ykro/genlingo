# Comandos

Todos los comandos del `Makefile`. `make help` los lista con su descripción. Volver al [README](../README.md). [English version](COMANDOS.en.md).

| Comando | Qué hace |
| --- | --- |
| `make help` | Lista los comandos con su descripción. |
| `make up` | Arranca Ollama (con `OLLAMA_MAX_LOADED_MODELS=4`), precarga los tres modelos de escena (David, el del mes pasado y EmbeddingGemma), levanta el duelo y la vista del presentador (la recompila si cambió su código). Funciona sin Wi-Fi y sin público. |
| `make reset` | Pone en cero rondas, votos, cola y marcador locales; con `AUDIENCE_FEED=1` y red, también borra las rondas del evento en Firestore. |
| `make test` | Pruebas de Python (`MOCK_AI=1`), Vitest, `tsc`, ESLint y, con JDK 21, las reglas de Firestore en el emulador. |
| `make eval` | Pasa el set de prueba por los modelos base, cada David y Goliath (con y sin glosario) y escribe `evals/report.md`. Acepta `EVAL_ARGS="--limit 50 --no-goliath"`. |
| `make eval-dev` | Pasa el set de desarrollo (decisiones de datos, ablaciones) y escribe `evals/report_dev.md`: `make eval-dev [EVAL_ARGS="--nbest 4"]`. |
| `make niches` | Calcula los nichos registrados de antemano ([evals/niche.md](../evals/niche.md)) a partir del último eval de prueba y escribe `evals/niche_report.md`. |
| `make test-set` | Construye los pares de prueba a partir de oraciones reales de la web y los valida contra el banco de términos (`auto_validated` o `rejected`, sin intervención humana). |
| `make real-pairs` | Pares de entrenamiento anclados en oraciones reales (las dos direcciones), validados contra el banco. |
| `make ambiguous-terms` | Marca los términos del banco que también son palabras comunes («cámara», «servir»), para que las métricas no los cuenten. |
| `make counterparts` | Tabla término → contraparte validada por significado (vecinos más cercanos mutuos + revisión del top 5 con Gemini) en `data/counterparts.jsonl`. |
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

## Arranque rápido

Requisitos (versiones en [ONBOARDING.md](ONBOARDING.md)): macOS con Apple Silicon, `uv`, Node 24, Ollama, `gcloud` con ADC.

```bash
cp .env.example .env                                  # modelos, precios y rutas
(cd duel && uv sync)                                  # servicio del duelo (Python 3.12)
(cd web && npm install && cp .env.example .env.local) # vista del presentador y app del público
gcloud auth application-default login                 # Goliath (Vertex AI) y descarga de modelos

ollama pull embeddinggemma                            # recuperación del léxico
make pull-model TAG=genlingo-2026-10c-e2b-nomulti     # David de escena (Q5_K_M, 3.62 GB)
make pull-model TAG=genlingo-2026-10-e2b-q5_k_m      # David del mes pasado (tecla M)

make up       # Ollama + David precalentado + duelo (:8787) + vista del presentador (:3000/presenter)
```

Ensayo sin red ni GPU: pon `MOCK_AI=1` en `.env` y corre `make up` (modelos simulados y deterministas).

El guion de la demo en escena, pantalla por pantalla (teclas, frases, qué decir, tiempos y qué hacer si algo falla), está en [DEMO.md](DEMO.md).
