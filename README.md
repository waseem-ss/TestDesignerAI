# AI-Powered Requirements Engineering Tool

A Python-based boilerplate for building LLM-driven Requirements Engineering (RE) tools that leverage the latest advances in Large Language Models and machine learning techniques.

**Based on:** Literature Review: AI-Powered Requirements Engineering Tool Using Large Language Models (Sem 4, MTech Data Science & AI)

---

## Overview

This tool implements a production-ready architecture for:
- **Requirements Extraction** - Extract requirements from natural language
- **Requirements Classification** - Classify into functional/non-functional
- **Named Entity Recognition (NER)** - Identify key entities in requirements
- **Question Answering** - Answer questions about requirements
- **Test Case Generation** - Generate test cases from requirements
- **Quality Assessment** - Evaluate requirement quality and completeness

The tool uses a **hybrid multi-model approach** combining:
- Fine-tuned BERT for classification/extraction/NER
- GPT-4o/ChatGPT/Gemini for generation and QA
- Claude for documentation
- Human-in-the-loop validation

---

## Architecture

### System Design Pattern

```
Input → Task Classification → Model Selection →
         Processing → Quality Validation → Human Review (if needed)
```

### Key Components

#### 1. **config.py** - Configuration Management
- Model configurations with baseline performance metrics
- Dataset configurations (Pure, PROMISE, Aerospace, REQuestA)
- Prompt engineering strategies (basic, intermediate, expert)
- Application settings and thresholds

#### 2. **data_loader.py** - Data Loading & Preprocessing
- `PureDataLoader` - Requirements Extraction (7,445 samples)
- `PROMISEDataLoader` - Requirements Classification (622 samples)
- `AerospaceDataLoader` - NER Tasks (6,347 words)
- `REQuestADataLoader` - Question Answering (300 QA pairs)
- Automatic data validation and train/val/test splitting

#### 3. **llm_interface.py** - LLM Model Abstraction
- `BaseLLMModel` - Abstract base class
- `GPT4OModel` - GPT-4o implementation
- `ChatGPTModel` - GPT-3.5-turbo implementation
- `GeminiModel` - Google Gemini implementation
- `ClaudeModel` - Anthropic Claude implementation
- `BERTModel` - BERT for classification/extraction
- `ModelFactory` - Factory pattern for model instantiation

#### 4. **evaluation.py** - Metrics & Evaluation
- **Classification Metrics**: Precision, Recall, F1, Accuracy
- **Text Generation Metrics**: BLEU, ROUGE-L scores
- **Test Coverage Metrics**: Line/Branch/Path coverage
- **Quality Metrics**: Completeness, Consistency, Ambiguity
- **NER Metrics**: Entity-level and token-level evaluation

#### 5. **pipeline.py** - Main Orchestration
- `REPipeline` - Main processing pipeline
- `TaskClassifier` - Routes requirements to appropriate models
- `QualityValidator` - Validates output quality
- `HumanInTheLoopQueue` - Manages human review process

#### 6. **logger.py** - Logging Infrastructure
- Structured logging to console and file
- Rotating file handlers with size limits
- Configurable log levels

#### 7. **main.py** - Entry Point
- Demonstrates all pipeline features
- Shows model comparison and capabilities
- Provides example usage patterns

---

## Performance Baselines (from Literature Review)

### Task Performance Comparison

| Task | Model | Metric | Performance |
|------|-------|--------|-------------|
| Requirement Extraction | Fine-tuned BERT | F1 | 0.86 |
| Requirement Extraction | ChatGPT | F1 | 0.76 |
| Requirement Classification | Fine-tuned BERT | F1 | 0.96 |
| Requirement Classification | ChatGPT/Gemini | F1 | 0.78 |
| Named Entity Recognition | Aero-BERT | F1 | 0.92 |
| Named Entity Recognition | ChatGPT | F1 | 0.36 |
| Question Answering | ChatGPT | F1 | 0.91 |
| Question Answering | Gemini | F1 | 0.88 |
| Test Case Generation (Line) | GPT-4o | Coverage | 98.65% |

---

## Installation

### Prerequisites
- Python 3.9+
- pip or conda
- API keys for LLM services (optional, tool has mock implementations)

### Setup

