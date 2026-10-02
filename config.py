"""
Configuration Management for AI-Powered Requirements Engineering Tool
Handles all configuration parameters, model settings, and environment variables
"""

import os
from dataclasses import dataclass
from typing import Dict, List
from enum import Enum

class ModelType(Enum):
    """Supported LLM Models"""
    GPT_4O = "gpt-4o"
    GPT_4 = "gpt-4"
    CHATGPT = "gpt-3.5-turbo"
    GEMINI = "gemini-pro"
    CLAUDE = "claude-3-opus-20240229"
    BERT = "bert-base-uncased"
    FINE_TUNED_BERT = "fine-tuned-bert-re"

class RETaskType(Enum):
    """Requirements Engineering Tasks"""
    EXTRACTION = "extraction"
    CLASSIFICATION = "classification"
    NER = "ner"
    QA = "question_answering"
    TEST_CASE_GEN = "test_case_generation"
    QUALITY_ASSESSMENT = "quality_assessment"
    SPECIFICATION_GEN = "specification_generation"

@dataclass
class DatasetConfig:
    """Dataset Configuration"""
    name: str
    path: str
    size: int
    task_type: RETaskType
    description: str

    # Known datasets from literature review
    PURE = "Pure"
    PROMISE = "PROMISE"
    AEROSPACE = "Aerospace"
    REQUESTQA = "REQuestA"

# Dataset Configurations
DATASETS = {
    DatasetConfig.PURE: DatasetConfig(
        name="Pure",
        path="data/pure_dataset.csv",
        size=7445,
        task_type=RETaskType.EXTRACTION,
        description="Requirements extraction dataset with 7,445 samples"
    ),
    DatasetConfig.PROMISE: DatasetConfig(
        name="PROMISE",
        path="data/promise_dataset.csv",
        size=622,
        task_type=RETaskType.CLASSIFICATION,
        description="Functional vs Non-functional requirement classification (622 samples)"
    ),
    DatasetConfig.AEROSPACE: DatasetConfig(
        name="Aerospace",
        path="data/aerospace_dataset.txt",
        size=6347,
        task_type=RETaskType.NER,
        description="Aerospace requirements NER dataset (6,347 words)"
    ),
    DatasetConfig.REQUESTQA: DatasetConfig(
        name="REQuestA",
        path="data/requestqa_dataset.json",
        size=300,
        task_type=RETaskType.QA,
        description="Question Answering dataset (300 QA pairs)"
    ),
}

@dataclass
class ModelConfig:
    """Model Configuration and Performance Baseline"""
    model_type: ModelType
    task_suitability: List[RETaskType]
    baseline_performance: Dict[str, float]
    max_tokens: int
    temperature: float
    api_key_env: str

MODEL_CONFIGS = {
    ModelType.GPT_4O: ModelConfig(
        model_type=ModelType.GPT_4O,
        task_suitability=[
            RETaskType.QA,
            RETaskType.SPECIFICATION_GEN,
            RETaskType.TEST_CASE_GEN,
            RETaskType.QUALITY_ASSESSMENT
        ],
        baseline_performance={
            "qa_f1": 0.91,
            "test_line_coverage": 0.9865,
            "test_branch_coverage": 0.9716,
            "quality_assessment_accuracy": 0.6955
        },
        max_tokens=4096,
        temperature=0.7,
        api_key_env="OPENAI_API_KEY"
    ),
    ModelType.CHATGPT: ModelConfig(
        model_type=ModelType.CHATGPT,
        task_suitability=[
            RETaskType.QA,
            RETaskType.SPECIFICATION_GEN,
            RETaskType.QUALITY_ASSESSMENT
        ],
        baseline_performance={
            "extraction_f1": 0.76,
            "classification_f1": 0.78,
            "ner_f1": 0.36,
            "qa_f1": 0.91
        },
        max_tokens=4096,
        temperature=0.7,
        api_key_env="OPENAI_API_KEY"
    ),
    ModelType.GEMINI: ModelConfig(
        model_type=ModelType.GEMINI,
        task_suitability=[
            RETaskType.QA,
            RETaskType.SPECIFICATION_GEN,
            RETaskType.QUALITY_ASSESSMENT
        ],
        baseline_performance={
            "extraction_f1": 0.77,
            "classification_f1": 0.78,
            "ner_f1": 0.25,
            "qa_f1": 0.88
        },
        max_tokens=4096,
        temperature=0.7,
        api_key_env="GOOGLE_API_KEY"
    ),
    ModelType.BERT: ModelConfig(
        model_type=ModelType.BERT,
        task_suitability=[
            RETaskType.CLASSIFICATION,
            RETaskType.EXTRACTION,
            RETaskType.NER
        ],
        baseline_performance={
            "extraction_f1": 0.86,
            "classification_f1": 0.96,  # Fine-tuned baseline
            "ner_f1": 0.92  # Aero-BERT baseline
        },
        max_tokens=512,
        temperature=0.0,
        api_key_env=""
    ),
}

