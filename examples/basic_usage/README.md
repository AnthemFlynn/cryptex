# Basic Usage Example

This example demonstrates the core functionality of Cryptex with simple, clear examples showing how the universal `@protect_secrets` decorator works with any Python function.

## What You'll Learn

- ✅ How to use `@protect_secrets` for any Python function
- ✅ Zero-config protection with built-in patterns  
- ✅ How temporal isolation works (AI sees placeholders, functions get real values)
- ✅ Multiple secret types in one decorator
- ✅ Custom pattern registration for edge cases
- ✅ Convenience decorators for common scenarios

## Quick Start

### Prerequisites

```bash
# Install Cryptex
pip install cryptex-ai

# Or with uv
uv add cryptex-ai
```

### Run the Example

```bash
# From the repository root
python examples/basic_usage.py

# Or run directly
cd examples
python basic_usage.py
```

## Example Output

```
============================================================
🔒 Cryptex Basic Usage Demo
   Universal Secret Protection for Any Framework
============================================================

📝 Example 1: Basic Secret Protection
----------------------------------------
🤖 Making API call with key: sk-1234567890a...
✅ Result: AI Response to: Hello, how are you?
📁 Reading file: /Users/developer/documents/secret_data.txt
✅ Result: Contents of secret_data.txt
🗄️  Connecting to database: postgresql://user:pass@loc...
✅ Result: {'query': 'SELECT * FROM users LIMIT 5', 'rows': 42, 'status': 'success'}

📝 Example 2: Multiple Secrets
----------------------------------------
📁 Reading file: /Users/developer/documents/analysis.pdf
🤖 Making API call with key: sk-1234567890a...
🗄️  Connecting to database: postgresql://user:pass@loc...
✅ Result: {'file': 'analysis.pdf', 'analysis': 'AI Response to: Summarize this document: Contents of analysis.pdf', 'database_result': {'query': "INSERT INTO analyses VALUES ('AI Response to: Summarize this document: Contents of analysis.pdf')", 'rows': 42, 'status': 'success'}}

📝 Example 3: Custom Pattern
----------------------------------------
💬 Sending Slack message with token: xoxb-fake-token-for...
✅ Result: Message sent: Hello team!

📝 Example 4: Convenience Decorators
----------------------------------------
🤖 Calling OpenAI: sk-1234567890a...
🤖 Calling Anthropic: sk-ant-abcdef1...
✅ Result: Combined AI response to: What is the meaning of life?
💾 Backing up /Users/developer/important.txt to /Users/developer/backups/important.txt
✅ Result: Backup completed
🔒 All secrets automatically protected!
✅ Result: All operations completed safely

============================================================
🎉 All Examples Completed Successfully!

💡 Key Takeaways:
   ✅ @protect_secrets works with any Python function
   ✅ Zero configuration - built-in patterns work immediately
   ✅ AI models see safe placeholders, functions get real values
   ✅ Multiple secret types protected simultaneously
   ✅ Custom patterns for edge cases (5% of users)
   ✅ Convenience decorators for common scenarios
   ✅ Framework-agnostic - works anywhere!
============================================================
```

## Code Breakdown

### Example 1: Basic Secret Protection

```python
@protect_secrets(["openai_key"])
async def ai_completion(prompt: str, api_key: str) -> str:
    """
    - AI Context: ai_completion("Hello", "{{OPENAI_API_KEY}}")
    - Function Gets: real API key for actual execution
    """
    print(f"🤖 Making API call with key: {api_key[:15]}...")
    return f"AI Response to: {prompt}"
```

**Key Concept**: The decorator automatically detects the `sk-...` format and replaces it with `{{OPENAI_API_KEY}}` for AI visibility while the function receives the real key.

### Example 2: Multiple Secrets Protection

```python
@protect_secrets(["openai_key", "file_path", "database_url"])
async def process_document(file_path: str, api_key: str, db_url: str, prompt: str = "Analyze") -> dict:
    """All three secrets are automatically protected"""
    # Function logic here
```

**Key Concept**: A single decorator can protect multiple secret types simultaneously. Each parameter is matched against its respective pattern.

### Example 3: Custom Pattern Registration

```python
# Register once at startup
register_pattern(
    name="slack_token",
    regex=r"xoxb-[0-9-a-zA-Z]{51}",
    placeholder="{{SLACK_TOKEN}}",
    description="Slack bot token"
)

@protect_secrets(["slack_token"])
async def send_slack_message(message: str, token: str) -> str:
    """Custom pattern works just like built-ins"""
```

