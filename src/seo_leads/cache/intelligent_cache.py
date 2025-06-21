"""
Intelligent Caching System for Phase 4C Performance Optimization

This module provides advanced multi-layer caching with:
- Multi-layer caching: Memory, Redis, and database caching
- Cache strategies: LRU, TTL, and intelligent cache warming
- Smart invalidation based on data freshness and patterns
- Performance metrics: Cache hit rates and performance monitoring
- Async operations for optimal performance
"""

import asyncio
import aioredis
import logging
import json
import hashlib
import pickle
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import OrderedDict
import sqlite3
import os

# Configure logging
logger = logging.getLogger(__name__)
cache_logger = logging.getLogger('intelligent_cache')

class CacheLevel(Enum):
    """Cache levels in order of speed"""
    MEMORY = 1      # Fastest - in-process memory
    REDIS = 2       # Fast - distributed memory
    DATABASE = 3    # Slower - persistent storage

class CacheStrategy(Enum):
    """Cache eviction strategies"""
    LRU = "lru"           # Least Recently Used
    TTL = "ttl"           # Time To Live
    LFU = "lfu"           # Least Frequently Used
    ADAPTIVE = "adaptive"  # Intelligent adaptation

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl_seconds is None:
            return False
        
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds
    
    def update_access(self):
        """Update access metadata"""
        self.last_accessed = datetime.now()
        self.access_count += 1

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    memory_hits: int = 0
    redis_hits: int = 0
    database_hits: int = 0
    evictions: int = 0
    invalidations: int = 0
    
    def get_hit_rate(self) -> float:
        """Calculate overall cache hit rate"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100
    
    def get_level_hit_rates(self) -> Dict[str, float]:
        """Get hit rates by cache level"""
        if self.total_requests == 0:
            return {'memory': 0.0, 'redis': 0.0, 'database': 0.0}
        
        return {
            'memory': (self.memory_hits / self.total_requests) * 100,
            'redis': (self.redis_hits / self.total_requests) * 100,
            'database': (self.database_hits / self.total_requests) * 100
        }

class MemoryCache:
    """High-performance in-memory cache with LRU eviction"""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache = OrderedDict()
        self.current_memory = 0
        self.lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get value from memory cache"""
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Check expiration
                if entry.is_expired():
                    del self.cache[key]
                    self.current_memory -= entry.size_bytes
                    return None
                
                # Update access and move to end (LRU)
                entry.update_access()
                self.cache.move_to_end(key)
                
                return entry
            
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
                  tags: List[str] = None) -> bool:
        """Set value in memory cache"""
        async with self.lock:
            # Calculate size
            try:
                serialized = pickle.dumps(value)
                size_bytes = len(serialized)
            except Exception:
                # Fallback size estimation
                size_bytes = len(str(value).encode('utf-8'))
            
            # Check if value is too large
            if size_bytes > self.max_memory_bytes / 10:  # Max 10% of cache size
                logger.warning(f"Value too large for memory cache: {size_bytes} bytes")
                return False
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                ttl_seconds=ttl_seconds,
                size_bytes=size_bytes,
                tags=tags or []
            )
            
            # Remove existing entry if present
            if key in self.cache:
                old_entry = self.cache[key]
                self.current_memory -= old_entry.size_bytes
                del self.cache[key]
            
            # Evict entries if needed
            while (len(self.cache) >= self.max_size or 
                   self.current_memory + size_bytes > self.max_memory_bytes):
                if not self.cache:
                    break
                
                # Remove least recently used item
                oldest_key, oldest_entry = self.cache.popitem(last=False)
                self.current_memory -= oldest_entry.size_bytes
                cache_logger.debug(f"Evicted from memory cache: {oldest_key}")
            
            # Add new entry
            self.cache[key] = entry
            self.current_memory += size_bytes
            
            return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from memory cache"""
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                self.current_memory -= entry.size_bytes
                del self.cache[key]
                return True
            return False
    
    async def clear_by_tags(self, tags: List[str]) -> int:
        """Clear entries with specific tags"""
        async with self.lock:
            keys_to_delete = []
            
            for key, entry in self.cache.items():
                if any(tag in entry.tags for tag in tags):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                entry = self.cache[key]
                self.current_memory -= entry.size_bytes
                del self.cache[key]
            
            return len(keys_to_delete)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory cache statistics"""
        return {
            'entries': len(self.cache),
            'max_size': self.max_size,
            'memory_usage_bytes': self.current_memory,
            'memory_usage_mb': round(self.current_memory / (1024 * 1024), 2),
            'max_memory_mb': self.max_memory_bytes / (1024 * 1024)
        }

