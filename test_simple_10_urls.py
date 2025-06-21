#!/usr/bin/env python3
"""
Simple Test - 10 URL System Test
Tests the system with 10 plumbing company URLs using basic content analysis
"""

import asyncio
import json
import logging
import time
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse

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

class SimpleSystemTest:
    """Simple System Testing Engine"""
    
    def __init__(self):
        self.test_start_time = None
        self.test_results = []
        self.total_companies_tested = 0
        self.successful_discoveries = 0
        self.total_executives_found = 0
        self.processing_times = []
        self.websites_accessible = 0
    
    async def test_single_company(self, company_name: str, company_url: str) -> Dict[str, Any]:
        """Test a single company with comprehensive analysis"""
        logger.info(f"🔍 Testing Company: {company_name}")
        start_time = time.time()
        
        # Basic website accessibility test with content analysis
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                # Set realistic headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                async with session.get(company_url, headers=headers, timeout=15) as response:
                    content = await response.text()
                    processing_time = time.time() - start_time
                    
                    # Track successful access
                    if response.status == 200:
                        self.websites_accessible += 1
                    
                    # Extract executives and analyze content
                    executives = self.extract_executives_from_content(content, company_name, company_url)
                    content_analysis = self.analyze_content_quality(content, company_name)
                    seo_analysis = self.analyze_seo_indicators(content)
                    contact_info = self.extract_contact_information(content)
                    
                    # Count successful discoveries
                    if len(executives) > 0:
                        self.successful_discoveries += 1
                        self.total_executives_found += len(executives)
                    
                    return {
                        'company_name': company_name,
                        'company_url': company_url,
                        'processing_time': processing_time,
                        'executives_found': len(executives),
                        'executives_data': executives,
                        'website_health': {
                            'status': 'accessible' if response.status == 200 else 'error',
                            'accessible': response.status == 200,
                            'status_code': response.status,
                            'content_length': len(content),
                            'response_time': processing_time
                        },
                        'content_analysis': content_analysis,
                        'seo_analysis': seo_analysis,
                        'contact_information': contact_info,
                        'discovery_sources': ['business_name_analysis', 'content_analysis'],
                        'success': response.status == 200,
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
                'seo_analysis': {},
                'contact_information': {},
                'discovery_sources': [],
                'success': False,
                'error': str(e)
            }
    
    def extract_executives_from_content(self, content: str, company_name: str, company_url: str) -> List[Dict[str, Any]]:
        """Extract potential executives from website content"""
        executives = []
        
        try:
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
            
            # Content analysis for executives
            content_lower = content.lower()
            
            # Look for common executive patterns
            executive_patterns = [
                (r'\b(director|manager|owner|founder|ceo|md|managing director)\b', 'Executive'),
                (r'\b(proprietor|principal|head|chief|lead)\b', 'Senior Executive'),
                (r'\b(project manager|site manager|contracts manager)\b', 'Manager'),
                (r'\b(business development manager|operations manager)\b', 'Manager'),
                (r'\b(plumber|heating engineer|gas engineer)\b', 'Tradesperson')
            ]
            
            # Simple name extraction around titles
            if any(keyword in content_lower for keyword in ['about', 'team', 'staff', 'contact', 'our', 'meet']):
                # Look for name patterns
                name_matches = re.findall(r'\b([A-Z][a-z]{2,15})\s+([A-Z][a-z]{2,15})\b', content)
                
                for first_name, last_name in name_matches:
                    full_name = f"{first_name} {last_name}"
                    if self.is_valid_name(full_name, company_name):
                        # Try to find associated title
                        title = self.find_title_near_name(content, full_name)
                        if not title:
                            title = "Team Member"
                        
                        executives.append({
                            'name': full_name,
                            'title': title,
                            'company': company_name,
                            'company_domain': self.extract_domain(company_url),
                            'confidence_score': 0.6,
                            'discovery_method': 'website_content_analysis',
                            'source': 'website_content',
                            'contact_info': {}
                        })
            
            # Remove duplicates
            seen_names = set()
            unique_executives = []
            for exec in executives:
                name_key = exec['name'].lower().strip()
                if name_key not in seen_names and len(name_key) > 3:
                    seen_names.add(name_key)
                    unique_executives.append(exec)
            
            return unique_executives[:5]  # Limit to top 5
            
        except Exception as e:
            logger.debug(f"Error extracting executives: {e}")
            return []
    
    def extract_owner_from_business_name(self, company_name: str) -> Dict[str, Any]:
        """Extract potential owner name from business name"""
        # Common patterns for owner names in business names
        patterns = [
            (r'^([A-Z][a-z]{2,})\s+(?:Plumbing|Heating|Gas|Electrical|Building)', 'Business Owner'),
            (r'^([A-Z][a-z]{2,})\s*\'s\s+(?:Plumbing|Heating|Gas)', 'Business Owner'),
            (r'^([A-Z][a-z]{2,})\s+&\s+(?:Sons?|Co|Company)', 'Business Owner'),
            (r'^([A-Z][a-z]{2,})\s+(?:and|&)\s+(?:Sons?|Daughters?)', 'Family Business Owner'),
            (r'([A-Z][a-z]{2,})\s+(?:Family|Brothers?)\s+(?:Business|Plumbing)', 'Family Business Owner')
        ]
        
        for pattern, title in patterns:
            match = re.search(pattern, company_name)
            if match:
                name = match.group(1)
                if self.is_valid_first_name(name):
                    return {
                        'name': name,
                        'title': title,
                        'confidence': 0.8
                    }
        
        return None
    
    def find_title_near_name(self, content: str, name: str) -> str:
        """Find executive title near a name in content"""
        # Look for the name in content and check surrounding text
        name_pos = content.lower().find(name.lower())
        if name_pos == -1:
            return "Team Member"
        
        # Check text around the name (200 characters before and after)
        start = max(0, name_pos - 200)
        end = min(len(content), name_pos + len(name) + 200)
        context = content[start:end].lower()
        
        # Look for titles in the context
        if any(word in context for word in ['director', 'manager', 'owner', 'founder']):
            return "Director/Manager"
        elif any(word in context for word in ['proprietor', 'principal', 'head', 'chief']):
            return "Senior Executive"
        elif any(word in context for word in ['plumber', 'engineer', 'technician']):
            return "Technical Specialist"
        
        return "Team Member"
    
    def is_valid_name(self, name: str, company_name: str) -> bool:
        """Check if name looks valid and isn't part of company name"""
        if not name or len(name) < 4 or len(name) > 50:
            return False
        
        # Check for common business words that aren't names
        business_words = ['plumbing', 'heating', 'gas', 'electrical', 'services', 'company', 'ltd', 'limited', 'solutions', 'about', 'contact', 'home', 'page']
        if any(word in name.lower() for word in business_words):
            return False
        
        # Don't include if name is part of company name
        if name.lower() in company_name.lower():
            return False
        
        # Must be proper case (First Last)
        parts = name.split()
        if len(parts) != 2:
            return False
        
        return all(part[0].isupper() and part[1:].islower() for part in parts if part)
    
    def is_valid_first_name(self, name: str) -> bool:
        """Check if first name looks valid"""
        if not name or len(name) < 2 or len(name) > 20:
            return False
        
        # Must be proper case
        return name[0].isupper() and name[1:].islower()
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
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
        has_address = any(keyword in content_lower for keyword in ['address', 'location', 'based in', 'serving', 'birmingham', 'uk', 'england'])
        
        # Check for business information
        has_about = any(keyword in content_lower for keyword in ['about', 'who we are', 'our story', 'experience'])
        has_services = any(keyword in content_lower for keyword in ['services', 'what we do', 'specialise', 'offer'])
        has_contact_page = any(keyword in content_lower for keyword in ['contact', 'get in touch', 'call us'])
        
        # Calculate quality score
        quality_score = 0
        if has_phone: quality_score += 20
        if has_email: quality_score += 20
        if has_address: quality_score += 15
        if has_about: quality_score += 15
        if has_services: quality_score += 15
        if has_contact_page: quality_score += 15
        
        return {
            'quality_score': quality_score,
            'has_contact_info': has_phone or has_email,
            'has_phone': has_phone,
            'has_email': has_email,
            'has_address': has_address,
            'has_about_section': has_about,
            'has_services_section': has_services,
            'has_contact_page': has_contact_page,
            'content_length': len(content),
            'business_focused': company_name.lower() in content_lower
        }
    
    def analyze_seo_indicators(self, content: str) -> Dict[str, Any]:
        """Analyze SEO quality indicators"""
        # Basic SEO checks
        has_meta_description = '<meta name="description"' in content
        has_title_tag = '<title>' in content and '</title>' in content
        has_h1 = '<h1' in content.lower()
        has_h2 = '<h2' in content.lower()
        has_images = '<img' in content.lower()
        
        # Extract title if available
        title = ""
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
        
        # Calculate SEO score
        seo_score = 0
        if has_meta_description: seo_score += 20
        if has_title_tag: seo_score += 20
        if has_h1: seo_score += 20
        if has_h2: seo_score += 15
        if has_images: seo_score += 10
        if len(title) > 10: seo_score += 15
        
        return {
            'seo_score': seo_score,
            'has_meta_description': has_meta_description,
            'has_title_tag': has_title_tag,
            'has_h1': has_h1,
            'has_h2': has_h2,
            'has_images': has_images,
            'page_title': title,
            'title_length': len(title)
        }
    
    def extract_contact_information(self, content: str) -> Dict[str, Any]:
        """Extract contact information from content"""
        # Phone numbers
        phone_pattern = r'\b(?:\+44|0)\s?(?:\d{3,4}\s?\d{3,4}\s?\d{3,4}|\d{10,11})\b'
        phones = re.findall(phone_pattern, content)
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        
        # Remove duplicates
        phones = list(set(phones))
        emails = list(set(emails))
        
        return {
            'phones': phones,
            'emails': emails,
            'phone_count': len(phones),
            'email_count': len(emails),
            'has_contact_details': len(phones) > 0 or len(emails) > 0
        }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test on all 10 URLs"""
        logger.info("🚀 Starting Simple System Test - 10 URLs")
        self.test_start_time = time.time()
        self.total_companies_tested = len(TEST_URLS)
        
        # Run tests with controlled concurrency
        semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent tests
        
        async def test_with_semaphore(company_data):
            async with semaphore:
                result = await self.test_single_company(company_data[0], company_data[1])
                self.processing_times.append(result.get('processing_time', 0))
                return result
        
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
                    'seo_analysis': {},
                    'contact_information': {},
                    'discovery_sources': [],
                    'success': False,
                    'error': str(result)
                }
        
        # Calculate final metrics
        total_test_time = time.time() - self.test_start_time
        average_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0.0
        success_rate = (self.successful_discoveries / self.total_companies_tested) * 100 if self.total_companies_tested > 0 else 0.0
        accessibility_rate = (self.websites_accessible / self.total_companies_tested) * 100 if self.total_companies_tested > 0 else 0.0
        
        # Compile comprehensive results
        return {
            'test_metadata': {
                'test_name': 'Simple System Test - 10 URLs',
                'test_date': datetime.now().isoformat(),
                'total_test_time': total_test_time,
                'system_version': 'Simple Content Analysis System v1.0',
                'description': 'Comprehensive analysis of 10 plumbing company websites'
            },
            'test_configuration': {
                'urls_tested': len(TEST_URLS),
                'concurrent_limit': 3,
                'timeout_per_request': 15,
                'analysis_methods': [
                    'business_name_analysis',
                    'website_content_analysis',
                    'contact_information_extraction',
                    'seo_analysis',
                    'content_quality_assessment'
                ]
            },
            'overall_metrics': {
                'total_companies_tested': self.total_companies_tested,
                'successful_discoveries': self.successful_discoveries,
                'success_rate_percentage': success_rate,
                'total_executives_found': self.total_executives_found,
                'average_executives_per_company': self.total_executives_found / self.total_companies_tested if self.total_companies_tested > 0 else 0.0,
                'websites_accessible': self.websites_accessible,
                'accessibility_rate_percentage': accessibility_rate,
                'average_processing_time': average_processing_time,
                'total_processing_time': total_test_time,
                'fastest_discovery': min(self.processing_times) if self.processing_times else 0.0,
                'slowest_discovery': max(self.processing_times) if self.processing_times else 0.0
            },
            'aggregate_analysis': {
                'content_quality': self._analyze_aggregate_content_quality(),
                'seo_quality': self._analyze_aggregate_seo_quality(),
                'contact_information': self._analyze_aggregate_contact_info(),
                'discovery_methods': self._analyze_discovery_methods(),
                'website_accessibility': self._analyze_website_accessibility()
            },
            'individual_results': self.test_results,
            'recommendations': self._generate_recommendations()
        }
    
    def _analyze_aggregate_content_quality(self) -> Dict[str, Any]:
        """Analyze aggregate content quality"""
        quality_scores = []
        sites_with_contact = 0
        sites_with_about = 0
        sites_with_services = 0
        
        for result in self.test_results:
            if isinstance(result, dict) and 'content_analysis' in result:
                analysis = result['content_analysis']
                if 'quality_score' in analysis:
                    quality_scores.append(analysis['quality_score'])
                if analysis.get('has_contact_info', False):
                    sites_with_contact += 1
                if analysis.get('has_about_section', False):
                    sites_with_about += 1
                if analysis.get('has_services_section', False):
                    sites_with_services += 1
        
        return {
            'average_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'sites_with_contact_info': sites_with_contact,
            'sites_with_about_section': sites_with_about,
            'sites_with_services_section': sites_with_services,
            'quality_distribution': {
                'high_quality': sum(1 for score in quality_scores if score >= 70),
                'medium_quality': sum(1 for score in quality_scores if 40 <= score < 70),
                'low_quality': sum(1 for score in quality_scores if score < 40)
            }
        }
    
    def _analyze_aggregate_seo_quality(self) -> Dict[str, Any]:
        """Analyze aggregate SEO quality"""
        seo_scores = []
        sites_with_meta = 0
        sites_with_title = 0
        sites_with_h1 = 0
        
        for result in self.test_results:
            if isinstance(result, dict) and 'seo_analysis' in result:
                analysis = result['seo_analysis']
                if 'seo_score' in analysis:
                    seo_scores.append(analysis['seo_score'])
                if analysis.get('has_meta_description', False):
                    sites_with_meta += 1
                if analysis.get('has_title_tag', False):
                    sites_with_title += 1
                if analysis.get('has_h1', False):
                    sites_with_h1 += 1
        
        return {
            'average_seo_score': sum(seo_scores) / len(seo_scores) if seo_scores else 0,
            'sites_with_meta_description': sites_with_meta,
            'sites_with_title_tag': sites_with_title,
            'sites_with_h1_tag': sites_with_h1,
            'seo_distribution': {
                'good_seo': sum(1 for score in seo_scores if score >= 70),
                'fair_seo': sum(1 for score in seo_scores if 40 <= score < 70),
                'poor_seo': sum(1 for score in seo_scores if score < 40)
            }
        }
    
    def _analyze_aggregate_contact_info(self) -> Dict[str, Any]:
        """Analyze aggregate contact information"""
        total_phones = 0
        total_emails = 0
        sites_with_phones = 0
        sites_with_emails = 0
        
        for result in self.test_results:
            if isinstance(result, dict) and 'contact_information' in result:
                contact = result['contact_information']
                phone_count = contact.get('phone_count', 0)
                email_count = contact.get('email_count', 0)
                
                total_phones += phone_count
                total_emails += email_count
                
                if phone_count > 0:
                    sites_with_phones += 1
                if email_count > 0:
                    sites_with_emails += 1
        
        return {
            'total_phone_numbers': total_phones,
            'total_email_addresses': total_emails,
            'sites_with_phone_numbers': sites_with_phones,
            'sites_with_email_addresses': sites_with_emails,
            'contact_completeness_rate': ((sites_with_phones + sites_with_emails) / (2 * len(self.test_results))) * 100 if self.test_results else 0
        }
    
    def _analyze_discovery_methods(self) -> Dict[str, int]:
        """Analyze discovery method effectiveness"""
        business_name_discoveries = 0
        content_discoveries = 0
        
        for result in self.test_results:
            if isinstance(result, dict) and result.get('executives_found', 0) > 0:
                for exec_data in result.get('executives_data', []):
                    method = exec_data.get('discovery_method', '')
                    if 'business_name' in method:
                        business_name_discoveries += 1
                    elif 'content' in method:
                        content_discoveries += 1
        
        return {
            'business_name_analysis': business_name_discoveries,
            'website_content_analysis': content_discoveries,
            'total_discoveries': business_name_discoveries + content_discoveries
        }
    
    def _analyze_website_accessibility(self) -> Dict[str, Any]:
        """Analyze website accessibility patterns"""
        accessible_sites = 0
        ssl_errors = 0
        timeout_errors = 0
        other_errors = 0
        
        for result in self.test_results:
            if isinstance(result, dict):
                if result.get('website_health', {}).get('accessible', False):
                    accessible_sites += 1
                else:
                    error = result.get('error', '') or ''
                    error_lower = error.lower()
                    if 'ssl' in error_lower or 'certificate' in error_lower:
                        ssl_errors += 1
                    elif 'timeout' in error_lower:
                        timeout_errors += 1
                    else:
                        other_errors += 1
        
        return {
            'accessible_sites': accessible_sites,
            'inaccessible_sites': len(self.test_results) - accessible_sites,
            'accessibility_rate': (accessible_sites / len(self.test_results)) * 100 if self.test_results else 0,
            'error_breakdown': {
                'ssl_certificate_errors': ssl_errors,
                'timeout_errors': timeout_errors,
                'other_errors': other_errors
            }
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Website accessibility recommendations
        accessible_rate = (self.websites_accessible / self.total_companies_tested) * 100 if self.total_companies_tested > 0 else 0
        if accessible_rate < 90:
            recommendations.append(f"Website accessibility is {accessible_rate:.1f}% - consider implementing fallback data sources for inaccessible sites")
        
        # Executive discovery recommendations
        discovery_rate = (self.successful_discoveries / self.total_companies_tested) * 100 if self.total_companies_tested > 0 else 0
        if discovery_rate < 50:
            recommendations.append(f"Executive discovery rate is {discovery_rate:.1f}% - consider enhancing pattern recognition or alternative data sources")
        
        # SEO opportunity recommendations
        avg_seo = self._calculate_average_seo_score()
        if avg_seo < 60:
            recommendations.append(f"Average SEO score is {avg_seo:.1f}/100 - significant SEO improvement opportunities identified")
        
        # Contact information recommendations
        contact_sites = sum(1 for r in self.test_results if isinstance(r, dict) and r.get('contact_information', {}).get('has_contact_details', False))
        contact_rate = (contact_sites / len(self.test_results)) * 100 if self.test_results else 0
        if contact_rate < 80:
            recommendations.append(f"Only {contact_rate:.1f}% of sites have easily extractable contact information - consider enhanced extraction methods")
        
        return recommendations
    
    def _calculate_average_seo_score(self) -> float:
        """Calculate average SEO score"""
        scores = []
        for result in self.test_results:
            if isinstance(result, dict) and 'seo_analysis' in result:
                score = result['seo_analysis'].get('seo_score', 0)
                scores.append(score)
        return sum(scores) / len(scores) if scores else 0.0

async def main():
    """Main test execution function"""
    logger.info("🚀 Simple System Test - Starting")
    
    # Initialize and run test
    test_engine = SimpleSystemTest()
    results = await test_engine.run_comprehensive_test()
    
    # Generate JSON output file
    timestamp = int(time.time())
    output_filename = f"simple_system_test_results_{timestamp}.json"
    
    with open(output_filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print comprehensive summary
    logger.info("🎉 Simple System Test - Complete")
    logger.info(f"📄 Results saved to: {output_filename}")
    logger.info(f"📊 Summary: {results['overall_metrics']['successful_discoveries']}/{results['overall_metrics']['total_companies_tested']} successful executive discoveries")
    logger.info(f"🌐 Website accessibility: {results['overall_metrics']['websites_accessible']}/{results['overall_metrics']['total_companies_tested']} sites accessible")
    logger.info(f"👥 Total executives found: {results['overall_metrics']['total_executives_found']}")
    logger.info(f"⏱️ Total time: {results['overall_metrics']['total_processing_time']:.2f}s")
    logger.info(f"🎯 Executive discovery rate: {results['overall_metrics']['success_rate_percentage']:.1f}%")
    logger.info(f"🌐 Website accessibility rate: {results['overall_metrics']['accessibility_rate_percentage']:.1f}%")
    
    print(f"\n✅ Simple System Test Complete!")
    print(f"📄 Results file: {output_filename}")
    print(f"📊 Executive Discovery: {results['overall_metrics']['successful_discoveries']}/{results['overall_metrics']['total_companies_tested']} companies")
    print(f"🌐 Website Access: {results['overall_metrics']['websites_accessible']}/{results['overall_metrics']['total_companies_tested']} sites accessible")
    print(f"👥 {results['overall_metrics']['total_executives_found']} total executives discovered")
    print(f"🎯 {results['overall_metrics']['success_rate_percentage']:.1f}% executive discovery rate")
    print(f"🌐 {results['overall_metrics']['accessibility_rate_percentage']:.1f}% website accessibility rate")
    print(f"⏱️ {results['overall_metrics']['total_processing_time']:.1f}s total processing time")
    
    return output_filename

if __name__ == "__main__":
    # Run the comprehensive test
    output_file = asyncio.run(main()) 