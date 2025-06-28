#!/usr/bin/env python3
"""
Comprehensive Production Test - SEO + Executive Discovery
Tests the complete workflow with all provided URLs and generates JSON results
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'comprehensive_test_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.seo_leads.orchestrators.executive_discovery_orchestrator import ExecutiveDiscoveryOrchestrator
    from src.seo_leads.analyzers.seo_analyzer import SEOAnalyzer
    from src.seo_leads.analyzers.website_health_checker import WebsiteHealthChecker
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    # Try alternative import
    import importlib.util
    
    spec = importlib.util.spec_from_file_location(
        "executive_discovery_orchestrator", 
        "src/seo_leads/orchestrators/executive_discovery_orchestrator.py"
    )
    exec_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exec_module)
    ExecutiveDiscoveryOrchestrator = exec_module.ExecutiveDiscoveryOrchestrator
    
    spec = importlib.util.spec_from_file_location(
        "seo_analyzer", 
        "src/seo_leads/analyzers/seo_analyzer.py"
    )
    seo_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seo_module)
    SEOAnalyzer = seo_module.SEOAnalyzer
    
    spec = importlib.util.spec_from_file_location(
        "website_health_checker", 
        "src/seo_leads/analyzers/website_health_checker.py"
    )
    health_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(health_module)
    WebsiteHealthChecker = health_module.WebsiteHealthChecker

class ComprehensiveProductionTester:
    """Comprehensive tester for SEO + Executive Discovery workflow"""
    
    def __init__(self):
        self.test_urls = [
            "https://supreme-plumbers-aq2qoadp7ocmvqll.builder-preview.com/",
            "http://www.idealplumbingservices.co.uk/",
            "https://2ndcitygasplumbingandheating.co.uk/?utm_source=google_profile&utm_campaign=localo&utm_medium=mainlink",
            "https://jacktheplumber.co.uk/",
            "https://www.swiftemergencyplumber.com/",
            "https://mkplumbingbirmingham.co.uk/",
            "http://www.rescueplumbing.co.uk/",
            "https://www.gdplumbingandheatingservices.co.uk/",
            "http://www.mattplumbingandheating.com/",
            "http://summitplumbingandheating.co.uk/",
            "https://macplumbheat.co.uk/",
            "https://ltfplumbing.co.uk/subscription",
            "http://www.ctmplumbing.co.uk/",
            "https://kingsheathplumbing.freeindex.co.uk/",
            "http://www.perry-plumbing.co.uk/"
        ]
        
        # Initialize components
        try:
            self.executive_orchestrator = ExecutiveDiscoveryOrchestrator()
            self.seo_analyzer = SEOAnalyzer()
            self.health_checker = WebsiteHealthChecker()
            logger.info("All components initialized successfully")
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            raise
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test on all URLs"""
        
        logger.info("🚀 Starting Comprehensive Production Test")
        logger.info(f"Testing {len(self.test_urls)} URLs with complete SEO + Executive Discovery workflow")
        
        test_start = time.time()
        results = {
            'test_metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_urls': len(self.test_urls),
                'test_type': 'comprehensive_seo_executive_discovery'
            },
            'results': [],
            'summary': {}
        }
        
        for i, url in enumerate(self.test_urls, 1):
            logger.info(f"🔍 Testing {i}/{len(self.test_urls)}: {url}")
            
            url_start = time.time()
            url_result = await self._test_single_url(url)
            url_result['processing_time'] = time.time() - url_start
            
            results['results'].append(url_result)
            
            # Log progress
            logger.info(f"✅ Completed {i}/{len(self.test_urls)} - {url_result['company_name']} - "
                       f"SEO: {url_result['seo'].get('overall_score', 0)}, "
                       f"Executives: {len(url_result['executives'])}, "
                       f"Companies House: {url_result['companies_house_verified']}")
        
        # Generate summary
        results['summary'] = self._generate_test_summary(results['results'])
        results['test_metadata']['total_time'] = time.time() - test_start
        
        logger.info(f"🎯 Comprehensive test completed in {results['test_metadata']['total_time']:.1f}s")
        
        return results
    
    async def _test_single_url(self, url: str) -> Dict[str, Any]:
        """Test a single URL with complete workflow"""
        
        result = {
            'url': url,
            'success': False,
            'company_name': '',
            'seo': {},
            'health': {},
            'executives': [],
            'companies_house_verified': False,
            'contact_information': {},
            'data_quality_score': 0.0,
            'errors': []
        }
        
        try:
            # Step 1: SEO Analysis
            try:
                seo_results = await self.seo_analyzer.analyze_website(url)
                result['seo'] = seo_results
                logger.info(f"✅ SEO analysis completed for {url}")
            except Exception as e:
                result['errors'].append(f"SEO analysis failed: {str(e)}")
                logger.warning(f"❌ SEO analysis failed for {url}: {e}")
            
            # Step 2: Website Health Check
            try:
                health_results = await self.health_checker.check_website_health(url)
                result['health'] = health_results
                logger.info(f"✅ Health check completed for {url}")
            except Exception as e:
                result['errors'].append(f"Health check failed: {str(e)}")
                logger.warning(f"❌ Health check failed for {url}: {e}")
            
            # Step 3: Executive Discovery (including Companies House)
            try:
                exec_results = await self.executive_orchestrator.execute_comprehensive_discovery(url)
                
                result['company_name'] = exec_results.company_name
                result['companies_house_verified'] = exec_results.companies_house_verified
                result['success'] = True
                
                # Convert executives to serializable format
                result['executives'] = []
                for exec in exec_results.executives:
                    exec_dict = {
                        'name': exec.name,
                        'title': exec.title,
                        'company_name': exec.company_name,
                        'email': exec.email,
                        'phone': exec.phone,
                        'linkedin_url': exec.linkedin_url,
                        'confidence_score': exec.confidence_score,
                        'discovery_sources': exec.discovery_sources,
                        'discovery_method': exec.discovery_method,
                        'validation_notes': exec.validation_notes
                    }
                    result['executives'].append(exec_dict)
                
                # Extract contact information summary
                result['contact_information'] = self._extract_contact_summary(result['executives'])
                result['data_quality_score'] = self._calculate_quality_score(result)
                
                logger.info(f"✅ Executive discovery completed for {url} - Found {len(result['executives'])} executives")
                
            except Exception as e:
                result['errors'].append(f"Executive discovery failed: {str(e)}")
                logger.error(f"❌ Executive discovery failed for {url}: {e}")
        
        except Exception as e:
            result['errors'].append(f"Overall test failed: {str(e)}")
            logger.error(f"❌ Complete test failed for {url}: {e}")
        
        return result
    
    def _extract_contact_summary(self, executives: List[Dict]) -> Dict[str, Any]:
        """Extract contact information summary"""
        summary = {
            'total_executives': len(executives),
            'executives_with_email': 0,
            'executives_with_phone': 0,
            'executives_with_linkedin': 0,
            'unique_emails': set(),
            'unique_phones': set(),
            'contact_completeness': 0.0
        }
        
        for exec in executives:
            if exec.get('email'):
                summary['executives_with_email'] += 1
                summary['unique_emails'].add(exec['email'])
            if exec.get('phone'):
                summary['executives_with_phone'] += 1
                summary['unique_phones'].add(exec['phone'])
            if exec.get('linkedin_url'):
                summary['executives_with_linkedin'] += 1
        
        # Convert sets to lists for JSON serialization
        summary['unique_emails'] = list(summary['unique_emails'])
        summary['unique_phones'] = list(summary['unique_phones'])
        
        # Calculate contact completeness
        if summary['total_executives'] > 0:
            total_possible_contacts = summary['total_executives'] * 3  # email, phone, linkedin
            actual_contacts = (summary['executives_with_email'] + 
                             summary['executives_with_phone'] + 
                             summary['executives_with_linkedin'])
            summary['contact_completeness'] = (actual_contacts / total_possible_contacts) * 100
        
        return summary
    
    def _calculate_quality_score(self, result: Dict) -> float:
        """Calculate overall data quality score"""
        score = 0.0
        
        # SEO score (20%)
        if 'seo' in result and 'overall_score' in result['seo']:
            score += result['seo']['overall_score'] * 0.2
        
        # Health score (20%)
        if 'health' in result and 'health_score' in result['health']:
            score += result['health']['health_score'] * 0.2
        
        # Executive discovery score (40%)
        exec_score = min(len(result['executives']) / 3, 1.0) * 0.4
        score += exec_score
        
        # Contact completeness score (20%)
        if 'contact_information' in result:
            contact_score = result['contact_information']['contact_completeness'] / 100 * 0.2
            score += contact_score
        
        return round(score, 3)
    
    def _generate_test_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        
        summary = {
            'overall_statistics': {
                'total_urls_tested': len(results),
                'successful_tests': sum(1 for r in results if r['success']),
                'seo_analysis_success': sum(1 for r in results if 'overall_score' in r.get('seo', {})),
                'health_check_success': sum(1 for r in results if 'health_score' in r.get('health', {})),
                'executive_discovery_success': sum(1 for r in results if len(r['executives']) > 0),
                'companies_house_verified': sum(1 for r in results if r['companies_house_verified'])
            },
            'seo_statistics': {
                'average_seo_score': 0.0,
                'websites_with_good_seo': 0,  # >0.7
                'average_word_count': 0,
                'websites_with_contact_info': 0
            },
            'executive_discovery_statistics': {
                'total_executives_found': sum(len(r['executives']) for r in results),
                'average_executives_per_company': 0.0,
                'companies_with_real_contacts': sum(1 for r in results if self._has_real_contacts(r)),
                'contact_discovery_rate': 0.0,
                'average_contact_completeness': 0.0
            },
            'companies_house_statistics': {
                'companies_searched': len(results),
                'official_directors_found': sum(1 for r in results if r['companies_house_verified']),
                'companies_house_coverage': 0.0
            },
            'quality_metrics': {
                'average_data_quality_score': 0.0,
                'high_quality_results': 0,  # >0.7
                'business_value_score': 0.0
            }
        }
        
        # Calculate SEO statistics
        seo_scores = [r['seo'].get('overall_score', 0) for r in results if 'seo' in r]
        if seo_scores:
            summary['seo_statistics']['average_seo_score'] = round(sum(seo_scores) / len(seo_scores), 3)
            summary['seo_statistics']['websites_with_good_seo'] = sum(1 for score in seo_scores if score > 0.7)
        
        word_counts = [r['seo'].get('word_count', 0) for r in results if 'seo' in r]
        if word_counts:
            summary['seo_statistics']['average_word_count'] = int(sum(word_counts) / len(word_counts))
        
        summary['seo_statistics']['websites_with_contact_info'] = sum(
            1 for r in results if r.get('seo', {}).get('has_contact_info', False)
        )
        
        # Calculate executive discovery statistics
        if summary['overall_statistics']['total_urls_tested'] > 0:
            summary['executive_discovery_statistics']['average_executives_per_company'] = round(
                summary['executive_discovery_statistics']['total_executives_found'] / 
                summary['overall_statistics']['total_urls_tested'], 2
            )
        
        contact_completeness_scores = [
            r['contact_information']['contact_completeness'] 
            for r in results if 'contact_information' in r
        ]
        if contact_completeness_scores:
            summary['executive_discovery_statistics']['average_contact_completeness'] = round(
                sum(contact_completeness_scores) / len(contact_completeness_scores), 2
            )
        
        summary['executive_discovery_statistics']['contact_discovery_rate'] = round(
            (summary['executive_discovery_statistics']['companies_with_real_contacts'] / 
             summary['overall_statistics']['total_urls_tested']) * 100, 2
        ) if summary['overall_statistics']['total_urls_tested'] > 0 else 0
        
        # Calculate Companies House statistics
        summary['companies_house_statistics']['companies_house_coverage'] = round(
            (summary['companies_house_statistics']['official_directors_found'] / 
             summary['companies_house_statistics']['companies_searched']) * 100, 2
        ) if summary['companies_house_statistics']['companies_searched'] > 0 else 0
        
        # Calculate quality metrics
        quality_scores = [r['data_quality_score'] for r in results if r['data_quality_score'] > 0]
        if quality_scores:
            summary['quality_metrics']['average_data_quality_score'] = round(
                sum(quality_scores) / len(quality_scores), 3
            )
            summary['quality_metrics']['high_quality_results'] = sum(1 for score in quality_scores if score > 0.7)
        
        # Business value score combines contact discovery and data quality
        summary['quality_metrics']['business_value_score'] = round(
            (summary['executive_discovery_statistics']['contact_discovery_rate'] * 0.6 + 
             summary['quality_metrics']['average_data_quality_score'] * 100 * 0.4), 2
        )
        
        return summary
    
    def _has_real_contacts(self, result: Dict) -> bool:
        """Check if result has real contact information"""
        if 'contact_information' not in result:
            return False
        
        contact_info = result['contact_information']
        return (contact_info['executives_with_email'] > 0 or 
                contact_info['executives_with_phone'] > 0 or 
                contact_info['executives_with_linkedin'] > 0)

