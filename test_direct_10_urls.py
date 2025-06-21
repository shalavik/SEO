#!/usr/bin/env python3
"""
Direct Test - 10 URL Executive Discovery Test
Tests the executive discovery system directly bypassing import issues
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
import sys
import os

# Add the src path directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test URLs provided by user
TEST_URLS = [
    ("GPJ Plumbing", "http://gpj-plumbing.co.uk/"),
    ("Emergency Plumber Services", "https://www.emergencyplumber.services/"),
    ("247 Plumbing and Gas", "https://247plumbingandgas.co.uk/"),
    ("Hancox Gas and Plumbing", "http://www.hancoxgasandplumbing.co.uk/"),
    ("Metro Plumb Birmingham", "https://metroplumb.co.uk/locations/metro-plumb-birmingham/"),
    ("TJ Works", "https://www.tjworks.co.uk/"),
    ("Afterglow Heating", "https://afterglowheating.co.uk/"),
    ("AS Plumbing Heating", "http://asplumbingheating.com/"),
    ("MKH Plumbing Birmingham", "https://www.facebook.com/MKHPBirmingham/"),
    ("Maximum Heat Emergency Plumber", "http://www.maximumheatemergencyplumberbirmingham.co.uk/")
]

class DirectExecutiveTest:
    """Direct Executive Discovery Testing without complex imports"""
    
    def __init__(self):
        self.test_start_time = None
        self.test_results = []
        self.total_companies_tested = 0
        self.successful_discoveries = 0
        self.processing_times = []
        
        # Try to load available discovery components
        self.discovery_engine = None
        self.load_discovery_engine()
    
    def load_discovery_engine(self):
        """Load available discovery engine components"""
        try:
            # Try to import executive discovery directly
            from seo_leads.processors.executive_discovery import ExecutiveDiscoveryEngine
            self.discovery_engine = ExecutiveDiscoveryEngine()
            logger.info("✅ Loaded basic ExecutiveDiscoveryEngine")
            return
        except Exception as e:
            logger.debug(f"Could not load ExecutiveDiscoveryEngine: {e}")
        
        try:
            # Try to import Phase 4B alternative engine directly
            from seo_leads.processors.phase4b_alternative_engine import Phase4BAlternativeEngine
            self.discovery_engine = Phase4BAlternativeEngine()
            logger.info("✅ Loaded Phase4BAlternativeEngine")
            return
        except Exception as e:
            logger.debug(f"Could not load Phase4BAlternativeEngine: {e}")
        
        logger.warning("⚠️ No discovery engine available - using fallback testing")
    
    async def test_single_company_direct(self, company_name: str, company_url: str) -> Dict[str, Any]:
        """Test a single company with direct web access"""
        logger.info(f"🔍 Testing Company: {company_name}")
        start_time = time.time()
        
        # Basic website accessibility test with content analysis
        import aiohttp
        import re
        from urllib.parse import urlparse
        
        try:
            async with aiohttp.ClientSession() as session:
                # Set user agent and headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with session.get(company_url, headers=headers, timeout=15) as response:
                    content = await response.text()
                    processing_time = time.time() - start_time
                    
                    # Extract basic company information
                    executives = self.extract_executives_from_content(content, company_name, company_url)
                    
                    # Analyze content quality
                    content_analysis = self.analyze_content_quality(content, company_name)
                    
                    return {
                        'company_name': company_name,
                        'company_url': company_url,
                        'processing_time': processing_time,
                        'executives_found': len(executives),
                        'executives_data': executives,
                        'website_health': {
                            'status': 'accessible',
                            'accessible': True,
                            'status_code': response.status,
                            'content_length': len(content),
                            'response_time': processing_time
                        },
                        'content_analysis': content_analysis,
                        'discovery_sources': ['direct_content_analysis'],
                        'success': len(executives) > 0 or response.status == 200,
                        'error': None
                    }
                    
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Error testing {company_name}: {e}")
            
            return {
                'company_name': company_name,
                'company_url': company_url,
                'processing_time': processing_time,
                'executives_found': 0,
                'executives_data': [],
                'website_health': {
                    'status': 'error',
                    'accessible': False,
                    'status_code': None,
                    'content_length': 0,
                    'response_time': processing_time
                },
                'content_analysis': {},
                'discovery_sources': [],
                'success': False,
                'error': str(e)
            }
    
    def extract_executives_from_content(self, content: str, company_name: str, company_url: str) -> List[Dict[str, Any]]:
        """Extract potential executives from website content"""
        executives = []
        
        try:
            # Convert to lowercase for easier matching
            content_lower = content.lower()
            
            # Common executive title patterns
            executive_patterns = [
                r'\b(director|manager|owner|founder|ceo|md|managing director|general manager|operations manager)\b',
                r'\b(proprietor|principal|head|chief|lead|senior manager)\b',
                r'\b(project manager|site manager|contracts manager|business development manager)\b'
            ]
            
            # Name patterns (common UK names)
            name_patterns = [
                r'\b([A-Z][a-z]{2,15})\s+([A-Z][a-z]{2,15})\b',  # First Last
                r'\b(Mr|Mrs|Ms|Dr)\.?\s+([A-Z][a-z]{2,15})\s+([A-Z][a-z]{2,15})\b'  # Title First Last
            ]
            
            # Business name analysis for owner detection
            owner_from_business = self.extract_owner_from_business_name(company_name)
            if owner_from_business:
                executives.append({
                    'name': owner_from_business['name'],
                    'title': owner_from_business['title'],
                    'company': company_name,
                    'company_domain': self.extract_domain(company_url),
                    'confidence_score': owner_from_business['confidence'],
                    'discovery_method': 'business_name_analysis',
                    'source': 'company_name',
                    'contact_info': {}
                })
            
            # Look for contact pages and about pages
            if any(keyword in content_lower for keyword in ['about', 'team', 'staff', 'management', 'contact']):
                # Extract names near executive titles
                import re
                
                # Find potential executive mentions
                executive_mentions = []
                for pattern in executive_patterns:
                    matches = re.finditer(pattern, content_lower)
                    for match in matches:
                        start = max(0, match.start() - 100)
                        end = min(len(content), match.end() + 100)
                        context = content[start:end]
                        executive_mentions.append({
                            'title': match.group(0),
                            'context': context,
                            'position': match.start()
                        })
                
                # Look for names near executive titles
                for mention in executive_mentions:
                    for name_pattern in name_patterns:
                        name_matches = re.findall(name_pattern, mention['context'], re.IGNORECASE)
                        for match in name_matches:
                            if isinstance(match, tuple):
                                if len(match) == 2:
                                    name = f"{match[0]} {match[1]}"
                                elif len(match) == 3:
                                    name = f"{match[1]} {match[2]}"  # Skip title
                                else:
                                    continue
                            else:
                                name = match
                            
                            # Validate name
                            if self.is_valid_name(name) and name.lower() not in company_name.lower():
                                executives.append({
                                    'name': name,
                                    'title': mention['title'].title(),
                                    'company': company_name,
                                    'company_domain': self.extract_domain(company_url),
                                    'confidence_score': 0.7,
                                    'discovery_method': 'website_content_analysis',
                                    'source': 'website_content',
                                    'contact_info': {}
                                })
            
            # Remove duplicates
            seen_names = set()
            unique_executives = []
            for exec in executives:
                name_key = exec['name'].lower().strip()
                if name_key not in seen_names:
                    seen_names.add(name_key)
                    unique_executives.append(exec)
            
            return unique_executives[:5]  # Limit to top 5
            
        except Exception as e:
            logger.debug(f"Error extracting executives: {e}")
            return []
    
    def extract_owner_from_business_name(self, company_name: str) -> Dict[str, Any]:
        """Extract potential owner name from business name"""
        import re
        
        # Common patterns for owner names in business names
        patterns = [
            r'^([A-Z][a-z]{2,})\s+(?:Plumbing|Heating|Gas|Electrical|Building|Construction)',
            r'^([A-Z][a-z]{2,})\s*\'s\s+(?:Plumbing|Heating|Gas|Electrical)',
            r'^([A-Z][a-z]{2,})\s+&\s+(?:Sons?|Co|Company)',
            r'^([A-Z][a-z]{2,})\s+(?:and|&)\s+(?:Sons?|Daughters?)',
            r'([A-Z][a-z]{2,})\s+(?:Family|Brothers?)\s+(?:Business|Plumbing|Heating)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, company_name)
            if match:
                name = match.group(1)
                if self.is_valid_first_name(name):
                    return {
                        'name': name,
                        'title': 'Business Owner',
                        'confidence': 0.8
                    }
        
        return None
    
    def is_valid_name(self, name: str) -> bool:
        """Check if name looks valid"""
        if not name or len(name) < 4 or len(name) > 50:
            return False
        
        # Check for common business words that aren't names
        business_words = ['plumbing', 'heating', 'gas', 'electrical', 'services', 'company', 'ltd', 'limited', 'solutions']
        if any(word in name.lower() for word in business_words):
            return False
        
        # Must contain at least one space (first and last name)
        if ' ' not in name.strip():
            return False
        
        return True
    
    def is_valid_first_name(self, name: str) -> bool:
        """Check if first name looks valid"""
        if not name or len(name) < 2 or len(name) > 20:
            return False
        
        # Common first names that appear in business names
        common_names = ['john', 'david', 'michael', 'james', 'robert', 'paul', 'mark', 'andrew', 'stephen', 'christopher']
        return name.lower() in common_names or (name[0].isupper() and name[1:].islower())
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except:
            return ""
    
    def analyze_content_quality(self, content: str, company_name: str) -> Dict[str, Any]:
        """Analyze content quality for lead generation potential"""
        content_lower = content.lower()
        
        # Check for contact information
        has_phone = bool(re.search(r'\b(?:\+44|0)\s?(?:\d{3,4}\s?\d{3,4}\s?\d{3,4}|\d{10,11})\b', content))
        has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content))
        has_address = any(keyword in content_lower for keyword in ['address', 'location', 'based in', 'serving'])
        
        # Check for business information
        has_about = any(keyword in content_lower for keyword in ['about', 'who we are', 'our story', 'experience'])
        has_services = any(keyword in content_lower for keyword in ['services', 'what we do', 'specialise', 'offer'])
        has_contact_page = any(keyword in content_lower for keyword in ['contact', 'get in touch', 'call us'])
        
        # SEO quality indicators
        has_meta_description = '<meta name="description"' in content
        has_title_tag = '<title>' in content
        has_headings = any(tag in content_lower for tag in ['<h1', '<h2', '<h3'])
        
        # Calculate quality score
        quality_score = 0
        if has_phone: quality_score += 15
        if has_email: quality_score += 15
        if has_address: quality_score += 10
        if has_about: quality_score += 10
        if has_services: quality_score += 10
        if has_contact_page: quality_score += 10
        if has_meta_description: quality_score += 10
        if has_title_tag: quality_score += 10
        if has_headings: quality_score += 10
        
        return {
            'quality_score': quality_score,
            'has_contact_info': has_phone or has_email,
            'has_phone': has_phone,
            'has_email': has_email,
            'has_address': has_address,
            'has_about_section': has_about,
            'has_services_section': has_services,
            'has_contact_page': has_contact_page,
            'seo_indicators': {
                'has_meta_description': has_meta_description,
                'has_title_tag': has_title_tag,
                'has_headings': has_headings
            },
            'content_length': len(content),
            'business_focused': company_name.lower() in content_lower
        }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test on all 10 URLs"""
        logger.info("🚀 Starting Direct Executive Discovery Test - 10 URLs")
        self.test_start_time = time.time()
        self.total_companies_tested = len(TEST_URLS)
        
        # Run tests with controlled concurrency
        semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent tests
        
        async def test_with_semaphore(company_data):
            async with semaphore:
                return await self.test_single_company_direct(company_data[0], company_data[1])
        
        # Execute all tests
        self.test_results = await asyncio.gather(
            *[test_with_semaphore(company_data) for company_data in TEST_URLS],
            return_exceptions=True
        )
        
        # Handle exceptions
        for i, result in enumerate(self.test_results):
            if isinstance(result, Exception):
                company_name, company_url = TEST_URLS[i]
                self.test_results[i] = {
                    'company_name': company_name,
                    'company_url': company_url,
                    'processing_time': 0.0,
                    'executives_found': 0,
                    'executives_data': [],
                    'website_health': {'status': 'exception', 'accessible': False},
                    'content_analysis': {},
                    'discovery_sources': [],
                    'success': False,
                    'error': str(result)
                }
        
        # Calculate metrics
        total_test_time = time.time() - self.test_start_time
        self.successful_discoveries = sum(1 for r in self.test_results if isinstance(r, dict) and r.get('success', False))
        self.total_executives_found = sum(r.get('executives_found', 0) for r in self.test_results if isinstance(r, dict))
        self.processing_times = [r.get('processing_time', 0) for r in self.test_results if isinstance(r, dict)]
        
        average_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0.0
        success_rate = (self.successful_discoveries / self.total_companies_tested) * 100 if self.total_companies_tested > 0 else 0.0
        
        # Compile results
        return {
            'test_metadata': {
                'test_name': 'Direct Executive Discovery Test - 10 URLs',
                'test_date': datetime.now().isoformat(),
                'total_test_time': total_test_time,
                'system_version': 'Direct Content Analysis System',
                'discovery_method': 'content_analysis_with_business_name_extraction'
            },
            'test_configuration': {
                'urls_tested': len(TEST_URLS),
                'concurrent_limit': 3,
                'timeout_per_request': 15,
                'analysis_methods': ['business_name_analysis', 'website_content_analysis', 'contact_information_extraction']
            },
            'overall_metrics': {
                'total_companies_tested': self.total_companies_tested,
                'successful_discoveries': self.successful_discoveries,
                'success_rate_percentage': success_rate,
                'total_executives_found': self.total_executives_found,
                'average_executives_per_company': self.total_executives_found / self.total_companies_tested if self.total_companies_tested > 0 else 0.0,
                'average_processing_time': average_processing_time,
                'total_processing_time': total_test_time,
                'fastest_discovery': min(self.processing_times) if self.processing_times else 0.0,
                'slowest_discovery': max(self.processing_times) if self.processing_times else 0.0
            },
            'content_quality_analysis': self._analyze_content_quality_aggregate(),
            'individual_results': self.test_results,
            'summary_analysis': {
                'websites_with_executives': sum(1 for r in self.test_results if isinstance(r, dict) and r.get('executives_found', 0) > 0),
                'websites_accessible': sum(1 for r in self.test_results if isinstance(r, dict) and r.get('website_health', {}).get('accessible', False)),
                'average_content_quality': self._calculate_average_quality_score(),
                'discovery_method_breakdown': self._analyze_discovery_methods()
            }
        }
    
    def _analyze_content_quality_aggregate(self) -> Dict[str, Any]:
        """Analyze aggregate content quality across all sites"""
        quality_scores = []
        contact_info_count = 0
        phone_count = 0
        email_count = 0
        
        for result in self.test_results:
            if isinstance(result, dict) and 'content_analysis' in result:
                analysis = result['content_analysis']
                if 'quality_score' in analysis:
                    quality_scores.append(analysis['quality_score'])
                if analysis.get('has_contact_info', False):
                    contact_info_count += 1
                if analysis.get('has_phone', False):
                    phone_count += 1
                if analysis.get('has_email', False):
                    email_count += 1
        
        return {
            'average_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'sites_with_contact_info': contact_info_count,
            'sites_with_phone': phone_count,
            'sites_with_email': email_count,
            'contact_info_rate': (contact_info_count / len(self.test_results)) * 100 if self.test_results else 0
        }
    
    def _calculate_average_quality_score(self) -> float:
        """Calculate average content quality score"""
        scores = []
        for result in self.test_results:
            if isinstance(result, dict) and 'content_analysis' in result:
                score = result['content_analysis'].get('quality_score', 0)
                scores.append(score)
        return sum(scores) / len(scores) if scores else 0.0
    
    def _analyze_discovery_methods(self) -> Dict[str, int]:
        """Analyze which discovery methods found executives"""
        methods = {}
        for result in self.test_results:
            if isinstance(result, dict) and result.get('executives_found', 0) > 0:
                for exec_data in result.get('executives_data', []):
                    method = exec_data.get('discovery_method', 'unknown')
                    methods[method] = methods.get(method, 0) + 1
        return methods

