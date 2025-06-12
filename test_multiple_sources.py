#!/usr/bin/env python3
"""
Test script to check multiple UK directory sources
"""

import asyncio
import sys
sys.path.insert(0, 'src')

from src.seo_leads.fetchers import get_fetcher

async def test_sources():
    """Test multiple UK directory sources"""
    
    sources_to_test = ['thomson', 'cylex', 'hotfrog', 'foursquare', 'brownbook']
    
    results = {}
    
    for source in sources_to_test:
        try:
            print(f'\n🔍 Testing {source}...')
            fetcher = get_fetcher(source)
            print(f'   Base URL: {fetcher.get_base_url()}')
            test_url = fetcher.build_search_url('Brighton', 'retail', 1)
            print(f'   Test URL: {test_url}')
            
            # Quick test with small limit
            async with fetcher:
                fetcher.processing_config.max_companies_per_city = 2
                companies = await fetcher.fetch_companies_batch(['Brighton'], ['retail'])
                print(f'   ✅ Result: {companies} companies found')
                results[source] = companies
                
        except Exception as e:
            print(f'   ❌ Error: {e}')
            results[source] = 0
    
    print(f'\n📊 Summary:')
    for source, count in results.items():
        status = "✅ Working" if count > 0 else "❌ Failed"
        print(f'   {source}: {count} companies - {status}')
    
    return results

if __name__ == "__main__":
    asyncio.run(test_sources()) 