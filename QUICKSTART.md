# Quick Start Guide

Get up and running with the AI-Powered Requirements Engineering Tool in 5 minutes!

## Installation (2 minutes)

```bash
# 1. Navigate to project directory
cd ai_re_tool_boilerplate

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the tool
python main.py
```

## Your First Requirement Processing (1 minute)

Create a file `quick_demo.py`:

```python
from pipeline import REPipeline

# Initialize pipeline
pipeline = REPipeline()

# Process a requirement
requirement = """
The system shall authenticate users using OAuth 2.0.
Authentication must complete within 3 seconds.
Failed attempts should be logged for security audit.
"""

result = pipeline.process_requirement("REQ_001", requirement)

# View results
print(f"✓ Status: {result.status.value}")
print(f"✓ Classification: {result.classification_result}")
print(f"✓ Extraction: {result.extraction_result}")
print(f"✓ Quality Assessment: {result.quality_assessment}")
print(f"✓ Needs Human Review: {result.human_review_required}")
```

Run it:
```bash
python quick_demo.py
```

## Process Multiple Requirements (1 minute)

```python
from pipeline import REPipeline

pipeline = REPipeline()

# Define requirements
requirements = [
    ("REQ_001", "The system shall validate email addresses"),
    ("REQ_002", "The database shall support 10,000 concurrent users"),
    ("REQ_003", "Users must receive password reset within 5 minutes"),
]

# Process all at once
results = pipeline.process_batch(requirements)

# Summary
stats = pipeline.get_pipeline_statistics()
print(f"Processed: {stats['total_processed']}")
print(f"Success: {stats['success_rate']:.1%}")
print(f"Review Queue: {stats['review_queue_status']['pending']} pending")
```

## Load a Dataset (1 minute)

Process one of the datasets from the literature review:

```python
from pipeline import REPipeline

pipeline = REPipeline()

# Load PROMISE dataset (Requirements Classification)
# Options: "Pure", "PROMISE", "Aerospace", "REQuestA"
results = pipeline.load_and_process_dataset("PROMISE")

print(f"Processed {len(results)} samples from dataset")
print(pipeline.generate_report())
```

## Access Model Information

```python
from config import AppConfig, ModelType, RETaskType

# Get model configuration
model_config = AppConfig.get_model_config(ModelType.GPT_4O)

print("GPT-4o Performance Baselines:")
for task, score in model_config.baseline_performance.items():
    print(f"  {task}: {score}")

# Check task suitability
print("\nSuitable for tasks:")
for task_type in model_config.task_suitability:
    print(f"  - {task_type.value}")
```

## Human Review Process

```python
from pipeline import REPipeline

pipeline = REPipeline()

# Process some requirements
requirement = "The system shall handle user input"
result = pipeline.process_requirement("REQ_001", requirement)

# Check if review is needed
if result.human_review_required:
    print("Requirement needs human review")
    
    # Get items waiting for review
    queue = pipeline.review_queue
    
    if queue.queue:
        item = queue.queue[0]
        print(f"Reviewing: {item.requirement_id}")
        
        # Approve
        queue.approve(item.requirement_id, notes="Looks good!")
        
        # Or reject
        # queue.reject(item.requirement_id, notes="Needs more clarity")
    
    # Check status
    status = queue.get_queue_status()
    print(f"Queue Status: {status}")
```

## Evaluate Performance

```python
from evaluation import ClassificationMetrics, EvaluationReporter

# True labels and predictions
y_true = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
y_pred = [1, 0, 1, 0, 0, 1, 0, 1, 1, 1]

# Calculate metrics
metrics = ClassificationMetrics.calculate_metrics(y_true, y_pred)

# View results
print(f"Precision: {metrics.precision:.3f}")
print(f"Recall: {metrics.recall:.3f}")
print(f"F1 Score: {metrics.f1_score:.3f}")
print(f"Accuracy: {metrics.accuracy:.3f}")
```