class RedisCache:
    """Redis-based distributed cache"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", 
                 key_prefix: str = "seo_leads:"):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.redis = None
        self.connected = False
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await aioredis.from_url(self.redis_url)
            await self.redis.ping()
            self.connected = True
            cache_logger.info("Redis cache connected")
        except Exception as e:
            cache_logger.warning(f"Redis connection failed: {e}")
            self.connected = False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.connected = False
    
    def _make_key(self, key: str) -> str:
        """Create Redis key with prefix"""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self.connected:
            return None
        
        try:
            redis_key = self._make_key(key)
            data = await self.redis.get(redis_key)
            
            if data:
                # Deserialize data
                cache_data = json.loads(data)
                
                # Check expiration
                if 'expires_at' in cache_data:
                    expires_at = datetime.fromisoformat(cache_data['expires_at'])
                    if datetime.now() > expires_at:
                        await self.redis.delete(redis_key)
                        return None
                
                return cache_data['value']
            
            return None
            
        except Exception as e:
            cache_logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None,
                  tags: List[str] = None) -> bool:
        """Set value in Redis cache"""
        if not self.connected:
            return False
        
        try:
            redis_key = self._make_key(key)
            
            # Prepare cache data
            cache_data = {
                'value': value,
                'created_at': datetime.now().isoformat(),
                'tags': tags or []
            }
            
            if ttl_seconds:
                cache_data['expires_at'] = (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()
            
            # Serialize and store
            serialized = json.dumps(cache_data, default=str)
            
            if ttl_seconds:
                await self.redis.setex(redis_key, ttl_seconds, serialized)
            else:
                await self.redis.set(redis_key, serialized)
            
            # Store tags for invalidation
            if tags:
                for tag in tags:
                    tag_key = f"{self.key_prefix}tag:{tag}"
                    await self.redis.sadd(tag_key, key)
            
            return True
            
        except Exception as e:
            cache_logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from Redis cache"""
        if not self.connected:
            return False
        
        try:
            redis_key = self._make_key(key)
            result = await self.redis.delete(redis_key)
            return result > 0
            
        except Exception as e:
            cache_logger.error(f"Redis delete error: {e}")
            return False
    
    async def clear_by_tags(self, tags: List[str]) -> int:
        """Clear entries with specific tags"""
        if not self.connected:
            return 0
        
        try:
            deleted_count = 0
            
            for tag in tags:
                tag_key = f"{self.key_prefix}tag:{tag}"
                keys = await self.redis.smembers(tag_key)
                
                if keys:
                    # Delete cache entries
                    redis_keys = [self._make_key(key.decode() if isinstance(key, bytes) else key) for key in keys]
                    deleted = await self.redis.delete(*redis_keys)
                    deleted_count += deleted
                    
                    # Delete tag set
                    await self.redis.delete(tag_key)
            
            return deleted_count
            
        except Exception as e:
            cache_logger.error(f"Redis clear by tags error: {e}")
            return 0

