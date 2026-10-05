#!/usr/bin/env bash
# Deploy the audience app (web/) to Cloud Run. min-instances=0, so a deploy never leaves it
# billing around the clock; on talk days `make stage-on` keeps one warm instance (the QR code is
# scanned by a whole room at once, and a cold start would greet them with a spinner) and
# `make stage-off` scales it back to zero afterwards.
#   EVENT_ID=gdg-guate-2027-03 EVENT_COUNTRY=GT RECAPTCHA_SITE_KEY=... infra/05-deploy-web.sh
# With RECAPTCHA_SITE_KEY set, the API routes require a valid App Check token (APP_CHECK_ENFORCE=1).
source "$(dirname "$0")/env.sh"
WEB_DIR="$(cd "$INFRA_DIR/../web" && pwd)"
SERVICE="${APP}"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
URL="https://${SERVICE}-${PROJECT_NUMBER}.${REGION}.run.app"   # deterministic Cloud Run URL
# The public Firebase web config lives in web/.env.local (written once by the web setup); read it
# from there when the environment doesn't set it, so a deploy needs no manual exports.
for k in FIREBASE_API_KEY FIREBASE_APP_ID RECAPTCHA_SITE_KEY ADMIN_EMAILS; do
  if [ -z "${!k:-}" ] && [ -f "$WEB_DIR/.env.local" ]; then
    v="$(sed -n "s/^${k}=//p" "$WEB_DIR/.env.local" | tail -1)"
    [ -n "$v" ] && export "$k=$v"
  fi
done
: "${FIREBASE_API_KEY:?set FIREBASE_API_KEY (public web config, see web/.env.example)}"
: "${FIREBASE_APP_ID:?set FIREBASE_APP_ID}"

deploy_run "$SERVICE" "$WEB_DIR" \
  --service-account "${APP}-web@${PROJECT_ID}.iam.gserviceaccount.com" \
  --allow-unauthenticated \
  --min-instances 0 --max-instances 10 \
  --cpu 1 --memory 512Mi --concurrency 200 \
  --set-env-vars "^@^GOOGLE_CLOUD_PROJECT=${PROJECT_ID}@FIRESTORE_DATABASE=${FIRESTORE_DATABASE:-genlingo}@EVENT_ID=${EVENT_ID:-ensayo}@EVENT_COUNTRY=${EVENT_COUNTRY:-GT}@FIREBASE_API_KEY=${FIREBASE_API_KEY}@FIREBASE_AUTH_DOMAIN=${PROJECT_ID}.firebaseapp.com@FIREBASE_APP_ID=${FIREBASE_APP_ID}@AUDIENCE_URL=${URL}@ADMIN_EMAILS=${ADMIN_EMAILS:-}@RECAPTCHA_SITE_KEY=${RECAPTCHA_SITE_KEY:-}@AUTO_APPROVE_PHRASES=${AUTO_APPROVE_PHRASES:-1}@APP_CHECK_ENFORCE=${APP_CHECK_ENFORCE:-$([ -n "${RECAPTCHA_SITE_KEY:-}" ] && echo 1 || echo 0)}"
echo "$URL"
