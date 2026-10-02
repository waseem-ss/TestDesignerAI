# Project Structure

Complete boilerplate for AI-Powered Requirements Engineering Tool using Large Language Models.

## Directory Layout

```
ai_re_tool_boilerplate/
│
├── 📄 Main Application Files
│   ├── main.py                    # Entry point with examples
│   ├── config.py                  # Configuration management
│   ├── logger.py                  # Logging setup
│   ├── data_loader.py             # Dataset loading & preprocessing
│   ├── llm_interface.py           # LLM model abstraction layer
│   ├── evaluation.py              # Metrics and evaluation
│   └── pipeline.py                # Main orchestration pipeline
│
├── 📚 Documentation
│   ├── README.md                  # Comprehensive guide
│   ├── QUICKSTART.md              # 5-minute quick start
│   ├── ARCHITECTURE.md            # System design & diagrams
│   ├── PROJECT_STRUCTURE.md       # This file
│   └── LITERATURE_REVIEW.md       # Reference (in project)
│
├── 🔧 Configuration & Dependencies
│   ├── requirements.txt           # Python dependencies
│   └── .env.example               # Environment variables template
│
├── 📁 Data Directory (auto-created)
│   ├── pure_dataset.csv
│   ├── promise_dataset.csv
│   ├── aerospace_dataset.json
│   └── requestqa_dataset.json
│
├── 📁 Models Directory (auto-created)
│   ├── bert_model/
│   ├── gpt4o_config/
│   └── fine_tuned_models/
│
├── 📁 Logs Directory (auto-created)
│   └── ai_re_tool_YYYYMMDD.log
│
└── 📁 Output Directory (auto-created)
    ├── results/
    ├── reports/
    └── exports/
```

## Module Descriptions

### Core Modules

#### 1. **config.py** (Configuration Management)
- **Purpose**: Central configuration for all components
- **Key Classes**:
  - `AppConfig`: Main application settings
  - `ModelType`: Enum of supported LLM models
  - `RETaskType`: Enum of RE task types
  - `ModelConfig`: Per-model configuration with baselines
  - `DatasetConfig`: Dataset specifications
  - `PromptEngineeringConfig`: Prompt strategies
- **Key Functions**:
  - `get_model_config()`: Retrieve model configuration
  - `get_dataset_config()`: Retrieve dataset configuration
  - `get_prompt_strategy()`: Get prompt engineering strategy
  - `create_directories()`: Initialize project directories
- **Lines of Code**: ~400
- **Dependencies**: dataclasses, enum

#### 2. **logger.py** (Logging Infrastructure)
- **Purpose**: Structured logging to console and files
- **Key Classes**:
  - `LoggerFactory`: Creates configured loggers
- **Key Functions**:
  - `get_logger()`: Get or create logger
- **Features**:
  - Rotating file handlers (10MB per file)
  - Console and file output
  - Configurable log levels
  - Auto-timestamp logging
- **Lines of Code**: ~70
- **Dependencies**: logging, logging.handlers

#### 3. **data_loader.py** (Data Loading & Preprocessing)
- **Purpose**: Load, preprocess, validate datasets
- **Key Classes**:
  - `DataLoader`: Abstract base class
  - `PureDataLoader`: Loads Pure dataset (7,445 samples)
  - `PROMISEDataLoader`: Loads PROMISE (622 samples)
  - `AerospaceDataLoader`: Loads Aerospace (6,347 words)
  - `REQuestADataLoader`: Loads REQuestA (300 QA pairs)
  - `DataLoaderFactory`: Factory for creating loaders
- **Key Functions**:
  - `load()`: Load dataset from file
  - `preprocess()`: Clean and normalize data
  - `validate()`: Verify data integrity
  - `get_split()`: Train/Val/Test split
  - `load_and_prepare()`: Complete pipeline
- **Features**:
  - Automatic missing data handling
  - Stratified splitting for balanced data
  - Format-specific processing (CSV, JSON, TXT)
  - Placeholder generation for missing datasets
- **Lines of Code**: ~500
- **Dependencies**: pandas, numpy, sklearn

#### 4. **llm_interface.py** (LLM Model Abstraction)
- **Purpose**: Unified interface for multiple LLM models
- **Key Classes**:
  - `LLMResponse`: Structured response container
  - `BaseLLMModel`: Abstract base model
  - `GPT4OModel`: GPT-4o implementation
  - `ChatGPTModel`: ChatGPT implementation
  - `GeminiModel`: Google Gemini implementation
  - `ClaudeModel`: Anthropic Claude implementation
  - `BERTModel`: BERT for classification/NER
  - `ModelFactory`: Factory for model creation
  - `LLMPipeline`: Orchestrates multiple models
