#!/usr/bin/env python3
"""
Robust Executive Extraction Overhaul Test
Testing the comprehensive executive extraction system with 8 URLs using the existing robust pipeline
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from seo_leads.fetchers.website_fetcher import WebsiteFetcher
    from seo_leads.processors.company_processor import CompanyProcessor
    from seo_leads.processors.robust_executive_pipeline import RobustExecutivePipeline
except ImportError as e:
    print(f"Import error: {e}")
    print("Attempting to import basic components...")
    try:
        from seo_leads.processors.enhanced_executive_discovery import EnhancedExecutiveDiscovery
        from seo_leads.fetchers.base_fetcher import BaseFetcher
        print("Using fallback components...")
    except ImportError:
        print("Unable to import required components. Please check the installation.")
        sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobustExecutiveExtractionTest:
    """Comprehensive test of the robust executive extraction overhaul"""
    
    def __init__(self):
        try:
            self.fetcher = WebsiteFetcher()
            self.processor = CompanyProcessor()
            self.robust_pipeline = RobustExecutivePipeline()
            self.use_robust_pipeline = True
        except:
            # Fallback to available components
            self.fetcher = BaseFetcher()
            self.processor = EnhancedExecutiveDiscovery()
            self.use_robust_pipeline = False
            logger.warning("Using fallback components instead of robust pipeline")
        
        # Test URLs provided by user
        self.test_urls = [
            "http://www.mjmplumbingservices.uk/",
            "http://rnplumbingandheating.co.uk/",
            "http://www.andrewrileyheating.co.uk/",
            "http://www.boldmereplumbingservices.co.uk/",
            "http://jmplumbingheating.co.uk/",
            "https://www.nunnplumbingandgas.co.uk/contact",
            "https://konigashomeservices.co.uk/",
            "http://www.ttsafegas.com/"
        ]
        
        self.results = []
        self.analytics = {
            'total_urls': len(self.test_urls),
            'successful_extractions': 0,
            'failed_extractions': 0,
            'total_executives_found': 0,
            'executives_with_emails': 0,
            'executives_with_phones': 0,
            'executives_with_linkedin': 0,
            'executives_with_meaningful_titles': 0,
            'high_quality_executives': 0,
            'processing_time': 0
        }
    
    async def run_comprehensive_test(self):
        """Run the comprehensive robust executive extraction test"""
        logger.info("🚀 Starting Robust Executive Extraction Overhaul Test")
        logger.info(f"📋 Testing {len(self.test_urls)} URLs")
        
        pipeline_type = "robust pipeline" if self.use_robust_pipeline else "fallback components"
        logger.info(f"🔧 Using: {pipeline_type}")
        
        start_time = time.time()
        
        for i, url in enumerate(self.test_urls, 1):
            logger.info(f"\n📍 Processing URL {i}/{len(self.test_urls)}: {url}")
            
            try:
                # Fetch website content
                logger.info("🌐 Fetching website content...")
                website_data = await self._fetch_website_data(url)
                
                if not website_data or not website_data.get('content'):
                    logger.warning(f"❌ Failed to fetch content for {url}")
                    self.analytics['failed_extractions'] += 1
                    continue
                
                # Extract executives
                logger.info("🎯 Extracting executives...")
                executives = await self._extract_executives(url, website_data)
                
                # Analyze results
                result = self._analyze_extraction_result(url, executives, website_data)
                self.results.append(result)
                
                # Update analytics
                self._update_analytics(result)
                
                logger.info(f"✅ Found {len(executives)} executives for {url}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {url}: {str(e)}")
                self.analytics['failed_extractions'] += 1
                continue
        
        # Calculate final analytics
        self.analytics['processing_time'] = time.time() - start_time
        self.analytics['success_rate'] = (self.analytics['successful_extractions'] / self.analytics['total_urls']) * 100
        
        # Generate comprehensive report
        await self._generate_comprehensive_report()
        
        logger.info("🎉 Robust Executive Extraction Overhaul Test Complete!")
        return self.results
    
    async def _fetch_website_data(self, url: str) -> Dict:
        """Fetch website data using available fetcher"""
        try:
            if hasattr(self.fetcher, 'fetch_website_data'):
                return await self.fetcher.fetch_website_data(url)
            else:
                # Basic fetch implementation
                import requests
                from bs4 import BeautifulSoup
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                return {
                    'url': url,
                    'content': soup.get_text(),
                    'html': response.text,
                    'title': soup.title.string if soup.title else '',
                    'status_code': response.status_code
                }
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    async def _extract_executives(self, url: str, website_data: Dict) -> List[Dict]:
        """Extract executives using available pipeline"""
        try:
            if self.use_robust_pipeline:
                # Use robust pipeline
                company_data = await self.processor.process_company(url, website_data)
                executive_profiles = self.robust_pipeline.extract_executives(
                    content=website_data['content'],
                    company_info=company_data
                )
                
                # Convert profiles to dict format
                executives = []
                for profile in executive_profiles:
                    if hasattr(profile, '__dict__'):
                        exec_dict = {
                            'name': profile.name,
                            'title': profile.title,
                            'email': profile.email or '',
                            'phone': profile.phone or '',
                            'linkedin_url': profile.linkedin_url or '',
                            'overall_confidence': profile.overall_confidence,
                            'name_confidence': profile.name_confidence,
                            'title_confidence': profile.title_confidence,
                            'email_confidence': profile.email_confidence,
                            'phone_confidence': profile.phone_confidence,
                            'linkedin_confidence': profile.linkedin_confidence
                        }
                    else:
                        exec_dict = profile
                    executives.append(exec_dict)
                
                return executives
            else:
                # Use fallback method
                return await self._fallback_executive_extraction(url, website_data)
                
        except Exception as e:
            logger.error(f"Error extracting executives from {url}: {str(e)}")
            return []
    
    async def _fallback_executive_extraction(self, url: str, website_data: Dict) -> List[Dict]:
        """Fallback executive extraction method"""
        try:
            # Basic name extraction
            import re
            content = website_data.get('content', '')
            
            # Simple name pattern
            name_pattern = r'\b([A-Z][a-z]{2,15})\s+([A-Z][a-z]{2,20})\b'
            matches = re.findall(name_pattern, content)
            
            executives = []
            for first_name, last_name in matches[:5]:  # Limit to 5
                name = f"{first_name} {last_name}"
                
                # Skip obvious non-names
                if any(term in name.lower() for term in ['plumbing', 'heating', 'service', 'emergency', 'commercial']):
                    continue
                
                executives.append({
                    'name': name,
                    'title': 'Unknown',
                    'email': '',
                    'phone': '',
                    'linkedin_url': '',
                    'overall_confidence': 0.5,
                    'name_confidence': 0.5,
                    'title_confidence': 0.0,
                    'email_confidence': 0.0,
                    'phone_confidence': 0.0,
                    'linkedin_confidence': 0.0
                })
            
            return executives
            
        except Exception as e:
            logger.error(f"Fallback extraction failed: {str(e)}")
            return []
    
    def _analyze_extraction_result(self, url: str, executives: List[Dict], website_data: Dict) -> Dict[str, Any]:
        """Analyze the extraction result for a single URL"""
        
        result = {
            'url': url,
            'company_name': self._extract_company_name(website_data),
            'extraction_timestamp': datetime.now().isoformat(),
            'executives_found': len(executives),
            'executives': executives,
            'quality_metrics': {
                'total_executives': len(executives),
                'executives_with_emails': 0,
                'executives_with_phones': 0,
                'executives_with_linkedin': 0,
                'executives_with_meaningful_titles': 0,
                'high_quality_executives': 0,
                'average_quality_score': 0.0
            }
        }
        
        total_quality_score = 0.0
        
        for executive in executives:
            # Update quality metrics
            if executive.get('email'):
                result['quality_metrics']['executives_with_emails'] += 1
            if executive.get('phone'):
                result['quality_metrics']['executives_with_phones'] += 1
            if executive.get('linkedin_url'):
                result['quality_metrics']['executives_with_linkedin'] += 1
            if executive.get('title') and executive.get('title') not in ['Unknown', '']:
                result['quality_metrics']['executives_with_meaningful_titles'] += 1
            if executive.get('overall_confidence', 0) >= 0.7:
                result['quality_metrics']['high_quality_executives'] += 1
            
            total_quality_score += executive.get('overall_confidence', 0)
        
        # Calculate average quality score
        if executives:
            result['quality_metrics']['average_quality_score'] = total_quality_score / len(executives)
        
        return result
    
    def _extract_company_name(self, website_data: Dict) -> str:
        """Extract company name from website data"""
        title = website_data.get('title', '')
        if title:
            return title.split(' - ')[0].split(' | ')[0]
        return 'Unknown'
    
    def _update_analytics(self, result: Dict[str, Any]):
        """Update overall analytics with result data"""
        self.analytics['successful_extractions'] += 1
        self.analytics['total_executives_found'] += result['quality_metrics']['total_executives']
        self.analytics['executives_with_emails'] += result['quality_metrics']['executives_with_emails']
        self.analytics['executives_with_phones'] += result['quality_metrics']['executives_with_phones']
        self.analytics['executives_with_linkedin'] += result['quality_metrics']['executives_with_linkedin']
        self.analytics['executives_with_meaningful_titles'] += result['quality_metrics']['executives_with_meaningful_titles']
        self.analytics['high_quality_executives'] += result['quality_metrics']['high_quality_executives']
    
    async def _generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        
        # Calculate percentages
        total_executives = self.analytics['total_executives_found']
        email_rate = (self.analytics['executives_with_emails'] / total_executives * 100) if total_executives > 0 else 0
        phone_rate = (self.analytics['executives_with_phones'] / total_executives * 100) if total_executives > 0 else 0
        linkedin_rate = (self.analytics['executives_with_linkedin'] / total_executives * 100) if total_executives > 0 else 0
        title_rate = (self.analytics['executives_with_meaningful_titles'] / total_executives * 100) if total_executives > 0 else 0
        quality_rate = (self.analytics['high_quality_executives'] / total_executives * 100) if total_executives > 0 else 0
        
        report = {
            'test_summary': {
                'test_name': 'Robust Executive Extraction Overhaul Test',
                'test_timestamp': datetime.now().isoformat(),
                'pipeline_used': 'robust_pipeline' if self.use_robust_pipeline else 'fallback',
                'total_urls_tested': self.analytics['total_urls'],
                'successful_extractions': self.analytics['successful_extractions'],
                'failed_extractions': self.analytics['failed_extractions'],
                'success_rate': f"{self.analytics['success_rate']:.1f}%",
                'total_processing_time': f"{self.analytics['processing_time']:.2f} seconds"
            },
            'executive_discovery_metrics': {
                'total_executives_found': total_executives,
                'average_executives_per_url': f"{total_executives / max(1, self.analytics['successful_extractions']):.1f}",
                'email_discovery_rate': f"{email_rate:.1f}%",
                'phone_discovery_rate': f"{phone_rate:.1f}%",
                'linkedin_discovery_rate': f"{linkedin_rate:.1f}%",
                'meaningful_title_rate': f"{title_rate:.1f}%",
                'high_quality_executive_rate': f"{quality_rate:.1f}%"
            },
            'detailed_results': self.results,
            'system_performance': {
                'average_processing_time_per_url': f"{self.analytics['processing_time'] / max(1, self.analytics['total_urls']):.2f} seconds",
                'extraction_efficiency': f"{total_executives / max(1, self.analytics['processing_time']):.1f} executives/second"
            }
        }
        
        # Save results to file
        timestamp = int(time.time())
        filename = f"robust_executive_extraction_overhaul_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Comprehensive report saved to: {filename}")
        
        # Print summary to console
        print("\n" + "="*80)
        print("🎯 ROBUST EXECUTIVE EXTRACTION OVERHAUL TEST RESULTS")
        print("="*80)
        print(f"🔧 Pipeline Used: {'Robust Pipeline' if self.use_robust_pipeline else 'Fallback Components'}")
        print(f"📋 URLs Tested: {self.analytics['total_urls']}")
        print(f"✅ Success Rate: {self.analytics['success_rate']:.1f}%")
        print(f"👥 Total Executives Found: {total_executives}")
        print(f"📧 Email Discovery Rate: {email_rate:.1f}%")
        print(f"📞 Phone Discovery Rate: {phone_rate:.1f}%")
        print(f"🔗 LinkedIn Discovery Rate: {linkedin_rate:.1f}%")
        print(f"🏷️ Meaningful Title Rate: {title_rate:.1f}%")
        print(f"⭐ High Quality Executive Rate: {quality_rate:.1f}%")
        print(f"⏱️ Total Processing Time: {self.analytics['processing_time']:.2f} seconds")
        print("="*80)
        
        return report

async def main():
    """Run the robust executive extraction overhaul test"""
    test = RobustExecutiveExtractionTest()
    
    try:
        results = await test.run_comprehensive_test()
        print(f"\n🎉 Test completed successfully!")
        print(f"🎯 Found {test.analytics['total_executives_found']} executives across {test.analytics['successful_extractions']} URLs")
        return results
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 