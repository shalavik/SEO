"""
Phase 1 Implementation Validation Test

This test validates the Phase 1 critical fixes implementation against the baseline
validation results from the comprehensive 20-URL validation.

Key Phase 1 improvements being tested:
1. Enhanced name extraction - target: 20% → 45% discovery rate
2. Quality control system - target: 55.6% → <15% false positive rate  
3. Confidence thresholding - target: 0.384 → >0.600 average confidence
4. Contextual validation - target: better executive identification

Author: AI Assistant
Date: 2025-01-23
Version: 1.0.0 - Phase 1 Validation Test
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import traceback

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from manual_data_loader import ManualDataLoader
from advanced_result_comparator import AdvancedResultComparator, URLComparisonResult

# Import Phase 1 enhanced components
try:
    from seo_leads.processors.enhanced_robust_executive_pipeline import (
        EnhancedRobustExecutivePipeline, 
        EnhancedExecutiveProfile
    )
    from seo_leads.ai.enhanced_name_extractor import EnhancedNameExtractor
    from seo_leads.ai.executive_quality_controller import ExecutiveQualityController
    PHASE1_AVAILABLE = True
    print("✅ Phase 1 enhanced components imported successfully")
except ImportError as e:
    print(f"⚠️ Phase 1 components not available: {e}")
    PHASE1_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase1ValidationTest:
    """
    Comprehensive validation test for Phase 1 implementation.
    
    Compares Phase 1 enhanced pipeline against baseline results and manual data.
    """
    
    def __init__(self, excel_file_path: str = "1Testfinal.xlsx"):
        """Initialize Phase 1 validation test"""
        self.excel_file_path = excel_file_path
        self.manual_loader = ManualDataLoader(excel_file_path)
        self.comparator = AdvancedResultComparator()
        
        # Initialize Phase 1 components if available
        if PHASE1_AVAILABLE:
            self.enhanced_pipeline = EnhancedRobustExecutivePipeline()
            self.enhanced_extractor = EnhancedNameExtractor()
            self.quality_controller = ExecutiveQualityController()
        else:
            self.enhanced_pipeline = None
            
        # Baseline results from comprehensive validation
        self.baseline_metrics = {
            'discovery_rate': 20.0,
            'false_positive_rate': 55.6,
            'average_confidence': 0.384,
            'url_coverage': 60.0,
            'executives_found': 4,
            'total_manual_executives': 20
        }
        
        # Phase 1 targets
        self.phase1_targets = {
            'discovery_rate': 45.0,  # Target: 20% → 45%
            'false_positive_rate': 15.0,  # Target: 55.6% → <15%
            'average_confidence': 0.600,  # Target: 0.384 → >0.600
            'url_coverage': 75.0,  # Target: 60% → 75%
            'improvement_threshold': 1.5  # Minimum improvement factor
        }
        
        # Results storage
        self.reference_data = {}
        self.phase1_results = {}
        self.comparison_results = {}
        self.improvement_metrics = {}
    
    def run_phase1_validation(self) -> Dict[str, Any]:
        """
        Run comprehensive Phase 1 validation test.
        
        Returns:
            Dict containing validation results, improvements, and recommendations
        """
        start_time = time.time()
        
        logger.info("🚀 Starting Phase 1 Implementation Validation")
        logger.info("📊 Testing enhanced extraction, quality control, and false positive reduction")
        
        try:
            # Phase 1: Load reference data
            logger.info("📋 Phase 1: Loading manual reference data...")
            self.reference_data = self.manual_loader.load_reference_data()
            
            if not PHASE1_AVAILABLE:
                logger.error("❌ Phase 1 components not available - cannot run validation")
                return self._create_error_result("Phase 1 components not available")
            
            # Phase 2: Run Phase 1 enhanced extraction
            logger.info("⚡ Phase 2: Running Phase 1 enhanced pipeline...")
            self.phase1_results = self._run_phase1_extraction()
            
            # Phase 3: Compare results with advanced analysis
            logger.info("🔄 Phase 3: Advanced comparison analysis...")
            self.comparison_results = self._compare_phase1_results()
            
            # Phase 4: Calculate improvement metrics
            logger.info("📈 Phase 4: Calculating improvement metrics...")
            self.improvement_metrics = self._calculate_improvement_metrics()
            
            # Phase 5: Generate comprehensive results
            execution_time = time.time() - start_time
            results = self._generate_phase1_validation_results(execution_time)
            
            logger.info(f"✅ Phase 1 validation completed in {execution_time:.2f} seconds")
            return results
            
        except Exception as e:
            logger.error(f"❌ Phase 1 validation failed: {str(e)}")
            logger.error(traceback.format_exc())
            return self._create_error_result(str(e))
    
    def _run_phase1_extraction(self) -> Dict[str, List[Dict[str, Any]]]:
        """Run Phase 1 enhanced extraction on test URLs"""
        phase1_results = {}
        
        # Sample HTML content for each URL (simplified for testing)
        test_content_samples = {
            "http://www.vernonheating.com": self._get_sample_content("vernon_heating"),
            "http://www.kwsmith.com": self._get_sample_content("kw_smith"),
            "http://thejoyceagency.com": self._get_sample_content("joyce_agency"),
            "http://sagewater.com": self._get_sample_content("sage_water"),
            "http://anhplumbing.com": self._get_sample_content("anh_plumbing")
        }
        
        for i, (url, content) in enumerate(test_content_samples.items(), 1):
            logger.info(f"Processing URL {i}/{len(test_content_samples)}: {url}")
            
            try:
                # Create company info
                company_info = {
                    'name': self._extract_company_name_from_url(url),
                    'domain': url,
                    'url': url
                }
                
                # Run Phase 1 enhanced extraction
                enhanced_profiles = self.enhanced_pipeline.extract_executives_enhanced(content, company_info)
                
                # Convert to standard format for comparison
                executives = []
                for profile in enhanced_profiles:
                    executives.append({
                        'name': profile.name,
                        'title': profile.title,
                        'email': profile.email,
                        'phone': profile.phone,
                        'linkedin_url': profile.linkedin_url,
                        'confidence': profile.overall_confidence,
                        'extraction_method': 'phase1_enhanced',
                        'context': f"Phase1: {profile.discovery_quality} quality, {profile.false_positive_risk} risk",
                        'source_sections': [profile.source_section],
                        
                        # Phase 1 specific metadata
                        'discovery_quality': profile.discovery_quality,
                        'false_positive_risk': profile.false_positive_risk,
                        'validation_status': profile.validation_status,
                        'phase1_enhanced': True
                    })
                
                phase1_results[url] = executives
                
                logger.info(f"  → Found {len(executives)} executives")
                for exec_data in executives:
                    logger.info(f"    • {exec_data['name']} ({exec_data['title']}) - "
                              f"Confidence: {exec_data['confidence']:.3f}")
                
            except Exception as e:
                logger.error(f"  → Error processing {url}: {str(e)}")
                phase1_results[url] = []
        
        return phase1_results
    
    def _get_sample_content(self, company_type: str) -> str:
        """Get sample HTML content for testing (simplified)"""
        
        content_templates = {
            "vernon_heating": """
            <html>
            <head><title>Vernon Heating Services</title></head>
            <body>
                <div class="about">
                    <h2>About Vernon Heating</h2>
                    <p>Vernon Heating Services has been serving the community for over 20 years. 
                    Founded by John Vernon, our family-run business specializes in central heating 
                    installations and boiler repairs.</p>
                    <p>Contact John Vernon, Owner for all your heating needs.</p>
                </div>
                <div class="contact">
                    <h3>Contact Information</h3>
                    <p>Email: info@vernonheating.com</p>
                    <p>Phone: 01234 567890</p>
                    <p>Speak to John Vernon directly for quotes and advice.</p>
                </div>
            </body>
            </html>
            """,
            
            "kw_smith": """
            <html>
            <head><title>K W Smith Plumbing</title></head>
            <body>
                <section id="about">
                    <h1>K W Smith Plumbing Services</h1>
                    <p>Ken Smith, Director of K W Smith Plumbing, brings over 15 years 
                    of experience in residential and commercial plumbing.</p>
                    <p>As a fully qualified and Gas Safe registered engineer, Ken Smith 
                    ensures all work meets the highest standards.</p>
                </section>
                <footer>
                    <p>Contact Ken Smith: kevin@kwsmith.com | 0161 234 5678</p>
                </footer>
            </body>
            </html>
            """,
            
            "joyce_agency": """
            <html>
            <head><title>The Joyce Agency</title></head>
            <body>
                <div class="team">
                    <h2>Meet Our Team</h2>
                    <div class="team-member">
                        <h3>Patricia Joyce - Agency Director</h3>
                        <p>Patricia Joyce founded The Joyce Agency in 2010 with a vision 
                        to provide exceptional marketing services.</p>
                        <p>Email: patricia@thejoyceagency.com</p>
                        <p>LinkedIn: https://www.linkedin.com/in/patricia-joyce-marketing</p>
                    </div>
                    <div class="team-member">
                        <h3>Troy Joyce - Operations Manager</h3>
                        <p>Troy Joyce handles day-to-day operations and client relationships.</p>
                        <p>Email: troy@thejoyceagency.com</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            
            "sage_water": """
            <html>
            <head><title>Sage Water Solutions</title></head>
            <body>
                <section class="leadership">
                    <h2>Leadership Team</h2>
                    <div class="executive">
                        <h3>Peter Page, President</h3>
                        <p>Peter Page leads Sage Water Solutions with over 25 years 
                        of experience in water treatment and management.</p>
                        <p>Contact: ppage@sagewater.com | 0203 456 7890</p>
                        <p>LinkedIn: https://www.linkedin.com/in/peter-page-water</p>
                    </div>
                </section>
            </body>
            </html>
            """,
            
            "anh_plumbing": """
            <html>
            <head><title>ANH Plumbing Services</title></head>
            <body>
                <div class="company-info">
                    <h1>ANH Plumbing Services</h1>
                    <p>Professional plumbing services for residential and commercial properties.</p>
                    <p>Established in 2005, we provide reliable and efficient plumbing solutions.</p>
                </div>
                <div class="contact">
                    <h2>Contact Us</h2>
                    <p>For all inquiries, contact our office:</p>
                    <p>Phone: 01455 822896</p>
                    <p>Email: admin@anhplumbing.com</p>
                    <div class="staff-note">
                        <p>Customer review: "Douglas Hart provided excellent service for our 
                        bathroom renovation. Highly recommended!" - Mrs. Johnson</p>
                    </div>
                </div>
            </body>
            </html>
            """
        }
        
        return content_templates.get(company_type, "<html><body><p>Sample content</p></body></html>")
    
    def _extract_company_name_from_url(self, url: str) -> str:
        """Extract company name from URL"""
        company_names = {
            "http://www.vernonheating.com": "Vernon Heating Services",
            "http://www.kwsmith.com": "K W Smith Plumbing",
            "http://thejoyceagency.com": "The Joyce Agency", 
            "http://sagewater.com": "Sage Water Solutions",
            "http://anhplumbing.com": "ANH Plumbing Services"
        }
        return company_names.get(url, "Unknown Company")
    
    def _compare_phase1_results(self) -> Dict[str, URLComparisonResult]:
        """Compare Phase 1 results with manual reference data"""
        comparison_results = {}
        
        for url in self.reference_data.keys():
            if url in self.phase1_results:
                system_executives = self.phase1_results[url]
                manual_executives = self.reference_data[url]
                
                logger.info(f"\nComparing Phase 1 results for {url}:")
                logger.info(f"  Phase 1 System: {len(system_executives)} executives")
                logger.info(f"  Manual Reference: {len(manual_executives)} executives")
                
                comparison_result = self.comparator.compare_executives(
                    system_executives, manual_executives, url
                )
                
                comparison_results[url] = comparison_result
                
                # Log detailed comparison
                logger.info(f"  Discovery Rate: {comparison_result.discovery_rate:.1f}%")
                logger.info(f"  Attribution Rate: {comparison_result.attribution_rate:.1f}%")
                logger.info(f"  Matches: {len(comparison_result.matches)}")
                logger.info(f"  False Positives: {len(comparison_result.false_positives)}")
                
                # Log Phase 1 specific metrics
                for i, exec_data in enumerate(system_executives):
                    logger.info(f"    Executive {i+1}: {exec_data['name']} "
                              f"(Quality: {exec_data.get('discovery_quality', 'unknown')}, "
                              f"Risk: {exec_data.get('false_positive_risk', 'unknown')})")
        
        return comparison_results
    
    def _calculate_improvement_metrics(self) -> Dict[str, Any]:
        """Calculate Phase 1 improvement metrics vs baseline"""
        
        # Calculate current Phase 1 metrics
        total_manual_executives = sum(len(execs) for execs in self.reference_data.values())
        total_system_executives = sum(len(execs) for execs in self.phase1_results.values())
        
        # Count good matches and false positives
        total_discovered = 0
        total_false_positives = 0
        confidence_scores = []
        
        urls_with_results = 0
        
        for result in self.comparison_results.values():
            # Count good matches (excluding weak/no matches)
            good_matches = sum(1 for match in result.matches 
                             if match.match_type.value not in ['no_match', 'weak_match'])
            total_discovered += good_matches
            
            # Count false positives
            total_false_positives += len(result.false_positives)
            
            # Collect confidence scores for good matches
            for match in result.matches:
                if match.match_type.value not in ['no_match', 'weak_match']:
                    confidence_scores.append(match.overall_confidence)
            
            # Count URLs with results
            if len(result.system_executives) > 0:
                urls_with_results += 1
        
        # Calculate Phase 1 metrics
        current_discovery_rate = (total_discovered / total_manual_executives) * 100 if total_manual_executives > 0 else 0
        current_false_positive_rate = (total_false_positives / total_system_executives) * 100 if total_system_executives > 0 else 0
        current_average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        current_url_coverage = (urls_with_results / len(self.reference_data)) * 100
        
        # Calculate improvements
        discovery_improvement = current_discovery_rate - self.baseline_metrics['discovery_rate']
        false_positive_improvement = self.baseline_metrics['false_positive_rate'] - current_false_positive_rate
        confidence_improvement = current_average_confidence - self.baseline_metrics['average_confidence']
        coverage_improvement = current_url_coverage - self.baseline_metrics['url_coverage']
        
        # Calculate improvement factors
        discovery_factor = current_discovery_rate / self.baseline_metrics['discovery_rate'] if self.baseline_metrics['discovery_rate'] > 0 else 0
        
        # Phase 1 quality analysis
        quality_distribution = self._analyze_phase1_quality()
        
        # Target achievement analysis
        target_achievement = {
            'discovery_rate': {
                'current': current_discovery_rate,
                'target': self.phase1_targets['discovery_rate'],
                'achieved': current_discovery_rate >= self.phase1_targets['discovery_rate']
            },
            'false_positive_rate': {
                'current': current_false_positive_rate,
                'target': self.phase1_targets['false_positive_rate'],
                'achieved': current_false_positive_rate <= self.phase1_targets['false_positive_rate']
            },
            'average_confidence': {
                'current': current_average_confidence,
                'target': self.phase1_targets['average_confidence'],
                'achieved': current_average_confidence >= self.phase1_targets['average_confidence']
            },
            'url_coverage': {
                'current': current_url_coverage,
                'target': self.phase1_targets['url_coverage'],
                'achieved': current_url_coverage >= self.phase1_targets['url_coverage']
            }
        }
        
        return {
            'baseline_metrics': self.baseline_metrics,
            'current_metrics': {
                'discovery_rate': current_discovery_rate,
                'false_positive_rate': current_false_positive_rate,
                'average_confidence': current_average_confidence,
                'url_coverage': current_url_coverage,
                'executives_found': total_discovered,
                'total_system_executives': total_system_executives
            },
            'improvements': {
                'discovery_rate_improvement': discovery_improvement,
                'false_positive_improvement': false_positive_improvement,
                'confidence_improvement': confidence_improvement,
                'coverage_improvement': coverage_improvement,
                'discovery_improvement_factor': discovery_factor
            },
            'target_achievement': target_achievement,
            'quality_distribution': quality_distribution,
            'overall_improvement_score': self._calculate_overall_improvement_score(target_achievement)
        }
    
    def _analyze_phase1_quality(self) -> Dict[str, Any]:
        """Analyze Phase 1 specific quality metrics"""
        quality_counts = {'excellent': 0, 'good': 0, 'poor': 0}
        risk_counts = {'low': 0, 'medium': 0, 'high': 0}
        validation_counts = {'validated': 0, 'flagged': 0, 'rejected': 0}
        
        total_executives = 0
        
        for url_results in self.phase1_results.values():
            for exec_data in url_results:
                total_executives += 1
                
                quality = exec_data.get('discovery_quality', 'unknown')
                if quality in quality_counts:
                    quality_counts[quality] += 1
                
                risk = exec_data.get('false_positive_risk', 'unknown')
                if risk in risk_counts:
                    risk_counts[risk] += 1
                
                validation = exec_data.get('validation_status', 'unknown')
                if validation in validation_counts:
                    validation_counts[validation] += 1
        
        return {
            'total_executives': total_executives,
            'discovery_quality': quality_counts,
            'false_positive_risk': risk_counts,
            'validation_status': validation_counts,
            'quality_percentage': {
                'excellent': (quality_counts['excellent'] / total_executives) * 100 if total_executives > 0 else 0,
                'good_or_excellent': ((quality_counts['excellent'] + quality_counts['good']) / total_executives) * 100 if total_executives > 0 else 0
            },
            'risk_percentage': {
                'low_risk': (risk_counts['low'] / total_executives) * 100 if total_executives > 0 else 0,
                'high_risk': (risk_counts['high'] / total_executives) * 100 if total_executives > 0 else 0
            }
        }
    
    def _calculate_overall_improvement_score(self, target_achievement: Dict) -> float:
        """Calculate overall improvement score for Phase 1"""
        scores = []
        
        for metric, data in target_achievement.items():
            if data['achieved']:
                scores.append(1.0)
            else:
                # Partial score based on progress toward target
                if metric == 'false_positive_rate':
                    # Lower is better for false positive rate
                    if data['target'] > 0:
                        progress = max(0, 1 - (data['current'] / (data['target'] * 2)))
                    else:
                        progress = 1.0 if data['current'] == 0 else 0.5
                else:
                    # Higher is better for other metrics
                    if data['target'] > 0:
                        progress = min(1.0, data['current'] / data['target'])
                    else:
                        progress = 0.5
                scores.append(progress)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _generate_phase1_validation_results(self, execution_time: float) -> Dict[str, Any]:
        """Generate comprehensive Phase 1 validation results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate performance assessment
        overall_score = self.improvement_metrics['overall_improvement_score']
        performance_rating = self._get_performance_rating(overall_score)
        
        # Generate recommendations
        recommendations = self._generate_phase1_recommendations()
        
        results = {
            'metadata': {
                'timestamp': timestamp,
                'execution_time_seconds': execution_time,
                'test_type': 'phase1_implementation_validation',
                'excel_file': self.excel_file_path,
                'pipeline_version': 'enhanced_robust_pipeline_v2.0.0',
                'phase1_components': ['enhanced_name_extractor', 'executive_quality_controller'],
                'urls_tested': len(self.reference_data),
                'phase1_available': PHASE1_AVAILABLE
            },
            
            'baseline_comparison': {
                'baseline_metrics': self.improvement_metrics['baseline_metrics'],
                'current_metrics': self.improvement_metrics['current_metrics'],
                'improvements': self.improvement_metrics['improvements'],
                'improvement_summary': {
                    'discovery_rate': f"{self.improvement_metrics['improvements']['discovery_rate_improvement']:+.1f}%",
                    'false_positive_rate': f"{self.improvement_metrics['improvements']['false_positive_improvement']:+.1f}%",
                    'average_confidence': f"{self.improvement_metrics['improvements']['confidence_improvement']:+.3f}",
                    'url_coverage': f"{self.improvement_metrics['improvements']['coverage_improvement']:+.1f}%"
                }
            },
            
            'phase1_target_achievement': self.improvement_metrics['target_achievement'],
            
            'quality_analysis': self.improvement_metrics['quality_distribution'],
            
            'performance_assessment': {
                'overall_improvement_score': overall_score,
                'performance_rating': performance_rating,
                'phase1_status': 'success' if overall_score >= 0.7 else 'partial' if overall_score >= 0.4 else 'needs_work',
                'ready_for_phase2': overall_score >= 0.6,
                'critical_issues_resolved': self._assess_critical_issues_resolved()
            },
            
            'detailed_results': {
                'url_comparisons': {},
                'executive_details': self._compile_executive_details()
            },
            
            'phase1_component_performance': self._get_component_performance(),
            
            'recommendations': recommendations,
            
            'next_steps': self._generate_next_steps(overall_score)
        }
        
        # Add detailed URL comparisons
        for url, comparison_result in self.comparison_results.items():
            results['detailed_results']['url_comparisons'][url] = {
                'manual_executives_count': len(comparison_result.manual_executives),
                'system_executives_count': len(comparison_result.system_executives),
                'discovery_rate': comparison_result.discovery_rate,
                'attribution_rate': comparison_result.attribution_rate,
                'matches_count': len(comparison_result.matches),
                'false_positives_count': len(comparison_result.false_positives),
                'match_quality': self._analyze_match_quality(comparison_result.matches)
            }
        
        return results
    
    def _get_performance_rating(self, score: float) -> str:
        """Get performance rating based on improvement score"""
        if score >= 0.9:
            return "Exceptional - Exceeds all targets"
        elif score >= 0.7:
            return "Excellent - Meets most targets"
        elif score >= 0.5:
            return "Good - Significant improvement"
        elif score >= 0.3:
            return "Fair - Some improvement"
        else:
            return "Poor - Limited improvement"
    
    def _assess_critical_issues_resolved(self) -> Dict[str, bool]:
        """Assess if critical issues from baseline have been resolved"""
        current = self.improvement_metrics['current_metrics']
        
        return {
            'false_positive_rate_reduced': current['false_positive_rate'] < 30.0,  # Significant reduction
            'discovery_rate_improved': current['discovery_rate'] > 30.0,  # Meaningful improvement
            'confidence_increased': current['average_confidence'] > 0.5,  # Better than baseline
            'url_coverage_maintained': current['url_coverage'] >= 60.0  # At least baseline
        }
    
    def _compile_executive_details(self) -> List[Dict[str, Any]]:
        """Compile detailed executive information for analysis"""
        executive_details = []
        
        for url, executives in self.phase1_results.items():
            for exec_data in executives:
                detail = {
                    'url': url,
                    'name': exec_data['name'],
                    'title': exec_data['title'],
                    'confidence': exec_data['confidence'],
                    'discovery_quality': exec_data.get('discovery_quality', 'unknown'),
                    'false_positive_risk': exec_data.get('false_positive_risk', 'unknown'),
                    'validation_status': exec_data.get('validation_status', 'unknown'),
                    'extraction_method': exec_data.get('extraction_method', 'unknown'),
                    'phase1_enhanced': exec_data.get('phase1_enhanced', False)
                }
                executive_details.append(detail)
        
        return executive_details
    
    def _get_component_performance(self) -> Dict[str, Any]:
        """Get performance metrics for Phase 1 components"""
        if not PHASE1_AVAILABLE:
            return {'status': 'components_not_available'}
        
        # Get quality controller metrics
        quality_metrics = self.quality_controller.get_quality_metrics()
        
        # Get enhanced pipeline metrics
        pipeline_metrics = self.enhanced_pipeline.get_enhanced_performance_summary()
        
        return {
            'enhanced_name_extractor': {
                'status': 'active',
                'extraction_methods': ['pattern_match', 'spacy_ner', 'nltk_ner', 'regex_pattern'],
                'section_analysis': True
            },
            'executive_quality_controller': quality_metrics,
            'enhanced_pipeline': pipeline_metrics
        }
    
    def _analyze_match_quality(self, matches: List) -> Dict[str, int]:
        """Analyze quality of matches"""
        quality_counts = {
            'exact_match': 0,
            'strong_match': 0,
            'partial_match': 0,
            'weak_match': 0,
            'no_match': 0
        }
        
        for match in matches:
            match_type = match.match_type.value
            if match_type in quality_counts:
                quality_counts[match_type] += 1
        
        return quality_counts
    
    def _generate_phase1_recommendations(self) -> List[str]:
        """Generate Phase 1 specific recommendations"""
        recommendations = []
        current = self.improvement_metrics['current_metrics']
        targets = self.improvement_metrics['target_achievement']
        
        # Discovery rate recommendations
        if not targets['discovery_rate']['achieved']:
            if current['discovery_rate'] < 30.0:
                recommendations.append("🔍 Discovery rate still low - review enhanced extraction patterns")
            else:
                recommendations.append("📈 Good discovery improvement - fine-tune for target achievement")
        else:
            recommendations.append("✅ Discovery rate target achieved - excellent improvement")
        
        # False positive recommendations
        if not targets['false_positive_rate']['achieved']:
            if current['false_positive_rate'] > 30.0:
                recommendations.append("❌ False positive rate still high - strengthen quality validation")
            else:
                recommendations.append("⚠️ Good false positive reduction - optimize further")
        else:
            recommendations.append("✅ False positive target achieved - excellent quality control")
        
        # Confidence recommendations
        if not targets['average_confidence']['achieved']:
            recommendations.append("🎪 Confidence below target - review validation algorithms")
        else:
            recommendations.append("✅ Confidence target achieved - strong validation")
        
        # Quality distribution recommendations
        quality_dist = self.improvement_metrics['quality_distribution']
        excellent_pct = quality_dist['quality_percentage']['excellent']
        
        if excellent_pct < 30:
            recommendations.append("📊 Low excellent quality rate - enhance pattern recognition")
        elif excellent_pct >= 50:
            recommendations.append("🏆 High excellent quality rate - exceptional performance")
        
        # Risk assessment recommendations
        high_risk_pct = quality_dist['risk_percentage']['high_risk']
        if high_risk_pct > 20:
            recommendations.append("⚠️ High false positive risk - review quality thresholds")
        
        # Phase 2 readiness
        overall_score = self.improvement_metrics['overall_improvement_score']
        if overall_score >= 0.7:
            recommendations.append("🚀 Ready for Phase 2 - content coverage expansion")
        elif overall_score >= 0.5:
            recommendations.append("⏭️ Close to Phase 2 readiness - address remaining issues")
        else:
            recommendations.append("🔧 Focus on Phase 1 optimization before Phase 2")
        
        return recommendations
    
    def _generate_next_steps(self, overall_score: float) -> List[str]:
        """Generate next steps based on validation results"""
        next_steps = []
        
        if overall_score >= 0.8:
            next_steps.extend([
                "🎯 Phase 1 excellent - proceed to Phase 2 implementation",
                "📋 Implement content coverage expansion",
                "🔗 Enhanced LinkedIn discovery integration",
                "📊 Monitor performance in production"
            ])
        elif overall_score >= 0.6:
            next_steps.extend([
                "🔧 Address remaining Phase 1 issues",
                "📈 Optimize discovery rate further",
                "⚡ Fine-tune quality validation",
                "⏭️ Prepare for Phase 2 implementation"
            ])
        else:
            next_steps.extend([
                "🛠️ Focus on Phase 1 critical fixes",
                "📊 Review and adjust quality thresholds",
                "🔍 Enhance pattern recognition",
                "⚠️ Validate against more test cases"
            ])
        
        return next_steps
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result when validation fails"""
        return {
            'metadata': {
                'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
                'test_type': 'phase1_implementation_validation',
                'status': 'error',
                'error_message': error_message,
                'phase1_available': PHASE1_AVAILABLE
            },
            'error': error_message,
            'recommendations': [
                "Ensure Phase 1 components are properly implemented",
                "Check import paths and dependencies",
                "Verify enhanced pipeline integration"
            ]
        }
    
    def save_results(self, results: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """Save Phase 1 validation results"""
        if output_file is None:
            timestamp = results['metadata']['timestamp']
            output_file = f"phase1_validation_results_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Phase 1 validation results saved to {output_file}")
        return output_file
    
    def print_phase1_report(self, results: Dict[str, Any]):
        """Print comprehensive Phase 1 validation report"""
        
        print("\n" + "="*100)
        print("⚡ PHASE 1 IMPLEMENTATION VALIDATION RESULTS")
        print("="*100)
        
        if 'error' in results:
            print(f"\n❌ VALIDATION ERROR: {results['error']}")
            return
        
        metadata = results['metadata']
        baseline = results['baseline_comparison']['baseline_metrics']
        current = results['baseline_comparison']['current_metrics']
        improvements = results['baseline_comparison']['improvements']
        targets = results['phase1_target_achievement']
        performance = results['performance_assessment']
        
        print(f"\n📊 EXECUTION SUMMARY:")
        print(f"  ⏱️  Execution Time: {metadata['execution_time_seconds']:.2f} seconds")
        print(f"  🌐 URLs Tested: {metadata['urls_tested']}")
        print(f"  🔧 Pipeline Version: {metadata['pipeline_version']}")
        print(f"  ⚡ Phase 1 Status: {performance['phase1_status'].upper()}")
        
        print(f"\n📈 BASELINE VS PHASE 1 COMPARISON:")
        print(f"  🎯 Discovery Rate: {baseline['discovery_rate']:.1f}% → {current['discovery_rate']:.1f}% "
              f"({improvements['discovery_rate_improvement']:+.1f}%)")
        print(f"  ❌ False Positive Rate: {baseline['false_positive_rate']:.1f}% → {current['false_positive_rate']:.1f}% "
              f"({improvements['false_positive_improvement']:+.1f}%)")
        print(f"  🎪 Average Confidence: {baseline['average_confidence']:.3f} → {current['average_confidence']:.3f} "
              f"({improvements['confidence_improvement']:+.3f})")
        print(f"  🌐 URL Coverage: {baseline['url_coverage']:.1f}% → {current['url_coverage']:.1f}% "
              f"({improvements['coverage_improvement']:+.1f}%)")
        
        print(f"\n🎯 PHASE 1 TARGET ACHIEVEMENT:")
        status_icon = lambda x: "✅" if x else "❌"
        print(f"  {status_icon(targets['discovery_rate']['achieved'])} Discovery Rate ≥{targets['discovery_rate']['target']:.0f}%: "
              f"{targets['discovery_rate']['current']:.1f}% ({targets['discovery_rate']['achieved']})")
        print(f"  {status_icon(targets['false_positive_rate']['achieved'])} False Positive Rate ≤{targets['false_positive_rate']['target']:.0f}%: "
              f"{targets['false_positive_rate']['current']:.1f}% ({targets['false_positive_rate']['achieved']})")
        print(f"  {status_icon(targets['average_confidence']['achieved'])} Average Confidence ≥{targets['average_confidence']['target']:.3f}: "
              f"{targets['average_confidence']['current']:.3f} ({targets['average_confidence']['achieved']})")
        
        print(f"\n🏆 PHASE 1 QUALITY ANALYSIS:")
        quality = results['quality_analysis']
        print(f"  💎 Excellent Quality: {quality['quality_percentage']['excellent']:.1f}%")
        print(f"  ⭐ Good+ Quality: {quality['quality_percentage']['good_or_excellent']:.1f}%")
        print(f"  🔒 Low Risk: {quality['risk_percentage']['low_risk']:.1f}%")
        print(f"  ⚠️  High Risk: {quality['risk_percentage']['high_risk']:.1f}%")
        
        print(f"\n📊 PERFORMANCE ASSESSMENT:")
        print(f"  🎪 Overall Score: {performance['overall_improvement_score']:.3f}")
        print(f"  🏆 Rating: {performance['performance_rating']}")
        print(f"  🚀 Ready for Phase 2: {performance['ready_for_phase2']}")
        
        print(f"\n🔧 CRITICAL ISSUES STATUS:")
        critical = performance['critical_issues_resolved']
        for issue, resolved in critical.items():
            status = "✅ Resolved" if resolved else "❌ Needs Work"
            print(f"  {status}: {issue.replace('_', ' ').title()}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for i, recommendation in enumerate(results['recommendations'], 1):
            print(f"  {i}. {recommendation}")
        
        print(f"\n⏭️ NEXT STEPS:")
        for i, step in enumerate(results['next_steps'], 1):
            print(f"  {i}. {step}")
        
        # Overall assessment
        overall_score = performance['overall_improvement_score']
        if overall_score >= 0.8:
            print(f"\n🎉 PHASE 1 ASSESSMENT: EXCEPTIONAL SUCCESS!")
            print("   🚀 All major targets achieved - ready for Phase 2!")
        elif overall_score >= 0.6:
            print(f"\n⭐ PHASE 1 ASSESSMENT: EXCELLENT PROGRESS!")
            print("   📈 Significant improvements achieved - close to Phase 2 readiness")
        elif overall_score >= 0.4:
            print(f"\n👍 PHASE 1 ASSESSMENT: GOOD IMPROVEMENT!")
            print("   🔧 Notable progress made - continue optimization")
        else:
            print(f"\n⚠️  PHASE 1 ASSESSMENT: NEEDS MORE WORK")
            print("   🛠️ Focus on critical improvements before Phase 2")
        
        print("="*100)


def main():
    """Main execution function for Phase 1 validation test"""
    try:
        # Initialize validator
        validator = Phase1ValidationTest()
        
        # Run Phase 1 validation
        results = validator.run_phase1_validation()
        
        # Save results
        output_file = validator.save_results(results)
        
        # Print comprehensive report
        validator.print_phase1_report(results)
        
        print(f"\n📄 Detailed results saved to: {output_file}")
        print("⚡ Phase 1 implementation validation completed!")
        
    except Exception as e:
        print(f"\n❌ Phase 1 validation failed: {str(e)}")
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 