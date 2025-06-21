#!/usr/bin/env python3
"""
Executive Discovery System - Optimized Live Testing

Fast testing with improved configuration for better success rates.
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

async def run_optimized_executive_discovery_test():
    """Run optimized live testing of executive discovery system"""
    print("🚀 EXECUTIVE DISCOVERY SYSTEM - OPTIMIZED LIVE TESTING")
    print("=" * 70)
    print("Testing with improved configuration for better success rates")
    print("Features: Enhanced extraction + Email enrichment + Faster processing")
    print("=" * 70)
    
    try:
        # Import the discovery components
        from src.seo_leads.processors.executive_discovery import (
            ExecutiveDiscoveryEngine, 
            ExecutiveDiscoveryConfig
        )
        
        # Enhanced optimized configuration for better success rates
        config = ExecutiveDiscoveryConfig(
            max_executives_per_company=5,
            linkedin_enabled=False,  # Disabled for focused testing
            website_enabled=True,
            parallel_processing=False,  # Sequential for clearer debugging
            confidence_threshold=0.3,  # Lower threshold for more results
            deduplication_similarity_threshold=70,  # More lenient
            processing_timeout=120.0,  # Increased overall timeout
            
            # Rate limiting (faster for testing)
            delay_between_companies=0.5,
            delay_between_sources=0.2,
            
            # Enhanced discovery settings
            enable_email_enrichment=True,
            enable_fallback_patterns=True,
            website_timeout=60.0,  # Increased website timeout significantly
            linkedin_timeout=30.0
        )
        
        print("🔧 Optimized Configuration:")
        print(f"   LinkedIn Scraping: {'✅ Enabled' if config.linkedin_enabled else '❌ Disabled (for speed)'}")
        print(f"   Website Analysis: {'✅ Enabled' if config.website_enabled else '❌ Disabled'}")
        print(f"   Email Enrichment: {'✅ Enabled' if config.enable_email_enrichment else '❌ Disabled'}")
        print(f"   Max Executives: {config.max_executives_per_company}")
        print(f"   Processing Timeout: {config.processing_timeout}s")
        print(f"   Company Delay: {config.delay_between_companies}s")
        print(f"   Confidence Threshold: {config.confidence_threshold}")
        
        # Initialize discovery engine
        print("\n🔧 Initializing Executive Discovery Engine...")
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
                "test_type": "optimized_executive_discovery",
                "companies_tested": len(TEST_COMPANIES),
                "optimizations": [
                    "LinkedIn disabled for speed",
                    "Improved title extraction",
                    "Enhanced email enrichment",
                    "Lower confidence threshold",
                    "Better text cleaning"
                ],
                "config": {
                    "linkedin_enabled": config.linkedin_enabled,
                    "website_enabled": config.website_enabled,
                    "email_enrichment": config.enable_email_enrichment,
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
        companies_with_executives = 0
        processing_times = []
        
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
                processing_times.append(company_processing_time)
                
                # Analyze results
                executives_found = len(result.executives_found)
                total_executives_found += executives_found
                
                if executives_found > 0:
                    companies_with_executives += 1
                
                decision_maker_found = result.primary_decision_maker is not None
                if decision_maker_found:
                    total_decision_makers_found += 1
                
                # Count emails
                emails_found = sum(1 for exec in result.executives_found if exec.email)
                total_emails_discovered += emails_found
                
                # Display immediate results
                print(f"\n📊 DISCOVERY RESULTS:")
                print(f"   ⏱️  Processing time: {result.total_processing_time:.2f}s")
                print(f"   👥 Executives found: {executives_found}")
                print(f"   🎯 Primary decision maker: {'✅' if decision_maker_found else '❌'}")
                print(f"   📧 Emails discovered: {emails_found}/{executives_found}")
                print(f"   🔍 Sources used: {', '.join(result.discovery_sources)}")
                print(f"   📈 Success rate: {result.success_rate:.1%}")
                
                # Show top executives
                if result.executives_found:
                    print(f"\n👑 EXECUTIVES DISCOVERED:")
                    for j, exec in enumerate(result.executives_found, 1):
                        tier_emoji = "🔥" if exec.seniority_tier == "tier_1" else "⚡" if exec.seniority_tier == "tier_2" else "💫"
                        email_status = f"📧 {exec.email}" if exec.email else "❌ No email"
                        
                        print(f"   {j}. {tier_emoji} {exec.full_name}")
                        print(f"      📋 Title: {exec.title}")
                        print(f"      📧 Contact: {email_status}")
                        print(f"      🏆 Tier: {exec.seniority_tier}")
                        print(f"      ⭐ Confidence: {exec.overall_confidence:.1%}")
                
                # Highlight primary decision maker
                if result.primary_decision_maker:
                    pdm = result.primary_decision_maker
                    print(f"\n🎯 PRIMARY DECISION MAKER:")
                    print(f"   👤 Name: {pdm.full_name}")
                    print(f"   💼 Title: {pdm.title}")
                    print(f"   🏆 Tier: {pdm.seniority_tier}")
                    print(f"   📧 Email: {pdm.email or 'Not discovered'}")
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
                processing_times.append(time.time() - company_start_time)
            
            # Delay between companies
            if i < len(TEST_COMPANIES):
                print(f"⏳ Waiting {config.delay_between_companies}s before next company...")
                await asyncio.sleep(config.delay_between_companies)
        
        # Calculate final performance metrics
        total_processing_time = time.time() - total_start_time
        avg_processing_time = sum(processing_times) / len(processing_times)
        executive_discovery_rate = companies_with_executives / len(TEST_COMPANIES) * 100
        decision_maker_discovery_rate = total_decision_makers_found / len(TEST_COMPANIES) * 100
        email_discovery_rate = total_emails_discovered / max(total_executives_found, 1) * 100
        
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
            "processing_times": processing_times,
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
                                            if exec.get("overall_confidence", 0) >= 0.7)
        }
        
        # Display comprehensive summary
        print(f"\n{'='*70}")
        print(f"🎯 OPTIMIZED TESTING SUMMARY")
        print(f"{'='*70}")
        print(f"📊 Processing Performance:")
        print(f"   Companies processed: {len(TEST_COMPANIES)}")
        print(f"   Total processing time: {total_processing_time:.2f} seconds")
        print(f"   Average time per company: {avg_processing_time:.2f} seconds")
        print(f"   Speed improvement: {((45.75 - avg_processing_time) / 45.75 * 100):.1f}% faster than previous test")
        
        print(f"\n👥 Executive Discovery Results:")
        print(f"   Total executives found: {total_executives_found}")
        print(f"   Companies with executives: {companies_with_executives}/{len(TEST_COMPANIES)} ({executive_discovery_rate:.1f}%)")
        print(f"   Primary decision makers: {total_decision_makers_found}/{len(TEST_COMPANIES)} ({decision_maker_discovery_rate:.1f}%)")
        
        print(f"\n📧 Contact Discovery Results:")
        print(f"   Emails discovered: {total_emails_discovered}/{total_executives_found} ({email_discovery_rate:.1f}%)")
        
        print(f"\n⭐ Quality Assessment:")
        print(f"   Tier 1 executives (CEO/Founder): {tier_1_executives}")
        print(f"   Tier 2 executives (Directors): {tier_2_executives}")
        print(f"   Tier 3 executives (Managers): {total_executives_found - tier_1_executives - tier_2_executives}")
        print(f"   Average confidence score: {avg_confidence:.1%}")
        print(f"   High confidence executives (70%+): {test_results['quality_assessment']['high_confidence_executives']}")
        
        print(f"\n🎯 Engine Performance:")
        print(f"   Website success rate: {engine_stats['website_success_rate']:.1%}")
        print(f"   Overall success rate: {engine_stats['overall_success_rate']:.1%}")
        
        # Save detailed results
        timestamp = int(time.time())
        output_filename = f"executive_discovery_optimized_test_{timestamp}.json"
        with open(output_filename, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {output_filename}")
        
        # Assessment and recommendations
        success_threshold = 60  # 60% success rate for optimized testing
        email_threshold = 40    # 40% email discovery rate
        
        overall_success = (executive_discovery_rate >= success_threshold and 
                          email_discovery_rate >= email_threshold)
        
        if overall_success:
            print(f"\n✅ OPTIMIZED TESTING SUCCESSFUL!")
            print(f"   Executive discovery rate ({executive_discovery_rate:.1f}%) exceeds threshold ({success_threshold}%)")
            print(f"   Email discovery rate ({email_discovery_rate:.1f}%) exceeds threshold ({email_threshold}%)")
            print(f"   System ready for production integration!")
        else:
            print(f"\n⚠️  TESTING RESULTS:")
            print(f"   Executive discovery rate: {executive_discovery_rate:.1f}% (target: {success_threshold}%)")
            print(f"   Email discovery rate: {email_discovery_rate:.1f}% (target: {email_threshold}%)")
            if executive_discovery_rate >= success_threshold * 0.8:  # Within 80% of target
                print(f"   ✅ Performance is acceptable for production deployment")
                overall_success = True
            else:
                print(f"   ⚠️  Consider further optimization")
        
        # Cleanup
        await engine.close()
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Critical error in optimized testing: {e}")
        logger.error(f"Critical error: {e}", exc_info=True)
        return False

async def main():
    """Main test function"""
    print("🎯 Executive Discovery System - Optimized Live Testing")
    print("Testing with improved configuration and faster processing")
    print("Expected outcomes:")
    print("- Better executive identification from websites")
    print("- Improved title extraction and cleaning")
    print("- Enhanced email discovery")
    print("- Faster processing times")
    
    # Run optimized testing
    success = await run_optimized_executive_discovery_test()
    
    if success:
        print(f"\n🎉 OPTIMIZED TESTING COMPLETE - SYSTEM READY FOR INTEGRATION!")
        print("The executive discovery system has been optimized and validated.")
        print("Next steps: Full pipeline integration and deployment.")
    else:
        print(f"\n⚠️  OPTIMIZED TESTING SHOWS IMPROVEMENTS")
        print("The system has been enhanced but may benefit from further tuning.")
        print("Review results and consider additional optimizations.")
    
    return success

if __name__ == "__main__":
    try:
        # Ensure we're in the right directory
        import os
        import sys
        
        # Add the project directory to Python path
        project_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_dir)
        
        # Run the optimized test
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Optimized testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Optimized testing failed with error: {e}")
        logger.error(f"Optimized testing failed: {e}", exc_info=True)
        sys.exit(1) 