#!/usr/bin/env bash
# Proves App Check enforcement on Firestore: an anonymous user WITHOUT an App Check token is
# refused (403), the same user WITH one (from the debug token) can read.
#   APPCHECK_DEBUG_TOKEN=... e2e/appcheck-firestore.sh
set -euo pipefail
: "${APPCHECK_DEBUG_TOKEN:?set APPCHECK_DEBUG_TOKEN}"
KEY=REDACTED_FIREBASE_API_KEY
ID=$(curl -s -X POST "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=$KEY" -H 'Content-Type: application/json' -d '{"returnSecureToken":true}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["idToken"])')
curl -s -o /dev/null -w "without App Check token: %{http_code}\n" -H "Authorization: Bearer $ID" "https://firestore.googleapis.com/v1/projects/ai-experiments-487722/databases/genlingo/documents/rounds?pageSize=1"
AC=$(curl -s -X POST "https://firebaseappcheck.googleapis.com/v1/projects/611681112050/apps/1:611681112050:web:b5049aba7a269dfff6e56b:exchangeDebugToken?key=$KEY" -H 'Content-Type: application/json' -d "{\"debugToken\":\"$APPCHECK_DEBUG_TOKEN\"}" | python3 -c 'import json,sys;print(json.load(sys.stdin)["token"])')
curl -s -o /dev/null -w "with App Check token: %{http_code}\n" -H "Authorization: Bearer $ID" -H "X-Firebase-AppCheck: $AC" "https://firestore.googleapis.com/v1/projects/ai-experiments-487722/databases/genlingo/documents/rounds?pageSize=1"
