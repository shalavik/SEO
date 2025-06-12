"""
Cylex UK Directory Fetcher

Scrapes UK company data from Cylex UK directory.
Cylex is a European business directory with a UK section.
"""

import logging
from typing import Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .base_fetcher import BaseDirectoryFetcher, CompanyBasicInfo

logger = logging.getLogger(__name__)


class CylexUKFetcher(BaseDirectoryFetcher):
    """
    Cylex UK directory scraper
    
    Cylex UK (https://www.cylex-uk.co.uk) is part of the European Cylex network
    providing business directory services across the UK.
    """
    
    def __init__(self):
        super().__init__("Cylex UK")
    
    def get_base_url(self) -> str:
        """Return the base URL for Cylex UK"""
        return "https://www.cylex-uk.co.uk"
    
    def build_search_url(self, city: str, sector: Optional[str] = None, page: int = 1) -> str:
        """Build search URL for Cylex UK city/sector combination"""
        base_url = self.get_base_url()
        
        if sector:
            # Format: /search?what=sector&where=city&page=X
            search_url = f"{base_url}/search?what={quote_plus(sector)}&where={quote_plus(city)}"
        else:
            # Format: /search?where=city&page=X
            search_url = f"{base_url}/search?where={quote_plus(city)}"
        
        # Add page parameter if not first page
        if page > 1:
            search_url += f"&page={page}"
        
        return search_url
    
    def get_listing_selector(self) -> str:
        """Return CSS selector for business listings on Cylex UK"""
        return '.company-entry, .business-listing, .search-result-item, .listing'
    
    def parse_listing(self, listing_element, city: str) -> Optional[CompanyBasicInfo]:
        """Parse a single Cylex UK business listing"""
        try:
            # Company name - try multiple selectors
            name = None
            name_selectors = [
                '.company-name',
                '.business-name',
                'h3 a',
                'h2 a',
                '.title a',
                '.name'
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
                '.contact-website a',
                'a[href^="http"]:not([href*="cylex"])'  # External links
            ]
            
            for selector in website_selectors:
                website_elem = listing_element.select_one(selector)
                if website_elem:
                    href = website_elem.get('href')
                    if href and href.startswith('http') and 'cylex' not in href:
                        website = href
                        break
            
            # Address - try multiple selectors
            address = None
            address_selectors = [
                '.company-address',
                '.address',
                '.location',
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
                '.telephone',
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
                '.company-category',
                '.category',
                '.business-type',
                '.classification'
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
            logger.debug(f"Error extracting company info from Cylex UK listing: {e}")
            return None
    
    def has_next_page(self, page_soup: BeautifulSoup) -> bool:
        """Check if there are more pages available on Cylex UK"""
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
async def fetch_cylex_companies(cities: Optional[list] = None, 
                              sectors: Optional[list] = None) -> int:
    """Convenience function to fetch UK companies from Cylex UK"""
    async with CylexUKFetcher() as fetcher:
        return await fetcher.fetch_companies_batch(cities or [], sectors)


if __name__ == "__main__":
    # Test the fetcher
    import asyncio
    
    async def test_fetcher():
        async with CylexUKFetcher() as fetcher:
            # Test with small sample
            test_cities = ['Birmingham']
            test_sectors = ['restaurant']
            
            companies_found = await fetcher.fetch_companies_batch(test_cities, test_sectors)
            print(f"Found {companies_found} companies from Cylex UK")
    
    asyncio.run(test_fetcher()) 