@dataclass
class PromptEngineeringConfig:
    """Prompt Engineering Strategy Configuration"""
    strategy_level: str  # "basic", "intermediate", "expert"
    include_examples: bool
    use_chain_of_thought: bool
    domain_context: str
    output_format: str

PROMPT_STRATEGIES = {
    "basic": PromptEngineeringConfig(
        strategy_level="basic",
        include_examples=False,
        use_chain_of_thought=False,
        domain_context="minimal",
        output_format="natural_language"
    ),
    "intermediate": PromptEngineeringConfig(
        strategy_level="intermediate",
        include_examples=True,
        use_chain_of_thought=True,
        domain_context="moderate",
        output_format="structured"
    ),
    "expert": PromptEngineeringConfig(
        strategy_level="expert",
        include_examples=True,
        use_chain_of_thought=True,
        domain_context="comprehensive",
        output_format="formal_specification"
    ),
}

class AppConfig:
    """Main Application Configuration"""

    # Project paths
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(PROJECT_ROOT, "data")
    LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
    MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
    OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

    # API Configuration
    DEFAULT_MODEL = ModelType.GPT_4O
    FALLBACK_MODELS = [ModelType.CHATGPT, ModelType.GEMINI]
    API_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

    # Processing Configuration
    BATCH_SIZE = 32
    VALIDATION_SPLIT = 0.2
    TEST_SPLIT = 0.1

    # Quality Assurance
    QUALITY_THRESHOLD = 0.7
    HUMAN_REVIEW_THRESHOLD = 0.5
    CONSISTENCY_CHECK_ENABLED = True

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Performance Tracking
    TRACK_PERFORMANCE_METRICS = True
    METRICS_EXPORT_FORMAT = "json"  # json, csv, prometheus

    # Cache Configuration
    ENABLE_CACHING = True
    CACHE_TTL = 3600  # seconds

    # Human-in-the-Loop Configuration
    HIML_ENABLED = True
    HIML_REVIEW_QUEUE_SIZE = 100

    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        for directory in [cls.DATA_DIR, cls.LOGS_DIR, cls.MODELS_DIR, cls.OUTPUT_DIR]:
            os.makedirs(directory, exist_ok=True)

    @classmethod
    def get_model_config(cls, model_type: ModelType) -> ModelConfig:
        """Get configuration for a specific model"""
        if model_type not in MODEL_CONFIGS:
            raise ValueError(f"Unknown model type: {model_type}")
        return MODEL_CONFIGS[model_type]

    @classmethod
    def get_dataset_config(cls, dataset_name: str) -> DatasetConfig:
        """Get configuration for a specific dataset"""
        if dataset_name not in DATASETS:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        return DATASETS[dataset_name]

    @classmethod
    def get_prompt_strategy(cls, level: str) -> PromptEngineeringConfig:
        """Get prompt engineering strategy"""
        if level not in PROMPT_STRATEGIES:
            raise ValueError(f"Unknown strategy level: {level}")
        return PROMPT_STRATEGIES[level]
