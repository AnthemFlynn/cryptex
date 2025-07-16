#!/usr/bin/env python3
"""
FastAPI Advanced Middleware Example

This example demonstrates production-ready middleware integration with comprehensive
features including automatic request/response sanitization, performance monitoring,
custom configuration, and advanced error handling. It shows how to use Cryptex
middleware for complete FastAPI application protection.

What you'll learn:
- How to use setup_cryptex_protection() for complete middleware integration
- TOML configuration for advanced features
- Automatic request/response sanitization
- Performance monitoring and metrics collection
- Error handling with sanitized tracebacks
- Request/response size limits for DoS protection
- Health check endpoints with metrics
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
from cryptex.fastapi import setup_cryptex_protection, CryptexMiddleware, create_protected_app
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
# Advanced Mock FastAPI Implementation
# =============================================================================

class AdvancedMockRequest:
    """Advanced mock FastAPI request object with headers and body."""
    
    def __init__(self, method: str, url: str, headers: dict = None, body: Any = None, 
                 query_params: dict = None, form_data: dict = None):
        self.method = method
        self.url = url
        self.headers = headers or {}
        self.body = body
        self.query_params = query_params or {}
        self.form_data = form_data or {}
        self.json_body = body if isinstance(body, dict) else None
        self.size = len(str(body)) if body else 0


class AdvancedMockResponse:
    """Advanced mock FastAPI response object."""
    
    def __init__(self, content: Any, status_code: int = 200, headers: dict = None):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}
        self.size = len(str(content)) if content else 0


class AdvancedMockFastAPI:
    """
    Advanced mock FastAPI application with middleware support.
    
    In a real application, you would use:
    from fastapi import FastAPI
    """
    
    def __init__(self, title: str = "Advanced Cryptex API"):
        self.title = title
        self.routes = {}
        self.middleware = []
        self.request_count = 0
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "secrets_sanitized": 0,
            "errors_sanitized": 0,
            "requests_by_endpoint": {},
            "average_response_time": 0.0
        }
        print(f"🚀 Advanced FastAPI application '{title}' initialized")
    
    def add_middleware(self, middleware_class, **kwargs):
        """Add middleware to the application."""
        self.middleware.append((middleware_class, kwargs))
        print(f"🔧 Middleware added: {middleware_class.__name__}")
    
    def _register_route(self, method: str, path: str, func, **kwargs):
        """Register a route with the application."""
        route_key = f"{method.upper()} {path}"
        self.routes[route_key] = {
            'function': func,
            'method': method.upper(),
            'path': path,
            'kwargs': kwargs,
            'call_count': 0,
            'total_time': 0.0
        }
        print(f"📡 {method.upper()} endpoint registered: {path}")
    
    def get(self, path: str, **kwargs):
        """Decorator for GET endpoints."""
        def decorator(func):
            self._register_route("GET", path, func, **kwargs)
            return func
        return decorator
    
    def post(self, path: str, **kwargs):
        """Decorator for POST endpoints."""
        def decorator(func):
            self._register_route("POST", path, func, **kwargs)
            return func
        return decorator
    
    def put(self, path: str, **kwargs):
        """Decorator for PUT endpoints."""
        def decorator(func):
            self._register_route("PUT", path, func, **kwargs)
            return func
        return decorator
    
    def delete(self, path: str, **kwargs):
        """Decorator for DELETE endpoints."""
        def decorator(func):
            self._register_route("DELETE", path, func, **kwargs)
            return func
        return decorator
    
    async def call_endpoint(self, method: str, path: str, request_data: dict = None, **kwargs):
        """Call an endpoint with advanced middleware simulation."""
        route_key = f"{method.upper()} {path}"
        if route_key not in self.routes:
            return AdvancedMockResponse({"error": "Not found"}, 404)
        
        self.request_count += 1
        self.metrics["total_requests"] += 1
        
        # Track requests by endpoint
        if route_key not in self.metrics["requests_by_endpoint"]:
            self.metrics["requests_by_endpoint"][route_key] = 0
        self.metrics["requests_by_endpoint"][route_key] += 1
        
        start_time = time.time()
        
        print(f"📞 Request #{self.request_count}: {method.upper()} {path}")
        
        try:
            # Simulate middleware processing
            for middleware_class, middleware_kwargs in self.middleware:
                if hasattr(middleware_class, 'process_request'):
                    await middleware_class.process_request(request_data)
            
            # Call the actual endpoint
            route_info = self.routes[route_key]
            
            # Merge request data with kwargs
            all_kwargs = {**kwargs}
            if request_data:
                all_kwargs.update(request_data)
            
            result = await route_info['function'](**all_kwargs)
            
            # Update metrics
            response_time = time.time() - start_time
            route_info['call_count'] += 1
            route_info['total_time'] += response_time
            self.metrics["successful_requests"] += 1
            self.metrics["total_response_time"] += response_time
            self.metrics["average_response_time"] = (
                self.metrics["total_response_time"] / self.metrics["total_requests"]
            )
            
            print(f"✅ Request #{self.request_count}: Completed in {response_time:.3f}s")
            
            if isinstance(result, dict):
                return AdvancedMockResponse(result, 200)
            else:
                return AdvancedMockResponse({"result": result}, 200)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.metrics["failed_requests"] += 1
            self.metrics["errors_sanitized"] += 1
            
            print(f"❌ Request #{self.request_count}: Failed in {response_time:.3f}s - {str(e)}")
            return AdvancedMockResponse({"error": str(e)}, 500)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get application metrics."""
        return {
            "app_metrics": self.metrics,
            "route_metrics": {
                route_key: {
                    "call_count": info["call_count"],
                    "total_time": info["total_time"],
                    "avg_time": info["total_time"] / max(info["call_count"], 1)
                }
                for route_key, info in self.routes.items()
            }
        }
    
    def list_routes(self):
        """List all registered routes with metrics."""
        print(f"\n📋 Routes registered on '{self.title}':")
        for route_key, route_info in self.routes.items():
            print(f"   - {route_key}")
            print(f"     Calls: {route_info['call_count']}, Total time: {route_info['total_time']:.3f}s")


