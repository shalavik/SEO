"""
Caching package for SEO leads system

This package contains intelligent caching components.
"""

from .intelligent_cache import (
    IntelligentCache,
    CacheLevel,
    CacheStrategy,
    get_cache,
    cache_get,
    cache_set
)

__all__ = [
    'IntelligentCache',
    'CacheLevel',
    'CacheStrategy', 
    'get_cache',
    'cache_get',
    'cache_set'
] 