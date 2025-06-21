#!/usr/bin/env python3
"""
Simple Executive Discovery Test

A simplified test that focuses on executive discovery without complex model dependencies.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our modules
from src.seo_leads.scrapers.website_executive_scraper import WebsiteExecutiveScraper
from src.seo_leads.processors.executive_email_enricher import ExecutiveEmailEnricher

async def test_executive_discovery():
    """Simple test of executive discovery functionality"""
    
    # Test companies
    test_companies = [
        {
            "name": "GPJ Plumbing",
            "url": "http://gpj-plumbing.co.uk/",
            "sector": "plumbing"
        },
        {
            "name": "Emergency Plumber Services", 
            "url": "https://www.emergencyplumber.services/",
            "sector": "plumbing"
        },
        {
            "name": "247 Plumbing and Gas",
            "url": "https://247plumbingandgas.co.uk/",
            "sector": "plumbing"
        },
        {
            "name": "Hancox Gas and Plumbing",
            "url": "http://www.hancoxgasandplumbing.co.uk/",
            "sector": "plumbing"
        },
        {
            "name": "Metro Plumb Birmingham",
            "url": "https://metroplumb.co.uk/locations/metro-plumb-birmingham/",
            "sector": "plumbing"
        }
    ]
    
    # Initialize components
    website_scraper = WebsiteExecutiveScraper()
    email_enricher = ExecutiveEmailEnricher()
    
    results = []
    start_time = time.time()
    
    for i, company in enumerate(test_companies, 1):
        print(f"\n📍 Processing {i}/{len(test_companies)}: {company['name']}")
        print(f"🔄 Processing: {company['name']} - {company['url']}")
        
        company_start_time = time.time()
        
        try:
            # Step 1: Website Executive Discovery
            print("   👔 Discovering executives from website...")
            executives = await website_scraper.discover_website_executives(
                company['url'], company['name']
            )
            
            # Step 2: Email Enrichment
            if executives:
                print(f"   📧 Enriching {len(executives)} executives with email patterns...")
                domain = urlparse(company['url']).netloc.replace('www.', '')
                enriched_executives = await email_enricher.enrich_executive_emails(
                    executives, domain
                )
            else:
                enriched_executives = []
            
            # Format results
            executive_data = []
            for exec in enriched_executives:
                exec_dict = {
                    'first_name': exec.first_name,
                    'last_name': exec.last_name,
                    'full_name': exec.full_name,
                    'title': exec.title,
                    'seniority_tier': exec.seniority_tier,
                    'email': exec.email,
                    'email_confidence': exec.email_confidence,
                    'phone': exec.phone,
                    'linkedin_url': exec.linkedin_url,
                    'overall_confidence': exec.overall_confidence,
                    'discovery_sources': exec.discovery_sources,
                    'discovery_method': exec.discovery_method
                }
                executive_data.append(exec_dict)
            
            processing_time = time.time() - company_start_time
            
            company_result = {
                'company_name': company['name'],
                'website_url': company['url'],
                'sector': company['sector'],
                'executives_found': len(enriched_executives),
                'executives': executive_data,
                'processing_time_seconds': processing_time,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
            print(f"   ✅ Found {len(enriched_executives)} executives in {processing_time:.2f}s")
            
            # Print executive details
            if enriched_executives:
                for exec in enriched_executives:
                    print(f"      • {exec.full_name} - {exec.title} ({exec.seniority_tier})")
                    if exec.email:
                        print(f"        📧 {exec.email} (confidence: {exec.email_confidence:.2f})")
                    if exec.phone:
                        print(f"        📞 {exec.phone}")
                    if exec.linkedin_url:
                        print(f"        🔗 {exec.linkedin_url}")
            
            results.append(company_result)
            
        except Exception as e:
            logger.error(f"Error processing {company['name']}: {e}")
            company_result = {
                'company_name': company['name'],
                'website_url': company['url'],
                'sector': company['sector'],
                'executives_found': 0,
                'executives': [],
                'processing_time_seconds': time.time() - company_start_time,
                'timestamp': datetime.now().isoformat(),
                'status': 'failed',
                'error': str(e)
            }
            results.append(company_result)
    
    # Generate final results
    total_time = time.time() - start_time
    successful_companies = [r for r in results if r['status'] == 'success']
    total_executives = sum(r['executives_found'] for r in results)
    
    final_results = {
        "test_info": {
            "name": "Simple Executive Discovery Test",
            "timestamp": datetime.now().isoformat(),
            "total_companies": len(test_companies),
            "total_processing_time_seconds": total_time,
            "average_time_per_company": total_time / len(test_companies)
        },
        "summary": {
            "successful_processes": len(successful_companies),
            "failed_processes": len(results) - len(successful_companies),
            "total_executives_found": total_executives,
            "companies_with_executives": len([r for r in results if r['executives_found'] > 0]),
            "average_executives_per_company": total_executives / len(results) if results else 0
        },
        "results": results
    }
    
    # Save results
    timestamp = int(time.time())
    filename = f"simple_executive_discovery_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(final_results, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "="*60)
    print("🎉 SIMPLE EXECUTIVE DISCOVERY TEST COMPLETE")
    print("📊 Results Summary:")
    print(f"   ✅ Successful: {len(successful_companies)}")
    print(f"   ❌ Failed: {len(results) - len(successful_companies)}")
    print(f"   👔 Total Executives Found: {total_executives}")
    print(f"   🏢 Companies with Executives: {len([r for r in results if r['executives_found'] > 0])}")
    print(f"   📈 Average Executives per Company: {total_executives / len(results):.1f}")
    print(f"   ⏱️  Total Time: {total_time:.2f}s")
    print(f"   📄 Results saved to: {filename}")
    print("="*60)
    
    # Print JSON results
    print("\n🔍 FINAL JSON RESULTS:")
    print(json.dumps(final_results, indent=2, default=str))
    
    return final_results

if __name__ == "__main__":
    asyncio.run(test_executive_discovery()) 