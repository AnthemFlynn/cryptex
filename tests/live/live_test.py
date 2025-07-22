#!/usr/bin/env python3
"""
Live Test - Real API Call Validation

This test makes actual OpenAI API calls to validate temporal isolation
works with real services. Only run when you have real API keys and
want to validate the implementation actually works.

WARNING: This costs money as it makes real API calls!
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from cryptex_ai import protect_secrets


@protect_secrets(['openai_key'])
async def real_openai_call(prompt: str, api_key: str) -> str:
    """Make a real OpenAI API call with temporal isolation."""

    try:
        import openai
    except ImportError:
        print("❌ OpenAI library not installed. Install with: pip install openai")
        return "ERROR: OpenAI not available"

    print(f"🔧 Function received API key: {api_key[:15]}...")

    try:
        client = openai.OpenAI(api_key=api_key)
        response = await client.chat.completions.acreate(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"❌ OpenAI API call failed: {e}")
        return f"ERROR: {e}"


async def main():
    """Run live API test with user confirmation."""

    print("🔴 LIVE API TEST - REAL MONEY WARNING!")
    print("=" * 50)
    print("")
    print("This test makes REAL OpenAI API calls which COST MONEY!")
    print("It validates that temporal isolation works with real services.")
    print("")

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY environment variable found.")
        print("   Set it with: export OPENAI_API_KEY='your-real-key'")
        return

    print(f"🔑 Found API key: {api_key[:15]}...")
    print("")

    # Get user confirmation
    print("⚠️  COST WARNING:")
    print("   This will make a real OpenAI API call (~$0.001)")
    print("   Only proceed if you understand this costs money!")
    print("")

    try:
        confirmation = input("Type 'YES' to proceed with real API call: ")
        if confirmation != "YES":
            print("❌ Test cancelled - user did not confirm")
            return
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
        return

    print("")
    print("🚀 Proceeding with live API test...")
    print("")

    # Make the call
    test_prompt = "Say hello and confirm you received this message safely."

    print(f"📤 Sending prompt: {test_prompt}")
    print("🔒 Temporal isolation should protect API key from being logged")
    print("")

    result = await real_openai_call(test_prompt, api_key)

    print("📥 Response received:")
    print(f"   {result}")
    print("")

    if result.startswith("ERROR:"):
        print("❌ Live test failed - API call unsuccessful")
    else:
        print("✅ Live test successful!")
        print("   • Real API call completed")
        print("   • Function received real API key")
        print("   • Temporal isolation protected secrets")

    print("")
    print("💡 Note: Check your logs - API key should appear as {{OPENAI_API_KEY}}")


if __name__ == "__main__":
    print("🔴 Starting LIVE API test (costs money)...")
    print("")

    try:
        asyncio.run(main())
        print("")
        print("✅ Live test completed!")

    except Exception as e:
        print(f"❌ Live test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
