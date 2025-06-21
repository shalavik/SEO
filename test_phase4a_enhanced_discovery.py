#!/usr/bin/env python3
"""
Phase 4A Enhanced Executive Discovery System Test
Advanced ML-powered executive discovery with 70%+ target success rate
Comprehensive testing and validation
"""

import asyncio
import sys
import os
import logging
import time
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from src.seo_leads.processors.phase4a_enhanced_engine import (
    Phase4AEnhancedEngine,
    test_phase4a_enhanced_discovery
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase4a_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Enhanced test company dataset
TEST_COMPANIES = [
    {
        'name': 'GPJ Plumbing',
        'website': 'https://gpjplumbing.co.uk',
        'expected_executives': ['Gary', 'Paul'],
        'industry': 'plumbing',
        'region': 'UK'
    },
    {
        'name': '247 Plumbing and Gas',
        'website': 'https://247plumbingandgas.co.uk',
        'expected_executives': ['Director', 'Manager'],
        'industry': 'plumbing',
        'region': 'UK'
    },
    {
        'name': 'Hancox Gas and Plumbing',
        'website': 'https://hancoxgasandplumbing.co.uk',
        'expected_executives': ['Hancox'],
        'industry': 'plumbing',
        'region': 'UK'
    },
    {
        'name': 'Emergency Plumber Services',
        'website': 'https://emergencyplumberservices.co.uk',
        'expected_executives': ['Owner', 'Director'],
        'industry': 'plumbing',
        'region': 'UK'
    },
    {
        'name': 'Metro Plumb Birmingham',
        'website': 'https://metroplumbbirmingham.co.uk',
        'expected_executives': ['Manager'],
        'industry': 'plumbing',
        'region': 'UK'
    }
]

def print_test_header():
    """Print test header with Phase 4A information"""
    print("\n" + "="*80)
    print("🚀 PHASE 4A ENHANCED EXECUTIVE DISCOVERY SYSTEM TEST")
    print("="*80)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🏢 Companies to Test: {len(TEST_COMPANIES)}")
    print(f"🎯 Target Success Rate: 70%+ (vs current 40%)")
    print(f"🧠 Enhancement: Advanced ML + Enhanced Content Extraction")
    print("="*80)

def print_company_header(company_data: Dict[str, Any], index: int):
    """Print header for individual company test"""
    print(f"\n{'='*60}")
    print(f"🏢 COMPANY {index + 1}/{len(TEST_COMPANIES)}: {company_data['name']}")
    print(f"🌐 Website: {company_data['website']}")
    print(f"📍 Region: {company_data.get('region', 'UK')}")
    print(f"🏭 Industry: {company_data.get('industry', 'plumbing')}")
    print(f"{'='*60}")

def print_result_summary(result: Dict[str, Any]):
    """Print detailed result summary"""
    test_summary = result['test_summary']
    
    print("\n" + "🎯 PHASE 4A TEST RESULTS SUMMARY")
    print("="*80)
    print(f"📊 Overall Performance:")
    print(f"   • Total Companies: {test_summary['total_companies']}")
    print(f"   • Successful Companies: {test_summary['successful_companies']}")
    print(f"   • Success Rate: {test_summary['success_rate_percentage']}%")
    print(f"   • Total Executives Found: {test_summary['total_executives_found']}")
    print(f"   • Processing Time: {test_summary['total_processing_time']:.2f}s")
    print(f"   • Avg Time per Company: {test_summary['average_processing_time']:.2f}s")
    print(f"   • Target Achievement: {test_summary['target_achievement']}")
    
    # Performance status
    success_rate = test_summary['success_rate_percentage']
    if success_rate >= 70:
        status = "🎉 EXCELLENT - Target Achieved!"
        improvement = success_rate - 40  # Previous baseline
        print(f"\n✅ {status}")
        print(f"📈 Improvement: +{improvement:.1f}% from baseline (40% → {success_rate}%)")
    elif success_rate >= 50:
        status = "🟡 GOOD - Progress Made"
        improvement = success_rate - 40
        print(f"\n🟡 {status}")
        print(f"📈 Improvement: +{improvement:.1f}% from baseline")
        print(f"🎯 Need {70 - success_rate:.1f}% more to reach target")
    else:
        status = "🔴 NEEDS IMPROVEMENT"
        print(f"\n❌ {status}")
        print(f"🎯 Need {70 - success_rate:.1f}% improvement to reach target")

def print_detailed_company_results(results: List[Dict[str, Any]]):
    """Print detailed results for each company"""
    print("\n📋 DETAILED COMPANY RESULTS")
    print("="*80)
    
    for i, result in enumerate(results):
        status_emoji = "✅" if result.success else "❌"
        confidence_dist = result.confidence_distribution
        
        print(f"\n{i+1}. {status_emoji} {result.company_name}")
        print(f"   🌐 URL: {result.website_url}")
        print(f"   👥 Executives Found: {result.final_executives_count}")
        print(f"   ⏱️ Processing Time: {result.processing_time:.2f}s")
        print(f"   🎯 Confidence Distribution: High:{confidence_dist['high']}, Med:{confidence_dist['medium']}, Low:{confidence_dist['low']}")
        print(f"   🔍 Methods Used: {', '.join(result.extraction_methods_used)}")
        print(f"   🧠 ML Candidates: {result.ml_processed_candidates}")
        
        if result.executives:
            print(f"   📄 Executive Details:")
            for j, exec in enumerate(result.executives[:3], 1):  # Show top 3
                confidence_emoji = "🟢" if exec.overall_confidence >= 0.7 else "🟡" if exec.overall_confidence >= 0.5 else "🔴"
                print(f"      {j}. {confidence_emoji} {exec.first_name} {exec.last_name}")
                if exec.title:
                    print(f"         Title: {exec.title}")
                print(f"         Confidence: {exec.overall_confidence:.2f}")
                if exec.email:
                    print(f"         Email: {exec.email}")
                if exec.phone:
                    print(f"         Phone: {exec.phone}")
            
            if len(result.executives) > 3:
                print(f"      ... and {len(result.executives) - 3} more executives")
        
        if not result.success and 'error' in result.analytics:
            print(f"   ❌ Error: {result.analytics['error']}")

def analyze_enhancement_effectiveness(results: List[Dict[str, Any]]):
    """Analyze the effectiveness of Phase 4A enhancements"""
    print("\n🔬 PHASE 4A ENHANCEMENT ANALYSIS")
    print("="*80)
    
    # Collect extraction methods
    all_methods = set()
    method_success = {}
    
    for result in results:
        for method in result.extraction_methods_used:
            all_methods.add(method)
            if method not in method_success:
                method_success[method] = {'total': 0, 'successful': 0}
            method_success[method]['total'] += 1
            if result.success:
                method_success[method]['successful'] += 1
    
    print("📊 Extraction Method Performance:")
    for method in sorted(all_methods):
        if method in method_success:
            total = method_success[method]['total']
            successful = method_success[method]['successful']
            rate = (successful / total * 100) if total > 0 else 0
            print(f"   • {method}: {successful}/{total} ({rate:.1f}%)")
    
    # Confidence analysis
    high_conf_count = sum(result.confidence_distribution['high'] for result in results)
    med_conf_count = sum(result.confidence_distribution['medium'] for result in results)
    low_conf_count = sum(result.confidence_distribution['low'] for result in results)
    total_execs = high_conf_count + med_conf_count + low_conf_count
    
    if total_execs > 0:
        print(f"\n🎯 Executive Quality Distribution:")
        print(f"   • High Confidence (≥0.7): {high_conf_count} ({high_conf_count/total_execs*100:.1f}%)")
        print(f"   • Medium Confidence (0.5-0.7): {med_conf_count} ({med_conf_count/total_execs*100:.1f}%)")
        print(f"   • Low Confidence (<0.5): {low_conf_count} ({low_conf_count/total_execs*100:.1f}%)")
    
    # ML processing effectiveness
    total_ml_candidates = sum(result.ml_processed_candidates for result in results)
    total_final_executives = sum(result.final_executives_count for result in results)
    
    if total_ml_candidates > 0:
        conversion_rate = (total_final_executives / total_ml_candidates) * 100
        print(f"\n🧠 ML Processing Effectiveness:")
        print(f"   • Total ML Candidates: {total_ml_candidates}")
        print(f"   • Final Executives: {total_final_executives}")
        print(f"   • Conversion Rate: {conversion_rate:.1f}%")

async def run_enhanced_test():
    """Run the enhanced Phase 4A test"""
    print_test_header()
    
    try:
        # Run the enhanced discovery test
        logger.info("Starting Phase 4A Enhanced Discovery Test")
        result = await test_phase4a_enhanced_discovery(TEST_COMPANIES)
        
        # Print comprehensive results
        print_result_summary(result)
        print_detailed_company_results(result['detailed_results'])
        analyze_enhancement_effectiveness(result['detailed_results'])
        
        # Performance analytics
        if 'performance_analytics' in result:
            analytics = result['performance_analytics']
            print(f"\n📈 ENGINE PERFORMANCE ANALYTICS")
            print("="*80)
            for key, value in analytics.items():
                print(f"   • {key.replace('_', ' ').title()}: {value}")
        
        # Success assessment
        success_rate = result['test_summary']['success_rate_percentage']
        if success_rate >= 70:
            print(f"\n🎉 PHASE 4A SUCCESS! Target of 70%+ achieved with {success_rate}%")
            print("✅ Ready for production deployment")
        elif success_rate >= 50:
            print(f"\n🟡 PHASE 4A PROGRESS! Achieved {success_rate}%, need {70-success_rate:.1f}% more")
            print("🔧 Recommend additional optimization")
        else:
            print(f"\n🔴 PHASE 4A NEEDS WORK! Achieved {success_rate}%, significant improvement needed")
            print("🛠️ Recommend system review and enhancement")
        
        print(f"\n📝 Test log saved to: phase4a_test.log")
        print("="*80)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        print(f"\n❌ TEST FAILED: {e}")
        return None

if __name__ == "__main__":
    # Run the test
    result = asyncio.run(run_enhanced_test())
    
    if result:
        # Exit with appropriate code
        success_rate = result['test_summary']['success_rate_percentage']
        if success_rate >= 70:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Needs improvement
    else:
        sys.exit(2)  # Test failed 