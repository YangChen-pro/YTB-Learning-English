"""Deterministic vocabulary extraction and lemma/POS deduplication."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from youtube_vocab.models import NormalizedSentence, VocabularyItem, VocabularyOccurrence


def extract_vocabulary(
    sentences: list[NormalizedSentence],
    nlp: Any,
    *,
    include_proper_nouns: bool = False,
) -> list[VocabularyItem]:
    grouped: dict[tuple[str, str], list[VocabularyOccurrence]] = defaultdict(list)
    metadata: dict[tuple[str, str], tuple[bool, bool]] = {}
    for sentence in sentences:
        document = nlp(sentence.text)
        for token in document:
            if token.is_space or token.is_punct or not token.is_alpha:
                continue
            lemma = (token.lemma_ or token.text).strip().lower()
            pos = str(token.pos_ or "X")
            if not lemma:
                continue
            is_proper = pos == "PROPN"
            if is_proper and not include_proper_nouns:
                continue
            key = (lemma, pos)
            grouped[key].append(
                VocabularyOccurrence(
                    surface=str(token.text),
                    lemma=lemma,
                    pos=pos,
                    sentence_id=sentence.id,
                    sentence=sentence.text,
                    timestamp=sentence.start,
                )
            )
            metadata[key] = (bool(token.is_stop), is_proper)
    items: list[VocabularyItem] = []
    for key, occurrences in grouped.items():
        forms = list(dict.fromkeys(occurrence.surface for occurrence in occurrences))
        is_stop, is_proper = metadata[key]
        items.append(
            VocabularyItem(
                lemma=key[0],
                pos=key[1],
                surface_forms=forms,
                count=len(occurrences),
                first_timestamp=min(item.timestamp for item in occurrences),
                occurrences=occurrences,
                is_stop=is_stop,
                is_proper_noun=is_proper,
            )
        )
    return sorted(items, key=lambda item: (item.first_timestamp, item.lemma, item.pos))


def filter_known_words(
    vocabulary: list[VocabularyItem], known: set[tuple[str, str]]
) -> list[VocabularyItem]:
    normalized = {(lemma.lower(), pos.upper()) for lemma, pos in known}
    return [
        item
        for item in vocabulary
        if (item.lemma.lower(), item.pos.upper()) not in normalized
        and (item.lemma.lower(), "X") not in normalized
    ]
