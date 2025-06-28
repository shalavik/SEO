"""
REAL Executive Discovery Test - Validation of Fixed Implementation
Tests the enhanced Executive Discovery Orchestrator with real data extraction
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import the fixed orchestrator
from src.seo_leads.orchestrators.executive_discovery_orchestrator import ExecutiveDiscoveryOrchestrator

class RealExecutiveDiscoveryTester:
    """Test real executive discovery with validation"""
    
    def __init__(self):
        self.orchestrator = ExecutiveDiscoveryOrchestrator()
        
    async def test_real_executive_discovery(self):
        """Test real executive discovery on various company websites"""
        
        # Test companies with known executive information
        test_companies = [
            {
                "company": "Ideal Plumbing Services",
                "url": "https://idealplumbingservices.com",
                "expected_executives": 1,
                "known_info": "Should find company executives with contact details"
            },
            {
                "company": "Jack The Plumber Birmingham", 
                "url": "https://jacktheplumber.co.uk",
                "expected_executives": 1,
                "known_info": "Should find Jack or management contact information"
            },
            {
                "company": "MK Plumbing Birmingham",
                "url": "https://mkplumbingbirmingham.co.uk", 
                "expected_executives": 1,
                "known_info": "Should find company leadership information"
            },
            {
                "company": "MATT Plumbing and Heating",
                "url": "https://mattplumbingandheating.com",
                "expected_executives": 1,
                "known_info": "Should find Matt or company executives"
            },
            {
                "company": "Summit Plumbing & Heating",
                "url": "https://summitplumbingandheating.co.uk",
                "expected_executives": 1,
                "known_info": "Should find company management information"
            }
        ]
        
        results = {
            'test_timestamp': datetime.now().isoformat(),
            'test_purpose': 'Validate REAL executive discovery vs placeholder data',
            'companies_tested': len(test_companies),
            'results': [],
            'summary': {}
        }
        
        logger.info("=== STARTING REAL EXECUTIVE DISCOVERY TEST ===")
        logger.info(f"Testing {len(test_companies)} companies for REAL executive data extraction")
        
        total_executives_found = 0
        real_contacts_found = 0
        companies_with_executives = 0
        
        for i, company in enumerate(test_companies, 1):
            logger.info(f"\n[{i}/{len(test_companies)}] Testing: {company['company']}")
            logger.info(f"URL: {company['url']}")
            
            start_time = time.time()
            
            try:
                # Execute real executive discovery
                discovery_result = await self.orchestrator.execute_comprehensive_discovery(company['url'])
                
                processing_time = time.time() - start_time
                
                # Analyze results for real vs placeholder data
                analysis = self._analyze_discovery_quality(discovery_result, company)
                
                company_result = {
                    'company_name': company['company'],
                    'test_url': company['url'],
                    'actual_url': discovery_result.actual_working_url,
                    'executives_found': len(discovery_result.executives),
                    'processing_time_seconds': round(processing_time, 2),
                    'discovery_success': len(discovery_result.executives) > 0,
                    'real_data_quality': analysis,
                    'executives': []
                }
                
                # Document each executive found
                for exec in discovery_result.executives:
                    exec_data = {
                        'name': exec.name,
                        'title': exec.title,
                        'email': exec.email,
                        'phone': exec.phone,
                        'linkedin_url': exec.linkedin_url,
                        'confidence_score': exec.confidence_score,
                        'discovery_method': exec.discovery_method,
                        'sources': exec.discovery_sources,
                        'validation_notes': exec.validation_notes,
                        'is_real_data': not exec.name.startswith('Managing Director')  # Check if not placeholder
                    }
                    
                    company_result['executives'].append(exec_data)
                    
                    # Count real contacts
                    if exec.email or exec.phone or exec.linkedin_url:
                        real_contacts_found += 1
                    
                    logger.info(f"  EXECUTIVE FOUND:")
                    logger.info(f"    Name: {exec.name}")
                    logger.info(f"    Title: {exec.title}")
                    logger.info(f"    Email: {exec.email or 'Not found'}")
                    logger.info(f"    Phone: {exec.phone or 'Not found'}")
                    logger.info(f"    LinkedIn: {exec.linkedin_url or 'Not found'}")
                    logger.info(f"    Confidence: {exec.confidence_score:.2f}")
                    logger.info(f"    Method: {exec.discovery_method}")
                
                total_executives_found += len(discovery_result.executives)
                if len(discovery_result.executives) > 0:
                    companies_with_executives += 1
                
                results['results'].append(company_result)
                
                logger.info(f"  ✅ Discovery complete: {len(discovery_result.executives)} executives found")
                
            except Exception as e:
                logger.error(f"  ❌ Discovery failed: {e}")
                
                company_result = {
                    'company_name': company['company'],
                    'test_url': company['url'],
                    'error': str(e),
                    'processing_time_seconds': round(time.time() - start_time, 2),
                    'discovery_success': False,
                    'executives': []
                }
                
                results['results'].append(company_result)
        
        # Calculate summary metrics
        results['summary'] = {
            'total_companies_tested': len(test_companies),
            'companies_with_executives': companies_with_executives,
            'executive_discovery_rate': f"{(companies_with_executives / len(test_companies) * 100):.1f}%",
            'total_executives_found': total_executives_found,
            'average_executives_per_company': round(total_executives_found / len(test_companies), 2),
            'real_contacts_found': real_contacts_found,
            'contact_discovery_rate': f"{(real_contacts_found / max(total_executives_found, 1) * 100):.1f}%",
            'placeholder_data_eliminated': self._check_placeholder_elimination(results['results']),
            'data_quality_assessment': self._assess_overall_quality(results['results'])
        }
        
        # Save results
        timestamp = int(time.time())
        filename = f"real_executive_discovery_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        self._print_test_summary(results)
        
        logger.info(f"\n✅ Test complete! Results saved to: {filename}")
        
        return results
    
    def _analyze_discovery_quality(self, discovery_result, company_info):
        """Analyze the quality of discovery results"""
        
        quality = {
            'url_handling': 'SUCCESS' if discovery_result.actual_working_url != company_info['url'] else 'PRESERVED',
            'company_identification': 'SUCCESS' if discovery_result.company_name else 'FAILED',
            'executive_extraction': len(discovery_result.executives),
            'contact_completeness': 0,
            'real_vs_placeholder': 'REAL_DATA',
            'confidence_scores': []
        }
        
        # Analyze contact completeness
        total_contacts = 0
        total_possible = len(discovery_result.executives) * 3  # email, phone, linkedin
        
        for exec in discovery_result.executives:
            if exec.email:
                total_contacts += 1
            if exec.phone:
                total_contacts += 1
            if exec.linkedin_url:
                total_contacts += 1
            
            quality['confidence_scores'].append(exec.confidence_score)
            
            # Check if this is placeholder data
            if exec.name == "Managing Director" and not exec.email and not exec.phone:
                quality['real_vs_placeholder'] = 'PLACEHOLDER_DETECTED'
        
        quality['contact_completeness'] = (total_contacts / max(total_possible, 1)) * 100
        quality['average_confidence'] = sum(quality['confidence_scores']) / max(len(quality['confidence_scores']), 1)
        
        return quality
    
    def _check_placeholder_elimination(self, results):
        """Check if placeholder data has been successfully eliminated"""
        
        placeholder_count = 0
        real_data_count = 0
        
        for result in results:
            for exec in result.get('executives', []):
                if exec.get('is_real_data', False):
                    real_data_count += 1
                else:
                    placeholder_count += 1
        
        if placeholder_count == 0 and real_data_count > 0:
            return "SUCCESS - No placeholder data detected"
        elif placeholder_count > 0:
            return f"PARTIAL - {placeholder_count} placeholder entries still found"
        else:
            return "NO_DATA - No executives found"
    
    def _assess_overall_quality(self, results):
        """Assess overall data quality"""
        
        total_executives = sum(len(r.get('executives', [])) for r in results)
        executives_with_contacts = sum(
            1 for r in results 
            for exec in r.get('executives', [])
            if exec.get('email') or exec.get('phone') or exec.get('linkedin_url')
        )
        
        if total_executives == 0:
            return "POOR - No executives found"
        
        contact_rate = (executives_with_contacts / total_executives) * 100
        
        if contact_rate >= 80:
            return f"EXCELLENT - {contact_rate:.1f}% of executives have contact info"
        elif contact_rate >= 60:
            return f"GOOD - {contact_rate:.1f}% of executives have contact info"
        elif contact_rate >= 40:
            return f"MODERATE - {contact_rate:.1f}% of executives have contact info"
        else:
            return f"POOR - Only {contact_rate:.1f}% of executives have contact info"
    
    def _print_test_summary(self, results):
        """Print comprehensive test summary"""
        
        summary = results['summary']
        
        print("\n" + "="*80)
        print("🎯 REAL EXECUTIVE DISCOVERY TEST SUMMARY")
        print("="*80)
        
        print(f"📊 DISCOVERY PERFORMANCE:")
        print(f"   • Companies Tested: {summary['total_companies_tested']}")
        print(f"   • Executive Discovery Rate: {summary['executive_discovery_rate']}")
        print(f"   • Total Executives Found: {summary['total_executives_found']}")
        print(f"   • Average per Company: {summary['average_executives_per_company']}")
        
        print(f"\n📧 CONTACT INFORMATION:")
        print(f"   • Real Contacts Found: {summary['real_contacts_found']}")
        print(f"   • Contact Discovery Rate: {summary['contact_discovery_rate']}")
        
        print(f"\n✅ DATA QUALITY:")
        print(f"   • Placeholder Elimination: {summary['placeholder_data_eliminated']}")
        print(f"   • Overall Quality: {summary['data_quality_assessment']}")
        
        print(f"\n📈 INDIVIDUAL COMPANY RESULTS:")
        for i, result in enumerate(results['results'], 1):
            status = "✅" if result.get('discovery_success', False) else "❌"
            execs = len(result.get('executives', []))
            contacts = sum(1 for e in result.get('executives', []) if e.get('email') or e.get('phone') or e.get('linkedin_url'))
            
            print(f"   {i}. {status} {result['company_name']}: {execs} executives, {contacts} with contacts")
        
        print("="*80)

async def main():
    """Run the real executive discovery test"""
    
    logger.info("Initializing Real Executive Discovery Test")
    
    tester = RealExecutiveDiscoveryTester()
    
    try:
        results = await tester.test_real_executive_discovery()
        
        # Verify the fix was successful
        total_execs = results['summary']['total_executives_found']
        real_contacts = results['summary']['real_contacts_found']
        
        if total_execs > 0 and real_contacts > 0:
            logger.info("🎉 SUCCESS: Real executive discovery is working!")
            logger.info(f"Found {total_execs} executives with {real_contacts} real contact details")
        else:
            logger.warning("⚠️  Limited success: Few real contacts found")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main()) 