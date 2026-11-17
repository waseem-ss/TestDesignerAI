"""
Benchmarking Module for TestDesignerAI
Provides comprehensive testing and performance evaluation across multiple LLM providers
"""

import time
import json
from typing import List, Dict, Any
from datetime import datetime
from pipeline import REPipeline
from llm_interface_v2 import FailoverLLMModel, get_provider_health_status
from config import AppConfig, ModelType
from data_loader import (
    PureDataLoader,
    PROMISEDataLoader,
    AerospaceDataLoader,
    REQuestADataLoader
)


class BenchmarkResult:
    """Container for benchmark results"""

    def __init__(self, model: str, task_type: str, dataset: str):
        self.model = model
        self.task_type = task_type
        self.dataset = dataset
        self.start_time = datetime.now()

        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

        self.response_times = []
        self.tokens_used = []
        self.quality_scores = []
        self.errors = []

    def add_result(self, response_time_ms: float, tokens: int, quality_score: float = 0.0, error: str = None):
        """Record a single benchmark result"""
        self.total_requests += 1

        if error:
            self.failed_requests += 1
            self.errors.append(error)
        else:
            self.successful_requests += 1
            self.response_times.append(response_time_ms)
            self.tokens_used.append(tokens)
            self.quality_scores.append(quality_score)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        avg_tokens = sum(self.tokens_used) / len(self.tokens_used) if self.tokens_used else 0
        avg_quality = sum(self.quality_scores) / len(self.quality_scores) if self.quality_scores else 0

        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0

        return {
            "model": self.model,
            "task_type": self.task_type,
            "dataset": self.dataset,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": f"{success_rate:.2f}%",
            "avg_response_time_ms": f"{avg_response_time:.2f}",
            "min_response_time_ms": f"{min(self.response_times):.2f}" if self.response_times else "N/A",
            "max_response_time_ms": f"{max(self.response_times):.2f}" if self.response_times else "N/A",
            "avg_tokens_used": f"{avg_tokens:.0f}",
            "avg_quality_score": f"{avg_quality:.2f}",
            "timestamp": self.start_time.isoformat()
        }


