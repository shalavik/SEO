#!/usr/bin/env python3
"""
Test script to debug Yelp UK structure and selectors
"""

import asyncio
import sys
sys.path.insert(0, 'src')

from playwright.async_api import async_playwright

async def test_yelp_uk():
    """Test Yelp UK to see what structure we get"""
    
    url = "https://www.yelp.co.uk/search?find_desc=retail&find_loc=Brighton"
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)  # Show browser
    
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={'width': 1280, 'height': 720}
    )
    
    page = await context.new_page()
    
    try:
        print(f"🔍 Testing: {url}")
        
        # Visit homepage first
        print("Visiting homepage...")
        await page.goto("https://www.yelp.co.uk", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        # Now visit search page
        print("Visiting search page...")
        response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        print(f"Status: {response.status}")
        
        if response.status == 200:
            await page.wait_for_timeout(3000)  # Wait for page to fully load
            
            # Get page title
            title = await page.title()
            print(f"Page title: {title}")
            
            # Try to find any business-related elements
            selectors_to_try = [
                '[data-testid="serp-ia-card"]',
                '.businessName', 
                '.search-result',
                '.biz-listing-large',
                '.result',
                '.business',
                '.listing',
                '[data-testid]',  # Any element with data-testid
                '.biz-name',
                'h3',
                'h4',
                'a[href*="/biz/"]'  # Yelp business links
            ]
            
            found_any = False
            for selector in selectors_to_try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"✅ Found {len(elements)} elements with selector: {selector}")
                    found_any = True
                    
                    # Show first few elements
                    for i, elem in enumerate(elements[:3]):
                        try:
                            text = await elem.text_content()
                            if text and text.strip():
                                print(f"   Element {i+1}: {text.strip()[:100]}...")
                        except:
                            pass
                    break
            
            if not found_any:
                print("❌ No business listings found with any selector")
                
                # Let's see what's actually on the page
                print("\n📄 Page content sample:")
                content = await page.content()
                # Look for common patterns
                if "business" in content.lower():
                    print("✅ Page contains 'business' text")
                if "retail" in content.lower():
                    print("✅ Page contains 'retail' text")
                if "brighton" in content.lower():
                    print("✅ Page contains 'brighton' text")
                    
                # Show a sample of the HTML
                print(f"HTML length: {len(content)} characters")
                
                # Look for any links that might be businesses
                links = await page.query_selector_all('a')
                business_links = []
                for link in links[:20]:  # Check first 20 links
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    if href and '/biz/' in href:
                        business_links.append((text, href))
                
                if business_links:
                    print(f"\n🔗 Found {len(business_links)} business links:")
                    for text, href in business_links[:5]:
                        print(f"   {text}: {href}")
                else:
                    print("❌ No business links found")
        
        else:
            print(f"❌ Error: {response.status}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_yelp_uk()) 