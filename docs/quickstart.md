# Quick Start

Get up and running with Cryptex-AI in minutes - no configuration required!

## Installation

Choose your preferred installation method:

=== "pip (default)"

    ```bash
    pip install cryptex-ai
    ```

=== "uv (modern package manager)"

    ```bash
    uv add cryptex-ai
    ```

## Your First Protection

Let's protect an OpenAI API call:

```python
from cryptex_ai import protect_secrets
import openai

@protect_secrets(secrets=["openai_key"])
async def chat_with_ai(prompt: str, api_key: str) -> str:
    """AI sees placeholder, tool gets real key"""
    client = openai.AsyncOpenAI(api_key=api_key)

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

# Usage
result = await chat_with_ai(
    "Hello!",
    "sk-your-actual-openai-key-here"
)
```

**What happens:**

1. **AI Request**: AI sees `chat_with_ai("Hello!", "{{OPENAI_API_KEY}}")`
2. **Tool Execution**: Function receives real API key
3. **Complete Isolation**: AI never sees the actual secret

## Built-in Patterns

Cryptex-AI recognizes these patterns automatically:

| Pattern | Example | Placeholder |
|---------|---------|-------------|
| `openai_key` | `sk-abc123...` | `{{OPENAI_API_KEY}}` |
| `anthropic_key` | `sk-ant-abc123...` | `{{ANTHROPIC_API_KEY}}` |
| `github_token` | `ghp_abc123...` | `{{GITHUB_TOKEN}}` |
| `file_path` | `/Users/john/secret.txt` | `/{USER_HOME}/secret.txt` |
| `database_url` | `postgres://user:pass@host` | `{{DATABASE_URL}}` |

## Multiple Secrets

Protect multiple secrets in one decorator:

```python
@protect_secrets(secrets=["github_token", "file_path"])
async def process_repo(token: str, config_path: str) -> dict:
    """Protect both GitHub token and file paths"""
    # AI sees: process_repo("{{GITHUB_TOKEN}}", "/{USER_HOME}/config.json")
    # Tool gets: real token and actual file path

    with open(config_path) as f:
        config = json.load(f)

    # Use real GitHub token for API calls
    headers = {"Authorization": f"token {token}"}
    # ... rest of implementation
```

## Custom Patterns (Advanced)

For the 5% of users who need custom patterns:

```python
from cryptex_ai.patterns import register_pattern

# Register once in your application
register_pattern(
    name="slack_token",
    regex=r"xoxb-[0-9-a-zA-Z]{51}",
    placeholder="{{SLACK_TOKEN}}"
)

# Use immediately
@protect_secrets(secrets=["slack_token"])
async def send_slack_message(token: str, message: str) -> bool:
    # AI sees: send_slack_message("{{SLACK_TOKEN}}", "Hello team!")
    # Tool gets: real Slack token
    pass
```

## Error Handling

Cryptex-AI provides clear error messages:

```python
@protect_secrets(secrets=["nonexistent_pattern"])
async def bad_function(secret: str) -> str:
    pass

# Raises: PatternNotFoundError with helpful message
```

## Performance Monitoring

Check if your application meets performance requirements:

```python
import time
from cryptex_ai import protect_secrets

@protect_secrets(secrets=["openai_key"])
async def timed_function(api_key: str) -> str:
    start = time.perf_counter()
    # Your function implementation
    duration = time.perf_counter() - start

    # Should be < 5ms for sanitization + resolution
    assert duration < 0.015, f"Too slow: {duration:.3f}s"

    return "result"
```

## Next Steps

- **[Basic Usage Guide](guide/basic-usage.md)**: Learn all the features
- **[Examples](examples/index.md)**: See real-world implementations
- **[Custom Patterns](guide/custom-patterns.md)**: Create organization-specific patterns

## Zero Configuration Promise

**Remember**: Cryptex-AI requires ZERO configuration files, environment variables, or setup steps. If you find yourself creating config files, you're overcomplicating it!
