"""
Main Entry Point for AI-Powered Requirements Engineering Tool
Demonstrates usage of the complete pipeline
"""

import sys
import json
from config import AppConfig, RETaskType, DatasetConfig, ModelType
from logger import get_logger
from pipeline import REPipeline
from evaluation import EvaluationReporter

logger = get_logger(__name__)


def main():
    """Main execution function"""

    print("\n" + "=" * 80)
    print("AI-POWERED REQUIREMENTS ENGINEERING TOOL")
    print("Based on LLM Literature Review (2025)")
    print("=" * 80 + "\n")

    # Initialize
    AppConfig.create_directories()
    pipeline = REPipeline()

    logger.info("AI-Powered RE Tool started")

    # Example 1: Process single requirement
    print("Example 1: Process Single Requirement")
    print("-" * 80)

    sample_requirement = """
    The system shall validate user input and display error messages if validation fails.
    The validation should support email, phone number, and postal code formats.
    The system must complete validation within 500ms.
    """

    result = pipeline.process_requirement("REQ_001", sample_requirement)

    print(f"\nRequirement ID: {result.requirement_id}")
    print(f"Status: {result.status.value}")
    print(f"Human Review Required: {result.human_review_required}")
    print(f"Confidence Scores: {result.confidence_scores}")

    if result.extraction_result:
        print(f"Extraction Result: {json.dumps(result.extraction_result, indent=2)}")

    if result.classification_result:
        print(f"Classification: {result.classification_result}")

    print("\n")

    # Example 2: Process batch of requirements
    print("Example 2: Process Batch of Requirements")
    print("-" * 80)

    batch_requirements = [
        ("REQ_002", "The system shall authenticate users using OAuth 2.0 protocol"),
        ("REQ_003", "The database shall support concurrent requests up to 1000 users"),
        ("REQ_004", "Users must receive password reset emails within 2 minutes"),
    ]

    batch_results = pipeline.process_batch(batch_requirements)

    print(f"\nProcessed {len(batch_results)} requirements")
    for result in batch_results:
        print(f"  {result.requirement_id}: {result.status.value}")

    print("\n")

    # Example 3.1: Load and process dataset Classification
    print("Example 3.1: Load and Process Dataset (Requirements Classification)")
    print("-" * 80)

    dataset_results = pipeline.load_and_process_dataset(DatasetConfig.PROMISE)
    print(f"\nLoaded and processed {len(dataset_results)} samples from PROMISE dataset")

    print("\n")

    # Example 3.2: Load and process dataset Extraction
    print("Example 3.2: Load and Process Dataset (Requirements Extraction)")
    print("-" * 80)

    dataset_results = pipeline.load_and_process_dataset(DatasetConfig.PURE)
    print(f"\nLoaded and processed {len(dataset_results)} samples from PURE dataset")

    print("\n")

    # Example 3.3: Load and process dataset Extraction
    print("Example 3.3: Load and Process Dataset (NER)")
    print("-" * 80)

    dataset_results = pipeline.load_and_process_dataset(DatasetConfig.AEROSPACE)
    print(f"\nLoaded and processed {len(dataset_results)} samples from AEROSPACE dataset")

    print("\n")

    # Example 3.4: Load and process dataset Question Answering
    print("Example 3.4: Load and Process Dataset (Question Answering)")
    print("-" * 80)

    dataset_results = pipeline.load_and_process_dataset(DatasetConfig.REQUESTQA)
    print(f"\nLoaded and processed {len(dataset_results)} samples from REQUESTQA dataset")

    print("\n")


    # Example 4: Generate report
    print("Example 4: Pipeline Report and Statistics")
    print("-" * 80)

    report = pipeline.generate_report()
    print(report)

    # Example 5: Demonstrate human review process
    print("Example 5: Human Review Process")
    print("-" * 80)

    queue_status = pipeline.review_queue.get_queue_status()
    print(f"Items waiting for review: {queue_status['pending']}")

    if pipeline.review_queue.queue:
        first_item = pipeline.review_queue.queue[0]
        print(f"\nFirst item in review queue:")
        print(f"  ID: {first_item.requirement_id}")
        print(f"  Text: {first_item.input_text[:100]}...")

        # Simulate human approval
        pipeline.review_queue.approve(
            first_item.requirement_id,
            notes="Requirement is clear and well-structured"
        )
        print(f"  Status: Approved")

    print("\n")

    # Example 6: Model comparison
    print("Example 6: Model Capabilities and Recommendations")
    print("-" * 80)

    model_info = {
        "Extraction": "Fine-tuned BERT (F1=0.86) > ChatGPT (F1=0.76) > Gemini (F1=0.77)",
        "Classification": "Fine-tuned BERT (F1=0.96) >> ChatGPT/Gemini (F1=0.78)",
        "NER": "Aero-BERT (F1=0.92) >> ChatGPT (F1=0.36) >> Gemini (F1=0.25)",
        "Question Answering": "ChatGPT (F1=0.91) > Gemini (F1=0.88) > BERT (F1=0.85)",
        "Test Case Generation": "GPT-4o (98.65% line coverage) >> ChatGPT (90.23%)",
    }

    for task, models in model_info.items():
        print(f"  {task}: {models}")

    print("\n")

    # Example 7: Configuration info
    print("Example 7: Tool Configuration")
    print("-" * 80)

    print(f"Project Root: {AppConfig.PROJECT_ROOT}")
    print(f"Data Directory: {AppConfig.DATA_DIR}")
    print(f"Models Directory: {AppConfig.MODELS_DIR}")
    print(f"Output Directory: {AppConfig.OUTPUT_DIR}")
    print(f"Logs Directory: {AppConfig.LOGS_DIR}")
    print(f"\nQuality Threshold: {AppConfig.QUALITY_THRESHOLD}")
    print(f"Human Review Threshold: {AppConfig.HUMAN_REVIEW_THRESHOLD}")
    print(f"Batch Size: {AppConfig.BATCH_SIZE}")
    print(f"HIML Enabled: {AppConfig.HIML_ENABLED}")

    print("\n")

    # Final statistics
    print("Final Pipeline Statistics")
    print("-" * 80)
    stats = pipeline.get_pipeline_statistics()
    print(json.dumps(stats, indent=2))

    print("\n" + "=" * 80)
    print("Execution completed successfully!")
    print("=" * 80 + "\n")

    logger.info("AI-Powered RE Tool completed successfully")


