"""
Cache Manager

P3.3 IMPLEMENTATION: Smart cache management and analytics
Features:
- Cache analytics and optimization
- Intelligent cache warming strategies
- Cache performance monitoring
- Automated cache maintenance
- Zero-cost architecture (local management)
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os

from .enrichment_cache import EnrichmentCache, CacheStats

logger = logging.getLogger(__name__)

@dataclass
class CachePerformanceMetrics:
    """Cache performance metrics"""
    hit_rate: float
    miss_rate: float
    average_response_time_ms: float
    cache_size_mb: float
    entries_count: int
    expired_entries_cleaned: int
    warming_effectiveness: float

@dataclass
class CacheWarmingStrategy:
    """Cache warming strategy configuration"""
    strategy_name: str
    key_generator: Callable[[], List[str]]
    data_fetcher: Callable[[str], Any]
    priority: int
    ttl: int
    enabled: bool = True

class CacheManager:
    """P3.3: Smart cache management system"""
    
    def __init__(self, cache: EnrichmentCache):
        self.cache = cache
        self.performance_metrics: List[CachePerformanceMetrics] = []
        self.warming_strategies: List[CacheWarmingStrategy] = []
        self.monitoring_enabled = True
        self.last_cleanup = time.time()
        self.cleanup_interval = 3600  # 1 hour
        
        # Performance tracking
        self.response_times: List[float] = []
        self.max_response_times = 1000  # Keep last 1000 response times
        
        # Start background maintenance thread
        self.maintenance_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self.maintenance_thread.start()
        
        logger.info("P3.3: Cache Manager initialized")
    
    def _maintenance_loop(self):
        """Background maintenance loop"""
        while True:
            try:
                current_time = time.time()
                
                # Periodic cleanup
                if current_time - self.last_cleanup > self.cleanup_interval:
                    self._perform_maintenance()
                    self.last_cleanup = current_time
                
                # Collect performance metrics
                if self.monitoring_enabled:
                    self._collect_performance_metrics()
                
                # Sleep for 5 minutes
                time.sleep(300)
                
            except Exception as e:
                logger.warning(f"P3.3: Cache maintenance error: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def _perform_maintenance(self):
        """Perform cache maintenance tasks"""
        try:
            # Clear expired entries
            expired_count = self.cache.clear_expired()
            
            # Save metadata
            self.cache._save_metadata()
            
            # Log maintenance
            if expired_count > 0:
                logger.info(f"P3.3: Cache maintenance completed, cleared {expired_count} expired entries")
            
        except Exception as e:
            logger.warning(f"P3.3: Cache maintenance failed: {e}")
    
    def _collect_performance_metrics(self):
        """Collect cache performance metrics"""
        try:
            stats = self.cache.get_stats()
            
            # Calculate average response time
            avg_response_time = 0.0
            if self.response_times:
                avg_response_time = sum(self.response_times) / len(self.response_times)
            
            # Calculate cache size in MB
            cache_size_mb = stats.total_size_bytes / (1024 * 1024)
            
            # Calculate warming effectiveness (placeholder)
            warming_effectiveness = 0.8  # Would be calculated based on actual warming success
            
            metrics = CachePerformanceMetrics(
                hit_rate=stats.hit_rate,
                miss_rate=1.0 - stats.hit_rate,
                average_response_time_ms=avg_response_time,
                cache_size_mb=cache_size_mb,
                entries_count=stats.total_entries,
                expired_entries_cleaned=stats.expired_entries,
                warming_effectiveness=warming_effectiveness
            )
            
            self.performance_metrics.append(metrics)
            
            # Keep only last 24 hours of metrics (assuming 5-minute intervals)
            if len(self.performance_metrics) > 288:
                self.performance_metrics = self.performance_metrics[-288:]
            
        except Exception as e:
            logger.warning(f"P3.3: Failed to collect performance metrics: {e}")
    
    def get_with_timing(self, key: str) -> tuple[Optional[Any], float]:
        """Get value from cache with response time tracking"""
        start_time = time.time()
        
        try:
            value = self.cache.get(key)
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Track response time
            self.response_times.append(response_time)
            if len(self.response_times) > self.max_response_times:
                self.response_times = self.response_times[-self.max_response_times:]
            
            return value, response_time
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.warning(f"P3.3: Cache get with timing failed: {e}")
            return None, response_time
    
    def set_with_analytics(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with analytics"""
        start_time = time.time()
        
        try:
            success = self.cache.set(key, value, ttl)
            response_time = (time.time() - start_time) * 1000
            
            # Track response time
            self.response_times.append(response_time)
            if len(self.response_times) > self.max_response_times:
                self.response_times = self.response_times[-self.max_response_times:]
            
            return success
            
        except Exception as e:
            logger.warning(f"P3.3: Cache set with analytics failed: {e}")
            return False
    
    def add_warming_strategy(self, strategy: CacheWarmingStrategy):
        """Add cache warming strategy"""
        self.warming_strategies.append(strategy)
        logger.info(f"P3.3: Added cache warming strategy: {strategy.strategy_name}")
    
    def execute_warming_strategies(self) -> Dict[str, int]:
        """Execute all enabled warming strategies"""
        results = {}
        
        # Sort strategies by priority
        sorted_strategies = sorted(
            [s for s in self.warming_strategies if s.enabled],
            key=lambda x: x.priority,
            reverse=True
        )
        
        for strategy in sorted_strategies:
            try:
                logger.info(f"P3.3: Executing warming strategy: {strategy.strategy_name}")
                
                # Generate keys to warm
                keys = strategy.key_generator()
                warmed_count = 0
                
                for key in keys:
                    # Check if key already exists
                    if not self.cache.exists(key):
                        try:
                            # Fetch data
                            data = strategy.data_fetcher(key)
                            if data is not None:
                                # Cache the data
                                if self.cache.set(key, data, strategy.ttl):
                                    warmed_count += 1
                        except Exception as e:
                            logger.debug(f"P3.3: Failed to warm key '{key}': {e}")
                
                results[strategy.strategy_name] = warmed_count
                logger.info(f"P3.3: Warmed {warmed_count} entries for strategy: {strategy.strategy_name}")
                
            except Exception as e:
                logger.warning(f"P3.3: Warming strategy '{strategy.strategy_name}' failed: {e}")
                results[strategy.strategy_name] = 0
        
        return results
    
    def optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache performance"""
        optimization_results = {}
        
        try:
            # Clear expired entries
            expired_count = self.cache.clear_expired()
            optimization_results['expired_cleared'] = expired_count
            
            # Analyze cache usage patterns
            cache_info = self.cache.get_cache_info()
            entries = cache_info.get('entries', [])
            
            # Find least accessed entries
            if entries:
                sorted_entries = sorted(entries, key=lambda x: x.get('access_count', 0))
                least_accessed = sorted_entries[:10]  # Bottom 10
                optimization_results['least_accessed_keys'] = [e['key'] for e in least_accessed]
            
            # Calculate cache efficiency
            stats = self.cache.get_stats()
            efficiency_score = stats.hit_rate * 100
            optimization_results['efficiency_score'] = efficiency_score
            
            # Recommendations
            recommendations = []
            if stats.hit_rate < 0.6:
                recommendations.append("Consider implementing more aggressive cache warming")
            if stats.total_size_bytes > 100 * 1024 * 1024:  # 100MB
                recommendations.append("Cache size is large, consider implementing LRU eviction")
            if expired_count > stats.total_entries * 0.2:
                recommendations.append("High expired entry ratio, consider adjusting TTL values")
            
            optimization_results['recommendations'] = recommendations
            
            logger.info(f"P3.3: Cache optimization completed, efficiency: {efficiency_score:.1f}%")
            
        except Exception as e:
            logger.warning(f"P3.3: Cache optimization failed: {e}")
            optimization_results['error'] = str(e)
        
        return optimization_results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            # Current cache stats
            current_stats = self.cache.get_stats()
            
            # Historical performance metrics
            if self.performance_metrics:
                recent_metrics = self.performance_metrics[-12:]  # Last hour (5-min intervals)
                avg_hit_rate = sum(m.hit_rate for m in recent_metrics) / len(recent_metrics)
                avg_response_time = sum(m.average_response_time_ms for m in recent_metrics) / len(recent_metrics)
                avg_cache_size = sum(m.cache_size_mb for m in recent_metrics) / len(recent_metrics)
            else:
                avg_hit_rate = current_stats.hit_rate
                avg_response_time = 0.0
                avg_cache_size = current_stats.total_size_bytes / (1024 * 1024)
            
            # Cache warming strategies status
            warming_status = {
                'total_strategies': len(self.warming_strategies),
                'enabled_strategies': len([s for s in self.warming_strategies if s.enabled]),
                'strategy_names': [s.strategy_name for s in self.warming_strategies if s.enabled]
            }
            
            # Performance trends
            trends = {}
            if len(self.performance_metrics) >= 2:
                latest = self.performance_metrics[-1]
                previous = self.performance_metrics[-2]
                
                trends = {
                    'hit_rate_trend': latest.hit_rate - previous.hit_rate,
                    'response_time_trend': latest.average_response_time_ms - previous.average_response_time_ms,
                    'cache_size_trend': latest.cache_size_mb - previous.cache_size_mb
                }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'current_stats': {
                    'total_entries': current_stats.total_entries,
                    'hit_rate': current_stats.hit_rate,
                    'hit_count': current_stats.hit_count,
                    'miss_count': current_stats.miss_count,
                    'total_size_mb': current_stats.total_size_bytes / (1024 * 1024),
                    'cache_directory': current_stats.cache_directory
                },
                'performance_averages': {
                    'avg_hit_rate': avg_hit_rate,
                    'avg_response_time_ms': avg_response_time,
                    'avg_cache_size_mb': avg_cache_size
                },
                'warming_status': warming_status,
                'trends': trends,
                'metrics_collected': len(self.performance_metrics)
            }
            
        except Exception as e:
            logger.warning(f"P3.3: Failed to generate performance report: {e}")
            return {'error': str(e)}
    
    def export_analytics(self, filepath: str) -> bool:
        """Export cache analytics to file"""
        try:
            report = self.get_performance_report()
            
            # Add detailed metrics history
            report['metrics_history'] = [
                {
                    'hit_rate': m.hit_rate,
                    'miss_rate': m.miss_rate,
                    'response_time_ms': m.average_response_time_ms,
                    'cache_size_mb': m.cache_size_mb,
                    'entries_count': m.entries_count
                }
                for m in self.performance_metrics
            ]
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"P3.3: Cache analytics exported to {filepath}")
            return True
            
        except Exception as e:
            logger.warning(f"P3.3: Failed to export analytics: {e}")
            return False

# Test function
async def test_cache_manager():
    """Test the cache manager system"""
    print("📊 Testing P3.3 Cache Manager System...")
    
    # Create cache and manager
    cache = EnrichmentCache("test_cache_manager")
    manager = CacheManager(cache)
    
    # Test basic operations with timing
    test_key = "test:company:example.com"
    test_data = {"name": "Example Company", "executives": ["John Doe"]}
    
    # Set data
    success = manager.set_with_analytics(test_key, test_data, ttl=3600)
    print(f"Set with analytics: {success}")
    
    # Get data with timing
    retrieved_data, response_time = manager.get_with_timing(test_key)
    print(f"Retrieved data: {retrieved_data is not None}")
    print(f"Response time: {response_time:.2f}ms")
    
    # Test cache warming strategy
    def generate_warm_keys():
        return ["warm:key1", "warm:key2", "warm:key3"]
    
    def fetch_warm_data(key):
        return {"key": key, "data": f"warmed_data_for_{key}"}
    
    warming_strategy = CacheWarmingStrategy(
        strategy_name="test_warming",
        key_generator=generate_warm_keys,
        data_fetcher=fetch_warm_data,
        priority=1,
        ttl=1800
    )
    
    manager.add_warming_strategy(warming_strategy)
    warming_results = manager.execute_warming_strategies()
    print(f"Warming results: {warming_results}")
    
    # Test cache optimization
    optimization_results = manager.optimize_cache()
    print(f"Optimization results: {optimization_results}")
    
    # Generate performance report
    report = manager.get_performance_report()
    print(f"📊 Performance Report:")
    print(f"  → Hit rate: {report['current_stats']['hit_rate']:.2%}")
    print(f"  → Total entries: {report['current_stats']['total_entries']}")
    print(f"  → Cache size: {report['current_stats']['total_size_mb']:.2f}MB")
    print(f"  → Warming strategies: {report['warming_status']['enabled_strategies']}")
    
    # Test analytics export
    export_success = manager.export_analytics("cache_analytics_test.json")
    print(f"Analytics export: {export_success}")
    
    print("🎉 P3.3 Cache Manager test complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_cache_manager()) 