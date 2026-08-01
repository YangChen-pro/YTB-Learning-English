"""Pydantic boundary models shared by the application."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class RawCaption(BaseModel):
    id: int
    start: float
    duration: float
    text: str


class NormalizedSentence(BaseModel):
    id: int
    text: str
    start: float
    end: float
    source_caption_ids: list[int]


class TranscriptTrack(BaseModel):
    language_code: str
    language: str
    is_generated: bool
    is_translatable: bool = False


class TranscriptDocument(BaseModel):
    video_id: str
    selected_track: TranscriptTrack
    available_tracks: list[TranscriptTrack]
    captions: list[RawCaption]


class VocabularyOccurrence(BaseModel):
    surface: str
    lemma: str
    pos: str
    sentence_id: int
    sentence: str
    timestamp: float


class VocabularyItem(BaseModel):
    lemma: str
    pos: str
    surface_forms: list[str]
    count: int
    first_timestamp: float
    occurrences: list[VocabularyOccurrence]
    is_stop: bool = False
    is_proper_noun: bool = False


ExpressionCategory = Literal[
    "phrasal_verb",
    "collocation",
    "idiom",
    "sentence_frame",
    "discourse_marker",
    "prepositional_phrase",
    "domain_expression",
]


class SubtitleCorrection(BaseModel):
    original: str
    suggested: str
    confidence: float = Field(ge=0, le=1)
    reason: str


class LearningWord(BaseModel):
    surface: str
    lemma: str
    pos: str
    meaning_zh: str
    explanation_zh: str
    evidence: str
    timestamp: float
    difficulty: int = Field(ge=1, le=5)
    usefulness: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0, le=1)


class ExpressionItem(BaseModel):
    expression: str
    canonical_form: str
    category: ExpressionCategory
    meaning_zh: str
    explanation_zh: str
    evidence: str
    timestamp: float
    usefulness: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0, le=1)


class ChunkAnalysis(BaseModel):
    vocabulary: list[LearningWord] = Field(default_factory=list)
    expressions: list[ExpressionItem] = Field(default_factory=list)
    corrections: list[SubtitleCorrection] = Field(default_factory=list)


class ContextChunk(BaseModel):
    id: int
    sentences: list[NormalizedSentence]
    candidates: list[VocabularyItem]
    known_words: list[tuple[str, str]] = Field(default_factory=list)

    @property
    def start(self) -> float:
        return self.sentences[0].start

    @property
    def end(self) -> float:
        return self.sentences[-1].end

    @property
    def text(self) -> str:
        return " ".join(sentence.text for sentence in self.sentences)


class AnalysisResult(BaseModel):
    video_id: str
    language_code: str
    is_generated: bool
    model: str | None
    prompt_version: str | None
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    raw_captions: list[RawCaption]
    sentences: list[NormalizedSentence]
    all_words: list[VocabularyItem]
    study_words: list[LearningWord]
    expressions: list[ExpressionItem]
    corrections: list[SubtitleCorrection]
    warnings: list[str] = Field(default_factory=list)
