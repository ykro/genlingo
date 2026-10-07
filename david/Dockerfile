# David in the cloud: Ollama on a Cloud Run GPU (NVIDIA L4) with the stage model and the embedding
# model baked into the image, so a cold start only loads weights (no download at start). start.sh
# reads the model files in parallel and loads both models before the first request (see its header).
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
ARG DAVID_TAG
ARG EMBEDDING_MODEL
COPY --from=models /models /models
COPY start.sh /start.sh
# CUDA kernels already compiled for the L4 (infra/07-david-jit-cache.sh): without them the driver compiles
# each one from PTX on its first run, which took most of a cold start.
COPY cuda-jit/ /cuda-jit/
# Port 8080 for Cloud Run; models stay loaded while the instance lives; up to 16 translations at a
# time on the one GPU (the throughput measured for the README's projections). Only the CUDA library
# is probed for GPUs (the default probe of every backend took ~20 s of each cold start).
ENV OLLAMA_MODELS=/models OLLAMA_HOST=0.0.0.0:8080 OLLAMA_KEEP_ALIVE=-1 OLLAMA_NUM_PARALLEL=16 \
    OLLAMA_MAX_LOADED_MODELS=2 OLLAMA_CONTEXT_LENGTH=2048 OLLAMA_LLM_LIBRARY=cuda_v13 \
    CUDA_CACHE_PATH=/cuda-jit CUDA_CACHE_MAXSIZE=4294967296 \
    DAVID_TAG=${DAVID_TAG} EMBEDDING_MODEL=${EMBEDDING_MODEL}
EXPOSE 8080
ENTRYPOINT ["/start.sh"]
