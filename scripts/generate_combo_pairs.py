"""Natural multi-term TRAINING pairs with Gemini: 2–3 slang terms of one country in one short sentence.

    uv run --project duel python scripts/generate_combo_pairs.py [--target 500] [--seed 6067]

Why: the hypothesis of round 5 is that a big model knows terms one at a time but a small model trained on a
country's data can win when a sentence packs several of them ("no manches güey, el profe está bien mamón y la
tarea está cañona"). Round 3 tried multi-term pairs (generate_multi_pairs.py) and they were left out: on dev
they cost 1.3 chrF++ points and David's answers got longer (p50 1.99 s). What was wrong there, and what this
script does instead:

- **Forced, unnatural combinations.** Round 3 named 2–3 random terms and made Gemini fit them all in, so it
  wrote sentences no one says ("quedó bien aesthetic, literal como me gustan"). Here Gemini gets a pool of
  POOL terms of the country and writes sentences with the 2–3 of them that a young person would really say
  together; the pool is drawn from terms that co-occur in real web sentences first.
- **Long sentences.** Round 3 allowed up to 30 words (40 in the target). Here the Gen Z side has
  MIN_WORDS–MAX_WORDS words and the other side 0.6–1.6× its length, so David does not learn to lengthen.
- **Meaning not checked per term.** Here every Gen Z term found in the sentence must come out on the parents'
  side as its meaning-validated counterpart (data/counterparts.jsonl) or as a content word of its meaning in
  the bank, the same test as «jerga correcta»; and the parents' side keeps no slang of any generation-Z kind.
- **Too large a share, one direction.** Round 3 was 24 % of training and 70 % papás → Gen Z. Each pair here
  gives both directions, and how much of it goes into training is a variant decided on dev.

Countries lean outside Guatemala (MX, CO, LATAM), where David tied Goliath. Training only: synthetic pairs never
go to the test set, dev, the probe or the combinations niche, and never quote any of their sentences.
Records model, prompt version and seed per pair -> data/pairs/synthetic_combo.jsonl (+ .meta.json).
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import re
import sys
import time
from collections import Counter

from _common import DATA, ROOT
from duel_core import cost_usd
from generate_pairs import gemini_generate, load_counterparts, test_sentences
from genlingo_duel.dataset import Pair, read_jsonl, write_jsonl
from genlingo_duel.prompts import COUNTRIES
from genlingo_duel.settings import get_settings, goliath_prices
from genlingo_duel.terms import STOPWORDS, TermBank, normalize

sys.path.insert(0, str(ROOT / "evals"))
from combos import distinct_terms  # noqa: E402

PROMPT_VERSION = "synthetic-combo-2026-10e"
PAIRS_PER_CALL = 4
POOL = 6
MIN_WORDS, MAX_WORDS = 5, 22
COUNTRY_WEIGHTS = {"MX": 0.32, "CO": 0.26, "LATAM": 0.30, "GT": 0.12}

SYSTEM = """Eres lingüista y conoces cómo habla la gente en {country_name}.
Escribes pares de frases para entrenar un traductor generacional del español de {country_name}:
- "genz": cómo lo escribiría un joven de 16 a 24 años de {country_name} en un chat o en redes.
- "papas": cómo diría LO MISMO un papá o una mamá de 45 a 60 años de {country_name}: español coloquial de su
  generación, SIN ninguna jerga juvenil (ni de los términos de la lista ni otra).
Reglas:
- Cada frase "genz" usa 2 o 3 términos de la lista, los que un joven de verdad usaría juntos en esa situación;
  tiene de {min_words} a {max_words} palabras y suena natural, no forzada.
- En "papas" cada término se dice con su equivalente de papás (si la lista lo da) o con su significado en
  palabras normales; el resto de la frase cambia lo mínimo y el largo es parecido.
- Situaciones cotidianas y variadas (escuela, trabajo, familia, comida, fiestas, dinero, redes, amigos, pareja),
  sin groserías fuertes ni contenido sexual, sin nombres de personas reales.
