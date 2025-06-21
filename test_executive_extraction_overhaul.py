#!/usr/bin/env python3
"""
Executive Extraction Overhaul Test
Testing the comprehensive executive extraction system with 8 URLs
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

from seo_leads.fetchers.website_fetcher import WebsiteFetcher
from seo_leads.processors.company_processor import CompanyProcessor
from seo_leads.ai.semantic_name_extractor import SemanticNameExtractor
from seo_leads.extractors.advanced_contact_attributor import AdvancedContactAttributor
from seo_leads.scrapers.real_linkedin_discoverer import RealLinkedInDiscoverer
from seo_leads.processors.executive_title_extractor import ExecutiveTitleExtractor
from seo_leads.processors.robust_executive_pipeline import RobustExecutivePipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExecutiveExtractionOverhaulTest:
    """Comprehensive test of the executive extraction overhaul"""
    
    def __init__(self):
        self.fetcher = WebsiteFetcher()
        self.processor = CompanyProcessor()
        self.robust_pipeline = RobustExecutivePipeline()
        
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
            'executives_with_titles': 0,
            'high_quality_executives': 0,
            'processing_time': 0
        }
    
    async def run_comprehensive_test(self):
        """Run the comprehensive executive extraction test"""
        logger.info("🚀 Starting Executive Extraction Overhaul Test")
        logger.info(f"📋 Testing {len(self.test_urls)} URLs with new robust pipeline")
        
        start_time = time.time()
        
        for i, url in enumerate(self.test_urls, 1):
            logger.info(f"\n📍 Processing URL {i}/{len(self.test_urls)}: {url}")
            
            try:
                # Fetch website content
                logger.info("🌐 Fetching website content...")
                website_data = await self.fetcher.fetch_website_data(url)
                
                if not website_data or not website_data.get('content'):
                    logger.warning(f"❌ Failed to fetch content for {url}")
                    self.analytics['failed_extractions'] += 1
                    continue
                
                # Process with robust executive pipeline
                logger.info("🔍 Processing with robust executive pipeline...")
                company_data = await self.processor.process_company(url, website_data)
                
                if not company_data:
                    logger.warning(f"❌ Failed to process company data for {url}")
                    self.analytics['failed_extractions'] += 1
                    continue
                
                # Extract executives using the new robust pipeline
                executives = await self.robust_pipeline.extract_executives(
                    url=url,
                    content=website_data['content'],
                    company_data=company_data
                )
                
                # Analyze results
                result = self._analyze_extraction_result(url, executives, company_data)
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
        
        logger.info("🎉 Executive Extraction Overhaul Test Complete!")
        return self.results
    
    def _analyze_extraction_result(self, url: str, executives: List, company_data: Dict) -> Dict[str, Any]:
        """Analyze the extraction result for a single URL"""
        
        result = {
            'url': url,
            'company_name': company_data.get('name', 'Unknown'),
            'domain': company_data.get('domain', ''),
            'extraction_timestamp': datetime.now().isoformat(),
            'executives_found': len(executives),
            'executives': [],
            'quality_metrics': {
                'total_executives': len(executives),
                'executives_with_emails': 0,
                'executives_with_phones': 0,
                'executives_with_linkedin': 0,
                'executives_with_titles': 0,
                'high_quality_executives': 0,
                'average_quality_score': 0.0
            }
        }
        
        total_quality_score = 0.0
        
        for executive in executives:
            exec_data = {
                'name': executive.get('name', 'Unknown'),
                'title': executive.get('title', 'Unknown'),
                'email': executive.get('email', ''),
                'phone': executive.get('phone', ''),
                'linkedin_url': executive.get('linkedin_url', ''),
                'quality_score': executive.get('quality_score', 0.0),
                'discovery_source': executive.get('discovery_source', 'unknown'),
                'attribution_confidence': executive.get('attribution_confidence', 0.0)
            }
            
            result['executives'].append(exec_data)
            
            # Update quality metrics
            if exec_data['email']:
                result['quality_metrics']['executives_with_emails'] += 1
            if exec_data['phone']:
                result['quality_metrics']['executives_with_phones'] += 1
            if exec_data['linkedin_url']:
                result['quality_metrics']['executives_with_linkedin'] += 1
            if exec_data['title'] and exec_data['title'] != 'Unknown':
                result['quality_metrics']['executives_with_titles'] += 1
            if exec_data['quality_score'] >= 0.7:
                result['quality_metrics']['high_quality_executives'] += 1
            
            total_quality_score += exec_data['quality_score']
        
        # Calculate average quality score
        if executives:
            result['quality_metrics']['average_quality_score'] = total_quality_score / len(executives)
        
        return result
    
    def _update_analytics(self, result: Dict[str, Any]):
        """Update overall analytics with result data"""
        self.analytics['successful_extractions'] += 1
        self.analytics['total_executives_found'] += result['quality_metrics']['total_executives']
        self.analytics['executives_with_emails'] += result['quality_metrics']['executives_with_emails']
        self.analytics['executives_with_phones'] += result['quality_metrics']['executives_with_phones']
        self.analytics['executives_with_linkedin'] += result['quality_metrics']['executives_with_linkedin']
        self.analytics['executives_with_titles'] += result['quality_metrics']['executives_with_titles']
        self.analytics['high_quality_executives'] += result['quality_metrics']['high_quality_executives']
    
    async def _generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        
        # Calculate percentages
        total_executives = self.analytics['total_executives_found']
        email_rate = (self.analytics['executives_with_emails'] / total_executives * 100) if total_executives > 0 else 0
        phone_rate = (self.analytics['executives_with_phones'] / total_executives * 100) if total_executives > 0 else 0
        linkedin_rate = (self.analytics['executives_with_linkedin'] / total_executives * 100) if total_executives > 0 else 0
        title_rate = (self.analytics['executives_with_titles'] / total_executives * 100) if total_executives > 0 else 0
        quality_rate = (self.analytics['high_quality_executives'] / total_executives * 100) if total_executives > 0 else 0
        
        report = {
            'test_summary': {
                'test_name': 'Executive Extraction Overhaul Test',
                'test_timestamp': datetime.now().isoformat(),
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
                'title_extraction_rate': f"{title_rate:.1f}%",
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
        filename = f"executive_extraction_overhaul_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Comprehensive report saved to: {filename}")
        
        # Print summary to console
        print("\n" + "="*80)
        print("🎯 EXECUTIVE EXTRACTION OVERHAUL TEST RESULTS")
        print("="*80)
        print(f"📋 URLs Tested: {self.analytics['total_urls']}")
        print(f"✅ Success Rate: {self.analytics['success_rate']:.1f}%")
        print(f"👥 Total Executives Found: {total_executives}")
        print(f"📧 Email Discovery Rate: {email_rate:.1f}%")
        print(f"📞 Phone Discovery Rate: {phone_rate:.1f}%")
        print(f"🔗 LinkedIn Discovery Rate: {linkedin_rate:.1f}%")
        print(f"🏷️ Title Extraction Rate: {title_rate:.1f}%")
        print(f"⭐ High Quality Executive Rate: {quality_rate:.1f}%")
        print(f"⏱️ Total Processing Time: {self.analytics['processing_time']:.2f} seconds")
        print("="*80)
        
        return report

async def main():
    """Run the executive extraction overhaul test"""
    test = ExecutiveExtractionOverhaulTest()
    
    try:
        results = await test.run_comprehensive_test()
        print(f"\n🎉 Test completed successfully! Found {test.analytics['total_executives_found']} executives across {test.analytics['successful_extractions']} URLs.")
        return results
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 