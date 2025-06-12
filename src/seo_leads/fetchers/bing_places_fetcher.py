"""
Bing Places Directory Fetcher

Scrapes UK company data from Bing Places via Bing Maps.
Bing Maps provides comprehensive business directory with good UK coverage.
"""

import logging
import asyncio
import random
from typing import Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .base_fetcher import BaseDirectoryFetcher, CompanyBasicInfo

logger = logging.getLogger(__name__)


class BingPlacesFetcher(BaseDirectoryFetcher):
    """
    Bing Places directory scraper
    
    Bing Places (via Bing Maps) provides comprehensive UK business listings
    with good geographic coverage and business details.
    """
    
    def __init__(self):
        super().__init__("Bing Places")
    
    def get_base_url(self) -> str:
        """Return the base URL for Bing Places"""
        return "https://www.bing.com"
    
    def build_search_url(self, city: str, sector: Optional[str] = None, page: int = 1) -> str:
        """Build search URL for Bing Maps business search"""
        base_url = self.get_base_url()
        
        if sector:
            # Format: /maps?q=sector+city+UK
            query = f"{sector}+{city}+UK"
        else:
            # Format: /maps?q=businesses+city+UK
            query = f"businesses+{city}+UK"
        
        search_url = f"{base_url}/maps?q={quote_plus(query)}"
        
        return search_url
    
    def get_listing_selector(self) -> str:
        """Return CSS selector for business listings on Bing Maps"""
        return '.taskItemCard, .business-card, [data-entity-id], .taskItem, .entityCard'
    
    async def setup_stealth_browser(self):
        """Setup browser with advanced stealth for Bing"""
        await super().setup_stealth_browser()
        
        # Add Bing-specific stealth measures
        await self.page.add_init_script("""
            // Remove automation indicators
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock Edge browser characteristics
            Object.defineProperty(navigator, 'userAgent', {
                get: () => 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            });
            
            // Mock plugins for Edge
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'PDF Viewer', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Microsoft Edge PDF Viewer', filename: 'edge-pdf-viewer' }
                ],
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-GB', 'en', 'en-US'],
            });
            
            // Mock Bing-specific objects
            window.Microsoft = {
                Maps: {
                    loadModule: function() {}
                }
            };
        """)
    
    async def fetch_page_with_retries(self, url: str, max_retries: int = 3):
        """Fetch page with Bing-specific retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to fetch Bing Maps page (attempt {attempt + 1})")
                
                # Visit Bing homepage first to establish session
                await self.page.goto("https://www.bing.com", wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(2, 4))
                
                # Human-like navigation
                await self.page.mouse.move(random.randint(100, 1000), random.randint(100, 600))
                await asyncio.sleep(0.5)
                
                # Navigate to search URL
                response = await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                if response.status == 200:
                    # Wait for dynamic content to load
                    await asyncio.sleep(random.uniform(4, 7))
                    
                    # Check if we got actual results
                    content = await self.page.content()
                    if 'maps' in content.lower() and ('business' in content.lower() or 'place' in content.lower()):
                        return response
                
                logger.warning(f"Bing Maps fetch attempt {attempt + 1} failed: {response.status}")
                await asyncio.sleep(random.uniform(3, 8))
                
            except Exception as e:
                logger.warning(f"Bing Maps fetch attempt {attempt + 1} error: {e}")
                await asyncio.sleep(random.uniform(2, 6))
        
        raise Exception(f"Failed to fetch Bing Maps page after {max_retries} attempts")
    
    def parse_listing(self, listing_element, city: str) -> Optional[CompanyBasicInfo]:
        """Parse a single Bing Places listing"""
        try:
            # Company name - Bing Maps specific selectors
            name = None
            name_selectors = [
                '.businessName',
                '.entityTitle',
                '.taskItemTitle',
                '[data-test-id="businessName"]',
                'h3',
                '.name',
                '.title'
            ]
            
            for selector in name_selectors:
                name_elem = listing_element.select_one(selector)
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    if name and len(name) > 2:
                        break
            
            if not name:
                return None
            
            # Address - Bing Maps specific
            address = None
            address_selectors = [
                '.businessAddress',
                '.entityAddress',
                '.taskItemAddress',
                '[data-test-id="businessAddress"]',
                '.address',
                '.location'
            ]
            
            for selector in address_selectors:
                address_elem = listing_element.select_one(selector)
                if address_elem:
                    address = address_elem.get_text(strip=True)
                    if address and len(address) > 5:
                        break
            
            # Category information
            category = None
            category_selectors = [
                '.businessCategory',
                '.entityCategory', 
                '.taskItemCategory',
                '[data-test-id="businessCategory"]',
                '.category',
                '.type'
            ]
            
            for selector in category_selectors:
                cat_elem = listing_element.select_one(selector)
                if cat_elem:
                    raw_category = cat_elem.get_text(strip=True)
                    if raw_category and '★' not in raw_category and 'rating' not in raw_category.lower():
                        category = self._map_sector(raw_category)
                        break
            
            # Phone number
            phone = None
            phone_selectors = [
                '.businessPhone',
                '.entityPhone',
                '.taskItemPhone',
                '[data-test-id="businessPhone"]',
                'a[href^="tel:"]',
                '.phone'
            ]
            
            for selector in phone_selectors:
                phone_elem = listing_element.select_one(selector)
                if phone_elem:
                    if phone_elem.get('href', '').startswith('tel:'):
                        phone = phone_elem.get('href')[4:]  # Remove 'tel:' prefix
                    else:
                        phone = phone_elem.get_text(strip=True)
                    if phone:
                        break
            
            # Website
            website = None
            website_selectors = [
                '.businessWebsite a',
                '.entityWebsite a', 
                '.taskItemWebsite a',
                '[data-test-id="businessWebsite"] a',
                'a[href^="http"]:not([href*="bing"])',
                '.website a'
            ]
            
            for selector in website_selectors:
                website_elem = listing_element.select_one(selector)
                if website_elem:
                    href = website_elem.get('href')
                    if href and href.startswith('http') and 'bing' not in href and 'microsoft' not in href:
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
            logger.debug(f"Error extracting company info from Bing listing: {e}")
            return None
    
    def has_next_page(self, page_soup: BeautifulSoup) -> bool:
        """Check if there are more pages available on Bing Maps"""
        # Look for next page indicators
        next_selectors = [
            '.pagination .next:not(.disabled)',
            '.paging .next:not(.disabled)',
            'a[aria-label="Next page"]:not(.disabled)',
            '.taskItemPaging .next:not(.disabled)'
        ]
        
        for selector in next_selectors:
            next_elem = page_soup.select_one(selector)
            if next_elem and not next_elem.get('disabled'):
                return True
        
        return False


# Convenience function
async def fetch_bing_companies(cities: Optional[list] = None, 
                              sectors: Optional[list] = None) -> int:
    """Convenience function to fetch UK companies from Bing Places"""
    async with BingPlacesFetcher() as fetcher:
        return await fetcher.fetch_companies_batch(cities or [], sectors)


if __name__ == "__main__":
    # Test the fetcher
    import asyncio
    
    async def test_fetcher():
        async with BingPlacesFetcher() as fetcher:
            # Test with small sample
            test_cities = ['Brighton']
            test_sectors = ['retail']
            
            companies_found = await fetcher.fetch_companies_batch(test_cities, test_sectors)
            print(f"Found {companies_found} companies from Bing Places")

    asyncio.run(test_fetcher()) 