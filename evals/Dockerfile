# The eval job (infra/06-eval-job.sh): Ollama and the eval code in one image, on a Cloud Run GPU.
# Models are not baked in: the job loads each one from the models bucket (mounted) while it runs.
ARG OLLAMA_VERSION=0.35.0
FROM ollama/ollama:${OLLAMA_VERSION}
ARG OLLAMA_VERSION
ENV OLLAMA_VERSION=${OLLAMA_VERSION}
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /bin/uv
ENV UV_PYTHON_INSTALL_DIR=/opt/python UV_LINK_MODE=copy PYTHONUNBUFFERED=1
WORKDIR /app
COPY duel/pyproject.toml duel/uv.lock duel/.python-version duel/
RUN cd duel && uv sync --frozen --no-dev --no-install-project
COPY duel/ duel/
COPY evals/ evals/
COPY data/ data/
COPY train/runs/ train/runs/
RUN cd duel && uv sync --frozen --no-dev
ENTRYPOINT ["bash", "/app/evals/cloud_eval.sh"]
