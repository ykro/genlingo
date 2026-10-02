"""Leak detection between the test set and the training data.

A test sentence must not appear in training, not even inside a longer training sentence (a
real dialogue turned into a training pair, or a synthetic pair that quotes it). Exact matching
misses those, so `TextIndex.overlaps` also checks substrings, both raw and normalized (case,
accents, punctuation), in both directions: the text inside a training sentence, or a training
sentence inside the text. Substring checks need at least MIN_WORDS words, so short common
phrases ("¿en serio?") don't count as leaks.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

MIN_WORDS = 4


def norm(text: str) -> str:
    """Lowercase, no accents, no punctuation, single spaces."""
    text = unicodedata.normalize("NFKD", (text or "").lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9ñ ]+", " ", text)).strip()


class TextIndex:
    def __init__(self, texts: Iterable[str]):
        self.raw = [t.strip() for t in texts if t and t.strip()]
        self.norms = {norm(t) for t in self.raw} - {""}
        self._raw_blob = "\n".join(self.raw)
        self._norm_blob = "\n".join(f" {n} " for n in self.norms)
        self._long = [f" {n} " for n in self.norms if len(n.split()) >= MIN_WORDS]

    def overlaps(self, text: str) -> bool:
        n = norm(text)
        if not n:
            return False
        if n in self.norms:  # same sentence
            return True
        padded = f" {n} "
        if len(n.split()) >= MIN_WORDS:
            if text.strip() in self._raw_blob or padded in self._norm_blob:  # inside a training sentence
                return True
        return any(m in padded for m in self._long)  # a training sentence inside this one

    def __len__(self) -> int:
        return len(self.norms)