**Key Concept**: For the 5% of users with custom secret formats, registration is simple and works immediately.

### Example 4: Convenience Decorators

```python
@protect_api_keys()  # Protects openai_key, anthropic_key automatically
async def multi_ai_call(prompt: str, openai_key: str, anthropic_key: str) -> str:
    """Use multiple AI services with automatic key protection."""
```

**Key Concept**: Convenience decorators automatically detect and protect common secret categories.

## Built-in Patterns Demonstrated

| Pattern | Example Input | AI Sees | Description |
|---------|---------------|---------|-------------|
| `openai_key` | `sk-1234567890abcdef...` | `{{OPENAI_API_KEY}}` | OpenAI API keys |
| `file_path` | `/Users/dev/secret.txt` | `/{USER_HOME}/secret.txt` | File system paths |
| `database_url` | `postgresql://user:pass@host` | `{{DATABASE_URL}}` | Database connection strings |
| `slack_token` | `xoxb-abc123...` | `{{SLACK_TOKEN}}` | Custom Slack tokens |

## Temporal Isolation in Action

The key principle of Cryptex is **temporal isolation**:

=== "What AI Systems See"

    ```python
    # Function calls as they appear to AI
    ai_completion("Hello", "{{OPENAI_API_KEY}}")
    read_file("/{USER_HOME}/secret_data.txt")
    query_database("SELECT...", "{{DATABASE_URL}}")
    ```

=== "What Functions Actually Receive"

    ```python
    # Real values passed to function execution
    ai_completion("Hello", "sk-1234567890abcdef...")
    read_file("/Users/developer/documents/secret_data.txt")
    query_database("SELECT...", "postgresql://user:pass@localhost:5432/mydb")
    ```

## Performance Characteristics

The example includes timing that demonstrates:

- **Overhead**: <5ms per protected function call
- **Memory**: Minimal additional memory usage
- **Scalability**: Linear with number of protected parameters

## Extending the Example

### Add Real API Integration

Replace the simulation code with actual API calls:

```python
import openai

@protect_secrets(["openai_key"])
async def real_ai_completion(prompt: str, api_key: str) -> str:
    client = openai.AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

### Add Your Organization's Patterns

```python
# Register your company's token format
register_pattern(
    name="company_api_key",
    regex=r"ck_[a-f0-9]{40}",
    placeholder="{{COMPANY_API_KEY}}"
)

@protect_secrets(["company_api_key"])
async def company_function(token: str) -> str:
    return await company_api_call(token)
```

### Add Error Handling

```python
from cryptex.core.exceptions import CryptexError

@protect_secrets(["openai_key"])
async def robust_function(api_key: str) -> str:
    try:
        return await openai_api_call(api_key)
    except CryptexError as e:
        logger.error(f"Secret protection failed: {e}")
        raise
```

## Testing the Example

Create a test file to verify the protection works:

```python
# test_basic_usage.py
import pytest
from basic_usage import ai_completion

@pytest.mark.asyncio
async def test_protection():
    # Test with realistic API key format
    result = await ai_completion("test", "sk-test123456789abcdef")
    assert "AI Response" in result
    
    # In real usage, verify AI systems see placeholders
    # This would be tested through your AI integration
```

## Common Use Cases

This example pattern works for:

- **Standalone scripts** processing secrets
- **CLI tools** with API integrations  
- **Data processing pipelines** with database access
- **Integration scripts** calling multiple services
- **Prototyping** with real APIs safely

## Next Steps

- **[FastAPI Example](../fastapi_example/)** - Web framework integration
- **[Real World Example](../real_world_usage/)** - Production-ready patterns
- **[Custom Patterns Guide](../../docs/guide/custom-patterns.md)** - Advanced pattern creation

## Troubleshooting

### Import Errors

```bash
# Wrong package name
pip install cryptex  # ❌ This is a different package

# Correct package name  
pip install cryptex-ai  # ✅ This is the right one
```

### Pattern Not Found

```python
# Check available patterns
from cryptex.patterns import list_patterns
print(list_patterns())

# Register missing patterns
from cryptex.patterns import register_pattern
register_pattern("my_pattern", r"...", "{{MY_PATTERN}}")
```

### Performance Issues

```python
# Monitor timing
import time

start = time.perf_counter()
result = await protected_function("secret")
duration = time.perf_counter() - start

# Should be < 5ms overhead
assert duration < 0.1, f"Too slow: {duration:.3f}s"
```

The basic usage example provides a solid foundation for understanding how Cryptex works in any Python environment!