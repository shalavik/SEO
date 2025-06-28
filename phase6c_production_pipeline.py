#!/usr/bin/env python3
"""
Phase 6C Production Executive Discovery Pipeline
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

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'phase6c_production_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Phase6CConfig:
    """Phase 6C production configuration using Context7 best practices"""
    # Performance settings
    max_concurrent_companies: int = 5
    max_pages_per_company: int = 8
    request_timeout: int = 30
    
    # Content extraction settings
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
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
            ]

@dataclass 
class Executive:
    """Executive data structure"""
    name: str
    title: str = ""
    email: str = ""
    phone: str = ""
    linkedin_url: str = ""
    source_url: str = ""
    confidence_score: float = 0.0
    business_context: str = ""
    extraction_method: str = ""
    last_updated: datetime = None

@dataclass
class Phase6CResult:
    """Phase 6C pipeline result structure"""
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

class Phase6CWebSession:
    """Production web session using Context7 best practices"""
    
    def __init__(self, config: Phase6CConfig):
        self.config = config
        self.session = None
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
    
    async def fetch_content(self, url: str) -> Tuple[str, bool]:
        """Fetch page content using Context7 best practices"""
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
            logger.warning(f"Request failed for {url}: {e}")
            return "", False
    
    def cleanup(self):
        """Cleanup resources"""
        if self.session:
            self.session.close()

class Phase6CNameValidator:
    """Simple name validator for Phase 6C"""
    
    def __init__(self):
        # Service terms to avoid (fake names)
        self.service_terms = [
            'heating', 'cooling', 'hvac', 'plumbing', 'electrical', 'service', 
            'repair', 'company', 'business', 'solutions', 'systems'
        ]
        
        # Valid name patterns
        self.valid_patterns = [
            r'^[A-Z][a-z]+ [A-Z][a-z]+$',  # First Last
            r'^[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+$',  # First M. Last
        ]

    def validate_name_pattern(self, name: str) -> bool:
        """Basic pattern validation for names"""
        if not name or len(name.split()) < 2:
            return False
            
        # Check for service terms
        name_lower = name.lower()
        for term in self.service_terms:
            if term in name_lower:
                return False
        
        # Check valid patterns
        return any(re.match(pattern, name) for pattern in self.valid_patterns)

    def is_real_executive_name(self, name: str) -> bool:
        """Main validation method"""
        return self.validate_name_pattern(name)

    def get_name_quality_score(self, name: str) -> float:
        """Get quality score for a name"""
        return 0.8 if self.is_real_executive_name(name) else 0.2

class Phase6CContentAnalyzer:
    """Production content analyzer using Context7 BeautifulSoup best practices"""
    
    def __init__(self, config: Phase6CConfig):
        self.config = config
        self.name_validator = Phase6CNameValidator()
        
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
        }
    
    def analyze_content(self, content: str, company_name: str, url: str) -> List[Executive]:
        """Analyze content for executives using Context7 techniques"""
        try:
            # Context7 BeautifulSoup parsing with strainer
            soup = BeautifulSoup(content, 'html.parser', parse_only=self.executive_strainer)
            
            # Clean and extract text
            text_content = self._extract_clean_text(soup)
            
            # Find executives
            executives = self._extract_executives(text_content, company_name, url)
            
            return executives
            
        except Exception as e:
            logger.error(f"Content analysis error for {url}: {e}")
            return []
    
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
                    
                    # Extract contact info
                    phone, email = self._extract_contact_info(text, name)
                    
                    # Create executive
                    executive = Executive(
                        name=name,
                        title=title,
                        email=email,
                        phone=phone,
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
    
    def _extract_contact_info(self, text: str, name: str) -> Tuple[str, str]:
        """Extract phone and email for specific executive"""
        phone = ""
        email = ""
        
        # Look for phone numbers
        phone_matches = re.findall(self.business_patterns['phone'], text, re.IGNORECASE)
        if phone_matches:
            phone = phone_matches[0]
        
        # Look for email addresses
        email_matches = re.findall(self.business_patterns['email'], text, re.IGNORECASE)
        if email_matches:
            email = email_matches[0]
        
        return phone, email
    
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

class Phase6CExecutivePipeline:
    """Phase 6C executive discovery pipeline - Production Ready"""
    
    def __init__(self, config: Optional[Phase6CConfig] = None):
        self.config = config or Phase6CConfig()
        self.analyzer = Phase6CContentAnalyzer(self.config)
        self.results = []
        
        # Performance metrics
        self.start_time = None
        self.companies_processed = 0
        self.total_executives_found = 0
        self.total_pages_analyzed = 0
        
    async def discover_executives_for_company(self, company_name: str, website_url: str) -> Phase6CResult:
        """Discover executives for a single company"""
        start_time = time.time()
        executives = []
        pages_analyzed = 0
        discovery_sources = []
        errors = []
        
        # Get web session
        session = Phase6CWebSession(self.config)
        
        try:
            # Discover pages to analyze
            pages_to_analyze = await self._discover_relevant_pages(website_url, session)
            
            # Analyze each page
            for page_url in pages_to_analyze[:self.config.max_pages_per_company]:
                try:
                    content, success = await session.fetch_content(page_url)
                    if success and content:
                        page_executives = self.analyzer.analyze_content(
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
            
            return Phase6CResult(
                company_id=f"phase6c_{int(time.time())}_{len(self.results)}",
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
            
            return Phase6CResult(
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
    
    async def _discover_relevant_pages(self, base_url: str, session: Phase6CWebSession) -> List[str]:
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
    
    async def process_companies_batch(self, companies: List[Tuple[str, str]]) -> List[Phase6CResult]:
        """Process multiple companies concurrently"""
        logger.info(f"🚀 Starting Phase 6C production batch processing for {len(companies)} companies")
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
        logger.info(f"✅ Phase 6C batch processing complete in {total_time:.2f}s")
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
            'phase6c_summary': {
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
                            'email': exec.email,
                            'phone': exec.phone,
                            'has_contact_info': bool(exec.email or exec.phone)
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
            filename = f'phase6c_production_results_{timestamp}.json'
        
        report = self.generate_production_report()
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 Phase 6C production results saved to {filename}")
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
    """Main Phase 6C production pipeline execution"""
    logger.info("🏭 PHASE 6C PRODUCTION EXECUTIVE DISCOVERY PIPELINE")
    logger.info("=" * 70)
    logger.info("Using Context7 best practices for enterprise-grade performance")
    logger.info("=" * 70)
    
    # Initialize production pipeline with conservative settings
    config = Phase6CConfig(
        max_concurrent_companies=3,  # Conservative for stability
        max_pages_per_company=5,     # Focus on quality over quantity
        request_timeout=30,
        min_confidence_score=0.6     # High quality threshold
    )
    
    pipeline = Phase6CExecutivePipeline(config)
    
    try:
        # Process test companies
        logger.info(f"Processing {len(PHASE6C_TEST_COMPANIES)} companies with Phase 6C pipeline...")
        results = await pipeline.process_companies_batch(PHASE6C_TEST_COMPANIES)
        
        # Generate and save report
        report_file = await pipeline.save_production_results()
        
        # Display summary
        report = pipeline.generate_production_report()
        summary = report['phase6c_summary']
        performance = report['performance_metrics']
        
        logger.info("\n" + "=" * 70)
        logger.info("🎯 PHASE 6C PRODUCTION RESULTS SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Companies Processed: {summary['total_companies_processed']}")
        logger.info(f"Executives Found: {summary['total_executives_found']}")
        logger.info(f"Success Rate: {summary['success_rate']:.1%}")
        logger.info(f"Avg Quality Score: {summary['average_quality_score']:.2f}")
        logger.info(f"Contact Completeness: {summary['average_contact_completeness']:.1%}")
        logger.info(f"Processing Time: {summary['total_processing_time']:.1f}s")
        logger.info(f"Companies/Hour: {performance['companies_per_hour']:.1f}")
        logger.info(f"Executives/Company: {performance['executives_per_company']:.1f}")
        logger.info("=" * 70)
        logger.info(f"📄 Results saved to: {report_file}")
        logger.info("=" * 70)
        
        # Show top discoveries
        if report['top_discoveries']:
            logger.info("\n🏆 TOP DISCOVERIES:")
            for discovery in report['top_discoveries'][:3]:
                logger.info(f"  • {discovery['company_name']}: {discovery['executives_count']} executives")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Phase 6C production pipeline failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 