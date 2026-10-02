# High-Level Design Document
## AI-Powered Requirements Engineering Tool

**Project:** AI Tool for Business Analyst and Test Engineer  
**Author:** Waseem Saleem Sayyed  
**Program:** MTech - Data Science & Artificial Intelligence (Sem 4)  
**Date:** October 2026  
**Version:** 1.0

---

## Executive Summary

This document presents the high-level design of an AI-powered Requirements Engineering (RE) tool that leverages Large Language Models (LLMs) and machine learning to automate and enhance various requirements engineering tasks. The tool processes requirements through an intelligent pipeline that classifies tasks, selects appropriate models, performs processing, and validates quality with optional human review.

The system integrates five different LLM models (BERT, GPT-4o, ChatGPT, Gemini, Claude) and supports seven critical RE tasks with performance baselines derived from peer-reviewed research in LLM applications for software engineering.

---

## 1. System Overview

### 1.1 Purpose and Scope

The AI Requirements Engineering Tool addresses the following challenges:
- **Automation:** Automate repetitive RE tasks including extraction, classification, entity recognition, and test case generation
- **Consistency:** Ensure consistent quality across large requirement sets using standardized processing
- **Enhancement:** Enhance human analysts' productivity by providing intelligent suggestions and automated validation
- **Scalability:** Process hundreds or thousands of requirements efficiently using distributed LLM models
- **Quality Assurance:** Implement multi-layered quality validation with human-in-the-loop capability

### 1.2 Key Stakeholders

| Stakeholder | Interest | Need |
|---|---|---|
| Business Analysts | Efficiency, Quality | Automated requirement processing |
| Test Engineers | Coverage, Traceability | Test case generation from requirements |
| Project Managers | Consistency, Compliance | Quality metrics and audit trails |
| System Designers | Scalability, Reliability | Production-ready system |

### 1.3 Success Criteria

- **Accuracy:** Achieve F1-scores matching or exceeding literature baselines
- **Performance:** Process requirements at enterprise scale (1000+ requirements/hour)
- **Reliability:** 99%+ uptime with graceful degradation
- **Usability:** Support both API and UI-based interactions
- **Auditability:** Maintain complete processing history and human decisions

---

## 2. System Architecture

### 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│          INPUT LAYER                                    │
│  Single/Batch/Dataset Requirements                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          PREPROCESSING LAYER                            │
│  Normalization, Validation, Format Conversion          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          TASK CLASSIFICATION                            │
│  Route to: Extraction | Classification | NER | QA...  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          MODEL SELECTION & ROUTING                      │
│  BERT | ChatGPT | GPT-4o | Gemini | Claude             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          PROCESSING LAYER                               │
│  Execute Task-Specific Processing                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          QUALITY VALIDATION LAYER                       │
│  Syntactic, Semantic, Consistency Checks               │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴─────────────┐
        │                          │
      PASS                        FAIL
        │                          │
        ▼                          ▼
   OUTPUT            HUMAN REVIEW QUEUE
