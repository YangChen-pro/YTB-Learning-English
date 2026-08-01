"""Transcript provider protocol."""

from typing import Protocol

from youtube_vocab.models import TranscriptDocument


class TranscriptProvider(Protocol):
    def fetch(self, video_id: str, language: str = "en") -> TranscriptDocument: ...

    def inspect(self, video_id: str, language: str = "en") -> TranscriptDocument: ...
