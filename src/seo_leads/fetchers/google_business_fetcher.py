"""
Google Business Directory Fetcher

Scrapes UK company data from Google Business listings via Google Maps.
Google Maps is the most comprehensive business directory.
"""

import logging
import asyncio
import random
from typing import Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .base_fetcher import BaseDirectoryFetcher, CompanyBasicInfo

logger = logging.getLogger(__name__)


class GoogleBusinessFetcher(BaseDirectoryFetcher):
    """
    Google Business directory scraper
    
    Google Business (via Google Maps) provides the most comprehensive
    UK business listings with detailed information.
    """
    
    def __init__(self):
        super().__init__("Google Business")
    
    def get_base_url(self) -> str:
        """Return the base URL for Google Business"""
        return "https://www.google.co.uk"
    
    def build_search_url(self, city: str, sector: Optional[str] = None, page: int = 1) -> str:
        """Build search URL for Google Maps business search"""
        base_url = self.get_base_url()
        
        if sector:
            # Format: /maps/search/sector+city
            query = f"{sector}+{city}"
        else:
            # Format: /maps/search/businesses+city
            query = f"businesses+{city}"
        
        search_url = f"{base_url}/maps/search/{quote_plus(query)}"
        
        return search_url
    
    def get_listing_selector(self) -> str:
        """Return CSS selector for business listings on Google Maps"""
        return '[data-result-index], .Nv2PK, [jsaction*="mouseover"], .hfpxzc'
    
    async def setup_stealth_browser(self):
        """Setup browser with advanced stealth for Google"""
        await super().setup_stealth_browser()
        
        # Add Google-specific stealth measures
        await self.page.add_init_script("""
            // Remove automation indicators
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock realistic screen properties
            Object.defineProperty(screen, 'availWidth', {
                get: () => 1366,
            });
            Object.defineProperty(screen, 'availHeight', {
                get: () => 728,
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin' }
                ],
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-GB', 'en', 'en-US'],
            });
            
            // Mock permissions
            if (navigator.permissions && navigator.permissions.query) {
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: 'default' }) :
                        originalQuery(parameters)
                );
            }
        """)
    
    async def fetch_page_with_retries(self, url: str, max_retries: int = 3):
        """Fetch page with Google-specific retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to fetch Google Maps page (attempt {attempt + 1})")
                
                # Visit Google homepage first to establish session
                await self.page.goto("https://www.google.co.uk", wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(2, 4))
                
                # Human-like navigation
                await self.page.mouse.move(random.randint(100, 800), random.randint(100, 600))
                await asyncio.sleep(0.5)
                
                # Navigate to search URL
                response = await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                if response.status == 200:
                    # Wait for dynamic content to load
                    await asyncio.sleep(random.uniform(3, 6))
                    
                    # Check if we got actual results
                    content = await self.page.content()
                    if 'maps' in content.lower() and ('business' in content.lower() or 'place' in content.lower()):
                        return response
                
                logger.warning(f"Google Maps fetch attempt {attempt + 1} failed: {response.status}")
                await asyncio.sleep(random.uniform(5, 10))
                
            except Exception as e:
                logger.warning(f"Google Maps fetch attempt {attempt + 1} error: {e}")
                await asyncio.sleep(random.uniform(3, 8))
        
        raise Exception(f"Failed to fetch Google Maps page after {max_retries} attempts")
    
    def parse_listing(self, listing_element, city: str) -> Optional[CompanyBasicInfo]:
        """Parse a single Google Business listing"""
        try:
            # Company name - Google Maps specific selectors
            name = None
            name_selectors = [
                '.qBF1Pd',
                '.NrDZNb',
                '.fontHeadlineSmall',
                '[data-value="Name"]',
                'h3',
                '.section-result-title',
                '.X0PbBb'
            ]
            
            for selector in name_selectors:
                name_elem = listing_element.select_one(selector)
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    if name and len(name) > 2:
                        break
            
            if not name:
                return None
            
            # Address - Google Maps specific
            address = None
            address_selectors = [
                '.W4Efsd:nth-of-type(2)',
                '.W4Efsd .fontBodyMedium',
                '[data-value="Address"]',
                '.section-result-location',
                '.address'
            ]
            
            for selector in address_selectors:
                address_elem = listing_element.select_one(selector)
                if address_elem:
                    address = address_elem.get_text(strip=True)
                    if address and len(address) > 5:
                        break
            
            # Rating and category info
            category = None
            category_selectors = [
                '.W4Efsd:nth-of-type(1)',
                '[data-value="Category"]',
                '.section-result-details',
                '.category'
            ]
            
            for selector in category_selectors:
                cat_elem = listing_element.select_one(selector)
                if cat_elem:
                    raw_category = cat_elem.get_text(strip=True)
                    if raw_category and '★' not in raw_category:  # Skip ratings
                        category = self._map_sector(raw_category)
                        break
            
            # Phone number (often not displayed in map results)
            phone = None
            phone_selectors = [
                '[data-value="Phone"]',
                '.section-result-phone-number',
                'a[href^="tel:"]'
            ]
            
            for selector in phone_selectors:
                phone_elem = listing_element.select_one(selector)
                if phone_elem:
                    phone = phone_elem.get_text(strip=True)
                    if phone:
                        break
            
            # Website - often requires clicking for details
            website = None
            website_selectors = [
                'a[data-value="Website"]',
                '.section-result-action-container a',
                'a[href^="http"]:not([href*="google"])'
            ]
            
            for selector in website_selectors:
                website_elem = listing_element.select_one(selector)
                if website_elem:
                    href = website_elem.get('href')
                    if href and href.startswith('http') and 'google' not in href:
                        website = href
                        break
            
            return CompanyBasicInfo(
                name=name,
                website=website,
                city=city,
                region=None,
                address=address,
                sector=category,
                phone=phone,
                source=self.source_name
            )
        
        except Exception as e:
            logger.debug(f"Error extracting company info from Google listing: {e}")
            return None
    
    def has_next_page(self, page_soup: BeautifulSoup) -> bool:
        """Check if there are more pages available on Google Maps"""
        # Google Maps uses infinite scroll, so we'll limit to first page for now
        return False


# Convenience function
async def fetch_google_companies(cities: Optional[list] = None, 
                                sectors: Optional[list] = None) -> int:
    """Convenience function to fetch UK companies from Google Business"""
    async with GoogleBusinessFetcher() as fetcher:
        return await fetcher.fetch_companies_batch(cities or [], sectors)


if __name__ == "__main__":
    # Test the fetcher
    import asyncio
    
    async def test_fetcher():
        async with GoogleBusinessFetcher() as fetcher:
            # Test with small sample
            test_cities = ['Brighton']
            test_sectors = ['retail']
            
            companies_found = await fetcher.fetch_companies_batch(test_cities, test_sectors)
            print(f"Found {companies_found} companies from Google Business")

    asyncio.run(test_fetcher()) 