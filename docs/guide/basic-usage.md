# Basic Usage

Learn the core features of Cryptex-AI for temporal isolation of secrets in AI/LLM applications.

## The Core Concept

Cryptex-AI provides **temporal isolation** - AI systems see placeholder values while tools receive real secrets:

```python
from cryptex_ai import protect_secrets

@protect_secrets(secrets=["openai_key"])
async def ai_tool(prompt: str, api_key: str) -> str:
    # AI Request: ai_tool("Hello", "{{OPENAI_API_KEY}}")
    # Tool Execution: receives actual API key
    return await process_with_real_key(api_key)
```

## Decorator Syntax

### Single Secret

Protect one type of secret:

```python
@protect_secrets(secrets=["github_token"])
async def github_api_call(token: str, repo: str) -> dict:
    headers = {"Authorization": f"token {token}"}
    # AI sees: github_api_call("{{GITHUB_TOKEN}}", "my-repo")
    # Function gets: real GitHub token
```

### Multiple Secrets

Protect multiple secret types:

```python
@protect_secrets(secrets=["openai_key", "database_url", "file_path"])
async def complex_operation(api_key: str, db_url: str, config_path: str) -> dict:
    # AI sees all placeholders, function gets real values
    config = load_config(config_path)  # Real file path
    db = connect(db_url)               # Real database URL
    ai_result = await openai_call(api_key)  # Real API key
    
    return {"ai": ai_result, "db": db.status}
```

## Built-in Pattern Matching

Cryptex automatically recognizes common secret patterns:

### API Keys

```python
@protect_secrets(secrets=["openai_key"])
async def openai_example(api_key: str) -> str:
    # Matches: sk-abc123... → {{OPENAI_API_KEY}}
    pass

@protect_secrets(secrets=["anthropic_key"])  
async def anthropic_example(api_key: str) -> str:
    # Matches: sk-ant-abc123... → {{ANTHROPIC_API_KEY}}
    pass
```

### Tokens and Credentials

```python
@protect_secrets(secrets=["github_token"])
async def github_example(token: str) -> str:
    # Matches: ghp_abc123... → {{GITHUB_TOKEN}}
    pass

@protect_secrets(secrets=["database_url"])
async def database_example(url: str) -> str:
    # Matches: postgres://user:pass@host → {{DATABASE_URL}}
    pass
```

### File Paths

```python
@protect_secrets(secrets=["file_path"])
async def file_example(path: str) -> str:
    # Matches: /Users/john/secret.txt → /{USER_HOME}/secret.txt
    # Matches: /home/user/config → /{USER_HOME}/config
    pass
```

## Function Signature Flexibility

Cryptex works with various function signatures:

### Positional Arguments

```python
@protect_secrets(secrets=["openai_key"])
async def positional_example(prompt: str, api_key: str, temperature: float = 0.7):
    # AI sees: positional_example("Hello", "{{OPENAI_API_KEY}}", 0.7)
    pass
```

### Keyword Arguments

```python
@protect_secrets(secrets=["github_token"])
async def keyword_example(repo: str, *, token: str, branch: str = "main"):
    # AI sees: keyword_example("my-repo", token="{{GITHUB_TOKEN}}", branch="main")
    pass
```

### Mixed Arguments

```python
@protect_secrets(secrets=["openai_key", "file_path"])
async def mixed_example(prompt: str, api_key: str, *, config_path: str, debug: bool = False):
    # AI sees mixed placeholders and real values appropriately
    pass
```

## Error Handling

### Pattern Not Found

```python
try:
    @protect_secrets(secrets=["nonexistent_pattern"])
    async def bad_function(secret: str):
        pass
except PatternNotFoundError as e:
    print(f"Pattern not found: {e}")
    # Suggests similar patterns or registration steps
```

### Invalid Usage

