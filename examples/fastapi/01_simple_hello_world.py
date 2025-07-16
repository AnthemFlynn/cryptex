#!/usr/bin/env python3
"""
FastAPI Simple Hello World Example

This example demonstrates basic secret protection using the @cryptex decorator
with FastAPI endpoints. It shows how Cryptex provides temporal isolation for
web applications - AI processing sees safe placeholders while endpoints get
real secret values.

What you'll learn:
- How to use the @cryptex decorator for individual endpoint protection
- How temporal isolation works for web requests and responses
- What gets logged vs what endpoints actually execute with
- Basic authentication and API key protection
- Request/response sanitization patterns
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to the Python path so we can import cryptex
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import Cryptex components
from cryptex import cryptex
from cryptex.core import secure_session

# Import example utilities
from examples.shared.utils import (
    setup_example_environment,
    print_separator,
    print_phase,
    print_security_demo,
    MockAPIClient,
    MockFileSystem,
    MockDatabase,
    validate_environment
)


# =============================================================================
# Mock FastAPI Implementation
# =============================================================================

class MockRequest:
    """Mock FastAPI request object."""
    
    def __init__(self, method: str, url: str, headers: dict = None, body: Any = None):
        self.method = method
        self.url = url
        self.headers = headers or {}
        self.body = body
        self.json_body = body if isinstance(body, dict) else None


class MockResponse:
    """Mock FastAPI response object."""
    
    def __init__(self, content: Any, status_code: int = 200, headers: dict = None):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}


class MockFastAPI:
    """
    Mock FastAPI application for demonstration purposes.
    
    In a real application, you would use:
    from fastapi import FastAPI
    """
    
    def __init__(self, title: str = "Cryptex FastAPI Example"):
        self.title = title
        self.routes = {}
        self.middleware = []
        self.request_count = 0
        print(f"🚀 Mock FastAPI application '{title}' initialized")
    
    def add_middleware(self, middleware_class, **kwargs):
        """Add middleware to the application."""
        self.middleware.append((middleware_class, kwargs))
        print(f"🔧 Middleware added: {middleware_class.__name__}")
    
    def get(self, path: str, **kwargs):
        """Decorator for GET endpoints."""
        def decorator(func):
            self.routes[f"GET {path}"] = {
                'function': func,
                'method': 'GET',
                'path': path,
                'kwargs': kwargs
            }
            print(f"📡 GET endpoint registered: {path}")
            return func
        return decorator
    
    def post(self, path: str, **kwargs):
        """Decorator for POST endpoints."""
        def decorator(func):
            self.routes[f"POST {path}"] = {
                'function': func,
                'method': 'POST',
                'path': path,
                'kwargs': kwargs
            }
            print(f"📡 POST endpoint registered: {path}")
            return func
        return decorator
    
    def put(self, path: str, **kwargs):
        """Decorator for PUT endpoints."""
        def decorator(func):
            self.routes[f"PUT {path}"] = {
                'function': func,
                'method': 'PUT',
                'path': path,
                'kwargs': kwargs
            }
            print(f"📡 PUT endpoint registered: {path}")
            return func
        return decorator
    
    async def call_endpoint(self, method: str, path: str, **kwargs):
        """Call an endpoint (simulating HTTP request)."""
        route_key = f"{method.upper()} {path}"
        if route_key not in self.routes:
            return MockResponse({"error": "Not found"}, 404)
        
        self.request_count += 1
        print(f"📞 Request #{self.request_count}: {method} {path}")
        
        try:
            route_info = self.routes[route_key]
            result = await route_info['function'](**kwargs)
            
            if isinstance(result, dict):
                return MockResponse(result, 200)
            else:
                return MockResponse({"result": result}, 200)
                
        except Exception as e:
            print(f"❌ Request #{self.request_count}: Failed - {str(e)}")
            return MockResponse({"error": str(e)}, 500)
    
    def list_routes(self):
        """List all registered routes."""
        print(f"\n📋 Routes registered on '{self.title}':")
        for route_key, route_info in self.routes.items():
            print(f"   - {route_key}")


# =============================================================================
# Example 1: Basic Authentication
# =============================================================================

# Create FastAPI app
app = MockFastAPI("Hello World API")

@app.post("/auth/login")
@cryptex(secrets=["jwt_secret"])
async def login(username: str, password: str, jwt_secret: str) -> Dict[str, Any]:
    """
    Login endpoint with JWT token generation.
    
    This demonstrates JWT secret protection:
    - Logs show: jwt_secret = "{RESOLVE:JWT_SECRET:hash}"
    - Endpoint gets: jwt_secret = "my-super-secret-jwt-key-123"
    """
    print_phase("Authentication", f"Processing login for user: {username}")
    
    # Show what the endpoint actually receives
    print_security_demo(
        "JWT Secret Protection",
        "{RESOLVE:JWT_SECRET:hash}",
        f"{jwt_secret[:20]}..."
    )
    
    # Simulate authentication
    if username == "admin" and password == "password":
        # Generate JWT token (mock)
        token = f"jwt.header.{jwt_secret[:8]}.signature"
        
        return {
            "status": "success",
            "message": "Login successful",
            "token": token,
            "user": {
                "username": username,
                "role": "admin"
            }
        }
    else:
        raise ValueError("Invalid credentials")


# =============================================================================
# Example 2: API Key Protection
# =============================================================================

@app.get("/api/chat")
@cryptex(secrets=["api_key"])
async def chat_completion(
    message: str,
    api_key: str,
    model: str = "gpt-4"
) -> Dict[str, Any]:
    """
    Chat completion endpoint with API key protection.
    
    This demonstrates API key protection:
    - Logs show: api_key = "{RESOLVE:API_KEY:hash}"
    - Endpoint gets: api_key = "sk-1234567890abcdef..."
    """
    print_phase("Chat Completion", f"Processing message with model: {model}")
    
    # Show what the endpoint actually receives
    print_security_demo(
        "API Key Protection",
        "{RESOLVE:API_KEY:hash}",
        f"{api_key[:15]}..."
    )
    
    # Call AI API with protected key
    client = MockAPIClient(api_key)
    response = await client.chat_completion([
        {"role": "user", "content": message}
    ])
    
    return {
        "response": response,
        "model": model,
        "usage": {
            "prompt_tokens": len(message.split()),
            "completion_tokens": len(response.split()),
            "total_tokens": len(message.split()) + len(response.split())
        }
    }


# =============================================================================
# Example 3: Database Operations
# =============================================================================

@app.get("/api/users")
@cryptex(secrets=["database_url"])
async def get_users(database_url: str, limit: int = 10) -> Dict[str, Any]:
    """
    Get users from database with protected connection string.
    
    This demonstrates database URL protection:
    - Logs show: database_url = "{RESOLVE:DATABASE_URL:hash}"
    - Endpoint gets: database_url = "postgresql://user:secret@localhost:5432/mydb"
    """
    print_phase("Database Query", f"Fetching {limit} users")
    
    # Show what the endpoint actually receives
    print_security_demo(
        "Database URL Protection",
        "{RESOLVE:DATABASE_URL:hash}",
        f"{database_url[:30]}..."
    )
    
    # Connect to database with protected URL
    db = MockDatabase()
    await db.connect(database_url)
    
    try:
        users = await db.query(f"SELECT * FROM users LIMIT {limit}")
        return {
            "users": users,
            "count": len(users),
            "limit": limit
        }
    finally:
        await db.close()


# =============================================================================
# Example 4: File Operations
# =============================================================================

@app.post("/api/files/process")
@cryptex(secrets=["file_path", "api_key"])
async def process_file(
    file_path: str,
    api_key: str,
    operation: str = "analyze"
) -> Dict[str, Any]:
    """
    Process files with path and API key protection.
    
    This demonstrates multiple secret types:
    - file_path: "/{USER_HOME}/.../{filename}"
    - api_key: "{RESOLVE:API_KEY:hash}"
    """
    print_phase("File Processing", f"Operation: {operation}")
    
    # Show what the endpoint actually receives
    print_security_demo(
        "File Path Protection",
        "/{USER_HOME}/.../{filename}",
        file_path
    )
    print_security_demo(
        "API Key Protection",
        "{RESOLVE:API_KEY:hash}",
        f"{api_key[:15]}..."
    )
    
    # Read file with protected path
    content = await MockFileSystem.read_file(file_path)
    
    # Process with AI API
    if operation == "analyze":
        client = MockAPIClient(api_key)
        analysis = await client.chat_completion([
            {"role": "user", "content": f"Analyze this file: {content[:200]}..."}
        ])
        
        return {
            "file_path": file_path,
            "operation": operation,
            "content_length": len(content),
            "analysis": analysis
        }
    else:
        raise ValueError(f"Unknown operation: {operation}")


# =============================================================================
# Example 5: Multiple Secret Types
# =============================================================================

@app.put("/api/admin/settings")
@cryptex(secrets=["database_url", "redis_url", "jwt_secret", "api_key"])
async def update_settings(
    database_url: str,
    redis_url: str,
    jwt_secret: str,
    api_key: str,
    settings: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update application settings with multiple protected secrets.
    
    This demonstrates protection of multiple secret types:
    - Database URL, Redis URL, JWT secret, API key all protected
    - Complex configuration updates
    - Validation and error handling
    """
    print_phase("Settings Update", "Updating application configuration")
    
    # Show all secret protections
    print_security_demo("Database URL", "{RESOLVE:DATABASE_URL:hash}", f"{database_url[:25]}...")
    print_security_demo("Redis URL", "{RESOLVE:REDIS_URL:hash}", f"{redis_url[:20]}...")
    print_security_demo("JWT Secret", "{RESOLVE:JWT_SECRET:hash}", f"{jwt_secret[:15]}...")
    print_security_demo("API Key", "{RESOLVE:API_KEY:hash}", f"{api_key[:15]}...")
    
    # Validate settings
    if not isinstance(settings, dict):
        raise ValueError("Settings must be a dictionary")
    
    # Update configurations (mock)
    updated_settings = {
        "database_config": {"url": database_url, "status": "updated"},
        "redis_config": {"url": redis_url, "status": "updated"},
        "auth_config": {"jwt_secret": jwt_secret[:8] + "...", "status": "updated"},
        "api_config": {"key": api_key[:10] + "...", "status": "updated"},
        "custom_settings": settings
    }
    
    return {
        "status": "success",
        "message": "Settings updated successfully",
        "updated_settings": updated_settings,
        "timestamp": time.time()
    }


