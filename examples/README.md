# Cryptex Examples

Comprehensive examples demonstrating Cryptex's temporal isolation capabilities for AI/LLM applications. These examples show how to protect secrets across FastMCP servers and FastAPI applications.

## 🔒 What is Temporal Isolation?

Cryptex implements a **three-phase security architecture** to ensure AI models never access real secrets:

1. **Sanitization**: Convert secrets to `{RESOLVE:SECRET_TYPE:HASH}` placeholders
2. **AI Processing**: AI processes data with placeholders, never real secrets  
3. **Resolution**: Convert placeholders back to real values for tool execution

### Security Guarantee

- **AI Context**: Sees safe placeholders like `{RESOLVE:API_KEY:a1b2c3d4}` or `/{USER_HOME}/...`
- **Tool Execution**: Gets real values for actual operations
- **Response Sanitization**: Tool outputs cleaned before returning to AI
- **Context Expiration**: Automatic cleanup prevents secret accumulation

## 📁 Examples Structure

```
examples/
├── README.md                    # This file
├── fastmcp/
│   ├── 01_simple_hello_world.py    # Basic @cryptex decorator usage
│   ├── 02_advanced_middleware.py   # Full middleware with monitoring
│   └── requirements.txt             # FastMCP dependencies
├── fastapi/
│   ├── 01_simple_hello_world.py    # Basic @cryptex decorator usage
│   ├── 02_advanced_middleware.py   # Full middleware with monitoring
│   └── requirements.txt             # FastAPI dependencies
├── config/
│   ├── simple.toml                 # Basic configuration
│   └── advanced.toml               # Advanced configuration
└── shared/
    └── utils.py                    # Common utilities
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Install Cryptex
pip install cryptex

# Set up example environment variables
export OPENAI_API_KEY="sk-example1234567890abcdef"
export ANTHROPIC_API_KEY="sk-ant-example1234567890abcdef"
export DATABASE_URL="postgresql://user:secret@localhost:5432/mydb"
export JWT_SECRET="my-secret-jwt-key-123"
```

### 2. Run FastMCP Examples

```bash
# Install FastMCP dependencies
pip install -r examples/fastmcp/requirements.txt

# Run simple example
python examples/fastmcp/01_simple_hello_world.py

# Run advanced example
python examples/fastmcp/02_advanced_middleware.py
```

### 3. Run FastAPI Examples

```bash
# Install FastAPI dependencies
pip install -r examples/fastapi/requirements.txt

# Run simple example
python examples/fastapi/01_simple_hello_world.py

# Run advanced example
python examples/fastapi/02_advanced_middleware.py
```

## 📚 Example Progression

### Level 1: Simple Hello World
- **Purpose**: Basic secret protection with `@cryptex` decorator
- **Features**: Single tool/endpoint, environment variables, basic sanitization
- **Learning**: How temporal isolation works in practice

### Level 2: Advanced Middleware
- **Purpose**: Production-ready middleware integration
- **Features**: Multiple tools/endpoints, TOML configuration, monitoring, metrics
- **Learning**: Full middleware capabilities, performance tuning, error handling

## 🛠️ Key Features Demonstrated

### Core Functionality
- ✅ **Temporal Isolation**: Sanitization → AI Processing → Resolution
- ✅ **Secret Detection**: API keys, database URLs, file paths, JWT tokens
- ✅ **Multiple Integration Patterns**: Decorator, middleware, context manager

### Security Features
- ✅ **Complete Isolation**: AI models never see real secret values
- ✅ **Pattern Detection**: Comprehensive regex patterns for common secrets
- ✅ **Response Sanitization**: Tool outputs cleaned before AI access
- ✅ **Error Sanitization**: Tracebacks cleaned to prevent secret leakage

### Performance Features
- ✅ **<5ms Sanitization**: Ultra-fast secret replacement
- ✅ **<10ms Resolution**: Quick placeholder resolution
- ✅ **Cache Optimization**: >95% cache hit rate for typical workloads
- ✅ **Background Cleanup**: Automatic context expiration

### Production Features
- ✅ **Configuration Management**: TOML-based configuration
- ✅ **Performance Monitoring**: Real-time metrics and statistics
- ✅ **Audit Logging**: Complete trail of secret transformations
- ✅ **Error Handling**: Comprehensive exception hierarchy

## 🔧 Configuration

### Simple Configuration (`config/simple.toml`)
Basic secret patterns and default security settings.

### Advanced Configuration (`config/advanced.toml`)
Custom patterns, performance tuning, audit logging, and advanced security features.

## 📊 What You'll See

### Before (AI Sees)
```json
{
  "api_key": "{RESOLVE:API_KEY:a1b2c3d4}",
  "database_url": "{RESOLVE:DATABASE_URL:x5y6z7w8}",
  "file_path": "/{USER_HOME}/documents/secret.txt"
}
```

### After (Tool Executes)
```json
{
  "api_key": "sk-1234567890abcdef1234567890abcdef",
  "database_url": "postgresql://user:secret@localhost:5432/mydb",
  "file_path": "/Users/john/documents/secret.txt"
}
```

## 🔍 Framework-Specific Examples

### FastMCP Integration
- **Simple**: Basic tool protection with `@cryptex` decorator
- **Advanced**: Complete middleware with `setup_cryptex_protection()`
- **Use Cases**: File operations, API calls, database queries, system commands

### FastAPI Integration  
- **Simple**: Basic endpoint protection with `@cryptex` decorator
- **Advanced**: Complete middleware with request/response sanitization
- **Use Cases**: Authentication, data processing, file uploads, external API calls

## 📈 Performance Metrics

Each advanced example includes performance monitoring:

- **Request Processing Time**: <5ms for typical payloads
- **Cache Hit Rate**: >95% for repeated patterns
- **Memory Usage**: <5% overhead vs unprotected applications
- **Secrets Detected**: Real-time detection statistics
- **Context Cleanup**: Automatic expiration metrics

## 🐛 Troubleshooting

### Common Issues

1. **Environment Variables**: Ensure all required environment variables are set
2. **Dependencies**: Install framework-specific requirements
3. **Configuration**: Check TOML syntax and pattern definitions
4. **Imports**: Verify Cryptex is properly installed

### Debug Mode

Set `CRYPTEX_DEBUG=true` to enable verbose logging:

```bash
export CRYPTEX_DEBUG=true
python examples/fastmcp/01_simple_hello_world.py
```

## 📖 Further Reading

- [Cryptex Documentation](../README.md)
- [Configuration Guide](../docs/configuration.md)
- [Security Model](../docs/security.md)
- [Performance Tuning](../docs/performance.md)

## 🤝 Contributing

Found an issue or want to add more examples? Please contribute!

1. Fork the repository
2. Create a feature branch
3. Add your example following the existing pattern
4. Include comprehensive documentation
5. Submit a pull request

## 📝 License

These examples are provided under the same license as the Cryptex project.