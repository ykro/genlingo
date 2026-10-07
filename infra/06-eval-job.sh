#!/usr/bin/env bash
# The eval in the cloud: a Cloud Run GPU job (1x L4, europe-west4) with Ollama inside. It reads every
# published David from the models bucket (mounted read-only), pulls the base models from the Ollama
# library, calls Gemini on Vertex AI, and writes the report to the staging bucket; `make eval` copies
# it back to evals/. Nothing runs on the laptop.
#   infra/06-eval-job.sh [run_eval.py args…]     e.g. --split dev, --limit 50, --models a,b
source "$(dirname "$0")/env.sh"
ROOT="$(cd "$INFRA_DIR/.." && pwd)"
set -a; [ -f "$ROOT/.env" ] && source "$ROOT/.env" || source "$ROOT/.env.example"; set +a
# EVAL_DAVID_TAGS (optional) evaluates other Davids than .env's DAVID_TAGS (e.g. a new round's variants before
# anyone decides to put one on the page; DAVID_MODEL_TAG, the page's David, stays as it is).
DAVID_TAGS="${EVAL_DAVID_TAGS:-$DAVID_TAGS}"
# EVAL_DAVID_MODEL_TAG (optional): the David the reports treat as the page's (role "david"), e.g. a round's
# winner evaluated before the page switches to it.
DAVID_MODEL_TAG="${EVAL_DAVID_MODEL_TAG:-$DAVID_MODEL_TAG}"
JOB="${APP}-eval"
SA="${APP}-eval"
SA_EMAIL="${SA}@${PROJECT_ID}.iam.gserviceaccount.com"
STAGING_BUCKET="${STAGING_BUCKET:-gs://${PROJECT_ID}-train-eu}"
EU_AR="${TRAIN_REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}"
RUN_ID="$(date +%Y%m%d-%H%M%S)"

say "Service account ${SA_EMAIL}"
exists gcloud iam service-accounts describe "$SA_EMAIL" \
  || gcloud iam service-accounts create "$SA" --display-name="Genlingo eval job"
gcloud storage buckets add-iam-policy-binding "$MODELS_BUCKET" --member="serviceAccount:${SA_EMAIL}" \
  --role=roles/storage.objectViewer --quiet >/dev/null
gcloud storage buckets add-iam-policy-binding "$STAGING_BUCKET" --member="serviceAccount:${SA_EMAIL}" \
  --role=roles/storage.objectAdmin --quiet >/dev/null
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:${SA_EMAIL}" \
  --role=roles/aiplatform.user --condition=None --quiet >/dev/null

# data/.private/ (make data-pull) goes into the image too: the eval needs the quoted sentences, and the
# image stays in the project's private Artifact Registry.
[ -d "$ROOT/data/.private" ] || { echo "data/.private is missing: run make data-pull first" >&2; exit 1; }
HASH="$( (cd "$ROOT" && git ls-files -s duel evals data train/runs; git -C "$ROOT" diff HEAD -- duel evals data train/runs
          find data/.private -type f -exec shasum {} + | sort) | shasum -a 256 | cut -c1-12)"
IMAGE="${EU_AR}/${JOB}:${HASH}"
if ! exists gcloud artifacts docker images describe "$IMAGE"; then
  say "Building ${IMAGE}"
  gcloud builds submit "$ROOT" --config "$INFRA_DIR/eval.cloudbuild.yaml" --region "$REGION" --quiet \
    --substitutions "_IMAGE=${IMAGE}" --ignore-file infra/eval.gcloudignore
fi

ENV="^@^GOOGLE_CLOUD_PROJECT=${PROJECT_ID}@GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION}@GEMINI_MODEL=${GEMINI_MODEL}"
ENV+="@GEMINI_THINKING_LEVEL=${GEMINI_THINKING_LEVEL}@GEMINI_PRICE_SCHEDULE=${GEMINI_PRICE_SCHEDULE}"
ENV+="@DAVID_MODEL_TAG=${DAVID_MODEL_TAG}@DAVID_TAGS=${DAVID_TAGS}@BASE_MODEL_TAGS=${BASE_MODEL_TAGS}"
ENV+="@EMBEDDING_MODEL=${EMBEDDING_MODEL}@OLLAMA_URL=http://127.0.0.1:11434@OLLAMA_MODELS=/tmp/ollama"
ENV+="@EVAL_MODELS_DIR=/mnt/models@EVAL_OUT=/mnt/staging/${APP}/evals/${RUN_ID}"
verb=(create)
exists gcloud run jobs describe "$JOB" --region "$TRAIN_REGION" && verb=(update --clear-volumes --clear-volume-mounts)
say "Cloud Run Job ${JOB} (${TRAIN_REGION}, 1x L4)"
gcloud run jobs "${verb[@]}" "$JOB" --region "$TRAIN_REGION" --image "$IMAGE" --service-account "$SA_EMAIL" \
  --gpu 1 --gpu-type nvidia-l4 --no-gpu-zonal-redundancy --cpu 8 --memory 32Gi --task-timeout 1h \
  --max-retries 0 --tasks 1 --quiet \
  --add-volume "name=models,type=cloud-storage,bucket=${MODELS_BUCKET#gs://},readonly=true" \
  --add-volume-mount "volume=models,mount-path=/mnt/models" \
  --add-volume "name=staging,type=cloud-storage,bucket=${STAGING_BUCKET#gs://}" \
  --add-volume-mount "volume=staging,mount-path=/mnt/staging" \
  --set-env-vars "$ENV"

say "Running the eval (${RUN_ID})"
ARGS="$(IFS=@; echo "$*")"   # "@" as gcloud's list delimiter: values like --models a,b keep their commas
gcloud run jobs execute "$JOB" --region "$TRAIN_REGION" --wait ${ARGS:+--args="^@^$ARGS"}

say "Copying the report back to evals/"
OUT="${STAGING_BUCKET}/${APP}/evals/${RUN_ID}"
gcloud storage cp "${OUT}/report*.md" "$ROOT/evals/" 2>/dev/null || true
mkdir -p "$ROOT/evals/results"
gcloud storage cp "${OUT}/results/*.json" "$ROOT/evals/results/" --no-clobber
