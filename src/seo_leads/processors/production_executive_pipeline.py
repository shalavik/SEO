#!/usr/bin/env python3
"""
Production Executive Pipeline - Phase 6C
Enterprise-grade executive discovery system using Context7 best practices
"""

import asyncio
import json
import time
import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple, Set
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup, SoupStrainer
import threading
from queue import Queue
import random

# Context7 best practices imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Internal imports
from src.seo_leads.models import Executive, ContactInfo, BusinessContext
from src.seo_leads.ai.advanced_name_validator import AdvancedNameValidator

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'production_pipeline_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ProductionConfig:
    """Production configuration using Context7 best practices"""
    # Performance settings
    max_concurrent_companies: int = 5
    max_pages_per_company: int = 8
    request_timeout: int = 30
    selenium_timeout: int = 20
    
    # Content extraction settings
    enable_selenium_fallback: bool = True
    enable_smart_content_filtering: bool = True
    enable_executive_validation: bool = True
    
    # Quality thresholds
    min_confidence_score: float = 0.6
    max_executives_per_company: int = 10
    
    # Rate limiting (Context7 best practice)
    request_delay_min: float = 1.0
    request_delay_max: float = 3.0
    
    # User agents for rotation (Context7 anti-detection)
    user_agents: List[str] = None
    
    def __post_init__(self):
        if self.user_agents is None:
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36'
            ]

@dataclass 
class ProductionResult:
    """Production pipeline result structure"""
    company_id: str
    company_name: str
    company_domain: str
    executives_found: List[Executive]
    total_pages_analyzed: int
    processing_time: float
    discovery_sources: List[str]
    quality_score: float
    confidence_distribution: Dict[str, int]
    contact_completeness: float
    errors: List[str]

class ProductionWebSession:
    """Production web session using Context7 best practices"""
    
    def __init__(self, config: ProductionConfig):
        self.config = config
        self.session = None
        self.selenium_driver = None
        self._setup_requests_session()
        
    def _setup_requests_session(self):
        """Setup requests session with Context7 optimizations"""
        self.session = requests.Session()
        
        # Context7 retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=['GET', 'POST']
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Context7 session headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def get_random_user_agent(self) -> str:
        """Get random user agent for anti-detection"""
        return random.choice(self.config.user_agents)
    
    async def fetch_content(self, url: str, use_selenium: bool = False) -> Tuple[str, bool]:
        """Fetch page content using Context7 best practices"""
        try:
            if use_selenium and self.config.enable_selenium_fallback:
                return await self._fetch_with_selenium(url)
            else:
                return await self._fetch_with_requests(url)
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return "", False
    
    async def _fetch_with_requests(self, url: str) -> Tuple[str, bool]:
        """Fetch content with requests session"""
        try:
            # Context7 rate limiting
            await asyncio.sleep(random.uniform(
                self.config.request_delay_min, 
                self.config.request_delay_max
            ))
            
            # Rotate user agent
            self.session.headers['User-Agent'] = self.get_random_user_agent()
            
            # Make request
            response = self.session.get(url, timeout=self.config.request_timeout)
            response.raise_for_status()
            
            return response.text, True
            
        except Exception as e:
            logger.warning(f"Requests failed for {url}: {e}")
            return "", False
    
    async def _fetch_with_selenium(self, url: str) -> Tuple[str, bool]:
        """Fetch content with Selenium for JavaScript sites"""
        if not self.selenium_driver:
            self._setup_selenium()
        
        try:
            self.selenium_driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.selenium_driver, self.config.selenium_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get page source
            content = self.selenium_driver.page_source
            return content, True
            
        except (TimeoutException, WebDriverException) as e:
            logger.warning(f"Selenium failed for {url}: {e}")
            return "", False
    
    def _setup_selenium(self):
        """Setup Selenium with Context7 performance optimizations"""
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')
            options.add_argument('--disable-javascript')  # Only when not needed
            options.add_argument(f'--user-agent={self.get_random_user_agent()}')
            
            # Context7 performance settings
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
                "profile.managed_default_content_settings.media_stream": 2,
            }
            options.add_experimental_option("prefs", prefs)
            
            self.selenium_driver = webdriver.Chrome(options=options)
            self.selenium_driver.set_page_load_timeout(self.config.selenium_timeout)
            
        except Exception as e:
            logger.error(f"Failed to setup Selenium: {e}")
            self.selenium_driver = None
    
    def cleanup(self):
        """Cleanup resources"""
        if self.session:
            self.session.close()
        if self.selenium_driver:
            self.selenium_driver.quit()

