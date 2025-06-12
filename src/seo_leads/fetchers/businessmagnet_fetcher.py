"""
Business Magnet UK Directory Fetcher

Scrapes UK company data from Business Magnet UK directory.
Business Magnet provides UK business listings and directory services.
"""

import logging
from typing import Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .base_fetcher import BaseDirectoryFetcher, CompanyBasicInfo

logger = logging.getLogger(__name__)


class BusinessMagnetFetcher(BaseDirectoryFetcher):
    """
    Business Magnet UK directory scraper
    
    Business Magnet (https://www.businessmagnet.co.uk) provides UK business
    directory services with comprehensive company listings.
    """
    
    def __init__(self):
        super().__init__("Business Magnet")
    
    def get_base_url(self) -> str:
        """Return the base URL for Business Magnet"""
        return "https://www.businessmagnet.co.uk"
    
    def build_search_url(self, city: str, sector: Optional[str] = None, page: int = 1) -> str:
        """Build search URL for Business Magnet city/sector combination"""
        base_url = self.get_base_url()
        
        if sector:
            # Format: /search?category=sector&location=city&page=X
            search_url = f"{base_url}/search?category={quote_plus(sector)}&location={quote_plus(city)}"
        else:
            # Format: /search?location=city&page=X
            search_url = f"{base_url}/search?location={quote_plus(city)}"
        
        # Add page parameter if not first page
        if page > 1:
            search_url += f"&page={page}"
        
        return search_url
    
    def get_listing_selector(self) -> str:
        """Return CSS selector for business listings on Business Magnet"""
        return '.business-listing, .company-item, .directory-entry, .listing-card'
    
    def parse_listing(self, listing_element, city: str) -> Optional[CompanyBasicInfo]:
        """Parse a single Business Magnet business listing"""
        try:
            # Company name - try multiple selectors
            name = None
            name_selectors = [
                '.business-name',
                '.company-title',
                'h3 a',
                'h2 a',
                '.listing-title',
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
                '.business-website a',
                'a[href^="http"]:not([href*="businessmagnet"])'  # External links
            ]
            
            for selector in website_selectors:
                website_elem = listing_element.select_one(selector)
                if website_elem:
                    href = website_elem.get('href')
                    if href and href.startswith('http') and 'businessmagnet' not in href:
                        website = href
                        break
            
            # Address - try multiple selectors
            address = None
            address_selectors = [
                '.business-address',
                '.company-address',
                '.address',
                '.location-info'
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
                '.contact-phone'
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
                '.company-category',
                '.category',
                '.industry'
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
            logger.debug(f"Error extracting company info from Business Magnet listing: {e}")
            return None
    
    def has_next_page(self, page_soup: BeautifulSoup) -> bool:
        """Check if there are more pages available on Business Magnet"""
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
async def fetch_businessmagnet_companies(cities: Optional[list] = None, 
                                       sectors: Optional[list] = None) -> int:
    """Convenience function to fetch UK companies from Business Magnet"""
    async with BusinessMagnetFetcher() as fetcher:
        return await fetcher.fetch_companies_batch(cities or [], sectors)


if __name__ == "__main__":
    # Test the fetcher
    import asyncio
    
    async def test_fetcher():
        async with BusinessMagnetFetcher() as fetcher:
            # Test with small sample
            test_cities = ['Edinburgh']
            test_sectors = ['restaurant']
            
            companies_found = await fetcher.fetch_companies_batch(test_cities, test_sectors)
            print(f"Found {companies_found} companies from Business Magnet")
    
    asyncio.run(test_fetcher()) 