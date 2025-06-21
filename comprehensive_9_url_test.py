#!/usr/bin/env python3
"""
Comprehensive 9 URLs Test - Latest System Analysis
Enhanced test with contact extraction, SEO analysis, and executive discovery.
"""

import asyncio
import json
import aiohttp
import traceback
from datetime import datetime
from typing import Dict, List, Any
from urllib.parse import urlparse
import re

class Comprehensive9URLTest:
    """Comprehensive test for 9 URLs with enhanced analysis"""
    
    def __init__(self):
        """Initialize comprehensive test"""
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
                "test_name": "Comprehensive 9 URLs Latest System Test",
                "test_date": datetime.now().isoformat(),
                "total_urls": len(self.test_urls),
                "system_version": "Latest with Phase 5 Enhancements",
                "description": "Complete analysis with contact extraction, SEO, and executive discovery"
            },
            "companies": [],
            "system_analytics": {
                "email_discovery_rate": 0,
                "phone_discovery_rate": 0,
                "executive_identification_rate": 0,
                "seo_analysis_success": 0,
                "contact_attribution_accuracy": 0
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
        """Fetch website content with error handling"""
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return {"status": "success", "content": content}
                    else:
                        return {"status": "error", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def extract_comprehensive_contacts(self, content: str) -> Dict[str, Any]:
        """Comprehensive contact extraction with enhanced patterns"""
        contacts = {
            "emails": [],
            "phones": [],
            "executives": [],
            "contact_attribution": {}
        }
        
        # Email extraction (enhanced patterns)
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
        ]
        
        emails = []
        for pattern in email_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            emails.extend(matches)
        contacts["emails"] = list(set(emails))
        
        # UK Phone extraction (comprehensive patterns)
        phone_patterns = [
            r'\b0[1-9]\d{8,9}\b',           # UK landline
            r'\b07\d{9}\b',                  # UK mobile
            r'\+44\s?[1-9]\d{8,9}\b',       # International
            r'\b\d{5}\s\d{6}\b'             # Spaced format
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, content)
            phones.extend(matches)
        contacts["phones"] = list(set(phones))
        
        # Executive extraction with enhanced patterns
        executive_patterns = [
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s*[-,]?\s*(Managing Director|CEO|Director|Manager|Owner|Founder)',
            r'(Managing Director|CEO|Director|Manager|Owner|Founder)[:\s-]*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
        ]
        
        executives = []
        for pattern in executive_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    name = match[0] if match[0] else match[1]
                    title = match[1] if len(match) > 1 and match[1] else "Unknown"
                else:
                    name = match
                    title = "Unknown"
                
                if name and len(name.split()) == 2:
                    executives.append({"name": name, "title": title})
        
        # Remove duplicates and filter false positives
        filtered_executives = []
        exclude_names = ['Terms Conditions', 'Privacy Policy', 'About Us', 'Contact Us', 
                        'West Midlands', 'United Kingdom', 'Great Britain', 'Boiler Services']
        
        for exec in executives:
            if exec["name"] not in exclude_names and exec not in filtered_executives:
                filtered_executives.append(exec)
        
        contacts["executives"] = filtered_executives[:10]  # Top 10
        
        # Contact attribution (basic proximity analysis)
        attribution = self.analyze_contact_attribution(content, contacts)
        contacts["contact_attribution"] = attribution
        
        return contacts

    def analyze_contact_attribution(self, content: str, contacts: Dict) -> Dict[str, Any]:
        """Analyze contact attribution to specific people"""
        attribution = {
            "attributed_contacts": 0,
            "attribution_confidence": 0.0,
            "attributions": []
        }
        
        # Simple proximity analysis - look for emails/phones near executive names
        for exec in contacts.get("executives", []):
            name = exec["name"]
            name_index = content.lower().find(name.lower())
            
            if name_index != -1:
                # Check 500 chars around the name for contact info
                start = max(0, name_index - 250)
                end = min(len(content), name_index + 250)
                context = content[start:end]
                
                attributed_emails = [email for email in contacts["emails"] if email in context]
                attributed_phones = [phone for phone in contacts["phones"] if phone in context]
                
                if attributed_emails or attributed_phones:
                    attribution["attributions"].append({
                        "executive": exec,
                        "emails": attributed_emails,
                        "phones": attributed_phones,
                        "confidence": 0.7
                    })
                    attribution["attributed_contacts"] += 1
        
        attribution["attribution_confidence"] = attribution["attributed_contacts"] / max(1, len(contacts.get("executives", [])))
        return attribution

    def analyze_enhanced_seo(self, content: str, url: str) -> Dict[str, Any]:
        """Enhanced SEO analysis"""
        seo = {}
        
        # Title analysis
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        seo["title"] = title_match.group(1).strip() if title_match else "No title"
        seo["title_length"] = len(seo["title"])
        seo["title_optimized"] = 30 <= seo["title_length"] <= 60
        
        # Meta description
        meta_desc = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', content, re.IGNORECASE)
        seo["has_meta_description"] = bool(meta_desc)
        seo["meta_description"] = meta_desc.group(1) if meta_desc else None
        
        # Heading analysis
        h1_tags = re.findall(r'<h1[^>]*>([^<]+)</h1>', content, re.IGNORECASE)
        seo["h1_count"] = len(h1_tags)
        seo["has_h1"] = len(h1_tags) > 0
        seo["h1_tags"] = h1_tags[:3]  # First 3
        
        # Technical SEO
        seo["has_ssl"] = url.startswith('https://')
        seo["mobile_viewport"] = 'viewport' in content.lower()
        seo["structured_data"] = 'application/ld+json' in content
        
        # Content analysis
        seo["content_length"] = len(content)
        seo["content_quality_score"] = self.calculate_enhanced_content_score(content)
        
        # Local SEO indicators
        uk_locations = ['birmingham', 'london', 'manchester', 'leeds', 'liverpool']
        seo["local_seo_signals"] = sum(1 for location in uk_locations if location in content.lower())
        
        return seo

    def calculate_enhanced_content_score(self, content: str) -> float:
        """Enhanced content quality scoring"""
        score = 0
        
        # Length scoring
        if len(content) > 10000: score += 25
        elif len(content) > 5000: score += 20
        elif len(content) > 2000: score += 15
        elif len(content) > 500: score += 10
        
        # Industry keyword density
        plumbing_keywords = ['plumbing', 'heating', 'boiler', 'emergency', 'repair', 'installation']
        electrical_keywords = ['electrical', 'electrician', 'wiring', 'testing', 'safety']
        
        plumbing_count = sum(content.lower().count(keyword) for keyword in plumbing_keywords)
        electrical_count = sum(content.lower().count(keyword) for keyword in electrical_keywords)
        keyword_score = min((plumbing_count + electrical_count) * 1.5, 25)
        score += keyword_score
        
        # Contact information
        if '@' in content: score += 15
        if re.search(r'\b0[1-9]\d{8,9}\b', content): score += 15
        
        # Structure elements
        if '<h1' in content: score += 10
        if 'contact' in content.lower(): score += 10
        
        return min(score, 100)

    async def test_single_url(self, url: str, index: int) -> Dict[str, Any]:
        """Comprehensive test of single URL"""
        print(f"\n🧪 Testing URL {index+1}/9: {url}")
        
        try:
            company_name = self.extract_company_name(url)
            print(f"   📝 Company: {company_name}")
            
            # Fetch content
            content_result = await self.fetch_website_content(url)
            if content_result["status"] != "success":
                return {
                    "url": url, "company_name": company_name, "status": "error",
                    "error": content_result.get("error", "Unknown error")
                }
            
            content = content_result["content"]
            print(f"   📄 Content: {len(content)} chars")
            
            # Comprehensive analysis
            contacts = self.extract_comprehensive_contacts(content)
            seo_analysis = self.analyze_enhanced_seo(content, url)
            
            print(f"   👥 Executives: {len(contacts['executives'])}")
            print(f"   📞 Contacts: {len(contacts['emails'])} emails, {len(contacts['phones'])} phones")
            print(f"   📊 SEO Score: {seo_analysis['content_quality_score']}")
            
            return {
                "url": url,
                "company_name": company_name,
                "status": "success",
                "contact_extraction": {
                    "emails": contacts["emails"],
                    "phones": contacts["phones"],
                    "executives": contacts["executives"],
                    "attribution": contacts["contact_attribution"]
                },
                "seo_analysis": seo_analysis,
                "business_intelligence": {
                    "decision_makers_identified": sum(1 for exec in contacts["executives"] 
                                                    if any(title in exec["title"].lower() 
                                                          for title in ["ceo", "director", "owner", "founder"])),
                    "contact_completeness": len(contacts["emails"]) + len(contacts["phones"]),
                    "executive_coverage": len(contacts["executives"]),
                    "attribution_confidence": contacts["contact_attribution"]["attribution_confidence"]
                },
                "processing_time": 0.0
            }
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return {"url": url, "company_name": company_name, "status": "error", "error": str(e)}

    async def run_comprehensive_test(self):
        """Run comprehensive test on all 9 URLs"""
        print("🚀 COMPREHENSIVE 9 URLs LATEST SYSTEM TEST")
        print("=" * 80)
        
        start_time = datetime.now()
        
        for i, url in enumerate(self.test_urls):
            url_start = datetime.now()
            result = await self.test_single_url(url, i)
            url_end = datetime.now()
            
            result['processing_time'] = (url_end - url_start).total_seconds()
            self.results["companies"].append(result)
        
        self._calculate_system_analytics()
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        successful = sum(1 for r in self.results["companies"] if r["status"] == "success")
        
        self.results["test_summary"] = {
            "total_processing_time": total_time,
            "average_time_per_url": total_time / len(self.test_urls),
            "successful_extractions": successful,
            "failed_extractions": len(self.test_urls) - successful,
            "success_rate": (successful / len(self.test_urls)) * 100
        }
        
        print(f"\n🎯 COMPREHENSIVE TEST COMPLETE")
        print(f"✅ Success: {successful}/9 URLs ({self.results['test_summary']['success_rate']:.1f}%)")
        print(f"⏱️ Time: {total_time:.2f}s (avg: {self.results['test_summary']['average_time_per_url']:.2f}s)")

    def _calculate_system_analytics(self):
        """Calculate comprehensive system analytics"""
        successful = [r for r in self.results["companies"] if r["status"] == "success"]
        if not successful: return
        
        total = len(successful)
        
        self.results["system_analytics"] = {
            "email_discovery_rate": (sum(1 for r in successful if r.get("contact_extraction", {}).get("emails")) / total) * 100,
            "phone_discovery_rate": (sum(1 for r in successful if r.get("contact_extraction", {}).get("phones")) / total) * 100,
            "executive_identification_rate": (sum(1 for r in successful if r.get("contact_extraction", {}).get("executives")) / total) * 100,
            "seo_analysis_success": (sum(1 for r in successful if r.get("seo_analysis", {}).get("content_quality_score", 0) > 50) / total) * 100,
            "contact_attribution_accuracy": sum(r.get("business_intelligence", {}).get("attribution_confidence", 0) for r in successful) / total * 100
        }

    def save_results(self, filename: str = None):
        """Save comprehensive results to JSON"""
        if filename is None:
            timestamp = int(datetime.now().timestamp())
            filename = f"comprehensive_9_url_latest_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Results saved to: {filename}")
        return filename

async def main():
    """Main execution"""
    test = Comprehensive9URLTest()
    
    try:
        await test.run_comprehensive_test()
        filename = test.save_results()
        
        print("\n🎯 SYSTEM ANALYTICS:")
        analytics = test.results["system_analytics"]
        print(f"   Email Discovery: {analytics['email_discovery_rate']:.1f}%")
        print(f"   Phone Discovery: {analytics['phone_discovery_rate']:.1f}%") 
        print(f"   Executive Identification: {analytics['executive_identification_rate']:.1f}%")
        print(f"   SEO Analysis Success: {analytics['seo_analysis_success']:.1f}%")
        print(f"   Contact Attribution Accuracy: {analytics['contact_attribution_accuracy']:.1f}%")
        
        print(f"\n✅ Complete results: {filename}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 