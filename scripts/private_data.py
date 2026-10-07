"""Verbatim text of sources that don't allow redistribution: kept in a private bucket, not in the repo.

    uv run --project duel python scripts/private_data.py pull     # bucket -> data/.private/ (make data-pull)
    uv run --project duel python scripts/private_data.py push     # data/.private/ -> bucket (make data-push)
    uv run --project duel python scripts/private_data.py split    # full repo files -> data/.private/ + redacted repo files

The repo keeps every record (term, paraphrased meaning, URL, our own rewrite) and the full text of the open
sources (genlingo_duel.dataset.OPEN_SOURCES); the quoted sentences of the other sources are null there and
listed in "redacted". data/.private/ holds the full files; genlingo_duel.dataset.read_jsonl reads them when
present, and write_jsonl writes both, so every script works the same once `make data-pull` has run.
`pull` also brings data/.cache/term_embeddings.json (the term bank's EmbeddingGemma vectors, a regenerable
cache the page image and the training data use; scripts rebuild it on David's service when it is missing).
"""

from __future__ import annotations

import os
import subprocess
import sys

from _common import DATA
from genlingo_duel.dataset import PRIVATE_DIRNAME, _write, is_private_file, read_jsonl, redact

PRIVATE = DATA / PRIVATE_DIRNAME


def bucket() -> str:
    uri = os.environ.get("PRIVATE_DATA_URI")
    if not uri:
        sys.exit("PRIVATE_DATA_URI is not set (see .env.example)")
    return uri.rstrip("/")


def gcloud(*args: str) -> None:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    subprocess.run(["gcloud", "storage", *args, *([f"--project={project}"] if project else [])], check=True)


def private_files() -> list[str]:
    return sorted(str(p.relative_to(DATA)) for p in DATA.rglob("*.jsonl")
                  if PRIVATE_DIRNAME not in p.parts and is_private_file(str(p.relative_to(DATA))))


def split() -> None:
    """Move the quoted text of closed sources out of the repo files (idempotent: reads the private copy first)."""
    n_red = 0
    for rel in private_files():
        rows = list(read_jsonl(DATA / rel))  # the full rows (from data/.private/ if it is there)
        _write(PRIVATE / rel, rows)
        public = [redact(rel, r) for r in rows]
        n_red += sum(1 for r in public if r.get("redacted"))
        _write(DATA / rel, public)
    print(f"{len(private_files())} files, {n_red} records with quoted text moved to {PRIVATE.relative_to(DATA.parent)}")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    cache = DATA / ".cache" / "term_embeddings.json"  # regenerable (EmbeddingGemma on David), kept out of git
    if cmd == "pull":
        PRIVATE.mkdir(parents=True, exist_ok=True)
        cache.parent.mkdir(parents=True, exist_ok=True)
        gcloud("rsync", "-r", f"{bucket()}/data", str(PRIVATE))
        gcloud("cp", f"{bucket()}/cache/term_embeddings.json", str(cache))
    elif cmd == "push":
        gcloud("rsync", "-r", str(PRIVATE), f"{bucket()}/data")
        if cache.exists():
            gcloud("cp", str(cache), f"{bucket()}/cache/term_embeddings.json")
    elif cmd == "split":
        split()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
