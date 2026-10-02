"""
Evaluation and Metrics Module for AI-Powered Requirements Engineering Tool
Implements metrics from literature review: F1, Precision, Recall, BLEU, ROUGE, Coverage
"""

import json
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import numpy as np
from logger import get_logger

logger = get_logger(__name__)


@dataclass
class EvaluationMetrics:
    """Container for evaluation metrics"""
    precision: float
    recall: float
    f1_score: float
    accuracy: Optional[float] = None
    confidence_score: Optional[float] = None
    additional_metrics: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        metrics = {
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score
        }
        if self.accuracy is not None:
            metrics['accuracy'] = self.accuracy
        if self.confidence_score is not None:
            metrics['confidence'] = self.confidence_score
        if self.additional_metrics:
            metrics.update(self.additional_metrics)
        return metrics

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class ClassificationMetrics:
    """Metrics for classification tasks (Extraction, Classification)"""

    @staticmethod
    def calculate_metrics(y_true: List[int], y_pred: List[int]) -> EvaluationMetrics:
        """Calculate precision, recall, F1 from predictions"""
        if len(y_true) != len(y_pred):
            raise ValueError("y_true and y_pred must have same length")

        # True Positives
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
        # False Positives
        fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
        # False Negatives
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
        # True Negatives
        tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (tp + tn) / len(y_true)

        return EvaluationMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1,
            accuracy=accuracy,
            additional_metrics={
                'true_positives': tp,
                'false_positives': fp,
                'false_negatives': fn,
                'true_negatives': tn
            }
        )

    @staticmethod
    def multilabel_metrics(y_true: List[List[int]], y_pred: List[List[int]]) -> EvaluationMetrics:
        """Calculate metrics for multilabel classification"""
        all_tp, all_fp, all_fn = 0, 0, 0

        for true_labels, pred_labels in zip(y_true, y_pred):
            tp = sum(1 for t, p in zip(true_labels, pred_labels) if t == 1 and p == 1)
            fp = sum(1 for t, p in zip(true_labels, pred_labels) if t == 0 and p == 1)
            fn = sum(1 for t, p in zip(true_labels, pred_labels) if t == 1 and p == 0)

            all_tp += tp
            all_fp += fp
            all_fn += fn

        precision = all_tp / (all_tp + all_fp) if (all_tp + all_fp) > 0 else 0.0
        recall = all_tp / (all_tp + all_fn) if (all_tp + all_fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return EvaluationMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1,
            additional_metrics={'tp': all_tp, 'fp': all_fp, 'fn': all_fn}
        )


class TextGenerationMetrics:
    """Metrics for text generation tasks (BLEU, ROUGE)"""

    @staticmethod
    def bleu_score(reference: str, hypothesis: str) -> float:
        """
        Simplified BLEU score calculation
        Compares n-gram overlap between reference and hypothesis
        """
        ref_tokens = reference.lower().split()
        hyp_tokens = hypothesis.lower().split()

        # Calculate precision for different n-grams
        scores = []
        for n in range(1, 5):
            ref_ngrams = set(
                tuple(ref_tokens[i:i + n]) for i in range(len(ref_tokens) - n + 1)
            )
            hyp_ngrams = [
                tuple(hyp_tokens[i:i + n]) for i in range(len(hyp_tokens) - n + 1)
            ]

            if not hyp_ngrams:
                scores.append(0.0)
                continue

            matches = sum(1 for ng in hyp_ngrams if ng in ref_ngrams)
            precision = matches / len(hyp_ngrams)
            scores.append(precision)

        # Geometric mean of n-gram precisions
        if all(s > 0 for s in scores):
            return float(np.exp(np.mean(np.log(scores))))
        return 0.0

    @staticmethod
    def rouge_l_score(reference: str, hypothesis: str) -> float:
        """
        ROUGE-L (Longest Common Subsequence) score
        Measures longest common subsequence between reference and hypothesis
        """
        ref_tokens = reference.lower().split()
        hyp_tokens = hypothesis.lower().split()

        # Calculate LCS length using dynamic programming
        m, n = len(ref_tokens), len(hyp_tokens)
        lcs = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if ref_tokens[i - 1] == hyp_tokens[j - 1]:
                    lcs[i][j] = lcs[i - 1][j - 1] + 1
                else:
                    lcs[i][j] = max(lcs[i - 1][j], lcs[i][j - 1])

        lcs_length = lcs[m][n]

        # Calculate ROUGE-L with precision and recall
        precision = lcs_length / len(hyp_tokens) if hyp_tokens else 0.0
        recall = lcs_length / len(ref_tokens) if ref_tokens else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return f1

    @staticmethod
    def bleu_batch(references: List[str], hypotheses: List[str]) -> float:
        """Calculate average BLEU score for batch"""
        if len(references) != len(hypotheses):
            raise ValueError("References and hypotheses must have same length")
        scores = [
            TextGenerationMetrics.bleu_score(ref, hyp)
            for ref, hyp in zip(references, hypotheses)
        ]
        return np.mean(scores)

    @staticmethod
    def rouge_batch(references: List[str], hypotheses: List[str]) -> float:
        """Calculate average ROUGE-L score for batch"""
        if len(references) != len(hypotheses):
            raise ValueError("References and hypotheses must have same length")
        scores = [
            TextGenerationMetrics.rouge_l_score(ref, hyp)
            for ref, hyp in zip(references, hypotheses)
        ]
        return np.mean(scores)


