"""
Social Media Profile Discovery - Phase 4B
Alternative data source for executive discovery via social media platforms
Focuses on Twitter, Facebook, and other professional networks
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import aiohttp
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

@dataclass
class SocialMediaProfile:
    """Social media profile information"""
    platform: str  # twitter, facebook, instagram, etc.
    profile_url: str
    username: str
    display_name: str
    bio: str = ""
    location: str = ""
    website: str = ""
    follower_count: Optional[int] = None
    verified: bool = False
    profile_image_url: str = ""
    company_mention: str = ""
    title_mention: str = ""
    confidence_score: float = 0.0
    extraction_method: str = ""

@dataclass
class SocialMediaExecutive:
    """Executive found via social media"""
    name: str
    title: str = ""
    company: str = ""
    profiles: List[SocialMediaProfile] = field(default_factory=list)
    confidence_score: float = 0.0
    discovery_method: str = ""
    contact_hints: Dict[str, str] = field(default_factory=dict)

class SocialMediaSearchEngine:
    """Search engine for finding social media profiles"""
    
    def __init__(self):
        self.session = None
        self.rate_limit_delay = 1.0  # Be respectful with rate limiting
        self.last_request_time = 0
        
        # Search patterns for different platforms
        self.platform_patterns = {
            'twitter': [
                'twitter.com',
                'x.com'
            ],
            'facebook': [
                'facebook.com',
                'fb.com'
            ],
            'linkedin': [
                'linkedin.com'
            ],
            'instagram': [
                'instagram.com'
            ]
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def search_social_profiles(self, person_name: str, company_name: str) -> List[SocialMediaProfile]:
        """Search for social media profiles of a person"""
        profiles = []
        
        # Create search queries
        search_queries = self._create_search_queries(person_name, company_name)
        
        for query in search_queries:
            await self._rate_limit()
            
            # Search using Google (publicly available information)
            google_results = await self._search_google(query)
            
            # Extract social media links from results
            social_links = self._extract_social_links(google_results)
            
            # Analyze each social link
            for link in social_links:
                profile = await self._analyze_social_profile(link, person_name, company_name)
                if profile and profile.confidence_score > 0.3:
                    profiles.append(profile)
        
        # Deduplicate profiles
        unique_profiles = self._deduplicate_profiles(profiles)
        
        return unique_profiles
    
    def _create_search_queries(self, person_name: str, company_name: str) -> List[str]:
        """Create search queries for finding social profiles"""
        queries = []
        
        # Basic person + company searches
        queries.append(f'"{person_name}" "{company_name}" twitter')
        queries.append(f'"{person_name}" "{company_name}" facebook')
        queries.append(f'"{person_name}" "{company_name}" linkedin')
        
        # Person + industry searches
        queries.append(f'"{person_name}" plumbing twitter')
        queries.append(f'"{person_name}" heating engineer facebook')
        
        # Company social searches
        queries.append(f'"{company_name}" twitter owner')
        queries.append(f'"{company_name}" facebook director')
        
        return queries
    
    async def _search_google(self, query: str) -> List[Dict[str, str]]:
        """Search Google for social media profiles (using publicly available data)"""
        # Note: In production, you would use Google Custom Search API
        # This is a simplified version for demonstration
        
        search_url = f"https://www.google.com/search?q={query}"
        
        try:
            if self.session:
                async with self.session.get(search_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_google_results(html)
            else:
                response = requests.get(search_url, timeout=30)
                if response.status_code == 200:
                    return self._parse_google_results(response.text)
        except Exception as e:
            logger.warning(f"Google search failed: {e}")
        
        return []
    
    def _parse_google_results(self, html: str) -> List[Dict[str, str]]:
        """Parse Google search results"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Find search result links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/url?q=' in href:
                # Extract actual URL from Google redirect
                url = href.split('/url?q=')[1].split('&')[0]
                
                # Get title and snippet
                title = link.get_text(strip=True)
                
                results.append({
                    'url': url,
                    'title': title,
                    'snippet': ''
                })
        
        return results[:10]  # Limit results
    
    def _extract_social_links(self, search_results: List[Dict[str, str]]) -> List[str]:
        """Extract social media links from search results"""
        social_links = []
        
        for result in search_results:
            url = result.get('url', '')
            
            for platform, domains in self.platform_patterns.items():
                for domain in domains:
                    if domain in url:
                        social_links.append(url)
                        break
        
        return list(set(social_links))  # Remove duplicates
    
    async def _analyze_social_profile(self, profile_url: str, person_name: str, 
                                    company_name: str) -> Optional[SocialMediaProfile]:
        """Analyze a social media profile"""
        try:
            platform = self._identify_platform(profile_url)
            
            if platform == 'twitter':
                return await self._analyze_twitter_profile(profile_url, person_name, company_name)
            elif platform == 'facebook':
                return await self._analyze_facebook_profile(profile_url, person_name, company_name)
            elif platform == 'linkedin':
                return await self._analyze_linkedin_profile(profile_url, person_name, company_name)
            else:
                return await self._analyze_generic_profile(profile_url, person_name, company_name, platform)
                
        except Exception as e:
            logger.warning(f"Profile analysis failed for {profile_url}: {e}")
            return None
    
    def _identify_platform(self, url: str) -> str:
        """Identify social media platform from URL"""
        for platform, domains in self.platform_patterns.items():
            for domain in domains:
                if domain in url:
                    return platform
        return 'unknown'
    
    async def _analyze_twitter_profile(self, url: str, person_name: str, 
                                     company_name: str) -> Optional[SocialMediaProfile]:
        """Analyze Twitter profile"""
        await self._rate_limit()
        
        try:
            if self.session:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_twitter_profile(html, url, person_name, company_name)
            else:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    return self._parse_twitter_profile(response.text, url, person_name, company_name)
        except Exception as e:
            logger.warning(f"Twitter profile fetch failed: {e}")
        
        return None
    
    def _parse_twitter_profile(self, html: str, url: str, person_name: str, 
                             company_name: str) -> Optional[SocialMediaProfile]:
        """Parse Twitter profile HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract username from URL
        username = url.split('/')[-1]
        
        # Find display name
        display_name = ""
        name_elements = soup.find_all(['h1', 'span'], string=re.compile(r'.+'))
        for element in name_elements:
            text = element.get_text(strip=True)
            if len(text) > 2 and len(text) < 50:
                display_name = text
                break
        
        # Find bio
        bio = ""
        bio_selectors = ['[data-testid="UserDescription"]', '.bio', '.description']
        for selector in bio_selectors:
            bio_element = soup.select_one(selector)
            if bio_element:
                bio = bio_element.get_text(strip=True)
                break
        
        # Calculate confidence score
        confidence = self._calculate_profile_confidence(
            display_name, bio, person_name, company_name
        )
        
        if confidence > 0.3:
            return SocialMediaProfile(
                platform='twitter',
                profile_url=url,
                username=username,
                display_name=display_name,
                bio=bio,
                confidence_score=confidence,
                extraction_method='twitter_scrape'
            )
        
        return None
    
    async def _analyze_facebook_profile(self, url: str, person_name: str, 
                                      company_name: str) -> Optional[SocialMediaProfile]:
        """Analyze Facebook profile"""
        # Facebook has strict anti-scraping measures
        # This would require Facebook Graph API in production
        
        # For demonstration, we'll create a basic profile
        username = url.split('/')[-1]
        
        return SocialMediaProfile(
            platform='facebook',
            profile_url=url,
            username=username,
            display_name=person_name,  # Assume name matches
            confidence_score=0.5,  # Medium confidence without actual data
            extraction_method='facebook_url'
        )
    
    async def _analyze_linkedin_profile(self, url: str, person_name: str, 
                                      company_name: str) -> Optional[SocialMediaProfile]:
        """Analyze LinkedIn profile"""
        # LinkedIn requires authentication for detailed data
        # This would use LinkedIn API in production
        
        username = url.split('/')[-1]
        
        return SocialMediaProfile(
            platform='linkedin',
            profile_url=url,
            username=username,
            display_name=person_name,
            confidence_score=0.7,  # Higher confidence for professional network
            extraction_method='linkedin_url'
        )
    
    async def _analyze_generic_profile(self, url: str, person_name: str, 
                                     company_name: str, platform: str) -> Optional[SocialMediaProfile]:
        """Analyze generic social media profile"""
        try:
            if self.session:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_generic_profile(html, url, person_name, company_name, platform)
        except Exception as e:
            logger.warning(f"Generic profile fetch failed: {e}")
        
        return None
    
    def _parse_generic_profile(self, html: str, url: str, person_name: str, 
                             company_name: str, platform: str) -> Optional[SocialMediaProfile]:
        """Parse generic social media profile"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title and meta description
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else ""
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ""
        
        # Calculate confidence
        confidence = self._calculate_profile_confidence(
            title_text, description, person_name, company_name
        )
        
        if confidence > 0.3:
            username = url.split('/')[-1]
            
            return SocialMediaProfile(
                platform=platform,
                profile_url=url,
                username=username,
                display_name=title_text,
                bio=description,
                confidence_score=confidence,
                extraction_method='generic_scrape'
            )
        
        return None
    
    def _calculate_profile_confidence(self, display_name: str, bio: str, 
                                    person_name: str, company_name: str) -> float:
        """Calculate confidence that profile belongs to the person"""
        confidence = 0.0
        
        # Check name similarity
        if person_name.lower() in display_name.lower():
            confidence += 0.4
        
        # Check for company mention
        if company_name.lower() in bio.lower():
            confidence += 0.3
        
        # Check for plumbing industry terms
        plumbing_terms = ['plumbing', 'plumber', 'heating', 'gas', 'boiler', 'engineer']
        for term in plumbing_terms:
            if term in bio.lower():
                confidence += 0.1
                break
        
        # Check for executive terms
        exec_terms = ['director', 'owner', 'ceo', 'manager', 'founder']
        for term in exec_terms:
            if term in bio.lower():
                confidence += 0.2
                break
        
        return min(1.0, confidence)
    
    def _deduplicate_profiles(self, profiles: List[SocialMediaProfile]) -> List[SocialMediaProfile]:
        """Remove duplicate profiles"""
        seen_urls = set()
        unique_profiles = []
        
        for profile in profiles:
            if profile.profile_url not in seen_urls:
                seen_urls.add(profile.profile_url)
                unique_profiles.append(profile)
        
        # Sort by confidence score
        unique_profiles.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return unique_profiles
    
    async def _rate_limit(self):
        """Implement rate limiting to be respectful"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()

class SocialMediaExecutiveExtractor:
    """Extract executives from social media platforms"""
    
    def __init__(self):
        self.search_engine = SocialMediaSearchEngine()
    
    async def find_executives_via_social_media(self, company_name: str) -> List[SocialMediaExecutive]:
        """Find executives using social media platforms"""
        logger.info(f"🔍 Searching social media for executives of: {company_name}")
        
        # Placeholder implementation for Phase 4B
        # In production, this would integrate with social media APIs
        
        return []

# Convenience function for testing
async def test_social_media_integration(company_name: str, executives: List[str] = None) -> Dict[str, Any]:
    """Test social media integration"""
    extractor = SocialMediaExecutiveExtractor()
    
    logger.info(f"Testing social media discovery for: {company_name}")
    social_executives = await extractor.find_executives_via_social_media(company_name)
    
    results = {
        'company_name': company_name,
        'executives_found': len(social_executives),
        'executives': []
    }
    
    for executive in social_executives:
        exec_data = {
            'name': executive.name,
            'confidence': executive.confidence_score,
            'discovery_method': executive.discovery_method,
            'profiles': []
        }
        
        for profile in executive.profiles:
            exec_data['profiles'].append({
                'platform': profile.platform,
                'url': profile.profile_url,
                'username': profile.username,
                'confidence': profile.confidence_score
            })
        
        results['executives'].append(exec_data)
    
    return results 