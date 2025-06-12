#!/usr/bin/env python3
"""
Test script to check Yell.com URL structure and find working URLs
"""

import asyncio
import sys
sys.path.insert(0, 'src')

from playwright.async_api import async_playwright

async def test_yell_urls():
    """Test different Yell.com URL formats to find what works"""
    
    # Test URLs to try
    test_urls = [
        "https://www.yell.com/s/retail-Brighton.html",
        "https://www.yell.com/s/shops-Brighton.html", 
        "https://www.yell.com/s/retail+shops-Brighton.html",
        "https://www.yell.com/ucs/UcsSearchAction.do?keywords=retail&location=Brighton",
        "https://www.yell.com/ucs/UcsSearchAction.do?keywords=shops&location=Brighton",
        "https://www.yell.com/s/retail%20shops-Brighton.html",
        "https://www.yell.com/",  # Just the homepage
    ]
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)  # Show browser
    
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={'width': 1280, 'height': 720}
    )
    
    page = await context.new_page()
    
    for url in test_urls:
        try:
            print(f"\n🔍 Testing: {url}")
            response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            print(f"   Status: {response.status}")
            
            if response.status == 200:
                # Check if we can find business listings
                await page.wait_for_timeout(2000)  # Wait 2 seconds for page to load
                
                # Try different selectors for business listings
                selectors_to_try = [
                    'div.businessCapsule--mainContent',
                    'div[data-business-id]',
                    '.business-listing',
                    '.searchResultItem',
                    '[data-testid="business-listing"]',
                    '.listing',
                    '.business'
                ]
                
                found_listings = False
                for selector in selectors_to_try:
                    listings = await page.query_selector_all(selector)
                    if listings:
                        print(f"   ✅ Found {len(listings)} listings with selector: {selector}")
                        found_listings = True
                        break
                
                if not found_listings:
                    print("   ⚠️  No business listings found")
                    # Get page title to see what we got
                    title = await page.title()
                    print(f"   Page title: {title}")
                
            elif response.status == 403:
                print("   ❌ 403 Forbidden - Blocked")
            elif response.status == 404:
                print("   ❌ 404 Not Found - URL doesn't exist")
            else:
                print(f"   ❌ Error: {response.status}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_yell_urls()) 