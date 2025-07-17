# FastAPI Integration Example

This example demonstrates how to integrate Cryptex with FastAPI to build secure web APIs that protect secrets from AI visibility while maintaining clean, simple code.

## What You'll Learn

- ✅ How to protect FastAPI endpoints with `@protect_secrets`
- ✅ Clean integration without complex middleware
- ✅ Multiple secret types in web API endpoints
- ✅ Dependency injection with secret protection
- ✅ Real-world API patterns with temporal isolation
- ✅ Error handling and API documentation

## Quick Start

### Prerequisites

```bash
# Install required packages
pip install cryptex-ai fastapi uvicorn

# Or with uv
uv add cryptex-ai fastapi uvicorn
```

### Run the Server

```bash
# From the repository root
python examples/fastapi_example.py

# Or run directly
cd examples/fastapi_example
python fastapi_example.py
```

The server will start at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## Example Requests

### 1. Chat Endpoint (OpenAI Protection)

```bash
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Hello, how are you?",
       "model": "gpt-4"
     }'
```

**Response:**
```json
{
  "response": "AI response to: Hello, how are you?",
  "model": "gpt-4",
  "protected": true
}
```

### 2. File Analysis (Multiple Secrets)

```bash
curl -X POST "http://localhost:8000/api/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "file_path": "/Users/developer/documents/report.pdf",
       "prompt": "Summarize this document"
     }'
```

**Response:**
```json
{
  "file": "report.pdf",
  "analysis": "Analysis of report.pdf: Summarize this document",
  "protected": true
}
```

### 3. Data Processing (Database + GitHub)

```bash
curl -X POST "http://localhost:8000/api/process" \
     -H "Content-Type: application/json" \
     -d '{
       "data": {"key1": "value1", "key2": "value2"},
       "operation": "sync"
     }'
```

**Response:**
```json
{
  "operation": "sync",
  "processed_count": 2,
  "status": "completed",
  "protected": true
}
```

### 4. Kitchen Sink (All Secrets)

```bash
curl -X POST "http://localhost:8000/api/kitchen-sink?operation=full-sync" \
     -H "Content-Type: application/json"
```

**Response:**
```json
{
  "operation": "full-sync",
  "secrets_protected": ["openai_key", "database_url", "github_token"],
  "status": "all secrets safely isolated"
}
```

## Code Architecture

### Clean Decorator Integration

```python
@app.post("/api/chat")
@protect_secrets(["openai_key"])
async def chat_endpoint(
    request: ChatRequest,
    api_key: str = Depends(get_openai_key)
) -> dict[str, Any]:
    """
    The @protect_secrets decorator ensures:
    - Logs show: {"api_key": "{{OPENAI_API_KEY}}"}
    - Function gets: real API key for OpenAI calls
    """
    # Use real API key here
    response = await openai_call(request.message, api_key)
    return {"response": response}
```

**Key Benefits:**
- **No middleware complexity** - just add the decorator
- **Framework agnostic** - works with any FastAPI pattern
- **Clean separation** - secrets protection is declarative
- **Full compatibility** - works with all FastAPI features

### Dependency Injection Pattern

```python
def get_openai_key() -> str:
    """Get OpenAI API key from environment."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="API key not configured")
    return key

@app.post("/api/endpoint")
@protect_secrets(["openai_key"])
async def protected_endpoint(
    api_key: str = Depends(get_openai_key)  # Injected and protected
):
    # api_key is automatically protected by Cryptex
    pass
```

**Advantages:**
- **Environment separation** - keys come from environment variables
- **Error handling** - proper HTTP errors for missing secrets
- **Testability** - dependencies can be mocked for testing
- **Reusability** - same dependency across multiple endpoints

## Request/Response Flow

### Temporal Isolation in Web APIs

=== "AI/Logging Perspective"

    ```python
    # What appears in logs and AI context
    POST /api/chat
    {
        "api_key": "{{OPENAI_API_KEY}}",
        "message": "Hello world"
    }
    
    # Function call as seen by AI
    chat_endpoint(request, api_key="{{OPENAI_API_KEY}}")
    ```

=== "Function Execution"

    ```python
    # What the function actually receives
    POST /api/chat
    {
        "api_key": "sk-abc123def456...",  # Real API key
        "message": "Hello world"
    }
    
    # Function executes with real values
    chat_endpoint(request, api_key="sk-abc123def456...")
    ```

### Multiple Secrets Protection

```python
@app.post("/api/analyze")
@protect_secrets(["openai_key", "file_path"])
async def analyze_file_endpoint(
    request: AnalysisRequest,
    api_key: str = Depends(get_openai_key)
):
    """
    Both the API key and file path in request.file_path are protected:
    - API key: sk-abc123... → {{OPENAI_API_KEY}}
    - File path: /Users/dev/secret.txt → /{USER_HOME}/secret.txt
    """
```

## Server Output

When running the server, you'll see output like:

```
🚀 Starting Cryptex FastAPI Example
📍 Open: http://localhost:8000
📊 Docs: http://localhost:8000/docs
🔒 All endpoints protected with cryptex!

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000

# When making requests:
🤖 Processing chat with model: gpt-4
🔑 Using API key: {{OPENAI_API_K...
📁 Analyzing file: /{USER_HOME}/report.pdf
🔑 Using API key: {{OPENAI_API_K...
🗄️  Processing data with database: {{DATABASE_URL}}...
🐙 Using GitHub token: {{GITHUB_TOKEN}}...
```

