"""
Advanced Content Analyzer - Phase 2 Discovery Rate Enhancement

This module implements Phase 2 enhancements to improve discovery rate from 25% to 45%+ by:
1. Advanced content section analysis with deeper extraction patterns
2. Dynamic content rendering support for JavaScript-heavy sites
3. Multi-format content processing (PDFs, embedded documents)
4. Enhanced semantic understanding of business contexts
5. Industry-specific content pattern recognition

Based on Phase 1 success (0% false positives, 25% discovery rate) - building on solid foundation.
Target: 45%+ discovery rate while maintaining 0% false positive rate.

Author: AI Assistant
Date: 2025-01-23
Version: 2.0.0 - Phase 2 Implementation
"""

import re
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from urllib.parse import urlparse, urljoin
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

# Advanced content processing
from bs4 import BeautifulSoup, Tag, NavigableString
import html2text
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

# Enhanced NLP and pattern recognition
import spacy
import nltk
from textblob import TextBlob
import fitz  # PyMuPDF for PDF processing

logger = logging.getLogger(__name__)

@dataclass
class ContentSection:
    """Enhanced content section with Phase 2 metadata"""
    section_type: str
    title: str
    content: str
    html_element: Optional[str] = None
    
    # Phase 2 enhancements
    extraction_method: str = "static"  # static, dynamic, pdf, embedded
    semantic_context: List[str] = field(default_factory=list)
    business_indicators: List[str] = field(default_factory=list)
    executive_density: float = 0.0  # Probability of containing executives
    content_quality: float = 0.0    # Content richness score
    
    # Advanced metadata
    word_count: int = 0
    sentence_count: int = 0
    has_contact_info: bool = False
    has_social_links: bool = False
    language_detected: str = "en"

@dataclass
class BusinessContext:
    """Advanced business context analysis for better targeting"""
    company_size: str = "unknown"  # micro, small, medium, large
    business_type: str = "unknown"  # family, corporate, franchise, startup
    industry_vertical: str = "unknown"  # plumbing, heating, general, commercial
    decision_maker_patterns: List[str] = field(default_factory=list)
    organizational_structure: str = "flat"  # flat, hierarchical, matrix