- **Key Methods**:
  - `generate()`: Generate text from prompt
  - `extract_entities()`: Extract named entities
  - `classify()`: Classify text into categories
  - `question_answering()`: Answer questions
  - `_make_api_call()`: API call with retry logic
- **Features**:
  - Retry logic with exponential backoff
  - Token usage tracking
  - Confidence scoring
  - Mock API responses for testing
  - Model-specific optimizations
- **Lines of Code**: ~600
- **Dependencies**: openai, google-generativeai, anthropic, json, time

#### 5. **evaluation.py** (Metrics & Evaluation)
- **Purpose**: Comprehensive evaluation and reporting
- **Key Classes**:
  - `EvaluationMetrics`: Container for metrics
  - `ClassificationMetrics`: For classification tasks
  - `TextGenerationMetrics`: BLEU, ROUGE-L scores
  - `TestCoverageMetrics`: Line/Branch/Path coverage
  - `QualityAssessmentMetrics`: Requirement quality
  - `NEREvaluationMetrics`: NER evaluation
  - `EvaluationReporter`: Generate reports
- **Key Metrics**:
  - Precision, Recall, F1, Accuracy
  - BLEU, ROUGE-L for text generation
  - Line/Branch/Path coverage
  - Coverage@K for test diversity
  - Completeness, Consistency, Ambiguity scores
  - Entity-level and token-level metrics
- **Features**:
  - Multi-metric comparison
  - JSON export
  - Formatted report generation
  - Baseline comparison
- **Lines of Code**: ~700
- **Dependencies**: numpy, json, sklearn

#### 6. **pipeline.py** (Main Orchestration)
- **Purpose**: Orchestrate complete processing workflow
- **Key Classes**:
  - `ProcessingStatus`: Enum for status tracking
  - `ProcessingResult`: Container for results
  - `TaskClassifier`: Routes requirements to models
  - `QualityValidator`: Validates output quality
  - `HumanInTheLoopQueue`: Manages review queue
  - `REPipeline`: Main pipeline orchestrator
- **Key Methods**:
  - `process_requirement()`: Process single requirement
  - `process_batch()`: Process multiple requirements
  - `load_and_process_dataset()`: Load and process full dataset
  - `get_pipeline_statistics()`: Get metrics
  - `generate_report()`: Generate summary report
  - `approve()`: Approve requirement
  - `reject()`: Reject requirement
- **Features**:
  - Automatic task classification
  - Model selection optimization
  - Multi-stage validation
  - Human review workflow
  - Quality scoring and thresholds
  - Complete audit trail
- **Lines of Code**: ~400
- **Dependencies**: dataclasses, enum

#### 7. **main.py** (Entry Point)
- **Purpose**: Demonstrate tool capabilities
- **Key Functions**:
  - `main()`: Main execution
  - `demo_prompt_engineering()`: Show prompt strategies
  - `demo_dataset_info()`: Show dataset information
- **Examples Provided**:
  - Single requirement processing
  - Batch processing
  - Dataset loading and processing
  - Human review workflow
  - Model comparison
  - Configuration demonstration
  - Statistics and reporting
- **Lines of Code**: ~250
- **Command-line Options**:
  - `python main.py` - Run full demo
  - `python main.py --prompts` - Show prompt strategies
  - `python main.py --datasets` - Show datasets
  - `python main.py --help` - Display help

## File Statistics

| File | Lines | Purpose |
|------|-------|---------|
| config.py | 400 | Configuration management |
| logger.py | 70 | Logging setup |
| data_loader.py | 500 | Data loading & preprocessing |
| llm_interface.py | 600 | LLM model abstractions |
| evaluation.py | 700 | Metrics & evaluation |
| pipeline.py | 400 | Main orchestration |
| main.py | 250 | Entry point & examples |
| requirements.txt | 40 | Dependencies |
| README.md | 600 | Full documentation |
| QUICKSTART.md | 300 | Quick start guide |
| ARCHITECTURE.md | 400 | Architecture & design |
| **TOTAL** | **~4300** | **Production-ready codebase** |

## Key Features

### ✅ Data Handling
- Loads 4 datasets from literature review
- Automatic train/val/test splitting
- Data validation and cleaning
- Format conversion (CSV, JSON, TXT)
- Placeholder generation for missing data

