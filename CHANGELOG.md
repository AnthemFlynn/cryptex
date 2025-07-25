# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned for v0.4.0
- Enhanced pattern validation and error reporting

### Planned for v0.5.0
- Advanced caching and performance optimizations

### Planned for v0.6.0
- Plugin system for custom secret sources

## [0.3.3] - 2025-07-22

### Major Fix - True Temporal Isolation
- **BREAKING FIX**: Fixed core decorator to implement genuine temporal isolation
- AI services now receive placeholders while functions get real secrets through monkey-patching
- Added context manager for temporary AI library interception during function execution

### Test Infrastructure Overhaul
- Reorganized test suite into proper unit/integration/security/performance structure
- Added comprehensive AI call interception tests (135 total tests passing)
- Created live demonstration scripts proving temporal isolation works
- Removed outdated example files that didn't reflect working implementation

### Documentation Updates
- Updated README.md with accurate implementation examples showing real AI call interception
- Fixed llms.txt to reflect monkey-patching architecture and true temporal isolation
- Updated all docstrings to show working examples
- Added comprehensive live test documentation

### Architecture Changes
- Implemented monkey-patching of OpenAI/Anthropic libraries during decorated function execution
- Added automatic cleanup and restoration of original methods
- Enhanced security model with three-phase isolation: Sanitization → AI Processing → Resolution

## [0.3.2] - 2025-07-18

### Documentation
- **Google Python Style Guide Compliance**: Enhanced all docstrings to meet Google standards
- **Comprehensive Raises Sections**: Added exception documentation to all public functions
- **Class Attribute Documentation**: Enhanced class docstrings with detailed Attributes sections
- **Method Documentation**: Added comprehensive Args/Returns/Raises to missing public methods
- **LLM Integration**: Added `llms.txt` file for LLM-based coding assistant compatibility
- **Formatting Consistency**: Standardized docstring formatting across all modules

### Enhanced API Documentation
- `protect_secrets()` decorator now documents ValueError, PatternNotFoundError, EngineInitializationError
- `TemporalIsolationEngine` class includes comprehensive attribute and method documentation
- All convenience decorators (`protect_files`, `protect_api_keys`, etc.) document exceptions
- Performance-critical methods include detailed return value specifications
- Complex private methods enhanced with purpose and parameter documentation

### Quality Improvements
- All 75 tests continue to pass
- Linting and type checking remain clean
- Maintains full API compatibility
- Enhanced examples and usage documentation throughout

## [0.3.1] - 2025-07-18

### Changed
- **PyPI Links**: Updated README badges to show live PyPI package links
- **Documentation Links**: Fixed all PyPI references to point to published package
- **Roadmap**: Updated version numbering to reflect completed milestones

### Fixed
- **Package Badges**: Replaced static badges with dynamic PyPI version badges
- **Link Consistency**: Ensured all documentation points to correct PyPI package

## [0.3.0] - 2025-07-18

### Added
- **GitHub Issue Templates**: Comprehensive bug report, feature request, and security issue templates
- **Release Automation**: Pre-release and release workflows with automated PyPI publishing
- **Documentation Site**: Full MkDocs-based documentation deployed to GitHub Pages
- **CI/CD Improvements**: Consolidated main workflow with parallel job execution
- **Codecov Integration**: Code coverage reporting with proper configuration

### Changed
- **Repository Rename**: Complete migration from `cryptex` to `cryptex-ai` across all files
- **Documentation Updates**: Consistent naming and improved installation guides
- **Development Workflow**: Clarified `uv` requirement in README development setup
- **CI Environment**: Added `CRYPTEX_SKIP_PERF_CHECKS` for stable CI test runs

### Fixed
- **CI/CD Pipeline**: Fixed all workflow issues including dependency installation and test execution
- **Documentation Naming**: Corrected all references to use `cryptex-ai` consistently
- **Build Configuration**: Updated Makefile project name from `codename` to `cryptex_ai`

### Documentation
- **Installation Guides**: Changed "pip (recommended)" to "pip (default)" to reflect standard practice
- **Complete Rebranding**: All documentation now uses consistent `cryptex-ai` naming
- **Enhanced Examples**: Updated all example code to use correct import statements

## [0.2.0] - 2025-07-17

### Added
- **Universal Decorator Architecture**: Complete transformation from middleware to universal `@protect_secrets` decorator
- **Zero Dependencies**: Eliminated all external dependencies, now pure Python 3.11+ standard library
- **SOLID Architecture**: Protocol-based design with clean abstractions and single responsibility
- **Convenience Decorators**: Added `protect_api_keys()`, `protect_files()`, `protect_all()` for common use cases
- **Thread-Safe Pattern Registry**: Concurrent access protection with proper locking mechanisms
- **Comprehensive Examples**: Working examples for FastMCP, FastAPI, Django, and any Python function
- **Pattern System Redesign**: Unified pattern registration without artificial built-in vs custom distinctions

