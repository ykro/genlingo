#!/usr/bin/env bash
# App Check for the audience app: only our web app (verified by reCAPTCHA Enterprise) may call
# the API routes and read Firestore from a browser.
#   1. reCAPTCHA Enterprise score key for the Cloud Run domain (+ localhost for rehearsals)
#   2. register it as the App Check provider of the "Genlingo audiencia" web app
#   3. a debug token for automated tests and emulators (they can't pass reCAPTCHA)
#   4. enforce App Check on Cloud Firestore (with ENFORCE_FIRESTORE=1)
# Prints the site key and, the first time, the debug token (keep it out of the repo).
#
# Note: Firestore enforcement is per project (App Check has no per-database policy for
# Firestore): any browser/mobile client of any database in this project must send App Check
# tokens. Server code (Admin SDK, IAM) is not affected.
source "$(dirname "$0")/env.sh"
APP_ID="${FIREBASE_APP_ID:?set FIREBASE_APP_ID (Genlingo web app id)}"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
DOMAINS="${RECAPTCHA_DOMAINS:-${APP}-${PROJECT_NUMBER}.${REGION}.run.app,localhost,127.0.0.1}"
API="https://firebaseappcheck.googleapis.com/v1/projects/${PROJECT_NUMBER}"
auth=(-H "Authorization: Bearer $(gcloud auth print-access-token)" -H "x-goog-user-project: ${PROJECT_ID}" -H "Content-Type: application/json")

say "reCAPTCHA Enterprise key"
KEY="$(gcloud recaptcha keys list --format='value(name.basename(),displayName)' | awk -F'\t' -v n="${APP} web" '$2==n{print $1}')"
if [ -z "$KEY" ]; then
  KEY="$(gcloud recaptcha keys create --display-name="${APP} web" --web --domains="$DOMAINS" \
    --integration-type=score --format='value(name.basename())')"
fi
echo "site key: $KEY"

say "App Check provider (reCAPTCHA Enterprise) for $APP_ID"
curl -sf -X PATCH "${auth[@]}" "${API}/apps/${APP_ID}/recaptchaEnterpriseConfig?updateMask=siteKey,tokenTtl" \
  -d "{\"siteKey\":\"${KEY}\",\"tokenTtl\":\"3600s\"}" >/dev/null

say "Debug token for e2e / emulator"
if curl -sf "${auth[@]}" "${API}/apps/${APP_ID}/debugTokens" | grep -q '"displayName": "e2e"'; then
  echo "debug token 'e2e' already exists (value in your web/.env.local as APPCHECK_DEBUG_TOKEN)"
else
  TOKEN="$(uuidgen | tr 'A-Z' 'a-z')"
  curl -sf -X POST "${auth[@]}" "${API}/apps/${APP_ID}/debugTokens" -d "{\"displayName\":\"e2e\",\"token\":\"${TOKEN}\"}" >/dev/null
  echo "APPCHECK_DEBUG_TOKEN=${TOKEN}"
fi

if [ "${ENFORCE_FIRESTORE:-0}" = 1 ]; then
  say "Enforcing App Check on Cloud Firestore"
  curl -sf -X PATCH "${auth[@]}" "${API}/services/firestore.googleapis.com?updateMask=enforcementMode" \
    -d '{"enforcementMode":"ENFORCED"}'
  echo
fi
