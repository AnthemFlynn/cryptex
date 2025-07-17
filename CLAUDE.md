# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cryptex is a **zero-config** temporal isolation engine for AI/LLM applications. It provides bulletproof secrets isolation with **zero cognitive overhead** - one decorator line = complete temporal isolation.

**Key Philosophy**: No config files, no environment variables, no setup required. Built-in patterns handle 95% of real-world usage.

## Key Directories

- `src/cryptex/`: Main library source code
- `tests/`: Comprehensive test suite (unit, integration, security, performance)
- `.claude/`: Claude Code commands and configuration
- `Makefile`: Development workflow automation
- `.github/`: CI/CD workflows

## Development Workflow

### Available Command-Line Tools
uv - A single tool to replace pip, pip-tools, pipx, poetry, pyenv, twine, virtualenv, and more. See: https://github.com/ajeetdsouza/uv
zoxide - A fast alternative to cd that learns your habits See: https://github.com/ajeetdsouza/zoxide
eza - A replacement for 'ls' See: https://github.com/eza-community/eza
fd - A simple, fast and user-friendly alternative to find. See: https://github.com/sharkdp/fd


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

### Zero-Config Protection (95% of users)
```python
from cryptex.decorators.mcp import protect_tool

# Works immediately - no setup required!
@protect_tool(secrets=["openai_key"])
async def ai_tool(prompt: str, api_key: str) -> str:
    # AI sees: ai_tool("Hello", "{{OPENAI_API_KEY}}")
    # Tool gets: real API key for execution
    return await openai_call(prompt, api_key)

@protect_tool(secrets=["file_path", "github_token"])
async def file_tool(file_path: str, token: str) -> str:
    # AI sees: file_tool("/{USER_HOME}/doc.txt", "{{GITHUB_TOKEN}}")
    # Tool gets: real path and token
    return await process_file(file_path, token)
```

### Custom Patterns (5% of users)
```python
from cryptex.patterns import register_pattern

# Register custom pattern once
register_pattern(
    name="slack_token",
    regex=r"xoxb-[0-9-a-zA-Z]{51}",
    placeholder="{{SLACK_TOKEN}}"
)

# Use in decorators
@protect_tool(secrets=["slack_token"])
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

### Pattern Registration API (Advanced)
```python
from cryptex.patterns import register_pattern, list_patterns

# List available patterns
patterns = list_patterns()  # ['openai_key', 'anthropic_key', ...]

# Register custom pattern (rare use case)
register_pattern("my_token", r"myapp-[a-f0-9]{32}", "{{MY_TOKEN}}")
```

## Performance Requirements

- **Sanitization Latency**: <5ms for 1KB payloads
- **Resolution Latency**: <10ms for 10 placeholders
- **Memory Overhead**: <5% of application memory

## Development Notes

- **Zero-Config Philosophy**: No config files belong in middleware libraries
- **95/5 Rule**: 95% of users need zero config, 5% use registration API
- **Async-First Design**: All core operations are async/await compatible
- **Type Safety**: Full type hints using Python 3.13+ features
- **Zero Dependencies**: Core functionality uses standard library only
- **Security First**: Every change requires security review and validation

## Architecture Principles

1. **Config files eliminated**: Pure code-based configuration only
2. **Built-in defaults**: Excellent patterns for common secrets (OpenAI, GitHub, etc.)
3. **Minimal API surface**: Simple registration for custom patterns
4. **No external dependencies**: No TOML parsing, file I/O, or config loading
5. **Middleware library**: Lightweight, fast startup, predictable behavior

# The Developer's Pact: Our Rules of Engagement
_This document outlines the core principles and conventions we will follow in this project. As my AI partner, your adherence to these rules is critical for building high-quality, maintainable software._

### 🏛️ Principle 1: Architecture & Structure
- **Modularity is Key:** No single file should exceed 500 lines. If it grows too large, your first step is to propose a refactoring plan to break it into smaller, logical modules.

- **Consistent Organization:** We group files by feature. For example, a new `user` feature would have its logic in `src/users/`, its API routes in `src/api/routes/users.py`, and its tests in `tests/users/`.

- **Clean Imports:** Use absolute imports for clarity (e.g., `from src.utils import helpers`). Avoid circular dependencies.

- **Environment First:** All sensitive keys, API endpoints, or configuration variables must be managed through a `.env` file and loaded using `python-dotenv`. Never hardcode them.

### ✅ Principle 2: Quality & Reliability
- **Test Everything That Matters:** Every new function, class, or API endpoint must be accompanied by unit tests in the tests/ directory.

- **The Test Triad:** For each feature, provide at least three tests:

  1. A "happy path" test for expected behavior.

  2. An "edge case" test for unusual but valid inputs.

  3. A "failure case" test for expected errors or invalid inputs.

- **Docstrings are Non-Negotiable:** Every function must have a Google-style docstring explaining its purpose, arguments (`Args:`), and return value (`Returns:`).

### ✍️ Principle 3: Code & Style
- **Follow the Standards:** All Python code must be formatted with `black` and adhere to `PEP8` guidelines.

- **Type Safety:** Use type hints for all function signatures and variables. We use `mypy` to enforce this.

- **Data Certainty:** Use `pydantic` for all data validation, especially for API request and response models. This is our single source of truth for data shapes.

### 🧠 Principle 4: Your Behavior as an AI
- **Clarify, Don't Assume:** If a requirement is ambiguous or context is missing, your first action is to ask for clarification.

- **No Hallucinations:** Do not invent libraries, functions, or file paths. If you need a tool you don't have, state what you need and why.

- **Plan Before You Code:** For any non-trivial task, first outline your implementation plan in a list or with pseudocode. We will approve it before you write the final code.

- **Explain the "Why":** For complex or non-obvious blocks of code, add a `# WHY:` comment explaining the reasoning behind the implementation choice.

### External File Loading

CRITICAL: When you encounter a file reference (e.g., @rules/general.md), use your Read tool to load it on a need-to-know basis. They're relevant to the SPECIFIC task at hand.

Instructions:

- Do NOT preemptively load all references - use lazy loading based on actual need
- When loaded, treat content as mandatory instructions that override defaults
- Follow references recursively when needed