## Configuration

Common configurations you might want to adjust:

```python
from config import AppConfig

# Adjust quality standards
AppConfig.QUALITY_THRESHOLD = 0.80      # Stricter quality check
AppConfig.HUMAN_REVIEW_THRESHOLD = 0.50 # More items for review

# Batch processing
AppConfig.BATCH_SIZE = 64               # Larger batches

# Enable/disable features
AppConfig.HIML_ENABLED = True           # Human-in-the-loop

# Logging
AppConfig.LOG_LEVEL = "DEBUG"           # More verbose logging
```

## Common Tasks

### Task 1: Classify Requirements
```python
from llm_interface import ModelFactory
from config import ModelType

# Use fine-tuned BERT for best performance
model = ModelFactory.create_model(ModelType.BERT)

# Classify
requirement = "The system shall authenticate users"
classification, confidence = model.classify(
    requirement, 
    ["Functional", "Non-Functional"]
)

print(f"Classification: {classification} ({confidence:.2%})")
```

### Task 2: Extract Entities
```python
from llm_interface import ModelFactory
from config import ModelType

# Use BERT for NER
model = ModelFactory.create_model(ModelType.BERT)

requirement = "The system shall validate email addresses within 500ms"
entities = model.extract_entities(requirement)

print(f"Entities: {entities}")
```

### Task 3: Question Answering
```python
from llm_interface import ModelFactory
from config import ModelType

# Use GPT-4o for best QA performance
model = ModelFactory.create_model(ModelType.GPT_4O)

context = "The system uses OAuth 2.0 for authentication"
question = "What authentication method is used?"

answer = model.question_answering(context, question)
print(f"Answer: {answer.content}")
```

### Task 4: Generate Specifications
```python
from llm_interface import ModelFactory
from config import ModelType

# Use GPT-4o for generation
model = ModelFactory.create_model(ModelType.GPT_4O)

from config import AppConfig
prompt = """Generate a formal specification for:
'The system shall validate user input'
Include acceptance criteria and test cases."""

response = model.generate(prompt)
print(response.content)
```

## Debug and Monitor

```python
from logger import get_logger

# Get logger for your module
logger = get_logger(__name__)

# Log at different levels
logger.debug("Detailed debugging info")
logger.info("General information")
logger.warning("Something might be wrong")
logger.error("An error occurred")

# Check logs
# Logs are saved in: logs/ai_re_tool_YYYYMMDD.log
```

## Troubleshooting

### Pipeline not responding?
```python
# Enable debug logging
from config import AppConfig
AppConfig.LOG_LEVEL = "DEBUG"

# Check logs
import os
print(AppConfig.LOGS_DIR)  # View log files here
```

### Low accuracy on your data?
```python
# Try different prompt strategy
strategy = AppConfig.get_prompt_strategy("expert")

# Use better model for task
from config import ModelType
model = ModelFactory.create_best_model_for_task(task_type)
```

### Need to process large volume?
```python
# Use batching
from pipeline import REPipeline

pipeline = REPipeline()
requirements = [...]  # Your large list

# Process in batches
batch_size = 100
for i in range(0, len(requirements), batch_size):
    batch = requirements[i:i+batch_size]
    results = pipeline.process_batch(batch)
```

## What's Next?

1. **Integrate LLM APIs** - Add your actual OpenAI/Gemini API keys
2. **Load Your Data** - Create a custom DataLoader for your requirements
3. **Fine-tune Models** - Train BERT on your domain data
4. **Deploy** - Move to production with proper monitoring
5. **Iterate** - Collect human feedback and improve prompts

## Documentation

- Full documentation: `README.md`
- Configuration guide: `config.py`
- API reference: Check docstrings in each module

## Need Help?

- Check example code in `main.py`
- Review literature review in your project docs
- Look at inline code comments
- Run with `--prompts` or `--datasets` flags

Happy RE-Engineering! 🚀
