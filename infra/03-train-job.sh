#!/usr/bin/env bash
# Training runtime: a Cloud Run Job with one NVIDIA L4 GPU (serverless, billed per second, same
# container image as the rest of the pipeline, nothing to keep running between monthly retrains).
#
# Creates or updates the job `${APP}-train` in ${TRAIN_REGION}. Each run is started by
# `make train` (train/submit_job.py) with `gcloud run jobs execute --args=...`.
#   IMAGE=... infra/03-train-job.sh     (IMAGE defaults to the output of 02-train-image.sh)
source "$(dirname "$0")/env.sh"

JOB="${APP}-train"
SA_EMAIL="${APP}-train@${PROJECT_ID}.iam.gserviceaccount.com"
STAGING_BUCKET="${STAGING_BUCKET:-gs://${PROJECT_ID}-train-eu}"
IMAGE="${IMAGE:-$(bash "$INFRA_DIR/02-train-image.sh")}"

# L4 minimums on Cloud Run: 4 vCPU / 16 GiB. We use 8 / 32 GiB: loading, merging and converting a
# 5B-parameter checkpoint is CPU- and RAM-heavy. Cloud Run's filesystem lives in memory, so the
# bulky files (base weights ~10 GB, merged model, GGUFs) go to a Cloud Storage volume at /mnt/work
# in the same region as the GPU; base weights stay cached there for the next retrain.
say "Cloud Run Job ${JOB} (${TRAIN_REGION}, 1x L4)"
verb=(create)
exists gcloud run jobs describe "$JOB" --region "$TRAIN_REGION" && verb=(update --clear-volumes --clear-volume-mounts)
gcloud run jobs "${verb[@]}" "$JOB" \
  --region "$TRAIN_REGION" \
  --image "$IMAGE" \
  --gpu 1 --gpu-type nvidia-l4 --no-gpu-zonal-redundancy \
  --cpu 8 --memory 32Gi \
  --task-timeout 3h --max-retries 0 --tasks 1 \
  --service-account "$SA_EMAIL" \
  --add-volume "name=work,type=cloud-storage,bucket=${STAGING_BUCKET#gs://}" \
  --add-volume-mount "volume=work,mount-path=/mnt/work" \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},CACHE_DIR=/mnt/work/${APP}/base-cache" \
  --quiet
echo "$JOB"