class DatabaseCache:
    """SQLite-based persistent cache"""
    
    def __init__(self, db_path: str = "cache.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        created_at TEXT,
                        expires_at TEXT,
                        access_count INTEGER DEFAULT 1,
                        tags TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tags ON cache_entries(tags)
                """)
                
                conn.commit()
                
        except Exception as e:
            cache_logger.error(f"Database initialization error: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from database cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT value, expires_at FROM cache_entries WHERE key = ?",
                    (key,)
                )
                row = cursor.fetchone()
                
                if row:
                    value_json, expires_at = row
                    
                    # Check expiration
                    if expires_at:
                        expires_dt = datetime.fromisoformat(expires_at)
                        if datetime.now() > expires_dt:
                            # Delete expired entry
                            conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                            conn.commit()
                            return None
                    
                    # Update access count
                    conn.execute(
                        "UPDATE cache_entries SET access_count = access_count + 1 WHERE key = ?",
                        (key,)
                    )
                    conn.commit()
                    
                    return json.loads(value_json)
                
                return None
                
        except Exception as e:
            cache_logger.error(f"Database get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None,
                  tags: List[str] = None) -> bool:
        """Set value in database cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                value_json = json.dumps(value, default=str)
                created_at = datetime.now().isoformat()
                expires_at = None
                
                if ttl_seconds:
                    expires_at = (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()
                
                tags_json = json.dumps(tags or [])
                
                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries 
                    (key, value, created_at, expires_at, tags)
                    VALUES (?, ?, ?, ?, ?)
                """, (key, value_json, created_at, expires_at, tags_json))
                
                conn.commit()
                return True
                
        except Exception as e:
            cache_logger.error(f"Database set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from database cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            cache_logger.error(f"Database delete error: {e}")
            return False
    
    async def clear_by_tags(self, tags: List[str]) -> int:
        """Clear entries with specific tags"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                deleted_count = 0
                
                for tag in tags:
                    cursor = conn.execute(
                        "DELETE FROM cache_entries WHERE tags LIKE ?",
                        (f'%"{tag}"%',)
                    )
                    deleted_count += cursor.rowcount
                
                conn.commit()
                return deleted_count
                
        except Exception as e:
            cache_logger.error(f"Database clear by tags error: {e}")
            return 0
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                now = datetime.now().isoformat()
                cursor = conn.execute(
                    "DELETE FROM cache_entries WHERE expires_at IS NOT NULL AND expires_at < ?",
                    (now,)
                )
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            cache_logger.error(f"Database cleanup error: {e}")
            return 0

class IntelligentCache:
    """Multi-layer intelligent caching system"""
    
    def __init__(self, memory_config: Dict = None, redis_config: Dict = None,
                 database_config: Dict = None):
        # Initialize cache layers
        self.memory_cache = MemoryCache(**(memory_config or {}))
        self.redis_cache = RedisCache(**(redis_config or {}))
        self.database_cache = DatabaseCache(**(database_config or {}))
        
        # Metrics
        self.metrics = CacheMetrics()
        
        # Configuration
        self.default_ttl = 3600  # 1 hour
        self.auto_warming_enabled = True
        
        cache_logger.info("Intelligent cache system initialized")
    
    async def initialize(self):
        """Initialize all cache layers"""
        try:
            await self.redis_cache.connect()
        except Exception as e:
            cache_logger.warning(f"Redis initialization failed: {e}")
    
    async def get(self, key: str, tags: List[str] = None) -> Optional[Any]:
        """
        Get value from cache (checks all layers in order)
        
        Args:
            key: Cache key
            tags: Optional tags for invalidation
            
        Returns:
            Cached value or None
        """
        self.metrics.total_requests += 1
        
        # Level 1: Memory cache
        entry = await self.memory_cache.get(key)
        if entry is not None:
            self.metrics.cache_hits += 1
            self.metrics.memory_hits += 1
            cache_logger.debug(f"Memory cache hit: {key}")
            return entry.value
        
        # Level 2: Redis cache
        value = await self.redis_cache.get(key)
        if value is not None:
            self.metrics.cache_hits += 1
            self.metrics.redis_hits += 1
            cache_logger.debug(f"Redis cache hit: {key}")
            
            # Warm memory cache
            await self.memory_cache.set(key, value, self.default_ttl, tags)
            return value
        
        # Level 3: Database cache
        value = await self.database_cache.get(key)
        if value is not None:
            self.metrics.cache_hits += 1
            self.metrics.database_hits += 1
            cache_logger.debug(f"Database cache hit: {key}")
            
            # Warm upper layers
            await self.memory_cache.set(key, value, self.default_ttl, tags)
            await self.redis_cache.set(key, value, self.default_ttl, tags)
            return value
        
        # Cache miss
        self.metrics.cache_misses += 1
        cache_logger.debug(f"Cache miss: {key}")
        return None
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None,
                  tags: List[str] = None, levels: List[CacheLevel] = None) -> bool:
        """
        Set value in cache layers
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
            tags: Tags for invalidation
            levels: Specific cache levels to use
            
        Returns:
            True if at least one cache level succeeded
        """
        if ttl_seconds is None:
            ttl_seconds = self.default_ttl
        
        if levels is None:
            levels = [CacheLevel.MEMORY, CacheLevel.REDIS, CacheLevel.DATABASE]
        
        success_count = 0
        
        # Set in specified cache levels
        if CacheLevel.MEMORY in levels:
            if await self.memory_cache.set(key, value, ttl_seconds, tags):
                success_count += 1
        
        if CacheLevel.REDIS in levels:
            if await self.redis_cache.set(key, value, ttl_seconds, tags):
                success_count += 1
        
        if CacheLevel.DATABASE in levels:
            if await self.database_cache.set(key, value, ttl_seconds, tags):
                success_count += 1
        
        cache_logger.debug(f"Cache set: {key} (success in {success_count} levels)")
        return success_count > 0
    
    async def delete(self, key: str) -> bool:
        """Delete value from all cache layers"""
        deleted_count = 0
        
        if await self.memory_cache.delete(key):
            deleted_count += 1
        
        if await self.redis_cache.delete(key):
            deleted_count += 1
        
        if await self.database_cache.delete(key):
            deleted_count += 1
        
        cache_logger.debug(f"Cache delete: {key} (deleted from {deleted_count} levels)")
        return deleted_count > 0
    
    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate cache entries by tags"""
        total_invalidated = 0
        
        # Invalidate from all levels
        total_invalidated += await self.memory_cache.clear_by_tags(tags)
        total_invalidated += await self.redis_cache.clear_by_tags(tags)
        total_invalidated += await self.database_cache.clear_by_tags(tags)
        
        self.metrics.invalidations += total_invalidated
        
        cache_logger.info(f"Invalidated {total_invalidated} entries for tags: {tags}")
        return total_invalidated
    
    async def cleanup(self):
        """Cleanup expired entries from all cache layers"""
        database_cleaned = await self.database_cache.cleanup_expired()
        cache_logger.info(f"Cleaned up {database_cleaned} expired database entries")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache metrics"""
        memory_stats = self.memory_cache.get_stats()
        
        return {
            'hit_rate': round(self.metrics.get_hit_rate(), 2),
            'total_requests': self.metrics.total_requests,
            'cache_hits': self.metrics.cache_hits,
            'cache_misses': self.metrics.cache_misses,
            'level_hit_rates': self.metrics.get_level_hit_rates(),
            'memory_cache': memory_stats,
            'redis_connected': self.redis_cache.connected,
            'evictions': self.metrics.evictions,
            'invalidations': self.metrics.invalidations
        }
    
    async def warm_cache(self, warming_data: Dict[str, Tuple[Any, int, List[str]]]):
        """
        Warm cache with predefined data
        
        Args:
            warming_data: Dict of {key: (value, ttl, tags)}
        """
        if not self.auto_warming_enabled:
            return
        
        warmed_count = 0
        
        for key, (value, ttl, tags) in warming_data.items():
            if await self.set(key, value, ttl, tags):
                warmed_count += 1
        
        cache_logger.info(f"Cache warmed with {warmed_count} entries")

# Global cache instance
_intelligent_cache: Optional[IntelligentCache] = None

async def get_cache() -> IntelligentCache:
    """Get global intelligent cache instance"""
    global _intelligent_cache
    if _intelligent_cache is None:
        _intelligent_cache = IntelligentCache()
        await _intelligent_cache.initialize()
    return _intelligent_cache

# Convenience functions
async def cache_get(key: str, tags: List[str] = None) -> Optional[Any]:
    """Convenience function for cache get"""
    cache = await get_cache()
    return await cache.get(key, tags)

async def cache_set(key: str, value: Any, ttl_seconds: Optional[int] = None,
                   tags: List[str] = None) -> bool:
    """Convenience function for cache set"""
    cache = await get_cache()
    return await cache.set(key, value, ttl_seconds, tags) 