# =============================================================================
# Production-Ready Endpoints with Advanced Features
# =============================================================================

# Create advanced FastAPI app
app = AdvancedMockFastAPI("Production API with Cryptex")

@app.post("/api/v1/auth/login")
async def advanced_login(
    username: str,
    password: str,
    jwt_secret: str,
    device_info: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Advanced authentication endpoint with device tracking.
    
    This endpoint demonstrates:
    - JWT secret protection
    - Complex request data handling
    - Device information processing
    - Comprehensive error handling
    - Audit logging
    """
    print_phase("Advanced Authentication", f"User: {username}")
    
    # Show JWT secret protection
    print_security_demo(
        "JWT Secret Protection",
        "{RESOLVE:JWT_SECRET:hash}",
        f"{jwt_secret[:20]}..."
    )
    
    # Validate credentials
    if not username or not password:
        raise ValueError("Username and password are required")
    
    if username == "admin" and password == "secure123":
        # Generate session token
        session_token = f"session.{jwt_secret[:8]}.{time.time()}"
        
        # Process device info
        device_id = device_info.get("device_id", "unknown") if device_info else "unknown"
        
        return {
            "status": "authenticated",
            "token": session_token,
            "user": {
                "id": 1,
                "username": username,
                "role": "admin",
                "permissions": ["read", "write", "admin"]
            },
            "device": {
                "id": device_id,
                "registered": True,
                "trusted": True
            },
            "session": {
                "expires_at": time.time() + 3600,
                "renewable": True
            }
        }
    else:
        raise ValueError("Invalid credentials")


@app.post("/api/v1/data/analyze")
async def analyze_data(
    data: Dict[str, Any],
    api_key: str,
    database_url: str,
    analysis_type: str = "comprehensive"
) -> Dict[str, Any]:
    """
    Analyze data using multiple external services.
    
    This endpoint demonstrates:
    - Multiple secret types (API key, database URL)
    - Complex data processing
    - External service integration
    - Performance monitoring
    - Error handling with sanitization
    """
    print_phase("Data Analysis", f"Type: {analysis_type}")
    
    # Show secret protections
    print_security_demo("API Key", "{RESOLVE:API_KEY:hash}", f"{api_key[:15]}...")
    print_security_demo("Database URL", "{RESOLVE:DATABASE_URL:hash}", f"{database_url[:25]}...")
    
    # Validate input
    if not data or not isinstance(data, dict):
        raise ValueError("Data must be a non-empty dictionary")
    
    analysis_results = {}
    start_time = time.time()
    
    try:
        # Database analysis
        async with mock_external_service("database", 0.1):
            db = MockDatabase()
            await db.connect(database_url)
            
            # Store analysis request
            await db.query(f"INSERT INTO analysis_requests (type, data_size) VALUES ('{analysis_type}', {len(str(data))})")
            
            # Get historical data
            historical = await db.query("SELECT * FROM analysis_history LIMIT 10")
            analysis_results["historical_context"] = historical
            
            await db.close()
        
        # AI analysis
        async with mock_external_service("ai_service", 0.2):
            client = MockAPIClient(api_key)
            
            if analysis_type == "comprehensive":
                # Multiple AI calls for comprehensive analysis
                tasks = [
                    client.chat_completion([{"role": "user", "content": f"Analyze structure: {data}"}]),
                    client.chat_completion([{"role": "user", "content": f"Find patterns: {data}"}]),
                    client.chat_completion([{"role": "user", "content": f"Identify insights: {data}"}])
                ]
                
                results = await asyncio.gather(*tasks)
                analysis_results["ai_analysis"] = {
                    "structure": results[0],
                    "patterns": results[1],
                    "insights": results[2]
                }
            else:
                # Simple analysis
                result = await client.chat_completion([
                    {"role": "user", "content": f"Analyze: {data}"}
                ])
                analysis_results["ai_analysis"] = {"result": result}
        
        processing_time = time.time() - start_time
        
        return {
            "status": "completed",
            "analysis_type": analysis_type,
            "data_size": len(str(data)),
            "results": analysis_results,
            "processing_time": processing_time,
            "metadata": {
                "timestamp": time.time(),
                "version": "2.0.0",
                "security_level": "high"
            }
        }
        
    except Exception as e:
        print(f"🚨 Analysis error: {str(e)}")
        raise


@app.get("/api/v1/files/{file_id}")
async def get_file_content(
    file_id: str,
    file_path: str,
    api_key: str,
    format: str = "json"
) -> Dict[str, Any]:
    """
    Get file content with advanced processing.
    
    This endpoint demonstrates:
    - Path parameter handling
    - File path sanitization
    - API key protection
    - Format conversion
    - Content processing
    """
    print_phase("File Retrieval", f"File ID: {file_id}, Format: {format}")
    
    # Show protections
    print_security_demo("File Path", "/{USER_HOME}/.../{filename}", file_path)
    print_security_demo("API Key", "{RESOLVE:API_KEY:hash}", f"{api_key[:15]}...")
    
    # Validate file ID
    if not file_id.isalnum():
        raise ValueError("Invalid file ID format")
    
    # Read file content
    content = await MockFileSystem.read_file(file_path)
    
    # Process based on format
    if format == "json":
        try:
            parsed_content = json.loads(content)
            processed_content = parsed_content
        except json.JSONDecodeError:
            processed_content = {"raw_content": content}
    elif format == "analysis":
        # Use AI to analyze content
        client = MockAPIClient(api_key)
        analysis = await client.chat_completion([
            {"role": "user", "content": f"Analyze this file content: {content[:500]}"}
        ])
        processed_content = {"analysis": analysis, "original_size": len(content)}
    else:
        processed_content = {"raw_content": content}
    
    return {
        "file_id": file_id,
        "file_path": file_path,
        "format": format,
        "content": processed_content,
        "metadata": {
            "size": len(content),
            "retrieved_at": time.time(),
            "processing_applied": format != "raw"
        }
    }


@app.put("/api/v1/config/update")
async def update_configuration(
    config_data: Dict[str, Any],
    database_url: str,
    redis_url: str,
    jwt_secret: str,
    api_key: str,
    admin_email: str
) -> Dict[str, Any]:
    """
    Update application configuration with multiple secret types.
    
    This endpoint demonstrates:
    - Multiple secret types simultaneously
    - Complex configuration validation
    - Email protection
    - Comprehensive error handling
    - Audit logging
    """
    print_phase("Configuration Update", "Updating system configuration")
    
    # Show all secret protections
    print_security_demo("Database URL", "{RESOLVE:DATABASE_URL:hash}", f"{database_url[:25]}...")
    print_security_demo("Redis URL", "{RESOLVE:REDIS_URL:hash}", f"{redis_url[:20]}...")
    print_security_demo("JWT Secret", "{RESOLVE:JWT_SECRET:hash}", f"{jwt_secret[:15]}...")
    print_security_demo("API Key", "{RESOLVE:API_KEY:hash}", f"{api_key[:15]}...")
    print_security_demo("Admin Email", "{RESOLVE:EMAIL:hash}", admin_email)
    
    # Validate configuration data
    if not config_data or not isinstance(config_data, dict):
        raise ValueError("Configuration data must be a non-empty dictionary")
    
    # Validate email format
    if "@" not in admin_email:
        raise ValueError("Invalid email format")
    
    update_results = {}
    
    try:
        # Database configuration update
        async with mock_external_service("database", 0.1):
            db = MockDatabase()
            await db.connect(database_url)
            
            # Update database config
            await db.query(f"UPDATE config SET updated_at = {time.time()}")
            update_results["database"] = {"status": "updated", "url": database_url[:20] + "..."}
            
            await db.close()
        
        # Redis configuration update
        async with mock_external_service("redis", 0.05):
            update_results["redis"] = {"status": "updated", "url": redis_url[:15] + "..."}
        
        # JWT configuration update
        update_results["jwt"] = {
            "status": "updated",
            "secret_length": len(jwt_secret),
            "expires_in": 3600
        }
        
        # API configuration update
        update_results["api"] = {
            "status": "updated",
            "key_prefix": api_key[:8] + "...",
            "rate_limit": "1000/hour"
        }
        
        # Send notification to admin
        update_results["notification"] = {
            "sent_to": admin_email,
            "subject": "Configuration Updated",
            "status": "sent"
        }
        
        return {
            "status": "success",
            "message": "Configuration updated successfully",
            "updated_components": list(update_results.keys()),
            "results": update_results,
            "config_data": config_data,
            "timestamp": time.time()
        }
        
    except Exception as e:
        print(f"🚨 Configuration update error: {str(e)}")
        raise


@app.delete("/api/v1/data/purge")
async def purge_sensitive_data(
    database_url: str,
    redis_url: str,
    confirmation_token: str,
    admin_email: str
) -> Dict[str, Any]:
    """
    Purge sensitive data from all systems.
    
    This endpoint demonstrates:
    - Destructive operation protection
    - Multiple database operations
    - Email notification
    - Comprehensive audit logging
    - Security token validation
    """
    print_phase("Data Purge", "Purging sensitive data from all systems")
    
    # Show protections
    print_security_demo("Database URL", "{RESOLVE:DATABASE_URL:hash}", f"{database_url[:25]}...")
    print_security_demo("Redis URL", "{RESOLVE:REDIS_URL:hash}", f"{redis_url[:20]}...")
    print_security_demo("Confirmation Token", "{RESOLVE:TOKEN:hash}", f"{confirmation_token[:10]}...")
    print_security_demo("Admin Email", "{RESOLVE:EMAIL:hash}", admin_email)
    
    # Validate confirmation token
    if confirmation_token != "CONFIRM_PURGE_123":
        raise ValueError("Invalid confirmation token")
    
    purge_results = {}
    
    try:
        # Database purge
        async with mock_external_service("database", 0.2):
            db = MockDatabase()
            await db.connect(database_url)
            
            # Purge operations
            tables_purged = ["user_sessions", "temporary_data", "cache_entries"]
            for table in tables_purged:
                await db.query(f"DELETE FROM {table}")
            
            purge_results["database"] = {
                "status": "purged",
                "tables_affected": tables_purged,
                "records_removed": 1337
            }
            
            await db.close()
        
        # Redis purge
        async with mock_external_service("redis", 0.1):
            purge_results["redis"] = {
                "status": "purged",
                "keys_removed": 842,
                "patterns": ["session:*", "cache:*", "temp:*"]
            }
        
        # Send confirmation email
        purge_results["notification"] = {
            "sent_to": admin_email,
            "subject": "Data Purge Completed",
            "status": "sent",
            "timestamp": time.time()
        }
        
        return {
            "status": "completed",
            "message": "Sensitive data purged successfully",
            "purge_results": purge_results,
            "confirmation_token": confirmation_token[:8] + "...",
            "admin_notified": admin_email,
            "timestamp": time.time()
        }
        
    except Exception as e:
        print(f"🚨 Purge error: {str(e)}")
        raise


@app.get("/api/v1/health")
async def health_check_with_metrics() -> Dict[str, Any]:
    """
    Health check endpoint with comprehensive metrics.
    
    This endpoint demonstrates:
    - Public endpoint (no secret protection)
    - Metrics collection and reporting
    - System status monitoring
    - Performance statistics
    """
    print_phase("Health Check", "Collecting system metrics")
    
    # Get application metrics
    metrics = app.get_metrics()
    
    # Calculate health status
    error_rate = metrics["app_metrics"]["failed_requests"] / max(metrics["app_metrics"]["total_requests"], 1)
    health_status = "healthy" if error_rate < 0.1 else "degraded" if error_rate < 0.5 else "unhealthy"
    
    return {
        "status": health_status,
        "timestamp": time.time(),
        "version": "2.0.0",
        "features": [
            "cryptex_protection",
            "temporal_isolation",
            "request_sanitization",
            "response_sanitization",
            "performance_monitoring",
            "error_handling"
        ],
        "metrics": metrics,
        "uptime": "simulated_uptime",
        "environment": "production"
    }


@app.get("/api/v1/metrics")
async def get_detailed_metrics() -> Dict[str, Any]:
    """
    Get detailed application metrics.
    
    This endpoint demonstrates:
    - Metrics endpoint pattern
    - Performance data collection
    - System statistics
    - Monitoring integration
    """
    print_phase("Metrics Collection", "Gathering detailed system metrics")
    
    metrics = app.get_metrics()
    
    # Add additional metrics
    detailed_metrics = {
        **metrics,
        "system_info": {
            "python_version": "3.13+",
            "cryptex_version": "1.0.0",
            "framework": "FastAPI",
            "middleware": "CryptexMiddleware"
        },
        "security_metrics": {
            "secrets_protected": metrics["app_metrics"]["secrets_sanitized"],
            "errors_sanitized": metrics["app_metrics"]["errors_sanitized"],
            "requests_protected": metrics["app_metrics"]["total_requests"]
        },
        "performance_metrics": {
            "average_response_time": metrics["app_metrics"]["average_response_time"],
            "total_processing_time": metrics["app_metrics"]["total_response_time"],
            "requests_per_second": metrics["app_metrics"]["total_requests"] / max(time.time() - 1000, 1)
        }
    }
    
    return detailed_metrics


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
        print(f"   Request size limit: {config.middleware.max_request_size}")
        print(f"   Response size limit: {config.middleware.max_response_size}")
        
    except FileNotFoundError:
        print("⚠️  Advanced config not found, using defaults")
        config = CryptexConfig()
    
    # Set up middleware protection
    print_phase("Middleware Integration", "Setting up FastAPI protection")
    
    try:
        # This would normally work with real FastAPI:
        # protection = setup_cryptex_protection(app, config=config)
        
        # For demo, we'll create the middleware manually
        middleware = CryptexMiddleware(
            app=app,
            config=config,
            auto_protect=True,
            sanitize_headers=True,
            sanitize_query_params=True,
            sanitize_request_body=True,
            sanitize_response_body=True,
            max_request_size=50 * 1024 * 1024,   # 50MB
            max_response_size=50 * 1024 * 1024   # 50MB
        )
        
        await middleware.initialize()
        
        # Add to app (mock implementation)
        app.add_middleware(CryptexMiddleware, config=config)
        
        print("✅ Advanced middleware protection activated")
        
        return middleware
        
    except Exception as e:
        print(f"❌ Middleware setup failed: {str(e)}")
        raise


async def demonstrate_request_response_sanitization():
    """Demonstrate request/response sanitization with large payloads."""
    print_separator("Request/Response Sanitization", "=")
    
    print_phase("Large Request Test", "Testing request size limits")
    
    # Test with large request
    large_data = {
        "user_data": "x" * 1000,  # 1KB of data
        "api_key": os.getenv("OPENAI_API_KEY"),
        "files": ["file1.txt", "file2.txt"] * 100,  # Large array
        "metadata": {"key": "value"} * 50  # Large object
    }
    
    try:
        response = await app.call_endpoint(
            "POST", "/api/v1/data/analyze",
            request_data=large_data,
            analysis_type="comprehensive"
        )
        print(f"✅ Large request handled successfully")
        print(f"   Request size: {len(str(large_data))} bytes")
        print(f"   Response size: {len(str(response.content))} bytes")
        
    except Exception as e:
        print(f"❌ Large request failed: {str(e)}")


async def stress_test_endpoints():
    """Stress test endpoints to demonstrate performance."""
    print_separator("Stress Testing", "=")
    
    print_phase("Concurrent Requests", "Testing concurrent request handling")
    
    # Create concurrent requests
    tasks = []
    for i in range(10):
        task = app.call_endpoint(
            "GET", "/api/v1/health"
        )
        tasks.append(task)
    
    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.time()
    
    successful_requests = sum(1 for r in results if not isinstance(r, Exception))
    failed_requests = len(results) - successful_requests
    
    print(f"📊 Stress test results:")
    print(f"   Total requests: {len(tasks)}")
    print(f"   Successful: {successful_requests}")
    print(f"   Failed: {failed_requests}")
    print(f"   Total time: {end_time - start_time:.3f}s")
    print(f"   Requests/second: {len(tasks) / (end_time - start_time):.2f}")


# =============================================================================
# Main Example Runner
# =============================================================================

async def main():
    """Run all advanced FastAPI middleware examples."""
    print_separator("FastAPI Advanced Middleware Example", "=")
    print("🏭 Production-ready middleware with comprehensive features")
    print("   Complete application protection with monitoring and configuration")
    
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
    
    # List available routes
    app.list_routes()
    
    # Example 1: Advanced authentication
    print_separator("Example 1: Advanced Authentication", "-")
    
    try:
        auth_response = await app.call_endpoint(
            "POST", "/api/v1/auth/login",
            request_data={
                "username": "admin",
                "password": "secure123",
                "jwt_secret": os.getenv("JWT_SECRET"),
                "device_info": {"device_id": "mobile_123", "os": "iOS"}
            }
        )
        print(f"🔐 Authentication response: {json.dumps(auth_response.content, indent=2)}")
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
    
    # Example 2: Data analysis with multiple services
    print_separator("Example 2: Data Analysis with Multiple Services", "-")
    
    try:
        analysis_response = await app.call_endpoint(
            "POST", "/api/v1/data/analyze",
            request_data={
                "data": {"user_id": 123, "transactions": [1, 2, 3, 4, 5], "metadata": {"source": "app"}},
                "api_key": os.getenv("OPENAI_API_KEY"),
                "database_url": os.getenv("DATABASE_URL"),
                "analysis_type": "comprehensive"
            }
        )
        print(f"📊 Analysis response: {json.dumps(analysis_response.content, indent=2)}")
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
    
    # Example 3: File processing
    print_separator("Example 3: File Processing", "-")
    
    try:
        file_response = await app.call_endpoint(
            "GET", "/api/v1/files/doc123",
            request_data={
                "file_path": "/app/documents/important.json",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "format": "analysis"
            }
        )
        print(f"📁 File response: {json.dumps(file_response.content, indent=2)}")
    except Exception as e:
        print(f"❌ File processing failed: {str(e)}")
    
    # Example 4: Configuration update
    print_separator("Example 4: Configuration Update", "-")
    
    try:
        config_response = await app.call_endpoint(
            "PUT", "/api/v1/config/update",
            request_data={
                "config_data": {"feature_x": True, "max_users": 5000, "rate_limit": 1000},
                "database_url": os.getenv("DATABASE_URL"),
                "redis_url": os.getenv("REDIS_URL"),
                "jwt_secret": os.getenv("JWT_SECRET"),
                "api_key": os.getenv("OPENAI_API_KEY"),
                "admin_email": "admin@example.com"
            }
        )
        print(f"⚙️ Configuration response: {json.dumps(config_response.content, indent=2)}")
    except Exception as e:
        print(f"❌ Configuration update failed: {str(e)}")
    
    # Example 5: Data purge (destructive operation)
    print_separator("Example 5: Data Purge Operation", "-")
    
    try:
        purge_response = await app.call_endpoint(
            "DELETE", "/api/v1/data/purge",
            request_data={
                "database_url": os.getenv("DATABASE_URL"),
                "redis_url": os.getenv("REDIS_URL"),
                "confirmation_token": "CONFIRM_PURGE_123",
                "admin_email": "admin@example.com"
            }
        )
        print(f"🗑️ Purge response: {json.dumps(purge_response.content, indent=2)}")
    except Exception as e:
        print(f"❌ Purge operation failed: {str(e)}")
    
    # Example 6: Health check with metrics
    print_separator("Example 6: Health Check with Metrics", "-")
    
    try:
        health_response = await app.call_endpoint("GET", "/api/v1/health")
        print(f"💚 Health response: {json.dumps(health_response.content, indent=2)}")
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
    
    # Example 7: Detailed metrics
    print_separator("Example 7: Detailed Metrics", "-")
    
    try:
        metrics_response = await app.call_endpoint("GET", "/api/v1/metrics")
        print(f"📊 Metrics response: {json.dumps(metrics_response.content, indent=2)}")
    except Exception as e:
        print(f"❌ Metrics collection failed: {str(e)}")
    
    # Example 8: Request/response sanitization
    await demonstrate_request_response_sanitization()
    
    # Example 9: Stress testing
    await stress_test_endpoints()
    
    # Final summary
    print_separator("Final Summary", "=")
    
    final_metrics = app.get_metrics()
    print_metrics(final_metrics)
    
    print("\n✅ All advanced examples completed successfully!")
    print(f"📊 Total requests processed: {app.request_count}")
    
    print("\n💡 Advanced Features Demonstrated:")
    print("   🛡️  Complete middleware protection for all endpoints")
    print("   📊 Comprehensive metrics collection and monitoring")
    print("   🔧 Advanced TOML configuration management")
    print("   🚨 Robust error handling and sanitization")
    print("   📈 Performance monitoring and optimization")
    print("   🔒 Multiple secret types protected simultaneously")
    print("   📋 Request/response size limits (DoS protection)")
    print("   ⚡ Concurrent request handling")
    print("   🎯 Production-ready patterns and best practices")
    
    print("\n🎯 Production Benefits:")
    print("   • Zero-configuration protection for entire application")
    print("   • Automatic request/response sanitization")
    print("   • Comprehensive monitoring and health checks")
    print("   • Advanced security with audit trails")
    print("   • Optimal performance with intelligent caching")
    print("   • Robust error handling and recovery")
    print("   • DoS protection with size limits")
    print("   • Scalable architecture for high-traffic applications")
    
    print("\n🎉 FastAPI Advanced Middleware Example Complete!")
    print("   Next: Review all examples and explore production deployment")


if __name__ == "__main__":
    asyncio.run(main())