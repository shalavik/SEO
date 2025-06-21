"""
Twitter API v2 Integration for Phase 4C Executive Discovery

This module provides production-ready Twitter API integration for executive discovery:
- Twitter API v2 with OAuth 2.0 authentication
- Rate limiting compliance (300 requests per 15-minute window)
- Advanced search queries for executive discovery
- Enhanced bio parsing with official API data
- Company association validation and confidence scoring
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import re
from urllib.parse import quote_plus

from ..config.credential_manager import get_credential_manager, APIProvider
from ..models import ExecutiveContact

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class TwitterProfile:
    """Twitter profile information"""
    id: str
    username: str
    name: str
    description: str
    verified: bool = False
    followers_count: int = 0
    following_count: int = 0
    tweet_count: int = 0
    location: Optional[str] = None
    url: Optional[str] = None
    profile_image_url: Optional[str] = None
    created_at: Optional[str] = None
    public_metrics: Dict[str, int] = field(default_factory=dict)
    
    def get_executive_indicators(self) -> List[str]:
        """Extract executive role indicators from profile"""
        indicators = []
        description_lower = self.description.lower()
        
        # Executive titles
        executive_titles = [
            'ceo', 'chief executive officer', 'chief executive',
            'cto', 'chief technology officer', 'chief technical officer',
            'cfo', 'chief financial officer', 'chief finance officer',
            'coo', 'chief operating officer', 'chief operations officer',
            'founder', 'co-founder', 'co founder',
            'director', 'managing director', 'md',
            'president', 'vice president', 'vp',
            'owner', 'proprietor', 'principal',
            'partner', 'managing partner'
        ]
        
        for title in executive_titles:
            if title in description_lower:
                indicators.append(title)
        
        return indicators
    
    def get_company_mentions(self) -> List[str]:
        """Extract company mentions from profile"""
        mentions = []
        
        # Look for company indicators in description
        company_patterns = [
            r'@(\w+)',  # @company mentions
            r'(?:at|work at|working at|employed at)\s+([A-Z][a-zA-Z\s&]+)',
            r'(?:ceo|founder|director)\s+(?:of|at)\s+([A-Z][a-zA-Z\s&]+)',
            r'([A-Z][a-zA-Z\s&]+)\s+(?:ltd|limited|llc|inc|corp|plc)',
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, self.description, re.IGNORECASE)
            mentions.extend(matches)
        
        return [mention.strip() for mention in mentions if len(mention.strip()) > 2]
    
    def calculate_executive_confidence(self, target_company: str) -> float:
        """Calculate confidence that this is an executive profile"""
        confidence = 0.0
        
        # Base confidence from verification
        if self.verified:
            confidence += 0.3
        
        # Executive title indicators
        executive_indicators = self.get_executive_indicators()
        if executive_indicators:
            confidence += 0.4
        
        # Company association
        company_mentions = self.get_company_mentions()
        if target_company.lower() in ' '.join(company_mentions).lower():
            confidence += 0.4
        
        # Follower count indicates influence
        if self.followers_count > 1000:
            confidence += 0.1
        if self.followers_count > 10000:
            confidence += 0.1
        
        # Professional URL/website
        if self.url and ('linkedin' in self.url or 'company' in self.url):
            confidence += 0.1
        
        return min(confidence, 1.0)

class TwitterRateLimiter:
    """Twitter API v2 rate limiter (300 requests per 15 minutes)"""
    
    def __init__(self, max_requests: int = 300, time_window: int = 900):  # 15 minutes
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self, endpoint: str = "default") -> bool:
        """Acquire rate limit slot for specific endpoint"""
        async with self.lock:
            now = datetime.now()
            
            # Remove old requests outside time window
            cutoff = now - timedelta(seconds=self.time_window)
            self.requests = [req_time for req_time in self.requests if req_time > cutoff]
            
            # Check if we can make request
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest_request = min(self.requests)
                wait_time = (oldest_request + timedelta(seconds=self.time_window) - now).total_seconds()
                
                if wait_time > 0:
                    logger.info(f"Twitter rate limit reached, waiting {wait_time:.2f} seconds")
                    await asyncio.sleep(wait_time)
                    return await self.acquire(endpoint)  # Recursive call after waiting
            
            # Record this request
            self.requests.append(now)
            return True

class TwitterAPIClient:
    """Production Twitter API v2 client"""
    
    def __init__(self):
        self.base_url = "https://api.twitter.com/2"
        self.credential_manager = get_credential_manager()
        self.rate_limiter = TwitterRateLimiter()
        self.session = None
        
        # Cache for API results
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'UK-SEO-Lead-Generator/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key for request"""
        cache_data = f"{endpoint}:{json.dumps(sorted(params.items()))}"
        return cache_data
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        if 'timestamp' not in cache_entry:
            return False
        
        cache_time = datetime.fromisoformat(cache_entry['timestamp'])
        return (datetime.now() - cache_time).total_seconds() < self.cache_ttl
    
    async def _make_api_request(self, endpoint: str, params: Dict = None) -> Tuple[bool, Any]:
        """
        Make authenticated Twitter API request
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters
            
        Returns:
            Tuple of (success, data/error_message)
        """
        # Check cache first
        cache_key = self._get_cache_key(endpoint, params or {})
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if self._is_cache_valid(cache_entry):
                logger.info(f"Twitter cache hit for {endpoint}")
                return True, cache_entry['data']
        
        # Get authentication headers
        headers = self.credential_manager.get_authentication_headers(APIProvider.TWITTER)
        if not headers:
            return False, "No valid Twitter API credentials available"
        
        # Rate limiting
        await self.rate_limiter.acquire(endpoint)
        
        try:
            url = f"{self.base_url}{endpoint}"
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Cache successful response
                    self.cache[cache_key] = {
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    return True, data
                
                elif response.status == 401:
                    error_msg = "Twitter authentication failed - invalid Bearer token"
                    self.credential_manager.mark_credential_invalid(
                        APIProvider.TWITTER, 
                        error_msg
                    )
                    return False, error_msg
                
                elif response.status == 429:
                    error_msg = "Twitter rate limit exceeded"
                    logger.warning(error_msg)
                    return False, error_msg
                
                else:
                    error_msg = f"Twitter API error: HTTP {response.status}"
                    error_text = await response.text()
                    logger.error(f"{error_msg} - {error_text}")
                    return False, error_msg
                    
        except asyncio.TimeoutError:
            error_msg = "Twitter API request timeout"
            logger.error(error_msg)
            return False, error_msg
        
        except Exception as e:
            error_msg = f"Twitter API request failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    async def search_users(self, query: str, max_results: int = 10) -> List[TwitterProfile]:
        """
        Search for Twitter users
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of TwitterProfile objects
        """
        logger.info(f"Searching Twitter users for: {query}")
        
        params = {
            'query': query,
            'max_results': min(max_results, 100),  # API limit
            'user.fields': 'id,username,name,description,verified,public_metrics,location,url,profile_image_url,created_at'
        }
        
        success, data = await self._make_api_request('/users/search', params)
        
        if not success:
            logger.error(f"Twitter user search failed: {data}")
            return []
        
        profiles = []
        users = data.get('data', [])
        
        for user in users:
            profile = TwitterProfile(
                id=user['id'],
                username=user['username'],
                name=user['name'],
                description=user.get('description', ''),
                verified=user.get('verified', False),
                location=user.get('location'),
                url=user.get('url'),
                profile_image_url=user.get('profile_image_url'),
                created_at=user.get('created_at'),
                public_metrics=user.get('public_metrics', {}),
                followers_count=user.get('public_metrics', {}).get('followers_count', 0),
                following_count=user.get('public_metrics', {}).get('following_count', 0),
                tweet_count=user.get('public_metrics', {}).get('tweet_count', 0)
            )
            profiles.append(profile)
        
        logger.info(f"Found {len(profiles)} Twitter profiles for '{query}'")
        return profiles
    
    async def get_user_by_username(self, username: str) -> Optional[TwitterProfile]:
        """
        Get Twitter user by username
        
        Args:
            username: Twitter username (without @)
            
        Returns:
            TwitterProfile object or None
        """
        logger.info(f"Getting Twitter user: @{username}")
        
        params = {
            'user.fields': 'id,username,name,description,verified,public_metrics,location,url,profile_image_url,created_at'
        }
        
        success, data = await self._make_api_request(f'/users/by/username/{username}', params)
        
        if not success:
            logger.error(f"Twitter user lookup failed for @{username}: {data}")
            return None
        
        user_data = data.get('data')
        if not user_data:
            return None
        
        profile = TwitterProfile(
            id=user_data['id'],
            username=user_data['username'],
            name=user_data['name'],
            description=user_data.get('description', ''),
            verified=user_data.get('verified', False),
            location=user_data.get('location'),
            url=user_data.get('url'),
            profile_image_url=user_data.get('profile_image_url'),
            created_at=user_data.get('created_at'),
            public_metrics=user_data.get('public_metrics', {}),
            followers_count=user_data.get('public_metrics', {}).get('followers_count', 0),
            following_count=user_data.get('public_metrics', {}).get('following_count', 0),
            tweet_count=user_data.get('public_metrics', {}).get('tweet_count', 0)
        )
        
        logger.info(f"Retrieved Twitter profile for @{username}")
        return profile
    
    def _generate_search_queries(self, company_name: str) -> List[str]:
        """Generate targeted search queries for executive discovery"""
        # Clean company name
        clean_name = re.sub(r'\b(ltd|limited|llc|inc|corp|plc)\b', '', company_name, flags=re.IGNORECASE).strip()
        
        queries = [
            # Company name with executive titles
            f'{clean_name} CEO',
            f'{clean_name} founder',
            f'{clean_name} director',
            f'{clean_name} owner',
            
            # Quoted company name
            f'"{clean_name}" CEO',
            f'"{clean_name}" founder',
            
            # Bio mentions
            f'CEO of {clean_name}',
            f'founder of {clean_name}',
            f'director at {clean_name}',
            
            # Company domain/website
            f'{clean_name.replace(" ", "").lower()}.com',
            f'{clean_name.replace(" ", "").lower()}.co.uk',
        ]
        
        return queries[:5]  # Limit to 5 queries to manage rate limits
    
    async def discover_company_executives(self, company_name: str) -> List[TwitterProfile]:
        """
        Discover executives for a company using multiple search strategies
        
        Args:
            company_name: Company name to search for
            
        Returns:
            List of TwitterProfile objects for potential executives
        """
        logger.info(f"Discovering Twitter executives for: {company_name}")
        
        all_profiles = []
        seen_ids = set()
        
        search_queries = self._generate_search_queries(company_name)
        
        for query in search_queries:
            try:
                profiles = await self.search_users(query, max_results=5)
                
                for profile in profiles:
                    # Avoid duplicates
                    if profile.id in seen_ids:
                        continue
                    
                    seen_ids.add(profile.id)
                    
                    # Filter for potential executives
                    confidence = profile.calculate_executive_confidence(company_name)
                    if confidence >= 0.3:  # Minimum confidence threshold
                        all_profiles.append(profile)
                
                # Small delay between queries to be respectful
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error searching Twitter for '{query}': {e}")
                continue
        
        # Sort by confidence score
        all_profiles.sort(key=lambda p: p.calculate_executive_confidence(company_name), reverse=True)
        
        logger.info(f"Found {len(all_profiles)} potential executives on Twitter for {company_name}")
        return all_profiles[:10]  # Return top 10 candidates
    
    async def discover_executives(self, company_name: str) -> List[ExecutiveContact]:
        """
        Discover executives for a company and convert to ExecutiveContact objects
        
        Args:
            company_name: Company name to search for
            
        Returns:
            List of ExecutiveContact objects
        """
        start_time = datetime.now()
        
        try:
            # Discover Twitter profiles
            profiles = await self.discover_company_executives(company_name)
            
            # Convert to ExecutiveContact objects
            executives = []
            
            for profile in profiles:
                confidence = profile.calculate_executive_confidence(company_name)
                executive_indicators = profile.get_executive_indicators()
                
                # Determine title from indicators
                title = "Executive"
                if executive_indicators:
                    title = executive_indicators[0].upper()
                
                # Create ExecutiveContact
                executive = ExecutiveContact(
                    name=profile.name,
                    title=title,
                    company=company_name,
                    email=None,  # Not available from Twitter
                    phone=None,  # Not available from Twitter
                    linkedin_url=profile.url if profile.url and 'linkedin' in profile.url else None,
                    source="twitter_api",
                    confidence=confidence,
                    extraction_method="twitter_api_v2",
                    metadata={
                        'twitter_username': profile.username,
                        'twitter_id': profile.id,
                        'verified': profile.verified,
                        'followers_count': profile.followers_count,
                        'description': profile.description,
                        'location': profile.location,
                        'executive_indicators': executive_indicators,
                        'company_mentions': profile.get_company_mentions(),
                        'api_version': 'v2'
                    }
                )
                
                executives.append(executive)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Twitter discovery complete: {len(executives)} executives found in {processing_time:.2f}s")
            
            return executives
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Twitter discovery failed: {str(e)} (time: {processing_time:.2f}s)")
            return []
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get Twitter API status and performance metrics"""
        return {
            'provider': 'twitter_api_v2',
            'base_url': self.base_url,
            'rate_limiter': {
                'max_requests': self.rate_limiter.max_requests,
                'time_window': self.rate_limiter.time_window,
                'current_requests': len(self.rate_limiter.requests)
            },
            'cache': {
                'entries': len(self.cache),
                'ttl_hours': self.cache_ttl / 3600
            },
            'credentials_valid': self.credential_manager.is_provider_available(APIProvider.TWITTER)
        }

# Convenience function for easy integration
async def discover_executives_twitter(company_name: str) -> List[ExecutiveContact]:
    """
    Convenience function for Twitter executive discovery
    
    Args:
        company_name: Company name to search for
        
    Returns:
        List of ExecutiveContact objects
    """
    async with TwitterAPIClient() as api:
        return await api.discover_executives(company_name) 