#!/usr/bin/env python3
"""
Website Scraper Debug Test

Direct testing of the website scraper to understand why it's not finding executives.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from seo_leads.scrapers.website_executive_scraper import WebsiteExecutiveScraper

# Test with one company first
TEST_COMPANY = {
    "name": "Jack The Plumber",
    "website": "https://jacktheplumber.co.uk",
    "expected": "owner, founder"
}

async def test_website_scraper():
    """Test the website scraper directly"""
    scraper = WebsiteExecutiveScraper()
    
    logger.info(f"🏢 Testing: {TEST_COMPANY['name']}")
    logger.info(f"🌐 Website: {TEST_COMPANY['website']}")
    logger.info(f"📋 Expected: {TEST_COMPANY['expected']}")
    
    try:
        # Test the scraper
        executives = await scraper.discover_website_executives(
            TEST_COMPANY['website'], 
            TEST_COMPANY['name']
        )
        
        logger.info(f"✅ Found {len(executives)} executives")
        
        for i, executive in enumerate(executives, 1):
            logger.info(f"  {i}. {executive.full_name} - {executive.title}")
            logger.info(f"     Email: {executive.email or 'None'}")
            logger.info(f"     Sources: {executive.discovery_sources}")
            logger.info(f"     Confidence: {executive.overall_confidence:.2f}")
        
        if not executives:
            logger.warning("❌ No executives found - testing page extraction manually...")
            
            # Test individual page extraction
            logger.info("🔍 Testing individual page extraction...")
            
            # Try to find executive pages
            executive_pages = await scraper._find_executive_pages(TEST_COMPANY['website'])
            logger.info(f"Found {len(executive_pages)} potential executive pages:")
            
            for page in executive_pages:
                logger.info(f"  - {page}")
                
                # Try to extract from each page
                try:
                    page_executives = await scraper._extract_executives_from_page(
                        page, TEST_COMPANY['name'], "jacktheplumber.co.uk"
                    )
                    logger.info(f"    Found {len(page_executives)} executives from this page")
                    
                    for exec_contact in page_executives:
                        logger.info(f"      - {exec_contact.full_name}: {exec_contact.title}")
                        
                except Exception as e:
                    logger.error(f"    Error extracting from {page}: {e}")
        
    except Exception as e:
        logger.error(f"❌ Website scraper failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_website_scraper()) 