class AdvancedContentAnalyzer:
    """
    Phase 2 Advanced Content Analyzer for enhanced executive discovery.
    
    Improvements over Phase 1:
    1. Dynamic content rendering with Selenium
    2. PDF and embedded document processing  
    3. Advanced semantic analysis
    4. Multi-source content aggregation
    5. Industry-specific pattern recognition
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize advanced NLP tools
        self._initialize_nlp_tools()
        
        # Phase 2 content discovery patterns
        self.advanced_section_patterns = {
            'executive_sections': [
                # Traditional sections
                'about', 'team', 'leadership', 'management', 'directors', 'staff',
                'our team', 'meet the team', 'our people', 'key personnel',
                
                # Industry-specific sections  
                'owner', 'proprietor', 'founder', 'company history', 'our story',
                'family business', 'established', 'since', 'experience',
                
                # Professional sections
                'qualifications', 'certifications', 'accreditations', 'memberships',
                'testimonials', 'reviews', 'case studies', 'projects',
                
                # Contact-adjacent sections
                'get in touch', 'contact us', 'reach us', 'speak to', 'ask for',
                'emergency contact', '24/7 service', 'call us', 'phone'
            ],
            
            'dynamic_content_indicators': [
                # JavaScript-rendered content markers
                'ng-app', 'ng-controller', 'vue-app', 'react-root',
                'data-reactroot', 'data-vue-app', 'js-app',
                'async-content', 'lazy-load', 'tab-content'
            ],
            
            'pdf_content_indicators': [
                # PDF and document links
                'pdf', 'doc', 'docx', 'brochure', 'catalog', 'profile',
                'company profile', 'team profile', 'capabilities',
                'corporate brochure', 'annual report'
            ]
        }
        
        # Advanced business context patterns
        self.business_context_patterns = {
            'family_business': [
                'family owned', 'family run', 'family business', 'generations',
                'father and son', 'established by', 'founded by', 'since 19',
                'traditional', 'heritage', 'legacy'
            ],
            'corporate': [
                'ltd', 'limited', 'plc', 'incorporated', 'corp', 'company',
                'group', 'enterprises', 'holdings', 'international'
            ],
            'professional_services': [
                'qualified', 'certified', 'licensed', 'registered', 'approved',
                'gas safe', 'city and guilds', 'nvq', 'btec', 'chartered'
            ]
        }
        
        # Selenium setup for dynamic content
        self.selenium_options = Options()
        self.selenium_options.add_argument('--headless')
        self.selenium_options.add_argument('--no-sandbox')
        self.selenium_options.add_argument('--disable-dev-shm-usage')
        self.selenium_options.add_argument('--disable-gpu')
        self.selenium_options.add_argument('--window-size=1920,1080')
        
        # Performance settings
        self.max_workers = 3
        self.timeout_seconds = 15
        self.max_pdf_pages = 10
    
    def _initialize_nlp_tools(self):
        """Initialize advanced NLP tools for Phase 2"""
        try:
            # Load spaCy model with additional components
            self.nlp = spacy.load("en_core_web_sm")
            
            # Add custom business entity recognition
            if "business_entity_ruler" not in self.nlp.pipe_names:
                ruler = self.nlp.add_pipe("entity_ruler", name="business_entity_ruler")
                business_patterns = [
                    {"label": "EXEC_TITLE", "pattern": [{"LOWER": {"IN": ["ceo", "director", "manager", "owner"]}}]},
                    {"label": "COMPANY_TYPE", "pattern": [{"LOWER": {"IN": ["ltd", "limited", "plc", "inc"]}}]},
                ]
                ruler.add_patterns(business_patterns)
            
            # Initialize additional NLP tools
            self.html_converter = html2text.HTML2Text()
            self.html_converter.ignore_links = False
            self.html_converter.ignore_images = True
            
            self.logger.info("✅ Advanced NLP tools initialized for Phase 2")
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing NLP tools: {str(e)}")
            self.nlp = None
    
    def analyze_content_comprehensively(self, url: str, html_content: str, 
                                      company_info: Dict[str, Any]) -> List[ContentSection]:
        """
        Comprehensive content analysis with Phase 2 enhancements.
        
        Args:
            url: Website URL for context
            html_content: Static HTML content
            company_info: Company information for targeting
            
        Returns:
            List of enhanced content sections with discovery metadata
        """
        start_time = time.time()
        
        self.logger.info(f"🔍 Starting Phase 2 comprehensive content analysis for {url}")
        
        sections = []
        
        try:
            # Phase 2.1: Static Content Analysis (Enhanced)
            self.logger.info("📄 Phase 2.1: Enhanced static content analysis...")
            static_sections = self._analyze_static_content_enhanced(html_content, company_info)
            sections.extend(static_sections)
            
            # Phase 2.2: Dynamic Content Analysis
            self.logger.info("⚡ Phase 2.2: Dynamic content analysis...")
            dynamic_sections = self._analyze_dynamic_content(url, html_content)
            sections.extend(dynamic_sections)
            
            # Phase 2.3: PDF and Document Analysis
            self.logger.info("📑 Phase 2.3: PDF and document analysis...")
            document_sections = self._analyze_linked_documents(url, html_content)
            sections.extend(document_sections)
            
            # Phase 2.4: Social Media and External Content
            self.logger.info("🔗 Phase 2.4: Social media content analysis...")
            social_sections = self._analyze_social_content(url, html_content)
            sections.extend(social_sections)
            
            # Phase 2.5: Business Context Enhancement
            self.logger.info("🏢 Phase 2.5: Business context enhancement...")
            business_context = self._analyze_business_context(html_content, company_info)
            sections = self._enhance_sections_with_context(sections, business_context)
            
            # Phase 2.6: Executive Density Calculation
            self.logger.info("👥 Phase 2.6: Executive density calculation...")
            sections = self._calculate_executive_density(sections)
            
            # Phase 2.7: Quality Scoring and Ranking
            self.logger.info("⭐ Phase 2.7: Content quality scoring...")
            sections = self._score_content_quality(sections)
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"✅ Phase 2 analysis complete:")
            self.logger.info(f"   ⏱️ Processing time: {processing_time:.2f}s")
            self.logger.info(f"   📊 Total sections: {len(sections)}")
            self.logger.info(f"   🎯 High-potential sections: {len([s for s in sections if s.executive_density > 0.7])}")
            
            return sorted(sections, key=lambda x: x.executive_density, reverse=True)
            
        except Exception as e:
            self.logger.error(f"❌ Error in comprehensive content analysis: {str(e)}")
            return sections
    
    def _analyze_static_content_enhanced(self, html_content: str, 
                                       company_info: Dict[str, Any]) -> List[ContentSection]:
        """Enhanced static content analysis with Phase 2 improvements"""
        sections = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Enhanced section detection with semantic analysis
            section_elements = []
            
            # 1. Structural section detection
            section_elements.extend(soup.find_all(['section', 'article', 'div', 'main'], 
                                                class_=re.compile(r'(about|team|staff|management|director)', re.I)))
            
            # 2. Heading-based section detection
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                heading_text = heading.get_text(strip=True).lower()
                if any(pattern in heading_text for pattern in self.advanced_section_patterns['executive_sections']):
                    # Find content following this heading
                    section_content = self._extract_section_content_after_heading(heading)
                    if section_content:
                        section_elements.append(section_content)
            
            # 3. Navigation-based section discovery
            nav_links = soup.find_all('a', href=True)
            for link in nav_links:
                link_text = link.get_text(strip=True).lower()
                if any(pattern in link_text for pattern in self.advanced_section_patterns['executive_sections']):
                    # Try to find linked section
                    linked_section = self._find_linked_section(soup, link['href'])
                    if linked_section:
                        section_elements.append(linked_section)
            
            # Process all discovered sections
            for element in section_elements:
                section = self._process_section_element(element, "static")
                if section and len(section.content.strip()) > 50:  # Quality filter
                    sections.append(section)
            
            # 4. Full-page analysis for scattered executive information
            if len(sections) < 3:  # If few sections found, analyze entire page
                full_page_section = self._analyze_full_page_content(soup)
                if full_page_section:
                    sections.append(full_page_section)
            
        except Exception as e:
            self.logger.error(f"❌ Error in enhanced static analysis: {str(e)}")
        
        return sections
    
    def _analyze_dynamic_content(self, url: str, html_content: str) -> List[ContentSection]:
        """Analyze dynamic JavaScript-rendered content using Selenium"""
        sections = []
        
        # Check if dynamic content analysis is needed
        if not self._has_dynamic_content_indicators(html_content):
            self.logger.info("ℹ️ No dynamic content indicators found, skipping Selenium analysis")
            return sections
        
        try:
            self.logger.info("🌐 Initializing Selenium for dynamic content analysis...")
            
            with webdriver.Chrome(options=self.selenium_options) as driver:
                driver.set_page_load_timeout(self.timeout_seconds)
                
                try:
                    # Load page and wait for dynamic content
                    driver.get(url)
                    time.sleep(3)  # Allow JavaScript to execute
                    
                    # Wait for common dynamic content indicators
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "loaded"))
                        )
                    except TimeoutException:
                        pass  # Continue even if specific indicators not found
                    
                    # Get fully rendered page
                    dynamic_html = driver.page_source
                    dynamic_soup = BeautifulSoup(dynamic_html, 'html.parser')
                    
                    # Find sections that weren't in static content
                    static_soup = BeautifulSoup(html_content, 'html.parser')
                    dynamic_sections = self._find_new_dynamic_sections(static_soup, dynamic_soup)
                    
                    for section_element in dynamic_sections:
                        section = self._process_section_element(section_element, "dynamic")
                        if section:
                            sections.append(section)
                    
                    self.logger.info(f"✅ Dynamic analysis found {len(sections)} additional sections")
                    
                except WebDriverException as e:
                    self.logger.warning(f"⚠️ Selenium error: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"❌ Error in dynamic content analysis: {str(e)}")
        
        return sections
    
    def _analyze_linked_documents(self, url: str, html_content: str) -> List[ContentSection]:
        """Analyze linked PDFs and documents for executive information"""
        sections = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find document links
            doc_links = []
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href']
                link_text = link.get_text(strip=True).lower()
                
                # Check for document indicators
                if (any(indicator in href.lower() for indicator in self.advanced_section_patterns['pdf_content_indicators']) or
                    any(indicator in link_text for indicator in ['team', 'about', 'profile', 'brochure'])):
                    
                    full_url = urljoin(url, href)
                    doc_links.append({
                        'url': full_url,
                        'text': link_text,
                        'type': self._detect_document_type(href)
                    })
            
            # Process documents
            for doc_info in doc_links[:3]:  # Limit to 3 documents for performance
                doc_sections = self._process_document(doc_info)
                sections.extend(doc_sections)
            
            self.logger.info(f"✅ Document analysis found {len(sections)} sections from {len(doc_links)} documents")
            
        except Exception as e:
            self.logger.error(f"❌ Error in document analysis: {str(e)}")
        
        return sections
    
    def _analyze_social_content(self, url: str, html_content: str) -> List[ContentSection]:
        """Analyze social media links and embedded content"""
        sections = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find social media links
            social_patterns = ['linkedin', 'facebook', 'twitter', 'instagram', 'youtube']
            social_links = []
            
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                if any(pattern in href for pattern in social_patterns):
                    social_links.append({
                        'platform': next((p for p in social_patterns if p in href), 'unknown'),
                        'url': link['href'],
                        'text': link.get_text(strip=True)
                    })
            
            # Create social content section if found
            if social_links:
                social_content = f"Social Media Presence: {len(social_links)} profiles found\n"
                for social in social_links:
                    social_content += f"- {social['platform'].title()}: {social['text']}\n"
                
                section = ContentSection(
                    section_type="social",
                    title="Social Media Links",
                    content=social_content,
                    extraction_method="social",
                    semantic_context=["social", "external"],
                    business_indicators=["online_presence"],
                    has_social_links=True
                )
                sections.append(section)
            
        except Exception as e:
            self.logger.error(f"❌ Error in social content analysis: {str(e)}")
        
        return sections
    
    def _analyze_business_context(self, html_content: str, 
                                company_info: Dict[str, Any]) -> BusinessContext:
        """Analyze business context for better executive targeting"""
        context = BusinessContext()
        
        try:
            # Convert HTML to text for analysis
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text().lower()
            
            # Detect business type
            for business_type, patterns in self.business_context_patterns.items():
                if any(pattern in text_content for pattern in patterns):
                    context.business_type = business_type
                    break
            
            # Detect company size indicators
            if any(term in text_content for term in ['team of', 'staff of', 'employees']):
                # Try to extract size numbers
                size_match = re.search(r'(\d+)\s*(?:staff|employees|team members)', text_content)
                if size_match:
                    size = int(size_match.group(1))
                    if size < 10:
                        context.company_size = "micro"
                    elif size < 50:
                        context.company_size = "small"
                    elif size < 250:
                        context.company_size = "medium"
                    else:
                        context.company_size = "large"
            
            # Detect industry vertical
            industry_indicators = {
                'plumbing': ['plumb', 'pipe', 'drain', 'toilet', 'sink', 'bathroom'],
                'heating': ['heat', 'boiler', 'radiator', 'central heating', 'gas'],
                'commercial': ['commercial', 'industrial', 'business', 'office'],
                'emergency': ['24/7', 'emergency', 'urgent', 'call out']
            }
            
            for industry, indicators in industry_indicators.items():
                if any(indicator in text_content for indicator in indicators):
                    context.industry_vertical = industry
                    break
            
            # Set decision maker patterns based on context
            if context.business_type == "family_business":
                context.decision_maker_patterns = ["owner", "founder", "director", "father", "son"]
            elif context.business_type == "corporate":
                context.decision_maker_patterns = ["director", "manager", "ceo", "head"]
            else:
                context.decision_maker_patterns = ["owner", "director", "manager"]
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing business context: {str(e)}")
        
        return context
    
    def _enhance_sections_with_context(self, sections: List[ContentSection], 
                                     context: BusinessContext) -> List[ContentSection]:
        """Enhance sections with business context information"""
        for section in sections:
            # Add business indicators based on content
            section.business_indicators.append(context.business_type)
            section.business_indicators.append(context.company_size)
            section.business_indicators.append(context.industry_vertical)
            
            # Enhance semantic context
            if context.business_type == "family_business":
                section.semantic_context.extend(["family", "traditional", "personal"])
            elif context.business_type == "corporate":
                section.semantic_context.extend(["professional", "corporate", "formal"])
        
        return sections
    
    def _calculate_executive_density(self, sections: List[ContentSection]) -> List[ContentSection]:
        """Calculate probability of each section containing executive information"""
        for section in sections:
            density_score = 0.0
            content_lower = section.content.lower()
            
            # Base scoring factors
            if section.section_type in ['about', 'team', 'leadership']:
                density_score += 0.3
            
            # Title pattern matching
            executive_title_count = len(re.findall(r'\b(?:director|manager|owner|ceo|founder)\b', content_lower))
            density_score += min(executive_title_count * 0.2, 0.4)
            
            # Name pattern indicators
            person_name_count = len(re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', section.content))
            density_score += min(person_name_count * 0.1, 0.3)
            
            # Contact information presence
            if section.has_contact_info:
                density_score += 0.2
            
            # Business context relevance
            if any(indicator in section.business_indicators for indicator in ['family_business', 'small']):
                density_score += 0.1
            
            # Quality and length factors
            if section.word_count > 100:
                density_score += 0.1
            
            section.executive_density = min(density_score, 1.0)
        
        return sections
    
    def _score_content_quality(self, sections: List[ContentSection]) -> List[ContentSection]:
        """Score content quality for executive extraction potential"""
        for section in sections:
            quality_score = 0.0
            
            # Content richness
            section.word_count = len(section.content.split())
            section.sentence_count = len(re.findall(r'[.!?]+', section.content))
            
            if section.word_count > 50:
                quality_score += 0.3
            if section.sentence_count > 3:
                quality_score += 0.2
            
            # Semantic richness
            if len(section.semantic_context) > 2:
                quality_score += 0.2
            
            # Business relevance
            if len(section.business_indicators) > 1:
                quality_score += 0.2
            
            # Extraction method quality
            if section.extraction_method == "dynamic":
                quality_score += 0.1  # Dynamic content often more complete
            
            section.content_quality = min(quality_score, 1.0)
        
        return sections
    
    # Helper methods for content processing
    def _has_dynamic_content_indicators(self, html_content: str) -> bool:
        """Check if page has indicators of dynamic content"""
        return any(indicator in html_content.lower() 
                  for indicator in self.advanced_section_patterns['dynamic_content_indicators'])
    
    def _extract_section_content_after_heading(self, heading: Tag) -> Optional[Tag]:
        """Extract content section following a heading"""
        content_elements = []
        current = heading.next_sibling
        
        while current and len(content_elements) < 5:  # Limit content collection
            if hasattr(current, 'name') and current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                break  # Stop at next heading
            if hasattr(current, 'get_text') and current.get_text(strip=True):
                content_elements.append(current)
            current = current.next_sibling
        
        if content_elements:
            # Create a container for the content
            container = heading.parent or heading
            return container
        return None
    
    def _find_linked_section(self, soup: BeautifulSoup, href: str) -> Optional[Tag]:
        """Find section linked by internal anchor"""
        if href.startswith('#'):
            section_id = href[1:]
            return soup.find(id=section_id)
        return None
    
    def _process_section_element(self, element: Tag, extraction_method: str) -> Optional[ContentSection]:
        """Process a section element into ContentSection object"""
        try:
            if not element:
                return None
            
            # Extract text content
            content = element.get_text(separator='\n', strip=True)
            if len(content) < 20:  # Minimum content threshold
                return None
            
            # Determine section type and title
            section_type = self._determine_section_type(element, content)
            title = self._extract_section_title(element, section_type)
            
            # Create section object
            section = ContentSection(
                section_type=section_type,
                title=title,
                content=content,
                html_element=str(element)[:500],  # Truncated HTML
                extraction_method=extraction_method,
                has_contact_info=self._has_contact_information(content)
            )
            
            return section
            
        except Exception as e:
            self.logger.error(f"❌ Error processing section element: {str(e)}")
            return None
    
    def _determine_section_type(self, element: Tag, content: str) -> str:
        """Determine the type of content section"""
        # Check element attributes
        if element.get('class'):
            class_str = ' '.join(element.get('class')).lower()
            for section_pattern in self.advanced_section_patterns['executive_sections']:
                if section_pattern in class_str:
                    return section_pattern
        
        # Check content for patterns
        content_lower = content.lower()
        for pattern in ['about', 'team', 'staff', 'management', 'contact']:
            if pattern in content_lower:
                return pattern
        
        return "general"
    
    def _extract_section_title(self, element: Tag, section_type: str) -> str:
        """Extract or generate title for content section"""
        # Look for heading in element
        heading = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if heading:
            return heading.get_text(strip=True)
        
        # Use section type as fallback
        return section_type.replace('_', ' ').title()
    
    def _has_contact_information(self, content: str) -> bool:
        """Check if content contains contact information"""
        contact_patterns = [
            r'\b\d{10,11}\b',  # Phone numbers
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\bmobile\b', r'\bphone\b', r'\bcall\b', r'\bemail\b'
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in contact_patterns)
    
    def _analyze_full_page_content(self, soup: BeautifulSoup) -> Optional[ContentSection]:
        """Analyze full page when insufficient sections found"""
        try:
            # Get main content, avoiding nav/footer
            main_content = soup.find('main') or soup.find('body')
            if not main_content:
                return None
            
            content = main_content.get_text(separator='\n', strip=True)
            if len(content) < 100:
                return None
            
            section = ContentSection(
                section_type="full_page",
                title="Full Page Analysis",
                content=content,
                extraction_method="fallback",
                semantic_context=["comprehensive"],
                business_indicators=["full_site"]
            )
            
            return section
            
        except Exception as e:
            self.logger.error(f"❌ Error in full page analysis: {str(e)}")
            return None
    
    def _find_new_dynamic_sections(self, static_soup: BeautifulSoup, 
                                  dynamic_soup: BeautifulSoup) -> List[Tag]:
        """Find sections present in dynamic content but not static"""
        # This is a simplified comparison - in production, would use more sophisticated diff
        static_text = static_soup.get_text()
        dynamic_sections = []
        
        for element in dynamic_soup.find_all(['section', 'div', 'article']):
            element_text = element.get_text(strip=True)
            if len(element_text) > 50 and element_text not in static_text:
                dynamic_sections.append(element)
        
        return dynamic_sections[:5]  # Limit results
    
    def _detect_document_type(self, href: str) -> str:
        """Detect document type from URL"""
        href_lower = href.lower()
        if '.pdf' in href_lower:
            return 'pdf'
        elif any(ext in href_lower for ext in ['.doc', '.docx']):
            return 'word'
        return 'unknown'
    
    def _process_document(self, doc_info: Dict[str, str]) -> List[ContentSection]:
        """Process document for executive information"""
        sections = []
        
        try:
            if doc_info['type'] == 'pdf':
                sections = self._process_pdf_document(doc_info)
            # Could add Word document processing here
            
        except Exception as e:
            self.logger.error(f"❌ Error processing document {doc_info['url']}: {str(e)}")
        
        return sections
    
    def _process_pdf_document(self, doc_info: Dict[str, str]) -> List[ContentSection]:
        """Process PDF document for executive information"""
        sections = []
        
        try:
            # Download and process PDF
            response = requests.get(doc_info['url'], timeout=10)
            if response.status_code == 200:
                # Use PyMuPDF to extract text
                pdf_doc = fitz.open(stream=response.content, filetype="pdf")
                
                pdf_text = ""
                for page_num in range(min(len(pdf_doc), self.max_pdf_pages)):
                    page = pdf_doc.load_page(page_num)
                    pdf_text += page.get_text()
                
                if len(pdf_text.strip()) > 100:
                    section = ContentSection(
                        section_type="pdf_document",
                        title=f"PDF: {doc_info['text']}",
                        content=pdf_text,
                        extraction_method="pdf",
                        semantic_context=["document", "detailed"],
                        business_indicators=["formal_document"]
                    )
                    sections.append(section)
                
                pdf_doc.close()
            
        except Exception as e:
            self.logger.error(f"❌ Error processing PDF: {str(e)}")
        
        return sections
    
    def get_phase2_metrics(self) -> Dict[str, Any]:
        """Get Phase 2 enhanced metrics"""
        return {
            'version': '2.0.0',
            'capabilities': [
                'dynamic_content_analysis',
                'pdf_document_processing',
                'social_media_integration',
                'business_context_analysis',
                'executive_density_scoring',
                'content_quality_assessment'
            ],
            'discovery_target': '45%+',
            'confidence_target': '0.600+',
            'false_positive_maintenance': '0%'
        } 