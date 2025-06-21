#!/usr/bin/env python3
"""
Simple test of 5 URLs through the system components
"""

import asyncio
import json
import time
from datetime import datetime
import sys
import os
import aiohttp

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from seo_leads.scrapers.website_executive_scraper import WebsiteExecutiveScraper
from seo_leads.enrichers.google_search_enricher import EnhancedGoogleSearchEnricher
from seo_leads.enrichers.linkedin_direct_enricher import LinkedInDirectEnricher
from seo_leads.enrichers.companies_house_enricher import CompaniesHouseEnricher
from seo_leads.enrichers.alternative_search_enricher import AlternativeSearchEnricher
from seo_leads.enrichers.phone_number_enricher import PhoneNumberEnricher
from seo_leads.processors.executive_email_enricher import ExecutiveEmailEnricher
from seo_leads.analyzers.seo_analyzer import SEOAnalyzer

class Simple5URLTest:
    def __init__(self):
        self.urls = [
            "https://macplumbheat.co.uk/",
            "https://ltfplumbing.co.uk/subscription", 
            "http://www.ctmplumbing.co.uk/",
            "https://kingsheathplumbing.freeindex.co.uk/",
            "http://www.perry-plumbing.co.uk/"
        ]
        
        # Initialize components
        self.website_scraper = WebsiteExecutiveScraper()
        self.google_enricher = EnhancedGoogleSearchEnricher()
        self.linkedin_enricher = LinkedInDirectEnricher()
        self.companies_house_enricher = CompaniesHouseEnricher()
        self.alternative_enricher = AlternativeSearchEnricher()
        self.phone_enricher = PhoneNumberEnricher()
        self.email_enricher = ExecutiveEmailEnricher()
        self.seo_analyzer = SEOAnalyzer()

    async def extract_basic_company_info(self, url: str) -> dict:
        """Extract basic company information from URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Extract domain
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc.replace('www.', '')
                        
                        # Basic extraction from HTML
                        import re
                        
                        # Try to extract company name from title or h1
                        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
                        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html, re.IGNORECASE)
                        
                        company_name = "Unknown Company"
                        if title_match:
                            company_name = title_match.group(1).strip()
                        elif h1_match:
                            company_name = h1_match.group(1).strip()
                        
                        # Extract phone numbers
                        phone_pattern = r'(\+44\s?|0)(\d{2,4}[\s-]?\d{3,4}[\s-]?\d{3,4})'
                        phones = re.findall(phone_pattern, html)
                        phone_numbers = [''.join(phone) for phone in phones[:3]]  # Limit to 3
                        
                        # Extract email addresses
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        emails = re.findall(email_pattern, html)
                        
                        return {
                            'name': company_name,
                            'domain': domain,
                            'url': url,
                            'phone_numbers': phone_numbers,
                            'emails': emails[:3],  # Limit to 3
                            'industry': 'Plumbing & Heating',  # All test URLs are plumbing companies
                            'location': {'country': 'UK'},
                            'description': f'Company website: {url}',
                            'executives': []
                        }
                    else:
                        return None
        except Exception as e:
            print(f"Error extracting basic info from {url}: {e}")
            return None

    async def process_single_url(self, url: str) -> dict:
        """Process a single URL through all enrichers"""
        print(f"\n🔄 Processing: {url}")
        start_time = time.time()
        
        try:
            # Step 1: Extract basic company info
            print("  📄 Extracting basic company info...")
            company = await self.extract_basic_company_info(url)
            if not company:
                return self._create_error_result(url, "Failed to extract basic company info")
            
            # Step 2: Website Executive Scraping
            print("  👥 Scraping website for executives...")
            try:
                website_executives = await self.website_scraper.scrape_executives(url)
                if website_executives:
                    company['executives'].extend(website_executives)
                    print(f"    Found {len(website_executives)} executives from website")
            except Exception as e:
                print(f"    ⚠️ Website scraping failed: {e}")
            
            # Step 3: Google Search Enrichment
            print("  🔍 Google search enrichment...")
            try:
                google_results = await self.google_enricher.discover_executives(company)
                if google_results:
                    company['executives'].extend(google_results)
                    print(f"    Found {len(google_results)} executives from Google")
            except Exception as e:
                print(f"    ⚠️ Google enrichment failed: {e}")
            
            # Step 4: LinkedIn Direct Enrichment
            print("  💼 LinkedIn direct enrichment...")
            try:
                linkedin_results = await self.linkedin_enricher.discover_executives(company)
                if linkedin_results:
                    company['executives'].extend(linkedin_results)
                    print(f"    Found {len(linkedin_results)} executives from LinkedIn")
            except Exception as e:
                print(f"    ⚠️ LinkedIn enrichment failed: {e}")
            
            # Step 5: Companies House Enrichment
            print("  🏛️ Companies House enrichment...")
            try:
                ch_results = await self.companies_house_enricher.discover_executives(company)
                if ch_results:
                    company['executives'].extend(ch_results)
                    print(f"    Found {len(ch_results)} executives from Companies House")
            except Exception as e:
                print(f"    ⚠️ Companies House enrichment failed: {e}")
            
            # Step 6: Alternative Search Enrichment
            print("  🔎 Alternative search enrichment...")
            try:
                alt_results = await self.alternative_enricher.discover_executives(company)
                if alt_results:
                    company['executives'].extend(alt_results)
                    print(f"    Found {len(alt_results)} executives from alternative search")
            except Exception as e:
                print(f"    ⚠️ Alternative search enrichment failed: {e}")
            
            # Step 7: Phone Number Enrichment
            print("  📞 Phone number enrichment...")
            try:
                phone_results = await self.phone_enricher.discover_phone_numbers(company)
                if phone_results:
                    company['phone_numbers'].extend(phone_results)
                    print(f"    Found {len(phone_results)} additional phone numbers")
            except Exception as e:
                print(f"    ⚠️ Phone enrichment failed: {e}")
            
            # Step 8: Email Enrichment for executives
            print("  📧 Email enrichment for executives...")
            try:
                for executive in company['executives']:
                    if not executive.get('email'):
                        email_result = await self.email_enricher.enrich_executive_email(executive, company)
                        if email_result and email_result.get('email'):
                            executive['email'] = email_result['email']
                            executive['email_confidence'] = email_result.get('confidence', 0.0)
                print(f"    Enriched emails for executives")
            except Exception as e:
                print(f"    ⚠️ Email enrichment failed: {e}")
            
            # Step 9: SEO Analysis
            print(f"   🔍 Running SEO analysis...")
            seo_result = await self.seo_analyzer.analyze_website_seo(
                company_id=company_id,
                website_url=url,
                company_sector="Plumbing Services"
            )
            
            processing_time = time.time() - start_time
            print(f"  ✅ Completed in {processing_time:.2f}s")
            
            return self._create_success_result(url, company, processing_time)
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"  ❌ Error processing {url}: {str(e)}")
            return self._create_error_result(url, str(e), processing_time)

    def _create_success_result(self, url: str, company: dict, processing_time: float) -> dict:
        """Create a successful result dictionary"""
        return {
            'url': url,
            'status': 'success',
            'processing_time': round(processing_time, 2),
            'company': {
                'name': company.get('name', 'Unknown'),
                'domain': company.get('domain', ''),
                'industry': company.get('industry', 'Unknown'),
                'location': company.get('location', {}),
                'description': company.get('description', ''),
                'phone_numbers': company.get('phone_numbers', []),
                'emails': company.get('emails', []),
                'executives': [
                    {
                        'name': exec.get('name', exec.get('full_name', 'Unknown')),
                        'title': exec.get('title', 'Unknown'),
                        'email': exec.get('email'),
                        'phone': exec.get('phone'),
                        'linkedin_url': exec.get('linkedin_url'),
                        'confidence_score': exec.get('confidence_score', exec.get('overall_confidence', 0.0)),
                        'seniority_tier': exec.get('seniority_tier', 'unknown'),
                        'email_confidence': exec.get('email_confidence', 0.0)
                    }
                    for exec in company.get('executives', [])
                ]
            },
            'metrics': {
                'executives_found': len(company.get('executives', [])),
                'emails_found': len([e for e in company.get('executives', []) if e.get('email')]) + len(company.get('emails', [])),
                'phones_found': len(company.get('phone_numbers', [])),
                'linkedin_profiles': len([e for e in company.get('executives', []) if e.get('linkedin_url')])
            }
        }

    def _create_error_result(self, url: str, error: str, processing_time: float = 0) -> dict:
        """Create an error result dictionary"""
        return {
            'url': url,
            'status': 'error',
            'error': error,
            'processing_time': round(processing_time, 2),
            'company': None,
            'metrics': {
                'executives_found': 0,
                'emails_found': 0,
                'phones_found': 0,
                'linkedin_profiles': 0
            }
        }

    async def run_test(self) -> dict:
        """Run the complete test on all 5 URLs"""
        print("🚀 Starting Simple 5 URL Test")
        print("=" * 50)
        
        overall_start = time.time()
        results = []
        
        # Process each URL
        for i, url in enumerate(self.urls, 1):
            print(f"\n📍 URL {i}/5")
            result = await self.process_single_url(url)
            results.append(result)
        
        total_time = time.time() - overall_start
        successful_results = [r for r in results if r['status'] == 'success']
        
        # Calculate summary statistics
        final_output = {
            'test_info': {
                'test_name': 'Simple 5 URL Test (No Business Directory)',
                'timestamp': datetime.now().isoformat(),
                'total_processing_time': round(total_time, 2),
                'urls_tested': len(self.urls)
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
        
        return final_output

async def main():
    """Main function to run the test"""
    test = Simple5URLTest()
    
    try:
        results = await test.run_test()
        
        # Output results as JSON
        print("\n" + "=" * 50)
        print("📊 FINAL RESULTS (JSON)")
        print("=" * 50)
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
        # Save to file
        with open('simple_5_url_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: simple_5_url_test_results.json")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 