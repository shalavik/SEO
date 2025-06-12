🎨🎨🎨 ENTERING CREATIVE PHASE: ARCHITECTURE DESIGN 🎨🎨🎨

# CREATIVE PHASE: API Integration Strategy Design

## PROBLEM STATEMENT

Design a robust API integration strategy for the UK company lead generation system, focusing on Google PageSpeed Insights API and future integrations. The strategy must:

1. **Handle rate limits** - Google PageSpeed API free tier: 25 requests/hour, 25,000/day
2. **Ensure reliability** - Graceful error handling and retry logic
3. **Support scalability** - Queue management for large datasets
4. **Enable monitoring** - Track API usage, success rates, and performance
5. **Future-proof design** - Easy integration of additional APIs (Clearbit, Hunter, etc.)

### Core Requirements
- Process 1000+ companies efficiently within rate limits
- 95%+ success rate for API calls
- Automatic retry with exponential backoff
- Comprehensive error logging and monitoring
- Modular design for easy API additions

## OPTIONS ANALYSIS

### Option 1: Simple Sequential API Calls
**Description**: Basic synchronous API calls with simple rate limiting

**Implementation**:
```python
import time
import requests
from datetime import datetime, timedelta

class SimpleAPIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.last_request_time = None
        self.requests_per_hour = 25
        
    def make_request(self, url):
        # Simple rate limiting
        if self.last_request_time:
            elapsed = datetime.now() - self.last_request_time
            if elapsed < timedelta(hours=1) / self.requests_per_hour:
                time.sleep((timedelta(hours=1) / self.requests_per_hour - elapsed).total_seconds())
        
        response = requests.get(url, params={'key': self.api_key})
        self.last_request_time = datetime.now()
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Error: {response.status_code}")
```

**Pros**:
- Simple to implement and understand
- Low complexity and memory usage
- Easy debugging and monitoring
- Predictable behavior

**Cons**:
- Inefficient for large datasets (40+ hours for 1000 companies)
- No retry logic for failures
- No queue management or batching
- Single point of failure

**Complexity**: Low
**Implementation Time**: 1-2 days

### Option 2: Asynchronous Queue-Based System
**Description**: Async processing with intelligent queue management and rate limiting

**Implementation**:
```python
import asyncio
import aiohttp
from asyncio import Queue
from datetime import datetime, timedelta
import logging

class AsyncAPIManager:
    def __init__(self, api_key, rate_limit=25, time_window=3600):
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.request_queue = Queue()
        self.response_queue = Queue()
        self.request_times = []
        
    async def process_requests(self):
        """Main processing loop with rate limiting"""
        while True:
            # Wait for rate limit window
            await self._wait_for_rate_limit()
            
            try:
                request_data = await asyncio.wait_for(
                    self.request_queue.get(), timeout=1.0
                )
                
                result = await self._make_api_call(request_data)
                await self.response_queue.put(result)
                
            except asyncio.TimeoutError:
                # No more requests, continue checking
                continue
            except Exception as e:
                logging.error(f"API call failed: {e}")
                # Handle error - could retry or mark as failed
    
    async def _wait_for_rate_limit(self):
        """Intelligent rate limiting based on request history"""
        now = datetime.now()
        
        # Remove old requests outside the time window
        self.request_times = [
            req_time for req_time in self.request_times
            if now - req_time < timedelta(seconds=self.time_window)
        ]
        
        # If we're at the rate limit, wait
        if len(self.request_times) >= self.rate_limit:
            oldest_request = min(self.request_times)
            wait_time = (oldest_request + timedelta(seconds=self.time_window) - now).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
    
    async def _make_api_call(self, request_data):
        """Make actual API call with retry logic"""
        for attempt in range(3):  # Max 3 attempts
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        request_data['url'],
                        params={'key': self.api_key}
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            self.request_times.append(datetime.now())
                            return {'success': True, 'data': data, 'request': request_data}
                        elif response.status == 429:  # Rate limited
                            # Exponential backoff
                            wait_time = (2 ** attempt) * 60
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            return {'success': False, 'error': f"HTTP {response.status}", 'request': request_data}
                            
            except Exception as e:
                if attempt == 2:  # Last attempt
                    return {'success': False, 'error': str(e), 'request': request_data}
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

**Pros**:
- Efficient async processing
- Intelligent rate limiting
- Built-in retry logic with exponential backoff
- Queue management for large datasets
- Better resource utilization

**Cons**:
- More complex implementation
- Async debugging complexity
- Memory management for queues
- Requires async/await understanding

**Complexity**: Medium-High
**Implementation Time**: 4-5 days

### Option 3: Enterprise-Grade API Gateway
**Description**: Full-featured API management with monitoring, caching, and multiple provider support

**Implementation**:
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import redis
import json
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class APIProvider:
    name: str
    base_url: str
    rate_limit: int
    time_window: int
    retry_attempts: int
    timeout: int

class APIGateway:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.providers = {}
        self.request_history = {}
        
    def register_provider(self, provider: APIProvider, api_client):
        """Register an API provider with its client"""
        self.providers[provider.name] = {
            'config': provider,
            'client': api_client
        }
        
    async def make_request(self, provider_name: str, request_data: Dict):
        """Universal API request method with caching and monitoring"""
        
        # Check cache first
        cache_key = self._generate_cache_key(provider_name, request_data)
        cached_result = self.redis.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        # Rate limiting check
        if not await self._can_make_request(provider_name):
            return {'success': False, 'error': 'Rate limit exceeded', 'retry_after': self._get_retry_after(provider_name)}
        
        # Make the request
        provider = self.providers[provider_name]
        result = await provider['client'].request(request_data)
        
        # Cache successful results
        if result.get('success'):
            self.redis.setex(
                cache_key, 
                timedelta(hours=24).total_seconds(),  # Cache for 24 hours
                json.dumps(result)
            )
        
        # Update monitoring
        self._update_metrics(provider_name, result)
        
        return result
    
    def get_provider_status(self, provider_name: str) -> Dict:
        """Get current status and metrics for a provider"""
        metrics_key = f"api_metrics:{provider_name}"
        metrics = self.redis.hgetall(metrics_key)
        
        return {
            'requests_today': int(metrics.get('requests_today', 0)),
            'success_rate': float(metrics.get('success_rate', 0)),
            'avg_response_time': float(metrics.get('avg_response_time', 0)),
            'last_error': metrics.get('last_error'),
            'rate_limit_status': self._get_rate_limit_status(provider_name)
        }
```

