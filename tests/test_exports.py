import csv
import json
from pathlib import Path

from youtube_vocab.export.json_export import export_result
from youtube_vocab.models import (
    AnalysisResult,
    ExpressionItem,
    LearningWord,
    NormalizedSentence,
    RawCaption,
)


def test_all_export_files_and_bom(tmp_path: Path) -> None:
    word = LearningWord(
        surface="entails",
        lemma="entail",
        pos="VERB",
        meaning_zh="意味着",
        explanation_zh="语境义",
        evidence="This entails work.",
        timestamp=3,
        difficulty=4,
        usefulness=5,
        confidence=0.9,
    )
    expression = ExpressionItem(
        expression="in terms of",
        canonical_form="in terms of",
        category="prepositional_phrase",
        meaning_zh="就……而言",
        explanation_zh="框定话题",
        evidence="in terms of cost",
        timestamp=4,
        usefulness=5,
        confidence=0.95,
    )
    result = AnalysisResult(
        video_id="dQw4w9WgXcQ",
        language_code="en",
        is_generated=False,
        model="test",
        prompt_version="v1",
        raw_captions=[RawCaption(id=0, start=3, duration=2, text="This entails work.")],
        sentences=[
            NormalizedSentence(
                id=0, text="This entails work.", start=3, end=5, source_caption_ids=[0]
            )
        ],
        all_words=[],
        study_words=[word],
        expressions=[expression],
        corrections=[],
    )
    destination = export_result(result, tmp_path)
    expected = {
        "metadata.json",
        "raw_captions.json",
        "normalized_sentences.json",
        "all_words.csv",
        "study_words.csv",
        "expressions.csv",
        "anki_words.csv",
        "anki_expressions.csv",
        "analysis.json",
        "report.html",
    }
    assert {path.name for path in destination.iterdir()} == expected
    assert (destination / "study_words.csv").read_bytes().startswith(b"\xef\xbb\xbf")
    assert (
        json.loads((destination / "analysis.json").read_text())["study_words"][0]["meaning_zh"]
        == "意味着"
    )
    with (destination / "anki_words.csv").open(encoding="utf-8-sig") as handle:
        row = next(csv.DictReader(handle))
    assert row["Timestamp URL"].endswith("&t=3s")
    report = (destination / "report.html").read_text(encoding="utf-8")
    assert "YouTube English Study Report" in report
    assert "deepseek" not in report.lower()
    assert "意味着" in report
