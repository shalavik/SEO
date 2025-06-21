#!/usr/bin/env python3
"""
Enhanced Executive Discovery System - Comprehensive Test

Tests the new zero-cost executive enrichment system using:
- Companies House API (FREE UK government data)
- Google Search intelligence (FREE search)
- Website scraping (enhanced fallback strategies)

Target: 80%+ executive discovery rate with £0.00 cost
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from seo_leads.processors.enhanced_executive_discovery import (
    EnhancedExecutiveDiscoveryEngine, 
    EnhancedDiscoveryConfig
)

# Test companies
TEST_COMPANIES = [
    {
        "id": "jack-the-plumber",
        "name": "Jack The Plumber",
        "website": "https://jacktheplumber.co.uk",
        "sector": "plumbing",
        "location": "UK",
        "expected_executives": ["Jack", "owner"]
    },
    {
        "id": "ideal-plumbing",
        "name": "Ideal Plumbing Services",
        "website": "https://idealplumbingservices.co.uk",
        "sector": "plumbing", 
        "location": "UK",
        "expected_executives": ["director", "manager"]
    }
]

async def test_enhanced_executive_discovery():
    """Test the enhanced executive discovery system"""
    
    logger.info("🚀 Starting Enhanced Executive Discovery System Test")
    logger.info("=" * 80)
    
    # Enhanced configuration for maximum success rate
    config = EnhancedDiscoveryConfig(
        max_executives_per_company=5,
        
        # Enable all FREE data sources
        companies_house_enabled=True,
        google_search_enabled=True,
        website_enabled=True,
        
        # Optimized processing settings
        parallel_processing=True,
        confidence_threshold=0.3,
        deduplication_similarity_threshold=75,
        processing_timeout=90.0,
        
        # Rate limiting
        delay_between_companies=2.0,
        delay_between_sources=1.0,
        
        # Email enrichment
        enable_email_enrichment=True,
        enable_email_validation=False,
        
        # Quality settings
        min_data_completeness=0.2,
        prioritize_tier_1_executives=True
    )
    
    # Initialize the enhanced discovery engine
    engine = EnhancedExecutiveDiscoveryEngine(config)
    
    try:
        # Initialize all data sources
        logger.info("🔧 Initializing Enhanced Executive Discovery Engine...")
        initialization_success = await engine.initialize()
        
        if not initialization_success:
            logger.error("❌ Failed to initialize discovery engine")
            return
        
        logger.info("✅ Enhanced discovery engine initialized successfully")
        logger.info("")
        
        # Test results storage
        test_results = {
            'test_metadata': {
                'test_name': 'Enhanced Executive Discovery System Test',
                'test_date': datetime.utcnow().isoformat(),
                'companies_tested': len(TEST_COMPANIES),
                'data_sources': ['companies_house', 'google_search', 'website_scraping'],
                'cost': '£0.00 (FREE)',
                'target_success_rate': '80%+'
            },
            'company_results': [],
            'overall_statistics': {}
        }
        
        # Process each company
        total_start_time = time.time()
        
        for i, company in enumerate(TEST_COMPANIES, 1):
            logger.info(f"🔍 Testing Company {i}/{len(TEST_COMPANIES)}: {company['name']}")
            logger.info(f"   Website: {company['website']}")
            
            company_start_time = time.time()
            
            try:
                # Discover executives using enhanced system
                result = await engine.discover_executives(
                    company_name=company['name'],
                    website_url=company['website'],
                    company_id=company['id']
                )
                
                company_processing_time = time.time() - company_start_time
                
                # Analyze results
                executives_found = len(result.executives)
                success_rate = (executives_found / 5) * 100
                
                # Log results
                logger.info(f"   ✅ Discovery Complete:")
                logger.info(f"      📊 Executives Found: {executives_found}")
                logger.info(f"      📈 Success Rate: {success_rate:.1f}%")
                logger.info(f"      ⏱️  Processing Time: {company_processing_time:.2f}s")
                logger.info(f"      🔗 Data Sources Used: {len(result.discovery_sources)}")
                
                # Log individual executives
                if result.executives:
                    logger.info(f"      👥 Executives Discovered:")
                    for j, exec in enumerate(result.executives, 1):
                        sources = ', '.join(exec.discovery_sources)
                        confidence = f"{exec.overall_confidence:.1%}"
                        
                        logger.info(f"         {j}. {exec.full_name} - {exec.title}")
                        logger.info(f"            Tier: {exec.seniority_tier} | Confidence: {confidence}")
                        logger.info(f"            Sources: {sources}")
                        
                        if exec.email:
                            logger.info(f"            📧 Email: {exec.email}")
                        if exec.linkedin_url:
                            logger.info(f"            🔗 LinkedIn: {exec.linkedin_url}")
                
                # Store company results
                company_result = {
                    'company_id': company['id'],
                    'company_name': company['name'],
                    'website': company['website'],
                    'executives_found': executives_found,
                    'success_rate': success_rate,
                    'processing_time_seconds': company_processing_time,
                    'data_sources_used': result.discovery_sources,
                    'executives': [
                        {
                            'name': exec.full_name,
                            'title': exec.title,
                            'seniority_tier': exec.seniority_tier,
                            'email': exec.email,
                            'linkedin_url': exec.linkedin_url,
                            'confidence': exec.overall_confidence,
                            'discovery_sources': exec.discovery_sources
                        }
                        for exec in result.executives
                    ]
                }
                
                test_results['company_results'].append(company_result)
                
            except Exception as e:
                logger.error(f"   ❌ Error processing {company['name']}: {e}")
                
                # Store error result
                company_result = {
                    'company_id': company['id'],
                    'company_name': company['name'],
                    'website': company['website'],
                    'executives_found': 0,
                    'success_rate': 0.0,
                    'processing_time_seconds': time.time() - company_start_time,
                    'error': str(e)
                }
                test_results['company_results'].append(company_result)
            
            logger.info("")
            
            # Rate limiting between companies
            if i < len(TEST_COMPANIES):
                await asyncio.sleep(config.delay_between_companies)
        
        # Calculate overall statistics
        total_processing_time = time.time() - total_start_time
        
        # Calculate success metrics
        successful_companies = sum(1 for r in test_results['company_results'] if r.get('executives_found', 0) > 0)
        total_executives_found = sum(r.get('executives_found', 0) for r in test_results['company_results'])
        overall_success_rate = (successful_companies / len(TEST_COMPANIES)) * 100
        
        # Store overall statistics
        test_results['overall_statistics'] = {
            'total_companies_tested': len(TEST_COMPANIES),
            'successful_companies': successful_companies,
            'overall_success_rate': f"{overall_success_rate:.1f}%",
            'total_executives_found': total_executives_found,
            'total_processing_time_seconds': total_processing_time,
            'cost_analysis': {
                'total_cost': '£0.00',
                'cost_per_company': '£0.00',
                'cost_per_executive': '£0.00'
            }
        }
        
        # Print final summary
        logger.info("🎯 ENHANCED EXECUTIVE DISCOVERY TEST RESULTS")
        logger.info("=" * 80)
        logger.info(f"📊 Overall Success Rate: {overall_success_rate:.1f}% ({successful_companies}/{len(TEST_COMPANIES)} companies)")
        logger.info(f"👥 Total Executives Found: {total_executives_found}")
        logger.info(f"⏱️  Total Processing Time: {total_processing_time:.2f}s")
        logger.info(f"💰 Total Cost: £0.00 (FREE)")
        
        # Save results to file
        results_file = f"enhanced_executive_discovery_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        logger.info(f"📄 Results saved to: {results_file}")
        
        return test_results
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return None
    
    finally:
        # Clean up
        await engine.close()

if __name__ == "__main__":
    # Run the test
    results = asyncio.run(test_enhanced_executive_discovery())
    
    if results:
        print("\n🎉 Enhanced Executive Discovery Test Completed Successfully!")
        print(f"📊 Overall Success Rate: {results['overall_statistics']['overall_success_rate']}")
        print(f"👥 Total Executives Found: {results['overall_statistics']['total_executives_found']}")
        print(f"💰 Total Cost: {results['overall_statistics']['cost_analysis']['total_cost']}")
    else:
        print("\n❌ Enhanced Executive Discovery Test Failed!")
        sys.exit(1) 