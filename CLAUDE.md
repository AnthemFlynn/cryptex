# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cryptex is a **zero-config** temporal isolation engine for AI/LLM applications. It provides bulletproof secrets isolation with **zero cognitive overhead** - one decorator line = complete temporal isolation.

**Key Philosophy**: No config files, no environment variables, no setup required. Built-in patterns handle 95% of real-world usage.

## Key Directories

- `src/cryptex/`: Main library source code
  - `decorators/`: Universal decorator implementation
  - `patterns/`: Pattern system with base classes and registry
  - `core/`: Temporal isolation engine and security components
- `tests/`: Comprehensive test suite (unit, integration, security, performance)
- `examples/`: Working examples demonstrating zero-config usage
- `Makefile`: Development workflow automation
- `.github/`: CI/CD workflows

## Development Workflow

### Available Command-Line Tools
- **uv**: A single tool to replace pip, pip-tools, pipx, poetry, pyenv, twine, virtualenv, and more. See: https://github.com/astral-sh/uv
- **zoxide**: A fast alternative to cd that learns your habits. See: https://github.com/ajeetdsouza/zoxide
- **eza**: A replacement for 'ls'. See: https://github.com/eza-community/eza
- **fd**: A simple, fast and user-friendly alternative to find. See: https://github.com/sharkdp/fd

### Essential Make Commands

```bash
# Development setup
make dev-setup              # Complete environment setup
make test                   # Run all tests
make lint                   # Code quality checks
make format                 # Code formatting
make pre-commit             # All quality gates

# Available as slash commands
/make:test, /make:lint, /make:format, etc.
```

### Available Development Tools

#### ast-grep
- **Purpose**: Structural code search and transformation for Python
- **Usage**: `ast-grep <pattern>` for code analysis, refactoring, and quality checks
- **Documentation**: https://ast-grep.github.io/reference/cli.html

#### GitHub CLI (gh)
- **Purpose**: GitHub repository management and automation
- **Usage**: `gh <command>` for issues, PRs, releases, and repository operations

## Quality Gates

**MANDATORY - These must be followed:**

- **All CI workflows must pass before code changes may be reviewed**
- **Every bug must be reproduced by a unit test before being fixed**
- **Every new feature must be covered by a unit test before it is implemented**
- **The existing code structure must not be changed without a strong reason**

## Core API Patterns

### Universal Decorator (95% of users)
```python
from cryptex import protect_secrets

# Works immediately - no setup required!
@protect_secrets(["openai_key"])
async def ai_tool(prompt: str, api_key: str) -> str:
    # AI sees: ai_tool("Hello", "{{OPENAI_API_KEY}}")
    # Function gets: real API key for execution
    return await openai_call(prompt, api_key)

@protect_secrets(["file_path", "github_token"])
async def file_tool(file_path: str, token: str) -> str:
    # AI sees: file_tool("/{USER_HOME}/.../{filename}", "{{GITHUB_TOKEN}}")
    # Function gets: real path and token
    return await process_file(file_path, token)
```

### Convenience Decorators
```python
from cryptex import protect_api_keys, protect_files, protect_all

@protect_api_keys()  # Protects OpenAI + Anthropic keys
async def ai_function(openai_key: str, anthropic_key: str) -> str:
    return await dual_ai_call(openai_key, anthropic_key)

@protect_files()  # Protects file system paths
async def file_function(file_path: str) -> str:
    return await process_file(file_path)

@protect_all()  # Protects all built-in patterns
async def comprehensive_function(api_key: str, file_path: str, db_url: str) -> str:
    return await complex_processing(api_key, file_path, db_url)
```

### Custom Patterns (5% of users)
```python
from cryptex import register_pattern, protect_secrets

# Register custom pattern once
register_pattern(
    name="slack_token",
    regex=r"xoxb-[0-9-a-zA-Z]{51}",
    placeholder="{{SLACK_TOKEN}}",
    description="Slack bot token"
)

# Use immediately in decorators
@protect_secrets(["slack_token"])
async def slack_tool(token: str) -> str:
    return await slack_api_call(token)
```