# =============================================================================
# Example 6: Context Manager Pattern
# =============================================================================

@app.post("/api/secure/process")
async def secure_process(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Demonstrate the context manager pattern for fine-grained control.
    
    This shows how to use secure_session() for manual control over
    the sanitization → AI processing → resolution cycle.
    """
    print_phase("Secure Processing", "Using context manager pattern")
    
    # Extract sensitive data from request
    sensitive_data = {
        "api_key": request_data.get("api_key"),
        "database_url": request_data.get("database_url"),
        "file_path": request_data.get("file_path"),
        "user_input": request_data.get("message", "")
    }
    
    print("📝 Original request contains sensitive data:")
    print(f"   API key: {sensitive_data['api_key'][:15]}...")
    print(f"   Database URL: {sensitive_data['database_url'][:25]}...")
    print(f"   File path: {sensitive_data['file_path']}")
    
    # Use secure session for temporal isolation
    async with secure_session() as session:
        print_phase("Phase 1", "Sanitizing request data")
        
        # Sanitize for AI processing
        sanitized = await session.sanitize_for_ai(sensitive_data)
        
        print("🤖 AI processing sees sanitized data:")
        print(f"   API key: {sanitized['api_key']}")
        print(f"   Database URL: {sanitized['database_url']}")
        print(f"   File path: {sanitized['file_path']}")
        
        print_phase("Phase 2", "AI processing (safe)")
        
        # Simulate AI processing
        ai_response = f"Processing request for file {sanitized['file_path']} with API key {sanitized['api_key']}"
        
        print_phase("Phase 3", "Resolving for execution")
        
        # Resolve for execution
        resolved = await session.resolve_secrets(ai_response)
        
        print("🔧 Execution gets resolved data:")
        print(f"   Resolved: {resolved}")
        
        print_phase("Phase 4", "Sanitizing response")
        
        # Create response with actual execution results
        execution_result = {
            "processed_file": sensitive_data['file_path'],
            "api_used": sensitive_data['api_key'][:15] + "...",
            "database_connected": True,
            "status": "completed"
        }
        
        # Sanitize response
        safe_response = await session.sanitize_response(execution_result)
        
        return {
            "result": safe_response,
            "processing_phases": 4,
            "security_level": "high"
        }


# =============================================================================
# Example 7: Health Check (No Protection Needed)
# =============================================================================

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint - no secret protection needed.
    
    This demonstrates that not all endpoints need protection.
    Public endpoints can work normally without any overhead.
    """
    print_phase("Health Check", "Checking application status")
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "features": [
            "secret_protection",
            "temporal_isolation",
            "fastapi_integration"
        ]
    }


