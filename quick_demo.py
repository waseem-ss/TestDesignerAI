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
