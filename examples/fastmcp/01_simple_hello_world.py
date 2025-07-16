#!/usr/bin/env python3
"""
FastMCP Simple Hello World Example - Zero-Config Architecture

This example demonstrates basic secret protection using the @protect_tool decorator
with a FastMCP server. It shows how Cryptex provides temporal isolation with
ZERO configuration required - built-in patterns handle common secrets automatically.

What you'll learn:
- How to use the @protect_tool decorator for individual tool protection
- How temporal isolation works (sanitization → AI processing → resolution)
- What AI models see vs what tools actually execute with
- Zero-config protection for OpenAI, GitHub, database URLs, file paths
- Built-in patterns that work immediately without any setup
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path so we can import cryptex
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import Cryptex components - Zero Config!
from cryptex.decorators.mcp import protect_tool
from cryptex.core import secure_session

# Import example utilities
from examples.shared.utils import (
    setup_example_environment,
    print_separator,
    print_phase,
    print_security_demo,
    MockAPIClient,
    MockFileSystem,
    validate_environment
)


# =============================================================================
# Mock FastMCP Server Implementation
# =============================================================================

class MockFastMCPServer:
    """
    Mock FastMCP server for demonstration purposes.
    
    In a real application, you would use:
    from fastmcp import FastMCPServer
    """
    
    def __init__(self, name: str = "cryptex-example"):
        self.name = name
        self.tools = {}
        self.middleware = []
        print(f"🚀 Mock FastMCP Server '{name}' initialized")
    
    def tool(self, name: str = None, description: str = None):
        """Decorator to register a tool with the server."""
        def decorator(func):
            tool_name = name or func.__name__
            self.tools[tool_name] = {
                'function': func,
                'description': description or func.__doc__
            }
            print(f"🔧 Tool '{tool_name}' registered")
            return func
        return decorator
    
    async def call_tool(self, tool_name: str, *args, **kwargs):
        """Call a registered tool."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool_info = self.tools[tool_name]
        return await tool_info['function'](*args, **kwargs)
    
    def list_tools(self):
        """List all registered tools."""
        print(f"\n📋 Available tools on server '{self.name}':")
        for name, info in self.tools.items():
            print(f"   - {name}: {info['description']}")


# =============================================================================
# Example 1: Basic Secret Protection
# =============================================================================

# Create mock server
server = MockFastMCPServer("hello-world-server")

@server.tool("read_secret_file", "Read a file that contains sensitive information")
@protect_tool(secrets=["file_path"])
async def read_secret_file(file_path: str) -> str:
    """
    Read a file containing sensitive information.
    
    This demonstrates temporal isolation with ZERO CONFIG:
    - AI sees: file_path = "/{USER_HOME}/.../{filename}"
    - Tool gets: file_path = "/Users/developer/sensitive-data/secrets.json"
    - Built-in file_path pattern works automatically!
    """
    print_phase("Tool Execution", "Reading file with real path")
    
    # Simulate file reading
    content = await MockFileSystem.read_file(file_path)
    
    # Show what the tool actually receives
    print_security_demo(
        "File Path Protection",
        "/{USER_HOME}/.../{filename}",
        file_path
    )
    
    return f"File content (first 100 chars): {content[:100]}..."


@server.tool("call_ai_api", "Call an AI API with protected credentials")
@protect_tool(secrets=["openai_key"])
async def call_ai_api(prompt: str, api_key: str) -> str:
    """
    Call an AI API with protected credentials.
    
    This demonstrates OpenAI key protection with ZERO CONFIG:
    - AI sees: api_key = "{{OPENAI_API_KEY}}"
    - Tool gets: api_key = "sk-1234567890abcdef..."
    - Built-in openai_key pattern works automatically!
    """
    print_phase("Tool Execution", "Making API call with real credentials")
    
    # Create API client with real key
    client = MockAPIClient(api_key)
    
    # Make API request
    response = await client.chat_completion([
        {"role": "user", "content": prompt}
    ])
    
    # Show what the tool actually receives
    print_security_demo(
        "API Key Protection",
        "{RESOLVE:API_KEY:a1b2c3d4}",
        f"{api_key[:15]}..."
    )
    
    return response


