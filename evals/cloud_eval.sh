#!/usr/bin/env bash
# Entry point of the eval job: start Ollama, load the embedding model, run evals/run_eval.py with the
# job's arguments, and copy the report and the raw results to EVAL_OUT (a folder on the mounted
# staging bucket, read back by `make eval`).
set -euo pipefail
: "${EVAL_OUT:?set EVAL_OUT}"
# Same Ollama settings as David's service (david/Dockerfile), so latencies are comparable; its log goes
# to the job's log.
export OLLAMA_KEEP_ALIVE=-1 OLLAMA_NUM_PARALLEL=4 OLLAMA_MAX_LOADED_MODELS=2 OLLAMA_CONTEXT_LENGTH=2048
ollama serve 2>&1 | sed 's/^/[ollama] /' &
for _ in $(seq 1 60); do ollama list >/dev/null 2>&1 && break; sleep 1; done
ollama pull "${EMBEDDING_MODEL}"
cd /app
uv run --project duel --no-sync python evals/run_eval.py "$@"
mkdir -p "$EVAL_OUT/results"
cp evals/report*.md "$EVAL_OUT/" 2>/dev/null || true
cp evals/results/*.json "$EVAL_OUT/results/"
echo "eval outputs -> $EVAL_OUT"
