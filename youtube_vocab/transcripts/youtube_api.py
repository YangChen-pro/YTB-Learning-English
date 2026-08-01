"""youtube-transcript-api adapter and YouTube ID parsing."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from youtube_vocab.errors import InvalidVideoURLError, NoEnglishTranscriptError, TranscriptError
from youtube_vocab.models import RawCaption, TranscriptDocument, TranscriptTrack

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
ENGLISH_PRIORITY = ("en", "en-US", "en-GB", "en-CA", "en-AU")


def parse_video_id(value: str) -> str:
    """Parse common YouTube URLs or a bare 11-character video ID."""
    candidate = value.strip()
    if VIDEO_ID_RE.fullmatch(candidate):
        return candidate
    parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
    host = (parsed.hostname or "").lower()
    video_id: str | None = None
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        else:
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live"}:
                video_id = parts[1]
    elif host in {"youtu.be", "www.youtu.be"}:
        parts = [part for part in parsed.path.split("/") if part]
        video_id = parts[0] if parts else None
    if video_id and VIDEO_ID_RE.fullmatch(video_id):
        return video_id
    raise InvalidVideoURLError(f"无法解析 YouTube 视频 URL 或 ID：{value!r}")


def _track_model(track: Any) -> TranscriptTrack:
    return TranscriptTrack(
        language_code=str(track.language_code),
        language=str(track.language),
        is_generated=bool(track.is_generated),
        is_translatable=bool(getattr(track, "is_translatable", False)),
    )


def _choose_track(tracks: Iterable[Any], language: str) -> Any:
    track_list = list(tracks)
    requested = [language] if language != "en" else list(ENGLISH_PRIORITY)
    for generated in (False, True):
        for code in requested:
            for track in track_list:
                if str(track.language_code) == code and bool(track.is_generated) is generated:
                    return track
    raise NoEnglishTranscriptError(
        "没有可用的英文字幕（已检查人工字幕和 YouTube 自动字幕）。"
        "当前版本不会下载音频，也不会运行 Whisper/ASR。"
    )


class YouTubeTranscriptProvider:
    """Fetch captions without downloading video or audio."""

    def __init__(self, api: YouTubeTranscriptApi | None = None) -> None:
        self.api = api or YouTubeTranscriptApi()

    def _list(self, video_id: str) -> list[object]:
        try:
            return list(self.api.list(video_id))
        except TranscriptsDisabled as exc:
            raise TranscriptError("该视频已禁用字幕；当前版本不执行音频转录。") from exc
        except VideoUnavailable as exc:
            raise TranscriptError("视频不存在、不可访问或受地区/年龄限制。") from exc
        except NoTranscriptFound as exc:
            raise NoEnglishTranscriptError(
                "没有可用的英文字幕；当前版本不会下载音频或运行 ASR。"
            ) from exc
        except CouldNotRetrieveTranscript as exc:
            raise TranscriptError(f"YouTube 字幕请求失败或被限流：{exc}") from exc

    def inspect(self, video_id: str, language: str = "en") -> TranscriptDocument:
        tracks = self._list(video_id)
        chosen = _choose_track(tracks, language)
        return TranscriptDocument(
            video_id=video_id,
            selected_track=_track_model(chosen),
            available_tracks=[_track_model(track) for track in tracks],
            captions=[],
        )

    def fetch(self, video_id: str, language: str = "en") -> TranscriptDocument:
        document = self.inspect(video_id, language)
        tracks = self._list(video_id)
        chosen = _choose_track(tracks, language)
        try:
            fetched = chosen.fetch()
            document.captions = [
                RawCaption(
                    id=index,
                    start=float(item.start),
                    duration=float(item.duration),
                    text=str(item.text),
                )
                for index, item in enumerate(fetched)
            ]
        except CouldNotRetrieveTranscript as exc:
            raise TranscriptError(f"字幕下载失败或请求被限流：{exc}") from exc
        return document
