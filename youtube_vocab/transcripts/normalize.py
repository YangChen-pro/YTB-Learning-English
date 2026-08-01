"""Caption cleanup, rolling-overlap removal, and sentence restoration."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

from youtube_vocab.models import ContextChunk, NormalizedSentence, RawCaption, VocabularyItem
from youtube_vocab.nlp.overlap import merge_overlapping_text

SENTENCE_RE = re.compile(r".+?(?:[.!?]+(?=\s|$)|$)", re.DOTALL)
SPACE_RE = re.compile(r"\s+")


@dataclass(slots=True)
class _CaptionGroup:
    text: str
    start: float
    end: float
    source_ids: list[int] = field(default_factory=list)


def clean_caption_text(text: str) -> str:
    text = html.unescape(text).replace("\n", " ")
    text = re.sub(r"</?[^>]+>", "", text)
    text = re.sub(r"\[(?:music|applause|laughter|noise)\]", "", text, flags=re.I)
    return SPACE_RE.sub(" ", text).strip()


def normalize_captions(
    captions: list[RawCaption],
    *,
    max_duration: float = 25.0,
    max_chars: int = 320,
    pause_threshold: float = 1.8,
) -> list[NormalizedSentence]:
    groups: list[_CaptionGroup] = []
    current: _CaptionGroup | None = None
    for caption in captions:
        text = clean_caption_text(caption.text)
        if not text:
            continue
        end = caption.start + caption.duration
        if current is None:
            current = _CaptionGroup(text, caption.start, end, [caption.id])
            continue
        gap = caption.start - current.end
        merged, overlapped = merge_overlapping_text(current.text, text)
        should_split = (
            gap > pause_threshold
            or end - current.start > max_duration
            or len(merged) > max_chars
            or (not overlapped and bool(re.search(r"[.!?][\"']?$", current.text)))
        )
        if should_split:
            groups.append(current)
            current = _CaptionGroup(text, caption.start, end, [caption.id])
        else:
            current.text = merged
            current.end = max(current.end, end)
            current.source_ids.append(caption.id)
    if current is not None:
        groups.append(current)

    sentences: list[NormalizedSentence] = []
    for group in groups:
        pieces = [
            SPACE_RE.sub(" ", match.group()).strip() for match in SENTENCE_RE.finditer(group.text)
        ]
        pieces = [piece for piece in pieces if piece]
        if not pieces:
            continue
        total_chars = max(sum(len(piece) for piece in pieces), 1)
        elapsed_chars = 0
        for piece in pieces:
            start_ratio = elapsed_chars / total_chars
            elapsed_chars += len(piece)
            end_ratio = elapsed_chars / total_chars
            sentences.append(
                NormalizedSentence(
                    id=len(sentences),
                    text=piece,
                    start=group.start + (group.end - group.start) * start_ratio,
                    end=group.start + (group.end - group.start) * end_ratio,
                    source_caption_ids=list(group.source_ids),
                )
            )
    return sentences


def make_context_chunks(
    sentences: list[NormalizedSentence],
    vocabulary: list[VocabularyItem],
    *,
    known_vocabulary: list[VocabularyItem] | None = None,
    max_duration: float = 90.0,
    max_chars: int = 3500,
) -> list[ContextChunk]:
    chunks: list[ContextChunk] = []
    group: list[NormalizedSentence] = []
    char_count = 0
    for sentence in sentences:
        if group and (
            sentence.end - group[0].start > max_duration
            or char_count + len(sentence.text) > max_chars
        ):
            chunks.append(_make_chunk(len(chunks), group, vocabulary, known_vocabulary or []))
            group = []
            char_count = 0
        group.append(sentence)
        char_count += len(sentence.text)
    if group:
        chunks.append(_make_chunk(len(chunks), group, vocabulary, known_vocabulary or []))
    return chunks


def _make_chunk(
    chunk_id: int,
    sentences: list[NormalizedSentence],
    vocabulary: list[VocabularyItem],
    known_vocabulary: list[VocabularyItem],
) -> ContextChunk:
    sentence_ids = {sentence.id for sentence in sentences}
    candidates = [
        item
        for item in vocabulary
        if any(occurrence.sentence_id in sentence_ids for occurrence in item.occurrences)
    ]
    known_words = [
        (item.lemma, item.pos)
        for item in known_vocabulary
        if any(occurrence.sentence_id in sentence_ids for occurrence in item.occurrences)
    ]
    return ContextChunk(
        id=chunk_id,
        sentences=list(sentences),
        candidates=candidates,
        known_words=known_words,
    )
