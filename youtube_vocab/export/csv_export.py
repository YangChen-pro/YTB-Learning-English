"""Excel-compatible CSV exports."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from youtube_vocab.models import AnalysisResult


def timestamp_url(video_id: str, timestamp: float) -> str:
    return f"https://www.youtube.com/watch?v={video_id}&t={max(0, int(timestamp))}s"


def _write(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_all_words(result: AnalysisResult, path: Path) -> None:
    fields = ["lemma", "pos", "surface_forms", "count", "first_timestamp", "example", "youtube_url"]
    _write(
        path,
        fields,
        (
            {
                "lemma": item.lemma,
                "pos": item.pos,
                "surface_forms": " | ".join(item.surface_forms),
                "count": item.count,
                "first_timestamp": item.first_timestamp,
                "example": item.occurrences[0].sentence if item.occurrences else "",
                "youtube_url": timestamp_url(result.video_id, item.first_timestamp),
            }
            for item in result.all_words
        ),
    )


def export_study_words(result: AnalysisResult, path: Path) -> None:
    fields = [
        "lemma",
        "surface",
        "pos",
        "meaning_zh",
        "explanation_zh",
        "difficulty",
        "usefulness",
        "confidence",
        "evidence",
        "timestamp",
        "youtube_url",
    ]
    _write(
        path,
        fields,
        (
            {
                **item.model_dump(),
                "youtube_url": timestamp_url(result.video_id, item.timestamp),
            }
            for item in result.study_words
        ),
    )


def export_expressions(result: AnalysisResult, path: Path) -> None:
    fields = [
        "canonical_form",
        "expression",
        "category",
        "meaning_zh",
        "explanation_zh",
        "usefulness",
        "confidence",
        "evidence",
        "timestamp",
        "youtube_url",
    ]
    _write(
        path,
        fields,
        (
            {
                **item.model_dump(),
                "youtube_url": timestamp_url(result.video_id, item.timestamp),
            }
            for item in result.expressions
        ),
    )
