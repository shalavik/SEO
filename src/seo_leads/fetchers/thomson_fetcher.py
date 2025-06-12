"""
Thomson Local UK Directory Fetcher

Scrapes UK company data from Thomson Local directory.
Thomson Local is a long-established UK business directory.
"""

import logging
import asyncio
import random
from typing import Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .base_fetcher import BaseDirectoryFetcher, CompanyBasicInfo

logger = logging.getLogger(__name__)


class ThomsonLocalFetcher(BaseDirectoryFetcher):
    """
    Thomson Local directory scraper
    
    Thomson Local (https://www.thomsonlocal.com) is an established UK business directory
    that provides local business listings across the UK.
    """
    
    def __init__(self):
        super().__init__("Thomson Local")
    
    def get_base_url(self) -> str:
        """Return the base URL for Thomson Local"""
        return "https://www.thomsonlocal.com"
    
    def build_search_url(self, city: str, sector: Optional[str] = None, page: int = 1) -> str:
        """Build search URL for Thomson Local city/sector combination"""
        base_url = self.get_base_url()
        
        # Try alternative URL patterns that might bypass blocking
        alternative_patterns = [
            f"{base_url}/find/{quote_plus(sector or 'business')}/{quote_plus(city)}",
            f"{base_url}/directory/{quote_plus(city)}/{quote_plus(sector or 'business')}",
            f"{base_url}/business-directory/{quote_plus(city)}",
            f"{base_url}/local/{quote_plus(city)}"
        ]
        
        # Use the first alternative pattern for now
        return alternative_patterns[0] if sector else alternative_patterns[2]
    
    def get_listing_selector(self) -> str:
        """Return CSS selector for business listings on Thomson Local"""
        return '.business-listing, .listing-item, .search-result, [data-business-id], .result, .business, .company'
    
    async def setup_stealth_browser(self):
        """Setup browser with advanced stealth for Thomson Local"""
        await super().setup_stealth_browser()
        
        # Add Thomson Local specific stealth measures
        await self.page.add_init_script("""
            // Remove automation indicators
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock realistic browser characteristics
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
            });
            
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    { name: 'Shockwave Flash', filename: 'pepflashplayer.dll' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin' }
                ],
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-GB', 'en'],
            });
            
            // Hide automation traces
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """)
    
    async def fetch_page_with_retries(self, url: str, max_retries: int = 3):
        """Fetch page with Thomson Local specific retry logic and stealth"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to fetch Thomson Local page (attempt {attempt + 1})")
                
                # Visit homepage first to establish session and get cookies
                await self.page.goto("https://www.thomsonlocal.com", wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(3, 6))
                
                # Perform human-like interactions
                await self.page.mouse.move(random.randint(100, 800), random.randint(100, 500))
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # Scroll a bit like a human
                await self.page.mouse.wheel(0, random.randint(100, 300))
                await asyncio.sleep(random.uniform(1, 3))
                
                # Navigate to search URL
                response = await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                if response.status == 200:
                    # Wait for dynamic content
                    await asyncio.sleep(random.uniform(3, 7))
                    
                    # Check if we got actual content
                    content = await self.page.content()
                    if len(content) > 5000 and not ('access denied' in content.lower() or 'blocked' in content.lower()):
                        return response
                
                logger.warning(f"Thomson Local fetch attempt {attempt + 1} failed: {response.status}")
                
                # Exponential backoff with randomization
                wait_time = (2 ** attempt) + random.uniform(2, 8)
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.warning(f"Thomson Local fetch attempt {attempt + 1} error: {e}")
                wait_time = random.uniform(3, 10)
                await asyncio.sleep(wait_time)
        
        raise Exception(f"Failed to fetch Thomson Local page after {max_retries} attempts")
    
    def parse_listing(self, listing_element, city: str) -> Optional[CompanyBasicInfo]:
        """Parse a single Thomson Local business listing"""
        try:
            # Company name - try multiple selectors
            name = None
            name_selectors = [
                '.business-name',
                '.listing-title',
                'h2 a',
                'h3 a',
                '.title',
                '[data-business-name]'
            ]
            
            for selector in name_selectors:
                name_elem = listing_element.select_one(selector)
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    if name:
                        break
            
            if not name:
                return None
            
            # Website - try multiple selectors
            website = None
            website_selectors = [
                'a[href*="website"]',
                '.website-link',
                'a[title*="website"]',
                '.contact-website a'
            ]
            
            for selector in website_selectors:
                website_elem = listing_element.select_one(selector)
                if website_elem:
                    href = website_elem.get('href')
                    if href and href.startswith('http'):
                        website = href
                        break
            
            # Address - try multiple selectors
            address = None
            address_selectors = [
                '.business-address',
                '.address',
                '.location-address',
                '.contact-address'
            ]
            
            for selector in address_selectors:
                address_elem = listing_element.select_one(selector)
                if address_elem:
                    address = address_elem.get_text(strip=True)
                    if address:
                        break
            
            # Phone - try multiple selectors
            phone = None
            phone_selectors = [
                'a[href^="tel:"]',
                '.phone-number',
                '.business-phone',
                '.contact-phone'
            ]
            
            for selector in phone_selectors:
                phone_elem = listing_element.select_one(selector)
                if phone_elem:
                    phone = phone_elem.get_text(strip=True)
                    # Clean up phone number
                    if phone:
                        phone = phone.replace('Call', '').replace('Tel:', '').strip()
                        if phone:
                            break
            
            # Sector/Category - try multiple selectors
            sector = None
            sector_selectors = [
                '.business-category',
                '.category',
                '.listing-category',
                '[data-category]'
            ]
            
            for selector in sector_selectors:
                sector_elem = listing_element.select_one(selector)
                if sector_elem:
                    raw_sector = sector_elem.get_text(strip=True)
                    if raw_sector:
                        sector = self._map_sector(raw_sector)
                        break
            
            return CompanyBasicInfo(
                name=name,
                website=website,
                city=city,
                region=None,
                address=address,
                sector=sector,
                phone=phone,
                source=self.source_name
            )
        
        except Exception as e:
            logger.debug(f"Error extracting company info from Thomson Local listing: {e}")
            return None
    
    def has_next_page(self, page_soup: BeautifulSoup) -> bool:
        """Check if there are more pages available on Thomson Local"""
        # Look for next page indicators
        next_selectors = [
            'a.next',
            '.pagination .next:not(.disabled)',
            '.paging .next:not(.disabled)',
            'a[aria-label="Next page"]',
            '.pagination a[rel="next"]'
        ]
        
        for selector in next_selectors:
            next_elem = page_soup.select_one(selector)
            if next_elem and not next_elem.get('disabled'):
                return True
        
        return False


# Convenience function
async def fetch_thomson_companies(cities: Optional[list] = None, 
                                sectors: Optional[list] = None) -> int:
    """Convenience function to fetch UK companies from Thomson Local"""
    async with ThomsonLocalFetcher() as fetcher:
        return await fetcher.fetch_companies_batch(cities or [], sectors)


if __name__ == "__main__":
    # Test the fetcher
    import asyncio
    
    async def test_fetcher():
        async with ThomsonLocalFetcher() as fetcher:
            # Test with small sample
            test_cities = ['Manchester']
            test_sectors = ['restaurant']
            
            companies_found = await fetcher.fetch_companies_batch(test_cities, test_sectors)
            print(f"Found {companies_found} companies from Thomson Local")
    
    asyncio.run(test_fetcher()) 