class TestCoverageMetrics:
    """Metrics for test case generation (Coverage metrics from TESTEVAL)"""

    @staticmethod
    def line_coverage(covered_lines: set, total_lines: set) -> float:
        """Calculate line coverage percentage"""
        if not total_lines:
            return 0.0
        return len(covered_lines & total_lines) / len(total_lines)

    @staticmethod
    def branch_coverage(covered_branches: set, total_branches: set) -> float:
        """Calculate branch coverage percentage"""
        if not total_branches:
            return 0.0
        return len(covered_branches & total_branches) / len(total_branches)

    @staticmethod
    def path_coverage(covered_paths: set, total_paths: set) -> float:
        """Calculate path coverage percentage"""
        if not total_paths:
            return 0.0
        return len(covered_paths & total_paths) / len(total_paths)

    @staticmethod
    def cov_at_k(test_cases: List[Dict], coverage_type: str = 'line', k: int = 10) -> float:
        """
        Coverage@K metric
        Measures diversity of test cases in top-k predictions
        """
        if not test_cases or k == 0:
            return 0.0

        top_k_tests = test_cases[:min(k, len(test_cases))]
        unique_coverage = len(set(t.get('coverage_id', i) for i, t in enumerate(top_k_tests)))
        return unique_coverage / len(top_k_tests)

    @staticmethod
    def coverage_comparison(baseline_coverage: float, model_coverage: float) -> Tuple[float, str]:
        """
        Compare model coverage against baseline
        Returns (improvement_percentage, status)
        """
        if baseline_coverage == 0:
            return 0.0, "baseline_zero"

        improvement = ((model_coverage - baseline_coverage) / baseline_coverage) * 100
        status = "improvement" if improvement > 0 else "degradation"
        return improvement, status


