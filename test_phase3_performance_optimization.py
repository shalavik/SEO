#!/usr/bin/env python3
"""
Phase 3: Performance Optimization Test
Building on Phase 2 success to achieve <60s processing time target
"""

import time
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import existing components
from src.seo_leads.models import ExecutiveContact
from src.seo_leads.processors.multi_source_executive_engine import MultiSourceExecutiveEngine

def test_performance_optimization():
    """Test performance optimization for Phase 3"""
    
    print("🚀 PHASE 3: PERFORMANCE OPTIMIZATION TEST")
    print("=" * 60)
    print("🎯 Target: Achieve <60s processing time per company")
    print("📈 Building on Phase 2 success (100% success rate, 36 executives found)")
    print()
    
    # Test companies (same as Phase 2 for comparison)
    test_companies = [
        {
            "name": "GPJ Plumbing",
            "url": "https://www.gpjplumbing.co.uk"
        },
        {
            "name": "Emergency Plumber Services", 
            "url": "https://www.emergencyplumberservices.co.uk"
        },
        {
            "name": "247 Plumbing and Gas",
            "url": "https://www.247plumbingandgas.co.uk"
        },
        {
            "name": "Hancox Gas and Plumbing",
            "url": "https://www.hancoxgasandplumbing.co.uk"
        },
        {
            "name": "Metro Plumb Birmingham",
            "url": "https://www.metroplumbbirmingham.co.uk"
        }
    ]
    
    # Initialize multi-source engine
    engine = MultiSourceExecutiveEngine()
    
    total_start_time = time.time()
    all_results = []
    total_executives = 0
    
    for i, company in enumerate(test_companies, 1):
        print(f"\n📋 TESTING COMPANY {i}/5: {company['name']}")
        print("-" * 50)
        
        company_start_time = time.time()
        
        try:
            # Discover executives using multi-source engine
            result = engine.discover_executives(company['name'], company['url'])
            
            company_processing_time = time.time() - company_start_time
            
            # Collect results
            executives_found = len(result.executives) if result else 0
            total_executives += executives_found
            
            all_results.append({
                'company': company['name'],
                'processing_time': company_processing_time,
                'executives_found': executives_found,
                'success': executives_found > 0,
                'target_achieved': company_processing_time < 60
            })
            
            # Display results
            print(f"✅ Processing Time: {company_processing_time:.2f}s")
            print(f"🎯 Target Achievement: {'✅ SUCCESS' if company_processing_time < 60 else '⚠️ NEEDS OPTIMIZATION'}")
            print(f"👥 Executives Found: {executives_found}")
            print(f"📊 Success Rate: {'✅ SUCCESS' if executives_found > 0 else '❌ FAILED'}")
            
            # Performance analysis
            if company_processing_time < 60:
                improvement = ((60 - company_processing_time) / 60) * 100
                print(f"📈 Performance: {improvement:.1f}% better than target")
            else:
                deficit = ((company_processing_time - 60) / 60) * 100
                print(f"📉 Performance: {deficit:.1f}% over target")
            
        except Exception as e:
            print(f"❌ Error processing {company['name']}: {e}")
            all_results.append({
                'company': company['name'],
                'processing_time': 0,
                'executives_found': 0,
                'success': False,
                'target_achieved': False
            })
            continue
    
    # Overall performance analysis
    total_time = time.time() - total_start_time
    
    print(f"\n🏆 PHASE 3 PERFORMANCE OPTIMIZATION RESULTS")
    print("=" * 60)
    
    if all_results:
        successful_results = [r for r in all_results if r['success']]
        avg_processing_time = sum(r['processing_time'] for r in successful_results) / max(1, len(successful_results))
        success_rate = len(successful_results) / len(all_results)
        target_achievement_rate = sum(1 for r in all_results if r['target_achieved']) / len(all_results)
        
        print(f"📊 PERFORMANCE METRICS:")
        print(f"• Companies Processed: {len(all_results)}")
        print(f"• Success Rate: {success_rate:.1%}")
        print(f"• Average Processing Time: {avg_processing_time:.2f}s")
        print(f"• Target Achievement Rate: {target_achievement_rate:.1%}")
        print(f"• Total Executives Found: {total_executives}")
        print(f"• Total Processing Time: {total_time:.2f}s")
        
        print(f"\n🎯 TARGET ANALYSIS:")
        if avg_processing_time < 60:
            print(f"✅ SUCCESS: Average processing time ({avg_processing_time:.2f}s) is under 60s target")
            improvement = ((60 - avg_processing_time) / 60) * 100
            print(f"📈 Performance improvement: {improvement:.1f}% better than target")
        else:
            print(f"⚠️ OPTIMIZATION NEEDED: Average processing time ({avg_processing_time:.2f}s) exceeds 60s target")
            deficit = ((avg_processing_time - 60) / 60) * 100
            print(f"📉 Performance deficit: {deficit:.1f}% over target")
        
        # Comparison with Phase 2 results
        print(f"\n📈 PHASE 2 vs PHASE 3 COMPARISON:")
        phase2_avg_time = 64.93  # From Phase 2 results
        if avg_processing_time < phase2_avg_time:
            improvement = ((phase2_avg_time - avg_processing_time) / phase2_avg_time) * 100
            print(f"✅ Performance Improvement: {improvement:.1f}% faster than Phase 2")
            print(f"• Phase 2: {phase2_avg_time:.2f}s average")
            print(f"• Phase 3: {avg_processing_time:.2f}s average")
        else:
            regression = ((avg_processing_time - phase2_avg_time) / phase2_avg_time) * 100
            print(f"⚠️ Performance Regression: {regression:.1f}% slower than Phase 2")
        
        # Individual company analysis
        print(f"\n📋 INDIVIDUAL COMPANY PERFORMANCE:")
        for result in all_results:
            status = "✅" if result['target_achieved'] else "⚠️"
            print(f"{status} {result['company']}: {result['processing_time']:.2f}s, {result['executives_found']} executives")
        
        # Phase 3 completion assessment
        print(f"\n🎯 PHASE 3 IMPLEMENTATION ASSESSMENT:")
        
        if target_achievement_rate >= 0.8 and success_rate >= 0.8:
            print(f"🎉 PHASE 3: ✅ COMPLETE SUCCESS")
            print(f"• Performance targets achieved ({target_achievement_rate:.1%} success rate)")
            print(f"• Executive discovery maintained ({success_rate:.1%} success rate)")
            print(f"• System ready for production deployment")
            print(f"• Phase 4 (Advanced Features) can begin")
        elif target_achievement_rate >= 0.6:
            print(f"🔧 PHASE 3: ⚠️ PARTIAL SUCCESS")
            print(f"• Performance targets partially achieved ({target_achievement_rate:.1%} success rate)")
            print(f"• Additional optimization recommended")
            print(f"• Consider parallel processing implementation")
        else:
            print(f"🚨 PHASE 3: ❌ NEEDS SIGNIFICANT OPTIMIZATION")
            print(f"• Performance targets not met ({target_achievement_rate:.1%} success rate)")
            print(f"• Major optimization required")
            print(f"• Consider architectural improvements")
        
        # Optimization recommendations
        print(f"\n🔧 OPTIMIZATION RECOMMENDATIONS:")
        if avg_processing_time > 60:
            print(f"• Implement parallel source processing")
            print(f"• Add request timeout controls")
            print(f"• Optimize website scraping algorithms")
            print(f"• Consider caching mechanisms")
        
        if success_rate < 1.0:
            print(f"• Improve error handling and recovery")
            print(f"• Add fallback processing strategies")
            print(f"• Enhance source reliability")
        
        print(f"\n📋 NEXT STEPS:")
        if target_achievement_rate >= 0.8:
            print(f"• Phase 3 implementation complete")
            print(f"• Begin Phase 4: Advanced Features")
            print(f"• Consider LinkedIn integration enhancement")
            print(f"• Implement contact enrichment pipeline")
        else:
            print(f"• Continue Phase 3 optimization")
            print(f"• Implement parallel processing")
            print(f"• Add performance monitoring")
            print(f"• Optimize critical path operations")
    
    else:
        print("❌ No results to analyze")
        print("🔧 System requires immediate attention")

if __name__ == "__main__":
    test_performance_optimization() 