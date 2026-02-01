"""
LLM provider abstraction for multiple backends.
Supports Ollama (default), OpenAI, and AWS Bedrock.

Configuration is driven by environment variables:
    LLM_PROVIDER: ollama | openai | aws_bedrock
    LLM_DEFAULT_MODEL: Model name for the chosen provider
    LLM_TEMPERATURE: Default temperature (0.0-1.0)
    LLM_MAX_TOKENS: Default max tokens
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncIterator
from enum import Enum

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProviderType(str, Enum):
    """Supported LLM provider types."""
    OPENAI = "openai"
    OLLAMA = "ollama"
    AWS_BEDROCK = "aws_bedrock"


class LLMResponse:
    """Standardized LLM response."""

    def __init__(
        self,
        content: str,
        model: str,
        provider: str,
        usage: Optional[Dict[str, int]] = None,
        finish_reason: Optional[str] = None,
        raw_response: Optional[Dict] = None,
    ):
        self.content = content
        self.model = model
        self.provider = provider
        self.usage = usage or {}
        self.finish_reason = finish_reason
        self.raw_response = raw_response

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
        }


class LLMConfig:
    """
    Configuration container for LLM settings.
    Can be overridden at platform or agent level.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        # Use provided values or fall back to global settings
        self.provider = provider or settings.LLM_PROVIDER
        self.model = model or settings.LLM_DEFAULT_MODEL
        self.temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        self.max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS
        self.timeout = timeout if timeout is not None else settings.LLM_TIMEOUT
        self.extra = kwargs

    @classmethod
    def from_settings(cls) -> "LLMConfig":
        """Create config from global settings."""
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
        }


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    Provides a unified interface for different LLM backends.
    """

    provider_name: str = "base"

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate a response from the LLM using a simple prompt."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Chat with the LLM using a list of messages."""
        pass

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream generation (default implementation yields full response)."""
        response = await self.generate(prompt, model, temperature, max_tokens, **kwargs)
        yield response.content

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream chat (default implementation yields full response)."""
        response = await self.chat(messages, model, temperature, max_tokens, **kwargs)
        yield response.content

    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy and accessible."""
        pass


class OllamaProvider(LLMProvider):
    """
    Ollama LLM provider for local models.

    Ollama runs locally and provides access to various open-source models
    like Llama, Mistral, CodeLlama, etc.
    """

    provider_name = "ollama"

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.default_model = default_model or settings.LLM_DEFAULT_MODEL
        self.timeout = timeout or settings.LLM_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        system: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate a response using Ollama's generate API."""
        client = await self._get_client()
        model = model or self.default_model
        temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            payload["system"] = system
        if stop:
            payload["options"]["stop"] = stop

        for key, value in kwargs.items():
            if key not in payload:
                payload["options"][key] = value

        try:
            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data.get("response", ""),
                model=model,
                provider=self.provider_name,
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                },
                finish_reason="stop" if data.get("done") else "length",
                raw_response=data,
            )
        except httpx.HTTPError as e:
            logger.error(f"Ollama generate error: {e}")
            raise RuntimeError(f"Ollama API error: {e}")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Chat with Ollama using the chat API."""
        client = await self._get_client()
        model = model or self.default_model
        temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

        ollama_messages = [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in messages
        ]

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if stop:
            payload["options"]["stop"] = stop

        for key, value in kwargs.items():
            if key not in payload:
                payload["options"][key] = value

        try:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

            message = data.get("message", {})
            return LLMResponse(
                content=message.get("content", ""),
                model=model,
                provider=self.provider_name,
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                },
                finish_reason="stop" if data.get("done") else "length",
                raw_response=data,
            )
        except httpx.HTTPError as e:
            logger.error(f"Ollama chat error: {e}")
            raise RuntimeError(f"Ollama API error: {e}")

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream generation from Ollama."""
        client = await self._get_client()
        model = model or self.default_model
        temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with client.stream("POST", "/api/generate", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import json
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done"):
                            break
        except httpx.HTTPError as e:
            logger.error(f"Ollama stream error: {e}")
            raise RuntimeError(f"Ollama API error: {e}")

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream chat from Ollama."""
        client = await self._get_client()
        model = model or self.default_model
        temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

        ollama_messages = [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in messages
        ]

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import json
                        data = json.loads(line)
                        message = data.get("message", {})
                        if "content" in message:
                            yield message["content"]
                        if data.get("done"):
                            break
        except httpx.HTTPError as e:
            logger.error(f"Ollama chat stream error: {e}")
            raise RuntimeError(f"Ollama API error: {e}")

    async def list_models(self) -> List[str]:
        """List available Ollama models."""
        client = await self._get_client()
        try:
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except httpx.HTTPError as e:
            logger.error(f"Ollama list models error: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if Ollama is running and accessible."""
        client = await self._get_client()
        try:
            response = await client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama library."""
        client = await self._get_client()
        try:
            response = await client.post(
                "/api/pull",
                json={"name": model, "stream": False},
                timeout=httpx.Timeout(600.0),
            )
            return response.status_code == 200
        except httpx.HTTPError as e:
            logger.error(f"Ollama pull model error: {e}")
            return False


class OpenAIProvider(LLMProvider):
    """
    OpenAI LLM provider.

    Supports GPT-4, GPT-3.5-turbo, and other OpenAI models.
    """

    provider_name = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip("/")
        self.default_model = default_model or settings.LLM_DEFAULT_MODEL
        self.timeout = timeout or settings.LLM_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None

        if not self.api_key:
            logger.warning("OpenAI API key not configured")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        system: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate using OpenAI's chat completions API."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        return await self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
            **kwargs,
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Chat with OpenAI using the chat completions API."""
        if not self.api_key:
            raise RuntimeError("OpenAI API key not configured")

        client = await self._get_client()
        model = model or self.default_model
        temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if stop:
            payload["stop"] = stop

        try:
            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            usage = data.get("usage", {})

            return LLMResponse(
                content=message.get("content", ""),
                model=model,
                provider=self.provider_name,
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                finish_reason=choice.get("finish_reason"),
                raw_response=data,
            )
        except httpx.HTTPError as e:
            logger.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"OpenAI API error: {e}")

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream generation from OpenAI."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async for chunk in self.chat_stream(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            yield chunk

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream chat from OpenAI."""
        if not self.api_key:
            raise RuntimeError("OpenAI API key not configured")

        client = await self._get_client()
        model = model or self.default_model
        temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            async with client.stream("POST", "/chat/completions", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        import json
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
        except httpx.HTTPError as e:
            logger.error(f"OpenAI stream error: {e}")
            raise RuntimeError(f"OpenAI API error: {e}")

    async def list_models(self) -> List[str]:
        """List available OpenAI models."""
        if not self.api_key:
            return []

        client = await self._get_client()
        try:
            response = await client.get("/models")
            response.raise_for_status()
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        except httpx.HTTPError as e:
            logger.error(f"OpenAI list models error: {e}")
            return ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        if not self.api_key:
            return False
        client = await self._get_client()
        try:
            response = await client.get("/models")
            return response.status_code == 200
        except Exception:
            return False


class AWSBedrockProvider(LLMProvider):
    """
    AWS Bedrock LLM provider.

    Supports Claude, Titan, and other models via AWS Bedrock.
    Requires boto3 and AWS credentials.
    """

    provider_name = "aws_bedrock"

    def __init__(
        self,
        region: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.region = region or settings.AWS_REGION
        self.default_model = default_model or settings.AWS_BEDROCK_MODEL
        self.timeout = timeout or settings.LLM_TIMEOUT
        self._client = None

    def _get_client(self):
        """Get or create the Bedrock client."""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    "bedrock-runtime",
                    region_name=self.region,
                )
            except ImportError:
                raise RuntimeError("boto3 is required for AWS Bedrock. Install with: pip install boto3")
            except Exception as e:
                raise RuntimeError(f"Failed to create Bedrock client: {e}")
        return self._client

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        system: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate using AWS Bedrock."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        return await self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
            **kwargs,
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Chat with AWS Bedrock."""
        import json
        import asyncio

        client = self._get_client()
        model = model or self.default_model
        temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

        # Format for Claude models on Bedrock
        if "anthropic" in model or "claude" in model.lower():
            # Extract system message if present
            system_prompt = None
            chat_messages = []
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt = msg.get("content", "")
                else:
                    chat_messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                    })

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": chat_messages,
            }
            if system_prompt:
                body["system"] = system_prompt
            if stop:
                body["stop_sequences"] = stop
        else:
            # Generic format for other models (Titan, etc.)
            prompt_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            body = {
                "inputText": prompt_text,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": temperature,
                },
            }
            if stop:
                body["textGenerationConfig"]["stopSequences"] = stop

        try:
            # Run synchronous boto3 call in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.invoke_model(
                    modelId=model,
                    body=json.dumps(body),
                    contentType="application/json",
                    accept="application/json",
                ),
            )

            response_body = json.loads(response["body"].read())

            # Parse response based on model type
            if "anthropic" in model or "claude" in model.lower():
                content = response_body.get("content", [{}])[0].get("text", "")
                usage = response_body.get("usage", {})
                return LLMResponse(
                    content=content,
                    model=model,
                    provider=self.provider_name,
                    usage={
                        "prompt_tokens": usage.get("input_tokens", 0),
                        "completion_tokens": usage.get("output_tokens", 0),
                        "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                    },
                    finish_reason=response_body.get("stop_reason"),
                    raw_response=response_body,
                )
            else:
                # Titan and other models
                results = response_body.get("results", [{}])
                content = results[0].get("outputText", "") if results else ""
                return LLMResponse(
                    content=content,
                    model=model,
                    provider=self.provider_name,
                    usage={},
                    finish_reason="stop",
                    raw_response=response_body,
                )
        except Exception as e:
            logger.error(f"AWS Bedrock error: {e}")
            raise RuntimeError(f"AWS Bedrock API error: {e}")

    async def list_models(self) -> List[str]:
        """List available Bedrock models."""
        return [
            "anthropic.claude-3-opus-20240229-v1:0",
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "anthropic.claude-3-haiku-20240307-v1:0",
            "anthropic.claude-v2:1",
            "anthropic.claude-v2",
            "anthropic.claude-instant-v1",
            "amazon.titan-text-express-v1",
            "amazon.titan-text-lite-v1",
        ]

    async def health_check(self) -> bool:
        """Check if AWS Bedrock is accessible."""
        try:
            self._get_client()
            return True
        except Exception:
            return False


# Provider registry - stores singleton instances
_providers: Dict[str, LLMProvider] = {}


def get_llm_provider(
    provider_type: Optional[LLMProviderType | str] = None,
    config: Optional[LLMConfig] = None,
    **kwargs,
) -> LLMProvider:
    """
    Factory function to get an LLM provider instance.

    Uses singleton pattern to reuse provider instances.
    Provider is determined by (in order of precedence):
    1. Explicit provider_type parameter
    2. config.provider if config is provided
    3. Global settings.LLM_PROVIDER

    Args:
        provider_type: Explicit provider type (overrides config)
        config: LLMConfig instance for additional settings
        **kwargs: Additional provider-specific arguments

    Returns:
        LLMProvider instance

    Examples:
        # Use global config (from .env LLM_PROVIDER)
        llm = get_llm_provider()

        # Explicit provider
        llm = get_llm_provider(LLMProviderType.OPENAI)

        # With config override
        config = LLMConfig(provider="ollama", model="llama3")
        llm = get_llm_provider(config=config)
    """
    # Determine provider type
    if provider_type is not None:
        if isinstance(provider_type, str):
            provider_type = LLMProviderType(provider_type)
        provider_key = provider_type.value
    elif config is not None:
        provider_key = config.provider
    else:
        provider_key = settings.LLM_PROVIDER

    # Return cached instance if available
    if provider_key in _providers:
        return _providers[provider_key]

    # Create new provider instance
    provider_classes = {
        LLMProviderType.OPENAI.value: OpenAIProvider,
        LLMProviderType.OLLAMA.value: OllamaProvider,
        LLMProviderType.AWS_BEDROCK.value: AWSBedrockProvider,
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
        "aws_bedrock": AWSBedrockProvider,
    }

    provider_class = provider_classes.get(provider_key)
    if not provider_class:
        raise ValueError(f"Unsupported LLM provider: {provider_key}")

    # Merge config kwargs with explicit kwargs
    init_kwargs = {}
    if config:
        init_kwargs["default_model"] = config.model
        init_kwargs["timeout"] = config.timeout
    init_kwargs.update(kwargs)

    _providers[provider_key] = provider_class(**init_kwargs)
    return _providers[provider_key]


def clear_provider_cache():
    """Clear the provider cache (useful for testing)."""
    global _providers
    _providers = {}


async def get_default_llm() -> LLMProvider:
    """Get the default LLM provider based on global settings."""
    return get_llm_provider()


# Export commonly used items
__all__ = [
    "LLMProviderType",
    "LLMProvider",
    "LLMResponse",
    "LLMConfig",
    "OllamaProvider",
    "OpenAIProvider",
    "AWSBedrockProvider",
    "get_llm_provider",
    "get_default_llm",
    "clear_provider_cache",
]
