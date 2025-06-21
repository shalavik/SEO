#!/usr/bin/env python3
"""
Direct Executive Discovery Module Test

Tests the executive discovery engine directly for the 5 specified URLs.
"""

import asyncio
import json
import time
from datetime import datetime
from src.seo_leads.processors.executive_discovery import ExecutiveDiscoveryEngine

async def run_executive_discovery():
    """Run executive discovery for the 5 specified companies"""
    
    companies = [
        {
            'name': 'GPJ Plumbing', 
            'url': 'http://gpj-plumbing.co.uk/', 
            'domain': 'gpj-plumbing.co.uk'
        },
        {
            'name': 'Emergency Plumber Services', 
            'url': 'https://www.emergencyplumber.services/', 
            'domain': 'emergencyplumber.services'
        },
        {
            'name': '247 Plumbing and Gas', 
            'url': 'https://247plumbingandgas.co.uk/', 
            'domain': '247plumbingandgas.co.uk'
        },
        {
            'name': 'Hancox Gas and Plumbing', 
            'url': 'http://www.hancoxgasandplumbing.co.uk/', 
            'domain': 'hancoxgasandplumbing.co.uk'
        },
        {
            'name': 'Metro Plumb Birmingham', 
            'url': 'https://metroplumb.co.uk/locations/metro-plumb-birmingham/', 
            'domain': 'metroplumb.co.uk'
        }
    ]
    
    print("🚀 Starting Executive Discovery Module Test")
    print(f"📊 Processing {len(companies)} companies...")
    
    engine = ExecutiveDiscoveryEngine()
    results = []
    start_time = time.time()
    
    for i, company in enumerate(companies, 1):
        print(f"\n📍 Processing {i}/{len(companies)}: {company['name']}")
        print(f"🔗 URL: {company['url']}")
        
        company_start_time = time.time()
        
        try:
            result = await engine.discover_executives(
                company_id=f"test-{company['name'].lower().replace(' ', '-')}",
                company_name=company['name'],
                website_url=company['url']
            )
            
            # Convert to dict for JSON serialization
            result_dict = {
                'company_id': result.company_id,
                'company_name': result.company_name,
                'company_domain': result.company_domain,
                'website_url': company['url'],
                'executives_found': len(result.executives_found),
                'executives': []
            }
            
            # Add executive details
            for exec in result.executives_found:
                exec_dict = {
                    'first_name': exec.first_name,
                    'last_name': exec.last_name,
                    'full_name': exec.full_name,
                    'title': exec.title,
                    'seniority_tier': exec.seniority_tier,
                    'email': exec.email,
                    'email_confidence': exec.email_confidence,
                    'phone': exec.phone,
                    'phone_confidence': exec.phone_confidence,
                    'linkedin_url': exec.linkedin_url,
                    'linkedin_verified': exec.linkedin_verified,
                    'overall_confidence': exec.overall_confidence,
                    'discovery_sources': exec.discovery_sources,
                    'discovery_method': exec.discovery_method,
                    'data_completeness_score': exec.data_completeness_score
                }
                result_dict['executives'].append(exec_dict)
            
            # Add primary decision maker
            if result.primary_decision_maker:
                result_dict['primary_decision_maker'] = {
                    'first_name': result.primary_decision_maker.first_name,
                    'last_name': result.primary_decision_maker.last_name,
                    'full_name': result.primary_decision_maker.full_name,
                    'title': result.primary_decision_maker.title,
                    'seniority_tier': result.primary_decision_maker.seniority_tier,
                    'email': result.primary_decision_maker.email,
                    'email_confidence': result.primary_decision_maker.email_confidence,
                    'phone': result.primary_decision_maker.phone,
                    'linkedin_url': result.primary_decision_maker.linkedin_url,
                    'overall_confidence': result.primary_decision_maker.overall_confidence
                }
            else:
                result_dict['primary_decision_maker'] = None
            
            # Add metadata
            result_dict.update({
                'discovery_sources': result.discovery_sources,
                'total_processing_time': result.total_processing_time,
                'success_rate': result.success_rate,
                'discovery_timestamp': result.discovery_timestamp.isoformat(),
                'status': 'success'
            })
            
            results.append(result_dict)
            
            processing_time = time.time() - company_start_time
            print(f"✅ Found {len(result.executives_found)} executives in {processing_time:.2f}s")
            
            # Print executive details
            if result.executives_found:
                print("👔 Executives discovered:")
                for exec in result.executives_found:
                    print(f"   • {exec.full_name} - {exec.title} ({exec.seniority_tier})")
                    if exec.email:
                        print(f"     📧 {exec.email} (confidence: {exec.email_confidence:.2f})")
                    if exec.phone:
                        print(f"     📞 {exec.phone}")
                    if exec.linkedin_url:
                        print(f"     🔗 {exec.linkedin_url}")
            else:
                print("   No executives found")
                
        except Exception as e:
            print(f"❌ Error processing {company['name']}: {e}")
            processing_time = time.time() - company_start_time
            results.append({
                'company_name': company['name'],
                'website_url': company['url'],
                'company_domain': company['domain'],
                'executives_found': 0,
                'executives': [],
                'primary_decision_maker': None,
                'processing_time_seconds': processing_time,
                'error': str(e),
                'status': 'failed'
            })
    
    # Generate final results
    total_time = time.time() - start_time
    successful_results = [r for r in results if r.get('status') == 'success']
    total_executives = sum(r.get('executives_found', 0) for r in results)
    
    final_results = {
        'test_info': {
            'name': 'Executive Discovery Module Test',
            'timestamp': datetime.now().isoformat(),
            'total_companies': len(companies),
            'total_processing_time_seconds': total_time,
            'average_time_per_company': total_time / len(companies)
        },
        'summary': {
            'successful_processes': len(successful_results),
            'failed_processes': len(results) - len(successful_results),
            'total_executives_found': total_executives,
            'companies_with_executives': len([r for r in results if r.get('executives_found', 0) > 0]),
            'average_executives_per_company': total_executives / len(results) if results else 0
        },
        'results': results
    }
    
    # Save results
    timestamp = int(time.time())
    filename = f"executive_discovery_direct_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(final_results, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "="*60)
    print("🎉 EXECUTIVE DISCOVERY MODULE TEST COMPLETE")
    print("📊 Results Summary:")
    print(f"   ✅ Successful: {len(successful_results)}")
    print(f"   ❌ Failed: {len(results) - len(successful_results)}")
    print(f"   👔 Total Executives Found: {total_executives}")
    print(f"   🏢 Companies with Executives: {len([r for r in results if r.get('executives_found', 0) > 0])}")
    print(f"   📈 Average Executives per Company: {total_executives / len(results):.1f}")
    print(f"   ⏱️  Total Time: {total_time:.2f}s")
    print(f"   📄 Results saved to: {filename}")
    print("="*60)
    
    # Print JSON results
    print("\n🔍 FINAL JSON RESULTS:")
    print(json.dumps(final_results, indent=2, default=str))
    
    return final_results

if __name__ == "__main__":
    asyncio.run(run_executive_discovery()) 