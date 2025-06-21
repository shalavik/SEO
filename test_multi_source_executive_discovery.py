#!/usr/bin/env python3
"""
Multi-Source Executive Discovery System Test

Tests the new Hybrid Intelligence Executive Discovery system with the 5 plumbing companies.
This test validates the transformation from 0% to 80%+ executive discovery success rate.

Features tested:
- Multi-source data fusion
- AI-powered name classification
- Contact enrichment pipeline
- Fallback strategy execution
- Performance optimization
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the new multi-source system
try:
    from src.seo_leads.processors.multi_source_executive_engine import MultiSourceExecutiveEngine
    MULTI_SOURCE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Multi-source engine not available: {e}")
    MULTI_SOURCE_AVAILABLE = False

# Fallback to existing system
from src.seo_leads.processors.executive_discovery import ExecutiveDiscoveryEngine

async def test_multi_source_discovery():
    """Test the new multi-source executive discovery system"""
    
    # Test companies (same 5 plumbing companies)
    companies = [
        {
            'id': 'test-gpj-plumbing',
            'name': 'GPJ Plumbing', 
            'url': 'http://gpj-plumbing.co.uk/',
            'domain': 'gpj-plumbing.co.uk'
        },
        {
            'id': 'test-emergency-plumber-services',
            'name': 'Emergency Plumber Services', 
            'url': 'https://www.emergencyplumber.services/',
            'domain': 'emergencyplumber.services'
        },
        {
            'id': 'test-247-plumbing-and-gas',
            'name': '247 Plumbing and Gas',
            'url': 'https://247plumbingandgas.co.uk/',
            'domain': '247plumbingandgas.co.uk'
        },
        {
            'id': 'test-hancox-gas-and-plumbing',
            'name': 'Hancox Gas and Plumbing',
            'url': 'http://www.hancoxgasandplumbing.co.uk/',
            'domain': 'hancoxgasandplumbing.co.uk'
        },
        {
            'id': 'test-metro-plumb-birmingham',
            'name': 'Metro Plumb Birmingham',
            'url': 'https://metroplumb.co.uk/locations/metro-plumb-birmingham/',
            'domain': 'metroplumb.co.uk'
        }
    ]
    
    print("🚀 MULTI-SOURCE EXECUTIVE DISCOVERY SYSTEM TEST")
    print("=" * 60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🏢 Companies: {len(companies)}")
    print(f"🎯 Target: Transform 0% → 80%+ executive discovery rate")
    print()
    
    # Initialize engines
    if MULTI_SOURCE_AVAILABLE:
        print("✅ Using NEW Multi-Source Executive Discovery Engine")
        engine = MultiSourceExecutiveEngine()
    else:
        print("⚠️  Using EXISTING Executive Discovery Engine (fallback)")
        engine = ExecutiveDiscoveryEngine()
        await engine.initialize()
    
    print()
    
    # Test results storage
    test_results = {
        'test_info': {
            'name': 'Multi-Source Executive Discovery Test',
            'timestamp': datetime.now().isoformat(),
            'engine_type': 'multi_source' if MULTI_SOURCE_AVAILABLE else 'existing',
            'total_companies': len(companies),
            'target_success_rate': 0.8,
            'target_executives_per_company': 2
        },
        'results': [],
        'summary': {}
    }
    
    total_start_time = time.time()
    total_executives_found = 0
    successful_companies = 0
    
    # Process each company
    for i, company in enumerate(companies, 1):
        print(f"🔍 [{i}/{len(companies)}] Processing: {company['name']}")
        print(f"   🌐 URL: {company['url']}")
        
        company_start_time = time.time()
        
        try:
            # Discover executives
            result = await engine.discover_executives(
                company['name'],  # company_name
                company['url']    # company_url
            )
            
            company_processing_time = time.time() - company_start_time
            
            # Count executives found (handle both result types)
            if hasattr(result, 'executives_found'):
                # Traditional ExecutiveDiscoveryResult
                executives_list = result.executives_found
                primary_decision_maker = result.primary_decision_maker
                discovery_sources = result.discovery_sources
                success_rate = result.success_rate
            else:
                # MultiSourceResult
                executives_list = result.executives
                primary_decision_maker = None  # Not available in MultiSourceResult yet
                discovery_sources = [source.value for source in result.sources_used]
                success_rate = result.success_rate
            
            executives_found = len(executives_list)
            total_executives_found += executives_found
            
            if executives_found > 0:
                successful_companies += 1
            
            # Analyze results
            print(f"   ✅ Completed in {company_processing_time:.2f}s")
            print(f"   👥 Executives found: {executives_found}")
            
            if executives_list:
                print("   📋 Executive Details:")
                for j, exec_contact in enumerate(executives_list[:3], 1):  # Show top 3
                    # Handle both ExecutiveContact and ExecutiveCandidate types
                    if hasattr(exec_contact, 'full_name'):
                        # ExecutiveContact
                        print(f"      {j}. {exec_contact.full_name}")
                        print(f"         Title: {exec_contact.title or 'N/A'}")
                        print(f"         Email: {exec_contact.email or 'N/A'}")
                        print(f"         Phone: {exec_contact.phone or 'N/A'}")
                        print(f"         LinkedIn: {'✓' if exec_contact.linkedin_url else '✗'}")
                        print(f"         Confidence: {exec_contact.confidence:.2f}")
                        print(f"         Seniority: {exec_contact.seniority_tier}")
                    else:
                        # ExecutiveCandidate
                        full_name = f"{exec_contact.first_name} {exec_contact.last_name}".strip()
                        print(f"      {j}. {full_name}")
                        print(f"         Title: {exec_contact.title or 'N/A'}")
                        print(f"         Email: {exec_contact.email or 'N/A'}")
                        print(f"         Phone: {exec_contact.phone or 'N/A'}")
                        print(f"         LinkedIn: {'✓' if exec_contact.linkedin_url else '✗'}")
                        print(f"         Confidence: {exec_contact.confidence:.2f}")
                        print(f"         Source: {exec_contact.source.value}")
                    print()
            else:
                print("   ❌ No executives found")
            
            # Store result
            company_result = {
                'company_id': company['id'],
                'company_name': company['name'],
                'company_domain': company['domain'],
                'website_url': company['url'],
                'executives_found': executives_found,
                'executives': [
                    {
                        'full_name': exec_contact.full_name if hasattr(exec_contact, 'full_name') else f"{exec_contact.first_name} {exec_contact.last_name}".strip(),
                        'first_name': exec_contact.first_name,
                        'last_name': exec_contact.last_name,
                        'title': exec_contact.title,
                        'email': exec_contact.email,
                        'phone': exec_contact.phone,
                        'linkedin_url': exec_contact.linkedin_url,
                        'seniority_tier': getattr(exec_contact, 'seniority_tier', 'unknown'),
                        'confidence': exec_contact.confidence,
                        'discovery_sources': getattr(exec_contact, 'discovery_sources', [exec_contact.source.value] if hasattr(exec_contact, 'source') else []),
                        'discovery_method': getattr(exec_contact, 'discovery_method', 'multi_source')
                    }
                    for exec_contact in executives_list
                ],
                'primary_decision_maker': {
                    'full_name': primary_decision_maker.full_name,
                    'title': primary_decision_maker.title,
                    'email': primary_decision_maker.email,
                    'phone': primary_decision_maker.phone,
                    'seniority_tier': primary_decision_maker.seniority_tier,
                    'confidence': primary_decision_maker.confidence
                } if primary_decision_maker else None,
                'discovery_sources': discovery_sources,
                'total_processing_time': company_processing_time,
                'success_rate': success_rate,
                'discovery_timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
            test_results['results'].append(company_result)
            
        except Exception as e:
            company_processing_time = time.time() - company_start_time
            print(f"   ❌ Error: {str(e)}")
            
            # Store error result
            error_result = {
                'company_id': company['id'],
                'company_name': company['name'],
                'company_domain': company['domain'],
                'website_url': company['url'],
                'executives_found': 0,
                'executives': [],
                'primary_decision_maker': None,
                'discovery_sources': [],
                'total_processing_time': company_processing_time,
                'success_rate': 0.0,
                'discovery_timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error_message': str(e)
            }
            
            test_results['results'].append(error_result)
        
        print()
    
    # Calculate final statistics
    total_processing_time = time.time() - total_start_time
    success_rate = successful_companies / len(companies)
    average_executives_per_company = total_executives_found / len(companies)
    average_processing_time = total_processing_time / len(companies)
    
    # Update summary
    test_results['summary'] = {
        'total_companies_processed': len(companies),
        'successful_companies': successful_companies,
        'failed_companies': len(companies) - successful_companies,
        'total_executives_found': total_executives_found,
        'companies_with_executives': successful_companies,
        'success_rate': success_rate,
        'average_executives_per_company': average_executives_per_company,
        'total_processing_time_seconds': total_processing_time,
        'average_processing_time_seconds': average_processing_time,
        'target_achievement': {
            'success_rate_target': 0.8,
            'success_rate_actual': success_rate,
            'success_rate_achievement': (success_rate / 0.8) * 100,
            'executives_target': 2.0,
            'executives_actual': average_executives_per_company,
            'executives_achievement': (average_executives_per_company / 2.0) * 100
        }
    }
    
    # Print final results
    print("📊 FINAL RESULTS SUMMARY")
    print("=" * 60)
    print(f"🏢 Companies Processed: {len(companies)}")
    print(f"✅ Successful Companies: {successful_companies}")
    print(f"❌ Failed Companies: {len(companies) - successful_companies}")
    print(f"👥 Total Executives Found: {total_executives_found}")
    print(f"📈 Success Rate: {success_rate:.1%} (Target: 80%)")
    print(f"📊 Avg Executives/Company: {average_executives_per_company:.1f} (Target: 2.0)")
    print(f"⏱️  Total Processing Time: {total_processing_time:.2f}s")
    print(f"⚡ Avg Processing Time: {average_processing_time:.2f}s/company")
    print()
    
    # Performance analysis
    if success_rate >= 0.8:
        print("🎉 SUCCESS: Target success rate achieved!")
    elif success_rate >= 0.5:
        print("⚠️  PARTIAL SUCCESS: Significant improvement but target not reached")
    else:
        print("❌ NEEDS IMPROVEMENT: Success rate below expectations")
    
    if average_executives_per_company >= 2.0:
        print("🎯 EXCELLENT: Executive discovery target exceeded!")
    elif average_executives_per_company >= 1.0:
        print("👍 GOOD: Solid executive discovery performance")
    else:
        print("📈 IMPROVING: Executive discovery needs enhancement")
    
    print()
    
    # Save results to file
    timestamp = int(time.time())
    filename = f"multi_source_executive_discovery_test_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    print(f"💾 Results saved to: {filename}")
    print()
    
    # Engine statistics
    if hasattr(engine, 'get_statistics'):
        stats = engine.get_statistics()
        print("🔧 ENGINE STATISTICS")
        print("=" * 30)
        for key, value in stats.items():
            print(f"{key}: {value}")
        print()
    
    return test_results

async def main():
    """Main test function"""
    try:
        results = await test_multi_source_discovery()
        
        # Print key insights
        print("🔍 KEY INSIGHTS")
        print("=" * 30)
        
        summary = results['summary']
        target_achievement = summary['target_achievement']
        
        print(f"Success Rate Achievement: {target_achievement['success_rate_achievement']:.1f}%")
        print(f"Executive Discovery Achievement: {target_achievement['executives_achievement']:.1f}%")
        
        if target_achievement['success_rate_achievement'] >= 100:
            print("✅ Multi-Source System: SUCCESS - Target achieved!")
        else:
            print("🔧 Multi-Source System: Needs further optimization")
        
        print()
        print("🚀 Next Steps:")
        if summary['success_rate'] < 0.8:
            print("1. Enhance LinkedIn scraping capabilities")
            print("2. Improve website executive extraction")
            print("3. Add more data sources")
            print("4. Optimize AI classification algorithms")
        else:
            print("1. System ready for production deployment")
            print("2. Monitor performance in real-world usage")
            print("3. Continue optimizing processing speed")
            print("4. Expand to additional industries")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 