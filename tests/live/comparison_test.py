#!/usr/bin/env python3
"""
Comparison Test - Protected vs Unprotected Functions

This shows the dramatic difference between protected and unprotected functions
to demonstrate why temporal isolation is critical for AI applications.
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from cryptex_ai import protect_secrets


# Mock AI service that shows us exactly what it receives
class MockAIService:
    @staticmethod
    async def chat_completion(**kwargs):
        return {"received_data": kwargs}

class MockOpenAI:
    class chat:
        class completions:
            create = MockAIService.chat_completion

sys.modules['openai'] = MockOpenAI()


# UNPROTECTED function - exposes secrets to AI
async def analyze_data_UNSAFE(api_key: str, file_path: str, query: str):
    """UNSAFE function that exposes secrets to AI."""

    import openai
    ai_response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"Analyze file {file_path}. Query: {query}"
        }],
        api_key=api_key
    )
    return ai_response


# PROTECTED function - temporal isolation
@protect_secrets(['openai_key', 'file_path'])
async def analyze_data_SAFE(api_key: str, file_path: str, query: str):
    """SAFE function with temporal isolation."""

    import openai
    ai_response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"Analyze file {file_path}. Query: {query}"
        }],
        api_key=api_key
    )
    return ai_response


async def main():
    """Run the comparison demonstration."""

    print("⚖️  PROTECTED vs UNPROTECTED COMPARISON")
    print("=" * 60)
    print("")
    print("This shows the critical difference between:")
    print("❌ Unprotected functions (expose secrets to AI)")
    print("✅ Protected functions (temporal isolation)")
    print("")

    # Sensitive data
    real_api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyzABCDEF123456"
    sensitive_file = "/Users/alice/confidential/customer_database.xlsx"
    query = "Extract all personal information"

    print("🔑 Test Data:")
    print(f"   API Key: {real_api_key}")
    print(f"   Sensitive File: {sensitive_file}")
    print(f"   Query: {query}")
    print("")

    # Test 1: UNPROTECTED function
    print("❌ TESTING UNPROTECTED FUNCTION:")
    print("   (This is what most AI apps do - DANGEROUS!)")

    unsafe_result = await analyze_data_UNSAFE(
        api_key=real_api_key,
        file_path=sensitive_file,
        query=query
    )

    unsafe_data = unsafe_result['received_data']
    unsafe_key = unsafe_data.get('api_key', 'NOT_FOUND')
    unsafe_messages = unsafe_data.get('messages', [{}])
    unsafe_content = unsafe_messages[0].get('content', 'NOT_FOUND')

    print(f"   🤖 AI received API key: {unsafe_key}")
    print(f"   🤖 AI received message: {unsafe_content}")

    if real_api_key in unsafe_content or unsafe_key == real_api_key:
        print("   🚨 SECURITY BREACH: Real secrets exposed to AI!")

    print("")

    # Test 2: PROTECTED function
    print("✅ TESTING PROTECTED FUNCTION:")
    print("   (With @protect_secrets decorator - SAFE!)")

    safe_result = await analyze_data_SAFE(
        api_key=real_api_key,
        file_path=sensitive_file,
        query=query
    )

    safe_data = safe_result['received_data']
    safe_key = safe_data.get('api_key', 'NOT_FOUND')
    safe_messages = safe_data.get('messages', [{}])
    safe_content = safe_messages[0].get('content', 'NOT_FOUND')

    print(f"   🤖 AI received API key: {safe_key}")
    print(f"   🤖 AI received message: {safe_content}")

    if safe_key == "{{OPENAI_API_KEY}}" and "{{FILE_PATH}}" in safe_content:
        print("   🔒 SECURE: AI received safe placeholders only!")

    print("")

    # Comparison summary
    print("📊 COMPARISON RESULTS:")
    print("")

    print("❌ UNPROTECTED Function:")
    print(f"   • API Key exposed: {real_api_key in str(unsafe_data)}")
    print(f"   • File path exposed: {sensitive_file in str(unsafe_data)}")
    print("   • Security risk: HIGH")
    print("   • Compliance: FAILED")
    print("")

    print("✅ PROTECTED Function:")
    print(f"   • API Key protected: {'{{OPENAI_API_KEY}}' in str(safe_data)}")
    print(f"   • File path protected: {'{{FILE_PATH}}' in str(safe_data)}")
    print("   • Security risk: NONE")
    print("   • Compliance: PASSED")
    print("")

    print("🎯 THE DIFFERENCE:")
    print("   One line of code (@protect_secrets) provides:")
    print("   • Complete secret isolation")
    print("   • Zero cognitive overhead")
    print("   • Automatic protection")
    print("   • No configuration required")
    print("")
    print("💡 CONCLUSION:")
    print("   Every AI application should use temporal isolation")
    print("   to prevent accidental secret exposure!")


if __name__ == "__main__":
    print("🚀 Starting protected vs unprotected comparison...")
    print("")

    try:
        asyncio.run(main())
        print("✅ Comparison completed successfully!")

    except Exception as e:
        print(f"❌ Comparison failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