class ModelBenchmark:
    """Comprehensive benchmarking for LLM models"""

    # Dataset loaders mapping
    DATASET_LOADERS = {
        "Pure": PureDataLoader,
        "PROMISE": PROMISEDataLoader,
        "Aerospace": AerospaceDataLoader,
        "REQuestA": REQuestADataLoader
    }

    # Task compatibility with datasets
    TASK_DATASET_COMPATIBILITY = {
        "extraction": ["Pure", "PROMISE"],
        "classification": ["PROMISE", "Pure"],
        "ner": ["Aerospace", "Pure"],
        "question_answering": ["REQuestA"],
        "test_generation": ["Pure", "PROMISE"]
    }

    def __init__(self):
        self.results = {}
        self.pipeline = REPipeline()

    def get_dataset_samples(self, dataset_name: str, num_samples: int) -> List[Dict[str, Any]]:
        """Load samples from specified dataset"""
        loader_class = self.DATASET_LOADERS.get(dataset_name)
        if not loader_class:
            raise ValueError(f"Unknown dataset: {dataset_name}")

        loader = loader_class()
        loader.load()

        # Get samples based on dataset type
        if hasattr(loader, 'train_data'):
            samples = loader.train_data[:num_samples]
        elif hasattr(loader, 'data'):
            samples = loader.data[:num_samples]
        else:
            samples = []

        return samples

    def benchmark_model(
        self,
        model_name: str,
        task_type: str,
        dataset_name: str,
        num_samples: int = 20,
        timeout: int = 60
    ) -> BenchmarkResult:
        """Benchmark a single model on a dataset"""

        result = BenchmarkResult(model_name, task_type, dataset_name)

        try:
            # Load dataset samples
            samples = self.get_dataset_samples(dataset_name, num_samples)

            if not samples:
                result.add_result(0, 0, 0, f"No samples found for dataset {dataset_name}")
                return result

            # Create model instance
            config = AppConfig.get_model_config(ModelType.GPT_4O)

            # Process each sample
            for idx, sample in enumerate(samples):
                try:
                    start_time = time.time()

                    # Extract requirement text
                    if isinstance(sample, dict):
                        req_text = sample.get("text", sample.get("requirement", str(sample)))
                    else:
                        req_text = str(sample)

                    # Process requirement
                    req_response = self.pipeline.process_requirement(
                        req_id=f"{model_name}_sample_{idx}",
                        text=req_text,
                        task_type=task_type,
                        model_name=model_name
                    )

                    elapsed_time = (time.time() - start_time) * 1000  # Convert to ms

                    # Extract metrics
                    tokens_used = req_response.get("tokens_used", 0) if isinstance(req_response, dict) else 0
                    quality_score = req_response.get("quality_score", 0.5) if isinstance(req_response, dict) else 0.5

                    result.add_result(elapsed_time, tokens_used, quality_score)

                except Exception as e:
                    result.add_result(0, 0, 0, str(e))

        except Exception as e:
            result.add_result(0, 0, 0, f"Benchmark setup error: {str(e)}")

        return result

    def benchmark_multiple_models(
        self,
        models: List[str],
        task_type: str,
        dataset_name: str,
        num_samples: int = 20,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """Benchmark multiple models"""

        results = []

        for model in models:
            print(f"Benchmarking {model} on {task_type} with {dataset_name}...")

            result = self.benchmark_model(
                model,
                task_type,
                dataset_name,
                num_samples,
                timeout
            )

            summary = result.get_summary()
            results.append(summary)

        return {
            "task_type": task_type,
            "dataset": dataset_name,
            "num_samples": num_samples,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }

    def benchmark_all_models(self, num_samples: int = 10) -> Dict[str, Any]:
        """Run comprehensive benchmarking across all models and tasks"""

        all_results = {
            "timestamp": datetime.now().isoformat(),
            "benchmarks": []
        }

        models = ["ollama", "groq", "openai", "claude", "gemini"]
        tasks = ["extraction", "classification", "ner", "question_answering", "test_generation"]

        for task in tasks:
            print(f"\n=== Benchmarking task: {task} ===")

            # Find compatible dataset
            compatible_datasets = self.TASK_DATASET_COMPATIBILITY.get(task, ["Pure"])
            dataset = compatible_datasets[0]

            # Benchmark models for this task
            benchmark_result = self.benchmark_multiple_models(
                models,
                task,
                dataset,
                num_samples
            )

            all_results["benchmarks"].append(benchmark_result)

        return all_results


class BenchmarkReporter:
    """Generate reports from benchmark results"""

    @staticmethod
    def print_text_report(benchmark_result: Dict[str, Any]) -> str:
        """Generate text report"""

        report = f"\n{'='*80}\n"
        report += f"BENCHMARK REPORT\n"
        report += f"{'='*80}\n\n"

        report += f"Task: {benchmark_result.get('task_type')}\n"
        report += f"Dataset: {benchmark_result.get('dataset')}\n"
        report += f"Samples: {benchmark_result.get('num_samples')}\n"
        report += f"Timestamp: {benchmark_result.get('timestamp')}\n\n"

        report += f"{'Model':<15} {'Avg Time':<15} {'Tokens':<15} {'Success%':<15}\n"
        report += f"{'-'*60}\n"

        for result in benchmark_result.get("results", []):
            model = result.get("model", "Unknown")[:14]
            avg_time = result.get("avg_response_time_ms", "N/A")[:14]
            tokens = result.get("avg_tokens_used", "N/A")[:14]
            success = result.get("success_rate", "N/A")[:14]

            report += f"{model:<15} {str(avg_time):<15} {str(tokens):<15} {str(success):<15}\n"

        report += f"{'='*80}\n"

        return report

    @staticmethod
    def save_json_report(benchmark_result: Dict[str, Any], filename: str):
        """Save benchmark result as JSON"""

        with open(filename, 'w') as f:
            json.dump(benchmark_result, f, indent=2)

        return filename


def run_quick_benchmark(models: List[str], task_type: str, dataset: str, num_samples: int = 10) -> Dict[str, Any]:
    """Quick benchmark utility function for API integration"""

    benchmark = ModelBenchmark()
    return benchmark.benchmark_multiple_models(
        models,
        task_type,
        dataset,
        num_samples
    )


if __name__ == "__main__":
    # Example usage
    benchmark = ModelBenchmark()

    # Quick benchmark
    result = benchmark.benchmark_multiple_models(
        ["ollama", "groq"],
        "extraction",
        "Pure",
        num_samples=5
    )

    # Print report
    reporter = BenchmarkReporter()
    print(reporter.print_text_report(result))

    # Save results
    reporter.save_json_report(result, "benchmark_results.json")
