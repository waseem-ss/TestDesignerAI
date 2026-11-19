"""
Enhanced LLM Interface Module for AI-Powered Requirements Engineering Tool
Provides abstraction layer with multi-provider support and automatic failover

NEW FEATURES:
- Groq support (fast, free open-source inference)
- Automatic failover chain: Ollama → Groq → OpenAI → Claude
- Health checks for all providers
- Provider availability tracking
"""

import os
import json
import time

# Use the Windows certificate store for HTTPS, so corporate TLS-inspection roots are trusted.
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from backend.config import ModelType, ModelConfig, AppConfig
from backend.logger import get_logger

logger = get_logger(__name__)

# Provider availability tracking
class LLMProvider(Enum):
    OLLAMA = "ollama"
    GROQ = "groq"
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    HF = "hf"
    MOCK = "mock"

class LLMResponse:
    def __init__(self, content: str, model: str, tokens_used: int, provider: Optional[str] = None, confidence: Optional[float] = None):
        self.content = content
        self.model = model
        self.tokens_used = tokens_used
        self.provider = provider or "unknown"
        self.confidence = confidence
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'model': self.model,
            'provider': self.provider,
            'tokens_used': self.tokens_used,
            'confidence': self.confidence,
            'timestamp': self.timestamp
        }

class ProviderHealth:
    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.is_healthy = True
        self.last_check = datetime.now()
        self.error_count = 0
        self.last_error = None
        self.response_time_ms = None

    def mark_success(self, response_time_ms: float):
        self.is_healthy = True
        self.error_count = max(0, self.error_count - 1)
        self.last_check = datetime.now()
        self.last_error = None
        self.response_time_ms = response_time_ms

    def mark_failure(self, error: str):
        self.error_count += 1
        self.last_error = error
        self.last_check = datetime.now()
        if self.error_count >= 3:
            self.is_healthy = False

