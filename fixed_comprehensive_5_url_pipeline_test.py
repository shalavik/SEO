#!/usr/bin/env python3
"""
Fixed Comprehensive 5-URL Pipeline Test
Runs the complete SEO lead generation process for 5 plumbing companies
without using Yell directory fetching.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import sys
import os
import uuid

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from seo_leads.database import initialize_database, get_db_session
from seo_leads.models import UKCompany, SEOAnalysis, ContactInfo, ExecutiveContact
from seo_leads.analyzers import SEOAnalyzer
from seo_leads.processors import ContactExtractor, LeadQualifier
from seo_leads.processors.executive_discovery import ExecutiveDiscoveryEngine
from seo_leads.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensivePipelineProcessor:
    """Processes companies through the complete pipeline without Yell fetching"""
    
    def __init__(self):
        self.config = get_config()
        self.seo_analyzer = SEOAnalyzer()
        self.contact_extractor = ContactExtractor()
        self.lead_qualifier = LeadQualifier()
        self.executive_discovery = ExecutiveDiscoveryEngine()
        
    async def process_url(self, url: str) -> Dict[str, Any]:
        """Process a single URL through the complete pipeline"""
        start_time = time.time()
        
        try:
            logger.info(f"🔄 Processing: {url}")
            
            # Step 1: Extract company info from URL
            company_info = self._extract_company_info_from_url(url)
            logger.info(f"   📋 Company: {company_info['name']}")
            
            # Step 2: Create/update company in database
            company_id = await self._create_or_update_company(company_info)
            
            # Step 3: SEO Analysis
            logger.info(f"   🔍 Running SEO analysis...")
            seo_result = await self.seo_analyzer.analyze_website_seo(
                company_id=company_id,
                website_url=url,
                company_name=company_info['name']
            )
            
            # Step 4: Contact Extraction
            logger.info(f"   📞 Extracting contacts...")
            contact_result = await self.contact_extractor.extract_contacts_with_executives(
                company_id=company_id,
                company_name=company_info['name'],
                website_url=url
            )
            
            # Step 5: Executive Discovery
            logger.info(f"   👔 Discovering executives...")
            executive_result = await self.executive_discovery.discover_executives(
                company_name=company_info['name'],
                website_url=url,
                company_id=company_id
            )
            
            # Step 6: Lead Qualification
            logger.info(f"   ⭐ Qualifying lead...")
            qualification_result = await self.lead_qualifier.qualify_lead(company_id)
            
            processing_time = time.time() - start_time
            
            # Compile comprehensive result
            result = {
                "url": url,
                "company_info": company_info,
                "company_id": company_id,
                "processing_time_seconds": round(processing_time, 2),
                "timestamp": datetime.now().isoformat(),
                "seo_analysis": self._format_seo_result(seo_result),
                "contact_extraction": self._format_contact_result(contact_result),
                "executive_discovery": self._format_executive_result(executive_result),
                "lead_qualification": self._format_qualification_result(qualification_result),
                "status": "success"
            }
            
            logger.info(f"   ✅ Completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"   ❌ Error processing {url}: {str(e)}")
            
            return {
                "url": url,
                "processing_time_seconds": round(processing_time, 2),
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "error"
            }
    
    def _extract_company_info_from_url(self, url: str) -> Dict[str, str]:
        """Extract basic company information from URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove common prefixes
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Extract company name from domain
        company_name = domain.split('.')[0]
        
        # Clean up common patterns
        company_name = company_name.replace('-', ' ').replace('_', ' ')
        company_name = ' '.join(word.capitalize() for word in company_name.split())
        
        # Special handling for known patterns
        if 'plumb' in company_name.lower():
            if not any(word in company_name.lower() for word in ['plumbing', 'plumber']):
                company_name += ' Plumbing'
        
        return {
            "name": company_name,
            "website": url,
            "domain": domain,
            "sector": "Plumbing Services",
            "city": "Birmingham",  # Default for these test companies
            "source": "Direct URL Processing"
        }
    
    async def _create_or_update_company(self, company_info: Dict[str, str]) -> str:
        """Create or update company in database"""
        with get_db_session() as session:
            # Check if company already exists
            existing = session.query(UKCompany).filter(
                UKCompany.website == company_info['website']
            ).first()
            
            if existing:
                # Update existing company
                existing.company_name = company_info['name']
                existing.sector = company_info['sector']
                existing.city = company_info['city']
                existing.source = company_info['source']
                session.commit()
                return existing.id
            else:
                # Create new company with generated ID
                company_id = str(uuid.uuid4())
                company = UKCompany(
                    id=company_id,
                    company_name=company_info['name'],
                    website=company_info['website'],
                    sector=company_info['sector'],
                    city=company_info['city'],
                    source=company_info['source']
                )
                session.add(company)
                session.commit()
                return company.id
    
    def _format_seo_result(self, seo_result) -> Dict[str, Any]:
        """Format SEO analysis result for JSON output"""
        if not seo_result:
            return {"status": "failed", "data": None}
        
        return {
            "status": "completed",
            "overall_score": getattr(seo_result, 'overall_score', 0),
            "technical_score": getattr(seo_result, 'technical_score', 0),
            "content_score": getattr(seo_result, 'content_score', 0),
            "performance_score": getattr(seo_result, 'performance_score', 0),
            "mobile_friendly": getattr(seo_result, 'mobile_friendly', False),
            "page_speed": getattr(seo_result, 'page_speed_score', 0),
            "meta_title": getattr(seo_result, 'meta_title', ''),
            "meta_description": getattr(seo_result, 'meta_description', ''),
            "h1_tags": getattr(seo_result, 'h1_tags', []),
            "issues_found": getattr(seo_result, 'issues_found', []),
            "recommendations": getattr(seo_result, 'recommendations', [])
        }
    
    def _format_contact_result(self, contact_result) -> Dict[str, Any]:
        """Format contact extraction result for JSON output"""
        if not contact_result:
            return {"status": "failed", "contacts": []}
        
        contacts = []
        if isinstance(contact_result, dict):
            # Handle the enhanced result format
            basic_contacts = contact_result.get('basic_contacts', [])
            for contact in basic_contacts:
                if hasattr(contact, '__dict__'):
                    contacts.append({
                        "type": "basic_contact",
                        "email": getattr(contact, 'email', ''),
                        "phone": getattr(contact, 'phone', ''),
                        "address": getattr(contact, 'address', ''),
                        "confidence": getattr(contact, 'confidence', 0)
                    })
        
        return {
            "status": "completed",
            "contacts_found": len(contacts),
            "contacts": contacts
        }
    
    def _format_executive_result(self, executive_result) -> Dict[str, Any]:
        """Format executive discovery result for JSON output"""
        if not executive_result:
            return {"status": "failed", "executives": []}
        
        executives = []
        if hasattr(executive_result, 'executives_found'):
            for exec in executive_result.executives_found:
                executives.append({
                    "first_name": getattr(exec, 'first_name', ''),
                    "last_name": getattr(exec, 'last_name', ''),
                    "full_name": getattr(exec, 'full_name', ''),
                    "title": getattr(exec, 'title', ''),
                    "email": getattr(exec, 'email', ''),
                    "phone": getattr(exec, 'phone', ''),
                    "linkedin_url": getattr(exec, 'linkedin_url', ''),
                    "seniority_tier": getattr(exec, 'seniority_tier', ''),
                    "overall_confidence": getattr(exec, 'overall_confidence', 0),
                    "discovery_sources": getattr(exec, 'discovery_sources', [])
                })
        elif isinstance(executive_result, list):
            for exec in executive_result:
                executives.append({
                    "first_name": getattr(exec, 'first_name', ''),
                    "last_name": getattr(exec, 'last_name', ''),
                    "full_name": getattr(exec, 'full_name', ''),
                    "title": getattr(exec, 'title', ''),
                    "email": getattr(exec, 'email', ''),
                    "phone": getattr(exec, 'phone', ''),
                    "linkedin_url": getattr(exec, 'linkedin_url', ''),
                    "seniority_tier": getattr(exec, 'seniority_tier', ''),
                    "overall_confidence": getattr(exec, 'overall_confidence', 0),
                    "discovery_sources": getattr(exec, 'discovery_sources', [])
                })
        
        return {
            "status": "completed",
            "executives_found": len(executives),
            "executives": executives,
            "discovery_stats": {
                "total_processing_time": getattr(executive_result, 'total_processing_time', 0) if hasattr(executive_result, 'total_processing_time') else 0,
                "success_rate": getattr(executive_result, 'success_rate', 0) if hasattr(executive_result, 'success_rate') else 0,
                "discovery_sources": getattr(executive_result, 'discovery_sources', []) if hasattr(executive_result, 'discovery_sources') else []
            }
        }
    
    def _format_qualification_result(self, qualification_result) -> Dict[str, Any]:
        """Format lead qualification result for JSON output"""
        if not qualification_result:
            return {"status": "failed", "score": 0}
        
        return {
            "status": "completed",
            "overall_score": getattr(qualification_result, 'overall_score', 0),
            "seo_score": getattr(qualification_result, 'seo_score', 0),
            "contact_score": getattr(qualification_result, 'contact_score', 0),
            "business_score": getattr(qualification_result, 'business_score', 0),
            "qualification_level": getattr(qualification_result, 'qualification_level', 'Unknown'),
            "reasons": getattr(qualification_result, 'reasons', []),
            "recommendations": getattr(qualification_result, 'recommendations', [])
        }

