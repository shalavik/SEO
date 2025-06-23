"""
Comprehensive 20-URL Validation with Real Pipeline

This version integrates with our actual robust executive extraction pipeline
to provide real validation results against the manual reference data.

Author: AI Assistant
Date: 2025-01-19
Project: SEO Lead Generation - Comprehensive Validation Framework
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import traceback
import asyncio

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from manual_data_loader import ManualDataLoader
from advanced_result_comparator import AdvancedResultComparator, URLComparisonResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealPipelineValidator:
    """
    Comprehensive validator that uses our actual robust executive extraction pipeline.
    """
    
    def __init__(self, excel_file_path: str = "1Testfinal.xlsx"):
        """Initialize the validator with real pipeline integration."""
        self.excel_file_path = excel_file_path
        self.manual_loader = ManualDataLoader(excel_file_path)
        self.comparator = AdvancedResultComparator()
        
        # Results storage
        self.reference_data = {}
        self.system_results = {}
        self.comparison_results = {}
        self.overall_metrics = {}
        
    def run_validation_with_robust_pipeline(self) -> Dict[str, Any]:
        """
        Execute validation using the robust executive extraction pipeline.
        
        Returns:
            Dict[str, Any]: Comprehensive validation results
        """
        start_time = time.time()
        
        logger.info("🚀 Starting Real Pipeline 20-URL Validation")
        
        try:
            # Phase 1: Load reference data
            logger.info("📋 Phase 1: Loading manual reference data...")
            self.reference_data = self.manual_loader.load_reference_data()
            
            # Phase 2: Run robust pipeline on all URLs
            logger.info("🔍 Phase 2: Running robust executive pipeline...")
            self.system_results = self._run_robust_pipeline_extraction()
            
            # Phase 3: Compare results
            logger.info("🔄 Phase 3: Advanced comparison analysis...")
            self.comparison_results = self._compare_all_results()
            
            # Phase 4: Calculate metrics
            logger.info("📊 Phase 4: Calculating performance metrics...")
            self.overall_metrics = self._calculate_comprehensive_metrics()
            
            # Phase 5: Generate results
            execution_time = time.time() - start_time
            results = self._generate_validation_results(execution_time)
            
            logger.info(f"✅ Real pipeline validation completed in {execution_time:.2f} seconds")
            return results
            
        except Exception as e:
            logger.error(f"❌ Real pipeline validation failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def _run_robust_pipeline_extraction(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run the robust executive extraction pipeline on all URLs.
        
        Returns:
            Dict[str, List[Dict]]: Extraction results by URL
        """
        # Import our robust pipeline
        from seo_leads.processors.robust_executive_pipeline import RobustExecutivePipeline
        
        pipeline = RobustExecutivePipeline()
        system_results = {}
        urls = self.manual_loader.get_all_urls()
        
        logger.info(f"Processing {len(urls)} URLs with robust pipeline...")
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing URL {i}/{len(urls)}: {url}")
            
            try:
                # Extract executives using robust pipeline
                executives = pipeline.extract_executives(url)
                
                # Format results consistently
                formatted_executives = []
                for exec_data in executives:
                    formatted_exec = {
                        'name': exec_data.get('name', ''),
                        'title': exec_data.get('title', ''),
                        'email': exec_data.get('email', ''),
                        'phone': exec_data.get('phone', ''),
                        'linkedin_url': exec_data.get('linkedin_url', ''),
                        'url': url,
                        'extraction_method': exec_data.get('extraction_method', 'robust_pipeline'),
                        'confidence': exec_data.get('overall_confidence', 0.0),
                        'context': exec_data.get('context', {}),
                        'source_sections': exec_data.get('source_sections', [])
                    }
                    formatted_executives.append(formatted_exec)
                
                system_results[url] = formatted_executives
                logger.info(f"  → Found {len(formatted_executives)} executives")
                
                # Log executive details
                for exec_data in formatted_executives:
                    logger.info(f"    • {exec_data['name']} ({exec_data['title']}) - {exec_data['email']}")
                
            except Exception as e:
                logger.error(f"  → Error processing {url}: {str(e)}")
                system_results[url] = []
        
        return system_results
    
    def _compare_all_results(self) -> Dict[str, URLComparisonResult]:
        """Compare all results using advanced comparison algorithms."""
        comparison_results = {}
        
        for url in self.reference_data.keys():
            system_executives = self.system_results.get(url, [])
            manual_executives = self.reference_data[url]
            
            logger.info(f"\nComparing {url}:")
            logger.info(f"  System: {len(system_executives)} executives")
            logger.info(f"  Manual: {len(manual_executives)} executives")
            
            comparison_result = self.comparator.compare_executives(
                system_executives, manual_executives, url
            )
            
            comparison_results[url] = comparison_result
            
            # Log detailed comparison results
            logger.info(f"  Discovery Rate: {comparison_result.discovery_rate:.1f}%")
            logger.info(f"  Attribution Rate: {comparison_result.attribution_rate:.1f}%")
            logger.info(f"  Matches: {len(comparison_result.matches)}")
            logger.info(f"  Missing: {len(comparison_result.missing_executives)}")
            logger.info(f"  False Positives: {len(comparison_result.false_positives)}")
            
            # Log match details
            for i, match in enumerate(comparison_result.matches):
                if match.manual_executive:
                    logger.info(f"    Match {i+1}: {match.match_type.value} "
                              f"(confidence: {match.overall_confidence:.3f})")
                    logger.info(f"      System: {match.system_executive.get('name', 'N/A')}")
                    logger.info(f"      Manual: {match.manual_executive.get('full_name', 'N/A')}")
        
        return comparison_results
    
    def _calculate_comprehensive_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive validation metrics."""
        total_manual_executives = sum(len(execs) for execs in self.reference_data.values())
        total_system_executives = sum(len(execs) for execs in self.system_results.values())
        
        # Detailed match analysis
        exact_matches = 0
        strong_matches = 0
        partial_matches = 0
        weak_matches = 0
        no_matches = 0
        
        total_discovered = 0
        total_with_email = 0
        total_with_linkedin = 0
        total_with_phone = 0
        total_false_positives = 0
        
        discovery_rates = []
        attribution_rates = []
        confidence_scores = []
        
        for result in self.comparison_results.values():
            # Count match types
            for match in result.matches:
                if match.match_type.value == 'exact_match':
                    exact_matches += 1
                elif match.match_type.value == 'strong_match':
                    strong_matches += 1
                elif match.match_type.value == 'partial_match':
                    partial_matches += 1
                elif match.match_type.value == 'weak_match':
                    weak_matches += 1
                else:
                    no_matches += 1
                
                # Track confidence scores for good matches
                if match.match_type.value not in ['no_match', 'weak_match']:
                    confidence_scores.append(match.overall_confidence)
            
            # Count good matches
            good_matches = sum(1 for match in result.matches 
                             if match.match_type.value not in ['no_match', 'weak_match'])
            total_discovered += good_matches
            
            # Count contact types for good matches
            for match in result.matches:
                if match.match_type.value not in ['no_match', 'weak_match']:
                    if match.system_executive.get('email'):
                        total_with_email += 1
                    if match.system_executive.get('linkedin_url'):
                        total_with_linkedin += 1
                    if match.system_executive.get('phone'):
                        total_with_phone += 1
            
            # Count false positives
            total_false_positives += len(result.false_positives)
            
            # Track rates
            discovery_rates.append(result.discovery_rate)
            attribution_rates.append(result.attribution_rate)
        
        # Calculate overall rates
        overall_discovery_rate = (total_discovered / total_manual_executives) * 100 if total_manual_executives > 0 else 0
        overall_email_rate = (total_with_email / total_discovered) * 100 if total_discovered > 0 else 0
        overall_linkedin_rate = (total_with_linkedin / total_discovered) * 100 if total_discovered > 0 else 0
        overall_phone_rate = (total_with_phone / total_discovered) * 100 if total_discovered > 0 else 0
        false_positive_rate = (total_false_positives / total_system_executives) * 100 if total_system_executives > 0 else 0
        
        # URL coverage metrics
        successful_urls = sum(1 for result in self.comparison_results.values() 
                            if len(result.system_executives) > 0)
        url_coverage = (successful_urls / len(self.reference_data)) * 100
        
        # Quality metrics
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Manual data baseline
        manual_stats = self.manual_loader.get_statistics()
        
        return {
            'totals': {
                'manual_executives': total_manual_executives,
                'system_executives': total_system_executives,
                'discovered_executives': total_discovered,
                'executives_with_email': total_with_email,
                'executives_with_linkedin': total_with_linkedin,
                'executives_with_phone': total_with_phone,
                'false_positives': total_false_positives,
                'unique_urls': len(self.reference_data)
            },
            'match_quality': {
                'exact_matches': exact_matches,
                'strong_matches': strong_matches,
                'partial_matches': partial_matches,
                'weak_matches': weak_matches,
                'no_matches': no_matches,
                'average_confidence': avg_confidence
            },
            'discovery_metrics': {
                'overall_discovery_rate': overall_discovery_rate,
                'average_discovery_rate': sum(discovery_rates) / len(discovery_rates) if discovery_rates else 0,
                'url_coverage': url_coverage,
                'successful_urls': successful_urls
            },
            'contact_attribution': {
                'email_attribution_rate': overall_email_rate,
                'linkedin_attribution_rate': overall_linkedin_rate,
                'phone_attribution_rate': overall_phone_rate,
                'false_positive_rate': false_positive_rate
            },
            'manual_data_baseline': {
                'email_coverage': manual_stats['email_coverage_percentage'],
                'linkedin_coverage': manual_stats['linkedin_coverage_percentage'],
                'phone_coverage': manual_stats['phone_coverage_percentage']
            },
            'performance_assessment': {
                'discovery_excellent': overall_discovery_rate >= 90.0,
                'discovery_good': overall_discovery_rate >= 70.0,
                'email_attribution_excellent': overall_email_rate >= 80.0,
                'email_attribution_good': overall_email_rate >= 60.0,
                'false_positive_acceptable': false_positive_rate <= 5.0,
                'url_coverage_complete': url_coverage >= 100.0
            }
        }
    
    def _generate_validation_results(self, execution_time: float) -> Dict[str, Any]:
        """Generate comprehensive validation results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = {
            'metadata': {
                'timestamp': timestamp,
                'execution_time_seconds': execution_time,
                'excel_file': self.excel_file_path,
                'system_pipeline': 'RobustExecutivePipeline',
                'validation_framework_version': '1.0.0',
                'urls_tested': len(self.reference_data)
            },
            'overall_metrics': self.overall_metrics,
            'url_results': {},
            'detailed_comparison': {},
            'recommendations': self._generate_recommendations()
        }
        
        # Add URL-level results
        for url, comparison_result in self.comparison_results.items():
            results['url_results'][url] = {
                'manual_executives_count': len(comparison_result.manual_executives),
                'system_executives_count': len(comparison_result.system_executives),
                'discovery_rate': comparison_result.discovery_rate,
                'attribution_rate': comparison_result.attribution_rate,
                'matches_count': len(comparison_result.matches),
                'missing_count': len(comparison_result.missing_executives),
                'false_positives_count': len(comparison_result.false_positives),
                'match_types': self._analyze_match_types(comparison_result.matches)
            }
            
            # Add detailed comparison data
            results['detailed_comparison'][url] = {
                'system_executives': comparison_result.system_executives,
                'manual_executives': comparison_result.manual_executives,
                'matches': [
                    {
                        'system_executive': match.system_executive,
                        'manual_executive': match.manual_executive,
                        'match_type': match.match_type.value,
                        'confidence': match.overall_confidence,
                        'field_scores': match.field_scores,
                        'reasons': match.match_reasons
                    }
                    for match in comparison_result.matches
                ],
                'missing_executives': comparison_result.missing_executives,
                'false_positives': comparison_result.false_positives
            }
        
        return results
    
    def _analyze_match_types(self, matches) -> Dict[str, int]:
        """Analyze the distribution of match types."""
        match_counts = {
            'exact_match': 0,
            'strong_match': 0,
            'partial_match': 0,
            'weak_match': 0,
            'no_match': 0
        }
        
        for match in matches:
            match_counts[match.match_type.value] += 1
        
        return match_counts
    
    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations based on results."""
        recommendations = []
        metrics = self.overall_metrics
        
        discovery_rate = metrics['discovery_metrics']['overall_discovery_rate']
        email_rate = metrics['contact_attribution']['email_attribution_rate']
        false_positive_rate = metrics['contact_attribution']['false_positive_rate']
        
        if discovery_rate < 70.0:
            recommendations.append("🔍 Low discovery rate: Enhance executive detection algorithms")
        elif discovery_rate < 90.0:
            recommendations.append("🎯 Good discovery rate: Fine-tune for excellent performance")
        
        if email_rate < 60.0:
            recommendations.append("📧 Poor email attribution: Improve contact linking algorithms")
        elif email_rate < 80.0:
            recommendations.append("📬 Good email attribution: Optimize for excellent performance")
        
        if false_positive_rate > 10.0:
            recommendations.append("❌ High false positives: Strengthen quality filters")
        elif false_positive_rate > 5.0:
            recommendations.append("⚠️ Moderate false positives: Refine validation rules")
        
        if metrics['discovery_metrics']['url_coverage'] < 100.0:
            recommendations.append("🌐 Incomplete URL coverage: Investigate failed URL processing")
        
        avg_confidence = metrics['match_quality']['average_confidence']
        if avg_confidence < 0.7:
            recommendations.append("🎪 Low match confidence: Review comparison algorithms")
        
        if not recommendations:
            recommendations.append("🎉 Excellent performance! System ready for production")
        
        return recommendations
    
    def save_results(self, results: Dict[str, Any], 
                    output_file: Optional[str] = None) -> str:
        """Save validation results to JSON file."""
        if output_file is None:
            timestamp = results['metadata']['timestamp']
            output_file = f"real_pipeline_validation_results_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Results saved to {output_file}")
        return output_file
    
    def print_comprehensive_report(self, results: Dict[str, Any]):
        """Print a detailed comprehensive report."""
        metrics = results['overall_metrics']
        
        print("\n" + "="*90)
        print("🎯 REAL PIPELINE 20-URL VALIDATION COMPREHENSIVE REPORT")
        print("="*90)
        
        print(f"\n📊 EXECUTION SUMMARY:")
        print(f"  ⏱️  Execution Time: {results['metadata']['execution_time_seconds']:.2f} seconds")
        print(f"  🌐 URLs Tested: {results['metadata']['urls_tested']}")
        print(f"  🔧 Pipeline: {results['metadata']['system_pipeline']}")
        
        print(f"\n📈 DISCOVERY PERFORMANCE:")
        discovery = metrics['discovery_metrics']
        totals = metrics['totals']
        print(f"  🎯 Overall Discovery Rate: {discovery['overall_discovery_rate']:.1f}%")
        print(f"  🌐 URL Coverage: {discovery['url_coverage']:.1f}% ({discovery['successful_urls']}/{totals['unique_urls']} URLs)")
        print(f"  👥 Executives Found: {totals['discovered_executives']}/{totals['manual_executives']}")
        
        print(f"\n🎪 MATCH QUALITY ANALYSIS:")
        quality = metrics['match_quality']
        print(f"  💎 Exact Matches: {quality['exact_matches']}")
        print(f"  ⭐ Strong Matches: {quality['strong_matches']}")
        print(f"  🔸 Partial Matches: {quality['partial_matches']}")
        print(f"  ⚠️  Weak Matches: {quality['weak_matches']}")
        print(f"  ❌ No Matches: {quality['no_matches']}")
        print(f"  📊 Average Confidence: {quality['average_confidence']:.3f}")
        
        print(f"\n📧 CONTACT ATTRIBUTION:")
        contact = metrics['contact_attribution']
        print(f"  📧 Email Attribution: {contact['email_attribution_rate']:.1f}% ({totals['executives_with_email']}/{totals['discovered_executives']})")
        print(f"  🔗 LinkedIn Attribution: {contact['linkedin_attribution_rate']:.1f}% ({totals['executives_with_linkedin']}/{totals['discovered_executives']})")
        print(f"  📞 Phone Attribution: {contact['phone_attribution_rate']:.1f}% ({totals['executives_with_phone']}/{totals['discovered_executives']})")
        print(f"  ❌ False Positive Rate: {contact['false_positive_rate']:.1f}%")
        
        print(f"\n🏆 PERFORMANCE ASSESSMENT:")
        assessment = metrics['performance_assessment']
        status_icon = lambda x: "✅" if x else "❌"
        print(f"  {status_icon(assessment['discovery_excellent'])} Discovery Rate ≥90%: {assessment['discovery_excellent']}")
        print(f"  {status_icon(assessment['email_attribution_excellent'])} Email Attribution ≥80%: {assessment['email_attribution_excellent']}")
        print(f"  {status_icon(assessment['false_positive_acceptable'])} False Positive Rate ≤5%: {assessment['false_positive_acceptable']}")
        print(f"  {status_icon(assessment['url_coverage_complete'])} Complete URL Coverage: {assessment['url_coverage_complete']}")
        
        print(f"\n📋 BASELINE COMPARISON:")
        baseline = metrics['manual_data_baseline']
        print(f"  📧 Manual Email Coverage: {baseline['email_coverage']:.1f}%")
        print(f"  🔗 Manual LinkedIn Coverage: {baseline['linkedin_coverage']:.1f}%")
        print(f"  📞 Manual Phone Coverage: {baseline['phone_coverage']:.1f}%")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for i, recommendation in enumerate(results['recommendations'], 1):
            print(f"  {i}. {recommendation}")
        
        # Overall assessment
        all_excellent = (assessment['discovery_excellent'] and 
                        assessment['email_attribution_excellent'] and 
                        assessment['false_positive_acceptable'] and 
                        assessment['url_coverage_complete'])
        
        if all_excellent:
            print(f"\n🎉 OVERALL ASSESSMENT: EXCELLENT - PRODUCTION READY!")
        else:
            good_performance = (discovery['overall_discovery_rate'] >= 70.0 and 
                              contact['email_attribution_rate'] >= 60.0 and 
                              contact['false_positive_rate'] <= 10.0)
            if good_performance:
                print(f"\n⭐ OVERALL ASSESSMENT: GOOD - NEEDS OPTIMIZATION")
            else:
                print(f"\n⚠️  OVERALL ASSESSMENT: NEEDS IMPROVEMENT")
        
        print("="*90)


def main():
    """Main execution function for real pipeline validation."""
    try:
        # Initialize validator
        validator = RealPipelineValidator()
        
        # Run validation with real pipeline
        results = validator.run_validation_with_robust_pipeline()
        
        # Save results
        output_file = validator.save_results(results)
        
        # Print comprehensive report
        validator.print_comprehensive_report(results)
        
        print(f"\n📄 Detailed results saved to: {output_file}")
        print("🎯 Real pipeline validation completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Real pipeline validation failed: {str(e)}")
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 