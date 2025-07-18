"""
Cryptex - Zero-Config Temporal Isolation Engine for AI/LLM Applications

Bulletproof secrets isolation with zero cognitive overhead.
One decorator line = complete temporal isolation.

## Zero Configuration Required!

Cryptex works perfectly without any configuration files, environment variables,
or setup. Built-in patterns handle 95% of real-world usage.

### Quick Start - Zero Config
```python
from cryptex_ai import protect_secrets

# Works immediately - no config needed!
@protect_secrets(secrets=["openai_key"])
async def ai_tool(prompt: str, api_key: str) -> str:
    # AI sees: ai_tool("Hello", "{{OPENAI_API_KEY}}")
    # Tool gets: real API key for execution
    return await openai_call(prompt, api_key)

@protect_secrets(secrets=["file_path", "github_token"])
async def file_tool(file_path: str, token: str) -> str:
    # AI sees: file_tool("/{USER_HOME}/doc.txt", "{{GITHUB_TOKEN}}")
    # Tool gets: real path and token
    with open(file_path, 'r') as f:
        return await github_api_call(f.read(), token)
```

### Built-in Patterns (Work Out of the Box)
- `openai_key`: OpenAI API keys (sk-...)
- `anthropic_key`: Anthropic API keys (sk-ant-...)
- `github_token`: GitHub tokens (ghp-...)
- `file_path`: User file system paths (/Users/..., /home/...)
- `database_url`: Database connection URLs (postgres://, mysql://, etc.)

### Advanced: Custom Patterns (5% of users)
```python
from cryptex_ai import register_pattern, protect_secrets

# Register custom pattern once
register_pattern(
    name="slack_token",
    regex=r"xoxb-[0-9-a-zA-Z]{51}",
    placeholder="{{SLACK_TOKEN}}"
)

# Use in decorators
@protect_secrets(secrets=["slack_token"])
async def slack_tool(token: str) -> str:
    return await slack_api_call(token)
```

## Architecture

### Three-Phase Security Model
1. **Sanitization**: Convert secrets to `{{PLACEHOLDER}}` templates
2. **AI Processing**: AI processes data with placeholders, never real secrets
3. **Resolution**: Convert placeholders back to real values for tool execution

### Temporal Isolation Guarantees
- **AI Context**: Sees safe placeholders like `{{OPENAI_API_KEY}}` or `/{USER_HOME}/...`
- **Tool Execution**: Gets real values for actual operations
- **Response Sanitization**: Tool outputs cleaned before returning to AI
- **Context Expiration**: Automatic cleanup prevents secret accumulation

## Performance
- **<5ms** sanitization latency for 1KB payloads
- **<10ms** resolution latency for 10 placeholders
- **<5%** memory overhead vs unprotected applications
- **Zero config loading time** (no file I/O)

## Security Features
- **Complete isolation**: AI models never see real secret values
- **Zero attack surface**: No config files, no parsing, no external dependencies
- **Pattern validation**: Built-in patterns tested against real-world secrets
- **Response sanitization**: Tool outputs cleaned before AI access

For comprehensive documentation and examples:
https://github.com/AnthemFlynn/cryptex-ai
"""

__version__ = "0.3.2"
__author__ = "AnthemFlynn"
__email__ = "noreply@github.com"

# Core components
from .core.api import secure_session
from .core.engine import (
    ResolvedData,
    SanitizedData,
    SecretPattern,
    TemporalIsolationEngine,
)
from .core.exceptions import CryptexError, SecurityError
from .core.manager import SecretManager

# Main decorator - the primary API
from .decorators import (
    protect_all,
    protect_api_keys,
    protect_database,
    protect_files,
    protect_secrets,
    protect_tokens,
)

# Pattern registration API
from .patterns import (
    clear_custom_patterns,
    get_all_patterns,
    get_pattern,
    list_patterns,
    register_pattern,
    register_patterns,
    unregister_pattern,
)

__all__ = [
    # Main API - what 95% of users need
    "protect_secrets",
    "secure_session",
    # Convenience decorators
    "protect_files",
    "protect_api_keys",
    "protect_tokens",
    "protect_database",
    "protect_all",
    # Pattern registration API
    "register_pattern",
    "unregister_pattern",
    "list_patterns",
    "get_pattern",
    "get_all_patterns",
    "clear_custom_patterns",
    "register_patterns",
    # Core components (advanced usage)
    "TemporalIsolationEngine",
    "SecretPattern",
    "SanitizedData",
    "ResolvedData",
    "SecretManager",
    "CryptexError",
    "SecurityError",
]
