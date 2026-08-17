from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

logger = structlog.get_logger()


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> LLMResponse: ...

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AsyncIterator[str]: ...


class OpenAILLM(LLMProvider):
    def __init__(self, model: str = "gpt-4o"):
        from openai import AsyncOpenAI

        settings = get_settings()
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = model

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> LLMResponse:
        import time

        start = time.perf_counter()
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        elapsed = (time.perf_counter() - start) * 1000

        usage = response.usage
        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            latency_ms=elapsed,
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicLLM(LLMProvider):
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        from anthropic import AsyncAnthropic

        settings = get_settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = model

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> LLMResponse:
        import time

        system_msg = ""
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        start = time.perf_counter()
        response = await self._client.messages.create(
            model=self._model,
            system=system_msg if system_msg else "You are a helpful assistant.",
            messages=chat_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        elapsed = (time.perf_counter() - start) * 1000

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        return LLMResponse(
            content=content,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            latency_ms=elapsed,
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        system_msg = ""
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        async with self._client.messages.stream(
            model=self._model,
            system=system_msg if system_msg else "You are a helpful assistant.",
            messages=chat_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ) as stream:
            async for text in stream.text_stream:
                yield text


class GoogleLLM(LLMProvider):
    def __init__(self, model: str = "gemini-2.5-flash", api_key: str | None = None):
        from google import genai

        settings = get_settings()
        self._genclient = genai.Client(api_key=api_key or settings.google_api_key)
        self._model = model

    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def model_name(self) -> str:
        return self._model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> LLMResponse:
        import time
        from google.genai import types

        system_instruction = None
        contents = []
        for m in messages:
            if m.role == "system":
                system_instruction = m.content
            else:
                role = "user" if m.role == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part(text=m.content)]))

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
        )

        start = time.perf_counter()
        response = await self._genclient.aio.models.generate_content(
            model=self._model,
            contents=contents,
            config=config,
        )
        elapsed = (time.perf_counter() - start) * 1000

        content = response.text or ""
        usage_meta = response.usage_metadata
        return LLMResponse(
            content=content,
            model=self._model,
            input_tokens=usage_meta.prompt_token_count if usage_meta else 0,
            output_tokens=usage_meta.candidates_token_count if usage_meta else 0,
            total_tokens=usage_meta.total_token_count if usage_meta else 0,
            latency_ms=elapsed,
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        from google.genai import types

        system_instruction = None
        contents = []
        for m in messages:
            if m.role == "system":
                system_instruction = m.content
            else:
                role = "user" if m.role == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part(text=m.content)]))

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
        )

        async for chunk in await self._genclient.aio.models.generate_content_stream(
            model=self._model,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield chunk.text


PROVIDER_MAP: dict[str, type[LLMProvider]] = {
    "openai": OpenAILLM,
    "anthropic": AnthropicLLM,
    "google": GoogleLLM,
}

PROVIDER_DEFAULTS: dict[str, str] = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-20250514",
    "google": "gemini-2.5-flash",
}


def get_llm_provider(
    provider: str = "openai",
    model: str | None = None,
    api_key: str | None = None,
) -> LLMProvider:
    settings = get_settings()

    if provider == "openai" and not settings.openai_api_key:
        if settings.google_api_key or api_key:
            logger.warning("No OPENAI_API_KEY, falling back to Google Gemini for LLM")
            provider = "google"
            model = None
        elif settings.anthropic_api_key:
            logger.warning("No OPENAI_API_KEY, falling back to Anthropic for LLM")
            provider = "anthropic"
            model = None

    cls = PROVIDER_MAP.get(provider)
    if not cls:
        raise ValueError(f"Unknown LLM provider: {provider}. Options: {list(PROVIDER_MAP)}")

    model = model or PROVIDER_DEFAULTS.get(provider, "")
    if provider == "google" and api_key:
        return cls(model=model, api_key=api_key)
    return cls(model=model)