### Built-in Patterns (Work Out of the Box)
- `openai_key`: OpenAI API keys (sk-...)
- `anthropic_key`: Anthropic API keys (sk-ant-...)
- `github_token`: GitHub tokens (ghp_...)
- `file_path`: User file system paths (/Users/..., /home/...)
- `database_url`: Database connection URLs (postgres://, mysql://, etc.)

## Testing Approach

### Test Structure
- `tests/unit/`: Unit tests for core components
- `tests/integration/`: End-to-end integration tests
- `tests/security/`: Security-specific test suite
- `tests/performance/`: Performance benchmarks

### Testing Rules
- **Every test case may contain only one assertion**
- **Every test must assert at least once**
- **Test cases must be as short as possible**
- **Tests must use random values as inputs**
- **Tests must not use mocks, favoring fake objects and stubs**

### Running Tests
```bash
make test                    # All tests
make test-unit               # Unit tests only
make test-security           # Security tests only
make test-performance        # Performance benchmarks
```

## Zero-Config Architecture

**NO CONFIGURATION REQUIRED!** The library works perfectly without any config files.

### Current Architecture (Post-Refactor)
- **Universal Decorator**: Single `@protect_secrets` decorator works with any Python function
- **Pattern Registry**: Thread-safe registry with Protocol-based design
- **Zero Dependencies**: Pure Python 3.11+ standard library
- **SOLID Principles**: Clean abstractions and single responsibility

### Pattern Registration API (Advanced)
```python
from cryptex import register_pattern, list_patterns, get_all_patterns

# List available patterns
patterns = list_patterns()  # ['openai_key', 'anthropic_key', ...]

# Get all pattern objects
all_patterns = get_all_patterns()

# Register custom pattern (rare use case)
register_pattern("my_token", r"myapp-[a-f0-9]{32}", "{{MY_TOKEN}}")
```

## Performance Requirements

- **Sanitization Latency**: <5ms for 1KB payloads
- **Resolution Latency**: <10ms for 10 placeholders
- **Memory Overhead**: <5% of application memory
- **Zero Startup Time**: No dependencies, no config loading

## Development Notes

- **Zero-Config Philosophy**: No config files belong in middleware libraries
- **95/5 Rule**: 95% of users need zero config, 5% use registration API
- **Universal Approach**: Works with any Python function (async/sync)
- **Type Safety**: Full type hints using Python 3.11+ features
- **Zero Dependencies**: Core functionality uses standard library only
- **Security First**: Every change requires security review and validation

## Architecture Principles

1. **Universal Decorator**: Single decorator pattern replaces framework-specific middleware
2. **Built-in Defaults**: Excellent patterns for common secrets (OpenAI, GitHub, etc.)
3. **Minimal API Surface**: Simple registration for custom patterns
4. **Zero Dependencies**: No external packages, no supply chain attacks
5. **SOLID Design**: Protocol-based extensibility with clean abstractions

## Key Files and Components

### Core Implementation
- `src/cryptex/__init__.py`: Main public API exports
- `src/cryptex/decorators/protect_secrets.py`: Universal decorator implementation
- `src/cryptex/patterns/`: Complete pattern system
  - `__init__.py`: Public pattern API
  - `base.py`: Protocol and base classes
  - `registry.py`: Thread-safe pattern registry

### Security Architecture
- **Temporal Isolation**: Three-phase sanitization → AI processing → resolution
- **Pattern Validation**: Runtime regex validation and error handling
- **Thread Safety**: Concurrent access protection with proper locking
- **Zero Attack Surface**: No config files, no parsing, no external dependencies

## Common Development Tasks

### Adding New Built-in Patterns
1. Add pattern to `DEFAULT_PATTERNS` in `src/cryptex/patterns/base.py`
2. Test pattern matching in `tests/unit/test_pattern_registration.py`
3. Update documentation in README.md

### Extending Core Functionality
1. Maintain SOLID principles and Protocol-based design
2. Ensure thread safety for concurrent access
3. Add comprehensive tests for new functionality
4. Validate security implications

### Performance Optimization
1. Maintain <5ms sanitization for 1KB payloads
2. Keep memory overhead <5% of application memory
3. Benchmark changes with `tests/performance/`
4. Document performance impact

## Framework Integration Examples

### FastMCP
```python
from fastmcp import FastMCPServer
from cryptex import protect_secrets

server = FastMCPServer("my-server")

@server.tool()
@protect_secrets(["openai_key"])
async def ai_tool(prompt: str, api_key: str) -> str:
    return await openai_call(prompt, api_key)
```

### FastAPI
```python
from fastapi import FastAPI
from cryptex import protect_secrets

app = FastAPI()

@app.post("/secure")
@protect_secrets(["database_url", "openai_key"])
async def secure_endpoint(data: dict, db_url: str, api_key: str):
    return await process_data(data, db_url, api_key)
```

### Any Python Function
```python
from cryptex import protect_secrets

@protect_secrets(["github_token"])
def sync_function(token: str) -> str:
    return github_api_call(token)

@protect_secrets(["openai_key"])
async def async_function(api_key: str) -> str:
    return await openai_call(api_key)
```

## Important Notes for Claude

- **Architecture Changed**: No more middleware - everything uses universal decorator
- **Import Pattern**: Always use `from cryptex import protect_secrets`
- **Zero Dependencies**: Never suggest adding external dependencies
- **Security Focus**: Every change requires security consideration
- **Test Coverage**: All new functionality must have comprehensive tests
- **Performance Awareness**: Maintain strict performance requirements