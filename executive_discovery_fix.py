#!/usr/bin/env python3
"""
Fixed Executive Discovery Test

Addresses the key issues found in the previous test:
1. LinkedIn scraper initialization method missing
2. HttpUrl database binding errors
3. Executive discovery timeout issues
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our modules
from src.seo_leads.analyzers.seo_analyzer import SEOAnalyzer
from src.seo_leads.processors.contact_extractor import ContactExtractor
from src.seo_leads.processors.lead_qualifier import LeadQualifier
from src.seo_leads.processors.executive_discovery import ExecutiveDiscoveryEngine, ExecutiveDiscoveryConfig
from src.seo_leads.scrapers.website_executive_scraper import WebsiteExecutiveScraper
from src.seo_leads.processors.executive_email_enricher import ExecutiveEmailEnricher
from src.seo_leads.models import UKCompany, ExecutiveContact
from src.seo_leads.database import get_db_session

class FixedExecutiveDiscovery:
    """Fixed executive discovery with proper error handling"""
    
    def __init__(self):
        self.website_scraper = WebsiteExecutiveScraper()
        self.email_enricher = ExecutiveEmailEnricher()
        
    async def discover_executives_fixed(self, company_name: str, website_url: str) -> List[ExecutiveContact]:
        """Fixed executive discovery without LinkedIn dependency"""
        try:
            logger.info(f"Starting fixed executive discovery for {company_name}")
            
            # Use only website scraping (more reliable)
            domain = urlparse(website_url).netloc.replace('www.', '')
            
            # Discover executives from website
            executives = await self.website_scraper.discover_executives(
                website_url, company_name
            )
            
            if executives:
                # Enrich with email patterns
                enriched_executives = await self.email_enricher.enrich_executive_emails(
                    executives, domain
                )
                
                logger.info(f"Found {len(enriched_executives)} executives for {company_name}")
                return enriched_executives
            else:
                logger.info(f"No executives found for {company_name}")
                return []
                
        except Exception as e:
            logger.error(f"Executive discovery failed for {company_name}: {e}")
            return []

async def run_fixed_executive_discovery_test():
    """Run the fixed executive discovery test on 5 plumbing companies"""
    
    # Test companies
    test_companies = [
        {
            "name": "GPJ Plumbing",
            "url": "http://gpj-plumbing.co.uk/",
            "sector": "plumbing"
        },
        {
            "name": "Emergency Plumber Services", 
            "url": "https://www.emergencyplumber.services/",
            "sector": "plumbing"
        },
        {
            "name": "247 Plumbing and Gas",
            "url": "https://247plumbingandgas.co.uk/",
            "sector": "plumbing"
        },
        {
            "name": "Hancox Gas and Plumbing",
            "url": "http://www.hancoxgasandplumbing.co.uk/",
            "sector": "plumbing"
        },
        {
            "name": "Metro Plumb Birmingham",
            "url": "https://metroplumb.co.uk/locations/metro-plumb-birmingham/",
            "sector": "plumbing"
        }
    ]
    
    # Initialize components
    seo_analyzer = SEOAnalyzer()
    contact_extractor = ContactExtractor()
    lead_qualifier = LeadQualifier()
    executive_discovery = FixedExecutiveDiscovery()
    
    results = []
    start_time = time.time()
    
    for i, company in enumerate(test_companies, 1):
        print(f"\n📍 Processing {i}/{len(test_companies)}: {company['name']}")
        print(f"🔄 Processing: {company['name']} - {company['url']}")
        
        company_start_time = time.time()
        company_id = str(uuid.uuid4())
        
        try:
            # Create company record with proper data types
            company_data = {
                'company_id': company_id,
                'company_name': company['name'],
                'website': company['url'],
                'sector': company['sector'],
                'processing_time_seconds': 0.0,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
            # Step 1: SEO Analysis
            print("   🔍 Running SEO analysis...")
            seo_result = await seo_analyzer.analyze_website_seo(
                company_id, company['url'], company['sector']
            )
            
            if seo_result:
                company_data['seo_analysis'] = {
                    'status': 'completed',
                    'overall_score': seo_result.overall_score,
                    'mobile_friendly': seo_result.mobile_friendly,
                    'page_speed_score': seo_result.pagespeed_score,
                    'ssl_certificate': seo_result.ssl_certificate,
                    'critical_issues': seo_result.critical_issues
                }
            else:
                company_data['seo_analysis'] = {'status': 'failed'}
            
            # Step 2: Contact Extraction (traditional)
            print("   📞 Extracting contacts...")
            contact_result = await contact_extractor.extract_contacts(company_id, company['url'])
            
            if contact_result and contact_result.contact_info:
                company_data['contact_extraction'] = {
                    'status': 'completed',
                    'contacts_found': 1,
                    'contacts': [{
                        'person': contact_result.contact_info.person,
                        'role': contact_result.contact_info.role,
                        'email': contact_result.contact_info.email,
                        'phone': contact_result.contact_info.phone,
                        'linkedin_url': str(contact_result.contact_info.linkedin_url) if contact_result.contact_info.linkedin_url else None,
                        'confidence': contact_result.contact_info.confidence
                    }]
                }
            else:
                company_data['contact_extraction'] = {
                    'status': 'completed',
                    'contacts_found': 0,
                    'contacts': []
                }
            
            # Step 3: Executive Discovery (fixed)
            print("   👔 Discovering executives...")
            executives = await executive_discovery.discover_executives_fixed(
                company['name'], company['url']
            )
            
            executive_data = []
            for exec in executives:
                exec_dict = {
                    'first_name': exec.first_name,
                    'last_name': exec.last_name,
                    'full_name': exec.full_name,
                    'title': exec.title,
                    'seniority_tier': exec.seniority_tier,
                    'email': exec.email,
                    'phone': exec.phone,
                    'linkedin_url': exec.linkedin_url,
                    'confidence': exec.confidence,
                    'discovery_sources': exec.discovery_sources
                }
                executive_data.append(exec_dict)
            
            company_data['executive_discovery'] = {
                'status': 'completed',
                'executives_found': len(executives),
                'executives': executive_data,
                'discovery_stats': {
                    'total_processing_time': time.time() - company_start_time,
                    'success_rate': 1.0 if executives else 0.0
                }
            }
            
            # Step 4: Lead Qualification
            print("   ⭐ Qualifying lead...")
            
            # Prepare data for lead qualifier (ensure it's a dictionary)
            lead_data = {
                'id': company_id,
                'company_name': company['name'],
                'website': company['url'],
                'sector': company['sector'],
                'seo_overall_score': seo_result.overall_score if seo_result else 0.0,
                'contact_confidence': contact_result.confidence if contact_result else 0.0,
                'executives_found': len(executives)
            }
            
            qualification_result = await lead_qualifier.qualify_lead(lead_data)
            
            if qualification_result:
                company_data['lead_qualification'] = {
                    'status': 'completed',
                    'overall_score': qualification_result.overall_score,
                    'priority_tier': qualification_result.priority_tier,
                    'tier_label': qualification_result.tier_label,
                    'estimated_value': qualification_result.estimated_value,
                    'urgency': qualification_result.urgency,
                    'talking_points': qualification_result.talking_points,
                    'recommended_actions': qualification_result.recommended_actions
                }
            else:
                company_data['lead_qualification'] = {'status': 'failed'}
            
            # Calculate total processing time
            company_data['processing_time_seconds'] = time.time() - company_start_time
            
            print(f"   ✅ Completed in {company_data['processing_time_seconds']:.2f}s")
            
            results.append(company_data)
            
        except Exception as e:
            logger.error(f"Error processing {company['name']}: {e}")
            company_data.update({
                'status': 'failed',
                'error': str(e),
                'processing_time_seconds': time.time() - company_start_time
            })
            results.append(company_data)
    
    # Generate final results
    total_time = time.time() - start_time
    successful_companies = [r for r in results if r['status'] == 'success']
    total_executives = sum(r.get('executive_discovery', {}).get('executives_found', 0) for r in results)
    total_contacts = sum(r.get('contact_extraction', {}).get('contacts_found', 0) for r in results)
    avg_seo_score = sum(r.get('seo_analysis', {}).get('overall_score', 0) for r in results) / len(results)
    avg_lead_score = sum(r.get('lead_qualification', {}).get('overall_score', 0) for r in results) / len(results)
    
    final_results = {
        "test_info": {
            "name": "Fixed Executive Discovery Test",
            "timestamp": datetime.now().isoformat(),
            "total_companies": len(test_companies),
            "total_processing_time_seconds": total_time,
            "average_time_per_company": total_time / len(test_companies)
        },
        "summary": {
            "successful_processes": len(successful_companies),
            "failed_processes": len(results) - len(successful_companies),
            "total_executives_found": total_executives,
            "total_contacts_found": total_contacts,
            "average_seo_score": avg_seo_score,
            "average_lead_score": avg_lead_score
        },
        "results": results
    }
    
    # Save results
    timestamp = int(time.time())
    filename = f"fixed_executive_discovery_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(final_results, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "="*60)
    print("🎉 FIXED EXECUTIVE DISCOVERY TEST COMPLETE")
    print("📊 Results Summary:")
    print(f"   ✅ Successful: {len(successful_companies)}")
    print(f"   ❌ Failed: {len(results) - len(successful_companies)}")
    print(f"   👔 Total Executives Found: {total_executives}")
    print(f"   📞 Total Contacts Found: {total_contacts}")
    print(f"   🔍 Average SEO Score: {avg_seo_score:.1f}")
    print(f"   ⭐ Average Lead Score: {avg_lead_score:.1f}")
    print(f"   ⏱️  Total Time: {total_time:.2f}s")
    print(f"   📄 Results saved to: {filename}")
    print("="*60)
    
    # Print JSON results
    print("\n🔍 FINAL JSON RESULTS:")
    print(json.dumps(final_results, indent=2, default=str))
    
    return final_results

if __name__ == "__main__":
    asyncio.run(run_fixed_executive_discovery_test()) 