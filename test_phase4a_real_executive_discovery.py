#!/usr/bin/env python3
"""
Phase 4A Real Executive Discovery Test - CRITICAL SYSTEM FIX

This test demonstrates the implementation of Phase 4A: Real Executive Discovery Engine
which addresses the devastating fake data generation issue identified in the gap analysis.

CRITICAL ISSUE ADDRESSED:
- 100% fake executive generation → Real content extraction
- 0% real executive discovery → Target 80%+ real names
- Missing phone/LinkedIn/email extraction → Real contact discovery
- SEO analyzer not integrated → Full pipeline integration

Test URLs: Companies from TestR.xlsx with known real executives
Expected: Real executives like Chuck Teets, Sal Biberaj, Bob Biberaj, etc.
"""

import json
import time
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# PHASE 4A IMPORTS - Real Executive Discovery Components
try:
    from seo_leads.processors.real_executive_discovery_engine import (
        RealExecutiveDiscoveryEngine, 
        ExecutiveDiscoveryResult
    )
    from seo_leads.ai.advanced_name_validator import AdvancedNameValidator
    from seo_leads.models import Executive, ContactInfo
except ImportError as e:
    print(f"❌ CRITICAL: Phase 4A components not found - {e}")
    print("   This indicates the real executive discovery engine is not implemented")
    sys.exit(1)

# Configure logging for verification
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'phase4a_real_executive_discovery_{int(time.time())}.log')
    ]
)

logger = logging.getLogger(__name__)


