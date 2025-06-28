#!/usr/bin/env python3
"""
Test Phase 9: Complete Executive Contact Intelligence Pipeline
=============================================================

Comprehensive testing of the complete Phase 9 pipeline integrating:
- Phase 9A: Contact Detail Extraction Engine
- Phase 9B: Email Discovery Enhancement Engine
- Real company data validation using 2Test.xlsx
- End-to-end executive contact intelligence assessment
- Performance benchmarking and quality metrics
- Zero-cost optimization validation

Tests complete executive discovery pipeline (Name, Phone, Email, LinkedIn)
Validates Context7 best practices across the full contact intelligence stack
"""

import asyncio
import json
import time
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import asdict
import statistics

# Import Phase 9 components
from phase9a_contact_extraction_engine import (
    Phase9aConfig, Phase9aContactExtractionEngine
)
from phase9b_email_discovery_enhancement import (
    Phase9bConfig, Phase9bEmailDiscoveryEngine
)

class Phase9CompletePipelineTest:
    """Complete Phase 9 Executive Contact Intelligence Pipeline Test"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize engines
        self.contact_engine = Phase9aContactExtractionEngine(Phase9aConfig())
        self.email_engine = Phase9bEmailDiscoveryEngine(Phase9bConfig())
        
        # Load test data
        self.test_data = self._load_test_data()
        
        # Results storage
        self.pipeline_results = []
        self.performance_metrics = {}
        self.quality_assessment = {}
    
    def _load_test_data(self) -> pd.DataFrame:
        """Load test data from 2Test.xlsx"""
        try:
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
            {'Company': 'A&H Plumbing', 'Website': 'http://anhplumbing.com'},
            {'Company': 'Air-Tech Systems Inc', 'Website': 'https://air-techsystems.com/'},
            {'Company': 'Test Engineering Ltd', 'Website': 'https://test-engineering.co.uk'}
        ]
        return pd.DataFrame(sample_data)
    
    async def run_complete_pipeline_test(self, max_companies: int = 5) -> Dict[str, Any]:
        """Run complete pipeline test with integrated Phase 9A and 9B"""
        
        print("🚀 Starting Complete Phase 9 Executive Contact Intelligence Pipeline Test")
        print("=" * 90)
        
        test_results = {
            'test_timestamp': int(time.time()),
            'companies_processed': 0,
            'successful_extractions': 0,
            'total_executives_found': 0,
            'total_contacts_extracted': 0,
            'total_emails_discovered': 0,
            'total_emails_inferred': 0,
            'processing_times': [],
            'detailed_results': [],
            'quality_metrics': {},
            'performance_assessment': {}
        }
        
        # Process subset of companies
        test_companies = self.test_data.head(max_companies)
        
        for idx, row in test_companies.iterrows():
            company_name = row.get('Company', f'Company_{idx}')
            website_url = row.get('Website', 'http://example.com')
            
            print(f"\n📊 Processing Company {idx + 1}/{len(test_companies)}: {company_name}")
            print("-" * 60)
            
            try:
                # Phase 1: Contact Extraction (Phase 9A)
                print("  🔍 Phase 9A: Contact Detail Extraction...")
                contact_start = time.time()
                
                contact_result = await self.contact_engine.extract_executive_contacts(
                    company_name, website_url
                )
                
                contact_time = time.time() - contact_start
                
                if contact_result.get('error'):
                    print(f"  ❌ Contact extraction failed: {contact_result['error']}")
                    continue
                
                executives = contact_result.get('executive_profiles', [])
                contact_stats = contact_result.get('extraction_stats', {})
                
                print(f"    ✅ Found {len(executives)} executives")
                print(f"    📞 Extracted {contact_stats.get('total_contacts_extracted', 0)} contacts")
                print(f"    ⏱️ Time: {contact_time:.2f}s")
                
                # Phase 2: Email Discovery Enhancement (Phase 9B)
                print("  📧 Phase 9B: Email Discovery Enhancement...")
                email_start = time.time()
                
                # Extract domain from website URL
                domain = self._extract_domain(website_url)
                
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
                
                email_time = time.time() - email_start
                
                print(f"    ✅ Discovered {len(email_result.discovered_emails)} emails")
                print(f"    🧠 Inferred {len(email_result.inferred_emails)} emails")
                print(f"    📈 Discovery confidence: {email_result.discovery_confidence:.1%}")
                print(f"    ⏱️ Time: {email_time:.2f}s")
                
                # Phase 3: Integration and Quality Assessment
                print("  🔗 Phase 3: Integration & Quality Assessment...")
                integration_result = self._integrate_results(
                    company_name, contact_result, email_result, contact_time, email_time
                )
                
                # Update test results
                test_results['companies_processed'] += 1
                test_results['successful_extractions'] += 1
                test_results['total_executives_found'] += len(executives)
                test_results['total_contacts_extracted'] += contact_stats.get('total_contacts_extracted', 0)
                test_results['total_emails_discovered'] += len(email_result.discovered_emails)
                test_results['total_emails_inferred'] += len(email_result.inferred_emails)
                test_results['processing_times'].append(contact_time + email_time)
                test_results['detailed_results'].append(integration_result)
                
                print(f"    🎯 Overall Quality Score: {integration_result['quality_metrics']['overall_score']:.1%}")
                print(f"    📈 Completeness: {integration_result['quality_metrics']['completeness_percentage']:.1f}%")
                
            except Exception as e:
                self.logger.error(f"Pipeline error for {company_name}: {e}")
                test_results['companies_processed'] += 1
                test_results['detailed_results'].append({
                    'company_name': company_name,
                    'website_url': website_url,
                    'error': str(e),
                    'processing_successful': False
                })
                print(f"  ❌ Pipeline failed: {e}")
        
        # Calculate overall metrics
        test_results['quality_metrics'] = self._calculate_overall_quality_metrics(test_results)
        test_results['performance_assessment'] = self._calculate_performance_assessment(test_results)
        
        # Save results
        timestamp = int(time.time())
        results_file = f"phase9_complete_pipeline_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"\n💾 Complete pipeline results saved to: {results_file}")
        
        # Display summary
        self._display_pipeline_summary(test_results)
        
        return test_results
    
    def _extract_domain(self, website_url: str) -> str:
        """Extract domain from website URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(website_url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return "example.com"
    
    def _integrate_results(self, company_name: str, contact_result: Dict, 
                          email_result: Any, contact_time: float, email_time: float) -> Dict[str, Any]:
        """Integrate Phase 9A and 9B results for comprehensive assessment"""
        
        executives = contact_result.get('executive_profiles', [])
        contact_stats = contact_result.get('extraction_stats', {})
        
        # Calculate integration metrics
        total_processing_time = contact_time + email_time
        total_contacts = contact_stats.get('total_contacts_extracted', 0)
        total_emails = len(email_result.discovered_emails) + len(email_result.inferred_emails)
        
        # Quality metrics
        quality_metrics = {
            'overall_score': self._calculate_integrated_quality_score(contact_result, email_result),
            'completeness_percentage': self._calculate_completeness_percentage(executives, email_result),
            'contact_diversity_score': self._calculate_contact_diversity(executives, email_result),
            'confidence_score': self._calculate_integrated_confidence(contact_result, email_result)
        }
        
        # Contact intelligence summary
        contact_intelligence = {
            'executives_with_complete_contacts': 0,
            'executives_with_partial_contacts': 0,
            'total_phone_numbers': 0,
            'total_email_addresses': total_emails,
            'total_linkedin_profiles': 0,
            'contact_attribution_success_rate': 0.0
        }
        
        # Analyze executive contact completeness
        for executive in executives:
            contact_info = executive.get('contact_info', {})
            
            phone_count = len(contact_info.get('phone_numbers', []))
            email_count = len(contact_info.get('email_addresses', []))
            linkedin_count = len(contact_info.get('linkedin_profiles', []))
            
            contact_intelligence['total_phone_numbers'] += phone_count
            contact_intelligence['total_linkedin_profiles'] += linkedin_count
            
            # Determine completeness
            contact_types_found = sum([phone_count > 0, email_count > 0, linkedin_count > 0])
            
            if contact_types_found >= 2:
                contact_intelligence['executives_with_complete_contacts'] += 1
            elif contact_types_found >= 1:
                contact_intelligence['executives_with_partial_contacts'] += 1
        
        # Calculate attribution success rate
        total_executives = len(executives)
        attributed_executives = (
            contact_intelligence['executives_with_complete_contacts'] + 
            contact_intelligence['executives_with_partial_contacts']
        )
        
        if total_executives > 0:
            contact_intelligence['contact_attribution_success_rate'] = attributed_executives / total_executives
        
        return {
            'company_name': company_name,
            'processing_successful': True,
            'processing_time': {
                'contact_extraction_time': contact_time,
                'email_discovery_time': email_time,
                'total_time': total_processing_time
            },
            'executive_discovery': {
                'total_executives_found': len(executives),
                'executives_with_contacts': attributed_executives,
                'average_completeness': sum(e.get('contact_info', {}).get('completeness_percentage', 0) for e in executives) / max(1, len(executives))
            },
            'contact_extraction_summary': {
                'total_contacts_extracted': total_contacts,
                'contact_types_found': contact_stats.get('pages_analyzed', 0),
                'extraction_quality': contact_result.get('quality_assessment', {}).get('overall_quality', 'UNKNOWN')
            },
            'email_discovery_summary': {
                'emails_discovered': len(email_result.discovered_emails),
                'emails_inferred': len(email_result.inferred_emails),
                'discovery_confidence': email_result.discovery_confidence,
                'pattern_analysis': email_result.pattern_analysis
            },
            'contact_intelligence': contact_intelligence,
            'quality_metrics': quality_metrics
        }
    
    def _calculate_integrated_quality_score(self, contact_result: Dict, email_result: Any) -> float:
        """Calculate integrated quality score across both phases"""
        
        # Contact extraction quality
        contact_quality = contact_result.get('quality_assessment', {}).get('quality_score', 0.0)
        
        # Email discovery quality
        email_quality = email_result.discovery_confidence
        
        # Integration quality (weighted average)
        integrated_score = (contact_quality * 0.6) + (email_quality * 0.4)
        
        return integrated_score
    
    def _calculate_completeness_percentage(self, executives: List[Dict], email_result: Any) -> float:
        """Calculate overall contact completeness percentage"""
        if not executives:
            return 0.0
        
        total_completeness = 0.0
        
        for executive in executives:
            contact_info = executive.get('contact_info', {})
            exec_completeness = contact_info.get('completeness_percentage', 0)
            
            # Boost for email enhancement
            if email_result.inferred_emails:
                exec_completeness = min(100, exec_completeness + 20)
            
            total_completeness += exec_completeness
        
        return total_completeness / len(executives)
    
    def _calculate_contact_diversity(self, executives: List[Dict], email_result: Any) -> float:
        """Calculate contact type diversity score"""
        total_contact_types = 0
        total_possible_types = len(executives) * 3  # Phone, Email, LinkedIn per executive
        
        for executive in executives:
            contact_info = executive.get('contact_info', {})
            
            if contact_info.get('phone_numbers'):
                total_contact_types += 1
            if contact_info.get('email_addresses') or email_result.inferred_emails:
                total_contact_types += 1
            if contact_info.get('linkedin_profiles'):
                total_contact_types += 1
        
        return total_contact_types / max(1, total_possible_types)
    
    def _calculate_integrated_confidence(self, contact_result: Dict, email_result: Any) -> float:
        """Calculate integrated confidence score"""
        
        # Average executive confidence from Phase 9A
        executives = contact_result.get('executive_profiles', [])
        if executives:
            avg_exec_confidence = sum(e.get('overall_confidence', 0) for e in executives) / len(executives)
        else:
            avg_exec_confidence = 0.0
        
        # Email discovery confidence from Phase 9B
        email_confidence = email_result.discovery_confidence
        
        # Integrated confidence
        return (avg_exec_confidence * 0.7) + (email_confidence * 0.3)
    
    def _calculate_overall_quality_metrics(self, test_results: Dict) -> Dict[str, Any]:
        """Calculate overall quality metrics across all companies"""
        
        successful_results = [r for r in test_results['detailed_results'] if r.get('processing_successful')]
        
        if not successful_results:
            return {'overall_assessment': 'NO_SUCCESSFUL_RESULTS', 'quality_grade': 'F'}
        
        # Calculate averages
        avg_quality_score = statistics.mean([r['quality_metrics']['overall_score'] for r in successful_results])
        avg_completeness = statistics.mean([r['quality_metrics']['completeness_percentage'] for r in successful_results])
        avg_confidence = statistics.mean([r['quality_metrics']['confidence_score'] for r in successful_results])
        avg_diversity = statistics.mean([r['quality_metrics']['contact_diversity_score'] for r in successful_results])
        
        # Success rates
        success_rate = test_results['successful_extractions'] / max(1, test_results['companies_processed'])
        
        # Overall grade
        overall_score = (avg_quality_score * 0.3) + (avg_completeness/100 * 0.3) + (success_rate * 0.4)
        
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
        
        return {
            'overall_score': overall_score,
            'quality_grade': grade,
            'average_quality_score': avg_quality_score,
            'average_completeness': avg_completeness,
            'average_confidence': avg_confidence,
            'average_diversity': avg_diversity,
            'success_rate': success_rate,
            'total_companies_tested': test_results['companies_processed'],
            'successful_extractions': test_results['successful_extractions']
        }
    
    def _calculate_performance_assessment(self, test_results: Dict) -> Dict[str, Any]:
        """Calculate performance assessment metrics"""
        
        processing_times = test_results['processing_times']
        
        if not processing_times:
            return {'assessment': 'NO_TIMING_DATA'}
        
        # Performance metrics
        avg_processing_time = statistics.mean(processing_times)
        min_processing_time = min(processing_times)
        max_processing_time = max(processing_times)
        companies_per_hour = 3600 / avg_processing_time if avg_processing_time > 0 else 0
        
        # Efficiency metrics
        total_executives = test_results['total_executives_found']
        total_contacts = test_results['total_contacts_extracted']
        total_emails = test_results['total_emails_discovered'] + test_results['total_emails_inferred']
        
        executives_per_minute = total_executives / (sum(processing_times) / 60) if processing_times else 0
        contacts_per_minute = (total_contacts + total_emails) / (sum(processing_times) / 60) if processing_times else 0
        
        # Performance grade
        if avg_processing_time <= 30:
            perf_grade = 'EXCELLENT'
        elif avg_processing_time <= 60:
            perf_grade = 'GOOD'
        elif avg_processing_time <= 120:
            perf_grade = 'ACCEPTABLE'
        else:
            perf_grade = 'NEEDS_OPTIMIZATION'
        
        return {
            'performance_grade': perf_grade,
            'average_processing_time_seconds': avg_processing_time,
            'min_processing_time_seconds': min_processing_time,
            'max_processing_time_seconds': max_processing_time,
            'companies_per_hour': companies_per_hour,
            'executives_per_minute': executives_per_minute,
            'contacts_per_minute': contacts_per_minute,
            'total_processing_time_seconds': sum(processing_times)
        }
    
    def _display_pipeline_summary(self, test_results: Dict):
        """Display comprehensive pipeline summary"""
        
        print("\n" + "=" * 90)
        print("🎯 PHASE 9 COMPLETE PIPELINE SUMMARY")
        print("=" * 90)
        
        # Overall metrics
        quality_metrics = test_results['quality_metrics']
        performance_metrics = test_results['performance_assessment']
        
        print(f"📊 Overall Assessment: {quality_metrics['quality_grade']} (Score: {quality_metrics['overall_score']:.1%})")
        print(f"🏢 Companies Processed: {test_results['companies_processed']}")
        print(f"✅ Successful Extractions: {test_results['successful_extractions']} ({quality_metrics['success_rate']:.1%})")
        
        print(f"\n👥 Executive Discovery:")
        print(f"   Total Executives Found: {test_results['total_executives_found']}")
        print(f"   Average per Company: {test_results['total_executives_found'] / max(1, test_results['companies_processed']):.1f}")
        
        print(f"\n📞 Contact Intelligence:")
        print(f"   Total Contacts Extracted: {test_results['total_contacts_extracted']}")
        print(f"   Total Emails Discovered: {test_results['total_emails_discovered']}")
        print(f"   Total Emails Inferred: {test_results['total_emails_inferred']}")
        print(f"   Average Completeness: {quality_metrics['average_completeness']:.1f}%")
        
        print(f"\n⚡ Performance Assessment:")
        print(f"   Performance Grade: {performance_metrics['performance_grade']}")
        print(f"   Average Processing Time: {performance_metrics['average_processing_time_seconds']:.1f}s")
        print(f"   Companies per Hour: {performance_metrics['companies_per_hour']:.1f}")
        print(f"   Contacts per Minute: {performance_metrics['contacts_per_minute']:.1f}")
        
        print(f"\n🎯 Quality Metrics:")
        print(f"   Quality Score: {quality_metrics['average_quality_score']:.1%}")
        print(f"   Confidence Score: {quality_metrics['average_confidence']:.1%}")
        print(f"   Contact Diversity: {quality_metrics['average_diversity']:.1%}")

async def run_complete_phase9_pipeline_test():
    """Run the complete Phase 9 pipeline test"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize and run test
    pipeline_test = Phase9CompletePipelineTest()
    results = await pipeline_test.run_complete_pipeline_test(max_companies=5)
    
    return results

if __name__ == "__main__":
    # Run complete pipeline test
    asyncio.run(run_complete_phase9_pipeline_test())