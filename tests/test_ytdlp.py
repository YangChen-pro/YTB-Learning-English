import subprocess
import sys
from pathlib import Path

import pytest

from youtube_vocab.transcripts.ytdlp import (
    YtDlpTranscriptProvider,
    _parse_caption_file,
    _select_caption_file,
)


def test_ytdlp_uses_current_python_and_browser_options(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        (tmp_path / "captions.en.vtt").write_text(
            "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello\n",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    provider = YtDlpTranscriptProvider(
        cookies_browser="edge",
        js_runtime="node:/opt/homebrew/bin/node",
        remote_components="ejs:github",
    )

    path, generated = provider._download(tmp_path, "dQw4w9WgXcQ", ["en", "en-US"])

    assert path.name == "captions.en.vtt"
    assert not generated
    assert calls[0][:4] == [sys.executable, "-m", "yt_dlp", "--write-subs"]
    assert _option_value(calls[0], "--sub-format") == "json3/vtt"
    assert _option_value(calls[0], "--cookies-from-browser") == "edge"
    assert _option_value(calls[0], "--js-runtimes") == "node:/opt/homebrew/bin/node"
    assert _option_value(calls[0], "--remote-components") == "ejs:github"


def test_select_caption_file_respects_language_priority(tmp_path: Path) -> None:
    british = tmp_path / "captions.en-GB.vtt"
    generic = tmp_path / "captions.en.json3"

    assert _select_caption_file([british, generic], ["en", "en-GB"]) == generic


def test_parse_json3_caption_file(tmp_path: Path) -> None:
    path = tmp_path / "captions.en.json3"
    path.write_text(
        '{"events":[{"tStartMs":1500,"dDurationMs":800,'
        '"segs":[{"utf8":"Hello "},{"utf8":"world"}]}]}',
        encoding="utf-8",
    )

    captions = _parse_caption_file(path)

    assert len(captions) == 1
    assert captions[0].start == 1.5
    assert captions[0].duration == 0.8
    assert captions[0].text == "Hello world"


def _option_value(command: list[str], name: str) -> str:
    return command[command.index(name) + 1]
