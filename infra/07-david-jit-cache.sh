#!/usr/bin/env bash
# CUDA's compiled kernels for David, made once on a real L4. Ollama's CUDA kernels come as PTX for this
# GPU, so the driver compiles each one the first time it runs: that was most of a cold start. This runs
# david/fill-jit-cache.sh as a one-off Cloud Run GPU job with David's current image and keeps the
# compiled kernels in the models bucket (cuda-jit/ollama-<version>-l4/); infra/04-david.sh bakes them into
# the image. Run it again after changing the Ollama version (the cache is per version and GPU driver; with a
# stale cache David still works, he just compiles again on start).
source "$(dirname "$0")/env.sh"
ROOT="$(cd "$INFRA_DIR/.." && pwd)"
set -a; [ -f "$ROOT/.env" ] && source "$ROOT/.env" || source "$ROOT/.env.example"; set +a
DAVID_REGION="${DAVID_REGION:-europe-west4}"
JOB="${APP}-david-jit"
SA_EMAIL="${APP}-eval@${PROJECT_ID}.iam.gserviceaccount.com"   # read/write on the staging bucket
STAGING_BUCKET="${STAGING_BUCKET:-gs://${PROJECT_ID}-train-eu}"
OLLAMA_VERSION="$(sed -n 's/^ARG OLLAMA_VERSION=//p' "$ROOT/david/Dockerfile")"
WORK="${APP}/cuda-jit"
DEST="${MODELS_BUCKET}/cuda-jit/ollama-${OLLAMA_VERSION}-l4"
IMAGE="$(gcloud run services describe "${APP}-david" --region "$DAVID_REGION" --format='value(spec.template.spec.containers[0].image)')"
: "${IMAGE:?deploy David first: infra/04-david.sh}"

gcloud storage cp "$ROOT/david/fill-jit-cache.sh" "${STAGING_BUCKET}/${WORK}/fill-jit-cache.sh" --quiet
verb=(create)
exists gcloud run jobs describe "$JOB" --region "$DAVID_REGION" && verb=(update --clear-volumes --clear-volume-mounts)
say "Cloud Run Job ${JOB} (${DAVID_REGION}, 1x L4) with ${IMAGE##*/}"
gcloud run jobs "${verb[@]}" "$JOB" --region "$DAVID_REGION" --image "$IMAGE" --service-account "$SA_EMAIL" \
  --gpu 1 --gpu-type nvidia-l4 --no-gpu-zonal-redundancy --cpu "${DAVID_CPU:-4}" --memory "${DAVID_MEMORY_GIB:-16}Gi" \
  --task-timeout 30m --max-retries 0 --tasks 1 --quiet \
  --add-volume "name=staging,type=cloud-storage,bucket=${STAGING_BUCKET#gs://}" \
  --add-volume-mount "volume=staging,mount-path=/mnt/staging" \
  --command bash --args="-c,ln -s /mnt/staging/${WORK} /cache && bash /cache/fill-jit-cache.sh"
gcloud run jobs execute "$JOB" --region "$DAVID_REGION" --wait

say "Keeping the kernels in ${DEST}"
gcloud storage rsync -r --delete-unmatched-destination-objects "${STAGING_BUCKET}/${WORK}/cuda-jit" "$DEST" --quiet
gcloud storage du -s "$DEST"