```

### 2.2 Core Layers

#### 2.2.1 Input Layer
- **Single Requirement:** Process individual requirements
- **Batch Processing:** Handle multiple requirements in parallel
- **Dataset Upload:** Load and process complete datasets

**Key Components:**
- Input validation
- Format detection
- Requirement parsing

#### 2.2.2 Preprocessing Layer
- Text normalization (lowercase, punctuation handling)
- Stop word removal (optional)
- Tokenization
- Train/Validation/Test split for datasets
- Data augmentation for imbalanced classes

**Key Components:**
- DataLoaderFactory
- Dataset-specific loaders (Pure, PROMISE, Aerospace, REQuestA)
- Format converters

#### 2.2.3 Task Classification
Routes requirements to appropriate processing pipeline based on task type:

| Task | Input | Output | Complexity |
|------|-------|--------|-----------|
| **Extraction** | Raw requirement text | Structured entities | Medium |
| **Classification** | Requirement | Type category | Low |
| **NER** | Requirement text | Tagged entities | High |
| **QA** | Context + Question | Answer | Medium |
| **Test Generation** | Requirement | Test cases | High |
| **Quality Assessment** | Requirement | Quality score | Medium |
| **Specification** | Requirement | Formal spec | High |

#### 2.2.4 Model Selection Layer
Intelligent model selection based on:
- Task type
- Accuracy requirements
- Latency constraints
- Cost budget
- Hardware availability

**Model Performance Matrix:**

| Task | BERT | ChatGPT | Gemini | GPT-4o | Performance |
|------|------|---------|--------|--------|-------------|
| Extraction | 0.86 ✓ | 0.76 | - | - | Primary |
| Classification | 0.96 ✓ | 0.78 | 0.78 | - | Primary |
| NER | 0.92 ✓ | 0.36 | 0.25 | - | Primary |
| QA | - | 0.91 | 0.88 | 0.95 ✓ | Best |
| Test Gen | - | 0.90 | - | 0.986 ✓ | Primary |
| Quality | - | - | - | 0.695 ✓ | Primary |

#### 2.2.5 Processing Layer
Task-specific processing using selected model:

**BERT Model (Local/Fast):**
- Fine-tuned on domain data
- No API calls required
- Fast inference (milliseconds)
- Ideal for classification and NER

**LLM Models (API-based):**
- ChatGPT/GPT-4o/Gemini/Claude
- Complex reasoning
- Generation tasks
- Customizable prompts

#### 2.2.6 Quality Validation Layer
Multi-stage validation:

1. **Syntactic Validation**
   - Check output format correctness
   - Verify required fields present
   - Validate token limits

2. **Semantic Validation**
   - Cross-reference with requirements
   - Check logical consistency
   - Verify domain appropriateness

3. **Confidence Assessment**
   - Model confidence scores
   - Semantic similarity checks
   - Anomaly detection

4. **Threshold-based Routing**
   - If confidence >= threshold → OUTPUT
   - If confidence < threshold → HUMAN REVIEW

#### 2.2.7 Human-in-the-Loop (HIML)
For low-confidence results:
- Queue requirement for human review
- Analyst approves, rejects, or requests changes
- Feedback incorporated for model improvement
- Final decision recorded in audit trail

#### 2.2.8 Output Layer
- Structured result objects
- JSON/CSV export
- Database storage
- API response generation

---

## 3. Component Architecture

### 3.1 Core Modules

```
AIREToolBoilerplate/
├── main.py                  # Entry point & examples
├── config.py               # Configuration management
├── logger.py               # Logging infrastructure
├── data_loader.py          # Dataset loading
├── llm_interface.py        # LLM model abstractions
├── evaluation.py           # Metrics & evaluation
└── pipeline.py             # Main orchestration
```

#### 3.1.1 Configuration Module (config.py)

**Responsibilities:**
- Centralized configuration management
- Environment-based settings
- Model and dataset configurations
- Quality thresholds
- API credentials

**Key Classes:**
- `AppConfig` - Application-level settings
- `ModelConfig` - Model-specific settings
- `DatasetConfig` - Dataset configurations
- `PromptEngineeringConfig` - Prompt templates and strategies

#### 3.1.2 Data Loading Module (data_loader.py)

**Responsibilities:**
- Dataset loading and preprocessing
- Train/validation/test splitting
- Format normalization
- Data validation

**Supported Datasets:**
1. **PURE** (7,445 samples) - Requirements Extraction
   - CSV format with ID, text, entities
   - Domain: General software requirements

2. **PROMISE** (622 samples) - Classification
   - Binary/multi-class classification
   - Domain: Functional/non-functional requirements

3. **Aerospace** (6,347 words) - Named Entity Recognition
   - NER tags: Function, Component, Property
   - Domain: Aerospace systems

4. **REQuestA** (300 pairs) - Question Answering
   - QA pairs with context
   - Domain: Requirements understanding

**Key Classes:**
- `DataLoader` - Abstract base class
- `PureDataLoader` - PURE dataset implementation
- `PROMISEDataLoader` - PROMISE dataset implementation
- `AerospaceDataLoader` - Aerospace dataset implementation
- `REQuestADataLoader` - REQuestA dataset implementation
- `DataLoaderFactory` - Factory pattern for dataset creation

#### 3.1.3 LLM Interface Module (llm_interface.py)

**Responsibilities:**
- Abstract LLM model interface
- Model-specific implementations
- Request/response handling
- Token management and caching
- Error handling and retries

**Supported Models:**

1. **BERT (Local)**
   - Fine-tuned versions available
   - Tasks: Classification, NER, Extraction
   - Performance: F1 0.86-0.96
   - Latency: <100ms

2. **GPT-4o (OpenAI)**
   - Best for generation and QA
   - Tasks: Test generation, Quality assessment
   - Performance: F1 0.95+, Coverage 98.65%
   - Latency: 1-3 seconds

3. **ChatGPT (OpenAI)**
   - Good balance of cost/performance
   - Tasks: Classification, Extraction, QA
   - Performance: F1 0.76-0.91
   - Latency: 0.5-2 seconds

4. **Gemini (Google)**
   - Alternative to OpenAI
   - Tasks: Classification, Extraction, NER
   - Performance: F1 0.25-0.88
   - Latency: 1-3 seconds

5. **Claude (Anthropic)**
   - Advanced reasoning capabilities
   - Tasks: Quality assessment, Complex analysis
   - Performance: Variable
   - Latency: 1-3 seconds

**Key Classes:**
- `BaseLLMModel` - Abstract base class
- `BERTModel` - BERT implementation
- `GPT4OModel` - GPT-4o implementation
- `ChatGPTModel` - ChatGPT implementation
- `GeminiModel` - Gemini implementation
- `ClaudeModel` - Claude implementation
- `ModelFactory` - Factory for model creation
- `LLMResponse` - Standardized response object

#### 3.1.4 Evaluation Module (evaluation.py)

**Responsibilities:**
- Calculate performance metrics
- Generate reports
- Compare against baselines
- Export results

**Metric Categories:**

1. **Classification Metrics**
   - Precision, Recall, F1-score
   - Accuracy, Specificity
   - Confusion matrix, Cohen's Kappa

2. **Text Generation Metrics**
   - BLEU (Bilingual Evaluation Understudy)
   - ROUGE-L (Longest Common Subsequence)
   - Semantic similarity

3. **NER Metrics**
   - Entity-level metrics
   - Token-level metrics
   - Partial matching

4. **Test Coverage Metrics**
   - Line coverage
   - Branch coverage
   - Path coverage
   - Coverage@k

5. **Quality Assessment Metrics**
   - Completeness score
   - Consistency score
   - Ambiguity detection
   - Overall quality score

**Key Classes:**
- `EvaluationMetrics` - Base metrics calculation
- `ClassificationMetrics` - Classification-specific
- `TextGenerationMetrics` - Generation-specific
- `NEREvaluationMetrics` - NER-specific
- `TestCoverageMetrics` - Test coverage analysis
- `EvaluationReporter` - Report generation

#### 3.1.5 Pipeline Module (pipeline.py)

**Responsibilities:**
- Orchestrate end-to-end processing
- Task classification and routing
- Quality validation
- Human-in-the-loop management
- Result aggregation and reporting

**Key Classes:**
- `TaskClassifier` - Classify incoming requirements
- `QualityValidator` - Validate processing results
- `HumanInTheLoopQueue` - Manage review queue
- `REPipeline` - Main orchestrator

**Key Methods:**
- `process_requirement()` - Single requirement
- `process_batch()` - Batch processing
- `load_and_process_dataset()` - Full dataset
- `get_pipeline_statistics()` - Metrics
- `generate_report()` - Summary report

---

## 4. Data Flow

### 4.1 Single Requirement Processing

```
Input Requirement
    ↓
