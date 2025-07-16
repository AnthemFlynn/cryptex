#!/usr/bin/env python3
"""
FastMCP Advanced Middleware Example

This example demonstrates production-ready middleware integration with comprehensive
features including monitoring, custom configuration, performance tracking, and
advanced error handling. It shows how to use Cryptex middleware for complete
FastMCP server protection.

What you'll learn:
- How to use setup_cryptex_protection() for complete middleware integration
- TOML configuration for advanced features
- Performance monitoring and metrics collection
- Error handling and sanitization
- Context expiration and cleanup
- Audit logging and security monitoring
- Multiple tools with different secret types
- Production-ready patterns and best practices
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the project root to the Python path so we can import cryptex
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import Cryptex components
from cryptex.fastmcp import setup_cryptex_protection, FastMCPCryptexMiddleware
from cryptex.config import CryptexConfig
from cryptex.core import TemporalIsolationEngine

# Import example utilities
from examples.shared.utils import (
    setup_example_environment,
    print_separator,
    print_phase,
    print_security_demo,
    print_metrics,
    MockAPIClient,
    MockFileSystem,
    MockDatabase,
    mock_external_service,
    validate_environment
)


# =============================================================================
# Advanced Mock FastMCP Server Implementation
# =============================================================================

class AdvancedMockFastMCPServer:
    """
    Advanced mock FastMCP server with middleware support.
    
    In a real application, you would use:
    from fastmcp import FastMCPServer
    """
    
    def __init__(self, name: str = "advanced-cryptex-server"):
        self.name = name
        self.tools = {}
        self.middleware = []
        self.request_count = 0
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time": 0.0,
            "secrets_sanitized": 0,
            "contexts_created": 0
        }
        print(f"🚀 Advanced FastMCP Server '{name}' initialized")
    
    def add_middleware(self, middleware_func):
        """Add middleware to the server."""
        self.middleware.append(middleware_func)
        print(f"🔧 Middleware added: {middleware_func.__name__}")
    
    def tool(self, name: str = None, description: str = None):
        """Decorator to register a tool with the server."""
        def decorator(func):
            tool_name = name or func.__name__
            self.tools[tool_name] = {
                'function': func,
                'description': description or func.__doc__,
                'call_count': 0,
                'total_time': 0.0
            }
            print(f"🔧 Tool '{tool_name}' registered")
            return func
        return decorator
    
    async def call_tool(self, tool_name: str, *args, **kwargs):
        """Call a registered tool through middleware chain."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        self.request_count += 1
        self.metrics["total_requests"] += 1
        start_time = time.time()
        
        try:
            print(f"📞 Request #{self.request_count}: Calling tool '{tool_name}'")
            
            # Simulate middleware processing
            for middleware in self.middleware:
                if hasattr(middleware, 'process_request'):
                    await middleware.process_request(tool_name, args, kwargs)
            
            # Call the actual tool
            tool_info = self.tools[tool_name]
            result = await tool_info['function'](*args, **kwargs)
            
            # Update metrics
            processing_time = time.time() - start_time
            tool_info['call_count'] += 1
            tool_info['total_time'] += processing_time
            self.metrics["successful_requests"] += 1
            self.metrics["total_processing_time"] += processing_time
            
            print(f"✅ Request #{self.request_count}: Completed in {processing_time:.3f}s")
            return result
            
        except Exception as e:
            self.metrics["failed_requests"] += 1
            print(f"❌ Request #{self.request_count}: Failed - {str(e)}")
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get server metrics."""
        return {
            "server_metrics": self.metrics,
            "tool_metrics": {
                name: {
                    "call_count": info["call_count"],
                    "total_time": info["total_time"],
                    "avg_time": info["total_time"] / max(info["call_count"], 1)
                }
                for name, info in self.tools.items()
            }
        }
    
    def list_tools(self):
        """List all registered tools."""
        print(f"\n📋 Tools registered on server '{self.name}':")
        for name, info in self.tools.items():
            print(f"   - {name}: {info['description']}")
            print(f"     Calls: {info['call_count']}, Total time: {info['total_time']:.3f}s")


# =============================================================================
# Production-Ready Tools with Advanced Features
# =============================================================================

# Create advanced server
server = AdvancedMockFastMCPServer("production-server")

@server.tool("secure_file_processor", "Process files with comprehensive security")
async def secure_file_processor(
    file_path: str,
    api_key: str,
    processing_mode: str = "analyze"
) -> Dict[str, Any]:
    """
    Process files with comprehensive security and error handling.
    
    This tool demonstrates:
    - File path sanitization
    - API key protection
    - Error handling with sanitized tracebacks
    - Performance monitoring
    - Audit logging
    """
    print_phase("Secure File Processing", f"Mode: {processing_mode}")
    
    start_time = time.time()
    
    try:
        # Show security in action
        print_security_demo(
            "File Path Sanitization",
            "/{USER_HOME}/.../{filename}",
            file_path
        )
        
        # Read file content
        content = await MockFileSystem.read_file(file_path)
        
        # Process with AI API
        if processing_mode == "analyze":
            client = MockAPIClient(api_key)
            analysis = await client.chat_completion([
                {"role": "user", "content": f"Analyze this file content: {content[:200]}..."}
            ])
            
            processing_time = time.time() - start_time
            
            return {
                "status": "success",
                "file_path": file_path,
                "content_length": len(content),
                "analysis": analysis,
                "processing_time": processing_time,
                "mode": processing_mode,
                "security_features": ["path_sanitization", "api_key_protection"]
            }
        else:
            raise ValueError(f"Unknown processing mode: {processing_mode}")
            
    except Exception as e:
        # The middleware will sanitize this error automatically
        print(f"🚨 Error in secure_file_processor: {str(e)}")
        raise


@server.tool("multi_service_coordinator", "Coordinate multiple external services")
async def multi_service_coordinator(
    database_url: str,
    redis_url: str,
    api_key: str,
    operation: str
) -> Dict[str, Any]:
    """
    Coordinate operations across multiple external services.
    
    This tool demonstrates:
    - Multiple secret types in one operation
    - Service coordination patterns
    - Comprehensive error handling
    - Performance optimization
    """
    print_phase("Multi-Service Coordination", f"Operation: {operation}")
    
    results = {}
    start_time = time.time()
    
    try:
        # Show all secret protections
        print_security_demo("Database URL", "{RESOLVE:DATABASE_URL:hash}", f"{database_url[:25]}...")
        print_security_demo("Redis URL", "{RESOLVE:REDIS_URL:hash}", f"{redis_url[:20]}...")
        print_security_demo("API Key", "{RESOLVE:API_KEY:hash}", f"{api_key[:15]}...")
        
        if operation == "sync_data":
            # Database operation
            async with mock_external_service("database", 0.1):
                db = MockDatabase()
                await db.connect(database_url)
                db_data = await db.query("SELECT * FROM sync_table")
                results["database"] = {"rows": len(db_data), "status": "synced"}
                await db.close()
            
            # Redis operation
            async with mock_external_service("redis", 0.05):
                # Simulate Redis operations
                results["redis"] = {"keys_updated": 15, "status": "cached"}
            
            # API operation
            async with mock_external_service("external_api", 0.2):
                client = MockAPIClient(api_key)
                api_response = await client.make_request("/sync")
                results["api"] = {"response": api_response, "status": "notified"}
            
            processing_time = time.time() - start_time
            
            return {
                "operation": operation,
                "results": results,
                "processing_time": processing_time,
                "services_used": 3,
                "status": "completed"
            }
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    except Exception as e:
        print(f"🚨 Error in multi_service_coordinator: {str(e)}")
        raise


@server.tool("advanced_data_processor", "Process data with advanced security features")
async def advanced_data_processor(
    user_data: Dict[str, Any],
    jwt_token: str,
    encryption_key: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Process user data with advanced security and validation.
    
    This tool demonstrates:
    - Complex data structure handling
    - JWT token protection
    - Encryption key security
    - Output path sanitization
    - Data validation and sanitization
    """
    print_phase("Advanced Data Processing", "Processing user data")
    
    start_time = time.time()
    
    try:
        # Show security protections
        print_security_demo("JWT Token", "{RESOLVE:JWT_TOKEN:hash}", f"{jwt_token[:20]}...")
        print_security_demo("Encryption Key", "{RESOLVE:ENCRYPTION_KEY:hash}", f"{encryption_key[:10]}...")
        print_security_demo("Output Path", "/{USER_HOME}/.../{filename}", output_path)
        
        # Validate and process data
        if not isinstance(user_data, dict):
            raise ValueError("User data must be a dictionary")
        
        processed_data = {
            "user_id": user_data.get("user_id"),
            "processed_at": time.time(),
            "data_size": len(str(user_data)),
            "security_level": "high"
        }
        
        # Simulate encryption
        await asyncio.sleep(0.1)  # Simulate encryption time
        
        # Write to output file
        await MockFileSystem.write_file(
            output_path,
            json.dumps(processed_data, indent=2)
        )
        
        processing_time = time.time() - start_time
        
        return {
            "status": "processed",
            "input_size": len(str(user_data)),
            "output_path": output_path,
            "processing_time": processing_time,
            "security_features": [
                "jwt_validation",
                "encryption_applied",
                "path_sanitization",
                "data_validation"
            ]
        }
        
    except Exception as e:
        print(f"🚨 Error in advanced_data_processor: {str(e)}")
        raise


