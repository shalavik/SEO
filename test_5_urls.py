#!/usr/bin/env python3
"""
Test 5 URLs through the complete system (excluding Business Directory Enricher)
"""

import asyncio
import json
import time
from datetime import datetime
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from seo_leads.cli import SEOLeadsCLI

async def test_5_urls():
    """Test the system with 5 URLs"""
    
    urls = [
        "https://macplumbheat.co.uk/",
        "https://ltfplumbing.co.uk/subscription", 
        "http://www.ctmplumbing.co.uk/",
        "https://kingsheathplumbing.freeindex.co.uk/",
        "http://www.perry-plumbing.co.uk/"
    ]
    
    print("🚀 Testing Complete System with 5 URLs")
    print("=" * 50)
    
    cli = SEOLeadsCLI()
    results = []
    overall_start = time.time()
    
    for i, url in enumerate(urls, 1):
        print(f"\n🔄 Processing URL {i}/5: {url}")
        start_time = time.time()
        
        try:
            # Process single URL using CLI
            result = await cli.process_single_url(url, skip_business_directory=True)
            processing_time = time.time() - start_time
            
            if result:
                results.append({
                    'url': url,
                    'status': 'success',
                    'processing_time': round(processing_time, 2),
                    'company': result.get('company', {}),
                    'executives': result.get('executives', []),
                    'metrics': {
                        'executives_found': len(result.get('executives', [])),
                        'emails_found': len([e for e in result.get('executives', []) if e.get('email')]),
                        'phones_found': len(result.get('phone_numbers', [])),
                        'linkedin_profiles': len([e for e in result.get('executives', []) if e.get('linkedin_url')])
                    }
                })
                print(f"  ✅ Success in {processing_time:.2f}s")
            else:
                results.append({
                    'url': url,
                    'status': 'failed',
                    'processing_time': round(processing_time, 2),
                    'error': 'No result returned',
                    'metrics': {'executives_found': 0, 'emails_found': 0, 'phones_found': 0, 'linkedin_profiles': 0}
                })
                print(f"  ❌ Failed in {processing_time:.2f}s")
                
        except Exception as e:
            processing_time = time.time() - start_time
            results.append({
                'url': url,
                'status': 'error',
                'processing_time': round(processing_time, 2),
                'error': str(e),
                'metrics': {'executives_found': 0, 'emails_found': 0, 'phones_found': 0, 'linkedin_profiles': 0}
            })
            print(f"  ❌ Error in {processing_time:.2f}s: {e}")
    
    total_time = time.time() - overall_start
    successful_results = [r for r in results if r['status'] == 'success']
    
    # Calculate summary statistics
    summary = {
        'test_info': {
            'test_name': 'Complete System Test (5 URLs, No Business Directory)',
            'timestamp': datetime.now().isoformat(),
            'total_processing_time': round(total_time, 2),
            'urls_tested': len(urls)
        },
        'processing_stats': {
            'total_companies': len(results),
            'successful_companies': len(successful_results),
            'total_executives': sum(r['metrics']['executives_found'] for r in successful_results),
            'total_emails': sum(r['metrics']['emails_found'] for r in successful_results),
            'total_phones': sum(r['metrics']['phones_found'] for r in successful_results),
            'total_linkedin': sum(r['metrics']['linkedin_profiles'] for r in successful_results),
            'success_rate': (len(successful_results) / len(results)) * 100 if results else 0,
            'avg_processing_time': sum(r['processing_time'] for r in results) / len(results) if results else 0
        },
        'results': results,
        'summary': {
            'companies_processed': len(successful_results),
            'executives_discovered': sum(r['metrics']['executives_found'] for r in successful_results),
            'emails_discovered': sum(r['metrics']['emails_found'] for r in successful_results),
            'phone_numbers_discovered': sum(r['metrics']['phones_found'] for r in successful_results),
            'linkedin_profiles_found': sum(r['metrics']['linkedin_profiles'] for r in successful_results),
            'success_rate_percent': round((len(successful_results) / len(results)) * 100, 1) if results else 0,
            'average_processing_time_seconds': round(sum(r['processing_time'] for r in results) / len(results), 2) if results else 0
        }
    }
    
    # Output JSON results
    print("\n" + "=" * 50)
    print("📊 FINAL RESULTS (JSON)")
    print("=" * 50)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    # Save to file
    with open('5_urls_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: 5_urls_test_results.json")
    
    return summary

if __name__ == "__main__":
    asyncio.run(test_5_urls()) 