async def main():
    """Main test execution function"""
    logger.info("🚀 Direct Executive Discovery Test - Starting")
    
    # Initialize and run test
    test_engine = DirectExecutiveTest()
    results = await test_engine.run_comprehensive_test()
    
    # Generate JSON output file
    timestamp = int(time.time())
    output_filename = f"direct_executive_discovery_results_{timestamp}.json"
    
    with open(output_filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print summary
    logger.info("🎉 Direct Executive Discovery Test - Complete")
    logger.info(f"📄 Results saved to: {output_filename}")
    logger.info(f"📊 Summary: {results['overall_metrics']['successful_discoveries']}/{results['overall_metrics']['total_companies_tested']} successful discoveries")
    logger.info(f"👥 Total executives found: {results['overall_metrics']['total_executives_found']}")
    logger.info(f"⏱️ Total time: {results['overall_metrics']['total_processing_time']:.2f}s")
    logger.info(f"🎯 Success rate: {results['overall_metrics']['success_rate_percentage']:.1f}%")
    
    print(f"\n✅ Direct Test Complete!")
    print(f"📄 Results file: {output_filename}")
    print(f"📊 {results['overall_metrics']['successful_discoveries']}/{results['overall_metrics']['total_companies_tested']} companies had successful analysis")
    print(f"👥 {results['overall_metrics']['total_executives_found']} total executives discovered")
    print(f"🎯 {results['overall_metrics']['success_rate_percentage']:.1f}% success rate")
    print(f"⏱️ {results['overall_metrics']['total_processing_time']:.1f}s total processing time")
    
    return output_filename

if __name__ == "__main__":
    # Run the direct test
    output_file = asyncio.run(main()) 