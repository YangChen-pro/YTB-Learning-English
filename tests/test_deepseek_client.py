from types import SimpleNamespace
from typing import Any

import pytest

from youtube_vocab.errors import LLMError
from youtube_vocab.llm.client import DeepSeekClient
from youtube_vocab.models import ChunkAnalysis


class FakeCompletions:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        message = SimpleNamespace(content=self.content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_deepseek_json_output_is_pydantic_validated() -> None:
    completions = FakeCompletions(ChunkAnalysis().model_dump_json())
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    client = DeepSeekClient(
        api_key="test",
        model="deepseek-v4-flash",
        client=fake_client,
    )

    result = client.analyze("Return JSON.", "Analyze this chunk.")

    assert result == ChunkAnalysis()
    request = completions.calls[0]
    assert request["model"] == "deepseek-v4-flash"
    assert request["response_format"] == {"type": "json_object"}
    assert request["extra_body"] == {"thinking": {"type": "disabled"}}


def test_deepseek_api_key_is_required() -> None:
    with pytest.raises(LLMError, match="DEEPSEEK_API_KEY"):
        DeepSeekClient(api_key="", model="deepseek-v4-flash")
