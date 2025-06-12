"""
UK Business Directory Fetchers

The primary fetcher targets Yell.com for comprehensive UK business listings.
Additional fetchers cover 10 major UK business directories for comprehensive coverage.

Available Fetchers:
- YellDirectoryFetcher: Yell.com (original, updated)
- ThomsonLocalFetcher: Thomson Local
- YelpUKFetcher: Yelp UK
- CylexUKFetcher: Cylex UK
- HotfrogUKFetcher: Hotfrog UK
- BrownbookUKFetcher: Brownbook UK
- UKCOMFetcher: UK.COM Business Directory
- BusinessMagnetFetcher: Business Magnet
- TupaloUKFetcher: Tupalo UK
- FoursquareUKFetcher: Foursquare UK
- OneNineTwoFetcher: 192.com

All fetchers use a common BaseDirectoryFetcher class for consistent functionality.
"""

from .base_fetcher import BaseDirectoryFetcher, CompanyBasicInfo
from .yell_fetcher import YellDirectoryFetcher, fetch_uk_companies
from .thomson_fetcher import ThomsonLocalFetcher, fetch_thomson_companies
from .yelp_uk_fetcher import YelpUKDirectoryFetcher, fetch_uk_companies_yelp
from .google_business_fetcher import GoogleBusinessFetcher, fetch_google_companies
from .bing_places_fetcher import BingPlacesFetcher, fetch_bing_companies
from .cylex_fetcher import CylexUKFetcher, fetch_cylex_companies
from .hotfrog_fetcher import HotfrogUKFetcher, fetch_hotfrog_companies
from .brownbook_fetcher import BrownbookUKFetcher, fetch_brownbook_companies
from .ukcom_fetcher import UKCOMFetcher, fetch_ukcom_companies
from .businessmagnet_fetcher import BusinessMagnetFetcher, fetch_businessmagnet_companies
from .tupalo_fetcher import TupaloUKFetcher, fetch_tupalo_companies
from .foursquare_fetcher import FoursquareUKFetcher, fetch_foursquare_companies
from .oneninetwo_fetcher import OneNineTwoFetcher, fetch_192_companies

__all__ = [
    # Base classes
    'BaseDirectoryFetcher',
    'CompanyBasicInfo',
    
    # Fetcher classes
    'YellDirectoryFetcher',
    'ThomsonLocalFetcher',
    'YelpUKDirectoryFetcher',
    'GoogleBusinessFetcher',
    'BingPlacesFetcher',
    'CylexUKFetcher',
    'HotfrogUKFetcher',
    'BrownbookUKFetcher',
    'UKCOMFetcher',
    'BusinessMagnetFetcher',
    'TupaloUKFetcher',
    'FoursquareUKFetcher',
    'OneNineTwoFetcher',
    
    # Convenience functions
    'fetch_uk_companies',        # Yell.com
    'fetch_thomson_companies',   # Thomson Local
    'fetch_uk_companies_yelp',   # Yelp UK
    'fetch_google_companies',    # Google Business
    'fetch_bing_companies',      # Bing Places
    'fetch_cylex_companies',     # Cylex UK
    'fetch_hotfrog_companies',   # Hotfrog UK
    'fetch_brownbook_companies', # Brownbook UK
    'fetch_ukcom_companies',     # UK.COM
    'fetch_businessmagnet_companies', # Business Magnet
    'fetch_tupalo_companies',    # Tupalo UK
    'fetch_foursquare_companies', # Foursquare UK
    'fetch_192_companies',       # 192.com
]

# Directory source mapping for easy access
DIRECTORY_SOURCES = {
    'yell': YellDirectoryFetcher,
    'thomson': ThomsonLocalFetcher,
    'yelp': YelpUKDirectoryFetcher,
    'google': GoogleBusinessFetcher,
    'bing': BingPlacesFetcher,
    'cylex': CylexUKFetcher,
    'hotfrog': HotfrogUKFetcher,
    'brownbook': BrownbookUKFetcher,
    'ukcom': UKCOMFetcher,
    'businessmagnet': BusinessMagnetFetcher,
    'tupalo': TupaloUKFetcher,
    'foursquare': FoursquareUKFetcher,
    '192': OneNineTwoFetcher,
}

# Convenience function mapping
FETCH_FUNCTIONS = {
    'yell': fetch_uk_companies,
    'thomson': fetch_thomson_companies,
    'yelp': fetch_uk_companies_yelp,
    'google': fetch_google_companies,
    'bing': fetch_bing_companies,
    'cylex': fetch_cylex_companies,
    'hotfrog': fetch_hotfrog_companies,
    'brownbook': fetch_brownbook_companies,
    'ukcom': fetch_ukcom_companies,
    'businessmagnet': fetch_businessmagnet_companies,
    'tupalo': fetch_tupalo_companies,
    'foursquare': fetch_foursquare_companies,
    '192': fetch_192_companies,
}


async def fetch_from_all_sources(cities: list, sectors: list = None) -> dict:
    """
    Fetch companies from all directory sources
    
    Args:
        cities: List of UK cities to search
        sectors: Optional list of business sectors to filter by
        
    Returns:
        Dictionary mapping source name to number of companies found
    """
    results = {}
    
    for source_name, fetch_function in FETCH_FUNCTIONS.items():
        try:
            companies_found = await fetch_function(cities, sectors)
            results[source_name] = companies_found
        except Exception as e:
            print(f"Error fetching from {source_name}: {e}")
            results[source_name] = 0
    
    return results


def get_fetcher(source_name: str) -> BaseDirectoryFetcher:
    """
    Get a fetcher instance by source name
    
    Args:
        source_name: Name of the directory source (e.g., 'yell', 'thomson')
        
    Returns:
        Fetcher instance
        
    Raises:
        ValueError: If source_name is not recognized
    """
    if source_name not in DIRECTORY_SOURCES:
        available = ', '.join(DIRECTORY_SOURCES.keys())
        raise ValueError(f"Unknown source '{source_name}'. Available sources: {available}")
    
    fetcher_class = DIRECTORY_SOURCES[source_name]
    return fetcher_class() 