class QualityAssessmentMetrics:
    """Metrics for requirement quality assessment"""

    @staticmethod
    def completeness_score(requirement: str) -> float:
        """
        Assess completeness of requirement
        Checks for presence of: subject, predicate, object, constraints
        """
        required_keywords = {
            'subject': ['system', 'application', 'user', 'actor', 'system shall'],
            'predicate': ['shall', 'must', 'should', 'will', 'provide', 'generate'],
            'object': []  # Context-dependent
        }

        score = 0.0
        max_score = len(required_keywords)

        for category, keywords in required_keywords.items():
            if any(keyword in requirement.lower() for keyword in keywords):
                score += 1

        return score / max_score if max_score > 0 else 0.0

    @staticmethod
    def consistency_score(requirements: List[str]) -> float:
        """
        Assess consistency across multiple requirements
        Checks for: terminology consistency, format consistency, structure similarity
        """
        if len(requirements) < 2:
            return 1.0

        # Simple heuristic: measure keyword overlap across requirements
        all_words = []
        for req in requirements:
            words = set(req.lower().split())
            all_words.append(words)

        # Calculate Jaccard similarity between all pairs
        similarities = []
        for i in range(len(all_words)):
            for j in range(i + 1, len(all_words)):
                intersection = len(all_words[i] & all_words[j])
                union = len(all_words[i] | all_words[j])
                similarity = intersection / union if union > 0 else 0.0
                similarities.append(similarity)

        return np.mean(similarities) if similarities else 0.0

    @staticmethod
    def ambiguity_score(requirement: str) -> float:
        """
        Detect potential ambiguity in requirement
        Lower score = more ambiguous
        """
        ambiguous_patterns = ['may', 'might', 'could', 'possibly', 'etc.', '...', 'and/or']
        ambiguity_count = sum(1 for pattern in ambiguous_patterns if pattern in requirement.lower())

        # Ambiguity penalty (0.0 = high ambiguity, 1.0 = clear)
        return 1.0 - min(ambiguity_count * 0.1, 1.0)

    @staticmethod
    def overall_quality_score(requirement: str, requirements_list: Optional[List[str]] = None) -> float:
        """
        Calculate overall quality score (0-1)
        Combines completeness, clarity, and consistency
        """
        completeness = QualityAssessmentMetrics.completeness_score(requirement)
        ambiguity = QualityAssessmentMetrics.ambiguity_score(requirement)

        consistency = 1.0
        if requirements_list and len(requirements_list) > 1:
            consistency = QualityAssessmentMetrics.consistency_score(requirements_list)

        # Weighted average
        quality = (completeness * 0.4) + (ambiguity * 0.35) + (consistency * 0.25)
        return quality


class NEREvaluationMetrics:
    """Metrics for Named Entity Recognition evaluation"""

    @staticmethod
    def entity_level_metrics(true_entities: List[Tuple], pred_entities: List[Tuple]) -> EvaluationMetrics:
        """
        Calculate metrics at entity level
        Each entity is compared as a whole
        """
        true_set = set(true_entities)
        pred_set = set(pred_entities)

        tp = len(true_set & pred_set)
        fp = len(pred_set - true_set)
        fn = len(true_set - pred_set)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return EvaluationMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1,
            additional_metrics={'tp': tp, 'fp': fp, 'fn': fn}
        )

    @staticmethod
    def token_level_metrics(true_tags: List[str], pred_tags: List[str]) -> EvaluationMetrics:
        """Calculate metrics at token level (token-wise comparison)"""
        if len(true_tags) != len(pred_tags):
            raise ValueError("Tag sequences must have same length")

        tp = sum(1 for t, p in zip(true_tags, pred_tags) if t != 'O' and t == p)
        fp = sum(1 for t, p in zip(true_tags, pred_tags) if t == 'O' and p != 'O')
        fn = sum(1 for t, p in zip(true_tags, pred_tags) if t != 'O' and p == 'O')

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return EvaluationMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1
        )


class EvaluationReporter:
    """Generate evaluation reports"""

    @staticmethod
    def generate_report(metrics_dict: Dict[str, EvaluationMetrics]) -> str:
        """Generate formatted evaluation report"""
        report = "=" * 80 + "\n"
        report += "EVALUATION REPORT\n"
        report += "=" * 80 + "\n\n"

        for task_name, metrics in metrics_dict.items():
            report += f"Task: {task_name}\n"
            report += "-" * 40 + "\n"
            report += f"  Precision: {metrics.precision:.4f}\n"
            report += f"  Recall:    {metrics.recall:.4f}\n"
            report += f"  F1 Score:  {metrics.f1_score:.4f}\n"

            if metrics.accuracy is not None:
                report += f"  Accuracy:  {metrics.accuracy:.4f}\n"

            if metrics.additional_metrics:
                for key, value in metrics.additional_metrics.items():
                    report += f"  {key}: {value}\n"

            report += "\n"

        return report

    @staticmethod
    def export_metrics_json(metrics_dict: Dict[str, EvaluationMetrics], filepath: str):
        """Export metrics to JSON file"""
        export_data = {
            task: metrics.to_dict()
            for task, metrics in metrics_dict.items()
        }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Metrics exported to {filepath}")
