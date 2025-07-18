# Cryptex-AI

**Zero-config temporal isolation engine for AI/LLM applications**

Cryptex-AI provides bulletproof secrets isolation with **zero cognitive overhead** - one decorator line = complete temporal isolation.

## Key Philosophy

**No config files, no environment variables, no setup required.** Built-in patterns handle 95% of real-world usage.

## Quick Start

### Installation

=== "pip (recommended)"

    ```bash
    pip install cryptex-ai
    ```

=== "uv (modern)"

    ```bash
    uv add cryptex-ai
    ```

### Basic Usage

```python
from cryptex_ai import protect_secrets

# Works immediately - no setup required!
@protect_secrets(secrets=["openai_key"])
async def ai_tool(prompt: str, api_key: str) -> str:
    # AI sees: ai_tool("Hello", "{{OPENAI_API_KEY}}")
    # Tool gets: real API key for execution
    return await openai_call(prompt, api_key)
```

## Core Features

- **Zero Configuration**: No config files, environment variables, or setup
- **Built-in Patterns**: OpenAI, Anthropic, GitHub tokens work out of the box
- **Temporal Isolation**: AI sees placeholders, tools get real secrets
- **High Performance**: <5ms sanitization, <10ms resolution latency
- **Type Safe**: Full Python 3.11+ type hints
- **Zero Dependencies**: Standard library only

## Architecture

```mermaid
graph LR
    A[AI Request] --> B[Decorator]
    B --> C[Sanitization]
    C --> D[AI Processing]
    D --> E[Resolution]
    E --> F[Tool Execution]
    
    C -.->|"sk-123 → {{OPENAI_KEY}}"| D
    E -.->|"{{OPENAI_KEY}} → sk-123"| F
```

## Performance Requirements

- **Sanitization Latency**: <5ms for 1KB payloads
- **Resolution Latency**: <10ms for 10 placeholders  
- **Memory Overhead**: <5% of application memory

## Zero-Config Philosophy

Cryptex-AI follows the **95/5 rule**:

- **95% of users** need zero configuration - built-in patterns handle common secrets
- **5% of users** use the registration API for custom patterns

No middleware library should require configuration files.

---

Ready to get started? Check out our [Quick Start Guide](quickstart.md) or explore [Examples](examples/index.md).