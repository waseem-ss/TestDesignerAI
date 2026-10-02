# System Architecture

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AI-POWERED REQUIREMENTS ENGINEERING TOOL             │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                                      │
├──────────────────────────────────────────────────────────────────────────┤
│  • Single Requirement  • Batch Requirements  • Dataset Upload            │
└──────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      PREPROCESSING LAYER                                 │
├──────────────────────────────────────────────────────────────────────────┤
│  • Data Loader Factory  • Text Normalization  • Validation               │
│  • Train/Val/Test Split • Format Conversion                              │
└──────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    TASK CLASSIFICATION                                   │
├──────────────────────────────────────────────────────────────────────────┤
│  Route to: Extraction | Classification | NER | QA | Test Generation     │
└──────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    MODEL SELECTION & ROUTING                             │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────────┐      │
│  │ Fine-tuned  │  │ ChatGPT /    │  │ Gemini   │  │ GPT-4o       │      │
│  │ BERT        │  │ GPT-3.5      │  │ (Google) │  │ (OpenAI)     │      │
│  └─────────────┘  └──────────────┘  └──────────┘  └──────────────┘      │
│  └──────────────┐  ┌──────────────────────────────────────────────┘      │
│                 │  │                                                      │
│  ┌──────────────┐  │  ┌──────────────┐                                   │
│  │ Claude       │  │  │ Model Factory│                                   │
│  │ (Anthropic)  │  │  └──────────────┘                                   │
│  └──────────────┘  │                                                      │
│                    └────────────────────────────────────────────────┐    │
└──────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    LLM PROCESSING PIPELINE                               │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │ Extract      │  │ Classify     │  │ Quality      │                   │
│  │ Entities     │  │ Type         │  │ Assessment   │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │ NER Tagging  │  │ QA System    │  │ Test Gen     │                   │
│  │              │  │              │  │              │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
└──────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    QUALITY VALIDATION LAYER                              │
├──────────────────────────────────────────────────────────────────────────┤
│  • Syntactic Validation   • Semantic Validation                          │
│  • Confidence Scoring     • Consistency Checking                         │
│  • Domain Appropriateness Check                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  Quality Acceptable?   │
                    └────────────────────────┘
                       │               │
                   YES │               │ NO
                       ▼               ▼
            ┌───────────────────┐  ┌──────────────────┐
            │ Output Result     │  │ Human Review     │
            │ (COMPLETED)       │  │ Queue            │
            └───────────────────┘  │ (WAITING_REVIEW) │
                                   └──────────────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │  Human Review       │
                            │  - Approve          │
                            │  - Reject           │
                            │  - Request Changes  │
                            └──────────────────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │ Final Output         │
                            │ (APPROVED/REJECTED)  │
                            └──────────────────────┘
```

## Detailed Component Architecture

### 1. Configuration Layer (`config.py`)

```
AppConfig
├── Directory Configuration
│   ├── PROJECT_ROOT
│   ├── DATA_DIR
│   ├── MODELS_DIR
│   ├── LOGS_DIR
│   └── OUTPUT_DIR
├── API Configuration
│   ├── DEFAULT_MODEL
│   ├── FALLBACK_MODELS
│   ├── API_TIMEOUT
│   └── MAX_RETRIES
├── Processing Configuration
│   ├── BATCH_SIZE
│   ├── VALIDATION_SPLIT
│   └── TEST_SPLIT
├── Quality Assurance
│   ├── QUALITY_THRESHOLD
│   ├── HUMAN_REVIEW_THRESHOLD
│   └── CONSISTENCY_CHECK_ENABLED
└── Human-in-the-Loop
    ├── HIML_ENABLED
    └── HIML_REVIEW_QUEUE_SIZE

ModelConfig
├── Model Type (GPT-4o, ChatGPT, Gemini, Claude, BERT)
├── Task Suitability
├── Baseline Performance
├── Max Tokens
├── Temperature
└── API Key Environment Variable

DatasetConfig
├── Pure (7,445 samples - Extraction)
├── PROMISE (622 samples - Classification)
├── Aerospace (6,347 words - NER)
└── REQuestA (300 pairs - QA)

PromptEngineeringConfig
├── Strategy Level (basic/intermediate/expert)
├── Include Examples
├── Use Chain-of-Thought
├── Domain Context
└── Output Format
```

### 2. Data Loading Layer (`data_loader.py`)

```
DataLoader (Abstract Base)
├── PureDataLoader
│   ├── load() - Load CSV dataset
│   ├── preprocess() - Clean & normalize
│   ├── validate() - Verify data integrity
│   └── get_split() - Train/Val/Test split
├── PROMISEDataLoader
│   ├── Stratified splitting
│   ├── Class balancing
│   └── Type validation
├── AerospaceDataLoader
│   ├── NER entity validation
│   ├── Token-level processing
│   └── Annotation handling
└── REQuestADataLoader
    ├── QA pair validation
    ├── Context verification
    └── Answer validation

