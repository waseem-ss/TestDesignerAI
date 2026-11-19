"""
FastAPI REST Interface for TestDesignerAI
Provides REST endpoints for the RE pipeline with automatic failover

Endpoints:
- POST /api/process - Process requirements
- GET /api/health - Provider health status
- GET /api/stats - Usage statistics
- POST /api/batch - Batch processing
- POST /api/benchmark - Run benchmark tests
- GET /api/datasets, /api/templates, /api/models - Choices for test generation
- POST /api/test-generation - Generate test cases for a dataset (background job)
- GET /api/test-generation/{job_id}[/results], POST /api/test-generation/{job_id}/stop
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import time
from datetime import datetime

from backend.pipeline import REPipeline
from backend.llm_interface_v2 import get_provider_health_status, get_available_providers
from backend.config import AppConfig
from backend.llm_interface import OLLAMA_MODEL, list_ollama_models
from backend.llm_interface_v2 import (
    PROVIDER_KEY_ENV, default_model, model_choices, provider_key_configured, resolve_provider,
)
from backend.prompt_engineering import TEMPLATES
from backend.test_generation import get_job, list_datasets, request_stop, start_job
from backend.analytics import collect_run_stats
from backend.requirement_tasks import run_task
import json as _json
import os as _os

try:
    from backend.benchmarking import ModelBenchmark
except ImportError:
    ModelBenchmark = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TestDesignerAI API",
    description="AI-Powered Requirements Engineering Tool with LLM Failover",
    version="1.0.0"
)

# Enable CORS for web UI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RE Pipeline
pipeline = REPipeline()

# ============================================================================
# Request/Response Models
# ============================================================================

class RequirementInput(BaseModel):
    """Input model for single requirement"""
    req_id: str
    text: str
    task_type: Optional[str] = "extraction"
    dataset: Optional[str] = "Pure"
    provider: Optional[str] = "ollama"     # ollama, hf, gemini, groq (or openai, claude, auto)
    llm_model: Optional[str] = None        # model for that provider; None = the .env default

class BatchRequirementInput(BaseModel):
    """Input model for batch processing"""
    requirements: List[RequirementInput]

class RequirementResponse(BaseModel):
    """Response model for processed requirement"""
    req_id: str
    input_text: str
    status: str
    result: Dict[str, Any]
    provider_used: str
    tokens_used: int
    processing_time_ms: float
    timestamp: str

class HealthStatus(BaseModel):
    """Provider health status"""
    provider: str
    is_healthy: bool
    error_count: int
    last_error: Optional[str]

class APIStatus(BaseModel):
    """API overall status"""
    status: str
    timestamp: str
    available_providers: List[str]
    provider_health: Dict[str, Any]
    total_requests: int
    total_tokens: int

class BenchmarkInput(BaseModel):
    """Input model for benchmark testing"""
    models: List[str]
    task_type: str
    dataset: str
    num_samples: int = 10
    timeout: int = 60

class BenchmarkResult(BaseModel):
    """Benchmark result"""
    model: str
    task_type: str
    dataset: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: str
    avg_response_time_ms: str
    avg_tokens_used: str
    avg_quality_score: str
    timestamp: str

# ============================================================================
# Global Statistics
# ============================================================================

class APIStats:
    def __init__(self):
        self.total_requests = 0
        self.total_tokens = 0
        self.start_time = datetime.now()

stats = APIStats()

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "TestDesignerAI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/api/health", response_model=APIStatus)
async def get_health():
    """Get API and provider health status"""
    try:
        health_status = get_provider_health_status()
        available = get_available_providers()
        
        return APIStatus(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            available_providers=available,
            provider_health=health_status,
            total_requests=stats.total_requests,
            total_tokens=stats.total_tokens
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process", response_model=RequirementResponse)
async def process_requirement(input_data: RequirementInput):
    """Run one requirement through the chosen task and provider."""
    start_time = time.time()
    model = None if input_data.llm_model in (None, "", "auto") else input_data.llm_model
    try:
        result, tokens, provider_used = run_task(
            input_data.task_type or "extraction", input_data.req_id, input_data.text,
            input_data.provider or "ollama", model,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Processing failed for {input_data.req_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    processing_time = (time.time() - start_time) * 1000
    stats.total_requests += 1
    stats.total_tokens += tokens
    logger.info(f"Processed {input_data.req_id} with {provider_used} in {processing_time:.2f}ms")

    return RequirementResponse(
        req_id=input_data.req_id,
        input_text=input_data.text,
        status="success",
        result=result,
        provider_used=provider_used,
        tokens_used=tokens,
        processing_time_ms=processing_time,
        timestamp=datetime.now().isoformat(),
    )


@app.post("/api/batch")
async def batch_process(input_data: BatchRequirementInput):
    """Process multiple requirements"""
    try:
        results = []
        
        for req in input_data.requirements:
            try:
                result = await process_requirement(req)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch processing failed for {req.req_id}: {e}")
                results.append({
                    "req_id": req.req_id,
                    "error": str(e)
                })
        
        return {
            "total": len(results),
            "successful": sum(1 for r in results if "error" not in r),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get API usage statistics"""
    uptime = datetime.now() - stats.start_time
    
    return {
        "total_requests": stats.total_requests,
        "total_tokens": stats.total_tokens,
        "avg_tokens_per_request": stats.total_tokens / max(1, stats.total_requests),
        "uptime_seconds": uptime.total_seconds(),
        "available_providers": get_available_providers()
    }