1. **Clone/Download the repository**
   ```bash
   cd ai_re_tool_boilerplate
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional, for actual API calls)
   ```bash
   # Create .env file
   OPENAI_API_KEY=your_openai_key
   GOOGLE_API_KEY=your_google_key
   ANTHROPIC_API_KEY=your_anthropic_key
   ```

5. **Verify installation**
   ```bash
   python -c "from config import AppConfig; print('Installation successful!')"
   ```

---

## Usage

### Basic Usage

#### 1. Process Single Requirement
```python
from pipeline import REPipeline

pipeline = REPipeline()

requirement = "The system shall validate user input and display error messages"
result = pipeline.process_requirement("REQ_001", requirement)

print(f"Status: {result.status.value}")
print(f"Classification: {result.classification_result}")
print(f"Needs Review: {result.human_review_required}")
```

#### 2. Process Batch of Requirements
```python
requirements = [
    ("REQ_001", "The system shall support OAuth 2.0"),
    ("REQ_002", "The database shall handle 1000 concurrent users"),
    ("REQ_003", "Users must receive confirmation emails within 2 minutes"),
]

results = pipeline.process_batch(requirements)

for result in results:
    print(f"{result.requirement_id}: {result.status.value}")
```

#### 3. Load and Process Dataset
```python
# Process PROMISE dataset for classification
dataset_results = pipeline.load_and_process_dataset("PROMISE")

print(f"Processed {len(dataset_results)} requirements")

# View statistics
stats = pipeline.get_pipeline_statistics()
print(f"Success rate: {stats['success_rate']:.2%}")
```

#### 4. Access Human Review Queue
```python
# Get pending reviews
queue_status = pipeline.review_queue.get_queue_status()
print(f"Pending: {queue_status['pending']}")

# Approve a requirement
pipeline.review_queue.approve("REQ_001", notes="Looks good!")

# Reject a requirement
pipeline.review_queue.reject("REQ_002", notes="Needs clarification")
```

### Command Line Usage

```bash
# Run main pipeline with examples
python main.py

# Show prompt engineering strategies
python main.py --prompts

# Show available datasets
python main.py --datasets

# Display help
python main.py --help
```

---

## Dataset Specifications

### 1. Pure Dataset (Requirement Extraction)
- **Size**: 7,445 samples
- **Task**: Extract structured requirements from text
- **Format**: CSV with source_text and extracted_requirements
- **Baseline F1**: 0.86 (Fine-tuned BERT)

### 2. PROMISE Dataset (Classification)
- **Size**: 622 samples
- **Task**: Classify as Functional or Non-Functional
- **Format**: CSV with requirement_text and type
- **Baseline F1**: 0.96 (Fine-tuned BERT)

### 3. Aerospace Dataset (NER)
- **Size**: 6,347 words
- **Task**: Named Entity Recognition for aerospace requirements
- **Format**: JSON with text and entity annotations
- **Baseline F1**: 0.92 (Aero-BERT)

### 4. REQuestA Dataset (QA)
- **Size**: 300 QA pairs
- **Task**: Answer questions about requirements
- **Format**: JSON with requirement, question, and answer
- **Baseline F1**: 0.91 (ChatGPT)

---

## Configuration Guide

### Model Selection

```python
from config import AppConfig, ModelType, RETaskType

# Get best model for task
config = AppConfig.get_model_config(ModelType.GPT_4O)
print(config.baseline_performance)  # View performance metrics

# Check suitability
if RETaskType.QA in config.task_suitability:
    print("GPT-4o is suitable for Question Answering")
```

### Prompt Engineering Strategies

```python
from config import AppConfig

# Get strategy
strategy = AppConfig.get_prompt_strategy("expert")
print(f"Use examples: {strategy.include_examples}")
print(f"Chain-of-thought: {strategy.use_chain_of_thought}")
print(f"Context level: {strategy.domain_context}")
```

### Quality Thresholds

```python
from config import AppConfig

# Adjust quality requirements
AppConfig.QUALITY_THRESHOLD = 0.75         # Higher quality bar
AppConfig.HUMAN_REVIEW_THRESHOLD = 0.60    # More items for review
AppConfig.HIML_ENABLED = True              # Enable human review
```

---

## Extension Guide

### Adding New Model

```python
from llm_interface import BaseLLMModel, ModelFactory
from config import ModelType, ModelConfig

class CustomModel(BaseLLMModel):
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        # Implement your model
        pass
    
    def extract_entities(self, text: str) -> Dict:
        # Implement entity extraction
        pass
    
    # ... implement other methods

# Register in factory
ModelFactory._models[ModelType.CUSTOM] = CustomModel
```

### Adding Custom Task Type

```python
from config import RETaskType