async def main():
    """Run comprehensive production test"""
    
    print("🚀 Comprehensive Production Test - SEO + Executive Discovery")
    print("=" * 80)
    print("Testing complete workflow with all 15 URLs")
    print("=" * 80)
    
    tester = ComprehensiveProductionTester()
    results = await tester.run_comprehensive_test()
    
    # Save results to JSON
    timestamp = int(time.time())
    results_file = f"comprehensive_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📊 Results saved to: {results_file}")
    
    # Display summary
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    
    summary = results['summary']
    overall = summary['overall_statistics']
    
    print(f"📈 Overall Success Rate: {(overall['successful_tests']/overall['total_urls_tested']*100):.1f}%")
    print(f"🔍 SEO Analysis Success: {(overall['seo_analysis_success']/overall['total_urls_tested']*100):.1f}%")
    print(f"👥 Executive Discovery Success: {(overall['executive_discovery_success']/overall['total_urls_tested']*100):.1f}%")
    print(f"🏛️ Companies House Coverage: {summary['companies_house_statistics']['companies_house_coverage']}%")
    
    print(f"\n📊 Key Metrics:")
    print(f"  - Total Executives Found: {summary['executive_discovery_statistics']['total_executives_found']}")
    print(f"  - Average Contact Completeness: {summary['executive_discovery_statistics']['average_contact_completeness']}%")
    print(f"  - Contact Discovery Rate: {summary['executive_discovery_statistics']['contact_discovery_rate']}%")
    print(f"  - Business Value Score: {summary['quality_metrics']['business_value_score']}")
    
    print("\n🎯 Comprehensive Production Test Complete!")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main()) 