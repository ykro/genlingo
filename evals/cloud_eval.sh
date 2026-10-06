#!/usr/bin/env bash
# Entry point of the eval job: start Ollama, load the embedding model, run evals/run_eval.py with the
# job's arguments, and copy the report and the raw results to EVAL_OUT (a folder on the mounted
# staging bucket, read back by `make eval`).
set -euo pipefail
: "${EVAL_OUT:?set EVAL_OUT}"
ollama serve >/tmp/ollama.log 2>&1 &
for _ in $(seq 1 60); do ollama list >/dev/null 2>&1 && break; sleep 1; done
ollama pull "${EMBEDDING_MODEL}"
cd /app
uv run --project duel --no-sync python evals/run_eval.py "$@"
mkdir -p "$EVAL_OUT/results"
cp evals/report*.md "$EVAL_OUT/" 2>/dev/null || true
cp evals/results/*.json "$EVAL_OUT/results/"
echo "eval outputs -> $EVAL_OUT"
