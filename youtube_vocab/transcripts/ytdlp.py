"""Optional yt-dlp subtitle-only fallback backend."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from youtube_vocab.errors import NoEnglishTranscriptError, TranscriptError
from youtube_vocab.models import RawCaption, TranscriptDocument, TranscriptTrack
from youtube_vocab.transcripts.vtt import parse_vtt_captions
from youtube_vocab.transcripts.youtube_api import ENGLISH_PRIORITY


class YtDlpTranscriptProvider:
    """Use the current Python environment's yt-dlp to download captions only."""

    def __init__(
        self,
        *,
        cookies_browser: str | None = None,
        js_runtime: str | None = None,
        remote_components: str | None = None,
    ) -> None:
        self.cookies_browser = cookies_browser
        self.js_runtime = js_runtime
        self.remote_components = remote_components

    def fetch(self, video_id: str, language: str = "en") -> TranscriptDocument:
        if importlib.util.find_spec("yt_dlp") is None:
            raise TranscriptError(
                "youtube-transcript-api 获取失败，且备用后端 yt-dlp 未安装。"
                "请运行 `uv sync --extra ytdlp`。"
            )
        languages = [language] if language != "en" else list(ENGLISH_PRIORITY)
        with tempfile.TemporaryDirectory(prefix="ytvocab-") as directory:
            path, is_generated = self._download(Path(directory), video_id, languages)
            captions = _parse_caption_file(path)
            track = TranscriptTrack(
                language_code=_language_from_filename(path.name, languages),
                language=_language_from_filename(path.name, languages),
                is_generated=is_generated,
            )
            return TranscriptDocument(
                video_id=video_id,
                selected_track=track,
                available_tracks=[track],
                captions=captions,
            )

    def _download(
        self, directory: Path, video_id: str, languages: list[str]
    ) -> tuple[Path, bool]:
        options = self._options(directory, video_id, languages)
        last_result: subprocess.CompletedProcess[str] | None = None
        for flag, is_generated in (("--write-subs", False), ("--write-auto-subs", True)):
            try:
                last_result = subprocess.run(
                    [sys.executable, "-m", "yt_dlp", flag, *options],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=120,
                )
            except subprocess.TimeoutExpired as exc:
                raise TranscriptError("yt-dlp 字幕获取超时。") from exc
            if path := _select_caption_file(_caption_files(directory), languages):
                return path, is_generated
        if last_result is not None and last_result.returncode != 0:
            raise TranscriptError(f"yt-dlp 字幕获取失败：{last_result.stderr.strip()}")
        raise NoEnglishTranscriptError(
            "没有可用的英文字幕；当前版本不会下载音频或运行 ASR。"
        )

    def _options(self, directory: Path, video_id: str, languages: list[str]) -> list[str]:
        options = [
            "--skip-download",
            "--sub-format",
            "json3/vtt",
            "--sub-langs",
            ",".join(languages),
            "--output",
            str(directory / "captions.%(ext)s"),
        ]
        if self.cookies_browser:
            options.extend(["--cookies-from-browser", self.cookies_browser])
        if self.js_runtime:
            options.extend(["--js-runtimes", self.js_runtime])
        if self.remote_components:
            options.extend(["--remote-components", self.remote_components])
        options.append(f"https://www.youtube.com/watch?v={video_id}")
        return options

    def inspect(self, video_id: str, language: str = "en") -> TranscriptDocument:
        return self.fetch(video_id, language)


def _caption_files(directory: Path) -> list[Path]:
    return sorted([*directory.glob("*.json3"), *directory.glob("*.vtt")])


def _select_caption_file(files: list[Path], languages: list[str]) -> Path | None:
    for language in languages:
        if path := next((item for item in files if f".{language}." in item.name), None):
            return path
    return files[0] if files else None


def _parse_caption_file(path: Path) -> list[RawCaption]:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix == ".vtt":
        return parse_vtt_captions(text)
    try:
        payload: dict[str, Any] = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TranscriptError(f"yt-dlp 字幕 JSON 解析失败：{path.name}") from exc
    captions: list[RawCaption] = []
    for event in payload.get("events", []):
        segments = event.get("segs") or []
        caption_text = "".join(str(segment.get("utf8", "")) for segment in segments).strip()
        if caption_text:
            captions.append(
                RawCaption(
                    id=len(captions),
                    start=float(event.get("tStartMs", 0)) / 1000,
                    duration=float(event.get("dDurationMs", 0)) / 1000,
                    text=caption_text,
                )
            )
    return captions


def _language_from_filename(filename: str, languages: list[str]) -> str:
    for language in languages:
        if f".{language}." in filename:
            return language
    return languages[0]
