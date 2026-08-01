import pytest

from youtube_vocab.errors import InvalidVideoURLError
from youtube_vocab.transcripts.youtube_api import parse_video_id


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ?t=12", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ],
)
def test_parse_video_id(value: str, expected: str) -> None:
    assert parse_video_id(value) == expected


def test_invalid_video_id() -> None:
    with pytest.raises(InvalidVideoURLError, match="无法解析"):
        parse_video_id("not-a-valid-video-id")
