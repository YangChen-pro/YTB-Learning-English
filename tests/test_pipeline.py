from pathlib import Path

import pytest
from conftest import FakeNLP

from youtube_vocab.config import Settings
from youtube_vocab.errors import NoEnglishTranscriptError
from youtube_vocab.models import RawCaption, TranscriptDocument, TranscriptTrack
from youtube_vocab.pipeline import analyze_video


class FakeProvider:
    def fetch(self, video_id: str, language: str = "en") -> TranscriptDocument:
        track = TranscriptTrack(language_code="en", language="English", is_generated=True)
        return TranscriptDocument(
            video_id=video_id,
            selected_track=track,
            available_tracks=[track],
            captions=[RawCaption(id=0, start=0, duration=2, text="cache invalidation is hard.")],
        )


class EmptyProvider:
    def fetch(self, video_id: str, language: str = "en") -> TranscriptDocument:
        raise NoEnglishTranscriptError("没有可用的英文字幕；当前版本不会运行 ASR。")


def test_no_llm_runs_without_api_key(tmp_path: Path) -> None:
    settings = Settings(model="test", api_key=None, database_path=tmp_path / "test.db")
    result, output, cached = analyze_video(
        "dQw4w9WgXcQ",
        settings=settings,
        output_dir=tmp_path / "out",
        no_llm=True,
        transcript_provider=FakeProvider(),
        nlp=FakeNLP(),
    )
    assert not cached
    assert result.study_words == []
    assert result.all_words
    assert (output / "analysis.json").exists()


def test_no_subtitles_has_clear_error(tmp_path: Path) -> None:
    settings = Settings(model="test", api_key=None, database_path=tmp_path / "test.db")
    with pytest.raises(NoEnglishTranscriptError, match="不会运行 ASR"):
        analyze_video(
            "dQw4w9WgXcQ",
            settings=settings,
            output_dir=tmp_path,
            no_llm=True,
            transcript_provider=EmptyProvider(),
            nlp=FakeNLP(),
        )
