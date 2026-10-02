"""
Main Pipeline Orchestration Module
Implements the recommended hybrid multi-model and human-in-the-loop pipeline
from the literature review
"""

from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
from config import (
    AppConfig, ModelType, RETaskType, ModelConfig,
    DatasetConfig, PromptEngineeringConfig, DATASETS
)
from logger import get_logger
from data_loader import DataLoaderFactory, DataLoader
from llm_interface import ModelFactory, BaseLLMModel, LLMResponse, LLMPipeline
from evaluation import (
    EvaluationMetrics, ClassificationMetrics, TextGenerationMetrics,
    TestCoverageMetrics, QualityAssessmentMetrics, NEREvaluationMetrics,
    EvaluationReporter
)

logger = get_logger(__name__)


class ProcessingStatus(Enum):
    """Status of processing stages"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_REVIEW = "waiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ProcessingResult:
    """Result from processing pipeline"""
    requirement_id: str
    input_text: str
    status: ProcessingStatus
    extraction_result: Optional[Dict[str, Any]] = None
    classification_result: Optional[Dict[str, Any]] = None
    quality_assessment: Optional[Dict[str, Any]] = None
    test_cases: Optional[List[str]] = None
    human_review_required: bool = False
    review_notes: Optional[str] = None
    confidence_scores: Optional[Dict[str, float]] = None
    errors: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'requirement_id': self.requirement_id,
            'input_text': self.input_text,
            'status': self.status.value,
            'extraction': self.extraction_result,
            'classification': self.classification_result,
            'quality_assessment': self.quality_assessment,
            'test_cases': self.test_cases,
            'human_review_required': self.human_review_required,
            'review_notes': self.review_notes,
            'confidence_scores': self.confidence_scores,
            'errors': self.errors
        }


class TaskClassifier:
    """Classifies requirements and routes to appropriate models"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def classify_task(self, requirement_text: str) -> RETaskType:
        """
        Determine which RE task is appropriate
        Default: route to extraction if unclear
        """
        text_lower = requirement_text.lower()

        # Simple keyword-based routing (in production, use ML classifier)
        if any(word in text_lower for word in ['test', 'verify', 'validate', 'cover']):
            return RETaskType.TEST_CASE_GEN

        elif any(word in text_lower for word in ['what', 'how', 'why', '?']):
            return RETaskType.QA

        elif any(word in text_lower for word in ['must', 'shall', 'should']):
            return RETaskType.EXTRACTION

        else:
            return RETaskType.EXTRACTION

    def select_models(self, task_type: RETaskType) -> List[ModelType]:
        """Select best models for task"""
        model_selections = {
            RETaskType.EXTRACTION: [ModelType.BERT, ModelType.GPT_4O],
            RETaskType.CLASSIFICATION: [ModelType.BERT, ModelType.CHATGPT],
            RETaskType.NER: [ModelType.BERT],  # Aero-BERT for specialized
            RETaskType.QA: [ModelType.GPT_4O, ModelType.CHATGPT],
            RETaskType.TEST_CASE_GEN: [ModelType.GPT_4O],
            RETaskType.QUALITY_ASSESSMENT: [ModelType.GPT_4O],
            RETaskType.SPECIFICATION_GEN: [ModelType.GPT_4O]
        }
        return model_selections.get(task_type, [ModelType.GPT_4O])


