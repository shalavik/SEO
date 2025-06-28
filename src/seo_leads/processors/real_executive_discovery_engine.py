"""
Real Executive Discovery Engine - Phase 4A Implementation

This module implements the core solution to the critical fake data generation issue.
It extracts real executive names, titles, and contact information from website content
using proven web scraping techniques from BeautifulSoup, Selenium, and requests.

Key Features:
- Real website content extraction (no fake generation)
- Multi-page analysis (About, Team, Contact, Staff directories)
- Executive name validation against real name patterns
- Business title extraction and standardization
- Phone number and email discovery
- LinkedIn profile detection
- SEO analysis integration

Target Metrics:
- 80%+ real executive discovery (vs current 0%)
- 0% fake generation (vs current 100%)
- Real name accuracy improvement
- Contact attribution from website content
"""

import re
import time
import logging
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
import json

# Web scraping imports based on Context7 documentation
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Core imports
from ..models import Executive, ContactInfo, BusinessContext
from ..ai.advanced_name_validator import AdvancedNameValidator
from ..analyzers.seo_analyzer import SEOAnalyzer


@dataclass
class ExecutiveDiscoveryResult:
    """Result of executive discovery from website content"""
    executives: List[Executive] = field(default_factory=list)
    pages_analyzed: List[str] = field(default_factory=list)
    extraction_method: str = ""
    confidence_score: float = 0.0
    processing_time: float = 0.0
    content_quality: str = "unknown"
    seo_analysis: Optional[Dict] = None
    business_context: Optional[BusinessContext] = None


@dataclass
class ExecutiveCandidate:
    """Candidate executive found during content analysis"""
    full_name: str
    first_name: str = ""
    last_name: str = ""
    title: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    context: str = ""
    source_page: str = ""
    confidence: float = 0.0
    extraction_patterns: List[str] = field(default_factory=list)


