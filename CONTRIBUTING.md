# Contributing to Cryptex

Thank you for your interest in contributing to Cryptex! This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management
- Git

### Quick Start

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/AnthemFlynn/cryptex.git
   cd cryptex
   ```

2. **Set up development environment:**
   ```bash
   make dev-setup
   ```

3. **Verify installation:**
   ```bash
   make test
   ```

## Development Philosophy

Cryptex follows a **zero-config philosophy**:

- **No Configuration Files**: Middleware libraries should never require config files
- **95/5 Rule**: 95% of users need zero config, 5% use registration API
- **Universal Approach**: Single decorator works with any Python function
- **Zero Dependencies**: Pure Python 3.11+ standard library only
- **Security First**: Every change requires security review

## Development Workflow

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes following our guidelines:**
   - Follow existing code style and patterns
   - Maintain SOLID principles and Protocol-based design
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks:**
   ```bash
   make pre-commit
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

### Quality Gates

**All contributions must pass these quality gates:**

- ✅ All tests pass (`make test`)
- ✅ Code formatting (`make format`)
- ✅ Linting checks (`make lint`)
- ✅ Security scan (built into test suite)
- ✅ Type checking (ruff static analysis)
- ✅ Performance requirements met

### Testing Requirements

- **Every bug must be reproduced by a unit test before being fixed**
- **Every new feature must be covered by a unit test before implementation**
- **Each test case may contain only one assertion**
- **Tests must use random values as inputs where possible**
- **No mocks - prefer fake objects and stubs**

### Code Style

- **Line length:** 88 characters (Black default)
- **Type hints:** Required for all public APIs using Python 3.11+ syntax
- **Docstrings:** Google style for all public functions/classes
- **Imports:** Organized with ruff
- **Zero Dependencies**: Never add external dependencies

## Architecture Guidelines

### Core Principles

1. **Universal Decorator**: Single `@protect_secrets` decorator for all use cases
2. **SOLID Design**: Protocol-based extensibility with clean abstractions
3. **Thread Safety**: Concurrent access protection with proper locking
4. **Performance**: <5ms sanitization, <10ms resolution, <5% memory overhead

### File Organization

```
src/cryptex/
├── __init__.py                 # Public API exports
├── decorators/
│   ├── __init__.py            # Decorator exports
│   └── protect_secrets.py     # Universal decorator
├── patterns/
│   ├── __init__.py            # Pattern API
│   ├── base.py                # Protocol and base classes
│   └── registry.py            # Thread-safe registry
└── core/                      # Temporal isolation engine
```

### Adding New Features

1. **Built-in Patterns**: Add to `DEFAULT_PATTERNS` in `patterns/base.py`
2. **Core Functionality**: Maintain Protocol-based design
3. **Security Features**: Validate with comprehensive security tests
4. **Performance Features**: Benchmark against requirements

## Testing

### Test Structure

```
tests/
├── unit/           # Fast isolated tests
├── integration/    # Full workflow tests  
├── security/       # Security-focused tests
├── performance/    # Benchmark tests
└── fixtures/       # Test data
```

### Running Tests

```bash
# All tests
make test

# Specific test categories
make test-unit
make test-security
make test-performance

# With coverage
make test-coverage
```

### Test Categories

- **Unit Tests**: Core component functionality
- **Security Tests**: Temporal isolation validation
- **Performance Tests**: Latency and memory benchmarks
- **Integration Tests**: End-to-end workflow validation

## Documentation

### Required Documentation Updates

- Update relevant docstrings with examples
- Add working examples to `examples/` directory
- Update `README.md` for significant API changes
- Update `CHANGELOG.md` for all changes

### Documentation Style

- Use Google-style docstrings
- Include copy-paste examples in docstrings
- Keep examples simple and focused on zero-config usage
- Show framework integration patterns

## Security

### Security Policy

- Report security vulnerabilities via GitHub Security Advisories
- Do not open public issues for security concerns
- Follow responsible disclosure practices

### Security Guidelines

- **Zero Attack Surface**: No config files, no parsing, no external dependencies
- **Temporal Isolation**: Validate three-phase security model
- **Pattern Validation**: Runtime regex validation and error handling
- **Thread Safety**: Concurrent access protection

### Security Testing

- All code changes require security review
- Run security tests: `make test-security`
- Validate temporal isolation: AI sees placeholders, functions get real values

## Performance

### Performance Requirements

- **Sanitization latency:** <5ms for 1KB payloads
- **Resolution latency:** <10ms for 10 placeholders  
- **Memory overhead:** <5% of application memory
- **Zero startup time:** No dependencies, no config loading

### Performance Testing

```bash
make test-performance
```

## Code Review Process

### Pull Request Guidelines

1. **Title:** Use conventional commits format
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `test:` for tests
   - `refactor:` for refactoring
   - `perf:` for performance improvements
   - `security:` for security fixes

2. **Description:** Include:
   - What changed and why
   - Zero-config philosophy maintained
   - Testing performed
   - Performance impact
   - Security implications
   - Breaking changes (if any)

3. **Checklist:**
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] CHANGELOG.md updated
   - [ ] All quality gates pass
   - [ ] Performance requirements met
   - [ ] Security review completed

### Review Criteria

- **Zero-Config Philosophy**: No configuration files introduced
- **Universal Compatibility**: Works with any Python function
- **Security**: Temporal isolation maintained
- **Performance**: Meets latency and memory requirements
- **Code Quality**: SOLID principles and Protocol-based design
- **Tests**: Comprehensive test coverage
- **Documentation**: Clear examples and usage

## Common Development Tasks

### Adding Built-in Patterns

1. Add pattern to `DEFAULT_PATTERNS` in `src/cryptex/patterns/base.py`
2. Test pattern matching in `tests/unit/test_pattern_registration.py`
3. Update pattern table in `README.md`
4. Add usage examples

### Framework Integration

1. Create example in `examples/` directory
2. Test with actual framework
3. Document in `README.md`
4. Validate zero-config operation

### Performance Optimization

1. Benchmark current performance
2. Implement optimization
3. Validate performance requirements met
4. Update performance tests

## Release Process

### Version Management

- Follow [Semantic Versioning](https://semver.org/)
- Use `bump2version` for version updates
- Tag releases with `v` prefix (e.g., `v0.3.0`)

### Release Checklist

1. Update CHANGELOG.md with all changes
2. Run full test suite including performance
3. Update version with bump2version
4. Create and merge release PR
5. Tag release
6. GitHub Actions handles PyPI publishing

## Getting Help

- **Questions:** Open a GitHub Discussion
- **Bug Reports:** Open a GitHub Issue
- **Feature Requests:** Open a GitHub Issue with enhancement label
- **Security Issues:** Use GitHub Security Advisories

## License

By contributing to Cryptex, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Cryptex! Your efforts help make AI applications more secure for everyone.