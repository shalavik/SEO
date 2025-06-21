#!/usr/bin/env python3
import asyncio
import sys
import os
import re
sys.path.append('.')
from src.seo_leads.scrapers.website_executive_scraper import WebsiteExecutiveScraper

async def test_patterns():
    scraper = WebsiteExecutiveScraper()
    
    # Test company names
    test_names = ['GPJ Plumbing', 'Jack The Plumber', 'Emergency Plumber Services', 'Smith Heating Ltd']
    
    for name in test_names:
        print(f'Testing: {name}')
        
        # Test pattern matching
        patterns = [
            r'([A-Z][a-z]{2,15})\s+(?:The\s+)?(?:Plumber|Electrician|Builder)',
            r'([A-Z][a-z]{2,15})(?:\'s|\s)\s*(?:Plumbing|Heating|Gas)',
            r'([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, name, re.IGNORECASE)
            if matches:
                print(f'  Pattern matched: {matches}')
                for match in matches:
                    clean_name = scraper._clean_extracted_name(match)
                    is_valid = scraper._is_valid_person_name(clean_name)
                    confidence = scraper._calculate_name_confidence(clean_name, 'business_context')
                    print(f'    {clean_name} -> Valid: {is_valid}, Confidence: {confidence:.2f}')
        print()

if __name__ == "__main__":
    asyncio.run(test_patterns()) 