class ProviderHealthMonitor:
    def __init__(self):
        self.health_status = {}
        for provider in LLMProvider:
            self.health_status[provider] = ProviderHealth(provider)

    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of healthy providers"""
        available = []
        for provider in [LLMProvider.OLLAMA, LLMProvider.GROQ, LLMProvider.HF, LLMProvider.OPENAI, LLMProvider.CLAUDE, LLMProvider.GEMINI]:
            health = self.health_status[provider]
            if health.is_healthy or health.error_count < 10:
                available.append(provider)
        return available

    def get_status_report(self) -> Dict[str, Any]:
        return {
            provider.value: {
                'is_healthy': health.is_healthy,
                'error_count': health.error_count,
                'last_error': health.last_error
            }
            for provider, health in self.health_status.items()
        }

health_monitor = ProviderHealthMonitor()

class BaseLLMModel(ABC):
    def __init__(self, model_config: ModelConfig):
        self.config = model_config
        self.logger = get_logger(self.__class__.__name__)
        self.call_count = 0
        self.total_tokens = 0
        self.provider = LLMProvider.MOCK

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        pass

    @abstractmethod
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        pass

    @abstractmethod
    def classify(self, text: str, categories: List[str]) -> Tuple[str, float]:
        pass

    @abstractmethod
    def question_answering(self, context: str, question: str) -> LLMResponse:
        pass

    def get_statistics(self) -> Dict[str, Any]:
        return {
            'provider': self.provider.value,
            'model': self.config.model_type.value,
            'call_count': self.call_count,
            'total_tokens': self.total_tokens,
        }

class GroqModel(BaseLLMModel):
    """Groq Cloud LLM - Fast open-source inference"""

    def __init__(self, model_config: ModelConfig):
        super().__init__(model_config)
        self.provider = LLMProvider.GROQ
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model_name = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")

        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set")

        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
        except ImportError:
            raise ImportError("Groq SDK required: pip install groq")

    def _make_request(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
            )
            response_time = (time.time() - start_time) * 1000
            health_monitor.health_status[LLMProvider.GROQ].mark_success(response_time)
            if hasattr(response, 'usage'):
                self.total_tokens += response.usage.total_tokens
            return response.choices[0].message.content
        except Exception as e:
            health_monitor.health_status[LLMProvider.GROQ].mark_failure(str(e))
            raise

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        self.call_count += 1
        content = self._make_request(prompt, kwargs.get("max_tokens"))
        return LLMResponse(content, self.model_name, 100, provider=self.provider.value)

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        return {'entities': []}

    def classify(self, text: str, categories: List[str]) -> Tuple[str, float]:
        return categories[0] if categories else "unknown", 0.8

    def question_answering(self, context: str, question: str) -> LLMResponse:
        content = f"Answer: {question}"
        return LLMResponse(content, self.model_name, 50, provider=self.provider.value)

# ---------------------------------------------------------------------------
# Provider calls. Every provider is reached through call_provider(), which
# returns (text, tokens_used) and updates the health monitor.
# ---------------------------------------------------------------------------

# Keys and default models come from .env (see .env.example).
PROVIDER_KEY_ENV = {
    "groq": "GROQ_API_KEY",
    "openai": "OPENAI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "hf": "HF_API_KEY",
}
PROVIDER_MODEL_ENV = {"groq": "GROQ_MODEL", "openai": "OPENAI_MODEL", "claude": "CLAUDE_MODEL",
                      "gemini": "GEMINI_MODEL", "hf": "HF_MODEL"}
# Extra models offered in the dashboard next to the .env default.
PROVIDER_MODEL_CHOICES = {
    "openai": ["gpt-4o", "gpt-4o-mini"],
    "claude": ["claude-sonnet-5-5", "claude-haiku-5-5", "claude-opus-5-5"],
    "gemini": ["gemini-2.5-flash", "gemini-2.5-pro"],
}
# Order used when the provider is "auto" and when failing over.
PROVIDER_ORDER = ("ollama", "groq", "hf", "openai", "claude", "gemini")


def provider_key_configured(provider: str) -> bool:
    env_name = PROVIDER_KEY_ENV.get(provider)
    return bool(env_name and os.getenv(env_name))


def default_model(provider: str) -> str:
    if provider == "ollama":
        return os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    return os.getenv(PROVIDER_MODEL_ENV.get(provider, ""), "")


def model_choices(provider: str) -> List[str]:
    """The .env default model first, then the extra models for this provider."""
    choices: List[str] = []
    for model in [default_model(provider), *PROVIDER_MODEL_CHOICES.get(provider, [])]:
        if model and model not in choices:
            choices.append(model)
    return choices


def _call_groq(key, model, prompt, max_tokens, temperature):
    from groq import Groq
    response = Groq(api_key=key).chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}],
        temperature=temperature, max_tokens=max_tokens,
    )
    tokens = response.usage.total_tokens if response.usage else 0
    return response.choices[0].message.content or "", tokens


def _call_openai(key, model, prompt, max_tokens, temperature):
    from openai import OpenAI
    response = OpenAI(api_key=key).chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}],
        temperature=temperature, max_completion_tokens=max_tokens,
    )
    tokens = response.usage.total_tokens if response.usage else 0
    return response.choices[0].message.content or "", tokens


def _call_claude(key, model, prompt, max_tokens, temperature):
    from anthropic import Anthropic
    # The installed SDK's messages.create has no temperature argument, so the model default applies.
    response = Anthropic(api_key=key).messages.create(
        model=model, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    return text, response.usage.input_tokens + response.usage.output_tokens


def _call_hf(key, model, prompt, max_tokens, temperature):
    from huggingface_hub import InferenceClient
    response = InferenceClient(api_key=key).chat_completion(
        model=model, messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens, temperature=max(temperature, 0.01),  # HF rejects exactly 0
    )
    tokens = response.usage.total_tokens if response.usage else 0
    return response.choices[0].message.content or "", tokens


def _call_gemini(key, model, prompt, max_tokens, temperature):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=model, contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=max_tokens, temperature=temperature),
    )
    tokens = response.usage_metadata.total_token_count if response.usage_metadata else 0
    return response.text or "", tokens or 0


_CLOUD_CALLERS = {"groq": _call_groq, "hf": _call_hf, "openai": _call_openai,
                  "claude": _call_claude, "gemini": _call_gemini}


def call_provider(provider: str, prompt: str, model: Optional[str] = None,
                  max_tokens: int = 512, temperature: float = 0.0) -> Tuple[str, int]:
    """Send one prompt to a provider. Returns (text, tokens_used)."""
    provider = provider.lower()
    model = model or default_model(provider)
    if provider == "ollama":
        from backend.llm_interface import ollama_request
        body = ollama_request(prompt, model=model, max_tokens=max_tokens, temperature=temperature)
        return body.get("response", ""), int(body.get("eval_count", 0) or 0)
    if provider not in _CLOUD_CALLERS:
        raise ValueError(f"Unknown provider {provider!r}")
    if not provider_key_configured(provider):
        raise ValueError(f"{PROVIDER_KEY_ENV[provider]} is not set in .env")
    if not model:
        raise ValueError(f"No model set for {provider}; set {PROVIDER_MODEL_ENV[provider]} in .env")

    health = health_monitor.health_status[LLMProvider(provider)]
    start = time.time()
    try:
        text, tokens = _CLOUD_CALLERS[provider](os.getenv(PROVIDER_KEY_ENV[provider]), model, prompt,
                                                max_tokens, temperature)
    except Exception as e:
        health.mark_failure(str(e))
        raise
    health.mark_success((time.time() - start) * 1000)
    return text, tokens


def resolve_provider(provider: str) -> str:
    """Turn "auto" into the first usable provider; other names are returned unchanged."""
    if provider != "auto":
        return provider
    for candidate in PROVIDER_ORDER:
        if candidate == "ollama":
            try:
                from backend.llm_interface import list_ollama_models
                list_ollama_models()
                return candidate
            except ConnectionError:
                continue
        elif provider_key_configured(candidate):
            return candidate
    raise ValueError("No LLM provider is available: start Ollama or set an API key in .env")


class CloudLLMModel(BaseLLMModel):
    """Any provider from call_provider() behind the BaseLLMModel interface."""

    def __init__(self, provider: str, model_config: ModelConfig, model_name: Optional[str] = None):
        super().__init__(model_config)
        self.provider = LLMProvider(provider)
        self.model_name = model_name or default_model(provider)

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        self.call_count += 1
        text, tokens = call_provider(
            self.provider.value, prompt, model=self.model_name,
            max_tokens=kwargs.get("max_tokens") or self.config.max_tokens,
            temperature=self.config.temperature,
        )
        self.total_tokens += tokens
        return LLMResponse(text, self.model_name, tokens, provider=self.provider.value)

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        return {'entities': []}

    def classify(self, text: str, categories: List[str]) -> Tuple[str, float]:
        return categories[0] if categories else "unknown", 0.5

    def question_answering(self, context: str, question: str) -> LLMResponse:
        return self.generate(f"Context: {context}\n\nQuestion: {question}")


class FailoverLLMModel(BaseLLMModel):
    """Automatic failover across multiple LLM providers"""

    def __init__(self, model_config: ModelConfig):
        super().__init__(model_config)
        self.selected_model: Optional[BaseLLMModel] = None
        self.failed_providers: set = set()

    def _select_best_provider(self) -> BaseLLMModel:
        """Priority: Ollama -> Groq -> OpenAI -> Claude -> Gemini -> Mock.

        Providers that failed earlier in this session are skipped.
        """
        config = AppConfig.get_model_config(ModelType.GPT_4O)
        for provider in PROVIDER_ORDER:
            if provider in self.failed_providers:
                continue
            if provider == "ollama" or provider_key_configured(provider):
                return CloudLLMModel(provider, config)
        logger.warning("No providers available, using mock")
        return MockModel(config)

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        self.call_count += 1
        if not self.selected_model:
            self.selected_model = self._select_best_provider()
        try:
            return self.selected_model.generate(prompt, **kwargs)
        except Exception as e:
            failed = self.selected_model.provider.value
            logger.error(f"Provider {failed} failed: {e}, trying the next provider...")
            self.failed_providers.add(failed)
            self.selected_model = self._select_best_provider()
            return self.selected_model.generate(prompt, **kwargs)

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        if not self.selected_model:
            self.selected_model = self._select_best_provider()
        return self.selected_model.extract_entities(text)

    def classify(self, text: str, categories: List[str]) -> Tuple[str, float]:
        if not self.selected_model:
            self.selected_model = self._select_best_provider()
        return self.selected_model.classify(text, categories)

    def question_answering(self, context: str, question: str) -> LLMResponse:
        if not self.selected_model:
            self.selected_model = self._select_best_provider()
        return self.selected_model.question_answering(context, question)

class MockModel(BaseLLMModel):
    """Mock model for testing"""

    def __init__(self, model_config: ModelConfig):
        super().__init__(model_config)
        self.provider = LLMProvider.MOCK

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        self.call_count += 1
        content = f"[MOCK] Response: {prompt[:30]}..."
        return LLMResponse(content, "mock", 10, provider=self.provider.value)

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        return {'entities': ['test_entity']}

    def classify(self, text: str, categories: List[str]) -> Tuple[str, float]:
        return categories[0] if categories else "mock", 0.5

    def question_answering(self, context: str, question: str) -> LLMResponse:
        content = f"[MOCK] Answer: test"
        return LLMResponse(content, "mock", 10, provider=self.provider.value)

def get_provider_health_status() -> Dict[str, Any]:
    """Get health status of all providers"""
    return health_monitor.get_status_report()

def get_available_providers() -> List[str]:
    """Get list of available providers"""
    return [p.value for p in health_monitor.get_available_providers()]
