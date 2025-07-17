# Cryptex Examples

Simple, practical examples showing how to use cryptex for universal secret protection.

## Quick Start

After installing cryptex:
```bash
pip install cryptex
```

Run any of these examples:

## 📚 Available Examples

### 1. `basic_usage.py` - Start Here!
```bash
python examples/basic_usage.py
```

**What you'll learn:**
- Core `@protect_secrets` decorator usage
- Zero-config protection with built-in patterns
- Multiple secret types in one function  
- Custom pattern registration
- Convenience decorators

**Perfect for:** First-time users, understanding core concepts

---

### 2. `fastapi_example.py` - Web API Integration
```bash
pip install fastapi uvicorn
python examples/fastapi_example.py
```

**What you'll learn:**
- Clean FastAPI integration without middleware complexity
- Protecting API endpoints with dependency injection
- Real-world web service patterns
- Multiple secrets in HTTP endpoints

**Perfect for:** Web developers, API developers

---

### 3. `real_world_usage.py` - Production Patterns  
```bash
python examples/real_world_usage.py
```

**What you'll learn:**
- Production-ready secret management
- Error handling with secret protection
- Performance monitoring with sanitized logs
- Complex multi-service workflows
- Advanced context manager usage

**Perfect for:** Production applications, enterprise usage

---

## 🎯 Key Concepts Demonstrated

### Universal Protection
All examples show the same core pattern:
```python
from cryptex import protect_secrets

@protect_secrets(["openai_key", "database_url"])
async def my_function(api_key: str, db_url: str):
    # AI sees: placeholders like {{OPENAI_API_KEY}}
    # Function gets: real values for execution
    return await process(api_key, db_url)
```

### Built-in Patterns (Zero Config)
- `openai_key`: OpenAI API keys (`sk-...`)
- `anthropic_key`: Anthropic API keys (`sk-ant-...`)  
- `github_token`: GitHub tokens (`ghp_...`)
- `file_path`: File system paths (`/Users/...`, `/home/...`)
- `database_url`: Database URLs (`postgresql://...`, `mysql://...`)

### Framework Agnostic
The same decorator works with:
- ✅ Standalone functions
- ✅ FastAPI endpoints
- ✅ AsyncIO applications
- ✅ Class methods
- ✅ Any Python framework

---

## 🚀 Running Examples

### Option 1: Direct Execution
```bash
# From project root
python examples/basic_usage.py
python examples/fastapi_example.py  
python examples/real_world_usage.py
```

### Option 2: With Environment Setup
```bash
# Set up your real secrets (optional - examples provide defaults)
export OPENAI_API_KEY="sk-your-real-key"
export DATABASE_URL="postgresql://user:pass@localhost:5432/db" 
export GITHUB_TOKEN="ghp_your-real-token"

# Run examples
python examples/basic_usage.py
```

---

## 📖 Next Steps

1. **Start with `basic_usage.py`** - Learn the fundamentals
2. **Try `fastapi_example.py`** - See web integration
3. **Study `real_world_usage.py`** - Production patterns
4. **Read the main README.md** - Full documentation
5. **Check the source code** - `src/cryptex/` for internals

---

## 💡 Tips

- **No configuration needed** - Examples work immediately
- **Built-in patterns** handle 95% of real-world usage  
- **Same decorator everywhere** - Learn once, use anywhere
- **Production ready** - These patterns scale to real applications
- **Zero dependencies** - Core cryptex has no external requirements

Happy coding with secure temporal isolation! 🔒