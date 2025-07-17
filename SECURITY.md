# Security Policy

## Supported Versions

We actively support the following versions of Cryptex with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities through one of the following methods:

### GitHub Security Advisories (Preferred)

1. Go to the [Security Advisories](https://github.com/AnthemFlynn/cryptex/security/advisories) page
2. Click "Report a vulnerability"
3. Fill out the vulnerability report form
4. Submit the report

### Email

You can also email security reports to: `security@cryptex-ai.com`

Please include the following information in your report:

- **Type of issue** (e.g., secret exposure, temporal isolation bypass, pattern injection, etc.)
- **Full paths of source file(s) related to the manifestation of the issue**
- **The location of the affected source code** (tag/branch/commit or direct URL)
- **Any special configuration required to reproduce the issue**
- **Step-by-step instructions to reproduce the issue**
- **Proof-of-concept or exploit code** (if possible)
- **Impact of the issue**, including how an attacker might exploit the issue

## Response Timeline

- **Initial Response:** Within 48 hours
- **Triage and Assessment:** Within 1 week
- **Fix Development:** Depends on severity and complexity
- **Security Advisory Publication:** After fix is available

## Security Architecture

### Zero Attack Surface Design

Cryptex is designed with security as the primary concern:

- **Zero Dependencies**: No external packages eliminates supply chain attacks
- **Zero Config Files**: No configuration parsing eliminates injection attacks
- **Zero File I/O**: Pure in-memory operation eliminates file-based attacks
- **Standard Library Only**: Pure Python 3.11+ standard library reduces attack surface

### Temporal Isolation Security Model

Cryptex provides **temporal isolation** through a three-phase security model:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Raw Secrets   │    │   AI Processing  │    │ Tool Execution  │
│                 │    │                  │    │                 │
│ sk-abc123...    │───▶│ {{OPENAI_KEY}}   │───▶│ sk-abc123...    │
│ /Users/alice/   │    │ /{USER_HOME}/    │    │ /Users/alice/   │
│ ghp_xyz789...   │    │ {{GITHUB_TOKEN}} │    │ ghp_xyz789...   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
     Phase 1:              Phase 2:              Phase 3: 
  Sanitization          AI sees safe          Resolution for
  for AI context       placeholders          tool execution
```

#### Phase 1: Sanitization
- **Input Processing**: All input data is scanned for secret patterns
- **Pattern Matching**: Built-in and custom patterns detect secrets
- **Placeholder Generation**: Secrets replaced with safe placeholders
- **Validation**: Ensures no secrets leak to AI context

#### Phase 2: AI Processing
- **Safe Context**: AI models only see sanitized data with placeholders
- **Zero Exposure**: Real secrets never enter AI processing pipelines
- **Audit Trail**: All AI interactions use sanitized data
- **Logging Safety**: Log entries contain only placeholder values

#### Phase 3: Resolution
- **Just-in-Time**: Secrets resolved only during function execution
- **Minimal Exposure**: Secrets exist in memory only during actual usage
- **Cleanup**: Sensitive data cleared after function completion
- **Isolation**: Each function execution gets isolated secret resolution

### Security Features

#### Pattern Security
- **Runtime Validation**: All regex patterns validated at runtime
- **Error Handling**: Comprehensive error handling prevents information leakage
- **Thread Safety**: Concurrent access protected with proper locking
- **Injection Protection**: Pattern registration validates against injection attacks

#### Memory Security
- **Minimal Lifetime**: Secrets minimized in memory lifetime
- **Isolated Execution**: Each function call gets isolated context
- **Result Sanitization**: Function outputs sanitized before returning
- **Exception Handling**: Error messages sanitized to prevent secret leakage

#### Concurrency Security
- **Thread-Safe Registry**: Pattern registry protected with threading locks
- **Atomic Operations**: All critical operations are atomic
- **Race Condition Protection**: Proper synchronization prevents race conditions
- **Context Isolation**: Each execution context is properly isolated

## Security Best Practices for Users

### Secure Usage Patterns

```python
from cryptex import protect_secrets

# ✅ Secure: Use built-in patterns
@protect_secrets(["openai_key", "github_token"])
async def secure_ai_function(prompt: str, api_key: str, token: str) -> str:
    # AI sees: secure_ai_function("Hello", "{{OPENAI_API_KEY}}", "{{GITHUB_TOKEN}}")
    # Function gets: real values for execution
    return await ai_workflow(prompt, api_key, token)

# ✅ Secure: Custom patterns for specific use cases
from cryptex import register_pattern

register_pattern(
    name="company_api_key",
    regex=r"mycompany-[a-f0-9]{32}",
    placeholder="{{COMPANY_API_KEY}}",
    description="Company internal API key"
)

@protect_secrets(["company_api_key"])
async def company_function(api_key: str) -> str:
    return await company_api_call(api_key)
```

### Security Anti-patterns

```python
# ❌ Insecure: Hardcoded secrets (but still protected)
api_key = "sk-1234567890abcdef"  # Don't hardcode secrets

# ❌ Insecure: Disabling auto-detection
@protect_secrets(["openai_key"], auto_detect=False)  # May miss other secrets

# ❌ Insecure: Using overly broad patterns
register_pattern("broad", r".*", "{{EVERYTHING}}")  # Too broad
```

### Environment Security

- **Development**: Test with security scanning enabled
- **Production**: Validate all secret patterns are properly configured
- **CI/CD**: Include security tests in automated pipelines
- **Monitoring**: Monitor for pattern matching failures

## Known Security Considerations

### Current Protections

1. **Memory Isolation**: Secrets isolated per function execution
2. **Sanitized Logging**: All logs contain only placeholder values
3. **Error Sanitization**: Exception messages sanitized automatically
4. **Thread Safety**: Concurrent access properly protected

### Acknowledged Limitations

1. **Process Memory**: Secrets exist in process memory during execution
2. **Memory Dumps**: No protection against process memory dumps
3. **Debugger Access**: Debuggers can access secret values during execution
4. **Stack Traces**: Deep stack traces may contain sensitive context

### Mitigation Strategies

- **Short-lived Execution**: Minimize secret lifetime in memory
- **Secure Environments**: Run in secure, isolated environments
- **Process Security**: Use process isolation and memory protection
- **Debug Security**: Disable debuggers in production environments

## Security Testing

### Automated Security Testing

```bash
# Run security test suite
make test-security

# Full test suite including security
make test

# Performance tests (security overhead validation)
make test-performance
```

### Security Test Categories

- **Pattern Matching**: Validate all built-in patterns detect real secrets
- **Temporal Isolation**: Verify AI context never sees real secrets
- **Thread Safety**: Concurrent access security validation
- **Error Handling**: Exception sanitization verification
- **Memory Security**: Validate proper cleanup and isolation

### Manual Security Testing

1. **Pattern Injection**: Test custom pattern validation
2. **Concurrency**: Test thread safety under load
3. **Error Paths**: Validate error message sanitization
4. **Memory Analysis**: Check for secret exposure in memory

## Security Updates

### Update Policy

- **Critical**: Immediate patch release (0-24 hours)
- **High**: Patch within 1-7 days
- **Medium**: Patch within 2-4 weeks
- **Low**: Patch in next minor release

### Notification Channels

- **GitHub Security Advisories**: Automatic notifications for repository watchers
- **Release Notes**: Security fixes documented in CHANGELOG.md
- **PyPI**: Security releases published to PyPI immediately

## Compliance and Standards

### Security Standards

- **OWASP**: Following OWASP Top 10 guidelines for secure coding
- **NIST**: Aligned with NIST Cybersecurity Framework
- **Zero Trust**: Never trust, always verify approach

### Security Controls

- **Static Analysis**: Code scanned with ruff and bandit
- **Dependency Management**: Zero external dependencies eliminates supply chain risks
- **Code Review**: All changes require security review
- **Automated Testing**: Security tests run on every commit

## Security Research

We welcome security research on Cryptex. If you're conducting security research:

1. **Responsible Disclosure**: Follow responsible disclosure practices
2. **Scope**: Focus on the temporal isolation security model
3. **Testing**: Use test environments, not production systems
4. **Documentation**: Document findings clearly with reproduction steps

### Research Areas of Interest

- **Pattern Bypass**: Attempts to bypass pattern matching
- **Temporal Isolation**: Attempts to access secrets during sanitized phases
- **Memory Analysis**: Memory-based attacks on secret storage
- **Concurrency**: Race conditions or thread safety issues

## Contact

For security-related questions or concerns:

- **Security Team**: security@cryptex-ai.com
- **General Issues**: Use GitHub Issues (for non-security issues only)
- **Documentation**: See CONTRIBUTING.md for development security guidelines

---

Thank you for helping keep Cryptex and its users secure!