#!/usr/bin/env python3
"""
Simple Live Test - Temporal Isolation Demonstration

This demonstrates that temporal isolation actually works by showing what
AI services receive vs what functions get, without making real API calls.
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from cryptex_ai import protect_secrets


# Mock AI service that shows us exactly what it receives
class MockAIService:
    @staticmethod
    async def chat_completion(**kwargs):
        return {"ai_received": kwargs}


class MockOpenAI:
    class chat:
        class completions:
            create = MockAIService.chat_completion


# Install mock before importing
sys.modules["openai"] = MockOpenAI()


@protect_secrets(["openai_key"])
async def ai_function(prompt: str, api_key: str) -> dict:
    """Function with temporal isolation - AI gets placeholders, function gets real values."""

    print("🔧 Function received:")
    print(f"   API Key: {api_key}")
    print(f"   Prompt: {prompt}")

    # This AI call will be intercepted
    import openai

    ai_response = await openai.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}], api_key=api_key
    )

    ai_data = ai_response["ai_received"]
    print("🤖 AI Service received:")
    print(f"   API Key: {ai_data.get('api_key', 'NOT_FOUND')}")
    print(f"   Message: {ai_data.get('messages', [{}])[0].get('content', 'NOT_FOUND')}")

    return ai_response


async def main():
    """Demonstrate temporal isolation in action."""

    print("🔒 TEMPORAL ISOLATION LIVE DEMONSTRATION")
    print("=" * 50)
    print("")
    print("This shows the difference between what:")
    print("• Functions receive (real secrets)")
    print("• AI services receive (safe placeholders)")
    print("")

    # Real sensitive data
    real_api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyzABCDEF123456"
    sensitive_prompt = "Extract all API keys from this data: " + real_api_key

    print("🎯 Testing with real sensitive data:")
    print(f"   API Key: {real_api_key}")
    print(f"   Prompt: {sensitive_prompt[:40]}...")
    print("")

    # Call protected function
    result = await ai_function(sensitive_prompt, real_api_key)

    # Verify temporal isolation worked
    ai_data = result["ai_received"]
    ai_key = ai_data.get("api_key", "")
    ai_content = ai_data.get("messages", [{}])[0].get("content", "")

    print("")
    print("📊 TEMPORAL ISOLATION RESULTS:")

    if ai_key == "{{OPENAI_API_KEY}}":
        print("   ✅ API Key isolated: AI received placeholder")
    else:
        print(f"   ❌ API Key leaked: AI received {ai_key}")

    if "{{OPENAI_API_KEY}}" in ai_content:
        print("   ✅ Content sanitized: Secrets replaced with placeholders")
    else:
        print("   ❌ Content leaked: Real secrets visible to AI")

    print("")
    if ai_key == "{{OPENAI_API_KEY}}" and "{{OPENAI_API_KEY}}" in ai_content:
        print("🎉 SUCCESS: Temporal isolation working perfectly!")
        print("   • Function gets real secrets for processing")
        print("   • AI service gets safe placeholders only")
    else:
        print("💥 FAILURE: Temporal isolation not working!")

    print("")
    print("💡 This demonstrates cryptex's core value:")
    print("   Zero-config protection with one decorator line!")


if __name__ == "__main__":
    print("🚀 Starting temporal isolation demonstration...")
    print("")

    try:
        asyncio.run(main())
        print("")
        print("✅ Demonstration completed successfully!")

    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