class ProductionContentAnalyzer:
    """Production content analyzer using Context7 BeautifulSoup best practices"""
    
    def __init__(self, config: ProductionConfig):
        self.config = config
        self.name_validator = AdvancedNameValidator()
        
        # Context7 BeautifulSoup optimizations
        self.executive_strainer = SoupStrainer(
            ["div", "p", "span", "section", "article", "header", "footer", "aside", "main"]
        )
        
        # Executive detection patterns
        self.executive_patterns = [
            r'(?:owner|director|manager|founder|ceo|president|proprietor)[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)[,\s]*(?:owner|director|manager|founder|ceo|president|proprietor)',
            r'contact[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)[,\s]*-[,\s]*(?:owner|director|manager)',
            r'established by[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'led by[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)'
        ]
        
        # Business context patterns
        self.business_patterns = {
            'phone': r'(?:tel|phone|call|mobile)[:\s]*(\+?[\d\s\-\(\)]{10,15})',
            'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            'address': r'(?:address|located|based)[:\s]*([A-Z][a-zA-Z0-9\s,.-]{20,100})',
            'established': r'(?:established|founded|since)[:\s]*(\d{4})',
            'services': r'(?:services|specializing)[:\s]*([a-zA-Z\s,&-]{10,100})'
        }
    
    def analyze_content(self, content: str, company_name: str, url: str) -> Tuple[List[Executive], BusinessContext]:
        """Analyze content for executives and business info using Context7 techniques"""
        try:
            # Context7 BeautifulSoup parsing with strainer
            soup = BeautifulSoup(content, 'html.parser', parse_only=self.executive_strainer)
            
            # Clean and extract text
            text_content = self._extract_clean_text(soup)
            
            # Find executives
            executives = self._extract_executives(text_content, company_name, url)
            
            # Extract business context
            business_context = self._extract_business_context(text_content, url)
            
            return executives, business_context
            
        except Exception as e:
            logger.error(f"Content analysis error for {url}: {e}")
            return [], BusinessContext(company_domain=urlparse(url).netloc)
    
    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text using Context7 best practices"""
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        # Get text with Context7 text extraction
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean multiple whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _extract_executives(self, text: str, company_name: str, url: str) -> List[Executive]:
        """Extract executives using pattern matching"""
        executives = []
        found_names = set()
        
        # Apply all executive patterns
        for pattern in self.executive_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                name = match.group(1).strip()
                
                # Validate name
                if (self.name_validator.is_real_executive_name(name) and 
                    name not in found_names and 
                    len(name.split()) >= 2):
                    
                    # Extract context around the match
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end]
                    
                    # Determine title from context
                    title = self._extract_title_from_context(context, name)
                    
                    # Create executive
                    executive = Executive(
                        name=name,
                        title=title,
                        email="",
                        phone="",
                        linkedin_url="",
                        source_url=url,
                        confidence_score=self._calculate_confidence(name, title, context),
                        business_context=f"Found in: {context[:100]}...",
                        extraction_method="pattern_matching",
                        last_updated=datetime.now(timezone.utc)
                    )
                    
                    executives.append(executive)
                    found_names.add(name)
                    
                    # Limit executives per company
                    if len(executives) >= self.config.max_executives_per_company:
                        break
        
        return executives
    
    def _extract_title_from_context(self, context: str, name: str) -> str:
        """Extract executive title from context"""
        context_lower = context.lower()
        
        # Executive title patterns
        if any(word in context_lower for word in ['owner', 'proprietor']):
            return 'Owner'
        elif any(word in context_lower for word in ['director', 'managing']):
            return 'Director'
        elif any(word in context_lower for word in ['manager', 'lead']):
            return 'Manager'
        elif any(word in context_lower for word in ['founder', 'established']):
            return 'Founder'
        elif any(word in context_lower for word in ['ceo', 'president']):
            return 'CEO'
        else:
            return 'Executive'
    
    def _calculate_confidence(self, name: str, title: str, context: str) -> float:
        """Calculate confidence score for executive"""
        score = 0.5  # Base score
        
        # Name quality
        if self.name_validator.get_name_quality_score(name) > 0.7:
            score += 0.2
        
        # Title quality
        if title in ['Owner', 'Director', 'CEO', 'Founder']:
            score += 0.2
        
        # Context quality
        if any(word in context.lower() for word in ['contact', 'phone', 'email', 'call']):
            score += 0.1
        
        return min(1.0, score)
    
    def _extract_business_context(self, text: str, url: str) -> BusinessContext:
        """Extract business context information"""
        domain = urlparse(url).netloc
        context = BusinessContext(company_domain=domain)
        
        # Extract contact information using patterns
        for pattern_type, pattern in self.business_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if pattern_type == 'phone':
                    context.contact_info = ContactInfo(
                        phone=matches[0] if matches else "",
                        email=context.contact_info.email if hasattr(context, 'contact_info') else ""
                    )
                elif pattern_type == 'email':
                    if hasattr(context, 'contact_info'):
                        context.contact_info.email = matches[0]
                    else:
                        context.contact_info = ContactInfo(phone="", email=matches[0])
        
        return context

class ProductionExecutivePipeline:
    """Production executive discovery pipeline - Phase 6C"""
    
    def __init__(self, config: Optional[ProductionConfig] = None):
        self.config = config or ProductionConfig()
        self.session_pool = []
        self.analyzer = ProductionContentAnalyzer(self.config)
        self.results = []
        
        # Performance metrics
        self.start_time = None
        self.companies_processed = 0
        self.total_executives_found = 0
        self.total_pages_analyzed = 0
        
    async def discover_executives_for_company(self, company_name: str, website_url: str) -> ProductionResult:
        """Discover executives for a single company"""
        start_time = time.time()
        executives = []
        pages_analyzed = 0
        discovery_sources = []
        errors = []
        
        # Get web session
        session = ProductionWebSession(self.config)
        
        try:
            # Discover pages to analyze
            pages_to_analyze = await self._discover_relevant_pages(website_url, session)
            
            # Analyze each page
            for page_url in pages_to_analyze[:self.config.max_pages_per_company]:
                try:
                    content, success = await session.fetch_content(page_url)
                    if success and content:
                        page_executives, business_context = self.analyzer.analyze_content(
                            content, company_name, page_url
                        )
                        
                        if page_executives:
                            executives.extend(page_executives)
                            discovery_sources.append(f"website:{urlparse(page_url).path}")
                        
                        pages_analyzed += 1
                        
                        # Respect rate limiting
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                        
                except Exception as e:
                    errors.append(f"Page {page_url}: {str(e)}")
                    logger.warning(f"Error analyzing page {page_url}: {e}")
            
            # Remove duplicates and validate
            executives = self._deduplicate_and_validate_executives(executives)
            
            # Calculate quality metrics
            quality_score = self._calculate_quality_score(executives, pages_analyzed)
            confidence_dist = self._analyze_confidence_distribution(executives)
            contact_completeness = self._calculate_contact_completeness(executives)
            
            processing_time = time.time() - start_time
            
            return ProductionResult(
                company_id=f"prod_{int(time.time())}_{len(self.results)}",
                company_name=company_name,
                company_domain=urlparse(website_url).netloc,
                executives_found=executives,
                total_pages_analyzed=pages_analyzed,
                processing_time=processing_time,
                discovery_sources=discovery_sources,
                quality_score=quality_score,
                confidence_distribution=confidence_dist,
                contact_completeness=contact_completeness,
                errors=errors
            )
            
        except Exception as e:
            errors.append(f"Pipeline error: {str(e)}")
            logger.error(f"Pipeline error for {company_name}: {e}")
            
            return ProductionResult(
                company_id=f"error_{int(time.time())}_{len(self.results)}",
                company_name=company_name,
                company_domain=urlparse(website_url).netloc,
                executives_found=[],
                total_pages_analyzed=0,
                processing_time=time.time() - start_time,
                discovery_sources=[],
                quality_score=0.0,
                confidence_distribution={'high': 0, 'medium': 0, 'low': 0},
                contact_completeness=0.0,
                errors=errors
            )
        
        finally:
            session.cleanup()
    
    async def _discover_relevant_pages(self, base_url: str, session: ProductionWebSession) -> List[str]:
        """Discover relevant pages for executive discovery"""
        pages = [base_url]  # Always include main page
        
        try:
            # Fetch main page to find additional relevant pages
            content, success = await session.fetch_content(base_url)
            if success and content:
                soup = BeautifulSoup(content, 'html.parser')
                
                # Look for relevant page links
                relevant_keywords = ['about', 'team', 'staff', 'contact', 'management', 'leadership', 'directors']
                
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '').lower()
                    if any(keyword in href for keyword in relevant_keywords):
                        full_url = urljoin(base_url, link['href'])
                        if full_url not in pages:
                            pages.append(full_url)
        
        except Exception as e:
            logger.warning(f"Error discovering pages for {base_url}: {e}")
        
        return pages
    
    def _deduplicate_and_validate_executives(self, executives: List[Executive]) -> List[Executive]:
        """Remove duplicates and validate executives"""
        seen_names = set()
        validated_executives = []
        
        for exec in executives:
            if (exec.name not in seen_names and 
                exec.confidence_score >= self.config.min_confidence_score):
                validated_executives.append(exec)
                seen_names.add(exec.name)
        
        return sorted(validated_executives, key=lambda x: x.confidence_score, reverse=True)
    
    def _calculate_quality_score(self, executives: List[Executive], pages_analyzed: int) -> float:
        """Calculate overall quality score"""
        if not executives:
            return 0.0
        
        # Base score from average confidence
        avg_confidence = sum(exec.confidence_score for exec in executives) / len(executives)
        
        # Bonus for multiple pages analyzed
        page_bonus = min(0.2, pages_analyzed * 0.05)
        
        # Bonus for contact information
        contact_bonus = sum(0.1 for exec in executives if exec.email or exec.phone) / len(executives)
        
        return min(1.0, avg_confidence + page_bonus + contact_bonus)
    
    def _analyze_confidence_distribution(self, executives: List[Executive]) -> Dict[str, int]:
        """Analyze confidence score distribution"""
        dist = {'high': 0, 'medium': 0, 'low': 0}
        
        for exec in executives:
            if exec.confidence_score >= 0.8:
                dist['high'] += 1
            elif exec.confidence_score >= 0.6:
                dist['medium'] += 1
            else:
                dist['low'] += 1
        
        return dist
    
    def _calculate_contact_completeness(self, executives: List[Executive]) -> float:
        """Calculate contact information completeness"""
        if not executives:
            return 0.0
        
        total_contacts = 0
        for exec in executives:
            if exec.email:
                total_contacts += 1
            if exec.phone:
                total_contacts += 1
        
        # Maximum possible contacts = 2 per executive (email + phone)
        max_possible = len(executives) * 2
        return total_contacts / max_possible if max_possible > 0 else 0.0
    
    async def process_companies_batch(self, companies: List[Tuple[str, str]]) -> List[ProductionResult]:
        """Process multiple companies concurrently"""
        logger.info(f"🚀 Starting production batch processing for {len(companies)} companies")
        self.start_time = time.time()
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.config.max_concurrent_companies)
        
        async def process_company_with_semaphore(company_data):
            async with semaphore:
                company_name, website_url = company_data
                return await self.discover_executives_for_company(company_name, website_url)
        
        # Process all companies concurrently
        tasks = [process_company_with_semaphore(company) for company in companies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed: {result}")
            else:
                valid_results.append(result)
                self.results.append(result)
        
        # Update metrics
        self.companies_processed = len(valid_results)
        self.total_executives_found = sum(len(r.executives_found) for r in valid_results)
        self.total_pages_analyzed = sum(r.total_pages_analyzed for r in valid_results)
        
        total_time = time.time() - self.start_time
        logger.info(f"✅ Batch processing complete in {total_time:.2f}s")
        logger.info(f"📊 {self.total_executives_found} executives found across {self.companies_processed} companies")
        
        return valid_results
    
    def generate_production_report(self) -> Dict:
        """Generate comprehensive production report"""
        if not self.results:
            return {'error': 'No results to report'}
        
        total_time = time.time() - self.start_time if self.start_time else 0
        
        # Aggregate metrics
        success_rate = len([r for r in self.results if r.executives_found]) / len(self.results)
        avg_processing_time = sum(r.processing_time for r in self.results) / len(self.results)
        avg_quality_score = sum(r.quality_score for r in self.results) / len(self.results)
        avg_contact_completeness = sum(r.contact_completeness for r in self.results) / len(self.results)
        
        # Top performing companies
        top_companies = sorted(self.results, key=lambda x: len(x.executives_found), reverse=True)[:5]
        
        return {
            'production_summary': {
                'total_companies_processed': self.companies_processed,
                'total_executives_found': self.total_executives_found,
                'total_pages_analyzed': self.total_pages_analyzed,
                'total_processing_time': total_time,
                'success_rate': success_rate,
                'average_processing_time': avg_processing_time,
                'average_quality_score': avg_quality_score,
                'average_contact_completeness': avg_contact_completeness
            },
            'performance_metrics': {
                'companies_per_hour': (self.companies_processed / total_time * 3600) if total_time > 0 else 0,
                'executives_per_company': self.total_executives_found / self.companies_processed if self.companies_processed > 0 else 0,
                'pages_per_company': self.total_pages_analyzed / self.companies_processed if self.companies_processed > 0 else 0
            },
            'top_discoveries': [
                {
                    'company_name': r.company_name,
                    'executives_count': len(r.executives_found),
                    'quality_score': r.quality_score,
                    'processing_time': r.processing_time
                }
                for r in top_companies
            ],
            'detailed_results': [
                {
                    'company_id': r.company_id,
                    'company_name': r.company_name,
                    'executives_found': len(r.executives_found),
                    'executives': [
                        {
                            'name': exec.name,
                            'title': exec.title,
                            'confidence_score': exec.confidence_score,
                            'has_email': bool(exec.email),
                            'has_phone': bool(exec.phone)
                        }
                        for exec in r.executives_found
                    ],
                    'quality_metrics': {
                        'quality_score': r.quality_score,
                        'confidence_distribution': r.confidence_distribution,
                        'contact_completeness': r.contact_completeness
                    }
                }
                for r in self.results
            ]
        }
    
    async def save_production_results(self, filename: Optional[str] = None):
        """Save production results to JSON file"""
        if filename is None:
            timestamp = int(time.time())
            filename = f'production_results_phase6c_{timestamp}.json'
        
        report = self.generate_production_report()
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 Production results saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return None

# Test companies for Phase 6C validation
PHASE6C_TEST_COMPANIES = [
    ("CH Parker Plumbing", "http://www.chparker-plumbing.co.uk/"),
    ("MS Heating & Plumbing", "http://www.msheatingandplumbing.co.uk/"),
    ("Absolute Plumbing Solutions", "http://www.absolute-plumbing-solutions.com/"),
    ("Cold Spring Plumbers", "https://coldspringplumbers.co.uk/"),
    ("Mere Green Gas & Plumbing", "http://www.meregreengasandplumbing.co.uk/"),
    ("Manor Vale Heating", "https://manorvale.co.uk/"),
    ("Star Cities Heating", "https://www.starcitiesheatingandplumbing.co.uk/"),
    ("Your Plumbing Services", "http://www.yourplumbingservices.co.uk/"),
    ("Complete Heating", "http://complete-heating.co.uk/"),
    ("Celm Engineering", "https://www.celmeng.co.uk/")
]

async def main():
    """Main production pipeline execution"""
    logger.info("🏭 PHASE 6C PRODUCTION EXECUTIVE DISCOVERY PIPELINE")
    logger.info("=" * 60)
    
    # Initialize production pipeline
    config = ProductionConfig(
        max_concurrent_companies=3,  # Conservative for stability
        max_pages_per_company=5,
        request_timeout=30,
        selenium_timeout=20,
        min_confidence_score=0.6
    )
    
    pipeline = ProductionExecutivePipeline(config)
    
    try:
        # Process test companies
        results = await pipeline.process_companies_batch(PHASE6C_TEST_COMPANIES)
        
        # Generate and save report
        report_file = await pipeline.save_production_results()
        
        # Display summary
        report = pipeline.generate_production_report()
        summary = report['production_summary']
        
        logger.info("\n" + "=" * 60)
        logger.info("🎯 PHASE 6C PRODUCTION RESULTS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Companies Processed: {summary['total_companies_processed']}")
        logger.info(f"Executives Found: {summary['total_executives_found']}")
        logger.info(f"Success Rate: {summary['success_rate']:.1%}")
        logger.info(f"Avg Quality Score: {summary['average_quality_score']:.2f}")
        logger.info(f"Processing Time: {summary['total_processing_time']:.1f}s")
        logger.info(f"Results saved to: {report_file}")
        logger.info("=" * 60)
        
        return results
        
    except Exception as e:
        logger.error(f"Production pipeline failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 