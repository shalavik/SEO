#!/usr/bin/env python3
"""
Simple Enhanced Executive Discovery Test

Tests only the website scraper component to validate the enhanced discovery system.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from seo_leads.scrapers.website_executive_scraper import WebsiteExecutiveScraper

async def test_simple_website_discovery():
    """Test the website scraper directly"""
    
    logger.info("🚀 Starting Simple Website Executive Discovery Test")
    logger.info("=" * 60)
    
    # Initialize website scraper
    scraper = WebsiteExecutiveScraper()
    
    # Test company
    company_name = "Jack The Plumber"
    website_url = "https://jacktheplumber.co.uk"
    
    logger.info(f"🔍 Testing: {company_name}")
    logger.info(f"   Website: {website_url}")
    
    try:
        # Discover executives
        executives = await scraper.discover_website_executives(website_url, company_name)
        
        logger.info(f"✅ Discovery Complete:")
        logger.info(f"   📊 Executives Found: {len(executives)}")
        
        if executives:
            logger.info(f"   👥 Executives:")
            for i, exec in enumerate(executives, 1):
                logger.info(f"      {i}. {exec.full_name} - {exec.title}")
                logger.info(f"         Tier: {exec.seniority_tier}")
                logger.info(f"         Confidence: {exec.overall_confidence:.1%}")
                if exec.email:
                    logger.info(f"         Email: {exec.email}")
                if exec.linkedin_url:
                    logger.info(f"         LinkedIn: {exec.linkedin_url}")
        else:
            logger.warning("   ⚠️  No executives found")
        
        return len(executives) > 0
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_website_discovery())
    
    if success:
        print("\n🎉 Website Discovery Test Passed!")
    else:
        print("\n❌ Website Discovery Test Failed!")
        sys.exit(1) 