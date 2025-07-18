# Cryptex-AI - AI/LLM Secrets Isolation Library
# Comprehensive Makefile for development workflows

.PHONY: help install install-dev test lint format security build clean release docs all
.DEFAULT_GOAL := help

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

# Python and package management
PYTHON = python3
UV = uv
VENV_DIR = .venv
VENV_ACTIVATE = . $(VENV_DIR)/bin/activate

# Project info
PROJECT_NAME = cryptex_ai
SRC_DIR = src
TESTS_DIR = tests
DOCS_DIR = docs

help: ## Show this help message
	@echo "$(GREEN)Cryptex-AI - AI/LLM Secrets Isolation Library$(NC)"
	@echo "$(YELLOW)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation targets
install: ## Install production dependencies
	$(UV) pip install -e .

install-dev: ## Install development dependencies
	$(UV) pip install -e ".[dev,fastmcp,fastapi,ml]"

install-all: venv install-dev ## Create virtual environment and install all dependencies
	@echo "$(GREEN)✅ Development environment ready$(NC)"

venv: ## Create virtual environment
	$(UV) venv $(VENV_DIR)

# Testing targets
test: ## Run all tests
	$(VENV_ACTIVATE) && pytest $(TESTS_DIR) -v

test-unit: ## Run unit tests only
	$(VENV_ACTIVATE) && pytest $(TESTS_DIR)/unit -v

test-integration: ## Run integration tests only
	$(VENV_ACTIVATE) && pytest $(TESTS_DIR)/integration -v

test-security: ## Run security tests only
	$(VENV_ACTIVATE) && pytest $(TESTS_DIR) -v -m security

test-performance: ## Run performance benchmarks
	$(VENV_ACTIVATE) && pytest $(TESTS_DIR) -v -m performance --benchmark-only

test-coverage: ## Run tests with coverage report
	$(VENV_ACTIVATE) && pytest $(TESTS_DIR) --cov=$(PROJECT_NAME) --cov-report=html --cov-report=term

test-all: test-coverage test-security test-performance ## Run all tests including coverage and benchmarks

# Code quality targets
lint: ## Run linting checks
	$(VENV_ACTIVATE) && ruff check $(SRC_DIR) $(TESTS_DIR)
	$(VENV_ACTIVATE) && mypy $(SRC_DIR)

lint-fix: ## Fix linting issues automatically
	$(VENV_ACTIVATE) && ruff check --fix $(SRC_DIR) $(TESTS_DIR)

format: ## Format code with black and ruff
	$(VENV_ACTIVATE) && black $(SRC_DIR) $(TESTS_DIR)
	$(VENV_ACTIVATE) && ruff format $(SRC_DIR) $(TESTS_DIR)

format-check: ## Check code formatting without making changes
	$(VENV_ACTIVATE) && black --check $(SRC_DIR) $(TESTS_DIR)
	$(VENV_ACTIVATE) && ruff format --check $(SRC_DIR) $(TESTS_DIR)

# Security targets
security: ## Run security checks
	$(VENV_ACTIVATE) && bandit -r $(SRC_DIR)
	$(VENV_ACTIVATE) && safety check

security-audit: ## Run comprehensive security audit
	$(VENV_ACTIVATE) && bandit -r $(SRC_DIR) -f json -o security-report.json
	$(VENV_ACTIVATE) && safety check --json --output security-deps.json

# Build targets
build: clean ## Build distribution packages
	$(VENV_ACTIVATE) && $(PYTHON) -m build

build-wheel: ## Build wheel package only
	$(VENV_ACTIVATE) && $(PYTHON) -m build --wheel

build-sdist: ## Build source distribution only
	$(VENV_ACTIVATE) && $(PYTHON) -m build --sdist

# Documentation targets
docs: ## Generate documentation
	$(VENV_ACTIVATE) && mkdir -p $(DOCS_DIR)
	$(VENV_ACTIVATE) && $(PYTHON) -m pydoc -w $(PROJECT_NAME)
	@echo "$(GREEN)📚 Documentation generated$(NC)"

