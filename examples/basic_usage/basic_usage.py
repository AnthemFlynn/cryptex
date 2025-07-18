#!/usr/bin/env python3
"""
Basic Usage Example - Universal Secret Protection

This example demonstrates the core cryptex functionality using the universal
@protect_secrets decorator. Works with any framework or standalone functions.

What you'll learn:
- How to use @protect_secrets for any Python function
- Zero-config protection with built-in patterns
- How temporal isolation works (AI sees placeholders, functions get real values)
- Multiple secret types in one decorator
"""

import asyncio
import os
import sys
from typing import Any

# Add src to path for local development
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Simple import - works immediately after: pip install cryptex-ai
from cryptex_ai import protect_secrets, register_pattern

try:
    from cryptex_ai import protect_all, protect_api_keys, protect_files
except ImportError:
    # For compatibility - convenience decorators might not be in all versions
    protect_all = protect_api_keys = protect_files = None

# =============================================================================
# Example 1: Basic Secret Protection
# =============================================================================

@protect_secrets(["openai_key"])
async def ai_completion(prompt: str, api_key: str) -> str:
    """
    Call AI API with protected credentials.

    - AI Context: ai_completion("Hello", "{{OPENAI_API_KEY}}")
    - Function Gets: real API key for actual execution
    """
    # Simulate API call
    print(f"🤖 Making API call with key: {api_key[:15]}...")
    await asyncio.sleep(0.1)  # Simulate network call
    return f"AI Response to: {prompt}"


@protect_secrets(["file_path"])
async def read_file(file_path: str) -> str:
    """
    Read file with protected path.

    - AI Context: read_file("/{USER_HOME}/.../{filename}")
    - Function Gets: real file path for actual reading
    """
    print(f"📁 Reading file: {file_path}")
    # Simulate file reading
    return f"Contents of {file_path.split('/')[-1]}"


@protect_secrets(["database_url"])
async def query_database(query: str, db_url: str) -> dict[str, Any]:
    """
    Execute database query with protected connection.

    - AI Context: query_database("SELECT...", "{{DATABASE_URL}}")
    - Function Gets: real database URL for actual connection
    """
    print(f"🗄️  Connecting to database: {db_url[:30]}...")
    await asyncio.sleep(0.1)  # Simulate DB call
    return {"query": query, "rows": 42, "status": "success"}


# =============================================================================
# Example 2: Multiple Secrets in One Function
# =============================================================================

@protect_secrets(["openai_key", "file_path", "database_url"])
async def process_document(
    file_path: str,
    api_key: str,
    db_url: str,
    prompt: str = "Analyze this document"
) -> dict[str, Any]:
    """
    Process document with multiple protected secrets.

    All three secrets are automatically protected:
    - file_path → /{USER_HOME}/.../{filename}
    - api_key → {{OPENAI_API_KEY}}
    - db_url → {{DATABASE_URL}}
    """
    # Read file
    content = await read_file(file_path)

    # Analyze with AI
    analysis = await ai_completion(f"{prompt}: {content}", api_key)

    # Save to database
    result = await query_database(
        f"INSERT INTO analyses VALUES ('{analysis}')",
        db_url
    )

    return {
        "file": file_path.split('/')[-1],
        "analysis": analysis,
        "database_result": result
    }


# =============================================================================
# Example 3: Custom Pattern Registration
# =============================================================================

# Register a custom secret pattern
register_pattern(
    name="slack_token",
    regex=r"xoxb-[0-9-a-zA-Z]{51}",
    placeholder="{{SLACK_TOKEN}}",
    description="Slack bot token"
)

@protect_secrets(["slack_token"])
async def send_slack_message(message: str, token: str) -> str:
    """
    Send Slack message with protected token.

    Custom pattern automatically protects slack tokens:
    - AI Context: send_slack_message("Hello", "{{SLACK_TOKEN}}")
    - Function Gets: real token (xoxb-...)
    """
    print(f"💬 Sending Slack message with token: {token[:20]}...")
    await asyncio.sleep(0.1)  # Simulate API call
    return f"Message sent: {message}"


# =============================================================================
# Example 4: Convenience Decorators
# =============================================================================

if protect_api_keys:
    @protect_api_keys()  # Protects openai_key, anthropic_key automatically
    async def multi_ai_call(prompt: str, openai_key: str, anthropic_key: str) -> str:
        """Use multiple AI services with automatic key protection."""
        print(f"🤖 Calling OpenAI: {openai_key[:15]}...")
        print(f"🤖 Calling Anthropic: {anthropic_key[:15]}...")
        return f"Combined AI response to: {prompt}"
