"""Preference prompts for the ORPO stage of training (data/train/pref.jsonl).

    uv run --project duel python scripts/build_pref_set.py [--n 300] [--rejects 150]

Two kinds of rows, each with the exact prompt David trains on (from data/train/chat.jsonl, or
rendered the same way for the rejects) and term-bank patterns the job uses to rank samples
(train/preference.py):

- training prompts (`--n`, stratified toward GT and papás -> Gen Z): `must` = the target-side terms
  of the reference, `must_not` = source slang that has to go + other countries' slang of the target
  generation. The job samples 8 answers and keeps the best and the worst.
- ready-made rejects (`--rejects`): pairs-v3 pairs whose counterpart link fails the meaning check
  (data/pairs/archive/synthetic_v3.jsonl vs data/counterparts.jsonl). Their v3 target used a term
  with another meaning: it becomes `rejected`, and that wrong term goes into `must_not`.

Only training data is read: never the test or dev sets.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random

from _common import DATA
from duel_core import OllamaClient
from genlingo_duel.dataset import read_jsonl, train_pairs
from genlingo_duel.glossary import Glossary, hashing_embedder, load_counterparts, render
from genlingo_duel.prompts import COUNTRIES, translation_messages
from genlingo_duel.settings import get_settings
from genlingo_duel.terms import TermBank

OUT = DATA / "train" / "pref.jsonl"


def patterns(bank: TermBank, ids) -> list[str]:
    return sorted({p.pattern for t in ids for p in bank._patterns.get(t, [])})


def spec(bank: TermBank, direction: str, country: str, source: str, reference: str) -> tuple[list[str], list[str]]:
    src_gen, tgt_gen = ("genz", "parent") if direction == "genz_to_parent" else ("parent", "genz")
    allowed = [country, "LATAM"]
    must = bank.found_in(reference, bank.ids(tgt_gen, allowed))
    must_not = list(bank.found_in(source, bank.ids(src_gen))) if direction == "genz_to_parent" else []
    foreign = [t for t in bank.ids(tgt_gen) if bank.terms[t]["country"] not in allowed]
    return patterns(bank, must), patterns(bank, must_not + foreign)


def wrong_term(prov: dict, cps: dict) -> str | None:
    """The term in a v3 target that came from an unvalidated (wrong-meaning) link, if any."""
    a, c, kind = prov.get("term_id"), prov.get("counterpart_id"), prov.get("kind")
    if not a or not c or cps.get(a) == c or cps.get(c) == a:
        return None
    return {"p2g_genz": a, "p2g_trap": a, "g2p_parent": a, "p2g_parent": c, "g2p_genz": c}.get(kind)


async def main_async(n: int, n_rejects: int, seed: int) -> None:
    s = get_settings()
    bank = TermBank(read_jsonl(DATA / "terms.jsonl"), ignore_ambiguous=True)
    cps = load_counterparts(DATA / "counterparts.jsonl")
    rng = random.Random(seed)
    pairs = {p.id: p for p in train_pairs(DATA)}
    chat = [r for r in read_jsonl(DATA / "train" / "chat.jsonl") if r["id"] in pairs]
    assert chat and chat[0]["messages"][0]["content"], "build data/train/chat.jsonl first (make train-data)"

    def weight(r):  # stratify toward the niche and the weak direction
        p = pairs[r["id"]]
        return (2.0 if p.country == "GT" else 1.0) * (1.5 if p.direction == "parent_to_genz" else 1.0)

    rows = []
    pool = [r for r in chat if spec(bank, pairs[r["id"]].direction, pairs[r["id"]].country, pairs[r["id"]].source,
                                     r["messages"][-1]["content"])[0]]
    for r in sorted(pool, key=lambda r: -weight(r) * rng.random())[:n]:
        p = pairs[r["id"]]
        must, must_not = spec(bank, p.direction, p.country, p.source, r["messages"][-1]["content"])
        rows.append({"id": r["id"], "messages": r["messages"][:-1], "reference": r["messages"][-1]["content"],
                     "must": must, "must_not": must_not})

    # Ready-made rejects from pairs-v3: same prompt rendering as training and the stage (v2+lex).
    if s.mock_ai or not s.embedding_model:
        glossary = await Glossary(bank, hashing_embedder(), counterparts=cps).load()
    else:
        ollama = OllamaClient(s.ollama_url)
        glossary = await Glossary(bank, lambda t: ollama.embed(t, model=s.embedding_model),
                                  cache=DATA / ".cache" / "term_embeddings.json", model=s.embedding_model, counterparts=cps).load()
    v3 = [p for p in read_jsonl(DATA / "pairs" / "archive" / "synthetic_v3.jsonl")]
    bad = [(p, w) for p in v3 if (w := wrong_term(p["provenance"], cps)) and bank.found(w, p["target"])]
    rng.shuffle(bad)
    for p, w in bad[:n_rejects]:
        entries = await glossary.lex_entries(p["source"], p["direction"], p["country"])
        msgs = translation_messages(p["source"], p["direction"], p["country"], "v2+lex", render(entries, COUNTRIES[p["country"]]))
        must, must_not = spec(bank, p["direction"], p["country"], p["source"], "")
        # Reference for the similarity tie-break: the source (a correct answer keeps most of its words), never the reject.
        rows.append({"id": p["id"], "messages": msgs, "reference": p["source"], "rejected": p["target"],
                     "must": [], "must_not": sorted(set(must_not) | set(patterns(bank, [w])))})
    n_out = 0
    with OUT.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            n_out += 1
    print(json.dumps({"rows": n_out, "train_prompts": min(n, len(pool)), "v3_bad_link_rejects": min(n_rejects, len(bad)),
                      "v3_bad_link_available": len(bad)}))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--rejects", type=int, default=150)
    ap.add_argument("--seed", type=int, default=2027)
    a = ap.parse_args()
    asyncio.run(main_async(a.n, a.rejects, a.seed))


if __name__ == "__main__":
    main()
