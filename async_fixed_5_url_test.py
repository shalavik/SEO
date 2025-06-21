import asyncio
import json
import time
import sys
import os
import random
from datetime import datetime
from typing import List, Dict, Any
import requests
from urllib.parse import urlparse
from playwright.async_api import async_playwright

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from seo_leads.models import ExecutiveContact
from seo_leads.scrapers.website_executive_scraper import WebsiteExecutiveScraper
from seo_leads.enrichers.google_search_enricher import EnhancedGoogleSearchEnricher
from seo_leads.enrichers.linkedin_direct_enricher import LinkedInDirectEnricher
from seo_leads.enrichers.companies_house_enricher import CompaniesHouseEnricher
from seo_leads.enrichers.alternative_search_enricher import AlternativeSearchEnricher
from seo_leads.enrichers.phone_number_enricher import PhoneNumberEnricher
from seo_leads.processors.executive_email_enricher import ExecutiveEmailEnricher

class AsyncRateLimitedEnricher:
    """Async wrapper to handle rate limiting gracefully"""
    
    def __init__(self, enricher, min_delay=3, max_delay=8):
        self.enricher = enricher
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_call = 0
    
    async def safe_call(self, method_name, *args, **kwargs):
        """Make a rate-limited async call to the enricher"""
        # Add random delay to avoid rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_call
        
        if time_since_last < self.min_delay:
            sleep_time = random.uniform(self.min_delay, self.max_delay)
            print(f"    ⏳ Rate limiting: waiting {sleep_time:.1f}s...")
            await asyncio.sleep(sleep_time)
        
        try:
            method = getattr(self.enricher, method_name)
            result = await method(*args, **kwargs)
            self.last_call = time.time()
            return result if result else []
        except Exception as e:
            print(f"    ⚠️ {method_name} failed: {str(e)[:100]}...")
            self.last_call = time.time()
            return []

def make_json_serializable(obj):
    """Convert objects to JSON-serializable format"""
    if hasattr(obj, '__dict__'):
        result = {}
        for key, value in obj.__dict__.items():
            if key.startswith('_'):
                continue
            result[key] = make_json_serializable(value)
        return result
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)

async def extract_company_info_robust(url: str) -> Dict[str, Any]:
    """Robust company information extraction with fallbacks"""
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state('domcontentloaded')
                
                # Extract company name from title or h1
                company_name = ""
                try:
                    title = await page.title()
                    if title:
                        company_name = title.split('|')[0].split('-')[0].strip()
                except:
                    pass
                
                if not company_name:
                    try:
                        h1_element = await page.query_selector('h1')
                        if h1_element:
                            company_name = await h1_element.inner_text()
                    except:
                        pass
                
                # Extract emails
                emails = []
                try:
                    content = await page.content()
                    import re
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    found_emails = re.findall(email_pattern, content)
                    # Filter out common non-business emails
                    emails = [email for email in found_emails 
                             if not any(skip in email.lower() for skip in ['example', 'test', 'noreply', 'no-reply'])][:3]
                except:
                    pass
                
                # Extract phone numbers
                phone_numbers = []
                try:
                    content = await page.content()
                    import re
                    # UK phone number patterns
                    phone_patterns = [
                        r'\b0\d{2,4}\s?\d{3}\s?\d{3,4}\b',  # Standard UK format
                        r'\b\+44\s?\d{2,4}\s?\d{3}\s?\d{3,4}\b',  # International format
                        r'\b07\d{3}\s?\d{6}\b',  # Mobile format
                        r'\b0800\s?\d{3}\s?\d{3,4}\b'  # Freephone
                    ]
                    for pattern in phone_patterns:
                        found_phones = re.findall(pattern, content)
                        phone_numbers.extend(found_phones)
                    phone_numbers = list(set(phone_numbers))[:5]  # Remove duplicates, limit to 5
                except:
                    pass
                
                domain = urlparse(url).netloc
                if not company_name:
                    company_name = f"Company from {domain}"
                
                return {
                    "name": company_name,
                    "domain": domain,
                    "description": f"Business website: {domain}",
                    "emails": emails,
                    "phone_numbers": phone_numbers
                }
                
            finally:
                await browser.close()
                
    except Exception as e:
        domain = urlparse(url).netloc
        print(f"    ⚠️ Company extraction failed: {str(e)[:100]}...")
        return {
            "name": f"Company from {domain}",
            "domain": domain,
            "description": "",
            "emails": [],
            "phone_numbers": []
        }

