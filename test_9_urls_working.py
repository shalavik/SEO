#!/usr/bin/env python3
"""
Working 9 URLs Test - Simple test with available components
Tests the 9 URLs with basic functionality using existing system.
"""

import asyncio
import json
import aiohttp
import traceback
from datetime import datetime
from typing import Dict, List, Any
from urllib.parse import urlparse
import re

class Working9URLTest:
    """Working test for 9 URLs using basic functionality"""
    
    def __init__(self):
        """Initialize test with 9 URLs"""
        self.test_urls = [
            "https://sitelift.site/richardhopeplumbingservices/",
            "https://www.am-electrical.co.uk/waterheater/",
            "https://www.trustatrader.com/traders/hgs-plumbing-heating-plumbers-selly-oak",
            "https://davisplumbing1.wixsite.com/davisplumbing",
            "http://mccannsheatingandplumbing.co.uk/",
            "http://www.fandpplumbing.co.uk/",
            "http://www.birminghamemergencyplumberforceheat.co.uk/",
            "https://www.pheaseyheating.co.uk/",
            "http://www.emergeplumbing.co.uk/"
        ]
        
        self.results = {
            "test_metadata": {
                "test_name": "Working 9 URLs System Test",
                "test_date": datetime.now().isoformat(),
                "total_urls": len(self.test_urls),
                "description": "Basic system test with website analysis and contact extraction"
            },
            "companies": [],
            "analytics": {
                "contact_extraction_rate": 0,
                "email_discovery_rate": 0,
                "phone_discovery_rate": 0,
                "content_analysis_success": 0
            },
            "test_summary": {}
        }

    def extract_company_name(self, url: str) -> str:
        """Extract company name from URL"""
        domain = urlparse(url).netloc.replace('www.', '')
        
        name_mapping = {
            "sitelift.site": "Richard Hope Plumbing Services",
            "am-electrical.co.uk": "AM Electrical",
            "trustatrader.com": "HGS Plumbing & Heating",
            "davisplumbing1.wixsite.com": "Davis Plumbing",
            "mccannsheatingandplumbing.co.uk": "McCann's Heating and Plumbing",
            "fandpplumbing.co.uk": "F&P Plumbing",
            "birminghamemergencyplumberforceheat.co.uk": "Birmingham Emergency Plumber Force Heat",
            "pheaseyheating.co.uk": "Pheasey Heating",
            "emergeplumbing.co.uk": "Emerge Plumbing"
        }
        
        for domain_key, name in name_mapping.items():
            if domain_key in domain:
                return name
        
        return f"Company from {domain}"

    async def fetch_website_content(self, url: str) -> Dict[str, Any]:
        """Fetch and analyze website content"""
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return {
                            "status": "success",
                            "content_length": len(content),
                            "content": content[:10000]  # First 10k chars for analysis
                        }
                    else:
                        return {
                            "status": "error",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def extract_contacts(self, content: str) -> Dict[str, Any]:
        """Extract contact information from content"""
        contacts = {
            "emails": [],
            "phones": [],
            "names": [],
            "titles": []
        }
        
        # Email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        contacts["emails"] = list(set(emails))  # Remove duplicates
        
        # UK Phone number extraction
        phone_patterns = [
            r'\b0[1-9]\d{8,9}\b',  # UK landline
            r'\b07\d{9}\b',        # UK mobile
            r'\+44\s?[1-9]\d{8,9}\b'  # International format
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, content))
        contacts["phones"] = list(set(phones))
        
        # Executive names (simple patterns)
        name_patterns = [
            r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b',  # First Last
        ]
        
        names = []
        for pattern in name_patterns:
            matches = re.findall(pattern, content)
            names.extend(matches)
        
        # Filter out common false positives
        filtered_names = []
        exclude_words = ['Terms Conditions', 'Privacy Policy', 'About Us', 'Contact Us', 
                        'West Midlands', 'United Kingdom', 'Great Britain']
        
        for name in names:
            if name not in exclude_words and len(name.split()) == 2:
                filtered_names.append(name)
        
        contacts["names"] = list(set(filtered_names))[:5]  # Top 5 unique names
        
        # Executive titles
        title_patterns = [
            r'\b(Managing Director|CEO|Director|Manager|Owner|Founder)\b',
        ]
        
        titles = []
        for pattern in title_patterns:
            titles.extend(re.findall(pattern, content, re.IGNORECASE))
        contacts["titles"] = list(set(titles))
        
        return contacts

    def analyze_seo_basics(self, content: str) -> Dict[str, Any]:
        """Basic SEO analysis"""
        try:
            # Title extraction
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else "No title"
            
            # Meta description
            meta_desc = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', content, re.IGNORECASE)
            has_meta_desc = bool(meta_desc)
            
            # H1 tags
            h1_tags = re.findall(r'<h1[^>]*>([^<]+)</h1>', content, re.IGNORECASE)
            has_h1 = len(h1_tags) > 0
            
            # SSL check (from URL)
            has_ssl = content.lower().count('https') > 0
            
            # Contact sections
            has_contact = 'contact' in content.lower()
            has_about = 'about' in content.lower()
            
            return {
                "title": title,
                "has_meta_description": has_meta_desc,
                "has_h1_tags": has_h1,
                "h1_count": len(h1_tags),
                "has_ssl_references": has_ssl,
                "has_contact_section": has_contact,
                "has_about_section": has_about,
                "content_quality_score": self.calculate_content_score(content)
            }
        except Exception as e:
            return {"error": str(e)}

    def calculate_content_score(self, content: str) -> float:
        """Calculate basic content quality score"""
        score = 0
        
        # Length score
        if len(content) > 5000:
            score += 20
        elif len(content) > 2000:
            score += 15
        elif len(content) > 500:
            score += 10
        
        # Keyword density (plumbing/electrical terms)
        keywords = ['plumbing', 'heating', 'electrical', 'emergency', 'repair', 'service']
        keyword_count = sum(content.lower().count(keyword) for keyword in keywords)
        score += min(keyword_count * 2, 30)
        
        # Contact information presence
        if '@' in content:
            score += 15
        if re.search(r'\b0[1-9]\d{8,9}\b', content):
            score += 15
        
        # Structure elements
        if '<h1' in content:
            score += 10
        if 'contact' in content.lower():
            score += 10
        
        return min(score, 100)

    async def test_single_url(self, url: str, index: int) -> Dict[str, Any]:
        """Test single URL with comprehensive analysis"""
        print(f"\n🧪 Testing URL {index+1}/9: {url}")
        
        try:
            # Extract company name
            company_name = self.extract_company_name(url)
            print(f"   📝 Company: {company_name}")
            
            # Fetch website content
            content_result = await self.fetch_website_content(url)
            if content_result["status"] != "success":
                return {
                    "url": url,
                    "company_name": company_name,
                    "status": "error",
                    "error": content_result.get("error", "Unknown error")
                }
            
            content = content_result["content"]
            print(f"   📄 Content fetched: {len(content)} chars")
            
            # Extract contacts
            contacts = self.extract_contacts(content)
            print(f"   📞 Contacts found: {len(contacts['emails'])} emails, {len(contacts['phones'])} phones, {len(contacts['names'])} names")
            
            # SEO analysis
            seo_analysis = self.analyze_seo_basics(content)
            print(f"   📊 SEO analysis completed")
            
            # Compile result
            result = {
                "url": url,
                "company_name": company_name,
                "status": "success",
                "contact_extraction": {
                    "emails_found": len(contacts["emails"]),
                    "phones_found": len(contacts["phones"]),
                    "names_found": len(contacts["names"]),
                    "titles_found": len(contacts["titles"]),
                    "emails": contacts["emails"],
                    "phones": contacts["phones"],
                    "names": contacts["names"],
                    "titles": contacts["titles"]
                },
                "seo_analysis": seo_analysis,
                "content_metrics": {
                    "content_length": content_result["content_length"],
                    "has_contact_info": len(contacts["emails"]) > 0 or len(contacts["phones"]) > 0
                },
                "processing_time": 0.0
            }
            
            return result
            
        except Exception as e:
            print(f"   ❌ Error processing {url}: {str(e)}")
            return {
                "url": url,
                "company_name": company_name,
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    async def run_comprehensive_test(self):
        """Run complete test on all 9 URLs"""
        print("🚀 STARTING WORKING 9 URLs SYSTEM TEST")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # Process all URLs
        for i, url in enumerate(self.test_urls):
            url_start = datetime.now()
            result = await self.test_single_url(url, i)
            url_end = datetime.now()
            
            if 'processing_time' in result:
                result['processing_time'] = (url_end - url_start).total_seconds()
            
            self.results["companies"].append(result)
        
        # Calculate analytics
        self._calculate_analytics()
        
        # Generate test summary
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        successful = sum(1 for r in self.results["companies"] if r["status"] == "success")
        failed = sum(1 for r in self.results["companies"] if r["status"] == "error")
        
        self.results["test_summary"] = {
            "total_processing_time": total_time,
            "average_time_per_url": total_time / len(self.test_urls),
            "successful_extractions": successful,
            "failed_extractions": failed,
            "success_rate": (successful / len(self.test_urls)) * 100
        }
        
        print("\n" + "=" * 80)
        print("🎯 TEST COMPLETION SUMMARY")
        print(f"✅ Successfully processed: {successful}/9 URLs")
        print(f"❌ Failed processing: {failed}/9 URLs")  
        print(f"📊 Success rate: {self.results['test_summary']['success_rate']:.1f}%")
        print(f"⏱️ Total time: {total_time:.2f} seconds")
        print(f"⚡ Average per URL: {self.results['test_summary']['average_time_per_url']:.2f} seconds")

    def _calculate_analytics(self):
        """Calculate test analytics"""
        successful_results = [r for r in self.results["companies"] if r["status"] == "success"]
        
        if not successful_results:
            return
        
        # Contact extraction rates
        email_found = sum(1 for r in successful_results 
                         if r.get("contact_extraction", {}).get("emails_found", 0) > 0)
        phone_found = sum(1 for r in successful_results 
                         if r.get("contact_extraction", {}).get("phones_found", 0) > 0)
        contact_found = sum(1 for r in successful_results 
                           if r.get("content_metrics", {}).get("has_contact_info", False))
        content_success = sum(1 for r in successful_results 
                             if r.get("seo_analysis", {}).get("content_quality_score", 0) > 50)
        
        total = len(successful_results)
        
        self.results["analytics"] = {
            "email_discovery_rate": (email_found / total) * 100,
            "phone_discovery_rate": (phone_found / total) * 100,
            "contact_extraction_rate": (contact_found / total) * 100,
            "content_analysis_success": (content_success / total) * 100
        }

    def save_results(self, filename: str = None):
        """Save test results to JSON file"""
        if filename is None:
            timestamp = int(datetime.now().timestamp())
            filename = f"working_9_url_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Results saved to: {filename}")
        return filename

async def main():
    """Main test execution"""
    print("🔬 WORKING 9 URLs SYSTEM TEST")
    print("Testing basic functionality with contact extraction and SEO analysis")
    print()
    
    test = Working9URLTest()
    
    try:
        await test.run_comprehensive_test()
        filename = test.save_results()
        
        # Display analytics
        print("\n🎯 EXTRACTION ANALYTICS:")
        analytics = test.results["analytics"]
        print(f"   Email Discovery Rate: {analytics['email_discovery_rate']:.1f}%")
        print(f"   Phone Discovery Rate: {analytics['phone_discovery_rate']:.1f}%")
        print(f"   Contact Extraction Rate: {analytics['contact_extraction_rate']:.1f}%")
        print(f"   Content Analysis Success: {analytics['content_analysis_success']:.1f}%")
        
        print(f"\n✅ Complete results saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main()) 