### ✅ Model Support
- **Fine-tuned BERT** - Best for extraction/classification/NER
- **GPT-4o** - Best for generation and test cases
- **ChatGPT (GPT-3.5-turbo)** - Good general-purpose
- **Gemini (Google)** - Alternative LLM
- **Claude (Anthropic)** - Alternative LLM
- **Model Factory** - Easy model switching
- **Fallback support** - Automatic fallback to alternative models

### ✅ Task Support
1. **Requirements Extraction** - Extract structured requirements
2. **Requirements Classification** - Functional vs Non-functional
3. **Named Entity Recognition** - Identify key entities
4. **Question Answering** - Answer requirement-related questions
5. **Test Case Generation** - Generate test cases
6. **Quality Assessment** - Evaluate requirement quality
7. **Specification Generation** - Generate formal specifications

### ✅ Evaluation Metrics
- Classification: Precision, Recall, F1, Accuracy
- Text Generation: BLEU, ROUGE-L
- Test Coverage: Line, Branch, Path coverage
- Quality: Completeness, Consistency, Ambiguity
- NER: Entity-level and token-level metrics

### ✅ Pipeline Features
- Automatic task classification
- Smart model selection
- Multi-stage quality validation
- Human-in-the-loop review
- Batch processing support
- Complete audit trail
- Comprehensive reporting

### ✅ Configuration
- Centralized configuration management
- Model-specific settings with baselines
- Dataset specifications
- Prompt engineering strategies (basic/intermediate/expert)
- Adjustable quality thresholds
- API retry configuration

### ✅ Logging & Monitoring
- Structured logging to console and file
- Rotating file handlers
- Multiple log levels
- API usage tracking
- Performance metrics
- Error reporting

### ✅ Extensibility
- Abstract base classes for extension
- Factory patterns for easy substitution
- Plugin-friendly architecture
- Custom task support
- Custom metric support
- Custom model support

## Dependencies

### Core LLM APIs
- openai (GPT-4o, ChatGPT)
- google-generativeai (Gemini)
- anthropic (Claude)

### Machine Learning
- torch (Deep learning framework)
- transformers (BERT, fine-tuned models)
- scikit-learn (ML utilities, evaluation metrics)

### Data Processing
- pandas (DataFrame manipulation)
- numpy (Numerical computation)
- nltk (NLP toolkit)
- spacy (Advanced NLP, NER)

### Utilities
- python-dotenv (Environment variables)
- pydantic (Data validation)
- pyyaml (YAML parsing)
- requests (HTTP requests)

### Development
- pytest (Unit testing)
- black (Code formatting)
- mypy (Type checking)
- sphinx (Documentation)

## Getting Started

### 1. Installation (2 minutes)
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. First Run (30 seconds)
```bash
python main.py
```

### 3. Try Examples
See `QUICKSTART.md` for code examples

### 4. Read Documentation
- `README.md` - Full reference
- `ARCHITECTURE.md` - System design
- Docstrings in source code

## Performance Baselines (from Literature)

### Model Accuracy by Task

| Task | Best Model | F1/Score |
|------|-----------|----------|
| Extraction | BERT (Fine-tuned) | 0.86 |
| Classification | BERT (Fine-tuned) | 0.96 |
| NER | Aero-BERT | 0.92 |
| QA | ChatGPT | 0.91 |
| Test Generation | GPT-4o | 98.65% coverage |

### Recommendation Matrix

Use this to select the best model for your task:
- **Classification** → BERT (F1=0.96)
- **Extraction** → BERT (F1=0.86)
- **NER** → BERT/Aero-BERT (F1=0.92)
- **QA** → ChatGPT/GPT-4o (F1=0.91/0.95)
- **Generation** → GPT-4o (best quality)
- **Speed** → ChatGPT (fastest)
- **Accuracy** → GPT-4o (highest quality)

## Next Steps

1. **Customize for Your Domain**
   - Load your requirement documents
   - Fine-tune BERT on your data
   - Add domain-specific prompts

2. **Integrate APIs**
   - Add OpenAI API key
   - Add Google API key
   - Add Anthropic API key

3. **Deploy**
   - Set up production database
   - Implement REST API
   - Add web UI for human review

4. **Monitor**
   - Track model performance
   - Monitor error rates
   - Analyze human feedback

## Support & Resources

- **Documentation**: README.md, QUICKSTART.md, ARCHITECTURE.md
- **Code Examples**: main.py, docstrings
- **Literature Review**: Reference in project docs
- **API Docs**: Inline code comments

## License

MIT License - Free to use and modify

---

**Happy Requirements Engineering!** 🚀