class WebsiteContentAnalyzer:
    """Extract real executive information from website content using proven techniques"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.name_validator = AdvancedNameValidator()
        self.seo_analyzer = SEOAnalyzer()
        
        # Initialize requests session with proper headers (Context7 best practices)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Chrome options for Selenium (Context7 headless configuration)
        self.chrome_options = ChromeOptions()
        self.chrome_options.add_argument("--headless=new")  # Context7 recommended headless
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        
        # Executive title patterns for business context
        self.executive_titles = {
            'c_level': ['CEO', 'CFO', 'CTO', 'COO', 'CMO', 'Chief Executive', 'Chief Financial', 'Chief Technology', 'Chief Operating'],
            'ownership': ['Owner', 'Founder', 'Co-Founder', 'Partner', 'Principal'],
            'management': ['President', 'Vice President', 'VP', 'Managing Director', 'General Manager', 'Director'],
            'operations': ['Operations Manager', 'Service Manager', 'Project Manager', 'Account Manager']
        }
        
        # Real name patterns (avoiding service terms)
        self.service_terms = {
            'hvac': ['heating', 'cooling', 'air', 'hvac', 'plumbing', 'electrical', 'service', 'repair', 'maintenance'],
            'business': ['company', 'business', 'services', 'solutions', 'systems', 'enterprises', 'group']
        }

    def analyze_website_content(self, url: str) -> ExecutiveDiscoveryResult:
        """
        Main method to analyze website content for real executives
        Uses Context7 documented approaches for content extraction
        """
        start_time = time.time()
        result = ExecutiveDiscoveryResult()
        
        try:
            self.logger.info(f"Starting real executive discovery for: {url}")
            
            # Step 1: Discover all relevant pages
            pages_to_analyze = self._discover_relevant_pages(url)
            result.pages_analyzed = pages_to_analyze
            
            # Step 2: Extract content using multiple methods
            all_candidates = []
            
            for page_url in pages_to_analyze:
                # Try BeautifulSoup first (faster, Context7 documented)
                candidates = self._extract_with_beautifulsoup(page_url)
                all_candidates.extend(candidates)
                
                # Use Selenium for JavaScript-heavy content if needed
                if not candidates:
                    candidates = self._extract_with_selenium(page_url)
                    all_candidates.extend(candidates)
            
            # Step 3: Validate and filter real executives
            validated_executives = self._validate_and_convert_candidates(all_candidates)
            result.executives = validated_executives
            
            # Step 4: Enrich with contact information
            enriched_executives = self._enrich_contact_information(validated_executives, pages_to_analyze)
            result.executives = enriched_executives
            
            # Step 5: SEO analysis integration (addressing missing component)
            result.seo_analysis = self._integrate_seo_analysis(url)
            
            # Step 6: Business context extraction
            result.business_context = self._extract_business_context(url, pages_to_analyze)
            
            # Calculate final metrics
            result.processing_time = time.time() - start_time
            result.confidence_score = self._calculate_discovery_confidence(result)
            result.extraction_method = "real_content_analysis"
            result.content_quality = self._assess_content_quality(all_candidates)
            
            self.logger.info(f"Discovered {len(result.executives)} real executives in {result.processing_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Error in executive discovery: {str(e)}")
            result.processing_time = time.time() - start_time
            
        return result

    def _discover_relevant_pages(self, base_url: str) -> List[str]:
        """Discover pages likely to contain executive information"""
        pages = [base_url]  # Always analyze main page
        
        try:
            # Get main page content to find relevant links
            response = self.session.get(base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find links to relevant pages (Context7 BeautifulSoup techniques)
            relevant_patterns = [
                'about', 'team', 'staff', 'leadership', 'management', 'contact',
                'executives', 'directors', 'officers', 'founder', 'owner', 'who-we-are'
            ]
            
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').lower()
                link_text = link.get_text().lower()
                
                for pattern in relevant_patterns:
                    if pattern in href or pattern in link_text:
                        full_url = urljoin(base_url, link['href'])
                        if full_url not in pages and self._is_same_domain(base_url, full_url):
                            pages.append(full_url)
                            break
            
            # Limit to top 5 most relevant pages for performance
            return pages[:5]
            
        except Exception as e:
            self.logger.warning(f"Error discovering pages: {str(e)}")
            return [base_url]

    def _extract_with_beautifulsoup(self, url: str) -> List[ExecutiveCandidate]:
        """Extract executives using BeautifulSoup (Context7 documented approach)"""
        candidates = []
        
        try:
            # Make request with proper headers (Context7 best practices)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse with BeautifulSoup (Context7 documentation)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements (clean content)
            for element in soup(["script", "style"]):
                element.decompose()
            
            # Extract text content (Context7 get_text method)
            text_content = soup.get_text()
            
            # Find executive patterns in structured content
            candidates.extend(self._find_executives_in_structured_content(soup, url))
            
            # Find executives in text content
            candidates.extend(self._find_executives_in_text_content(text_content, url))
            
            self.logger.debug(f"BeautifulSoup extracted {len(candidates)} candidates from {url}")
            
        except Exception as e:
            self.logger.warning(f"BeautifulSoup extraction failed for {url}: {str(e)}")
            
        return candidates

    def _extract_with_selenium(self, url: str) -> List[ExecutiveCandidate]:
        """Extract executives using Selenium for JavaScript content (Context7 documented)"""
        candidates = []
        driver = None
        
        try:
            # Initialize Chrome driver with Context7 recommended options
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.set_page_load_timeout(15)
            
            # Navigate to page (Context7 navigation method)
            driver.get(url)
            
            # Wait for content to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get page source after JavaScript execution
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract using same methods as BeautifulSoup
            candidates.extend(self._find_executives_in_structured_content(soup, url))
            
            text_content = soup.get_text()
            candidates.extend(self._find_executives_in_text_content(text_content, url))
            
            self.logger.debug(f"Selenium extracted {len(candidates)} candidates from {url}")
            
        except Exception as e:
            self.logger.warning(f"Selenium extraction failed for {url}: {str(e)}")
            
        finally:
            if driver:
                driver.quit()
                
        return candidates

    def _find_executives_in_structured_content(self, soup: BeautifulSoup, url: str) -> List[ExecutiveCandidate]:
        """Find executives in structured HTML content (Context7 find_all techniques)"""
        candidates = []
        
        # Look for common structural patterns
        patterns = [
            # Team/staff sections
            {'tag': 'div', 'class_': re.compile(r'team|staff|about|bio', re.I)},
            {'tag': 'section', 'class_': re.compile(r'team|staff|leadership', re.I)},
            # Contact information
            {'tag': 'div', 'class_': re.compile(r'contact|person|member', re.I)},
            # Profile sections
            {'tag': 'article', 'class_': re.compile(r'profile|bio|person', re.I)},
        ]
        
        for pattern in patterns:
            elements = soup.find_all(pattern['tag'], class_=pattern.get('class_'))
            
            for element in elements:
                candidate = self._extract_executive_from_element(element, url)
                if candidate:
                    candidates.append(candidate)
        
        return candidates

    def _find_executives_in_text_content(self, text: str, url: str) -> List[ExecutiveCandidate]:
        """Find executives in plain text content using pattern matching"""
        candidates = []
        
        # Pattern for "Name - Title" or "Title: Name"
        patterns = [
            r'([A-Z][a-z]+ [A-Z][a-z]+)\s*[-–]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):?\s*([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+),?\s+(CEO|Owner|President|Manager|Director)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                name = match.group(1).strip()
                title = match.group(2).strip()
                
                if self._is_valid_executive_name(name):
                    candidate = ExecutiveCandidate(
                        full_name=name,
                        title=title,
                        source_page=url,
                        context=match.group(0),
                        extraction_patterns=['text_pattern_match']
                    )
                    candidates.append(candidate)
        
        return candidates

    def _extract_executive_from_element(self, element, url: str) -> Optional[ExecutiveCandidate]:
        """Extract executive information from HTML element"""
        try:
            text = element.get_text(' ', strip=True)
            
            # Look for name patterns in element text
            name_patterns = [
                r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b',
                r'\b([A-Z]\. [A-Z][a-z]+)\b',
            ]
            
            for pattern in name_patterns:
                matches = re.findall(pattern, text)
                for name in matches:
                    if self._is_valid_executive_name(name):
                        # Look for title in same element
                        title = self._extract_title_from_text(text)
                        
                        candidate = ExecutiveCandidate(
                            full_name=name,
                            title=title,
                            source_page=url,
                            context=text[:200],
                            extraction_patterns=['structured_element']
                        )
                        return candidate
                        
        except Exception as e:
            self.logger.debug(f"Error extracting from element: {str(e)}")
            
        return None

    def _is_valid_executive_name(self, name: str) -> bool:
        """Validate that name is a real person, not a service term"""
        if not name or len(name.split()) < 2:
            return False
            
        name_lower = name.lower()
        
        # Check against service terms (avoid fake names like "Heating Service")
        for category, terms in self.service_terms.items():
            for term in terms:
                if term in name_lower:
                    return False
        
        # Use advanced name validator for real name patterns
        return self.name_validator.validate_name_pattern(name)

    def _extract_title_from_text(self, text: str) -> str:
        """Extract business title from text content"""
        text_lower = text.lower()
        
        for category, titles in self.executive_titles.items():
            for title in titles:
                if title.lower() in text_lower:
                    return title
                    
        return ""

    def _validate_and_convert_candidates(self, candidates: List[ExecutiveCandidate]) -> List[Executive]:
        """Convert validated candidates to Executive objects"""
        executives = []
        seen_names = set()
        
        for candidate in candidates:
            # Avoid duplicates
            name_key = candidate.full_name.lower().replace(' ', '')
            if name_key in seen_names:
                continue
                
            # Final validation using advanced name validator
            if self.name_validator.is_real_executive_name(candidate.full_name):
                seen_names.add(name_key)
                
                # Parse name parts
                name_parts = candidate.full_name.split()
                first_name = name_parts[0] if name_parts else ""
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                
                # Create Executive object
                executive = Executive(
                    first_name=first_name,
                    last_name=last_name,
                    full_name=candidate.full_name,
                    title=candidate.title,
                    contact_info=ContactInfo(
                        email=candidate.email,
                        phone=candidate.phone,
                        linkedin=candidate.linkedin
                    ),
                    confidence=candidate.confidence,
                    source="real_website_content"
                )
                
                executives.append(executive)
        
        return executives

    def _enrich_contact_information(self, executives: List[Executive], pages: List[str]) -> List[Executive]:
        """Enrich executives with contact information from website"""
        for executive in executives:
            for page_url in pages:
                try:
                    # Get page content
                    response = self.session.get(page_url, timeout=5)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract phone numbers
                    phone = self._extract_phone_numbers(soup, executive.full_name)
                    if phone and not executive.contact_info.phone:
                        executive.contact_info.phone = phone
                    
                    # Extract emails
                    email = self._extract_email_addresses(soup, executive.full_name)
                    if email and not executive.contact_info.email:
                        executive.contact_info.email = email
                    
                    # Extract LinkedIn
                    linkedin = self._extract_linkedin_profiles(soup, executive.full_name)
                    if linkedin and not executive.contact_info.linkedin:
                        executive.contact_info.linkedin = linkedin
                        
                except Exception as e:
                    self.logger.debug(f"Error enriching contact info: {str(e)}")
                    
        return executives

    def _extract_phone_numbers(self, soup: BeautifulSoup, executive_name: str) -> str:
        """Extract phone numbers from website content"""
        text = soup.get_text()
        
        # Phone number patterns
        phone_patterns = [
            r'\b(\d{3}[-.]?\d{3}[-.]?\d{4})\b',
            r'\b(\(\d{3}\)\s*\d{3}[-.]?\d{4})\b',
            r'\b(\d{3}\s\d{3}\s\d{4})\b'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]  # Return first found phone
                
        return ""

    def _extract_email_addresses(self, soup: BeautifulSoup, executive_name: str) -> str:
        """Extract email addresses from website content"""
        text = soup.get_text()
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        
        # Try to match email to executive name
        name_parts = executive_name.lower().split()
        for email in matches:
            email_lower = email.lower()
            for part in name_parts:
                if part in email_lower:
                    return email
                    
        # Return first email if no name match
        return matches[0] if matches else ""

    def _extract_linkedin_profiles(self, soup: BeautifulSoup, executive_name: str) -> str:
        """Extract LinkedIn profiles from website content"""
        # Look for LinkedIn links
        linkedin_links = soup.find_all('a', href=re.compile(r'linkedin\.com', re.I))
        
        for link in linkedin_links:
            href = link.get('href', '')
            if 'linkedin.com/in/' in href:
                return href
                
        return ""

    def _integrate_seo_analysis(self, url: str) -> Dict:
        """Integrate SEO analysis into discovery process"""
        try:
            seo_result = self.seo_analyzer.analyze_url(url)
            return {
                'seo_score': seo_result.get('overall_score', 0),
                'title_quality': seo_result.get('title_score', 0),
                'content_quality': seo_result.get('content_score', 0),
                'analysis_timestamp': time.time()
            }
        except Exception as e:
            self.logger.warning(f"SEO analysis failed: {str(e)}")
            return {}

    def _extract_business_context(self, url: str, pages: List[str]) -> BusinessContext:
        """Extract business context information"""
        context = BusinessContext()
        
        try:
            # Analyze main page for business context
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text().lower()
            
            # Determine business type
            if any(term in text for term in ['plumbing', 'plumber']):
                context.business_type = 'plumbing'
            elif any(term in text for term in ['heating', 'cooling', 'hvac']):
                context.business_type = 'hvac'
            elif any(term in text for term in ['electrical', 'electrician']):
                context.business_type = 'electrical'
            else:
                context.business_type = 'general_contractor'
            
            # Extract service areas
            location_patterns = [
                r'\b([A-Z][a-z]+,\s*[A-Z]{2})\b',
                r'\bserving\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
            ]
            
            for pattern in location_patterns:
                matches = re.findall(pattern, text, re.I)
                context.service_areas.extend(matches[:3])  # Limit to 3
                
        except Exception as e:
            self.logger.warning(f"Business context extraction failed: {str(e)}")
            
        return context

    def _calculate_discovery_confidence(self, result: ExecutiveDiscoveryResult) -> float:
        """Calculate confidence score for discovery results"""
        if not result.executives:
            return 0.0
            
        factors = {
            'executive_count': min(len(result.executives) / 3.0, 1.0) * 0.3,  # Up to 3 executives = full score
            'pages_analyzed': min(len(result.pages_analyzed) / 3.0, 1.0) * 0.2,  # 3+ pages = full score
            'contact_completeness': self._calculate_contact_completeness(result.executives) * 0.3,
            'name_quality': self._calculate_name_quality(result.executives) * 0.2
        }
        
        return sum(factors.values())

    def _calculate_contact_completeness(self, executives: List[Executive]) -> float:
        """Calculate contact information completeness"""
        if not executives:
            return 0.0
            
        total_contacts = 0
        for exec in executives:
            contacts = 0
            if exec.contact_info.email:
                contacts += 1
            if exec.contact_info.phone:
                contacts += 1
            if exec.contact_info.linkedin:
                contacts += 1
            total_contacts += contacts / 3.0  # Max 3 contact types
            
        return total_contacts / len(executives)

    def _calculate_name_quality(self, executives: List[Executive]) -> float:
        """Calculate name quality score"""
        if not executives:
            return 0.0
            
        quality_scores = []
        for exec in executives:
            score = self.name_validator.get_name_quality_score(exec.full_name)
            quality_scores.append(score)
            
        return sum(quality_scores) / len(quality_scores)

    def _assess_content_quality(self, candidates: List[ExecutiveCandidate]) -> str:
        """Assess the quality of extracted content"""
        if not candidates:
            return "poor"
        elif len(candidates) >= 3:
            return "excellent"
        elif len(candidates) >= 2:
            return "good"
        else:
            return "fair"

    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain"""
        try:
            domain1 = urlparse(url1).netloc.lower()
            domain2 = urlparse(url2).netloc.lower()
            return domain1 == domain2
        except:
            return False


