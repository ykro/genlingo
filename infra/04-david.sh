#!/usr/bin/env bash
# David on Cloud Run with a GPU (NVIDIA L4, europe-west4: where the project has L4 quota).
# Private service: only the page's service account may call it. Scales to zero when idle
# (min-instances 0, max 1), so it costs nothing between talks; the page wakes it when opened.
# Idempotent: the image tag is a hash of the recipe and the model, so an unchanged David is not rebuilt.
source "$(dirname "$0")/env.sh"
ROOT="$(cd "$INFRA_DIR/.." && pwd)"
set -a; [ -f "$ROOT/.env" ] && source "$ROOT/.env" || source "$ROOT/.env.example"; set +a
DAVID_REGION="${DAVID_REGION:-europe-west4}"
SERVICE="${APP}-david"
SA="${APP}-david"
SA_EMAIL="${SA}@${PROJECT_ID}.iam.gserviceaccount.com"
EU_AR="${DAVID_REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}"
GGUF="${DAVID_MODEL_TAG}-$(echo "${QUANT}" | tr 'A-Z' 'a-z').gguf"
HASH="$( (cat "$ROOT/david/Dockerfile" "$ROOT/david/cloudbuild.yaml"; echo "$DAVID_MODEL_TAG $GGUF $EMBEDDING_MODEL";
          gcloud storage objects describe "${MODELS_BUCKET}/${DAVID_MODEL_TAG}/${GGUF}" --format='value(md5_hash)') | shasum -a 256 | cut -c1-12)"
IMAGE="${EU_AR}/${SERVICE}:${HASH}"

say "Artifact Registry ${AR_REPO} in ${DAVID_REGION}"
exists gcloud artifacts repositories describe "$AR_REPO" --location="$DAVID_REGION" \
  || gcloud artifacts repositories create "$AR_REPO" --repository-format=docker --location="$DAVID_REGION" \
       --description="Charlas 2027 images that run in ${DAVID_REGION} (GPU)"

say "Service account ${SA_EMAIL} (no roles: David only answers requests)"
exists gcloud iam service-accounts describe "$SA_EMAIL" \
  || gcloud iam service-accounts create "$SA" --display-name="Genlingo David (Ollama on GPU)"

if exists gcloud artifacts docker images describe "$IMAGE"; then
  say "Image ${IMAGE} already built"
else
  say "Building ${IMAGE} (Cloud Build, ~10 min)"
  gcloud builds submit "$ROOT/david" --config "$ROOT/david/cloudbuild.yaml" --region "$REGION" --quiet \
    --substitutions "_IMAGE=${IMAGE},_MODELS_BUCKET=${MODELS_BUCKET},_DAVID_TAG=${DAVID_MODEL_TAG},_GGUF=${GGUF},_EMBEDDING_MODEL=${EMBEDDING_MODEL}"
fi

say "Deploying ${SERVICE} (${DAVID_REGION}, 1x L4)"
gcloud run deploy "$SERVICE" --image "$IMAGE" --region "$DAVID_REGION" --quiet \
  --service-account "$SA_EMAIL" --no-allow-unauthenticated \
  --gpu 1 --gpu-type nvidia-l4 --no-gpu-zonal-redundancy \
  --cpu 4 --memory 16Gi --no-cpu-throttling \
  --min-instances 0 --max-instances 1 --concurrency 8 --timeout 600 \
  --port 8080 --labels "app=${APP}"
gcloud run services describe "$SERVICE" --region "$DAVID_REGION" --format='value(status.url)'