async def main():
    """Main function to run the comprehensive pipeline test"""
    
    # Test URLs
    test_urls = [
        "http://gpj-plumbing.co.uk/",
        "https://www.emergencyplumber.services/",
        "https://247plumbingandgas.co.uk/",
        "http://www.hancoxgasandplumbing.co.uk/",
        "https://metroplumb.co.uk/locations/metro-plumb-birmingham/"
    ]
    
    print("🚀 Starting Fixed Comprehensive 5-URL Pipeline Test")
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    print(f"🎯 Processing {len(test_urls)} URLs")
    print("=" * 60)
    
    # Initialize database
    try:
        initialize_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    # Initialize processor
    processor = ComprehensivePipelineProcessor()
    
    # Process all URLs
    results = []
    total_start_time = time.time()
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📍 Processing URL {i}/{len(test_urls)}: {url}")
        result = await processor.process_url(url)
        results.append(result)
    
    total_processing_time = time.time() - total_start_time
    
    # Compile final results
    final_results = {
        "test_info": {
            "name": "Fixed Comprehensive 5-URL Pipeline Test",
            "timestamp": datetime.now().isoformat(),
            "total_urls": len(test_urls),
            "total_processing_time_seconds": round(total_processing_time, 2),
            "average_time_per_url": round(total_processing_time / len(test_urls), 2)
        },
        "summary": {
            "successful_processes": len([r for r in results if r.get('status') == 'success']),
            "failed_processes": len([r for r in results if r.get('status') == 'error']),
            "total_executives_found": sum(r.get('executive_discovery', {}).get('executives_found', 0) for r in results),
            "total_contacts_found": sum(r.get('contact_extraction', {}).get('contacts_found', 0) for r in results)
        },
        "results": results
    }
    
    # Save results to file
    timestamp = int(time.time())
    filename = f"fixed_comprehensive_5_url_pipeline_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("🎉 FIXED COMPREHENSIVE PIPELINE TEST COMPLETE")
    print(f"📊 Results Summary:")
    print(f"   ✅ Successful: {final_results['summary']['successful_processes']}")
    print(f"   ❌ Failed: {final_results['summary']['failed_processes']}")
    print(f"   👔 Total Executives Found: {final_results['summary']['total_executives_found']}")
    print(f"   📞 Total Contacts Found: {final_results['summary']['total_contacts_found']}")
    print(f"   ⏱️  Total Time: {final_results['test_info']['total_processing_time_seconds']}s")
    print(f"   📄 Results saved to: {filename}")
    print("=" * 60)
    
    # Print JSON results to console
    print("\n🔍 FINAL JSON RESULTS:")
    print(json.dumps(final_results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())