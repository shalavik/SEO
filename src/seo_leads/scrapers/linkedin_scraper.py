"""
LinkedIn Executive Contact Scraper

Advanced LinkedIn scraping with anti-detection measures for executive discovery.
Implements the LinkedIn-first strategy for finding decision maker contacts.
"""

import asyncio
import logging
import random
import re
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, quote_plus
from dataclasses import dataclass

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

from ..models import LinkedInProfile, LinkedInCompanyData, ExecutiveContact, EXECUTIVE_PATTERNS
from ..config import get_processing_config

logger = logging.getLogger(__name__)

class LinkedInAntiDetection:
    """Anti-detection measures for LinkedIn scraping"""
    
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        ]
        
        self.request_delays = {
            'min_delay': 2.0,      # Minimum 2 seconds between requests
            'max_delay': 5.0,      # Maximum 5 seconds between requests
            'page_delay': 8.0,     # 8 seconds between different pages
            'profile_delay': 12.0  # 12 seconds between profile views
        }
        
        self.scroll_delays = {
            'min_scroll': 0.5,     # Minimum scroll delay
            'max_scroll': 1.5,     # Maximum scroll delay
            'scroll_distance': (200, 600)  # Random scroll distance
        }
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent"""
        return random.choice(self.user_agents)
    
    async def random_delay(self, delay_type: str = 'min_delay'):
        """Add randomized delays to avoid detection"""
        if delay_type in self.request_delays:
            base_delay = self.request_delays[delay_type]
            actual_delay = base_delay + random.uniform(0, 2.0)
            await asyncio.sleep(actual_delay)
        else:
            await asyncio.sleep(random.uniform(1.0, 3.0))
    
    def setup_stealth_options(self) -> Options:
        """Setup Chrome options for stealth browsing"""
        options = Options()
        
        # Basic stealth options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        # Remove problematic excludeSwitches option
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Random user agent
        options.add_argument(f"--user-agent={self.get_random_user_agent()}")
        
        # Additional privacy options
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins-discovery")
        options.add_argument("--disable-default-apps")
        
        # Additional stealth options
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        
        return options
    
    async def simulate_human_behavior(self, driver):
        """Simulate human-like browsing behavior"""
        # Random scrolling
        scroll_distance = random.randint(*self.scroll_delays['scroll_distance'])
        driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
        
        # Random delay
        await asyncio.sleep(random.uniform(
            self.scroll_delays['min_scroll'], 
            self.scroll_delays['max_scroll']
        ))
        
        # Sometimes scroll back up a bit
        if random.random() < 0.3:
            driver.execute_script(f"window.scrollBy(0, -{scroll_distance // 3});")
            await asyncio.sleep(random.uniform(0.5, 1.0))

class LinkedInScraper:
    """LinkedIn scraper for executive contact discovery"""
    
    def __init__(self, linkedin_email: str = None, linkedin_password: str = None):
        self.linkedin_email = linkedin_email
        self.linkedin_password = linkedin_password
        self.anti_detection = LinkedInAntiDetection()
        self.processing_config = get_processing_config()
        self.driver = None
        self.logged_in = False
        
        # LinkedIn URL patterns
        self.company_search_url = "https://www.linkedin.com/search/results/companies/"
        self.people_search_url = "https://www.linkedin.com/search/results/people/"
        self.base_url = "https://www.linkedin.com"
    
    async def initialize(self) -> bool:
        """Initialize the LinkedIn scraper - required by ExecutiveDiscoveryEngine"""
        try:
            logger.info("Initializing LinkedIn scraper...")
            # Setup driver if not already done
            if not self.driver:
                success = await self.setup_driver()
                if not success:
                    return False
            
            # Login if credentials provided
            if not self.logged_in:
                await self.login_to_linkedin()
            
            logger.info("LinkedIn scraper initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LinkedIn scraper: {e}")
            return False
    
    async def setup_driver(self) -> bool:
        """Setup the Chrome driver with anti-detection"""
        try:
            options = self.anti_detection.setup_stealth_options()
            
            # Use undetected-chromedriver
            self.driver = uc.Chrome(options=options, version_main=None)
            
            # Remove automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("LinkedIn scraper driver setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup LinkedIn scraper driver: {e}")
            return False
    
    async def login_to_linkedin(self) -> bool:
        """Login to LinkedIn if credentials provided"""
        if not self.linkedin_email or not self.linkedin_password:
            logger.info("No LinkedIn credentials provided, using guest access")
            return True
        
        try:
            self.driver.get("https://www.linkedin.com/login")
            await self.anti_detection.random_delay('page_delay')
            
            # Enter email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(self.linkedin_email)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.linkedin_password)
            
            # Click login
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            await self.anti_detection.random_delay('page_delay')
            
            # Check if login successful
            if "feed" in self.driver.current_url or "in/" in self.driver.current_url:
                self.logged_in = True
                logger.info("Successfully logged in to LinkedIn")
                return True
            else:
                logger.warning("LinkedIn login may have failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to login to LinkedIn: {e}")
            return False
    
    async def find_company_linkedin_url(self, company_name: str, website_domain: str) -> Optional[str]:
        """Find LinkedIn company page URL"""
        try:
            # Method 1: Direct company search
            search_query = f"{company_name}"
            search_url = f"{self.company_search_url}?keywords={quote_plus(search_query)}"
            
            self.driver.get(search_url)
            await self.anti_detection.random_delay('page_delay')
            await self.anti_detection.simulate_human_behavior(self.driver)
            
            # Look for company results
            company_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/company/']")
            
            for link in company_links[:3]:  # Check first 3 results
                href = link.get_attribute('href')
                if href and '/company/' in href:
                    # Verify it's the right company by checking name similarity
                    try:
                        link_text = link.text.strip()
                        if self._is_company_match(company_name, link_text):
                            logger.info(f"Found LinkedIn company URL: {href}")
                            return href
                    except:
                        continue
            
            # Method 2: Google search fallback
            google_query = f"site:linkedin.com/company {company_name}"
            return await self._google_search_linkedin_company(google_query, company_name)
            
        except Exception as e:
            logger.error(f"Error finding LinkedIn company URL for {company_name}: {e}")
            return None
    
    async def scrape_company_employees(self, linkedin_company_url: str) -> List[LinkedInProfile]:
        """Scrape employee list from LinkedIn company page"""
        try:
            # Navigate to company page
            self.driver.get(linkedin_company_url)
            await self.anti_detection.random_delay('page_delay')
            
            # Navigate to people section
            people_url = f"{linkedin_company_url.rstrip('/')}/people/"
            self.driver.get(people_url)
            await self.anti_detection.random_delay('page_delay')
            await self.anti_detection.simulate_human_behavior(self.driver)
            
            employees = []
            
            # Scroll to load more employees
            for scroll_attempt in range(3):  # Limit scrolling
                await self._scroll_and_extract_employees(employees)
                await self.anti_detection.random_delay()
            
            logger.info(f"Found {len(employees)} employees from LinkedIn company page")
            return employees
            
        except Exception as e:
            logger.error(f"Error scraping company employees: {e}")
            return []
    
    async def _scroll_and_extract_employees(self, employees: List[LinkedInProfile]):
        """Scroll page and extract employee profiles"""
        try:
            # Scroll to load more content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(2)
            
            # Extract employee cards
            employee_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-view-name='people-search-result']")
            
            for card in employee_cards:
                try:
                    profile = await self._extract_employee_from_card(card)
                    if profile and not self._is_duplicate_profile(profile, employees):
                        employees.append(profile)
                except Exception as e:
                    logger.debug(f"Error extracting employee from card: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Error in scroll and extract: {e}")
    
    async def _extract_employee_from_card(self, card) -> Optional[LinkedInProfile]:
        """Extract LinkedIn profile data from employee card"""
        try:
            # Extract profile URL
            profile_link = card.find_element(By.CSS_SELECTOR, "a[href*='/in/']")
            profile_url = profile_link.get_attribute('href')
            
            # Extract name
            name_element = card.find_element(By.CSS_SELECTOR, ".entity-result__title-text a")
            full_name = name_element.text.strip()
            
            # Extract title
            title_element = card.find_element(By.CSS_SELECTOR, ".entity-result__primary-subtitle")
            title = title_element.text.strip()
            
            # Extract company (should match target company)
            try:
                company_element = card.find_element(By.CSS_SELECTOR, ".entity-result__secondary-subtitle")
                company_name = company_element.text.strip()
            except:
                company_name = ""
            
            # Extract location if available
            try:
                location_element = card.find_element(By.CSS_SELECTOR, ".entity-result__location")
                location = location_element.text.strip()
            except:
                location = None
            
            return LinkedInProfile(
                profile_url=profile_url,
                full_name=full_name,
                title=title,
                company_name=company_name,
                location=location
            )
            
        except Exception as e:
            logger.debug(f"Error extracting employee card: {e}")
            return None
    
    async def filter_executives(self, employees: List[LinkedInProfile]) -> List[LinkedInProfile]:
        """Filter employees to find executives based on title patterns"""
        executives = []
        
        for employee in employees:
            seniority_tier = self._classify_executive_role(employee.title)
            if seniority_tier:
                # Add seniority info to profile
                employee.seniority_tier = seniority_tier
                executives.append(employee)
        
        # Sort by seniority (tier_1 first, then tier_2, tier_3)
        executives.sort(key=lambda x: (
            1 if x.seniority_tier == 'tier_1' else 
            2 if x.seniority_tier == 'tier_2' else 3
        ))
        
        logger.info(f"Filtered {len(executives)} executives from {len(employees)} employees")
        return executives
    
    def _classify_executive_role(self, title: str) -> Optional[str]:
        """Classify role into seniority tier based on title"""
        title_lower = title.lower()
        
        # Check tier 1 (highest seniority)
        for pattern in EXECUTIVE_PATTERNS['tier_1']:
            if pattern.lower() in title_lower:
                return 'tier_1'
        
        # Check tier 2
        for pattern in EXECUTIVE_PATTERNS['tier_2']:
            if pattern.lower() in title_lower:
                return 'tier_2'
        
        # Check tier 3
        for pattern in EXECUTIVE_PATTERNS['tier_3']:
            if pattern.lower() in title_lower:
                return 'tier_3'
        
        return None
    
    async def scrape_executive_profile_details(self, profile_url: str) -> Optional[Dict]:
        """Scrape detailed information from executive LinkedIn profile"""
        try:
            self.driver.get(profile_url)
            await self.anti_detection.random_delay('profile_delay')
            await self.anti_detection.simulate_human_behavior(self.driver)
            
            # Extract additional profile details
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            details = {
                'profile_url': profile_url,
                'contact_info': await self._extract_contact_info(soup),
                'experience': await self._extract_experience(soup),
                'education': await self._extract_education(soup),
                'connections': await self._extract_connections(soup)
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error scraping profile details for {profile_url}: {e}")
            return None
    
    async def _extract_contact_info(self, soup) -> Dict:
        """Extract contact information from LinkedIn profile"""
        contact_info = {}
        
        try:
            # Look for contact info section
            contact_section = soup.find('section', {'data-section': 'contactInfo'})
            if contact_section:
                # Extract email if available
                email_link = contact_section.find('a', href=re.compile(r'mailto:'))
                if email_link:
                    contact_info['email'] = email_link['href'].replace('mailto:', '')
                
                # Extract phone if available
                phone_link = contact_section.find('a', href=re.compile(r'tel:'))
                if phone_link:
                    contact_info['phone'] = phone_link['href'].replace('tel:', '')
        
        except Exception as e:
            logger.debug(f"Error extracting contact info: {e}")
        
        return contact_info
    
    async def _extract_experience(self, soup) -> List[Dict]:
        """Extract work experience from LinkedIn profile"""
        experience = []
        
        try:
            # Look for experience section
            exp_section = soup.find('section', {'data-section': 'experience'})
            if exp_section:
                exp_items = exp_section.find_all('div', class_='experience-item')
                for item in exp_items[:3]:  # Limit to recent 3 positions
                    exp_data = {
                        'title': item.find('h3').text.strip() if item.find('h3') else '',
                        'company': item.find('h4').text.strip() if item.find('h4') else '',
                        'duration': item.find('.date-range').text.strip() if item.find('.date-range') else ''
                    }
                    experience.append(exp_data)
        
        except Exception as e:
            logger.debug(f"Error extracting experience: {e}")
        
        return experience
    
    async def _extract_education(self, soup) -> List[Dict]:
        """Extract education from LinkedIn profile"""
        education = []
        
        try:
            # Look for education section
            edu_section = soup.find('section', {'data-section': 'education'})
            if edu_section:
                edu_items = edu_section.find_all('div', class_='education-item')
                for item in edu_items[:2]:  # Limit to 2 education entries
                    edu_data = {
                        'school': item.find('h3').text.strip() if item.find('h3') else '',
                        'degree': item.find('h4').text.strip() if item.find('h4') else '',
                        'field': item.find('.field-of-study').text.strip() if item.find('.field-of-study') else ''
                    }
                    education.append(edu_data)
        
        except Exception as e:
            logger.debug(f"Error extracting education: {e}")
        
        return education
    
    async def _extract_connections(self, soup) -> Optional[int]:
        """Extract number of connections"""
        try:
            connections_text = soup.find('span', string=re.compile(r'\d+\s+connections?'))
            if connections_text:
                numbers = re.findall(r'\d+', connections_text.text)
                if numbers:
                    return int(numbers[0])
        except Exception as e:
            logger.debug(f"Error extracting connections: {e}")
        
        return None
    
    def _is_company_match(self, target_company: str, found_company: str) -> bool:
        """Check if found company matches target company using fuzzy matching"""
        similarity = fuzz.ratio(target_company.lower(), found_company.lower())
        return similarity >= 70  # 70% similarity threshold
    
    def _is_duplicate_profile(self, profile: LinkedInProfile, existing: List[LinkedInProfile]) -> bool:
        """Check if profile is duplicate"""
        for existing_profile in existing:
            if profile.profile_url == existing_profile.profile_url:
                return True
            # Also check name similarity
            if fuzz.ratio(profile.full_name, existing_profile.full_name) >= 90:
                return True
        return False
    
    async def _google_search_linkedin_company(self, query: str, company_name: str) -> Optional[str]:
        """Fallback Google search for LinkedIn company page"""
        # This would require a Google search implementation
        # For now, return None as fallback
        logger.debug(f"Google search fallback not implemented for: {query}")
        return None
    
    async def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("LinkedIn scraper driver closed")
    
    async def discover_company_executives(self, company_name: str, website_domain: str) -> List[ExecutiveContact]:
        """Main method to discover executives for a company"""
        start_time = time.time()
        executives = []
        
        try:
            # Setup driver if not already done
            if not self.driver:
                success = await self.setup_driver()
                if not success:
                    return []
            
            # Login if credentials provided
            if not self.logged_in:
                await self.login_to_linkedin()
            
            # Find company LinkedIn page
            company_url = await self.find_company_linkedin_url(company_name, website_domain)
            if not company_url:
                logger.warning(f"Could not find LinkedIn company page for {company_name}")
                return []
            
            # Scrape employees
            employees = await self.scrape_company_employees(company_url)
            if not employees:
                logger.warning(f"No employees found for {company_name}")
                return []
            
            # Filter executives
            linkedin_executives = await self.filter_executives(employees)
            
            # Convert to ExecutiveContact format
            for linkedin_exec in linkedin_executives[:5]:  # Limit to top 5 executives
                executive_contact = ExecutiveContact(
                    first_name=linkedin_exec.full_name.split()[0] if linkedin_exec.full_name.split() else "",
                    last_name=" ".join(linkedin_exec.full_name.split()[1:]) if len(linkedin_exec.full_name.split()) > 1 else "",
                    full_name=linkedin_exec.full_name,
                    title=linkedin_exec.title,
                    seniority_tier=getattr(linkedin_exec, 'seniority_tier', 'tier_3'),
                    linkedin_url=linkedin_exec.profile_url,
                    linkedin_verified=True,
                    company_name=company_name,
                    company_domain=website_domain,
                    discovery_sources=['linkedin'],
                    discovery_method='linkedin_company_scraping',
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
                executives.append(executive_contact)
            
            logger.info(f"LinkedIn discovery found {len(executives)} executives for {company_name}")
            return executives
            
        except Exception as e:
            logger.error(f"Error in LinkedIn executive discovery for {company_name}: {e}")
            return []
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass 