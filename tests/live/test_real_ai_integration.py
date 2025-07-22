"""
Live integration test with real AI services.

This test makes actual API calls to validate that temporal isolation
works in practice with real AI services. It requires real API keys
and should only be run manually or in CI with proper secrets.

Usage:
    export OPENAI_API_KEY="sk-your-real-key"
    pytest tests/live/test_real_ai_integration.py -v
"""

import os

import pytest

# Only run if explicitly requested
pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_LIVE_TESTS"),
    reason="Live tests require RUN_LIVE_TESTS=1 and real API keys"
)

from cryptex_ai import protect_secrets


class TestLiveAIIntegration:
    """Live integration tests with real AI services."""

    def setup_method(self):
        """Set up for live tests."""
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        if not self.openai_key:
            pytest.skip("OPENAI_API_KEY not provided")

        # Track what AI service actually receives
        self.ai_received_data = {}

    @pytest.mark.asyncio
    async def test_live_openai_temporal_isolation(self):
        """Test temporal isolation with real OpenAI API."""

        # Patch the actual OpenAI create method to capture what it receives

        async def capture_openai_call(*args, **kwargs):
            """Capture what OpenAI actually receives."""
            self.ai_received_data = kwargs.copy()

            # Make a minimal real call to validate the key format
            # Use the cheapest model and minimal tokens
            try:
                import openai
                client = openai.OpenAI(api_key=kwargs.get('api_key'))
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=1
                )
                return response
            except Exception as e:
                # Return the error so we can analyze what happened
                return {"error": str(e), "received_api_key": kwargs.get('api_key')}

        @protect_secrets(['openai_key'])
        async def ai_function(api_key: str, user_message: str):
            """Function that makes real AI call - should be intercepted."""

            # This call should be intercepted by our decorator
            result = await capture_openai_call(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": user_message}],
                api_key=api_key,
                max_tokens=1
            )
            return result

        # Execute the protected function with real API key
        result = await ai_function(
            api_key=self.openai_key,
            user_message="Test message with secret path: /Users/alice/secrets/key.txt"
        )

        print("\n🔍 Live Test Results:")
        print(f"   Real API key: {self.openai_key[:20]}...")
        print(f"   AI received key: {self.ai_received_data.get('api_key', 'NOT_CAPTURED')}")
        print(f"   AI received message: {self.ai_received_data.get('messages', [{}])[0].get('content', 'NOT_CAPTURED')}")

        # Validate temporal isolation
        received_key = self.ai_received_data.get('api_key')

        if received_key == '{{OPENAI_API_KEY}}':
            print("✅ SUCCESS: AI service received placeholder!")
            print("🔒 True temporal isolation confirmed with live AI service")
            assert True
        elif received_key == self.openai_key:
            print("❌ FAILURE: AI service received real API key!")
            print("🚨 Temporal isolation is NOT working with live AI service")
            raise AssertionError("Real API key leaked to AI service")
        else:
            print(f"❓ UNEXPECTED: AI received: {received_key}")
            print("Result:", result)
            raise AssertionError(f"Unexpected API key received: {received_key}")

    def test_dogfooding_protection(self):
        """Test the library protecting itself - dogfooding/self-referential test."""

        @protect_secrets(['openai_key'])
        def analyze_library_code(api_key: str, file_path: str):
            """
            Function that would analyze this library's code.
            This is 'dogfooding' - using the library to protect itself.
            """

            # Simulate what would happen if we sent library code to AI
            code_analysis_prompt = f"""
            Analyze this Python library code:
            - API Key: {api_key}
            - Code location: {file_path}
            - Please review the security implementation
            """

            # In a real scenario, this would go to an AI service
            # For this test, we just return what would be sent
            return {
                "prompt": code_analysis_prompt,
                "api_key": api_key,
                "file_path": file_path
            }

        # Test with real-looking data
        real_api_key = self.openai_key if self.openai_key else "sk-test1234567890abcdefghijklmnopqrstuvwxyz"
        real_file_path = "/Users/developer/cryptex-ai/src/cryptex_ai/core/engine.py"

        result = analyze_library_code(
            api_key=real_api_key,
            file_path=real_file_path
        )

        print("\n🔄 Dogfooding Test Results:")
        print(f"   Input API key: {real_api_key[:20]}...")
        print(f"   Input file path: {real_file_path}")
        print(f"   Result API key: {result['api_key']}")
        print(f"   Result file path: {result['file_path']}")

        # The function should receive real values (for processing)
        # but any AI service would receive placeholders
        assert result['api_key'] == real_api_key, "Function should receive real API key"
        assert result['file_path'] == real_file_path, "Function should receive real file path"

        # Check that the prompt contains placeholders (what would go to AI)
        prompt = result['prompt']
        if '{{OPENAI_API_KEY}}' in prompt and '{{FILE_PATH}}' in prompt:
            print("✅ SUCCESS: Library protected itself - placeholders in AI prompt")
        else:
            print("❌ FAILURE: Real secrets in prompt that would go to AI")
            print(f"Prompt: {prompt}")
            raise AssertionError("Secrets not properly sanitized in AI prompt")

    def test_live_test_instructions(self):
        """Provide instructions for running live tests."""
        print("\n📋 To run live tests:")
        print("   1. Set environment variables:")
        print("      export OPENAI_API_KEY='your-real-openai-key'")
        print("      export RUN_LIVE_TESTS=1")
        print("   2. Run with pytest:")
        print("      pytest tests/live/test_real_ai_integration.py -v -s")
        print("   3. This will make real API calls and cost money!")
        print("   4. Only run this when you want to validate temporal isolation works with real AI services")

        # This test always passes - it's just for instructions
        assert True
