"""Provider-agnostic LLM client used by every agent in the pipeline.

Agents call `complete()` / `complete_structured()` against this interface
rather than an SDK directly, so the model/provider can change (or fall back
to a deterministic mock when no API key is configured) without touching
agent logic.
"""
import abc
import logging
from typing import Any

import anthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from backend.core.config import get_settings
from backend.core.exceptions import AgentExecutionError

logger = logging.getLogger(__name__)

_RETRYABLE_ANTHROPIC_ERRORS = (
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    anthropic.RateLimitError,
    anthropic.InternalServerError,
)


class LLMClient(abc.ABC):
    @abc.abstractmethod
    def complete(self, system: str, prompt: str, max_tokens: int = 4096) -> str:
        """Free-form text completion."""

    @abc.abstractmethod
    def complete_structured(
        self,
        system: str,
        prompt: str,
        schema: dict[str, Any],
        schema_name: str,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Completion constrained to the given JSON schema.

        Implemented via forced tool-use rather than "please respond with
        JSON" prompting — Claude's tool-calling is schema-validated by the
        API itself, which is far more reliable than parsing free-form text.
        """


class AnthropicClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(_RETRYABLE_ANTHROPIC_ERRORS),
    )
    def _create(self, **kwargs: Any) -> anthropic.types.Message:
        try:
            return self._client.messages.create(**kwargs)
        except anthropic.APIStatusError as exc:
            raise AgentExecutionError(f"LLM request failed: {exc}") from exc

    def complete(self, system: str, prompt: str, max_tokens: int = 4096) -> str:
        response = self._create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")

    def complete_structured(
        self,
        system: str,
        prompt: str,
        schema: dict[str, Any],
        schema_name: str,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        tool = {
            "name": schema_name,
            "description": f"Submit the result as {schema_name}.",
            "input_schema": schema,
        }
        response = self._create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            tools=[tool],
            tool_choice={"type": "tool", "name": schema_name},
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == schema_name:
                return block.input
        raise AgentExecutionError(f"Model did not return a structured {schema_name} response")


class MockClient(LLMClient):
    """Deterministic offline stand-in used when no API key is configured.

    Lets the rest of the pipeline (routes, orchestration, tests) run
    end-to-end without live model credentials — it returns schema-shaped
    but empty/placeholder data rather than raising.
    """

    def complete(self, system: str, prompt: str, max_tokens: int = 4096) -> str:
        return "[mock response — set ANTHROPIC_API_KEY for real completions]"

    def complete_structured(
        self,
        system: str,
        prompt: str,
        schema: dict[str, Any],
        schema_name: str,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        return _mock_value_for_schema(schema)


def _mock_value_for_schema(schema: dict[str, Any]) -> Any:
    schema_type = schema.get("type", "object")
    if schema_type == "object":
        return {
            key: _mock_value_for_schema(sub_schema)
            for key, sub_schema in schema.get("properties", {}).items()
        }
    if schema_type == "array":
        return []
    if schema_type == "string":
        return schema.get("default", "")
    if schema_type in ("integer", "number"):
        return schema.get("default", 0)
    if schema_type == "boolean":
        return schema.get("default", False)
    return None


_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is not None:
        return _client

    settings = get_settings()
    if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
        _client = AnthropicClient(settings.anthropic_api_key, settings.anthropic_model)
    elif settings.llm_provider == "openai":
        raise NotImplementedError(
            "The OpenAI provider is a documented extension point (implement an "
            "LLMClient subclass in this module) but isn't wired up yet — set "
            "LLM_PROVIDER=anthropic or LLM_PROVIDER=mock."
        )
    else:
        if settings.llm_provider == "anthropic":
            logger.warning("ANTHROPIC_API_KEY not set — falling back to the mock LLM client")
        _client = MockClient()
    return _client
