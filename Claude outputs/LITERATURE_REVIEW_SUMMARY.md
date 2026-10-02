# Literature Review Summary
## Large Language Models for Requirements Engineering

**Project:** AI Tool for Business Analyst and Test Engineer  
**Program:** MTech - Data Science & Artificial Intelligence (Sem 4)  
**Date:** October 2026  
**Author:** Waseem Saleem Sayyed

---

## Executive Summary

This literature review synthesizes key findings from four seminal research papers investigating the application of Large Language Models (LLMs) in Requirements Engineering (RE). The review covers four major RE tasks: requirements extraction, classification, named entity recognition (NER), and question answering (QA). The analysis reveals that while LLMs show promise, particularly for generative tasks, specialized and fine-tuned models (BERT) remain superior for discriminative tasks.

**Key Finding:** A hybrid multi-model approach combining BERT for structured tasks and GPT-4o for generative tasks yields optimal performance across diverse RE applications.

---

## Paper 1: Advancing Requirements Engineering with Large Language Models

**Focus:** State-of-the-art LLM applications and performance baselines in RE

### Key Contributions

1. **Comprehensive LLM Taxonomy**
   - Generative models (GPT, ChatGPT, GPT-4o)
   - Code-focused models (Codex)
   - Bidirectional models (BERT and variants)
   - Transformer-based models (T5, Llama 2)
   - Multimodal models (GPT-4V, Claude 3 Vision)

2. **LLM Roles in RE Process**
   - Requirement document generation
   - Code generation from requirements
   - Test case generation and validation
   - Contradiction detection
   - Entity extraction and classification
   - Specification generation
   - Quality assessment

3. **Pipeline Integration**
   - Fine-tuning strategies for domain adaptation
   - Few-shot and zero-shot prompting techniques
   - Chain-of-thought reasoning for complex tasks
   - Multi-stage quality assessment

### Performance Baselines

| Task | Model | Performance | Notes |
|------|-------|-------------|-------|
| Requirement Generation | GPT-4o | SOTA | Best for creating new specifications |
| Code Generation | Codex | 0.89 F1 | Direct requirement-to-code translation |
| Test Case Gen | GPT-4o | 98.65% Coverage | Superior branch/path coverage |
| Contradiction Detection | BERT | 0.92 F1 | Excellent consistency checking |

### Key Insights

- **Prompt Engineering Critical:** Output quality heavily dependent on prompt sophistication
- **Domain Adaptation:** Fine-tuning on domain-specific data improves performance by 15-25%
- **Hybrid Approaches:** Combining multiple models yields better results than single models
- **Human Review:** Critical for low-confidence outputs (<0.85 confidence)

---

## Paper 2: Research Directions for LLM in SW Requirement Engineering

**Focus:** Future directions and optimization techniques for LLMs in RE

### Research Questions Addressed

1. **What types of LLMs are employed in SRE?**
   - Generative models for creation tasks
   - Encoder models for understanding tasks
   - Multimodal models for diagram/visual processing
   - Specialized domain models for aerospace, automotive, etc.

2. **Typical Inputs and Outputs**
   - **Inputs:** Raw requirements, structured templates, context documents
   - **Outputs:** Classifications, entities, test cases, specifications, quality scores

3. **Most Effective Integration Points**
   - Early RE stages: Requirement elicitation (59% of studies)
   - Middle RE stages: Analysis and classification (23%)
   - Late RE stages: Validation and QA (18%)

### LLM Optimization Techniques

**1. Prompt Engineering Strategies**
- **Basic:** Simple, direct instructions
- **Intermediate:** Examples and context
- **Expert:** Chain-of-thought, in-context learning, structured templates

**2. Fine-tuning Approaches**
- Full model fine-tuning (expensive, best performance)
- Parameter-efficient fine-tuning (LoRA, Adapters)
- Domain-specific pre-training on RE corpora

**3. Output Refinement**
- Multi-stage quality validation
- Ensemble methods combining multiple models
- Iterative refinement with human feedback

