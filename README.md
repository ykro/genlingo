# Genlingo — traductor generacional: Gen Z ↔ papás

Demo de la charla *«David vs. Goliath: cómo un modelo pequeño le gana a un modelo frontier»*. «no manches, la peli estuvo bien chilera pero el final me dio cringe» ↔ «la película estuvo bien chévere pero el final me dio pena ajena». **David** es Gemma 4 E2B afinado con LoRA sobre pares propios y corre en la laptop del escenario con Ollama, **sin internet**. **Goliath** es Gemini (`GEMINI_MODEL`, hoy `gemini-3.8-flash`) en Vertex AI. El público entra con un QR, manda frases desde el teléfono y vota quién tradujo mejor; una métrica objetiva compara a los dos contra referencias humanas.

[English version](README.en.md)

## Qué vas a aprender

1. **Datos propios con `origin`:** cada par dice de dónde salió (`web`, `synthetic` o `human`); sin eso no se puede evaluar ni reentrenar cada mes.
2. **Banco de términos y oraciones reales:** 406 términos de 57 fuentes y 334 pares anclados en oraciones reales; la ventaja de David son sus datos.
3. **LoRA en Cloud Run Jobs:** una L4 entrena y un job de CPU fusiona y exporta GGUF; cada ejecución registra su duración y costo.
4. **El costo de comprimir:** f16 contra Q4_K_M, Q5_K_M, Q6_K, Q8_0 e imatrix, en tamaño, latencia y jerga perdida.
5. **Evals con métricas de término:** chrF++ más *jerga resuelta* y *cambios acertados*; las derrotas de David se publican.
6. **Reentrenamiento mensual y offline por diseño:** la tecla `M` enfrenta al David del mes pasado; sin red, Goliath sale «sin conexión» y David sigue.

![Qué corre en la laptop y qué en la nube](docs/diagrams/arquitectura.png)

![Qué se prueba en la demo](docs/diagrams/que-se-prueba.png)

## Resultado

Eval del 2026-10-02 sobre 399 frases de prueba web `auto_validated` ([tabla completa y salvedades](docs/DECISIONES.md#resultados)):

| Variante | Jerga resuelta | papás → Gen Z | chrF++ | p50 | Costo / 1,000 frases |
| --- | --- | --- | --- | --- | --- |
| **David en escena** (`genlingo-2026-10b-e2b`, Q5_K_M, 3.62 GB) | **82 %** | **59 %** | **56.6** | **557 ms** | **$0** |
| David anterior (`genlingo-2026-10-e2b-q5_k_m`, tecla `M`) | 74 % | 43 % | 55.4 | 564 ms | $0 |
| Goliath `gemini-3.8-flash` | 78 % | 51 % | 53.1 | 3.26 s | $1.08 |
| Goliath + el mismo glosario | 82 % | 62 % | 56.5 | 3.84 s | $1.24 |
| Copiar la frase (línea base) | 1 % | 3 % | 53.2 | — | — |

Con el mismo glosario empatan en jerga: la ventaja de David no es ser mejor modelo, son sus datos. Reentrenar cada mes cuesta $0.71 de punta a punta en la nube ([costo por ejecución](docs/DECISIONES.md#costo-de-entrenamiento-por-ejecución)).

## Lo que no funcionó

Una línea por callejón sin salida; el detalle está en [docs/BITACORA.md](docs/BITACORA.md).

- **Paráfrasis libres:** David quedó por debajo de copiar la frase.
- **Un modelo más grande (E4B):** la misma jerga resuelta que E2B y más lento.
- **Q4_K_M:** perdía 7 puntos de jerga contra f16.
- **Entrenar, fusionar y convertir en un solo job:** murió por memoria; ahora son dos jobs.
- **Contrapartes por *embedding*:** la mayoría de los enlaces significaban otra cosa.

## Arranque rápido

```bash
cp .env.example .env && (cd duel && uv sync) && (cd web && npm install && cp .env.example .env.local)
gcloud auth application-default login                 # Goliath (Vertex AI) y descarga de modelos
ollama pull embeddinggemma && make pull-model TAG=genlingo-2026-10b-e2b   # glosario + David de escena
make up       # Ollama + David precalentado + duelo (:8787) + vista del presentador (:3000/presenter)
make test     # pruebas sin red (MOCK_AI=1)
```

Ensayo sin red ni GPU: `MOCK_AI=1` en `.env` y `make up`. Requisitos, el David del mes pasado y la versión completa en [docs/COMANDOS.md](docs/COMANDOS.md#arranque-rápido).

## App desplegada

- Público: **https://genlingo-611681112050.us-central1.run.app** (evento `ensayo`, país `GT`); moderación en `/admin` (cuenta con `admin=true`).
- Vista del presentador: local, `http://127.0.0.1:3000/presenter` con `make up`.

## Documentación

- [docs/DEMO.md](docs/DEMO.md): guion de la demo, pantalla por pantalla (teclas, frases, qué decir, tiempos y qué hacer si algo falla).
- [docs/ONBOARDING.md](docs/ONBOARDING.md): instalación, nube, cadena de datos y entrenamiento, recorrido del código, problemas frecuentes y lista del día.
- [docs/BITACORA.md](docs/BITACORA.md): la historia de David iteración por iteración, con los callejones sin salida y los nichos.
- [docs/DECISIONES.md](docs/DECISIONES.md): lo que enseña la demo en detalle, cada decisión técnica, resultados completos y costo de entrenamiento.
- [docs/COMANDOS.md](docs/COMANDOS.md): todos los comandos `make` y el arranque rápido completo.
- [docs/ESTRUCTURA.md](docs/ESTRUCTURA.md): arquitectura, ciclo mensual, pantallas, mapa del repositorio y versiones.
- [docs/CREDITOS.md](docs/CREDITOS.md): procedencia de los datos y licencias.
- [evals/report.md](evals/report.md) y [evals/niche.md](evals/niche.md): reporte del eval y nichos definidos antes de mirar resultados.
- [docs/diagrams/](docs/diagrams/): arquitectura, qué se prueba, ciclo mensual, resultados y bitácora (HTML, SVG y PNG).
- [data/SOURCES.md](data/SOURCES.md) y [data/DATASHEET.md](data/DATASHEET.md): fuentes y datasheet de los datos.
