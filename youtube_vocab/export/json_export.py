"""Write the complete per-video artifact directory."""

from __future__ import annotations

import json
from pathlib import Path

from youtube_vocab.export.anki_export import export_anki_expressions, export_anki_words
from youtube_vocab.export.csv_export import export_all_words, export_expressions, export_study_words
from youtube_vocab.export.html_export import export_html_report
from youtube_vocab.models import AnalysisResult


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )


def export_result(result: AnalysisResult, output_root: Path) -> Path:
    destination = output_root / result.video_id
    try:
        destination.mkdir(parents=True, exist_ok=True)
        _write_json(
            destination / "metadata.json",
            {
                "video_id": result.video_id,
                "language_code": result.language_code,
                "is_generated": result.is_generated,
                "model": result.model,
                "prompt_version": result.prompt_version,
                "analyzed_at": result.analyzed_at,
                "caption_count": len(result.raw_captions),
                "sentence_count": len(result.sentences),
            },
        )
        _write_json(
            destination / "raw_captions.json",
            [item.model_dump(mode="json") for item in result.raw_captions],
        )
        _write_json(
            destination / "normalized_sentences.json",
            [item.model_dump(mode="json") for item in result.sentences],
        )
        _write_json(destination / "analysis.json", result.model_dump(mode="json"))
        export_all_words(result, destination / "all_words.csv")
        export_study_words(result, destination / "study_words.csv")
        export_expressions(result, destination / "expressions.csv")
        export_anki_words(result, destination / "anki_words.csv")
        export_anki_expressions(result, destination / "anki_expressions.csv")
        export_html_report(result, destination / "report.html")
    except OSError as exc:
        raise OSError(f"输出目录不可写：{destination}（{exc}）") from exc
    return destination
