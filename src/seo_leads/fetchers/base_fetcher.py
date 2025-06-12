"""
Base Directory Fetcher for UK Business Directories

Provides common functionality for scraping UK business directories with
rate limiting, error handling, and database integration.

Inspired by the fetch module patterns but adapted for business directory scraping.
"""

import asyncio
import logging
import time
import hashlib
import random
from typing import Dict, List, Optional, Generator, Tuple
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup

from ..config import get_api_config, get_processing_config
from ..database import get_db_session
from ..models import UKCompany, ProcessingStatus

logger = logging.getLogger(__name__)

@dataclass
class CompanyBasicInfo:
    """Basic company information from directory listing"""
    name: str
    website: Optional[str]
    city: str
    region: Optional[str]
    address: Optional[str]
    sector: Optional[str]
    phone: Optional[str]
    source: str  # Directory source name


class BaseDirectoryFetcher(ABC):
    """
    Base class for UK business directory scrapers
    
    Features:
    - Intelligent rate limiting
    - Resume from previous state
    - Batch processing with database persistence
    - Error recovery and retry logic
    - Site-specific customization through inheritance
    """
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.api_config = get_api_config()
        self.processing_config = get_processing_config()
        self.browser = None
        self.page = None
        
        # Rate limiting state
        self.last_request_time = 0
        self.request_count = 0
        self.start_time = time.time()
        
        # Processing state
        self.total_companies_found = 0
        self.companies_processed = 0
        self.errors_encountered = 0
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._init_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_browser()
    
    async def _init_browser(self):
        """Initialize browser with optimal settings"""
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=self.api_config.headless_browser,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--no-first-run',
                '--no-default-browser-check'
            ]
        )
        
        context = await self.browser.new_context(
            user_agent=self.api_config.browser_user_agent,
            viewport={'width': 1280, 'height': 720},
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        self.page = await context.new_page()
        
        # Add stealth JavaScript to avoid detection
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-GB', 'en'],
            });
            
            window.chrome = {
                runtime: {},
            };
        """)
        
        # Set timeouts
        self.page.set_default_timeout(self.api_config.browser_timeout * 1000)
        
        # Small delay to let browser fully initialize
        await asyncio.sleep(1)
    
    async def _close_browser(self):
        """Clean up browser resources"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
    
    def _rate_limit(self):
        """Enforce rate limiting for directory requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Enforce minimum delay between requests with some randomness
        min_delay = getattr(self.api_config, 'yell_page_delay', 6.0)  # Use yell_page_delay or default to 6 seconds
        # Add random variation to make it more human-like (±20%)
        random_delay = min_delay + random.uniform(-min_delay * 0.2, min_delay * 0.2)
        
        if time_since_last < random_delay:
            sleep_time = random_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
        
        # Log rate limiting stats periodically
        if self.request_count % 50 == 0:
            elapsed = self.last_request_time - self.start_time
            rate = self.request_count / elapsed if elapsed > 0 else 0
            logger.info(f"Rate limiting stats: {self.request_count} requests in {elapsed:.1f}s ({rate:.2f} req/s)")
    
    @abstractmethod
    def get_base_url(self) -> str:
        """Return the base URL for this directory"""
        pass
    
    @abstractmethod
    def build_search_url(self, city: str, sector: Optional[str] = None, page: int = 1) -> str:
        """Build search URL for city/sector combination"""
        pass
    
    @abstractmethod
    def get_listing_selector(self) -> str:
        """Return CSS selector for business listings on search results page"""
        pass
    
    @abstractmethod
    def parse_listing(self, listing_element, city: str) -> Optional[CompanyBasicInfo]:
        """Parse a single business listing element into CompanyBasicInfo"""
        pass
    
    @abstractmethod
    def has_next_page(self, page_soup: BeautifulSoup) -> bool:
        """Check if there are more pages available"""
        pass
    
    async def fetch_companies_batch(self, cities: List[str], sectors: Optional[List[str]] = None) -> int:
        """
        Fetch companies in batch from specified cities and sectors
        
        Args:
            cities: List of UK cities to search
            sectors: Optional list of business sectors to filter by
            
        Returns:
            Total number of companies found and stored
        """
        logger.info(f"Starting batch fetch for {self.source_name}")
        logger.info(f"Cities: {len(cities)}, Sectors: {len(sectors) if sectors else 'All'}")
        
        total_found = 0
        
        for city in cities:
            try:
                if sectors:
                    for sector in sectors:
                        companies = await self._search_companies_in_city(city, sector)
                        stored_count = self._store_companies_batch(companies)
                        total_found += stored_count
                        logger.info(f"Stored {stored_count} companies for {city} - {sector}")
                        self._update_progress('scraping', stored_count)
                else:
                    companies = await self._search_companies_in_city(city)
                    stored_count = self._store_companies_batch(companies)
                    total_found += stored_count
                    logger.info(f"Stored {stored_count} companies for {city}")
                    self._update_progress('scraping', stored_count)
                    
            except Exception as e:
                logger.error(f"Error processing {city}: {e}")
                continue
        
        logger.info(f"Batch fetch complete for {self.source_name}. Total companies found: {total_found}")
        return total_found
    
    async def _search_companies_in_city(self, city: str, sector: Optional[str] = None) -> List[CompanyBasicInfo]:
        """Search for companies in a specific city and sector"""
        companies = []
        
        try:
            page_number = 1
            max_pages = getattr(self.api_config, 'max_pages', 10)
            
            while page_number <= max_pages:
                # Rate limiting
                self._rate_limit()
                
                # Build page URL
                search_url = self.build_search_url(city, sector, page_number)
                
                logger.debug(f"Fetching page {page_number}: {search_url}")
                
                try:
                    # First visit homepage to establish session (anti-bot measure)
                    if page_number == 1:
                        logger.debug("Visiting homepage first to establish session...")
                        homepage_response = await self.page.goto(self.get_base_url(), wait_until="domcontentloaded")
                        if homepage_response.status == 200:
                            await asyncio.sleep(2)  # Wait like a human would
                        
                    # Navigate to search page
                    response = await self.page.goto(search_url, wait_until="domcontentloaded")
                    
                    if response.status != 200:
                        logger.warning(f"Non-200 response ({response.status}) for {search_url}")
                        break
                    
                    # Wait for listings to load
                    try:
                        await self.page.wait_for_selector(self.get_listing_selector(), timeout=10000)
                    except:
                        logger.warning(f"Listing selector not found on {search_url}")
                        break
                    
                    # Extract page content
                    content = await self.page.content()
                    page_companies = self._parse_search_results(content, city)
                    
                    if not page_companies:
                        logger.info(f"No more companies found on page {page_number}")
                        break
                    
                    companies.extend(page_companies)
                    logger.info(f"Found {len(page_companies)} companies on page {page_number}")
                    
                    # Check if there's a next page
                    soup = BeautifulSoup(content, 'html.parser')
                    if not self.has_next_page(soup):
                        logger.info("No next page found, stopping")
                        break
                    
                    page_number += 1
                    
                    # Apply per-city limit
                    max_companies = getattr(self.processing_config, 'max_companies_per_city', 1000)
                    if len(companies) >= max_companies:
                        logger.info(f"Reached max companies limit for {city}: {len(companies)}")
                        break
                
                except Exception as e:
                    logger.error(f"Error on page {page_number} for {city}: {e}")
                    self.errors_encountered += 1
                    break
        
        except Exception as e:
            logger.error(f"Error searching companies in {city}: {e}")
            self.errors_encountered += 1
        
        logger.info(f"Total companies found in {city}: {len(companies)}")
        return companies
    
    def _parse_search_results(self, html_content: str, city: str) -> List[CompanyBasicInfo]:
        """Parse search results page and extract company information"""
        companies = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            listings = soup.select(self.get_listing_selector())
            
            for listing in listings:
                try:
                    company = self.parse_listing(listing, city)
                    if company:
                        company.source = self.source_name
                        companies.append(company)
                except Exception as e:
                    logger.debug(f"Error parsing listing: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
        
        return companies
    
    def _store_companies_batch(self, companies: List[CompanyBasicInfo]) -> int:
        """Store a batch of companies in the database"""
        stored_count = 0
        
        try:
            with get_db_session() as session:
                for company_info in companies:
                    try:
                        # Generate unique ID
                        company_id = self._generate_company_id(
                            company_info.name, 
                            company_info.website, 
                            company_info.city
                        )
                        
                        # Check if company already exists
                        existing = session.query(UKCompany).filter_by(id=company_id).first()
                        if existing:
                            continue
                        
                        # Create new company record
                        company = UKCompany(
                            id=company_id,
                            company_name=company_info.name,
                            website=company_info.website,
                            city=company_info.city,
                            region=company_info.region,
                            address=company_info.address,
                            sector=company_info.sector,
                            phone=company_info.phone,
                            status='scraped',
                            source=company_info.source
                        )
                        
                        session.add(company)
                        stored_count += 1
                        
                    except Exception as e:
                        logger.debug(f"Error storing company {company_info.name}: {e}")
                        continue
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Error storing companies batch: {e}")
        
        return stored_count
    
    def _generate_company_id(self, name: str, website: Optional[str], city: str) -> str:
        """Generate a unique ID for a company"""
        # Use website as primary identifier, fallback to name+city
        if website:
            identifier = website.lower().strip()
        else:
            identifier = f"{name.lower().strip()}:{city.lower().strip()}"
        
        return hashlib.md5(identifier.encode()).hexdigest()
    
    def _update_progress(self, stage: str, increment: int):
        """Update processing progress for a stage"""
        try:
            with get_db_session() as session:
                status = session.query(ProcessingStatus).filter_by(stage=stage).first()
                if status:
                    status.processed_companies += increment
                    if status.total_companies > 0:
                        status.success_rate = (status.processed_companies / status.total_companies) * 100
                    session.commit()
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
    
    def _map_sector(self, raw_sector: str) -> Optional[str]:
        """Map raw sector text to standardized sectors"""
        if not raw_sector:
            return None
        
        raw_sector = raw_sector.lower().strip()
        
        # Mapping common directory categories to our target sectors
        sector_mappings = {
            'restaurant': 'hospitality',
            'food': 'hospitality',
            'hotel': 'hospitality',
            'cafe': 'hospitality',
            'construction': 'construction',
            'building': 'construction',
            'builder': 'construction',
            'plumber': 'construction',
            'electrician': 'construction',
            'retail': 'retail',
            'shop': 'retail',
            'store': 'retail',
            'technology': 'technology',
            'software': 'technology',
            'it': 'technology',
            'computer': 'technology',
            'health': 'healthcare',
            'medical': 'healthcare',
            'dental': 'healthcare',
            'fitness': 'healthcare',
            'legal': 'professional',
            'lawyer': 'professional',
            'accountant': 'professional',
            'consultant': 'professional',
            'marketing': 'professional',
            'finance': 'financial',
            'bank': 'financial',
            'insurance': 'financial',
            'automotive': 'automotive',
            'car': 'automotive',
            'garage': 'automotive',
            'education': 'education',
            'training': 'education',
            'school': 'education'
        }
        
        for keyword, sector in sector_mappings.items():
            if keyword in raw_sector:
                return sector
        
        # Return the raw sector if no mapping found
        return raw_sector[:50]  # Limit length 