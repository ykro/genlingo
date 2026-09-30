"""Run the same training on this laptop (Apple Silicon, MPS) and record it like a cloud run.

    make train-local TAG=genlingo-2027-03

Fallback for when the Vertex AI job can't run (e.g. no GPU quota): identical script, identical
outputs (GGUF Q4 + f16, Modelfile, uploaded to the models bucket), so `make pull-model` and the
eval don't care where David was trained. The run file says where and how long it took; the cost
is 0 because the laptop is already paid for, but compare the duration with a cloud L4.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import train_lora  # noqa: E402


def machine() -> str:
    try:
        chip = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
        mem = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout) / 1024**3
        return f"{chip} {mem:.0f} GB (local, MPS)"
    except Exception:
        return f"{platform.machine()} (local)"


def main() -> None:
    tag, data = sys.argv[1], sys.argv[2]
    extra = sys.argv[3:]
    llama = subprocess.run([str(HERE / "setup_llama_cpp.sh")], capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1]
    os.environ["PATH"] = f"{llama}/bin:{os.environ['PATH']}"
    t0 = time.time()
    metrics = train_lora.main([
        "--data", data, "--tag", tag, "--llama-cpp", llama,
        "--work-dir", str(HERE.parent / "models" / ".work" / tag), *extra,
    ])
    duration = time.time() - t0
    run = {
        "tag": tag,
        "app": tag.rsplit("-", 2)[0],  # tags are <app>-YYYY-MM
        "where": "local",
        "machine": machine(),
        "region": "laptop",
        "base_model": metrics["base_model"],
        "data_date": tag[-7:],
        "examples": metrics["examples"],
        "output_uri": f"{os.environ.get('MODELS_BUCKET', '').rstrip('/')}/{tag}/" if os.environ.get("MODELS_BUCKET") else None,
        "hourly_usd": 0.0,
        "state": "JOB_STATE_SUCCEEDED",
        "duration_s": round(duration, 1),
        "estimated_cost_usd": 0.0,
        "metrics": {k: v for k, v in metrics.items() if k != "merged_dir"},
    }
    out = HERE / "runs" / f"{tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(run, indent=2) + "\n")
    print(json.dumps({k: run[k] for k in ("tag", "machine", "duration_s", "examples")}))


if __name__ == "__main__":
    main()
