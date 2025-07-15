"""
Core Temporal Isolation Engine for Cryptex middleware.

This module implements the fundamental engine that powers secret isolation
in middleware deployments for FastMCP servers and FastAPI applications.
"""

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Pattern, Union
import asyncio
import json
import time
import threading
from collections import OrderedDict


@dataclass
class SecretPattern:
    """Definition of a secret pattern for detection and replacement."""
    name: str
    pattern: Pattern[str]
    placeholder_template: str
    description: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecretPattern':
        """Create SecretPattern from dictionary configuration."""
        return cls(
            name=data['name'],
            pattern=re.compile(data['pattern']),
            placeholder_template=data['template'],
            description=data.get('description', '')
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
    placeholders: Dict[str, str] = field(default_factory=dict)  # placeholder -> real_value
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    
    def get_real_value(self, placeholder: str) -> Optional[str]:
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
    
    def __init__(self, 
                 patterns: Optional[List[SecretPattern]] = None,
                 max_cache_size: int = 1000,
                 max_cache_age: int = 3600,
                 enable_background_cleanup: bool = True):
        """
        Initialize the isolation engine.
        
        Args:
            patterns: List of secret patterns to detect. Uses defaults if None.
            max_cache_size: Maximum number of contexts to cache (LRU eviction)
            max_cache_age: Maximum age of cached contexts in seconds
            enable_background_cleanup: Whether to run background cache cleanup
        """
        self.patterns = patterns or self._get_default_patterns()
        self._context_cache: OrderedDict[str, SanitizedData] = OrderedDict()
        self._max_cache_size = max_cache_size
        self._max_cache_age = max_cache_age
        self._cache_lock = threading.RLock()  # Thread-safe cache operations
        self._cleanup_task: Optional[asyncio.Task] = None
        self._enable_background_cleanup = enable_background_cleanup
        self._last_access_times: Dict[str, float] = {}
        
        # Background cleanup will be started when first needed (lazy initialization)
        
    def _get_default_patterns(self) -> List[SecretPattern]:
        """Get default secret patterns for common use cases."""
        return [
            SecretPattern(
                name="openai_key",
                pattern=re.compile(r'sk-[a-zA-Z0-9]{48}'),
                placeholder_template="{{OPENAI_API_KEY}}",
                description="OpenAI API key"
            ),
            SecretPattern(
                name="anthropic_key", 
                pattern=re.compile(r'sk-ant-[a-zA-Z0-9-]{95}'),
                placeholder_template="{{ANTHROPIC_API_KEY}}",
                description="Anthropic API key"
            ),
            SecretPattern(
                name="github_token",
                pattern=re.compile(r'ghp_[a-zA-Z0-9]{36}'),
                placeholder_template="{{GITHUB_TOKEN}}",
                description="GitHub personal access token"
            ),
            SecretPattern(
                name="file_path",
                pattern=re.compile(r'/(?:Users|home)/[^/\s]+(?:/[^/\s]*)*'),
                placeholder_template="/{USER_HOME}/...",
                description="User file system paths"
            ),
            SecretPattern(
                name="database_url",
                pattern=re.compile(r'(?:postgres|mysql|redis|mongodb)://[^\s]+'),
                placeholder_template="{{DATABASE_URL}}",
                description="Database connection URLs"
            ),
        ]
    
    async def sanitize_for_ai(self, data: Any, context_id: Optional[str] = None) -> SanitizedData:
        """
        Sanitize data for AI processing by replacing secrets with placeholders.
        
        Args:
            data: Raw data that may contain secrets
            context_id: Optional context ID for tracking
            
        Returns:
            SanitizedData with secrets replaced by placeholders
            
        Raises:
            ValueError: If data cannot be sanitized
        """
        if context_id is None:
            context_id = str(uuid.uuid4())
            
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
        sanitized_data, placeholders = await self._replace_with_placeholders(data, detected_secrets)
        
        # Create sanitized data object
        result = SanitizedData(
            data=sanitized_data,
            placeholders=placeholders,
            context_id=context_id
        )
        
        # Cache the context for later resolution with LRU management
        self._cache_context(context_id, result)
        
        return result
    
    async def resolve_for_execution(self, data: Any, context_id: str) -> ResolvedData:
        """
        Resolve placeholders back to real values for tool execution.
        
        Args:
            data: Data containing placeholders to resolve
            context_id: Context ID to look up placeholder mappings
            
        Returns:
            ResolvedData with placeholders replaced by real values
            
        Raises:
            ValueError: If context not found or resolution fails
        """
        # Get the sanitized context with access tracking
        sanitized_context = self._get_cached_context(context_id)
        if not sanitized_context:
            raise ValueError(f"Context {context_id} not found or expired")
        
        # Resolve placeholders in the data
        resolved_data, resolved_count = await self._resolve_placeholders(
            data, sanitized_context.placeholders
        )
        
        return ResolvedData(
            data=resolved_data,
            resolved_count=resolved_count,
            context_id=context_id
        )
    
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
    
    async def _detect_secrets(self, data: Any) -> List[DetectedSecret]:
        """Detect secrets in various data types."""
        detected_secrets = []
        
        if isinstance(data, str):
            detected_secrets.extend(await self._detect_secrets_in_string(data))
        elif isinstance(data, dict):
            detected_secrets.extend(await self._detect_secrets_in_dict(data))
        elif isinstance(data, (list, tuple)):
            detected_secrets.extend(await self._detect_secrets_in_list(data))
        elif hasattr(data, '__dict__'):
            # Handle custom objects
            detected_secrets.extend(await self._detect_secrets_in_dict(data.__dict__))
        
        return detected_secrets
    
    async def _detect_secrets_in_string(self, text: str) -> List[DetectedSecret]:
        """Detect secrets in a string."""
        detected = []
        
        for pattern in self.patterns:
            for match in pattern.pattern.finditer(text):
                placeholder = self._generate_placeholder(
                    match.group(), pattern.name, pattern.placeholder_template
                )
                
                detected.append(DetectedSecret(
                    value=match.group(),
                    pattern_name=pattern.name,
                    placeholder=placeholder,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return detected
    
    async def _detect_secrets_in_dict(self, data: Dict[str, Any]) -> List[DetectedSecret]:
        """Detect secrets in a dictionary."""
        detected = []
        
        for key, value in data.items():
            if isinstance(value, str):
                detected.extend(await self._detect_secrets_in_string(value))
            elif isinstance(value, (dict, list, tuple)):
                detected.extend(await self._detect_secrets(value))
        
        return detected
    
    async def _detect_secrets_in_list(self, data: List[Any]) -> List[DetectedSecret]:
        """Detect secrets in a list."""
        detected = []
        
        for item in data:
            detected.extend(await self._detect_secrets(item))
        
        return detected
    
    def _generate_placeholder(self, secret_value: str, pattern_name: str, template: str) -> str:
        """Generate a unique placeholder for a secret value."""
        # Create a hash of the secret for uniqueness
        secret_hash = hashlib.sha256(secret_value.encode()).hexdigest()[:8]
        
        # Use template if it contains placeholders, otherwise use default format
        if '{{' in template and '}}' in template:
            return template
        else:
            return f"{{RESOLVE:{pattern_name.upper()}:{secret_hash}}}"
    
    async def _replace_with_placeholders(self, data: Any, secrets: List[DetectedSecret]) -> tuple[Any, Dict[str, str]]:
        """Replace detected secrets with placeholders using optimized algorithm."""
        if not secrets:
            return data, {}
        
        placeholders = {}
        
        if isinstance(data, str):
            # Optimized single-pass replacement for strings
            sanitized_data = self._replace_secrets_in_string(data, secrets, placeholders)
            return sanitized_data, placeholders
        
        elif isinstance(data, dict):
            sanitized_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    # Find relevant secrets for this specific string value
                    relevant_secrets = self._find_relevant_secrets(value, secrets)
                    if relevant_secrets:
                        sanitized_value = self._replace_secrets_in_string(value, relevant_secrets, placeholders)
                        sanitized_data[key] = sanitized_value
                    else:
                        sanitized_data[key] = value
                elif isinstance(value, (dict, list, tuple)):
                    # Recursively handle nested structures
                    sanitized_value, nested_placeholders = await self._replace_with_placeholders(value, secrets)
                    sanitized_data[key] = sanitized_value
                    placeholders.update(nested_placeholders)
                else:
                    sanitized_data[key] = value
            return sanitized_data, placeholders
        
        elif isinstance(data, (list, tuple)):
            sanitized_data = []
            for item in data:
                if isinstance(item, str):
                    # Find relevant secrets for this specific string item
                    relevant_secrets = self._find_relevant_secrets(item, secrets)
                    if relevant_secrets:
                        sanitized_item = self._replace_secrets_in_string(item, relevant_secrets, placeholders)
                        sanitized_data.append(sanitized_item)
                    else:
                        sanitized_data.append(item)
                elif isinstance(item, (dict, list, tuple)):
                    # Recursively handle nested structures
                    sanitized_item, nested_placeholders = await self._replace_with_placeholders(item, secrets)
                    sanitized_data.append(sanitized_item)
                    placeholders.update(nested_placeholders)
                else:
                    sanitized_data.append(item)
            return sanitized_data, placeholders
        
        return data, {}
    
    async def _resolve_placeholders(self, data: Any, placeholder_map: Dict[str, str]) -> tuple[Any, int]:
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
                resolved_value, count = await self._resolve_placeholders(value, placeholder_map)
                resolved_data[key] = resolved_value
                resolved_count += count
            return resolved_data, resolved_count
        
        elif isinstance(data, (list, tuple)):
            resolved_data = []
            for item in data:
                resolved_item, count = await self._resolve_placeholders(item, placeholder_map)
                resolved_data.append(resolved_item)
                resolved_count += count
            return resolved_data, resolved_count
        
        return data, resolved_count
    
    async def _replace_real_values_with_placeholders(self, data: Any, placeholder_map: Dict[str, str]) -> Any:
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
                sanitized[key] = await self._replace_real_values_with_placeholders(value, placeholder_map)
            return sanitized
        
        elif isinstance(data, (list, tuple)):
            sanitized = []
            for item in data:
                sanitized.append(await self._replace_real_values_with_placeholders(item, placeholder_map))
            return sanitized
        
        return data
    
    def _find_relevant_secrets(self, text: str, secrets: List[DetectedSecret]) -> List[DetectedSecret]:
        """Find secrets that are actually present in the given text."""
        relevant = []
        for secret in secrets:
            if secret.value in text:
                relevant.append(secret)
        return relevant
    
    def _replace_secrets_in_string(self, text: str, secrets: List[DetectedSecret], placeholders: Dict[str, str]) -> str:
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
        cleanup_interval = min(300, self._max_cache_age // 6)  # Clean every 5 minutes or 1/6 of max age
        
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
        """Cache a context with LRU eviction."""
        with self._cache_lock:
            # Remove if already exists (to update position)
            if context_id in self._context_cache:
                del self._context_cache[context_id]
            
            # Add to end (most recently used)
            self._context_cache[context_id] = context
            self._last_access_times[context_id] = time.time()
            
            # Enforce size limit
            self._enforce_cache_size_limit()
    
    def _get_cached_context(self, context_id: str) -> Optional[SanitizedData]:
        """Get a cached context and update access time (LRU)."""
        with self._cache_lock:
            context = self._context_cache.get(context_id)
            if context:
                # Move to end (mark as recently used)
                del self._context_cache[context_id]
                self._context_cache[context_id] = context
                self._last_access_times[context_id] = time.time()
            return context
    
    def _enforce_cache_size_limit(self) -> None:
        """Enforce cache size limit by evicting least recently used entries."""
        while len(self._context_cache) > self._max_cache_size:
            # Remove oldest entry (least recently used)
            oldest_context_id, _ = self._context_cache.popitem(last=False)
            self._last_access_times.pop(oldest_context_id, None)
    
    async def _clean_expired_cache(self) -> None:
        """Remove expired contexts from cache."""
        current_time = time.time()
        
        with self._cache_lock:
            expired_keys = [
                context_id for context_id, context in self._context_cache.items()
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
        with self._cache_lock:
            context_existed = self._context_cache.pop(context_id, None) is not None
            self._last_access_times.pop(context_id, None)
            return context_existed
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        with self._cache_lock:
            current_time = time.time()
            
            # Calculate age distribution
            ages = [current_time - context.created_at for context in self._context_cache.values()]
            avg_age = sum(ages) / len(ages) if ages else 0
            
            return {
                "cached_contexts": len(self._context_cache),
                "max_cache_size": self._max_cache_size,
                "cache_utilization": len(self._context_cache) / self._max_cache_size,
                "max_cache_age": self._max_cache_age,
                "average_context_age": avg_age,
                "patterns_loaded": len(self.patterns),
                "background_cleanup_enabled": self._enable_background_cleanup,
                "cleanup_task_active": self._cleanup_task is not None and not self._cleanup_task.done()
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
        with self._cache_lock:
            count = len(self._context_cache)
            self._context_cache.clear()
            self._last_access_times.clear()
            return count