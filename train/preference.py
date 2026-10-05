"""Preference stage after SFT (ORPO), in the same job: teach David which outputs are right, not only
what one reference looks like.

For each preference prompt (data/train/pref.jsonl, built by scripts/build_pref_set.py) the SFT model
samples N candidates. A term-bank score ranks them:

    score = 2 · (expected target terms present) − 2 · (source slang left + other countries' slang)
            + similarity to the reference (0–1, tie-breaker)

chosen = the best sample; rejected = the row's fixed reject when it has one (an archived synthetic target
that used a wrong-meaning counterpart), else the worst sample. Pairs where chosen doesn't beat rejected
are dropped. Then ORPO (odds-ratio preference optimization, TRL) continues training the same LoRA
adapter. Everything is regex + difflib: no model judges the samples.
"""

from __future__ import annotations

import difflib
import json
import re
import time
import unicodedata
from pathlib import Path


def normalize(text: str) -> str:
    """Same as genlingo_duel.terms.normalize: the patterns in pref.jsonl match normalized text."""
    text = text.lower().replace("ñ", "\u0001")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).replace("\u0001", "ñ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-zñ0-9 ]+", " ", text)).strip()


def log(msg: str) -> None:
    print(f"[preference {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def load_rows(path: Path) -> list[dict]:
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    for r in rows:
        r["_must"] = [re.compile(p, re.I) for p in r.get("must", [])]
        r["_must_not"] = [re.compile(p, re.I) for p in r.get("must_not", [])]
    return rows


def score(text: str, row: dict) -> float:
    if not text.strip():
        return -10.0
    norm = normalize(text)
    good = sum(1 for p in row["_must"] if p.search(norm))
    bad = sum(1 for p in row["_must_not"] if p.search(norm))
    sim = difflib.SequenceMatcher(None, text.lower(), row["reference"].lower()).ratio()
    return 2 * good - 2 * bad + sim


def sample(model, tokenizer, rows: list[dict], n: int, batch_prompts: int, max_new_tokens: int, temperature: float) -> None:
    """Fill row["samples"] with n sampled answers per prompt (left-padded batches)."""
    import torch

    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model.eval()
    for i in range(0, len(rows), batch_prompts):
        chunk = rows[i : i + batch_prompts]
        prompts = [tokenizer.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=True) for r in chunk]
        enc = tokenizer(prompts, return_tensors="pt", padding=True, add_special_tokens=False).to(model.device)
        with torch.no_grad():
            # use_cache: training turned the KV cache off for gradient checkpointing; sampling needs it back.
            out = model.generate(**enc, do_sample=True, temperature=temperature, top_p=0.95, max_new_tokens=max_new_tokens,
                                 num_return_sequences=n, pad_token_id=tokenizer.pad_token_id, use_cache=True)
        texts = tokenizer.batch_decode(out[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
        for j, r in enumerate(chunk):
            r["samples"] = [t.strip().split("\n")[0].strip() for t in texts[j * n : (j + 1) * n]]
        if i % (batch_prompts * 10) == 0:
            log(f"sampled {i + len(chunk)}/{len(rows)} prompts")


def build_pairs(rows: list[dict]) -> tuple[list[dict], dict]:
    pairs, stats = [], {"prompts": len(rows), "fixed_rejects": 0, "dropped_no_margin": 0, "chosen_hits": 0}
    for r in rows:
        ranked = sorted(r.get("samples", []), key=lambda t: score(t, r), reverse=True)
        if not ranked:
            continue
        chosen = ranked[0]
        rejected = r.get("rejected") or ranked[-1]
        if score(chosen, r) <= score(rejected, r) or chosen == rejected:
            stats["dropped_no_margin"] += 1
            continue
        stats["fixed_rejects"] += bool(r.get("rejected"))
        stats["chosen_hits"] += all(p.search(normalize(chosen)) for p in r["_must"]) if r["_must"] else 0
        pairs.append({"prompt": r["messages"], "chosen": [{"role": "assistant", "content": chosen}],
                      "rejected": [{"role": "assistant", "content": rejected}]})
    stats["pairs"] = len(pairs)
    return pairs, stats


def orpo(model, tokenizer, pairs: list[dict], out_dir: Path, *, lr: float, beta: float, epochs: float,
         batch_size: int, grad_accum: int, max_length: int, seed: int, max_steps: int = -1) -> dict:
    from datasets import Dataset
    from trl.experimental.orpo import ORPOConfig, ORPOTrainer

    tokenizer.padding_side = "right"
    model.train()
    cfg = ORPOConfig(
        output_dir=str(out_dir), beta=beta, learning_rate=lr, num_train_epochs=epochs, max_steps=max_steps,
        per_device_train_batch_size=batch_size, gradient_accumulation_steps=grad_accum, max_length=max_length,
        lr_scheduler_type="cosine", warmup_steps=0.1, bf16=True, gradient_checkpointing=True, logging_steps=5,
        save_strategy="no", report_to="none", seed=seed, remove_unused_columns=False,
    )
    trainer = ORPOTrainer(model=model, args=cfg, train_dataset=Dataset.from_list(pairs), processing_class=tokenizer)
    t0 = time.time()
    result = trainer.train()
    losses = [h["loss"] for h in trainer.state.log_history if "loss" in h]
    return {"orpo_s": round(time.time() - t0, 1), "orpo_steps": trainer.state.global_step,
            "orpo_loss_first": losses[0] if losses else None, "orpo_loss_last": losses[-1] if losses else None,
            "orpo_loss_mean": result.training_loss}
