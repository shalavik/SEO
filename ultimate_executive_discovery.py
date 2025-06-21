import asyncio
import json
import time
import sys
import os
import random
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright
import requests
from dataclasses import dataclass
import logging

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from seo_leads.models import ExecutiveContact

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UltimateExecutiveDiscovery:
    """Ultimate executive discovery system with real results"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Multiple search engines to avoid blocks
        self.search_engines = [
            'https://www.bing.com/search?q={}',
            'https://search.yahoo.com/search?p={}',
            'https://www.startpage.com/sp/search?query={}',
            'https://searx.org/search?q={}',
        ]
        
        # Executive patterns for UK businesses
        self.executive_patterns = [
            r'(?i)(CEO|Managing Director|Director|Owner|Founder|Manager|Principal)\s*:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'(?i)([A-Z][a-z]+\s+[A-Z][a-z]+)\s*[-,]?\s*(CEO|Managing Director|Director|Owner|Founder|Manager)',
            r'(?i)Contact\s*:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'(?i)Speak\s+to\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'(?i)([A-Z][a-z]+\s+[A-Z][a-z]+)\s*is\s*the\s*(owner|director|manager)',
            r'(?i)Mr\.?\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'(?i)Mrs\.?\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        ]
        
        # Email patterns
        self.email_patterns = [
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        ]
        
        # Phone patterns for UK
        self.phone_patterns = [
            r'(\+44\s?\d{2,4}\s?\d{3,4}\s?\d{3,4})',
            r'(0\d{2,4}\s?\d{3,4}\s?\d{3,4})',
            r'(\d{5}\s?\d{6})',
        ]

    async def discover_executives_ultimate(self, company_name: str, website_url: str) -> List[ExecutiveContact]:
        """Ultimate executive discovery with real results"""
        print(f"\n🎯 ULTIMATE Executive Discovery for: {company_name}")
        print(f"🌐 Website: {website_url}")
        
        all_executives = []
        domain = urlparse(website_url).netloc.replace('www.', '')
        
        # Strategy 1: Deep Website Scraping with Playwright
        print("\n🔍 Strategy 1: Deep Website Scraping")
        website_executives = await self._deep_website_scraping(website_url, company_name)
        all_executives.extend(website_executives)
        print(f"   ✅ Found {len(website_executives)} executives from website")
        
        # Strategy 2: Multi-Engine Search
        print("\n🔎 Strategy 2: Multi-Engine Search")
        search_executives = await self._multi_engine_search(company_name, domain)
        all_executives.extend(search_executives)
        print(f"   ✅ Found {len(search_executives)} executives from search engines")
        
        # Strategy 3: Social Media Deep Dive
        print("\n📱 Strategy 3: Social Media Deep Dive")
        social_executives = await self._social_media_deep_dive(company_name, domain)
        all_executives.extend(social_executives)
        print(f"   ✅ Found {len(social_executives)} executives from social media")
        
        # Strategy 4: Business Registry Mining
        print("\n🏛️ Strategy 4: Business Registry Mining")
        registry_executives = await self._business_registry_mining(company_name, domain)
        all_executives.extend(registry_executives)
        print(f"   ✅ Found {len(registry_executives)} executives from registries")
        
        # Strategy 5: Contact Information Analysis
        print("\n📞 Strategy 5: Contact Information Analysis")
        contact_executives = await self._contact_analysis(website_url, company_name)
        all_executives.extend(contact_executives)
        print(f"   ✅ Found {len(contact_executives)} executives from contact analysis")
        
        # Merge and enhance
        unique_executives = self._merge_and_enhance(all_executives, domain)
        
        print(f"\n🎉 TOTAL REAL EXECUTIVES DISCOVERED: {len(unique_executives)}")
        return unique_executives

    async def _deep_website_scraping(self, website_url: str, company_name: str) -> List[ExecutiveContact]:
        """Deep website scraping with advanced techniques"""
        executives = []
        
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                # Comprehensive page list
                pages_to_check = [
                    website_url,
                    urljoin(website_url, '/about'),
                    urljoin(website_url, '/about-us'),
                    urljoin(website_url, '/team'),
                    urljoin(website_url, '/our-team'),
                    urljoin(website_url, '/staff'),
                    urljoin(website_url, '/management'),
                    urljoin(website_url, '/leadership'),
                    urljoin(website_url, '/directors'),
                    urljoin(website_url, '/contact'),
                    urljoin(website_url, '/contact-us'),
                    urljoin(website_url, '/meet-the-team'),
                    urljoin(website_url, '/who-we-are'),
                    urljoin(website_url, '/our-people'),
                    urljoin(website_url, '/company'),
                ]
                
                for page_url in pages_to_check:
                    try:
                        print(f"     📄 Scraping: {page_url}")
                        
                        await page.goto(page_url, wait_until='domcontentloaded', timeout=30000)
                        await page.wait_for_timeout(2000)  # Wait for dynamic content
                        
                        # Get both text content and HTML
                        text_content = await page.inner_text('body')
                        html_content = await page.content()
                        
                        # Extract executives from both
                        text_executives = self._extract_executives_from_text(text_content, company_name, page_url)
                        html_executives = self._extract_executives_from_html(html_content, company_name, page_url)
                        
                        executives.extend(text_executives)
                        executives.extend(html_executives)
                        
                        # Look for specific executive sections
                        executive_sections = await page.query_selector_all('[class*="team"], [class*="staff"], [class*="about"], [id*="team"], [id*="staff"]')
                        for section in executive_sections:
                            section_text = await section.inner_text()
                            section_executives = self._extract_executives_from_text(section_text, company_name, page_url)
                            executives.extend(section_executives)
                        
                        await asyncio.sleep(1)  # Be respectful
                        
                    except Exception as e:
                        print(f"       ⚠️ Failed to scrape {page_url}: {str(e)[:50]}...")
                        continue
                
                await browser.close()
                
        except Exception as e:
            print(f"   ❌ Website scraping failed: {e}")
            
        return executives

    def _extract_executives_from_text(self, content: str, company_name: str, source_url: str) -> List[ExecutiveContact]:
        """Extract executives from text content"""
        executives = []
        
        for pattern in self.executive_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) >= 2:
                        # Determine which is name and which is title
                        part1, part2 = match[0], match[1]
                        if any(title_word in part1.lower() for title_word in ['ceo', 'director', 'manager', 'owner']):
                            title, name = part1, part2
                        else:
                            name, title = part1, part2
                    else:
                        name = match[0]
                        title = "Executive"
                else:
                    name = match
                    title = "Executive"
                
                # Validate and create executive
                if self._is_valid_executive_name(name):
                    executive = self._create_executive(name, title, company_name, source_url)
                    executives.append(executive)
        
        return executives

    def _extract_executives_from_html(self, html_content: str, company_name: str, source_url: str) -> List[ExecutiveContact]:
        """Extract executives from HTML structure"""
        executives = []
        
        # Look for structured data
        structured_patterns = [
            r'<[^>]*class="[^"]*(?:team|staff|executive|director)[^"]*"[^>]*>([^<]+)</[^>]*>',
            r'<h[1-6][^>]*>([^<]*(?:CEO|Director|Manager|Owner)[^<]*)</h[1-6]>',
            r'<span[^>]*>([^<]*(?:CEO|Director|Manager|Owner)[^<]*)</span>',
        ]
        
        for pattern in structured_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                # Extract name and title from structured content
                text = match.strip()
                if self._contains_executive_info(text):
                    name, title = self._parse_executive_text(text)
                    if name and self._is_valid_executive_name(name):
                        executive = self._create_executive(name, title, company_name, source_url)
                        executives.append(executive)
        
        return executives

    async def _multi_engine_search(self, company_name: str, domain: str) -> List[ExecutiveContact]:
        """Search multiple engines for executive information"""
        executives = []
        
        search_queries = [
            f'"{company_name}" CEO director owner',
            f'"{company_name}" management team',
            f'"{domain}" director owner',
            f'"{company_name}" "managing director"',
            f'"{company_name}" founder owner',
        ]
        
        for query in search_queries:
            for engine_url in self.search_engines:
                try:
                    print(f"     🔍 Searching: {engine_url.split('/')[2]} for '{query[:30]}...'")
                    
                    search_url = engine_url.format(requests.utils.quote(query))
                    
                    response = self.session.get(search_url, timeout=15)
                    if response.status_code == 200:
                        search_executives = self._extract_executives_from_search_results(
                            response.text, company_name, search_url
                        )
                        executives.extend(search_executives)
                    
                    await asyncio.sleep(random.uniform(2, 5))  # Rate limiting
                    
                except Exception as e:
                    print(f"       ⚠️ Search failed: {str(e)[:50]}...")
                    continue
        
        return executives

    async def _social_media_deep_dive(self, company_name: str, domain: str) -> List[ExecutiveContact]:
        """Deep dive into social media for executives"""
        executives = []
        
        # LinkedIn company page search
        linkedin_queries = [
            f'site:linkedin.com/company "{company_name}"',
            f'site:linkedin.com/in "{company_name}" director',
            f'site:linkedin.com/in "{domain}" CEO',
        ]
        
        for query in linkedin_queries:
            try:
                # Use Bing for LinkedIn searches (less blocking)
                search_url = f'https://www.bing.com/search?q={requests.utils.quote(query)}'
                response = self.session.get(search_url, timeout=15)
                
                if response.status_code == 200:
                    linkedin_executives = self._extract_linkedin_executives(response.text, company_name)
                    executives.extend(linkedin_executives)
                
                await asyncio.sleep(random.uniform(3, 6))
                
            except Exception as e:
                print(f"       ⚠️ LinkedIn search failed: {e}")
                continue
        
        return executives

    async def _business_registry_mining(self, company_name: str, domain: str) -> List[ExecutiveContact]:
        """Mine business registries for executive information"""
        executives = []
        
        # UK business directories
        directory_searches = [
            f'site:companieshouse.gov.uk "{company_name}"',
            f'site:yell.com "{company_name}" director',
            f'site:thomsonlocal.com "{company_name}" owner',
            f'site:freeindex.co.uk "{company_name}" contact',
        ]
        
        for query in directory_searches:
            try:
                search_url = f'https://www.bing.com/search?q={requests.utils.quote(query)}'
                response = self.session.get(search_url, timeout=15)
                
                if response.status_code == 200:
                    directory_executives = self._extract_directory_executives(response.text, company_name)
                    executives.extend(directory_executives)
                
                await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"       ⚠️ Directory search failed: {e}")
                continue
        
        return executives

    async def _contact_analysis(self, website_url: str, company_name: str) -> List[ExecutiveContact]:
        """Analyze contact information for executive details"""
        executives = []
        
        try:
            # Get website content
            response = self.session.get(website_url, timeout=15)
            if response.status_code == 200:
                content = response.text
                
                # Extract emails and try to identify executives
                emails = re.findall(self.email_patterns[0], content)
                for email in emails:
                    if not any(skip in email.lower() for skip in ['info', 'admin', 'support', 'sales', 'contact', 'enquiries']):
                        # Try to generate name from email
                        name = self._generate_name_from_email(email)
                        if name:
                            executive = self._create_executive(name, "Contact Person", company_name, website_url)
                            executive.email = email
                            executive.email_confidence = 0.8
                            executives.append(executive)
                
                # Extract phone numbers and search for associated names
                phones = []
                for pattern in self.phone_patterns:
                    phones.extend(re.findall(pattern, content))
                
                for phone in phones:
                    # Search for names near phone numbers
                    phone_context = self._get_phone_context(content, phone)
                    names = self._extract_names_from_context(phone_context)
                    for name in names:
                        if self._is_valid_executive_name(name):
                            executive = self._create_executive(name, "Contact Person", company_name, website_url)
                            executive.phone = phone
                            executive.phone_confidence = 0.7
                            executives.append(executive)
        
        except Exception as e:
            print(f"   ⚠️ Contact analysis failed: {e}")
        
        return executives

    def _merge_and_enhance(self, executives: List[ExecutiveContact], domain: str) -> List[ExecutiveContact]:
        """Merge duplicates and enhance with additional information"""
        if not executives:
            return []
        
        # Group by similar names
        groups = {}
        for exec in executives:
            key = exec.full_name.lower().replace(" ", "").replace(".", "")
            if key not in groups:
                groups[key] = []
            groups[key].append(exec)
        
        # Merge each group
        merged = []
        for group in groups.values():
            if len(group) == 1:
                enhanced = self._enhance_executive(group[0], domain)
                merged.append(enhanced)
            else:
                # Merge multiple executives with same name
                best_exec = max(group, key=lambda x: x.overall_confidence)
                
                # Combine information from all sources
                all_sources = []
                for exec in group:
                    all_sources.extend(exec.discovery_sources)
                    if exec.email and not best_exec.email:
                        best_exec.email = exec.email
                        best_exec.email_confidence = exec.email_confidence
                    if exec.phone and not best_exec.phone:
                        best_exec.phone = exec.phone
                        best_exec.phone_confidence = exec.phone_confidence
                
                best_exec.discovery_sources = list(set(all_sources))
                best_exec.overall_confidence = min(0.95, best_exec.overall_confidence + 0.1 * (len(group) - 1))
                
                enhanced = self._enhance_executive(best_exec, domain)
                merged.append(enhanced)
        
        # Sort by confidence
        merged.sort(key=lambda x: x.overall_confidence, reverse=True)
        
        return merged

    def _enhance_executive(self, executive: ExecutiveContact, domain: str) -> ExecutiveContact:
        """Enhance executive with additional information"""
        # Generate email if not present
        if not executive.email:
            generated_email = self._generate_executive_email(executive.full_name, domain)
            if generated_email:
                executive.email = generated_email
                executive.email_confidence = 0.6
        
        # Enhance title if generic
        if executive.title in ["Executive", "Contact Person"]:
            enhanced_title = self._infer_title_from_context(executive)
            if enhanced_title:
                executive.title = enhanced_title
        
        # Set seniority tier
        executive.seniority_tier = self._determine_seniority_tier(executive.title)
        
        return executive

    # Helper methods
    def _is_valid_executive_name(self, name: str) -> bool:
        """Check if name looks like a real person"""
        if not name or len(name) < 3:
            return False
        
        # Remove business words
        business_words = ['ltd', 'limited', 'company', 'services', 'plumbing', 'heating']
        name_lower = name.lower()
        for word in business_words:
            if word in name_lower:
                return False
        
        # Must have at least first and last name
        parts = name.split()
        if len(parts) < 2:
            return False
        
        # Check for valid name pattern
        return re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+', name) is not None

    def _create_executive(self, name: str, title: str, company_name: str, source_url: str) -> ExecutiveContact:
        """Create ExecutiveContact object"""
        parts = name.split()
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        return ExecutiveContact(
            first_name=first_name,
            last_name=last_name,
            full_name=name,
            title=title,
            company_name=company_name,
            company_domain=urlparse(source_url).netloc,
            discovery_sources=[source_url],
            discovery_method="ultimate_discovery",
            overall_confidence=0.8,
            extracted_at=datetime.utcnow()
        )

    def _contains_executive_info(self, text: str) -> bool:
        """Check if text contains executive information"""
        executive_keywords = ['ceo', 'director', 'manager', 'owner', 'founder', 'principal']
        return any(keyword in text.lower() for keyword in executive_keywords)

    def _parse_executive_text(self, text: str) -> tuple:
        """Parse executive name and title from text"""
        # Simple parsing - can be enhanced
        if '-' in text:
            parts = text.split('-')
            return parts[0].strip(), parts[1].strip()
        elif ',' in text:
            parts = text.split(',')
            return parts[0].strip(), parts[1].strip()
        else:
            return text.strip(), "Executive"

    def _extract_executives_from_search_results(self, html: str, company_name: str, source_url: str) -> List[ExecutiveContact]:
        """Extract executives from search results"""
        executives = []
        
        # Look for executive mentions in search snippets
        for pattern in self.executive_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    name, title = match[0], match[1]
                    if self._is_valid_executive_name(name):
                        executive = self._create_executive(name, title, company_name, source_url)
                        executives.append(executive)
        
        return executives

    def _extract_linkedin_executives(self, html: str, company_name: str) -> List[ExecutiveContact]:
        """Extract executives from LinkedIn search results"""
        executives = []
        
        # LinkedIn-specific patterns
        linkedin_patterns = [
            r'linkedin\.com/in/([^"]+)"[^>]*>([^<]+)</a>',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)[^<]*(?:CEO|Director|Manager)',
        ]
        
        for pattern in linkedin_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                if isinstance(match, tuple):
                    name = match[1] if len(match) > 1 else match[0]
                    if self._is_valid_executive_name(name):
                        executive = self._create_executive(name, "LinkedIn Executive", company_name, "linkedin.com")
                        executives.append(executive)
        
        return executives

    def _extract_directory_executives(self, html: str, company_name: str) -> List[ExecutiveContact]:
        """Extract executives from directory search results"""
        executives = []
        
        # Directory-specific patterns
        for pattern in self.executive_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    name, title = match[0], match[1]
                    if self._is_valid_executive_name(name):
                        executive = self._create_executive(name, title, company_name, "business_directory")
                        executives.append(executive)
        
        return executives

    def _generate_name_from_email(self, email: str) -> Optional[str]:
        """Generate likely name from email address"""
        local_part = email.split('@')[0]
        
        # Handle common patterns
        if '.' in local_part:
            parts = local_part.split('.')
            if len(parts) == 2:
                first, last = parts
                return f"{first.capitalize()} {last.capitalize()}"
        
        # Handle firstname.lastname patterns
        if len(local_part) > 3:
            return local_part.capitalize()
        
        return None

    def _get_phone_context(self, content: str, phone: str) -> str:
        """Get context around phone number"""
        phone_index = content.find(phone)
        if phone_index != -1:
            start = max(0, phone_index - 100)
            end = min(len(content), phone_index + 100)
            return content[start:end]
        return ""

    def _extract_names_from_context(self, context: str) -> List[str]:
        """Extract names from context"""
        names = []
        name_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
        matches = re.findall(name_pattern, context)
        for match in matches:
            if self._is_valid_executive_name(match):
                names.append(match)
        return names

    def _generate_executive_email(self, name: str, domain: str) -> Optional[str]:
        """Generate likely email for executive"""
        parts = name.lower().split()
        if len(parts) >= 2:
            first, last = parts[0], parts[-1]
            patterns = [
                f"{first}.{last}@{domain}",
                f"{first}@{domain}",
                f"{first[0]}{last}@{domain}",
            ]
            return patterns[0]  # Return most likely pattern
        return None

    def _infer_title_from_context(self, executive: ExecutiveContact) -> Optional[str]:
        """Infer title from context"""
        # Simple inference based on common patterns
        if "owner" in executive.discovery_sources[0].lower():
            return "Owner"
        elif "director" in executive.discovery_sources[0].lower():
            return "Director"
        elif "manager" in executive.discovery_sources[0].lower():
            return "Manager"
        return None

    def _determine_seniority_tier(self, title: str) -> str:
        """Determine seniority tier from title"""
        title_lower = title.lower()
        if any(word in title_lower for word in ['ceo', 'managing director', 'founder', 'owner']):
            return "tier_1"
        elif any(word in title_lower for word in ['director', 'head', 'principal']):
            return "tier_2"
        else:
            return "tier_3"


# Test function
async def test_ultimate_discovery():
    """Test the ultimate discovery system"""
    print("🚀 ULTIMATE EXECUTIVE DISCOVERY SYSTEM")
    print("=" * 60)
    
    test_companies = [
        {
            "name": "Expert In Heating & Plumbing In Birmingham",
            "url": "https://macplumbheat.co.uk/"
        },
        {
            "name": "LTF Plumbing",
            "url": "https://ltfplumbing.co.uk/"
        },
    ]
    
    discovery = UltimateExecutiveDiscovery()
    all_results = []
    
    for company in test_companies:
        print(f"\n{'='*60}")
        print(f"🏢 Company: {company['name']}")
        print(f"🌐 Website: {company['url']}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            executives = await discovery.discover_executives_ultimate(
                company['name'], 
                company['url']
            )
            
            processing_time = time.time() - start_time
            
            result = {
                "company": company['name'],
                "url": company['url'],
                "executives_found": len(executives),
                "processing_time": round(processing_time, 2),
                "executives": []
            }
            
            print(f"\n🎉 DISCOVERY COMPLETE!")
            print(f"⏱️  Processing time: {processing_time:.2f}s")
            print(f"👥 Executives found: {len(executives)}")
            print(f"\n📋 EXECUTIVE DETAILS:")
            
            for i, exec in enumerate(executives, 1):
                exec_data = {
                    "name": exec.full_name,
                    "title": exec.title,
                    "email": exec.email,
                    "phone": exec.phone,
                    "confidence": exec.overall_confidence,
                    "sources": len(exec.discovery_sources),
                    "seniority": exec.seniority_tier
                }
                result["executives"].append(exec_data)
                
                print(f"\n   {i}. 👤 {exec.full_name}")
                print(f"      🏷️  Title: {exec.title}")
                print(f"      📧 Email: {exec.email or 'Not found'}")
                print(f"      📞 Phone: {exec.phone or 'Not found'}")
                print(f"      🎯 Confidence: {exec.overall_confidence:.2f}")
                print(f"      📍 Sources: {len(exec.discovery_sources)}")
                print(f"      ⭐ Seniority: {exec.seniority_tier}")
            
            all_results.append(result)
            
        except Exception as e:
            print(f"❌ Discovery failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Save results
    timestamp = int(time.time())
    filename = f"ultimate_executive_discovery_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")
    
    # Final summary
    total_executives = sum(r['executives_found'] for r in all_results)
    avg_time = sum(r['processing_time'] for r in all_results) / len(all_results) if all_results else 0
    
    print(f"\n🏆 FINAL SUMMARY:")
    print(f"Companies processed: {len(all_results)}")
    print(f"Total real executives found: {total_executives}")
    print(f"Average processing time: {avg_time:.2f}s")
    print(f"Average executives per company: {total_executives / len(all_results) if all_results else 0:.1f}")
    
    return all_results

if __name__ == "__main__":
    asyncio.run(test_ultimate_discovery()) 