from pathlib import Path

from youtube_vocab.models import VocabularyItem
from youtube_vocab.nlp.vocabulary import filter_known_words
from youtube_vocab.storage.database import Database
from youtube_vocab.storage.known_words import KnownWordsRepository


def test_known_words_are_keyed_and_filtered_by_lemma_and_pos(tmp_path: Path) -> None:
    repository = KnownWordsRepository(Database(tmp_path / "test.db"))
    repository.add("record", "NOUN")
    items = [
        VocabularyItem(
            lemma="record",
            pos="NOUN",
            surface_forms=["record"],
            count=1,
            first_timestamp=0,
            occurrences=[],
        ),
        VocabularyItem(
            lemma="record",
            pos="VERB",
            surface_forms=["record"],
            count=1,
            first_timestamp=0,
            occurrences=[],
        ),
    ]
    filtered = filter_known_words(items, repository.filtering_keys())
    assert [(item.lemma, item.pos) for item in filtered] == [("record", "VERB")]
