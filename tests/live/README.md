# Live Integration Tests

This directory contains tests that validate temporal isolation works with real AI services.

## Test Files

### `test_real_ai_integration.py`
- **Purpose**: pytest-compatible live tests with real AI APIs
- **Requirements**: Real API keys and `RUN_LIVE_TESTS=1` environment variable
- **Cost**: Makes real API calls (costs money)
- **Usage**: Only run in CI or when explicitly validating live integration

### Root Directory Live Tests

#### `simple_live_test.py`
- **Purpose**: Demonstrate temporal isolation without real API calls
- **Method**: Uses mock AI service to show what AI receives vs function receives
- **Cost**: Free (no real API calls)
- **Usage**: Safe to run anytime to prove the concept works

```bash
python simple_live_test.py
```

#### `comparison_test.py`
- **Purpose**: Show the security difference between protected and unprotected functions
- **Method**: Side-by-side comparison of secret exposure
- **Cost**: Free (no real API calls)
- **Usage**: Educational demonstration of why temporal isolation matters

```bash
python comparison_test.py
```

#### `live_test.py`
- **Purpose**: Real API call validation with user confirmation
- **Method**: Makes actual OpenAI API calls with real keys
- **Cost**: Expensive (real API calls)
- **Usage**: Manual validation only when needed

```bash
export OPENAI_API_KEY="your-real-key"
python live_test.py
```

## Running Live Tests

### Safe Tests (Recommended)
```bash
# Demonstrate working temporal isolation (no cost)
python simple_live_test.py

# Show security comparison (no cost)
python comparison_test.py
```

### Real API Tests (Costs Money)
```bash
# Set up environment
export OPENAI_API_KEY="your-real-openai-key"
export RUN_LIVE_TESTS=1

# Run pytest live tests
pytest tests/live/test_real_ai_integration.py -v

# Run manual live test with confirmation
python live_test.py
```

## What Live Tests Prove

1. **Temporal Isolation Works**: Functions receive real secrets, AI services receive placeholders
2. **Monkey-Patching Works**: AI library calls are actually intercepted
3. **Security Guarantee**: No real secrets leak to AI services
4. **Zero Configuration**: Works out of the box with no setup

## Expected Results

### Protected Function
```
🔧 Function received:
   API Key: sk-1234567890abcdefghijklmnopqrstuvwxyzABCDEF123456
   
🤖 AI Service received:
   API Key: {{OPENAI_API_KEY}}
   
✅ SUCCESS: Temporal isolation working!
```

### Unprotected Function  
```
🤖 AI Service received:
   API Key: sk-1234567890abcdefghijklmnopqrstuvwxyzABCDEF123456
   
🚨 SECURITY BREACH: Real secrets exposed to AI!
```

## Integration with CI/CD

Live tests can be integrated into CI/CD pipelines:

```yaml
# Only run if secrets are available
- name: Run Live Integration Tests
  if: env.OPENAI_API_KEY != ''
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    RUN_LIVE_TESTS: 1
  run: pytest tests/live/ -v
```

This ensures temporal isolation works in production environments.