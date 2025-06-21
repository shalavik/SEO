#!/usr/bin/env python3
"""
Content Extraction Debug Test

Test the actual HTML content extraction to understand why executives are not being found.
"""

import asyncio
import logging
import sys
from pathlib import Path
import re

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from seo_leads.scrapers.website_executive_scraper import WebsiteExecutiveScraper

async def test_content_extraction():
    """Test content extraction from Jack The Plumber about page"""
    
    scraper = WebsiteExecutiveScraper()
    
    # Test URL
    test_url = "https://jacktheplumber.co.uk/about"
    company_name = "Jack The Plumber"
    domain = "jacktheplumber.co.uk"
    
    logger.info(f"🔍 Testing content extraction from: {test_url}")
    
    try:
        # Test the main discovery method
        logger.info("🔄 Testing full discovery method...")
        executives = await scraper.discover_website_executives(test_url, company_name)
        logger.info(f"✅ Executives extracted: {len(executives)}")
        
        for exec in executives:
            logger.info(f"👤 Executive: {exec.first_name} {exec.last_name} - {exec.title}")
            
        # Test the page extraction method directly
        logger.info("📄 Testing direct page extraction...")
        page_executives = await scraper._extract_executives_from_page(test_url, company_name, domain)
        logger.info(f"📊 Page executives found: {len(page_executives)}")
        
        for exec in page_executives:
            logger.info(f"👤 Page Executive: {exec.first_name} {exec.last_name} - {exec.title}")
            
    except Exception as e:
        logger.error(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_content_extraction()) 