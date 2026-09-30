"""Generate synthetic TRAINING pairs with Gemini, anchored on the real-slang term bank.

    uv run --project duel python scripts/generate_pairs.py [--target 1000] [--seed 2027]

Why anchored: asked cold, a model invents slang that sounds like an ad ("¡qué épico, bro!").
Each call gets one real term with its meaning, a real usage example and the country, so the
synthetic sentences use slang people actually say. Why synthetic only for training: a test set
written by Gemini would reward Gemini (Goliath) for sounding like itself; the test set comes
from real web usage instead (scripts/build_test_set.py).

Every pair records model, prompt version and seed. Balanced by direction by construction:
calls alternate genz_to_parent / parent_to_genz.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

from _common import ROOT  # noqa: F401  (puts duel/ on sys.path)
from duel_core import Price, cost_usd  # noqa: E402
from genlingo_duel.dataset import Pair, read_jsonl, write_jsonl  # noqa: E402
from genlingo_duel.prompts import COUNTRIES  # noqa: E402
from genlingo_duel.settings import get_settings  # noqa: E402

# pairs-v1 let Gemini paraphrase freely; David learned to add "mijo", extra clauses and length,
# and scored below the base model on real test pairs. pairs-v2 asks for minimal edits: change
# only the generational words, keep everything else. That is what a translation of register is.
PROMPT_VERSION = "pairs-v2"
PAIRS_PER_CALL = 5
MAX_WORDS = 30

SYSTEM = """Eres lingüista y conoces cómo habla la gente en {country_name}.
Escribes pares de frases para entrenar un traductor generacional:
- Habla Gen Z: jóvenes de 16 a 24 años de {country_name}, como escriben en chats y redes.
- Habla de papás: adultos de 45 a 60 años de {country_name}, registro coloquial de su generación, sin slang juvenil.
Cada par dice lo mismo en las dos formas de hablar. Frases cotidianas y variadas (escuela, trabajo,
familia, comida, fiestas, dinero, redes, noviazgo), de 4 a {max_words} palabras, sin groserías fuertes
ni contenido sexual, sin nombres de personas reales.
Reglas del "target" (es una traducción de registro, no una paráfrasis):
- Cambia solo las palabras y expresiones generacionales; conserva el resto de palabras, el orden y la puntuación.
- No agregues vocativos que no estén en el "source" (mijo, hijo, bro, mano, parce…), ni explicaciones, ni información nueva.
- Misma longitud aproximada (±3 palabras) y misma persona gramatical."""

USER = """Término real: «{term}» ({generation_label})
Significado: {meaning}
Ejemplo real de uso: «{example}»

