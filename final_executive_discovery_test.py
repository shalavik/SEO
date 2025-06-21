import asyncio
import json
import time
import sys
import os
import re
import requests
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import urlparse

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import our fixed executive discovery
from fixed_executive_discovery import FixedExecutiveDiscovery

class ComprehensiveLeadGenerator:
    """Comprehensive lead generation with executive discovery"""
    
    def __init__(self):
        self.executive_discovery = FixedExecutiveDiscovery()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    async def extract_company_info(self, url: str) -> Dict[str, Any]:
        """Extract basic company information from website"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                content = response.text
                
                # Extract company name from title or content
                company_name = self._extract_company_name(content, url)
                
                # Extract basic business info
                business_info = self._extract_business_info(content)
                
                return {
                    "company_name": company_name,
                    "website": url,
                    "domain": urlparse(url).netloc.replace('www.', ''),
                    "business_type": business_info.get('type', 'Unknown'),
                    "location": business_info.get('location', 'Unknown'),
                    "description": business_info.get('description', '')
                }
        except Exception as e:
            domain = urlparse(url).netloc.replace('www.', '')
            return {
                "company_name": domain.split('.')[0].title(),
                "website": url,
                "domain": domain,
                "business_type": "Unknown",
                "location": "Unknown",
                "description": "",
                "extraction_error": str(e)
            }
    
    async def extract_contact_info(self, url: str) -> Dict[str, Any]:
        """Extract contact information from website"""
        emails = []
        phones = []
        
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                content = response.text
                
                # Extract emails
                email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
                emails = list(set(re.findall(email_pattern, content)))
                
                # Extract UK phone numbers
                phone_patterns = [
                    r'(\+44\s?\d{2,4}\s?\d{3,4}\s?\d{3,4})',
                    r'(0\d{2,4}\s?\d{3,4}\s?\d{3,4})',
                    r'(\d{5}\s?\d{6})',
                ]
                
                for pattern in phone_patterns:
                    phones.extend(re.findall(pattern, content))
                
                phones = list(set(phones))
                
        except Exception as e:
            pass
        
        return {
            "emails": emails,
            "phones": phones,
            "total_emails": len(emails),
            "total_phones": len(phones)
        }
    
    def _extract_company_name(self, content: str, url: str) -> str:
        """Extract company name from content"""
        # Try title tag first
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            # Clean up title
            title = re.sub(r'\s*-\s*.*$', '', title)  # Remove everything after dash
            title = re.sub(r'\s*\|\s*.*$', '', title)  # Remove everything after pipe
            if len(title) > 5 and not any(word in title.lower() for word in ['home', 'welcome', 'index']):
                return title
        
        # Try h1 tags
        h1_matches = re.findall(r'<h1[^>]*>([^<]+)</h1>', content, re.IGNORECASE)
        for h1 in h1_matches:
            h1 = h1.strip()
            if len(h1) > 5 and not any(word in h1.lower() for word in ['welcome', 'home']):
                return h1
        
        # Fallback to domain
        domain = urlparse(url).netloc.replace('www.', '')
        return domain.split('.')[0].title()
    
    def _extract_business_info(self, content: str) -> Dict[str, str]:
        """Extract business information from content"""
        info = {}
        
        # Extract business type
        if any(word in content.lower() for word in ['plumb', 'heating', 'boiler']):
            info['type'] = 'Plumbing & Heating'
        elif any(word in content.lower() for word in ['electric', 'electrical']):
            info['type'] = 'Electrical'
        elif any(word in content.lower() for word in ['build', 'construct']):
            info['type'] = 'Construction'
        else:
            info['type'] = 'Service Business'
        
        # Extract location (UK cities)
        uk_cities = ['birmingham', 'london', 'manchester', 'liverpool', 'leeds', 'sheffield', 'bristol', 'coventry', 'leicester', 'nottingham']
        for city in uk_cities:
            if city in content.lower():
                info['location'] = city.title()
                break
        
        return info

async def comprehensive_executive_discovery_test():
    """Comprehensive test of executive discovery system"""
    
    print("🚀 COMPREHENSIVE EXECUTIVE DISCOVERY TEST")
    print("=" * 70)
    print("🎯 Testing complete executive discovery pipeline")
    print("📊 Processing 5 URLs with full executive enrichment")
    print("=" * 70)
    
    # Test URLs
    test_urls = [
        "https://macplumbheat.co.uk/",
        "https://ltfplumbing.co.uk/subscription",
        "http://www.ctmplumbing.co.uk/",
        "https://kingsheathplumbing.freeindex.co.uk/",
        "http://www.perry-plumbing.co.uk/"
    ]
    
    # Initialize lead generator
    lead_generator = ComprehensiveLeadGenerator()
    
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
            company_info = await lead_generator.extract_company_info(url)
            
            company_name = company_info.get('company_name', 'Unknown Company')
            domain = company_info.get('domain', 'unknown.com')
            
            print(f"   ✅ Company: {company_name}")
            print(f"   🌐 Domain: {domain}")
            print(f"   🏢 Type: {company_info.get('business_type', 'Unknown')}")
            
            # Step 2: Extract contact information
            print("\n📞 Step 2: Contact Information Extraction")
            contact_info = await lead_generator.extract_contact_info(url)
            
            emails = contact_info.get('emails', [])
            phones = contact_info.get('phones', [])
            
            print(f"   📧 Emails found: {len(emails)}")
            print(f"   📞 Phones found: {len(phones)}")
            
            # Step 3: Executive Discovery (MAIN FOCUS)
            print("\n👥 Step 3: Executive Discovery")
            executives = await lead_generator.executive_discovery.discover_executives_fixed(company_name, url)
            
            print(f"   ✅ Executives discovered: {len(executives)}")
            
            # Show executive details
            for j, exec in enumerate(executives, 1):
                print(f"      {j}. 👤 {exec.full_name}")
                print(f"         🏷️  {exec.title} ({exec.seniority_tier})")
                print(f"         📧 {exec.email or 'No email'}")
                print(f"         📞 {exec.phone or 'No phone'}")
                print(f"         🎯 Confidence: {exec.overall_confidence:.2f}")
                print(f"         📊 Completeness: {exec.data_completeness_score:.2f}")
            
            # Calculate processing time
            processing_time = time.time() - url_start_time
            
            # Compile comprehensive results
            result = {
                "url": url,
                "company_info": company_info,
                "contact_info": contact_info,
                "executives": {
                    "total_found": len(executives),
                    "executives_list": [
                        {
                            "name": exec.full_name,
                            "first_name": exec.first_name,
                            "last_name": exec.last_name,
                            "title": exec.title,
                            "seniority_tier": exec.seniority_tier,
                            "email": exec.email,
                            "email_confidence": exec.email_confidence,
                            "phone": exec.phone,
                            "phone_confidence": exec.phone_confidence,
                            "linkedin_url": exec.linkedin_url,
                            "overall_confidence": exec.overall_confidence,
                            "data_completeness_score": exec.data_completeness_score,
                            "discovery_method": exec.discovery_method,
                            "discovery_sources": exec.discovery_sources,
                            "extracted_at": exec.extracted_at.isoformat() if exec.extracted_at else None
                        }
                        for exec in executives
                    ]
                },
                "analytics": {
                    "processing_time_seconds": round(processing_time, 2),
                    "executives_with_emails": sum(1 for exec in executives if exec.email),
                    "executives_with_phones": sum(1 for exec in executives if exec.phone),
                    "tier_1_executives": sum(1 for exec in executives if exec.seniority_tier == "tier_1"),
                    "tier_2_executives": sum(1 for exec in executives if exec.seniority_tier == "tier_2"),
                    "tier_3_executives": sum(1 for exec in executives if exec.seniority_tier == "tier_3"),
                    "average_confidence": round(sum(exec.overall_confidence for exec in executives) / len(executives) if executives else 0, 2),
                    "average_completeness": round(sum(exec.data_completeness_score for exec in executives) / len(executives) if executives else 0, 2),
                    "discovery_methods": list(set(exec.discovery_method for exec in executives)),
                    "primary_decision_maker": executives[0].full_name if executives and executives[0].seniority_tier == "tier_1" else None
                },
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
            
            all_results.append(result)
            
            print(f"\n✅ URL {i} COMPLETED in {processing_time:.2f}s")
            print(f"   📊 Summary: {len(executives)} executives, {len(emails)} emails, {len(phones)} phones")
            
        except Exception as e:
            processing_time = time.time() - url_start_time
            print(f"\n❌ URL {i} FAILED after {processing_time:.2f}s: {e}")
            
            # Add failed result
            result = {
                "url": url,
                "status": "failed",
                "error": str(e),
                "processing_time_seconds": round(processing_time, 2),
                "timestamp": datetime.now().isoformat()
            }
            all_results.append(result)
    
    # Calculate comprehensive statistics
    total_processing_time = time.time() - total_start_time
    successful_results = [r for r in all_results if r['status'] == 'success']
    
    # Aggregate all executives
    all_executives = []
    for result in successful_results:
        all_executives.extend(result.get('executives', {}).get('executives_list', []))
    
    final_results = {
        "test_metadata": {
            "test_name": "Comprehensive Executive Discovery Test",
            "test_timestamp": datetime.now().isoformat(),
            "total_urls_tested": len(test_urls),
            "successful_urls": len(successful_results),
            "failed_urls": len(all_results) - len(successful_results),
            "success_rate_percentage": round((len(successful_results) / len(test_urls)) * 100, 1),
            "total_processing_time_seconds": round(total_processing_time, 2),
            "average_processing_time_per_url": round(total_processing_time / len(test_urls), 2)
        },
        "executive_discovery_summary": {
            "total_companies_processed": len(successful_results),
            "total_executives_discovered": len(all_executives),
            "average_executives_per_company": round(len(all_executives) / len(successful_results) if successful_results else 0, 1),
            "executives_with_emails": sum(1 for exec in all_executives if exec.get('email')),
            "executives_with_phones": sum(1 for exec in all_executives if exec.get('phone')),
            "email_discovery_rate_percentage": round((sum(1 for exec in all_executives if exec.get('email')) / len(all_executives)) * 100 if all_executives else 0, 1),
            "phone_discovery_rate_percentage": round((sum(1 for exec in all_executives if exec.get('phone')) / len(all_executives)) * 100 if all_executives else 0, 1),
            "seniority_breakdown": {
                "tier_1_executives": sum(1 for exec in all_executives if exec.get('seniority_tier') == 'tier_1'),
                "tier_2_executives": sum(1 for exec in all_executives if exec.get('seniority_tier') == 'tier_2'),
                "tier_3_executives": sum(1 for exec in all_executives if exec.get('seniority_tier') == 'tier_3')
            },
            "quality_metrics": {
                "average_confidence_score": round(sum(exec.get('overall_confidence', 0) for exec in all_executives) / len(all_executives) if all_executives else 0, 2),
                "average_completeness_score": round(sum(exec.get('data_completeness_score', 0) for exec in all_executives) / len(all_executives) if all_executives else 0, 2),
                "high_confidence_executives": sum(1 for exec in all_executives if exec.get('overall_confidence', 0) > 0.7),
                "complete_profiles": sum(1 for exec in all_executives if exec.get('data_completeness_score', 0) > 0.8)
            },
            "discovery_methods": {
                method: sum(1 for exec in all_executives if exec.get('discovery_method') == method)
                for method in set(exec.get('discovery_method', 'unknown') for exec in all_executives)
            }
        },
        "detailed_results": all_results,
        "top_executives": sorted(all_executives, key=lambda x: (
            1 if x.get('seniority_tier') == 'tier_1' else 2 if x.get('seniority_tier') == 'tier_2' else 3,
            -x.get('overall_confidence', 0)
        ))[:10]  # Top 10 executives by seniority and confidence
    }
    
    # Save comprehensive results
    timestamp = int(time.time())
    filename = f"comprehensive_executive_discovery_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(final_results, f, indent=2, default=str)
    
    # Print comprehensive summary
    print(f"\n{'='*70}")
    print("🏆 COMPREHENSIVE TEST RESULTS")
    print(f"{'='*70}")
    
    metadata = final_results['test_metadata']
    summary = final_results['executive_discovery_summary']
    
    print(f"📊 Test Overview:")
    print(f"   URLs Processed: {metadata['total_urls_tested']}")
    print(f"   ✅ Successful: {metadata['successful_urls']}")
    print(f"   ❌ Failed: {metadata['failed_urls']}")
    print(f"   📈 Success Rate: {metadata['success_rate_percentage']}%")
    print(f"   ⏱️  Total Time: {metadata['total_processing_time_seconds']:.2f}s")
    print(f"   ⚡ Avg Time/URL: {metadata['average_processing_time_per_url']:.2f}s")
    
    print(f"\n🎯 Executive Discovery Results:")
    print(f"   🏢 Companies: {summary['total_companies_processed']}")
    print(f"   👥 Total Executives: {summary['total_executives_discovered']}")
    print(f"   📊 Avg Executives/Company: {summary['average_executives_per_company']}")
    print(f"   📧 Executives with Emails: {summary['executives_with_emails']} ({summary['email_discovery_rate_percentage']}%)")
    print(f"   📞 Executives with Phones: {summary['executives_with_phones']} ({summary['phone_discovery_rate_percentage']}%)")
    
    print(f"\n⭐ Seniority Breakdown:")
    seniority = summary['seniority_breakdown']
    print(f"   💼 Tier 1 (CEO/Owner): {seniority['tier_1_executives']}")
    print(f"   🎖️  Tier 2 (Director): {seniority['tier_2_executives']}")
    print(f"   🏅 Tier 3 (Manager): {seniority['tier_3_executives']}")
    
    print(f"\n📈 Quality Metrics:")
    quality = summary['quality_metrics']
    print(f"   🎯 Avg Confidence: {quality['average_confidence_score']:.2f}")
    print(f"   📊 Avg Completeness: {quality['average_completeness_score']:.2f}")
    print(f"   ⭐ High Confidence: {quality['high_confidence_executives']}")
    print(f"   ✅ Complete Profiles: {quality['complete_profiles']}")
    
    print(f"\n🔍 Discovery Methods:")
    for method, count in summary['discovery_methods'].items():
        print(f"   {method}: {count}")
    
    print(f"\n💾 Results saved to: {filename}")
    
    return final_results

if __name__ == "__main__":
    asyncio.run(comprehensive_executive_discovery_test()) 