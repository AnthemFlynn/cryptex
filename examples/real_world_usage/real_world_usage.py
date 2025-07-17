#!/usr/bin/env python3
"""
Real-World Usage Example - Production Patterns

This example demonstrates realistic usage patterns for cryptex in production
applications. Shows how to build secure AI tools and services.

What you'll learn:
- Production-ready secret management patterns
- Integration with real services (GitHub, databases, file systems)
- Error handling with secret protection
- Monitoring and logging with sanitized data
- Performance considerations for high-throughput applications
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any

# Add src to path for local development
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from cryptex_ai import protect_secrets, register_pattern
try:
    from cryptex_ai import secure_session
except ImportError:
    # For compatibility - secure_session might not be in all versions
    secure_session = None

# Set up logging (will show sanitized data thanks to cryptex)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Custom Patterns for Organization
# =============================================================================

# Register organization-specific patterns
register_pattern(
    name="internal_api_key",
    regex=r"ik_[a-zA-Z0-9]{32}",
    placeholder="{{INTERNAL_API_KEY}}",
    description="Internal service API key"
)

register_pattern(
    name="customer_data_token",
    regex=r"cdt_[a-zA-Z0-9]{40}",
    placeholder="{{CUSTOMER_DATA_TOKEN}}",
    description="Customer data access token"
)


# =============================================================================
# Production AI Assistant Class
# =============================================================================

class SecureAIAssistant:
    """
    Production AI assistant with comprehensive secret protection.

    Demonstrates real-world patterns for building secure AI tools.
    """

    def __init__(self):
        self.session_count = 0
        self.start_time = time.time()

    @protect_secrets(["openai_key"])
    async def generate_response(
        self,
        prompt: str,
        api_key: str,
        model: str = "gpt-4",
        max_tokens: int = 500
    ) -> dict[str, Any]:
        """
        Generate AI response with protected API key.

        Logs will show sanitized key, but function gets real key for API calls.
        """
        logger.info(f"Generating response with model: {model}")
        logger.info(f"API key: {api_key}")  # This will be sanitized in logs

        start = time.time()

        # Simulate OpenAI API call
        await asyncio.sleep(0.1)  # Simulate network latency

        response = {
            "content": f"AI response to: {prompt[:50]}...",
            "model": model,
            "tokens_used": max_tokens // 2,
            "duration_ms": int((time.time() - start) * 1000)
        }

        logger.info(f"Response generated in {response['duration_ms']}ms")
        return response

    @protect_secrets(["github_token", "file_path"])
    async def analyze_repository(
        self,
        repo_path: str,
        github_token: str,
        file_patterns: list[str] = None
    ) -> dict[str, Any]:
        """
        Analyze GitHub repository with protected credentials and paths.

        Both GitHub token and file paths are protected from AI context.
        """
        if file_patterns is None:
            file_patterns = ["*.py", "*.js", "*.md"]

        logger.info(f"Analyzing repository: {repo_path}")
        logger.info(f"Using GitHub token: {github_token}")  # Sanitized in logs

        # Simulate GitHub API calls
        await asyncio.sleep(0.2)

        # Simulate file system scanning
        files_found = []
        for pattern in file_patterns:
            files_found.extend([f"example_{pattern.replace('*', '1')}",
                              f"test_{pattern.replace('*', '2')}"])

        analysis = {
            "repository": repo_path.split('/')[-1],
            "files_analyzed": len(files_found),
            "file_types": file_patterns,
            "analysis_time": datetime.now().isoformat(),
            "security_score": 85
        }

        logger.info(f"Repository analysis complete: {len(files_found)} files")
        return analysis

    @protect_secrets(["database_url", "customer_data_token"])
    async def process_customer_data(
        self,
        customer_id: str,
        db_url: str,
        data_token: str,
        operation: str = "analyze"
    ) -> dict[str, Any]:
        """
        Process customer data with database and token protection.

        Demonstrates handling sensitive customer data safely.
        """
        logger.info(f"Processing customer {customer_id} with operation: {operation}")
        logger.info(f"Database URL: {db_url}")  # Sanitized in logs
        logger.info(f"Data token: {data_token}")  # Sanitized in logs

        # Simulate database connection
        await asyncio.sleep(0.1)

        # Simulate customer data processing
        result = {
            "customer_id": customer_id,
            "operation": operation,
            "records_processed": 1247,
            "data_quality_score": 92.5,
            "processing_time": time.time() - self.start_time,
            "compliance_status": "GDPR_COMPLIANT"
        }

        logger.info(f"Customer data processing complete for {customer_id}")
        return result

    @protect_secrets(["openai_key", "internal_api_key", "file_path"])
    async def multi_service_workflow(
        self,
        input_file: str,
        openai_key: str,
        internal_key: str,
        workflow_type: str = "document_analysis"
    ) -> dict[str, Any]:
        """
        Complex workflow using multiple protected services.

        Demonstrates real production pattern with multiple secrets.
        """
        logger.info(f"Starting {workflow_type} workflow")
        logger.info(f"Input file: {input_file}")  # Path sanitized
        logger.info(f"OpenAI key: {openai_key}")  # Key sanitized
        logger.info(f"Internal key: {internal_key}")  # Key sanitized

        workflow_results = []

        # Step 1: File processing
        logger.info("Step 1: Processing input file")
        await asyncio.sleep(0.1)
        workflow_results.append({
            "step": "file_processing",
            "status": "completed",
            "duration_ms": 100
        })

        # Step 2: AI analysis
        logger.info("Step 2: AI analysis")
        ai_result = await self.generate_response(
            f"Analyze the content from {input_file}",
            openai_key
        )
        workflow_results.append({
            "step": "ai_analysis",
            "status": "completed",
            "duration_ms": ai_result["duration_ms"]
        })

        # Step 3: Internal service call
        logger.info("Step 3: Internal service processing")
        await asyncio.sleep(0.15)
        workflow_results.append({
            "step": "internal_service",
            "status": "completed",
            "duration_ms": 150
        })

        total_duration = sum(step["duration_ms"] for step in workflow_results)

        final_result = {
            "workflow_type": workflow_type,
            "input_file": input_file.split('/')[-1],  # Just filename for result
            "steps_completed": len(workflow_results),
            "total_duration_ms": total_duration,
            "status": "success",
            "results": workflow_results
        }

        logger.info(f"Workflow completed in {total_duration}ms")
        return final_result


# =============================================================================
# Error Handling with Secret Protection
# =============================================================================

class SecureErrorHandler:
    """Demonstrates secure error handling that protects secrets in exceptions."""

    @protect_secrets(["database_url"])
    async def risky_database_operation(self, db_url: str, query: str) -> dict[str, Any]:
        """
        Database operation that might fail with protected error messages.

        Even if exceptions occur, secrets in error messages are protected.
        """
        logger.info(f"Executing query on: {db_url}")  # URL sanitized in logs

        try:
            # Simulate database connection failure
            if "invalid" in db_url:
                raise ConnectionError(f"Cannot connect to database: {db_url}")

            # Simulate successful operation
            await asyncio.sleep(0.1)
            return {"query": query, "status": "success", "rows": 42}

        except Exception as e:
            # The exception message will have secrets sanitized automatically
            logger.error(f"Database operation failed: {e}")
            raise


# =============================================================================
# Performance Monitoring with Secret Protection
# =============================================================================

class SecurePerformanceMonitor:
    """Monitor application performance while keeping secrets safe in metrics."""

    def __init__(self):
        self.metrics = []

    @protect_secrets(["openai_key", "database_url"])
    async def benchmark_operation(
        self,
        operation_name: str,
        api_key: str,
        db_url: str,
        iterations: int = 100
    ) -> dict[str, Any]:
        """
        Benchmark operations while protecting secrets in performance logs.
        """
        logger.info(f"Benchmarking {operation_name} with {iterations} iterations")
        logger.info(f"API key: {api_key}")  # Sanitized
        logger.info(f"Database: {db_url}")  # Sanitized

        durations = []

        for i in range(iterations):
            start = time.time()

            # Simulate operation
            await asyncio.sleep(0.001)  # 1ms operation

            duration = (time.time() - start) * 1000  # Convert to ms
            durations.append(duration)

            if i % 20 == 0:  # Log progress every 20 iterations
                logger.info(f"Progress: {i}/{iterations} iterations completed")

        # Calculate statistics
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)

        benchmark_result = {
            "operation": operation_name,
            "iterations": iterations,
            "avg_duration_ms": round(avg_duration, 2),
            "min_duration_ms": round(min_duration, 2),
            "max_duration_ms": round(max_duration, 2),
            "total_time_ms": round(sum(durations), 2)
        }

        # Store metrics (secrets already sanitized)
        self.metrics.append(benchmark_result)

        logger.info(f"Benchmark complete: {avg_duration:.2f}ms average")
        return benchmark_result


# =============================================================================
# Main Production Demo
# =============================================================================

async def production_demo():
    """
    Demonstrate real-world usage patterns in production environment.
    """
    print("🏭 Production Usage Demo - Cryptex in Real Applications")
    print("=" * 60)

    # Set up mock production environment
    os.environ.setdefault("OPENAI_API_KEY", "sk-" + "prod1234567890abcdef" * 2)
    os.environ.setdefault("DATABASE_URL", "postgresql://prod:secret@db.company.com:5432/prod_db")
    os.environ.setdefault("GITHUB_TOKEN", "ghp_production1234567890abcdef1234567890abcdef12")
    os.environ.setdefault("INTERNAL_API_KEY", "ik_" + "a" * 32)
    os.environ.setdefault("CUSTOMER_DATA_TOKEN", "cdt_" + "b" * 40)

    # Initialize secure components
    ai_assistant = SecureAIAssistant()
    error_handler = SecureErrorHandler()
    monitor = SecurePerformanceMonitor()

    print("\n🤖 Demo 1: Secure AI Assistant")
    print("-" * 30)

    # AI response generation
    response1 = await ai_assistant.generate_response(
        "Explain quantum computing in simple terms",
        os.environ["OPENAI_API_KEY"]
    )
    print(f"✅ AI Response: {response1['content']}")

    # Repository analysis
    response2 = await ai_assistant.analyze_repository(
        "/Users/developer/company/critical-app",
        os.environ["GITHUB_TOKEN"],
        ["*.py", "*.yml", "*.json"]
    )
    print(f"✅ Repository Analysis: {response2['files_analyzed']} files analyzed")

    # Customer data processing
    response3 = await ai_assistant.process_customer_data(
        "customer_12345",
        os.environ["DATABASE_URL"],
        os.environ["CUSTOMER_DATA_TOKEN"],
        "compliance_check"
    )
    print(f"✅ Customer Processing: {response3['records_processed']} records")

    # Multi-service workflow
    response4 = await ai_assistant.multi_service_workflow(
        "/Users/developer/company/sensitive_document.pdf",
        os.environ["OPENAI_API_KEY"],
        os.environ["INTERNAL_API_KEY"],
        "security_audit"
    )
    print(f"✅ Multi-Service Workflow: {response4['steps_completed']} steps in {response4['total_duration_ms']}ms")

    print("\n🛡️ Demo 2: Secure Error Handling")
    print("-" * 30)

    # Successful operation
    try:
        result = await error_handler.risky_database_operation(
            os.environ["DATABASE_URL"],
            "SELECT * FROM secure_table"
        )
        print(f"✅ Successful operation: {result['rows']} rows")
    except Exception as e:
        print(f"❌ Operation failed: {e}")

    # Failed operation (secrets still protected in error)
    try:
        await error_handler.risky_database_operation(
            "postgresql://invalid:secret@badhost:5432/invalid_db",
            "SELECT * FROM nonexistent"
        )
    except Exception as e:
        print(f"❌ Expected failure (secrets protected): {type(e).__name__}")

    print("\n📊 Demo 3: Performance Monitoring")
    print("-" * 30)

    # Benchmark with secret protection
    benchmark1 = await monitor.benchmark_operation(
        "api_call_simulation",
        os.environ["OPENAI_API_KEY"],
        os.environ["DATABASE_URL"],
        50  # Reduced for demo
    )
    print(f"✅ Benchmark: {benchmark1['avg_duration_ms']}ms average over {benchmark1['iterations']} iterations")

    print("\n" + "=" * 60)
    print("🎉 Production Demo Complete!")
    print("\n💡 Key Production Benefits:")
    print("   🔒 All secrets automatically sanitized in logs")
    print("   ⚡ Zero performance impact on business logic")
    print("   🛡️ Exception messages safely cleaned")
    print("   📊 Metrics and monitoring remain functional")
    print("   🏗️ Simple integration with existing code")
    print("   🎯 Works with any framework or standalone functions")
    print("=" * 60)


# =============================================================================
# Context Manager Demo (Advanced Usage)
# =============================================================================

async def context_manager_demo():
    """
    Demonstrate advanced usage with secure_session context manager.
    """
    print("\n🔧 Advanced: Context Manager Usage")
    print("-" * 40)

    if secure_session is None:
        print("❌ secure_session not available in this version - skipping demo")
        return

    # Using secure_session for fine-grained control
    async with secure_session() as session:
        # Original data with secrets
        sensitive_request = {
            "user_id": "user_123",
            "api_key": os.environ["OPENAI_API_KEY"],
            "database_url": os.environ["DATABASE_URL"],
            "file_path": "/Users/developer/company/financial_data.xlsx",
            "query": "Process Q4 earnings report"
        }

        print("📝 Original request contains real secrets")

        # Sanitize for AI processing (simplified demo)
        sanitized_request = dict(sensitive_request)
        for key, value in sanitized_request.items():
            if key == "api_key" and value.startswith("sk-"):
                sanitized_request[key] = "{{OPENAI_API_KEY}}"
            elif key == "database_url" and "postgresql://" in value:
                sanitized_request[key] = "{{DATABASE_URL}}"
            elif key == "file_path" and value.startswith("/"):
                sanitized_request[key] = value.replace("/Users/developer", "/{USER_HOME}")
        
        print(f"🤖 AI sees sanitized data: {sanitized_request}")

        # AI processing happens here with safe data
        ai_instructions = f"Process this request: {sanitized_request}"
        print(f"🧠 AI processing: {ai_instructions[:60]}...")

        # Function execution uses real values from original request
        print("🔧 Function gets real values for execution")

    print("✅ Context manager demo complete")


if __name__ == "__main__":
    asyncio.run(production_demo())
    asyncio.run(context_manager_demo())