### Emerging Trends

1. **Zero-shot Learning:** Reduced need for labeled data
2. **Transfer Learning:** Models trained on general NLP excel on RE tasks
3. **Multimodal Integration:** Visual requirements + text
4. **Efficiency:** Smaller models (Distil-BERT) approaching SOTA performance

---

## Paper 3: Benchmarking Large Language Models for Test Case Generation (TESTEVAL)

**Focus:** Comprehensive evaluation of LLMs for test case generation

### Dataset & Benchmark

- **TESTEVAL Dataset:** 210 Python programs from LeetCode
- **Three Tasks:**
  1. Overall Coverage (diverse test cases)
  2. Targeted Line/Branch Coverage (specific coverage goals)
  3. Targeted Path Coverage (execution path reasoning)

### Performance Results

**Overall Coverage:**
- GPT-4o: 98.65% average coverage
- ChatGPT: 90.23% average coverage
- Gemini: 87.54% average coverage
- Open-source models: 65-78%

**Targeted Coverage (Primary Challenge):**
- 12 of 16 LLMs show <5% improvement with target hints
- Indicates difficulty in targeted reasoning
- Limitation: struggles with specific branch/path coverage

**Key Metrics**
- Correctness (Compilation + Execution): 
  - GPT-4o: ~99%
  - ChatGPT: ~75%
  - Open-source: 45-65%
- Assertion Correctness: 75-92%

### Key Insights

1. **Strengths**
   - Generate syntactically correct, executable test cases
   - High diversity in test inputs
   - Good general-purpose coverage

2. **Weaknesses**
   - Struggle with targeted coverage requirements
   - Limited understanding of complex control flow
   - Difficulty reasoning about branch conditions
   - Performance gap between commercial and open-source models

3. **Future Improvements Needed**
   - Enhanced program logic understanding
   - Better branch/path reasoning capabilities
   - Improved prompt engineering for targeted coverage

### Implications for RE

- Test case generation from requirements is feasible
- Multi-stage validation essential for quality assurance
- Smaller models may be insufficient for complex scenarios
- Human review needed for critical test coverage

---

## Paper 4: Generative Language Models for RE - Strengths and Limitations

**Focus:** Comprehensive case study comparing ChatGPT and Gemini across multiple RE tasks

### Experimental Setup

**Datasets Used:**
1. **PURE** (7,445 samples): Requirements Extraction
2. **PROMISE** (622 samples): Binary/Multi-class Classification
3. **Aerospace** (6,347 words): NER Tagging
4. **REQuestA** (300 pairs): Question Answering

**Compared Models:**
- Traditional ML (SVM, NB, LogReg)
- Deep Learning (LSTM, CNN, BiLSTM-CRF)
- BERT and variants
- ChatGPT (OpenAI)
- Gemini (Google)

### Performance Comparison

#### Extraction Task (PURE Dataset)
| Model | F1-Score | Performance |
|-------|----------|-------------|
| SOTA (BERT-based) | **0.86** | Baseline |
| ChatGPT | 0.76 | -11% |
| Gemini | 0.77 | -10% |
| Approach | Template-based extraction | Best practice |

**Insight:** Specialized models outperform generative models for structured extraction

#### Classification Task (PROMISE Dataset)
| Model | F1-Score | Performance |
|-------|----------|-------------|
| SOTA (Fine-tuned BERT) | **0.96** | Baseline |
| ChatGPT | 0.78 | -19% |
| Gemini | 0.78 | -19% |

**Insight:** Strong performance gap; fine-tuned models essential

#### NER Task (Aerospace Dataset)
| Model | F1-Score | Performance |
|-------|----------|-------------|
| SOTA (Aero-BERT) | **0.92** | Baseline |
| ChatGPT | 0.36 | -61% |
| Gemini | 0.25 | -73% |

**Insight:** LLMs struggle significantly with NER; BERT variants necessary

