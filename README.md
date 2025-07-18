# Cryptex

<div align="center">

**Zero-config temporal isolation for AI/LLM applications**

*Bulletproof secrets isolation with zero cognitive overhead*

[![Python Support](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![Package](https://img.shields.io/badge/package-cryptex--ai-blue)](https://github.com/AnthemFlynn/cryptex-ai)
[![Status](https://img.shields.io/badge/status-beta-orange)](https://github.com/AnthemFlynn/cryptex-ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/AnthemFlynn/cryptex-ai/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/AnthemFlynn/cryptex-ai/actions)
[![Coverage](https://codecov.io/gh/AnthemFlynn/cryptex-ai/branch/main/graph/badge.svg)](https://codecov.io/gh/AnthemFlynn/cryptex-ai)

[**Documentation**](https://anthemflynn.github.io/cryptex-ai/) | [**Examples**](./examples/) | [**PyPI** (Coming Soon)](#) | [**Changelog**](./CHANGELOG.md)

</div>

---

## The Problem

AI/LLM applications face an impossible choice:
- **Expose secrets to AI** → Security nightmare 🔓
- **Hide secrets completely** → Broken functionality 💥

## The Solution

Cryptex provides **temporal isolation** - AI sees safe placeholders while your code gets real secrets.

```python
from cryptex_ai import protect_secrets

# Works immediately - no config files required!
@protect_secrets(["openai_key"])
async def ai_tool(prompt: str, api_key: str) -> str:
    # AI sees: ai_tool("Hello", "{{OPENAI_API_KEY}}")  
    # Function gets: real API key for execution
    return await openai_call(prompt, api_key)
```

**One decorator line = complete temporal isolation** ✨

---

## 🚀 Key Features

- **🔧 Zero Configuration**: Works immediately, no setup required
- **⚡ Built-in Patterns**: OpenAI, Anthropic, GitHub, file paths, databases  
- **🛡️ Security First**: Zero dependencies, no config files, no parsing vulnerabilities
- **🚄 High Performance**: <5ms sanitization, <10ms resolution
- **🔗 Universal**: Works with any Python function - FastMCP, FastAPI, Django, Flask, etc.
- **📝 Simple API**: 95% of users need zero config, 5% get simple registration

---

## 📦 Installation

### Using pip (recommended)
```bash
pip install cryptex-ai
```

### Using uv (modern Python package manager)
```bash
uv add cryptex-ai
```

**Requirements**: Python 3.11+ • Zero dependencies

---

## ⚡ Quick Start

### Zero-Config Protection (95% of users)

Cryptex works immediately with built-in patterns for common secrets:

```python
from cryptex_ai import protect_secrets

# Protect OpenAI API calls
@protect_secrets(["openai_key"])
async def ai_completion(prompt: str, api_key: str) -> str:
    # AI context: "{{OPENAI_API_KEY}}"
    # Function execution: "sk-real-key-here..."
    return await openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        api_key=api_key
    )

# Protect file operations  
@protect_secrets(["file_path"])
async def read_file(file_path: str) -> str:
    # AI context: "/{USER_HOME}/.../{filename}"
    # Function execution: "/Users/alice/secrets/document.txt"
    with open(file_path, 'r') as f:
        return f.read()

# Protect multiple secrets at once
@protect_secrets(["github_token", "file_path", "database_url"])
async def process_data(repo_path: str, token: str, db_url: str) -> dict:
    # All secrets automatically protected
    data = await fetch_from_github(repo_path, token)
    result = await process_ai_data(data)
    await save_to_database(result, db_url)
    return result
```

### Convenience Decorators

For common patterns, use convenience decorators:

```python
from cryptex_ai import protect_api_keys, protect_files, protect_all

@protect_api_keys()  # Protects OpenAI + Anthropic keys
async def ai_function(openai_key: str, anthropic_key: str) -> str:
    # Both API keys automatically protected
    pass

@protect_files()  # Protects file system paths
async def file_function(file_path: str) -> str:
    # File paths automatically protected
    pass

@protect_all()  # Protects all built-in patterns
async def comprehensive_function(api_key: str, file_path: str, db_url: str) -> str:
    # Everything automatically protected
    pass
```

---

## 🛠️ Built-in Patterns

Cryptex includes battle-tested patterns that handle **95% of real-world usage**:

| Pattern | Detects | Example | Placeholder |
|---------|---------|---------|-------------|
| `openai_key` | OpenAI API keys | `sk-...` | `{{OPENAI_API_KEY}}` |
| `anthropic_key` | Anthropic API keys | `sk-ant-...` | `{{ANTHROPIC_API_KEY}}` |
| `github_token` | GitHub tokens | `ghp_...` | `{{GITHUB_TOKEN}}` |
| `file_path` | User file paths | `/Users/...`, `/home/...` | `/{USER_HOME}/.../{filename}` |
| `database_url` | Database URLs | `postgres://...`, `mysql://...` | `{{DATABASE_URL}}` |

**No configuration required** - patterns work out of the box! 📦

---

## 🔧 Custom Patterns (Advanced - 5% of users)

For edge cases, register custom patterns programmatically:

```python
from cryptex_ai import register_pattern, protect_secrets

# Register custom pattern once
register_pattern(
    name="slack_token",
    regex=r"xoxb-[0-9-a-zA-Z]{51}",
    placeholder="{{SLACK_TOKEN}}",
    description="Slack bot token"
)

# Use immediately in decorators
@protect_secrets(["slack_token"])
async def slack_integration(token: str) -> str:
    return await slack_api_call(token)

# Bulk registration
from cryptex_ai import register_patterns
register_patterns([
    ("discord_token", r"[MNO][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}", "{{DISCORD_TOKEN}}"),
    ("custom_key", r"myapp-[a-f0-9]{32}", "{{CUSTOM_KEY}}")
])
```

---

## 🏗️ Framework Examples

### FastMCP Tools

```python
from fastmcp import FastMCPServer
from cryptex_ai import protect_secrets

server = FastMCPServer("my-server")

@server.tool()
@protect_secrets(["openai_key"])
async def ai_tool(prompt: str, api_key: str) -> str:
    # MCP sees: ai_tool("Hello", "{{OPENAI_API_KEY}}")
    # Tool gets: real API key for execution
    return await openai_call(prompt, api_key)
```

### FastAPI Endpoints

```python
from fastapi import FastAPI
from cryptex_ai import protect_secrets

app = FastAPI()

@app.post("/api/process")
@protect_secrets(["database_url", "openai_key"])
async def process_endpoint(data: dict, db_url: str, api_key: str):
    # Request/response logs show placeholders
    # Endpoint gets real secrets for execution
    return await process_with_secrets(data, db_url, api_key)
```

### Django Views

```python
from django.http import JsonResponse
from cryptex_ai import protect_secrets

@protect_secrets(["database_url"])
async def django_view(request, db_url: str):
    # Django logs show placeholders
    # View gets real database URL
    return JsonResponse(await query_database(db_url))
```

### Any Python Function

```python
from cryptex_ai import protect_secrets

@protect_secrets(["github_token"])
def sync_function(token: str) -> str:
    # Works with sync functions too!
    return github_api_call(token)

@protect_secrets(["openai_key"])
async def async_function(api_key: str) -> str:
    # And async functions
    return await openai_call(api_key)
```

---

## ⚡ Performance

Cryptex is designed for production workloads:

| Metric | Performance | Context |
|--------|-------------|---------|
| **Sanitization** | <5ms | 1KB payloads |
| **Resolution** | <10ms | 10 placeholders |
| **Memory Overhead** | <5% | vs unprotected apps |
| **Startup Time** | 0ms | Zero dependencies |
| **Throughput** | >1000 req/s | Typical workloads |

*Benchmarked on MacBook Pro M1, Python 3.11*

---

## 🏗️ Architecture

### Three-Phase Temporal Isolation

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Raw Secrets   │    │   AI Processing  │    │ Tool Execution  │
│                 │    │                  │    │                 │
│ sk-abc123...    │───▶│ {{OPENAI_KEY}}   │───▶│ sk-abc123...    │
│ /Users/alice/   │    │ /{USER_HOME}/    │    │ /Users/alice/   │
│ ghp_xyz789...   │    │ {{GITHUB_TOKEN}} │    │ ghp_xyz789...   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
     Phase 1:              Phase 2:              Phase 3: 
  Sanitization          AI sees safe          Resolution for
  for AI context       placeholders          tool execution
```

### Zero-Config Philosophy

- **🚫 No Attack Surface**: No config files to inject, no parsing to exploit
- **⚡ Lightning Fast**: Zero file I/O, zero parsing overhead  
- **🎯 Middleware Focused**: Lightweight, predictable, zero dependencies
- **👨‍💻 Developer Friendly**: Works immediately, no setup friction
- **🔒 Security First**: Configuration in version-controlled code only

---

## 📚 Examples

Explore comprehensive examples in the [`examples/`](./examples/) directory:

- **[Basic Usage](./examples/basic_usage.py)**: Zero-config protection patterns
- **[FastAPI Integration](./examples/fastapi_example.py)**: Web API protection  
- **[Real World Usage](./examples/real_world_usage.py)**: Complex multi-pattern scenarios

Run examples locally:

```bash
git clone https://github.com/AnthemFlynn/cryptex-ai.git
cd cryptex-ai
python examples/basic_usage.py
```

---

## 🛡️ Security

Cryptex follows security-first principles:

- **Zero Dependencies**: No external packages, no supply chain attacks
- **Zero Config Files**: No TOML parsing, no injection attacks
- **Minimal Attack Surface**: No file I/O, pure Python standard library  
- **Secure by Default**: Built-in patterns tested against real-world secrets
- **Audit Trail**: Full temporal isolation with context tracking
- **Pattern Validation**: Runtime regex validation and comprehensive error handling

**Security Policy**: See [SECURITY.md](./SECURITY.md) for vulnerability reporting.

---

## 🧪 Testing

### Using pip
```bash
# Install dependencies
pip install -e ".[dev]"

# Run test suite
make test

# Run with coverage
make test-coverage

# Performance benchmarks
make test-performance

# Security tests
make test-security
```

### Using uv
```bash
# Install dependencies
uv sync --dev

# Run test suite
uv run make test

# Run with coverage
uv run make test-coverage

# Performance benchmarks
uv run make test-performance

# Security tests
uv run make test-security
```

---

## 🤝 Contributing

We welcome contributions! Cryptex follows a **zero-config philosophy** - keep it simple.

### Quick Development Setup

```bash
git clone https://github.com/AnthemFlynn/cryptex-ai.git
cd cryptex-ai
make dev-setup  # Sets up environment
make test       # Run test suite
make lint       # Code quality checks
make format     # Code formatting
```

### Development Guidelines

- **Zero-Config First**: No configuration files in middleware libraries
- **Security First**: Every change requires security review
- **Performance Matters**: <5ms sanitization, <10ms resolution
- **Test Everything**: Every bug gets a test, every feature gets tests
- **SOLID Principles**: Clean architecture and abstractions

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

---

## 📈 Roadmap

- **v0.3.0**: Enhanced pattern validation and error reporting
- **v0.4.0**: Advanced caching and performance optimizations  
- **v0.5.0**: Plugin system for custom secret sources
- **v1.0.0**: Production hardening and stability guarantees

---

## 📜 License

MIT License - see [LICENSE](./LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastMCP Community**: For excellent MCP server patterns
- **FastAPI**: For inspiring clean API design  
- **Python Community**: For async/await and type system excellence
- **Security Researchers**: For temporal isolation concepts

---

<div align="center">

**Made with ❤️ for the AI/LLM community**

[⭐ Star us on GitHub](https://github.com/AnthemFlynn/cryptex-ai) | [📖 Read the Docs](https://anthemflynn.github.io/cryptex-ai/) | [💬 Join Discussions](https://github.com/AnthemFlynn/cryptex-ai/discussions)

</div>