def demo_prompt_engineering():
    """Demonstrate prompt engineering strategies"""

    print("\n" + "=" * 80)
    print("PROMPT ENGINEERING STRATEGIES DEMONSTRATION")
    print("=" * 80 + "\n")

    prompt_levels = ["basic", "intermediate", "expert"]

    for level in prompt_levels:
        strategy = AppConfig.get_prompt_strategy(level)

        print(f"Strategy Level: {strategy.strategy_level.upper()}")
        print(f"Include Examples: {strategy.include_examples}")
        print(f"Chain-of-Thought: {strategy.use_chain_of_thought}")
        print(f"Domain Context: {strategy.domain_context}")
        print(f"Output Format: {strategy.output_format}")
        print()


def demo_dataset_info():
    """Display information about available datasets"""

    print("\n" + "=" * 80)
    print("AVAILABLE DATASETS FROM LITERATURE REVIEW")
    print("=" * 80 + "\n")

    from config import DATASETS

    for dataset_name, config in DATASETS.items():
        print(f"Dataset: {config.name}")
        print(f"  Task: {config.task_type.value}")
        print(f"  Size: {config.size} samples")
        print(f"  Description: {config.description}")
        print()


if __name__ == "__main__":
    try:
        # Run main pipeline
        main()

        # Display additional information
        if len(sys.argv) > 1:
            if sys.argv[1] == "--prompts":
                demo_prompt_engineering()
            elif sys.argv[1] == "--datasets":
                demo_dataset_info()
            elif sys.argv[1] == "--help":
                print("Usage: python main.py [OPTIONS]")
                print("Options:")
                print("  --prompts   Show prompt engineering strategies")
                print("  --datasets  Show available datasets")
                print("  --help      Show this help message")

    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")
        sys.exit(1)
