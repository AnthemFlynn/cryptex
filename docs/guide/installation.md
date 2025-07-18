# Installation

Cryptex-AI supports multiple installation methods to fit your workflow.

## Requirements

- **Python**: 3.11+ (uses modern type hints and async features)
- **Dependencies**: Zero runtime dependencies (standard library only)

## Installation Methods

### pip (Default)

The traditional and most widely supported method:

```bash
pip install cryptex-ai
```

### uv (Modern Alternative)

[uv](https://github.com/astral-sh/uv) is a fast, modern Python package manager:

```bash
# Add to existing project
uv add cryptex-ai

# Install globally
uv pip install cryptex-ai
```

### Development Installation

For contributors and developers:

```bash
# Clone the repository
git clone https://github.com/AnthemFlynn/cryptex-ai.git
cd cryptex-ai

# Install in development mode with all dependencies
uv sync --dev

# Or with pip
pip install -e ".[dev,test,docs]"
```

## Verification

Verify your installation:

```python
import cryptex_ai
print(cryptex_ai.__version__)

# Test core functionality
from cryptex_ai import protect_secrets, list_patterns
print("Available patterns:", list_patterns())
```

## Virtual Environments

### With venv

```bash
python -m venv cryptex-env
source cryptex-env/bin/activate  # On Windows: cryptex-env\Scripts\activate
pip install cryptex-ai
```

### With uv

```bash
# Create project with uv
uv init my-cryptex-project
cd my-cryptex-project
uv add cryptex-ai
```

## Docker

Use Cryptex in containerized environments:

```dockerfile
FROM python:3.11-slim

# Install uv for faster package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy your application
COPY . .

# Run your application
CMD ["uv", "run", "python", "main.py"]
```

## Troubleshooting

### Python Version Issues

Cryptex-AI requires Python 3.11+. Check your version:

```bash
python --version
```

If you need to install a newer Python version:

```bash
# With uv
uv python install 3.11

# With pyenv
pyenv install 3.11.0
pyenv global 3.11.0
```

### Import Errors

If you see import errors:

1. **Wrong package name**: Make sure you installed `cryptex-ai`, not `cryptex`
2. **Virtual environment**: Ensure you're in the correct virtual environment
3. **Python path**: Verify Cryptex is installed in the active Python environment

```bash
# Check where cryptex_ai is installed
python -c "import cryptex_ai; print(cryptex_ai.__file__)"
```

### Performance Issues

If you experience slow performance:

1. **Check Python version**: Ensure you're using Python 3.11+ for optimal performance
2. **Profile your code**: Use the built-in performance monitoring tools
3. **Verify no debugging**: Make sure you're not running with Python's `-O` flag disabled

### PyPI Package Name

**Important**: The PyPI package is named `cryptex-ai`, and you import it as `cryptex_ai`:

```bash
# Install this package
pip install cryptex-ai
```

```python
# Import like this
import cryptex_ai
from cryptex_ai import protect_secrets
```

## Next Steps

Once installed, head to the [Quick Start Guide](../quickstart.md) to begin using Cryptex-AI!
