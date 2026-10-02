"""Term -> counterpart table, validated by MEANING (data/counterparts.jsonl).

    uv run --project duel python scripts/build_counterparts.py [--no-judge]

Why: pairs-v3 picked each term's counterpart in the other generation as its nearest neighbour by
embedding, and the embedding of "term: meaning" is dominated by the term's surface. 175 of the 217
links used by synthetic.jsonl had cosine < 0.6 ("brainrot -> patatús", "luca -> crush"), so most
synthetic pairs taught David a wrong-meaning substitution. Now a link exists only if:

  1. mnn      the two terms are mutual nearest neighbours with cosine >= MNN_COS, or
  2. judged   Gemini, shown the term and its top-5 candidates (same country or neutral, other
              generation), picks one as "same meaning" (or NONE), AND a deterministic check
              confirms it: a shared content word between the two meanings (5-letter stems) or
              cosine >= CHECK_COS.

Everything else has no counterpart: Gen Z -> papás then paraphrases the meaning, and papás -> Gen Z
pairs are not generated for it. The test set is never read here.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import re
import sys
import unicodedata

from _common import DATA
from genlingo_duel.dataset import read_jsonl, write_jsonl
from genlingo_duel.settings import get_settings

MNN_COS, CHECK_COS = 0.65, 0.60
OUT = DATA / "counterparts.jsonl"
STOP = set("""de la el los las un una unos unas y o a en con por para que se su sus al del lo le les
algo alguien alguna alguno muy mas más como cuando donde también tambien ser estar hacer tener dar ir
persona personas cosa cosas forma manera expresion expresión palabra decir dice dicho usado usa uso
cuando sobre todo según segun tono veces mucho mucha""".split())


def stems(meaning: str) -> set[str]:
    t = unicodedata.normalize("NFKD", meaning.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return {w[:5] for w in re.findall(r"[a-zñ]+", t) if len(w) > 3 and w not in STOP}


def cos(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b)) / math.sqrt(sum(x * x for x in a) * sum(x * x for x in b))


def pool(terms: dict, tid: str, generation: str) -> list[str]:
    """Candidates for tid: the other generation, same country or neutral (LATAM terms: LATAM only)."""
    c = terms[tid]["country"]
    allowed = {"LATAM"} if c == "LATAM" else {c, "LATAM"}
    return [k for k, t in terms.items() if t["generation"] == generation and t["country"] in allowed and not t.get("ambiguous")]


def score(terms, V, a, b) -> float:
    return cos(V[a], V[b]) + 0.15 * len(stems(terms[a]["meaning"]) & stems(terms[b]["meaning"]))


def confirmed(terms, V, a, b) -> bool:
    return bool(stems(terms[a]["meaning"]) & stems(terms[b]["meaning"])) or cos(V[a], V[b]) >= CHECK_COS


JUDGE = """Término de {gen_a} de {country}: «{term}» = {meaning}

¿Cuál de estas expresiones de {gen_b} significa lo mismo (se podría usar en su lugar en la misma frase)?
{options}
Responde solo JSON: {{"choice": <número de la opción> o null si ninguna significa lo mismo}}."""
GEN = {"genz": "jóvenes (Gen Z)", "parent": "papás"}


async def judge(client, model, terms, a, cands) -> str | None:
    from google.genai import types

    t = terms[a]
    other = "parent" if t["generation"] == "genz" else "genz"
    options = "\n".join(f"{i + 1}. «{terms[c]['term']}» = {terms[c]['meaning']}" for i, c in enumerate(cands))
    prompt = JUDGE.format(gen_a=GEN[t["generation"]], gen_b=GEN[other], country=t["country"], term=t["term"],
                          meaning=t["meaning"], options=options)
    cfg = types.GenerateContentConfig(temperature=0.0, response_mime_type="application/json",
                                      thinking_config=types.ThinkingConfig(thinking_level="low"))
    for attempt in range(4):
        try:
            res = await asyncio.wait_for(client.aio.models.generate_content(model=model, contents=prompt, config=cfg), 60)
            choice = json.loads(res.text).get("choice")
            return cands[int(choice) - 1] if isinstance(choice, int) and 1 <= choice <= len(cands) else None
        except Exception:
            await asyncio.sleep(2 ** (attempt + 1))
    return None


async def main_async(no_judge: bool) -> None:
    s = get_settings()
    terms = {t["id"]: t for t in read_jsonl(DATA / "terms.jsonl")}
    V = json.loads((DATA / ".cache" / "term_embeddings.json").read_text())["vectors"]
    ids = [k for k, t in terms.items() if k in V and not t.get("ambiguous")]
    top: dict[str, list[str]] = {}
    for a in ids:
        other = "parent" if terms[a]["generation"] == "genz" else "genz"
        cands = [c for c in pool(terms, a, other) if c in V]
        top[a] = sorted(cands, key=lambda c: -score(terms, V, a, c))[:5]

    def nearest_back(c: str, a: str) -> str | None:
        """c's nearest term in a's generation and a's country pool (so the relation can be mutual)."""
        back = [k for k in pool(terms, a, terms[a]["generation"]) if k in V]
        return max(back, key=lambda k: cos(V[c], V[k]), default=None)

    rows, todo = {}, []
    for a in ids:
        if not top[a]:
            rows[a] = (None, None, "no_candidates")
            continue
        c = max(top[a], key=lambda c: cos(V[a], V[c]))
        if cos(V[a], V[c]) >= MNN_COS and nearest_back(c, a) == a:
            rows[a] = (c, cos(V[a], V[c]), "mnn")
        else:
            todo.append(a)
    if todo and not no_judge and not s.mock_ai:
        from google import genai

        client = genai.Client(vertexai=True, project=s.project, location=s.location)
        sem = asyncio.Semaphore(8)

        async def one(a):
            async with sem:
                return a, await judge(client, s.gemini_model, terms, a, top[a])

        for a, pick in await asyncio.gather(*(one(a) for a in todo)):
            if pick and confirmed(terms, V, a, pick):
                rows[a] = (pick, cos(V[a], V[pick]), "judged")
            else:
                rows[a] = (None, None, "judge_none" if pick is None else "judge_unconfirmed")
    for a in ids:
        rows.setdefault(a, (None, None, "unjudged"))
    out = []
    for a in ids:
        c, cs, method = rows[a]
        out.append({"term_id": a, "term": terms[a]["term"], "generation": terms[a]["generation"], "country": terms[a]["country"],
                    "counterpart_id": c, "counterpart": terms[c]["term"] if c else None,
                    "cos": round(cs, 3) if cs is not None else None, "method": method, "candidates": top[a]})
    write_jsonl(OUT, out)
    by = {}
    for r in out:
        by[r["method"]] = by.get(r["method"], 0) + 1
    print(json.dumps({"terms": len(out), "with_counterpart": sum(1 for r in out if r["counterpart_id"]), "by_method": by}))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-judge", action="store_true", help="mutual nearest neighbours only (no Gemini)")
    asyncio.run(main_async(ap.parse_args().no_judge))


if __name__ == "__main__":
    sys.exit(main())
