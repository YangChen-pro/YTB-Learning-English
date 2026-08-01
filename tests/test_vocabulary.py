from conftest import FakeNLP

from youtube_vocab.models import NormalizedSentence
from youtube_vocab.nlp.vocabulary import extract_vocabulary


def sentence(text: str, identifier: int = 0) -> NormalizedSentence:
    return NormalizedSentence(
        id=identifier,
        text=text,
        start=float(identifier),
        end=identifier + 1,
        source_caption_ids=[identifier],
    )


def test_inflections_merge_by_lemma_and_pos() -> None:
    items = extract_vocabulary([sentence("take takes took taken")], FakeNLP())
    assert len(items) == 1
    assert items[0].lemma == "take"
    assert items[0].pos == "VERB"
    assert items[0].count == 4
    assert items[0].surface_forms == ["take", "takes", "took", "taken"]


def test_same_lemma_different_pos_does_not_merge() -> None:
    items = extract_vocabulary([sentence("record_n record_v")], FakeNLP())
    assert {(item.lemma, item.pos) for item in items} == {("record", "NOUN"), ("record", "VERB")}