async def discover_executives_robust(company_info: Dict[str, Any], enrichers: Dict[str, Any]) -> List[ExecutiveContact]:
    """Robust executive discovery with proper error handling"""
    all_executives = []
    company_name = company_info["name"]
    domain = company_info["domain"]
    
    # Website executive scraping
    try:
        print("    👥 Website executive scraping...")
        website_executives = await enrichers['website_scraper'].safe_call(
            'discover_website_executives', f"https://{domain}", company_name
        )
        all_executives.extend(website_executives)
        print(f"    ✓ Found {len(website_executives)} website executives")
    except Exception as e:
        print(f"    ⚠️ Website scraping failed: {str(e)[:100]}...")
    
    # Google search with rate limiting
    try:
        print("    🔍 Google search enrichment...")
        google_executives = await enrichers['google_enricher'].safe_call(
            'discover_executives', company_name, domain
        )
        all_executives.extend(google_executives)
        print(f"    ✓ Found {len(google_executives)} Google executives")
    except Exception as e:
        print(f"    ⚠️ Google search failed: {str(e)[:100]}...")
    
    # LinkedIn with rate limiting
    try:
        print("    💼 LinkedIn enrichment...")
        linkedin_executives = await enrichers['linkedin_enricher'].safe_call(
            'discover_executives', company_name, domain
        )
        all_executives.extend(linkedin_executives)
        print(f"    ✓ Found {len(linkedin_executives)} LinkedIn executives")
    except Exception as e:
        print(f"    ⚠️ LinkedIn search failed: {str(e)[:100]}...")
    
    # Companies House with better error handling
    try:
        print("    🏛️ Companies House enrichment...")
        ch_executives = await enrichers['companies_house_enricher'].safe_call(
            'discover_executives', company_name, domain
        )
        all_executives.extend(ch_executives)
        print(f"    ✓ Found {len(ch_executives)} Companies House executives")
    except Exception as e:
        print(f"    ⚠️ Companies House failed: {str(e)[:100]}...")
    
    # Alternative search with rate limiting
    try:
        print("    🔎 Alternative search enrichment...")
        alt_executives = await enrichers['alternative_enricher'].safe_call(
            'discover_executives', company_name, domain
        )
        all_executives.extend(alt_executives)
        print(f"    ✓ Found {len(alt_executives)} alternative search executives")
    except Exception as e:
        print(f"    ⚠️ Alternative search failed: {str(e)[:100]}...")
    
    return all_executives

async def enrich_phone_numbers_robust(company_info: Dict[str, Any], enrichers: Dict[str, Any]) -> List[str]:
    """Robust phone number enrichment"""
    phone_numbers = list(company_info.get("phone_numbers", []))
    
    try:
        print("    📞 Phone number enrichment...")
        phone_results = await enrichers['phone_enricher'].safe_call(
            'discover_phone_numbers', company_info["name"], company_info["domain"]
        )
        
        # Extract phone numbers from results
        if hasattr(phone_results, 'phone_numbers'):
            phone_numbers.extend(phone_results.phone_numbers)
        elif isinstance(phone_results, list):
            phone_numbers.extend(phone_results)
        
        # Remove duplicates while preserving order
        unique_phones = []
        seen = set()
        for phone in phone_numbers:
            phone_str = str(phone)
            if phone_str not in seen:
                unique_phones.append(phone_str)
                seen.add(phone_str)
        
        print(f"    ✓ Total phone numbers: {len(unique_phones)}")
        return unique_phones
        
    except Exception as e:
        print(f"    ⚠️ Phone enrichment failed: {str(e)[:100]}...")
        return [str(p) for p in phone_numbers]