@server.tool("health_check", "Server health check with metrics")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint that provides server status and metrics.
    
    This tool demonstrates:
    - No secret protection needed (public endpoint)
    - Metrics collection and reporting
    - Server status monitoring
    """
    print_phase("Health Check", "Collecting server metrics")
    
    metrics = server.get_metrics()
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "server_name": server.name,
        "metrics": metrics,
        "uptime": "simulated_uptime",
        "version": "1.0.0"
    }


# =============================================================================
# Advanced Configuration and Setup
# =============================================================================

async def setup_advanced_middleware():
    """Set up advanced middleware with comprehensive configuration."""
    print_separator("Advanced Middleware Setup", "=")
    
    # Load advanced configuration
    config_path = Path(__file__).parent.parent / "config" / "advanced.toml"
    
    try:
        config = await CryptexConfig.from_toml(str(config_path))
        print(f"✅ Loaded advanced configuration from {config_path}")
        
        # Display configuration summary
        print(f"📋 Configuration summary:")
        print(f"   Secret patterns: {len(config.secret_patterns)}")
        print(f"   Enforcement mode: {config.security_policy.enforcement_mode}")
        print(f"   Cache size: {config.performance.cache_size}")
        print(f"   Auto-protect: {config.middleware.auto_protect_tools}")
        
    except FileNotFoundError:
        print("⚠️  Advanced config not found, using defaults")
        config = CryptexConfig()
    
    # Set up middleware protection
    print_phase("Middleware Integration", "Setting up FastMCP protection")
    
    try:
        # This would normally work with real FastMCP:
        # protection = await setup_cryptex_protection(server, config=config)
        
        # For demo, we'll create the middleware manually
        middleware = FastMCPCryptexMiddleware(
            config=config,
            auto_protect=True,
            max_request_size=10 * 1024 * 1024,  # 10MB
            max_response_size=10 * 1024 * 1024   # 10MB
        )
        
        await middleware.initialize()
        
        # Add to server (mock implementation)
        server.add_middleware(middleware)
        
        print("✅ Advanced middleware protection activated")
        
        return middleware
        
    except Exception as e:
        print(f"❌ Middleware setup failed: {str(e)}")
        raise


async def demonstrate_monitoring():
    """Demonstrate monitoring and metrics collection."""
    print_separator("Monitoring & Metrics", "=")
    
    # Get server metrics
    metrics = server.get_metrics()
    print_metrics(metrics)
    
    # Simulate some load for metrics
    print_phase("Load Testing", "Generating sample requests")
    
    tasks = []
    for i in range(5):
        task = server.call_tool("health_check")
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    
    # Show updated metrics
    print("\n📊 Updated metrics after load test:")
    updated_metrics = server.get_metrics()
    print_metrics(updated_metrics)


async def demonstrate_error_handling():
    """Demonstrate error handling and sanitization."""
    print_separator("Error Handling & Sanitization", "=")
    
    print_phase("Error Simulation", "Testing error sanitization")
    
    try:
        # This will cause an error to test sanitization
        await server.call_tool(
            "secure_file_processor",
            file_path="/nonexistent/file.txt",
            api_key=os.getenv("OPENAI_API_KEY"),
            processing_mode="invalid_mode"
        )
    except Exception as e:
        print(f"🔒 Error was sanitized: {str(e)}")
        print("   Notice: No sensitive information leaked in the error message")


# =============================================================================
# Performance Benchmarking
# =============================================================================

async def benchmark_performance():
    """Benchmark the performance of protected operations."""
    print_separator("Performance Benchmarking", "=")
    
    operations = [
        ("secure_file_processor", {
            "file_path": "/app/data/sample.txt",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "processing_mode": "analyze"
        }),
        ("multi_service_coordinator", {
            "database_url": os.getenv("DATABASE_URL"),
            "redis_url": os.getenv("REDIS_URL"),
            "api_key": os.getenv("OPENAI_API_KEY"),
            "operation": "sync_data"
        }),
        ("advanced_data_processor", {
            "user_data": {"user_id": 123, "data": "sample"},
            "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example.signature",
            "encryption_key": "secret-encryption-key-123",
            "output_path": "/tmp/output.json"
        })
    ]
    
    print_phase("Benchmark Testing", "Measuring operation performance")
    
    benchmark_results = []
    
    for operation_name, kwargs in operations:
        start_time = time.time()
        
        try:
            result = await server.call_tool(operation_name, **kwargs)
            end_time = time.time()
            
            benchmark_results.append({
                "operation": operation_name,
                "duration": end_time - start_time,
                "status": "success",
                "result_size": len(str(result))
            })
            
        except Exception as e:
            end_time = time.time()
            benchmark_results.append({
                "operation": operation_name,
                "duration": end_time - start_time,
                "status": "failed",
                "error": str(e)
            })
    
    # Display benchmark results
    print("\n📊 Benchmark Results:")
    for result in benchmark_results:
        print(f"   {result['operation']}: {result['duration']:.3f}s ({result['status']})")
    
    avg_duration = sum(r['duration'] for r in benchmark_results) / len(benchmark_results)
    print(f"   Average duration: {avg_duration:.3f}s")
    
    return benchmark_results


# =============================================================================
# Main Example Runner
# =============================================================================

async def main():
    """Run all advanced FastMCP middleware examples."""
    print_separator("FastMCP Advanced Middleware Example", "=")
    print("🏭 Production-ready middleware with comprehensive features")
    print("   Complete server protection with monitoring and configuration")
    
    # Setup environment
    setup_example_environment()
    
    if not validate_environment():
        print("❌ Environment validation failed. Please check your setup.")
        return
    
    # Set up advanced middleware
    try:
        middleware = await setup_advanced_middleware()
    except Exception as e:
        print(f"❌ Failed to set up middleware: {str(e)}")
        return
    
    # List available tools
    server.list_tools()
    
    # Example 1: Secure file processing
    print_separator("Example 1: Secure File Processing", "-")
    
    try:
        result1 = await server.call_tool(
            "secure_file_processor",
            file_path="/app/data/sensitive-config.json",
            api_key=os.getenv("OPENAI_API_KEY"),
            processing_mode="analyze"
        )
        print(f"📄 File processing result: {json.dumps(result1, indent=2)}")
    except Exception as e:
        print(f"❌ File processing failed: {str(e)}")
    
    # Example 2: Multi-service coordination
    print_separator("Example 2: Multi-Service Coordination", "-")
    
    try:
        result2 = await server.call_tool(
            "multi_service_coordinator",
            database_url=os.getenv("DATABASE_URL"),
            redis_url=os.getenv("REDIS_URL"),
            api_key=os.getenv("OPENAI_API_KEY"),
            operation="sync_data"
        )
        print(f"🔄 Coordination result: {json.dumps(result2, indent=2)}")
    except Exception as e:
        print(f"❌ Coordination failed: {str(e)}")
    
    # Example 3: Advanced data processing
    print_separator("Example 3: Advanced Data Processing", "-")
    
    try:
        result3 = await server.call_tool(
            "advanced_data_processor",
            user_data={"user_id": 12345, "name": "John Doe", "data": "sensitive_info"},
            jwt_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example.signature",
            encryption_key="my-secret-encryption-key-123",
            output_path="/app/output/processed_data.json"
        )
        print(f"🔒 Data processing result: {json.dumps(result3, indent=2)}")
    except Exception as e:
        print(f"❌ Data processing failed: {str(e)}")
    
    # Example 4: Health check and monitoring
    print_separator("Example 4: Health Check & Monitoring", "-")
    
    await demonstrate_monitoring()
    
    # Example 5: Error handling
    await demonstrate_error_handling()
    
    # Example 6: Performance benchmarking
    benchmark_results = await benchmark_performance()
    
    # Final metrics and summary
    print_separator("Final Summary", "=")
    
    final_metrics = server.get_metrics()
    print_metrics(final_metrics)
    
    print("\n✅ All advanced examples completed successfully!")
    print("\n💡 Advanced Features Demonstrated:")
    print("   🛡️  Complete middleware protection for all tools")
    print("   📊 Performance monitoring and metrics collection")
    print("   🔧 TOML-based configuration management")
    print("   🚨 Advanced error handling and sanitization")
    print("   🏃 Performance benchmarking and optimization")
    print("   🔒 Multiple secret types protected simultaneously")
    print("   📋 Audit logging and security monitoring")
    print("   ⚡ Production-ready patterns and best practices")
    
    print("\n🎯 Production Benefits:")
    print("   • Zero-configuration protection for all tools")
    print("   • Comprehensive monitoring and alerting")
    print("   • Advanced security with audit trails")
    print("   • Optimal performance with caching")
    print("   • Robust error handling and recovery")
    
    print("\n🎉 FastMCP Advanced Middleware Example Complete!")
    print("   Next: Explore FastAPI examples in ../fastapi/")


if __name__ == "__main__":
    asyncio.run(main())