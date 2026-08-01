"""Anki-friendly UTF-8 BOM CSV files."""

from __future__ import annotations

from pathlib import Path

from youtube_vocab.export.csv_export import _write, timestamp_url
from youtube_vocab.models import AnalysisResult


def export_anki_words(result: AnalysisResult, path: Path) -> None:
    fields = ["Front", "Back", "Example", "Timestamp URL", "Tags"]
    _write(
        path,
        fields,
        (
            {
                "Front": f"{item.lemma} ({item.pos})",
                "Back": f"{item.meaning_zh}<br>{item.explanation_zh}",
                "Example": item.evidence,
                "Timestamp URL": timestamp_url(result.video_id, item.timestamp),
                "Tags": f"ytvocab word {item.pos.lower()}",
            }
            for item in result.study_words
        ),
    )


def export_anki_expressions(result: AnalysisResult, path: Path) -> None:
    fields = ["Front", "Back", "Example", "Timestamp URL", "Category", "Tags"]
    _write(
        path,
        fields,
        (
            {
                "Front": item.canonical_form,
                "Back": f"{item.meaning_zh}<br>{item.explanation_zh}",
                "Example": item.evidence,
                "Timestamp URL": timestamp_url(result.video_id, item.timestamp),
                "Category": item.category,
                "Tags": f"ytvocab expression {item.category}",
            }
            for item in result.expressions
        ),
    )
