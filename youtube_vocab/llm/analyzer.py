"""Chunk prompting, grounding checks, filtering, and global deduplication."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable

from youtube_vocab.llm.prompts import SYSTEM_PROMPT
from youtube_vocab.models import (
    ChunkAnalysis,
    ContextChunk,
    ExpressionItem,
    LearningWord,
    SubtitleCorrection,
)

WarningSink = Callable[[str], None]


def build_user_prompt(chunk: ContextChunk) -> str:
    payload = {
        "time_range": {"start": chunk.start, "end": chunk.end},
        "sentences": [
            {"id": sentence.id, "timestamp": sentence.start, "text": sentence.text}
            for sentence in chunk.sentences
        ],
        "candidates": [
            {
                "lemma": item.lemma,
                "pos": item.pos,
                "surface_forms": item.surface_forms,
                "count_in_video": item.count,
            }
            for item in chunk.candidates
        ],
        "known_words_in_this_chunk": [
            {"lemma": lemma, "pos": pos} for lemma, pos in chunk.known_words
        ],
    }
    return "Analyze this grounded caption chunk:\n" + json.dumps(payload, ensure_ascii=False)


def _normalized_text(value: str) -> str:
    return " ".join(value.casefold().split())


def validate_chunk_analysis(
    analysis: ChunkAnalysis,
    chunk: ContextChunk,
    *,
    min_usefulness: int,
    min_confidence: float,
    warn: WarningSink,
) -> ChunkAnalysis:
    context = _normalized_text(chunk.text)
    candidates = {(item.lemma.casefold(), item.pos.upper()) for item in chunk.candidates}
    words: list[LearningWord] = []
    for item in analysis.vocabulary:
        reason: str | None = None
        if _normalized_text(item.evidence) not in context:
            reason = f"词汇 {item.lemma}/{item.pos} 的 evidence 不在输入上下文中"
        elif not chunk.start <= item.timestamp <= chunk.end:
            reason = f"词汇 {item.lemma}/{item.pos} 的 timestamp 越界"
        elif (item.lemma.casefold(), item.pos.upper()) not in candidates:
            reason = f"词汇 {item.lemma}/{item.pos} 不在本地候选列表中"
        elif item.usefulness < min_usefulness or item.confidence < min_confidence:
            reason = f"词汇 {item.lemma}/{item.pos} 未达到阈值"
        if reason:
            warn(reason)
        else:
            words.append(item)

    expressions: list[ExpressionItem] = []
    for expression in analysis.expressions:
        if _normalized_text(expression.evidence) not in context:
            warn(f"表达 {expression.canonical_form!r} 的 evidence 不在输入上下文中")
        elif not chunk.start <= expression.timestamp <= chunk.end:
            warn(f"表达 {expression.canonical_form!r} 的 timestamp 越界")
        elif expression.usefulness < min_usefulness or expression.confidence < min_confidence:
            warn(f"表达 {expression.canonical_form!r} 未达到阈值")
        else:
            expressions.append(expression)

    corrections: list[SubtitleCorrection] = []
    for correction in analysis.corrections:
        if _normalized_text(correction.original) not in context:
            warn(f"字幕纠错原文 {correction.original!r} 不在输入上下文中")
        elif correction.confidence < min_confidence:
            warn(f"字幕纠错 {correction.original!r} 未达到置信度阈值")
        else:
            corrections.append(correction)
    return ChunkAnalysis(vocabulary=words, expressions=expressions, corrections=corrections)


def analyze_chunks(
    chunks: Iterable[ContextChunk],
    client: object,
    *,
    min_usefulness: int,
    min_confidence: float,
    warn: WarningSink,
) -> ChunkAnalysis:
    words: list[LearningWord] = []
    expressions: list[ExpressionItem] = []
    corrections: list[SubtitleCorrection] = []
    for chunk in chunks:
        raw = client.analyze(SYSTEM_PROMPT, build_user_prompt(chunk))  # type: ignore[attr-defined]
        valid = validate_chunk_analysis(
            raw,
            chunk,
            min_usefulness=min_usefulness,
            min_confidence=min_confidence,
            warn=warn,
        )
        words.extend(valid.vocabulary)
        expressions.extend(valid.expressions)
        corrections.extend(valid.corrections)
    return ChunkAnalysis(
        vocabulary=deduplicate_learning_words(words),
        expressions=deduplicate_expressions(expressions),
        corrections=deduplicate_corrections(corrections),
    )


def deduplicate_learning_words(items: Iterable[LearningWord]) -> list[LearningWord]:
    selected: dict[tuple[str, str], LearningWord] = {}
    first_seen: dict[tuple[str, str], float] = {}
    for item in items:
        key = (item.lemma.casefold(), item.pos.upper())
        first_seen[key] = min(first_seen.get(key, item.timestamp), item.timestamp)
        current = selected.get(key)
        quality = (item.confidence, item.usefulness, len(item.evidence), -item.timestamp)
        if current is None or quality > (
            current.confidence,
            current.usefulness,
            len(current.evidence),
            -current.timestamp,
        ):
            selected[key] = item
    return sorted(
        selected.values(), key=lambda item: first_seen[(item.lemma.casefold(), item.pos.upper())]
    )


def canonical_expression(value: str) -> str:
    value = re.sub(r"[^\w\s'-]", " ", value.casefold())
    return " ".join(value.split())


def deduplicate_expressions(items: Iterable[ExpressionItem]) -> list[ExpressionItem]:
    selected: dict[str, ExpressionItem] = {}
    for item in items:
        key = canonical_expression(item.canonical_form)
        current = selected.get(key)
        quality = (item.confidence, item.usefulness, len(item.evidence), -item.timestamp)
        if current is None or quality > (
            current.confidence,
            current.usefulness,
            len(current.evidence),
            -current.timestamp,
        ):
            selected[key] = item
    return sorted(selected.values(), key=lambda item: item.timestamp)


def deduplicate_corrections(items: Iterable[SubtitleCorrection]) -> list[SubtitleCorrection]:
    selected: dict[tuple[str, str], SubtitleCorrection] = {}
    for item in items:
        key = (_normalized_text(item.original), _normalized_text(item.suggested))
        if key not in selected or item.confidence > selected[key].confidence:
            selected[key] = item
    return list(selected.values())
