"""
SEO Performance Analyzer

Multi-factor SEO analysis with business context awareness.
Integrates Google PageSpeed Insights API with intelligent rate limiting.

Based on creative design decisions:
- Multi-factor weighted scoring (PageSpeed 40%, meta 15%, mobile 15%, load time 15%, H1 10%, SSL 5%)
- Business context multipliers for company size and sector
- Intelligent rate limiting with caching and retry logic
"""

import asyncio
import logging
import time
import hashlib
from typing import Dict, Optional, List, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup

from ..config import get_api_config, get_processing_config
from ..database import get_db_session
from ..models import UKCompany, SEOAnalysis, SEOPerformance, SEOContent, SECTOR_SEO_DEPENDENCY

logger = logging.getLogger(__name__)

@dataclass
class SEOFactors:
    """Individual SEO factor scores"""
    pagespeed_score: float = 0.0
    meta_description_present: bool = False
    mobile_friendly: bool = False
    load_time: float = 0.0
    h1_tags_present: bool = False
    ssl_certificate: bool = False
    critical_issues: List[str] = None
    
    def __post_init__(self):
        if self.critical_issues is None:
            self.critical_issues = []

class SEOAnalyzer:
    """
    SEO performance analyzer with multi-factor scoring
    
    Features:
    - Google PageSpeed Insights integration
    - On-page SEO analysis via web scraping
    - Business context-aware scoring
    - Intelligent caching and rate limiting
    """
    
    def __init__(self):
        self.api_config = get_api_config()
        self.processing_config = get_processing_config()
        
        # Initialize Google PageSpeed API
        self.pagespeed_service = None
        if self.api_config.google_api_key:
            try:
                self.pagespeed_service = build('pagespeedonline', 'v5', 
                                             developerKey=self.api_config.google_api_key)
                logger.info("Google PageSpeed API initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize PageSpeed API: {e}")
        
        # Rate limiting state
        self.last_api_call = 0
        self.api_call_count = 0
        self.api_call_window_start = time.time()
        
        # Caching for repeated analysis
        self.analysis_cache = {}
        
        # Scoring weights (from creative design)
        self.weights = {
            'pagespeed': 0.40,
            'meta_description': 0.15,
            'mobile_friendly': 0.15,
            'load_time': 0.15,
            'h1_tags': 0.10,
            'ssl_certificate': 0.05
        }
    
    def _enforce_rate_limit(self):
        """Enforce Google API rate limiting (25 requests per hour)"""
        current_time = time.time()
        
        # Reset counter if hour has passed
        if current_time - self.api_call_window_start >= 3600:
            self.api_call_count = 0
            self.api_call_window_start = current_time
        
        # Check if we've hit the hourly limit
        if self.api_call_count >= self.api_config.pagespeed_requests_per_hour:
            wait_time = 3600 - (current_time - self.api_call_window_start)
            logger.warning(f"API rate limit reached. Waiting {wait_time:.0f} seconds")
            time.sleep(wait_time)
            
            # Reset after waiting
            self.api_call_count = 0
            self.api_call_window_start = time.time()
        
        self.api_call_count += 1
        self.last_api_call = current_time
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for URL analysis"""
        return hashlib.md5(url.lower().encode()).hexdigest()
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for analysis"""
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        # Remove trailing slash and www prefix for consistency
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return f"https://{domain}"
    
    async def analyze_website_seo(self, company_id: str, website_url: str, 
                                 company_sector: Optional[str] = None,
                                 company_size: Optional[str] = None) -> Optional[SEOAnalysis]:
        """
        Comprehensive SEO analysis for a website
        
        Args:
            company_id: Unique company identifier
            website_url: Company website URL
            company_sector: Business sector for context
            company_size: Company size for context
            
        Returns:
            SEOAnalysis object with scores and recommendations
        """
        try:
            # Normalize URL
            url = self._normalize_url(website_url)
            cache_key = self._get_cache_key(url)
            
            # Check cache first
            if cache_key in self.analysis_cache:
                logger.debug(f"Using cached analysis for {url}")
                return self.analysis_cache[cache_key]
            
            logger.info(f"Analyzing SEO for {url}")
            
            # Collect SEO factors
            seo_factors = await self._collect_seo_factors(url)
            
            # Calculate weighted score
            overall_score = self._calculate_weighted_score(seo_factors, company_sector, company_size)
            
            # Build analysis result
            analysis = SEOAnalysis(
                overall_score=overall_score,
                performance=SEOPerformance(
                    pagespeed_score=seo_factors.pagespeed_score,
                    load_time=seo_factors.load_time,
                    mobile_friendly=seo_factors.mobile_friendly
                ),
                content=SEOContent(
                    meta_description_missing=not seo_factors.meta_description_present,
                    h1_tags_present=seo_factors.h1_tags_present,
                    ssl_certificate=seo_factors.ssl_certificate
                ),
                critical_issues=seo_factors.critical_issues
            )
            
            # Cache the result
            self.analysis_cache[cache_key] = analysis
            
            # Update database
            self._update_company_seo_data(company_id, analysis)
            
            logger.info(f"SEO analysis complete for {url}: Score {overall_score:.1f}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing SEO for {website_url}: {e}")
            return None
    
    async def _collect_seo_factors(self, url: str) -> SEOFactors:
        """Collect all SEO factors for analysis"""
        factors = SEOFactors()
        
        # Collect PageSpeed data (if API available)
        if self.pagespeed_service:
            pagespeed_data = await self._get_pagespeed_data(url)
            if pagespeed_data:
                factors.pagespeed_score = pagespeed_data.get('performance_score', 0)
                factors.load_time = pagespeed_data.get('load_time', 0)
                factors.mobile_friendly = pagespeed_data.get('mobile_friendly', False)
        
        # Collect on-page SEO data
        onpage_data = await self._analyze_onpage_seo(url)
        if onpage_data:
            factors.meta_description_present = onpage_data.get('meta_description', False)
            factors.h1_tags_present = onpage_data.get('h1_tags', False)
            factors.ssl_certificate = onpage_data.get('ssl', False)
            factors.critical_issues.extend(onpage_data.get('issues', []))
        
        return factors
    
    async def _get_pagespeed_data(self, url: str) -> Optional[Dict]:
        """Get PageSpeed Insights data with rate limiting"""
        try:
            # Enforce rate limiting
            self._enforce_rate_limit()
            
            # Make API request
            request = self.pagespeed_service.pagespeedapi().runpagespeed(
                url=url,
                category=['PERFORMANCE', 'ACCESSIBILITY', 'SEO'],
                strategy='MOBILE'
            )
            
            response = request.execute()
            
            # Extract key metrics
            lighthouse_result = response.get('lighthouseResult', {})
            categories = lighthouse_result.get('categories', {})
            audits = lighthouse_result.get('audits', {})
            
            performance_score = 0
            if 'performance' in categories:
                performance_score = categories['performance']['score'] * 100
            
            # Extract load time metrics
            load_time = 0
            if 'first-contentful-paint' in audits:
                fcp = audits['first-contentful-paint']['numericValue']
                load_time = fcp / 1000  # Convert to seconds
            
            # Check mobile friendliness
            mobile_friendly = False
            if 'viewport' in audits:
                mobile_friendly = audits['viewport']['score'] == 1
            
            return {
                'performance_score': performance_score,
                'load_time': load_time,
                'mobile_friendly': mobile_friendly
            }
            
        except HttpError as e:
            if e.resp.status == 429:  # Rate limited
                logger.warning("API rate limit hit, implementing backoff")
                time.sleep(self.api_config.pagespeed_retry_delay)
                return None
            else:
                logger.error(f"PageSpeed API error for {url}: {e}")
                return None
        except Exception as e:
            logger.error(f"Error getting PageSpeed data for {url}: {e}")
            return None
    
    async def _analyze_onpage_seo(self, url: str) -> Optional[Dict]:
        """Analyze on-page SEO factors via web scraping"""
        try:
            # Make HTTP request with timeout
            headers = {
                'User-Agent': self.api_config.browser_user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            issues = []
            
            # Check meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            has_meta_desc = meta_desc is not None and meta_desc.get('content', '').strip()
            if not has_meta_desc:
                issues.append("Missing meta description")
            
            # Check H1 tags
            h1_tags = soup.find_all('h1')
            has_h1 = len(h1_tags) > 0
            if not has_h1:
                issues.append("Missing H1 tag")
            elif len(h1_tags) > 1:
                issues.append("Multiple H1 tags detected")
            
            # Check SSL (from URL scheme)
            has_ssl = url.startswith('https://')
            if not has_ssl:
                issues.append("No SSL certificate (not using HTTPS)")
            
            # Check title tag
            title = soup.find('title')
            if not title or not title.get_text(strip=True):
                issues.append("Missing or empty title tag")
            
            return {
                'meta_description': has_meta_desc,
                'h1_tags': has_h1,
                'ssl': has_ssl,
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"Error analyzing on-page SEO for {url}: {e}")
            return None
    
    def _calculate_weighted_score(self, factors: SEOFactors, 
                                company_sector: Optional[str] = None,
                                company_size: Optional[str] = None) -> float:
        """Calculate weighted SEO score with business context"""
        
        # Base weighted score calculation
        score = 0.0
        
        # PageSpeed score (40% weight)
        score += (factors.pagespeed_score / 100) * self.weights['pagespeed']
        
        # Meta description (15% weight)
        score += (1.0 if factors.meta_description_present else 0.0) * self.weights['meta_description']
        
        # Mobile friendly (15% weight)
        score += (1.0 if factors.mobile_friendly else 0.0) * self.weights['mobile_friendly']
        
        # Load time (15% weight) - inverted scoring (faster = better)
        load_time_score = max(0, 1.0 - (factors.load_time / 5.0))  # 5 seconds = 0 score
        score += load_time_score * self.weights['load_time']
        
        # H1 tags (10% weight)
        score += (1.0 if factors.h1_tags_present else 0.0) * self.weights['h1_tags']
        
        # SSL certificate (5% weight)
        score += (1.0 if factors.ssl_certificate else 0.0) * self.weights['ssl_certificate']
        
        # Convert to 0-100 scale
        base_score = score * 100
        
        # Apply business context multipliers
        final_score = self._apply_business_context(base_score, company_sector, company_size)
        
        return round(final_score, 1)
    
    def _apply_business_context(self, base_score: float, 
                              company_sector: Optional[str] = None,
                              company_size: Optional[str] = None) -> float:
        """Apply business context multipliers to base SEO score"""
        
        # Sector SEO dependency multiplier
        sector_multiplier = 1.0
        if company_sector and company_sector in SECTOR_SEO_DEPENDENCY:
            # Higher dependency = lower tolerance for poor SEO
            dependency = SECTOR_SEO_DEPENDENCY[company_sector]
            if dependency >= 90:
                sector_multiplier = 1.2  # High dependency sectors penalized more
            elif dependency >= 80:
                sector_multiplier = 1.1
            elif dependency <= 70:
                sector_multiplier = 0.9   # Low dependency sectors penalized less
        
        # Company size multiplier (larger companies should have better SEO)
        size_multiplier = 1.0
        if company_size:
            if company_size == 'large':
                size_multiplier = 1.15    # Large companies expected to have better SEO
            elif company_size == 'medium':
                size_multiplier = 1.05
            # Small/micro companies get no penalty
        
        # Apply multipliers (but cap at reasonable bounds)
        adjusted_score = base_score * sector_multiplier * size_multiplier
        
        return min(100.0, max(0.0, adjusted_score))
    
    def _update_company_seo_data(self, company_id: str, analysis: SEOAnalysis):
        """Update company record with SEO analysis results"""
        try:
            with get_db_session() as session:
                company = session.query(UKCompany).filter_by(id=company_id).first()
                
                if company:
                    # Update SEO fields
                    company.seo_overall_score = analysis.overall_score
                    company.pagespeed_score = analysis.performance.pagespeed_score
                    company.mobile_friendly = analysis.performance.mobile_friendly
                    company.meta_description_missing = analysis.content.meta_description_missing
                    company.h1_tags_present = analysis.content.h1_tags_present
                    company.ssl_certificate = analysis.content.ssl_certificate
                    company.load_time = analysis.performance.load_time
                    company.critical_issues = analysis.critical_issues
                    
                    # Update status
                    if company.status == 'contacts_extracted':
                        company.status = 'seo_analyzed'
                    
                    session.commit()
                    logger.debug(f"Updated SEO data for company {company_id}")
                
        except Exception as e:
            logger.error(f"Error updating company SEO data: {e}")
    
    def analyze_batch(self, batch_size: int = 50) -> int:
        """Analyze SEO for a batch of companies that need analysis"""
        try:
            with get_db_session() as session:
                # Get companies needing SEO analysis
                companies = session.query(UKCompany).filter(
                    UKCompany.status == 'contacts_extracted',
                    UKCompany.website.isnot(None)
                ).limit(batch_size).all()
                
                if not companies:
                    logger.info("No companies found needing SEO analysis")
                    return 0
                
                logger.info(f"Starting SEO analysis for {len(companies)} companies")
                analyzed_count = 0
                
                for company in companies:
                    try:
                        # Run analysis
                        analysis = asyncio.run(
                            self.analyze_website_seo(
                                company.id, 
                                company.website,
                                company.sector,
                                company.size_category
                            )
                        )
                        
                        if analysis:
                            analyzed_count += 1
                            logger.info(f"Analyzed {company.company_name}: Score {analysis.overall_score}")
                        
                        # Respect rate limiting
                        time.sleep(2)  # 2 second delay between companies
                        
                    except Exception as e:
                        logger.error(f"Error analyzing {company.company_name}: {e}")
                        continue
                
                logger.info(f"SEO analysis batch complete: {analyzed_count}/{len(companies)} analyzed")
                return analyzed_count
                
        except Exception as e:
            logger.error(f"Error in SEO analysis batch: {e}")
            return 0

# Convenience function
def analyze_seo_batch(batch_size: int = 50) -> int:
    """Convenience function to analyze SEO for a batch of companies"""
    analyzer = SEOAnalyzer()
    return analyzer.analyze_batch(batch_size)

if __name__ == "__main__":
    # Test the analyzer
    analyzer = SEOAnalyzer()
    
    # Test with a sample website
    import asyncio
    
    async def test_analyzer():
        result = await analyzer.analyze_website_seo(
            "test123", 
            "https://example.com",
            "retail",
            "small"
        )
        if result:
            print(f"SEO Score: {result.overall_score}")
            print(f"Critical Issues: {result.critical_issues}")
    
    asyncio.run(test_analyzer()) 