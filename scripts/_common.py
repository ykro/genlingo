"""Shared bootstrap for scripts: make the duel package importable and expose repo paths."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
if str(ROOT / "duel") not in sys.path:
    sys.path.insert(0, str(ROOT / "duel"))


def audience_service(project: str, region: str = "us-central1", service: str = "genlingo") -> dict:
    """The audience app on Cloud Run: {"url", "min_instances", "env"} (gcloud, the laptop's credentials).
    Raises RuntimeError with gcloud's message when it can't be read."""
    import json
    import subprocess

    out = subprocess.run(
        ["gcloud", "run", "services", "describe", service, "--region", region, "--project", project, "--format=json"],
        capture_output=True, text=True, timeout=60,
    )
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip().splitlines()[-1][:160] if out.stderr.strip() else "gcloud falló")
    svc = json.loads(out.stdout)
    annotations = svc["spec"]["template"]["metadata"].get("annotations", {})
    env = {e["name"]: e.get("value", "") for e in svc["spec"]["template"]["spec"]["containers"][0].get("env", [])}
    return {"url": svc["status"]["url"], "min_instances": int(annotations.get("autoscaling.knative.dev/minScale", 0)), "env": env}
