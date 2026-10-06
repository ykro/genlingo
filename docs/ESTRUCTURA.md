# Estructura del repositorio

Qué corre dónde, cómo se ve y dónde está cada cosa en el código. Volver al [README](../README.md). [English version](ESTRUCTURA.en.md).

## Arquitectura

![Qué corre en la laptop y qué en la nube](diagrams/arquitectura.png)

Fuente editable: [diagrams/arquitectura.html](diagrams/arquitectura.html) (también en `.svg`). Por qué cada pieza corre en la laptop o en la nube: [DECISIONES.md](DECISIONES.md#qué-corre-en-la-laptop-y-por-qué).

El ciclo de cada mes, de los datos al escenario y de vuelta:

![Ciclo mensual](diagrams/ciclo-mensual.png)

## Pantallas

![Vista del presentador: ronda de evaluación, David y Goliath traducen la misma frase](demo/02-ronda-evaluacion.png)

![App del público en un teléfono: frase enviada y voto](demo/06-publico-telefono.png)

La demo de la charla, la página para traducir con David, en [DEMO.md](DEMO.md).

## Mapa del repositorio

```
duel/                 Servicio del duelo (FastAPI) — corre en la laptop
  duel_core/          Núcleo reutilizable: duelo en paralelo, clientes Ollama/Gemini/mock,
                      conectividad, costo con tarifas fechadas, chrF++, percentiles
  genlingo_duel/      La app: prompts, glosario, banco de términos, arena, marcador (SQLite),
                      puente con Firestore (audience_feed.py), API (main.py), la página para
                      traducir (translate_page.py, static/traducir.html)
  tests/              Pruebas del servicio (MOCK_AI=1)
web/                  Next.js: app del público (/), moderación (/admin), vista del presentador (/presenter)
  app/api/            Rutas del público (frases, pares, votos, config) y de admin
  lib/server/         Auth + App Check, límite de 20 s, blocklist, validación, Firestore
  e2e/                Ensayos con Playwright y con el emulador de Android
  firestore.rules     Ningún cliente escribe directo; todo pasa por la API
data/                 terms.jsonl, raw/web_usage.jsonl, pairs/, review/, SOURCES.md, DATASHEET.md,
                      translate_examples.json (los ejemplos de /traducir, verificados)
scripts/              Construcción de datos, revisión, export, reset, make up, warmup, preflight
train/                train_lora.py, finish.py, submit_job.py, finish_local.py, train_local.py, notebook, runs/
evals/                run_eval.py, term_accuracy.py, report.py, report.md, experiments/
infra/                Scripts gcloud numerados (01–06, 60 stage on/off) y env.sh compartido
docs/                 DEMO, ONBOARDING, BITACORA, DECISIONES, COMANDOS, ESTRUCTURA, CREDITOS,
                      diagrams/ (HTML + SVG + PNG), demo/ (capturas del guion)
```

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
