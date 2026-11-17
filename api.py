"""
FastAPI REST Interface for TestDesignerAI
Provides REST endpoints for the RE pipeline with automatic failover

Endpoints:
- POST /api/process - Process requirements
- GET /api/health - Provider health status
- GET /api/stats - Usage statistics
- POST /api/batch - Batch processing
- POST /api/benchmark - Run benchmark tests
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from pipeline import REPipeline
from llm_interface_v2 import get_provider_health_status, get_available_providers
from config import AppConfig

try:
    from benchmarking import ModelBenchmark
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
    llm_model: Optional[str] = "auto"

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
    """Process a single requirement through the pipeline"""
    try:
        import time
        start_time = time.time()
        
        # Process requirement
        result = pipeline.process_requirement(
            input_data.req_id,
            input_data.text
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Update statistics
        stats.total_requests += 1
        if hasattr(result, 'tokens_used'):
            stats.total_tokens += result.tokens_used
        
        logger.info(f"Processed {input_data.req_id} in {processing_time:.2f}ms")
        
        return RequirementResponse(
            req_id=input_data.req_id,
            input_text=input_data.text,
            status="success",
            result={"classification": "functional", "entities": []},
            provider_used=getattr(result, 'provider', 'unknown'),
            tokens_used=getattr(result, 'tokens_used', 0),
            processing_time_ms=processing_time,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Processing failed for {input_data.req_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
