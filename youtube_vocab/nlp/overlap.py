"""Token-level overlap removal for rolling YouTube captions."""

from __future__ import annotations

import re

TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*|[^\w\s]", re.UNICODE)
NO_SPACE_BEFORE = set('.,!?;:%)]}’"')
NO_SPACE_AFTER = set('([{‘"')


def tokenize_for_merge(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def _lexical(token: str) -> str | None:
    normalized = token.lower().replace("’", "'")
    return normalized if any(char.isalnum() for char in normalized) else None


def longest_token_overlap(previous: str, following: str) -> tuple[int, int]:
    """Return lexical overlap length and next-token cut index.

    Matching ignores punctuation and case, while the cut index addresses original next tokens.
    """
    previous_tokens = tokenize_for_merge(previous)
    next_tokens = tokenize_for_merge(following)
    prev_words = [word for token in previous_tokens if (word := _lexical(token)) is not None]
    next_word_positions = [
        (index, word)
        for index, token in enumerate(next_tokens)
        if (word := _lexical(token)) is not None
    ]
    next_words = [word for _, word in next_word_positions]
    maximum = min(len(prev_words), len(next_words))
    for size in range(maximum, 0, -1):
        if prev_words[-size:] == next_words[:size]:
            return size, next_word_positions[size - 1][0] + 1
    return 0, 0


def untokenize(tokens: list[str]) -> str:
    output = ""
    previous = ""
    for token in tokens:
        if not output or token in NO_SPACE_BEFORE or previous in NO_SPACE_AFTER:
            output += token
        else:
            output += " " + token
        previous = token
    return output.strip()


def merge_overlapping_text(previous: str, following: str) -> tuple[str, bool]:
    """Append only the non-overlapping portion of *following*."""
    overlap, cut = longest_token_overlap(previous, following)
    if overlap == 0:
        return untokenize(tokenize_for_merge(previous) + tokenize_for_merge(following)), False
    following_tokens = tokenize_for_merge(following)
    remaining = following_tokens[cut:]
    while remaining and _lexical(remaining[0]) is None:
        # Prefer punctuation from the newer caption at the overlap boundary.
        if remaining[0] in ".,!?;:":
            previous = previous.rstrip(".,!?;:") + remaining.pop(0)
        else:
            remaining.pop(0)
    return untokenize(tokenize_for_merge(previous) + remaining), True