# In config.py, add to RETaskType enum
class RETaskType(Enum):
    # ... existing tasks
    CUSTOM_TASK = "custom_task"

# Create specialized data loader
from data_loader import DataLoader

class CustomDataLoader(DataLoader):
    def load(self):
        # Load your data
        pass
    # ... implement other methods
```

### Custom Evaluation Metrics

```python
from evaluation import EvaluationMetrics

def custom_metric(y_true, y_pred):
    # Calculate your metric
    score = ...
    return EvaluationMetrics(
        precision=...,
        recall=...,
        f1_score=...,
        additional_metrics={'custom_metric': score}
    )
```

---

## Key Findings from Literature Review

### Strengths of LLMs in RE
- ✅ Specification generation and UML diagram creation
- ✅ Requirement quality assessment
- ✅ Question answering about requirements (F1=0.91)
- ✅ Test case generation (98.65% line coverage with GPT-4o)
- ✅ Interactive refinement processes

### Limitations of LLMs
- ❌ Named Entity Recognition (F1=0.36 for ChatGPT vs 0.92 baseline)
- ❌ Complex multi-step reasoning
- ❌ Hallucination and inconsistency
- ❌ Handling large requirement documents
- ❌ Structured output consistency

### Recommendations
1. **Use hybrid approach**: Fine-tuned BERT for extraction/classification, GPT-4o for generation
2. **Implement human-in-the-loop**: Review low-confidence outputs
3. **Prompt engineering matters**: Expert prompts improve Gemini by ~5-10%
4. **Multiple iterations**: Average outputs over multiple runs for stability
5. **Task-specific models**: Don't use one model for all tasks

---

## Best Practices

1. **Data Validation**
   - Always validate datasets before processing
   - Check for duplicates and missing values
   - Use stratified splits for imbalanced data

2. **Quality Assurance**
   - Enable human review for low-confidence outputs
   - Track consistency across multiple runs
   - Monitor degradation over time

3. **Prompt Engineering**
   - Start simple, add complexity gradually
   - Use domain-specific examples
   - Define output format explicitly

4. **Model Selection**
   - Use fine-tuned BERT for extraction/classification
   - Use GPT-4o/ChatGPT for generation and QA
   - Consider computational cost vs performance

5. **Logging & Monitoring**
   - Log all API calls and token usage
   - Track success/failure rates
   - Monitor cost and performance trends

---

## Performance Monitoring

```python
# Get API usage statistics
stats = model.get_statistics()
print(f"Total calls: {stats['call_count']}")
print(f"Total tokens: {stats['total_tokens']}")
print(f"Avg tokens/call: {stats['avg_tokens_per_call']}")

# Get pipeline statistics
pipeline_stats = pipeline.get_pipeline_statistics()
print(f"Success rate: {pipeline_stats['success_rate']:.2%}")
print(f"Review queue: {pipeline_stats['review_queue_status']}")

# Generate report
report = pipeline.generate_report()
print(report)
```

---

## Troubleshooting

### Issue: API Key Not Found
**Solution**: Set environment variables or pass keys explicitly
```python
import os
os.environ['OPENAI_API_KEY'] = 'your_key'
```

### Issue: Low Model Performance
**Solution**: Try different prompt engineering strategies
```python
strategy = AppConfig.get_prompt_strategy("expert")
# Use comprehensive domain context and examples
```

### Issue: High False Positive Rate in NER
**Solution**: Use fine-tuned BERT instead of general LLM
```python
model = ModelFactory.create_model(ModelType.BERT)
```

---

## Future Enhancements

- [ ] Fine-tuning pipeline for custom models
- [ ] Multi-GPU support
- [ ] API rate limiting and caching
- [ ] Web UI for human review
- [ ] Advanced prompt optimization
- [ ] Requirement traceability tracking
- [ ] Integration with RE tools (ReqIF, Doors)
- [ ] Cost optimization strategies

---

## References

1. Ellsel, C., & Stark, R. (2025). Advancing Requirements Engineering with Large Language Models.
2. Wang, W., et al. (2025). TESTEVAL: Benchmarking Large Language Models for Test Case Generation.
3. Hemmat, A., et al. (2025). Research directions for using LLM in software requirement engineering.
4. Saleem, S., et al. (2025). Generative language models' potential for requirement engineering applications.

---

## License

MIT License

---

## Support

For issues, questions, or contributions, please refer to the documentation or contact the development team.

---

**Happy Requirements Engineering with AI!** 🚀