Normalize & Tokenize
    ↓
Classify Task Type
    ↓
Select Model
    ↓
Execute Task
    ↓
Calculate Confidence
    ↓
Validate Quality
    ↓
    ├─ PASS (Confidence ≥ Threshold)
    │   ↓
    │   Output Result (COMPLETED)
    │
    └─ FAIL (Confidence < Threshold)
        ↓
        Add to Review Queue (WAITING_REVIEW)
        ↓
        Human Review
        ├─ Approve → Output (APPROVED)
        ├─ Reject → Discard (REJECTED)
        └─ Revise → Reprocess
```

### 4.2 Batch Processing

```
Batch Input [REQ1, REQ2, ..., REQn]
    ↓
[Parallel Processing]
├─ Process REQ1 ──┐
├─ Process REQ2  ├─ Pipeline
├─ ...           │
└─ Process REQn ──┘
    ↓
Collect Results
    ├─ Completed: n1
    ├─ Failed: n2
    └─ Pending Review: n3
    ↓
Calculate Batch Statistics
```

### 4.3 Dataset Processing

```
Dataset Upload
    ↓
Load & Preprocess
    ↓
Split Data (Train/Val/Test)
    ↓
Process Each Split
    ├─ Training: Collect baselines
    ├─ Validation: Evaluate performance
    └─ Test: Final assessment
    ↓
