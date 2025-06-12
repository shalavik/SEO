"""
Yell.com UK Directory Fetcher

Scrapes UK company data from Yell.com directory with intelligent rate limiting,
batch processing, and state management for resumable operations.

Updated to use BaseDirectoryFetcher for consistency with other directory scrapers.
"""

import logging
from typing import Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .base_fetcher import BaseDirectoryFetcher, CompanyBasicInfo

logger = logging.getLogger(__name__)


class YellDirectoryFetcher(BaseDirectoryFetcher):
    """
    Yell.com directory scraper with batch processing and state management
    
    Features:
    - Intelligent rate limiting
    - Resume from previous state
    - Batch processing with database persistence
    - Error recovery and retry logic
    """
    
    def __init__(self):
        super().__init__("Yell.com")
    
    def get_base_url(self) -> str:
        """Return the base URL for Yell.com"""
        return "https://www.yell.com"
    
    def build_search_url(self, city: str, sector: Optional[str] = None, page: int = 1) -> str:
        """Build search URL for Yell.com city/sector combination"""
        base_url = self.get_base_url()
        
        if sector:
            # Format: /s/sector-city.html
            search_url = f"{base_url}/s/{quote_plus(sector.replace(' ', '-'))}-{quote_plus(city.replace(' ', '-'))}.html"
        else:
            # Format: /s/companies-city.html
            search_url = f"{base_url}/s/companies-{quote_plus(city.replace(' ', '-'))}.html"
        
        # Add page parameter if not first page
        if page > 1:
            search_url += f"?page={page}"
        
        return search_url
    
    def get_listing_selector(self) -> str:
        """Return CSS selector for business listings on Yell.com"""
        # Updated selectors to handle current Yell.com structure
        return 'div.businessCapsule--mainContent, div[data-business-id], .business-listing, .searchResultItem'
    
    def parse_listing(self, listing_element, city: str) -> Optional[CompanyBasicInfo]:
        """Parse a single Yell.com business listing"""
        try:
            # Company name - try multiple selectors
            name = None
            name_selectors = [
                'h2.businessCapsule--name',
                'h2 a span[title]',
                '.business-name',
                '.title a',
                'h2 a',
                'h3 a'
            ]
            
            for selector in name_selectors:
                name_elem = listing_element.select_one(selector)
                if name_elem:
                    name = name_elem.get('title') or name_elem.get_text(strip=True)
                    if name:
                        break
            
            if not name:
                return None
            
            # Website - try multiple selectors
            website = None
            website_selectors = [
                'a[data-tracking="website"]',
                'a[href*="yell.com/go/"]',
                '.website-link',
                'a[title*="website"]'
            ]
            
            for selector in website_selectors:
                website_elem = listing_element.select_one(selector)
                if website_elem:
                    href = website_elem.get('href')
                    if href:
                        # Extract actual website from Yell redirect
                        if 'yell.com/go/' in href:
                            # This is a Yell redirect, we'll keep the redirect URL
                            website = href
                        elif href.startswith('http'):
                            website = href
                        elif not href.startswith('/'):
                            website = f"https://{href}"
                        break
            
            # Address - try multiple selectors
            address = None
            address_selectors = [
                'span.businessCapsule--address',
                '.address',
                '.location',
                '.contact-info .address'
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
                'a[data-tracking="phone"]',
                'a[href^="tel:"]',
                '.phone-number',
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
                'span.businessCapsule--classification',
                '.business-category',
                '.category',
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
                region=None,  # Yell.com doesn't typically provide region info
                address=address,
                sector=sector,
                phone=phone,
                source=self.source_name
            )
        
        except Exception as e:
            logger.debug(f"Error extracting company info from Yell.com listing: {e}")
            return None
    
    def has_next_page(self, page_soup: BeautifulSoup) -> bool:
        """Check if there are more pages available on Yell.com"""
        # Look for next page indicators
        next_selectors = [
            'a[data-tracking="next"]',
            'a.next',
            '.pagination .next:not(.disabled)',
            '.paging .next:not(.disabled)',
            'a[aria-label="Next page"]'
        ]
        
        for selector in next_selectors:
            next_elem = page_soup.select_one(selector)
            if next_elem and not next_elem.get('disabled'):
                return True
        
        return False


# Convenience functions for backward compatibility
async def fetch_uk_companies(cities: Optional[list] = None, 
                           sectors: Optional[list] = None) -> int:
    """Convenience function to fetch UK companies from Yell.com"""
    async with YellDirectoryFetcher() as fetcher:
        return await fetcher.fetch_companies_batch(cities or [], sectors)


if __name__ == "__main__":
    # Test the fetcher
    import asyncio
    
    async def test_fetcher():
        async with YellDirectoryFetcher() as fetcher:
            # Test with small sample
            test_cities = ['Brighton']
            test_sectors = ['restaurant']
            
            companies_found = await fetcher.fetch_companies_batch(test_cities, test_sectors)
            print(f"Found {companies_found} companies")
    
    asyncio.run(test_fetcher()) 