```python
from cryptex_ai.core.exceptions import CryptexError

try:
    result = await protected_function("invalid-input")
except CryptexError as e:
    print(f"Cryptex error: {e}")
    # Handle isolation or pattern matching errors
```

## Performance Considerations

### Latency Requirements

Cryptex is designed for high-performance applications:

```python
import time

@protect_secrets(secrets=["openai_key"])
async def performance_test(api_key: str) -> str:
    start = time.perf_counter()
    
    # Your implementation here
    result = await some_operation(api_key)
    
    duration = time.perf_counter() - start
    
    # Cryptex adds <5ms overhead for sanitization/resolution
    # Total should stay under your performance requirements
    assert duration < 0.100, f"Operation too slow: {duration:.3f}s"
    
    return result
```

### Memory Usage

Cryptex maintains minimal memory overhead:

```python
import tracemalloc

tracemalloc.start()

@protect_secrets(secrets=["openai_key"])
async def memory_test(api_key: str) -> str:
    # Cryptex adds <5% memory overhead
    return await process_data(api_key)

# Monitor memory usage in your application
current, peak = tracemalloc.get_traced_memory()
print(f"Memory usage: {current / 1024 / 1024:.2f} MB")
```

## Async/Sync Support

### Async Functions (Recommended)

```python
@protect_secrets(secrets=["openai_key"])
async def async_example(api_key: str) -> str:
    # Fully async - optimal performance
    return await async_operation(api_key)
```

### Sync Functions

```python
@protect_secrets(secrets=["openai_key"])
def sync_example(api_key: str) -> str:
    # Also supported, but async is preferred
    return sync_operation(api_key)
```

## Debugging and Logging

### Safe Logging

```python
import logging

@protect_secrets(secrets=["openai_key"])
async def logged_function(api_key: str) -> str:
    # Safe: logs show placeholder, not real key
    logging.info(f"Processing with key: {api_key}")  # Logs: {{OPENAI_API_KEY}}
    
    result = await process(api_key)  # Gets real key
    logging.info(f"Result: {result}")
    
    return result
```

### Development Mode

```python
# Enable debug mode to see pattern matching
import os
os.environ["CRYPTEX_DEBUG"] = "1"

@protect_secrets(secrets=["openai_key"])
async def debug_example(api_key: str) -> str:
    # Additional logging shows pattern matching process
    return await process(api_key)
```

## Best Practices

### 1. Use Type Hints

```python
@protect_secrets(secrets=["openai_key"])
async def typed_function(prompt: str, api_key: str) -> str:
    """Clear typing helps with development and debugging"""
    pass
```

### 2. Document Secret Requirements

```python
@protect_secrets(secrets=["github_token", "database_url"])
async def documented_function(token: str, db_url: str) -> dict:
    """
    Process GitHub data with database storage.
    
    Args:
        token: GitHub personal access token (ghp_...)
        db_url: PostgreSQL connection URL
        
    Returns:
        Processing results dictionary
    """
    pass
```

### 3. Keep Functions Focused

```python
# Good: Single responsibility
@protect_secrets(secrets=["openai_key"])
async def generate_text(prompt: str, api_key: str) -> str:
    return await openai_call(prompt, api_key)

# Better than: Multiple responsibilities in one function
@protect_secrets(secrets=["openai_key", "database_url", "file_path"])
async def do_everything(api_key: str, db_url: str, file_path: str) -> dict:
    # Too many responsibilities
    pass
```

### 4. Test with Real Patterns

```python
# In tests, use realistic secret formats
test_api_key = "sk-test-key-that-matches-real-pattern-abc123"
test_github_token = "ghp_test-token-matching-github-format-abc123"

result = await protected_function(test_api_key)
```

## Next Steps

- **[Zero Config Guide](zero-config.md)**: Learn about the zero-configuration philosophy
- **[Custom Patterns](custom-patterns.md)**: Create organization-specific patterns  
- **[Examples](../examples/index.md)**: See real-world implementations