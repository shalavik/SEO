"""
LinkedIn Scraper Service

Stealth LinkedIn scraping for director profile discovery with:
- Anti-detection measures
- Rate limiting
- Profile matching
- Contact hint extraction
"""

import asyncio
import aiohttp
import random
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set
from urllib.parse import quote, urljoin
import re
from dataclasses import dataclass

from ..core.director_models import (
    LinkedInProfile, ContactHints, Director, DataSource, FreeDataBundle
)

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """LinkedIn search result"""
    name: str
    title: str
    company: str
    profile_url: str
    location: str
    confidence: float


class UserAgentRotator:
    """Rotate user agents to avoid detection"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
    def get_random_agent(self) -> str:
        """Get random user agent"""
        return random.choice(self.user_agents)


class RateLimiter:
    """Rate limiter for LinkedIn requests"""
    
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire rate limit permission"""
        async with self.lock:
            now = datetime.now()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < timedelta(minutes=1)]
            
            if len(self.requests) >= self.requests_per_minute:
                # Wait until we can make another request
                oldest_request = min(self.requests)
                wait_time = 60 - (now - oldest_request).total_seconds()
                if wait_time > 0:
                    logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                    await asyncio.sleep(wait_time)
            
            self.requests.append(now)


class LinkedInScraper:
    """LinkedIn scraper with stealth capabilities"""
    
    def __init__(self, rate_limit: int = 10):
        self.rate_limiter = RateLimiter(rate_limit)
        self.user_agent_rotator = UserAgentRotator()
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = "https://www.linkedin.com"
        
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30, connect=10),
            headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _add_stealth_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Add stealth headers to avoid detection"""
        stealth_headers = headers.copy()
        stealth_headers.update({
            'User-Agent': self.user_agent_rotator.get_random_agent(),
            'Referer': 'https://www.google.com/',
            'X-Forwarded-For': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        })
        return stealth_headers
    
    async def _make_request(self, url: str, params: Dict[str, str] = None) -> Optional[str]:
        """Make stealth request with rate limiting"""
        await self.rate_limiter.acquire()
        
        # Random delay between requests
        await asyncio.sleep(random.uniform(1.0, 3.0))
        
        headers = self._add_stealth_headers({})
        
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 429:
                    logger.warning("Rate limited by LinkedIn, backing off")
                    await asyncio.sleep(random.uniform(30, 60))
                    return None
                else:
                    logger.warning(f"LinkedIn request failed: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error making LinkedIn request: {e}")
            return None
    
    def _extract_profile_data(self, html: str, profile_url: str) -> Optional[LinkedInProfile]:
        """Extract profile data from LinkedIn HTML"""
        try:
            # Extract name
            name_match = re.search(r'<h1[^>]*class="[^"]*text-heading-xlarge[^"]*"[^>]*>([^<]+)</h1>', html)
            if not name_match:
                name_match = re.search(r'"name":"([^"]+)"', html)
            
            if not name_match:
                return None
            
            full_name = name_match.group(1).strip()
            
            # Extract headline
            headline_match = re.search(r'<div[^>]*class="[^"]*text-body-medium[^"]*"[^>]*>([^<]+)</div>', html)
            headline = headline_match.group(1).strip() if headline_match else None
            
            # Extract current position
            position_match = re.search(r'"title":"([^"]+)"', html)
            current_position = position_match.group(1).strip() if position_match else None
            
            # Extract company
            company_match = re.search(r'"companyName":"([^"]+)"', html)
            company = company_match.group(1).strip() if company_match else None
            
            # Extract location
            location_match = re.search(r'"geoLocationName":"([^"]+)"', html)
            location = location_match.group(1).strip() if location_match else None
            
            # Extract connections count
            connections_match = re.search(r'(\d+(?:,\d+)*)\s+connections?', html, re.IGNORECASE)
            connections = None
            if connections_match:
                connections_str = connections_match.group(1).replace(',', '')
                try:
                    connections = int(connections_str)
                except ValueError:
                    pass
            
            # Check for premium account indicators
            premium_account = 'premium' in html.lower() or 'linkedin premium' in html.lower()
            
            # Check for contact info availability
            contact_info_available = 'contact-info' in html or 'contact info' in html.lower()
            
            return LinkedInProfile(
                profile_url=profile_url,
                full_name=full_name,
                headline=headline,
                current_position=current_position,
                company=company,
                location=location,
                connections=connections,
                contact_info_available=contact_info_available,
                premium_account=premium_account,
                confidence=0.8  # Base confidence for scraped data
            )
            
        except Exception as e:
            logger.error(f"Error extracting profile data: {e}")
            return None
    
    def _extract_contact_hints(self, html: str) -> ContactHints:
        """Extract contact hints from LinkedIn profile"""
        email_patterns = []
        phone_patterns = []
        social_profiles = []
        contact_pages = []
        
        try:
            # Look for email patterns in text
            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_regex, html)
            email_patterns.extend(emails)
            
            # Look for phone patterns
            phone_regex = r'(?:\+44|0)\s*\d{2,4}\s*\d{3,4}\s*\d{3,4}'
            phones = re.findall(phone_regex, html)
            phone_patterns.extend(phones)
            
            # Look for social media links
            social_regex = r'https?://(?:www\.)?(?:twitter|facebook|instagram|github)\.com/[^\s"<>]+'
            socials = re.findall(social_regex, html)
            social_profiles.extend(socials)
            
            # Look for website/contact page links
            website_regex = r'https?://[^\s"<>]+(?:contact|about|team)[^\s"<>]*'
            websites = re.findall(website_regex, html)
            contact_pages.extend(websites)
            
        except Exception as e:
            logger.error(f"Error extracting contact hints: {e}")
        
        return ContactHints(
            email_patterns=list(set(email_patterns)),
            phone_patterns=list(set(phone_patterns)),
            social_profiles=list(set(social_profiles)),
            website_contact_pages=list(set(contact_pages)),
            confidence=0.6,  # Lower confidence for hints
            extraction_method="linkedin_scraping"
        )
    
    async def search_profiles(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search LinkedIn profiles"""
        search_url = f"{self.base_url}/search/results/people/"
        params = {
            'keywords': query,
            'origin': 'GLOBAL_SEARCH_HEADER'
        }
        
        html = await self._make_request(search_url, params)
        if not html:
            return []
        
        results = []
        try:
            # Extract search results (simplified pattern matching)
            # In a real implementation, you'd use more sophisticated parsing
            profile_pattern = r'<a[^>]*href="([^"]*\/in\/[^"]*)"[^>]*>.*?<span[^>]*>([^<]+)</span>'
            matches = re.findall(profile_pattern, html, re.DOTALL)
            
            for match in matches[:limit]:
                profile_url, name = match
                if not profile_url.startswith('http'):
                    profile_url = urljoin(self.base_url, profile_url)
                
                results.append(SearchResult(
                    name=name.strip(),
                    title="",  # Would need additional parsing
                    company="",  # Would need additional parsing
                    profile_url=profile_url,
                    location="",  # Would need additional parsing
                    confidence=0.7
                ))
                
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
        
        return results
    
    async def get_profile(self, profile_url: str) -> Optional[LinkedInProfile]:
        """Get LinkedIn profile data"""
        html = await self._make_request(profile_url)
        if not html:
            return None
        
        return self._extract_profile_data(html, profile_url)
    
    async def get_profile_with_hints(self, profile_url: str) -> tuple[Optional[LinkedInProfile], ContactHints]:
        """Get profile data with contact hints"""
        html = await self._make_request(profile_url)
        if not html:
            return None, ContactHints(confidence=0.0, extraction_method="failed")
        
        profile = self._extract_profile_data(html, profile_url)
        hints = self._extract_contact_hints(html)
        
        return profile, hints


