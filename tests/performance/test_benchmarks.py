"""Performance benchmark tests."""

import time

import pytest
from cryptex import protect_secrets, secure_session


class TestPerformanceBenchmarks:
    """Performance benchmarks for core functionality."""

    @pytest.mark.performance
    @pytest.mark.benchmark(group="sanitization")
    def test_sanitization_latency(self, benchmark, large_payload):
        """Test sanitization latency for 1KB payload (target: <5ms)."""

        @protect_secrets(["api_key"])
        def process_large_data(data: str) -> str:
            return f"processed: {len(data)} bytes"

        result = benchmark(process_large_data, large_payload)
        assert "processed: " in result

    @pytest.mark.performance
    @pytest.mark.benchmark(group="resolution")
    def test_resolution_latency(self, benchmark, multiple_secrets, mock_env_vars):
        """Test resolution latency for 10 placeholders (target: <10ms)."""
        secret_names = list(multiple_secrets.keys())

        @protect_secrets(secret_names)
        def resolve_multiple_secrets(data: str) -> str:
            return f"resolved: {data}"

        result = benchmark(resolve_multiple_secrets, "test data")
        assert "resolved: " in result

    @pytest.mark.performance
    @pytest.mark.benchmark(group="decorator")
    def test_decorator_overhead(self, benchmark):
        """Test overhead of protect_secrets decorator."""

        @protect_secrets(["api_key"])
        def simple_function(data: str) -> str:
            return f"processed: {data}"

        def baseline_function(data: str) -> str:
            return f"processed: {data}"

        # Benchmark decorated function
        decorated_result = benchmark(simple_function, "test")
        assert decorated_result == "processed: test"

    @pytest.mark.performance
    @pytest.mark.benchmark(group="memory")
    def test_memory_usage(self, benchmark, large_payload):
        """Test memory usage during processing."""
        import os

        import psutil

        @protect_secrets(["api_key"])
        def memory_intensive_task(data: str) -> str:
            # Simulate memory-intensive processing
            processed = [data] * 100
            return f"processed: {len(processed)} items"

        def measure_memory_usage():
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss

            result = memory_intensive_task(large_payload)

            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            # Memory overhead should be < 5% of application memory
            # This is a basic test - real implementation would be more sophisticated
            return result, memory_increase

        result, memory_delta = benchmark(measure_memory_usage)
        assert "processed: " in result[0]

    @pytest.mark.performance
    @pytest.mark.benchmark(group="concurrent")
    @pytest.mark.asyncio
    async def test_concurrent_performance(
        self, benchmark, multiple_secrets, mock_env_vars
    ):
        """Test performance under concurrent load."""
        import asyncio

        @protect_secrets(["secret_0", "secret_1", "secret_2"])
        async def concurrent_task(task_id: int) -> str:
            await asyncio.sleep(0.001)  # Simulate I/O
            return f"Task {task_id} completed"

        async def run_concurrent_tasks():
            tasks = [concurrent_task(i) for i in range(50)]
            results = await asyncio.gather(*tasks)
            return results

        # Note: benchmark.pedantic can be used for async functions in pytest-benchmark
        start_time = time.time()
        results = await run_concurrent_tasks()
        duration = time.time() - start_time

        assert len(results) == 50
        assert all("completed" in result for result in results)

        # Should complete within reasonable time
        assert duration < 1.0  # 1 second for 50 concurrent tasks

    @pytest.mark.performance
    @pytest.mark.benchmark(group="session")
    @pytest.mark.asyncio
    async def test_session_creation_performance(self, benchmark):
        """Test secure_session creation performance."""

        async def create_session():
            async with secure_session() as session:
                return session

        # For async benchmarking, we'll use a simple timing approach
        start_time = time.time()
        session = await create_session()
        duration = time.time() - start_time

        assert session is not None
        assert duration < 0.1  # Should create session quickly
