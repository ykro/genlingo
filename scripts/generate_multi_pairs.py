"""Generate multi-term synthetic TRAINING pairs with Gemini, built from the term bank.

    uv run --project duel python scripts/generate_multi_pairs.py [--target 800] [--seed 2028]

Why: on the test set David changes fewer of the words the reference changes than Goliath does
(reference-change recall 22 % vs 30 %). One substitution per sentence teaches David
to swap one term and leave the rest. Here every pair has 2–3 slang terms that change at
once, and every expected counterpart must be present in the target:

- p2g_multi    papás -> Gen Z: 2–3 parents' expressions in the source, their Gen Z counterparts of the
               same country in the target, plus a hard negative (a foreign term it must not use);
- p2g_plain    papás -> Gen Z: the MEANINGS of 2–3 Gen Z terms in plain parents' speech in the source,
               those Gen Z terms in the target, plus a hard negative;
- g2p_multi    Gen Z -> papás: 2–3 Gen Z terms in the source; in the target, each one's parents'
               counterpart when the table has one, else its meaning in plain words.

70 % papás -> Gen Z, the direction David is weaker at. Counterparts come only from the
meaning-validated table (data/counterparts.jsonl): p2g_multi uses only parents' terms that have
one. Traps are the foreign term nearest by embedding (cached vectors, no model call). Every pair is
validated against the term bank (validate_multi) and never overlaps a test sentence, not even as a
substring. Training only: synthetic pairs never go to the test, dev or niche sets.
Writes data/pairs/synthetic_multi.jsonl (+ .meta.json); the single-term pairs stay in synthetic.jsonl.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
import time
from pathlib import Path

from _common import ROOT  # noqa: F401  (puts duel/ on sys.path)
from duel_core import cost_usd  # noqa: E402
from generate_pairs import MAX_WORDS, SYSTEM, gemini_generate, load_counterparts, nearest, test_sentences, to_pairs  # noqa: E402
from genlingo_duel.dataset import Pair, read_jsonl, write_jsonl  # noqa: E402
from genlingo_duel.prompts import COUNTRIES  # noqa: E402
from genlingo_duel.settings import get_settings, goliath_prices  # noqa: E402
from genlingo_duel.terms import TermBank, normalize  # noqa: E402

PROMPT_VERSION = "synthetic-multi-2026-10b"
PAIRS_PER_CALL = 4
MIX = {"p2g_multi": 0.45, "p2g_plain": 0.25, "g2p_multi": 0.30}
COUNTRY_WEIGHTS = {"GT": 0.4, "CO": 0.25, "MX": 0.25, "LATAM": 0.10}  # the talk is in Guatemala

USER = """Dirección: {direction_label}.
En "source" usa, todos en la misma frase: {source_rule}
En "target" usa, todos en la misma frase: {target_rule}
{trap_rule}
Escribe {n} pares distintos con situaciones distintas. Todos los términos indicados aparecen en cada frase
(puedes conjugarlos o cambiarles género y número); el resto de la frase cambia lo mínimo.
Devuelve solo JSON: una lista de objetos con "source" y "target"."""

DIRECTION_LABEL = {
    "genz_to_parent": "Gen Z → papás (source = habla Gen Z, target = cómo lo diría un papá o una mamá)",
    "parent_to_genz": "papás → Gen Z (source = habla de papás, target = cómo lo diría alguien Gen Z)",
}


def _term(bank: TermBank, tid: str) -> str:
    t = bank.terms[tid]
    return f"«{t['term']}» ({t['meaning']})"


def plan_calls(bank: TermBank, vectors: dict, target: int, seed: int, counterparts: dict) -> list[dict]:
    rng = random.Random(seed)
    n_calls = -(-target // PAIRS_PER_CALL)
    kinds = [k for k, w in MIX.items() for _ in range(round(w * 20))]
    countries = [c for c, w in COUNTRY_WEIGHTS.items() for _ in range(round(w * 20))]
    rng.shuffle(kinds)
    rng.shuffle(countries)
    calls = []
    for i in range(n_calls):
        kind, country = kinds[i % len(kinds)], countries[(i * 7) % len(countries)]
        src_gen = "parent" if kind.startswith("p2g") else "genz"
        tgt_gen = "genz" if src_gen == "parent" else "parent"
        k = rng.choice((2, 2, 3))
        anchors_pool = sorted(t for t in bank.ids(src_gen if kind != "p2g_plain" else tgt_gen, [country]) if t in vectors)
        if kind == "p2g_multi":  # only parents' terms with a meaning-validated Gen Z counterpart
            anchors_pool = [t for t in anchors_pool if counterparts.get(t)]
        if len(anchors_pool) < k:
            k = len(anchors_pool)
        if k < 2:
            continue
        picks = rng.sample(anchors_pool, k)
        if kind == "p2g_plain":
            source_ids, target_ids = [], picks
        elif kind == "p2g_multi":
            source_ids, target_ids = picks, [counterparts[t] for t in picks]
            if len(set(target_ids)) != len(target_ids):
                continue
        else:  # g2p_multi: the counterpart where validated, the meaning otherwise
            source_ids, target_ids = picks, [counterparts[t] for t in picks if counterparts.get(t)]
        trap = None
        if kind.startswith("p2g"):
            foreign = [t for t in bank.ids("genz") if bank.terms[t]["country"] not in (country, "LATAM") and t in vectors]
            trap = nearest(vectors, target_ids[0], foreign) if target_ids else None
        direction = "parent_to_genz" if kind.startswith("p2g") else "genz_to_parent"
        calls.append({"i": i, "kind": kind, "country": country, "direction": direction, "source_ids": source_ids,
                      "target_ids": target_ids, "trap": trap, "seed": seed + i,
                      "links": {t: counterparts.get(t) for t in source_ids},
                      # to_pairs() provenance fields
                      "anchor": (source_ids or target_ids)[0], "counterpart": target_ids[0] if target_ids else None,
                      "trap_id": trap})
    return calls


def render(bank: TermBank, call: dict) -> tuple[str, str]:
    country = call["country"]
    plain_parent = "español coloquial de papás, sin ninguna jerga juvenil"
    meaning = lambda t: f"«{bank.terms[t]['term']}» dicho con palabras normales ({bank.terms[t]['meaning']})"  # noqa: E731
    if call["kind"] == "p2g_plain":
        source_rule = f"{plain_parent}; di las ideas de " + ", ".join(meaning(t) for t in call["target_ids"])
    else:
        gen = "las expresiones de papás" if call["direction"] == "parent_to_genz" else "los términos Gen Z"
        source_rule = f"{gen} " + ", ".join(_term(bank, t) for t in call["source_ids"])
    if call["direction"] == "parent_to_genz":
        target_rule = "los términos Gen Z " + ", ".join(_term(bank, t) for t in call["target_ids"])
    else:
        cps = {s: c for s, c in call.get("links", {}).items()}
        parts = [f"la expresión de papás {_term(bank, cps[t])}" if cps.get(t) else meaning(t) for t in call["source_ids"]]
        target_rule = f"{plain_parent}; en lugar de cada término Gen Z: " + "; ".join(parts)
    trap_rule = ""
    if call["trap"]:
        tr = bank.terms[call["trap"]]
        trap_rule = (f"Ojo: en {COUNTRIES[country]} NO se dice «{tr['term']}» (eso es de {COUNTRIES[tr['country']]}); "
                     "usa solo los términos indicados.")
    system = SYSTEM.format(country_name=COUNTRIES[country], max_words=MAX_WORDS)
    user = USER.format(direction_label=DIRECTION_LABEL[call["direction"]], source_rule=source_rule,
                       target_rule=target_rule, trap_rule=trap_rule, n=PAIRS_PER_CALL)
    return system, user


def validate_multi(bank: TermBank, call: dict, pair: dict) -> str | None:
    """Reason to reject a multi-term pair, or None. Every expected term on each side must be there."""
    src, tgt, country = pair["source"], pair["target"], pair["country"]
    if any(not bank.found(t, src) for t in call["source_ids"]):
        return "source_missing_term"
    if any(not bank.found(t, tgt) for t in call["target_ids"]):
        return "target_missing_counterpart"
    if bank.foreign_in(tgt, country) or bank.foreign_in(src, country):
        return "foreign_term"
    if call["trap"] and bank.found(call["trap"], tgt):
        return "trap_used"
    if call["direction"] == "genz_to_parent":
        if bank.found_in(tgt, bank.ids("genz")):
            return "slang_left_in_target"
    else:
        if bank.found_in(src, bank.ids("genz")):
            return "genz_slang_in_source"
        if [t for t in bank.found_in(src, bank.ids("parent")) if bank.found(t, tgt)]:
            return "parent_term_left_in_target"
    return None


def filter_multi(bank: TermBank, calls: dict, pairs: list[dict], forbidden) -> tuple[list[dict], dict]:
    kept, seen, dropped = [], set(), {}
    for p in pairs:
        s, t = normalize(p["source"]), normalize(p["target"])
        call = calls[p["provenance"]["seed"]]
        if len(p["source"].split()) > MAX_WORDS or len(p["target"].split()) > MAX_WORDS + 10 or len(s) < 3:
            reason = "length"
        elif s == t:
            reason = "identical"
        elif s in seen:
            reason = "duplicate"
        elif forbidden.overlaps(p["source"]) or forbidden.overlaps(p["target"]):
            reason = "test_leak"
        else:
            reason = validate_multi(bank, call, p)
        if reason is None:
            try:
                Pair.model_validate(p)
            except Exception:
                reason = "schema"
        if reason:
            dropped[reason] = dropped.get(reason, 0) + 1
        else:
            seen.add(s)
            kept.append(p)
    return kept, dropped


def mock_generate(bank: TermBank, call: dict) -> list[dict]:
    w = lambda ids: " y ".join(bank.terms[t]["term"].split("/")[0].strip(" ¡!¿?") for t in ids) or "nada"  # noqa: E731
    return [{"source": f"{w(call['source_ids'])} en la casa {k} {call['i']}", "target": f"{w(call['target_ids'])} en la casa {k} {call['i']}"}
            for k in range(PAIRS_PER_CALL)]


async def main_async(args) -> None:
    s = get_settings()
    data = s.data_dir
    bank = TermBank(read_jsonl(data / "terms.jsonl"), ignore_ambiguous=True)
    vectors = json.loads((data / ".cache" / "term_embeddings.json").read_text())["vectors"]
    calls = plan_calls(bank, vectors, int(args.target * 2.2), args.seed, load_counterparts(data))  # strict validation: over-generate
    model = "mock" if s.mock_ai else s.gemini_model
    usage, t0 = {"input": 0, "output": 0}, time.time()
    if s.mock_ai:
        raws = [mock_generate(bank, c) for c in calls]
    else:
        from google import genai

        client = genai.Client(vertexai=True, project=s.project, location=s.location)
        sem = asyncio.Semaphore(args.concurrency)

        async def one(c):
            async with sem:
                system, user = render(bank, c)
                return await gemini_generate(client, model, system, user, c["seed"], usage)

        raws = await asyncio.gather(*(one(c) for c in calls))
    pairs = []
    for c, raw in zip(calls, raws):
        for p in to_pairs(c, raw, model):
            p["provenance"].update(prompt_version=PROMPT_VERSION, source_term_ids=c["source_ids"], target_term_ids=c["target_ids"])
            pairs.append(p)
    kept, dropped = filter_multi(bank, {c["seed"]: c for c in calls}, pairs, test_sentences(data))
    p2g = [p for p in kept if p["direction"] == "parent_to_genz"][: round(args.target * 0.7)]
    g2p = [p for p in kept if p["direction"] == "genz_to_parent"][: args.target - len(p2g)]
    final = p2g + g2p
    out = data / "pairs" / "synthetic_multi.jsonl"
    write_jsonl(out, final)
    kinds, countries = {}, {}
    for p in final:
        kinds[p["provenance"]["kind"]] = kinds.get(p["provenance"]["kind"], 0) + 1
        countries[p["country"]] = countries.get(p["country"], 0) + 1
    meta = {"model": model, "prompt_version": PROMPT_VERSION, "base_seed": args.seed, "calls": len(calls),
            "generated": len(pairs), "valid": len(kept), "kept": len(final), "dropped": dropped, "kinds": kinds,
            "countries": countries, "tokens": usage,
            "cost_usd": round(cost_usd(goliath_prices(s).at(), usage["input"], usage["output"]), 4),
            "duration_s": round(time.time() - t0, 1), "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(meta, ensure_ascii=False))


def refilter(data: Path) -> None:
    """Re-validate the multi-term pairs against the CURRENT term bank (it grows each research round)."""
    bank = TermBank(read_jsonl(data / "terms.jsonl"), ignore_ambiguous=True)
    path = data / "pairs" / "synthetic_multi.jsonl"
    kept, dropped = [], {}
    for p in read_jsonl(path):
        pr = p["provenance"]
        call = {"source_ids": pr.get("source_term_ids", []), "target_ids": pr.get("target_term_ids", []),
                "trap": pr.get("trap_id"), "direction": p["direction"]}
        reason = validate_multi(bank, call, p)
        if reason:
            dropped[reason] = dropped.get(reason, 0) + 1
        else:
            kept.append(p)
    write_jsonl(path, kept)
    meta_path = path.with_suffix(".meta.json")
    meta = json.loads(meta_path.read_text())
    meta["refiltered"] = {"terms": len(bank.terms), "dropped": dropped, "kept": len(kept), "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(meta["refiltered"], ensure_ascii=False))


def main() -> None:
    if "--refilter" in sys.argv:
        return refilter(get_settings().data_dir)
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--target", type=int, default=800)
    ap.add_argument("--seed", type=int, default=2028)
    ap.add_argument("--concurrency", type=int, default=8)
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()
