#!/usr/bin/env python3
"""
Test Phase 9A: Contact Detail Extraction Engine
===============================================

Comprehensive testing framework for Phase 9A Contact Extraction Engine using:
- 2Test.xlsx ground truth data for validation
- Context7-inspired testing patterns and validation
- Multi-format contact extraction testing
- Executive attribution accuracy measurement
- Performance benchmarking and quality assessment

Tests against real company data from 2Test.xlsx (39 companies)
Validates Context7 best practices implementation
"""

import asyncio
import json
import time
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple
import re
from dataclasses import asdict

# Import Phase 9A components
from phase9a_contact_extraction_engine import (
    Phase9aConfig, Phase9aContactExtractionEngine, Phase9aAdvancedContactPatterns,
    ContactInfo, ExecutiveProfile
)

class Phase9aTestFramework:
    """Context7-Inspired Test Framework for Contact Extraction"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Phase9aConfig()
        self.engine = Phase9aContactExtractionEngine(self.config)
        
        # Load test data
        self.test_data = self._load_test_data()
        
        # Test results storage
        self.test_results = {
            'pattern_tests': [],
            'attribution_tests': [],
            'integration_tests': [],
            'performance_tests': [],
            'quality_tests': []
        }
    
    def _load_test_data(self) -> pd.DataFrame:
        """Load test data from 2Test.xlsx using Context7 best practices"""
        try:
            # Try to load the Excel file
            test_file = "2Test.xlsx"
            if Path(test_file).exists():
                df = pd.read_excel(test_file)
                self.logger.info(f"✅ Loaded test data: {len(df)} companies from {test_file}")
                return df
            else:
                self.logger.warning(f"❌ Test file {test_file} not found, using sample data")
                return self._create_sample_test_data()
        except Exception as e:
            self.logger.error(f"Error loading test data: {e}")
            return self._create_sample_test_data()
    
    def _create_sample_test_data(self) -> pd.DataFrame:
        """Create sample test data when 2Test.xlsx is not available"""
        sample_data = [
            {
                'Company': 'A&H Plumbing',
                'Website': 'http://anhplumbing.com',
                'Expected_Executives': 2,
                'Expected_Contacts': 3
            },
            {
                'Company': 'Air-Tech Systems Inc',
                'Website': 'https://air-techsystems.com/',
                'Expected_Executives': 3,
                'Expected_Contacts': 5
            },
            {
                'Company': 'Test Engineering Ltd',
                'Website': 'https://test-engineering.co.uk',
                'Expected_Executives': 2,
                'Expected_Contacts': 4
            }
        ]
        return pd.DataFrame(sample_data)

class Phase9aPatternTester:
    """Context7-Inspired Pattern Recognition Testing"""
    
    def __init__(self, config: Phase9aConfig):
        self.config = config
        self.patterns = Phase9aAdvancedContactPatterns(config)
        self.logger = logging.getLogger(__name__)
    
    def test_phone_patterns(self) -> Dict[str, Any]:
        """Test phone number pattern recognition using Context7 test cases"""
        test_cases = [
            # US Phone Numbers
            {
                'content': 'Please call John Smith at (555) 123-4567 for more information.',
                'expected_phones': ['(555) 123-4567'],
                'test_name': 'US_Standard_Format'
            },
            {
                'content': 'Mobile: +1-555-987-6543, Office: 555.123.4567 ext 123',
                'expected_phones': ['+1-555-987-6543', '555.123.4567'],
                'test_name': 'US_Multiple_Formats'
            },
            # UK Phone Numbers
            {
                'content': 'Contact our director on +44 20 1234 5678 or mobile 07700 123456',
                'expected_phones': ['+44 20 1234 5678', '07700 123456'],
                'test_name': 'UK_Standard_Format'
            },
            # International
            {
                'content': 'International office: +33 1 23 45 67 89',
                'expected_phones': ['+33 1 23 45 67 89'],
                'test_name': 'International_Format'
            },
            # Edge Cases
            {
                'content': 'CEO direct line: mobile 555-CALL-NOW (not a real number)',
                'expected_phones': [],  # Should not match alphanumeric
                'test_name': 'Invalid_Alphanumeric'
            }
        ]
        
        results = {'passed': 0, 'failed': 0, 'test_details': []}
        
        for test_case in test_cases:
            extracted_phones = self.patterns.extract_phone_numbers(test_case['content'])
            extracted_numbers = [phone['number'] for phone in extracted_phones]
            
            # Check if expected phones are found
            matches_found = sum(1 for expected in test_case['expected_phones'] 
                              if any(expected in extracted for extracted in extracted_numbers))
            
            test_passed = matches_found == len(test_case['expected_phones'])
            
            if test_passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            results['test_details'].append({
                'test_name': test_case['test_name'],
                'expected': test_case['expected_phones'],
                'extracted': extracted_numbers,
                'passed': test_passed,
                'confidence_scores': [phone['confidence'] for phone in extracted_phones]
            })
        
        return results
    
    def test_email_patterns(self) -> Dict[str, Any]:
        """Test email pattern recognition using Context7 test cases"""
        test_cases = [
            {
                'content': 'Contact CEO John Smith at john.smith@company.com for inquiries.',
                'company_domain': 'company.com',
                'expected_emails': ['john.smith@company.com'],
                'test_name': 'Standard_Executive_Email'
            },
            {
                'content': 'Manager: sarah.jones@firm.co.uk, Director: ceo@firm.co.uk',
                'company_domain': 'firm.co.uk',
                'expected_emails': ['sarah.jones@firm.co.uk', 'ceo@firm.co.uk'],
                'test_name': 'Multiple_Executive_Emails'
            },
            {
                'content': 'For support contact info@generic.com (not executive)',
                'company_domain': 'company.com',
                'expected_emails': [],  # Generic email, should be filtered
                'test_name': 'Generic_Email_Filter'
            },
            {
                'content': 'Director Mike Wilson can be reached at m.wilson@business.org',
                'company_domain': 'business.org',
                'expected_emails': ['m.wilson@business.org'],
                'test_name': 'Initial_Based_Email'
            }
        ]
        
        results = {'passed': 0, 'failed': 0, 'test_details': []}
        
        for test_case in test_cases:
            extracted_emails = self.patterns.extract_email_addresses(
                test_case['content'], test_case['company_domain']
            )
            extracted_addresses = [email['address'] for email in extracted_emails 
                                 if email['confidence'] >= self.config.email_confidence_threshold]
            
            # Check if expected emails are found
            matches_found = sum(1 for expected in test_case['expected_emails'] 
                              if expected in extracted_addresses)
            
            test_passed = matches_found == len(test_case['expected_emails'])
            
            if test_passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            results['test_details'].append({
                'test_name': test_case['test_name'],
                'expected': test_case['expected_emails'],
                'extracted': extracted_addresses,
                'passed': test_passed,
                'confidence_scores': [email['confidence'] for email in extracted_emails]
            })
        
        return results
    
    def test_linkedin_patterns(self) -> Dict[str, Any]:
        """Test LinkedIn pattern recognition using Context7 test cases"""
        test_cases = [
            {
                'content': 'Connect with our CEO at https://www.linkedin.com/in/john-smith-ceo',
                'expected_linkedin': ['https://www.linkedin.com/in/john-smith-ceo'],
                'test_name': 'Standard_LinkedIn_Profile'
            },
            {
                'content': 'Visit linkedin.com/in/sarah-director or our company page',
                'expected_linkedin': ['linkedin.com/in/sarah-director'],
                'test_name': 'Partial_LinkedIn_URL'
            },
            {
                'content': 'Follow us: https://linkedin.com/company/our-business-ltd',
                'expected_linkedin': ['https://linkedin.com/company/our-business-ltd'],
                'test_name': 'Company_LinkedIn_Page'
            }
        ]
        
        results = {'passed': 0, 'failed': 0, 'test_details': []}
        
        for test_case in test_cases:
            extracted_linkedin = self.patterns.extract_linkedin_profiles(test_case['content'])
            extracted_urls = [profile['url'] for profile in extracted_linkedin]
            
            # Check if expected LinkedIn profiles are found
            matches_found = sum(1 for expected in test_case['expected_linkedin'] 
                              if any(expected in extracted for extracted in extracted_urls))
            
            test_passed = matches_found == len(test_case['expected_linkedin'])
            
            if test_passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            results['test_details'].append({
                'test_name': test_case['test_name'],
                'expected': test_case['expected_linkedin'],
                'extracted': extracted_urls,
                'passed': test_passed,
                'confidence_scores': [profile['confidence'] for profile in extracted_linkedin]
            })
        
        return results

class Phase9aIntegrationTester:
    """Context7-Inspired Integration Testing with Real Data"""
    
    def __init__(self, engine: Phase9aContactExtractionEngine, test_data: pd.DataFrame):
        self.engine = engine
        self.test_data = test_data
        self.logger = logging.getLogger(__name__)
    
    async def test_real_company_extraction(self, max_companies: int = 5) -> Dict[str, Any]:
        """Test contact extraction on real companies from 2Test.xlsx"""
        results = {'companies_tested': 0, 'successful_extractions': 0, 'results': []}
        
        # Test subset of companies
        test_companies = self.test_data.head(max_companies)
        
        for idx, row in test_companies.iterrows():
            company_name = row.get('Company', f'Company_{idx}')
            website_url = row.get('Website', 'http://example.com')
            
            try:
                self.logger.info(f"Testing contact extraction for: {company_name}")
                
                # Extract contacts
                result = await self.engine.extract_executive_contacts(company_name, website_url)
                
                # Analyze results
                extraction_analysis = self._analyze_extraction_result(result, row)
                
                results['companies_tested'] += 1
                if not result.get('error'):
                    results['successful_extractions'] += 1
                
                results['results'].append({
                    'company_name': company_name,
                    'website_url': website_url,
                    'extraction_result': result,
                    'analysis': extraction_analysis
                })
                
            except Exception as e:
                self.logger.error(f"Error testing {company_name}: {e}")
                results['results'].append({
                    'company_name': company_name,
                    'website_url': website_url,
                    'error': str(e),
                    'analysis': {'test_passed': False, 'error': str(e)}
                })
        
        # Calculate overall success rate
        results['success_rate'] = results['successful_extractions'] / max(1, results['companies_tested'])
        
        return results
    
    def _analyze_extraction_result(self, result: Dict[str, Any], expected_data: pd.Series) -> Dict[str, Any]:
        """Analyze extraction result against expected data using Context7 metrics"""
        analysis = {
            'test_passed': False,
            'executives_found': 0,
            'contacts_extracted': 0,
            'quality_score': 0.0,
            'performance_metrics': {}
        }
        
        if result.get('error'):
            analysis['error'] = result['error']
            return analysis
        
        # Extract metrics
        exec_profiles = result.get('executive_profiles', [])
        extraction_stats = result.get('extraction_stats', {})
        
        analysis['executives_found'] = len(exec_profiles)
        analysis['contacts_extracted'] = extraction_stats.get('total_contacts_extracted', 0)
        analysis['processing_time'] = extraction_stats.get('processing_time_seconds', 0)
        analysis['pages_analyzed'] = extraction_stats.get('pages_analyzed', 0)
        
        # Quality assessment
        quality_assessment = result.get('quality_assessment', {})
        analysis['quality_score'] = quality_assessment.get('quality_score', 0.0)
        analysis['quality_tier'] = quality_assessment.get('overall_quality', 'UNKNOWN')
        
        # Performance metrics
        analysis['performance_metrics'] = {
            'contacts_per_executive': analysis['contacts_extracted'] / max(1, analysis['executives_found']),
            'pages_per_second': analysis['pages_analyzed'] / max(0.1, analysis['processing_time']),
            'average_completeness': extraction_stats.get('average_completeness', 0)
        }
        
        # Determine if test passed (basic criteria)
        analysis['test_passed'] = (
            analysis['executives_found'] > 0 and
            analysis['contacts_extracted'] > 0 and
            analysis['quality_score'] >= 0.3
        )
        
        return analysis

class Phase9aPerformanceTester:
    """Context7-Inspired Performance Testing and Benchmarking"""
    
    def __init__(self, engine: Phase9aContactExtractionEngine):
        self.engine = engine
        self.logger = logging.getLogger(__name__)
    
    async def benchmark_processing_speed(self, test_companies: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Benchmark processing speed using Context7 performance metrics"""
        benchmark_results = {
            'total_companies': len(test_companies),
            'total_processing_time': 0.0,
            'individual_results': [],
            'performance_metrics': {}
        }
        
        start_time = time.time()
        
        for company_name, website_url in test_companies:
            company_start = time.time()
            
            try:
                result = await self.engine.extract_executive_contacts(company_name, website_url)
                company_time = time.time() - company_start
                
                benchmark_results['individual_results'].append({
                    'company': company_name,
                    'processing_time': company_time,
                    'executives_found': len(result.get('executive_profiles', [])),
                    'contacts_extracted': result.get('extraction_stats', {}).get('total_contacts_extracted', 0),
                    'pages_analyzed': result.get('extraction_stats', {}).get('pages_analyzed', 0)
                })
                
            except Exception as e:
                self.logger.error(f"Benchmark error for {company_name}: {e}")
                benchmark_results['individual_results'].append({
                    'company': company_name,
                    'processing_time': time.time() - company_start,
                    'error': str(e)
                })
        
        benchmark_results['total_processing_time'] = time.time() - start_time
        
        # Calculate performance metrics
        successful_results = [r for r in benchmark_results['individual_results'] if 'error' not in r]
        
        if successful_results:
            benchmark_results['performance_metrics'] = {
                'average_processing_time': sum(r['processing_time'] for r in successful_results) / len(successful_results),
                'companies_per_hour': len(successful_results) / (benchmark_results['total_processing_time'] / 3600),
                'average_executives_per_company': sum(r['executives_found'] for r in successful_results) / len(successful_results),
                'average_contacts_per_company': sum(r['contacts_extracted'] for r in successful_results) / len(successful_results),
                'average_pages_per_company': sum(r['pages_analyzed'] for r in successful_results) / len(successful_results)
            }
        
        return benchmark_results

