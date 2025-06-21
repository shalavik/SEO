#!/usr/bin/env python3
"""
Complete System Test - End-to-End Processing
Tests the full SEO lead generation pipeline on 5 URLs without Business Directory Enricher
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from seo_leads.models import UKCompany, ExecutiveContact
from seo_leads.scrapers.website_scraper import WebsiteScraper
from seo_leads.analyzers.company_analyzer import CompanyAnalyzer
from seo_leads.enrichers.google_search_enricher import GoogleSearchEnricher
from seo_leads.enrichers.linkedin_direct_enricher import LinkedInDirectEnricher
from seo_leads.enrichers.companies_house_enricher import CompaniesHouseEnricher
from seo_leads.enrichers.alternative_search_enricher import AlternativeSearchEnricher
from seo_leads.enrichers.phone_number_enricher import PhoneNumberEnricher
from seo_leads.ai.name_recognition_engine import NameRecognitionEngine
from seo_leads.ml.enrichment_optimizer import EnrichmentOptimizer
from seo_leads.cache.enrichment_cache import EnrichmentCache
from seo_leads.processors.email_enricher import EmailEnricher

class CompleteSystemTest:
    def __init__(self):
        self.test_urls = [
            "https://macplumbheat.co.uk/",
            "https://ltfplumbing.co.uk/subscription", 
            "http://www.ctmplumbing.co.uk/",
            "https://kingsheathplumbing.freeindex.co.uk/",
            "http://www.perry-plumbing.co.uk/"
        ]
        
        # Initialize all components
        self.website_scraper = WebsiteScraper()
        self.company_analyzer = CompanyAnalyzer()
        self.google_enricher = GoogleSearchEnricher()
        self.linkedin_enricher = LinkedInDirectEnricher()
        self.companies_house_enricher = CompaniesHouseEnricher()
        self.alternative_enricher = AlternativeSearchEnricher()
        self.phone_enricher = PhoneNumberEnricher()
        self.name_recognition = NameRecognitionEngine()
        self.ml_optimizer = EnrichmentOptimizer()
        self.cache = EnrichmentCache()
        self.email_enricher = EmailEnricher()
        
        self.results = []
        self.processing_stats = {
            'total_companies': 0,
            'total_executives': 0,
            'total_emails': 0,
            'total_phones': 0,
            'processing_time': 0,
            'success_rate': 0
        }

    async def process_single_url(self, url: str) -> Dict[str, Any]:
        """Process a single URL through the complete pipeline"""
        print(f"\n🔄 Processing: {url}")
        start_time = time.time()
        
        try:
            # Step 1: Scrape website
            print("  📄 Scraping website...")
            scraped_data = await self.website_scraper.scrape_website(url)
            if not scraped_data:
                return self._create_error_result(url, "Failed to scrape website")
            
            # Step 2: Analyze company
            print("  🏢 Analyzing company...")
            company = self.company_analyzer.analyze_company(scraped_data, url)
            if not company:
                return self._create_error_result(url, "Failed to analyze company")
            
            # Step 3: ML Optimization - determine best enrichment strategy
            print("  🤖 Optimizing enrichment strategy...")
            optimization_strategy = await self.ml_optimizer.optimize_enrichment_strategy(company)
            
            # Step 4: Google Search Enrichment
            print("  🔍 Google search enrichment...")
            google_results = await self.google_enricher.discover_executives(company)
            if google_results:
                company.executives.extend(google_results)
            
            # Step 5: LinkedIn Direct Enrichment
            print("  💼 LinkedIn direct enrichment...")
            linkedin_results = await self.linkedin_enricher.discover_executives(company)
            if linkedin_results:
                company.executives.extend(linkedin_results)
            
            # Step 6: Companies House Enrichment
            print("  🏛️ Companies House enrichment...")
            ch_results = await self.companies_house_enricher.discover_executives(company)
            if ch_results:
                company.executives.extend(ch_results)
            
            # Step 7: Alternative Search Enrichment
            print("  🔎 Alternative search enrichment...")
            alt_results = await self.alternative_enricher.discover_executives(company)
            if alt_results:
                company.executives.extend(alt_results)
            
            # Step 8: AI Name Recognition Enhancement
            print("  🧠 AI name recognition...")
            for executive in company.executives:
                enhanced_info = await self.name_recognition.enhance_executive_info(executive)
                if enhanced_info:
                    executive.confidence_score = enhanced_info.get('confidence_score', executive.confidence_score)
                    executive.seniority_tier = enhanced_info.get('seniority_tier', executive.seniority_tier)
            
            # Step 9: Email Enrichment
            print("  📧 Email enrichment...")
            for executive in company.executives:
                if not executive.email:
                    email_result = await self.email_enricher.enrich_executive_email(executive, company)
                    if email_result and email_result.get('email'):
                        executive.email = email_result['email']
                        executive.email_confidence = email_result.get('confidence', 0.0)
            
            # Step 10: Phone Number Enrichment
            print("  📞 Phone number enrichment...")
            phone_results = await self.phone_enricher.discover_phone_numbers(company)
            if phone_results:
                company.phone_numbers.extend(phone_results)
                # Associate phones with executives where possible
                for executive in company.executives:
                    if not executive.phone and phone_results:
                        executive.phone = phone_results[0]  # Assign first available phone
            
            # Step 11: Cache results
            print("  💾 Caching results...")
            cache_key = f"company_{company.domain}"
            await self.cache.set(cache_key, {
                'company': company.to_dict(),
                'processing_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            })
            
            processing_time = time.time() - start_time
            print(f"  ✅ Completed in {processing_time:.2f}s")
            
            return self._create_success_result(url, company, processing_time)
            
        except Exception as e:
            print(f"  ❌ Error processing {url}: {str(e)}")
            return self._create_error_result(url, str(e))

    def _create_success_result(self, url: str, company: Company, processing_time: float) -> Dict[str, Any]:
        """Create a successful result dictionary"""
        return {
            'url': url,
            'status': 'success',
            'processing_time': round(processing_time, 2),
            'company': {
                'name': company.name,
                'domain': company.domain,
                'industry': company.industry,
                'location': company.location,
                'description': company.description,
                'phone_numbers': company.phone_numbers,
                'social_media': company.social_media,
                'executives': [
                    {
                        'name': exec.name,
                        'title': exec.title,
                        'email': exec.email,
                        'phone': exec.phone,
                        'linkedin_url': exec.linkedin_url,
                        'confidence_score': exec.confidence_score,
                        'seniority_tier': exec.seniority_tier,
                        'email_confidence': getattr(exec, 'email_confidence', 0.0)
                    }
                    for exec in company.executives
                ]
            },
            'metrics': {
                'executives_found': len(company.executives),
                'emails_found': len([e for e in company.executives if e.email]),
                'phones_found': len(company.phone_numbers),
                'linkedin_profiles': len([e for e in company.executives if e.linkedin_url])
            }
        }

    def _create_error_result(self, url: str, error: str) -> Dict[str, Any]:
        """Create an error result dictionary"""
        return {
            'url': url,
            'status': 'error',
            'error': error,
            'processing_time': 0,
            'company': None,
            'metrics': {
                'executives_found': 0,
                'emails_found': 0,
                'phones_found': 0,
                'linkedin_profiles': 0
            }
        }

    def _calculate_final_stats(self):
        """Calculate final processing statistics"""
        successful_results = [r for r in self.results if r['status'] == 'success']
        
        self.processing_stats.update({
            'total_companies': len(self.results),
            'successful_companies': len(successful_results),
            'total_executives': sum(r['metrics']['executives_found'] for r in successful_results),
            'total_emails': sum(r['metrics']['emails_found'] for r in successful_results),
            'total_phones': sum(r['metrics']['phones_found'] for r in successful_results),
            'total_linkedin': sum(r['metrics']['linkedin_profiles'] for r in successful_results),
            'processing_time': sum(r['processing_time'] for r in self.results),
            'success_rate': (len(successful_results) / len(self.results)) * 100 if self.results else 0,
            'avg_processing_time': sum(r['processing_time'] for r in self.results) / len(self.results) if self.results else 0
        })

    async def run_complete_test(self) -> Dict[str, Any]:
        """Run the complete system test on all URLs"""
        print("🚀 Starting Complete System Test")
        print("=" * 50)
        
        overall_start = time.time()
        
        # Process each URL
        for url in self.test_urls:
            result = await self.process_single_url(url)
            self.results.append(result)
        
        # Calculate final statistics
        self._calculate_final_stats()
        
        overall_time = time.time() - overall_start
        
        # Create final output
        final_output = {
            'test_info': {
                'test_name': 'Complete System Test (No Business Directory)',
                'timestamp': datetime.now().isoformat(),
                'total_processing_time': round(overall_time, 2),
                'urls_tested': len(self.test_urls)
            },
            'processing_stats': self.processing_stats,
            'results': self.results,
            'summary': {
                'companies_processed': self.processing_stats['successful_companies'],
                'executives_discovered': self.processing_stats['total_executives'],
                'emails_discovered': self.processing_stats['total_emails'],
                'phone_numbers_discovered': self.processing_stats['total_phones'],
                'linkedin_profiles_found': self.processing_stats['total_linkedin'],
                'success_rate_percent': round(self.processing_stats['success_rate'], 1),
                'average_processing_time_seconds': round(self.processing_stats['avg_processing_time'], 2)
            }
        }
        
        return final_output

async def main():
    """Main function to run the complete system test"""
    test = CompleteSystemTest()
    
    try:
        results = await test.run_complete_test()
        
        # Output results as JSON
        print("\n" + "=" * 50)
        print("📊 FINAL RESULTS (JSON)")
        print("=" * 50)
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
        # Also save to file
        with open('complete_system_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: complete_system_test_results.json")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 