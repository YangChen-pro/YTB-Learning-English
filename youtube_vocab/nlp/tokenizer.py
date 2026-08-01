"""spaCy loading with a clear installation error."""

from __future__ import annotations

from typing import Any

import spacy

from youtube_vocab.errors import NLPModelError


def load_english_model(name: str = "en_core_web_sm") -> Any:
    try:
        return spacy.load(name)
    except OSError as exc:
        raise NLPModelError(
            f"spaCy 模型 {name!r} 未安装。请运行：uv run python -m spacy download {name}"
        ) from exc
