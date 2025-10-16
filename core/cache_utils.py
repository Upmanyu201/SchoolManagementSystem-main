"""
Cache utilities for safe cache key handling
"""
import hashlib
import re
from typing import Any

def sanitize_cache_key(key: str) -> str:
    """
    Sanitize cache key to remove problematic characters for memcached compatibility
    """
    if not key:
        return "empty_key"
    
    # Convert to string and remove problematic characters
    clean_key = str(key)
    
    # Replace spaces, colons, and other problematic characters with underscores
    clean_key = re.sub(r'[^\w\-_.]', '_', clean_key)
    
    # Remove multiple consecutive underscores
    clean_key = re.sub(r'_+', '_', clean_key)
    
    # Ensure key length is within limits (250 chars for memcached)
    if len(clean_key) > 200:
        # Hash long keys
        hash_suffix = hashlib.md5(clean_key.encode()).hexdigest()[:8]
        clean_key = clean_key[:190] + '_' + hash_suffix
    
    # Ensure key doesn't start or end with underscore
    clean_key = clean_key.strip('_')
    
    return clean_key or "default_key"

def make_cache_key(*args, **kwargs) -> str:
    """
    Create a safe cache key from multiple arguments
    """
    parts = []
    
    # Add positional arguments
    for arg in args:
        if arg is not None:
            parts.append(str(arg))
    
    # Add keyword arguments
    for key, value in sorted(kwargs.items()):
        if value is not None:
            parts.append(f"{key}_{value}")
    
    # Join and sanitize
    cache_key = "_".join(parts)
    return sanitize_cache_key(cache_key)

def safe_cache_set(cache, key: str, value: Any, timeout: int = 300):
    """
    Safely set cache value with sanitized key
    """
    try:
        clean_key = sanitize_cache_key(key)
        cache.set(clean_key, value, timeout)
        return True
    except Exception:
        return False

def safe_cache_get(cache, key: str, default=None):
    """
    Safely get cache value with sanitized key
    """
    try:
        clean_key = sanitize_cache_key(key)
        return cache.get(clean_key, default)
    except Exception:
        return default