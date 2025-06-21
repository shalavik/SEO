"""
API Gateway for Phase 4C Production Integration

This module provides a unified API gateway for all external API integrations:
- Unified interface for all external API calls
- Intelligent request routing based on API availability
- Comprehensive monitoring integration with request/response logging
- Circuit breaker patterns for automatic failover
- Load balancing and retry logic
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from abc import ABC, abstractmethod

from ..config.credential_manager import get_credential_manager, APIProvider
from ..models import ExecutiveContact

# Configure logging
logger = logging.getLogger(__name__)
gateway_logger = logging.getLogger('api_gateway')

class RequestPriority(Enum):
    """Request priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class GatewayStatus(Enum):
    """API Gateway status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"

@dataclass
class APIRequest:
    """API request container"""
    request_id: str
    provider: APIProvider
    endpoint: str
    method: str = "GET"
    params: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    data: Optional[Dict[str, Any]] = None
    priority: RequestPriority = RequestPriority.NORMAL
    timeout: int = 30
    retry_attempts: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class APIResponse:
    """API response container"""
    request_id: str
    provider: APIProvider
    success: bool
    status_code: Optional[int] = None
    data: Optional[Any] = None
    error_message: Optional[str] = None
    response_time: float = 0.0
    attempts: int = 1
    cached: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProviderMetrics:
    """Metrics for an API provider"""
    provider: APIProvider
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    circuit_breaker_trips: int = 0
    
    def get_success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def is_healthy(self) -> bool:
        """Check if provider is healthy (>80% success rate)"""
        return self.get_success_rate() >= 80.0

class CircuitBreaker:
    """Enhanced circuit breaker with metrics"""
    
    def __init__(self, provider: APIProvider, failure_threshold: int = 5, 
                 recovery_timeout: int = 60, half_open_max_calls: int = 3):
        self.provider = provider
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
        self.half_open_calls = 0
        self.trip_count = 0
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.state == 'open':
            if self.last_failure_time:
                time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
                if time_since_failure > self.recovery_timeout:
                    self.state = 'half-open'
                    self.half_open_calls = 0
                    logger.info(f"Circuit breaker half-open for {self.provider.value}")
                    return False
            return True
        return False
    
    def can_proceed(self) -> bool:
        """Check if request can proceed"""
        if self.state == 'closed':
            return True
        elif self.state == 'half-open':
            return self.half_open_calls < self.half_open_max_calls
        else:  # open
            return not self.is_open()
    
    def record_success(self):
        """Record successful API call"""
        if self.state == 'half-open':
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = 'closed'
                self.failure_count = 0
                logger.info(f"Circuit breaker closed for {self.provider.value}")
        elif self.state == 'closed':
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed API call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == 'half-open':
            self.state = 'open'
            self.trip_count += 1
            logger.warning(f"Circuit breaker re-opened for {self.provider.value}")
        elif self.failure_count >= self.failure_threshold:
            self.state = 'open'
            self.trip_count += 1
            logger.warning(f"Circuit breaker opened for {self.provider.value} after {self.failure_count} failures")

class RequestQueue:
    """Priority-based request queue with load balancing"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queues = {
            RequestPriority.CRITICAL: asyncio.Queue(),
            RequestPriority.HIGH: asyncio.Queue(),
            RequestPriority.NORMAL: asyncio.Queue(),
            RequestPriority.LOW: asyncio.Queue()
        }
        self.pending_count = 0
    
    async def put(self, request: APIRequest) -> bool:
        """Add request to appropriate priority queue"""
        if self.pending_count >= self.max_size:
            return False
        
        await self.queues[request.priority].put(request)
        self.pending_count += 1
        return True
    
    async def get(self) -> APIRequest:
        """Get next request based on priority"""
        # Check queues in priority order
        for priority in [RequestPriority.CRITICAL, RequestPriority.HIGH, 
                        RequestPriority.NORMAL, RequestPriority.LOW]:
            queue = self.queues[priority]
            if not queue.empty():
                request = await queue.get()
                self.pending_count -= 1
                return request
        
        # Wait for any request if all queues empty
        tasks = [asyncio.create_task(queue.get()) for queue in self.queues.values()]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
        
        request = done.pop().result()
        self.pending_count -= 1
        return request
    
    def get_queue_status(self) -> Dict[str, int]:
        """Get current queue status"""
        return {
            priority.name: queue.qsize() 
            for priority, queue in self.queues.items()
        }