class RealExecutiveDiscoveryEngine:
    """
    Main engine for real executive discovery - Phase 4A implementation
    Replaces fake data generation with real website content extraction
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.content_analyzer = WebsiteContentAnalyzer()
        
    def discover_real_executives(self, url: str) -> ExecutiveDiscoveryResult:
        """
        Discover real executives from website content
        
        This is the main method that implements Phase 4A requirements:
        - Replace fake generation with real content extraction
        - Find actual executives from website content
        - Validate names against real patterns
        - Extract business titles and contact information
        """
        self.logger.info(f"🔍 Starting REAL executive discovery for: {url}")
        self.logger.info("📋 Phase 4A: Real Executive Discovery Engine - NO FAKE GENERATION")
        
        try:
            # Analyze website content for real executives
            result = self.content_analyzer.analyze_website_content(url)
            
            # Log results for verification
            self._log_discovery_results(url, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Real executive discovery failed for {url}: {str(e)}")
            return ExecutiveDiscoveryResult()
    
    def _log_discovery_results(self, url: str, result: ExecutiveDiscoveryResult):
        """Log discovery results for validation"""
        self.logger.info(f"✅ Real Executive Discovery Complete for {url}")
        self.logger.info(f"📊 Results Summary:")
        self.logger.info(f"   • Real Executives Found: {len(result.executives)}")
        self.logger.info(f"   • Pages Analyzed: {len(result.pages_analyzed)}")
        self.logger.info(f"   • Processing Time: {result.processing_time:.2f}s")
        self.logger.info(f"   • Confidence Score: {result.confidence_score:.3f}")
        self.logger.info(f"   • Content Quality: {result.content_quality}")
        
        for i, executive in enumerate(result.executives, 1):
            self.logger.info(f"   {i}. {executive.full_name} - {executive.title}")
            if executive.contact_info.phone:
                self.logger.info(f"      📞 Phone: {executive.contact_info.phone}")
            if executive.contact_info.email:
                self.logger.info(f"      📧 Email: {executive.contact_info.email}")
            if executive.contact_info.linkedin:
                self.logger.info(f"      🔗 LinkedIn: {executive.contact_info.linkedin}")
        
        if not result.executives:
            self.logger.warning("⚠️  No real executives found - content may need manual review")
        else:
            self.logger.info("🎯 SUCCESS: Real executives discovered from website content")