class QualityValidator:
    """Validates output quality and determines if human review is needed"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def validate_extraction(self, extraction_result: Dict[str, Any], confidence: float) -> Tuple[bool, str]:
        """Validate extraction result"""
        if not extraction_result or len(extraction_result) == 0:
            return False, "No entities extracted"

        if confidence < AppConfig.QUALITY_THRESHOLD:
            return False, f"Confidence ({confidence}) below threshold ({AppConfig.QUALITY_THRESHOLD})"

        return True, "Extraction valid"

    def validate_classification(self, classification: str, confidence: float) -> Tuple[bool, str]:
        """Validate classification result"""
        if not classification:
            return False, "No classification provided"

        if confidence < AppConfig.QUALITY_THRESHOLD:
            return False, f"Confidence ({confidence}) below threshold"

        return True, "Classification valid"

    def validate_quality_assessment(self, quality_score: float) -> Tuple[bool, str]:
        """Validate quality assessment"""
        if quality_score < 0.5:
            return False, f"Requirement quality low ({quality_score})"

        return True, "Quality acceptable"

    def needs_human_review(self, confidence_scores: Dict[str, float]) -> Tuple[bool, str]:
        """Determine if human review is needed"""
        # If any confidence is below review threshold, request review
        for task, confidence in confidence_scores.items():
            if confidence < AppConfig.HUMAN_REVIEW_THRESHOLD:
                return True, f"Low confidence on {task}: {confidence}"

        return False, "All confidence scores acceptable"


class HumanInTheLoopQueue:
    """Manages human review queue"""

    def __init__(self, max_queue_size: int = AppConfig.HIML_REVIEW_QUEUE_SIZE):
        self.logger = get_logger(self.__class__.__name__)
        self.queue: List[ProcessingResult] = []
        self.max_size = max_queue_size
        self.approved: List[ProcessingResult] = []
        self.rejected: List[ProcessingResult] = []

    def add_to_queue(self, result: ProcessingResult) -> bool:
        """Add result to review queue"""
        if len(self.queue) >= self.max_size:
            self.logger.warning("Human review queue full")
            return False

        self.queue.append(result)
        self.logger.info(f"Added requirement {result.requirement_id} to review queue")
        return True

    def approve(self, requirement_id: str, notes: str = "") -> bool:
        """Approve a requirement"""
        for i, result in enumerate(self.queue):
            if result.requirement_id == requirement_id:
                result.status = ProcessingStatus.APPROVED
                result.review_notes = notes
                self.approved.append(self.queue.pop(i))
                self.logger.info(f"Approved requirement {requirement_id}")
                return True
        return False

    def reject(self, requirement_id: str, notes: str = "") -> bool:
        """Reject a requirement"""
        for i, result in enumerate(self.queue):
            if result.requirement_id == requirement_id:
                result.status = ProcessingStatus.REJECTED
                result.review_notes = notes
                self.rejected.append(self.queue.pop(i))
                self.logger.info(f"Rejected requirement {requirement_id}")
                return True
        return False

    def get_queue_status(self) -> Dict[str, int]:
        """Get queue statistics"""
        return {
            'pending': len(self.queue),
            'approved': len(self.approved),
            'rejected': len(self.rejected),
            'total': len(self.queue) + len(self.approved) + len(self.rejected)
        }


class REPipeline:
    """
    Main Requirements Engineering Pipeline
    Implements: Task Classification → Model Selection → Processing →
                Quality Validation → Human Review (if needed)
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.classifier = TaskClassifier()
        self.validator = QualityValidator()
        self.review_queue = HumanInTheLoopQueue()
        self.llm_pipeline = LLMPipeline()
        self.results: List[ProcessingResult] = []
        self.metrics: Dict[str, EvaluationMetrics] = {}

        AppConfig.create_directories()

    def process_requirement(self, requirement_id: str, requirement_text: str) -> ProcessingResult:
        """Process single requirement through pipeline"""
        self.logger.info(f"Processing requirement: {requirement_id}")

        result = ProcessingResult(
            requirement_id=requirement_id,
            input_text=requirement_text,
            status=ProcessingStatus.IN_PROGRESS,
            confidence_scores={},
            errors=[]
        )

        try:
            # Step 1: Classify task
            task_type = self.classifier.classify_task(requirement_text)
            self.logger.debug(f"Classified as task: {task_type.value}")

            # Step 2: Process through LLM pipeline
            processing_results = self.llm_pipeline.process_requirement(
                requirement_text,
                ['extract', 'classify', 'quality_assess']
            )

            result.extraction_result = processing_results['tasks_results'].get('extraction')
            result.classification_result = processing_results['tasks_results'].get('classification')
            result.quality_assessment = processing_results['tasks_results'].get('quality_assessment')

            # Step 3: Extract confidence scores
            if result.classification_result:
                result.confidence_scores['classification'] = \
                    result.classification_result.get('confidence', 0.0)

            # Step 4: Quality validation
            valid, validation_msg = self.validator.validate_extraction(
                result.extraction_result or {},
                result.confidence_scores.get('classification', 0.0)
            )

            if not valid:
                result.errors.append(f"Validation failed: {validation_msg}")
                self.logger.warning(f"Validation failed for {requirement_id}: {validation_msg}")

            # Step 5: Determine if human review needed
            needs_review, review_reason = self.validator.needs_human_review(
                result.confidence_scores
            )

            if needs_review and AppConfig.HIML_ENABLED:
                result.human_review_required = True
                result.status = ProcessingStatus.WAITING_REVIEW
                self.review_queue.add_to_queue(result)
                self.logger.info(f"Added {requirement_id} to review: {review_reason}")
            else:
                result.status = ProcessingStatus.COMPLETED
                self.logger.info(f"Successfully processed requirement: {requirement_id}")

        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.errors.append(str(e))
            self.logger.error(f"Error processing requirement {requirement_id}: {str(e)}")

        self.results.append(result)
        return result

    def process_batch(self, requirements: List[Tuple[str, str]]) -> List[ProcessingResult]:
        """Process batch of requirements"""
        self.logger.info(f"Processing batch of {len(requirements)} requirements")

        results = []
        for req_id, req_text in requirements:
            result = self.process_requirement(req_id, req_text)
            results.append(result)

        self.logger.info(f"Batch processing complete. {len(results)} requirements processed")
        return results

    def load_and_process_dataset(self, dataset_name: str) -> List[ProcessingResult]:
        """Load dataset and process all samples"""
        self.logger.info(f"Loading and processing dataset: {dataset_name}")

        try:
            dataset_config = AppConfig.get_dataset_config(dataset_name)
            loader = DataLoaderFactory.create_loader(dataset_config)
            loader.load()
            loader.preprocess()

            if not loader.validate():
                raise ValueError(f"Dataset validation failed: {dataset_name}")

            # Get training data (smaller subset for demo)
            train, val, test = loader.get_split()
            data_to_process = train.head(10) if hasattr(train, 'head') else train[:10]

            # Process requirements
            requirements = []
            if hasattr(data_to_process, 'iterrows'):  # DataFrame
                for idx, row in data_to_process.iterrows():
                    text = row.get('source_text') or row.get('requirement_text') or str(row)
                    requirements.append((f"req_{idx}", text))
            else:  # List or other format
                for i, item in enumerate(data_to_process):
                    text = item.get('text') if isinstance(item, dict) else str(item)
                    requirements.append((f"req_{i}", text))

            return self.process_batch(requirements)

        except Exception as e:
            self.logger.error(f"Error loading/processing dataset: {str(e)}")
            return []

    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Get overall pipeline statistics"""
        total_processed = len(self.results)
        completed = sum(1 for r in self.results if r.status == ProcessingStatus.COMPLETED)
        failed = sum(1 for r in self.results if r.status == ProcessingStatus.FAILED)
        waiting_review = sum(1 for r in self.results if r.status == ProcessingStatus.WAITING_REVIEW)

        return {
            'total_processed': total_processed,
            'completed': completed,
            'failed': failed,
            'waiting_review': waiting_review,
            'success_rate': completed / total_processed if total_processed > 0 else 0.0,
            'review_queue_status': self.review_queue.get_queue_status()
        }

    def generate_report(self) -> str:
        """Generate processing report"""
        stats = self.get_pipeline_statistics()
        report = "\n" + "=" * 80 + "\n"
        report += "REQUIREMENTS ENGINEERING PIPELINE REPORT\n"
        report += "=" * 80 + "\n\n"

        report += "Pipeline Statistics:\n"
        report += f"  Total Processed: {stats['total_processed']}\n"
        report += f"  Completed: {stats['completed']}\n"
        report += f"  Failed: {stats['failed']}\n"
        report += f"  Waiting Review: {stats['waiting_review']}\n"
        report += f"  Success Rate: {stats['success_rate']:.2%}\n"
        report += f"\nHuman Review Queue:\n"
        for key, value in stats['review_queue_status'].items():
            report += f"  {key}: {value}\n"

        return report
