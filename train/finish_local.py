"""Finish a cloud fine-tune on this Mac: adapter (from the bucket) -> merge -> GGUF -> models bucket.

    make train-finish TAG=genlingo-2026-10-e4b

Why: the Cloud Run L4 job has 32 GiB of memory and its local disk lives in that memory. Gemma 4
E4B trains fine there (the LoRA adapter is saved to the Cloud Storage volume), but merging a 16 GB
checkpoint and converting it to GGUF doesn't fit. The laptop has 64 GB: the GPU-hungry part runs in
the cloud, the RAM-hungry part here, with the same functions as train_lora.py. The output is the
same (Modelfile + Q4_K_M GGUF + metrics in gs://<MODELS_BUCKET>/<tag>/), so `make pull-model`
doesn't care where the merge happened; the run file records it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import train_lora  # noqa: E402


def main() -> None:
    tag = sys.argv[1]
    app = os.environ.get("APP") or tag.split("-")[0]
    run_path = HERE / "runs" / f"{tag}.json"
    run = json.loads(run_path.read_text()) if run_path.exists() else {}
    base_model = run.get("base_model") or os.environ["GEMMA_BASE_MODEL"]
    weights_uri = run.get("weights_uri") or os.environ["GEMMA_WEIGHTS_URI"]
    staging = os.environ["STAGING_BUCKET"].rstrip("/")
    models = os.environ["MODELS_BUCKET"].rstrip("/")
    work = HERE.parent / "models" / ".work" / tag
    out = HERE.parent / "models" / tag
    work.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    metrics: dict = {"tag": tag, "base_model": base_model, "where_merged": "laptop"}

    if not os.environ.get("HF_TOKEN"):
        token = train_lora.hf_token_from_secret_manager(os.environ.get("GOOGLE_CLOUD_PROJECT"))
        if token:
            os.environ["HF_TOKEN"] = token

    t0 = time.time()
    adapter = train_lora.fetch(f"{staging}/{app}/runs/{tag}/adapter", work / "adapter")
    base_dir = train_lora.base_weights(base_model, weights_uri, work / "base")
    metrics["download_s"] = round(time.time() - t0, 1)

    t0 = time.time()
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM

    model = AutoModelForCausalLM.from_pretrained(base_dir, dtype=torch.bfloat16, low_cpu_mem_usage=True)
    merged = PeftModel.from_pretrained(model, adapter).merge_and_unload()
    merged_dir = work / "merged"
    merged.save_pretrained(merged_dir, safe_serialization=True)
    for f in base_dir.iterdir():  # tokenizer, chat template, processor config (same rule as train_lora)
        if f.is_file() and not f.name.endswith(train_lora.WEIGHT_SUFFIXES) and f.name not in {"config.json", "model.safetensors.index.json"}:
            shutil.copy2(f, merged_dir / f.name)
    del model, merged
    metrics["merge_s"] = round(time.time() - t0, 1)

    llama_cpp = Path(subprocess.run(["bash", str(HERE / "setup_llama_cpp.sh")], check=True,
                                    capture_output=True, text=True).stdout.strip().splitlines()[-1])
    os.environ["PATH"] = f"{llama_cpp / 'bin'}:{os.environ['PATH']}"  # prebuilt llama-quantize
    metrics.update(train_lora.to_gguf(merged_dir, out, tag, llama_cpp, "Q4_K_M", drop_merged=True, outtype="f16"))
    (out / f"{tag}-f16.gguf").unlink(missing_ok=True)  # the laptop only needs the quantized model
    train_lora.write_modelfile(out, metrics["gguf_quant"], os.environ["OLLAMA_RENDERER"], 0.2)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    train_lora.publish(out, f"{models}/{tag}")
    if run:  # the run file keeps the cloud cost and adds where/how long the merge took
        run["finish"] = metrics
        run_path.write_text(json.dumps(run, indent=2) + "\n")
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()
