"""
Phase 4A Enhanced Multi-Source Executive Discovery Engine
Advanced ML-powered executive discovery with 70%+ target success rate
Integration of advanced content extraction and enhanced AI classification
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import requests

from ..extractors.advanced_content_extractor import (
    AdvancedContentExtractor, 
    ExtractedExecutive,
    ExtractionContext
)
from ..ai.enhanced_executive_classifier import (
    EnhancedExecutiveClassifier,
    ExecutiveCandidate
)
from ..models import ExecutiveContact
from ..enrichers.executive_contact_enricher import ExecutiveContactEnricher
from ..scrapers.linkedin_professional_scraper import LinkedInProfessionalScraper

logger = logging.getLogger(__name__)

@dataclass
class EnhancedDiscoveryResult:
    """Enhanced discovery result with detailed analytics"""
    company_name: str
    website_url: str
    executives: List[ExecutiveContact]
    processing_time: float
    success: bool
    total_candidates_found: int
    ml_processed_candidates: int
    final_executives_count: int
    extraction_methods_used: List[str]
    confidence_distribution: Dict[str, int]
    analytics: Dict[str, Any] = field(default_factory=dict)

class Phase4AEnhancedEngine:
    """Phase 4A Enhanced Multi-Source Executive Discovery Engine"""
    
    def __init__(self):
        self.advanced_extractor = AdvancedContentExtractor()
        self.ml_classifier = EnhancedExecutiveClassifier()
        # Note: Commented out enrichers to avoid integration issues for now
        # self.contact_enricher = ExecutiveContactEnricher()
        # self.linkedin_scraper = LinkedInProfessionalScraper()
        
        # Performance tracking
        self.stats = {
            'total_companies_processed': 0,
            'successful_companies': 0,
            'total_executives_found': 0,
            'total_processing_time': 0,
            'method_success_rates': {}
        }
        
        # Enhanced configuration
        self.config = {
            'min_confidence_threshold': 0.4,
            'max_executives_per_company': 15,
            'enable_linkedin_enrichment': False,  # Disabled for now
            'enable_contact_enrichment': False,   # Disabled for now
            'enable_parallel_processing': True,
            'timeout_seconds': 60,
            'quality_over_quantity': True
        }
    
    async def discover_executives_enhanced(self, company_data: Dict[str, Any]) -> EnhancedDiscoveryResult:
        """Main enhanced executive discovery method"""
        company_name = company_data.get('name', 'Unknown Company')
        website_url = company_data.get('website', '')
        
        logger.info(f"🚀 Phase 4A Enhanced Discovery: {company_name}")
        start_time = time.time()
        
        try:
            # Step 1: Advanced content extraction
            extraction_result = await self._extract_content_advanced(website_url, company_name)
            
            if not extraction_result['success']:
                return self._create_failed_result(company_name, website_url, start_time, "Content extraction failed")
            
            # Step 2: ML-powered executive classification
            ml_result = await self._classify_executives_ml(
                extraction_result['content'], 
                company_name
            )
            
            # Step 3: Multi-source enrichment (simplified for now)
            enriched_executives = await self._enrich_executives_simple(
                ml_result['candidates'], 
                company_name,
                website_url
            )
            
            # Step 4: Quality assurance and ranking
            final_executives = self._apply_quality_assurance(enriched_executives, company_name)
            
            processing_time = time.time() - start_time
            
            # Create detailed result
            result = EnhancedDiscoveryResult(
                company_name=company_name,
                website_url=website_url,
                executives=final_executives,
                processing_time=processing_time,
                success=len(final_executives) > 0,
                total_candidates_found=extraction_result.get('total_candidates', 0),
                ml_processed_candidates=ml_result.get('processed_count', 0),
                final_executives_count=len(final_executives),
                extraction_methods_used=extraction_result.get('methods_used', []),
                confidence_distribution=self._calculate_confidence_distribution(final_executives)
            )
            
            # Update statistics
            self._update_statistics(result)
            
            logger.info(f"✅ Enhanced discovery complete: {len(final_executives)} executives found in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced discovery failed for {company_name}: {e}")
            return self._create_failed_result(company_name, website_url, start_time, str(e))
    
    async def _extract_content_advanced(self, website_url: str, company_name: str) -> Dict[str, Any]:
        """Advanced content extraction with multiple strategies"""
        try:
            # Fetch website content
            content_result = await self._fetch_website_content(website_url)
            
            if not content_result['success']:
                return {'success': False, 'error': content_result['error']}
            
            html_content = content_result['content']
            
            # Advanced extraction using multiple methods
            extracted_executives = self.advanced_extractor.extract_executives_advanced(
                html_content, website_url, company_name
            )
            
            # Collect extraction methods used
            methods_used = list(set([exec.extraction_method for exec in extracted_executives]))
            
            logger.info(f"📋 Advanced extraction: {len(extracted_executives)} candidates from {len(methods_used)} methods")
            
            return {
                'success': True,
                'content': html_content,
                'executives': extracted_executives,
                'total_candidates': len(extracted_executives),
                'methods_used': methods_used
            }
            
        except Exception as e:
            logger.error(f"❌ Advanced content extraction failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _fetch_website_content(self, website_url: str) -> Dict[str, Any]:
        """Fetch website content with enhanced error handling"""
        if not website_url:
            return {'success': False, 'error': 'No website URL provided'}
        
        # Ensure URL has protocol
        if not website_url.startswith(('http://', 'https://')):
            website_url = f'https://{website_url}'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(website_url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        return {'success': True, 'content': content}
                    else:
                        return {'success': False, 'error': f'HTTP {response.status}'}
                        
        except Exception as e:
            logger.warning(f"⚠️ Async fetch failed, trying sync: {e}")
            
            # Fallback to synchronous request
            try:
                response = requests.get(website_url, headers=headers, timeout=30)
                if response.status_code == 200:
                    return {'success': True, 'content': response.text}
                else:
                    return {'success': False, 'error': f'HTTP {response.status_code}'}
            except Exception as sync_e:
                return {'success': False, 'error': f'Both async and sync failed: {sync_e}'}
    
    async def _classify_executives_ml(self, html_content: str, company_name: str) -> Dict[str, Any]:
        """ML-powered executive classification"""
        try:
            # Extract text content from HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Run ML classification
            candidates = self.ml_classifier.classify_executives(text_content, company_name)
            
            logger.info(f"🧠 ML Classification: {len(candidates)} high-quality candidates identified")
            
            return {
                'success': True,
                'candidates': candidates,
                'processed_count': len(candidates)
            }
            
        except Exception as e:
            logger.error(f"❌ ML classification failed: {e}")
            return {'success': False, 'error': str(e), 'candidates': []}
    
    async def _enrich_executives_simple(self, candidates: List[ExecutiveCandidate], 
                                      company_name: str, website_url: str) -> List[ExecutiveContact]:
        """Simplified executive enrichment without external dependencies"""
        enriched_executives = []
        
        for candidate in candidates:
            try:
                # Extract domain from website URL
                domain = website_url.replace('https://', '').replace('http://', '').split('/')[0]
                
                # Convert candidate to ExecutiveContact with proper parameters
                executive_contact = ExecutiveContact(
                    first_name=candidate.first_name,
                    last_name=candidate.last_name,
                    full_name=candidate.full_name,
                    title=candidate.title or "Executive",
                    seniority_tier="tier_2",  # Default tier
                    company_name=company_name,
                    company_domain=domain,
                    email=getattr(candidate, 'email', None),
                    phone=getattr(candidate, 'phone', None),
                    overall_confidence=candidate.confidence_score,
                    discovery_sources=['website'],
                    discovery_method=candidate.extraction_method
                )
                
                enriched_executives.append(executive_contact)
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to convert candidate {candidate.full_name}: {e}")
                continue
        
        logger.info(f"🔍 Simple enrichment: {len(enriched_executives)} executives processed")
        return enriched_executives
    
    def _apply_quality_assurance(self, executives: List[ExecutiveContact], company_name: str) -> List[ExecutiveContact]:
        """Apply quality assurance and final filtering"""
        # Filter by minimum confidence threshold
        qualified_executives = [
            exec for exec in executives 
            if exec.overall_confidence >= self.config['min_confidence_threshold']
        ]
        
        # Remove obvious business names
        filtered_executives = []
        for executive in qualified_executives:
            if not self._is_business_name_final_check(executive, company_name):
                filtered_executives.append(executive)
        
        # Sort by confidence and limit results
        filtered_executives.sort(key=lambda x: x.overall_confidence, reverse=True)
        
        # Apply quantity limit while maintaining quality
        max_executives = self.config['max_executives_per_company']
        final_executives = filtered_executives[:max_executives]
        
        logger.info(f"🎯 Quality assurance: {len(final_executives)} high-quality executives selected")
        return final_executives
    
    def _is_business_name_final_check(self, executive: ExecutiveContact, company_name: str) -> bool:
        """Final check for business names"""
        full_name = f"{executive.first_name} {executive.last_name}".lower()
        
        # Check against company name
        if company_name and any(word in full_name for word in company_name.lower().split() if len(word) > 3):
            return True
        
        # Check for business indicators
        business_indicators = [
            'plumbing', 'heating', 'gas', 'services', 'emergency', 'qualified',
            'certified', 'professional', 'company', 'business', 'ltd', 'limited'
        ]
        
        return any(indicator in full_name for indicator in business_indicators)
    
    def _calculate_confidence_distribution(self, executives: List[ExecutiveContact]) -> Dict[str, int]:
        """Calculate confidence score distribution"""
        distribution = {'high': 0, 'medium': 0, 'low': 0}
        
        for executive in executives:
            if executive.overall_confidence >= 0.7:
                distribution['high'] += 1
            elif executive.overall_confidence >= 0.5:
                distribution['medium'] += 1
            else:
                distribution['low'] += 1
        
        return distribution
    
    def _update_statistics(self, result: EnhancedDiscoveryResult):
        """Update engine statistics"""
        self.stats['total_companies_processed'] += 1
        if result.success:
            self.stats['successful_companies'] += 1
        self.stats['total_executives_found'] += result.final_executives_count
        self.stats['total_processing_time'] += result.processing_time
    
    def _create_failed_result(self, company_name: str, website_url: str, start_time: float, error: str) -> EnhancedDiscoveryResult:
        """Create a failed result object"""
        return EnhancedDiscoveryResult(
            company_name=company_name,
            website_url=website_url,
            executives=[],
            processing_time=time.time() - start_time,
            success=False,
            total_candidates_found=0,
            ml_processed_candidates=0,
            final_executives_count=0,
            extraction_methods_used=[],
            confidence_distribution={'high': 0, 'medium': 0, 'low': 0},
            analytics={'error': error}
        )
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """Get detailed performance analytics"""
        if self.stats['total_companies_processed'] == 0:
            return {'message': 'No companies processed yet'}
        
        success_rate = (self.stats['successful_companies'] / self.stats['total_companies_processed']) * 100
        avg_processing_time = self.stats['total_processing_time'] / self.stats['total_companies_processed']
        avg_executives_per_company = self.stats['total_executives_found'] / max(1, self.stats['successful_companies'])
        
        return {
            'success_rate_percentage': round(success_rate, 2),
            'total_companies_processed': self.stats['total_companies_processed'],
            'successful_companies': self.stats['successful_companies'],
            'total_executives_found': self.stats['total_executives_found'],
            'average_processing_time_seconds': round(avg_processing_time, 2),
            'average_executives_per_successful_company': round(avg_executives_per_company, 2),
            'performance_status': 'EXCELLENT' if success_rate >= 70 else 'GOOD' if success_rate >= 50 else 'NEEDS_IMPROVEMENT'
        }

# Convenience function for easy testing
async def test_phase4a_enhanced_discovery(test_companies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Test the Phase 4A Enhanced Discovery Engine"""
    engine = Phase4AEnhancedEngine()
    
    logger.info(f"🧪 Testing Phase 4A Enhanced Discovery with {len(test_companies)} companies")
    
    results = []
    total_start_time = time.time()
    
    for company in test_companies:
        result = await engine.discover_executives_enhanced(company)
        results.append(result)
        
        # Log individual result
        status = "✅ SUCCESS" if result.success else "❌ FAILED"
        logger.info(f"{status}: {result.company_name} - {result.final_executives_count} executives, {result.processing_time:.2f}s")
    
    total_time = time.time() - total_start_time
    
    # Calculate overall statistics
    successful_companies = sum(1 for r in results if r.success)
    total_executives = sum(r.final_executives_count for r in results)
    success_rate = (successful_companies / len(test_companies)) * 100
    
    summary = {
        'test_summary': {
            'total_companies': len(test_companies),
            'successful_companies': successful_companies,
            'success_rate_percentage': round(success_rate, 2),
            'total_executives_found': total_executives,
            'total_processing_time': round(total_time, 2),
            'average_processing_time': round(total_time / len(test_companies), 2),
            'target_achievement': 'ACHIEVED' if success_rate >= 70 else 'IN_PROGRESS' if success_rate >= 50 else 'NEEDS_WORK'
        },
        'detailed_results': results,
        'performance_analytics': engine.get_performance_analytics()
    }
    
    logger.info(f"🎯 Phase 4A Test Complete: {success_rate:.1f}% success rate, {total_executives} executives found")
    
    return summary 