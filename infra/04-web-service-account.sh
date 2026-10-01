#!/usr/bin/env bash
# Service account for the audience web app on Cloud Run: read/write only the `genlingo`
# Firestore database (IAM condition), nothing else in the project.
source "$(dirname "$0")/env.sh"
SA="${APP}-web"
SA_EMAIL="${SA}@${PROJECT_ID}.iam.gserviceaccount.com"
DATABASE="${FIRESTORE_DATABASE:-genlingo}"

say "Service account ${SA_EMAIL}"
exists gcloud iam service-accounts describe "$SA_EMAIL" \
  || gcloud iam service-accounts create "$SA" --display-name="Genlingo audience web app"

say "Firestore access limited to database ${DATABASE}"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" --role=roles/datastore.user \
  --condition="expression=resource.name==\"projects/${PROJECT_ID}/databases/${DATABASE}\",title=${APP}-db-only" \
  --quiet >/dev/null
echo "$SA_EMAIL"
