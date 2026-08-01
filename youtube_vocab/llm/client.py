"""DeepSeek Chat Completions adapter with JSON Output and Pydantic validation."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from youtube_vocab.errors import LLMError
from youtube_vocab.models import ChunkAnalysis


class DeepSeekClient:
    """Call DeepSeek through its official OpenAI-compatible endpoint.

    DeepSeek JSON Output guarantees JSON syntax; Pydantic then enforces the complete
    application schema before any result reaches grounding validation.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://api.deepseek.com",
        client: Any | None = None,
    ) -> None:
        if not api_key:
            raise LLMError("缺少 DEEPSEEK_API_KEY。可配置密钥，或使用 --no-llm。")
        self.model = model
        self.client = client or OpenAI(api_key=api_key, base_url=base_url)

    def analyze(self, system_prompt: str, user_prompt: str) -> ChunkAnalysis:
        schema = json.dumps(ChunkAnalysis.model_json_schema(), ensure_ascii=False)
        structured_prompt = (
            f"{user_prompt}\n\n"
            f"Return one JSON object conforming exactly to this JSON Schema:\n{schema}"
        )
        last_error: Exception | None = None
        for _attempt in range(2):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": structured_prompt},
                    ],
                    response_format={"type": "json_object"},
                    extra_body={"thinking": {"type": "disabled"}},
                    max_tokens=8192,
                )
                content = response.choices[0].message.content
                if not content:
                    raise LLMError("DeepSeek JSON Output 返回了空内容。")
                return ChunkAnalysis.model_validate_json(content)
            except (OpenAIError, ValidationError, LLMError) as exc:
                last_error = exc
        raise LLMError(f"DeepSeek 请求或 Pydantic 结构化输出校验失败：{last_error}")
