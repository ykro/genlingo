"""Fallback: finish a cloud fine-tune on this Mac (adapter from the bucket -> merge -> GGUF -> models bucket).

    QUANT=Q5_K_M KEEP_F16=1 make train-finish TAG=genlingo-2026-10b-e2b

`make train` already does this in the cloud (the `${APP}-finish` Cloud Run Job, finish.py). Use this
only when that job can't run, or to re-quantize an existing adapter without paying for a job. Same
code as the cloud job, so the output is the same (Modelfile + GGUFs + metrics in gs://<MODELS_BUCKET>/<tag>/)
and `make pull-model` doesn't care where the merge happened; the run file records it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import finish  # noqa: E402


def main() -> None:
    tag = sys.argv[1]
    app = os.environ.get("APP") or tag.split("-")[0]
    run_path = HERE / "runs" / f"{tag}.json"
    run = json.loads(run_path.read_text()) if run_path.exists() else {}
    llama_cpp = Path(subprocess.run(["bash", str(HERE / "setup_llama_cpp.sh")], check=True,
                                    capture_output=True, text=True).stdout.strip().splitlines()[-1])
    os.environ["PATH"] = f"{llama_cpp / 'bin'}:{os.environ['PATH']}"  # prebuilt llama-quantize
    metrics = finish.finish(
        tag=tag,
        adapter_uri=f"{os.environ['STAGING_BUCKET'].rstrip('/')}/{app}/runs/{tag}/adapter",
        base_model=run.get("base_model") or os.environ["GEMMA_BASE_MODEL"],
        weights_uri=run.get("weights_uri") or os.environ["GEMMA_WEIGHTS_URI"],
        renderer=os.environ["OLLAMA_RENDERER"],
        work=HERE.parent / "models" / ".work" / tag,
        out=HERE.parent / "models" / tag,
        quant=os.environ["QUANT"],  # .env: Q5_K_M, the quant sweep's pick (smallest within 2 points of f16)
        keep_f16=os.environ.get("KEEP_F16") == "1",
        llama_cpp=llama_cpp,
        output_uri=os.environ["MODELS_BUCKET"],
        where="laptop",
    )
    if run:  # the run file keeps the cloud cost and adds where/how long the merge took
        run["finish"] = {k: v for k, v in metrics.items() if k in finish.FINISH_KEYS}
        run_path.write_text(json.dumps(run, indent=2) + "\n")
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()
