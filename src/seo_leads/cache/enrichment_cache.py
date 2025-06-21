"""
Enrichment Cache System

P3.3 IMPLEMENTATION: Advanced caching for enrichment data
Features:
- File-based caching (zero-cost alternative to Redis)
- TTL-based cache expiration (30 days default)
- Cache compression for large datasets
- Cache hit rate monitoring
- Intelligent cache warming
- Zero-cost architecture (local file system)
"""

import logging
import json
import pickle
import gzip
import os
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    data: Any
    created_at: float
    expires_at: float
    access_count: int = 0
    last_accessed: float = 0.0
    compressed: bool = False
    size_bytes: int = 0

@dataclass
class CacheStats:
    """Cache statistics"""
    total_entries: int
    hit_count: int
    miss_count: int
    hit_rate: float
    total_size_bytes: int
    expired_entries: int
    cache_directory: str

class EnrichmentCache:
    """P3.3: Advanced enrichment caching system"""
    
    def __init__(self, cache_dir: str = "cache", default_ttl: int = 2592000):  # 30 days
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'expired': 0
        }
        self.lock = threading.RLock()
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize cache metadata
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()
        
        logger.info(f"P3.3: Enrichment Cache initialized at {self.cache_dir}")
    
    def _load_metadata(self) -> Dict:
        """Load cache metadata"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"P3.3: Failed to load cache metadata: {e}")
        
        return {
            'created_at': time.time(),
            'entries': {},
            'stats': {'hits': 0, 'misses': 0, 'sets': 0}
        }
    
    def _save_metadata(self):
        """Save cache metadata"""
        try:
            with self.lock:
                self.metadata['stats'] = self.stats
                with open(self.metadata_file, 'w') as f:
                    json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.warning(f"P3.3: Failed to save cache metadata: {e}")
    
    def _generate_cache_key(self, key: str) -> str:
        """Generate cache file key"""
        # Create hash of the key for filename
        hash_obj = hashlib.md5(key.encode())
        return hash_obj.hexdigest()
    
    def _get_cache_file_path(self, cache_key: str, compressed: bool = False) -> Path:
        """Get cache file path"""
        extension = '.pkl.gz' if compressed else '.pkl'
        return self.cache_dir / f"{cache_key}{extension}"
    
    def get(self, key: str) -> Optional[Any]:
        """P3.3: Get value from cache"""
        try:
            with self.lock:
                cache_key = self._generate_cache_key(key)
                
                # Check if entry exists in metadata
                if cache_key not in self.metadata['entries']:
                    self.stats['misses'] += 1
                    return None
                
                entry_meta = self.metadata['entries'][cache_key]
                
                # Check if expired
                if time.time() > entry_meta['expires_at']:
                    self._delete_entry(cache_key)
                    self.stats['expired'] += 1
                    self.stats['misses'] += 1
                    return None
                
                # Load data from file
                compressed = entry_meta.get('compressed', False)
                cache_file = self._get_cache_file_path(cache_key, compressed)
                
                if not cache_file.exists():
                    # File missing, clean up metadata
                    del self.metadata['entries'][cache_key]
                    self.stats['misses'] += 1
                    return None
                
                # Load and decompress if needed
                if compressed:
                    with gzip.open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                else:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                
                # Update access statistics
                entry_meta['access_count'] += 1
                entry_meta['last_accessed'] = time.time()
                self.stats['hits'] += 1
                
                logger.debug(f"P3.3: Cache hit for key: {key}")
                return data
                
        except Exception as e:
            logger.warning(f"P3.3: Cache get failed for key '{key}': {e}")
            self.stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, compress: bool = None) -> bool:
        """P3.3: Set value in cache"""
        try:
            with self.lock:
                cache_key = self._generate_cache_key(key)
                expires_at = time.time() + (ttl or self.default_ttl)
                
                # Determine if compression should be used
                if compress is None:
                    # Auto-compress large objects
                    serialized_size = len(pickle.dumps(value))
                    compress = serialized_size > 10240  # 10KB threshold
                
                # Save data to file
                cache_file = self._get_cache_file_path(cache_key, compress)
                
                if compress:
                    with gzip.open(cache_file, 'wb') as f:
                        pickle.dump(value, f)
                else:
                    with open(cache_file, 'wb') as f:
                        pickle.dump(value, f)
                
                # Calculate file size
                file_size = cache_file.stat().st_size
                
                # Update metadata
                self.metadata['entries'][cache_key] = {
                    'key': key,
                    'created_at': time.time(),
                    'expires_at': expires_at,
                    'access_count': 0,
                    'last_accessed': 0.0,
                    'compressed': compress,
                    'size_bytes': file_size
                }
                
                self.stats['sets'] += 1
                
                # Periodic metadata save
                if self.stats['sets'] % 10 == 0:
                    self._save_metadata()
                
                logger.debug(f"P3.3: Cache set for key: {key} (compressed: {compress}, size: {file_size})")
                return True
                
        except Exception as e:
            logger.warning(f"P3.3: Cache set failed for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        try:
            with self.lock:
                cache_key = self._generate_cache_key(key)
                return self._delete_entry(cache_key)
        except Exception as e:
            logger.warning(f"P3.3: Cache delete failed for key '{key}': {e}")
            return False
    
    def _delete_entry(self, cache_key: str) -> bool:
        """Delete cache entry by cache key"""
        try:
            # Remove from metadata
            if cache_key in self.metadata['entries']:
                entry_meta = self.metadata['entries'][cache_key]
                compressed = entry_meta.get('compressed', False)
                del self.metadata['entries'][cache_key]
                
                # Remove file
                cache_file = self._get_cache_file_path(cache_key, compressed)
                if cache_file.exists():
                    cache_file.unlink()
                
                self.stats['deletes'] += 1
                return True
        except Exception as e:
            logger.warning(f"P3.3: Failed to delete cache entry {cache_key}: {e}")
        
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        cache_key = self._generate_cache_key(key)
        
        with self.lock:
            if cache_key not in self.metadata['entries']:
                return False
            
            entry_meta = self.metadata['entries'][cache_key]
            
            # Check if expired
            if time.time() > entry_meta['expires_at']:
                self._delete_entry(cache_key)
                return False
            
            return True
    
    def clear_expired(self) -> int:
        """Clear expired entries"""
        expired_count = 0
        current_time = time.time()
        
        with self.lock:
            expired_keys = []
            
            for cache_key, entry_meta in self.metadata['entries'].items():
                if current_time > entry_meta['expires_at']:
                    expired_keys.append(cache_key)
            
            for cache_key in expired_keys:
                if self._delete_entry(cache_key):
                    expired_count += 1
        
        if expired_count > 0:
            self._save_metadata()
            logger.info(f"P3.3: Cleared {expired_count} expired cache entries")
        
        return expired_count
    
    def clear_all(self) -> bool:
        """Clear all cache entries"""
        try:
            with self.lock:
                # Remove all cache files
                for cache_file in self.cache_dir.glob("*.pkl*"):
                    cache_file.unlink()
                
                # Reset metadata
                self.metadata['entries'] = {}
                self.stats = {'hits': 0, 'misses': 0, 'sets': 0, 'deletes': 0, 'expired': 0}
                self._save_metadata()
                
                logger.info("P3.3: Cleared all cache entries")
                return True
        except Exception as e:
            logger.error(f"P3.3: Failed to clear cache: {e}")
            return False
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        with self.lock:
            total_entries = len(self.metadata['entries'])
            total_hits = self.stats['hits']
            total_misses = self.stats['misses']
            hit_rate = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0.0
            
            # Calculate total size
            total_size = sum(
                entry.get('size_bytes', 0) 
                for entry in self.metadata['entries'].values()
            )
            
            return CacheStats(
                total_entries=total_entries,
                hit_count=total_hits,
                miss_count=total_misses,
                hit_rate=hit_rate,
                total_size_bytes=total_size,
                expired_entries=self.stats.get('expired', 0),
                cache_directory=str(self.cache_dir)
            )
    
    def warm_cache(self, keys_and_values: List[Tuple[str, Any]], ttl: Optional[int] = None):
        """P3.3: Warm cache with common data"""
        warmed_count = 0
        
        for key, value in keys_and_values:
            if not self.exists(key):
                if self.set(key, value, ttl):
                    warmed_count += 1
        
        logger.info(f"P3.3: Warmed cache with {warmed_count} entries")
        return warmed_count
    
    def get_cache_info(self) -> Dict:
        """Get detailed cache information"""
        with self.lock:
            entries_info = []
            current_time = time.time()
            
            for cache_key, entry_meta in self.metadata['entries'].items():
                time_to_expire = entry_meta['expires_at'] - current_time
                entries_info.append({
                    'key': entry_meta['key'],
                    'size_bytes': entry_meta.get('size_bytes', 0),
                    'access_count': entry_meta.get('access_count', 0),
                    'compressed': entry_meta.get('compressed', False),
                    'time_to_expire_seconds': max(0, time_to_expire),
                    'expired': time_to_expire <= 0
                })
            
            return {
                'cache_directory': str(self.cache_dir),
                'total_entries': len(entries_info),
                'stats': self.stats,
                'entries': entries_info
            }

# Test function
async def test_enrichment_cache():
    """Test the enrichment cache system"""
    print("⚡ Testing P3.3 Enrichment Cache System...")
    
    cache = EnrichmentCache("test_cache")
    
    # Test basic operations
    test_data = {
        'company_name': 'Jack The Plumber',
        'executives': [{'name': 'Jack Plumber', 'title': 'Master Plumber'}],
        'discovery_time': time.time()
    }
    
    # Test set and get
    key = "company:jacktheplumber.co.uk"
    print(f"Setting cache entry: {key}")
    success = cache.set(key, test_data, ttl=3600)  # 1 hour TTL
    print(f"  → Set success: {success}")
    
    # Test get
    cached_data = cache.get(key)
    print(f"  → Retrieved data: {cached_data is not None}")
    print(f"  → Data matches: {cached_data == test_data if cached_data else False}")
    
    # Test exists
    exists = cache.exists(key)
    print(f"  → Key exists: {exists}")
    
    # Test compression with large data
    large_data = {'data': 'x' * 20000}  # 20KB of data
    large_key = "large_data_test"
    cache.set(large_key, large_data)
    retrieved_large = cache.get(large_key)
    print(f"  → Large data compressed and retrieved: {retrieved_large == large_data}")
    
    # Test cache warming
    warm_data = [
        ("warm_key_1", {"test": "data1"}),
        ("warm_key_2", {"test": "data2"}),
        ("warm_key_3", {"test": "data3"})
    ]
    warmed = cache.warm_cache(warm_data)
    print(f"  → Cache warmed with {warmed} entries")
    
    # Get statistics
    stats = cache.get_stats()
    print(f"📊 Cache Statistics:")
    print(f"  → Total entries: {stats.total_entries}")
    print(f"  → Hit rate: {stats.hit_rate:.2%}")
    print(f"  → Total size: {stats.total_size_bytes} bytes")
    print(f"  → Cache directory: {stats.cache_directory}")
    
    # Test cleanup
    expired_count = cache.clear_expired()
    print(f"  → Expired entries cleared: {expired_count}")
    
    print("🎉 P3.3 Enrichment Cache test complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_enrichment_cache()) 