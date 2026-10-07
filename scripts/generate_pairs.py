"""Generate synthetic TRAINING pairs with Gemini, built from the term bank ("pares sintéticos").

    uv run --project duel python scripts/generate_pairs.py [--target 1500] [--seed 2027]

Every pair is a *term substitution* checked against the term bank:
- each call names a slang term and, only when the meaning-validated lexicon has one
  (data/counterparts.jsonl, scripts/build_counterparts.py), its counterpart in the other generation;
  without a counterpart the parents' side says the term's MEANING in plain words, and calls that need
  a parents' term are skipped;
- rebalanced toward papás -> Gen Z (the direction David was worst at);
- hard negatives: "in Mexico it's «feria», not «pisto» (Guatemala)";
- every pair is validated against the term bank; the reasons for rejection are counted.

Dead ends, in one line each (docs/BITACORA.md): free paraphrases taught David to rewrite everything;
minimal edits left the slang alone; counterparts picked by embedding meant something else (those
pairs are archived in data/pairs/archive/ and only used as rejected answers for ORPO).

Traps (hard negatives) are the foreign term nearest by embedding (cached vectors, no model call).
Why synthetic only for training: a test set written by Gemini would reward Gemini (Goliath) for
sounding like itself; the test set comes from real web usage instead (scripts/build_test_set.py).
Every pair records model, prompt version, seed and the term ids it was built from.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import random
import re
import sys
import time
import unicodedata
from pathlib import Path

from _common import ROOT  # noqa: F401  (puts duel/ on sys.path)
from duel_core import cost_usd  # noqa: E402
from genlingo_duel.dataset import Pair, read_jsonl, write_jsonl  # noqa: E402
from genlingo_duel.glossary import Glossary, hashing_embedder  # noqa: E402
from genlingo_duel.overlap import TextIndex  # noqa: E402
from genlingo_duel.prompts import COUNTRIES  # noqa: E402
from genlingo_duel.settings import get_settings, goliath_prices  # noqa: E402
from genlingo_duel.terms import TermBank  # noqa: E402

PROMPT_VERSION = "synthetic-2026-10b"  # data-date name, like the model tags
PAIRS_PER_CALL = 4
MAX_WORDS = 30
# Share of calls per kind (p2g = papás -> Gen Z, g2p = Gen Z -> papás). 60 % p2g.
MIX = {"p2g_genz": 0.30, "p2g_parent": 0.15, "p2g_trap": 0.15, "g2p_genz": 0.25, "g2p_parent": 0.15}

SYSTEM = """Eres lingüista y conoces cómo habla la gente en {country_name}.
Escribes pares de frases para entrenar un traductor generacional del español de {country_name}:
- Habla Gen Z: jóvenes de 16 a 24 años de {country_name}, como escriben en chats y redes.
- Habla de papás: adultos de 45 a 60 años de {country_name}, registro coloquial de su generación, sin jerga juvenil.
Cada par dice lo mismo en las dos formas de hablar. La diferencia entre "source" y "target" es la jerga:
el término indicado se sustituye por su equivalente de la otra generación; el resto de la frase cambia lo mínimo.
Frases cotidianas y variadas (escuela, trabajo, familia, comida, fiestas, dinero, redes, noviazgo), de 4 a
{max_words} palabras, sin groserías fuertes ni contenido sexual, sin nombres de personas reales.
Solo expresiones de {country_name} o del español neutro: nada de jerga de otros países. No agregues vocativos
(mijo, bro, mano, parce) que no estén en la otra frase."""

USER = """Dirección: {direction_label}.
En "source" usa: {source_rule}
En "target" usa: {target_rule}
{trap_rule}
Escribe {n} pares distintos con situaciones distintas. Puedes conjugar el término o cambiarle género y número.
Devuelve solo JSON: una lista de objetos con "source" y "target"."""

DIRECTION_LABEL = {
    "genz_to_parent": "Gen Z → papás (source = habla Gen Z, target = cómo lo diría un papá o una mamá)",
    "parent_to_genz": "papás → Gen Z (source = habla de papás, target = cómo lo diría alguien Gen Z)",
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9ñ ]+", "", re.sub(r"\s+", " ", text)).strip()


def _cos(a: list[float], b: list[float]) -> float:
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0


def nearest(vectors: dict[str, list[float]], tid: str, candidates: list[str]) -> str | None:
    cands = [c for c in candidates if c != tid and c in vectors]
    return max(cands, key=lambda c: _cos(vectors[tid], vectors[c]), default=None) if tid in vectors else None


def load_counterparts(data_dir: Path) -> dict[str, str | None]:
    """term_id -> meaning-validated counterpart id (or None). Missing table = no counterparts at all."""
    return {r["term_id"]: r["counterpart_id"] for r in read_jsonl(data_dir / "counterparts.jsonl")}


def plan_calls(bank: TermBank, vectors: dict[str, list[float]], target: int, seed: int,
               counterparts: dict[str, str | None] | None = None, anchor_prefix: str = "",
               countries: list[str] | None = None, mix: dict[str, float] | None = None) -> list[dict]:
    """Round-robin over countries and terms; each call = one kind, one anchor term, its validated counterpart.
    `countries` / `mix` narrow a top-up round (e.g. the pan-Hispanic Gen Z round: LATAM + MX, Gen Z anchors)."""
    counterparts = counterparts or {}
    rng = random.Random(seed)
    n_calls = -(-target // PAIRS_PER_CALL)
    kinds = [k for k, share in (mix or MIX).items() for _ in range(round(share * 20))]
    rng.shuffle(kinds)  # interleave kinds, so any prefix of the plan keeps the mix
    calls = []
    countries = countries or list(COUNTRIES)
    cursors = {}
    for i in range(n_calls):
        kind = kinds[i % len(kinds)]
        country = countries[i % len(countries)]
        anchor_gen = "parent" if kind.endswith("_parent") else "genz"
        pool = sorted(bank.ids(anchor_gen, [country])) or sorted(bank.ids(anchor_gen, ["LATAM"]))
        if anchor_prefix:  # top-up rounds: only the terms a new research round added
            pool = [t for t in pool if t.startswith(anchor_prefix)]
            if not pool:
                continue
        key = (kind, country)
        cursors[key] = cursors.get(key, rng.randrange(len(pool)))
        anchor = pool[cursors[key] % len(pool)]
        cursors[key] += 1
        counterpart = counterparts.get(anchor)
        if kind in ("p2g_parent", "g2p_parent") and not counterpart:
            continue  # needs a parents' term with the same meaning: no validated link, no call
        trap = None
        if kind == "p2g_trap":
            foreign = [t for t in bank.ids("genz") if bank.terms[t]["country"] not in (country, "LATAM")]
            trap = nearest(vectors, anchor, foreign)
        direction = "parent_to_genz" if kind.startswith("p2g") else "genz_to_parent"
        calls.append({"i": i, "kind": kind, "country": country, "direction": direction, "anchor": anchor,
                      "counterpart": counterpart, "trap": trap, "seed": seed + i})
    return calls


def _term(bank: TermBank, tid: str | None) -> str:
    t = bank.terms[tid]
    return f"«{t['term']}» ({t['meaning']})"


def render(bank: TermBank, call: dict) -> tuple[str, str]:
    country = call["country"]
    a, cp = call["anchor"], call["counterpart"]
    plain_parent = "español coloquial de papás, sin ninguna jerga juvenil"
    meaning = f"la idea de «{bank.terms[a]['term']}» dicha con palabras normales ({bank.terms[a]['meaning']})"
    if call["kind"] in ("p2g_genz", "p2g_trap"):  # parent source (meaning or counterpart) -> genz target with anchor
        source_rule = f"{plain_parent}: {meaning}" + (f"; si encaja, la expresión de papás {_term(bank, cp)}" if cp else "")
        target_rule = f"el término Gen Z {_term(bank, a)}"
    elif call["kind"] == "p2g_parent":  # parent anchor in source -> genz counterpart in target
        source_rule = f"la expresión de papás {_term(bank, a)}"
        target_rule = f"el término Gen Z {_term(bank, cp)}" if cp else "jerga Gen Z de " + COUNTRIES[country]
    elif call["kind"] == "g2p_genz":  # genz anchor in source -> its meaning (or validated counterpart) in target
        source_rule = f"el término Gen Z {_term(bank, a)}"
        target_rule = (f"{plain_parent}: la expresión de papás {_term(bank, cp)}" if cp else f"{plain_parent}: {meaning}")
    else:  # g2p_parent: genz counterpart in source -> parent anchor in target
        source_rule = f"el término Gen Z {_term(bank, cp)}" if cp else "jerga Gen Z de " + COUNTRIES[country]
        target_rule = f"la expresión de papás {_term(bank, a)}"
    trap_rule = ""
    if call["trap"]:
        tr = bank.terms[call["trap"]]
        trap_rule = (f"Ojo: en {COUNTRIES[country]} NO se dice «{tr['term']}» (eso es de {COUNTRIES[tr['country']]}); "
                     f"usa «{bank.terms[a]['term']}».")
    system = SYSTEM.format(country_name=COUNTRIES[country], max_words=MAX_WORDS)
    user = USER.format(direction_label=DIRECTION_LABEL[call["direction"]], source_rule=source_rule,
                       target_rule=target_rule, trap_rule=trap_rule, n=PAIRS_PER_CALL)
    return system, user


def expected_terms(call: dict) -> tuple[str | None, str | None]:
    """(term that must be in source, term that must be in target), when the call fixes them."""
    k, a, cp = call["kind"], call["anchor"], call["counterpart"]
    return {
        "p2g_genz": (None, a),
        "p2g_trap": (None, a),
        "p2g_parent": (a, cp),
        "g2p_genz": (a, None),
        "g2p_parent": (cp, a),
    }[k]


def validate(bank: TermBank, call: dict, pair: dict) -> str | None:
    """Reason to reject a pair, or None. All checks are against the term bank."""
    src, tgt, country = pair["source"], pair["target"], pair["country"]
    must_src, must_tgt = expected_terms(call)
    if must_src and not bank.found(must_src, src):
        return "source_missing_term"
    if must_tgt and not bank.found(must_tgt, tgt):
        return "target_missing_term"
    if bank.foreign_in(tgt, country) or bank.foreign_in(src, country):
        return "foreign_term"
    if call["direction"] == "genz_to_parent":
        if bank.found_in(tgt, bank.ids("genz")):
            return "slang_left_in_target"  # parents' speech must not keep Gen Z slang
    else:
        if not bank.found_in(tgt, bank.ids("genz", [country, "LATAM"])):
            return "target_without_genz_slang"
        if bank.found_in(src, bank.ids("genz")):
            return "genz_slang_in_source"
        if must_src is None and bank.found(call["anchor"], src):
            return "term_not_substituted"
        if [t for t in bank.found_in(src, bank.ids("parent")) if bank.found(t, tgt)]:
            return "parent_term_left_in_target"  # the parents' expression must be replaced too
    return None


def mock_generate(bank: TermBank, call: dict) -> list[dict]:
    must_src, must_tgt = expected_terms(call)
    s = bank.terms[must_src]["term"].split("/")[0].strip(" ¡!¿?") if must_src else "qué cosa"
    t = bank.terms[must_tgt]["term"].split("/")[0].strip(" ¡!¿?") if must_tgt else "qué cosa"
    return [{"source": f"{s} en la escuela {k} {call['i']}", "target": f"{t} en la escuela {k} {call['i']}"} for k in range(PAIRS_PER_CALL)]


async def gemini_generate(client, model: str, system: str, user: str, seed: int, usage: dict) -> list[dict]:
    from google.genai import types

    schema = {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"source": {"type": "STRING"}, "target": {"type": "STRING"}},
                                         "required": ["source", "target"]}}
    cfg = types.GenerateContentConfig(
        system_instruction=system, temperature=1.0, seed=seed, response_mime_type="application/json", response_schema=schema,
        thinking_config=types.ThinkingConfig(thinking_level="low"),
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    for attempt in range(5):
        try:
            res = await asyncio.wait_for(client.aio.models.generate_content(model=model, contents=user, config=cfg), 90)
            u = res.usage_metadata
            usage["input"] += u.prompt_token_count or 0
            usage["output"] += (u.candidates_token_count or 0) + (u.thoughts_token_count or 0)
            return json.loads(res.text)
        except Exception as exc:  # 429s, timeouts, bad JSON: back off and retry
            if attempt == 4:
                print(f"  call failed: {type(exc).__name__}: {str(exc)[:120]}", file=sys.stderr)
                return []
            await asyncio.sleep(2 ** (attempt + 1))
    return []


def to_pairs(call: dict, raw: list[dict], model: str) -> list[dict]:
    out = []
    for k, r in enumerate(raw[:PAIRS_PER_CALL]):
        src, tgt = str(r.get("source", "")).strip(), str(r.get("target", "")).strip()
        out.append({
            "id": "syn-" + hashlib.sha1(f"{call['seed']}|{k}|{src}".encode()).hexdigest()[:10],
            "direction": call["direction"], "source": src, "target": tgt, "country": call["country"],
            "age_range": "16-24", "split": "train",
            "status": "approved",  # auto-approved only after validate() and filter_pairs() pass
            "origin": "synthetic",
            "provenance": {"model": model, "prompt_version": PROMPT_VERSION, "seed": call["seed"], "item": k,
                           "kind": call["kind"], "term_id": call["anchor"], "counterpart_id": call["counterpart"],
                           "trap_id": call["trap"]},
        })
    return out


def filter_pairs(bank: TermBank, calls_by_seed: dict[int, dict], pairs: list[dict], forbidden: TextIndex):
    """Schema, length, duplicates, test leakage, then the term-bank validation."""
    kept, seen, dropped = [], set(), {}
    for p in pairs:
        reason = None
        try:
            Pair.model_validate(p)
        except Exception:
            reason = "schema"
        s, t = normalize(p["source"]), normalize(p["target"])
        if reason is None:
            if len(p["source"].split()) > MAX_WORDS or len(p["target"].split()) > MAX_WORDS + 10 or len(s) < 3:
                reason = "length"
            elif s == t:
                reason = "identical"
            elif s in seen:
                reason = "duplicate"
            elif forbidden.overlaps(p["source"]) or forbidden.overlaps(p["target"]):
                reason = "test_leak"  # also a test sentence quoted inside the pair, or the pair inside one
            else:
                reason = validate(bank, calls_by_seed[p["provenance"]["seed"]], p)
        if reason:
            dropped[reason] = dropped.get(reason, 0) + 1
        else:
            seen.add(s)
            kept.append(p)
    return kept, dropped


def test_sentences(data_dir: Path) -> TextIndex:
    """Sentences reserved for the test set: the generator must never reproduce them, whole or in part."""
    texts: list[str] = []
    for row in read_jsonl(data_dir / "raw" / "web_usage.jsonl"):
        texts += [row["example"], row.get("rewrite", "")]
    for rel in ("pairs/test_web.jsonl", "eval/probe_genz.jsonl", "pairs/dev_real.jsonl"):
        for row in read_jsonl(data_dir / rel):
            texts += [row["source"], row["target"]]
    return TextIndex(texts)


async def main_async(args: argparse.Namespace) -> None:
    s = get_settings()
    data = s.data_dir
    bank = TermBank(read_jsonl(data / "terms.jsonl"))
    if s.mock_ai:
        vectors = (await Glossary(bank, hashing_embedder()).load()).vectors
    else:  # cached EmbeddingGemma vectors, used only to pick traps (no model call)
        vectors = json.loads((data / ".cache" / "term_embeddings.json").read_text())["vectors"]
    # Over-generate: validation against the term bank is strict and rejects a good share.
    countries = [c.strip() for c in args.countries.split(",") if c.strip()] or None
    mix = {k: MIX[k] for k in args.kinds.split(",") if k.strip()} if args.kinds else None
    calls = plan_calls(bank, vectors, int(args.target * 2.2), args.seed, load_counterparts(data), args.anchor_prefix,
                       countries=countries, mix=mix)
    model = "mock" if s.mock_ai else s.gemini_model
    usage = {"input": 0, "output": 0}
    t0 = time.time()
    if s.mock_ai:
        raws = [mock_generate(bank, c) for c in calls]
    else:
        from google import genai

        client = genai.Client(vertexai=True, project=s.project, location=s.location)
        sem = asyncio.Semaphore(args.concurrency)
        done = 0

        async def one(c):
            nonlocal done
            async with sem:
                system, user = render(bank, c)
                out = await gemini_generate(client, model, system, user, c["seed"], usage)
            done += 1
            if done % 50 == 0:
                print(f"  {done}/{len(calls)} calls", flush=True)
            return out

        raws = await asyncio.gather(*(one(c) for c in calls))

    pairs = [p for c, raw in zip(calls, raws) for p in to_pairs(c, raw, model)]
    kept, dropped = filter_pairs(bank, {c["seed"]: c for c in calls}, pairs, test_sentences(data))
    # Rebalance: 60 % papás -> Gen Z, 40 % Gen Z -> papás, up to the target.
    p2g = [p for p in kept if p["direction"] == "parent_to_genz"][: round(args.target * args.p2g_share)]
    g2p = [p for p in kept if p["direction"] == "genz_to_parent"][: args.target - len(p2g)]
    final = p2g + g2p
    out = Path(args.out) if args.out else data / "pairs" / "synthetic.jsonl"
    write_jsonl(out, final)
    kinds = {}
    for p in final:
        kinds[p["provenance"]["kind"]] = kinds.get(p["provenance"]["kind"], 0) + 1
    meta = {
        "model": model, "prompt_version": PROMPT_VERSION, "base_seed": args.seed, "calls": len(calls),
        "generated": len(pairs), "valid": len(kept), "kept": len(final), "dropped": dropped, "kinds": kinds,
        "counterparts": "data/counterparts.jsonl", "tokens": usage,
        "cost_usd": round(cost_usd(goliath_prices(s).at(), usage["input"], usage["output"]), 4),
        "duration_s": round(time.time() - t0, 1), "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(meta, ensure_ascii=False))


def refilter(data: Path) -> None:
    """Re-validate existing synthetic pairs against the CURRENT term bank (it grows each research
    round) and drop those that now break a rule; the meta file records how many and why."""
    bank = TermBank(read_jsonl(data / "terms.jsonl"))
    path = data / "pairs" / "synthetic.jsonl"
    kept, dropped = [], {}
    for p in read_jsonl(path):
        pr = p["provenance"]
        call = {"kind": pr["kind"], "anchor": pr["term_id"], "counterpart": pr.get("counterpart_id"),
                "trap": pr.get("trap_id"), "direction": p["direction"]}
        reason = validate(bank, call, p)
        if reason:
            dropped[reason] = dropped.get(reason, 0) + 1
        else:
            kept.append(p)
    write_jsonl(path, kept)
    meta_path = path.with_suffix(".meta.json")
    meta = json.loads(meta_path.read_text())
    meta["refiltered"] = {"terms": len(bank.terms), "dropped": dropped, "kept": len(kept),
                          "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(meta["refiltered"], ensure_ascii=False))


def main() -> None:
    if "--refilter" in sys.argv:
        return refilter(get_settings().data_dir)
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--target", type=int, default=int(__import__("os").environ.get("SYNTHETIC_PAIRS_TARGET", 1500)))
    ap.add_argument("--seed", type=int, default=2027)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--out", default=None)
    ap.add_argument("--countries", default="", help="comma-separated countries to plan for (default: all)")
    ap.add_argument("--kinds", default="", help="comma-separated MIX kinds to use (default: all, with their shares)")
    ap.add_argument("--p2g-share", type=float, default=0.6, help="share of papás -> Gen Z pairs in the output")
    ap.add_argument("--anchor-prefix", default="", help="only anchor on term ids with this prefix (top-up for a new round)")
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()
