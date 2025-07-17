"""
Core Temporal Isolation Engine for Cryptex middleware.

This module implements the fundamental engine that powers secret isolation
in middleware deployments for FastMCP servers and FastAPI applications.
"""

import asyncio
import hashlib
import re
import threading
import time
import uuid
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from re import Pattern
from typing import Any

from .exceptions import (
    ContextError,
    PerformanceError,
    ResolutionError,
    SanitizationError,
    context_not_found_error,
    resolution_timeout_error,
    sanitization_timeout_error,
)


class ReadWriteLock:
    """
    A reader-writer lock implementation for better cache concurrency.

    Allows multiple concurrent readers but exclusive writers.
    """

    def __init__(self):
        self._readers = 0
        self._writers = 0
        self._read_ready = threading.Condition(threading.RLock())
        self._write_ready = threading.Condition(threading.RLock())

    def acquire_read(self):
        """Acquire a read lock."""
        with self._read_ready:
            while self._writers > 0:
                self._read_ready.wait()
            self._readers += 1

    def release_read(self):
        """Release a read lock."""
        with self._read_ready:
            self._readers -= 1
            if self._readers == 0:
                self._read_ready.notify_all()

    def acquire_write(self):
        """Acquire a write lock."""
        with self._write_ready:
            while self._writers > 0 or self._readers > 0:
                self._write_ready.wait()
            self._writers += 1

    def release_write(self):
        """Release a write lock."""
        with self._write_ready:
            self._writers -= 1
            self._write_ready.notify_all()

        # Notify readers separately to avoid lock ordering issues
        with self._read_ready:
            self._read_ready.notify_all()

    def __enter__(self):
        """Context manager for write lock."""
        self.acquire_write()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager for write lock."""
        self.release_write()


class ReadLockContext:
    """Context manager for read locks."""

    def __init__(self, lock: ReadWriteLock):
        self.lock = lock

    def __enter__(self):
        self.lock.acquire_read()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lock.release_read()


@dataclass
class SecretPattern:
    """Definition of a secret pattern for detection and replacement."""

    name: str
    pattern: Pattern[str]
    placeholder_template: str
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SecretPattern":
        """Create SecretPattern from dictionary configuration."""
        return cls(
            name=data["name"],
            pattern=re.compile(data["pattern"]),
            placeholder_template=data["template"],
            description=data.get("description", ""),
        )


@dataclass
class DetectedSecret:
    """A secret that was detected in data."""

    value: str
    pattern_name: str
    placeholder: str
    start_pos: int = -1
    end_pos: int = -1


@dataclass
class SanitizedData:
    """Data with secrets replaced by placeholders."""

    data: Any
    placeholders: dict[str, str] = field(
        default_factory=dict
    )  # placeholder -> real_value
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)

    def get_real_value(self, placeholder: str) -> str | None:
        """Get the real value for a placeholder."""
        return self.placeholders.get(placeholder)


@dataclass
class ResolvedData:
    """Data with placeholders resolved back to real values."""

    data: Any
    resolved_count: int = 0
    context_id: str = ""


class TemporalIsolationEngine:
    """
    Core engine for temporal isolation of secrets in middleware.

    Implements the three-phase security architecture:
    1. Sanitization: Convert secrets to {RESOLVE:SECRET_TYPE:HASH} placeholders
    2. AI Processing: AI sees placeholders, never real secrets
    3. Resolution: Convert placeholders back to real values for execution
    """

    def __init__(
        self,
        patterns: list[SecretPattern] | None = None,
        max_cache_size: int = 1000,
        max_cache_age: int = 3600,
        enable_background_cleanup: bool = True,
        max_data_size: int = 10 * 1024 * 1024,  # 10MB default limit
        max_string_length: int = 1024 * 1024,  # 1MB per string
    ):
        """
        Initialize the isolation engine.

        Args:
            patterns: List of secret patterns to detect. Uses defaults if None.
            max_cache_size: Maximum number of contexts to cache (LRU eviction)
            max_cache_age: Maximum age of cached contexts in seconds
            enable_background_cleanup: Whether to run background cache cleanup
            max_data_size: Maximum size in bytes for input data (DoS protection)
            max_string_length: Maximum length for individual strings (DoS protection)
        """
        self.patterns = patterns or self._get_default_patterns()

        # Pre-compile regex patterns for better performance
        self._compiled_patterns: dict[str, Pattern[str]] = {}
        self._compile_patterns()

        self._context_cache: OrderedDict[str, SanitizedData] = OrderedDict()
        self._max_cache_size = max_cache_size
        self._max_cache_age = max_cache_age
        self._cache_lock = ReadWriteLock()  # Reader-writer lock for better concurrency
        self._cleanup_task: asyncio.Task | None = None
        self._enable_background_cleanup = enable_background_cleanup
        self._last_access_times: dict[str, float] = {}

        # Input validation limits for DoS protection
        self._max_data_size = max_data_size
        self._max_string_length = max_string_length

        # Performance monitoring
        self._performance_metrics = {
            "sanitization_calls": 0,
            "resolution_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "secrets_detected": 0,
            "total_sanitization_time": 0.0,
            "total_resolution_time": 0.0,
            "avg_sanitization_time": 0.0,
            "avg_resolution_time": 0.0,
            "performance_violations": 0,
        }
        self._performance_callbacks: list[Callable] = []

        # Background cleanup will be started when first needed (lazy initialization)

    def _compile_patterns(self) -> None:
        """
        Pre-compile regex patterns for better performance.

        This method compiles all regex patterns once during initialization
        to avoid recompilation during runtime pattern matching.
        """
        self._compiled_patterns.clear()

        for pattern in self.patterns:
            try:
                # Use the already compiled pattern from SecretPattern
                self._compiled_patterns[pattern.name] = pattern.pattern
            except Exception as e:
                # If pattern compilation fails, log error but continue
                import logging

                logging.getLogger(__name__).warning(
                    f"Failed to compile pattern '{pattern.name}': {e}"
                )

    def add_pattern(self, pattern: SecretPattern) -> None:
        """
        Add a new secret pattern and compile it.

        Args:
            pattern: SecretPattern to add
        """
        self.patterns.append(pattern)
        try:
            self._compiled_patterns[pattern.name] = pattern.pattern
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(
                f"Failed to compile new pattern '{pattern.name}': {e}"
            )

    def remove_pattern(self, pattern_name: str) -> bool:
        """
        Remove a pattern by name.

        Args:
            pattern_name: Name of pattern to remove

        Returns:
            True if pattern was found and removed, False otherwise
        """
        # Remove from patterns list
        original_count = len(self.patterns)
        self.patterns = [p for p in self.patterns if p.name != pattern_name]

        # Remove from compiled patterns
        self._compiled_patterns.pop(pattern_name, None)

        return len(self.patterns) < original_count

    def _validate_input_size(self, data: Any) -> None:
        """
        Validate input data size to prevent DoS attacks.

        Args:
            data: Input data to validate

        Raises:
            SanitizationError: If input exceeds size limits
        """
        import sys

        # Calculate approximate size of the data
        data_size = sys.getsizeof(data)

        # Check total data size
        if data_size > self._max_data_size:
            raise SanitizationError(
                f"Input data size {data_size} bytes exceeds maximum limit of {self._max_data_size} bytes",
                details={
                    "data_size": data_size,
                    "max_size": self._max_data_size,
                    "suggestion": "Reduce input data size or increase max_data_size limit",
                },
            )

        # Recursively check string lengths
        self._validate_string_lengths(data)

    def _validate_string_lengths(self, data: Any, path: str = "root") -> None:
        """
        Recursively validate string lengths in data structure.

        Args:
            data: Data to validate
            path: Current path in data structure for error reporting

        Raises:
            SanitizationError: If any string exceeds length limit
        """
        if isinstance(data, str):
            if len(data) > self._max_string_length:
                raise SanitizationError(
                    f"String at {path} length {len(data)} exceeds maximum limit of {self._max_string_length}",
                    details={
                        "path": path,
                        "string_length": len(data),
                        "max_length": self._max_string_length,
                        "suggestion": "Reduce string length or increase max_string_length limit",
                    },
                )
        elif isinstance(data, dict):
            for key, value in data.items():
                self._validate_string_lengths(value, f"{path}.{key}")
        elif isinstance(data, list | tuple):
            for i, item in enumerate(data):
                self._validate_string_lengths(item, f"{path}[{i}]")
        elif hasattr(data, "__dict__"):
            # Handle custom objects
            self._validate_string_lengths(data.__dict__, f"{path}.__dict__")

    def _get_default_patterns(self) -> list[SecretPattern]:
        """Get default secret patterns for common use cases."""
        return [
            SecretPattern(
                name="openai_key",
                pattern=re.compile(r"sk-[a-zA-Z0-9]{48}"),
                placeholder_template="{{OPENAI_API_KEY}}",
                description="OpenAI API key",
            ),
            SecretPattern(
                name="anthropic_key",
                pattern=re.compile(r"sk-ant-[a-zA-Z0-9-]{95}"),
                placeholder_template="{{ANTHROPIC_API_KEY}}",
                description="Anthropic API key",
            ),
            SecretPattern(
                name="github_token",
                pattern=re.compile(r"ghp_[a-zA-Z0-9]{36}"),
                placeholder_template="{{GITHUB_TOKEN}}",
                description="GitHub personal access token",
            ),
            SecretPattern(
                name="file_path",
                pattern=re.compile(r"/(?:Users|home)/[^/\s]+(?:/[^/\s]*)*"),
                placeholder_template="/{USER_HOME}/...",
                description="User file system paths",
            ),
            SecretPattern(
                name="database_url",
                pattern=re.compile(r"(?:postgres|mysql|redis|mongodb)://[^\s]+"),
                placeholder_template="{{DATABASE_URL}}",
                description="Database connection URLs",
            ),
        ]

    async def sanitize_for_ai(
        self, data: Any, context_id: str | None = None
    ) -> SanitizedData:
        """
        Sanitize data for AI processing by replacing secrets with placeholders.

        Args:
            data: Raw data that may contain secrets
            context_id: Optional context ID for tracking

        Returns:
            SanitizedData with secrets replaced by placeholders

        Raises:
            SanitizationError: If data cannot be sanitized or exceeds size limits
            PerformanceError: If sanitization exceeds performance thresholds
        """
        start_time = time.time()

        if context_id is None:
            context_id = str(uuid.uuid4())

        try:
            # Validate input size to prevent DoS attacks
            self._validate_input_size(data)
            # Start background cleanup if not already running
            self._start_background_cleanup()

            # Clean expired cache entries
            await self._clean_expired_cache()

            # Detect secrets in the data
            detected_secrets = await self._detect_secrets(data)

            if not detected_secrets:
                # No secrets found, return data as-is
                return SanitizedData(data=data, context_id=context_id)

            # Replace secrets with placeholders
            sanitized_data, placeholders = await self._replace_with_placeholders(
                data, detected_secrets
            )

            # Create sanitized data object
            result = SanitizedData(
                data=sanitized_data, placeholders=placeholders, context_id=context_id
            )

            # Cache the context for later resolution with LRU management
            self._cache_context(context_id, result)

            # Update performance metrics
            duration_ms = (time.time() - start_time) * 1000
            self._update_sanitization_metrics(duration_ms, len(detected_secrets))

            # Check performance threshold
            if duration_ms > 5.0:  # 5ms threshold
                self._performance_metrics["performance_violations"] += 1
                await self._trigger_performance_callbacks(
                    "sanitization_timeout",
                    {
                        "duration_ms": duration_ms,
                        "threshold_ms": 5.0,
                        "context_id": context_id,
                    },
                )
                raise sanitization_timeout_error(duration_ms, 5.0)

            return result

        except Exception as e:
            if isinstance(e, SanitizationError | PerformanceError):
                raise

            # Wrap unexpected errors
            raise SanitizationError(
                f"Failed to sanitize data: {str(e)}",
                context_id=context_id,
                details={"data_type": type(data).__name__, "error": str(e)},
                cause=e,
            ) from e

    async def resolve_for_execution(self, data: Any, context_id: str) -> ResolvedData:
        """
        Resolve placeholders back to real values for tool execution.

        Args:
            data: Data containing placeholders to resolve
            context_id: Context ID to look up placeholder mappings

        Returns:
            ResolvedData with placeholders replaced by real values

        Raises:
            ContextError: If context not found or expired
            ResolutionError: If placeholder resolution fails
            PerformanceError: If resolution exceeds performance thresholds
        """
        start_time = time.time()

        try:
            # Get the sanitized context with access tracking
            sanitized_context = self._get_cached_context(context_id)
            if not sanitized_context:
                raise context_not_found_error(context_id)

            # Resolve placeholders in the data
            resolved_data, resolved_count = await self._resolve_placeholders(
                data, sanitized_context.placeholders
            )

            # Update performance metrics
            duration_ms = (time.time() - start_time) * 1000
            self._update_resolution_metrics(duration_ms, resolved_count)

            # Check performance threshold
            if duration_ms > 10.0:  # 10ms threshold
                self._performance_metrics["performance_violations"] += 1
                await self._trigger_performance_callbacks(
                    "resolution_timeout",
                    {
                        "duration_ms": duration_ms,
                        "threshold_ms": 10.0,
                        "context_id": context_id,
                        "resolved_count": resolved_count,
                    },
                )
                raise resolution_timeout_error(duration_ms, 10.0)

            return ResolvedData(
                data=resolved_data, resolved_count=resolved_count, context_id=context_id
            )

        except Exception as e:
            if isinstance(e, ContextError | ResolutionError | PerformanceError):
                raise

            # Wrap unexpected errors
            raise ResolutionError(
                f"Failed to resolve placeholders: {str(e)}",
                context_id=context_id,
                details={"data_type": type(data).__name__, "error": str(e)},
                cause=e,
            ) from e

    async def sanitize_response(self, response: Any, context_id: str) -> Any:
        """
        Sanitize response data to ensure no secrets leak back to AI.

        Args:
            response: Response data from tool execution
            context_id: Context ID for placeholder mappings

        Returns:
            Sanitized response safe for AI consumption
        """
        sanitized_context = self._get_cached_context(context_id)
        if not sanitized_context:
            # No context found, scan for secrets anyway
            result = await self.sanitize_for_ai(response)
            return result.data

        # Replace any real values that might have leaked into response
        sanitized_response = await self._replace_real_values_with_placeholders(
            response, sanitized_context.placeholders
        )

        return sanitized_response

    async def _detect_secrets(self, data: Any) -> list[DetectedSecret]:
        """Detect secrets in various data types."""
        detected_secrets = []

        if isinstance(data, str):
            detected_secrets.extend(await self._detect_secrets_in_string(data))
        elif isinstance(data, dict):
            detected_secrets.extend(await self._detect_secrets_in_dict(data))
        elif isinstance(data, list | tuple):
            detected_secrets.extend(await self._detect_secrets_in_list(data))
        elif hasattr(data, "__dict__"):
            # Handle custom objects
            detected_secrets.extend(await self._detect_secrets_in_dict(data.__dict__))

        return detected_secrets

    async def _detect_secrets_in_string(self, text: str) -> list[DetectedSecret]:
        """Detect secrets in a string using pre-compiled patterns."""
        detected = []

        for pattern in self.patterns:
            # Use pre-compiled pattern for better performance
            compiled_pattern = self._compiled_patterns.get(pattern.name)
            if not compiled_pattern:
                # Fallback to pattern.pattern if not in compiled cache
                compiled_pattern = pattern.pattern

            for match in compiled_pattern.finditer(text):
                placeholder = self._generate_placeholder(
                    match.group(), pattern.name, pattern.placeholder_template
                )

                detected.append(
                    DetectedSecret(
                        value=match.group(),
                        pattern_name=pattern.name,
                        placeholder=placeholder,
                        start_pos=match.start(),
                        end_pos=match.end(),
                    )
                )

        return detected

    async def _detect_secrets_in_dict(
        self, data: dict[str, Any]
    ) -> list[DetectedSecret]:
        """Detect secrets in a dictionary."""
        detected = []

        for _key, value in data.items():
            if isinstance(value, str):
                detected.extend(await self._detect_secrets_in_string(value))
            elif isinstance(value, dict | list | tuple):
                detected.extend(await self._detect_secrets(value))

        return detected

    async def _detect_secrets_in_list(self, data: list[Any]) -> list[DetectedSecret]:
        """Detect secrets in a list."""
        detected = []

        for item in data:
            detected.extend(await self._detect_secrets(item))

        return detected

    def _generate_placeholder(
        self, secret_value: str, pattern_name: str, template: str
    ) -> str:
        """Generate a unique placeholder for a secret value."""
        # Create a hash of the secret for uniqueness
        secret_hash = hashlib.sha256(secret_value.encode()).hexdigest()[:8]

        # Use template if it contains placeholders, otherwise use default format
        if "{{" in template and "}}" in template:
            return template
        else:
            return f"{{RESOLVE:{pattern_name.upper()}:{secret_hash}}}"

    async def _replace_with_placeholders(
        self, data: Any, secrets: list[DetectedSecret]
    ) -> tuple[Any, dict[str, str]]:
        """Replace detected secrets with placeholders using optimized algorithm."""
        if not secrets:
            return data, {}

        placeholders = {}

        if isinstance(data, str):
            # Optimized single-pass replacement for strings
            sanitized_data = self._replace_secrets_in_string(
                data, secrets, placeholders
            )
            return sanitized_data, placeholders

        elif isinstance(data, dict):
            sanitized_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    # Find relevant secrets for this specific string value
                    relevant_secrets = self._find_relevant_secrets(value, secrets)
                    if relevant_secrets:
                        sanitized_value = self._replace_secrets_in_string(
                            value, relevant_secrets, placeholders
                        )
                        sanitized_data[key] = sanitized_value
                    else:
                        sanitized_data[key] = value
                elif isinstance(value, dict | list | tuple):
                    # Recursively handle nested structures
                    (
                        sanitized_value,
                        nested_placeholders,
                    ) = await self._replace_with_placeholders(value, secrets)
                    sanitized_data[key] = sanitized_value
                    placeholders.update(nested_placeholders)
                else:
                    sanitized_data[key] = value
            return sanitized_data, placeholders

        elif isinstance(data, list | tuple):
            sanitized_data = []
            for item in data:
                if isinstance(item, str):
                    # Find relevant secrets for this specific string item
                    relevant_secrets = self._find_relevant_secrets(item, secrets)
                    if relevant_secrets:
                        sanitized_item = self._replace_secrets_in_string(
                            item, relevant_secrets, placeholders
                        )
                        sanitized_data.append(sanitized_item)
                    else:
                        sanitized_data.append(item)
                elif isinstance(item, dict | list | tuple):
                    # Recursively handle nested structures
                    (
                        sanitized_item,
                        nested_placeholders,
                    ) = await self._replace_with_placeholders(item, secrets)
                    sanitized_data.append(sanitized_item)
                    placeholders.update(nested_placeholders)
                else:
                    sanitized_data.append(item)
            return sanitized_data, placeholders

        return data, {}

    async def _resolve_placeholders(
        self, data: Any, placeholder_map: dict[str, str]
    ) -> tuple[Any, int]:
        """Resolve placeholders back to real values."""
        resolved_count = 0

        if isinstance(data, str):
            resolved_data = data
            for placeholder, real_value in placeholder_map.items():
                if placeholder in resolved_data:
                    resolved_data = resolved_data.replace(placeholder, real_value)
                    resolved_count += 1
            return resolved_data, resolved_count

        elif isinstance(data, dict):
            resolved_data = {}
            for key, value in data.items():
                resolved_value, count = await self._resolve_placeholders(
                    value, placeholder_map
                )
                resolved_data[key] = resolved_value
                resolved_count += count
            return resolved_data, resolved_count

        elif isinstance(data, list | tuple):
            resolved_data = []
            for item in data:
                resolved_item, count = await self._resolve_placeholders(
                    item, placeholder_map
                )
                resolved_data.append(resolved_item)
                resolved_count += count
            return resolved_data, resolved_count

        return data, resolved_count

    async def _replace_real_values_with_placeholders(
        self, data: Any, placeholder_map: dict[str, str]
    ) -> Any:
        """Replace any real values that leaked into response with placeholders."""
        if isinstance(data, str):
            sanitized = data
            for placeholder, real_value in placeholder_map.items():
                if real_value in sanitized:
                    sanitized = sanitized.replace(real_value, placeholder)
            return sanitized

        elif isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                sanitized[key] = await self._replace_real_values_with_placeholders(
                    value, placeholder_map
                )
            return sanitized

        elif isinstance(data, list | tuple):
            sanitized = []
            for item in data:
                sanitized.append(
                    await self._replace_real_values_with_placeholders(
                        item, placeholder_map
                    )
                )
            return sanitized

        return data

    def _find_relevant_secrets(
        self, text: str, secrets: list[DetectedSecret]
    ) -> list[DetectedSecret]:
        """Find secrets that are actually present in the given text."""
        relevant = []
        for secret in secrets:
            if secret.value in text:
                relevant.append(secret)
        return relevant

    def _replace_secrets_in_string(
        self, text: str, secrets: list[DetectedSecret], placeholders: dict[str, str]
    ) -> str:
        """
        Optimized single-pass replacement of secrets in a string.

        Uses sorted positions to ensure correct replacement without position shifts.
        """
        if not secrets:
            return text

        # Build a list of all replacement positions
        replacements = []
        for secret in secrets:
            # Find all occurrences of this secret in the text
            start = 0
            while True:
                pos = text.find(secret.value, start)
                if pos == -1:
                    break
                replacements.append((pos, pos + len(secret.value), secret.placeholder))
                placeholders[secret.placeholder] = secret.value
                start = pos + 1

        # Sort replacements by position in reverse order
        replacements.sort(key=lambda x: x[0], reverse=True)

        # Apply replacements from end to beginning to maintain positions
        result = text
        for start_pos, end_pos, placeholder in replacements:
            result = result[:start_pos] + placeholder + result[end_pos:]

        return result

    def _start_background_cleanup(self) -> None:
        """Start background cache cleanup task if event loop is available."""
        if not self._enable_background_cleanup:
            return

        try:
            # Only start if we have a running event loop
            loop = asyncio.get_running_loop()
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = loop.create_task(self._background_cleanup_loop())
        except RuntimeError:
            # No event loop running, background cleanup will start later
            pass

    async def _background_cleanup_loop(self) -> None:
        """Background task to periodically clean expired cache entries."""
        cleanup_interval = min(
            300, self._max_cache_age // 6
        )  # Clean every 5 minutes or 1/6 of max age

        while True:
            try:
                await asyncio.sleep(cleanup_interval)
                await self._clean_expired_cache()
                self._enforce_cache_size_limit()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue cleanup loop
                import logging

                logging.getLogger(__name__).warning(f"Cache cleanup error: {e}")

    def _cache_context(self, context_id: str, context: SanitizedData) -> None:
        """Cache a context with LRU eviction using write lock."""
        with self._cache_lock:  # Write lock for cache modification
            # Remove if already exists (to update position)
            if context_id in self._context_cache:
                del self._context_cache[context_id]

            # Add to end (most recently used)
            self._context_cache[context_id] = context
            self._last_access_times[context_id] = time.time()

            # Enforce size limit
            self._enforce_cache_size_limit()

    def _get_cached_context(self, context_id: str) -> SanitizedData | None:
        """Get a cached context and update access time (LRU)."""
        # First try to get with read lock
        with ReadLockContext(self._cache_lock):
            context = self._context_cache.get(context_id)
            if context:
                # Update metrics immediately
                self._performance_metrics["cache_hits"] += 1
            else:
                self._performance_metrics["cache_misses"] += 1
                return None

        # If found, update access time with write lock
        if context:
            with self._cache_lock:  # Write lock for LRU update
                # Double-check the context still exists
                if context_id in self._context_cache:
                    # Move to end (mark as recently used)
                    del self._context_cache[context_id]
                    self._context_cache[context_id] = context
                    self._last_access_times[context_id] = time.time()
                    return context

        return None

    def _enforce_cache_size_limit(self) -> None:
        """Enforce cache size limit by evicting least recently used entries."""
        while len(self._context_cache) > self._max_cache_size:
            # Remove oldest entry (least recently used)
            oldest_context_id, _ = self._context_cache.popitem(last=False)
            self._last_access_times.pop(oldest_context_id, None)

    async def _clean_expired_cache(self) -> None:
        """Remove expired contexts from cache."""
        current_time = time.time()

        with self._cache_lock:  # Write lock for cache modification
            expired_keys = [
                context_id
                for context_id, context in self._context_cache.items()
                if current_time - context.created_at > self._max_cache_age
            ]

            for key in expired_keys:
                del self._context_cache[key]
                self._last_access_times.pop(key, None)

    def clear_context(self, context_id: str) -> bool:
        """
        Manually clear a context from cache.

        Args:
            context_id: Context ID to remove

        Returns:
            True if context was found and removed, False otherwise
        """
        with self._cache_lock:  # Write lock for cache modification
            context_existed = self._context_cache.pop(context_id, None) is not None
            self._last_access_times.pop(context_id, None)
            return context_existed

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics for monitoring."""
        with ReadLockContext(self._cache_lock):  # Read lock for stats
            current_time = time.time()

            # Calculate age distribution
            ages = [
                current_time - context.created_at
                for context in self._context_cache.values()
            ]
            avg_age = sum(ages) / len(ages) if ages else 0

            return {
                "cached_contexts": len(self._context_cache),
                "max_cache_size": self._max_cache_size,
                "cache_utilization": len(self._context_cache) / self._max_cache_size,
                "max_cache_age": self._max_cache_age,
                "average_context_age": avg_age,
                "patterns_loaded": len(self.patterns),
                "background_cleanup_enabled": self._enable_background_cleanup,
                "cleanup_task_active": self._cleanup_task is not None
                and not self._cleanup_task.done(),
            }

    def stop_background_cleanup(self) -> None:
        """Stop the background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

    def clear_all_contexts(self) -> int:
        """
        Clear all cached contexts.

        Returns:
            Number of contexts that were cleared
        """
        with self._cache_lock:  # Write lock for cache modification
            count = len(self._context_cache)
            self._context_cache.clear()
            self._last_access_times.clear()
            return count

    # Performance monitoring methods

    def add_performance_callback(
        self, callback: Callable[[str, dict[str, Any]], None]
    ) -> None:
        """
        Add a callback function for performance monitoring events.

        Args:
            callback: Function to call with (event_type, event_data) parameters
        """
        self._performance_callbacks.append(callback)

    def remove_performance_callback(self, callback: Callable) -> bool:
        """
        Remove a performance callback.

        Args:
            callback: The callback function to remove

        Returns:
            True if callback was found and removed, False otherwise
        """
        try:
            self._performance_callbacks.remove(callback)
            return True
        except ValueError:
            return False

    async def _trigger_performance_callbacks(
        self, event_type: str, event_data: dict[str, Any]
    ) -> None:
        """Trigger all registered performance callbacks."""
        for callback in self._performance_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, event_data)
                else:
                    callback(event_type, event_data)
            except Exception as e:
                # Log callback errors but don't fail the operation
                import logging

                logging.getLogger(__name__).warning(f"Performance callback failed: {e}")

    def _update_sanitization_metrics(
        self, duration_ms: float, secrets_count: int
    ) -> None:
        """Update sanitization performance metrics."""
        self._performance_metrics["sanitization_calls"] += 1
        self._performance_metrics["secrets_detected"] += secrets_count
        self._performance_metrics["total_sanitization_time"] += duration_ms

        # Update average
        calls = self._performance_metrics["sanitization_calls"]
        total_time = self._performance_metrics["total_sanitization_time"]
        self._performance_metrics["avg_sanitization_time"] = total_time / calls

    def _update_resolution_metrics(
        self, duration_ms: float, resolved_count: int
    ) -> None:
        """Update resolution performance metrics."""
        self._performance_metrics["resolution_calls"] += 1
        self._performance_metrics["total_resolution_time"] += duration_ms

        # Update average
        calls = self._performance_metrics["resolution_calls"]
        total_time = self._performance_metrics["total_resolution_time"]
        self._performance_metrics["avg_resolution_time"] = total_time / calls

    def get_performance_metrics(self) -> dict[str, Any]:
        """
        Get comprehensive performance metrics.

        Returns:
            Dictionary containing all performance metrics and statistics
        """
        cache_stats = self.get_cache_stats()

        # Calculate additional derived metrics
        total_calls = (
            self._performance_metrics["sanitization_calls"]
            + self._performance_metrics["resolution_calls"]
        )

        cache_hit_rate = 0.0
        if (
            self._performance_metrics["cache_hits"]
            + self._performance_metrics["cache_misses"]
        ) > 0:
            total_cache_ops = (
                self._performance_metrics["cache_hits"]
                + self._performance_metrics["cache_misses"]
            )
            cache_hit_rate = self._performance_metrics["cache_hits"] / total_cache_ops

        return {
            **self._performance_metrics,
            "cache_stats": cache_stats,
            "total_operations": total_calls,
            "cache_hit_rate": cache_hit_rate,
            "performance_violation_rate": (
                self._performance_metrics["performance_violations"] / total_calls
                if total_calls > 0
                else 0.0
            ),
            "avg_secrets_per_sanitization": (
                self._performance_metrics["secrets_detected"]
                / self._performance_metrics["sanitization_calls"]
                if self._performance_metrics["sanitization_calls"] > 0
                else 0.0
            ),
        }

    def reset_performance_metrics(self) -> None:
        """Reset all performance metrics to zero."""
        for key in self._performance_metrics:
            if isinstance(self._performance_metrics[key], int | float):
                self._performance_metrics[key] = (
                    0 if isinstance(self._performance_metrics[key], int) else 0.0
                )

    async def sanitize_traceback(self, error: Exception) -> Exception:
        """
        Sanitize exception traceback to prevent secret exposure.

        Creates a new exception with sanitized traceback frames that removes
        sensitive information like file paths, local variables, and code context.

        Args:
            error: Original exception with potentially sensitive traceback

        Returns:
            New exception with sanitized traceback
        """
        import traceback

        # Get the original traceback
        original_tb = error.__traceback__
        if not original_tb:
            return error

        # Extract traceback information
        tb_lines = traceback.format_exception(type(error), error, original_tb)

        # Sanitize each line of the traceback
        sanitized_lines = []
        for line in tb_lines:
            # Sanitize file paths and sensitive content
            sanitized_line = await self._sanitize_traceback_line(line)
            sanitized_lines.append(sanitized_line)

        # Create new exception with sanitized message
        if sanitized_lines:
            sanitized_message = sanitized_lines[-1].strip()  # Only keep the exception message
            # Additional sanitization for error message content
            import re
            # Remove specific line numbers from error messages
            sanitized_message = re.sub(r"line \d+", "line <redacted>", sanitized_message)
            # Apply general sanitization to the error message
            error_data = await self.sanitize_for_ai(sanitized_message)
            sanitized_message = error_data.data
        else:
            sanitized_message = str(error)

        sanitized_error = type(error)(sanitized_message)

        # Don't preserve the original traceback - create a clean one
        # This prevents any potential information leakage through frame objects

        return sanitized_error

    async def _sanitize_traceback_line(self, line: str) -> str:
        """Sanitize a single traceback line to remove sensitive information."""
        # Sanitize the line using our standard sanitization
        sanitized_data = await self.sanitize_for_ai(line)
        sanitized_line = sanitized_data.data

        # Additional traceback-specific sanitization
        import re

        # Replace absolute paths with relative paths
        sanitized_line = re.sub(
            r'File "([^"]*)/([^"/]+/[^"/]+)"',
            r'File ".../<sanitized_path>/\2"',
            sanitized_line,
        )

        # Remove line numbers that might reveal code structure
        sanitized_line = re.sub(r", line \d+", ", line <redacted>", sanitized_line)

        # Remove local variable information
        if "local variables:" in sanitized_line.lower():
            sanitized_line = "    <local variables redacted for security>\n"

        return sanitized_line
