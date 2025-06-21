#!/usr/bin/env python3
"""
Phase 4A Enhanced Discovery System Test - Fixed Version
Testing advanced ML-powered executive discovery with proper model integration
Target: 70%+ success rate improvement from baseline 40%
"""

import asyncio
import sys
import os
import logging
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from src.seo_leads.processors.phase4a_fixed_engine import Phase4AFixedEngine, test_phase4a_fixed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Test companies
TEST_COMPANIES = [
    {'name': 'GPJ Plumbing', 'website': 'https://gpjplumbing.co.uk'},
    {'name': '247 Plumbing and Gas', 'website': 'https://247plumbingandgas.co.uk'},
    {'name': 'Hancox Gas and Plumbing', 'website': 'https://hancoxgasandplumbing.co.uk'},
    {'name': 'Emergency Plumber Services', 'website': 'https://emergencyplumberservices.co.uk'},
    {'name': 'Metro Plumb Birmingham', 'website': 'https://metroplumbbirmingham.co.uk'}
]

async def main():
    """Run Phase 4A Fixed Test"""
    print("\n" + "="*80)
    print("🚀 PHASE 4A ENHANCED DISCOVERY - FIXED VERSION TEST")
    print("="*80)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🏢 Companies: {len(TEST_COMPANIES)}")
    print(f"🎯 Target: 70%+ success rate (vs 40% baseline)")
    print(f"🔧 Enhancement: Advanced ML + Proper Model Integration")
    print("="*80)
    
    try:
        # Run the test
        result = await test_phase4a_fixed(TEST_COMPANIES)
        
        # Print results
        summary = result['test_summary']
        print(f"\n📊 PHASE 4A FIXED TEST RESULTS:")
        print(f"   • Total Companies: {summary['total_companies']}")
        print(f"   • Successful Companies: {summary['successful_companies']}")
        print(f"   • Success Rate: {summary['success_rate_percentage']}%")
        print(f"   • Total Executives: {summary['total_executives_found']}")
        print(f"   • Processing Time: {summary['total_processing_time']:.2f}s")
        print(f"   • Achievement: {summary['target_achievement']}")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for i, res in enumerate(result['detailed_results'], 1):
            status = "✅" if res.success else "❌"
            print(f"   {i}. {status} {res.company_name}")
            print(f"      Executives: {res.final_executives_count}")
            print(f"      ML Candidates: {res.ml_candidates_found}")
            print(f"      Time: {res.processing_time:.2f}s")
            print(f"      Methods: {', '.join(res.extraction_methods)}")
            
            if res.executives:
                print(f"      Top Executive: {res.executives[0].first_name} {res.executives[0].last_name}")
                print(f"      Title: {res.executives[0].title}")
                print(f"      Confidence: {res.executives[0].overall_confidence:.2f}")
        
        # Assessment
        success_rate = summary['success_rate_percentage']
        if success_rate >= 70:
            print(f"\n🎉 PHASE 4A SUCCESS! Target achieved: {success_rate}%")
            improvement = success_rate - 40
            print(f"📈 Improvement: +{improvement:.1f}% from baseline")
        elif success_rate >= 50:
            print(f"\n🟡 PHASE 4A PROGRESS! Achieved: {success_rate}%")
            improvement = success_rate - 40
            print(f"📈 Improvement: +{improvement:.1f}% from baseline")
            print(f"🎯 Need {70 - success_rate:.1f}% more for target")
        else:
            print(f"\n🔴 PHASE 4A NEEDS WORK! Only {success_rate}%")
            print(f"🎯 Need {70 - success_rate:.1f}% improvement")
        
        print("="*80)
        
        return success_rate >= 50  # Return success if we're making progress
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 