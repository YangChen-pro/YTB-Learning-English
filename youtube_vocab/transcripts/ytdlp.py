"""Optional yt-dlp subtitle-only fallback backend."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from youtube_vocab.errors import NoEnglishTranscriptError, TranscriptError
from youtube_vocab.models import RawCaption, TranscriptDocument, TranscriptTrack
from youtube_vocab.transcripts.youtube_api import ENGLISH_PRIORITY


class YtDlpTranscriptProvider:
    """Use yt-dlp to download JSON3 captions, never video or audio."""

    def fetch(self, video_id: str, language: str = "en") -> TranscriptDocument:
        executable = shutil.which("yt-dlp")
        if executable is None:
            raise TranscriptError(
                "youtube-transcript-api 获取失败，且备用后端 yt-dlp 未安装。"
                "请运行 `uv sync --extra ytdlp`。"
            )
        languages = [language] if language != "en" else list(ENGLISH_PRIORITY)
        with tempfile.TemporaryDirectory(prefix="ytvocab-") as directory:
            template = str(Path(directory) / "captions.%(ext)s")
            common = [
                executable,
                "--skip-download",
                "--sub-format",
                "json3",
                "--sub-langs",
                ",".join(languages),
                "--output",
                template,
                f"https://www.youtube.com/watch?v={video_id}",
            ]
            # Run distinct passes so manual captions retain strict priority and the
            # generated flag remains reliable.
            completed = subprocess.run(
                [common[0], "--write-subs", *common[1:]],
                capture_output=True,
                text=True,
                check=False,
            )
            files = sorted(Path(directory).glob("*.json3"))
            is_generated = False
            if not files:
                completed = subprocess.run(
                    [common[0], "--write-auto-subs", *common[1:]],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                files = sorted(Path(directory).glob("*.json3"))
                is_generated = True
            if completed.returncode != 0 and not files:
                raise TranscriptError(f"yt-dlp 字幕获取失败：{completed.stderr.strip()}")
            if not files:
                raise NoEnglishTranscriptError(
                    "没有可用的英文字幕；当前版本不会下载音频或运行 ASR。"
                )
            path = files[0]
            payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            captions: list[RawCaption] = []
            for event in payload.get("events", []):
                segments = event.get("segs") or []
                text = "".join(str(segment.get("utf8", "")) for segment in segments).strip()
                if text:
                    captions.append(
                        RawCaption(
                            id=len(captions),
                            start=float(event.get("tStartMs", 0)) / 1000,
                            duration=float(event.get("dDurationMs", 0)) / 1000,
                            text=text,
                        )
                    )
            language_code = _language_from_filename(path.name, languages)
            track = TranscriptTrack(
                language_code=language_code,
                language=language_code,
                is_generated=is_generated,
            )
            return TranscriptDocument(
                video_id=video_id,
                selected_track=track,
                available_tracks=[track],
                captions=captions,
            )

    def inspect(self, video_id: str, language: str = "en") -> TranscriptDocument:
        return self.fetch(video_id, language)


def _language_from_filename(filename: str, languages: list[str]) -> str:
    for language in languages:
        if f".{language}." in filename:
            return language
    return languages[0]