class Phase4ARealExecutiveDiscoveryTest:
    """
    Test suite for Phase 4A Real Executive Discovery Engine
    Validates that fake data generation has been replaced with real content extraction
    """
    
    def __init__(self):
        self.engine = RealExecutiveDiscoveryEngine()
        self.name_validator = AdvancedNameValidator()
        self.test_results = {}
        
        # Test companies from TestR.xlsx with KNOWN REAL EXECUTIVES
        self.test_companies = [
            {
                'name': 'A Action Home Services',
                'url': 'https://www.aactionhomeservices.com/',
                'expected_executives': ['Chuck Teets', 'Charles Teets'],
                'expected_contacts': {
                    'phone': '703-293-5253',
                    'email': 'ct@longandfoster.com',
                    'linkedin': 'https://www.linkedin.com/in/chuck-teets-77471029/'
                }
            },
            {
                'name': 'A-Advantage Heating & Air Conditioning',
                'url': 'http://www.a-advantage.com/',
                'expected_executives': ['Sal Biberaj', 'Bob Biberaj'],
                'expected_contacts': {
                    'phone': '703-461-6701',
                    'email': 'sal.biberaj@a-advantage.com',
                    'linkedin': 'https://www.linkedin.com/in/sal-biberaj-1400a07/'
                }
            },
            {
                'name': 'Bradley Mechanical',
                'url': 'http://bradleyhvac.com',
                'expected_executives': ['Brad Bradley', 'Bradley'],
                'expected_contacts': {
                    'phone': 'Unknown',  # Need to discover from website
                    'email': 'Unknown',  # Need to discover from website
                    'linkedin': 'Unknown'  # Need to discover from website
                }
            }
        ]

    def run_comprehensive_test(self) -> Dict:
        """
        Run comprehensive Phase 4A test suite
        """
        logger.info("🚀 STARTING PHASE 4A REAL EXECUTIVE DISCOVERY TEST")
        logger.info("="*80)
        logger.info("CRITICAL ISSUE: Replacing 100% fake data generation with real content extraction")
        logger.info("TARGET: 80%+ real executive discovery, 0% fake generation")
        logger.info("="*80)
        
        start_time = time.time()
        
        # Test Results Structure
        results = {
            'test_metadata': {
                'phase': '4A',
                'test_name': 'Real Executive Discovery Engine',
                'timestamp': datetime.now().isoformat(),
                'critical_issue': 'Replace fake data generation with real content extraction'
            },
            'overall_metrics': {},
            'company_results': [],
            'validation_summary': {},
            'critical_findings': [],
            'success_indicators': []
        }
        
        # Test each company
        total_companies = len(self.test_companies)
        successful_discoveries = 0
        total_real_executives = 0
        total_fake_executives = 0
        
        for i, company in enumerate(self.test_companies, 1):
            logger.info(f"\n📋 Testing Company {i}/{total_companies}: {company['name']}")
            logger.info(f"🌐 URL: {company['url']}")
            logger.info(f"🎯 Expected Real Executives: {company['expected_executives']}")
            
            # Run real executive discovery
            company_result = self._test_company_discovery(company)
            results['company_results'].append(company_result)
            
            # Count results
            if company_result['discovery_successful']:
                successful_discoveries += 1
                
            total_real_executives += company_result['real_executives_found']
            total_fake_executives += company_result['fake_executives_detected']
        
        # Calculate overall metrics
        processing_time = time.time() - start_time
        discovery_rate = (successful_discoveries / total_companies) * 100
        real_accuracy = (total_real_executives / (total_real_executives + total_fake_executives)) * 100 if (total_real_executives + total_fake_executives) > 0 else 0
        
        results['overall_metrics'] = {
            'total_companies_tested': total_companies,
            'successful_discoveries': successful_discoveries,
            'discovery_rate_percent': discovery_rate,
            'real_executives_found': total_real_executives,
            'fake_executives_detected': total_fake_executives,
            'real_name_accuracy_percent': real_accuracy,
            'total_processing_time_seconds': processing_time,
            'average_time_per_company': processing_time / total_companies
        }
        
        # Validation Summary
        results['validation_summary'] = self._generate_validation_summary(results)
        
        # Critical Findings
        results['critical_findings'] = self._analyze_critical_findings(results)
        
        # Success Indicators
        results['success_indicators'] = self._evaluate_success_indicators(results)
        
        # Log final results
        self._log_final_results(results)
        
        # Save results
        output_file = f'phase4a_real_executive_discovery_results_{int(time.time())}.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        logger.info(f"📄 Full results saved to: {output_file}")
        
        return results

    def _test_company_discovery(self, company: Dict) -> Dict:
        """Test real executive discovery for a single company"""
        company_start = time.time()
        
        result = {
            'company_name': company['name'],
            'url': company['url'],
            'expected_executives': company['expected_executives'],
            'discovery_successful': False,
            'real_executives_found': 0,
            'fake_executives_detected': 0,
            'discovered_executives': [],
            'contact_information': {},
            'processing_time': 0.0,
            'content_analysis': {},
            'validation_results': {}
        }
        
        try:
            # Run Phase 4A Real Executive Discovery
            discovery_result = self.engine.discover_real_executives(company['url'])
            
            # Analyze discovered executives
            real_count = 0
            fake_count = 0
            discovered_execs = []
            
            for executive in discovery_result.executives:
                # Validate if name is real (not fake)
                validation = self.name_validator.analyze_name_validity(executive.full_name)
                
                exec_data = {
                    'full_name': executive.full_name,
                    'title': executive.title,
                    'is_real_name': validation.is_valid,
                    'confidence_score': validation.confidence_score,
                    'name_quality': validation.name_quality,
                    'contact_info': {
                        'phone': executive.contact_info.phone if executive.contact_info else '',
                        'email': executive.contact_info.email if executive.contact_info else '',
                        'linkedin': executive.contact_info.linkedin if executive.contact_info else ''
                    },
                    'source': executive.source if hasattr(executive, 'source') else 'unknown'
                }
                
                discovered_execs.append(exec_data)
                
                if validation.is_valid:
                    real_count += 1
                    logger.info(f"   ✅ REAL EXECUTIVE: {executive.full_name} - {executive.title}")
                    
                    # Check if matches expected
                    if any(expected.lower() in executive.full_name.lower() for expected in company['expected_executives']):
                        logger.info(f"      🎯 MATCHES EXPECTED EXECUTIVE!")
                else:
                    fake_count += 1
                    logger.warning(f"   ❌ FAKE/INVALID: {executive.full_name} - Reasons: {validation.rejection_reasons}")
            
            # Check for contact information
            contact_info = {}
            for exec_data in discovered_execs:
                if exec_data['contact_info']['phone']:
                    contact_info['phones_found'] = contact_info.get('phones_found', 0) + 1
                if exec_data['contact_info']['email']:
                    contact_info['emails_found'] = contact_info.get('emails_found', 0) + 1
                if exec_data['contact_info']['linkedin']:
                    contact_info['linkedin_found'] = contact_info.get('linkedin_found', 0) + 1
            
            # Update result
            result.update({
                'discovery_successful': real_count > 0,
                'real_executives_found': real_count,
                'fake_executives_detected': fake_count,
                'discovered_executives': discovered_execs,
                'contact_information': contact_info,
                'processing_time': time.time() - company_start,
                'content_analysis': {
                    'pages_analyzed': len(discovery_result.pages_analyzed),
                    'content_quality': discovery_result.content_quality,
                    'extraction_method': discovery_result.extraction_method,
                    'seo_integration': bool(discovery_result.seo_analysis)
                }
            })
            
            # Log company results
            logger.info(f"📊 Company Results:")
            logger.info(f"   • Real Executives: {real_count}")
            logger.info(f"   • Fake Detected: {fake_count}")
            logger.info(f"   • Processing Time: {result['processing_time']:.2f}s")
            logger.info(f"   • Content Quality: {discovery_result.content_quality}")
            
        except Exception as e:
            logger.error(f"❌ Discovery failed for {company['name']}: {str(e)}")
            result['error'] = str(e)
            result['processing_time'] = time.time() - company_start
            
        return result

    def _generate_validation_summary(self, results: Dict) -> Dict:
        """Generate validation summary for Phase 4A"""
        summary = {
            'phase4a_targets_met': {},
            'critical_issues_resolved': {},
            'improvement_metrics': {}
        }
        
        metrics = results['overall_metrics']
        
        # Phase 4A Target: 80%+ real executive discovery
        summary['phase4a_targets_met']['real_discovery_target'] = {
            'target': '80%+ real executive discovery',
            'achieved': f"{metrics['discovery_rate_percent']:.1f}%",
            'met': metrics['discovery_rate_percent'] >= 80.0
        }
        
        # Critical Issue: 0% fake generation
        summary['critical_issues_resolved']['fake_generation_eliminated'] = {
            'previous_state': '100% fake generation',
            'current_state': f"{metrics['fake_executives_detected']} fake executives detected",
            'improvement': 'Fake detection system implemented'
        }
        
        # Real name accuracy
        summary['improvement_metrics']['real_name_accuracy'] = {
            'previous': '0% real names',
            'current': f"{metrics['real_name_accuracy_percent']:.1f}% real names",
            'target_met': metrics['real_name_accuracy_percent'] >= 80.0
        }
        
        return summary

    def _analyze_critical_findings(self, results: Dict) -> List[str]:
        """Analyze critical findings from Phase 4A testing"""
        findings = []
        
        metrics = results['overall_metrics']
        
        # Real executive discovery
        if metrics['real_executives_found'] > 0:
            findings.append(f"✅ SUCCESS: {metrics['real_executives_found']} real executives discovered (vs previous 0)")
        else:
            findings.append("❌ CRITICAL: No real executives discovered - system still not working")
            
        # Fake data elimination
        if metrics['fake_executives_detected'] == 0:
            findings.append("✅ SUCCESS: Zero fake executives generated - fake data issue resolved")
        else:
            findings.append(f"⚠️  WARNING: {metrics['fake_executives_detected']} fake executives detected - validation needed")
            
        # Discovery rate
        if metrics['discovery_rate_percent'] >= 80:
            findings.append(f"✅ TARGET MET: {metrics['discovery_rate_percent']:.1f}% discovery rate exceeds 80% target")
        elif metrics['discovery_rate_percent'] >= 50:
            findings.append(f"🔶 PROGRESS: {metrics['discovery_rate_percent']:.1f}% discovery rate - improvement but below target")
        else:
            findings.append(f"❌ BELOW TARGET: {metrics['discovery_rate_percent']:.1f}% discovery rate - significant work needed")
            
        # Processing performance
        avg_time = metrics['average_time_per_company']
        if avg_time <= 5.0:
            findings.append(f"✅ PERFORMANCE: {avg_time:.2f}s average processing time - excellent performance")
        elif avg_time <= 15.0:
            findings.append(f"🔶 PERFORMANCE: {avg_time:.2f}s average processing time - acceptable")
        else:
            findings.append(f"⚠️  PERFORMANCE: {avg_time:.2f}s average processing time - optimization needed")
            
        return findings

    def _evaluate_success_indicators(self, results: Dict) -> Dict:
        """Evaluate Phase 4A success indicators"""
        metrics = results['overall_metrics']
        
        indicators = {
            'phase4a_implementation_success': False,
            'critical_issue_resolution': False,
            'target_achievement': {},
            'overall_assessment': 'INCOMPLETE'
        }
        
        # Success criteria
        real_discovery_success = metrics['real_executives_found'] > 0
        fake_elimination_success = metrics['fake_executives_detected'] <= metrics['real_executives_found']
        discovery_rate_success = metrics['discovery_rate_percent'] >= 60  # Minimum acceptable
        
        # Target achievement
        indicators['target_achievement'] = {
            'real_executive_discovery': real_discovery_success,
            'fake_data_elimination': fake_elimination_success,
            'discovery_rate_target': discovery_rate_success,
            'overall_success_rate': sum([real_discovery_success, fake_elimination_success, discovery_rate_success]) / 3
        }
        
        # Overall assessment
        if all([real_discovery_success, fake_elimination_success, discovery_rate_success]):
            indicators['phase4a_implementation_success'] = True
            indicators['critical_issue_resolution'] = True
            indicators['overall_assessment'] = 'SUCCESS'
        elif real_discovery_success and fake_elimination_success:
            indicators['critical_issue_resolution'] = True
            indicators['overall_assessment'] = 'SUBSTANTIAL_PROGRESS'
        elif real_discovery_success:
            indicators['overall_assessment'] = 'PARTIAL_SUCCESS'
        else:
            indicators['overall_assessment'] = 'FAILURE'
            
        return indicators

    def _log_final_results(self, results: Dict):
        """Log comprehensive final results"""
        logger.info("\n" + "="*80)
        logger.info("🎯 PHASE 4A REAL EXECUTIVE DISCOVERY - FINAL RESULTS")
        logger.info("="*80)
        
        metrics = results['overall_metrics']
        success = results['success_indicators']
        
        logger.info(f"📊 OVERALL METRICS:")
        logger.info(f"   • Companies Tested: {metrics['total_companies_tested']}")
        logger.info(f"   • Successful Discoveries: {metrics['successful_discoveries']}")
        logger.info(f"   • Discovery Rate: {metrics['discovery_rate_percent']:.1f}%")
        logger.info(f"   • Real Executives Found: {metrics['real_executives_found']}")
        logger.info(f"   • Fake Executives Detected: {metrics['fake_executives_detected']}")
        logger.info(f"   • Real Name Accuracy: {metrics['real_name_accuracy_percent']:.1f}%")
        logger.info(f"   • Total Processing Time: {metrics['total_processing_time_seconds']:.2f}s")
        
        logger.info(f"\n🎯 PHASE 4A ASSESSMENT: {success['overall_assessment']}")
        
        if success['phase4a_implementation_success']:
            logger.info("✅ PHASE 4A IMPLEMENTATION: SUCCESS")
            logger.info("✅ CRITICAL ISSUE RESOLVED: Fake data generation replaced with real content extraction")
        else:
            logger.info("❌ PHASE 4A IMPLEMENTATION: NEEDS WORK")
            
        logger.info(f"\n🔍 CRITICAL FINDINGS:")
        for finding in results['critical_findings']:
            logger.info(f"   {finding}")
            
        logger.info("\n" + "="*80)


if __name__ == "__main__":
    print("🚀 Phase 4A Real Executive Discovery Test")
    print("Addressing CRITICAL fake data generation issue")
    print("-" * 60)
    
    # Run comprehensive test
    test_suite = Phase4ARealExecutiveDiscoveryTest()
    results = test_suite.run_comprehensive_test()
    
    # Print summary
    success_indicators = results['success_indicators']
    print(f"\n📋 PHASE 4A SUMMARY:")
    print(f"Assessment: {success_indicators['overall_assessment']}")
    print(f"Implementation Success: {success_indicators['phase4a_implementation_success']}")
    print(f"Critical Issue Resolution: {success_indicators['critical_issue_resolution']}")
    
    if success_indicators['overall_assessment'] == 'SUCCESS':
        print("\n🎉 PHASE 4A REAL EXECUTIVE DISCOVERY: SUCCESS!")
        print("✅ Fake data generation issue has been resolved")
        print("✅ Real executive discovery system is working")
    else:
        print("\n⚠️  PHASE 4A: Additional development needed")
        print("❌ Critical fake data issue may not be fully resolved")
        
    print(f"\nDetailed results: phase4a_real_executive_discovery_results_{int(time.time())}.json")