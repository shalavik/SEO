#!/usr/bin/env python3
"""
Test Enhanced Executive Discovery + SEO Analysis Pipeline
Tests 5 plumbing companies with full SEO classification and executive enrichment
Outputs results in JSON format for analysis
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test imports
from src.seo_leads.processors.enhanced_executive_discovery import EnhancedExecutiveDiscoveryEngine
from src.seo_leads.analyzers.seo_analyzer import SEOAnalyzer
from src.seo_leads.processors.lead_qualifier import LeadQualifier
from src.seo_leads.models import ExecutiveContact

async def test_full_pipeline_5_companies():
    """Test the complete pipeline with 5 plumbing companies"""
    
    print("\n" + "="*80)
    print("🚀 TESTING ENHANCED PIPELINE: 5 PLUMBING COMPANIES")
    print("="*80)
    
    # Test companies from user's request
    test_companies = [
        {
            'name': 'MK Plumbing Birmingham',
            'website': 'https://mkplumbingbirmingham.co.uk/',
            'sector': 'plumbing',
            'city': 'Birmingham',
            'region': 'West Midlands'
        },
        {
            'name': 'Rescue Plumbing & Gas Ltd',
            'website': 'http://www.rescueplumbing.co.uk/',
            'sector': 'plumbing',
            'city': 'Birmingham',
            'region': 'West Midlands'
        },
        {
            'name': 'GD Plumbing & Heating Services Ltd',
            'website': 'https://www.gdplumbingandheatingservices.co.uk/',
            'sector': 'plumbing',
            'city': 'Birmingham',
            'region': 'West Midlands'
        },
        {
            'name': 'Matt Plumbing and Heating',
            'website': 'http://www.mattplumbingandheating.com/',
            'sector': 'plumbing',
            'city': 'Birmingham',
            'region': 'West Midlands'
        },
        {
            'name': 'Summit Plumbing and Heating',
            'website': 'http://summitplumbingandheating.co.uk/',
            'sector': 'plumbing',
            'city': 'Birmingham',
            'region': 'West Midlands'
        }
    ]
    
    # Initialize components
    print("🔧 Initializing pipeline components...")
    discovery_engine = EnhancedExecutiveDiscoveryEngine()
    await discovery_engine.initialize()
    
    seo_analyzer = SEOAnalyzer()
    lead_qualifier = LeadQualifier()
    
    # Results storage
    results = {
        "test_metadata": {
            "test_name": "Enhanced Pipeline Test - 5 Plumbing Companies",
            "test_date": datetime.utcnow().isoformat(),
            "companies_tested": len(test_companies),
            "pipeline_components": [
                "Enhanced Executive Discovery",
                "SEO Analysis",
                "Lead Qualification"
            ]
        },
        "companies": [],
        "summary": {
            "total_companies": len(test_companies),
            "executives_found": 0,
            "average_seo_score": 0.0,
            "lead_distribution": {"A": 0, "B": 0, "C": 0, "D": 0},
            "total_processing_time": 0.0,
            "success_rate": 0.0
        }
    }
    
    total_start_time = time.time()
    total_executives_found = 0
    total_seo_score = 0.0
    
    print(f"\n📊 Processing {len(test_companies)} companies...")
    
    for i, company in enumerate(test_companies, 1):
        print(f"\n{'='*60}")
        print(f"🏢 COMPANY {i}/{len(test_companies)}: {company['name']}")
        print(f"🌐 Website: {company['website']}")
        print(f"{'='*60}")
        
        company_start_time = time.time()
        company_result = {
            "company_info": company,
            "processing_time": 0.0,
            "executives": [],
            "seo_analysis": {},
            "lead_qualification": {},
            "status": "processing",
            "errors": []
        }
        
        try:
            # 1. Executive Discovery
            print("🔍 Step 1: Executive Discovery...")
            exec_start_time = time.time()
            
            discovery_result = await discovery_engine.discover_executives(
                company_name=company['name'],
                website_url=company['website']
            )
            
            exec_processing_time = time.time() - exec_start_time
            executives = discovery_result.executives_found
            
            print(f"   👥 Executives Found: {len(executives)}")
            total_executives_found += len(executives)
            
            # Convert executives to JSON-serializable format
            executives_json = []
            for exec in executives:
                exec_data = {
                    "full_name": exec.full_name,
                    "title": exec.title,
                    "seniority_tier": exec.seniority_tier,
                    "email": exec.email,
                    "phone": exec.phone,
                    "linkedin_url": exec.linkedin_url,
                    "confidence": exec.overall_confidence,
                    "data_completeness": exec.data_completeness_score,
                    "discovery_sources": exec.discovery_sources,
                    "discovery_method": exec.discovery_method
                }
                executives_json.append(exec_data)
            
            company_result["executives"] = executives_json
            company_result["executive_discovery"] = {
                "executives_found": len(executives),
                "processing_time": exec_processing_time,
                "primary_decision_maker": discovery_result.primary_decision_maker.full_name if discovery_result.primary_decision_maker else None,
                "discovery_sources": discovery_result.discovery_sources,
                "success_rate": discovery_result.success_rate
            }
            
            # 2. SEO Analysis
            print("📈 Step 2: SEO Analysis...")
            seo_start_time = time.time()
            
            # Create a mock company object for SEO analysis
            mock_company = {
                'website': company['website'],
                'company_name': company['name'],
                'sector': company['sector']
            }
            
            seo_analysis = await seo_analyzer.analyze_company_seo(mock_company)
            seo_processing_time = time.time() - seo_start_time
            
            print(f"   📊 SEO Score: {seo_analysis.overall_score:.1f}/100")
            total_seo_score += seo_analysis.overall_score
            
            company_result["seo_analysis"] = {
                "overall_score": seo_analysis.overall_score,
                "performance": {
                    "pagespeed_score": seo_analysis.performance.pagespeed_score,
                    "load_time": seo_analysis.performance.load_time,
                    "mobile_friendly": seo_analysis.performance.mobile_friendly
                },
                "content": {
                    "meta_description_missing": seo_analysis.content.meta_description_missing,
                    "h1_tags_present": seo_analysis.content.h1_tags_present,
                    "ssl_certificate": seo_analysis.content.ssl_certificate
                },
                "critical_issues": seo_analysis.critical_issues,
                "processing_time": seo_processing_time
            }
            
            # 3. Lead Qualification
            print("🎯 Step 3: Lead Qualification...")
            qual_start_time = time.time()
            
            # Create mock company data for qualification
            company_data = {
                'company_name': company['name'],
                'website': company['website'],
                'sector': company['sector'],
                'city': company['city'],
                'region': company['region'],
                'seo_analysis': seo_analysis,
                'contact_info': {
                    'person': executives[0].full_name if executives else None,
                    'role': executives[0].title if executives else None,
                    'seniority_tier': executives[0].seniority_tier if executives else None,
                    'email': executives[0].email if executives else None,
                    'confidence': executives[0].overall_confidence if executives else 0.0
                }
            }
            
            qualification = lead_qualifier.qualify_lead(company_data)
            qual_processing_time = time.time() - qual_start_time
            
            print(f"   🏆 Lead Score: {qualification.final_score:.1f}/100 (Tier {qualification.priority_tier.value})")
            
            company_result["lead_qualification"] = {
                "final_score": qualification.final_score,
                "priority_tier": qualification.priority_tier.value,
                "tier_label": qualification.tier_label,
                "confidence": qualification.confidence,
                "factor_breakdown": {
                    factor: {
                        "score": breakdown.score,
                        "weight": breakdown.weight,
                        "contribution": breakdown.contribution
                    }
                    for factor, breakdown in qualification.factor_breakdown.items()
                },
                "processing_time": qual_processing_time
            }
            
            # Update summary
            results["summary"]["lead_distribution"][qualification.priority_tier.value] += 1
            
            company_result["status"] = "completed"
            
        except Exception as e:
            error_msg = f"Error processing {company['name']}: {str(e)}"
            print(f"   ❌ {error_msg}")
            logger.error(error_msg, exc_info=True)
            company_result["errors"].append(error_msg)
            company_result["status"] = "failed"
        
        finally:
            company_result["processing_time"] = time.time() - company_start_time
            results["companies"].append(company_result)
            
            print(f"   ⏱️ Company Processing Time: {company_result['processing_time']:.1f}s")
    
    # Calculate final summary
    total_processing_time = time.time() - total_start_time
    successful_companies = len([c for c in results["companies"] if c["status"] == "completed"])
    
    results["summary"].update({
        "executives_found": total_executives_found,
        "average_seo_score": total_seo_score / len(test_companies) if test_companies else 0.0,
        "total_processing_time": total_processing_time,
        "success_rate": (successful_companies / len(test_companies)) * 100 if test_companies else 0.0,
        "average_processing_time_per_company": total_processing_time / len(test_companies) if test_companies else 0.0
    })
    
    # Output results
    print(f"\n" + "="*80)
    print("📊 PIPELINE TEST RESULTS")
    print("="*80)
    
    print(f"🏢 Companies Processed: {len(test_companies)}")
    print(f"✅ Successful: {successful_companies}")
    print(f"👥 Total Executives Found: {total_executives_found}")
    print(f"📈 Average SEO Score: {results['summary']['average_seo_score']:.1f}/100")
    print(f"⏱️ Total Processing Time: {total_processing_time:.1f}s")
    print(f"📊 Success Rate: {results['summary']['success_rate']:.1f}%")
    
    print(f"\n🎯 Lead Distribution:")
    for tier, count in results["summary"]["lead_distribution"].items():
        print(f"   Tier {tier}: {count} companies")
    
    # Save results to JSON file
    output_filename = f"pipeline_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_filename}")
    
    # Output JSON to console
    print(f"\n" + "="*80)
    print("📄 JSON RESULTS")
    print("="*80)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    return results

if __name__ == "__main__":
    asyncio.run(test_full_pipeline_5_companies()) 