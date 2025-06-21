"""
LinkedIn Professional Network Scraper

Enhanced LinkedIn scraper for executive contact discovery with advanced anti-detection
and professional network analysis capabilities.

Features:
- Company page employee extraction
- Executive profile identification
- Contact information harvesting
- Professional network analysis
- Anti-detection measures
- Role-based filtering
"""

import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, quote

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser

from ..models import ExecutiveContact
from ..config import get_processing_config

logger = logging.getLogger(__name__)

@dataclass
class LinkedInProfile:
    """LinkedIn profile information"""
    name: str
    title: str
    profile_url: str
    company: str
    location: str
    email: Optional[str] = None
    phone: Optional[str] = None
    connections: int = 0
    experience_years: int = 0
    seniority_score: float = 0.0

@dataclass
class LinkedInCompanyPage:
    """LinkedIn company page information"""
    company_name: str
    company_url: str
    employee_count: int
    industry: str
    location: str
    employees: List[LinkedInProfile]

class LinkedInAntiDetection:
    """
    Advanced anti-detection system for LinkedIn scraping.
    """
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        self.viewport_sizes = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864}
        ]
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent"""
        return random.choice(self.user_agents)
    
    def get_random_viewport(self) -> Dict[str, int]:
        """Get a random viewport size"""
        return random.choice(self.viewport_sizes)
    
    async def setup_stealth_page(self, page: Page) -> None:
        """Setup page with stealth configurations"""
        # Set random user agent
        await page.set_user_agent(self.get_random_user_agent())
        
        # Set random viewport
        viewport = self.get_random_viewport()
        await page.set_viewport_size(viewport['width'], viewport['height'])
        
        # Add stealth scripts
        await page.add_init_script("""
            // Override webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
    
    async def human_like_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """Add human-like delay between actions"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def random_mouse_movement(self, page: Page) -> None:
        """Simulate random mouse movements"""
        try:
            viewport = await page.viewport_size()
            x = random.randint(100, viewport['width'] - 100)
            y = random.randint(100, viewport['height'] - 100)
            await page.mouse.move(x, y)
            await self.human_like_delay(0.1, 0.3)
        except Exception:
            pass  # Ignore mouse movement errors


class LinkedInProfessionalScraper:
    """
    Enhanced LinkedIn scraper for professional executive discovery.
    """
    
    def __init__(self):
        self.config = get_processing_config()
        self.anti_detection = LinkedInAntiDetection()
        
        # LinkedIn URL patterns
        self.base_url = "https://www.linkedin.com"
        self.company_search_url = "https://www.linkedin.com/search/results/companies/"
        self.people_search_url = "https://www.linkedin.com/search/results/people/"
        
        # Executive role keywords for filtering
        self.executive_keywords = [
            'ceo', 'chief executive', 'founder', 'owner', 'managing director',
            'director', 'manager', 'head of', 'senior', 'principal', 'partner',
            'president', 'vice president', 'chairman', 'supervisor'
        ]
        
        # Rate limiting
        self.request_delay = (2.0, 5.0)  # Random delay between requests
        self.page_delay = (3.0, 8.0)    # Random delay between pages
    
    async def discover_executives(self, company: 'CompanyInfo') -> List[ExecutiveContact]:
        """
        Main method to discover executives from LinkedIn for a company.
        
        Args:
            company: CompanyInfo object with company details
            
        Returns:
            List of ExecutiveContact objects
        """
        start_time = time.time()
        executives = []
        
        try:
            async with async_playwright() as playwright:
                browser = await self._launch_browser(playwright)
                page = await browser.new_page()
                
                # Setup stealth configurations
                await self.anti_detection.setup_stealth_page(page)
                
                # Find company LinkedIn page
                company_url = await self._find_company_page(page, company.company_name)
                
                if company_url:
                    # Extract executives from company page
                    company_executives = await self._extract_company_executives(page, company_url)
                    executives.extend(company_executives)
                    
                    # Search for additional executives
                    search_executives = await self._search_company_executives(
                        page, company.company_name, company.domain
                    )
                    executives.extend(search_executives)
                
                await browser.close()
                
        except Exception as e:
            logger.error(f"LinkedIn scraping failed for {company.company_name}: {e}")
        
        # Convert to ExecutiveContact objects
        executive_contacts = []
        for profile in executives:
            contact = self._convert_to_executive_contact(profile, company)
            if contact:
                executive_contacts.append(contact)
        
        processing_time = time.time() - start_time
        logger.info(f"LinkedIn discovery found {len(executive_contacts)} executives in {processing_time:.2f}s")
        
        return executive_contacts[:10]  # Limit to top 10
    
    async def _launch_browser(self, playwright) -> Browser:
        """Launch browser with stealth configurations"""
        return await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
    
    async def _find_company_page(self, page: Page, company_name: str) -> Optional[str]:
        """
        Find the LinkedIn company page URL.
        
        Args:
            page: Playwright page object
            company_name: Name of the company
            
        Returns:
            LinkedIn company page URL or None
        """
        try:
            # Search for company
            search_query = quote(company_name)
            search_url = f"{self.company_search_url}?keywords={search_query}"
            
            await page.goto(search_url, timeout=30000)
            await self.anti_detection.human_like_delay(2.0, 4.0)
            
            # Look for company results
            company_links = await page.query_selector_all('a[href*="/company/"]')
            
            for link in company_links[:3]:  # Check first 3 results
                try:
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    
                    if href and text and self._is_company_match(text, company_name):
                        full_url = urljoin(self.base_url, href)
                        logger.info(f"Found LinkedIn company page: {full_url}")
                        return full_url
                        
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to find company page for {company_name}: {e}")
            return None
    
    def _is_company_match(self, linkedin_name: str, search_name: str) -> bool:
        """Check if LinkedIn company name matches search name"""
        if not linkedin_name or not search_name:
            return False
        
        # Normalize names for comparison
        linkedin_clean = linkedin_name.lower().strip()
        search_clean = search_name.lower().strip()
        
        # Direct match
        if linkedin_clean == search_clean:
            return True
        
        # Partial match (company name contained in LinkedIn name)
        if search_clean in linkedin_clean or linkedin_clean in search_clean:
            return True
        
        # Word-based matching
        linkedin_words = set(linkedin_clean.split())
        search_words = set(search_clean.split())
        
        # Remove common business words
        common_words = {'ltd', 'limited', 'plc', 'company', 'co', 'corp', 'inc', 'services'}
        linkedin_words -= common_words
        search_words -= common_words
        
        if linkedin_words and search_words:
            overlap = len(linkedin_words & search_words)
            return overlap >= min(2, len(search_words))
        
        return False
    
    async def _extract_company_executives(self, page: Page, company_url: str) -> List[LinkedInProfile]:
        """
        Extract executives from LinkedIn company page.
        
        Args:
            page: Playwright page object
            company_url: LinkedIn company page URL
            
        Returns:
            List of LinkedInProfile objects
        """
        executives = []
        
        try:
            # Navigate to company page
            await page.goto(company_url, timeout=30000)
            await self.anti_detection.human_like_delay(2.0, 4.0)
            
            # Try to find "People" or "Employees" section
            people_links = await page.query_selector_all('a[href*="/people/"]')
            
            if people_links:
                # Click on people section
                await people_links[0].click()
                await self.anti_detection.human_like_delay(3.0, 6.0)
                
                # Extract employee profiles
                executives = await self._extract_employee_profiles(page)
            
            # Alternative: Look for featured employees on main page
            if not executives:
                executives = await self._extract_featured_employees(page)
            
        except Exception as e:
            logger.warning(f"Failed to extract company executives: {e}")
        
        return executives
    
    async def _extract_employee_profiles(self, page: Page) -> List[LinkedInProfile]:
        """Extract employee profiles from people page"""
        profiles = []
        
        try:
            # Wait for profiles to load
            await page.wait_for_selector('[data-test-id="people-card"]', timeout=10000)
            
            # Get all profile cards
            profile_cards = await page.query_selector_all('[data-test-id="people-card"]')
            
            for card in profile_cards[:20]:  # Limit to first 20 profiles
                try:
                    profile = await self._extract_profile_from_card(card)
                    if profile and self._is_executive_profile(profile):
                        profiles.append(profile)
                        
                except Exception:
                    continue
                
                # Add delay between extractions
                await self.anti_detection.human_like_delay(0.5, 1.0)
            
        except Exception as e:
            logger.debug(f"Failed to extract employee profiles: {e}")
        
        return profiles
    
    async def _extract_featured_employees(self, page: Page) -> List[LinkedInProfile]:
        """Extract featured employees from company main page"""
        profiles = []
        
        try:
            # Look for employee sections
            employee_sections = await page.query_selector_all('.org-people-profile-card')
            
            for section in employee_sections:
                try:
                    profile = await self._extract_profile_from_section(section)
                    if profile and self._is_executive_profile(profile):
                        profiles.append(profile)
                        
                except Exception:
                    continue
            
        except Exception as e:
            logger.debug(f"Failed to extract featured employees: {e}")
        
        return profiles
    
    async def _extract_profile_from_card(self, card) -> Optional[LinkedInProfile]:
        """Extract profile information from a profile card"""
        try:
            # Extract name
            name_element = await card.query_selector('.actor-name, .profile-card__name, h3')
            name = await name_element.text_content() if name_element else ""
            
            # Extract title
            title_element = await card.query_selector('.actor-occupation, .profile-card__occupation, .t-14')
            title = await title_element.text_content() if title_element else ""
            
            # Extract profile URL
            link_element = await card.query_selector('a[href*="/in/"]')
            profile_url = await link_element.get_attribute('href') if link_element else ""
            
            # Extract location
            location_element = await card.query_selector('.actor-meta-item, .profile-card__location')
            location = await location_element.text_content() if location_element else ""
            
            if name and title:
                return LinkedInProfile(
                    name=name.strip(),
                    title=title.strip(),
                    profile_url=urljoin(self.base_url, profile_url) if profile_url else "",
                    company="",  # Will be filled later
                    location=location.strip(),
                    seniority_score=self._calculate_seniority_score(title)
                )
            
        except Exception as e:
            logger.debug(f"Failed to extract profile from card: {e}")
        
        return None
    
    async def _extract_profile_from_section(self, section) -> Optional[LinkedInProfile]:
        """Extract profile information from a section element"""
        try:
            # Extract name
            name_element = await section.query_selector('.profile-card__name, h3, .name')
            name = await name_element.text_content() if name_element else ""
            
            # Extract title
            title_element = await section.query_selector('.profile-card__occupation, .title, .headline')
            title = await title_element.text_content() if title_element else ""
            
            # Extract profile URL
            link_element = await section.query_selector('a[href*="/in/"]')
            profile_url = await link_element.get_attribute('href') if link_element else ""
            
            if name and title:
                return LinkedInProfile(
                    name=name.strip(),
                    title=title.strip(),
                    profile_url=urljoin(self.base_url, profile_url) if profile_url else "",
                    company="",
                    location="",
                    seniority_score=self._calculate_seniority_score(title)
                )
            
        except Exception as e:
            logger.debug(f"Failed to extract profile from section: {e}")
        
        return None
    
    def _is_executive_profile(self, profile: LinkedInProfile) -> bool:
        """Check if profile represents an executive"""
        if not profile.title:
            return False
        
        title_lower = profile.title.lower()
        
        # Check for executive keywords
        return any(keyword in title_lower for keyword in self.executive_keywords)
    
    def _calculate_seniority_score(self, title: str) -> float:
        """Calculate seniority score based on title"""
        if not title:
            return 0.0
        
        title_lower = title.lower()
        
        # Tier 1: Top executives (score 1.0)
        tier1_keywords = ['ceo', 'chief executive', 'founder', 'owner', 'managing director', 'president']
        if any(keyword in title_lower for keyword in tier1_keywords):
            return 1.0
        
        # Tier 2: Senior management (score 0.8)
        tier2_keywords = ['director', 'manager', 'head of', 'senior', 'principal', 'partner']
        if any(keyword in title_lower for keyword in tier2_keywords):
            return 0.8
        
        # Tier 3: Middle management (score 0.6)
        tier3_keywords = ['supervisor', 'coordinator', 'lead', 'specialist']
        if any(keyword in title_lower for keyword in tier3_keywords):
            return 0.6
        
        return 0.4  # Default score
    
    async def _search_company_executives(self, page: Page, company_name: str, 
                                       domain: str) -> List[LinkedInProfile]:
        """
        Search for company executives using LinkedIn people search.
        
        Args:
            page: Playwright page object
            company_name: Company name
            domain: Company domain
            
        Returns:
            List of LinkedInProfile objects
        """
        executives = []
        
        try:
            # Search for executives at the company
            for keyword in ['CEO', 'Director', 'Manager', 'Founder']:
                search_query = f"{keyword} {company_name}"
                encoded_query = quote(search_query)
                
                search_url = f"{self.people_search_url}?keywords={encoded_query}"
                
                await page.goto(search_url, timeout=30000)
                await self.anti_detection.human_like_delay(2.0, 4.0)
                
                # Extract search results
                search_results = await self._extract_search_results(page, company_name)
                executives.extend(search_results)
                
                # Limit total results
                if len(executives) >= 15:
                    break
                
                # Delay between searches
                await self.anti_detection.human_like_delay(3.0, 6.0)
            
        except Exception as e:
            logger.warning(f"Failed to search company executives: {e}")
        
        return executives
    
    async def _extract_search_results(self, page: Page, company_name: str) -> List[LinkedInProfile]:
        """Extract profiles from search results"""
        profiles = []
        
        try:
            # Wait for search results
            await page.wait_for_selector('.search-result', timeout=10000)
            
            # Get search result cards
            result_cards = await page.query_selector_all('.search-result')
            
            for card in result_cards[:10]:  # Limit to first 10 results
                try:
                    profile = await self._extract_profile_from_search_card(card)
                    if profile and self._is_company_related(profile, company_name):
                        profiles.append(profile)
                        
                except Exception:
                    continue
            
        except Exception as e:
            logger.debug(f"Failed to extract search results: {e}")
        
        return profiles
    
    async def _extract_profile_from_search_card(self, card) -> Optional[LinkedInProfile]:
        """Extract profile from search result card"""
        try:
            # Extract name
            name_element = await card.query_selector('.actor-name, h3')
            name = await name_element.text_content() if name_element else ""
            
            # Extract title and company
            subtitle_element = await card.query_selector('.subline-level-1, .actor-occupation')
            subtitle = await subtitle_element.text_content() if subtitle_element else ""
            
            # Parse title and company from subtitle
            title, company = self._parse_title_company(subtitle)
            
            # Extract profile URL
            link_element = await card.query_selector('a[href*="/in/"]')
            profile_url = await link_element.get_attribute('href') if link_element else ""
            
            if name and title:
                return LinkedInProfile(
                    name=name.strip(),
                    title=title.strip(),
                    profile_url=urljoin(self.base_url, profile_url) if profile_url else "",
                    company=company.strip(),
                    location="",
                    seniority_score=self._calculate_seniority_score(title)
                )
            
        except Exception as e:
            logger.debug(f"Failed to extract profile from search card: {e}")
        
        return None
    
    def _parse_title_company(self, subtitle: str) -> Tuple[str, str]:
        """Parse title and company from subtitle text"""
        if not subtitle:
            return "", ""
        
        # Common patterns: "Title at Company" or "Title | Company"
        if " at " in subtitle:
            parts = subtitle.split(" at ", 1)
            return parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""
        
        if " | " in subtitle:
            parts = subtitle.split(" | ", 1)
            return parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""
        
        # Fallback: treat entire subtitle as title
        return subtitle.strip(), ""
    
    def _is_company_related(self, profile: LinkedInProfile, company_name: str) -> bool:
        """Check if profile is related to the target company"""
        if not profile.company:
            return True  # Assume related if no company info
        
        company_lower = profile.company.lower()
        target_lower = company_name.lower()
        
        # Direct match or containment
        return target_lower in company_lower or company_lower in target_lower
    
    def _convert_to_executive_contact(self, profile: LinkedInProfile, 
                                    company: 'CompanyInfo') -> Optional[ExecutiveContact]:
        """Convert LinkedInProfile to ExecutiveContact"""
        try:
            # Determine seniority tier
            seniority_tier = "tier_3"  # Default
            if profile.seniority_score >= 0.9:
                seniority_tier = "tier_1"
            elif profile.seniority_score >= 0.7:
                seniority_tier = "tier_2"
            
            # Extract first and last name
            name_parts = profile.name.split()
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[-1] if len(name_parts) > 1 else ""
            
            return ExecutiveContact(
                full_name=profile.name,
                first_name=first_name,
                last_name=last_name,
                title=profile.title,
                email=profile.email,
                phone=profile.phone,
                linkedin_url=profile.profile_url,
                company_name=company.company_name,
                seniority_tier=seniority_tier,
                confidence=min(0.9, 0.6 + profile.seniority_score * 0.3),  # LinkedIn profiles get high confidence
                discovery_sources=["linkedin"],
                discovery_method="linkedin_professional_scraping",
                processing_time_ms=0  # Will be set by caller
            )
            
        except Exception as e:
            logger.warning(f"Failed to convert LinkedIn profile to ExecutiveContact: {e}")
            return None 