DataLoaderFactory
└── create_loader(dataset_config) → Specific DataLoader
```

### 3. LLM Interface Layer (`llm_interface.py`)

```
BaseLLMModel (Abstract Base)
├── GPT4OModel
│   ├── generate() - Best for generation & QA
│   ├── extract_entities()
│   ├── classify()
│   └── question_answering() - Strongest QA (F1=0.91)
├── ChatGPTModel
│   ├── generate()
│   ├── extract_entities() - F1=0.76
│   ├── classify() - F1=0.78
│   └── question_answering() - F1=0.91
├── GeminiModel
│   ├── generate()
│   ├── extract_entities() - F1=0.77
│   ├── classify() - F1=0.78
│   └── question_answering() - F1=0.88
├── ClaudeModel
│   ├── generate()
│   ├── extract_entities()
│   ├── classify()
│   └── question_answering()
└── BERTModel
    ├── extract_entities() - F1=0.92 (Aero-BERT)
    ├── classify() - F1=0.96 (fine-tuned)
    └── question_answering() - Extractive QA

LLMResponse
├── content - Generated response
├── model - Model used
├── tokens_used - Token count
├── confidence - Confidence score
└── timestamp - Processing time

ModelFactory
└── create_model(model_type) → Specific Model
└── create_best_model_for_task(task_type) → Optimal Model

LLMPipeline
├── process_requirement() - Process through multiple tasks
├── models - Cached model instances
└── results_cache - Cached responses
```

### 4. Evaluation Layer (`evaluation.py`)

```
EvaluationMetrics
├── precision
├── recall
├── f1_score
├── accuracy
├── confidence_score
└── additional_metrics

ClassificationMetrics
├── calculate_metrics(y_true, y_pred) - Binary classification
├── multilabel_metrics() - Multilabel classification
└── Cohen's Kappa, confusion matrix

TextGenerationMetrics
├── bleu_score() - N-gram based
├── rouge_l_score() - LCS based
├── bleu_batch()
└── rouge_batch()

TestCoverageMetrics
├── line_coverage()
├── branch_coverage()
├── path_coverage()
├── cov@k() - Diversity metric
└── coverage_comparison()

QualityAssessmentMetrics
├── completeness_score() - Checks structure
├── consistency_score() - Cross-requirement consistency
├── ambiguity_score() - Detects ambiguous language
└── overall_quality_score()

NEREvaluationMetrics
├── entity_level_metrics() - Whole entity comparison
└── token_level_metrics() - Token-wise comparison

EvaluationReporter
├── generate_report() - Formatted text report
└── export_metrics_json() - JSON export
```

### 5. Pipeline Orchestration Layer (`pipeline.py`)

```
TaskClassifier
├── classify_task(requirement_text) - Route to RE task
└── select_models(task_type) - Choose best models

QualityValidator
├── validate_extraction()
├── validate_classification()
├── validate_quality_assessment()
└── needs_human_review()

HumanInTheLoopQueue
├── add_to_queue() - Add for review
├── approve() - Approve requirement
├── reject() - Reject requirement
├── get_queue_status() - Queue statistics
├── approved - Approved requirements
├── rejected - Rejected requirements
└── queue - Pending review

REPipeline (Main Orchestrator)
├── process_requirement() - Single requirement
├── process_batch() - Multiple requirements
├── load_and_process_dataset() - Full dataset
├── get_pipeline_statistics() - Metrics
├── generate_report() - Summary report
├── classifier - TaskClassifier instance
├── validator - QualityValidator instance
├── review_queue - HumanInTheLoopQueue instance
├── llm_pipeline - LLMPipeline instance
└── results - Processed results
```

## Data Flow

### Single Requirement Processing Flow

```
Input Requirement
       │
       ▼
   Tokenize & Normalize
       │
       ▼
   Classify Task Type
       │
       ├─ Extraction ───→ BERT Model
       ├─ Classification ─→ BERT Model
       ├─ NER ──────────→ BERT/Aero-BERT
       ├─ QA ──────────→ GPT-4o/ChatGPT
       ├─ Test Gen ────→ GPT-4o
       └─ Quality Assess ──→ GPT-4o
       │
       ▼
   Execute Task
       │
       ├─ Extract Results
       ├─ Calculate Confidence
       └─ Get Quality Scores
       │
       ▼
   Validate Quality
       │
       ├─ Syntactic Check
       ├─ Semantic Check
       └─ Confidence Threshold
       │
       ├─ PASS ──────→ Status: COMPLETED
       │
       └─ FAIL ──────→ Add to Review Queue
                              │
                              ▼
                          Human Review
                              │
                              ├─ Approve ──→ Status: APPROVED
                              │
                              └─ Reject ───→ Status: REJECTED