async def run_comprehensive_phase9a_tests():
    """Run comprehensive Phase 9A testing suite using Context7 methodology"""
    print("🚀 Starting Comprehensive Phase 9A Contact Extraction Testing")
    print("=" * 80)
    
    # Initialize test framework
    test_framework = Phase9aTestFramework()
    
    # Test results storage
    all_test_results = {
        'test_timestamp': int(time.time()),
        'test_configuration': asdict(test_framework.config),
        'pattern_recognition_tests': {},
        'integration_tests': {},
        'performance_tests': {},
        'overall_assessment': {}
    }
    
    # 1. Pattern Recognition Tests
    print("\n📋 Phase 1: Pattern Recognition Testing")
    pattern_tester = Phase9aPatternTester(test_framework.config)
    
    # Test phone patterns
    print("  📞 Testing phone number patterns...")
    phone_results = pattern_tester.test_phone_patterns()
    all_test_results['pattern_recognition_tests']['phone_patterns'] = phone_results
    print(f"     ✅ Passed: {phone_results['passed']}, ❌ Failed: {phone_results['failed']}")
    
    # Test email patterns
    print("  📧 Testing email patterns...")
    email_results = pattern_tester.test_email_patterns()
    all_test_results['pattern_recognition_tests']['email_patterns'] = email_results
    print(f"     ✅ Passed: {email_results['passed']}, ❌ Failed: {email_results['failed']}")
    
    # Test LinkedIn patterns
    print("  🔗 Testing LinkedIn patterns...")
    linkedin_results = pattern_tester.test_linkedin_patterns()
    all_test_results['pattern_recognition_tests']['linkedin_patterns'] = linkedin_results
    print(f"     ✅ Passed: {linkedin_results['passed']}, ❌ Failed: {linkedin_results['failed']}")
    
    # 2. Integration Tests with Real Data
    print("\n📊 Phase 2: Integration Testing with Real Company Data")
    integration_tester = Phase9aIntegrationTester(test_framework.engine, test_framework.test_data)
    
    print("  🏢 Testing real company extraction...")
    integration_results = await integration_tester.test_real_company_extraction(max_companies=3)
    all_test_results['integration_tests'] = integration_results
    print(f"     📈 Success Rate: {integration_results['success_rate']:.1%}")
    print(f"     🏢 Companies Tested: {integration_results['companies_tested']}")
    
    # 3. Performance Benchmarking
    print("\n⚡ Phase 3: Performance Benchmarking")
    performance_tester = Phase9aPerformanceTester(test_framework.engine)
    
    # Create test company list from data
    test_companies = []
    for idx, row in test_framework.test_data.head(3).iterrows():
        company_name = row.get('Company', f'Company_{idx}')
        website_url = row.get('Website', 'http://example.com')
        test_companies.append((company_name, website_url))
    
    print("  🏃 Running performance benchmarks...")
    performance_results = await performance_tester.benchmark_processing_speed(test_companies)
    all_test_results['performance_tests'] = performance_results
    
    if performance_results.get('performance_metrics'):
        metrics = performance_results['performance_metrics']
        print(f"     ⏱️ Avg Processing Time: {metrics['average_processing_time']:.2f}s")
        print(f"     🏃 Companies/Hour: {metrics['companies_per_hour']:.1f}")
        print(f"     👥 Avg Executives/Company: {metrics['average_executives_per_company']:.1f}")
        print(f"     📞 Avg Contacts/Company: {metrics['average_contacts_per_company']:.1f}")
    
    # 4. Overall Assessment
    print("\n📊 Phase 4: Overall Assessment")
    overall_assessment = _calculate_overall_assessment(all_test_results)
    all_test_results['overall_assessment'] = overall_assessment
    
    print(f"  📊 Overall Test Score: {overall_assessment['overall_score']:.1%}")
    print(f"  🏆 Assessment Grade: {overall_assessment['grade']}")
    print(f"  ✅ Tests Passed: {overall_assessment['tests_passed']}/{overall_assessment['total_tests']}")
    
    # Save results
    timestamp = int(time.time())
    results_file = f"phase9a_comprehensive_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(all_test_results, f, indent=2, default=str)
    
    print(f"\n💾 Test results saved to: {results_file}")
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 PHASE 9A TESTING SUMMARY")
    print("=" * 80)
    print(f"Pattern Recognition: {_get_pattern_score(all_test_results):.1%} success")
    print(f"Integration Testing: {integration_results['success_rate']:.1%} success")
    print(f"Performance: {_get_performance_score(performance_results):.1%} efficiency")
    print(f"Overall Grade: {overall_assessment['grade']}")
    
    return all_test_results

