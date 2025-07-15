# Cryptex

Bulletproof secrets isolation for AI/LLM applications.

## Purpose

Cryptex solves the "All-or-Nothing Security Dilemma" where developers must choose between exposing secrets to AI (dangerous) or hiding them completely (broken functionality). It provides temporal isolation that allows AI to process data safely while ensuring secrets are only resolved during execution.

## How It Works

Cryptex implements a three-phase Temporal Isolation Engine:

1. **Sanitization Phase**: Converts sensitive data to AI-safe placeholders `{RESOLVE:SECRET_TYPE:HASH}`
2. **AI Processing Phase**: AI sees placeholders, never real secrets
3. **Secret Resolution Phase**: Placeholders resolved during execution

## Quick Start

```python
import cryptex

@cryptex(secrets=['api_key', 'database_url'])
async def ai_powered_function(user_input: str) -> str:
    # AI sees: api_key="{RESOLVE:API_KEY:abc123}"
    # Execution gets: api_key="sk-real-key"
    return await ai_workflow(user_input)
```

For fine-grained control:

```python
async with cryptex.secure_session() as session:
    sanitized_data = await session.sanitize_for_ai(raw_data)
    ai_result = await ai_function(sanitized_data)
    resolved_result = await session.resolve_secrets(ai_result)
```

## Installation

```bash
pip install cryptex
```

## Performance

- Sanitization: <5ms for 1KB payloads
- Resolution: <10ms for 10 placeholders
- Memory overhead: <5% of application memory

## License

MIT