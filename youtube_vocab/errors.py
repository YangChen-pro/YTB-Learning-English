"""User-facing application exceptions."""


class YTVocabError(Exception):
    """Base class for errors that the CLI can present without a traceback."""


class InvalidVideoURLError(YTVocabError):
    """The supplied YouTube URL or ID cannot be parsed."""


class TranscriptError(YTVocabError):
    """Captions could not be retrieved."""


class NoEnglishTranscriptError(TranscriptError):
    """No supported English caption track exists."""


class NLPModelError(YTVocabError):
    """The configured spaCy model is unavailable."""


class LLMError(YTVocabError):
    """The DeepSeek request failed or returned unusable data."""
