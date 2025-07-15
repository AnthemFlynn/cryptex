#!/usr/bin/env python3
"""
Comprehensive examples for Codename middleware integration.

This example demonstrates temporal isolation middleware for FastMCP servers and FastAPI applications.
Codename ensures AI/LLMs see safe placeholders while tools/endpoints get real secret values.
"""

import asyncio
import os
from typing import Dict, Any, List

# Import the main Codename components
import codename
from codename import (
    # Core components
    TemporalIsolationEngine,
    CodenameConfig,
    
    # Decorators
    protect_tool,
    protect_endpoint,
    protect_file_tool,
    protect_api_tool,
    
    # Universal setup
    setup_protection
)

# Set up example environment
def setup_example_environment():
    """Set up example environment variables."""
    os.environ['OPENAI_API_KEY'] = 'sk-example1234567890abcdef12345678901234567890abcdef'
    os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-example1234567890abcdef12345678901234567890abcdef12345678901234567890abcdef1234567890abcdef'
    os.environ['DATABASE_URL'] = 'postgresql://user:secret@localhost:5432/mydb'
    os.environ['PROJECT_DIR'] = '/Users/john/secret-project/myapp'


#
# FastMCP Examples
#

async def fastmcp_middleware_example():
    """Example: FastMCP server with middleware protection."""
    print("🔧 FastMCP Middleware Example")
    print("=" * 40)
    
    try:
        # This would normally import from fastmcp
        # from fastmcp import FastMCPServer
        
        # For demo purposes, we'll create a mock server
        class MockFastMCPServer:
            def __init__(self):
                self.tools = {}
                self.middleware = []
            
            def add_middleware(self, middleware):
                self.middleware.append(middleware)
            
            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func
                return decorator
        
        server = MockFastMCPServer()
        
        # One-line setup for complete protection
        try:
            protection = await codename.setup_fastmcp_protection(
                server, 
                config_path="config/codename.toml"
            )
            print("✅ FastMCP protection installed")
        except ImportError:
            print("⚠️  FastMCP not available (demo mode)")
            return
        
        # Tools are now automatically protected
        @server.tool()
        @protect_tool(secrets=["file_paths", "api_keys"])
        async def read_and_analyze_file(file_path: str, api_key: str) -> str:
            """
            Tool that reads a file and analyzes it with AI API.
            
            AI/LLM sees:
            - file_path: "/{USER_HOME}/documents/file.txt"
            - api_key: "{{OPENAI_API_KEY}}"
            
            Tool executes with:
            - file_path: "/Users/john/secret-project/documents/file.txt"
            - api_key: "sk-real-api-key..."
            """
            print(f"Tool reading file: {file_path}")
            print(f"Tool using API key: {api_key[:10]}...")
            
            # Simulate file reading and API call
            content = f"Content from {file_path}"
            result = f"AI analysis using {api_key[:10]}...: {content}"
            
            return result
        
        # Simulate tool execution
        result = await read_and_analyze_file(
            "/Users/john/secret-project/documents/test.txt",
            os.getenv('OPENAI_API_KEY')
        )
        print(f"Tool result: {result}")
        
    except Exception as e:
        print(f"FastMCP example error: {e}")


async def fastmcp_decorator_example():
    """Example: Individual FastMCP tool protection with decorators."""
    print("\n🎯 FastMCP Decorator Example")
    print("=" * 40)
    
    # File operation tool
    @protect_file_tool(config_path="config/codename.toml")
    async def file_search_tool(directory: str, pattern: str) -> List[str]:
        """
        Search for files in a directory.
        
        AI sees: file_search_tool("/{USER_HOME}/projects", "*.py")
        Tool executes: with real directory path
        """
        print(f"Searching in: {directory}")
        print(f"Pattern: {pattern}")
        
        # Simulate file search
        files = [
            f"{directory}/main.py",
            f"{directory}/utils.py",
            f"{directory}/config.py"
        ]
        return files
    
    # API calling tool
    @protect_api_tool(config_path="config/codename.toml")
    async def ai_completion_tool(prompt: str, api_key: str) -> str:
        """
        Call AI API for text completion.
        
        AI sees: ai_completion_tool("Hello", "{{OPENAI_API_KEY}}")
        Tool executes: with real API key
        """
        print(f"AI prompt: {prompt}")
        print(f"Using API key: {api_key[:15]}...")
        
        # Simulate AI API call
        return f"AI response to '{prompt}' using key {api_key[:10]}..."
    
    # Execute examples
    files = await file_search_tool("/Users/john/secret-project", "*.py")
    print(f"Found files: {files}")
    
    completion = await ai_completion_tool("Hello world", os.getenv('OPENAI_API_KEY'))
    print(f"AI completion: {completion}")


