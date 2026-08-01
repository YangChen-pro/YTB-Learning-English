from youtube_vocab.llm.analyzer import deduplicate_expressions
from youtube_vocab.models import ExpressionItem


def expression(canonical: str, confidence: float, usefulness: int = 4) -> ExpressionItem:
    return ExpressionItem(
        expression=canonical,
        canonical_form=canonical,
        category="collocation",
        meaning_zh="含义",
        explanation_zh="解释",
        evidence=f"we use {canonical} here",
        timestamp=1,
        usefulness=usefulness,
        confidence=confidence,
    )


def test_expression_normalization_and_quality_deduplication() -> None:
    result = deduplicate_expressions(
        [expression("in terms of!", 0.8), expression(" In   Terms Of ", 0.95)]
    )
    assert len(result) == 1
    assert result[0].confidence == 0.95