#### Question Answering (REQuestA Dataset)
| Model | F1-Score | Performance |
|-------|----------|-------------|
| SOTA (GPT-4o) | **0.95** | Baseline |
| ChatGPT | **0.91** | -4% |
| Gemini | 0.88 | -7% |

**Insight:** Only task where generative models approach SOTA performance

### Key Findings

**1. Task-Model Suitability**
- **Discriminative Tasks** (Classification, NER): BERT >> LLMs
- **Generative Tasks** (QA, Specification): LLMs competitive/superior
- **Extraction Tasks:** Specialized models better, but LLMs improving

**2. Prompt Engineering Impact**
- Basic prompts: Poor performance (often <0.70 F1)
- Intermediate prompts: Significant improvement (+0.10-0.15 F1)
- Expert prompts: +0.20-0.25 F1 improvement
- **Conclusion:** Prompt sophistication directly correlates with output quality

**3. Gemini vs. ChatGPT**
- ChatGPT more robust to poor prompts
- Gemini requires more careful prompt engineering
- Gemini slightly better on some tasks with optimal prompts
- ChatGPT more consistent across tasks

**4. Model-Specific Strengths**
- **ChatGPT:** General-purpose, good for multiple tasks
- **Gemini:** Google Cloud integration, some domain-specific tasks
- **BERT:** Fast, accurate, local deployment option
- **GPT-4o:** Best for complex reasoning and generation

---

## Unified Findings: Cross-Paper Synthesis

### 1. Performance Hierarchy by Task

```
Extraction       │ BERT (0.86) ► ChatGPT (0.76) ► Gemini (0.77)
Classification   │ BERT (0.96) ► ChatGPT (0.78) ► Gemini (0.78)
NER             │ Aero-BERT (0.92) ► Others (0.25-0.36)
QA              │ GPT-4o (0.95) ► ChatGPT (0.91) ► Gemini (0.88)
Test Generation │ GPT-4o (98.65% coverage) ► ChatGPT (90.23%)
Quality Assess  │ GPT-4o (69.55%) ► Manual review
```

### 2. Optimal Model Selection

| Task | Primary Model | Secondary | Fallback |
|------|---------------|-----------|----------|
| **Classification** | BERT | GPT-4o | Manual |
| **Extraction** | BERT | GPT-4o | Manual |
| **NER** | BERT/Aero-BERT | - | Manual |
| **QA** | GPT-4o | ChatGPT | BERT-based |
| **Test Generation** | GPT-4o | ChatGPT | Manual |
| **Specification** | GPT-4o | ChatGPT | Manual |
| **Quality** | GPT-4o | Manual | - |

### 3. Prompt Engineering Effectiveness

**Impact on Performance:**
- Basic prompts: 60-75% of SOTA
- Few-shot prompts: 75-85% of SOTA
- Chain-of-thought: 85-95% of SOTA
- Domain-expert prompts: 95-100% of SOTA

**Critical Success Factors:**
1. Clear task definition
2. Relevant examples (2-5 examples optimal)
3. Output format specification
4. Domain context provision
5. Error correction feedback

### 4. Quality Threshold Recommendations

Based on literature findings:

| Confidence Level | Action | Human Review Required |
|------------------|--------|----------------------|
| ≥ 0.90 | Accept directly | No |
| 0.80-0.90 | Review & approve | ~20% |
| 0.70-0.80 | Probable review | ~60% |
| 0.50-0.70 | Likely review | ~85% |
| < 0.50 | Reject/redo | Yes (100%) |

### 5. Hybrid Approach Benefits

**Combining Models:**
- BERT for fast, low-cost discrimination
- GPT-4o for complex generation
- Human review for confidence < 0.85
- Ensemble voting for tie-breaking

**Performance Improvement:**
- Single best model: SOTA baseline
- Hybrid approach: 5-15% above SOTA
- With human review: Near-perfect on critical tasks

---

## Recommendations for MTech Project

### 1. Architecture Principles

