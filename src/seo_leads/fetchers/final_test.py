#!/usr/bin/env python3
"""
Final End-to-End Test for All Directory Scrapers
Fetches 2 entries from each of the 11 directory sites to validate functionality
"""

import asyncio
import sys
import logging
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.seo_leads.fetchers import DIRECTORY_SOURCES, get_fetcher

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_end_to_end():
    """Test all 11 scrapers with small sample to validate functionality"""
    print('🚀 STARTING END-TO-END TEST FOR ALL 11 DIRECTORY SCRAPERS')
    print('=' * 70)
    
    # Test configuration - small sample to get 2 entries per site
    test_cities = ['Brighton']  # Single city for faster testing
    test_sectors = ['restaurant']  # Single sector
    
    results = {}
    total_companies = 0
    successful_scrapers = 0
    
    print(f'Testing with: Cities={test_cities}, Sectors={test_sectors}')
    print(f'Target: 2 entries per site across {len(DIRECTORY_SOURCES)} sources')
    print('-' * 70)
    
    for i, (source_key, fetcher_class) in enumerate(DIRECTORY_SOURCES.items(), 1):
        print(f'[{i:2d}/11] Testing {source_key}...', end=' ', flush=True)
        
        try:
            async with get_fetcher(source_key) as fetcher:
                # Override max pages to get small sample quickly
                if hasattr(fetcher, 'processing_config'):
                    original_max = getattr(fetcher.processing_config, 'max_companies_per_city', 1000)
                    fetcher.processing_config.max_companies_per_city = 2
                
                companies_found = await fetcher.fetch_companies_batch(test_cities, test_sectors)
                
                results[source_key] = {
                    'companies': companies_found,
                    'success': True,
                    'error': None
                }
                
                total_companies += companies_found
                successful_scrapers += 1
                
                print(f'✅ {companies_found} companies')
                
        except Exception as e:
            error_msg = str(e)[:100] + '...' if len(str(e)) > 100 else str(e)
            results[source_key] = {
                'companies': 0,
                'success': False,
                'error': error_msg
            }
            print(f'❌ Error: {error_msg}')
        
        # Small delay between requests to be respectful
        if i < len(DIRECTORY_SOURCES):
            await asyncio.sleep(1)
    
    # Summary
    print('=' * 70)
    print('📊 FINAL RESULTS SUMMARY')
    print('=' * 70)
    
    print(f'✅ Successful scrapers: {successful_scrapers}/{len(DIRECTORY_SOURCES)}')
    print(f'📈 Total companies found: {total_companies}')
    print(f'📊 Average per scraper: {total_companies/len(DIRECTORY_SOURCES):.1f}')
    
    print('\n📋 DETAILED RESULTS:')
    print(f"{'Source':<15} {'Status':<8} {'Companies':<10} {'Error'}")
    print('-' * 70)
    
    for source, result in results.items():
        status = '✅ OK' if result['success'] else '❌ FAIL'
        error = result['error'] or ''
        error_short = error[:30] + '...' if len(error) > 30 else error
        
        print(f"{source:<15} {status:<8} {result['companies']:<10} {error_short}")
    
    if successful_scrapers == len(DIRECTORY_SOURCES):
        print('\n🎉 ALL SCRAPERS WORKING! End-to-end test PASSED!')
        return True
    else:
        failed = len(DIRECTORY_SOURCES) - successful_scrapers
        print(f'\n⚠️  {failed} scrapers failed. Check errors above.')
        return False

# Run the test
if __name__ == '__main__':
    success = asyncio.run(test_end_to_end())
    sys.exit(0 if success else 1) 