#!/usr/bin/env bash
# The comparison page on Cloud Run (public URL). Its service account may call Gemini (Vertex AI)
# and David's private service, nothing else. min-instances 0: it costs nothing between talks.
source "$(dirname "$0")/env.sh"
ROOT="$(cd "$INFRA_DIR/.." && pwd)"
set -a; [ -f "$ROOT/.env" ] && source "$ROOT/.env" || source "$ROOT/.env.example"; set +a
DAVID_REGION="${DAVID_REGION:-europe-west4}"
SERVICE="${APP}"
SA="${APP}-page"
SA_EMAIL="${SA}@${PROJECT_ID}.iam.gserviceaccount.com"

say "Service account ${SA_EMAIL}"
exists gcloud iam service-accounts describe "$SA_EMAIL" \
  || gcloud iam service-accounts create "$SA" --display-name="Genlingo comparison page"
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:${SA_EMAIL}" \
  --role=roles/aiplatform.user --condition=None --quiet >/dev/null

DAVID_URL="$(gcloud run services describe "${APP}-david" --region "$DAVID_REGION" --format='value(status.url)')"
: "${DAVID_URL:?deploy David first: infra/04-david.sh}"
say "The page may call David (${DAVID_URL})"
gcloud run services add-iam-policy-binding "${APP}-david" --region "$DAVID_REGION" \
  --member="serviceAccount:${SA_EMAIL}" --role=roles/run.invoker --quiet >/dev/null

IMAGE="${AR}/${SERVICE}:$(date +%Y%m%d-%H%M%S)"
[ -f "$ROOT/data/.cache/term_embeddings.json" ] || { echo "data/.cache/term_embeddings.json is missing: run make data-pull" >&2; exit 1; }
say "Building ${IMAGE}"
gcloud builds submit "$ROOT" --config "$INFRA_DIR/page.cloudbuild.yaml" --region "$REGION" --quiet \
  --substitutions "_IMAGE=${IMAGE}"

say "Deploying ${SERVICE}"
gcloud run deploy "$SERVICE" --image "$IMAGE" --region "$REGION" --quiet \
  --service-account "$SA_EMAIL" --allow-unauthenticated \
  --min-instances 0 --max-instances 3 --cpu 1 --memory 1Gi --timeout 900 --concurrency 40 \
  --labels "app=${APP}" \
  --set-env-vars "^@^GOOGLE_CLOUD_PROJECT=${PROJECT_ID}@GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION}@GEMINI_MODEL=${GEMINI_MODEL}@GEMINI_THINKING_LEVEL=${GEMINI_THINKING_LEVEL}@GEMINI_PRICE_SCHEDULE=${GEMINI_PRICE_SCHEDULE}@DAVID_MODEL_TAG=${DAVID_MODEL_TAG}@EMBEDDING_MODEL=${EMBEDDING_MODEL}@DAVID_URL=${DAVID_URL}@EVENT_COUNTRY=${EVENT_COUNTRY:-GT}@DAVID_NBEST=${DAVID_NBEST:-1}@DAVID_CPU=${DAVID_CPU:-4}@DAVID_MEMORY_GIB=${DAVID_MEMORY_GIB:-16}@CLOUD_RUN_L4_USD_PER_S=${CLOUD_RUN_L4_USD_PER_S}@CLOUD_RUN_VCPU_USD_PER_S=${CLOUD_RUN_VCPU_USD_PER_S}@CLOUD_RUN_GIB_USD_PER_S=${CLOUD_RUN_GIB_USD_PER_S}@LIMIT_TRANSLATE_PER_MIN=${LIMIT_TRANSLATE_PER_MIN:-60}@LIMIT_WAKE_PER_MIN=${LIMIT_WAKE_PER_MIN:-12}@LIMIT_GEMINI_PER_DAY=${LIMIT_GEMINI_PER_DAY:-1500}@LIMIT_WAKES_PER_DAY=${LIMIT_WAKES_PER_DAY:-24}"
gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)'
