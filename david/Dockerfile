# David in the cloud: Ollama on a Cloud Run GPU (NVIDIA L4) with the stage model and the embedding
# model baked into the image, so a cold start only loads weights (no download at start).
# Built by infra/04-david.sh with Cloud Build; the GGUF and its Modelfile come from the models bucket.
ARG OLLAMA_VERSION=0.35.0

FROM ollama/ollama:${OLLAMA_VERSION} AS models
ARG DAVID_TAG
ARG EMBEDDING_MODEL
ENV OLLAMA_MODELS=/models
COPY model/ /build/
RUN (ollama serve >/tmp/ollama.log 2>&1 &) \
    && for i in $(seq 1 30); do ollama list >/dev/null 2>&1 && break; sleep 1; done \
    && cd /build && ollama create "${DAVID_TAG}" -f Modelfile \
    && ollama pull "${EMBEDDING_MODEL}" \
    && ollama list

FROM ollama/ollama:${OLLAMA_VERSION}
COPY --from=models /models /models
# Port 8080 for Cloud Run; models stay loaded while the instance lives; 4 requests at a time
# (both directions of the page plus the embedding lookups).
ENV OLLAMA_MODELS=/models OLLAMA_HOST=0.0.0.0:8080 OLLAMA_KEEP_ALIVE=-1 OLLAMA_NUM_PARALLEL=4 \
    OLLAMA_MAX_LOADED_MODELS=2 OLLAMA_CONTEXT_LENGTH=2048
EXPOSE 8080
ENTRYPOINT ["ollama", "serve"]