# =============================================================================
# Main Example Runner
# =============================================================================

async def main():
    """Run all FastAPI simple examples."""
    print_separator("FastAPI Simple Hello World Example", "=")
    print("🌐 Demonstrating web application secret protection")
    print("   Request/response sanitization with temporal isolation")
    
    # Setup environment
    setup_example_environment()
    
    if not validate_environment():
        print("❌ Environment validation failed. Please check your setup.")
        return
    
    # List available routes
    app.list_routes()
    
    # Example 1: Authentication
    print_separator("Example 1: Authentication with JWT Protection", "-")
    
    try:
        response1 = await app.call_endpoint(
            "POST", "/auth/login",
            username="admin",
            password="password",
            jwt_secret=os.getenv("JWT_SECRET")
        )
        print(f"🔐 Login response: {json.dumps(response1.content, indent=2)}")
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
    
    # Example 2: Chat completion
    print_separator("Example 2: Chat Completion with API Key Protection", "-")
    
    try:
        response2 = await app.call_endpoint(
            "GET", "/api/chat",
            message="Hello, how are you?",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4"
        )
        print(f"🤖 Chat response: {json.dumps(response2.content, indent=2)}")
    except Exception as e:
        print(f"❌ Chat completion failed: {str(e)}")
    
    # Example 3: Database operations
    print_separator("Example 3: Database Query with URL Protection", "-")
    
    try:
        response3 = await app.call_endpoint(
            "GET", "/api/users",
            database_url=os.getenv("DATABASE_URL"),
            limit=5
        )
        print(f"📊 Users response: {json.dumps(response3.content, indent=2)}")
    except Exception as e:
        print(f"❌ Database query failed: {str(e)}")
    
    # Example 4: File processing
    print_separator("Example 4: File Processing with Multiple Secrets", "-")
    
    try:
        response4 = await app.call_endpoint(
            "POST", "/api/files/process",
            file_path="/app/data/important-file.txt",
            api_key=os.getenv("OPENAI_API_KEY"),
            operation="analyze"
        )
        print(f"📁 File processing response: {json.dumps(response4.content, indent=2)}")
    except Exception as e:
        print(f"❌ File processing failed: {str(e)}")
    
    # Example 5: Settings update
    print_separator("Example 5: Settings Update with Multiple Secrets", "-")
    
    try:
        response5 = await app.call_endpoint(
            "PUT", "/api/admin/settings",
            database_url=os.getenv("DATABASE_URL"),
            redis_url=os.getenv("REDIS_URL"),
            jwt_secret=os.getenv("JWT_SECRET"),
            api_key=os.getenv("OPENAI_API_KEY"),
            settings={"feature_x": True, "max_users": 1000}
        )
        print(f"⚙️ Settings response: {json.dumps(response5.content, indent=2)}")
    except Exception as e:
        print(f"❌ Settings update failed: {str(e)}")
    
    # Example 6: Context manager pattern
    print_separator("Example 6: Context Manager Pattern", "-")
    
    try:
        response6 = await app.call_endpoint(
            "POST", "/api/secure/process",
            request_data={
                "api_key": os.getenv("OPENAI_API_KEY"),
                "database_url": os.getenv("DATABASE_URL"),
                "file_path": "/app/secure/data.json",
                "message": "Process this securely"
            }
        )
        print(f"🔒 Secure processing response: {json.dumps(response6.content, indent=2)}")
    except Exception as e:
        print(f"❌ Secure processing failed: {str(e)}")
    
    # Example 7: Health check
    print_separator("Example 7: Health Check (No Protection)", "-")
    
    try:
        response7 = await app.call_endpoint("GET", "/health")
        print(f"💚 Health response: {json.dumps(response7.content, indent=2)}")
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
    
    # Summary
    print_separator("Summary", "=")
    print("✅ All examples completed successfully!")
    print(f"📊 Total requests processed: {app.request_count}")
    
    print("\n💡 Key Takeaways:")
    print("   🔒 The @cryptex decorator provides automatic secret protection")
    print("   🌐 Web requests/responses are automatically sanitized")
    print("   🤖 AI processing and logging see safe placeholders")
    print("   🔧 Endpoints receive real values for actual operations")
    print("   📊 Multiple secret types protected simultaneously")
    print("   🎯 Three-phase security: Sanitization → AI Processing → Resolution")
    print("   🔄 Context manager pattern for fine-grained control")
    print("   💚 Public endpoints work normally without overhead")
    
    print("\n🎉 FastAPI Simple Example Complete!")
    print("   Next: Try the advanced middleware example (02_advanced_middleware.py)")


if __name__ == "__main__":
    asyncio.run(main())