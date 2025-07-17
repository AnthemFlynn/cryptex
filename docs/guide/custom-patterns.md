# Custom Patterns

While Cryptex's built-in patterns handle 95% of use cases, some applications need custom secret patterns. This guide shows you how to create and use them effectively.

## When to Use Custom Patterns

Consider custom patterns only when:

1. **Built-in patterns don't match your secret format**
2. **Your organization has unique token standards** 
3. **You need different placeholder text for clarity**
4. **Third-party services use non-standard formats**

!!! tip "Try Built-ins First"
    Always check [built-in patterns](zero-config.md#built-in-patterns-95-of-users) before creating custom ones. You might be surprised what's already covered!

## Basic Pattern Registration

### Simple Registration

```python
from cryptex.patterns import register_pattern

# Register a custom pattern
register_pattern(
    name="slack_token",
    regex=r"xoxb-[0-9-a-zA-Z]{51}",
    placeholder="{{SLACK_TOKEN}}"
)

# Use immediately
from cryptex import protect_secrets

@protect_secrets(secrets=["slack_token"])
async def send_slack_message(token: str, message: str) -> bool:
    # AI sees: send_slack_message("{{SLACK_TOKEN}}", "Hello team!")
    # Function gets: real Slack token (xoxb-abc123...)
    return await slack_api.send(token, message)
```

### Pattern Components

| Component | Description | Example |
|-----------|-------------|---------|
| `name` | Unique identifier for the pattern | `"company_api_key"` |
| `regex` | Regular expression to match secrets | `r"ck_[a-f0-9]{40}"` |
| `placeholder` | Text shown to AI systems | `"{{COMPANY_API_KEY}}"` |

## Real-World Pattern Examples

### Company-Specific Tokens

```python
# Example: Stripe API keys
register_pattern(
    name="stripe_secret_key",
    regex=r"sk_live_[a-zA-Z0-9]{24}",
    placeholder="{{STRIPE_SECRET_KEY}}"
)

register_pattern(
    name="stripe_publishable_key", 
    regex=r"pk_live_[a-zA-Z0-9]{24}",
    placeholder="{{STRIPE_PUBLISHABLE_KEY}}"
)

@protect_secrets(secrets=["stripe_secret_key"])
async def process_payment(amount: int, secret_key: str) -> dict:
    # AI sees placeholder, function gets real key
    return await stripe.charge(amount, secret_key)
```

### AWS Credentials

```python
# AWS Access Key ID
register_pattern(
    name="aws_access_key",
    regex=r"AKIA[0-9A-Z]{16}", 
    placeholder="{{AWS_ACCESS_KEY_ID}}"
)

# AWS Secret Access Key
register_pattern(
    name="aws_secret_key",
    regex=r"[A-Za-z0-9/+=]{40}",
    placeholder="{{AWS_SECRET_ACCESS_KEY}}"
)

@protect_secrets(secrets=["aws_access_key", "aws_secret_key"])
async def aws_operation(access_key: str, secret_key: str) -> dict:
    # Both credentials protected
    return await aws_client.call(access_key, secret_key)
```

### Database Credentials

```python
# MongoDB connection strings
register_pattern(
    name="mongodb_url",
    regex=r"mongodb://[^:]+:[^@]+@[^/]+/[^?]+",
    placeholder="{{MONGODB_URL}}"
)

# Redis URLs
register_pattern(
    name="redis_url", 
    regex=r"redis://[^:]*:[^@]*@[^:]+:\d+",
    placeholder="{{REDIS_URL}}"
)

@protect_secrets(secrets=["mongodb_url", "redis_url"])
async def database_sync(mongo_url: str, redis_url: str) -> bool:
    # AI sees placeholders for both database URLs
    return await sync_databases(mongo_url, redis_url)
```

## Advanced Pattern Features

### Complex Regex Patterns

```python
# API keys with optional prefixes
register_pattern(
    name="flexible_api_key",
    regex=r"(?:api_)?key_[a-zA-Z0-9]{32,64}",  # Matches key_abc123 or api_key_abc123
    placeholder="{{API_KEY}}"
)

# JWT tokens
register_pattern(
    name="jwt_token",
    regex=r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",
    placeholder="{{JWT_TOKEN}}"
)

# UUID-based secrets
register_pattern(
    name="uuid_secret",
    regex=r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    placeholder="{{UUID_SECRET}}"
)
```

### Multi-Format Patterns

```python
# Handle multiple formats in one pattern
register_pattern(
    name="github_token_extended",
    regex=r"(?:ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36}|ghu_[a-zA-Z0-9]{36})",
    placeholder="{{GITHUB_TOKEN}}"
)

# This matches:
# - Personal access tokens: ghp_abc123...
# - OAuth tokens: gho_abc123...  
# - User-to-server tokens: ghu_abc123...
```

## Pattern Registration Strategies

### Application Startup Registration

Register all patterns when your application starts:

```python
# patterns.py
from cryptex.patterns import register_pattern

def register_app_patterns():
    """Register all custom patterns for this application"""
    
    # Company API tokens
    register_pattern("company_api_key", r"ck_[a-f0-9]{40}", "{{COMPANY_API_KEY}}")
    register_pattern("company_webhook_secret", r"wh_[a-f0-9]{32}", "{{WEBHOOK_SECRET}}")
    
    # Third-party services
    register_pattern("sendgrid_key", r"SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}", "{{SENDGRID_API_KEY}}")
    register_pattern("twilio_sid", r"AC[a-f0-9]{32}", "{{TWILIO_ACCOUNT_SID}}")
    
    # Database connections
    register_pattern("custom_db_url", r"mydb://[^:]+:[^@]+@[^/]+/[^?]+", "{{CUSTOM_DB_URL}}")

# main.py
from patterns import register_app_patterns

def main():
    # Register patterns first
    register_app_patterns()
    
    # Start application
    app.run()
```

### Module-Level Registration

Register patterns in relevant modules:

```python
# payment_service.py
from cryptex.patterns import register_pattern
from cryptex import protect_secrets

# Register payment-related patterns
register_pattern("stripe_secret", r"sk_live_[a-zA-Z0-9]{24}", "{{STRIPE_SECRET}}")
register_pattern("paypal_client_secret", r"[A-Z]{2}[a-zA-Z0-9_-]{64}", "{{PAYPAL_SECRET}}")

@protect_secrets(secrets=["stripe_secret"])
async def stripe_payment(amount: int, secret_key: str) -> dict:
    return await process_stripe_payment(amount, secret_key)

@protect_secrets(secrets=["paypal_client_secret"])  
async def paypal_payment(amount: int, secret: str) -> dict:
    return await process_paypal_payment(amount, secret)
```

## Pattern Testing and Validation

### Test Your Patterns

```python
import re
from cryptex.patterns import register_pattern, get_pattern

def test_custom_pattern():
    # Register test pattern
    register_pattern("test_token", r"test_[a-z]{10}", "{{TEST_TOKEN}}")
    
    # Test matching
    pattern = get_pattern("test_token")
    
    # Should match
    assert re.match(pattern.regex, "test_abcdefghij")
    
    # Should not match
    assert not re.match(pattern.regex, "test_ABC123")  # Wrong case
    assert not re.match(pattern.regex, "test_abc")     # Too short
    
    print("✅ Pattern validation passed")

test_custom_pattern()
```

### Integration Testing

```python
@protect_secrets(secrets=["custom_token"])
async def test_function(token: str) -> str:
    return f"Processed: {token}"

async def test_pattern_integration():
    # Test with matching token
    result = await test_function("custom_abc123def456")
    
    # Verify AI would see placeholder
    # (This is conceptual - actual testing depends on your AI integration)
    assert "{{CUSTOM_TOKEN}}" in ai_visible_call_log
    
    # Verify function got real token
    assert result == "Processed: custom_abc123def456"
    
    print("✅ Integration test passed")
```

## Pattern Management

### List Available Patterns

```python
from cryptex.patterns import list_patterns

# See all patterns (built-in + custom)
all_patterns = list_patterns()
print("Available patterns:", all_patterns)

# Filter to custom patterns only
custom_patterns = [p for p in all_patterns if not p.startswith(('openai_', 'github_', 'anthropic_'))]
print("Custom patterns:", custom_patterns)
```

### Pattern Information

```python
from cryptex.patterns import get_pattern, pattern_exists

# Check if pattern exists
if pattern_exists("slack_token"):
    pattern = get_pattern("slack_token")
    print(f"Regex: {pattern.regex}")
    print(f"Placeholder: {pattern.placeholder}")
else:
    print("Pattern not found")
```

### Update Patterns

```python
# You can re-register to update a pattern
register_pattern(
    name="slack_token",
    regex=r"xoxb-[0-9-a-zA-Z]{51,56}",  # Updated regex
    placeholder="{{SLACK_BOT_TOKEN}}"   # Updated placeholder
)
```

## Common Patterns Library

Here are some commonly needed custom patterns:

### Social Media APIs

```python
# Twitter API v2
register_pattern("twitter_bearer", r"AAAAAAAAAAAAAAAAAAAAAA[a-zA-Z0-9%]*", "{{TWITTER_BEARER_TOKEN}}")

# Discord bot tokens
register_pattern("discord_bot_token", r"[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}", "{{DISCORD_BOT_TOKEN}}")

# Facebook Graph API
register_pattern("facebook_token", r"EAA[a-zA-Z0-9]{100,}", "{{FACEBOOK_ACCESS_TOKEN}}")
```

### Communication Services

```python
# Twilio
register_pattern("twilio_auth_token", r"[a-f0-9]{32}", "{{TWILIO_AUTH_TOKEN}}")

# SendGrid
register_pattern("sendgrid_key", r"SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}", "{{SENDGRID_API_KEY}}")

# Mailgun
register_pattern("mailgun_key", r"key-[a-f0-9]{32}", "{{MAILGUN_API_KEY}}")
```

### Cloud Services

```python
# Google Cloud
register_pattern("gcp_service_account", r'"private_key":\s*"-----BEGIN PRIVATE KEY-----[^"]+-----END PRIVATE KEY-----"', "{{GCP_SERVICE_ACCOUNT_KEY}}")

# Azure
register_pattern("azure_client_secret", r"[a-zA-Z0-9~._-]{34}", "{{AZURE_CLIENT_SECRET}}")

# DigitalOcean
register_pattern("digitalocean_token", r"[a-f0-9]{64}", "{{DIGITALOCEAN_TOKEN}}")
```

## Best Practices

### 1. Specific Pattern Names

```python
# Good: Specific and clear
register_pattern("stripe_secret_key", r"sk_live_[a-zA-Z0-9]{24}", "{{STRIPE_SECRET_KEY}}")

# Bad: Too generic
register_pattern("api_key", r"[a-zA-Z0-9]{32}", "{{API_KEY}}")
```

### 2. Conservative Regex Patterns

```python
# Good: Specific format matching
register_pattern("github_token", r"ghp_[a-zA-Z0-9]{36}", "{{GITHUB_TOKEN}}")

# Bad: Too broad (matches many things)
register_pattern("any_token", r"[a-zA-Z0-9]+", "{{TOKEN}}")
```

### 3. Clear Placeholder Names

```python
# Good: Clear service and key type
register_pattern("aws_secret_key", r"[A-Za-z0-9/+=]{40}", "{{AWS_SECRET_ACCESS_KEY}}")

# Bad: Unclear what this represents
register_pattern("aws_secret_key", r"[A-Za-z0-9/+=]{40}", "{{SECRET}}")
```

### 4. Document Custom Patterns

```python
"""
Custom Cryptex Patterns

This module registers application-specific secret patterns:

- company_api_key: Internal API keys (format: ck_[40 hex chars])
- webhook_secret: Webhook validation secrets (format: wh_[32 hex chars])
- database_token: Database access tokens (format: db_[64 alphanumeric])

Register these patterns by calling register_app_patterns() at startup.
"""
```

## Error Handling

### Pattern Registration Errors

```python
from cryptex.core.exceptions import PatternRegistrationError

try:
    register_pattern("invalid_pattern", "[invalid regex", "{{INVALID}}")
except PatternRegistrationError as e:
    print(f"Pattern registration failed: {e}")
    # Handle error appropriately
```

### Runtime Pattern Errors

```python
from cryptex.core.exceptions import PatternNotFoundError

try:
    @protect_secrets(secrets=["nonexistent_pattern"])
    async def failing_function(secret: str) -> str:
        return secret
except PatternNotFoundError as e:
    print(f"Pattern not found: {e}")
    # Suggest registration or check for typos
```

## Migration Guide

### From Manual String Replacement

Before:
```python
def sanitize_for_ai(text: str) -> str:
    # Manual pattern replacement
    text = re.sub(r"sk-[a-zA-Z0-9]{32,}", "{{OPENAI_KEY}}", text)
    text = re.sub(r"ghp_[a-zA-Z0-9]{36}", "{{GITHUB_TOKEN}}", text)
    return text
```

After:
```python
from cryptex import protect_secrets

@protect_secrets(secrets=["openai_key", "github_token"])
async def ai_function(openai_key: str, github_token: str) -> str:
    # Automatic protection with better performance and reliability
    return await process_with_credentials(openai_key, github_token)
```

### From Environment Variable Patterns

Before:
```python
import os

# Pattern stored in environment
CUSTOM_PATTERN = os.environ["CUSTOM_TOKEN_PATTERN"]
CUSTOM_PLACEHOLDER = os.environ["CUSTOM_TOKEN_PLACEHOLDER"]

def protect_custom_secret(text: str) -> str:
    return re.sub(CUSTOM_PATTERN, CUSTOM_PLACEHOLDER, text)
```

After:
```python
from cryptex.patterns import register_pattern
from cryptex import protect_secrets

# Register pattern in code (no environment variables needed)
register_pattern("custom_token", r"ct_[a-f0-9]{32}", "{{CUSTOM_TOKEN}}")

@protect_secrets(secrets=["custom_token"])
async def protected_function(token: str) -> str:
    # Automatic protection
    return await process_token(token)
```

## Conclusion

Custom patterns extend Cryptex's zero-config philosophy to handle your specific needs while maintaining simplicity:

- **Register once** at application startup
- **Use everywhere** with the same `@protect_secrets` decorator
- **Test thoroughly** to ensure correct matching
- **Document clearly** for team members

Remember: Custom patterns should be the **exception**, not the rule. The built-in patterns handle 95% of real-world use cases. Only create custom patterns when you genuinely need them.