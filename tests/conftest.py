from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FakeToken:
    text: str
    lemma_: str
    pos_: str
    is_stop: bool = False
    is_space: bool = False
    is_punct: bool = False
    is_alpha: bool = True


class FakeNLP:
    mapping = {
        "take": ("take", "VERB"),
        "takes": ("take", "VERB"),
        "took": ("take", "VERB"),
        "taken": ("take", "VERB"),
        "record_n": ("record", "NOUN"),
        "record_v": ("record", "VERB"),
        "entail": ("entail", "VERB"),
        "cache": ("cache", "NOUN"),
        "hard": ("hard", "ADJ"),
    }

    def __call__(self, text: str) -> list[FakeToken]:
        tokens: list[FakeToken] = []
        for raw in text.split():
            clean = raw.strip(".,!?;:")
            lemma, pos = self.mapping.get(clean, (clean.lower(), "NOUN"))
            tokens.append(FakeToken(clean, lemma, pos))
        return tokens
