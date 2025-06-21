import asyncio
import json
import time
import sys
import os
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import urlparse

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from seo_leads.models import UKCompany, ExecutiveContact
from seo_leads.scrapers.website_executive_scraper import WebsiteExecutiveScraper
from seo_leads.enrichers.google_search_enricher import EnhancedGoogleSearchEnricher
from seo_leads.enrichers.linkedin_direct_enricher import LinkedInDirectEnricher
from seo_leads.enrichers.companies_house_enricher import CompaniesHouseEnricher
from seo_leads.enrichers.alternative_search_enricher import AlternativeSearchEnricher
from seo_leads.enrichers.phone_number_enricher import PhoneNumberEnricher
from seo_leads.processors.executive_email_enricher import ExecutiveEmailEnricher
from seo_leads.processors.contact_extractor import ContactExtractor

# Import our fixed executive discovery
from fixed_executive_discovery import FixedExecutiveDiscovery

def make_json_serializable(obj):
    """Convert objects to JSON-serializable format"""
    if hasattr(obj, '__dict__'):
        return {k: make_json_serializable(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif hasattr(obj, 'isoformat'):  # datetime objects
        return obj.isoformat()
    else:
        return obj

async def comprehensive_seo_lead_test():
    """Comprehensive test of the complete SEO lead generation system"""
    
    print("🚀 COMPREHENSIVE SEO LEAD GENERATION SYSTEM TEST")
    print("=" * 70)
    print("🎯 Testing complete pipeline with FIXED executive discovery")
    print("📊 Processing 5 URLs with full enrichment")
    print("=" * 70)
    
    # Test URLs
    test_urls = [
        "https://macplumbheat.co.uk/",
        "https://ltfplumbing.co.uk/subscription",
        "http://www.ctmplumbing.co.uk/",
        "https://kingsheathplumbing.freeindex.co.uk/",
        "http://www.perry-plumbing.co.uk/"
    ]
    
    # Initialize components
    contact_extractor = ContactExtractor()
    executive_discovery = FixedExecutiveDiscovery()
    email_enricher = ExecutiveEmailEnricher()
    phone_enricher = PhoneNumberEnricher()
    
    # Results storage
    all_results = []
    total_start_time = time.time()
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{'='*70}")
        print(f"🏢 Processing URL {i}/5: {url}")
        print(f"{'='*70}")
        
        url_start_time = time.time()
        
        try:
            # Step 1: Extract basic company information
            print("\n📋 Step 1: Company Information Extraction")
            company_info = await contact_extractor.extract_company_info(url)
            
            company_name = company_info.get('company_name', 'Unknown Company')
            domain = urlparse(url).netloc.replace('www.', '')
            
            print(f"   ✅ Company: {company_name}")
            print(f"   🌐 Domain: {domain}")
            
            # Step 2: Extract contact information
            print("\n📞 Step 2: Contact Information Extraction")
            contact_info = await contact_extractor.extract_contact_info(url)
            
            emails = contact_info.get('emails', [])
            phones = contact_info.get('phones', [])
            
            print(f"   📧 Emails found: {len(emails)}")
            print(f"   📞 Phones found: {len(phones)}")
            
            # Step 3: Executive Discovery (FIXED)
            print("\n👥 Step 3: Executive Discovery (FIXED)")
            executives = await executive_discovery.discover_executives_fixed(company_name, url)
            
            print(f"   ✅ Executives discovered: {len(executives)}")
            for exec in executives[:3]:  # Show first 3
                print(f"      👤 {exec.full_name} - {exec.title} ({exec.seniority_tier})")
            
            # Step 4: Email Enrichment
            print("\n📧 Step 4: Email Enrichment")
            if executives:
                try:
                    enriched_executives = email_enricher.enrich_executives_emails(executives, domain)
                    email_enriched_count = sum(1 for exec in enriched_executives if exec.email)
                    print(f"   ✅ Executives with emails: {email_enriched_count}/{len(enriched_executives)}")
                    executives = enriched_executives
                except Exception as e:
                    print(f"   ⚠️ Email enrichment failed: {e}")
            
            # Step 5: Phone Number Discovery
            print("\n📞 Step 5: Phone Number Discovery")
            try:
                phone_results = await phone_enricher.discover_phone_numbers(company_name, domain)
                additional_phones = [str(result.phone_number) for result in phone_results if hasattr(result, 'phone_number')]
                all_phones = list(set(phones + additional_phones))
                print(f"   ✅ Total phone numbers: {len(all_phones)}")
            except Exception as e:
                print(f"   ⚠️ Phone discovery failed: {e}")
                all_phones = phones
            
            # Calculate processing time
            processing_time = time.time() - url_start_time
            
            # Compile results
            result = {
                "url": url,
                "company_name": company_name,
                "domain": domain,
                "processing_time_seconds": round(processing_time, 2),
                "status": "success",
                "company_info": company_info,
                "contact_info": {
                    "emails": emails,
                    "phones": all_phones,
                    "total_emails": len(emails),
                    "total_phones": len(all_phones)
                },
                "executives": {
                    "total_found": len(executives),
                    "executives_list": [
                        {
                            "name": exec.full_name,
                            "title": exec.title,
                            "seniority_tier": exec.seniority_tier,
                            "email": exec.email,
                            "phone": exec.phone,
                            "confidence": exec.overall_confidence,
                            "completeness": exec.data_completeness_score,
                            "discovery_method": exec.discovery_method
                        }
                        for exec in executives
                    ]
                },
                "summary": {
                    "executives_with_emails": sum(1 for exec in executives if exec.email),
                    "executives_with_phones": sum(1 for exec in executives if exec.phone),
                    "tier_1_executives": sum(1 for exec in executives if exec.seniority_tier == "tier_1"),
                    "tier_2_executives": sum(1 for exec in executives if exec.seniority_tier == "tier_2"),
                    "tier_3_executives": sum(1 for exec in executives if exec.seniority_tier == "tier_3"),
                    "data_completeness_avg": round(sum(exec.data_completeness_score for exec in executives) / len(executives) if executives else 0, 2),
                    "confidence_avg": round(sum(exec.overall_confidence for exec in executives) / len(executives) if executives else 0, 2)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            all_results.append(result)
            
            print(f"\n✅ URL {i} COMPLETED in {processing_time:.2f}s")
            print(f"   📊 Summary: {len(executives)} executives, {len(emails)} emails, {len(all_phones)} phones")
            
        except Exception as e:
            processing_time = time.time() - url_start_time
            print(f"\n❌ URL {i} FAILED after {processing_time:.2f}s: {e}")
            
            # Add failed result
            result = {
                "url": url,
                "company_name": "Unknown",
                "domain": urlparse(url).netloc.replace('www.', ''),
                "processing_time_seconds": round(processing_time, 2),
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            all_results.append(result)
    
    # Calculate final statistics
    total_processing_time = time.time() - total_start_time
    successful_results = [r for r in all_results if r['status'] == 'success']
    
    final_stats = {
        "test_info": {
            "total_urls": len(test_urls),
            "successful_urls": len(successful_results),
            "failed_urls": len(all_results) - len(successful_results),
            "success_rate": f"{(len(successful_results) / len(test_urls)) * 100:.1f}%",
            "total_processing_time": round(total_processing_time, 2),
            "average_processing_time": round(total_processing_time / len(test_urls), 2)
        },
        "aggregate_stats": {
            "total_companies": len(successful_results),
            "total_executives": sum(r.get('executives', {}).get('total_found', 0) for r in successful_results),
            "total_emails": sum(r.get('contact_info', {}).get('total_emails', 0) for r in successful_results),
            "total_phones": sum(r.get('contact_info', {}).get('total_phones', 0) for r in successful_results),
            "executives_with_emails": sum(r.get('summary', {}).get('executives_with_emails', 0) for r in successful_results),
            "executives_with_phones": sum(r.get('summary', {}).get('executives_with_phones', 0) for r in successful_results),
            "tier_1_executives": sum(r.get('summary', {}).get('tier_1_executives', 0) for r in successful_results),
            "tier_2_executives": sum(r.get('summary', {}).get('tier_2_executives', 0) for r in successful_results),
            "tier_3_executives": sum(r.get('summary', {}).get('tier_3_executives', 0) for r in successful_results),
            "average_executives_per_company": round(sum(r.get('executives', {}).get('total_found', 0) for r in successful_results) / len(successful_results) if successful_results else 0, 1)
        },
        "results": all_results,
        "test_timestamp": datetime.now().isoformat()
    }
    
    # Save results
    timestamp = int(time.time())
    filename = f"comprehensive_seo_lead_test_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(final_stats, f, indent=2, default=str)
    
    # Print final summary
    print(f"\n{'='*70}")
    print("🏆 FINAL TEST RESULTS")
    print(f"{'='*70}")
    print(f"📊 URLs Processed: {final_stats['test_info']['total_urls']}")
    print(f"✅ Successful: {final_stats['test_info']['successful_urls']}")
    print(f"❌ Failed: {final_stats['test_info']['failed_urls']}")
    print(f"📈 Success Rate: {final_stats['test_info']['success_rate']}")
    print(f"⏱️  Total Time: {final_stats['test_info']['total_processing_time']:.2f}s")
    print(f"⚡ Avg Time/URL: {final_stats['test_info']['average_processing_time']:.2f}s")
    print()
    print("🎯 DISCOVERY RESULTS:")
    print(f"🏢 Companies: {final_stats['aggregate_stats']['total_companies']}")
    print(f"👥 Executives: {final_stats['aggregate_stats']['total_executives']}")
    print(f"📧 Emails: {final_stats['aggregate_stats']['total_emails']}")
    print(f"📞 Phones: {final_stats['aggregate_stats']['total_phones']}")
    print(f"💼 Tier 1 Executives: {final_stats['aggregate_stats']['tier_1_executives']}")
    print(f"🎖️  Tier 2 Executives: {final_stats['aggregate_stats']['tier_2_executives']}")
    print(f"🏅 Tier 3 Executives: {final_stats['aggregate_stats']['tier_3_executives']}")
    print(f"📊 Avg Executives/Company: {final_stats['aggregate_stats']['average_executives_per_company']}")
    print()
    print(f"💾 Results saved to: {filename}")
    
    return final_stats

if __name__ == "__main__":
    asyncio.run(comprehensive_seo_lead_test()) 