else:
    @protect_secrets(["openai_key", "anthropic_key"])
    async def multi_ai_call(prompt: str, openai_key: str, anthropic_key: str) -> str:
        """Use multiple AI services with explicit key protection."""
        print(f"🤖 Calling OpenAI: {openai_key[:15]}...")
        print(f"🤖 Calling Anthropic: {anthropic_key[:15]}...")
        return f"Combined AI response to: {prompt}"

if protect_files:
    @protect_files()  # Protects file_path automatically
    async def backup_file(source_path: str, dest_path: str) -> str:
        """Backup file with automatic path protection."""
        print(f"💾 Backing up {source_path} to {dest_path}")
        return "Backup completed"
else:
    @protect_secrets(["file_path"])
    async def backup_file(source_path: str, dest_path: str) -> str:
        """Backup file with explicit path protection."""
        print(f"💾 Backing up {source_path} to {dest_path}")
        return "Backup completed"

if protect_all:
    @protect_all()  # Protects all built-in secret types
    async def kitchen_sink_function(
        api_key: str,
        db_url: str,
        file_path: str,
        token: str
    ) -> str:
        """Function that might use any type of secret."""
        print("🔒 All secrets automatically protected!")
        return "All operations completed safely"
else:
    @protect_secrets(["openai_key", "database_url", "file_path", "github_token"])
    async def kitchen_sink_function(
        api_key: str,
        db_url: str,
        file_path: str,
        token: str
    ) -> str:
        """Function that uses multiple types of secrets."""
        print("🔒 All secrets explicitly protected!")
        return "All operations completed safely"


# =============================================================================
# Main Demo Runner
# =============================================================================

async def main():
    """Run all examples to demonstrate cryptex functionality."""
    print("=" * 60)
    print("🔒 Cryptex Basic Usage Demo")
    print("   Universal Secret Protection for Any Framework")
    print("=" * 60)

    # Set up mock environment
    os.environ.setdefault("OPENAI_API_KEY", "sk-" + "1234567890abcdef" * 3)
    os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/mydb")
    os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-" + "abcdef123456" * 3)

    # Example 1: Basic protection
    print("\n📝 Example 1: Basic Secret Protection")
    print("-" * 40)

    result1 = await ai_completion(
        "Hello, how are you?",
        os.environ["OPENAI_API_KEY"]
    )
    print(f"✅ Result: {result1}")

    result2 = await read_file("/Users/developer/documents/secret_data.txt")
    print(f"✅ Result: {result2}")

    result3 = await query_database(
        "SELECT * FROM users LIMIT 5",
        os.environ["DATABASE_URL"]
    )
    print(f"✅ Result: {result3}")

    # Example 2: Multiple secrets
    print("\n📝 Example 2: Multiple Secrets")
    print("-" * 40)

    result4 = await process_document(
        "/Users/developer/documents/analysis.pdf",
        os.environ["OPENAI_API_KEY"],
        os.environ["DATABASE_URL"],
        "Summarize this document"
    )
    print(f"✅ Result: {result4}")

    # Example 3: Custom pattern
    print("\n📝 Example 3: Custom Pattern")
    print("-" * 40)

    slack_token = "xoxb-fake-token-for-demo-purposes-only-not-real"
    result5 = await send_slack_message("Hello team!", slack_token)
    print(f"✅ Result: {result5}")

    # Example 4: Convenience decorators
    print("\n📝 Example 4: Convenience Decorators")
    print("-" * 40)

    result6 = await multi_ai_call(
        "What is the meaning of life?",
        os.environ["OPENAI_API_KEY"],
        os.environ["ANTHROPIC_API_KEY"]
    )
    print(f"✅ Result: {result6}")

    result7 = await backup_file(
        "/Users/developer/important.txt",
        "/Users/developer/backups/important.txt"
    )
    print(f"✅ Result: {result7}")

    result8 = await kitchen_sink_function(
        os.environ["OPENAI_API_KEY"],
        os.environ["DATABASE_URL"],
        "/Users/developer/data.json",
        "ghp_1234567890abcdef1234567890abcdef12345678"
    )
    print(f"✅ Result: {result8}")

    # Summary
    print("\n" + "=" * 60)
    print("🎉 All Examples Completed Successfully!")
    print("\n💡 Key Takeaways:")
    print("   ✅ @protect_secrets works with any Python function")
    print("   ✅ Zero configuration - built-in patterns work immediately")
    print("   ✅ AI models see safe placeholders, functions get real values")
    print("   ✅ Multiple secret types protected simultaneously")
    print("   ✅ Custom patterns for edge cases (5% of users)")
    print("   ✅ Convenience decorators for common scenarios")
    print("   ✅ Framework-agnostic - works anywhere!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