### Changed
- **BREAKING**: Removed all framework-specific middleware (FastMCP, FastAPI integrations)
- **BREAKING**: Changed from `from cryptex.decorators.mcp import protect_tool` to `from cryptex import protect_secrets`
- **BREAKING**: Eliminated configuration files - now pure code-based configuration only
- **API Simplification**: Streamlined public API to focus on universal decorator pattern
- **Performance Improvements**: Reduced codebase from 5,854 lines to 1,991 (net -3,863 lines)
- **Import Structure**: Simplified imports with main API accessible from root package
- **Pattern Registration**: Unified pattern system with single `register_pattern()` function

### Removed
- **Framework Middleware**: Eliminated FastMCP and FastAPI specific middleware modules
- **Configuration Files**: Removed all TOML configuration support in favor of code-based patterns
- **External Dependencies**: Removed typing-extensions dependency
- **Complex Integrations**: Simplified to universal decorator that works with any Python function

### Fixed
- **Critical Security Bug**: Universal decorator now properly returns sanitized results instead of original data
- **Thread Safety**: Proper concurrent access protection in pattern registry
- **Memory Management**: Enhanced cleanup and isolation between function executions
- **Error Handling**: Comprehensive error sanitization to prevent secret leakage
- **Pattern Validation**: Runtime regex validation with proper error handling

### Security
- **Zero Attack Surface**: No config files, no parsing, no external dependencies
- **Enhanced Temporal Isolation**: Improved three-phase security model
- **Pattern Security**: Runtime validation and injection protection
- **Memory Security**: Minimized secret lifetime with proper cleanup
- **Concurrency Security**: Thread-safe operations with race condition protection

### Performance
- **<5ms Sanitization**: Maintained sub-5ms latency for 1KB payloads
- **<10ms Resolution**: Maintained sub-10ms latency for 10 placeholders
- **<5% Memory Overhead**: Minimal memory footprint impact
- **Zero Startup Time**: No dependencies or config loading overhead

## [0.1.0] - 2025-07-15

### Added
- Initial release of Cryptex
- Basic secrets isolation functionality with middleware approach
- FastMCP and FastAPI specific integrations
- Configuration-based pattern management
- Core temporal isolation engine
- Comprehensive test suite
- CI/CD pipeline with GitHub Actions
- Security scanning and quality gates

### Security
- Implemented temporal isolation security model
- Added security scanning with bandit and safety
- Pattern-based secret detection and sanitization

---

## Migration Guide: 0.1.x → 0.2.0

### Breaking Changes

#### 1. Import Changes
```python
# Before (0.1.x)
from cryptex.decorators.mcp import protect_tool
from cryptex.decorators.fastapi import protect_endpoint

# After (0.2.0)
from cryptex import protect_secrets
```

#### 2. Decorator Usage
```python
# Before (0.1.x)
@protect_tool(secrets=["openai_key"])
async def mcp_function(api_key: str) -> str:
    return await openai_call(api_key)

# After (0.2.0)
@protect_secrets(["openai_key"])
async def universal_function(api_key: str) -> str:
    return await openai_call(api_key)
```

#### 3. Configuration
```python
# Before (0.1.x) - Configuration files
# codename.toml
[patterns]
custom_pattern = { regex = "...", placeholder = "..." }

# After (0.2.0) - Code-based registration
from cryptex import register_pattern

register_pattern(
    name="custom_pattern",
    regex=r"...",
    placeholder="{{CUSTOM}}",
    description="Custom pattern"
)
```

#### 4. Framework Integration
```python
# Before (0.1.x) - Framework-specific
from cryptex.decorators.fastapi import protect_endpoint

@app.post("/secure")
@protect_endpoint(secrets=["database_url"])
async def secure_endpoint(db_url: str):
    return await query_database(db_url)

# After (0.2.0) - Universal decorator
from cryptex import protect_secrets

@app.post("/secure")
@protect_secrets(["database_url"])
async def secure_endpoint(db_url: str):
    return await query_database(db_url)
```

### New Features in 0.2.0

#### Convenience Decorators
```python
from cryptex import protect_api_keys, protect_files, protect_all

@protect_api_keys()  # Protects OpenAI + Anthropic keys
@protect_files()     # Protects file system paths  
@protect_all()       # Protects all built-in patterns
```

#### Universal Compatibility
```python
# Works with any Python function
@protect_secrets(["openai_key"])
def sync_function(api_key: str) -> str:
    return openai_call(api_key)

@protect_secrets(["openai_key"])
async def async_function(api_key: str) -> str:
    return await openai_call(api_key)
```

### Migration Steps

1. **Update imports**: Change all decorator imports to `from cryptex import protect_secrets`
2. **Replace decorators**: Change `@protect_tool` and `@protect_endpoint` to `@protect_secrets`
3. **Remove config files**: Delete any `codename.toml` or configuration files
4. **Update patterns**: Convert file-based patterns to code-based `register_pattern()` calls
5. **Test thoroughly**: Validate that temporal isolation still works correctly
6. **Update dependencies**: Remove cryptex from dependencies and reinstall

### Benefits After Migration

- **Simpler API**: Single decorator for all use cases
- **Zero Dependencies**: No external packages required
- **Better Performance**: Reduced overhead and faster startup
- **Enhanced Security**: Zero attack surface with no config files
- **Universal Compatibility**: Works with any Python framework
- **Cleaner Code**: Elimination of framework-specific complexity