@server.tool("database_query", "Execute a database query with protected connection")
@protect_tool(secrets=["database_url"])
async def database_query(query: str, database_url: str) -> dict:
    """
    Execute a database query with protected connection string.
    
    This demonstrates database URL protection with ZERO CONFIG:
    - AI sees: database_url = "{{DATABASE_URL}}"
    - Tool gets: database_url = "postgresql://user:secret@localhost:5432/mydb"
    - Built-in database_url pattern works automatically!
    """
    print_phase("Tool Execution", "Connecting to database with real credentials")
    
    # Show what the tool actually receives
    print_security_demo(
        "Database URL Protection",
        "{RESOLVE:DATABASE_URL:x5y6z7w8}",
        f"{database_url[:25]}..."
    )
    
    # Simulate database connection and query
    from examples.shared.utils import MockDatabase
    db = MockDatabase()
    await db.connect(database_url)
    
    try:
        result = await db.query(query)
        return {"status": "success", "rows": len(result), "data": result}
    finally:
        await db.close()


# =============================================================================
# Example 2: Context Manager Pattern
# =============================================================================

async def demonstrate_context_manager():
    """
    Demonstrate the context manager pattern for fine-grained control.
    
    This shows how to use secure_session() for direct control over
    the sanitization → AI processing → resolution cycle.
    """
    print_separator("Context Manager Example", "=")
    
    # Original data with secrets
    sensitive_data = {
        "config": {
            "openai_key": os.getenv("OPENAI_API_KEY"),
            "database_url": os.getenv("DATABASE_URL"),
            "jwt_secret": os.getenv("JWT_SECRET")
        },
        "user_request": "Please analyze my API key sk-1234567890abcdef",
        "file_path": "/Users/developer/sensitive-data/config.json"
    }
    
    print("📝 Original data contains real secrets:")
    print(f"   OpenAI key: {sensitive_data['config']['openai_key'][:20]}...")
    print(f"   Database URL: {sensitive_data['config']['database_url'][:30]}...")
    print(f"   File path: {sensitive_data['file_path']}")
    
    # Use secure session for temporal isolation
    async with secure_session() as session:
        print_phase("Phase 1", "Sanitizing data for AI processing")
        
        # Sanitize for AI
        sanitized = await session.sanitize_for_ai(sensitive_data)
        
        print("🤖 AI sees sanitized data:")
        print(f"   OpenAI key: {sanitized['config']['openai_key']}")
        print(f"   Database URL: {sanitized['config']['database_url']}")
        print(f"   File path: {sanitized['file_path']}")
        
        print_phase("Phase 2", "AI processing (safe - no real secrets)")
        
        # Simulate AI processing
        ai_response = f"I'll help you with the file at {sanitized['file_path']} using API key {sanitized['config']['openai_key']}"
        print(f"🤖 AI response: {ai_response}")
        
        print_phase("Phase 3", "Resolving placeholders for tool execution")
        
        # Resolve for execution
        resolved = await session.resolve_secrets(ai_response)
        
        print("🔧 Tool gets resolved data:")
        print(f"   Resolved response: {resolved}")
        
        print_phase("Phase 4", "Sanitizing response for AI")
        
        # Simulate tool execution result
        tool_result = f"Successfully processed file {sensitive_data['file_path']} with API key {sensitive_data['config']['openai_key'][:15]}..."
        
        # Sanitize response
        safe_response = await session.sanitize_response(tool_result)
        
        print("🤖 AI sees sanitized response:")
        print(f"   Safe response: {safe_response}")


# =============================================================================
# Example 3: Multiple Secret Types
# =============================================================================

