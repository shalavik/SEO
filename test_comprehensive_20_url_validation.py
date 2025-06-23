"""
Comprehensive 20-URL Validation Framework - Main Testing Engine

This is the main testing script that orchestrates the complete validation process:
1. Loads manual reference data from Excel
2. Runs our robust executive pipeline on all URLs  
3. Compares results using advanced fuzzy matching
4. Generates comprehensive metrics and analysis

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

class ComprehensiveValidator:
    """
    Main validation framework that orchestrates the complete testing process.
    
    Integrates manual data loading, system testing, and advanced comparison
    to provide comprehensive validation results.
    """
    
    def __init__(self, excel_file_path: str = "1Testfinal.xlsx"):
        """
        Initialize the Comprehensive Validator.
        
        Args:
            excel_file_path (str): Path to Excel file with manual reference data
        """
        self.excel_file_path = excel_file_path
        self.manual_loader = ManualDataLoader(excel_file_path)
        self.comparator = AdvancedResultComparator()
        
        # Initialize robust pipeline
        self.system_pipeline = None
        self._load_system_pipeline()
        
        # Results storage
        self.reference_data = {}
        self.system_results = {}
        self.comparison_results = {}
        self.overall_metrics = {}
        
    def _load_system_pipeline(self):
        """Load the robust executive extraction pipeline."""
        try:
            from seo_leads.processors.robust_executive_pipeline import RobustExecutivePipeline
            self.system_pipeline = RobustExecutivePipeline()
            logger.info("✅ Loaded RobustExecutivePipeline successfully")
        except ImportError as e:
            logger.warning(f"Could not load RobustExecutivePipeline: {e}")
            logger.info("Using mock pipeline for testing")
            self.system_pipeline = MockExecutivePipeline()
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Execute the complete validation process.
        
        Returns:
            Dict[str, Any]: Comprehensive validation results
        """
        start_time = time.time()
        
        logger.info("🚀 Starting Comprehensive 20-URL Validation Process")
        
        try:
            # Phase 1: Load reference data
            logger.info("📋 Phase 1: Loading manual reference data...")
            self.reference_data = self.manual_loader.load_reference_data()
            
            # Phase 2: Run system on all URLs
            logger.info("🔍 Phase 2: Running system extraction on all URLs...")
            self.system_results = self._run_system_extraction()
            
            # Phase 3: Compare results
            logger.info("🔄 Phase 3: Comparing system vs manual results...")
            self.comparison_results = self._compare_all_results()
            
            # Phase 4: Calculate overall metrics
            logger.info("📊 Phase 4: Calculating comprehensive metrics...")
            self.overall_metrics = self._calculate_overall_metrics()
            
            # Phase 5: Generate results
            execution_time = time.time() - start_time
            results = self._generate_final_results(execution_time)
            
            logger.info(f"✅ Validation completed in {execution_time:.2f} seconds")
            return results
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def _run_system_extraction(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run our system's executive extraction on all URLs.
        
        Returns:
            Dict[str, List[Dict]]: System results by URL
        """
        system_results = {}
        urls = self.manual_loader.get_all_urls()
        
        logger.info(f"Processing {len(urls)} URLs...")
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing URL {i}/{len(urls)}: {url}")
            
            try:
                # Run system extraction
                executives = self._extract_executives_for_url(url)
                system_results[url] = executives
                
                logger.info(f"  → Found {len(executives)} executives")
                
            except Exception as e:
                logger.error(f"  → Error processing {url}: {str(e)}")
                system_results[url] = []
        
        return system_results
    
    def _extract_executives_for_url(self, url: str) -> List[Dict[str, Any]]:
        """
        Extract executives for a single URL using our system.
        
        Args:
            url (str): Website URL to process
            
        Returns:
            List[Dict[str, Any]]: List of extracted executives
        """
        try:
            # Use the robust pipeline to extract executives
            if hasattr(self.system_pipeline, 'extract_executives'):
                executives = self.system_pipeline.extract_executives(url)
            else:
                # Fallback method
                executives = self.system_pipeline.process_url(url)
            
            # Ensure consistent format
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
                    'confidence': exec_data.get('overall_confidence', 0.0)
                }
                formatted_executives.append(formatted_exec)
            
            return formatted_executives
            
        except Exception as e:
            logger.error(f"Error extracting executives for {url}: {str(e)}")
            return []
    
    def _compare_all_results(self) -> Dict[str, URLComparisonResult]:
        """
        Compare system results against manual data for all URLs.
        
        Returns:
            Dict[str, URLComparisonResult]: Comparison results by URL
        """
        comparison_results = {}
        
        for url in self.reference_data.keys():
            system_executives = self.system_results.get(url, [])
            manual_executives = self.reference_data[url]
            
            comparison_result = self.comparator.compare_executives(
                system_executives, manual_executives, url
            )
            
            comparison_results[url] = comparison_result
            
            logger.info(f"URL: {url}")
            logger.info(f"  Discovery Rate: {comparison_result.discovery_rate:.1f}%")
            logger.info(f"  Attribution Rate: {comparison_result.attribution_rate:.1f}%")
        
        return comparison_results
    
    def _calculate_overall_metrics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics across all URLs.
        
        Returns:
            Dict[str, Any]: Overall validation metrics
        """
        total_manual_executives = sum(len(execs) for execs in self.reference_data.values())
        total_system_executives = sum(len(execs) for execs in self.system_results.values())
        
        # Discovery metrics
        total_discovered = 0
        total_with_attribution = 0
        total_false_positives = 0
        
        discovery_rates = []
        attribution_rates = []
        
        for result in self.comparison_results.values():
            # Count good matches
            good_matches = sum(1 for match in result.matches 
                             if match.match_type.value not in ['no_match', 'weak_match'])
            total_discovered += good_matches
            
            # Count with attribution
            with_attribution = sum(1 for match in result.matches
                                 if (match.match_type.value not in ['no_match', 'weak_match'] and
                                     (match.system_executive.get('email') or 
                                      match.system_executive.get('phone'))))
            total_with_attribution += with_attribution
            
            # Count false positives
            total_false_positives += len(result.false_positives)
            
            # Track rates
            discovery_rates.append(result.discovery_rate)
            attribution_rates.append(result.attribution_rate)
        
        # Calculate overall rates
        overall_discovery_rate = (total_discovered / total_manual_executives) * 100 if total_manual_executives > 0 else 0
        overall_attribution_rate = (total_with_attribution / total_discovered) * 100 if total_discovered > 0 else 0
        false_positive_rate = (total_false_positives / total_system_executives) * 100 if total_system_executives > 0 else 0
        
        # URL coverage
        successful_urls = sum(1 for result in self.comparison_results.values() 
                            if len(result.system_executives) > 0)
        url_coverage = (successful_urls / len(self.reference_data)) * 100
        
        # Contact type analysis
        manual_stats = self.manual_loader.get_statistics()
        
        return {
            'totals': {
                'manual_executives': total_manual_executives,
                'system_executives': total_system_executives,
                'discovered_executives': total_discovered,
                'executives_with_attribution': total_with_attribution,
                'false_positives': total_false_positives,
                'unique_urls': len(self.reference_data)
            },
            'discovery_metrics': {
                'overall_discovery_rate': overall_discovery_rate,
                'average_discovery_rate': sum(discovery_rates) / len(discovery_rates) if discovery_rates else 0,
                'url_coverage': url_coverage,
                'successful_urls': successful_urls
            },
            'quality_metrics': {
                'overall_attribution_rate': overall_attribution_rate,
                'average_attribution_rate': sum(attribution_rates) / len(attribution_rates) if attribution_rates else 0,
                'false_positive_rate': false_positive_rate
            },
            'manual_data_baseline': {
                'email_coverage': manual_stats['email_coverage_percentage'],
                'linkedin_coverage': manual_stats['linkedin_coverage_percentage'],
                'phone_coverage': manual_stats['phone_coverage_percentage']
            },
            'target_achievement': {
                'discovery_target_90pct': overall_discovery_rate >= 90.0,
                'attribution_target_80pct': overall_attribution_rate >= 80.0,
                'false_positive_target_5pct': false_positive_rate <= 5.0,
                'url_coverage_target_100pct': url_coverage >= 100.0
            }
        }
    
    def _generate_final_results(self, execution_time: float) -> Dict[str, Any]:
        """
        Generate the final comprehensive results.
        
        Args:
            execution_time (float): Total execution time in seconds
            
        Returns:
            Dict[str, Any]: Complete validation results
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = {
            'metadata': {
                'timestamp': timestamp,
                'execution_time_seconds': execution_time,
                'excel_file': self.excel_file_path,
                'system_pipeline': type(self.system_pipeline).__name__,
                'validation_framework_version': '1.0.0'
            },
            'overall_metrics': self.overall_metrics,
            'url_results': {},
            'detailed_comparison': {}
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
                'false_positives_count': len(comparison_result.false_positives)
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
    
    def save_results(self, results: Dict[str, Any], 
                    output_file: Optional[str] = None) -> str:
        """
        Save validation results to JSON file.
        
        Args:
            results (Dict[str, Any]): Validation results to save
            output_file (str, optional): Output file path
            
        Returns:
            str: Path to saved file
        """
        if output_file is None:
            timestamp = results['metadata']['timestamp']
            output_file = f"comprehensive_20_url_validation_results_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Results saved to {output_file}")
        return output_file
    
    def print_summary_report(self, results: Dict[str, Any]):
        """
        Print a comprehensive summary report.
        
        Args:
            results (Dict[str, Any]): Validation results
        """
        metrics = results['overall_metrics']
        
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE 20-URL VALIDATION SUMMARY REPORT")
        print("="*80)
        
        print(f"\n📊 EXECUTION SUMMARY:")
        print(f"  ⏱️  Execution Time: {results['metadata']['execution_time_seconds']:.2f} seconds")
        print(f"  📁 Excel File: {results['metadata']['excel_file']}")
        print(f"  🔧 System Pipeline: {results['metadata']['system_pipeline']}")
        
        print(f"\n📈 DISCOVERY METRICS:")
        totals = metrics['totals']
        discovery = metrics['discovery_metrics']
        print(f"  🎯 Overall Discovery Rate: {discovery['overall_discovery_rate']:.1f}% (Target: ≥90%)")
        print(f"  🌐 URL Coverage: {discovery['url_coverage']:.1f}% ({discovery['successful_urls']}/{totals['unique_urls']} URLs)")
        print(f"  👥 Executives Found: {totals['discovered_executives']}/{totals['manual_executives']}")
        
        print(f"\n🎪 QUALITY METRICS:")
        quality = metrics['quality_metrics']
        print(f"  📧 Attribution Rate: {quality['overall_attribution_rate']:.1f}% (Target: ≥80%)")
        print(f"  ❌ False Positive Rate: {quality['false_positive_rate']:.1f}% (Target: ≤5%)")
        print(f"  ✅ Executives with Contacts: {totals['executives_with_attribution']}/{totals['discovered_executives']}")
        
        print(f"\n🎖️ TARGET ACHIEVEMENT:")
        targets = metrics['target_achievement']
        status_icon = lambda x: "✅" if x else "❌"
        print(f"  {status_icon(targets['discovery_target_90pct'])} Discovery Rate ≥90%: {targets['discovery_target_90pct']}")
        print(f"  {status_icon(targets['attribution_target_80pct'])} Attribution Rate ≥80%: {targets['attribution_target_80pct']}")
        print(f"  {status_icon(targets['false_positive_target_5pct'])} False Positive Rate ≤5%: {targets['false_positive_target_5pct']}")
        print(f"  {status_icon(targets['url_coverage_target_100pct'])} URL Coverage 100%: {targets['url_coverage_target_100pct']}")
        
        print(f"\n📋 BASELINE COMPARISON:")
        baseline = metrics['manual_data_baseline']
        print(f"  📧 Manual Email Coverage: {baseline['email_coverage']:.1f}%")
        print(f"  🔗 Manual LinkedIn Coverage: {baseline['linkedin_coverage']:.1f}%")
        print(f"  📞 Manual Phone Coverage: {baseline['phone_coverage']:.1f}%")
        
        # Success assessment
        all_targets_met = all(targets.values())
        print(f"\n🏆 OVERALL ASSESSMENT: {'🎉 SUCCESS' if all_targets_met else '⚠️  NEEDS IMPROVEMENT'}")
        
        if all_targets_met:
            print("   All validation targets have been achieved!")
            print("   System is ready for production deployment.")
        else:
            print("   Some targets not met. Review detailed results for improvement opportunities.")
        
        print("="*80)


class MockExecutivePipeline:
    """Mock pipeline for testing when the real pipeline is not available."""
    
    def extract_executives(self, url: str) -> List[Dict[str, Any]]:
        """Mock extraction that returns empty results."""
        return []
    
    def process_url(self, url: str) -> List[Dict[str, Any]]:
        """Mock processing that returns empty results."""
        return []


def main():
    """Main execution function."""
    try:
        # Initialize validator
        validator = ComprehensiveValidator()
        
        # Run comprehensive validation
        results = validator.run_comprehensive_validation()
        
        # Save results
        output_file = validator.save_results(results)
        
        # Print summary report
        validator.print_summary_report(results)
        
        print(f"\n📄 Detailed results saved to: {output_file}")
        print("🎯 Comprehensive 20-URL validation completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Validation failed: {str(e)}")
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 