Generate Evaluation Report
```

---

## 5. System Design Decisions

### 5.1 Architecture Patterns

**1. Factory Pattern (Model & Dataset Selection)**
- Benefits: Extensibility, loose coupling
- Implementation: ModelFactory, DataLoaderFactory
- Extension: Easy to add new models/datasets

**2. Strategy Pattern (Task Processing)**
- Benefits: Runtime algorithm selection
- Implementation: Task-specific processors
- Extension: Easy to add new RE tasks

**3. Template Method (Data Loading)**
- Benefits: Consistent interface, shared logic
- Implementation: DataLoader abstract base
- Extension: Dataset-specific implementations

**4. Observer Pattern (Human-in-the-Loop)**
- Benefits: Event-driven processing
- Implementation: Review queue notifications
- Extension: Webhook callbacks for external systems

### 5.2 Technology Choices

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Base Model | BERT | Fast, accurate for classification/NER |
| API Models | OpenAI, Google, Anthropic | SOTA performance, enterprise support |
| Language | Python 3.9+ | ML ecosystem, readability |
| Config | YAML/Python | Flexible, environment-aware |
| Logging | Python logging | Built-in, production-ready |
| Testing | pytest | Standard in Python community |
| Deployment | Docker/Cloud | Scalability, reproducibility |

### 5.3 Performance Optimization

**1. Caching Strategy**
- Cache model instances (BERT)
- Cache LLM responses for similar requirements
- Use Redis for distributed caching

**2. Batching**
- Process multiple requirements per LLM call
- Reduces API overhead
- Improves token efficiency

**3. Model Selection**
- Use BERT for high-volume, low-latency tasks
- Use LLMs for complex, generation-heavy tasks
- Implement fallback chains for reliability

**4. Parallel Processing**
- Process batch requirements in parallel
- Thread pool for I/O-bound operations
- Async for LLM API calls

---

## 6. Quality Assurance

### 6.1 Quality Validation Layers

```
Level 1: Syntactic Validation
├─ Format correctness
├─ Required fields present
└─ Token limits

Level 2: Semantic Validation
├─ Cross-requirement consistency
├─ Domain appropriateness
└─ Logical coherence

Level 3: Confidence Assessment
├─ Model confidence scores
├─ Semantic similarity
└─ Anomaly detection

