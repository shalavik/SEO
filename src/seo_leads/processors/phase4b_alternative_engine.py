"""
Phase 4B Alternative Data Sources Engine
Integrates multiple alternative data sources for executive discovery:
- Companies House API for UK director information
- Social media profile discovery
- Website health checking with fallback mechanisms
- Alternative content source aggregation
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Internal imports
from ..models import ExecutiveContact
from ..integrations.companies_house_api import CompaniesHouseExecutiveExtractor, CompaniesHouseDirector
from ..scrapers.social_media_scraper import SocialMediaExecutiveExtractor, SocialMediaExecutive
from ..analyzers.website_health_checker import EnhancedWebsiteFetcher, WebsiteHealthStatus

logger = logging.getLogger(__name__)

@dataclass
class AlternativeDiscoveryResult:
    """Result from alternative discovery sources"""
    source_type: str  # companies_house, social_media, website_fallback
    executives_found: List[ExecutiveContact]
    confidence_score: float
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Phase4BResults:
    """Combined results from Phase 4B alternative data sources"""
    company_name: str
    company_url: str
    website_health: WebsiteHealthStatus
    
    # Alternative source results
    companies_house_results: AlternativeDiscoveryResult
    social_media_results: AlternativeDiscoveryResult
    fallback_content_results: AlternativeDiscoveryResult
    
    # Combined results
    total_executives_found: int = 0
    unique_executives: List[ExecutiveContact] = field(default_factory=list)
    best_source: str = ""
    overall_confidence: float = 0.0
    total_processing_time: float = 0.0
    
    # Quality metrics
    data_quality_score: float = 0.0
    source_diversity_score: float = 0.0
    verification_score: float = 0.0

class Phase4BAlternativeEngine:
    """Phase 4B Engine for alternative data source discovery"""
    
    def __init__(self):
        self.companies_house_extractor = CompaniesHouseExecutiveExtractor()
        self.social_media_extractor = SocialMediaExecutiveExtractor()
        self.enhanced_fetcher = EnhancedWebsiteFetcher()
        
        # Performance tracking
        self.stats = {
            'total_processed': 0,
            'companies_house_successes': 0,
            'social_media_successes': 0,
            'fallback_successes': 0,
            'average_processing_time': 0.0
        }
    
    async def discover_executives_alternative_sources(self, 
                                                    company_name: str, 
                                                    company_url: str) -> Phase4BResults:
        """
        Discover executives using alternative data sources
        Phase 4B main processing function
        """
        logger.info(f"🚀 Phase 4B Alternative Discovery: {company_name}")
        start_time = time.time()
        
        # Initialize results container
        results = Phase4BResults(
            company_name=company_name,
            company_url=company_url,
            website_health=None,
            companies_house_results=None,
            social_media_results=None,
            fallback_content_results=None
        )
        
        # Step 1: Website Health Check
        logger.info(f"🔍 Step 1: Website Health Assessment")
        website_content, website_health = await self.enhanced_fetcher.fetch_with_fallbacks(company_url)
        results.website_health = website_health
        
        # Step 2: Run all alternative discovery methods in parallel
        logger.info(f"🔄 Step 2: Parallel Alternative Source Discovery")
        
        discovery_tasks = [
            self._discover_via_companies_house(company_name),
            self._discover_via_social_media(company_name),
            self._discover_via_fallback_content(company_name, website_content, website_health)
        ]
        
        # Execute all discovery methods concurrently
        ch_results, sm_results, fb_results = await asyncio.gather(*discovery_tasks, return_exceptions=True)
        
        # Handle any exceptions
        if isinstance(ch_results, Exception):
            logger.error(f"Companies House discovery failed: {ch_results}")
            ch_results = self._create_empty_result("companies_house")
        
        if isinstance(sm_results, Exception):
            logger.error(f"Social media discovery failed: {sm_results}")
            sm_results = self._create_empty_result("social_media")
        
        if isinstance(fb_results, Exception):
            logger.error(f"Fallback content discovery failed: {fb_results}")
            fb_results = self._create_empty_result("website_fallback")
        
        # Store individual results
        results.companies_house_results = ch_results
        results.social_media_results = sm_results
        results.fallback_content_results = fb_results
        
        # Step 3: Combine and deduplicate results
        logger.info(f"🔀 Step 3: Result Combination and Deduplication")
        results.unique_executives = self._combine_and_deduplicate_executives([
            ch_results.executives_found,
            sm_results.executives_found,
            fb_results.executives_found
        ])
        
        results.total_executives_found = len(results.unique_executives)
        
        # Step 4: Calculate quality metrics
        logger.info(f"📊 Step 4: Quality Metrics Calculation")
        results.best_source = self._determine_best_source([ch_results, sm_results, fb_results])
        results.overall_confidence = self._calculate_overall_confidence(results)
        results.data_quality_score = self._calculate_data_quality_score(results)
        results.source_diversity_score = self._calculate_source_diversity_score(results)
        results.verification_score = self._calculate_verification_score(results)
        
        # Finalize metrics
        results.total_processing_time = time.time() - start_time
        
        # Update statistics
        self._update_statistics(results)
        
        logger.info(f"✅ Phase 4B Complete: {results.total_executives_found} executives found in {results.total_processing_time:.2f}s")
        
        return results
    
    async def _discover_via_companies_house(self, company_name: str) -> AlternativeDiscoveryResult:
        """Discover executives via Companies House API"""
        logger.info(f"🏢 Companies House Discovery: {company_name}")
        start_time = time.time()
        
        try:
            # Search Companies House for directors
            ch_directors = await self.companies_house_extractor.find_executives_by_company_name(company_name)
            
            # Convert to ExecutiveContact objects
            executives = []
            for director in ch_directors:
                executive = ExecutiveContact(
                    name=director.name,
                    title=director.title or director.officer_role,
                    company=company_name,
                    company_domain="",  # Not available from Companies House
                    confidence_score=0.9,  # High confidence from official registry
                    discovery_method="companies_house_api",
                    additional_info={
                        'nationality': director.nationality,
                        'occupation': director.occupation,
                        'appointment_date': str(director.appointment_date) if director.appointment_date else "",
                        'country_of_residence': director.country_of_residence,
                        'officer_role': director.officer_role
                    }
                )
                executives.append(executive)
            
            processing_time = time.time() - start_time
            
            result = AlternativeDiscoveryResult(
                source_type="companies_house",
                executives_found=executives,
                confidence_score=0.9 if executives else 0.0,
                processing_time=processing_time,
                metadata={
                    'directors_count': len(ch_directors),
                    'search_method': 'companies_house_api'
                }
            )
            
            if executives:
                self.stats['companies_house_successes'] += 1
                logger.info(f"✅ Companies House: Found {len(executives)} directors")
            else:
                logger.info(f"❌ Companies House: No directors found")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Companies House discovery failed: {e}")
            return AlternativeDiscoveryResult(
                source_type="companies_house",
                executives_found=[],
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                metadata={'error': str(e)}
            )
    
    async def _discover_via_social_media(self, company_name: str) -> AlternativeDiscoveryResult:
        """Discover executives via social media platforms"""
        logger.info(f"📱 Social Media Discovery: {company_name}")
        start_time = time.time()
        
        try:
            # Search social media platforms
            sm_executives = await self.social_media_extractor.find_executives_via_social_media(company_name)
            
            # Convert to ExecutiveContact objects
            executives = []
            for sm_exec in sm_executives:
                executive = ExecutiveContact(
                    name=sm_exec.name,
                    title=sm_exec.title,
                    company=company_name,
                    company_domain="",
                    confidence_score=sm_exec.confidence_score,
                    discovery_method="social_media_discovery",
                    additional_info={
                        'social_profiles': [
                            {
                                'platform': profile.platform,
                                'url': profile.profile_url,
                                'username': profile.username,
                                'confidence': profile.confidence_score
                            }
                            for profile in sm_exec.profiles
                        ],
                        'discovery_method': sm_exec.discovery_method
                    }
                )
                executives.append(executive)
            
            processing_time = time.time() - start_time
            
            result = AlternativeDiscoveryResult(
                source_type="social_media",
                executives_found=executives,
                confidence_score=max([e.confidence_score for e in executives]) if executives else 0.0,
                processing_time=processing_time,
                metadata={
                    'executives_count': len(sm_executives),
                    'search_method': 'multi_platform_social'
                }
            )
            
            if executives:
                self.stats['social_media_successes'] += 1
                logger.info(f"✅ Social Media: Found {len(executives)} executives")
            else:
                logger.info(f"❌ Social Media: No executives found")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Social Media discovery failed: {e}")
            return AlternativeDiscoveryResult(
                source_type="social_media",
                executives_found=[],
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                metadata={'error': str(e)}
            )
    
    async def _discover_via_fallback_content(self, 
                                           company_name: str, 
                                           website_content: Optional[str],
                                           website_health: WebsiteHealthStatus) -> AlternativeDiscoveryResult:
        """Discover executives via fallback content sources"""
        logger.info(f"🔄 Fallback Content Discovery: {company_name}")
        start_time = time.time()
        
        try:
            executives = []
            
            # If website is inaccessible, try alternative content sources
            if not website_health.is_accessible or website_health.content_quality_score < 0.3:
                logger.info(f"🔍 Website inaccessible/low quality, trying alternative sources")
                
                # This would integrate with additional fallback mechanisms:
                # - Wayback Machine archives
                # - Google Cache
                # - Alternative domain variations
                # - Third-party business directories
                
                # For Phase 4B implementation, we'll create a placeholder
                # In production, this would be fully implemented
                
                if website_health.alternative_urls:
                    for alt_url in website_health.alternative_urls[:2]:  # Try top 2 alternatives
                        alt_content, alt_health = await self.enhanced_fetcher.fetch_with_fallbacks(alt_url)
                        if alt_content and alt_health.content_quality_score > 0.5:
                            # Extract executives from alternative content
                            # This would use the advanced content extractor
                            logger.info(f"✅ Found alternative content source: {alt_url}")
                            break
            
            processing_time = time.time() - start_time
            
            result = AlternativeDiscoveryResult(
                source_type="website_fallback",
                executives_found=executives,
                confidence_score=0.5 if executives else 0.0,
                processing_time=processing_time,
                metadata={
                    'website_accessible': website_health.is_accessible,
                    'content_quality': website_health.content_quality_score,
                    'alternatives_tried': len(website_health.alternative_urls)
                }
            )
            
            if executives:
                self.stats['fallback_successes'] += 1
                logger.info(f"✅ Fallback Content: Found {len(executives)} executives")
            else:
                logger.info(f"❌ Fallback Content: No executives found")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Fallback content discovery failed: {e}")
            return AlternativeDiscoveryResult(
                source_type="website_fallback",
                executives_found=[],
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                metadata={'error': str(e)}
            )
    
    def _create_empty_result(self, source_type: str) -> AlternativeDiscoveryResult:
        """Create empty result for failed discovery"""
        return AlternativeDiscoveryResult(
            source_type=source_type,
            executives_found=[],
            confidence_score=0.0,
            processing_time=0.0,
            metadata={'status': 'failed'}
        )
    
    def _combine_and_deduplicate_executives(self, 
                                          executive_lists: List[List[ExecutiveContact]]) -> List[ExecutiveContact]:
        """Combine and deduplicate executives from multiple sources"""
        all_executives = []
        for exec_list in executive_lists:
            all_executives.extend(exec_list)
        
        if not all_executives:
            return []
        
        # Deduplicate by name similarity
        unique_executives = []
        seen_names = set()
        
        for executive in all_executives:
            name_key = self._normalize_name(executive.name)
            
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_executives.append(executive)
            else:
                # If duplicate, merge information from multiple sources
                for existing in unique_executives:
                    if self._normalize_name(existing.name) == name_key:
                        # Merge additional info and use higher confidence
                        if executive.confidence_score > existing.confidence_score:
                            existing.confidence_score = executive.confidence_score
                            existing.discovery_method += f", {executive.discovery_method}"
                        break
        
        # Sort by confidence score
        unique_executives.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return unique_executives
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for deduplication"""
        return name.lower().strip().replace('.', '').replace(',', '')
    
    def _determine_best_source(self, results: List[AlternativeDiscoveryResult]) -> str:
        """Determine which source provided the best results"""
        best_source = ""
        best_score = 0.0
        
        for result in results:
            # Score based on number of executives and confidence
            score = len(result.executives_found) * result.confidence_score
            
            if score > best_score:
                best_score = score
                best_source = result.source_type
        
        return best_source or "none"
    
    def _calculate_overall_confidence(self, results: Phase4BResults) -> float:
        """Calculate overall confidence in the results"""
        if not results.unique_executives:
            return 0.0
        
        # Weight by source reliability
        source_weights = {
            'companies_house': 0.9,
            'social_media': 0.6,
            'website_fallback': 0.5
        }
        
        total_weight = 0.0
        weighted_confidence = 0.0
        
        for result in [results.companies_house_results, results.social_media_results, results.fallback_content_results]:
            if result and result.executives_found:
                weight = source_weights.get(result.source_type, 0.5)
                total_weight += weight
                weighted_confidence += result.confidence_score * weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def _calculate_data_quality_score(self, results: Phase4BResults) -> float:
        """Calculate data quality score"""
        quality_factors = []
        
        # Website accessibility
        if results.website_health.is_accessible:
            quality_factors.append(0.3)
        
        # Multiple source verification
        sources_with_results = sum(1 for result in [
            results.companies_house_results,
            results.social_media_results,
            results.fallback_content_results
        ] if result and result.executives_found)
        
        quality_factors.append(min(sources_with_results / 3.0, 1.0) * 0.4)
        
        # Executive confidence scores
        if results.unique_executives:
            avg_confidence = sum(e.confidence_score for e in results.unique_executives) / len(results.unique_executives)
            quality_factors.append(avg_confidence * 0.3)
        
        return sum(quality_factors)
    
    def _calculate_source_diversity_score(self, results: Phase4BResults) -> float:
        """Calculate source diversity score"""
        active_sources = sum(1 for result in [
            results.companies_house_results,
            results.social_media_results,
            results.fallback_content_results
        ] if result and result.executives_found)
        
        return active_sources / 3.0
    
    def _calculate_verification_score(self, results: Phase4BResults) -> float:
        """Calculate cross-source verification score"""
        if len(results.unique_executives) <= 1:
            return 0.5  # Can't cross-verify with single result
        
        # Check for name overlaps across sources
        ch_names = set(e.name for e in results.companies_house_results.executives_found) if results.companies_house_results else set()
        sm_names = set(e.name for e in results.social_media_results.executives_found) if results.social_media_results else set()
        
        if ch_names and sm_names:
            overlap = len(ch_names.intersection(sm_names))
            total_unique = len(ch_names.union(sm_names))
            return overlap / total_unique if total_unique > 0 else 0.0
        
        return 0.3  # Default moderate verification score
    
    def _update_statistics(self, results: Phase4BResults):
        """Update processing statistics"""
        self.stats['total_processed'] += 1
        
        # Update average processing time
        total_time = self.stats['average_processing_time'] * (self.stats['total_processed'] - 1)
        total_time += results.total_processing_time
        self.stats['average_processing_time'] = total_time / self.stats['total_processed']
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if self.stats['total_processed'] == 0:
            return self.stats
        
        return {
            **self.stats,
            'companies_house_success_rate': self.stats['companies_house_successes'] / self.stats['total_processed'],
            'social_media_success_rate': self.stats['social_media_successes'] / self.stats['total_processed'],
            'fallback_success_rate': self.stats['fallback_successes'] / self.stats['total_processed']
        }

# Convenience function for testing Phase 4B
async def test_phase4b_alternative_engine(companies: List[Tuple[str, str]]) -> Dict[str, Any]:
    """Test Phase 4B Alternative Data Sources Engine"""
    engine = Phase4BAlternativeEngine()
    results = {}
    
    logger.info(f"🚀 Testing Phase 4B with {len(companies)} companies")
    
    for company_name, company_url in companies:
        logger.info(f"Testing: {company_name}")
        
        result = await engine.discover_executives_alternative_sources(company_name, company_url)
        
        results[company_name] = {
            'executives_found': result.total_executives_found,
            'best_source': result.best_source,
            'overall_confidence': result.overall_confidence,
            'data_quality_score': result.data_quality_score,
            'source_diversity_score': result.source_diversity_score,
            'verification_score': result.verification_score,
            'processing_time': result.total_processing_time,
            'website_accessible': result.website_health.is_accessible,
            'executives': [
                {
                    'name': e.name,
                    'title': e.title,
                    'confidence': e.confidence_score,
                    'discovery_method': e.discovery_method
                }
                for e in result.unique_executives
            ]
        }
    
    # Add performance stats
    results['_performance_stats'] = engine.get_performance_stats()
    
    return results 