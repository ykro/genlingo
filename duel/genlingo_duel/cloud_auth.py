"""ID tokens for calling David's private Cloud Run service.

On Cloud Run the page's service account mints them from the metadata server; on a developer
machine (evals, data scripts) `gcloud auth print-identity-token` uses the signed-in account,
which needs roles/run.invoker on the David service. Tokens last an hour: cached for 50 minutes.
"""

from __future__ import annotations

import subprocess
import threading
import time

import httpx

TTL_S = 50 * 60


def _fetch(audience: str) -> str:
    try:
        import google.auth.transport.requests
        import google.oauth2.id_token

        return google.oauth2.id_token.fetch_id_token(google.auth.transport.requests.Request(), audience)
    except Exception:
        out = subprocess.run(["gcloud", "auth", "print-identity-token"], capture_output=True, text=True, timeout=30)
        if out.returncode != 0 or not out.stdout.strip():
            raise RuntimeError(f"no ID token for {audience}: {out.stderr.strip()[:200]}")
        return out.stdout.strip()


class IdTokenAuth(httpx.Auth):
    def __init__(self, audience: str):
        self.audience = audience.rstrip("/")
        self._token, self._at = "", 0.0
        self._lock = threading.Lock()

    def token(self) -> str:
        with self._lock:
            if not self._token or time.time() - self._at > TTL_S:
                self._token, self._at = _fetch(self.audience), time.time()
            return self._token

    def auth_flow(self, request: httpx.Request):
        request.headers["Authorization"] = f"Bearer {self.token()}"
        yield request
