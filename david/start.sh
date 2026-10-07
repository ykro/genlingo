#!/bin/bash
# David's container entrypoint. A cold start used to spend most of its ~4 minutes reading files a few
# pages at a time: Cloud Run streams the image lazily, so the GPU libraries (read while Ollama probes the
# GPU and the first time each kernel runs) and the GGUF (mapped by llama.cpp and touched piece by piece:
# its warm-up run alone took 60 s, the first translations ~50 s more) came in on demand. Here they are
# read once, front to back in parallel chunks: the GPU libraries before Ollama starts, the models while
# it starts. Then both models are loaded and kept loaded, so the first request from the page finds David
# ready.
set -u
PORT="${OLLAMA_HOST##*:}"
log() { echo "[start] $(date -u +%T) $*"; }

prefetch() {  # prefetch <find args…>: read every file over 1 MB that find lists into the page cache
  local f size chunk parts=8 i
  while IFS= read -r f; do
    size=$(stat -c %s "$f")
    chunk=$(( size / parts / 16777216 + 1 ))   # 16 MiB blocks per part
    for ((i = 0; i < parts; i++)); do
      dd if="$f" of=/dev/null bs=16M skip=$((i * chunk)) count="$chunk" status=none &
    done
  done < <(find -L "$@" -type f -size +1M)
  wait
}

api() {  # api <path> <json>: POST to the local Ollama with bash only (the image has no curl)
  local body="$2"
  exec 3<>"/dev/tcp/127.0.0.1/${PORT}" || return 1
  printf 'POST %s HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n%s' \
    "$1" "${#body}" "$body" >&3
  head -c 200 <&3 | head -1
  exec 3>&-
}

t0=$SECONDS
# Ollama's own libraries and the CUDA 13 ones it uses on the L4 (OLLAMA_LLM_LIBRARY), not the other backends.
prefetch /usr/lib/ollama -maxdepth 1 && prefetch "/usr/lib/ollama/${OLLAMA_LLM_LIBRARY:-cuda_v13}"
log "GPU libraries read in $((SECONDS - t0)) s"
prefetch "$OLLAMA_MODELS" &
PREFETCH=$!
ollama serve &
SERVE=$!
for _ in $(seq 1 120); do api /api/version '{}' >/dev/null 2>&1 && break; sleep 0.5; done
wait "$PREFETCH"
log "model files read in $((SECONDS - t0)) s"
api /api/generate "{\"model\":\"${DAVID_TAG}\",\"keep_alive\":-1}" & A=$!
api /api/embed "{\"model\":\"${EMBEDDING_MODEL}\",\"input\":\"hola\",\"keep_alive\":-1}" & B=$!
wait "$A" "$B"
log "models loaded $((SECONDS - t0)) s after start"
wait "$SERVE"
