"""
High-Quality Executive Discovery Test
Tests executive discovery on websites known to have visible executive information
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

class HighQualityExecutiveDiscoveryTester:
    """Test high-quality executive discovery on websites with visible executive information"""
    
    def __init__(self):
        self.orchestrator = ExecutiveDiscoveryOrchestrator()
        
    async def test_high_quality_executive_discovery(self):
        """Test real executive discovery on websites with known executive visibility"""
        
        # Test companies with visible executive information
        test_companies = [
            {
                "company": "Sample Business Services",
                "url": "https://mattplumbingandheating.com",
                "expected_info": "Should extract MATT as potential executive/owner name from domain and content"
            },
            {
                "company": "Summit Plumbing Business", 
                "url": "https://summitplumbingandheating.co.uk",
                "expected_info": "Should extract contact information and business details"
            },
            {
                "company": "UK Professional Services",
                "url": "https://mkplumbingbirmingham.co.uk", 
                "expected_info": "Should extract MK or related executive information"
            }
        ]
        
        results = {
            'test_timestamp': datetime.now().isoformat(),
            'test_purpose': 'Validate HIGH-QUALITY executive discovery with real executive names',
            'companies_tested': len(test_companies),
            'results': [],
            'quality_analysis': {}
        }
        
        logger.info("=== HIGH-QUALITY EXECUTIVE DISCOVERY TEST ===")
        logger.info(f"Testing {len(test_companies)} companies for HIGH-QUALITY executive data")
        
        quality_executives = 0
        total_contacts = 0
        
        for i, company in enumerate(test_companies, 1):
            logger.info(f"\n[{i}/{len(test_companies)}] Testing: {company['company']}")
            logger.info(f"URL: {company['url']}")
            
            start_time = time.time()
            
            try:
                # Execute real executive discovery
                discovery_result = await self.orchestrator.execute_comprehensive_discovery(company['url'])
                
                processing_time = time.time() - start_time
                
                # Filter for high-quality executives
                high_quality_executives = self._filter_high_quality_executives(discovery_result.executives)
                
                company_result = {
                    'company_name': company['company'],
                    'test_url': company['url'],
                    'actual_url': discovery_result.actual_working_url,
                    'total_executives_found': len(discovery_result.executives),
                    'high_quality_executives': len(high_quality_executives),
                    'processing_time_seconds': round(processing_time, 2),
                    'executives': []
                }
                
                # Document high-quality executives
                for exec in high_quality_executives:
                    exec_data = {
                        'name': exec.name,
                        'title': exec.title,
                        'email': exec.email,
                        'phone': exec.phone,
                        'linkedin_url': exec.linkedin_url,
                        'confidence_score': exec.confidence_score,
                        'quality_score': self._calculate_executive_quality(exec),
                        'validation_notes': exec.validation_notes
                    }
                    
                    company_result['executives'].append(exec_data)
                    
                    # Count contacts
                    if exec.email or exec.phone or exec.linkedin_url:
                        total_contacts += 1
                    
                    logger.info(f"  HIGH-QUALITY EXECUTIVE:")
                    logger.info(f"    Name: {exec.name}")
                    logger.info(f"    Title: {exec.title}")
                    logger.info(f"    Email: {exec.email or 'Not found'}")
                    logger.info(f"    Phone: {exec.phone or 'Not found'}")
                    logger.info(f"    Quality Score: {exec_data['quality_score']:.2f}")
                
                quality_executives += len(high_quality_executives)
                
                results['results'].append(company_result)
                
                logger.info(f"  ✅ High-quality discovery: {len(high_quality_executives)} quality executives")
                
            except Exception as e:
                logger.error(f"  ❌ Discovery failed: {e}")
                
                company_result = {
                    'company_name': company['company'],
                    'test_url': company['url'],
                    'error': str(e),
                    'executives': []
                }
                
                results['results'].append(company_result)
        
        # Quality analysis
        results['quality_analysis'] = {
            'total_companies_tested': len(test_companies),
            'high_quality_executives_found': quality_executives,
            'average_quality_per_company': round(quality_executives / len(test_companies), 2),
            'total_contacts_found': total_contacts,
            'contact_rate_on_quality_executives': f"{(total_contacts / max(quality_executives, 1) * 100):.1f}%",
            'overall_assessment': self._assess_overall_quality(results['results'])
        }
        
        # Save results
        timestamp = int(time.time())
        filename = f"high_quality_executive_discovery_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        self._print_quality_summary(results)
        
        logger.info(f"\n✅ High-quality test complete! Results saved to: {filename}")
        
        return results
    
    def _filter_high_quality_executives(self, executives):
        """Filter executives to only include high-quality entries"""
        
        high_quality = []
        
        for exec in executives:
            quality_score = self._calculate_executive_quality(exec)
            
            # Only include executives with quality score >= 0.7
            if quality_score >= 0.7:
                high_quality.append(exec)
        
        return high_quality
    
    def _calculate_executive_quality(self, exec):
        """Calculate quality score for an executive based on name and contact validity"""
        
        quality_score = 0.0
        
        # Name quality (40% of score)
        name_quality = self._assess_name_quality(exec.name)
        quality_score += name_quality * 0.4
        
        # Contact completeness (30% of score)
        contact_count = sum(1 for contact in [exec.email, exec.phone, exec.linkedin_url] if contact)
        contact_score = contact_count / 3.0
        quality_score += contact_score * 0.3
        
        # Title relevance (20% of score) 
        title_quality = self._assess_title_quality(exec.title)
        quality_score += title_quality * 0.2
        
        # Confidence score (10% of score)
        quality_score += exec.confidence_score * 0.1
        
        return min(quality_score, 1.0)
    
    def _assess_name_quality(self, name):
        """Assess the quality of an executive name"""
        
        if not name:
            return 0.0
        
        # Check for obvious non-person names
        invalid_indicators = [
            'plumbing', 'heating', 'services', 'emergency', 'free', 'estimate',
            'learn', 'more', 'contact', 'call', 'home', 'about', 'facebook',
            'instagram', 'water', 'heater', 'drainage', 'boiler', 'gallery',
            'verified', 'reviews', 'ideal', 'customers', 'choose', 'why'
        ]
        
        name_lower = name.lower()
        for indicator in invalid_indicators:
            if indicator in name_lower:
                return 0.0  # Clearly not a person name
        
        # Check for person-like name structure
        name_parts = name.split()
        
        if len(name_parts) == 2:
            # Two words - likely first/last name
            first, last = name_parts
            if (first.isalpha() and last.isalpha() and 
                len(first) >= 2 and len(last) >= 2 and
                first[0].isupper() and last[0].isupper()):
                return 1.0  # High quality name
        
        # Check for business owner patterns (e.g., "Matt" from domain)
        if len(name) >= 3 and name.isalpha() and name[0].isupper():
            return 0.8  # Potentially owner/founder name
        
        return 0.3  # Low quality but possible
    
    def _assess_title_quality(self, title):
        """Assess the quality of an executive title"""
        
        if not title or title == "Unknown":
            return 0.5
        
        executive_titles = [
            'ceo', 'managing director', 'director', 'manager', 'owner', 
            'founder', 'partner', 'principal', 'president', 'vice president'
        ]
        
        title_lower = title.lower()
        for exec_title in executive_titles:
            if exec_title in title_lower:
                return 1.0
        
        return 0.6
    
    def _assess_overall_quality(self, results):
        """Assess overall quality of discovery results"""
        
        total_quality_executives = sum(r.get('high_quality_executives', 0) for r in results)
        total_companies = len(results)
        
        if total_quality_executives == 0:
            return "POOR - No high-quality executives found"
        
        avg_quality_per_company = total_quality_executives / total_companies
        
        if avg_quality_per_company >= 2.0:
            return f"EXCELLENT - {avg_quality_per_company:.1f} quality executives per company"
        elif avg_quality_per_company >= 1.0:
            return f"GOOD - {avg_quality_per_company:.1f} quality executives per company"
        elif avg_quality_per_company >= 0.5:
            return f"MODERATE - {avg_quality_per_company:.1f} quality executives per company"
        else:
            return f"POOR - Only {avg_quality_per_company:.1f} quality executives per company"
    
    def _print_quality_summary(self, results):
        """Print comprehensive quality summary"""
        
        analysis = results['quality_analysis']
        
        print("\n" + "="*80)
        print("🎯 HIGH-QUALITY EXECUTIVE DISCOVERY SUMMARY")
        print("="*80)
        
        print(f"📊 QUALITY PERFORMANCE:")
        print(f"   • Companies Tested: {analysis['total_companies_tested']}")
        print(f"   • High-Quality Executives: {analysis['high_quality_executives_found']}")
        print(f"   • Average Quality per Company: {analysis['average_quality_per_company']}")
        
        print(f"\n📧 CONTACT QUALITY:")
        print(f"   • Total Contacts Found: {analysis['total_contacts_found']}")
        print(f"   • Contact Rate (Quality Executives): {analysis['contact_rate_on_quality_executives']}")
        
        print(f"\n✅ OVERALL ASSESSMENT:")
        print(f"   • Quality Rating: {analysis['overall_assessment']}")
        
        print(f"\n📈 COMPANY-BY-COMPANY QUALITY:")
        for i, result in enumerate(results['results'], 1):
            quality_execs = result.get('high_quality_executives', 0)
            total_execs = result.get('total_executives_found', 0)
            status = "✅" if quality_execs > 0 else "❌"
            
            print(f"   {i}. {status} {result['company_name']}: {quality_execs}/{total_execs} quality executives")
            
            # Show top executive if available
            if result.get('executives'):
                top_exec = result['executives'][0]
                print(f"      → Top: {top_exec['name']} ({top_exec['title']}) - Quality: {top_exec['quality_score']:.2f}")
        
        print("="*80)

async def main():
    """Run the high-quality executive discovery test"""
    
    logger.info("Initializing High-Quality Executive Discovery Test")
    
    tester = HighQualityExecutiveDiscoveryTester()
    
    try:
        results = await tester.test_high_quality_executive_discovery()
        
        # Evaluate success
        quality_execs = results['quality_analysis']['high_quality_executives_found']
        
        if quality_execs > 0:
            logger.info("🎉 SUCCESS: High-quality executive discovery is working!")
            logger.info(f"Found {quality_execs} high-quality executives")
        else:
            logger.warning("⚠️  Challenge: No high-quality executives found - need further refinement")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main()) 