**Pros**:
- Enterprise-level features (caching, monitoring, metrics)
- Multi-provider support from day one
- Comprehensive error handling and recovery
- Detailed analytics and monitoring
- Production-ready scalability

**Cons**:
- Significant implementation complexity
- Requires Redis infrastructure
- Over-engineered for current needs
- Higher maintenance overhead

**Complexity**: High
**Implementation Time**: 1-2 weeks

### Option 4: Hybrid Lightweight Gateway
**Description**: Balanced approach with essential features but without over-engineering

**Implementation**:
```python
class LightweightAPIGateway:
    def __init__(self):
        self.providers = {}
        self.request_cache = {}  # Simple in-memory cache
        self.metrics = {}
        
    def register_provider(self, name: str, client_class, config: Dict):
        """Register API provider with configuration"""
        self.providers[name] = {
            'client': client_class(config),
            'config': config,
            'requests_made': 0,
            'success_count': 0,
            'error_count': 0
        }
        
    async def request(self, provider_name: str, endpoint: str, params: Dict):
        """Make API request with built-in rate limiting and retry"""
        provider = self.providers[provider_name]
        
        # Simple cache check
        cache_key = f"{provider_name}:{endpoint}:{hash(str(params))}"
        if cache_key in self.request_cache:
            cache_entry = self.request_cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(hours=1):
                return cache_entry['data']
        
        # Rate limiting
        if not self._check_rate_limit(provider_name):
            await self._wait_for_rate_limit(provider_name)
        
        # Make request with retry
        result = await self._make_request_with_retry(provider, endpoint, params)
        
        # Cache and metrics
        if result.get('success'):
            self.request_cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }
            provider['success_count'] += 1
        else:
            provider['error_count'] += 1
            
        provider['requests_made'] += 1
        
        return result
```

**Pros**:
- Good balance of features and complexity
- Built-in caching and metrics
- Easy to extend with new providers
- Reasonable implementation timeline
- Production-ready with growth potential

**Cons**:
- Still moderately complex
- In-memory cache limitations
- Not as full-featured as enterprise solution
- Requires careful testing

**Complexity**: Medium
**Implementation Time**: 3-4 days

🎨 CREATIVE CHECKPOINT: API Integration Options Evaluated 🎨

## DECISION

**Chosen Option: Option 4 - Hybrid Lightweight Gateway**

