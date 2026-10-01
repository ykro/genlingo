#!/usr/bin/env bash
# `make up`: everything the stage needs on the laptop, working with Wi-Fi off.
#   Ollama (David) -> duel service (:8787) -> presenter view (:3000/presenter)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
set -a; [ -f .env ] && source .env; set +a
PORT="${DUEL_PORT:-8787}"

if ! curl -sf http://127.0.0.1:11434/api/version >/dev/null; then
  (ollama serve >/tmp/genlingo-ollama.log 2>&1 &)
  for _ in $(seq 1 40); do curl -sf http://127.0.0.1:11434/api/version >/dev/null && break; sleep 0.25; done
fi
if [ "${MOCK_AI:-0}" != 1 ]; then
  ollama list | grep -q "^${LOCAL_MODEL_TAG}[: ]" || { echo "!! David (${LOCAL_MODEL_TAG}) no está en Ollama: make pull-model TAG=${LOCAL_MODEL_TAG}"; exit 1; }
  # Load David now: a cold load costs seconds, and the first round must not pay it.
  curl -sf http://127.0.0.1:11434/api/chat -d "{\"model\":\"${LOCAL_MODEL_TAG}\",\"messages\":[],\"keep_alive\":\"30m\"}" >/dev/null
fi

trap 'kill 0' EXIT INT TERM
(cd duel && uv run uvicorn genlingo_duel.main:create_app --factory --host 127.0.0.1 --port "$PORT") &
# Presenter view: production build of web/, fonts and QR generated locally (no network needed).
(cd web && { [ -f .next/BUILD_ID ] || npm run build; } && DUEL_URL="http://127.0.0.1:${PORT}" npx next start -p 3000 -H 127.0.0.1) &
for _ in $(seq 1 120); do curl -sf http://127.0.0.1:3000/api/config >/dev/null && break; sleep 0.5; done
echo
echo "  Duelo:      http://127.0.0.1:${PORT}/health"
echo "  Pantalla:   http://127.0.0.1:3000/presenter   (F = pantalla completa)"
echo
command -v open >/dev/null && open "http://127.0.0.1:3000/presenter" || true
wait
