"""
LinkedIn Direct Enricher

P2.2 LINKEDIN DIRECT INTEGRATION
Discovers executives from public LinkedIn profiles without authentication.
Implements advanced scraping techniques for executive discovery.

Features:
- Public LinkedIn profile discovery
- Company page executive extraction
- LinkedIn URL validation and cleaning
- Executive role detection from profiles
- LinkedIn data confidence scoring
- Zero-cost architecture maintenance
"""

import asyncio
import logging
import random
import re
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urljoin, urlparse
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

from ..models import ExecutiveContact
from ..config import get_processing_config

logger = logging.getLogger(__name__)

@dataclass
class LinkedInProfile:
    """LinkedIn profile data structure"""
    name: str
    title: str
    company: str
    profile_url: str
    confidence: float = 0.0
    location: str = ""
    summary: str = ""

class LinkedInDirectEnricher:
    """P2.2 ENHANCED: LinkedIn direct integration for executive discovery"""
    
    def __init__(self):
        self.processing_config = get_processing_config()
        
        # P2.2: LinkedIn-specific user agents (less likely to be blocked)
        self.linkedin_user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # P2.2: LinkedIn search patterns for executive discovery
        self.linkedin_search_patterns = [
            # Direct company searches
            'site:linkedin.com/in "{company_name}" CEO',
            'site:linkedin.com/in "{company_name}" founder',
            'site:linkedin.com/in "{company_name}" director',
            'site:linkedin.com/in "{company_name}" owner',
            'site:linkedin.com/in "{company_name}" manager',
            
            # Industry-specific patterns
            'site:linkedin.com/in "{company_name}" "master plumber"',
            'site:linkedin.com/in "{company_name}" "qualified electrician"',
            'site:linkedin.com/in "{company_name}" "chartered engineer"',
            
            # Company page patterns
            'site:linkedin.com/company/{company_slug}',
            'site:linkedin.com/company/{company_slug}/people',
            
            # General executive patterns
            'linkedin.com/in {company_name} executive',
            'linkedin.com/in {company_name} leadership'
        ]
        
        # P2.2: Executive title patterns for LinkedIn
        self.executive_title_patterns = [
            r'(?i)(ceo|chief executive officer)',
            r'(?i)(founder|co-founder)',
            r'(?i)(managing director|md)',
            r'(?i)(director|executive director)',
            r'(?i)(owner|business owner)',
            r'(?i)(president|vice president)',
            r'(?i)(manager|general manager)',
            r'(?i)(head of|head)',
            r'(?i)(master plumber|qualified plumber)',
            r'(?i)(master electrician|qualified electrician)',
            r'(?i)(chartered engineer|senior engineer)'
        ]
        
        # Request session with LinkedIn-optimized settings
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
        
        # Rate limiting for LinkedIn (more conservative)
        self.last_request = 0
        self.min_delay = 3.0  # 3 seconds between LinkedIn requests
        
        logger.info("LinkedIn Direct Enricher initialized for P2.2 executive discovery")
    
    async def discover_executives(self, company_name: str, domain: str, 
                                industry: str = None) -> List[ExecutiveContact]:
        """P2.2 ENHANCED: Discover executives from LinkedIn profiles"""
        logger.info(f"🔗 P2.2: Starting LinkedIn direct discovery for: {company_name}")
        
        all_executives = []
        
        try:
            # Strategy 1: Search for LinkedIn profiles via search engines
            search_executives = await self._search_linkedin_profiles(company_name, domain)
            all_executives.extend(search_executives)
            
            # Strategy 2: Try to find company LinkedIn page
            company_executives = await self._discover_from_company_page(company_name, domain)
            all_executives.extend(company_executives)
            
            # Strategy 3: Industry-specific LinkedIn searches
            if industry:
                industry_executives = await self._search_industry_linkedin(company_name, industry)
                all_executives.extend(industry_executives)
            
            # Deduplicate and score
            unique_executives = self._deduplicate_linkedin_executives(all_executives)
            scored_executives = self._score_linkedin_confidence(unique_executives)
            
            logger.info(f"🎯 P2.2: LinkedIn discovery found {len(scored_executives)} unique executives")
            return scored_executives
            
        except Exception as e:
            logger.warning(f"❌ P2.2: LinkedIn discovery failed: {e}")
            return []
    
    async def _search_linkedin_profiles(self, company_name: str, domain: str) -> List[ExecutiveContact]:
        """Search for LinkedIn profiles using search engines"""
        executives = []
        
        try:
            # Generate LinkedIn search queries
            queries = self._generate_linkedin_queries(company_name, domain)
            
            for query in queries[:5]:  # Limit to top 5 queries
                try:
                    await self._enforce_rate_limit()
                    
                    # Use DuckDuckGo for LinkedIn searches (less blocking)
                    search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
                    
                    headers = {
                        'User-Agent': random.choice(self.linkedin_user_agents),
                        'Referer': 'https://duckduckgo.com/',
                        'DNT': '1'
                    }
                    
                    logger.debug(f"LinkedIn search: {query}")
                    
                    response = self.session.get(search_url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        # Extract LinkedIn URLs from search results
                        linkedin_urls = self._extract_linkedin_urls(response.text)
                        
                        # Process each LinkedIn URL
                        for url in linkedin_urls[:3]:  # Limit to top 3 per query
                            try:
                                profile = await self._scrape_linkedin_profile(url, company_name)
                                if profile:
                                    executive = self._convert_profile_to_executive(
                                        profile, company_name, domain
                                    )
                                    if executive:
                                        executives.append(executive)
                            except Exception as e:
                                logger.debug(f"Failed to scrape LinkedIn profile {url}: {e}")
                                continue
                    
                except Exception as e:
                    logger.debug(f"LinkedIn search query failed: {query} - {e}")
                    continue
            
            logger.info(f"LinkedIn profile search found {len(executives)} executives")
            return executives
            
        except Exception as e:
            logger.warning(f"LinkedIn profile search failed: {e}")
            return []
    
    async def _discover_from_company_page(self, company_name: str, domain: str) -> List[ExecutiveContact]:
        """Discover executives from LinkedIn company page"""
        executives = []
        
        try:
            # Generate possible LinkedIn company URLs
            company_slugs = self._generate_company_slugs(company_name)
            
            for slug in company_slugs:
                try:
                    await self._enforce_rate_limit()
                    
                    # Try company page URL
                    company_url = f"https://www.linkedin.com/company/{slug}"
                    
                    headers = {
                        'User-Agent': random.choice(self.linkedin_user_agents),
                        'Referer': 'https://www.linkedin.com/',
                    }
                    
                    logger.debug(f"Checking LinkedIn company page: {company_url}")
                    
                    response = self.session.get(company_url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        # Extract executive information from company page
                        page_executives = self._extract_executives_from_company_page(
                            response.text, company_name, domain
                        )
                        executives.extend(page_executives)
                        
                        # If we found the company page, try the people page
                        people_url = f"{company_url}/people"
                        await self._enforce_rate_limit()
                        
                        people_response = self.session.get(people_url, headers=headers, timeout=10)
                        if people_response.status_code == 200:
                            people_executives = self._extract_executives_from_people_page(
                                people_response.text, company_name, domain
                            )
                            executives.extend(people_executives)
                        
                        break  # Found the company, no need to try other slugs
                    
                except Exception as e:
                    logger.debug(f"Failed to check company page {slug}: {e}")
                    continue
            
            logger.info(f"LinkedIn company page found {len(executives)} executives")
            return executives
            
        except Exception as e:
            logger.warning(f"LinkedIn company page discovery failed: {e}")
            return []
    
    async def _search_industry_linkedin(self, company_name: str, industry: str) -> List[ExecutiveContact]:
        """Search for industry-specific LinkedIn profiles"""
        executives = []
        
        try:
            # Industry-specific search patterns
            industry_queries = [
                f'site:linkedin.com/in "{company_name}" {industry} owner',
                f'site:linkedin.com/in "{company_name}" {industry} director',
                f'linkedin.com/in {industry} {company_name}'
            ]
            
            for query in industry_queries:
                try:
                    await self._enforce_rate_limit()
                    
                    # Use Bing for industry searches
                    search_url = f"https://www.bing.com/search?q={quote_plus(query)}"
                    
                    headers = {
                        'User-Agent': random.choice(self.linkedin_user_agents),
                        'Referer': 'https://www.bing.com/',
                    }
                    
                    response = self.session.get(search_url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        linkedin_urls = self._extract_linkedin_urls(response.text)
                        
                        for url in linkedin_urls[:2]:  # Limit to top 2 per query
                            try:
                                profile = await self._scrape_linkedin_profile(url, company_name)
                                if profile:
                                    executive = self._convert_profile_to_executive(
                                        profile, company_name, ""
                                    )
                                    if executive:
                                        executives.append(executive)
                            except Exception as e:
                                logger.debug(f"Failed to scrape industry profile {url}: {e}")
                                continue
                
                except Exception as e:
                    logger.debug(f"Industry LinkedIn search failed: {query} - {e}")
                    continue
            
            logger.info(f"Industry LinkedIn search found {len(executives)} executives")
            return executives
            
        except Exception as e:
            logger.warning(f"Industry LinkedIn search failed: {e}")
            return []
    
    def _generate_linkedin_queries(self, company_name: str, domain: str) -> List[str]:
        """Generate LinkedIn search queries"""
        queries = []
        
        # Clean company name for search
        clean_name = company_name.replace('"', '').strip()
        
        for pattern in self.linkedin_search_patterns:
            try:
                # Generate company slug for LinkedIn URLs
                company_slug = self._generate_company_slugs(company_name)[0]
                
                query = pattern.format(
                    company_name=clean_name,
                    company_slug=company_slug
                )
                queries.append(query)
            except (KeyError, IndexError):
                # Skip patterns that don't match available variables
                continue
        
        return queries
    
    def _generate_company_slugs(self, company_name: str) -> List[str]:
        """Generate possible LinkedIn company slugs"""
        slugs = []
        
        # Clean company name
        clean_name = re.sub(r'[^\w\s]', '', company_name.lower())
        clean_name = re.sub(r'\s+', '-', clean_name.strip())
        
        # Generate variations
        slugs.append(clean_name)
        slugs.append(clean_name.replace('-', ''))
        slugs.append(clean_name.replace('-the-', '-'))
        
        # Remove common business suffixes
        suffixes = ['ltd', 'limited', 'plc', 'company', 'co', 'inc']
        for suffix in suffixes:
            if clean_name.endswith(f'-{suffix}'):
                slugs.append(clean_name.replace(f'-{suffix}', ''))
        
        return list(set(slugs))  # Remove duplicates
    
    def _extract_linkedin_urls(self, html: str) -> List[str]:
        """Extract LinkedIn profile URLs from search results"""
        urls = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all links
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href']
                
                # Check if it's a LinkedIn profile URL
                if self._is_linkedin_profile_url(href):
                    # Clean and validate URL
                    clean_url = self._clean_linkedin_url(href)
                    if clean_url and clean_url not in urls:
                        urls.append(clean_url)
            
            logger.debug(f"Extracted {len(urls)} LinkedIn URLs from search results")
            return urls[:10]  # Limit to top 10
            
        except Exception as e:
            logger.debug(f"Failed to extract LinkedIn URLs: {e}")
            return []
    
    def _is_linkedin_profile_url(self, url: str) -> bool:
        """Check if URL is a LinkedIn profile URL"""
        if not url:
            return False
        
        # LinkedIn profile patterns
        linkedin_patterns = [
            r'linkedin\.com/in/',
            r'linkedin\.com/pub/',
            r'linkedin\.com/profile/'
        ]
        
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in linkedin_patterns)
    
    def _clean_linkedin_url(self, url: str) -> Optional[str]:
        """Clean and validate LinkedIn URL"""
        try:
            # Remove tracking parameters and clean URL
            if url.startswith('//'):
                url = 'https:' + url
            elif not url.startswith('http'):
                url = 'https://' + url
            
            # Parse URL
            parsed = urlparse(url)
            
            # Ensure it's LinkedIn
            if 'linkedin.com' not in parsed.netloc.lower():
                return None
            
            # Clean path
            path = parsed.path.rstrip('/')
            
            # Reconstruct clean URL
            clean_url = f"https://www.linkedin.com{path}"
            
            return clean_url
            
        except Exception as e:
            logger.debug(f"Failed to clean LinkedIn URL {url}: {e}")
            return None
    
    async def _scrape_linkedin_profile(self, url: str, company_name: str) -> Optional[LinkedInProfile]:
        """Scrape LinkedIn profile for executive information"""
        try:
            await self._enforce_rate_limit()
            
            headers = {
                'User-Agent': random.choice(self.linkedin_user_agents),
                'Referer': 'https://www.linkedin.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            logger.debug(f"Scraping LinkedIn profile: {url}")
            
            response = self.session.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return self._parse_linkedin_profile(response.text, url, company_name)
            else:
                logger.debug(f"LinkedIn profile returned status {response.status_code}: {url}")
                return None
                
        except Exception as e:
            logger.debug(f"Failed to scrape LinkedIn profile {url}: {e}")
            return None
    
    def _parse_linkedin_profile(self, html: str, url: str, company_name: str) -> Optional[LinkedInProfile]:
        """Parse LinkedIn profile HTML for executive information"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract name (multiple possible selectors)
            name = self._extract_profile_name(soup)
            if not name:
                return None
            
            # Extract title
            title = self._extract_profile_title(soup)
            
            # Extract company
            company = self._extract_profile_company(soup, company_name)
            
            # Extract location
            location = self._extract_profile_location(soup)
            
            # Extract summary
            summary = self._extract_profile_summary(soup)
            
            # Validate that this profile is relevant to our company
            if not self._is_profile_relevant(name, title, company, company_name):
                return None
            
            # Calculate confidence
            confidence = self._calculate_profile_confidence(name, title, company, company_name)
            
            profile = LinkedInProfile(
                name=name,
                title=title or "Executive",
                company=company or company_name,
                profile_url=url,
                confidence=confidence,
                location=location or "",
                summary=summary or ""
            )
            
            logger.debug(f"Parsed LinkedIn profile: {name} ({title}) - Confidence: {confidence:.2f}")
            return profile
            
        except Exception as e:
            logger.debug(f"Failed to parse LinkedIn profile: {e}")
            return None
    
    def _extract_profile_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract name from LinkedIn profile"""
        # Multiple selectors for name extraction
        name_selectors = [
            'h1.text-heading-xlarge',
            'h1.pv-text-details__left-panel h1',
            '.pv-text-details__left-panel h1',
            'h1[data-anonymize="person-name"]',
            '.pv-top-card--list li:first-child',
            'h1.top-card-layout__title'
        ]
        
        for selector in name_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    name = element.get_text(strip=True)
                    if name and len(name) > 2:
                        return name
            except Exception:
                continue
        
        return None
    
    def _extract_profile_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract title from LinkedIn profile"""
        title_selectors = [
            '.text-body-medium.break-words',
            '.pv-text-details__left-panel .text-body-medium',
            '.pv-top-card--list li:nth-child(2)',
            '.top-card-layout__headline',
            '.pv-entity__summary-info h2'
        ]
        
        for selector in title_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text(strip=True)
                    if title and any(pattern.search(title) for pattern in [re.compile(p) for p in self.executive_title_patterns]):
                        return title
            except Exception:
                continue
        
        return None
    
    def _extract_profile_company(self, soup: BeautifulSoup, target_company: str) -> Optional[str]:
        """Extract company from LinkedIn profile"""
        company_selectors = [
            '.pv-entity__secondary-title',
            '.pv-entity__company-summary-info h3',
            '.experience-item__subtitle',
            '.pv-experience-section__company-name'
        ]
        
        for selector in company_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    company = element.get_text(strip=True)
                    if company and fuzz.ratio(company.lower(), target_company.lower()) > 70:
                        return company
            except Exception:
                continue
        
        return None
    
    def _extract_profile_location(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract location from LinkedIn profile"""
        location_selectors = [
            '.pv-text-details__left-panel .text-body-small',
            '.top-card-layout__first-subline',
            '.pv-top-card--list-bullet li'
        ]
        
        for selector in location_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    location = element.get_text(strip=True)
                    if location and ('UK' in location or 'United Kingdom' in location or 'England' in location):
                        return location
            except Exception:
                continue
        
        return None
    
    def _extract_profile_summary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract summary from LinkedIn profile"""
        summary_selectors = [
            '.pv-about__summary-text',
            '.pv-about-section .pv-about__summary-text',
            '.summary .pv-about__summary-text'
        ]
        
        for selector in summary_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    summary = element.get_text(strip=True)
                    if summary and len(summary) > 20:
                        return summary[:200]  # Limit to 200 chars
            except Exception:
                continue
        
        return None
    
    def _is_profile_relevant(self, name: str, title: str, company: str, target_company: str) -> bool:
        """Check if LinkedIn profile is relevant to our search"""
        if not name:
            return False
        
        # Check if name looks like a person's name
        if not self._is_valid_person_name(name):
            return False
        
        # Check if title indicates executive role
        if title:
            title_match = any(pattern.search(title) for pattern in [re.compile(p) for p in self.executive_title_patterns])
            if not title_match:
                return False
        
        # Check company relevance
        if company:
            company_similarity = fuzz.ratio(company.lower(), target_company.lower())
            if company_similarity < 60:
                return False
        
        return True
    
    def _is_valid_person_name(self, name: str) -> bool:
        """Validate if text looks like a person's name"""
        if not name or len(name) < 3 or len(name) > 50:
            return False
        
        # Should contain at least two words
        words = name.split()
        if len(words) < 2:
            return False
        
        # Should start with capital letters
        if not all(word[0].isupper() for word in words if word):
            return False
        
        # Should not contain numbers or special characters
        if re.search(r'[0-9@#$%^&*()+={}[\]|\\:";\'<>?/]', name):
            return False
        
        return True
    
    def _calculate_profile_confidence(self, name: str, title: str, company: str, target_company: str) -> float:
        """Calculate confidence score for LinkedIn profile"""
        confidence = 0.6  # Base confidence for LinkedIn profiles
        
        # Boost for valid name
        if name and self._is_valid_person_name(name):
            confidence += 0.1
        
        # Boost for executive title
        if title:
            title_match = any(pattern.search(title) for pattern in [re.compile(p) for p in self.executive_title_patterns])
            if title_match:
                confidence += 0.15
                
                # Extra boost for senior titles
                if any(keyword in title.lower() for keyword in ['ceo', 'founder', 'director']):
                    confidence += 0.1
        
        # Boost for company match
        if company:
            company_similarity = fuzz.ratio(company.lower(), target_company.lower())
            if company_similarity > 80:
                confidence += 0.15
            elif company_similarity > 60:
                confidence += 0.1
        
        return min(1.0, confidence)
    
    def _convert_profile_to_executive(self, profile: LinkedInProfile, company_name: str, domain: str) -> Optional[ExecutiveContact]:
        """Convert LinkedIn profile to ExecutiveContact"""
        try:
            # Parse name
            name_parts = profile.name.split()
            if len(name_parts) < 2:
                return None
            
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:])
            
            # Determine seniority tier
            seniority_tier = self._determine_seniority_tier(profile.title)
            
            executive = ExecutiveContact(
                first_name=first_name,
                last_name=last_name,
                full_name=profile.name,
                title=profile.title,
                company_name=company_name,
                email=None,  # Will be enriched later
                phone=None,
                bio=profile.summary,
                discovery_sources=[f"linkedin_direct_{profile.profile_url}"],
                confidence=profile.confidence,
                seniority_tier=seniority_tier,
                company_domain=domain,
                linkedin_url=profile.profile_url
            )
            
            return executive
            
        except Exception as e:
            logger.debug(f"Failed to convert LinkedIn profile to executive: {e}")
            return None
    
    def _determine_seniority_tier(self, title: str) -> str:
        """Determine executive seniority tier from LinkedIn title"""
        if not title:
            return 'tier_4'
        
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in ['ceo', 'chief executive', 'founder', 'owner']):
            return 'tier_1'
        elif any(keyword in title_lower for keyword in ['director', 'managing director', 'md', 'president']):
            return 'tier_2'
        elif any(keyword in title_lower for keyword in ['manager', 'head of', 'vice president']):
            return 'tier_3'
        else:
            return 'tier_4'
    
    def _extract_executives_from_company_page(self, html: str, company_name: str, domain: str) -> List[ExecutiveContact]:
        """Extract executives from LinkedIn company page"""
        executives = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for leadership section
            leadership_sections = soup.find_all(['div', 'section'], class_=re.compile(r'leadership|management|team'))
            
            for section in leadership_sections:
                # Extract executive information from leadership section
                exec_elements = section.find_all(['div', 'li'], class_=re.compile(r'person|employee|member'))
                
                for element in exec_elements:
                    try:
                        # Extract name and title
                        name_elem = element.find(['h3', 'h4', 'span'], class_=re.compile(r'name|title'))
                        title_elem = element.find(['p', 'span'], class_=re.compile(r'title|role|position'))
                        
                        if name_elem:
                            name = name_elem.get_text(strip=True)
                            title = title_elem.get_text(strip=True) if title_elem else "Executive"
                            
                            if self._is_valid_person_name(name):
                                # Create executive contact
                                name_parts = name.split()
                                if len(name_parts) >= 2:
                                    executive = ExecutiveContact(
                                        first_name=name_parts[0],
                                        last_name=' '.join(name_parts[1:]),
                                        full_name=name,
                                        title=title,
                                        company_name=company_name,
                                        email=None,
                                        phone=None,
                                        bio="",
                                        discovery_sources=["linkedin_company_page"],
                                        confidence=0.7,
                                        seniority_tier=self._determine_seniority_tier(title),
                                        company_domain=domain
                                    )
                                    executives.append(executive)
                    except Exception as e:
                        logger.debug(f"Failed to extract executive from company page element: {e}")
                        continue
            
            return executives
            
        except Exception as e:
            logger.debug(f"Failed to extract executives from company page: {e}")
            return []
    
    def _extract_executives_from_people_page(self, html: str, company_name: str, domain: str) -> List[ExecutiveContact]:
        """Extract executives from LinkedIn company people page"""
        # Similar to company page extraction but focused on people listings
        return self._extract_executives_from_company_page(html, company_name, domain)
    
    def _deduplicate_linkedin_executives(self, executives: List[ExecutiveContact]) -> List[ExecutiveContact]:
        """Remove duplicate LinkedIn executives"""
        if not executives:
            return []
        
        unique_executives = []
        
        for executive in executives:
            is_duplicate = False
            
            for existing in unique_executives:
                # Check name similarity
                name_similarity = fuzz.ratio(
                    executive.full_name.lower(),
                    existing.full_name.lower()
                )
                
                # Check LinkedIn URL similarity
                linkedin_similarity = 0
                if (hasattr(executive, 'linkedin_url') and hasattr(existing, 'linkedin_url') and 
                    executive.linkedin_url and existing.linkedin_url):
                    linkedin_similarity = fuzz.ratio(executive.linkedin_url, existing.linkedin_url)
                
                if name_similarity > 85 or linkedin_similarity > 90:
                    is_duplicate = True
                    # Keep the one with higher confidence
                    if executive.confidence > existing.confidence:
                        unique_executives.remove(existing)
                        unique_executives.append(executive)
                    break
            
            if not is_duplicate:
                unique_executives.append(executive)
        
        return unique_executives
    
    def _score_linkedin_confidence(self, executives: List[ExecutiveContact]) -> List[ExecutiveContact]:
        """Score LinkedIn executive confidence"""
        for executive in executives:
            # Base confidence from LinkedIn discovery
            base_confidence = executive.confidence
            
            # Boost for LinkedIn URL
            if hasattr(executive, 'linkedin_url') and executive.linkedin_url:
                base_confidence += 0.1
            
            # Boost for seniority tier
            if executive.seniority_tier == 'tier_1':
                base_confidence += 0.1
            elif executive.seniority_tier == 'tier_2':
                base_confidence += 0.05
            
            # Cap at 1.0
            executive.confidence = min(1.0, base_confidence)
        
        # Sort by confidence (highest first)
        executives.sort(key=lambda x: x.confidence, reverse=True)
        
        return executives
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting for LinkedIn requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            logger.debug(f"LinkedIn rate limiting: sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)
        
        self.last_request = time.time()

# Usage example
async def test_linkedin_direct():
    """Test function for LinkedIn direct enricher"""
    enricher = LinkedInDirectEnricher()
    executives = await enricher.discover_executives("Jack The Plumber", "jacktheplumber.co.uk", "plumbing")
    
    print(f"Found {len(executives)} executives:")
    for exec in executives:
        print(f"- {exec.full_name} ({exec.title}) - Confidence: {exec.confidence:.2f}")
        if hasattr(exec, 'linkedin_url'):
            print(f"  LinkedIn: {exec.linkedin_url}")

if __name__ == "__main__":
    asyncio.run(test_linkedin_direct()) 