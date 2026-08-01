from youtube_vocab.llm.analyzer import validate_chunk_analysis
from youtube_vocab.models import (
    ChunkAnalysis,
    ContextChunk,
    LearningWord,
    NormalizedSentence,
    VocabularyItem,
)


def make_word(evidence: str, timestamp: float) -> LearningWord:
    return LearningWord(
        surface="entails",
        lemma="entail",
        pos="VERB",
        meaning_zh="意味着",
        explanation_zh="语境义",
        evidence=evidence,
        timestamp=timestamp,
        difficulty=4,
        usefulness=4,
        confidence=0.9,
    )


def make_chunk() -> ContextChunk:
    sentence = NormalizedSentence(
        id=0, text="This entails real work.", start=10, end=12, source_caption_ids=[0]
    )
    candidate = VocabularyItem(
        lemma="entail",
        pos="VERB",
        surface_forms=["entails"],
        count=1,
        first_timestamp=10,
        occurrences=[],
    )
    return ContextChunk(id=0, sentences=[sentence], candidates=[candidate])


def test_missing_evidence_is_rejected() -> None:
    warnings: list[str] = []
    result = validate_chunk_analysis(
        ChunkAnalysis(vocabulary=[make_word("invented text", 10)]),
        make_chunk(),
        min_usefulness=3,
        min_confidence=0.75,
        warn=warnings.append,
    )
    assert result.vocabulary == []
    assert "evidence" in warnings[0]


def test_out_of_range_timestamp_is_rejected() -> None:
    warnings: list[str] = []
    result = validate_chunk_analysis(
        ChunkAnalysis(vocabulary=[make_word("This entails real work.", 99)]),
        make_chunk(),
        min_usefulness=3,
        min_confidence=0.75,
        warn=warnings.append,
    )
    assert result.vocabulary == []
    assert "timestamp" in warnings[0]