Level 4: Human Review (if needed)
├─ Expert validation
├─ Feedback collection
└─ Continuous improvement
```

### 6.2 Quality Metrics

- **Accuracy:** Match against gold standards
- **Precision/Recall:** Comprehensive evaluation
- **F1-Score:** Balanced metric
- **Confidence Calibration:** Predict uncertainty correctly
- **Coverage:** Completeness of processing

### 6.3 Quality Thresholds

| Task | Model | Threshold | Fallback |
|------|-------|-----------|----------|
| Classification | BERT | 0.9 | ChatGPT (0.8) |
| Extraction | BERT | 0.85 | GPT-4o (0.95) |
| NER | BERT | 0.88 | Manual review |
| QA | GPT-4o | 0.92 | Human review |
| Test Gen | GPT-4o | 0.90 | Manual validation |

---

## 7. Security & Privacy

### 7.1 Data Protection

- **API Keys:** Store in environment variables, never in code
- **Encrypted Communication:** HTTPS for all API calls
- **Data Retention:** Define retention policies per dataset
- **Audit Logging:** Log all model decisions and human reviews

### 7.2 Model Security

- **Version Control:** Track model versions and updates
- **Access Control:** Restrict access to production models
- **Input Validation:** Sanitize all inputs before processing
- **Output Filtering:** Remove sensitive data from outputs

### 7.3 Deployment Security

- **Container Hardening:** Minimal Docker images
- **Network Segmentation:** Restrict API access
- **Rate Limiting:** Prevent abuse
- **Monitoring:** Track anomalies and errors

---

## 8. Scalability & Performance

### 8.1 Scalability Dimensions

**Horizontal:**
- Distribute processing across multiple workers
- Batch requirements for load balancing
- Use message queues (Celery, RabbitMQ)

**Vertical:**
- Optimize model inference
- Implement caching layers
- Use GPU acceleration for BERT

### 8.2 Performance Targets

| Task | Throughput | Latency | Accuracy |
|------|-----------|---------|----------|
| Classification | 1000/hour | <100ms | F1=0.96 |
| Extraction | 500/hour | <200ms | F1=0.86 |
| NER | 400/hour | <250ms | F1=0.92 |
| QA | 200/hour | <1s | F1=0.95 |
| Test Gen | 100/hour | <3s | 98.65% coverage |
| Quality | 300/hour | <1s | Acc=69.55% |

### 8.3 Resource Requirements

- **CPU:** 4+ cores for parallel processing
- **Memory:** 8GB+ for BERT and LLM pipeline
- **Storage:** 2GB+ for models and datasets
- **Network:** High-bandwidth for LLM APIs

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- ✓ Core module implementation
- ✓ Configuration management
- ✓ Data loading framework

### Phase 2: LLM Integration (Weeks 3-4)
- ✓ BERT model integration
- ✓ LLM API wrappers
- ✓ Model factory

### Phase 3: RE Tasks (Weeks 5-6)
- ✓ Implement 7 RE tasks
- ✓ Task classification
- ✓ Model selection

### Phase 4: Quality & Validation (Weeks 7-8)
- ✓ Quality validator
- ✓ Human-in-the-loop
- ✓ Evaluation metrics

### Phase 5: Deployment (Weeks 9-10)
- REST API wrapper
- Web UI
- Production deployment

---

## 10. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| LLM API unavailability | High | Fallback models, local caching |
| Poor model accuracy | High | Fine-tuning, prompt engineering |
| High token costs | Medium | Caching, BERT for low-cost tasks |
| Privacy concerns | High | On-premise deployment option |
| Integration complexity | Medium | Well-documented APIs, examples |

---

## 11. Success Metrics

### Technical Metrics
- **Accuracy:** F1 scores ≥ literature baselines
- **Latency:** <1s per requirement (target)
- **Throughput:** 1000+ requirements/hour
- **Availability:** 99%+ uptime

### Business Metrics
- **Productivity:** 5x faster requirement processing
- **Quality:** Consistent across large datasets
- **Cost:** Efficient LLM usage through caching
- **User Satisfaction:** >90% approval rate

---

## 12. Conclusion

This high-level design provides a robust, scalable foundation for an AI-powered Requirements Engineering tool. The modular architecture allows for easy extension, the multi-model approach ensures optimal performance across diverse tasks, and the human-in-the-loop mechanism maintains quality and oversight.

The system successfully integrates state-of-the-art LLM technologies with proven machine learning practices to create a production-ready platform for enterprise requirements engineering.

---

**Document Version:** 1.0  
**Last Updated:** October 2026  
**Next Review:** December 2026
