"""Minimal WebVTT caption parser for yt-dlp subtitle output."""

from __future__ import annotations

import re

from youtube_vocab.models import RawCaption

TIMING_RE = re.compile(
    r"^(?P<start>(?:\d{2}:)?\d{2}:\d{2}\.\d{3})\s+-->\s+"
    r"(?P<end>(?:\d{2}:)?\d{2}:\d{2}\.\d{3})(?:\s+.*)?$"
)


def _seconds(value: str) -> float:
    parts = value.split(":")
    hours = int(parts[0]) if len(parts) == 3 else 0
    minutes = int(parts[-2])
    return hours * 3600 + minutes * 60 + float(parts[-1])


def parse_vtt_captions(text: str) -> list[RawCaption]:
    """Convert WebVTT cues into timestamped raw captions."""
    captions: list[RawCaption] = []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    for block in re.split(r"\n{2,}", normalized.lstrip("\ufeff")):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing_index, timing = _find_timing(lines)
        if timing is None:
            continue
        caption_text = " ".join(lines[timing_index + 1 :]).strip()
        if not caption_text:
            continue
        start = _seconds(timing.group("start"))
        end = _seconds(timing.group("end"))
        captions.append(
            RawCaption(
                id=len(captions),
                start=start,
                duration=max(0.0, end - start),
                text=caption_text,
            )
        )
    return captions


def _find_timing(lines: list[str]) -> tuple[int, re.Match[str] | None]:
    for index, line in enumerate(lines):
        if match := TIMING_RE.match(line):
            return index, match
    return -1, None
