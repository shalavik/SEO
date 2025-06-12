"""
Yelp UK Directory Fetcher

Alternative UK business directory scraper for when Yell.com is blocked.
Yelp UK has good coverage of UK businesses and is typically more accessible.
"""

import logging
from typing import Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .base_fetcher import BaseDirectoryFetcher, CompanyBasicInfo

logger = logging.getLogger(__name__)


class YelpUKDirectoryFetcher(BaseDirectoryFetcher):
    """
    Yelp UK directory scraper as alternative to Yell.com
    
    Features:
    - Good UK business coverage
    - Less aggressive bot detection
    - Similar data structure to Yell.com
    """
    
    def __init__(self):
        super().__init__("Yelp UK")
    
    def get_base_url(self) -> str:
        """Return the base URL for Yelp UK"""
        return "https://www.yelp.co.uk"
    
    def build_search_url(self, city: str, sector: Optional[str] = None, page: int = 1) -> str:
        """Build search URL for Yelp UK city/sector combination"""
        base_url = self.get_base_url()
        
        # Yelp UK uses /search format
        search_term = sector if sector else "businesses"
        location = city
        
        search_url = f"{base_url}/search?find_desc={quote_plus(search_term)}&find_loc={quote_plus(location)}"
        
        # Add page parameter if not first page (Yelp uses 'start' parameter)
        if page > 1:
            start = (page - 1) * 10  # Yelp typically shows 10 results per page
            search_url += f"&start={start}"
        
        return search_url
    
    def get_listing_selector(self) -> str:
        """Return CSS selector for business listings on Yelp UK"""
        return '[data-testid="serp-ia-card"]'
    
    def parse_listing(self, listing_element, city: str) -> Optional[CompanyBasicInfo]:
        """Parse a single Yelp UK business listing"""
        try:
            # Company name - look for business name in the card
            name = None
            name_selectors = [
                'h3 a span',
                'h3 span',
                'a[href*="/biz/"] span',
                '.css-1m051bw',  # Common Yelp class for business names
                'h3',
                'h4'
            ]
            
            for selector in name_selectors:
                name_elem = listing_element.select_one(selector)
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    if name and len(name) > 2:  # Valid business name
                        break
            
            if not name:
                return None
            
            # Website - Yelp business profile URL (we can extract website later)
            website = None
            profile_selectors = [
                'h3 a[href*="/biz/"]',
                'a[href*="/biz/"]'
            ]
            
            for selector in profile_selectors:
                profile_elem = listing_element.select_one(selector)
                if profile_elem:
                    href = profile_elem.get('href')
                    if href:
                        if href.startswith('/'):
                            website = f"{self.get_base_url()}{href}"
                        else:
                            website = href
                        break
            
            # Address - look for address information
            address = None
            address_selectors = [
                '[data-testid="address"]',
                '.css-1e4fdj9',  # Common Yelp address class
                'p:contains("Brighton")',
                'span:contains("Brighton")'
            ]
            
            for selector in address_selectors:
                address_elem = listing_element.select_one(selector)
                if address_elem:
                    address_text = address_elem.get_text(strip=True)
                    if address_text and ('Brighton' in address_text or len(address_text) > 10):
                        address = address_text
                        break
            
            # Phone - look for phone numbers
            phone = None
            phone_selectors = [
                '[data-testid="phone"]',
                'a[href^="tel:"]',
                '.css-1p9ibgf'  # Common Yelp phone class
            ]
            
            for selector in phone_selectors:
                phone_elem = listing_element.select_one(selector)
                if phone_elem:
                    if selector == 'a[href^="tel:"]':
                        phone = phone_elem.get('href', '').replace('tel:', '')
                    else:
                        phone = phone_elem.get_text(strip=True)
                    if phone:
                        break
            
            # Sector/Category - look for category information
            sector = None
            sector_selectors = [
                '[data-testid="categories"]',
                '.css-1fdy0l5',  # Common Yelp category class
                'span:contains("Restaurant")',
                'span:contains("Shop")',
                'span:contains("Store")'
            ]
            
            for selector in sector_selectors:
                sector_elem = listing_element.select_one(selector)
                if sector_elem:
                    raw_sector = sector_elem.get_text(strip=True)
                    if raw_sector:
                        sector = self._map_sector(raw_sector)
                        break
            
            # If no specific sector found, use the search term
            if not sector:
                sector = "retail"  # Default for our search
            
            return CompanyBasicInfo(
                name=name,
                website=website,  # This will be Yelp profile URL
                city=city,
                region=None,
                address=address,
                sector=sector,
                phone=phone,
                source=self.source_name
            )
        
        except Exception as e:
            logger.debug(f"Error extracting company info from Yelp UK listing: {e}")
            return None
    
    def has_next_page(self, page_soup: BeautifulSoup) -> bool:
        """Check if there are more pages available on Yelp UK"""
        # Look for next page indicators
        next_selectors = [
            '.next-link',
            'a[aria-label="Next"]',
            '.pagination .next:not(.disabled)',
            '.pager .next'
        ]
        
        for selector in next_selectors:
            next_elem = page_soup.select_one(selector)
            if next_elem and not next_elem.get('disabled'):
                return True
        
        return False


# Convenience functions
async def fetch_uk_companies_yelp(cities: Optional[list] = None, 
                                 sectors: Optional[list] = None) -> int:
    """Convenience function to fetch UK companies from Yelp UK"""
    async with YelpUKDirectoryFetcher() as fetcher:
        return await fetcher.fetch_companies_batch(cities or [], sectors)


if __name__ == "__main__":
    # Test the fetcher
    import asyncio
    
    async def test_fetcher():
        async with YelpUKDirectoryFetcher() as fetcher:
            # Test with small sample
            test_cities = ['London']
            test_sectors = ['restaurant']
            
            companies_found = await fetcher.fetch_companies_batch(test_cities, test_sectors)
            print(f"Found {companies_found} companies from Yelp UK")
    
    asyncio.run(test_fetcher()) 