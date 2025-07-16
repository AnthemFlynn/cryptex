"""
Shared utilities for Cryptex examples.

This module provides common functions, mock implementations, and utilities
used across the FastMCP and FastAPI examples.
"""

import asyncio
import json
import os
import random
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager


# Mock data for examples
MOCK_USERS = [
    {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "role": "admin"},
    {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "role": "user"},
    {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "role": "user"},
]

MOCK_FILES = [
    {"name": "config.json", "path": "/app/config/config.json", "size": 1024},
    {"name": "secrets.env", "path": "/app/.env", "size": 512},
    {"name": "database.sql", "path": "/app/database.sql", "size": 8192},
    {"name": "main.py", "path": "/app/main.py", "size": 2048},
]

MOCK_API_RESPONSES = {
    "openai": {
        "model": "gpt-4",
        "choices": [{"message": {"content": "This is a mock AI response from OpenAI API"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
    },
    "anthropic": {
        "model": "claude-3-sonnet",
        "content": [{"text": "This is a mock AI response from Anthropic API"}],
        "usage": {"input_tokens": 10, "output_tokens": 15}
    }
}


@dataclass
class MockDatabase:
    """Mock database for demonstration purposes."""
    
    def __init__(self):
        self.connected = False
        self.connection_string = None
        
    async def connect(self, connection_string: str):
        """Simulate database connection."""
        self.connection_string = connection_string
        await asyncio.sleep(0.1)  # Simulate connection time
        self.connected = True
        print(f"📊 Connected to database: {connection_string[:20]}...")
        
    async def query(self, sql: str) -> List[Dict[str, Any]]:
        """Simulate database query."""
        if not self.connected:
            raise ValueError("Database not connected")
            
        await asyncio.sleep(0.05)  # Simulate query time
        
        if "users" in sql.lower():
            return MOCK_USERS
        elif "files" in sql.lower():
            return MOCK_FILES
        else:
            return [{"result": "Mock query result", "rows_affected": 1}]
            
    async def close(self):
        """Simulate closing database connection."""
        self.connected = False
        print("📊 Database connection closed")


class MockFileSystem:
    """Mock file system for demonstration purposes."""
    
    @staticmethod
    async def read_file(file_path: str) -> str:
        """Simulate reading a file."""
        await asyncio.sleep(0.02)  # Simulate file I/O
        
        filename = os.path.basename(file_path)
        if filename == "config.json":
            return json.dumps({
                "app_name": "Cryptex Example",
                "debug": True,
                "features": ["temporal_isolation", "secret_protection"]
            }, indent=2)
        elif filename == "secrets.env":
            return "# Environment variables\nAPP_SECRET=mock-secret-value\nDB_PASSWORD=mock-password"
        elif filename.endswith(".py"):
            return f"# {filename}\n\ndef main():\n    print('Hello from {filename}')\n\nif __name__ == '__main__':\n    main()"
        else:
            return f"Mock content for {filename}\nFile path: {file_path}\nTimestamp: {time.time()}"
    
    @staticmethod
    async def write_file(file_path: str, content: str) -> bool:
        """Simulate writing a file."""
        await asyncio.sleep(0.03)  # Simulate file I/O
        print(f"📁 Writing {len(content)} bytes to {file_path}")
        return True
    
    @staticmethod
    async def list_files(directory: str, pattern: str = "*") -> List[str]:
        """Simulate listing files in a directory."""
        await asyncio.sleep(0.01)  # Simulate directory listing
        
        # Return mock files based on pattern
        if pattern == "*.py":
            return [f"{directory}/main.py", f"{directory}/utils.py", f"{directory}/config.py"]
        elif pattern == "*.json":
            return [f"{directory}/config.json", f"{directory}/package.json"]
        elif pattern == "*.env":
            return [f"{directory}/.env", f"{directory}/.env.example"]
        else:
            return [f"{directory}/main.py", f"{directory}/config.json", f"{directory}/.env"]


class MockAPIClient:
    """Mock API client for demonstration purposes."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.example.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.request_count = 0
        
    async def make_request(self, endpoint: str, data: Any = None) -> Dict[str, Any]:
        """Simulate API request."""
        await asyncio.sleep(0.1)  # Simulate network latency
        self.request_count += 1
        
        print(f"🌐 API Request #{self.request_count} to {endpoint}")
        print(f"🔑 Using API key: {self.api_key[:15]}...")
        
        # Return mock response based on endpoint
        if "openai" in endpoint or "gpt" in endpoint:
            return MOCK_API_RESPONSES["openai"]
        elif "anthropic" in endpoint or "claude" in endpoint:
            return MOCK_API_RESPONSES["anthropic"]
        else:
            return {
                "success": True,
                "data": data,
                "timestamp": time.time(),
                "request_id": f"req_{random.randint(1000, 9999)}"
            }
    
    async def chat_completion(self, messages: List[Dict[str, str]], model: str = "gpt-4") -> str:
        """Simulate chat completion."""
        response = await self.make_request(f"/chat/completions", {
            "model": model,
            "messages": messages
        })
        
        if "choices" in response:
            return response["choices"][0]["message"]["content"]
        elif "content" in response:
            return response["content"][0]["text"]
        else:
            return "Mock AI response generated successfully"


def setup_example_environment():
    """Set up environment variables for examples."""
    example_vars = {
        'OPENAI_API_KEY': 'sk-example1234567890abcdef1234567890abcdef12345678',
        'ANTHROPIC_API_KEY': 'sk-ant-example1234567890abcdef1234567890abcdef12345678901234567890abcdef1234567890abcdef',
        'DATABASE_URL': 'postgresql://user:secret@localhost:5432/cryptex_examples',
        'REDIS_URL': 'redis://localhost:6379/0',
        'JWT_SECRET': 'my-super-secret-jwt-key-that-should-be-protected',
        'AWS_ACCESS_KEY_ID': 'AKIAIOSFODNN7EXAMPLE',
        'AWS_SECRET_ACCESS_KEY': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        'GOOGLE_API_KEY': 'AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI',
        'CRYPTEX_DEBUG': 'true',
        'PROJECT_HOME': '/Users/developer/projects/cryptex-examples',
        'SENSITIVE_DATA_DIR': '/Users/developer/sensitive-data',
    }
    
    for key, value in example_vars.items():
        if key not in os.environ:
            os.environ[key] = value
    
    print("🔧 Example environment variables set up")


def print_separator(title: str, char: str = "=", width: int = 60):
    """Print a formatted separator with title."""
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}")


def print_phase(phase: str, description: str):
    """Print a formatted phase description."""
    print(f"\n🔄 Phase: {phase}")
    print(f"   {description}")
    print("-" * 50)


def print_security_demo(label: str, ai_sees: Any, tool_gets: Any):
    """Print a security demonstration showing what AI sees vs what tool gets."""
    print(f"\n🔒 {label}")
    print(f"   AI sees:   {ai_sees}")
    print(f"   Tool gets: {tool_gets}")


def print_metrics(metrics: Dict[str, Any]):
    """Print formatted metrics information."""
    print("\n📊 Performance Metrics:")
    for key, value in metrics.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for sub_key, sub_value in value.items():
                print(f"     {sub_key}: {sub_value}")
        else:
            print(f"   {key}: {value}")


@asynccontextmanager
async def mock_external_service(service_name: str, delay: float = 0.1):
    """Context manager for mocking external services."""
    print(f"🔌 Connecting to {service_name}...")
    await asyncio.sleep(delay)
    print(f"✅ Connected to {service_name}")
    
    try:
        yield f"mock_{service_name}_client"
    finally:
        print(f"🔌 Disconnecting from {service_name}...")
        await asyncio.sleep(delay / 2)
        print(f"✅ Disconnected from {service_name}")


def validate_environment():
    """Validate that required environment variables are set."""
    required_vars = [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY', 
        'DATABASE_URL',
        'JWT_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Run setup_example_environment() to set default values")
        return False
    
    print("✅ All required environment variables are set")
    return True


def get_mock_secret(secret_type: str) -> str:
    """Get a mock secret value for demonstration."""
    secrets = {
        "api_key": "sk-1234567890abcdef1234567890abcdef12345678",
        "database_url": "postgresql://user:secret@localhost:5432/mydb",
        "jwt_secret": "my-super-secret-jwt-key-123",
        "aws_access_key": "AKIAIOSFODNN7EXAMPLE",
        "aws_secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "file_path": "/Users/developer/sensitive-data/secrets.json",
        "email": "user@example.com",
        "phone": "555-123-4567",
        "credit_card": "4111111111111111",
        "ssn": "123-45-6789"
    }
    
    return secrets.get(secret_type, f"mock_{secret_type}_value")


# Export commonly used functions
__all__ = [
    "MockDatabase",
    "MockFileSystem", 
    "MockAPIClient",
    "setup_example_environment",
    "print_separator",
    "print_phase",
    "print_security_demo",
    "print_metrics",
    "mock_external_service",
    "validate_environment",
    "get_mock_secret",
    "MOCK_USERS",
    "MOCK_FILES",
    "MOCK_API_RESPONSES"
]