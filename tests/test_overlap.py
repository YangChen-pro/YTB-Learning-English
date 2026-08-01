import pytest

from youtube_vocab.nlp.overlap import merge_overlapping_text


@pytest.mark.parametrize(
    ("previous", "following", "expected"),
    [
        ("the problem is that", "the problem is that", "the problem is that"),
        ("the problem is that", "the problem is that cache", "the problem is that cache"),
        (
            "the problem is cache invalidation",
            "cache invalidation is hard",
            "the problem is cache invalidation is hard",
        ),
        ("hello there", "general kenobi", "hello there general kenobi"),
        ("Cache invalidation", "cache, invalidation is hard", "Cache invalidation is hard"),
    ],
)
def test_merge_overlapping_text(previous: str, following: str, expected: str) -> None:
    assert merge_overlapping_text(previous, following)[0] == expected
