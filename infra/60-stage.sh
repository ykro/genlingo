#!/usr/bin/env bash
# Talk days: keep one warm instance of the audience app (no cold start when the whole room
# scans the QR at once). Other days: scale to zero so nothing bills around the clock.
#   ./infra/60-stage.sh on | off
source "$(dirname "$0")/env.sh"
mode="${1:?usage: 60-stage.sh on|off}"
case "$mode" in
  on) min=1 ;;
  off) min=0 ;;
  *) echo "usage: 60-stage.sh on|off" >&2; exit 2 ;;
esac
say "${APP}: min-instances=${min}"
gcloud run services update "$APP" --region "$REGION" --min-instances "$min" --quiet >/dev/null
# Read it back (no annotation means 0) and fail loudly if Cloud Run doesn't show what was asked.
now="$(gcloud run services describe "$APP" --region "$REGION" \
  --format='value(spec.template.metadata.annotations."autoscaling.knative.dev/minScale")')"
echo "${APP}: min-instances=${now:-0} en Cloud Run"
[ "${now:-0}" = "$min" ] || { echo "!! se pidió min-instances=${min} y Cloud Run muestra ${now:-0}" >&2; exit 1; }
