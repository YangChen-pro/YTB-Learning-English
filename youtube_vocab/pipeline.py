"""End-to-end analysis orchestration."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from youtube_vocab.config import Settings
from youtube_vocab.errors import NoEnglishTranscriptError, TranscriptError
from youtube_vocab.export.json_export import export_result
from youtube_vocab.llm.analyzer import analyze_chunks
from youtube_vocab.llm.client import DeepSeekClient
from youtube_vocab.llm.prompts import PROMPT_VERSION
from youtube_vocab.models import AnalysisResult, TranscriptDocument
from youtube_vocab.nlp.tokenizer import load_english_model
from youtube_vocab.nlp.vocabulary import extract_vocabulary, filter_known_words
from youtube_vocab.storage.database import Database
from youtube_vocab.storage.known_words import KnownWordsRepository
from youtube_vocab.transcripts.normalize import make_context_chunks, normalize_captions
from youtube_vocab.transcripts.youtube_api import YouTubeTranscriptProvider, parse_video_id
from youtube_vocab.transcripts.ytdlp import YtDlpTranscriptProvider

Progress = Callable[[str], None]


def analyze_video(
    video_url: str,
    *,
    settings: Settings,
    output_dir: Path,
    language: str = "en",
    min_usefulness: int = 3,
    min_confidence: float = 0.75,
    include_proper_nouns: bool = False,
    no_llm: bool = False,
    force: bool = False,
    progress: Progress = lambda _: None,
    transcript_provider: Any | None = None,
    nlp: Any | None = None,
    llm_client: Any | None = None,
) -> tuple[AnalysisResult, Path, bool]:
    video_id = parse_video_id(video_url)
    database = Database(settings.database_path)
    if not force:
        cached = database.latest_result(video_id)
        if cached is not None:
            progress("复用数据库中的最近分析结果")
            return cached, export_result(cached, output_dir), True

    progress("获取英文字幕")
    provider = transcript_provider or YouTubeTranscriptProvider()
    try:
        transcript: TranscriptDocument = provider.fetch(video_id, language)
    except NoEnglishTranscriptError:
        raise
    except TranscriptError as primary_error:
        if transcript_provider is not None:
            raise
        progress("主字幕后端失败，尝试 yt-dlp 字幕后端")
        try:
            transcript = YtDlpTranscriptProvider().fetch(video_id, language)
        except TranscriptError as fallback_error:
            raise TranscriptError(
                f"{primary_error}\n备用字幕后端也失败：{fallback_error}"
            ) from fallback_error

    progress("清洗滚动字幕并恢复句子")
    sentences = normalize_captions(transcript.captions)
    progress("执行本地 tokenization、lemmatization 与 POS 标注")
    language_model = nlp or load_english_model(settings.spacy_model)
    all_words = extract_vocabulary(
        sentences, language_model, include_proper_nouns=include_proper_nouns
    )
    known_repository = KnownWordsRepository(database)
    known_keys = known_repository.filtering_keys()
    candidates = filter_known_words(all_words, known_keys)
    candidate_keys = {(item.lemma, item.pos) for item in candidates}
    known_vocabulary = [item for item in all_words if (item.lemma, item.pos) not in candidate_keys]

    warnings: list[str] = []
    study_words = []
    expressions = []
    corrections = []
    model: str | None = None
    prompt_version: str | None = None
    if not no_llm:
        progress("使用 LLM 评估学习价值和固定表达")
        client = llm_client or DeepSeekClient(
            api_key=settings.api_key or "",
            model=settings.model,
            base_url=settings.base_url,
        )
        chunks = make_context_chunks(
            sentences,
            candidates,
            known_vocabulary=known_vocabulary,
        )
        analysis = analyze_chunks(
            chunks,
            client,
            min_usefulness=min_usefulness,
            min_confidence=min_confidence,
            warn=warnings.append,
        )
        study_words = analysis.vocabulary
        expressions = analysis.expressions
        corrections = analysis.corrections
        model = settings.model
        prompt_version = PROMPT_VERSION

    result = AnalysisResult(
        video_id=video_id,
        language_code=transcript.selected_track.language_code,
        is_generated=transcript.selected_track.is_generated,
        model=model,
        prompt_version=prompt_version,
        raw_captions=transcript.captions,
        sentences=sentences,
        all_words=all_words,
        study_words=study_words,
        expressions=expressions,
        corrections=corrections,
        warnings=warnings,
    )
    progress("保存分析历史并导出文件")
    database.save_result(result)
    destination = export_result(result, output_dir)
    return result, destination, False
