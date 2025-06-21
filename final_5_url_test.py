#!/usr/bin/env python3
"""
Final 5-URL Test
Complete end-to-end processing of 5 plumbing company URLs through the entire pipeline
"""

import asyncio
import json
import logging
import time
from datetime import datetime
import sys
import os
import uuid

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from seo_leads.database import initialize_database, get_db_session
from seo_leads.models import UKCompany
from seo_leads.analyzers.seo_analyzer import SEOAnalyzer
from seo_leads.processors.contact_extractor import ContactExtractor
from seo_leads.processors.lead_qualifier import LeadQualifier
from seo_leads.processors.executive_discovery import ExecutiveDiscoveryEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_single_url(url: str, company_name: str) -> dict:
    """Process a single URL through the complete pipeline"""
    start_time = time.time()
    
    try:
        print(f"🔄 Processing: {company_name} - {url}")
        
        # Create company in database
        company_id = str(uuid.uuid4())
        with get_db_session() as session:
            company = UKCompany(
                id=company_id,
                company_name=company_name,
                website=url,
                sector="Plumbing Services",
                city="Birmingham",
                source="Direct URL Test"
            )
            session.add(company)
            session.commit()
        
        # Initialize processors
        seo_analyzer = SEOAnalyzer()
        contact_extractor = ContactExtractor()
        lead_qualifier = LeadQualifier()
        executive_discovery = ExecutiveDiscoveryEngine()
        
        # Step 1: SEO Analysis
        print(f"   🔍 Running SEO analysis...")
        seo_result = await seo_analyzer.analyze_website_seo(
            company_id=company_id,
            website_url=url,
            company_sector="Plumbing Services"
        )
        
        # Step 2: Contact Extraction
        print(f"   📞 Extracting contacts...")
        contact_result = await contact_extractor.extract_contacts_with_executives(
            company_id=company_id,
            company_name=company_name,
            website_url=url
        )
        
        # Step 3: Executive Discovery
        print(f"   👔 Discovering executives...")
        executive_result = await executive_discovery.discover_executives(
            company_name=company_name,
            website_url=url,
            company_id=company_id
        )
        
        # Step 4: Lead Qualification - Format data properly
        print(f"   ⭐ Qualifying lead...")
        
        # Format contact info for lead qualifier
        contact_info = {}
        if contact_result and isinstance(contact_result, dict):
            basic_contacts = contact_result.get('basic_contacts', [])
            if basic_contacts:
                first_contact = basic_contacts[0]
                contact_info = {
                    'person': getattr(first_contact, 'email', '').split('@')[0] if hasattr(first_contact, 'email') else '',
                    'role': 'Contact',
                    'email': getattr(first_contact, 'email', ''),
                    'phone': getattr(first_contact, 'phone', ''),
                    'confidence': getattr(first_contact, 'confidence', 0.0)
                }
        
        # Format company data for lead qualifier
        company_data = {
            'company_name': company_name,
            'website': url,
            'city': 'Birmingham',
            'sector': 'Plumbing Services',
            'seo_analysis': seo_result,
            'contact_info': contact_info
        }
        
        qualification_result = await lead_qualifier.qualify_lead(company_data)
        
        processing_time = time.time() - start_time
        
        # Format results
        result = {
            "url": url,
            "company_name": company_name,
            "company_id": company_id,
            "processing_time_seconds": round(processing_time, 2),
            "timestamp": datetime.now().isoformat(),
            "seo_analysis": {
                "status": "completed" if seo_result else "failed",
                "overall_score": getattr(seo_result, 'overall_score', 0),
                "mobile_friendly": getattr(seo_result.performance, 'mobile_friendly', False) if seo_result and hasattr(seo_result, 'performance') else False,
                "page_speed_score": getattr(seo_result.performance, 'pagespeed_score', 0) if seo_result and hasattr(seo_result, 'performance') else 0,
                "ssl_certificate": getattr(seo_result.content, 'ssl_certificate', False) if seo_result and hasattr(seo_result, 'content') else False,
                "critical_issues": getattr(seo_result, 'critical_issues', []) if seo_result else []
            },
            "contact_extraction": {
                "status": "completed" if contact_result else "failed",
                "contacts_found": len(contact_result.get('basic_contacts', [])) if isinstance(contact_result, dict) else 0,
                "contacts": []
            },
            "executive_discovery": {
                "status": "completed" if executive_result else "failed",
                "executives_found": len(getattr(executive_result, 'executives_found', [])) if hasattr(executive_result, 'executives_found') else 0,
                "executives": [],
                "discovery_stats": {
                    "total_processing_time": getattr(executive_result, 'total_processing_time', 0) if hasattr(executive_result, 'total_processing_time') else 0,
                    "success_rate": getattr(executive_result, 'success_rate', 0) if hasattr(executive_result, 'success_rate') else 0
                }
            },
            "lead_qualification": {
                "status": "completed" if qualification_result else "failed",
                "overall_score": getattr(qualification_result, 'final_score', 0) if qualification_result else 0,
                "priority_tier": getattr(qualification_result, 'priority_tier', 'Unknown') if qualification_result else 'Unknown',
                "tier_label": getattr(qualification_result, 'tier_label', 'Unknown') if qualification_result else 'Unknown',
                "estimated_value": getattr(qualification_result, 'estimated_value', 0) if qualification_result else 0,
                "urgency": getattr(qualification_result, 'urgency', 'Unknown') if qualification_result else 'Unknown',
                "talking_points": getattr(qualification_result, 'talking_points', []) if qualification_result else [],
                "recommended_actions": getattr(qualification_result, 'recommended_actions', []) if qualification_result else []
            },
            "status": "success"
        }
        
        # Add contact details if found
        if contact_result and isinstance(contact_result, dict):
            basic_contacts = contact_result.get('basic_contacts', [])
            for contact in basic_contacts:
                if hasattr(contact, '__dict__'):
                    result["contact_extraction"]["contacts"].append({
                        "email": getattr(contact, 'email', ''),
                        "phone": getattr(contact, 'phone', ''),
                        "address": getattr(contact, 'address', ''),
                        "confidence": getattr(contact, 'confidence', 0)
                    })
        
        # Add executive details if found
        if executive_result and hasattr(executive_result, 'executives_found'):
            for exec in executive_result.executives_found:
                result["executive_discovery"]["executives"].append({
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
        
        print(f"   ✅ Completed in {processing_time:.2f}s")
        return result
        
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"   ❌ Error: {str(e)}")
        
        return {
            "url": url,
            "company_name": company_name,
            "processing_time_seconds": round(processing_time, 2),
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "status": "error"
        }

async def main():
    """Main function to run the test"""
    
    # Test companies
    test_companies = [
        ("http://gpj-plumbing.co.uk/", "GPJ Plumbing"),
        ("https://www.emergencyplumber.services/", "Emergency Plumber Services"),
        ("https://247plumbingandgas.co.uk/", "247 Plumbing and Gas"),
        ("http://www.hancoxgasandplumbing.co.uk/", "Hancox Gas and Plumbing"),
        ("https://metroplumb.co.uk/locations/metro-plumb-birmingham/", "Metro Plumb Birmingham")
    ]
    
    print("🚀 Starting Final 5-URL Pipeline Test")
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    print(f"🎯 Processing {len(test_companies)} companies")
    print("=" * 60)
    
    # Initialize database
    try:
        initialize_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    # Process all companies
    results = []
    total_start_time = time.time()
    
    for i, (url, company_name) in enumerate(test_companies, 1):
        print(f"\n📍 Processing {i}/{len(test_companies)}: {company_name}")
        result = await process_single_url(url, company_name)
        results.append(result)
    
    total_processing_time = time.time() - total_start_time
    
    # Compile final results
    final_results = {
        "test_info": {
            "name": "Final 5-URL Pipeline Test",
            "timestamp": datetime.now().isoformat(),
            "total_companies": len(test_companies),
            "total_processing_time_seconds": round(total_processing_time, 2),
            "average_time_per_company": round(total_processing_time / len(test_companies), 2)
        },
        "summary": {
            "successful_processes": len([r for r in results if r.get('status') == 'success']),
            "failed_processes": len([r for r in results if r.get('status') == 'error']),
            "total_executives_found": sum(r.get('executive_discovery', {}).get('executives_found', 0) for r in results),
            "total_contacts_found": sum(r.get('contact_extraction', {}).get('contacts_found', 0) for r in results),
            "average_seo_score": round(sum(r.get('seo_analysis', {}).get('overall_score', 0) for r in results) / len(results), 2),
            "average_lead_score": round(sum(r.get('lead_qualification', {}).get('overall_score', 0) for r in results) / len(results), 2)
        },
        "results": results
    }
    
    # Save results to file
    timestamp = int(time.time())
    filename = f"final_5_url_test_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("🎉 FINAL PIPELINE TEST COMPLETE")
    print(f"📊 Results Summary:")
    print(f"   ✅ Successful: {final_results['summary']['successful_processes']}")
    print(f"   ❌ Failed: {final_results['summary']['failed_processes']}")
    print(f"   👔 Total Executives Found: {final_results['summary']['total_executives_found']}")
    print(f"   📞 Total Contacts Found: {final_results['summary']['total_contacts_found']}")
    print(f"   🔍 Average SEO Score: {final_results['summary']['average_seo_score']}")
    print(f"   ⭐ Average Lead Score: {final_results['summary']['average_lead_score']}")
    print(f"   ⏱️  Total Time: {final_results['test_info']['total_processing_time_seconds']}s")
    print(f"   📄 Results saved to: {filename}")
    print("=" * 60)
    
    # Print JSON results to console
    print("\n🔍 FINAL JSON RESULTS:")
    print(json.dumps(final_results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main()) 