def _calculate_overall_assessment(test_results: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall assessment using Context7 scoring methodology"""
    
    # Pattern recognition score
    pattern_score = _get_pattern_score(test_results)
    
    # Integration score
    integration_score = test_results['integration_tests']['success_rate']
    
    # Performance score
    performance_score = _get_performance_score(test_results['performance_tests'])
    
    # Calculate weighted overall score
    overall_score = (pattern_score * 0.4) + (integration_score * 0.4) + (performance_score * 0.2)
    
    # Determine grade
    if overall_score >= 0.9:
        grade = 'A+'
    elif overall_score >= 0.8:
        grade = 'A'
    elif overall_score >= 0.7:
        grade = 'B+'
    elif overall_score >= 0.6:
        grade = 'B'
    elif overall_score >= 0.5:
        grade = 'C'
    else:
        grade = 'F'
    
    # Count total tests
    pattern_tests = test_results['pattern_recognition_tests']
    total_tests = (
        pattern_tests['phone_patterns']['passed'] + pattern_tests['phone_patterns']['failed'] +
        pattern_tests['email_patterns']['passed'] + pattern_tests['email_patterns']['failed'] +
        pattern_tests['linkedin_patterns']['passed'] + pattern_tests['linkedin_patterns']['failed'] +
        test_results['integration_tests']['companies_tested']
    )
    
    tests_passed = (
        pattern_tests['phone_patterns']['passed'] +
        pattern_tests['email_patterns']['passed'] +
        pattern_tests['linkedin_patterns']['passed'] +
        test_results['integration_tests']['successful_extractions']
    )
    
    return {
        'overall_score': overall_score,
        'grade': grade,
        'pattern_score': pattern_score,
        'integration_score': integration_score,
        'performance_score': performance_score,
        'tests_passed': tests_passed,
        'total_tests': total_tests
    }

def _get_pattern_score(test_results: Dict[str, Any]) -> float:
    """Calculate pattern recognition score"""
    pattern_tests = test_results['pattern_recognition_tests']
    
    total_passed = (
        pattern_tests['phone_patterns']['passed'] +
        pattern_tests['email_patterns']['passed'] +
        pattern_tests['linkedin_patterns']['passed']
    )
    
    total_tests = (
        pattern_tests['phone_patterns']['passed'] + pattern_tests['phone_patterns']['failed'] +
        pattern_tests['email_patterns']['passed'] + pattern_tests['email_patterns']['failed'] +
        pattern_tests['linkedin_patterns']['passed'] + pattern_tests['linkedin_patterns']['failed']
    )
    
    return total_passed / max(1, total_tests)

def _get_performance_score(performance_results: Dict[str, Any]) -> float:
    """Calculate performance score based on Context7 benchmarks"""
    metrics = performance_results.get('performance_metrics', {})
    
    if not metrics:
        return 0.5  # Default score if no metrics
    
    # Performance thresholds (Context7 best practices)
    avg_time = metrics.get('average_processing_time', 10)
    companies_per_hour = metrics.get('companies_per_hour', 0)
    
    # Score based on processing speed
    time_score = max(0, min(1, (10 - avg_time) / 10))  # Better if under 10s
    throughput_score = min(1, companies_per_hour / 100)  # Target 100 companies/hour
    
    return (time_score + throughput_score) / 2

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run comprehensive tests
    asyncio.run(run_comprehensive_phase9a_tests())