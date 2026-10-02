#!/usr/bin/env bash
# `make up`: everything the stage needs on the laptop, working with Wi-Fi off.
#   Ollama (David, last month's David, EmbeddingGemma) -> duel service (:8787) -> presenter view (:3000/presenter)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
set -a; [ -f .env ] && source .env; set +a
PORT="${DUEL_PORT:-8787}"

# Three models must stay loaded at once (David now, David last month, EmbeddingGemma); Ollama's
# default can evict one mid-talk. The setting only applies to an Ollama we start ourselves.
export OLLAMA_MAX_LOADED_MODELS="${OLLAMA_MAX_LOADED_MODELS:-4}"
export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-2h}"
if ! curl -sf http://127.0.0.1:11434/api/version >/dev/null; then
  (ollama serve >/tmp/genlingo-ollama.log 2>&1 &)
  for _ in $(seq 1 40); do curl -sf http://127.0.0.1:11434/api/version >/dev/null && break; sleep 0.25; done
else
  echo "(Ollama ya estaba corriendo: si no lo arrancó make up, define OLLAMA_MAX_LOADED_MODELS=4 en su configuración)"
fi

if [ "${MOCK_AI:-0}" != 1 ]; then
  # Read the list once (grep -q on a pipe under pipefail can kill `ollama list` and fail falsely).
  MODELS="$(ollama list)"
  for tag in "${LOCAL_MODEL_TAG}" ${DAVID_PREVIOUS_TAG:+"$DAVID_PREVIOUS_TAG"}; do
    if ! grep -qE "^${tag}(:latest)?[[:space:]]" <<<"$MODELS"; then
      echo "!! ${tag} no está en Ollama: make pull-model TAG=${tag}"; exit 1
    fi
  done
  # Preload exactly the stage models, so the first round doesn't pay a cold load.
  for tag in "${LOCAL_MODEL_TAG}" ${DAVID_PREVIOUS_TAG:+"$DAVID_PREVIOUS_TAG"}; do
    curl -sf http://127.0.0.1:11434/api/chat -d "{\"model\":\"${tag}\",\"messages\":[],\"keep_alive\":\"${OLLAMA_KEEP_ALIVE}\"}" >/dev/null
  done
  [ -n "${EMBEDDING_MODEL:-}" ] && curl -sf http://127.0.0.1:11434/api/embed \
    -d "{\"model\":\"${EMBEDDING_MODEL}\",\"input\":[\"hola\"],\"keep_alive\":\"${OLLAMA_KEEP_ALIVE}\"}" >/dev/null
fi

trap 'kill 0' EXIT INT TERM
(cd duel && uv run uvicorn genlingo_duel.main:create_app --factory --host 127.0.0.1 --port "$PORT") &

# Presenter view: production build of web/, rebuilt whenever its sources changed since the last build.
cd web
if [ ! -f .next/BUILD_ID ] || [ -n "$(find app components lib public next.config.ts package.json -newer .next/BUILD_ID -print -quit 2>/dev/null)" ]; then
  npm run build
fi
(DUEL_URL="http://127.0.0.1:${PORT}" npx next start -p 3000 -H 127.0.0.1) &
cd "$ROOT"
for _ in $(seq 1 120); do curl -sf http://127.0.0.1:3000/api/config >/dev/null && break; sleep 0.5; done
echo
echo "  Duelo:      http://127.0.0.1:${PORT}/health"
echo "  Pantalla:   http://127.0.0.1:3000/presenter   (F pantalla completa, E set de prueba, / escribir, M mes pasado)"
echo
command -v open >/dev/null && open "http://127.0.0.1:3000/presenter" || true
wait
