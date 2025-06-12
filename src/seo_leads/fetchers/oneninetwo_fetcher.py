"""
192.com UK Directory Fetcher

Scrapes UK company data from 192.com directory.
192.com is a comprehensive UK business directory with extensive coverage.
"""

import logging
from typing import Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .base_fetcher import BaseDirectoryFetcher, CompanyBasicInfo

logger = logging.getLogger(__name__)


class OneNineTwoFetcher(BaseDirectoryFetcher):
    """
    192.com directory scraper
    
    192.com (https://www.192.com) is a comprehensive UK business directory
    providing detailed business listings across all regions of the UK.
    """
    
    def __init__(self):
        super().__init__("192.com")
    
    def get_base_url(self) -> str:
        """Return the base URL for 192.com"""
        return "https://www.192.com"
    
    def build_search_url(self, city: str, sector: Optional[str] = None, page: int = 1) -> str:
        """Build search URL for 192.com city/sector combination"""
        base_url = self.get_base_url()
        
        if sector:
            # Format: /business/search?business=sector&location=city&page=X
            search_url = f"{base_url}/business/search?business={quote_plus(sector)}&location={quote_plus(city)}"
        else:
            # Format: /business/search?location=city&page=X
            search_url = f"{base_url}/business/search?location={quote_plus(city)}"
        
        # Add page parameter if not first page
        if page > 1:
            search_url += f"&page={page}"
        
        return search_url
    
    def get_listing_selector(self) -> str:
        """Return CSS selector for business listings on 192.com"""
        return '.business-listing, .listing-item, .business-item, .search-result'
    
    def parse_listing(self, listing_element, city: str) -> Optional[CompanyBasicInfo]:
        """Parse a single 192.com business listing"""
        try:
            # Company name - try multiple selectors
            name = None
            name_selectors = [
                '.business-name',
                '.listing-name',
                'h3 a',
                'h2 a',
                '.title',
                '.company-name'
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
                'a[title*="website" i]',
                '.business-url a',
                'a[href^="http"]:not([href*="192.com"])'  # External links
            ]
            
            for selector in website_selectors:
                website_elem = listing_element.select_one(selector)
                if website_elem:
                    href = website_elem.get('href')
                    if href and href.startswith('http') and '192.com' not in href:
                        website = href
                        break
            
            # Address - try multiple selectors
            address = None
            address_selectors = [
                '.business-address',
                '.listing-address',
                '.address',
                '.location'
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
                '.business-phone',
                '.phone-number',
                '.listing-phone'
            ]
            
            for selector in phone_selectors:
                phone_elem = listing_element.select_one(selector)
                if phone_elem:
                    phone = phone_elem.get_text(strip=True)
                    # Clean up phone number
                    if phone:
                        phone = phone.replace('Tel:', '').replace('Phone:', '').strip()
                        if phone:
                            break
            
            # Sector/Category - try multiple selectors
            sector = None
            sector_selectors = [
                '.business-category',
                '.listing-category',
                '.category',
                '.business-type'
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
            logger.debug(f"Error extracting company info from 192.com listing: {e}")
            return None
    
    def has_next_page(self, page_soup: BeautifulSoup) -> bool:
        """Check if there are more pages available on 192.com"""
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
async def fetch_192_companies(cities: Optional[list] = None, 
                            sectors: Optional[list] = None) -> int:
    """Convenience function to fetch UK companies from 192.com"""
    async with OneNineTwoFetcher() as fetcher:
        return await fetcher.fetch_companies_batch(cities or [], sectors)


if __name__ == "__main__":
    # Test the fetcher
    import asyncio
    
    async def test_fetcher():
        async with OneNineTwoFetcher() as fetcher:
            # Test with small sample
            test_cities = ['Liverpool']
            test_sectors = ['restaurant']
            
            companies_found = await fetcher.fetch_companies_batch(test_cities, test_sectors)
            print(f"Found {companies_found} companies from 192.com")
    
    asyncio.run(test_fetcher()) 