- Solo expresiones de {country_name}{neutral}: nada de jerga de otros países."""

USER = """Términos Gen Z de {country_name}:
{terms}
Escribe {n} pares distintos, cada uno en una situación distinta.
Devuelve solo JSON: una lista de objetos con "source" (la frase genz) y "target" (la frase de papas)."""


def _words(text: str) -> int:
    return len(text.split())


def co_occurring(bank: TermBank, rows: list[dict], country: str) -> list[tuple[str, ...]]:
    """Sets of Gen Z terms that appear together in real web sentences of the country (training rows only)."""
    out = []
    for r in rows:
        if r["country"] == country and r["generation"] == "genz":
            found = distinct_terms(bank, r["example"], country)
            if len(found) >= 2:
                out.append(tuple(sorted(found)))
    return out


def plan_calls(bank: TermBank, counterparts: dict, real_rows: list[dict], target: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    n_calls = -(-target // PAIRS_PER_CALL)
    countries = [c for c, w in COUNTRY_WEIGHTS.items() for _ in range(round(w * 50))]
    rng.shuffle(countries)
    combos = {c: co_occurring(bank, real_rows, c) for c in COUNTRY_WEIGHTS}
    calls = []
    for i in range(n_calls):
        country = countries[i % len(countries)]
        allowed = [country] if country == "LATAM" else [country, "LATAM"]
        own = sorted(bank.ids("genz", [country]))
        everyone = sorted(bank.ids("genz", allowed))
        pool: list[str] = []
        if combos[country] and rng.random() < 0.5:  # half the calls start from a real combination
            pool += list(rng.choice(combos[country]))
        while len(pool) < POOL:
            src = own if rng.random() < 0.75 or country == "LATAM" else everyone
            t = rng.choice(src)
            if t not in pool:
                pool.append(t)
        calls.append({"i": i, "country": country, "pool": pool, "seed": seed + i,
                      "links": {t: counterparts.get(t) for t in pool}})
    return calls


def render(bank: TermBank, call: dict) -> tuple[str, str]:
    country = call["country"]
    lines = []
    for t in call["pool"]:
        e = bank.terms[t]
        cp = call["links"].get(t)
        tail = f"; equivalente de papás: «{bank.terms[cp]['term']}»" if cp and cp in bank.terms else ""
        lines.append(f"- «{e['term']}»: {e['meaning']}{tail}")
    neutral = "" if country == "LATAM" else " o del español neutro"
    system = SYSTEM.format(country_name=COUNTRIES[country], min_words=MIN_WORDS, max_words=MAX_WORDS, neutral=neutral)
    user = USER.format(country_name=COUNTRIES[country], terms="\n".join(lines), n=PAIRS_PER_CALL)
    return system, user


def _stems(text: str) -> set[str]:
    return {w[:5] for w in normalize(text).split() if len(w) > 3 and w not in STOPWORDS}


def validate(bank: TermBank, counterparts: dict, country: str, genz: str, parent: str) -> tuple[str | None, list[str]]:
    """(reason to reject or None, the Gen Z terms of the sentence). Every term is checked by meaning."""
    terms = distinct_terms(bank, genz, country)
    nw, np_ = _words(genz), _words(parent)
    if not MIN_WORDS <= nw <= MAX_WORDS or not 0.6 <= np_ / nw <= 1.6:
        return "length", terms
    if len(terms) < 2:
        return "fewer_than_2_terms", terms
    if bank.foreign_in(genz, country) or bank.foreign_in(parent, country):
        return "foreign_term", terms
    if bank.found_in(parent, bank.ids("genz")):
        return "slang_left_in_parents", terms
    stems = _stems(parent)
    for t in terms:
        cp = counterparts.get(t)
        if cp and cp in bank.terms and bank.found(cp, parent):
            continue
        if not (_stems(bank.terms[t]["meaning"]) & stems):
            return "term_meaning_missing", terms
    if [t for t in bank.found_in(parent, bank.ids("parent")) if bank.found(t, genz)]:
        return "parent_term_left_in_genz", terms
    return None, terms


def to_pairs(call: dict, k: int, genz: str, parent: str, terms: list[str], model: str) -> list[dict]:
    base = hashlib.sha1(f"{call['seed']}|{k}|{genz}".encode()).hexdigest()[:10]
    prov = {"model": model, "prompt_version": PROMPT_VERSION, "seed": call["seed"], "item": k, "kind": "combo",
            "term_ids": terms, "pool": call["pool"], "counterpart_ids": {t: call["links"].get(t) for t in terms}}
    common = {"country": call["country"], "age_range": "16-24", "split": "train", "status": "approved", "origin": "synthetic"}
    return [
        {"id": f"cmb-{base}-f", "direction": "genz_to_parent", "source": genz, "target": parent, **common, "provenance": prov},
        {"id": f"cmb-{base}-b", "direction": "parent_to_genz", "source": parent, "target": genz, **common, "provenance": prov},
    ]


def mock_generate(bank: TermBank, call: dict) -> list[dict]:
    a, b = (bank.terms[t]["term"].split("/")[0].strip(" ¡!¿?") for t in call["pool"][:2])
    return [{"source": f"oye {a} y {b} en la escuela hoy {k}", "target": f"oye esto y aquello en la escuela hoy {k}"}
            for k in range(PAIRS_PER_CALL)]


async def main_async(args) -> None:
    s = get_settings()
    bank = TermBank(read_jsonl(DATA / "terms.jsonl"), ignore_ambiguous=True)
    counterparts = load_counterparts(DATA)
    from real_usage import usage_rows

    calls = plan_calls(bank, counterparts, usage_rows("train"), int(args.target * 2.5), args.seed)
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
    forbidden = test_sentences(DATA)
    kept, dropped, seen = [], Counter(), set()
    for c, raw in zip(calls, raws):
        for k, r in enumerate((raw or [])[:PAIRS_PER_CALL]):
            genz, parent = str(r.get("source", "")).strip(), str(r.get("target", "")).strip()
            key = normalize(genz)
            if not genz or not parent or normalize(parent) == key:
                reason = "empty_or_identical"
            elif key in seen:
                reason = "duplicate"
            elif forbidden.overlaps(genz) or forbidden.overlaps(parent):
                reason = "test_leak"  # a test, dev, probe or niche sentence, whole or inside
            else:
                reason, terms = validate(bank, counterparts, c["country"], genz, parent)
            if reason:
                dropped[reason] += 1
                continue
            seen.add(key)
            pairs = to_pairs(c, k, genz, parent, terms, model)
            for p in pairs:
                Pair.model_validate(p)
            kept.append(pairs)
    rng = random.Random(args.seed)
    rng.shuffle(kept)
    final = [p for pp in kept[: args.target] for p in pp]
    out = DATA / "pairs" / "synthetic_combo.jsonl"
    write_jsonl(out, final)
    g2p = [p for p in final if p["direction"] == "genz_to_parent"]
    meta = {"model": model, "prompt_version": PROMPT_VERSION, "base_seed": args.seed, "calls": len(calls),
            "generated": sum(len((r or [])[:PAIRS_PER_CALL]) for r in raws), "valid": len(kept),
            "kept_sentences": len(g2p), "kept_pairs": len(final), "dropped": dict(dropped),
            "countries": dict(Counter(p["country"] for p in g2p)),
            "terms_per_sentence": dict(Counter(len(p["provenance"]["term_ids"]) for p in g2p)),
            "words_genz_mean": round(sum(_words(p["source"]) for p in g2p) / max(1, len(g2p)), 1),
            "counterparts": "data/counterparts.jsonl", "tokens": usage,
            "cost_usd": round(cost_usd(goliath_prices(s).at(), usage["input"], usage["output"]), 4),
            "duration_s": round(time.time() - t0, 1), "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(meta, ensure_ascii=False))


def refilter() -> None:
    """Re-validate the kept sentences against the CURRENT term bank and counterparts; drop both directions of any
    sentence that now breaks a rule (the meta file records how many and why)."""
    bank = TermBank(read_jsonl(DATA / "terms.jsonl"), ignore_ambiguous=True)
    counterparts = load_counterparts(DATA)
    path = DATA / "pairs" / "synthetic_combo.jsonl"
    rows = list(read_jsonl(path))
    bad, dropped = set(), Counter()
    for p in rows:
        if p["direction"] == "genz_to_parent":
            reason, _ = validate(bank, counterparts, p["country"], p["source"], p["target"])
            if reason:
                bad.add(p["id"][:-2])
                dropped[reason] += 1
    kept = [p for p in rows if p["id"][:-2] not in bad]
    write_jsonl(path, kept)
    meta_path = path.with_suffix(".meta.json")
    meta = json.loads(meta_path.read_text())
    meta["refiltered"] = {"terms": len(bank.terms), "dropped_sentences": dict(dropped), "kept_pairs": len(kept),
                          "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(meta["refiltered"], ensure_ascii=False))


def main() -> None:
    if "--refilter" in sys.argv:
        return refilter()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--target", type=int, default=500, help="sentences kept (each gives one pair per direction)")
    ap.add_argument("--seed", type=int, default=6067)
    ap.add_argument("--concurrency", type=int, default=8)
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()
