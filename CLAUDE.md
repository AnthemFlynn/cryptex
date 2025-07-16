# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cryptex is a production-ready Python library that provides bulletproof secrets isolation for AI/LLM applications. It implements a **Temporal Isolation Engine** with three-phase security architecture: Sanitization → AI Processing → Secret Resolution.

## Key Directories

- `src/cryptex/`: Main library source code
- `tests/`: Comprehensive test suite (unit, integration, security, performance)
- `.claude/`: Claude Code commands and configuration
- `Makefile`: Development workflow automation
- `.github/`: CI/CD workflows

## Development Workflow

### Essential Commands

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

### Primary Protection Decorator (Main Interface)
```python
@cryptex(secrets=['api_key', 'database_url'])
async def my_tool(user_input: str, api_key: str, database_url: str) -> str:
    # Developer writes normal code - no special handling needed
    # AI sees placeholders, tool execution gets real values
    # ALL errors are automatically sanitized before reaching AI
    result = await external_api.call(user_input, api_key)
    await database.save(result, database_url)
    return result
```

**Developer Experience Principles:**
- **One decorator line** = complete temporal isolation
- **Zero cognitive overhead** = developers write normal code
- **Bulletproof security** = automatic error sanitization, input/output protection
- **Framework agnostic** = works with FastMCP, FastAPI automatically

### Context Manager for Advanced Use Cases
```python
async with cryptex.secure_session() as session:
    sanitized_data = await session.sanitize_for_ai(raw_data)
    ai_result = await ai_function(sanitized_data)
    resolved_result = await session.resolve_secrets(ai_result)
```

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

## Configuration

Configuration via `cryptex.toml`:
```toml
[secrets]
api_keys = ["openai_api_key", "anthropic_api_key"]

[security]
enforcement_mode = "strict"
block_exposure = true
```

## Performance Requirements

- **Sanitization Latency**: <5ms for 1KB payloads
- **Resolution Latency**: <10ms for 10 placeholders
- **Memory Overhead**: <5% of application memory

## Development Notes

- **Async-First Design**: All core operations are async/await compatible
- **Type Safety**: Full type hints using Python 3.13+ features
- **Zero Dependencies**: Core functionality uses standard library only
- **Security First**: Every change requires security review and validation

## Architecture Guidelines

### Error Handling Strategy
- **Decorator-First**: All error sanitization happens in the `@cryptex` decorator
- **Automatic**: Developers never handle errors manually - decorator catches and sanitizes ALL exceptions
- **Transparent**: Decorated functions work exactly like normal functions, just secure

### Library Boundaries
- **Cryptex provides utilities** for FastMCP/FastAPI middleware, not its own middleware layer
- **Decorator pattern is primary interface** - simplest developer experience
- **Engine utilities support decorator** - not standalone middleware orchestration

### Refactoring Priorities
1. **Fix decorator error handling** - ensure ALL exceptions are sanitized automatically
2. **Remove over-complex engine utilities** - keep only what decorator needs
3. **Simplify error sanitization** - direct pattern replacement, not complex context management
4. **Maintain developer experience** - one decorator line should provide complete protection