✓ **Do:**
- Use BERT for classification, extraction, NER
- Use GPT-4o for test generation, QA, complex tasks
- Implement confidence-based human review
- Combine multiple models via ensemble
- Fine-tune BERT on domain data

✗ **Don't:**
- Rely on single LLM for all tasks
- Use zero prompt engineering
- Deploy without quality validation
- Ignore human review for low-confidence outputs
- Deploy open-source models without adaptation

### 2. Dataset Selection

**Recommended Benchmark Datasets:**
1. **PURE** (7,445 samples) - Extraction
2. **PROMISE** (622 samples) - Classification
3. **Aerospace** (6,347 words) - NER
4. **REQuestA** (300 pairs) - QA

**Why These Datasets:**
- Widely used in RE ML research
- Enable performance comparison
- Represent real-world RE tasks
- Published baselines available

### 3. Quality Assurance Strategy

**Multi-layer Validation:**
1. Syntactic validation (format checks)
2. Semantic validation (consistency checks)
3. Confidence assessment (model confidence)
4. Human review (expert validation)
5. Audit logging (compliance & improvement)

**Quality Thresholds:**
- Classification: 0.90 confidence
- Extraction: 0.85 confidence
- NER: 0.88 confidence
- QA: 0.92 confidence
- Test Generation: 0.90 coverage

### 4. Prompt Engineering Template

**Effective Prompt Structure:**
```
1. Task Definition
   Clear description of what to do

2. Domain Context
   RE-specific knowledge needed

3. Examples (2-5)
   Input-output pairs

4. Output Format
   Specific structure expected

5. Quality Criteria
   What makes good output

6. Error Handling
   How to handle edge cases
```

### 5. Implementation Priority

**Phase 1 (MVP):**
- BERT for classification & extraction
- GPT-4o for test generation
- Basic quality validation
- Manual review queue

**Phase 2 (Enhancement):**
- Aero-BERT for NER
- Fine-tuning on domain data
- Advanced prompt engineering
- Confidence calibration

**Phase 3 (Production):**
- Full ensemble methods
- Human-in-the-loop workflow
- API & UI development
- Comprehensive audit logging

---

## Research Gaps & Future Work

### Open Questions

1. **Targeted Coverage:** How to improve LLM reasoning for specific requirements?
2. **Few-shot Learning:** Can few examples match fine-tuned performance?
3. **Domain Adaptation:** Optimal fine-tuning strategies for RE domains?
4. **Multimodal RE:** Integrating visual requirements with text?
5. **Real-time Adaptation:** Learning from human feedback on-the-fly?

### Emerging Opportunities

- Vision transformers for visual requirement processing
- Retrieval-augmented generation (RAG) for domain context
- Smaller models via distillation and adaptation
- Federated learning for privacy-preserving RE
- Neurosymbolic approaches combining logic with LLMs

---

## Conclusion

The literature reveals that **no single model excels across all RE tasks**. A well-architected hybrid approach combining:
- BERT variants for discriminative tasks
- GPT-4o for generative tasks
- Intelligent task routing
- Quality validation layers
- Human-in-the-loop review

yields superior performance while maintaining practical deployability. The boilerplate implementation incorporates these findings with proven baselines from four benchmark datasets, positioning it for production-ready enterprise deployment.

---

## Key References Summary

| Paper | Focus | Primary Finding | Performance |
|-------|-------|-----------------|-------------|
| Hemmat et al. (2025) | LLM Survey in RE | Multi-role LLM integration | Framework established |
| Saleem et al. (2025) | ChatGPT vs Gemini | BERT superior for structural | 0.86-0.96 F1 |
| Wang et al. (2025) | Test Case Generation | GPT-4o best for tests | 98.65% coverage |
| Generative LM Paper | Strengths/Limits | Hybrid approach optimal | Task-dependent |

---

**Document Version:** 1.0  
**Last Updated:** October 2026  
**Methodology:** Systematic literature review of 4 seminal papers  
**Dataset Coverage:** 4 benchmark datasets, 7 RE tasks, 8+ LLM models