class LinkedInDirectorMatcher:
    """Match directors with LinkedIn profiles"""
    
    def __init__(self):
        pass
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity score"""
        name1_clean = re.sub(r'[^\w\s]', '', name1.lower())
        name2_clean = re.sub(r'[^\w\s]', '', name2.lower())
        
        # Simple word overlap scoring
        words1 = set(name1_clean.split())
        words2 = set(name2_clean.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _calculate_company_similarity(self, company1: str, company2: str) -> float:
        """Calculate company name similarity"""
        if not company1 or not company2:
            return 0.0
        
        company1_clean = re.sub(r'[^\w\s]', '', company1.lower())
        company2_clean = re.sub(r'[^\w\s]', '', company2.lower())
        
        # Check for exact match or substring match
        if company1_clean == company2_clean:
            return 1.0
        elif company1_clean in company2_clean or company2_clean in company1_clean:
            return 0.8
        else:
            return 0.0
    
    def match_director_to_profile(self, director: Director, 
                                profile: LinkedInProfile, 
                                company_name: str) -> float:
        """Calculate match confidence between director and LinkedIn profile"""
        
        # Name similarity (most important)
        name_score = self._calculate_name_similarity(director.full_name, profile.full_name)
        
        # Company similarity
        company_score = 0.0
        if profile.company:
            company_score = self._calculate_company_similarity(company_name, profile.company)
        
        # Role/title similarity (if available)
        role_score = 0.0
        if profile.current_position and director.role:
            role_keywords = {
                'ceo': ['ceo', 'chief executive', 'managing director'],
                'director': ['director', 'board member'],
                'cfo': ['cfo', 'chief financial', 'finance director'],
                'coo': ['coo', 'chief operating', 'operations director']
            }
            
            role_key = director.role.value.replace('-', '_')
            if role_key in role_keywords:
                position_lower = profile.current_position.lower()
                for keyword in role_keywords[role_key]:
                    if keyword in position_lower:
                        role_score = 0.8
                        break
        
        # Weighted scoring
        total_score = (
            name_score * 0.6 +      # Name is most important
            company_score * 0.3 +   # Company match is important
            role_score * 0.1        # Role is nice to have
        )
        
        return min(total_score, 1.0)


class LinkedInScraperService:
    """Main LinkedIn scraper service"""
    
    def __init__(self, rate_limit: int = 10):
        self.rate_limit = rate_limit
        self.matcher = LinkedInDirectorMatcher()
    
    async def find_director_profiles(self, directors: List[Director], 
                                   company_name: str) -> FreeDataBundle:
        """Find LinkedIn profiles for directors"""
        start_time = datetime.now()
        linkedin_profiles = []
        contact_hints = []
        errors = []
        
        try:
            async with LinkedInScraper(self.rate_limit) as scraper:
                for director in directors:
                    try:
                        # Search for director
                        search_query = f"{director.full_name} {company_name}"
                        search_results = await scraper.search_profiles(search_query, limit=5)
                        
                        best_match = None
                        best_score = 0.0
                        
                        # Evaluate each search result
                        for result in search_results:
                            # Get full profile
                            profile = await scraper.get_profile(result.profile_url)
                            if profile:
                                # Calculate match score
                                match_score = self.matcher.match_director_to_profile(
                                    director, profile, company_name
                                )
                                
                                if match_score > best_score and match_score > 0.6:
                                    best_score = match_score
                                    best_match = profile
                        
                        if best_match:
                            # Update confidence with match score
                            best_match.confidence = best_score
                            linkedin_profiles.append(best_match)
                            
                            # Get contact hints
                            _, hints = await scraper.get_profile_with_hints(best_match.profile_url)
                            if hints.confidence > 0:
                                contact_hints.append(hints)
                            
                            logger.info(f"Found LinkedIn profile for {director.full_name} (confidence: {best_score:.2f})")
                        else:
                            logger.info(f"No suitable LinkedIn profile found for {director.full_name}")
                    
                    except Exception as e:
                        error_msg = f"Error processing {director.full_name}: {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        
        except Exception as e:
            error_msg = f"LinkedIn scraper error: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return FreeDataBundle(
            linkedin_profiles=linkedin_profiles,
            contact_hints=contact_hints,
            processing_time_ms=processing_time,
            sources_used=[DataSource.LINKEDIN_SCRAPER],
            errors=errors
        ) 