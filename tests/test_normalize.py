from youtube_vocab.models import RawCaption
from youtube_vocab.transcripts.normalize import normalize_captions


def test_rolling_captions_keep_provenance_and_time() -> None:
    captions = [
        RawCaption(id=0, start=0, duration=1, text="the problem is that"),
        RawCaption(id=1, start=0.8, duration=1, text="the problem is that cache"),
        RawCaption(id=2, start=1.6, duration=1, text="the problem is that cache invalidation."),
        RawCaption(id=3, start=2.5, duration=1, text="It is hard."),
    ]
    sentences = normalize_captions(captions)
    assert sentences[0].text == "the problem is that cache invalidation."
    assert sentences[0].source_caption_ids == [0, 1, 2]
    assert sentences[0].start == 0
    assert sentences[-1].end == 3.5


def test_long_pause_splits_without_punctuation() -> None:
    captions = [
        RawCaption(id=0, start=0, duration=1, text="first thought"),
        RawCaption(id=1, start=4, duration=1, text="second thought"),
    ]
    assert [item.text for item in normalize_captions(captions)] == [
        "first thought",
        "second thought",
    ]
