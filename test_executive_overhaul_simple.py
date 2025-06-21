#!/usr/bin/env python3
"""
Simple Executive Extraction Overhaul Test
Testing the executive extraction system with 8 URLs using available components
"""

import asyncio
import json
import logging
import time
import requests
from datetime import datetime
from typing import List, Dict, Any
import sys
import os
from bs4 import BeautifulSoup
import re

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from seo_leads.processors.robust_executive_pipeline import RobustExecutivePipeline
    from seo_leads.ai.semantic_name_extractor import SemanticNameExtractor
    from seo_leads.extractors.advanced_contact_attributor import AdvancedContactAttributor
    robust_available = True
    print("✅ Robust pipeline components available")
except ImportError as e:
    print(f"⚠️ Robust pipeline not available: {e}")
    robust_available = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleExecutiveExtractionTest:
    """Simple test of executive extraction capabilities"""
    
    def __init__(self):
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
        
        # Initialize components if available
        if robust_available:
            try:
                self.robust_pipeline = RobustExecutivePipeline()
                self.semantic_extractor = SemanticNameExtractor()
                self.contact_attributor = AdvancedContactAttributor()
                self.use_robust = True
                print("✅ Using robust pipeline components")
            except Exception as e:
                print(f"⚠️ Error initializing robust components: {e}")
                self.use_robust = False
        else:
            self.use_robust = False
        
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
    
    async def run_test(self):
        """Run the executive extraction test"""
        logger.info("🚀 Starting Executive Extraction Overhaul Test")
        logger.info(f"📋 Testing {len(self.test_urls)} URLs")
        logger.info(f"🔧 Using: {'Robust Pipeline' if self.use_robust else 'Basic Extraction'}")
        
        start_time = time.time()
        
        for i, url in enumerate(self.test_urls, 1):
            logger.info(f"\n📍 Processing URL {i}/{len(self.test_urls)}: {url}")
            
            try:
                # Fetch website content
                logger.info("🌐 Fetching website content...")
                website_data = await self._fetch_website_data(url)
                
                if not website_data:
                    logger.warning(f"❌ Failed to fetch content for {url}")
                    self.analytics['failed_extractions'] += 1
                    continue
                
                # Extract executives
                logger.info("🎯 Extracting executives...")
                executives = await self._extract_executives(website_data)
                
                # Analyze results
                result = self._analyze_result(url, executives, website_data)
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
        
        # Generate report
        await self._generate_report()
        
        logger.info("🎉 Executive Extraction Test Complete!")
        return self.results
    
    async def _fetch_website_data(self, url: str) -> Dict:
        """Fetch website data"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, timeout=15, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
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
    
    async def _extract_executives(self, website_data: Dict) -> List[Dict]:
        """Extract executives using available methods"""
        if self.use_robust:
            return await self._robust_extraction(website_data)
        else:
            return await self._basic_extraction(website_data)
    
    async def _robust_extraction(self, website_data: Dict) -> List[Dict]:
        """Use robust pipeline for extraction"""
        try:
            content = website_data.get('content', '')
            
            # Create basic company info
            company_info = {
                'name': self._extract_company_name(website_data),
                'domain': website_data.get('url', '').replace('http://', '').replace('https://', '').split('/')[0],
                'url': website_data.get('url', '')
            }
            
            # Use robust pipeline
            executive_profiles = self.robust_pipeline.extract_executives(
                content=content,
                company_info=company_info
            )
            
            # Convert to dict format
            executives = []
            for profile in executive_profiles:
                if hasattr(profile, '__dict__'):
                    exec_dict = {
                        'name': profile.name,
                        'title': profile.title or 'Unknown',
                        'email': profile.email or '',
                        'phone': profile.phone or '',
                        'linkedin_url': profile.linkedin_url or '',
                        'overall_confidence': profile.overall_confidence,
                        'extraction_method': 'robust_pipeline'
                    }
                else:
                    exec_dict = profile
                    exec_dict['extraction_method'] = 'robust_pipeline'
                executives.append(exec_dict)
            
            return executives
            
        except Exception as e:
            logger.error(f"Robust extraction failed: {str(e)}")
            return await self._basic_extraction(website_data)
    
    async def _basic_extraction(self, website_data: Dict) -> List[Dict]:
        """Basic executive extraction"""
        try:
            content = website_data.get('content', '')
            
            # Improved name pattern
            name_pattern = r'\b([A-Z][a-z]{2,15})\s+([A-Z][a-z]{2,20})\b'
            matches = re.findall(name_pattern, content)
            
            # Email pattern
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, content)
            
            # Phone pattern (UK)
            phone_pattern = r'(\+44\s?[0-9\s]{10,}|0[0-9\s]{10,})'
            phones = re.findall(phone_pattern, content)
            
            executives = []
            service_terms = {'plumbing', 'heating', 'service', 'emergency', 'commercial', 'residential', 'repair', 'installation'}
            
            seen_names = set()
            for first_name, last_name in matches[:10]:  # Limit to 10
                name = f"{first_name} {last_name}"
                
                # Skip obvious non-names and duplicates
                if (any(term in name.lower() for term in service_terms) or 
                    name.lower() in seen_names):
                    continue
                
                seen_names.add(name.lower())
                
                # Simple email attribution (if email contains name parts)
                attributed_email = ''
                for email in emails:
                    if (first_name.lower() in email.lower() or 
                        last_name.lower() in email.lower()):
                        attributed_email = email
                        break
                
                executives.append({
                    'name': name,
                    'title': 'Unknown',
                    'email': attributed_email,
                    'phone': phones[0] if phones else '',
                    'linkedin_url': '',
                    'overall_confidence': 0.6 if attributed_email else 0.4,
                    'extraction_method': 'basic_pattern'
                })
            
            return executives
            
        except Exception as e:
            logger.error(f"Basic extraction failed: {str(e)}")
            return []
    
    def _extract_company_name(self, website_data: Dict) -> str:
        """Extract company name from website data"""
        title = website_data.get('title', '')
        if title:
            # Clean up title
            name = title.split(' - ')[0].split(' | ')[0]
            return name.strip()
        return 'Unknown'
    
    def _analyze_result(self, url: str, executives: List[Dict], website_data: Dict) -> Dict[str, Any]:
        """Analyze extraction result"""
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
                'average_confidence': 0.0
            }
        }
        
        total_confidence = 0.0
        
        for executive in executives:
            if executive.get('email'):
                result['quality_metrics']['executives_with_emails'] += 1
            if executive.get('phone'):
                result['quality_metrics']['executives_with_phones'] += 1
            if executive.get('linkedin_url'):
                result['quality_metrics']['executives_with_linkedin'] += 1
            if executive.get('title') and executive.get('title') != 'Unknown':
                result['quality_metrics']['executives_with_meaningful_titles'] += 1
            if executive.get('overall_confidence', 0) >= 0.7:
                result['quality_metrics']['high_quality_executives'] += 1
            
            total_confidence += executive.get('overall_confidence', 0)
        
        if executives:
            result['quality_metrics']['average_confidence'] = total_confidence / len(executives)
        
        return result
    
    def _update_analytics(self, result: Dict[str, Any]):
        """Update analytics"""
        self.analytics['successful_extractions'] += 1
        self.analytics['total_executives_found'] += result['quality_metrics']['total_executives']
        self.analytics['executives_with_emails'] += result['quality_metrics']['executives_with_emails']
        self.analytics['executives_with_phones'] += result['quality_metrics']['executives_with_phones']
        self.analytics['executives_with_linkedin'] += result['quality_metrics']['executives_with_linkedin']
        self.analytics['executives_with_meaningful_titles'] += result['quality_metrics']['executives_with_meaningful_titles']
        self.analytics['high_quality_executives'] += result['quality_metrics']['high_quality_executives']
    
    async def _generate_report(self):
        """Generate comprehensive report"""
        total_executives = self.analytics['total_executives_found']
        email_rate = (self.analytics['executives_with_emails'] / total_executives * 100) if total_executives > 0 else 0
        phone_rate = (self.analytics['executives_with_phones'] / total_executives * 100) if total_executives > 0 else 0
        linkedin_rate = (self.analytics['executives_with_linkedin'] / total_executives * 100) if total_executives > 0 else 0
        title_rate = (self.analytics['executives_with_meaningful_titles'] / total_executives * 100) if total_executives > 0 else 0
        quality_rate = (self.analytics['high_quality_executives'] / total_executives * 100) if total_executives > 0 else 0
        
        report = {
            'test_summary': {
                'test_name': 'Executive Extraction Overhaul Test',
                'test_timestamp': datetime.now().isoformat(),
                'pipeline_used': 'robust_pipeline' if self.use_robust else 'basic_extraction',
                'total_urls_tested': self.analytics['total_urls'],
                'successful_extractions': self.analytics['successful_extractions'],
                'failed_extractions': self.analytics['failed_extractions'],
                'success_rate': f"{self.analytics['success_rate']:.1f}%",
                'total_processing_time': f"{self.analytics['processing_time']:.2f} seconds"
            },
            'metrics': {
                'total_executives_found': total_executives,
                'average_per_url': f"{total_executives / max(1, self.analytics['successful_extractions']):.1f}",
                'email_discovery_rate': f"{email_rate:.1f}%",
                'phone_discovery_rate': f"{phone_rate:.1f}%",
                'linkedin_discovery_rate': f"{linkedin_rate:.1f}%",
                'meaningful_title_rate': f"{title_rate:.1f}%",
                'high_quality_rate': f"{quality_rate:.1f}%"
            },
            'detailed_results': self.results
        }
        
        # Save results
        timestamp = int(time.time())
        filename = f"executive_extraction_overhaul_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Report saved to: {filename}")
        
        # Print summary
        print("\n" + "="*80)
        print("🎯 EXECUTIVE EXTRACTION OVERHAUL TEST RESULTS")
        print("="*80)
        print(f"🔧 Pipeline: {'Robust Pipeline' if self.use_robust else 'Basic Extraction'}")
        print(f"📋 URLs Tested: {self.analytics['total_urls']}")
        print(f"✅ Success Rate: {self.analytics['success_rate']:.1f}%")
        print(f"👥 Total Executives: {total_executives}")
        print(f"📧 Email Rate: {email_rate:.1f}%")
        print(f"📞 Phone Rate: {phone_rate:.1f}%")
        print(f"🔗 LinkedIn Rate: {linkedin_rate:.1f}%")
        print(f"🏷️ Title Rate: {title_rate:.1f}%")
        print(f"⭐ Quality Rate: {quality_rate:.1f}%")
        print(f"⏱️ Processing Time: {self.analytics['processing_time']:.2f}s")
        print("="*80)
        
        return report

async def main():
    """Run the test"""
    test = SimpleExecutiveExtractionTest()
    
    try:
        results = await test.run_test()
        print(f"\n🎉 Test completed!")
        print(f"Found {test.analytics['total_executives_found']} executives across {test.analytics['successful_extractions']} URLs")
        return results
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
"""
Simple Executive Extraction Overhaul Test
Testing the executive extraction system with 8 URLs using available components
"""

import asyncio
import json
import logging
import time
import requests
from datetime import datetime
from typing import List, Dict, Any
import sys
import os
from bs4 import BeautifulSoup
import re

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from seo_leads.processors.robust_executive_pipeline import RobustExecutivePipeline
    from seo_leads.ai.semantic_name_extractor import SemanticNameExtractor
    from seo_leads.extractors.advanced_contact_attributor import AdvancedContactAttributor
    robust_available = True
    print("✅ Robust pipeline components available")
except ImportError as e:
    print(f"⚠️ Robust pipeline not available: {e}")
    robust_available = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleExecutiveExtractionTest:
    """Simple test of executive extraction capabilities"""
    
    def __init__(self):
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
        
        # Initialize components if available
        if robust_available:
            try:
                self.robust_pipeline = RobustExecutivePipeline()
                self.semantic_extractor = SemanticNameExtractor()
                self.contact_attributor = AdvancedContactAttributor()
                self.use_robust = True
                print("✅ Using robust pipeline components")
            except Exception as e:
                print(f"⚠️ Error initializing robust components: {e}")
                self.use_robust = False
        else:
            self.use_robust = False
        
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
    
    async def run_test(self):
        """Run the executive extraction test"""
        logger.info("🚀 Starting Executive Extraction Overhaul Test")
        logger.info(f"📋 Testing {len(self.test_urls)} URLs")
        logger.info(f"🔧 Using: {'Robust Pipeline' if self.use_robust else 'Basic Extraction'}")
        
        start_time = time.time()
        
        for i, url in enumerate(self.test_urls, 1):
            logger.info(f"\n📍 Processing URL {i}/{len(self.test_urls)}: {url}")
            
            try:
                # Fetch website content
                logger.info("🌐 Fetching website content...")
                website_data = await self._fetch_website_data(url)
                
                if not website_data:
                    logger.warning(f"❌ Failed to fetch content for {url}")
                    self.analytics['failed_extractions'] += 1
                    continue
                
                # Extract executives
                logger.info("🎯 Extracting executives...")
                executives = await self._extract_executives(website_data)
                
                # Analyze results
                result = self._analyze_result(url, executives, website_data)
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
        
        # Generate report
        await self._generate_report()
        
        logger.info("🎉 Executive Extraction Test Complete!")
        return self.results
    
    async def _fetch_website_data(self, url: str) -> Dict:
        """Fetch website data"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, timeout=15, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
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
    
    async def _extract_executives(self, website_data: Dict) -> List[Dict]:
        """Extract executives using available methods"""
        if self.use_robust:
            return await self._robust_extraction(website_data)
        else:
            return await self._basic_extraction(website_data)
    
    async def _robust_extraction(self, website_data: Dict) -> List[Dict]:
        """Use robust pipeline for extraction"""
        try:
            content = website_data.get('content', '')
            
            # Create basic company info
            company_info = {
                'name': self._extract_company_name(website_data),
                'domain': website_data.get('url', '').replace('http://', '').replace('https://', '').split('/')[0],
                'url': website_data.get('url', '')
            }
            
            # Use robust pipeline
            executive_profiles = self.robust_pipeline.extract_executives(
                content=content,
                company_info=company_info
            )
            
            # Convert to dict format
            executives = []
            for profile in executive_profiles:
                if hasattr(profile, '__dict__'):
                    exec_dict = {
                        'name': profile.name,
                        'title': profile.title or 'Unknown',
                        'email': profile.email or '',
                        'phone': profile.phone or '',
                        'linkedin_url': profile.linkedin_url or '',
                        'overall_confidence': profile.overall_confidence,
                        'extraction_method': 'robust_pipeline'
                    }
                else:
                    exec_dict = profile
                    exec_dict['extraction_method'] = 'robust_pipeline'
                executives.append(exec_dict)
            
            return executives
            
        except Exception as e:
            logger.error(f"Robust extraction failed: {str(e)}")
            return await self._basic_extraction(website_data)
    
    async def _basic_extraction(self, website_data: Dict) -> List[Dict]:
        """Basic executive extraction"""
        try:
            content = website_data.get('content', '')
            
            # Improved name pattern
            name_pattern = r'\b([A-Z][a-z]{2,15})\s+([A-Z][a-z]{2,20})\b'
            matches = re.findall(name_pattern, content)
            
            # Email pattern
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, content)
            
            # Phone pattern (UK)
            phone_pattern = r'(\+44\s?[0-9\s]{10,}|0[0-9\s]{10,})'
            phones = re.findall(phone_pattern, content)
            
            executives = []
            service_terms = {'plumbing', 'heating', 'service', 'emergency', 'commercial', 'residential', 'repair', 'installation'}
            
            seen_names = set()
            for first_name, last_name in matches[:10]:  # Limit to 10
                name = f"{first_name} {last_name}"
                
                # Skip obvious non-names and duplicates
                if (any(term in name.lower() for term in service_terms) or 
                    name.lower() in seen_names):
                    continue
                
                seen_names.add(name.lower())
                
                # Simple email attribution (if email contains name parts)
                attributed_email = ''
                for email in emails:
                    if (first_name.lower() in email.lower() or 
                        last_name.lower() in email.lower()):
                        attributed_email = email
                        break
                
                executives.append({
                    'name': name,
                    'title': 'Unknown',
                    'email': attributed_email,
                    'phone': phones[0] if phones else '',
                    'linkedin_url': '',
                    'overall_confidence': 0.6 if attributed_email else 0.4,
                    'extraction_method': 'basic_pattern'
                })
            
            return executives
            
        except Exception as e:
            logger.error(f"Basic extraction failed: {str(e)}")
            return []
    
    def _extract_company_name(self, website_data: Dict) -> str:
        """Extract company name from website data"""
        title = website_data.get('title', '')
        if title:
            # Clean up title
            name = title.split(' - ')[0].split(' | ')[0]
            return name.strip()
        return 'Unknown'
    
    def _analyze_result(self, url: str, executives: List[Dict], website_data: Dict) -> Dict[str, Any]:
        """Analyze extraction result"""
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
                'average_confidence': 0.0
            }
        }
        
        total_confidence = 0.0
        
        for executive in executives:
            if executive.get('email'):
                result['quality_metrics']['executives_with_emails'] += 1
            if executive.get('phone'):
                result['quality_metrics']['executives_with_phones'] += 1
            if executive.get('linkedin_url'):
                result['quality_metrics']['executives_with_linkedin'] += 1
            if executive.get('title') and executive.get('title') != 'Unknown':
                result['quality_metrics']['executives_with_meaningful_titles'] += 1
            if executive.get('overall_confidence', 0) >= 0.7:
                result['quality_metrics']['high_quality_executives'] += 1
            
            total_confidence += executive.get('overall_confidence', 0)
        
        if executives:
            result['quality_metrics']['average_confidence'] = total_confidence / len(executives)
        
        return result
    
    def _update_analytics(self, result: Dict[str, Any]):
        """Update analytics"""
        self.analytics['successful_extractions'] += 1
        self.analytics['total_executives_found'] += result['quality_metrics']['total_executives']
        self.analytics['executives_with_emails'] += result['quality_metrics']['executives_with_emails']
        self.analytics['executives_with_phones'] += result['quality_metrics']['executives_with_phones']
        self.analytics['executives_with_linkedin'] += result['quality_metrics']['executives_with_linkedin']
        self.analytics['executives_with_meaningful_titles'] += result['quality_metrics']['executives_with_meaningful_titles']
        self.analytics['high_quality_executives'] += result['quality_metrics']['high_quality_executives']
    
    async def _generate_report(self):
        """Generate comprehensive report"""
        total_executives = self.analytics['total_executives_found']
        email_rate = (self.analytics['executives_with_emails'] / total_executives * 100) if total_executives > 0 else 0
        phone_rate = (self.analytics['executives_with_phones'] / total_executives * 100) if total_executives > 0 else 0
        linkedin_rate = (self.analytics['executives_with_linkedin'] / total_executives * 100) if total_executives > 0 else 0
        title_rate = (self.analytics['executives_with_meaningful_titles'] / total_executives * 100) if total_executives > 0 else 0
        quality_rate = (self.analytics['high_quality_executives'] / total_executives * 100) if total_executives > 0 else 0
        
        report = {
            'test_summary': {
                'test_name': 'Executive Extraction Overhaul Test',
                'test_timestamp': datetime.now().isoformat(),
                'pipeline_used': 'robust_pipeline' if self.use_robust else 'basic_extraction',
                'total_urls_tested': self.analytics['total_urls'],
                'successful_extractions': self.analytics['successful_extractions'],
                'failed_extractions': self.analytics['failed_extractions'],
                'success_rate': f"{self.analytics['success_rate']:.1f}%",
                'total_processing_time': f"{self.analytics['processing_time']:.2f} seconds"
            },
            'metrics': {
                'total_executives_found': total_executives,
                'average_per_url': f"{total_executives / max(1, self.analytics['successful_extractions']):.1f}",
                'email_discovery_rate': f"{email_rate:.1f}%",
                'phone_discovery_rate': f"{phone_rate:.1f}%",
                'linkedin_discovery_rate': f"{linkedin_rate:.1f}%",
                'meaningful_title_rate': f"{title_rate:.1f}%",
                'high_quality_rate': f"{quality_rate:.1f}%"
            },
            'detailed_results': self.results
        }
        
        # Save results
        timestamp = int(time.time())
        filename = f"executive_extraction_overhaul_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Report saved to: {filename}")
        
        # Print summary
        print("\n" + "="*80)
        print("🎯 EXECUTIVE EXTRACTION OVERHAUL TEST RESULTS")
        print("="*80)
        print(f"🔧 Pipeline: {'Robust Pipeline' if self.use_robust else 'Basic Extraction'}")
        print(f"📋 URLs Tested: {self.analytics['total_urls']}")
        print(f"✅ Success Rate: {self.analytics['success_rate']:.1f}%")
        print(f"👥 Total Executives: {total_executives}")
        print(f"📧 Email Rate: {email_rate:.1f}%")
        print(f"📞 Phone Rate: {phone_rate:.1f}%")
        print(f"🔗 LinkedIn Rate: {linkedin_rate:.1f}%")
        print(f"🏷️ Title Rate: {title_rate:.1f}%")
        print(f"⭐ Quality Rate: {quality_rate:.1f}%")
        print(f"⏱️ Processing Time: {self.analytics['processing_time']:.2f}s")
        print("="*80)
        
        return report

async def main():
    """Run the test"""
    test = SimpleExecutiveExtractionTest()
    
    try:
        results = await test.run_test()
        print(f"\n🎉 Test completed!")
        print(f"Found {test.analytics['total_executives_found']} executives across {test.analytics['successful_extractions']} URLs")
        return results
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 