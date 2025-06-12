"""
Foursquare UK Directory Fetcher

Scrapes UK company data from Foursquare UK directory.
Foursquare provides location-based business data and listings.
"""

import logging
from typing import Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .base_fetcher import BaseDirectoryFetcher, CompanyBasicInfo

logger = logging.getLogger(__name__)


class FoursquareUKFetcher(BaseDirectoryFetcher):
    """
    Foursquare UK directory scraper
    
    Foursquare (https://foursquare.com) provides location-based business data
    and comprehensive listings across the UK.
    """
    
    def __init__(self):
        super().__init__("Foursquare UK")
    
    def get_base_url(self) -> str:
        """Return the base URL for Foursquare"""
        return "https://foursquare.com"
    
    def build_search_url(self, city: str, sector: Optional[str] = None, page: int = 1) -> str:
        """Build search URL for Foursquare UK city/sector combination"""
        base_url = self.get_base_url()
        
        if sector:
            # Format: /explore?mode=url&near=city,UK&q=sector
            search_url = f"{base_url}/explore?mode=url&near={quote_plus(city)},UK&q={quote_plus(sector)}"
        else:
            # Format: /explore?mode=url&near=city,UK
            search_url = f"{base_url}/explore?mode=url&near={quote_plus(city)},UK"
        
        # Foursquare uses infinite scroll, but we can simulate pagination
        if page > 1:
            search_url += f"&offset={page * 20}"
        
        return search_url
    
    def get_listing_selector(self) -> str:
        """Return CSS selector for business listings on Foursquare"""
        return '.venueItem, .venue-item, .search-result, .venue-card'
    
    def parse_listing(self, listing_element, city: str) -> Optional[CompanyBasicInfo]:
        """Parse a single Foursquare business listing"""
        try:
            # Company name - try multiple selectors
            name = None
            name_selectors = [
                '.venue-name',
                '.business-name',
                'h3 a',
                'h2 a',
                '.title',
                '.venueName'
            ]
            
            for selector in name_selectors:
                name_elem = listing_element.select_one(selector)
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    if name:
                        break
            
            if not name:
                return None
            
            # Website - Foursquare may not directly show websites in search results
            # We'll capture the Foursquare venue URL which can be used to get website later
            website = None
            profile_selectors = [
                'a[href*="/v/"]',  # Foursquare venue links
                '.venue-link',
                'h3 a',
                'h2 a'
            ]
            
            for selector in profile_selectors:
                profile_elem = listing_element.select_one(selector)
                if profile_elem:
                    href = profile_elem.get('href')
                    if href:
                        # Convert to full URL if relative
                        if href.startswith('/'):
                            website = f"{self.get_base_url()}{href}"
                        else:
                            website = href
                        break
            
            # Address - try multiple selectors
            address = None
            address_selectors = [
                '.venue-address',
                '.business-address',
                '.address',
                '.location'
            ]
            
            for selector in address_selectors:
                address_elem = listing_element.select_one(selector)
                if address_elem:
                    address = address_elem.get_text(strip=True)
                    if address:
                        break
            
            # Phone - Foursquare may not show phone in search results
            phone = None
            phone_selectors = [
                'a[href^="tel:"]',
                '.venue-phone',
                '.phone-number',
                '.business-phone'
            ]
            
            for selector in phone_selectors:
                phone_elem = listing_element.select_one(selector)
                if phone_elem:
                    phone = phone_elem.get_text(strip=True)
                    if phone:
                        break
            
            # Sector/Category - try multiple selectors
            sector = None
            sector_selectors = [
                '.venue-category',
                '.business-category',
                '.category',
                '.venue-type'
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
                website=website,  # This will be Foursquare venue URL
                city=city,
                region=None,
                address=address,
                sector=sector,
                phone=phone,
                source=self.source_name
            )
        
        except Exception as e:
            logger.debug(f"Error extracting company info from Foursquare listing: {e}")
            return None
    
    def has_next_page(self, page_soup: BeautifulSoup) -> bool:
        """Check if there are more pages available on Foursquare"""
        # Foursquare uses infinite scroll, so we check for presence of venues
        # and limit to a reasonable number of pages
        venues = page_soup.select(self.get_listing_selector())
        
        # If we found venues and haven't hit our limit, assume more pages exist
        return len(venues) > 0
    
    async def _search_companies_in_city(self, city: str, sector: Optional[str] = None) -> list:
        """Override to limit Foursquare pages since it uses infinite scroll"""
        companies = []
        
        try:
            page_number = 1
            max_pages = 5  # Limit Foursquare to 5 pages due to infinite scroll
            
            while page_number <= max_pages:
                # Rate limiting
                self._rate_limit()
                
                # Build page URL
                search_url = self.build_search_url(city, sector, page_number)
                
                logger.debug(f"Fetching page {page_number}: {search_url}")
                
                try:
                    # Navigate to page
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


# Convenience function
async def fetch_foursquare_companies(cities: Optional[list] = None, 
                                   sectors: Optional[list] = None) -> int:
    """Convenience function to fetch UK companies from Foursquare"""
    async with FoursquareUKFetcher() as fetcher:
        return await fetcher.fetch_companies_batch(cities or [], sectors)


if __name__ == "__main__":
    # Test the fetcher
    import asyncio
    
    async def test_fetcher():
        async with FoursquareUKFetcher() as fetcher:
            # Test with small sample
            test_cities = ['Newcastle']
            test_sectors = ['restaurant']
            
            companies_found = await fetcher.fetch_companies_batch(test_cities, test_sectors)
            print(f"Found {companies_found} companies from Foursquare")
    
    asyncio.run(test_fetcher()) 