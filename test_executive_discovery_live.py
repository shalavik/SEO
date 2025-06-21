#!/usr/bin/env python3
"""
Executive Discovery System - Live Testing

Real-world testing of the executive discovery system with the 5 plumbing companies.
Tests LinkedIn scraping, website analysis, and executive email discovery.
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from typing import Dict, List
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test companies (same as previous testing for comparison)
TEST_COMPANIES = [
    {
        "id": "supreme-plumbers",
        "name": "Supreme Plumbers",
        "website": "https://supreme-plumbers-aq2qoadp7ocmvqll.builder-preview.com",
        "sector": "plumbing",
        "location": "UK",
        "expected_executives": ["owner", "manager"],
        "priority": "high"
    },
    {
        "id": "ideal-plumbing",
        "name": "Ideal Plumbing Services", 
        "website": "https://idealplumbingservices.co.uk",
        "sector": "plumbing",
        "location": "UK",
        "expected_executives": ["director", "manager"],
        "priority": "high"
    },
    {
        "id": "2nd-city-gas",
        "name": "2nd City Gas, Plumbing and Heating",
        "website": "https://2ndcitygasplumbingandheating.co.uk", 
        "sector": "plumbing",
        "location": "UK",
        "expected_executives": ["owner", "director"],
        "priority": "medium"
    },
    {
        "id": "jack-plumber",
        "name": "Jack The Plumber",
        "website": "https://jacktheplumber.co.uk",
        "sector": "plumbing", 
        "location": "UK",
        "expected_executives": ["owner", "founder"],
        "priority": "high"
    },
    {
        "id": "swift-emergency",
        "name": "Swift Emergency Plumber",
        "website": "https://swiftemergencyplumber.com",
        "sector": "plumbing",
        "location": "UK", 
        "expected_executives": ["director", "manager"],
        "priority": "medium"
    }
]

async def run_live_executive_discovery_test():
    """Run comprehensive live testing of executive discovery system"""
    print("🚀 EXECUTIVE DISCOVERY SYSTEM - LIVE TESTING")
    print("=" * 70)
    print("Testing with 5 real UK plumbing companies")
    print("Features: LinkedIn scraping + Website analysis + Email discovery")
    print("=" * 70)
    
    try:
        # Import the discovery components
        from src.seo_leads.processors.executive_discovery import (
            ExecutiveDiscoveryEngine, 
            ExecutiveDiscoveryConfig
        )
        
        # Setup configuration for live testing
        config = ExecutiveDiscoveryConfig(
            linkedin_enabled=True,  # Enable LinkedIn scraping
            website_enabled=True,   # Enable website scraping
            parallel_processing=True,  # Use parallel processing for speed
            max_executives_per_company=8,  # Increase for thorough testing
            processing_timeout=60.0,  # Longer timeout for real websites
            delay_between_companies=4.0,  # 4 second delay to be respectful
            confidence_threshold=0.5,  # Lower threshold for testing
            deduplication_similarity_threshold=80  # Slightly more lenient
        )
        
        print("🔧 Initializing Executive Discovery Engine...")
        print(f"   LinkedIn Scraping: {'✅ Enabled' if config.linkedin_enabled else '❌ Disabled'}")
        print(f"   Website Analysis: {'✅ Enabled' if config.website_enabled else '❌ Disabled'}")
        print(f"   Parallel Processing: {'✅ Enabled' if config.parallel_processing else '❌ Disabled'}")
        print(f"   Max Executives: {config.max_executives_per_company}")
        print(f"   Processing Timeout: {config.processing_timeout}s")
        print(f"   Company Delay: {config.delay_between_companies}s")
        
        # Initialize discovery engine
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
                "test_type": "live_executive_discovery",
                "companies_tested": len(TEST_COMPANIES),
                "config": {
                    "linkedin_enabled": config.linkedin_enabled,
                    "website_enabled": config.website_enabled,
                    "parallel_processing": config.parallel_processing,
                    "max_executives": config.max_executives_per_company,
                    "timeout": config.processing_timeout,
                    "confidence_threshold": config.confidence_threshold
                }
            },
            "company_results": [],
            "executive_discoveries": [],
            "performance_metrics": {},
            "quality_assessment": {}
        }
        
        # Process each test company
        total_start_time = time.time()
        total_executives_found = 0
        total_decision_makers_found = 0
        total_emails_discovered = 0
        total_linkedin_profiles = 0
        companies_with_executives = 0
        source_success_rates = {"linkedin": 0, "website": 0, "hybrid": 0}
        
        for i, company in enumerate(TEST_COMPANIES, 1):
            print(f"\n{'='*20} TESTING {i}/{len(TEST_COMPANIES)} {'='*20}")
            print(f"🏢 Company: {company['name']}")
            print(f"🌐 Website: {company['website']}")
            print(f"🎯 Priority: {company['priority']}")
            print(f"📋 Expected: {', '.join(company['expected_executives'])}")
            
            company_start_time = time.time()
            
            try:
                # Discover executives
                print("🔍 Starting executive discovery...")
                result = await engine.discover_executives(
                    company_id=company['id'],
                    company_name=company['name'],
                    website_url=company['website']
                )
                
                company_processing_time = time.time() - company_start_time
                
                # Analyze results
                executives_found = len(result.executives_found)
                total_executives_found += executives_found
                
                if executives_found > 0:
                    companies_with_executives += 1
                
                decision_maker_found = result.primary_decision_maker is not None
                if decision_maker_found:
                    total_decision_makers_found += 1
                
                # Count emails and LinkedIn profiles
                emails_found = sum(1 for exec in result.executives_found if exec.email)
                linkedin_profiles = sum(1 for exec in result.executives_found if exec.linkedin_url)
                total_emails_discovered += emails_found
                total_linkedin_profiles += linkedin_profiles
                
                # Track source success
                if 'linkedin' in result.discovery_sources:
                    source_success_rates['linkedin'] += 1
                if 'website' in result.discovery_sources:
                    source_success_rates['website'] += 1
                if len(result.discovery_sources) > 1:
                    source_success_rates['hybrid'] += 1
                
                # Display immediate results
                print(f"\n📊 DISCOVERY RESULTS:")
                print(f"   ⏱️  Processing time: {result.total_processing_time:.2f}s")
                print(f"   👥 Executives found: {executives_found}")
                print(f"   🎯 Primary decision maker: {'✅' if decision_maker_found else '❌'}")
                print(f"   📧 Emails discovered: {emails_found}/{executives_found}")
                print(f"   🔗 LinkedIn profiles: {linkedin_profiles}/{executives_found}")
                print(f"   🔍 Sources used: {', '.join(result.discovery_sources)}")
                print(f"   📈 Success rate: {result.success_rate:.1%}")
                
                # Show top executives
                if result.executives_found:
                    print(f"\n👑 TOP EXECUTIVES DISCOVERED:")
                    for j, exec in enumerate(result.executives_found[:3], 1):
                        tier_emoji = "🔥" if exec.seniority_tier == "tier_1" else "⚡" if exec.seniority_tier == "tier_2" else "💫"
                        email_status = f"📧 {exec.email}" if exec.email else "❌ No email"
                        linkedin_status = "🔗 LinkedIn" if exec.linkedin_url else "❌ No LinkedIn"
                        
                        print(f"   {j}. {tier_emoji} {exec.full_name}")
                        print(f"      📋 Title: {exec.title}")
                        print(f"      📧 Contact: {email_status}")
                        print(f"      🔗 Profile: {linkedin_status}")
                        print(f"      ⭐ Confidence: {exec.overall_confidence:.1%}")
                        print(f"      🔍 Sources: {', '.join(exec.discovery_sources)}")
                
                # Highlight primary decision maker
                if result.primary_decision_maker:
                    pdm = result.primary_decision_maker
                    print(f"\n🎯 PRIMARY DECISION MAKER:")
                    print(f"   👤 Name: {pdm.full_name}")
                    print(f"   💼 Title: {pdm.title}")
                    print(f"   🏆 Tier: {pdm.seniority_tier}")
                    print(f"   📧 Email: {pdm.email or 'Not discovered'}")
                    print(f"   📱 Phone: {pdm.phone or 'Not discovered'}")
                    print(f"   🔗 LinkedIn: {'Yes' if pdm.linkedin_url else 'No'}")
                    print(f"   ⭐ Confidence: {pdm.overall_confidence:.1%}")
                
                # Store detailed results
                company_result = {
                    "company_info": company,
                    "discovery_result": {
                        "processing_time": result.total_processing_time,
                        "success_rate": result.success_rate,
                        "discovery_sources": result.discovery_sources,
                        "executives_found": executives_found,
                        "emails_discovered": emails_found,
                        "linkedin_profiles": linkedin_profiles,
                        "primary_decision_maker_found": decision_maker_found
                    },
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
                        "overall_confidence": exec.overall_confidence,
                        "data_completeness_score": exec.data_completeness_score
                    }
                    company_result["executives"].append(exec_data)
                    test_results["executive_discoveries"].append({
                        "company_name": company['name'],
                        **exec_data
                    })
                
                test_results["company_results"].append(company_result)
                print(f"✅ {company['name']} processing complete")
                
            except Exception as e:
                print(f"❌ Error processing {company['name']}: {e}")
                logger.error(f"Error processing {company['name']}: {e}", exc_info=True)
                
                # Store error result
                error_result = {
                    "company_info": company,
                    "error": str(e),
                    "processing_time": time.time() - company_start_time,
                    "success_rate": 0.0,
                    "executives_found": 0,
                    "primary_decision_maker_found": False
                }
                test_results["company_results"].append(error_result)
            
            # Delay between companies (be respectful)
            if i < len(TEST_COMPANIES):
                print(f"⏳ Waiting {config.delay_between_companies}s before next company...")
                await asyncio.sleep(config.delay_between_companies)
        
        # Calculate final performance metrics
        total_processing_time = time.time() - total_start_time
        avg_processing_time = total_processing_time / len(TEST_COMPANIES)
        executive_discovery_rate = companies_with_executives / len(TEST_COMPANIES) * 100
        decision_maker_discovery_rate = total_decision_makers_found / len(TEST_COMPANIES) * 100
        email_discovery_rate = total_emails_discovered / max(total_executives_found, 1) * 100
        linkedin_discovery_rate = total_linkedin_profiles / max(total_executives_found, 1) * 100
        
        # Get engine statistics
        engine_stats = engine.get_statistics()
        
        # Store performance metrics
        test_results["performance_metrics"] = {
            "total_processing_time": total_processing_time,
            "avg_processing_time_per_company": avg_processing_time,
            "total_executives_found": total_executives_found,
            "companies_with_executives": companies_with_executives,
            "executive_discovery_rate_percent": executive_discovery_rate,
            "decision_maker_discovery_rate_percent": decision_maker_discovery_rate,
            "email_discovery_rate_percent": email_discovery_rate,
            "linkedin_discovery_rate_percent": linkedin_discovery_rate,
            "source_success_rates": {
                "linkedin_success": source_success_rates['linkedin'],
                "website_success": source_success_rates['website'], 
                "hybrid_success": source_success_rates['hybrid']
            },
            "engine_statistics": engine_stats
        }
        
        # Quality assessment
        tier_1_executives = sum(1 for result in test_results["company_results"] 
                               for exec in result.get("executives", []) 
                               if exec.get("seniority_tier") == "tier_1")
        tier_2_executives = sum(1 for result in test_results["company_results"]
                               for exec in result.get("executives", [])
                               if exec.get("seniority_tier") == "tier_2")
        
        avg_confidence = sum(exec.get("overall_confidence", 0) 
                           for result in test_results["company_results"]
                           for exec in result.get("executives", [])) / max(total_executives_found, 1)
        
        test_results["quality_assessment"] = {
            "tier_1_executives_found": tier_1_executives,
            "tier_2_executives_found": tier_2_executives,
            "tier_3_executives_found": total_executives_found - tier_1_executives - tier_2_executives,
            "average_confidence_score": avg_confidence,
            "high_confidence_executives": sum(1 for result in test_results["company_results"]
                                            for exec in result.get("executives", [])
                                            if exec.get("overall_confidence", 0) >= 0.8)
        }
        
        # Display comprehensive summary
        print(f"\n{'='*70}")
        print(f"🎯 LIVE TESTING SUMMARY")
        print(f"{'='*70}")
        print(f"📊 Processing Performance:")
        print(f"   Companies processed: {len(TEST_COMPANIES)}")
        print(f"   Total processing time: {total_processing_time:.2f} seconds")
        print(f"   Average time per company: {avg_processing_time:.2f} seconds")
        
        print(f"\n👥 Executive Discovery Results:")
        print(f"   Total executives found: {total_executives_found}")
        print(f"   Companies with executives: {companies_with_executives}/{len(TEST_COMPANIES)} ({executive_discovery_rate:.1f}%)")
        print(f"   Primary decision makers: {total_decision_makers_found}/{len(TEST_COMPANIES)} ({decision_maker_discovery_rate:.1f}%)")
        
        print(f"\n📧 Contact Discovery Results:")
        print(f"   Emails discovered: {total_emails_discovered}/{total_executives_found} ({email_discovery_rate:.1f}%)")
        print(f"   LinkedIn profiles: {total_linkedin_profiles}/{total_executives_found} ({linkedin_discovery_rate:.1f}%)")
        
        print(f"\n🔍 Source Performance:")
        print(f"   LinkedIn successful: {source_success_rates['linkedin']}/{len(TEST_COMPANIES)} companies")
        print(f"   Website successful: {source_success_rates['website']}/{len(TEST_COMPANIES)} companies")
        print(f"   Hybrid success: {source_success_rates['hybrid']}/{len(TEST_COMPANIES)} companies")
        
        print(f"\n⭐ Quality Assessment:")
        print(f"   Tier 1 executives (CEO/Founder): {tier_1_executives}")
        print(f"   Tier 2 executives (Directors): {tier_2_executives}")
        print(f"   Tier 3 executives (Managers): {total_executives_found - tier_1_executives - tier_2_executives}")
        print(f"   Average confidence score: {avg_confidence:.1%}")
        print(f"   High confidence executives (80%+): {test_results['quality_assessment']['high_confidence_executives']}")
        
        print(f"\n🎯 Engine Performance:")
        print(f"   LinkedIn success rate: {engine_stats['linkedin_success_rate']:.1%}")
        print(f"   Website success rate: {engine_stats['website_success_rate']:.1%}")
        print(f"   Overall success rate: {engine_stats['overall_success_rate']:.1%}")
        
        # Save detailed results
        timestamp = int(time.time())
        output_filename = f"executive_discovery_live_test_{timestamp}.json"
        with open(output_filename, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {output_filename}")
        
        # Assessment and recommendations
        success_threshold = 70  # 70% success rate for live testing
        email_threshold = 50    # 50% email discovery rate
        
        overall_success = (executive_discovery_rate >= success_threshold and 
                          email_discovery_rate >= email_threshold)
        
        if overall_success:
            print(f"\n✅ LIVE TESTING SUCCESSFUL!")
            print(f"   Executive discovery rate ({executive_discovery_rate:.1f}%) exceeds threshold ({success_threshold}%)")
            print(f"   Email discovery rate ({email_discovery_rate:.1f}%) exceeds threshold ({email_threshold}%)")
            print(f"   System ready for production deployment!")
        else:
            print(f"\n⚠️  LIVE TESTING NEEDS OPTIMIZATION")
            if executive_discovery_rate < success_threshold:
                print(f"   Executive discovery rate ({executive_discovery_rate:.1f}%) below threshold ({success_threshold}%)")
            if email_discovery_rate < email_threshold:
                print(f"   Email discovery rate ({email_discovery_rate:.1f}%) below threshold ({email_threshold}%)")
            print(f"   Recommendations:")
            print(f"   - Tune confidence thresholds")
            print(f"   - Enhance email pattern generation")
            print(f"   - Improve LinkedIn scraping robustness")
        
        # Cleanup
        await engine.close()
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Critical error in live testing: {e}")
        logger.error(f"Critical error: {e}", exc_info=True)
        return False

async def main():
    """Main test function"""
    print("🎯 Executive Discovery System - Live Testing with Real Companies")
    print("Testing the complete executive contact discovery pipeline")
    print("Expected outcomes:")
    print("- Executive identification from LinkedIn + websites")
    print("- Role-specific email discovery")
    print("- Primary decision maker identification")
    print("- Quality confidence scoring")
    
    # Run live testing
    success = await run_live_executive_discovery_test()
    
    if success:
        print(f"\n🎉 LIVE TESTING COMPLETE - SYSTEM READY FOR PRODUCTION!")
        print("The executive discovery system has been validated with real companies.")
        print("Next steps: Full pipeline integration and deployment.")
    else:
        print(f"\n⚠️  LIVE TESTING REQUIRES OPTIMIZATION")
        print("The system needs tuning before production deployment.")
        print("Review results and adjust configuration parameters.")
    
    return success

if __name__ == "__main__":
    try:
        # Ensure we're in the right directory
        import os
        import sys
        
        # Add the project directory to Python path
        project_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_dir)
        
        # Run the live test
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Live testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Live testing failed with error: {e}")
        logger.error(f"Live testing failed: {e}", exc_info=True)
        sys.exit(1) 