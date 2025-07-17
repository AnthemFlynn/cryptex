# Examples

Real-world examples showing how to use Cryptex in different scenarios and frameworks.

## Available Examples

### [Basic Usage](basic-usage.md)
Simple examples demonstrating core Cryptex functionality with common secret types.

**What you'll learn:**
- Single secret protection
- Multiple secrets in one function
- Built-in pattern usage
- Error handling

**Use this when:** You're getting started with Cryptex

---

### FastAPI Integration
Complete FastAPI application with Cryptex protecting API endpoints that use secrets.

**What you'll learn:**
- Web framework integration
- Request/response protection
- Background task isolation
- API documentation with protected secrets

**Use this when:** Building web APIs that handle secrets

---

### Real World Usage
Complex application simulating real production scenarios with multiple services and secret types.

**What you'll learn:**
- Multi-service architecture
- Custom pattern registration
- Performance optimization
- Error handling and logging

**Use this when:** Understanding production-ready implementations

## Quick Start

Each example includes:

- **Complete source code** with detailed comments
- **Installation instructions** for dependencies
- **Expected output** showing AI vs tool perspectives
- **Explanation** of key concepts demonstrated

## Running Examples

### Prerequisites

```bash
# Install Cryptex
pip install cryptex-ai

# Or with uv
uv add cryptex-ai
```

### Basic Example

```bash
# Clone the repository
git clone https://github.com/anthemflynn/cryptex.git
cd cryptex

# Run basic example
python examples/basic_usage.py
```

### Web Framework Example

```bash
# Install FastAPI dependencies
pip install fastapi uvicorn

# Run FastAPI example
python examples/fastapi_example.py
```

### Production Example

```bash
# Install all dependencies
pip install -r examples/requirements.txt

# Run real-world example
python examples/real_world_usage.py
```

## Example Categories

### 🚀 Getting Started
- [Basic Usage](basic-usage.md) - Core functionality demonstration

### 🌐 Web Frameworks  
- [FastAPI Integration](fastapi.md) - RESTful API with secret protection

### 🏢 Production Ready
- [Real World Usage](real-world.md) - Multi-service production patterns

### 📋 Common Patterns

Each example follows these patterns:

```python
from cryptex import protect_secrets

# 1. Import and decorate
@protect_secrets(secrets=["openai_key", "github_token"])
async def protected_function(api_key: str, token: str) -> str:
    # 2. Use secrets normally
    result = await external_api_call(api_key, token)
    return result

# 3. Call function with real secrets
result = await protected_function(
    "sk-real-openai-key-here",
    "ghp_real-github-token-here"  
)

# AI sees: protected_function("{{OPENAI_API_KEY}}", "{{GITHUB_TOKEN}}")
# Function gets: real secrets for execution
```

## Understanding the Examples

### AI Perspective vs Tool Perspective

Each example demonstrates the **temporal isolation** principle:

=== "AI Perspective"

    ```python
    # What AI systems see:
    ai_function("{{OPENAI_API_KEY}}", "{{GITHUB_TOKEN}}")
    
    # Logs show:
    INFO: Processing with key: {{OPENAI_API_KEY}}
    INFO: Repository: {{GITHUB_TOKEN}}
    ```

=== "Tool Perspective"

    ```python
    # What the actual function receives:
    ai_function("sk-abc123def456...", "ghp_xyz789abc123...")
    
    # Function executes with real secrets:
    openai_client = OpenAI(api_key="sk-abc123def456...")
    github_client = Github("ghp_xyz789abc123...")
    ```

### Performance Demonstration

Examples include timing demonstrations:

```python
import time

@protect_secrets(secrets=["openai_key"])
async def timed_example(api_key: str) -> str:
    start = time.perf_counter()
    
    result = await process_with_api_key(api_key)
    
    duration = time.perf_counter() - start
    print(f"Total time: {duration:.3f}s (includes <5ms Cryptex overhead)")
    
    return result
```

## Extending the Examples

### Adding Custom Patterns

Most examples show how to extend with custom patterns:

```python
from cryptex.patterns import register_pattern

# Add your organization's patterns
register_pattern("company_token", r"ct_[a-f0-9]{32}", "{{COMPANY_TOKEN}}")

@protect_secrets(secrets=["company_token"])
async def company_function(token: str) -> str:
    return await company_api_call(token)
```

### Framework Integration

Examples demonstrate integration patterns for:

- **Web frameworks** (FastAPI, Django, Flask)
- **AI frameworks** (LangChain, LlamaIndex) 
- **Task queues** (Celery, RQ)
- **Cloud functions** (AWS Lambda, Google Cloud Functions)

## Example Testing

Each example includes test cases:

```python
# test_example.py
import pytest
from examples.basic_usage import protected_function

@pytest.mark.asyncio
async def test_protection():
    # Test with realistic secret formats
    result = await protected_function("sk-test-key-format-abc123")
    
    # Verify function executed correctly
    assert result is not None
    assert "processed" in result.lower()
```

## Common Patterns Across Examples

### 1. Application Startup

```python
from cryptex.patterns import register_pattern

def setup_patterns():
    """Register any custom patterns at startup"""
    register_pattern("app_secret", r"as_[a-f0-9]{32}", "{{APP_SECRET}}")

def main():
    setup_patterns()  # Register patterns first
    # Start application
```

### 2. Error Handling

```python
from cryptex.core.exceptions import CryptexError

@protect_secrets(secrets=["openai_key"])
async def robust_function(api_key: str) -> str:
    try:
        return await external_api_call(api_key)
    except CryptexError as e:
        logger.error(f"Secret protection error: {e}")
        raise
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise
```

### 3. Logging Best Practices

```python
import logging

@protect_secrets(secrets=["github_token"])
async def logged_function(token: str) -> str:
    # Safe: logs show placeholder
    logger.info(f"Processing with token: {token}")  # Logs: {{GITHUB_TOKEN}}
    
    result = await github_api_call(token)  # Gets real token
    
    # Safe: no secrets in result logging
    logger.info(f"Operation completed successfully")
    
    return result
```

## Next Steps

After exploring the examples:

1. **[Installation Guide](../guide/installation.md)** - Set up Cryptex in your project
2. **[Basic Usage Guide](../guide/basic-usage.md)** - Learn all the features
3. **[API Reference](../api/)** - Complete API documentation
4. **[Custom Patterns](../guide/custom-patterns.md)** - Create organization-specific patterns

## Contributing Examples

Have a great Cryptex example? We'd love to include it! See our [Contributing Guide](../development/contributing.md) for how to submit examples.