async def process_url_fixed(url: str, enrichers: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single URL with comprehensive error handling and rate limiting"""
    print(f"🔄 Processing: {url}")
    start_time = time.time()
    
    try:
        # Step 1: Extract company information
        print("  📄 Extracting company information...")
        company_info = await extract_company_info_robust(url)
        
        # Step 2: Discover executives with rate limiting
        print("  👥 Discovering executives...")
        executives = await discover_executives_robust(company_info, enrichers)
        
        # Step 3: Enrich phone numbers
        print("  📞 Enriching phone numbers...")
        phone_numbers = await enrich_phone_numbers_robust(company_info, enrichers)
        company_info["phone_numbers"] = phone_numbers
        
        # Step 4: Email enrichment for executives
        enriched_executives = []
        if executives:
            try:
                print("  📧 Enriching executive emails...")
                enriched_executives = enrichers['email_enricher'].enrich_executives_emails(executives)
                print(f"    ✓ Enriched {len(enriched_executives)} executives")
            except Exception as e:
                print(f"    ⚠️ Email enrichment failed: {str(e)[:100]}...")
                enriched_executives = executives
        
        processing_time = time.time() - start_time
        
        result = {
            "url": url,
            "status": "success",
            "processing_time": round(processing_time, 2),
            "company": {
                "name": company_info["name"],
                "domain": company_info["domain"],
                "description": company_info["description"],
                "emails": company_info["emails"],
                "phone_numbers": company_info["phone_numbers"]
            },
            "executives": [make_json_serializable(exec) for exec in enriched_executives],
            "discovery_stats": {
                "total_executives": len(enriched_executives),
                "total_emails": len(company_info["emails"]),
                "total_phones": len(company_info["phone_numbers"])
            }
        }
        
        print(f"  ✅ Completed in {processing_time:.2f}s")
        return result
        
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"  ❌ Failed in {processing_time:.2f}s: {str(e)}")
        return {
            "url": url,
            "status": "failed",
            "processing_time": round(processing_time, 2),
            "error": str(e),
            "company": None,
            "executives": [],
            "discovery_stats": {
                "total_executives": 0,
                "total_emails": 0,
                "total_phones": 0
            }
        }

async def main():
    """Main async test function with fixes"""
    print("🚀 Starting ASYNC FIXED Complete SEO Lead Generation System Test")
    print("=" * 70)
    
    # Test URLs
    urls = [
        "https://macplumbheat.co.uk/",
        "https://ltfplumbing.co.uk/subscription",
        "http://www.ctmplumbing.co.uk/",
        "https://kingsheathplumbing.freeindex.co.uk/",
        "http://www.perry-plumbing.co.uk/"
    ]
    
    # Initialize enrichers with rate limiting wrappers
    print("🔧 Initializing enrichers with rate limiting...")
    enrichers = {
        'website_scraper': AsyncRateLimitedEnricher(WebsiteExecutiveScraper(), 5, 10),
        'google_enricher': AsyncRateLimitedEnricher(EnhancedGoogleSearchEnricher(), 8, 15),
        'linkedin_enricher': AsyncRateLimitedEnricher(LinkedInDirectEnricher(), 6, 12),
        'companies_house_enricher': AsyncRateLimitedEnricher(CompaniesHouseEnricher(), 4, 8),
        'alternative_enricher': AsyncRateLimitedEnricher(AlternativeSearchEnricher(), 10, 20),
        'phone_enricher': AsyncRateLimitedEnricher(PhoneNumberEnricher(), 3, 6),
        'email_enricher': ExecutiveEmailEnricher()
    }
    
    # Process all URLs with delays between them
    results = []
    total_start_time = time.time()
    
    for i, url in enumerate(urls, 1):
        print(f"\n📍 URL {i}/{len(urls)}")
        result = await process_url_fixed(url, enrichers)
        results.append(result)
        
        # Add delay between URLs to avoid rate limiting
        if i < len(urls):
            delay = random.uniform(15, 30)
            print(f"⏳ Waiting {delay:.1f}s before next URL...")
            await asyncio.sleep(delay)
    
    total_processing_time = time.time() - total_start_time
    
    # Calculate summary statistics
    successful_results = [r for r in results if r['status'] == 'success']
    failed_results = [r for r in results if r['status'] == 'failed']
    
    total_executives = sum(r['discovery_stats']['total_executives'] for r in successful_results)
    total_emails = sum(r['discovery_stats']['total_emails'] for r in successful_results)
    total_phones = sum(r['discovery_stats']['total_phones'] for r in successful_results)
    
    # Create final results
    final_results = {
        "test_info": {
            "timestamp": datetime.now().isoformat(),
            "version": "ASYNC_FIXED_VERSION_1.0",
            "total_urls": len(urls),
            "successful_urls": len(successful_results),
            "failed_urls": len(failed_results),
            "total_processing_time": round(total_processing_time, 2),
            "average_processing_time": round(total_processing_time / len(urls), 2) if urls else 0
        },
        "summary_stats": {
            "companies_processed": len(successful_results),
            "executives_discovered": total_executives,
            "emails_discovered": total_emails,
            "phone_numbers_discovered": total_phones,
            "success_rate": f"{(len(successful_results) / len(urls) * 100):.1f}%" if urls else "0%"
        },
        "improvements_made": [
            "Converted to async/await architecture matching system design",
            "Added comprehensive rate limiting with random delays (3-20s between calls)",
            "Implemented robust error handling for all enrichers",
            "Added fallback mechanisms for failed API calls",
            "Improved phone number and email extraction with regex patterns",
            "Added inter-URL delays (15-30s) to prevent rate limiting",
            "Enhanced JSON serialization for all object types",
            "Used Playwright for robust website content extraction",
            "Added proper async context management for browser operations"
        ],
        "url_results": results
    }
    
    print("\n" + "=" * 70)
    print("📊 ASYNC FIXED TEST RESULTS (JSON)")
    print("=" * 70)
    
    try:
        json_output = json.dumps(final_results, indent=2, ensure_ascii=False)
        print(json_output)
        
        # Save to file
        filename = f"async_fixed_5_url_test_results_{int(time.time())}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(json_output)
        print(f"\n💾 Results saved to: {filename}")
        
        # Print summary
        print(f"\n📊 SUMMARY:")
        print(f"✅ Success rate: {final_results['summary_stats']['success_rate']}")
        print(f"👥 Executives found: {total_executives}")
        print(f"📧 Emails found: {total_emails}")
        print(f"📞 Phone numbers found: {total_phones}")
        print(f"⏱️  Total time: {final_results['test_info']['total_processing_time']:.1f}s")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 