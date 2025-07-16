# Cryptex

<div align="center">

**Zero-config temporal isolation for AI/LLM applications**

*Bulletproof secrets isolation with zero cognitive overhead*

[![PyPI version](https://badge.fury.io/py/cryptex.svg)](https://badge.fury.io/py/cryptex)
[![Python Support](https://img.shields.io/pypi/pyversions/cryptex.svg)](https://pypi.org/project/cryptex/)
[![Downloads](https://static.pepy.tech/badge/cryptex)](https://pepy.tech/project/cryptex)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/anthemflynn/cryptex/workflows/Tests/badge.svg)](https://github.com/anthemflynn/cryptex/actions)
[![Coverage](https://codecov.io/gh/anthemflynn/cryptex/branch/main/graph/badge.svg)](https://codecov.io/gh/anthemflynn/cryptex)

[**Documentation**](https://cryptex.readthedocs.io) | [**Examples**](./examples/) | [**PyPI**](https://pypi.org/project/cryptex/) | [**Changelog**](./CHANGELOG.md)

</div>

---

## The Problem

AI/LLM applications face an impossible choice:
- **Expose secrets to AI** → Security nightmare 🔓
- **Hide secrets completely** → Broken functionality 💥

## The Solution

Cryptex provides **temporal isolation** - AI sees safe placeholders while tools get real secrets.

```python
from cryptex.decorators.mcp import protect_tool

# Works immediately - no config files required!
@protect_tool(secrets=["openai_key"])
async def ai_tool(prompt: str, api_key: str) -> str:
    # AI sees: ai_tool("Hello", "{{OPENAI_API_KEY}}")  
    # Tool gets: real API key for execution
    return await openai_call(prompt, api_key)
```

**One decorator line = complete temporal isolation** ✨

---

## 🚀 Key Features

- **🔧 Zero Configuration**: Works immediately, no setup required
- **⚡ Built-in Patterns**: OpenAI, Anthropic, GitHub, file paths, databases  
- **🛡️ Security First**: No config files, no parsing vulnerabilities
- **🚄 High Performance**: <5ms sanitization, <10ms resolution
- **🔗 Framework Agnostic**: FastMCP, FastAPI, any Python async/await
- **📝 Simple API**: 95% of users need zero config, 5% get simple registration

---

## 📦 Installation

```bash
pip install cryptex
```

**Requirements**: Python 3.8+

---

## ⚡ Quick Start

### Zero-Config Protection (95% of users)

Cryptex works immediately with built-in patterns for common secrets:

```python
from cryptex.decorators.mcp import protect_tool

# Protect OpenAI API calls
@protect_tool(secrets=["openai_key"])
async def ai_completion(prompt: str, api_key: str) -> str:
    # AI context: "{{OPENAI_API_KEY}}"
    # Tool execution: "sk-real-key-here..."
    return await openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        api_key=api_key
    )

# Protect file operations  
@protect_tool(secrets=["file_path"])
async def read_file(file_path: str) -> str:
    # AI context: "/{USER_HOME}/document.txt"
    # Tool execution: "/Users/alice/secrets/document.txt"
    with open(file_path, 'r') as f:
        return f.read()

# Protect multiple secrets
@protect_tool(secrets=["github_token", "file_path"])
async def git_operations(repo_path: str, token: str) -> str:
    # Both secrets automatically protected
    return await github_api_call(repo_path, token)
```

### FastAPI Integration

```python
from fastapi import FastAPI
from cryptex.decorators.fastapi import protect_endpoint

app = FastAPI()

@app.post("/api/process")
@protect_endpoint(secrets=["database_url", "openai_key"])
async def process_data(data: dict, db_url: str, api_key: str):
    # Request/response automatically sanitized
    # Endpoint gets real secrets for execution
    return await process_with_secrets(data, db_url, api_key)
```

---

## 🛠️ Built-in Patterns

Cryptex includes battle-tested patterns that handle **95% of real-world usage**:

| Pattern | Detects | Example | Placeholder |
|---------|---------|---------|-------------|
| `openai_key` | OpenAI API keys | `sk-...` | `{{OPENAI_API_KEY}}` |
| `anthropic_key` | Anthropic API keys | `sk-ant-...` | `{{ANTHROPIC_API_KEY}}` |
| `github_token` | GitHub tokens | `ghp_...` | `{{GITHUB_TOKEN}}` |
| `file_path` | User file paths | `/Users/...`, `/home/...` | `/{USER_HOME}/...` |
| `database_url` | Database URLs | `postgres://...`, `mysql://...` | `{{DATABASE_URL}}` |

**No configuration required** - patterns work out of the box! 📦

---

## 🔧 Custom Patterns (Advanced - 5% of users)

For edge cases, register custom patterns programmatically:

```python
from cryptex.patterns import register_pattern
from cryptex.decorators.mcp import protect_tool

# Register custom pattern once
register_pattern(
    name="slack_token",
    regex=r"xoxb-[0-9-a-zA-Z]{51}",
    placeholder="{{SLACK_TOKEN}}",
    description="Slack bot token"
)

# Use in decorators
@protect_tool(secrets=["slack_token"])
async def slack_integration(token: str) -> str:
    return await slack_api_call(token)

# Bulk registration
from cryptex.patterns import register_patterns
register_patterns(
    discord_token=(r"[MNO][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}", "{{DISCORD_TOKEN}}"),
    custom_key=(r"myapp-[a-f0-9]{32}", "{{CUSTOM_KEY}}")
)
```

---

## ⚡ Performance

Cryptex is designed for production workloads:

| Metric | Performance | Context |
|--------|-------------|---------|
| **Sanitization** | <5ms | 1KB payloads |
| **Resolution** | <10ms | 10 placeholders |
| **Memory Overhead** | <5% | vs unprotected apps |
| **Startup Time** | 0ms | No config loading |
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

### Why Zero Config?

- **🚫 No Attack Surface**: No config files to inject, no parsing to exploit
- **⚡ Lightning Fast**: Zero file I/O, zero parsing overhead  
- **🎯 Middleware Focused**: Lightweight, predictable, no external dependencies
- **👨‍💻 Developer Friendly**: Works immediately, no setup friction
- **🔒 Security First**: Configuration in version-controlled code only

---

## 🔗 Framework Support

### FastMCP Tools
```python
from fastmcp import FastMCPServer
from cryptex.decorators.mcp import protect_tool

server = FastMCPServer("my-server")

@server.tool()
@protect_tool(secrets=["openai_key"])
async def ai_tool(prompt: str, api_key: str) -> str:
    return await openai_call(prompt, api_key)
```

### FastAPI Endpoints
```python
from fastapi import FastAPI
from cryptex.decorators.fastapi import protect_endpoint

app = FastAPI()

@app.post("/secure")
@protect_endpoint(secrets=["database_url"]) 
async def secure_endpoint(data: dict, db_url: str):
    return await process_data(data, db_url)
```

### Universal Decorator
```python
from cryptex.decorators.cryptex import cryptex

# Auto-detects FastMCP or FastAPI context
@cryptex(secrets=["openai_key"])
async def universal_protection(api_key: str) -> str:
    return await ai_call(api_key)
```

---

## 📚 Examples

Explore comprehensive examples in the [`examples/`](./examples/) directory:

- **[Basic Usage](./examples/fastmcp/01_simple_hello_world.py)**: Zero-config protection
- **[FastAPI Integration](./examples/fastapi/01_simple_hello_world.py)**: Web API protection  
- **[Advanced Patterns](./examples/fastmcp/02_advanced_middleware.py)**: Custom patterns and middleware
- **[Performance Demo](./demo_new_architecture.py)**: Architecture showcase

---

## 🛡️ Security

Cryptex follows security-first principles:

- **Zero Config Files**: No TOML parsing, no injection attacks
- **Minimal Attack Surface**: No file I/O, no external dependencies  
- **Secure by Default**: Built-in patterns tested against real-world secrets
- **Audit Trail**: Full temporal isolation with context tracking
- **Pattern Validation**: Runtime regex validation and error handling

**Security Policy**: See [SECURITY.md](./SECURITY.md) for vulnerability reporting.

---

## 🤝 Contributing

We welcome contributions! Cryptex follows a **zero-config philosophy** - keep it simple.

- **[Contributing Guide](./CONTRIBUTING.md)**: How to contribute
- **[Code of Conduct](./CODE_OF_CONDUCT.md)**: Community standards  
- **[Security Policy](./SECURITY.md)**: Report security issues
- **[Architecture Docs](./docs/)**: Technical deep-dives

### Quick Development Setup

```bash
git clone https://github.com/anthemflynn/cryptex.git
cd cryptex
make dev-setup  # Sets up environment
make test       # Run test suite
make lint       # Code quality checks
```

---

## 📜 License

MIT License - see [LICENSE](./LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastMCP**: For excellent MCP server framework
- **FastAPI**: For inspiring API design patterns  
- **Python Community**: For async/await and type hints
- **Security Researchers**: For temporal isolation concepts

---

<div align="center">

**Made with ❤️ for the AI/LLM community**

[⭐ Star us on GitHub](https://github.com/anthemflynn/cryptex) | [📖 Read the Docs](https://cryptex.readthedocs.io) | [💬 Join Discussions](https://github.com/anthemflynn/cryptex/discussions)

</div>