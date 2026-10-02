"""
LLM Interface Module for AI-Powered Requirements Engineering Tool
Provides abstraction layer for multiple LLM models
Supports: GPT-4o, ChatGPT, Gemini, Claude
"""

import os
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from config import ModelType, ModelConfig, AppConfig, PromptEngineeringConfig
from logger import get_logger

logger = get_logger(__name__)


class LLMResponse:
    """Structured response from LLM"""

    def __init__(self, content: str, model: str, tokens_used: int, confidence: Optional[float] = None):
        self.content = content
        self.model = model
        self.tokens_used = tokens_used
        self.confidence = confidence
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'content': self.content,
            'model': self.model,
            'tokens_used': self.tokens_used,
            'confidence': self.confidence,
            'timestamp': self.timestamp
        }


class BaseLLMModel(ABC):
    """Base class for LLM models"""

    def __init__(self, model_config: ModelConfig):
        self.config = model_config
        self.logger = get_logger(self.__class__.__name__)
        self.api_key = os.getenv(model_config.api_key_env, "")
        self.call_count = 0
        self.total_tokens = 0

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response from prompt"""
        pass

    @abstractmethod
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text"""
        pass

    @abstractmethod
    def classify(self, text: str, categories: List[str]) -> Tuple[str, float]:
        """Classify text into categories"""
        pass

    @abstractmethod
    def question_answering(self, context: str, question: str) -> LLMResponse:
        """Answer question based on context"""
        pass

    def _make_api_call(self, prompt: str, max_retries: int = AppConfig.MAX_RETRIES) -> str:
        """Make API call with retry logic"""
        for attempt in range(max_retries):
            try:
                self.call_count += 1
                # Actual API call implementation would go here
                # This is a placeholder
                logger.debug(f"API call {self.call_count} for {self.config.model_type.value}")
                return self._mock_api_response(prompt)

            except Exception as e:
                self.logger.error(f"API call failed (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(AppConfig.RETRY_DELAY)
                else:
                    raise

        raise RuntimeError("API call failed without an available retry")

    def _mock_api_response(self, prompt: str) -> str:
        """Generate mock response for demonstration"""
        return f"Generated response based on: {prompt[:50]}..."

    def get_statistics(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        return {
            'call_count': self.call_count,
            'total_tokens': self.total_tokens,
            'avg_tokens_per_call': self.total_tokens / self.call_count if self.call_count > 0 else 0
        }


class GPT4OModel(BaseLLMModel):
    """GPT-4o Model Implementation"""

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using GPT-4o"""
        try:
            # In production, this would use OpenAI API
            # response = openai.ChatCompletion.create(
            #     model="gpt-4o",
            #     messages=[{"role": "user", "content": prompt}],
            #     temperature=kwargs.get('temperature', self.config.temperature),
            #     max_tokens=kwargs.get('max_tokens', self.config.max_tokens)
            # )
            # return LLMResponse(response.choices[0].message.content, "gpt-4o", response.usage.total_tokens)

            content = self._make_api_call(prompt)
            self.total_tokens += 100  # Mock token count
            return LLMResponse(content, "gpt-4o", 100)

        except Exception as e:
            self.logger.error(f"GPT-4o generation failed: {str(e)}")
            raise

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using GPT-4o"""
        prompt = f"""Extract named entities from the following requirement text.
Classify them as: ACTOR, ACTION, ENTITY, ATTRIBUTE, CONSTRAINT

Text: {text}

Return as JSON with entity types as keys and lists of entities as values."""

        response = self.generate(prompt)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse entity extraction JSON")
            return {}

    def classify(self, text: str, categories: List[str]) -> Tuple[str, float]:
        """Classify text into categories using GPT-4o"""
        categories_str = ", ".join(categories)
        prompt = f"""Classify the following requirement into one of these categories: {categories_str}
Provide a confidence score (0-1).

Requirement: {text}

Response format: CATEGORY|CONFIDENCE"""

        response = self.generate(prompt)
        parts = response.content.split("|")
        if len(parts) == 2:
            return parts[0].strip(), float(parts[1].strip())
        return categories[0], 0.5

    def question_answering(self, context: str, question: str) -> LLMResponse:
        """Answer question about requirements"""
        prompt = f"""Based on the following requirement context, answer the question.

Context: {context}

Question: {question}

Provide a clear, concise answer."""

        return self.generate(prompt)


class ChatGPTModel(BaseLLMModel):
    """ChatGPT (GPT-3.5-turbo) Model Implementation"""

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using ChatGPT"""
        try:
            content = self._make_api_call(prompt)
            self.total_tokens += 80  # Mock token count
            return LLMResponse(content, "gpt-3.5-turbo", 80)

        except Exception as e:
            self.logger.error(f"ChatGPT generation failed: {str(e)}")
            raise

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using ChatGPT"""
        # ChatGPT generally underperforms on NER (F1=0.36), so recommend fine-tuned BERT
        prompt = f"""Extract key entities from: {text}"""
        response = self.generate(prompt)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse entity extraction JSON")
            return {}

    def classify(self, text: str, categories: List[str]) -> Tuple[str, float]:
        """Classify text into categories"""
        categories_str = ", ".join(categories)
        prompt = f"Classify '{text}' into: {categories_str}"
        response = self.generate(prompt)
        return categories[0], 0.78  # Baseline from literature review

    def question_answering(self, context: str, question: str) -> LLMResponse:
        """Answer question - ChatGPT's strongest capability (F1=0.91)"""
        prompt = f"""Context: {context}
Question: {question}
Answer:"""
        return self.generate(prompt)


class GeminiModel(BaseLLMModel):
    """Google Gemini Model Implementation"""

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using Gemini"""
        try:
            content = self._make_api_call(prompt)
            self.total_tokens += 90
            return LLMResponse(content, "gemini-pro", 90)

        except Exception as e:
            self.logger.error(f"Gemini generation failed: {str(e)}")
            raise

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using Gemini"""
        prompt = f"""Extract entities from requirement: {text}"""
        response = self.generate(prompt)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {}

    def classify(self, text: str, categories: List[str]) -> Tuple[str, float]:
        """Classify text - similar performance to ChatGPT (F1=0.78)"""
        categories_str = ", ".join(categories)
        prompt = f"Classify: '{text}' into {categories_str}"
        response = self.generate(prompt)
        return categories[0], 0.78

    def question_answering(self, context: str, question: str) -> LLMResponse:
        """Answer question - performs well (F1=0.88)"""
        prompt = f"""Context: {context}
Question: {question}
Answer:"""
        return self.generate(prompt)


class ClaudeModel(BaseLLMModel):
    """Anthropic Claude Model Implementation"""

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using Claude"""
        try:
            content = self._make_api_call(prompt)
            self.total_tokens += 110
            return LLMResponse(content, "claude-3-opus", 110)

        except Exception as e:
            self.logger.error(f"Claude generation failed: {str(e)}")
            raise

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using Claude"""
        prompt = f"""Carefully extract all entities from this requirement text:
{text}"""
        response = self.generate(prompt)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {}

    def classify(self, text: str, categories: List[str]) -> Tuple[str, float]:
        """Classify text"""
        categories_str = ", ".join(categories)
        prompt = f"Classify this requirement into one category: {categories_str}\n\nRequirement: {text}"
        response = self.generate(prompt)
        return categories[0], 0.80

    def question_answering(self, context: str, question: str) -> LLMResponse:
        """Answer question"""
        prompt = f"""Using this requirement context:
{context}

Answer this question:
{question}"""
        return self.generate(prompt)


class BERTModel(BaseLLMModel):
    """BERT Model for Classification and Extraction"""

    def __init__(self, model_config: ModelConfig):
        super().__init__(model_config)
        # In production, load actual BERT model
        # self.model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased")
        # self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """BERT doesn't support free-form generation"""
        raise NotImplementedError("BERT doesn't support free-form text generation")

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities - BERT's strength (F1=0.92 for Aero-BERT)"""
        # In production: use token classification head
        self.total_tokens += 50
        return {
            'entities': ['entity1', 'entity2']
        }

    def classify(self, text: str, categories: List[str]) -> Tuple[str, float]:
        """Classify text - BERT's strength (F1=0.96 for functional/non-functional)"""
        # In production: run through classification head
        self.total_tokens += 40
        return categories[0], 0.96

    def question_answering(self, context: str, question: str) -> LLMResponse:
        """BERT as Q&A model"""
        # In production: use extractive Q&A with span prediction
        content = "Answer extracted from context"
        return LLMResponse(content, "bert-base-uncased", 50)


class ModelFactory:
    """Factory for creating LLM model instances"""

    _models = {
        ModelType.GPT_4O: GPT4OModel,
        ModelType.CHATGPT: ChatGPTModel,
        ModelType.GEMINI: GeminiModel,
        ModelType.CLAUDE: ClaudeModel,
        ModelType.BERT: BERTModel,
    }

    @staticmethod
    def create_model(model_type: ModelType) -> BaseLLMModel:
        """Create model instance"""
        model_class = ModelFactory._models.get(model_type)
        if model_class is None:
            raise ValueError(f"Unknown model type: {model_type}")

        model_config = AppConfig.get_model_config(model_type)
        return model_class(model_config)

    @staticmethod
    def create_best_model_for_task(task_type: Any) -> BaseLLMModel:
        """Create best model for a task represented by an enum or string."""
        task_value = getattr(task_type, 'value', task_type)

        if task_value == "question_answering":
            return ModelFactory.create_model(ModelType.GPT_4O)
        elif task_value in ("extraction", "classification", "ner"):
            return ModelFactory.create_model(ModelType.BERT)
        else:
            return ModelFactory.create_model(ModelType.GPT_4O)


class LLMPipeline:
    """Orchestrates multiple LLM models for RE tasks"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.models: Dict[ModelType, BaseLLMModel] = {}
        self.results_cache = {}

    def process_requirement(self, requirement_text: str, tasks: List[str]) -> Dict[str, Any]:
        """Process requirement through multiple LLM tasks"""
        results = {
            'input': requirement_text,
            'tasks_results': {}
        }

        for task in tasks:
            try:
                if task == 'extract':
                    model = ModelFactory.create_best_model_for_task('extraction')
                    result = model.extract_entities(requirement_text)
                    results['tasks_results']['extraction'] = result

                elif task == 'classify':
                    model = ModelFactory.create_best_model_for_task('classification')
                    classification, confidence = model.classify(requirement_text, ['Functional', 'Non-Functional'])
                    results['tasks_results']['classification'] = {
                        'type': classification,
                        'confidence': confidence
                    }

                elif task == 'quality_assess':
                    model = ModelFactory.create_model(ModelType.GPT_4O)
                    response = model.generate(f"Assess quality of: {requirement_text}")
                    results['tasks_results']['quality_assessment'] = response.to_dict()

            except Exception as e:
                self.logger.error(f"Error processing task {task}: {str(e)}")
                results['tasks_results'][task] = {'error': str(e)}

        return results
