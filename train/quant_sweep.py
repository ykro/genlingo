"""Quantization sweep: how small can David get before he forgets the slang?

    make quant-sweep TAG=genlingo-2026-10-e2b

From the f16 GGUF of a trained David, builds Q5_K_M, Q6_K and Q8_0, plus Q4_K_M and Q5_K_M
calibrated with an **importance matrix** (imatrix): llama.cpp runs the f16 model over sample text,
measures which weights matter most, and spends the bits there. The calibration text is our
**training** pairs rendered with David's prompt, never the test set (that would leak the eval).

Each file is registered in Ollama as <tag>-<quant> (e.g. genlingo-2026-10-e2b-iq-q4_k_m) with the
same Modelfile settings, so `make eval` can compare them with the same glossary prompt.
"""

from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

PLAIN = ["Q5_K_M", "Q6_K", "Q8_0"]
CALIBRATED = ["Q4_K_M", "Q5_K_M"]
CALIBRATION_EXAMPLES = 600  # ~150k tokens of David-style prompts and answers


def gemma_chat_text(messages: list[dict]) -> str:
    """Render a chat the way the model sees it, so the imatrix reflects real activations."""
    role = {"system": "system", "user": "user", "assistant": "model"}
    return "".join(f"<|turn>{role[m['role']]}\n{m['content']}<turn|>\n" for m in messages)


def calibration_file(out: Path, seed: int = 2027) -> Path:
    rows = [json.loads(line) for line in (ROOT / "data" / "train" / "chat.jsonl").read_text().splitlines() if line.strip()]
    assert all(r["id"].startswith(("syn-", "hum-")) for r in rows), "calibration must come from training pairs only"
    random.Random(seed).shuffle(rows)
    out.write_text("\n".join(gemma_chat_text(r["messages"]) for r in rows[:CALIBRATION_EXAMPLES]), encoding="utf-8")
    return out


def sh(*cmd: str) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def publish(tag: str, suffix: str) -> None:
    """Upload one variant as its own model folder (gs://<MODELS_BUCKET>/<tag>-<suffix>/) for `make pull-model`."""
    folder = ROOT / "models" / tag
    variant = f"{tag}-{suffix}"
    dest = f"{os.environ['MODELS_BUCKET'].rstrip('/')}/{variant}/"
    staging = folder / variant
    staging.mkdir(exist_ok=True)
    (staging / "Modelfile").write_text((folder / f"Modelfile.{suffix}").read_text())
    subprocess.run(["gcloud", "storage", "cp", str(staging / "Modelfile"), str(folder / f"{variant}.gguf"), dest], check=True)


def main() -> None:
    tag = sys.argv[1]
    if len(sys.argv) > 3 and sys.argv[2] == "--publish":
        return publish(tag, sys.argv[3])
    renderer = os.environ["OLLAMA_RENDERER"]
    folder = ROOT / "models" / tag
    f16 = folder / f"{tag}-f16.gguf"
    if not f16.exists():
        sys.exit(f"missing {f16}: make pull-model TAG={tag} FP16=1")
    llama = Path(subprocess.run(["bash", str(HERE / "setup_llama_cpp.sh")], check=True, capture_output=True, text=True).stdout.strip().splitlines()[-1])
    quantize, imatrix_bin = llama / "bin" / "llama-quantize", llama / "bin" / "llama-imatrix"
    report: dict = {"tag": tag, "variants": {}}

    imatrix = folder / f"{tag}.imatrix.gguf"
    if not imatrix.exists():
        t0 = time.time()
        calib = calibration_file(folder / "calibration.txt")
        sh(str(imatrix_bin), "-m", str(f16), "-f", str(calib), "-o", str(imatrix), "-c", "512", "--chunks", "300", "-ngl", "99")
        report["imatrix_s"] = round(time.time() - t0, 1)

    builds = [(q, False) for q in PLAIN] + [(q, True) for q in CALIBRATED]
    for quant, calibrated in builds:
        suffix = ("iq-" if calibrated else "") + quant.lower()
        gguf = folder / f"{tag}-{suffix}.gguf"
        if not gguf.exists():
            extra = ["--imatrix", str(imatrix)] if calibrated else []
            sh(str(quantize), *extra, str(f16), str(gguf), quant)
        named = folder / f"Modelfile.{suffix}"  # same settings as train_lora.write_modelfile
        named.write_text(f"FROM ./{gguf.name}\nRENDERER {renderer}\nPARSER {renderer}\n"
                         "PARAMETER temperature 0.2\nPARAMETER top_p 0.95\nPARAMETER num_ctx 2048\n")
        ollama_tag = f"{tag}-{suffix}"
        subprocess.run(["ollama", "create", ollama_tag, "-f", str(named)], check=True, cwd=folder,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        report["variants"][ollama_tag] = {"quant": quant, "imatrix": calibrated, "bytes": gguf.stat().st_size}
        print(f"{ollama_tag}: {gguf.stat().st_size / 1e9:.2f} GB", flush=True)
    (ROOT / "evals" / "quant_sweep.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