class APIGateway:
    """Unified API Gateway for all external integrations"""
    
    def __init__(self, max_concurrent_requests: int = 10):
        self.credential_manager = get_credential_manager()
        self.max_concurrent_requests = max_concurrent_requests
        
        # Initialize components
        self.request_queue = RequestQueue()
        self.circuit_breakers = {
            provider: CircuitBreaker(provider) 
            for provider in APIProvider
        }
        self.metrics = {
            provider: ProviderMetrics(provider) 
            for provider in APIProvider
        }
        
        # Worker management
        self.workers = []
        self.is_running = False
        self.session = None
        
        # Cache
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour default
        
        gateway_logger.info("API Gateway initialized", extra={
            'max_concurrent_requests': max_concurrent_requests,
            'providers_configured': len(self.circuit_breakers)
        })
    
    async def start(self):
        """Start the API gateway"""
        if self.is_running:
            return
        
        self.is_running = True
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            connector=aiohttp.TCPConnector(limit=50),
            headers={'User-Agent': 'UK-SEO-Lead-Generator-Gateway/1.0'}
        )
        
        # Start worker tasks
        for i in range(self.max_concurrent_requests):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        gateway_logger.info(f"API Gateway started with {len(self.workers)} workers")
    
    async def stop(self):
        """Stop the API gateway"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        # Close session
        if self.session:
            await self.session.close()
            self.session = None
        
        gateway_logger.info("API Gateway stopped")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
    
    async def _worker(self, worker_id: str):
        """Worker task to process requests"""
        gateway_logger.info(f"Worker {worker_id} started")
        
        try:
            while self.is_running:
                try:
                    # Get next request
                    request = await asyncio.wait_for(
                        self.request_queue.get(), 
                        timeout=1.0
                    )
                    
                    # Process request
                    response = await self._process_request(request)
                    
                    # Log response
                    gateway_logger.info(
                        f"Request processed by {worker_id}",
                        extra={
                            'request_id': request.request_id,
                            'provider': request.provider.value,
                            'success': response.success,
                            'response_time': response.response_time
                        }
                    )
                    
                except asyncio.TimeoutError:
                    # No requests available, continue
                    continue
                except Exception as e:
                    gateway_logger.error(f"Worker {worker_id} error: {e}")
                    
        except asyncio.CancelledError:
            gateway_logger.info(f"Worker {worker_id} cancelled")
            raise
        except Exception as e:
            gateway_logger.error(f"Worker {worker_id} crashed: {e}")
    
    def _get_cache_key(self, request: APIRequest) -> str:
        """Generate cache key for request"""
        cache_data = {
            'provider': request.provider.value,
            'endpoint': request.endpoint,
            'params': sorted(request.params.items()) if request.params else [],
            'method': request.method
        }
        return json.dumps(cache_data, sort_keys=True)
    
    def _is_cacheable(self, request: APIRequest) -> bool:
        """Check if request is cacheable"""
        # Only cache GET requests
        if request.method != "GET":
            return False
        
        # Don't cache high priority requests
        if request.priority in [RequestPriority.CRITICAL, RequestPriority.HIGH]:
            return False
        
        return True
    
    async def _check_cache(self, request: APIRequest) -> Optional[APIResponse]:
        """Check cache for existing response"""
        if not self._is_cacheable(request):
            return None
        
        cache_key = self._get_cache_key(request)
        
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            
            # Check if cache is still valid
            if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self.cache_ttl):
                gateway_logger.info(f"Cache hit for {request.provider.value}")
                
                return APIResponse(
                    request_id=request.request_id,
                    provider=request.provider,
                    success=True,
                    data=cache_entry['data'],
                    response_time=0.01,  # Very fast cache response
                    cached=True
                )
        
        return None
    
    async def _cache_response(self, request: APIRequest, response: APIResponse):
        """Cache successful response"""
        if not self._is_cacheable(request) or not response.success:
            return
        
        cache_key = self._get_cache_key(request)
        self.cache[cache_key] = {
            'data': response.data,
            'timestamp': datetime.now()
        }
    
    async def _process_request(self, request: APIRequest) -> APIResponse:
        """Process a single API request"""
        start_time = datetime.now()
        
        # Check cache first
        cached_response = await self._check_cache(request)
        if cached_response:
            return cached_response
        
        # Check circuit breaker
        circuit_breaker = self.circuit_breakers[request.provider]
        if not circuit_breaker.can_proceed():
            return APIResponse(
                request_id=request.request_id,
                provider=request.provider,
                success=False,
                error_message="Circuit breaker is open",
                response_time=0.0
            )
        
        # Get authentication headers
        auth_headers = self.credential_manager.get_authentication_headers(request.provider)
        if not auth_headers:
            return APIResponse(
                request_id=request.request_id,
                provider=request.provider,
                success=False,
                error_message="No valid credentials available",
                response_time=0.0
            )
        
        # Merge headers
        headers = {**request.headers, **auth_headers}
        
        # Get provider base URL
        base_urls = {
            APIProvider.COMPANIES_HOUSE: "https://api.company-information.service.gov.uk",
            APIProvider.TWITTER: "https://api.twitter.com/2",
            APIProvider.LINKEDIN: "https://api.linkedin.com/v2",
            APIProvider.FACEBOOK: "https://graph.facebook.com/v18.0"
        }
        
        base_url = base_urls.get(request.provider)
        if not base_url:
            return APIResponse(
                request_id=request.request_id,
                provider=request.provider,
                success=False,
                error_message=f"No base URL configured for {request.provider.value}",
                response_time=0.0
            )
        
        # Make HTTP request with retries
        for attempt in range(request.retry_attempts):
            try:
                url = f"{base_url}{request.endpoint}"
                
                async with self.session.request(
                    method=request.method,
                    url=url,
                    params=request.params,
                    headers=headers,
                    json=request.data,
                    timeout=aiohttp.ClientTimeout(total=request.timeout)
                ) as http_response:
                    
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    if http_response.status == 200:
                        data = await http_response.json()
                        
                        # Success - update metrics and circuit breaker
                        circuit_breaker.record_success()
                        self._update_metrics(request.provider, True, response_time)
                        
                        response = APIResponse(
                            request_id=request.request_id,
                            provider=request.provider,
                            success=True,
                            status_code=http_response.status,
                            data=data,
                            response_time=response_time,
                            attempts=attempt + 1
                        )
                        
                        # Cache successful response
                        await self._cache_response(request, response)
                        
                        return response
                    
                    elif http_response.status == 429:  # Rate limited
                        if attempt < request.retry_attempts - 1:
                            # Exponential backoff
                            wait_time = (2 ** attempt) * 1.0
                            await asyncio.sleep(wait_time)
                            continue
                    
                    elif http_response.status in [500, 502, 503, 504]:  # Server errors
                        if attempt < request.retry_attempts - 1:
                            wait_time = (2 ** attempt) * 0.5
                            await asyncio.sleep(wait_time)
                            continue
                    
                    # Non-retriable error
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    error_response = APIResponse(
                        request_id=request.request_id,
                        provider=request.provider,
                        success=False,
                        status_code=http_response.status,
                        error_message=f"HTTP {http_response.status}",
                        response_time=response_time,
                        attempts=attempt + 1
                    )
                    
                    # Update metrics
                    circuit_breaker.record_failure()
                    self._update_metrics(request.provider, False, response_time)
                    
                    return error_response
                    
            except asyncio.TimeoutError:
                if attempt < request.retry_attempts - 1:
                    continue
                
                response_time = (datetime.now() - start_time).total_seconds()
                circuit_breaker.record_failure()
                self._update_metrics(request.provider, False, response_time)
                
                return APIResponse(
                    request_id=request.request_id,
                    provider=request.provider,
                    success=False,
                    error_message="Request timeout",
                    response_time=response_time,
                    attempts=attempt + 1
                )
            
            except Exception as e:
                if attempt < request.retry_attempts - 1:
                    continue
                
                response_time = (datetime.now() - start_time).total_seconds()
                circuit_breaker.record_failure()
                self._update_metrics(request.provider, False, response_time)
                
                return APIResponse(
                    request_id=request.request_id,
                    provider=request.provider,
                    success=False,
                    error_message=str(e),
                    response_time=response_time,
                    attempts=attempt + 1
                )
    
    def _update_metrics(self, provider: APIProvider, success: bool, response_time: float):
        """Update provider metrics"""
        metrics = self.metrics[provider]
        metrics.total_requests += 1
        
        if success:
            metrics.successful_requests += 1
            metrics.last_success = datetime.now()
        else:
            metrics.failed_requests += 1
            metrics.last_failure = datetime.now()
        
        # Update average response time
        if metrics.total_requests == 1:
            metrics.average_response_time = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            metrics.average_response_time = (
                alpha * response_time + 
                (1 - alpha) * metrics.average_response_time
            )
    
    async def make_request(self, provider: APIProvider, endpoint: str,
                          method: str = "GET", params: Dict = None,
                          priority: RequestPriority = RequestPriority.NORMAL) -> APIResponse:
        """
        Make API request through the gateway
        
        Args:
            provider: API provider
            endpoint: API endpoint
            method: HTTP method
            params: Query parameters
            priority: Request priority
            
        Returns:
            APIResponse with result
        """
        request = APIRequest(
            request_id=str(uuid.uuid4()),
            provider=provider,
            endpoint=endpoint,
            method=method,
            params=params or {},
            priority=priority
        )
        
        # For high priority requests, process immediately
        if priority in [RequestPriority.CRITICAL, RequestPriority.HIGH]:
            return await self._process_request(request)
        
        # Add to queue for normal/low priority
        if await self.request_queue.put(request):
            # Wait for processing (simplified - in production would use callbacks)
            await asyncio.sleep(0.1)  # Allow time for processing
            return APIResponse(
                request_id=request.request_id,
                provider=provider,
                success=True,
                data={'message': 'Request queued for processing'},
                response_time=0.1
            )
        else:
            return APIResponse(
                request_id=request.request_id,
                provider=provider,
                success=False,
                error_message="Request queue full",
                response_time=0.0
            )
    
    def get_gateway_status(self) -> Dict[str, Any]:
        """Get comprehensive gateway status"""
        total_requests = sum(m.total_requests for m in self.metrics.values())
        total_successes = sum(m.successful_requests for m in self.metrics.values())
        
        overall_success_rate = (total_successes / total_requests * 100) if total_requests > 0 else 0
        
        # Determine overall status
        healthy_providers = sum(1 for m in self.metrics.values() if m.is_healthy())
        total_providers = len(self.metrics)
        
        if healthy_providers == total_providers:
            status = GatewayStatus.HEALTHY
        elif healthy_providers >= total_providers * 0.5:
            status = GatewayStatus.DEGRADED
        else:
            status = GatewayStatus.UNHEALTHY
        
        return {
            'status': status.value,
            'overall_success_rate': round(overall_success_rate, 2),
            'total_requests': total_requests,
            'cache_entries': len(self.cache),
            'queue_status': self.request_queue.get_queue_status(),
            'workers_active': len([w for w in self.workers if not w.done()]),
            'providers': {
                provider.value: {
                    'healthy': metrics.is_healthy(),
                    'success_rate': round(metrics.get_success_rate(), 2),
                    'total_requests': metrics.total_requests,
                    'average_response_time': round(metrics.average_response_time, 3),
                    'circuit_breaker_state': self.circuit_breakers[provider].state,
                    'circuit_breaker_trips': self.circuit_breakers[provider].trip_count
                }
                for provider, metrics in self.metrics.items()
            }
        }

# Global gateway instance
_api_gateway: Optional[APIGateway] = None

async def get_api_gateway() -> APIGateway:
    """Get global API gateway instance"""
    global _api_gateway
    if _api_gateway is None:
        _api_gateway = APIGateway()
        await _api_gateway.start()
    return _api_gateway 