#
# FastAPI Examples
#

async def fastapi_middleware_example():
    """Example: FastAPI application with middleware protection."""
    print("\n🌐 FastAPI Middleware Example")
    print("=" * 40)
    
    try:
        # This would normally import from fastapi
        # from fastapi import FastAPI, Header
        
        # For demo purposes, we'll create a mock app
        class MockFastAPI:
            def __init__(self):
                self.middleware = []
                self.routes = {}
            
            def add_middleware(self, middleware_class, **kwargs):
                self.middleware.append((middleware_class, kwargs))
            
            def post(self, path):
                def decorator(func):
                    self.routes[f"POST {path}"] = func
                    return func
                return decorator
        
        app = MockFastAPI()
        
        # One-line setup for complete protection
        try:
            protection = codename.setup_fastapi_protection(
                app,
                config_path="config/codename.toml"
            )
            print("✅ FastAPI protection installed")
        except ImportError:
            print("⚠️  FastAPI not available (demo mode)")
            return
        
        # Endpoints are now automatically protected
        @app.post("/api/process")
        @protect_endpoint(secrets=["api_key", "database_url"])
        async def process_data(data: dict, api_key: str, db_url: str):
            """
            Endpoint that processes data with external API and database.
            
            Request sees:
            - api_key: "{{OPENAI_API_KEY}}"
            - db_url: "{{DATABASE_URL}}"
            
            Endpoint executes with:
            - api_key: "sk-real-api-key..."
            - db_url: "postgresql://user:secret@localhost/db"
            """
            print(f"Processing data: {data}")
            print(f"Using API key: {api_key[:15]}...")
            print(f"Using DB: {db_url}")
            
            # Simulate processing
            result = {
                "status": "processed",
                "data": data,
                "api_used": api_key[:10] + "...",
                "db_connected": True
            }
            
            return result
        
        # Simulate endpoint execution
        result = await process_data(
            {"text": "Hello world"},
            os.getenv('OPENAI_API_KEY'),
            os.getenv('DATABASE_URL')
        )
        print(f"Endpoint result: {result}")
        
    except Exception as e:
        print(f"FastAPI example error: {e}")


async def fastapi_decorator_example():
    """Example: Individual FastAPI endpoint protection with decorators."""
    print("\n🛡️  FastAPI Decorator Example")
    print("=" * 40)
    
    # Authentication endpoint
    @protect_endpoint(secrets=["jwt_secret", "api_key"])
    async def login_endpoint(username: str, password: str, jwt_secret: str):
        """
        Login endpoint with JWT token generation.
        
        Request logs see: jwt_secret as "{{JWT_SECRET}}"
        Endpoint executes: with real JWT secret for token signing
        """
        print(f"Login attempt: {username}")
        print(f"JWT secret: {jwt_secret[:10]}...")
        
        # Simulate authentication
        if username and password:
            token = f"jwt.token.signed.with.{jwt_secret[:8]}"
            return {"token": token, "user": username}
        else:
            raise ValueError("Invalid credentials")
    
    # Database endpoint
    @protect_endpoint(secrets=["database_url"])
    async def get_user_data(user_id: int, db_url: str):
        """
        Fetch user data from database.
        
        Request logs see: db_url as "{{DATABASE_URL}}"
        Endpoint executes: with real database connection string
        """
        print(f"Fetching user {user_id}")
        print(f"DB URL: {db_url}")
        
        # Simulate database query
        return {
            "user_id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com"
        }
    
    # Execute examples
    login_result = await login_endpoint("john", "password", "jwt-secret-key-123")
    print(f"Login result: {login_result}")
    
    user_data = await get_user_data(123, os.getenv('DATABASE_URL'))
    print(f"User data: {user_data}")