Escribe {n} pares distintos en dirección {direction_label}.
{usage_rule}
No copies el ejemplo; inventa situaciones nuevas.
Devuelve solo JSON: una lista de objetos con "source" y "target"."""

DIRECTION_LABEL = {
    "genz_to_parent": "Gen Z → papás (source = habla Gen Z, target = cómo lo diría un papá o una mamá)",
    "parent_to_genz": "papás → Gen Z (source = habla de papás, target = cómo lo diría alguien Gen Z)",
}


def usage_rule(generation: str, direction: str) -> str:
    side = {
        ("genz", "genz_to_parent"): "source",
        ("genz", "parent_to_genz"): "target",
        ("parent", "genz_to_parent"): "target",
        ("parent", "parent_to_genz"): "source",
    }[(generation, direction)]
    return f"El término «{{term}}» debe aparecer (o una variante natural) en el lado \"{side}\"; el otro lado no lo usa."


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9ñ ]+", "", re.sub(r"\s+", " ", text)).strip()


def plan_calls(terms: list[dict], target: int, seed: int) -> list[dict]:
    """Round-robin over countries so no variant dominates; directions alternate per call."""
    by_country: dict[str, list[dict]] = {}
    for t in sorted(terms, key=lambda t: t["id"]):
        by_country.setdefault(t["country"], []).append(t)
    order = [c for c in COUNTRIES if c in by_country]
    n_calls = -(-target // PAIRS_PER_CALL)
    calls, cursor = [], {c: 0 for c in order}
    for i in range(n_calls):
        country = order[i % len(order)]
        bucket = by_country[country]
        term = bucket[cursor[country] % len(bucket)]
        cursor[country] += 1
        direction = "genz_to_parent" if i % 2 == 0 else "parent_to_genz"
        calls.append({"i": i, "term": term, "direction": direction, "seed": seed + i})
    return calls


def render(call: dict) -> tuple[str, str]:
    t = call["term"]
    system = SYSTEM.format(country_name=COUNTRIES[t["country"]], max_words=MAX_WORDS)
    user = USER.format(
        term=t["term"],
        generation_label="habla Gen Z" if t["generation"] == "genz" else "habla de papás",
        meaning=t["meaning"],
        example=t["example"],
        n=PAIRS_PER_CALL,
        direction_label=DIRECTION_LABEL[call["direction"]],
        usage_rule=usage_rule(t["generation"], call["direction"]).format(term=t["term"]),
    )
    return system, user


def mock_generate(call: dict) -> list[dict]:
    t = call["term"]
    return [
        {"source": f"{t['term']} ejemplo {k} de {call['i']}", "target": f"significa {t['meaning']} ({k}/{call['i']})"}
        for k in range(PAIRS_PER_CALL)
    ]


async def gemini_generate(client, model: str, call: dict, usage: dict) -> list[dict]:
    from google.genai import types

    system, user = render(call)
    schema = {
        "type": "ARRAY",
        "items": {"type": "OBJECT", "properties": {"source": {"type": "STRING"}, "target": {"type": "STRING"}}, "required": ["source", "target"]},
    }
    cfg = types.GenerateContentConfig(
        system_instruction=system,
        temperature=1.0,  # variety matters more than determinism here; the seed makes it repeatable
        seed=call["seed"],
        response_mime_type="application/json",
        response_schema=schema,
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
        except Exception as exc:  # 429s, timeouts and the occasional bad JSON: back off and retry
            if attempt == 4:
                print(f"  call {call['i']} failed: {type(exc).__name__}: {str(exc)[:120]}", file=sys.stderr)
                return []
            await asyncio.sleep(2 ** (attempt + 1))
    return []


def to_pairs(call: dict, raw: list[dict], model: str) -> list[dict]:
    t = call["term"]
    out = []
    for k, r in enumerate(raw[:PAIRS_PER_CALL]):
        src, tgt = str(r.get("source", "")).strip(), str(r.get("target", "")).strip()
        pid = "syn-" + hashlib.sha1(f"{call['seed']}|{k}|{src}".encode()).hexdigest()[:10]
        out.append(
            {
                "id": pid,
                "direction": call["direction"],
                "source": src,
                "target": tgt,
                "country": t["country"],
                "age_range": "16-24",
                "split": "train",
                # Synthetic pairs are auto-approved after the automatic checks below; people only
                # review the test set and audience pairs.
                "status": "approved",
                "origin": "synthetic",
                "provenance": {
                    "model": model,
                    "prompt_version": PROMPT_VERSION,
                    "seed": call["seed"],
                    "term_id": t["id"],
                    "item": k,
                },
            }
        )
    return out


def filter_pairs(pairs: list[dict], forbidden: set[str]) -> tuple[list[dict], dict[str, int]]:
    """Automatic checks: schema, length, not identical, no duplicates, no test-set leakage."""
    kept, seen, dropped = [], set(), {"schema": 0, "length": 0, "identical": 0, "duplicate": 0, "leak": 0}
    for p in pairs:
        try:
            Pair.model_validate(p)
        except Exception:
            dropped["schema"] += 1
            continue
        s, t = normalize(p["source"]), normalize(p["target"])
        if len(p["source"].split()) > MAX_WORDS or len(p["target"].split()) > MAX_WORDS + 10 or len(s) < 3:
            dropped["length"] += 1
        elif s == t:
            dropped["identical"] += 1
        elif s in seen:
            dropped["duplicate"] += 1
        elif s in forbidden or t in forbidden:
            dropped["leak"] += 1
        else:
            seen.add(s)
            kept.append(p)
    return kept, dropped


def balance(pairs: list[dict], target: int) -> list[dict]:
    """Same number of pairs per direction (target/2 each), keeping generation order."""
    per_dir = target // 2
    by_dir = {d: [p for p in pairs if p["direction"] == d] for d in DIRECTION_LABEL}
    n = min(per_dir, *(len(v) for v in by_dir.values()))
    keep = {p["id"] for v in by_dir.values() for p in v[:n]}
    return [p for p in pairs if p["id"] in keep]


def test_sentences(data_dir: Path) -> set[str]:
    """Sentences reserved for the test set: the generator must never reproduce them."""
    forbidden = set()
    for row in read_jsonl(data_dir / "raw" / "web_usage.jsonl"):
        forbidden |= {normalize(row["example"]), normalize(row.get("rewrite", ""))}
    for row in read_jsonl(data_dir / "pairs" / "test_web.jsonl"):
        forbidden |= {normalize(row["source"]), normalize(row["target"])}
    forbidden.discard("")
    return forbidden


async def main_async(args: argparse.Namespace) -> None:
    s = get_settings()
    data = s.data_dir
    terms = list(read_jsonl(data / "terms.jsonl"))
    if not terms:
        sys.exit("data/terms.jsonl is empty: build the term bank first")
    forbidden = test_sentences(data)
    # The generator sees the term-bank example; it must not be a test sentence.
    terms = [t for t in terms if normalize(t["example"]) not in forbidden]
    # Over-generate ~10% because the automatic checks drop some pairs, then trim to balance.
    calls = plan_calls(terms, int(args.target * 1.1), args.seed)
    model = "mock" if s.mock_ai else s.gemini_model
    usage = {"input": 0, "output": 0}
    t0 = time.time()

    if s.mock_ai:
        raws = [mock_generate(c) for c in calls]
    else:
        from google import genai

        client = genai.Client(vertexai=True, project=s.project, location=s.location)
        sem = asyncio.Semaphore(args.concurrency)

        async def one(c):
            async with sem:
                return await gemini_generate(client, model, c, usage)

        done = 0

        async def tracked(c):
            nonlocal done
            out = await one(c)
            done += 1
            if done % 20 == 0:
                print(f"  {done}/{len(calls)} calls", flush=True)
            return out

        raws = await asyncio.gather(*(tracked(c) for c in calls))

    pairs = [p for c, raw in zip(calls, raws) for p in to_pairs(c, raw, model)]
    kept, dropped = filter_pairs(pairs, forbidden)
    kept = balance(kept, args.target)
    out = Path(args.out) if args.out else data / "pairs" / "synthetic.jsonl"
    write_jsonl(out, kept)
    meta = {
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "base_seed": args.seed,
        "calls": len(calls),
        "generated": len(pairs),
        "kept": len(kept),
        "dropped": dropped,
        "tokens": usage,
        "cost_usd": round(cost_usd(Price(s.gemini_input_usd_per_m, s.gemini_output_usd_per_m), usage["input"], usage["output"]), 4),
        "duration_s": round(time.time() - t0, 1),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(meta, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--target", type=int, default=int(__import__("os").environ.get("SYNTHETIC_PAIRS_TARGET", 1000)))
    ap.add_argument("--seed", type=int, default=2027)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--out", default=None)
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()
