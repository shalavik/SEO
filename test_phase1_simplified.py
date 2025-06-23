"""
Simplified Phase 1 Implementation Test

This test demonstrates Phase 1 improvements using existing robust pipeline components
and compares performance against baseline validation results.

Author: AI Assistant
Date: 2025-01-23
Version: 1.0.0 - Simplified Phase 1 Test
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from manual_data_loader import ManualDataLoader
from advanced_result_comparator import AdvancedResultComparator

# Import existing robust components
try:
    from seo_leads.processors.robust_executive_pipeline import RobustExecutivePipeline
    ROBUST_PIPELINE_AVAILABLE = True
    print("✅ Robust pipeline components imported successfully")
except ImportError as e:
    print(f"⚠️ Robust pipeline not available: {e}")
    ROBUST_PIPELINE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplifiedPhase1Test:
    """Simplified Phase 1 implementation test using existing components"""
    
    def __init__(self, excel_file_path: str = "1Testfinal.xlsx"):
        self.excel_file_path = excel_file_path
        self.manual_loader = ManualDataLoader(excel_file_path)
        self.comparator = AdvancedResultComparator()
        
        if ROBUST_PIPELINE_AVAILABLE:
            self.pipeline = RobustExecutivePipeline()
        
        # Baseline metrics from comprehensive validation
        self.baseline_metrics = {
            'discovery_rate': 20.0,
            'false_positive_rate': 55.6,
            'average_confidence': 0.384,
            'url_coverage': 60.0,
            'executives_found': 4
        }
    
    def run_phase1_test(self) -> Dict[str, Any]:
        """Run simplified Phase 1 test"""
        start_time = time.time()
        
        logger.info("🚀 Starting Simplified Phase 1 Implementation Test")
        
        try:
            # Load reference data
            logger.info("📋 Loading manual reference data...")
            reference_data = self.manual_loader.load_reference_data()
            
            if not ROBUST_PIPELINE_AVAILABLE:
                return self._create_error_result("Robust pipeline not available")
            
            # Run robust pipeline on test samples
            logger.info("⚡ Running robust executive pipeline...")
            system_results = self._run_robust_pipeline_test(reference_data)
            
            # Compare results
            logger.info("🔄 Comparing results with manual data...")
            comparison_results = self._compare_results(system_results, reference_data)
            
            # Calculate metrics
            logger.info("📈 Calculating performance metrics...")
            metrics = self._calculate_metrics(comparison_results, reference_data)
            
            # Generate results
            execution_time = time.time() - start_time
            results = self._generate_results(metrics, comparison_results, execution_time)
            
            logger.info(f"✅ Phase 1 test completed in {execution_time:.2f} seconds")
            return results
            
        except Exception as e:
            logger.error(f"❌ Phase 1 test failed: {str(e)}")
            return self._create_error_result(str(e))
    
    def _run_robust_pipeline_test(self, reference_data: Dict) -> Dict[str, List[Dict]]:
        """Run robust pipeline on simplified test content"""
        system_results = {}
        
        # Create test content for key URLs
        test_content = {
            "http://www.vernonheating.com": """
            About Vernon Heating Services - John Vernon, Owner
            Founded by John Vernon over 20 years ago, Vernon Heating Services 
            specializes in central heating installations. Contact John Vernon 
            directly at info@vernonheating.com or 01234 567890.
            """,
            
            "http://www.kwsmith.com": """
            K W Smith Plumbing - Ken Smith, Director
            Ken Smith brings over 15 years of experience as Director of K W Smith Plumbing.
            As a Gas Safe registered engineer, Ken ensures quality work.
            Contact: kevin@kwsmith.com | 0161 234 5678
            """,
            
            "http://thejoyceagency.com": """
            Meet Our Team
            Patricia Joyce - Agency Director
            Patricia Joyce founded The Joyce Agency in 2010. 
            Email: patricia@thejoyceagency.com
            
            Troy Joyce - Operations Manager  
            Troy handles operations and client relationships.
            Email: troy@thejoyceagency.com
            """,
            
            "http://sagewater.com": """
            Leadership Team
            Peter Page, President
            Peter Page leads Sage Water Solutions with 25 years experience.
            Contact: ppage@sagewater.com | 0203 456 7890
            """,
            
            "http://anhplumbing.com": """
            ANH Plumbing Services
            Professional plumbing services since 2005.
            Phone: 01455 822896 | Email: admin@anhplumbing.com
            Customer review: "Douglas Hart provided excellent service!" - Mrs. Johnson
            """
        }
        
        # Process each URL with robust pipeline
        for url, content in test_content.items():
            if url in reference_data:
                logger.info(f"Processing {url}")
                
                try:
                    company_info = {
                        'name': self._extract_company_name(url),
                        'domain': url,
                        'url': url
                    }
                    
                    # Run robust pipeline
                    executives = self.pipeline.extract_executives(content, company_info)
                    
                    # Convert to standard format
                    system_executives = []
                    for exec_profile in executives:
                        system_executives.append({
                            'name': exec_profile.name,
                            'title': exec_profile.title,
                            'email': exec_profile.email,
                            'phone': exec_profile.phone,
                            'linkedin_url': exec_profile.linkedin_url,
                            'confidence': exec_profile.overall_confidence,
                            'extraction_method': 'robust_pipeline',
                            'context': f"Confidence: {exec_profile.overall_confidence:.3f}",
                            'source_sections': ['main_content']
                        })
                    
                    system_results[url] = system_executives
                    logger.info(f"  → Found {len(system_executives)} executives")
                    
                except Exception as e:
                    logger.error(f"  → Error processing {url}: {str(e)}")
                    system_results[url] = []
        
        return system_results
    
    def _extract_company_name(self, url: str) -> str:
        """Extract company name from URL"""
        company_names = {
            "http://www.vernonheating.com": "Vernon Heating Services",
            "http://www.kwsmith.com": "K W Smith Plumbing", 
            "http://thejoyceagency.com": "The Joyce Agency",
            "http://sagewater.com": "Sage Water Solutions",
            "http://anhplumbing.com": "ANH Plumbing Services"
        }
        return company_names.get(url, "Unknown Company")
    
    def _compare_results(self, system_results: Dict, reference_data: Dict) -> Dict:
        """Compare system results with reference data"""
        comparison_results = {}
        
        for url in reference_data.keys():
            if url in system_results:
                system_executives = system_results[url]
                manual_executives = reference_data[url]
                
                comparison_result = self.comparator.compare_executives(
                    system_executives, manual_executives, url
                )
                comparison_results[url] = comparison_result
                
                logger.info(f"{url}: {len(system_executives)} system vs {len(manual_executives)} manual")
        
        return comparison_results
    
    def _calculate_metrics(self, comparison_results: Dict, reference_data: Dict) -> Dict:
        """Calculate performance metrics"""
        total_manual = sum(len(execs) for execs in reference_data.values())
        total_system = sum(len(result.system_executives) for result in comparison_results.values())
        
        # Count discoveries and false positives
        total_discovered = 0
        total_false_positives = 0
        confidence_scores = []
        urls_with_results = 0
        
        for result in comparison_results.values():
            # Count good matches
            good_matches = sum(1 for match in result.matches 
                             if match.match_type.value not in ['no_match', 'weak_match'])
            total_discovered += good_matches
            
            # Count false positives
            total_false_positives += len(result.false_positives)
            
            # Collect confidence scores
            for match in result.matches:
                if match.match_type.value not in ['no_match', 'weak_match']:
                    confidence_scores.append(match.overall_confidence)
            
            # Count URLs with results
            if len(result.system_executives) > 0:
                urls_with_results += 1
        
        # Calculate current metrics
        discovery_rate = (total_discovered / total_manual) * 100 if total_manual > 0 else 0
        false_positive_rate = (total_false_positives / total_system) * 100 if total_system > 0 else 0
        average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        url_coverage = (urls_with_results / len(reference_data)) * 100
        
        # Calculate improvements vs baseline
        discovery_improvement = discovery_rate - self.baseline_metrics['discovery_rate']
        fp_improvement = self.baseline_metrics['false_positive_rate'] - false_positive_rate
        confidence_improvement = average_confidence - self.baseline_metrics['average_confidence']
        coverage_improvement = url_coverage - self.baseline_metrics['url_coverage']
        
        return {
            'current': {
                'discovery_rate': discovery_rate,
                'false_positive_rate': false_positive_rate,
                'average_confidence': average_confidence,
                'url_coverage': url_coverage,
                'executives_found': total_discovered,
                'total_system_executives': total_system
            },
            'improvements': {
                'discovery_rate': discovery_improvement,
                'false_positive_rate': fp_improvement,
                'average_confidence': confidence_improvement,
                'url_coverage': coverage_improvement
            },
            'baseline': self.baseline_metrics
        }
    
    def _generate_results(self, metrics: Dict, comparison_results: Dict, execution_time: float) -> Dict:
        """Generate comprehensive test results"""
        current = metrics['current']
        improvements = metrics['improvements']
        
        # Assess performance
        targets_met = {
            'discovery_improved': improvements['discovery_rate'] > 0,
            'false_positives_reduced': improvements['false_positive_rate'] > 0,
            'confidence_improved': improvements['average_confidence'] > 0,
            'coverage_maintained': current['url_coverage'] >= 40.0
        }
        
        targets_achieved = sum(targets_met.values())
        overall_score = targets_achieved / len(targets_met)
        
        performance_rating = (
            "Excellent" if overall_score >= 0.75 else
            "Good" if overall_score >= 0.5 else
            "Fair" if overall_score >= 0.25 else
            "Poor"
        )
        
        return {
            'metadata': {
                'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
                'execution_time': execution_time,
                'test_type': 'simplified_phase1_test',
                'pipeline_version': 'robust_executive_pipeline',
                'urls_tested': len(comparison_results)
            },
            
            'performance_metrics': {
                'baseline': metrics['baseline'],
                'current': current,
                'improvements': improvements,
                'targets_met': targets_met,
                'overall_score': overall_score,
                'performance_rating': performance_rating
            },
            
            'detailed_results': {
                'url_comparisons': {
                    url: {
                        'discovery_rate': result.discovery_rate,
                        'false_positives': len(result.false_positives),
                        'matches': len(result.matches),
                        'system_executives': len(result.system_executives),
                        'manual_executives': len(result.manual_executives)
                    }
                    for url, result in comparison_results.items()
                }
            },
            
            'recommendations': self._generate_recommendations(metrics, targets_met),
            'phase1_status': 'success' if overall_score >= 0.5 else 'needs_improvement'
        }
    
    def _generate_recommendations(self, metrics: Dict, targets_met: Dict) -> List[str]:
        """Generate recommendations based on results"""
        recommendations = []
        current = metrics['current']
        improvements = metrics['improvements']
        
        if not targets_met['discovery_improved']:
            if current['discovery_rate'] < 15.0:
                recommendations.append("🔍 Discovery rate very low - implement enhanced name extraction")
            else:
                recommendations.append("📈 Discovery rate shows promise - optimize extraction patterns")
        else:
            recommendations.append("✅ Discovery rate improved over baseline")
        
        if not targets_met['false_positives_reduced']:
            recommendations.append("❌ False positive rate needs attention - implement quality validation")
        else:
            recommendations.append("✅ False positive rate reduced successfully")
        
        if not targets_met['confidence_improved']:
            recommendations.append("🎪 Confidence scores need improvement - enhance validation algorithms")
        else:
            recommendations.append("✅ Confidence scores improved")
        
        if current['discovery_rate'] > 30.0 and current['false_positive_rate'] < 30.0:
            recommendations.append("🚀 Ready for enhanced Phase 1 implementation")
        elif current['discovery_rate'] > 15.0:
            recommendations.append("⏭️ Good foundation - proceed with Phase 1 enhancements")
        else:
            recommendations.append("🔧 Focus on basic extraction improvements first")
        
        return recommendations
    
    def _create_error_result(self, error_message: str) -> Dict:
        """Create error result"""
        return {
            'metadata': {
                'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
                'test_type': 'simplified_phase1_test',
                'status': 'error'
            },
            'error': error_message,
            'recommendations': ["Check pipeline availability and dependencies"]
        }
    
    def print_results(self, results: Dict):
        """Print test results"""
        print("\n" + "="*80)
        print("⚡ SIMPLIFIED PHASE 1 IMPLEMENTATION TEST RESULTS")
        print("="*80)
        
        if 'error' in results:
            print(f"\n❌ TEST ERROR: {results['error']}")
            return
        
        metadata = results['metadata']
        metrics = results['performance_metrics']
        baseline = metrics['baseline']
        current = metrics['current']
        improvements = metrics['improvements']
        
        print(f"\n📊 EXECUTION SUMMARY:")
        print(f"  ⏱️  Execution Time: {metadata['execution_time']:.2f} seconds")
        print(f"  🌐 URLs Tested: {metadata['urls_tested']}")
        print(f"  🔧 Pipeline: {metadata['pipeline_version']}")
        print(f"  📈 Overall Score: {metrics['overall_score']:.3f}")
        print(f"  🏆 Rating: {metrics['performance_rating']}")
        
        print(f"\n📈 BASELINE VS CURRENT COMPARISON:")
        print(f"  🎯 Discovery Rate: {baseline['discovery_rate']:.1f}% → {current['discovery_rate']:.1f}% "
              f"({improvements['discovery_rate']:+.1f}%)")
        print(f"  ❌ False Positive Rate: {baseline['false_positive_rate']:.1f}% → {current['false_positive_rate']:.1f}% "
              f"({improvements['false_positive_rate']:+.1f}%)")
        print(f"  🎪 Average Confidence: {baseline['average_confidence']:.3f} → {current['average_confidence']:.3f} "
              f"({improvements['average_confidence']:+.3f})")
        print(f"  🌐 URL Coverage: {baseline['url_coverage']:.1f}% → {current['url_coverage']:.1f}% "
              f"({improvements['url_coverage']:+.1f}%)")
        
        print(f"\n🎯 TARGET ACHIEVEMENT:")
        targets = metrics['targets_met']
        for target, achieved in targets.items():
            status = "✅" if achieved else "❌"
            print(f"  {status} {target.replace('_', ' ').title()}: {achieved}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for i, recommendation in enumerate(results['recommendations'], 1):
            print(f"  {i}. {recommendation}")
        
        print(f"\n📊 URL-LEVEL RESULTS:")
        for url, data in results['detailed_results']['url_comparisons'].items():
            print(f"  {url}:")
            print(f"    Discovery: {data['discovery_rate']:.1f}% | "
                  f"Matches: {data['matches']} | "
                  f"False Positives: {data['false_positives']}")
        
        # Overall assessment
        if metrics['overall_score'] >= 0.75:
            print(f"\n🎉 ASSESSMENT: EXCELLENT PROGRESS!")
            print("   🚀 Strong foundation for Phase 1 enhancements")
        elif metrics['overall_score'] >= 0.5:
            print(f"\n👍 ASSESSMENT: GOOD PROGRESS!")
            print("   📈 Ready for Phase 1 improvements")
        else:
            print(f"\n⚠️  ASSESSMENT: NEEDS IMPROVEMENT")
            print("   🔧 Focus on basic extraction before Phase 1")
        
        print("="*80)
    
    def save_results(self, results: Dict, output_file: Optional[str] = None) -> str:
        """Save test results"""
        if output_file is None:
            timestamp = results['metadata']['timestamp']
            output_file = f"simplified_phase1_test_results_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return output_file

def main():
    """Main execution function"""
    try:
        # Run simplified Phase 1 test
        tester = SimplifiedPhase1Test()
        results = tester.run_phase1_test()
        
        # Print results
        tester.print_results(results)
        
        # Save results
        output_file = tester.save_results(results)
        print(f"\n📄 Detailed results saved to: {output_file}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main()) 