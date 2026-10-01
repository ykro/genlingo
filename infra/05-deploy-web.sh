#!/usr/bin/env bash
# Deploy the audience app (web/) to Cloud Run. min-instances=1: the QR code is scanned by a
# whole room at once, and a cold start would greet them with a spinner.
#   EVENT_ID=gdg-guate-2027-03 EVENT_COUNTRY=GT ADMIN_EMAILS=you@example.com infra/05-deploy-web.sh
source "$(dirname "$0")/env.sh"
WEB_DIR="$(cd "$INFRA_DIR/../web" && pwd)"
SERVICE="${APP}"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
URL="https://${SERVICE}-${PROJECT_NUMBER}.${REGION}.run.app"   # deterministic Cloud Run URL
: "${FIREBASE_API_KEY:?set FIREBASE_API_KEY (public web config, see web/.env.example)}"
: "${FIREBASE_APP_ID:?set FIREBASE_APP_ID}"

deploy_run "$SERVICE" "$WEB_DIR" \
  --service-account "${APP}-web@${PROJECT_ID}.iam.gserviceaccount.com" \
  --allow-unauthenticated \
  --min-instances 1 --max-instances 10 \
  --cpu 1 --memory 512Mi --concurrency 200 \
  --set-env-vars "^@^GOOGLE_CLOUD_PROJECT=${PROJECT_ID}@FIRESTORE_DATABASE=${FIRESTORE_DATABASE:-genlingo}@EVENT_ID=${EVENT_ID:-ensayo}@EVENT_COUNTRY=${EVENT_COUNTRY:-LATAM}@FIREBASE_API_KEY=${FIREBASE_API_KEY}@FIREBASE_AUTH_DOMAIN=${PROJECT_ID}.firebaseapp.com@FIREBASE_APP_ID=${FIREBASE_APP_ID}@AUDIENCE_URL=${URL}@ADMIN_EMAILS=${ADMIN_EMAILS:-}@APP_CHECK_ENFORCE=${APP_CHECK_ENFORCE:-0}"
echo "$URL"
