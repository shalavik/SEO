#!/usr/bin/env python3
"""
Comprehensive Phase 9 Executive Contact Intelligence Pipeline Test
- Tests complete SEO analysis and executive extraction pipeline
- Phase 9A: Contact Detail Extraction Engine
- Phase 9B: Email Discovery Enhancement Engine  
- Processes URLs with error handling and recovery
- Generates comprehensive JSON results report

Context7-inspired Phase 9 pipeline testing - Zero-cost executive discovery
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import traceback
import sys

# Import Phase 9 pipeline components only
sys.path.append('.')
from phase9a_contact_extraction_engine import (
    Phase9aConfig, Phase9aContactExtractionEngine
)
from phase9b_email_discovery_enhancement import (
    Phase9bConfig, Phase9bEmailDiscoveryEngine
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Phase9ComprehensiveTestResult:
    """Complete Phase 9 test results for all URLs"""
    test_id: str = ""
    test_timestamp: str = ""
    total_urls: int = 0
    successful_processes: int = 0
    failed_processes: int = 0
    total_processing_time: float = 0.0
    
    # URL Results
    url_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Phase 9 Aggregate Metrics
    total_executives_found: int = 0
    total_contacts_extracted: int = 0
    total_emails_discovered: int = 0
    total_emails_inferred: int = 0
    
    # Quality Metrics
    average_confidence: float = 0.0
    average_completeness: float = 0.0
    average_quality_score: float = 0.0
    success_rate: float = 0.0
    
    # Error Tracking
    error_summary: Dict[str, int] = field(default_factory=dict)
    failed_urls: List[str] = field(default_factory=list)

class Phase9ComprehensiveFullPipelineTest:
    """Context7-inspired Phase 9 comprehensive pipeline testing system"""
    
    def __init__(self):
        # Initialize Phase 9 engines
        self.contact_engine = Phase9aContactExtractionEngine(Phase9aConfig())
        self.email_engine = Phase9bEmailDiscoveryEngine(Phase9bConfig())
        
        self.test_urls = [
            "www.webbplumbingheatingandair.com",
            "http://hspvirginia.com/",
            "https://www.hugeecorporation.com/?utm_source=google&utm_medium=organic&utm_campaign=gbp",
            "https://www.justbetterhomeservices.com/locations/richmond",
            "www.keilservice.com",
            "http://kellammechanical.com",
            "http://www.krafftservice.net/",
            "www.maddoxairandelectrical.com",
            "https://magnoliacompanies.com/?utm_source=GMB&utm_medium=Organic&utm_campaign=1SEO_SM",
            "http://millershomecomfort.com",
            "http://nicehomeservices.com",
            "www.norfolkair-hvac.com",
            "www.nvac4u.com",
            "www.philbrickheatingandcooling.com",
            "www.powells-plumbing.com",
            "https://www.reddickandsons.com/",
            "https://www.richardsac.com/?utm_source=google&utm_medium=organic&utm_campaign=falls_church_gbp"
        ]
        
    def normalize_url(self, url: str) -> str:
        """Normalize URL format for processing"""
        url = url.strip()
        if url.startswith('@'):
            url = url[1:]
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
    
    def extract_company_name(self, url: str) -> str:
        """Extract company name from URL"""
        # Remove protocol and www
        domain = url.replace('https://', '').replace('http://', '')
        domain = domain.replace('www.', '')
        # Get base domain
        domain = domain.split('/')[0].split('?')[0]
        # Convert to company name
        company_name = domain.replace('.com', '').replace('.net', '').replace('.org', '')
        # Convert camelCase or domain format to readable name
        words = []
        current_word = ''
        for char in company_name:
            if char.isupper() and current_word:
                words.append(current_word)
                current_word = char
            elif char in ['-', '_', '.']:
                if current_word:
                    words.append(current_word)
                current_word = ''
            else:
                current_word += char
        if current_word:
            words.append(current_word)
        
        return ' '.join(words).title()
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL for email discovery"""
        try:
            domain = url.replace('https://', '').replace('http://', '')
            domain = domain.replace('www.', '')
            domain = domain.split('/')[0].split('?')[0]
            return domain
        except:
            return "example.com"
    
    async def test_single_url(self, url: str) -> Dict[str, Any]:
        """Test single URL with comprehensive Phase 9 pipeline"""
        normalized_url = self.normalize_url(url)
        company_name = self.extract_company_name(normalized_url)
        domain = self.extract_domain(normalized_url)
        
        logger.info(f"Testing URL: {normalized_url} (Company: {company_name})")
        
        start_time = time.time()
        result = {
            'original_url': url,
            'normalized_url': normalized_url,
            'company_name': company_name,
            'domain': domain,
            'success': False,
            'processing_time': 0.0,
            'executives_found': 0,
            'contacts_extracted': 0,
            'emails_discovered': 0,
            'emails_inferred': 0,
            'confidence_score': 0.0,
            'completeness_score': 0.0,
            'quality_score': 0.0,
            'quality_grade': 'F',
            'data_sources': ['Phase 9A Contact Extraction', 'Phase 9B Email Discovery'],
            'error_message': None,
            'detailed_results': None
        }
        
        try:
            # Phase 9A: Contact Detail Extraction
            logger.info(f"  🔍 Phase 9A: Contact extraction from {normalized_url}")
            contact_result = await self.contact_engine.extract_executive_contacts(
                company_name, normalized_url
            )
            
            if contact_result.get('error'):
                raise Exception(f"Phase 9A failed: {contact_result['error']}")
            
            executives = contact_result.get('executive_profiles', [])
            contact_stats = contact_result.get('extraction_stats', {})
            
            # Phase 9B: Email Discovery Enhancement  
            logger.info(f"  📧 Phase 9B: Email discovery for {domain}")
            
            # Convert executives for Phase 9B
            exec_list = []
            for exec_profile in executives:
                exec_list.append({
                    'name': exec_profile.get('name', ''),
                    'title': exec_profile.get('title', '')
                })
            
            email_result = await self.email_engine.discover_executive_emails(
                company_name, domain, exec_list
            )
            
            # Process successful results
            result['success'] = True
            result['executives_found'] = len(executives)
            result['contacts_extracted'] = contact_stats.get('total_contacts_extracted', 0)
            result['emails_discovered'] = len(email_result.discovered_emails)
            result['emails_inferred'] = len(email_result.inferred_emails)
            
            # Calculate quality metrics
            result['confidence_score'] = self._calculate_confidence_score(contact_result, email_result)
            result['completeness_score'] = self._calculate_completeness_score(executives, email_result)
            result['quality_score'] = self._calculate_overall_quality_score(result)
            
            # Generate detailed results
            result['detailed_results'] = {
                'phase_9a_results': {
                    'executive_profiles': executives,
                    'extraction_stats': contact_stats,
                    'processing_metadata': contact_result.get('processing_metadata', {})
                },
                'phase_9b_results': {
                    'discovered_emails': email_result.discovered_emails,
                    'inferred_emails': email_result.inferred_emails,
                    'discovery_confidence': email_result.discovery_confidence,
                    'domain_intelligence': email_result.domain_intelligence
                },
                'integration_metrics': {
                    'total_contact_points': result['contacts_extracted'] + result['emails_discovered'] + result['emails_inferred'],
                    'executive_coverage': len([e for e in executives if e.get('contact_info')]),
                    'data_completeness': result['completeness_score']
                }
            }
            
            # Calculate quality grade
            if result['quality_score'] >= 0.8:
                result['quality_grade'] = 'A'
            elif result['quality_score'] >= 0.7:
                result['quality_grade'] = 'B'
            elif result['quality_score'] >= 0.6:
                result['quality_grade'] = 'C'
            elif result['quality_score'] >= 0.5:
                result['quality_grade'] = 'D'
            else:
                result['quality_grade'] = 'F'
                
        except Exception as e:
            logger.error(f"Error processing {normalized_url}: {str(e)}")
            result['error_message'] = str(e)
            result['traceback'] = traceback.format_exc()
        
        result['processing_time'] = time.time() - start_time
        logger.info(f"Completed {normalized_url} in {result['processing_time']:.2f}s - Success: {result['success']}")
        
        return result
    
    def _calculate_confidence_score(self, contact_result: Dict, email_result: Any) -> float:
        """Calculate integrated confidence score from Phase 9A and 9B"""
        contact_confidence = contact_result.get('quality_metrics', {}).get('overall_confidence', 0.0)
        email_confidence = email_result.discovery_confidence if hasattr(email_result, 'discovery_confidence') else 0.0
        return (contact_confidence + email_confidence) / 2
    
    def _calculate_completeness_score(self, executives: List[Dict], email_result: Any) -> float:
        """Calculate data completeness percentage"""
        if not executives:
            return 0.0
        
        total_possible_contacts = len(executives) * 3  # name + phone + email per executive
        actual_contacts = 0
        
        for exec_profile in executives:
            if exec_profile.get('name'):
                actual_contacts += 1
            contact_info = exec_profile.get('contact_info', {})
            if contact_info.get('phones'):
                actual_contacts += 1
            if contact_info.get('emails'):
                actual_contacts += 1
        
        # Add email discovery bonus
        if hasattr(email_result, 'discovered_emails'):
            actual_contacts += len(email_result.discovered_emails) * 0.5
        if hasattr(email_result, 'inferred_emails'):
            actual_contacts += len(email_result.inferred_emails) * 0.3
        
        return min(actual_contacts / total_possible_contacts, 1.0)
    
    def _calculate_overall_quality_score(self, result: Dict) -> float:
        """Calculate overall quality score"""
        weights = {
            'success': 0.3,
            'confidence': 0.3,
            'completeness': 0.2,
            'contact_diversity': 0.2
        }
        
        success_score = 1.0 if result['success'] else 0.0
        confidence_score = result['confidence_score']
        completeness_score = result['completeness_score']
        
        # Contact diversity score
        total_contacts = result['contacts_extracted'] + result['emails_discovered'] + result['emails_inferred']
        diversity_score = min(total_contacts / 10, 1.0)  # Normalize to max 10 contacts
        
        quality_score = (
            weights['success'] * success_score +
            weights['confidence'] * confidence_score +
            weights['completeness'] * completeness_score +
            weights['contact_diversity'] * diversity_score
        )
        
        return quality_score
    
    async def run_comprehensive_test(self) -> Phase9ComprehensiveTestResult:
        """Run comprehensive Phase 9 test on all URLs"""
        test_id = f"phase9_comprehensive_test_{int(time.time())}"
        logger.info(f"Starting comprehensive Phase 9 pipeline test: {test_id}")
        logger.info(f"Testing {len(self.test_urls)} URLs with Phase 9 executive contact intelligence")
        
        test_result = Phase9ComprehensiveTestResult(
            test_id=test_id,
            test_timestamp=datetime.now().isoformat(),
            total_urls=len(self.test_urls)
        )
        
        start_time = time.time()
        
        # Process URLs with conservative rate limiting
        for i, url in enumerate(self.test_urls, 1):
            logger.info(f"Processing URL {i}/{len(self.test_urls)}: {url}")
            
            url_result = await self.test_single_url(url)
            test_result.url_results.append(url_result)
            
            # Update aggregate metrics
            if url_result['success']:
                test_result.successful_processes += 1
                test_result.total_executives_found += url_result['executives_found']
                test_result.total_contacts_extracted += url_result['contacts_extracted']
                test_result.total_emails_discovered += url_result['emails_discovered']
                test_result.total_emails_inferred += url_result['emails_inferred']
            else:
                test_result.failed_processes += 1
                test_result.failed_urls.append(url)
                error_type = type(url_result.get('error_message', 'Unknown')).__name__
                test_result.error_summary[error_type] = test_result.error_summary.get(error_type, 0) + 1
            
            # Rate limiting - be respectful to websites
            if i < len(self.test_urls):
                logger.info("Waiting 3 seconds before next request...")
                await asyncio.sleep(3)
        
        test_result.total_processing_time = time.time() - start_time
        
        # Calculate final metrics
        test_result.success_rate = (test_result.successful_processes / test_result.total_urls) * 100
        
        if test_result.successful_processes > 0:
            successful_results = [r for r in test_result.url_results if r['success']]
            test_result.average_confidence = sum(r['confidence_score'] for r in successful_results) / len(successful_results)
            test_result.average_completeness = sum(r['completeness_score'] for r in successful_results) / len(successful_results)
            test_result.average_quality_score = sum(r['quality_score'] for r in successful_results) / len(successful_results)
        
        logger.info(f"Phase 9 test completed: {test_result.successful_processes}/{test_result.total_urls} successful")
        return test_result
    
    def save_results(self, test_result: Phase9ComprehensiveTestResult) -> str:
        """Save test results to JSON file"""
        filename = f"phase9_comprehensive_full_pipeline_results_{test_result.test_id}.json"
        filepath = Path(filename)
        
        # Convert dataclass to dict
        results_dict = {
            'test_metadata': {
                'test_id': test_result.test_id,
                'test_timestamp': test_result.test_timestamp,
                'total_urls': test_result.total_urls,
                'successful_processes': test_result.successful_processes,
                'failed_processes': test_result.failed_processes,
                'total_processing_time': test_result.total_processing_time,
                'pipeline_version': 'Phase 9 Executive Contact Intelligence'
            },
            'aggregate_metrics': {
                'total_executives_found': test_result.total_executives_found,
                'total_contacts_extracted': test_result.total_contacts_extracted,
                'total_emails_discovered': test_result.total_emails_discovered,
                'total_emails_inferred': test_result.total_emails_inferred,
                'average_confidence': test_result.average_confidence,
                'average_completeness': test_result.average_completeness,
                'average_quality_score': test_result.average_quality_score,
                'success_rate': test_result.success_rate
            },
            'error_analysis': {
                'error_summary': test_result.error_summary,
                'failed_urls': test_result.failed_urls
            },
            'detailed_results': test_result.url_results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {filepath}")
        return str(filepath)

async def main():
    """Main test execution"""
    print("🚀 Starting Comprehensive Phase 9 Executive Contact Intelligence Pipeline Test")
    print("=" * 80)
    print("Phase 9A: Contact Detail Extraction Engine")
    print("Phase 9B: Email Discovery Enhancement Engine")
    print("Zero-cost executive discovery with Context7 best practices")
    print("=" * 80)
    
    test_runner = Phase9ComprehensiveFullPipelineTest()
    
    try:
        # Run comprehensive Phase 9 test
        results = await test_runner.run_comprehensive_test()
        
        # Save results
        results_file = test_runner.save_results(results)
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 PHASE 9 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"Test ID: {results.test_id}")
        print(f"Total URLs Tested: {results.total_urls}")
        print(f"Successful Processes: {results.successful_processes}")
        print(f"Failed Processes: {results.failed_processes}")
        print(f"Success Rate: {results.success_rate:.1f}%")
        print(f"Total Processing Time: {results.total_processing_time:.2f} seconds")
        print(f"Average Time per URL: {results.total_processing_time/results.total_urls:.2f} seconds")
        print()
        print("📈 PHASE 9 AGGREGATE METRICS:")
        print(f"Total Executives Found: {results.total_executives_found}")
        print(f"Total Contacts Extracted: {results.total_contacts_extracted}")
        print(f"Total Emails Discovered: {results.total_emails_discovered}")
        print(f"Total Emails Inferred: {results.total_emails_inferred}")
        print(f"Average Confidence Score: {results.average_confidence:.3f}")
        print(f"Average Completeness Score: {results.average_completeness:.3f}")
        print(f"Average Quality Score: {results.average_quality_score:.3f}")
        print()
        print(f"📄 Detailed results saved to: {results_file}")
        
        if results.failed_urls:
            print(f"\n❌ Failed URLs ({len(results.failed_urls)}):")
            for url in results.failed_urls:
                print(f"  - {url}")
        
        print("\n✅ Phase 9 comprehensive pipeline test completed successfully!")
        print("🎯 Executive Contact Intelligence: Name + Phone + Email + LinkedIn")
        print("💰 Zero-cost operation with Context7 best practices")
        
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        print(f"\n❌ Test execution failed: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 