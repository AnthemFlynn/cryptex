#!/usr/bin/env python3
"""
FastAPI Integration Example - Simple and Clean

This example shows how to use cryptex with FastAPI using simple decorators
rather than complex middleware. This is the recommended approach.

Requirements:
    pip install cryptex-ai fastapi uvicorn

What you'll learn:
- How to protect FastAPI endpoints with @protect_secrets
- Clean integration without middleware complexity
- Real-world API patterns with secret protection
"""

import os
import sys
from typing import Any

# Add src to path for local development
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Simple imports - no middleware needed!
from cryptex_ai import protect_secrets

# FastAPI imports
try:
    from fastapi import Depends, FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except ImportError:
    print("❌ FastAPI not installed. Run: pip install fastapi uvicorn")
    exit(1)


# =============================================================================
# Pydantic Models
# =============================================================================

class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-4"

class AnalysisRequest(BaseModel):
    file_path: str
    prompt: str = "Analyze this file"

class ProcessRequest(BaseModel):
    data: dict[str, Any]
    operation: str = "process"


# =============================================================================
# FastAPI App Setup
# =============================================================================

app = FastAPI(
    title="Cryptex FastAPI Example",
    description="Secure API endpoints with cryptex secret protection",
    version="1.0.0"
)


# =============================================================================
# Dependency Functions (Clean Separation)
# =============================================================================

def get_openai_key() -> str:
    """Get OpenAI API key from environment."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    return key

def get_database_url() -> str:
    """Get database URL from environment."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise HTTPException(status_code=500, detail="Database URL not configured")
    return url

def get_github_token() -> str:
    """Get GitHub token from environment."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="GitHub token not configured")
    return token


# =============================================================================
# Protected API Endpoints
# =============================================================================

@app.post("/api/chat")
@protect_secrets(["openai_key"])
async def chat_endpoint(
    request: ChatRequest,
    api_key: str = Depends(get_openai_key)
) -> dict[str, Any]:
    """
    Chat endpoint with OpenAI API key protection.

    The @protect_secrets decorator ensures:
    - Logs show: {"api_key": "{{OPENAI_API_KEY}}"}
    - Function gets: real API key for OpenAI calls
    """
    # Simulate OpenAI API call
    print(f"🤖 Processing chat with model: {request.model}")
    print(f"🔑 Using API key: {api_key[:15]}...")

    # In real implementation, you'd call OpenAI here
    response = f"AI response to: {request.message}"

    return {
        "response": response,
        "model": request.model,
        "protected": True
    }


@app.post("/api/analyze")
@protect_secrets(["openai_key", "file_path"])
async def analyze_file_endpoint(
    request: AnalysisRequest,
    api_key: str = Depends(get_openai_key)
) -> dict[str, Any]:
    """
    File analysis endpoint with multiple secret protection.

    Protects both API key and file path:
    - Logs show: {"api_key": "{{OPENAI_API_KEY}}", "file_path": "/{USER_HOME}/.../{filename}"}
    - Function gets: real values for actual processing
    """
    print(f"📁 Analyzing file: {request.file_path}")
    print(f"🔑 Using API key: {api_key[:15]}...")

    # Simulate file reading and AI analysis
    try:
        # In real implementation, you'd read the file and call OpenAI
        analysis = f"Analysis of {request.file_path.split('/')[-1]}: {request.prompt}"

        return {
            "file": request.file_path.split('/')[-1],
            "analysis": analysis,
            "protected": True
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Analysis failed: {str(e)}")


@app.post("/api/process")
@protect_secrets(["database_url", "github_token"])
async def process_data_endpoint(
    request: ProcessRequest,
    db_url: str = Depends(get_database_url),
    github_token: str = Depends(get_github_token)
) -> dict[str, Any]:
    """
    Data processing endpoint with database and GitHub protection.

    Protects multiple secrets:
    - Logs show: {"db_url": "{{DATABASE_URL}}", "github_token": "{{GITHUB_TOKEN}}"}
    - Function gets: real values for actual operations
    """
    print(f"🗄️  Processing data with database: {db_url[:30]}...")
    print(f"🐙 Using GitHub token: {github_token[:20]}...")

    # Simulate data processing
    processed_count = len(request.data)

    # Simulate database save
    # In real implementation, you'd connect to database
    print(f"💾 Saved {processed_count} records to database")

    # Simulate GitHub API call
    # In real implementation, you'd call GitHub API
    print(f"📊 Updated GitHub with {request.operation} operation")

    return {
        "operation": request.operation,
        "processed_count": processed_count,
        "status": "completed",
        "protected": True
    }


# =============================================================================
# Convenience Endpoint (Multiple Secrets at Once)
# =============================================================================

from cryptex_ai import protect_all


@app.post("/api/kitchen-sink")
@protect_all()  # Protects all built-in secret types
async def kitchen_sink_endpoint(
    operation: str,
    api_key: str = Depends(get_openai_key),
    db_url: str = Depends(get_database_url),
    github_token: str = Depends(get_github_token)
) -> dict[str, Any]:
    """
    Endpoint that demonstrates protecting all secret types at once.

    The @protect_all decorator protects:
    - openai_key, anthropic_key, github_token, file_path, database_url
    """
    print(f"🔒 All secrets protected for operation: {operation}")

    return {
        "operation": operation,
        "secrets_protected": ["openai_key", "database_url", "github_token"],
        "status": "all secrets safely isolated"
    }


# =============================================================================
# Health Check (No Protection Needed)
# =============================================================================

@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint - no secrets involved."""
    return {"status": "healthy", "protection": "cryptex active"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "Cryptex FastAPI Example",
        "description": "Secure API with temporal secret isolation",
        "protected_endpoints": [
            "/api/chat",
            "/api/analyze",
            "/api/process",
            "/api/kitchen-sink"
        ],
        "cryptex_version": "0.2.0"
    }


# =============================================================================
# Environment Setup for Demo
# =============================================================================

def setup_demo_environment():
    """Set up mock environment variables for demo."""
    if not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "sk-" + "1234567890abcdef" * 3

    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql://user:secret@localhost:5432/mydb"

    if not os.getenv("GITHUB_TOKEN"):
        os.environ["GITHUB_TOKEN"] = "ghp_1234567890abcdef1234567890abcdef12345678"


# =============================================================================
# Development Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    # Setup demo environment
    setup_demo_environment()

    print("🚀 Starting Cryptex FastAPI Example")
    print("📍 Open: http://localhost:8000")
    print("📊 Docs: http://localhost:8000/docs")
    print("🔒 All endpoints protected with cryptex!")

    uvicorn.run(
        "fastapi_example:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
