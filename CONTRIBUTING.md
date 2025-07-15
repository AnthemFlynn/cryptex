# Contributing to Codename

Thank you for your interest in contributing to Codename! This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) for dependency management
- Git

### Quick Start

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/AnthemFlynn/codename.git
   cd codename
   ```

2. **Set up development environment:**
   ```bash
   make dev-setup
   ```

3. **Verify installation:**
   ```bash
   make test
   ```

## Development Workflow

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes following our guidelines:**
   - Follow existing code style and patterns
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
- ✅ Security scan (`make security`)
- ✅ Type checking (`mypy src/`)

### Testing Requirements

- **Every bug must be reproduced by a unit test before being fixed**
- **Every new feature must be covered by a unit test before implementation**
- **Each test case may contain only one assertion**
- **Tests must use random values as inputs where possible**
- **No mocks - prefer fake objects and stubs**

### Code Style

- **Line length:** 88 characters (Black default)
- **Type hints:** Required for all public APIs
- **Docstrings:** Google style for all public functions/classes
- **Imports:** Organized with isort/ruff

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

# Watch mode
make watch-tests
```

## Documentation

### Adding Documentation

- Update relevant docstrings
- Add examples to `examples/` directory
- Update `docs/` for significant changes
- Update `CHANGELOG.md`

### Documentation Style

- Use Google-style docstrings
- Include examples in docstrings
- Keep examples simple and focused

## Security

### Security Policy

- Report security vulnerabilities via GitHub Security Advisories
- Do not open public issues for security concerns
- Follow responsible disclosure practices

### Security Testing

- All code changes require security review
- Run security tests: `make test-security`
- Check dependencies: `make security`

## Performance

### Performance Requirements

- **Sanitization latency:** <5ms for 1KB payloads
- **Resolution latency:** <10ms for 10 placeholders  
- **Memory overhead:** <5% of application memory

### Performance Testing

```bash
make test-performance
make benchmark
```

## Code Review Process

### Pull Request Guidelines

1. **Title:** Use conventional commits format
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `test:` for tests
   - `refactor:` for refactoring

2. **Description:** Include:
   - What changed and why
   - Testing performed
   - Breaking changes (if any)
   - Related issues

3. **Checklist:**
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] CHANGELOG.md updated
   - [ ] All quality gates pass

### Review Criteria

- **Functionality:** Does it work correctly?
- **Security:** No security vulnerabilities
- **Performance:** Meets performance requirements
- **Code Quality:** Clean, readable, maintainable
- **Tests:** Adequate test coverage
- **Documentation:** Clear and complete

## Release Process

### Version Management

- Follow [Semantic Versioning](https://semver.org/)
- Use `bump2version` for version updates
- Tag releases with `v` prefix (e.g., `v1.0.0`)

### Release Checklist

1. Update CHANGELOG.md
2. Run full test suite
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

By contributing to Codename, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Codename! Your efforts help make AI applications more secure for everyone.