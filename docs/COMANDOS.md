# Comandos

Todos los comandos del `Makefile`. `make help` los lista con su descripción. Volver al [README](../README.md). [English version](COMANDOS.en.md).

Para usar la demo no hace falta ninguno: la página está en **https://genlingo-611681112050.us-central1.run.app** ([DEMO.md](DEMO.md)). Estos comandos sirven para reconstruirla, entrenar a David y evaluarlo. Todo corre en Google Cloud; la laptop solo manda los trabajos.

| Comando | Qué hace |
| --- | --- |
| `make help` | Lista los comandos con su descripción. |
| `make deploy` | Despliega a David (`infra/04-david.sh`: imagen de Ollama con el David de `DAVID_MODEL_TAG` y EmbeddingGemma dentro, servicio privado de Cloud Run con una GPU L4 en `europe-west4`, `min-instances=0`, `max-instances=1`) y la página (`infra/05-page.sh`: servicio público en `us-central1` cuya cuenta de servicio solo puede llamar a Gemini y a David). La imagen de David solo se reconstruye si cambió su receta, el modelo o los kernels de CUDA compilados (`infra/07-david-jit-cache.sh`, que se corre solo al cambiar la versión de Ollama). |
| `make check` | Revisa la página en vivo como la usa el navegador: la abre, despierta a David (dice cuánto tardó) y traduce cada ejemplo con los dos. Falla si David no acierta toda la jerga de un ejemplo o si Goliath la acierta. |
| `make screenshots` | Capturas de la página en vivo en un navegador real, tema claro, en `docs/demo/`: proyector (1920×1080), laptop (1280×800), tableta (768×1024) y teléfonos (375×812 y 414×896), con una frase escrita y la nota «¿Cómo se lee esta página?». Avisa si algo se sale a lo ancho. |
| `make capacity` | Mide cuántas traducciones por hora aguanta David (1, 4, 8 y 16 a la vez) y el tiempo y costo por traducción de los dos, con el mismo código de la página → `docs/data/capacity.json`. De ahí salen las proyecciones del README. Abre la página antes para que David esté despierto. |
| `make test` | Pruebas de Python sin red (`MOCK_AI=1`): la página, la revisión por término, los datos, el eval y el reporte. |
| `make eval` | Pasa el set de prueba por los modelos base, cada David y Goliath (con y sin léxico) en Cloud Run Jobs con una GPU L4 (`infra/06-eval-job.sh`): cada job corre Ollama adentro con los kernels de CUDA ya compilados de David y carga cada modelo desde el bucket de modelos. Como un job con GPU dura como máximo 1 hora, corre los grupos de `EVAL_GROUPS` uno tras otro y `evals/merge_results.py` los junta en `evals/report.md`. Necesita `make data-pull` antes. |
| `make eval-dev` | Lo mismo con el set de desarrollo (decisiones de datos, ablaciones): `evals/report_dev.md`. `make eval-dev [EVAL_ARGS="--nbest 4"]`. |
| `make eval-probe` | La sonda de jerga Gen Z general (32 oraciones reales, en las dos direcciones, como español neutro y como Guatemala; `data/eval/probe_genz.jsonl`): `evals/report_probe.md`. `make eval-probe EVAL_ARGS="--models <tag>,goliath"`. |
| `make data-pull` | Baja del bucket privado (`PRIVATE_DATA_URI`) a `data/.private/` las oraciones citadas de fuentes que no se pueden redistribuir, y la caché de vectores del banco. Lo necesitan los scripts de datos, el eval y el build de la página. |
| `make data-push` | Sube `data/.private/` al bucket privado después de una ronda de datos. |
| `make niches` | Calcula los nichos registrados de antemano ([evals/niche.md](../evals/niche.md)) a partir del último eval de prueba y escribe `evals/niche_report.md`. |
| `make test-set` | Construye los pares de prueba a partir de oraciones reales de la web y los valida contra el banco de términos (`auto_validated` o `rejected`, sin intervención humana). |
| `make real-pairs` | Pares de entrenamiento anclados en oraciones reales (las dos direcciones), validados contra el banco. |
| `make ambiguous-terms` | Marca los términos del banco que también son palabras comunes («cámara», «servir»), para que las métricas no los cuenten. |
| `make counterparts` | Tabla término → contraparte validada por significado (vecinos más cercanos mutuos + revisión del top 5 con Gemini) en `data/counterparts.jsonl`. |
| `make pairs` | Genera los pares sintéticos de un término con `GEMINI_MODEL` (de pago; `SYNTHETIC_PAIRS_TARGET`, hoy 1,500). Los pares de 2–3 términos (`scripts/generate_multi_pairs.py`, `data/pairs/synthetic_multi.jsonl`) no entran en la receta de David y no se regeneran aquí. |
| `make datasheet` | Recuenta `data/DATASHEET.md`. |
| `make data` | `test-set` + `real-pairs` + `pairs` + `datasheet`. |
| `make train-data` | Renderiza los pares de entrenamiento al JSONL de chat con el mismo prompt (y léxico) que usa la página, con la receta de David: sin los pares de 2–3 términos y sin etapa ORPO. El léxico usa el modelo de embeddings del servicio de David (`DAVID_URL`). `MULTI=1` incluye esos pares y `ORPO=1` arma también `data/train/pref.jsonl` (variantes descartadas, para ablaciones). |
| `make train` | Entrena en un Cloud Run Job con una L4 y después fusiona y convierte a GGUF en un job de CPU: `make train [TAG=…] [QUANT=Q5_K_M] [TRAIN_ARGS=…]`; `TAG` vale por defecto `genlingo-<año>-<mes>` del día. Corre `make train-data` antes (acepta `MULTI=1` y `ORPO=1`). Escribe `train/runs/<tag>.json`. Para poner el modelo nuevo en la página: `DAVID_MODEL_TAG=<tag>` en `.env` y `make deploy`. |

## Arranque rápido

Requisitos (versiones en [ONBOARDING.md](ONBOARDING.md)): `uv` y `gcloud` con ADC en el proyecto `ai-experiments-487722`.

```bash
cp .env.example .env                  # modelos, precios y buckets
(cd duel && uv sync)                  # código de la página y del eval (Python 3.12)
gcloud auth application-default login
make deploy                           # David (GPU) + la página
make check                            # la página en vivo, de punta a punta
```

## Día de la charla

Nada que ejecutar: abre la página unos diez minutos antes ([DEMO.md](DEMO.md)).
