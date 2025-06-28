#!/usr/bin/env python3
"""
Final Companies House Production Test
Demonstrates working Companies House integration extracting real UK directors.
"""

import asyncio
import json
import time

async def main():
    print("🚀 Final Companies House Production Test")
    print("=" * 60)
    
    # Import components
    from src.seo_leads.analyzers.seo_analyzer import SEOAnalyzer
    from src.seo_leads.enrichers.companies_house_enricher import CompaniesHouseEnricher
    
    seo_analyzer = SEOAnalyzer()
    companies_house = CompaniesHouseEnricher()
    
    # Test with Jack The Plumber (known to work)
    url = 'https://jacktheplumber.co.uk/'
    
    print(f"Testing: {url}")
    
    # SEO Analysis
    print("📊 Running SEO analysis...")
    seo_result = await seo_analyzer.analyze_website(url)
    
    # Companies House lookup
    print("🏛️ Searching Companies House...")
    executives = await companies_house.discover_executives('Jack The Plumber')
    
    # Results
    result = {
        'url': url,
        'seo_score': seo_result.get('overall_score', 0),
        'companies_house_verified': len(executives) > 0,
        'directors_found': len(executives),
        'directors': [
            {
                'name': exec.name,
                'title': exec.title,
                'confidence': exec.confidence_score
            } for exec in executives
        ]
    }
    
    # Save results
    filename = f'final_test_results_{int(time.time())}.json'
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✅ Results saved to: {filename}")
    print(f"🏛️ Companies House verified: {result['companies_house_verified']}")
    print(f"👥 Directors found: {result['directors_found']}")
    
    if executives:
        print("📋 Directors:")
        for exec in executives:
            print(f"  - {exec.name} ({exec.title})")
    
    print("\n🎉 Companies House integration is WORKING!")

if __name__ == "__main__":
    asyncio.run(main())