@app.get("/api/analytics")
async def get_analytics():
    """Totals and breakdowns over every saved test-generation run, plus live API counters."""
    try:
        report = collect_run_stats()
    except Exception as e:
        logger.error(f"Analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    report["live"] = {
        "total_requests": stats.total_requests,
        "total_tokens": stats.total_tokens,
        "uptime_seconds": (datetime.now() - stats.start_time).total_seconds(),
    }
    return report

@app.get("/api/providers")
async def get_providers():
    """Get list of available providers"""
    return {
        "available": get_available_providers(),
        "health": get_provider_health_status()
    }

@app.post("/api/benchmark")
async def benchmark_models(input_data: BenchmarkInput):
    """Run benchmark tests on specified models"""
    try:
        if not ModelBenchmark:
            raise HTTPException(status_code=500, detail="Benchmarking module not available")

        # Validate inputs
        if not input_data.models:
            raise HTTPException(status_code=400, detail="At least one model must be specified")

        if not input_data.task_type:
            raise HTTPException(status_code=400, detail="Task type must be specified")

        if not input_data.dataset:
            raise HTTPException(status_code=400, detail="Dataset must be specified")

        logger.info(f"Starting benchmark: models={input_data.models}, task={input_data.task_type}, dataset={input_data.dataset}")

        # Run benchmark
        benchmark = ModelBenchmark()
        results = benchmark.benchmark_multiple_models(
            models=input_data.models,
            task_type=input_data.task_type,
            dataset_name=input_data.dataset,
            num_samples=input_data.num_samples,
            timeout=input_data.timeout
        )

        logger.info(f"Benchmark completed: {len(results.get('results', []))} models tested")

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Dataset Test Generation
# ============================================================================

class TestGenerationRequest(BaseModel):
    dataset: str                       # file name under data/, e.g. "promise_dataset.csv"
    template: str = "requirement_test_cases"
    provider: str = "ollama"           # ollama, groq, openai, claude, gemini or auto
    model: Optional[str] = None        # model for that provider; None = the .env default
    limit: Optional[int] = None        # first N rows; None or 0 = all rows


@app.get("/api/datasets")
async def get_datasets():
    """Every dataset file under data/ with its row count and detected columns."""
    return {"datasets": list_datasets()}


@app.get("/api/templates")
async def get_templates():
    """Prompt templates that can be used for test generation."""
    return {"templates": sorted(TEMPLATES)}


@app.get("/api/models")
async def get_models(provider: str = "ollama"):
    """Models for a provider. Ollama lists the models installed locally; cloud providers
    list the .env default plus common choices, and are empty when no API key is set."""
    provider = provider.lower()
    if provider == "auto":
        try:
            provider = resolve_provider("auto")
        except ValueError as e:
            raise HTTPException(status_code=503, detail=str(e))
    if provider == "ollama":
        try:
            models = list_ollama_models()
        except ConnectionError as e:
            raise HTTPException(status_code=503, detail=str(e))
        return {"provider": provider, "configured": True, "models": models, "default": OLLAMA_MODEL}
    if provider not in PROVIDER_KEY_ENV:
        raise HTTPException(status_code=400, detail=f"Unknown provider {provider!r}")
    configured = provider_key_configured(provider)
    return {
        "provider": provider, "configured": configured,
        "models": model_choices(provider) if configured else [],
        "default": default_model(provider),
    }


@app.post("/api/test-generation", status_code=202)
async def create_test_generation(req: TestGenerationRequest):
    """Start generating test cases for a dataset in the background. Returns a job to poll."""
    try:
        return start_job(req.dataset, req.template, req.provider, req.model, req.limit or None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/test-generation/{job_id}")
async def get_test_generation(job_id: str):
    """Status and progress of a generation job."""
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="unknown job id")
    return job


@app.get("/api/test-generation/{job_id}/results")
async def get_test_generation_results(job_id: str):
    """Generated test cases for a finished or stopped job."""
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="unknown job id")
    json_path = (job.get("summary") or {}).get("json_path")
    if json_path is None or not _os.path.exists(json_path):
        raise HTTPException(status_code=409, detail="no results saved yet")
    with open(json_path, encoding="utf-8") as f:
        return {"job_id": job_id, "results": _json.load(f)}


@app.post("/api/test-generation/{job_id}/stop")
async def stop_test_generation(job_id: str):
    """Stop a running job after the current row. Rows already saved are kept."""
    job = request_stop(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="unknown job id")
    return job


# ============================================================================
# Health Check Endpoint (for load balancers)
# ============================================================================

@app.get("/health")
async def health_check():
    """Simple health check for load balancers"""
    return {"status": "healthy"}

# ============================================================================
# Startup & Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("TestDesignerAI API starting...")
    logger.info(f"Available providers: {get_available_providers()}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("TestDesignerAI API shutting down...")
    logger.info(f"Total requests processed: {stats.total_requests}")
    logger.info(f"Total tokens used: {stats.total_tokens}")

# ============================================================================
# Run the API
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
