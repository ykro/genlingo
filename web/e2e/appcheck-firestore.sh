#!/usr/bin/env bash
# Proves App Check enforcement on Firestore: an anonymous user WITHOUT an App Check token is
# refused (403), the same user WITH one (from the debug token) can read.
#   FIREBASE_API_KEY=... FIREBASE_APP_ID=... APPCHECK_DEBUG_TOKEN=... e2e/appcheck-firestore.sh
# (the first two are the web app's public config, the same values infra/05-deploy-web.sh uses)
set -euo pipefail
: "${APPCHECK_DEBUG_TOKEN:?set APPCHECK_DEBUG_TOKEN}"
: "${FIREBASE_API_KEY:?set FIREBASE_API_KEY}"
: "${FIREBASE_APP_ID:?set FIREBASE_APP_ID (1:<project number>:web:<id>)}"
KEY="$FIREBASE_API_KEY"
PROJECT="${GOOGLE_CLOUD_PROJECT:-ai-experiments-487722}"
PROJECT_NUMBER="$(cut -d: -f2 <<<"$FIREBASE_APP_ID")"
# The browser key only accepts requests from the app's own origins (HTTP-referrer restriction).
REFERER="${APP_URL:-https://genlingo-${PROJECT_NUMBER}.us-central1.run.app}/"
ID=$(curl -s -X POST "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=$KEY" -H "Referer: $REFERER" -H 'Content-Type: application/json' -d '{"returnSecureToken":true}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["idToken"])')
curl -s -o /dev/null -w "without App Check token: %{http_code}\n" -H "Authorization: Bearer $ID" "https://firestore.googleapis.com/v1/projects/$PROJECT/databases/genlingo/documents/rounds?pageSize=1"
AC=$(curl -s -X POST "https://firebaseappcheck.googleapis.com/v1/projects/$PROJECT_NUMBER/apps/$FIREBASE_APP_ID:exchangeDebugToken?key=$KEY" -H "Referer: $REFERER" -H 'Content-Type: application/json' -d "{\"debugToken\":\"$APPCHECK_DEBUG_TOKEN\"}" | python3 -c 'import json,sys;print(json.load(sys.stdin)["token"])')
curl -s -o /dev/null -w "with App Check token: %{http_code}\n" -H "Authorization: Bearer $ID" -H "X-Firebase-AppCheck: $AC" "https://firestore.googleapis.com/v1/projects/$PROJECT/databases/genlingo/documents/rounds?pageSize=1"
