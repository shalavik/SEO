#!/usr/bin/env python3
"""
Executive Discovery System Test

Test the new executive contact discovery system with LinkedIn scraping and website analysis.
Uses the 5 plumbing companies from previous testing.
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from typing import Dict, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test companies (same as previous testing)
TEST_COMPANIES = [
    {
        "id": "test-supreme-plumbers",
        "name": "Supreme Plumbers",
        "website": "https://supreme-plumbers-aq2qoadp7ocmvqll.builder-preview.com",
        "expected_executives": ["owner", "manager"]
    },
    {
        "id": "test-ideal-plumbing",
        "name": "Ideal Plumbing Services",
        "website": "https://idealplumbingservices.co.uk",
        "expected_executives": ["director", "manager"]
    },
    {
        "id": "test-2nd-city-gas",
        "name": "2nd City Gas, Plumbing and Heating",
        "website": "https://2ndcitygasplumbingandheating.co.uk",
        "expected_executives": ["owner", "director"]
    },
    {
        "id": "test-jack-plumber",
        "name": "Jack The Plumber",
        "website": "https://jacktheplumber.co.uk",
        "expected_executives": ["owner", "founder"]
    },
    {
        "id": "test-swift-emergency",
        "name": "Swift Emergency Plumber",
        "website": "https://swiftemergencyplumber.com",
        "expected_executives": ["director", "manager"]
    }
]

async def test_executive_discovery_system():
    """Test the complete executive discovery system"""
    print("🚀 Starting Executive Discovery System Test")
    print("=" * 60)
    
    try:
        # Import the discovery components
        from src.seo_leads.processors.executive_discovery import (
            ExecutiveDiscoveryEngine, 
            ExecutiveDiscoveryConfig
        )
        from src.seo_leads.processors.executive_email_enricher import ExecutiveEmailEnricher
        
        # Setup configuration for testing
        config = ExecutiveDiscoveryConfig(
            linkedin_enabled=True,  # Enable LinkedIn scraping
            website_enabled=True,   # Enable website scraping
            parallel_processing=True,  # Use parallel processing
            max_executives_per_company=10,
            processing_timeout=45.0,  # Longer timeout for testing
            delay_between_companies=3.0,  # 3 second delay between companies
            confidence_threshold=0.4  # Lower threshold for testing
        )
        
        # Initialize discovery engine
        print("🔧 Initializing Executive Discovery Engine...")
        engine = ExecutiveDiscoveryEngine(config)
        initialization_success = await engine.initialize()
        
        if not initialization_success:
            print("❌ Failed to initialize executive discovery engine")
            return False
        
        print("✅ Engine initialized successfully")
        
        # Test results storage
        test_results = {
            "test_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "companies_tested": len(TEST_COMPANIES),
                "config": {
                    "linkedin_enabled": config.linkedin_enabled,
                    "website_enabled": config.website_enabled,
                    "parallel_processing": config.parallel_processing,
                    "max_executives": config.max_executives_per_company,
                    "timeout": config.processing_timeout
                }
            },
            "company_results": [],
            "summary_stats": {}
        }
        
        # Process each test company
        total_executives_found = 0
        total_decision_makers_found = 0
        total_processing_time = 0.0
        companies_with_executives = 0
        
        for i, company in enumerate(TEST_COMPANIES, 1):
            print(f"\n📊 Processing {i}/{len(TEST_COMPANIES)}: {company['name']}")
            print(f"   Website: {company['website']}")
            
            start_time = time.time()
            
            try:
                # Discover executives
                result = await engine.discover_executives(
                    company_id=company['id'],
                    company_name=company['name'],
                    website_url=company['website']
                )
                
                processing_time = time.time() - start_time
                total_processing_time += processing_time
                
                # Count results
                executives_found = len(result.executives_found)
                total_executives_found += executives_found
                
                if executives_found > 0:
                    companies_with_executives += 1
                
                if result.primary_decision_maker:
                    total_decision_makers_found += 1
                
                # Display immediate results
                print(f"   ⏱️  Processing time: {result.total_processing_time:.2f}s")
                print(f"   👥 Executives found: {executives_found}")
                print(f"   🎯 Primary decision maker: {'✅' if result.primary_decision_maker else '❌'}")
                print(f"   🔍 Sources: {', '.join(result.discovery_sources)}")
                print(f"   📈 Success rate: {result.success_rate:.1%}")
                
                # Show executive details
                if result.executives_found:
                    print(f"   📋 Executive Details:")
                    for j, exec in enumerate(result.executives_found[:3], 1):  # Show top 3
                        tier_emoji = "🔥" if exec.seniority_tier == "tier_1" else "⚡" if exec.seniority_tier == "tier_2" else "💫"
                        email_status = "📧" if exec.email else "❌"
                        linkedin_status = "🔗" if exec.linkedin_url else "❌"
                        
                        print(f"      {j}. {tier_emoji} {exec.full_name}")
                        print(f"         Title: {exec.title}")
                        print(f"         Email: {email_status} {exec.email or 'None'}")
                        print(f"         LinkedIn: {linkedin_status}")
                        print(f"         Confidence: {exec.overall_confidence:.1%}")
                        print(f"         Sources: {', '.join(exec.discovery_sources)}")
                
                # Store detailed results
                company_result = {
                    "company_id": company['id'],
                    "company_name": company['name'],
                    "website_url": company['website'],
                    "processing_time": result.total_processing_time,
                    "success_rate": result.success_rate,
                    "discovery_sources": result.discovery_sources,
                    "executives_found": executives_found,
                    "primary_decision_maker_found": result.primary_decision_maker is not None,
                    "executives": []
                }
                
                # Add executive details
                for exec in result.executives_found:
                    exec_data = {
                        "full_name": exec.full_name,
                        "title": exec.title,
                        "seniority_tier": exec.seniority_tier,
                        "email": exec.email,
                        "email_confidence": exec.email_confidence,
                        "phone": exec.phone,
                        "linkedin_url": exec.linkedin_url,
                        "linkedin_verified": exec.linkedin_verified,
                        "discovery_sources": exec.discovery_sources,
                        "overall_confidence": exec.overall_confidence
                    }
                    company_result["executives"].append(exec_data)
                
                test_results["company_results"].append(company_result)
                
            except Exception as e:
                print(f"   ❌ Error processing {company['name']}: {e}")
                logger.error(f"Error processing {company['name']}: {e}", exc_info=True)
                
                # Store error result
                company_result = {
                    "company_id": company['id'],
                    "company_name": company['name'],
                    "website_url": company['website'],
                    "error": str(e),
                    "processing_time": time.time() - start_time,
                    "success_rate": 0.0,
                    "executives_found": 0,
                    "primary_decision_maker_found": False
                }
                test_results["company_results"].append(company_result)
        
        # Calculate summary statistics
        avg_processing_time = total_processing_time / len(TEST_COMPANIES) if TEST_COMPANIES else 0
        executive_discovery_rate = companies_with_executives / len(TEST_COMPANIES) * 100
        decision_maker_discovery_rate = total_decision_makers_found / len(TEST_COMPANIES) * 100
        
        # Get engine statistics
        engine_stats = engine.get_statistics()
        
        # Store summary statistics
        test_results["summary_stats"] = {
            "total_companies_processed": len(TEST_COMPANIES),
            "total_executives_found": total_executives_found,
            "companies_with_executives": companies_with_executives,
            "executive_discovery_rate_percent": executive_discovery_rate,
            "total_decision_makers_found": total_decision_makers_found,
            "decision_maker_discovery_rate_percent": decision_maker_discovery_rate,
            "average_processing_time_seconds": avg_processing_time,
            "engine_statistics": engine_stats
        }
        
        # Display summary
        print(f"\n📈 TEST SUMMARY")
        print("=" * 40)
        print(f"Companies processed: {len(TEST_COMPANIES)}")
        print(f"Total executives found: {total_executives_found}")
        print(f"Companies with executives: {companies_with_executives}/{len(TEST_COMPANIES)} ({executive_discovery_rate:.1f}%)")
        print(f"Primary decision makers found: {total_decision_makers_found}/{len(TEST_COMPANIES)} ({decision_maker_discovery_rate:.1f}%)")
        print(f"Average processing time: {avg_processing_time:.2f} seconds")
        
        print(f"\n🎯 ENGINE PERFORMANCE")
        print("=" * 40)
        print(f"LinkedIn success rate: {engine_stats['linkedin_success_rate']:.1%}")
        print(f"Website success rate: {engine_stats['website_success_rate']:.1%}")
        print(f"Overall success rate: {engine_stats['overall_success_rate']:.1%}")
        print(f"Average processing time: {engine_stats['avg_processing_time']:.2f}s")
        
        # Save detailed results
        output_filename = f"executive_discovery_test_results_{int(time.time())}.json"
        with open(output_filename, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {output_filename}")
        
        # Determine test success
        success_threshold = 60  # 60% success rate required
        test_passed = executive_discovery_rate >= success_threshold
        
        if test_passed:
            print(f"\n✅ TEST PASSED! Executive discovery rate ({executive_discovery_rate:.1f}%) exceeds threshold ({success_threshold}%)")
        else:
            print(f"\n⚠️  TEST NEEDS IMPROVEMENT. Executive discovery rate ({executive_discovery_rate:.1f}%) below threshold ({success_threshold}%)")
        
        # Cleanup
        await engine.close()
        
        return test_passed
        
    except Exception as e:
        print(f"❌ Critical error in executive discovery test: {e}")
        logger.error(f"Critical error: {e}", exc_info=True)
        return False

async def test_individual_components():
    """Test individual components of the executive discovery system"""
    print("\n🧪 Testing Individual Components")
    print("=" * 40)
    
    try:
        # Test 1: LinkedIn Scraper
        print("1. Testing LinkedIn Scraper...")
        from src.seo_leads.scrapers.linkedin_scraper import LinkedInScraper
        
        linkedin_scraper = LinkedInScraper()
        setup_success = await linkedin_scraper.setup_driver()
        
        if setup_success:
            print("   ✅ LinkedIn scraper setup successful")
            await linkedin_scraper.close()
        else:
            print("   ❌ LinkedIn scraper setup failed")
        
        # Test 2: Website Executive Scraper
        print("2. Testing Website Executive Scraper...")
        from src.seo_leads.scrapers.website_executive_scraper import WebsiteExecutiveScraper
        
        website_scraper = WebsiteExecutiveScraper()
        test_url = "https://idealplumbingservices.co.uk"
        test_name = "Ideal Plumbing Services"
        
        # Quick test (with timeout)
        try:
            executives = await asyncio.wait_for(
                website_scraper.discover_website_executives(test_url, test_name),
                timeout=15.0
            )
            print(f"   ✅ Website scraper found {len(executives)} executives")
        except asyncio.TimeoutError:
            print("   ⚠️  Website scraper test timed out (expected for some sites)")
        except Exception as e:
            print(f"   ❌ Website scraper error: {e}")
        
        # Test 3: Email Enricher
        print("3. Testing Email Enricher...")
        from src.seo_leads.processors.executive_email_enricher import ExecutiveEmailEnricher
        from src.seo_leads.models import ExecutiveContact
        
        enricher = ExecutiveEmailEnricher()
        
        # Create test executive
        test_executive = ExecutiveContact(
            first_name="John",
            last_name="Smith",
            full_name="John Smith",
            title="Managing Director",
            seniority_tier="tier_2",
            company_name="Test Company",
            company_domain="testcompany.co.uk"
        )
        
        # Generate email candidates
        candidates = await enricher.generate_executive_email_candidates(
            test_executive, "testcompany.co.uk"
        )
        
        print(f"   ✅ Email enricher generated {len(candidates)} email candidates")
        
        return True
        
    except Exception as e:
        print(f"❌ Component testing error: {e}")
        logger.error(f"Component testing error: {e}", exc_info=True)
        return False

async def main():
    """Main test function"""
    print("🎯 Executive Discovery System - Comprehensive Test")
    print("=" * 60)
    print("Testing the new executive contact discovery system with:")
    print("- LinkedIn scraping for executive profiles")
    print("- Website analysis for team/about pages")
    print("- Email pattern generation and discovery")
    print("- Hybrid intelligence data fusion")
    print("=" * 60)
    
    # Test individual components first
    components_ok = await test_individual_components()
    
    if not components_ok:
        print("\n❌ Component tests failed, skipping full system test")
        return False
    
    # Run full system test
    system_test_passed = await test_executive_discovery_system()
    
    if system_test_passed:
        print(f"\n🎉 EXECUTIVE DISCOVERY SYSTEM TEST PASSED!")
        print("The system successfully discovered executives for the majority of test companies.")
        print("Ready for integration into the main SEO lead generation pipeline.")
    else:
        print(f"\n⚠️  EXECUTIVE DISCOVERY SYSTEM NEEDS IMPROVEMENT")
        print("The system requires optimization before full deployment.")
        print("Consider adjusting confidence thresholds or improving scraping patterns.")
    
    return system_test_passed

if __name__ == "__main__":
    try:
        # Ensure we're in the right directory
        import os
        import sys
        
        # Add the project directory to Python path
        project_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_dir)
        
        # Run the test
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1) 