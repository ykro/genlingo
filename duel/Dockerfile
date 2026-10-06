# The comparison page on Cloud Run (infra/05-page.sh). Built from the repo root: it needs the
# page code (duel/), the data the page reads (term bank, counterparts, examples, cached term
# embeddings) and the training run files (David's prompt style).
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /bin/uv
WORKDIR /app
COPY duel/pyproject.toml duel/uv.lock duel/
RUN cd duel && uv sync --frozen --no-dev --no-install-project
COPY duel/ duel/
COPY data/terms.jsonl data/counterparts.jsonl data/translate_examples.json data/
COPY data/eval/terms_test.jsonl data/eval/
COPY data/.cache/term_embeddings.json data/.cache/
COPY train/runs/ train/runs/
RUN cd duel && uv sync --frozen --no-dev
ENV PYTHONUNBUFFERED=1 PORT=8080
CMD ["sh", "-c", "cd /app/duel && exec uv run --no-sync uvicorn genlingo_duel.main:create_app --factory --host 0.0.0.0 --port ${PORT}"]