### Rationale

After evaluating all options against our requirements and constraints:

1. **Feature Balance**: Provides essential enterprise features without over-engineering
2. **Implementation Timeline**: Fits within our 3-4 day API integration development window
3. **Scalability**: Designed for growth but not over-complicated initially
4. **Maintainability**: Clean architecture that's easy to understand and extend
5. **Performance**: Built-in caching and intelligent rate limiting
6. **Future-Proofing**: Easy to add new API providers as needed

### Implementation Plan

#### Core Gateway Architecture
```python
class UKLeadAPIGateway:
    def __init__(self):
        self.providers = {
            'google_pagespeed': GooglePageSpeedProvider(),
            'company_data': CompanyDataProvider(),  # Future: Companies House API
            'contact_enrichment': ContactProvider()  # Future: Hunter.io, Clearbit
        }
        
        self.rate_limiters = {
            'google_pagespeed': RateLimiter(25, 3600),  # 25/hour
            'company_data': RateLimiter(600, 3600),     # Example: 600/hour
            'contact_enrichment': RateLimiter(100, 3600) # Example: 100/hour
        }
        
        self.cache = SimpleCache(max_size=1000, ttl_hours=24)
        self.metrics = MetricsCollector()
```

#### Google PageSpeed Integration
```python
class GooglePageSpeedProvider:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        
    async def analyze_website(self, url: str, strategy='mobile'):
        """Analyze website SEO using PageSpeed Insights"""
        params = {
            'url': url,
            'key': self.api_key,
            'strategy': strategy,
            'category': ['PERFORMANCE', 'SEO', 'BEST_PRACTICES']
        }
        
        try:
            response = await self._make_request(params)
            return self._parse_pagespeed_response(response)
        except Exception as e:
            return {'success': False, 'error': str(e), 'url': url}
    
    def _parse_pagespeed_response(self, response):
        """Extract relevant SEO data from PageSpeed response"""
        lighthouse_result = response.get('lighthouseResult', {})
        audits = lighthouse_result.get('audits', {})
        
        return {
            'success': True,
            'performance_score': lighthouse_result.get('categories', {}).get('performance', {}).get('score', 0) * 100,
            'seo_score': lighthouse_result.get('categories', {}).get('seo', {}).get('score', 0) * 100,
            'mobile_friendly': audits.get('viewport', {}).get('score') == 1,
            'meta_description': audits.get('meta-description', {}).get('score') == 1,
            'h1_tags': audits.get('heading-order', {}).get('score') == 1,
            'load_time': audits.get('speed-index', {}).get('numericValue', 0) / 1000,
            'critical_issues': self._extract_critical_issues(audits)
        }
```

#### Rate Limiting Strategy
```python
class RateLimiter:
    def __init__(self, requests_per_window: int, window_seconds: int):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.request_times = []
        
    async def acquire(self):
        """Wait if necessary to respect rate limits"""
        now = datetime.now()
        
        # Remove old requests
        self.request_times = [
            req_time for req_time in self.request_times
            if now - req_time < timedelta(seconds=self.window_seconds)
        ]
        
        # Check if we need to wait
        if len(self.request_times) >= self.requests_per_window:
            oldest_request = min(self.request_times)
            wait_time = (oldest_request + timedelta(seconds=self.window_seconds) - now).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time + 1)  # Add 1 second buffer
        
        # Record this request
        self.request_times.append(now)
```

#### Expected Integration Workflow
```
UK Company → API Gateway → Rate Limiter → Google PageSpeed API
     ↓              ↓             ↓                 ↓
Database ← Parsed Results ← Cache Check ← Raw API Response
```

### Validation Criteria
- [ ] Process 1000+ companies within Google's rate limits (40+ hours acceptable)
- [ ] Achieve 95%+ success rate for API calls
- [ ] Automatic retry with exponential backoff works correctly
- [ ] Cache reduces redundant API calls by 30%+
- [ ] Easy integration of new API providers

🎨🎨🎨 EXITING CREATIVE PHASE - DECISION MADE 🎨🎨🎨

## SUMMARY

**Decision**: Hybrid Lightweight API Gateway with Intelligent Rate Limiting
**Key Innovation**: Balanced feature set optimized for growth without over-engineering
**Implementation Priority**: High (critical for SEO analysis)
**Dependencies**: Async processing, caching system, metrics collection

This strategy provides a robust foundation for API integrations while maintaining simplicity and extensibility for future enhancements. 