docs-serve: ## Serve documentation locally
	$(VENV_ACTIVATE) && $(PYTHON) -m http.server 8000 --directory $(DOCS_DIR)

# Release targets
version: ## Show current version
	$(VENV_ACTIVATE) && $(PYTHON) -c "import $(PROJECT_NAME); print($(PROJECT_NAME).__version__)"

release-check: test-all lint security ## Run all checks before release
	@echo "$(GREEN)✅ All release checks passed$(NC)"

release-build: release-check build ## Build release after running all checks
	@echo "$(GREEN)🚀 Release build complete$(NC)"

release-test: release-build ## Test release on Test PyPI
	$(VENV_ACTIVATE) && twine upload --repository testpypi dist/*

release: release-build ## Release to PyPI (production)
	$(VENV_ACTIVATE) && twine upload dist/*

# Cleanup targets
clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf security-*.json
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# New Zed-specific targets
zed-setup: ## Configure Zed for this project
	@mkdir -p .zed
	@echo "$(GREEN)✅ Zed configuration ready$(NC)"
	@echo "$(YELLOW)Zed tasks available:$(NC)"
	@echo "  • Cmd+Shift+P -> 'task: Run All Tests'"
	@echo "  • Cmd+Shift+P -> 'task: Format Code'"
	@echo "  • Cmd+Shift+P -> 'task: Lint Code'"

# Enhanced development workflow targets
dev-server: ## Start development server with live reload (FastAPI example)
	$(VENV_ACTIVATE) && python examples/fastapi_integration.py

docs-live: ## Start live documentation server
	$(VENV_ACTIVATE) && cd $(DOCS_DIR) && python -m sphinx_autobuild . _build/html --host 0.0.0.0 --port 8080

watch-all: ## Watch files and run tests + lint on changes
	$(VENV_ACTIVATE) && watchmedo auto-restart --patterns="*.py" --recursive --signal SIGTERM python -c "import subprocess; subprocess.run(['make', 'quick-check'])"

type-check: ## Run type checking separately
	$(VENV_ACTIVATE) && mypy $(SRC_DIR) --strict

install-hooks: ## Install pre-commit hooks
	$(VENV_ACTIVATE) && pre-commit install
	$(VENV_ACTIVATE) && pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✅ Pre-commit hooks installed$(NC)"

# Example running targets
run-examples: ## Run all examples
	@echo "$(YELLOW)Running basic usage example:$(NC)"
	$(VENV_ACTIVATE) && python examples/basic_usage.py
	@echo "$(YELLOW)Running async patterns example:$(NC)"
	$(VENV_ACTIVATE) && python examples/async_patterns.py
	@echo "$(YELLOW)Running advanced config example:$(NC)"
	$(VENV_ACTIVATE) && python examples/advanced_config.py

run-example-basic: ## Run basic usage example
	$(VENV_ACTIVATE) && python examples/basic_usage.py

run-example-async: ## Run async patterns example
	$(VENV_ACTIVATE) && python examples/async_patterns.py

run-example-fastapi: ## Run FastAPI example server
	$(VENV_ACTIVATE) && python examples/fastapi_integration.py

run-example-config: ## Run advanced configuration example
	$(VENV_ACTIVATE) && python examples/advanced_config.py

# Documentation targets (enhanced)
docs-build: ## Build documentation
	$(VENV_ACTIVATE) && cd $(DOCS_DIR) && sphinx-build -b html . _build/html

docs-clean: ## Clean documentation build
	$(VENV_ACTIVATE) && cd $(DOCS_DIR) && rm -rf _build/

docs-check: ## Check documentation for issues
	$(VENV_ACTIVATE) && cd $(DOCS_DIR) && sphinx-build -b linkcheck . _build/linkcheck

# Testing enhancements
test-watch: ## Run tests in watch mode
	$(VENV_ACTIVATE) && pytest-watch $(TESTS_DIR) --clear

test-coverage-html: ## Generate HTML coverage report
	$(VENV_ACTIVATE) && pytest $(TESTS_DIR) --cov=$(PROJECT_NAME) --cov-report=html
	@echo "$(GREEN)📊 Coverage report: htmlcov/index.html$(NC)"

test-parallel: ## Run tests in parallel
	$(VENV_ACTIVATE) && pytest $(TESTS_DIR) -n auto

# Code quality enhancements  
lint-fix-all: ## Fix all linting issues automatically
	$(VENV_ACTIVATE) && ruff check --fix $(SRC_DIR) $(TESTS_DIR)
	$(VENV_ACTIVATE) && black $(SRC_DIR) $(TESTS_DIR)
	$(VENV_ACTIVATE) && ruff format $(SRC_DIR) $(TESTS_DIR)

complexity-check: ## Check code complexity
	$(VENV_ACTIVATE) && radon cc $(SRC_DIR) -a

# Git workflow helpers
git-hooks-test: ## Test pre-commit hooks on all files
	$(VENV_ACTIVATE) && pre-commit run --all-files

commit-check: ## Run all quality checks before commit
	make format lint test-unit security
	@echo "$(GREEN)✅ Ready to commit$(NC)"

# Environment and dependency management
upgrade-deps: ## Upgrade all dependencies
	$(UV) pip list --outdated
	@echo "$(YELLOW)Run 'uv pip install --upgrade <package>' to upgrade specific packages$(NC)"

check-deps-security: ## Check dependencies for security issues
	$(VENV_ACTIVATE) && safety check --json --output security-deps.json || true
	@echo "$(GREEN)📋 Security report: security-deps.json$(NC)"

# Development environment diagnostics
check-env-detailed: ## Detailed environment check
	@echo "$(YELLOW)🔍 Detailed Environment Check:$(NC)"
	@echo "Python: $(shell $(PYTHON) --version 2>&1 || echo '❌ Not found')"
	@echo "UV: $(shell $(UV) --version 2>&1 || echo '❌ Not found')"
	@echo "Virtual env: $(shell test -d $(VENV_DIR) && echo '✅ Exists' || echo '❌ Missing')"
	@echo "Git: $(shell git --version 2>&1 || echo '❌ Not found')"
	@echo "Pre-commit: $(shell $(VENV_ACTIVATE) && pre-commit --version 2>&1 || echo '❌ Not installed')"
	@echo "Project root: $(shell pwd)"
	@echo "Make version: $(shell make --version | head -n1)"

# Maintenance tasks
update-copyright: ## Update copyright year in files
	@find . -name "*.py" -type f -exec sed -i.bak 's/Copyright (c) [0-9]\{4\}/Copyright (c) $(shell date +%Y)/g' {} \;
	@find . -name "*.py.bak" -delete
	@echo "$(GREEN)✅ Copyright updated$(NC)"

count-lines: ## Count lines of code
	@echo "$(YELLOW)📊 Code Statistics:$(NC)"
	@find $(SRC_DIR) -name "*.py" | xargs wc -l | tail -n1
	@echo "Tests:"
	@find $(TESTS_DIR) -name "*.py" | xargs wc -l | tail -n1
	@echo "Examples:"
	@find examples -name "*.py" | xargs wc -l | tail -n1 2>/dev/null || echo "No examples found"

# Advanced CI targets
ci-local: ## Run complete CI pipeline locally
	make clean
	make install-dev
	make lint
	make test-all
	make security
	make build
	@echo "$(GREEN)🎉 Local CI pipeline completed successfully$(NC)"

validate-structure: ## Validate project structure
	@echo "$(YELLOW)🏗️  Validating project structure:$(NC)"
	@test -f pyproject.toml && echo "✅ pyproject.toml" || echo "❌ pyproject.toml missing"
	@test -f $(SRC_DIR)/$(PROJECT_NAME)/__init__.py && echo "✅ Package __init__.py" || echo "❌ Package __init__.py missing"
	@test -f $(SRC_DIR)/$(PROJECT_NAME)/py.typed && echo "✅ py.typed marker" || echo "❌ py.typed marker missing"
	@test -d $(TESTS_DIR) && echo "✅ Tests directory" || echo "❌ Tests directory missing"
	@test -f README.md && echo "✅ README.md" || echo "❌ README.md missing"
	@test -f CHANGELOG.md && echo "✅ CHANGELOG.md" || echo "❌ CHANGELOG.md missing"
	@test -f CONTRIBUTING.md && echo "✅ CONTRIBUTING.md" || echo "❌ CONTRIBUTING.md missing"
	@test -f SECURITY.md && echo "✅ SECURITY.md" || echo "❌ SECURITY.md missing"

clean-all: clean ## Clean everything including virtual environment
	rm -rf $(VENV_DIR)

# Development workflow targets
dev-setup: venv install-dev ## Complete development environment setup
	@echo "$(GREEN)🔧 Development environment setup complete$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  • Run 'make test' to verify installation"
	@echo "  • Run 'make help' to see available commands"

pre-commit: format lint test ## Run pre-commit checks
	@echo "$(GREEN)✅ Pre-commit checks passed$(NC)"

ci: install-dev test-all lint security ## Run CI pipeline locally
	@echo "$(GREEN)✅ CI pipeline completed$(NC)"

# Task Master integration
tm-next: ## Show next task from Task Master
	@echo "$(YELLOW)Next available task:$(NC)"
	@cd . && /project:tm/next || echo "Task Master not available"

tm-status: ## Show Task Master project status
	@echo "$(YELLOW)Project status:$(NC)"
	@cd . && /project:tm/status || echo "Task Master not available"

# Quick development commands
quick-test: ## Quick test run (no coverage)
	$(VENV_ACTIVATE) && pytest $(TESTS_DIR) -x --tb=short

quick-check: lint format-check ## Quick code quality check
	@echo "$(GREEN)✅ Quick checks passed$(NC)"

# Performance and profiling
profile: ## Profile application performance
	$(VENV_ACTIVATE) && $(PYTHON) -m cProfile -o profile.stats -m pytest $(TESTS_DIR) -m performance

benchmark: ## Run performance benchmarks
	$(VENV_ACTIVATE) && pytest $(TESTS_DIR) -m performance --benchmark-only --benchmark-sort=mean

# Information targets
info: ## Show project information
	@echo "$(GREEN)Project Information:$(NC)"
	@echo "  Name: $(PROJECT_NAME)"
	@echo "  Source: $(SRC_DIR)"
	@echo "  Tests: $(TESTS_DIR)"
	@echo "  Python: $(shell $(PYTHON) --version)"
	@echo "  UV: $(shell $(UV) --version)"
	@echo "  Virtual Environment: $(VENV_DIR)"

deps: ## Show dependency information
	$(VENV_ACTIVATE) && pip list

deps-outdated: ## Show outdated dependencies
	$(VENV_ACTIVATE) && pip list --outdated

# All-in-one targets
all: clean install-dev test-all lint security build ## Run complete workflow
	@echo "$(GREEN)🎉 Complete workflow finished successfully$(NC)"

# Docker targets (if needed)
docker-build: ## Build Docker image
	docker build -t $(PROJECT_NAME) .

docker-test: ## Test in Docker container
	docker run --rm $(PROJECT_NAME) make test

# Utility targets
watch-tests: ## Watch for changes and run tests
	$(VENV_ACTIVATE) && pytest-watch $(TESTS_DIR)

open-coverage: ## Open coverage report in browser
	open htmlcov/index.html

# Project-specific targets
demo: ## Run demonstration of core functionality
	$(VENV_ACTIVATE) && $(PYTHON) -c "from $(PROJECT_NAME) import protect_secrets; print('Cryptex-AI is working!')"

validate-config: ## Validate project configuration
	$(VENV_ACTIVATE) && $(PYTHON) -c "import tomli; tomli.load(open('pyproject.toml', 'rb'))"

# Environment check
check-env: ## Check development environment
	@echo "$(YELLOW)Environment Check:$(NC)"
	@$(PYTHON) --version || echo "$(RED)❌ Python not found$(NC)"
	@$(UV) --version || echo "$(RED)❌ UV not found$(NC)"
	@test -d $(VENV_DIR) && echo "$(GREEN)✅ Virtual environment exists$(NC)" || echo "$(YELLOW)⚠️  Virtual environment missing - run 'make venv'$(NC)"