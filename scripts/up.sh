#!/usr/bin/env bash
# `make up`: everything the stage needs on the laptop, working with Wi-Fi off.
#   Ollama (David, last month's David, EmbeddingGemma) -> duel service (:8787) -> presenter view (:3000/presenter)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
set -a; [ -f .env ] && source .env; set +a
PORT="${DUEL_PORT:-8787}"
fail() { echo "!! $*" >&2; exit 1; }
# Never die silently: name the command that failed.
trap 'echo "!! make up se detuvo en scripts/up.sh:${LINENO}: ${BASH_COMMAND}" >&2' ERR

if [ "${MOCK_AI:-0}" = 1 ]; then
  echo "(MOCK_AI=1: modelos simulados, sin Ollama)"
else
  # Three models must stay loaded at once (David now, David last month, EmbeddingGemma); Ollama's
  # default can evict one mid-talk. The setting only applies to an Ollama we start ourselves.
  export OLLAMA_MAX_LOADED_MODELS="${OLLAMA_MAX_LOADED_MODELS:-4}"
  export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-2h}"
  export OLLAMA_NUM_PARALLEL="${OLLAMA_NUM_PARALLEL:-4}"  # DAVID_NBEST answers in parallel, not one after another
  if ! curl -sf http://127.0.0.1:11434/api/version >/dev/null; then
    command -v ollama >/dev/null || fail "Ollama no está instalado (brew install ollama)"
    (ollama serve >/tmp/genlingo-ollama.log 2>&1 &)
    for _ in $(seq 1 40); do curl -sf http://127.0.0.1:11434/api/version >/dev/null && break; sleep 0.25; done
    curl -sf http://127.0.0.1:11434/api/version >/dev/null || fail "Ollama no arrancó en 10 s (ver /tmp/genlingo-ollama.log)"
  else
    echo "(Ollama ya estaba corriendo: si no lo arrancó make up, define OLLAMA_MAX_LOADED_MODELS=4 en su configuración)"
  fi

  # Read the list once (grep -q on a pipe under pipefail can kill `ollama list` and fail falsely).
  MODELS="$(ollama list)" || fail "ollama list falló"
  for tag in "${LOCAL_MODEL_TAG}" ${DAVID_PREVIOUS_TAG:+"$DAVID_PREVIOUS_TAG"}; do
    grep -qE "^${tag}(:latest)?[[:space:]]" <<<"$MODELS" || fail "${tag} no está en Ollama: make pull-model TAG=${tag}"
  done
  # Preload exactly the stage models, so the first round doesn't pay a cold load.
  for tag in "${LOCAL_MODEL_TAG}" ${DAVID_PREVIOUS_TAG:+"$DAVID_PREVIOUS_TAG"}; do
    curl -sf http://127.0.0.1:11434/api/chat -d "{\"model\":\"${tag}\",\"messages\":[],\"keep_alive\":\"${OLLAMA_KEEP_ALIVE}\"}" >/dev/null \
      || fail "no se pudo cargar ${tag} en Ollama (¿memoria? mira /tmp/genlingo-ollama.log)"
  done
  if [ -n "${EMBEDDING_MODEL:-}" ]; then
    curl -sf http://127.0.0.1:11434/api/embed \
      -d "{\"model\":\"${EMBEDDING_MODEL}\",\"input\":[\"hola\"],\"keep_alive\":\"${OLLAMA_KEEP_ALIVE}\"}" >/dev/null \
      || fail "${EMBEDDING_MODEL} no responde en Ollama: ollama pull ${EMBEDDING_MODEL} (sin él, el duelo sigue sin glosario)"
  fi
fi

trap 'kill 0' EXIT INT TERM
(cd duel && uv run uvicorn genlingo_duel.main:create_app --factory --host 127.0.0.1 --port "$PORT") &

# Presenter view: production build of web/ (standalone server, like the Cloud Run image), rebuilt
# whenever its sources changed since the last build.
cd web
if [ ! -f .next/BUILD_ID ] || [ -n "$(find app components lib public next.config.ts package.json -newer .next/BUILD_ID -print -quit 2>/dev/null)" ]; then
  npm run build || fail "npm run build falló en web/"  # postbuild copies static files into the standalone server
fi
[ -d .next/standalone/.next/static ] || npm run --silent postbuild  # a build from before postbuild existed
[ -f .next/standalone/server.js ] || fail "falta web/.next/standalone/server.js: borra web/.next y vuelve a correr make up"
(set -a; [ -f .env.local ] && source .env.local; set +a
 DUEL_URL="http://127.0.0.1:${PORT}" PORT=3000 HOSTNAME=127.0.0.1 exec node .next/standalone/server.js) &
cd "$ROOT"
for _ in $(seq 1 120); do curl -sf http://127.0.0.1:3000/api/config >/dev/null && break; sleep 0.5; done
curl -sf http://127.0.0.1:3000/api/config >/dev/null || fail "la vista del presentador no respondió en :3000 (¿puerto ocupado?)"
curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null || fail "el servicio del duelo no respondió en :${PORT}"
echo
echo "  Duelo:      http://127.0.0.1:${PORT}/health"
echo "  Pantalla:   http://127.0.0.1:3000/presenter   (F pantalla completa, E set de prueba, / escribir, M mes pasado)"
echo
[ "${NO_OPEN:-0}" = 1 ] || { command -v open >/dev/null && open "http://127.0.0.1:3000/presenter" || true; }
wait