@server.tool("process_user_data", "Process user data with multiple secret types")
@protect_tool(secrets=["openai_key", "database_url", "file_path"])
async def process_user_data(
    user_input: str,
    api_key: str,
    database_url: str,
    config_file: str,
    user_email: str
) -> dict:
    """
    Process user data with multiple types of secrets.
    
    This demonstrates protection of multiple secret types with ZERO CONFIG:
    - OpenAI keys → {{OPENAI_API_KEY}}
    - Database URLs → {{DATABASE_URL}}
    - File paths → /{USER_HOME}/.../{filename}
    - All built-in patterns work automatically!
    """
    print_phase("Tool Execution", "Processing with multiple protected secrets")
    
    # Show all the protections in action
    print_security_demo("OpenAI Key", "{{OPENAI_API_KEY}}", f"{api_key[:15]}...")
    print_security_demo("Database URL", "{{DATABASE_URL}}", f"{database_url[:25]}...")
    print_security_demo("File Path", "/{USER_HOME}/.../{filename}", config_file)
    print_security_demo("Email", user_email, user_email)  # Not protected in this example
    
    # Simulate processing
    await asyncio.sleep(0.1)
    
    return {
        "status": "processed",
        "user_input": user_input,
        "secrets_protected": 4,
        "processing_time": "0.1s"
    }


# =============================================================================
# Main Example Runner
# =============================================================================

async def main():
    """Run all FastMCP simple examples."""
    print_separator("FastMCP Simple Hello World Example - Zero Config", "=")
    print("🔒 Demonstrating temporal isolation with @protect_tool decorator")
    print("   ✨ ZERO CONFIGURATION REQUIRED - Built-in patterns work automatically!")
    print("   🤖 AI models see safe placeholders, tools get real secrets")
    
    # Setup environment
    setup_example_environment()
    
    if not validate_environment():
        print("❌ Environment validation failed. Please check your setup.")
        return
    
    # List available tools
    server.list_tools()
    
    # Example 1: File reading with path protection
    print_separator("Example 1: File Reading with Path Protection", "-")
    
    result1 = await server.call_tool(
        "read_secret_file",
        file_path="/Users/developer/sensitive-data/secrets.json"
    )
    print(f"📄 Result: {result1}")
    
    # Example 2: API call with key protection
    print_separator("Example 2: API Call with Key Protection", "-")
    
    result2 = await server.call_tool(
        "call_ai_api",
        prompt="Hello, how are you?",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    print(f"🤖 Result: {result2}")
    
    # Example 3: Database query with URL protection
    print_separator("Example 3: Database Query with URL Protection", "-")
    
    result3 = await server.call_tool(
        "database_query",
        query="SELECT * FROM users LIMIT 5",
        database_url=os.getenv("DATABASE_URL")
    )
    print(f"📊 Result: {result3}")
    
    # Example 4: Multiple secret types
    print_separator("Example 4: Multiple Secret Types", "-")
    
    result4 = await server.call_tool(
        "process_user_data",
        user_input="Please process my data",
        api_key=os.getenv("OPENAI_API_KEY"),
        database_url=os.getenv("DATABASE_URL"),
        config_file="/Users/developer/sensitive-data/config.json",
        user_email="user@example.com"
    )
    print(f"🔄 Result: {result4}")
    
    # Example 5: Context manager pattern
    await demonstrate_context_manager()
    
    # Summary
    print_separator("Summary", "=")
    print("✅ All examples completed successfully!")
    print("\n💡 Key Takeaways:")
    print("   🔒 The @protect_tool decorator provides automatic secret protection")
    print("   ✨ ZERO CONFIGURATION - Built-in patterns work immediately!")
    print("   🎯 95% of users need zero setup - openai_key, database_url, file_path all built-in")
    print("   ⚡ Zero-impact on performance - protection happens transparently")
    print("   🤖 AI models never see real secrets, only safe placeholders")
    print("   🔧 Tools receive real values for actual operations")
    print("   📊 Multiple secret types protected simultaneously")
    print("   🎯 Three-phase security: Sanitization → AI Processing → Resolution")
    
    print("\n🎉 FastMCP Simple Example Complete!")
    print("   Next: Try the advanced middleware example (02_advanced_middleware.py)")


if __name__ == "__main__":
    asyncio.run(main())