#
# Core Engine Examples
#

async def core_engine_example():
    """Example: Direct usage of the core temporal isolation engine."""
    print("\n⚙️  Core Engine Example")
    print("=" * 40)
    
    # Create engine with default patterns
    engine = TemporalIsolationEngine()
    
    # Example data containing secrets
    sensitive_data = {
        "config": {
            "api_key": "sk-1234567890abcdef1234567890abcdef12345678",
            "database_url": "postgresql://user:secret@localhost:5432/mydb"
        },
        "file_path": "/Users/john/secret-project/config.json",
        "user_input": "Please read my API key sk-1234567890abcdef1234567890abcdef12345678"
    }
    
    print("Original data:")
    print(f"  API key: {sensitive_data['config']['api_key']}")
    print(f"  DB URL: {sensitive_data['config']['database_url']}")
    print(f"  File path: {sensitive_data['file_path']}")
    
    # Phase 1: Sanitize for AI
    sanitized = await engine.sanitize_for_ai(sensitive_data)
    print(f"\nSanitized for AI (context: {sanitized.context_id[:8]}...):")
    print(f"  API key: {sanitized.data['config']['api_key']}")
    print(f"  DB URL: {sanitized.data['config']['database_url']}")
    print(f"  File path: {sanitized.data['file_path']}")
    
    # Phase 2: AI processing (AI only sees sanitized data)
    ai_response = f"I processed your request using the API key {sanitized.data['config']['api_key']}"
    print(f"\nAI response: {ai_response}")
    
    # Phase 3: Resolve for execution
    resolved = await engine.resolve_for_execution(ai_response, sanitized.context_id)
    print(f"\nResolved for execution:")
    print(f"  Response: {resolved.data}")
    print(f"  Resolved count: {resolved.resolved_count}")
    
    # Demonstrate response sanitization
    execution_result = f"Successfully connected to {sensitive_data['config']['database_url']}"
    sanitized_response = await engine.sanitize_response(execution_result, sanitized.context_id)
    print(f"\nExecution result sanitized for AI: {sanitized_response}")


async def configuration_example():
    """Example: Configuration system usage."""
    print("\n📋 Configuration Example")
    print("=" * 40)
    
    try:
        # Load configuration from TOML file
        config = await CodenameConfig.from_toml("config/codename.toml")
        print("✅ Configuration loaded from TOML")
        
        print(f"Secret patterns: {len(config.secret_patterns)}")
        for pattern in config.secret_patterns[:3]:  # Show first 3
            print(f"  - {pattern.name}: {pattern.description}")
        
        print(f"Security mode: {config.security_policy.enforcement_mode}")
        print(f"Performance cache size: {config.performance.cache_size}")
        print(f"Auto-protect endpoints: {config.middleware.auto_protect_endpoints}")
        
    except FileNotFoundError:
        print("⚠️  Configuration file not found, using defaults")
        config = CodenameConfig()
        print(f"Default patterns: {len(config.secret_patterns)}")


async def main():
    """Run all examples to demonstrate Codename's capabilities."""
    print("🔒 Codename Middleware Examples")
    print("=" * 50)
    print("Demonstrating temporal isolation for AI/LLM applications")
    print()
    
    # Set up environment
    setup_example_environment()
    
    # Run examples
    await fastmcp_middleware_example()
    await fastmcp_decorator_example()
    await fastapi_middleware_example()
    await fastapi_decorator_example()
    await core_engine_example()
    await configuration_example()
    
    print("\n✅ All examples completed!")
    print("\n💡 Key Takeaways:")
    print("   🔧 Middleware approach: Zero-code protection for entire apps")
    print("   🎯 Decorator approach: Fine-grained control per function")
    print("   ⚙️  Core engine: Direct control for custom integrations")
    print("   📋 Configuration: Flexible TOML-based setup")
    print("\n🎯 Result: AI/LLMs see safe placeholders, tools get real values!")


if __name__ == "__main__":
    asyncio.run(main())