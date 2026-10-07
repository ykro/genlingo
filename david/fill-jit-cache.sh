#!/bin/bash
# Fills CUDA's JIT cache on a real L4 (infra/07-david-jit-cache.sh runs it as a Cloud Run GPU job with
# David's image). Ollama's CUDA kernels ship as PTX for this GPU, so the driver compiles them the first
# time each one runs: that was most of David's cold start (the warm-up runs, and seconds on the first
# phrase of each new shape). This starts David like Cloud Run does, runs every shape the page uses
# (prompts of many lengths, 1 to 16 at a time, embedding batches of 1 to 64) and saves the compiled
# kernels to /cache/cuda-jit; the next image build bakes them in (david/Dockerfile, CUDA_CACHE_PATH).
export LC_ALL=C   # ${#body} counts bytes, as Content-Length needs
export CUDA_CACHE_PATH=/tmp/cuda-jit CUDA_CACHE_MAXSIZE=4294967296
/start.sh > /tmp/start.log 2>&1 &
until grep -q "models loaded" /tmp/start.log; do sleep 2; done
grep "\[start\]" /tmp/start.log
echo "== JIT cache after loading: $(du -sh /tmp/cuda-jit | cut -f1)"
post() {  # post <path> <json>: one request, at most 120 s
  timeout 120 bash -c 'exec 3<>/dev/tcp/127.0.0.1/8080
    printf "POST %s HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n%s" "$1" "${#2}" "$2" >&3
    head -1 <&3' _ "$1" "$2"
}
words="qué onda vos ese plan estuvo bien chilero pero el final me dio cringe y la neta no traigo pisto para el bus"
for round in 1 2 3; do
  for n in 1 2 4 8 16; do
    pids=()
    for i in $(seq 1 $n); do
      len=$(( (i * 7 + round * 13) % 60 + 3 ))
      p=$(for j in $(seq 1 $len); do echo -n "$words " ; done | cut -c1-$((len * 12)))
      post /api/generate "{\"model\":\"${DAVID_TAG}\",\"prompt\":\"Traduce: $p\",\"stream\":false,\"options\":{\"num_predict\":$(( 8 + i * 4 )),\"temperature\":0}}" & pids+=($!)
    done
    wait "${pids[@]}"   # not a bare wait: that would wait for Ollama too
    echo "round $round, $n at a time: $(du -sh /tmp/cuda-jit | cut -f1)"
  done
done
for b in 1 2 3 5 8 13 21 34 64; do
  inputs=$(for j in $(seq 1 $b); do echo -n "\"término $j: significado número $j de la jerga\","; done)
  post /api/embed "{\"model\":\"${EMBEDDING_MODEL}\",\"input\":[${inputs%,}]}"
done
echo "== JIT cache:"; du -sh /tmp/cuda-jit; find /tmp/cuda-jit -type f | wc -l
rm -rf /cache/cuda-jit && mkdir -p /cache/cuda-jit && cp -r /tmp/cuda-jit/. /cache/cuda-jit/ && echo "saved to /cache/cuda-jit"