**Notice**: All sensitive values show as placeholders in logs, but functions receive real values.

## API Documentation

FastAPI automatically generates interactive documentation at `/docs`:

![API Documentation](https://docs.example.com/fastapi-docs-screenshot.png)

The documentation shows:
- **Request schemas** with protected fields
- **Response examples** 
- **Try it out** functionality that works with real secrets
- **Security notes** about secret protection

## Production Deployment

### Environment Variables

```bash
# Required environment variables
export OPENAI_API_KEY="sk-your-real-openai-key"
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export GITHUB_TOKEN="ghp_your-real-github-token"

# Optional configuration
export CRYPTEX_DEBUG="false"
export LOG_LEVEL="INFO"
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Set environment variables (use secrets management)
ENV OPENAI_API_KEY=""
ENV DATABASE_URL=""
ENV GITHUB_TOKEN=""

# Run server
CMD ["uvicorn", "fastapi_example:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cryptex-fastapi
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cryptex-fastapi
  template:
    metadata:
      labels:
        app: cryptex-fastapi
    spec:
      containers:
      - name: app
        image: your-registry/cryptex-fastapi:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: openai-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: database-url
```

## Testing the Example

### Unit Testing

```python
# test_fastapi_example.py
import pytest
from fastapi.testclient import TestClient
from fastapi_example import app

client = TestClient(app)

def test_chat_endpoint():
    """Test chat endpoint with secret protection."""
    response = client.post(
        "/api/chat",
        json={"message": "Hello", "model": "gpt-4"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["protected"] is True
    assert "response" in data

def test_analyze_endpoint():
    """Test file analysis with multiple secrets."""
    response = client.post(
        "/api/analyze",
        json={
            "file_path": "/Users/test/document.pdf",
            "prompt": "Summarize"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["protected"] is True
    assert data["file"] == "document.pdf"
```

### Integration Testing

```python
import requests

def test_full_api_integration():
    """Test the API with real-like requests."""
    base_url = "http://localhost:8000"
    
    # Test chat
    response = requests.post(f"{base_url}/api/chat", json={
        "message": "Test message",
        "model": "gpt-4"
    })
    assert response.status_code == 200
    
    # Test analysis
    response = requests.post(f"{base_url}/api/analyze", json={
        "file_path": "/tmp/test.txt",
        "prompt": "Analyze this"
    })
    assert response.status_code == 200
```

## Performance Considerations

### Latency Impact

The FastAPI integration adds minimal overhead:

```python
import time
from fastapi import Request

@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Cryptex adds <5ms overhead
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

### Concurrent Requests

Cryptex is thread-safe and handles concurrent requests efficiently:

```python
import asyncio
import aiohttp

async def load_test():
    """Test concurrent requests to protected endpoints."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(100):
            task = session.post(
                "http://localhost:8000/api/chat",
                json={"message": f"Test {i}"}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
    # All requests should succeed with <5ms overhead per request
    assert all(r.status == 200 for r in responses)
```

## Security Features

### Automatic Secret Detection

Cryptex automatically detects and protects secrets in:

- **Request parameters** - API keys, tokens, file paths
- **Function arguments** - Dependency injection values
- **Log output** - All logging shows placeholders
- **Error messages** - No secrets leaked in exceptions

### Framework Integration Benefits

- **No middleware complexity** - Simple decorator approach
- **Full FastAPI compatibility** - Works with all features
- **Development friendly** - Immediate feedback and debugging
- **Production ready** - Zero-configuration deployment

## Common Patterns

### Background Tasks

```python
from fastapi import BackgroundTasks

@app.post("/api/background")
@protect_secrets(["openai_key"])
async def background_endpoint(
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_openai_key)
):
    """Background tasks also respect secret protection."""
    
    @protect_secrets(["openai_key"])
    async def background_task(api_key: str):
        # Protected background processing
        await process_with_ai(api_key)
    
    background_tasks.add_task(background_task, api_key)
    return {"status": "task scheduled"}
```

### WebSocket Support

```python
@app.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    api_key: str = Depends(get_openai_key)
):
    """WebSocket endpoints can use protected secrets."""
    await websocket.accept()
    
    @protect_secrets(["openai_key"])
    async def process_message(message: str, api_key: str) -> str:
        return await ai_chat(message, api_key)
    
    async for message in websocket.iter_text():
        response = await process_message(message, api_key)
        await websocket.send_text(response)
```

### Error Handling

```python
from fastapi import HTTPException
from cryptex.core.exceptions import CryptexError

@app.exception_handler(CryptexError)
async def cryptex_exception_handler(request: Request, exc: CryptexError):
    """Handle Cryptex-specific errors gracefully."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Secret protection error",
            "detail": "Please check your secret configuration",
            "type": "cryptex_error"
        }
    )
```

## Next Steps

- **[Real World Example](../real_world_usage/)** - Production-ready patterns
- **[Basic Usage](../basic_usage/)** - Core concepts and patterns
- **[Custom Patterns Guide](../../docs/guide/custom-patterns.md)** - Organization-specific secrets

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure FastAPI is installed: `pip install fastapi uvicorn`
2. **Secret Not Protected**: Check the decorator is applied correctly
3. **Environment Variables**: Ensure all required env vars are set
4. **Performance**: Monitor request timing with middleware

### Debug Mode

```python
import os
os.environ["CRYPTEX_DEBUG"] = "true"

# This will show detailed secret protection logs
```

The FastAPI integration example demonstrates how Cryptex provides enterprise-grade secret protection with minimal code changes and maximum developer productivity!