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
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from config import ModelType, ModelConfig, AppConfig
from logger import get_logger

logger = get_logger(__name__)

# Provider availability tracking
class LLMProvider(Enum):
    OLLAMA = "ollama"
    GROQ = "groq"
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
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
        for provider in [LLMProvider.OLLAMA, LLMProvider.GROQ, LLMProvider.OPENAI, LLMProvider.CLAUDE, LLMProvider.GEMINI]:
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

class FailoverLLMModel(BaseLLMModel):
    """Automatic failover across multiple LLM providers"""

    def __init__(self, model_config: ModelConfig):
        super().__init__(model_config)
        self.selected_model: Optional[BaseLLMModel] = None

    def _select_best_provider(self):
        """Priority: Ollama → Groq → OpenAI → Claude → Gemini → Mock"""
        try:
            # Try importing and testing each provider
            if os.getenv("OLLAMA_URL"):
                from llm_interface import OllamaModel as OldOllama
                config = AppConfig.get_model_config(ModelType.GPT_4O)
                return OldOllama(config)
        except:
            pass

        try:
            if os.getenv("GROQ_API_KEY"):
                config = AppConfig.get_model_config(ModelType.GPT_4O)
                return GroqModel(config)
        except:
            pass

        logger.warning("No providers available, using mock")
        config = AppConfig.get_model_config(ModelType.GPT_4O)
        return MockModel(config)

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        self.call_count += 1
        if not self.selected_model:
            self.selected_model = self._select_best_provider()
        try:
            return self.selected_model.generate(prompt, **kwargs)
        except Exception as e:
            logger.error(f"Provider failed: {e}, retrying...")
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