```

### Batch Processing Flow

```
Batch of Requirements [REQ1, REQ2, ..., REQn]
       │
       ▼
   [Parallel Processing]
   ├─ Process REQ1 ─────┐
   ├─ Process REQ2 ─────┤ Pipeline
   ├─ ...               │
   └─ Process REQn ─────┘
       │
       ▼
   Collect Results
       │
       ├─ Completed: n1
       ├─ Failed: n2
       └─ Waiting Review: n3
       │
       ▼
   Calculate Statistics
       │
       ├─ Success Rate
       ├─ Average Confidence
       ├─ Coverage Metrics
       └─ Error Analysis
```

## API Call Sequence

```
Client Application
       │
       ├─ pipeline.process_requirement("REQ_001", text)
       │       │
       │       ├─ classifier.classify_task(text)
       │       ├─ ModelFactory.create_model(model_type)
       │       ├─ model.extract_entities(text)
       │       ├─ model.classify(text, categories)
       │       ├─ model.question_answering(context, question)
       │       │
       │       ├─ validator.validate_extraction(result)
       │       ├─ validator.needs_human_review(scores)
       │       │
       │       └─ review_queue.add_to_queue(result)
       │
       └─ Return ProcessingResult

ProcessingResult
├── requirement_id
├── input_text
├── status (COMPLETED / WAITING_REVIEW / FAILED)
├── extraction_result
├── classification_result
├── quality_assessment
├── human_review_required
├── confidence_scores
└── errors
```

## Performance & Scalability

### Model Performance (from Literature Review)

```
Task                Method          F1/Score    Suitable
─────────────────────────────────────────────────────
Extraction          BERT (FT)       0.86        ✓ Primary
                    ChatGPT         0.76        ✗ Secondary

Classification      BERT (FT)       0.96        ✓ Primary
                    ChatGPT/Gemini  0.78        ✗ Secondary

NER                 Aero-BERT       0.92        ✓ Primary
                    ChatGPT         0.36        ✗ Not suitable
                    Gemini          0.25        ✗ Not suitable

QA                  ChatGPT         0.91        ✓ Primary
                    Gemini          0.88        ✓ Primary
                    GPT-4o          0.95+       ✓ Best

Test Coverage       GPT-4o          98.65%      ✓ Best
                    ChatGPT         90.23%      ✓ Secondary

Quality Assess      GPT-4o          69.55%      ✓ Primary
```

### Scalability Considerations

1. **Batch Processing**
   - Process up to `BATCH_SIZE` requirements in parallel
   - Reduce per-request overhead
   - Optimize token usage

2. **Caching**
   - Cache similar requirement responses
   - Reduce API calls
   - Improve latency

3. **Model Selection**
   - Use faster models (BERT) when accuracy permits
   - Fall back to GPT-4o for complex tasks
   - Implement early stopping

4. **Queue Management**
   - Limit review queue size to prevent memory issues
   - Implement batch review workflow
   - Archive completed reviews

## Security Considerations

1. **API Keys**
   - Store in environment variables
   - Never commit to version control
   - Rotate regularly

2. **Data Privacy**
   - Consider on-premise model deployment for sensitive data
   - Implement audit logging
   - Use HTTPS for API calls

3. **Rate Limiting**
   - Implement token bucket algorithm
   - Respect API rate limits
   - Queue overload requests

4. **Error Handling**
   - Graceful degradation
   - Fallback models
   - Comprehensive logging

## Extension Points

1. **Custom Models**
   - Implement `BaseLLMModel` interface
   - Register in `ModelFactory`
   - Add performance baselines to config

2. **Custom Tasks**
   - Extend `RETaskType` enum
   - Create specialized `DataLoader`
   - Implement evaluation metrics

3. **Custom Evaluation**
   - Create custom metric classes
   - Extend `EvaluationMetrics`
   - Integrate into pipeline

4. **Custom UI**
   - Build REST API wrapper
   - Implement web interface
   - Add visualization components

---

This architecture provides a flexible, scalable, and production-ready system for AI-powered requirements engineering.
