"""
Test All Directory Scrapers

Utility script to test all UK business directory scrapers with various configurations.
Useful for validation and performance testing.
"""

import asyncio
import logging
import time
from typing import List, Dict, Optional

from . import (
    fetch_from_all_sources, get_fetcher, DIRECTORY_SOURCES,
    YellDirectoryFetcher, ThomsonLocalFetcher, YelpUKFetcher
)
from .directory_config import (
    get_recommended_sources, UK_MAJOR_CITIES, UK_BUSINESS_SECTORS,
    PRIORITY_GROUPS
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_single_scraper(source_name: str, 
                            cities: List[str], 
                            sectors: Optional[List[str]] = None) -> Dict:
    """Test a single scraper and return results"""
    try:
        start_time = time.time()
        logger.info(f"Testing {source_name} scraper...")
        
        async with get_fetcher(source_name) as fetcher:
            companies_found = await fetcher.fetch_companies_batch(cities, sectors)
        
        duration = time.time() - start_time
        
        result = {
            'source': source_name,
            'companies_found': companies_found,
            'duration_seconds': round(duration, 2),
            'success': True,
            'error': None
        }
        
        logger.info(f"{source_name}: Found {companies_found} companies in {duration:.2f}s")
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        error_msg = str(e)
        
        result = {
            'source': source_name,
            'companies_found': 0,
            'duration_seconds': round(duration, 2),
            'success': False,
            'error': error_msg
        }
        
        logger.error(f"{source_name}: Error - {error_msg}")
        return result


async def test_all_scrapers(cities: List[str], 
                          sectors: Optional[List[str]] = None,
                          sources: Optional[List[str]] = None) -> List[Dict]:
    """Test all or specified scrapers"""
    if sources is None:
        sources = list(DIRECTORY_SOURCES.keys())
    
    logger.info(f"Testing {len(sources)} scrapers with cities: {cities}")
    if sectors:
        logger.info(f"Filtering by sectors: {sectors}")
    
    results = []
    total_start = time.time()
    
    for source in sources:
        result = await test_single_scraper(source, cities, sectors)
        results.append(result)
        
        # Add delay between scrapers to be respectful
        await asyncio.sleep(2)
    
    total_duration = time.time() - total_start
    
    # Summary
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    total_companies = sum(r['companies_found'] for r in successful)
    
    logger.info(f"\n=== SUMMARY ===")
    logger.info(f"Total duration: {total_duration:.2f}s")
    logger.info(f"Successful scrapers: {len(successful)}/{len(results)}")
    logger.info(f"Total companies found: {total_companies}")
    logger.info(f"Failed scrapers: {[r['source'] for r in failed]}")
    
    return results


async def quick_test():
    """Quick test with a few sources and small search"""
    logger.info("=== QUICK TEST ===")
    
    # Test with high-quality sources only
    sources = PRIORITY_GROUPS['high_quality'][:3]  # Top 3 sources
    cities = ['Brighton']  # Single city
    sectors = ['restaurant']  # Single sector
    
    results = await test_all_scrapers(cities, sectors, sources)
    return results


async def comprehensive_test():
    """Comprehensive test with multiple cities and sectors"""
    logger.info("=== COMPREHENSIVE TEST ===")
    
    # Test with multiple cities and sectors
    cities = ['London', 'Manchester', 'Birmingham']
    sectors = ['restaurant', 'retail']
    sources = PRIORITY_GROUPS['high_quality']  # High-quality sources
    
    results = await test_all_scrapers(cities, sectors, sources)
    return results


async def sector_specific_test(sector: str):
    """Test scrapers optimized for a specific sector"""
    logger.info(f"=== SECTOR SPECIFIC TEST: {sector.upper()} ===")
    
    # Get recommended sources for this sector
    sources = get_recommended_sources(sector, quality_focus=True)
    cities = ['London', 'Bristol']  # Two cities
    sectors = [sector]
    
    results = await test_all_scrapers(cities, sectors, sources)
    return results


async def reliability_test():
    """Test the most reliable scrapers with various configurations"""
    logger.info("=== RELIABILITY TEST ===")
    
    # Test Yell.com with different configurations
    configs = [
        (['London'], ['restaurant']),
        (['Manchester'], ['retail']),
        (['Birmingham'], None),  # No sector filter
    ]
    
    all_results = []
    
    for cities, sectors in configs:
        logger.info(f"Testing config: cities={cities}, sectors={sectors}")
        result = await test_single_scraper('yell', cities, sectors)
        all_results.append(result)
        await asyncio.sleep(3)  # Longer delay for reliability test
    
    return all_results


def print_detailed_results(results: List[Dict]):
    """Print detailed results in a formatted table"""
    print("\n" + "="*80)
    print("DETAILED RESULTS")
    print("="*80)
    print(f"{'Source':<20} {'Companies':<10} {'Duration':<10} {'Status':<10} {'Error'}")
    print("-"*80)
    
    for result in results:
        status = "SUCCESS" if result['success'] else "FAILED"
        error = result['error'][:30] + "..." if result['error'] and len(result['error']) > 30 else result['error'] or ""
        
        print(f"{result['source']:<20} {result['companies_found']:<10} {result['duration_seconds']:<10} {status:<10} {error}")
    
    print("-"*80)


async def main():
    """Main test function with different test modes"""
    import sys
    
    # Parse command line arguments
    test_mode = 'quick'
    if len(sys.argv) > 1:
        test_mode = sys.argv[1]
    
    if test_mode == 'quick':
        results = await quick_test()
    elif test_mode == 'comprehensive':
        results = await comprehensive_test()
    elif test_mode == 'reliability':
        results = await reliability_test()
    elif test_mode.startswith('sector:'):
        sector = test_mode.split(':')[1]
        results = await sector_specific_test(sector)
    else:
        logger.info("Available test modes:")
        logger.info("  quick - Test top 3 sources with 1 city")
        logger.info("  comprehensive - Test high-quality sources with multiple cities")
        logger.info("  reliability - Test Yell.com with different configurations")
        logger.info("  sector:SECTOR_NAME - Test sources optimized for specific sector")
        logger.info("  Examples: sector:restaurant, sector:retail, sector:professional")
        return
    
    print_detailed_results(results)


if __name__ == "__main__":
    # Example usage:
    # python test_all_scrapers.py quick
    # python test_all_scrapers.py comprehensive
    # python test_all_scrapers.py sector:restaurant
    # python test_all_scrapers.py reliability
    
    asyncio.run(main()) 