"""
Integration tests for AI call interception within decorated functions.

Validates that the @protect_secrets decorator actually intercepts AI library
calls and ensures AI services receive sanitized data instead of real secrets.
"""

import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

from cryptex_ai import protect_secrets


class TestAICallInterception:
    """Test that decorated functions intercept AI calls properly."""

    def setup_method(self):
        """Set up mock AI libraries for testing."""
        # Create mock OpenAI module
        self.mock_openai_create = AsyncMock()
        mock_openai = MagicMock()
        mock_openai.chat.completions.create = self.mock_openai_create
        sys.modules['openai'] = mock_openai
        
        # Create mock Anthropic module
        self.mock_anthropic_create = AsyncMock()
        mock_anthropic = MagicMock()
        mock_anthropic.messages.create = self.mock_anthropic_create
        sys.modules['anthropic'] = mock_anthropic

    def teardown_method(self):
        """Clean up mock modules."""
        if 'openai' in sys.modules:
            del sys.modules['openai']
        if 'anthropic' in sys.modules:
            del sys.modules['anthropic']

    @pytest.mark.asyncio
    async def test_openai_call_interception(self):
        """Test that OpenAI calls are intercepted and sanitized."""
        @protect_secrets(['openai_key'])
        async def ai_function(api_key: str, prompt: str):
            import openai
            return await openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                api_key=api_key
            )

        real_api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyzABCDEF123456"
        
        # Mock return value
        self.mock_openai_create.return_value = {"response": "test"}
        
        # Execute function
        await ai_function(real_api_key, "Hello AI")
        
        # Verify OpenAI was called with sanitized data
        assert self.mock_openai_create.called
        call_kwargs = self.mock_openai_create.call_args.kwargs
        
        # API key should be sanitized
        assert call_kwargs['api_key'] == '{{OPENAI_API_KEY}}'
        # Other data should remain unchanged
        assert call_kwargs['model'] == 'gpt-4'
        assert call_kwargs['messages'][0]['content'] == 'Hello AI'

    @pytest.mark.asyncio 
    async def test_multiple_secrets_interception(self):
        """Test that multiple secret types are all intercepted."""
        @protect_secrets(['openai_key', 'file_path'])
        async def complex_ai_function(api_key: str, file_path: str):
            import openai
            return await openai.chat.completions.create(
                model="gpt-4",
                messages=[{
                    "role": "user", 
                    "content": f"Analyze file: {file_path}"
                }],
                api_key=api_key
            )

        real_api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyzABCDEF123456"
        real_file_path = "/Users/john/secret-documents/passwords.txt"
        
        # Mock return value
        self.mock_openai_create.return_value = {"response": "analysis"}
        
        # Execute function
        await complex_ai_function(real_api_key, real_file_path)
        
        # Verify both secrets were sanitized
        call_kwargs = self.mock_openai_create.call_args.kwargs
        assert call_kwargs['api_key'] == '{{OPENAI_API_KEY}}'
        
        message_content = call_kwargs['messages'][0]['content']
        assert '{{FILE_PATH}}' in message_content
        assert real_file_path not in message_content

    @pytest.mark.asyncio
    async def test_function_gets_real_values(self):
        """Test that the function itself receives real values, not placeholders."""
        received_values = {}
        
        @protect_secrets(['openai_key'])
        async def ai_function(api_key: str):
            # Store what the function receives
            received_values['api_key'] = api_key
            
            # Call AI (this will be intercepted)
            import openai
            return await openai.chat.completions.create(
                model="gpt-4",
                api_key=api_key
            )

        real_api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyzABCDEF123456"
        
        # Mock return value
        self.mock_openai_create.return_value = {"response": "test"}
        
        # Execute function
        await ai_function(real_api_key)
        
        # Function should receive real values
        assert received_values['api_key'] == real_api_key
        
        # But AI should receive sanitized values
        call_kwargs = self.mock_openai_create.call_args.kwargs
        assert call_kwargs['api_key'] == '{{OPENAI_API_KEY}}'

    @pytest.mark.asyncio
    async def test_no_ai_libraries_available(self):
        """Test that decorator works even when AI libraries aren't imported."""
        # Remove mock modules to simulate no AI libraries
        if 'openai' in sys.modules:
            del sys.modules['openai']
        if 'anthropic' in sys.modules:
            del sys.modules['anthropic']
        
        @protect_secrets(['openai_key'])
        async def simple_function(api_key: str):
            # No AI calls, just return the key
            return f"Key received: {api_key}"

        real_api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyzABCDEF123456"
        
        # Should work without errors
        result = await simple_function(real_api_key)
        
        # Function should still work normally
        assert "Key received:" in str(result)

    @pytest.mark.asyncio
    async def test_anthropic_call_interception(self):
        """Test that Anthropic calls are also intercepted."""
        @protect_secrets(['anthropic_key'])
        async def anthropic_function(api_key: str):
            import anthropic
            return await anthropic.messages.create(
                model="claude-3",
                messages=[{"role": "user", "content": "Hello"}],
                api_key=api_key
            )

        real_api_key = "sk-ant-api03-1234567890abcdefghijklmnopqrstuvwxyz-AA"
        
        # Mock return value
        self.mock_anthropic_create.return_value = {"response": "hello"}
        
        # Execute function
        await anthropic_function(real_api_key)
        
        # Verify Anthropic was called with sanitized data
        assert self.mock_anthropic_create.called
        call_kwargs = self.mock_anthropic_create.call_args.kwargs
        assert call_kwargs['api_key'] == '{{ANTHROPIC_API_KEY}}'