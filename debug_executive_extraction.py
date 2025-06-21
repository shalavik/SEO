#!/usr/bin/env python3
"""
DEBUG EXECUTIVE EXTRACTION - Phase 2 BUILD MODE
"""

import asyncio
import sys
import os
import re
from typing import List

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.seo_leads.scrapers.website_executive_scraper import WebsiteExecutiveScraper

class ExecutiveExtractionDebugger:
    def __init__(self):
        self.scraper = WebsiteExecutiveScraper()
        
    async def debug_company_extraction(self, company_name: str, company_url: str):
        print(f"\n🔍 DEBUGGING: {company_name}")
        print(f"URL: {company_url}")
        print("=" * 60)
        
        # Test name patterns on company name
        print(f"\n🎯 TESTING COMPANY NAME PATTERNS:")
        print(f"Company Name: '{company_name}'")
        
        # Test business name to person name extraction
        personified_patterns = [
            r'([A-Z][a-z]{2,15})\s+(?:The\s+)?(?:Plumber|Electrician|Builder)',
            r'([A-Z][a-z]{2,15})(?:\'s|\s)\s*(?:Plumbing|Heating|Gas)',
            r'([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
        ]
        
        for i, pattern in enumerate(personified_patterns, 1):
            matches = re.findall(pattern, company_name, re.IGNORECASE)
            print(f"   Pattern {i}: {pattern}")
            if matches:
                print(f"      ✅ Matches: {matches}")
                for match in matches:
                    clean_name = self.scraper._clean_extracted_name(match)
                    is_valid = self.scraper._is_valid_person_name(clean_name)
                    confidence = self.scraper._calculate_name_confidence(clean_name, "business_context")
                    print(f"         '{clean_name}' -> Valid: {is_valid}, Confidence: {confidence:.2f}")
            else:
                print(f"      ❌ No matches")
        
        # Run actual extraction
        print(f"\n⚡ RUNNING ACTUAL EXTRACTION:")
        executives = await self.scraper.discover_website_executives(company_url, company_name)
        print(f"   Found {len(executives)} executives")
        
        for exec in executives:
            print(f"   - {exec.first_name} {exec.last_name} ({exec.title})")

async def main():
    debugger = ExecutiveExtractionDebugger()
    
    test_companies = [
        {'name': 'GPJ Plumbing', 'url': 'http://gpj-plumbing.co.uk/'},
        {'name': 'Jack The Plumber', 'url': 'https://example.com'},  # Test case
    ]
    
    for company in test_companies:
        await debugger.debug_company_extraction(company['name'], company['url'])

if __name__ == "__main__":
    asyncio.run(main()) 