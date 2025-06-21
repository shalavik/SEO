"""
Executive Discovery Engine

Implements the Hybrid Intelligence Strategy for executive contact discovery.
Combines LinkedIn scraping and website analysis for maximum success rate.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
from datetime import datetime

from fuzzywuzzy import fuzz

from ..models import ExecutiveContact, ExecutiveDiscoveryResult
from ..scrapers.linkedin_scraper import LinkedInScraper
from ..scrapers.website_executive_scraper import WebsiteExecutiveScraper
from ..config import get_processing_config
from ..database import get_db_session
from ..models import UKCompany, ExecutiveContactDB
from ..processors.executive_email_enricher import ExecutiveEmailEnricher

# Import new multi-source engine
try:
    from .multi_source_executive_engine import MultiSourceExecutiveEngine
    MULTI_SOURCE_AVAILABLE = True
except ImportError:
    MULTI_SOURCE_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ExecutiveDiscoveryConfig:
    """Configuration for executive discovery"""
    max_executives_per_company: int = 10
    linkedin_enabled: bool = True
    website_enabled: bool = True
    parallel_processing: bool = True
    confidence_threshold: float = 0.5  # Lowered for better discovery
    deduplication_similarity_threshold: float = 80  # More lenient
    processing_timeout: float = 45.0  # Increased timeout
    
    # Multi-source engine settings
    use_multi_source_engine: bool = True  # Enable new engine by default
    
    # LinkedIn specific
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None
    
    # Rate limiting
    delay_between_companies: float = 2.0
    delay_between_sources: float = 0.5  # Reduced delay
    
    # Enhanced discovery settings
    enable_email_enrichment: bool = True
    enable_fallback_patterns: bool = True
    website_timeout: float = 20.0  # Website specific timeout
    linkedin_timeout: float = 25.0  # LinkedIn specific timeout

class ExecutiveDiscoveryEngine:
    """Enhanced executive discovery engine with improved success rates"""
    
    def __init__(self, config: Optional[ExecutiveDiscoveryConfig] = None):
        self.config = config or ExecutiveDiscoveryConfig()
        self.processing_config = get_processing_config()
        
        # Initialize multi-source engine if available
        self.multi_source_engine = None
        if MULTI_SOURCE_AVAILABLE and self.config.use_multi_source_engine:
            try:
                self.multi_source_engine = MultiSourceExecutiveEngine()
                logger.info("✅ Multi-Source Executive Engine initialized")
            except Exception as e:
                logger.warning(f"Multi-Source Engine initialization failed: {e}")
                self.multi_source_engine = None
        
        # Initialize traditional scrapers as fallback
        self.linkedin_scraper = None
        self.website_scraper = WebsiteExecutiveScraper()
        self.email_enricher = ExecutiveEmailEnricher()
        
        # Performance tracking
        self.stats = {
            'companies_processed': 0,
            'executives_found': 0,
            'linkedin_success_rate': 0.0,
            'website_success_rate': 0.0,
            'overall_success_rate': 0.0,
            'avg_processing_time': 0.0,
            'multi_source_usage': 0,
            'fallback_usage': 0
        }
        
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the discovery engine and scrapers"""
        try:
            logger.info("Initializing executive discovery engine...")
            
            # Multi-source engine doesn't need initialization
            if self.multi_source_engine:
                logger.info("✅ Multi-Source Engine ready")
            
            # Initialize LinkedIn scraper if enabled (fallback)
            if self.config.linkedin_enabled:
                try:
                    self.linkedin_scraper = LinkedInScraper()
                    await self.linkedin_scraper.initialize()
                    logger.info("✅ LinkedIn scraper initialized (fallback)")
                except Exception as e:
                    logger.warning(f"LinkedIn scraper initialization failed: {e}")
                    self.linkedin_scraper = None
                    # Continue without LinkedIn
            
            # Website scraper is always available (no async init needed)
            logger.info("✅ Website scraper ready (fallback)")
            
            # Email enricher initialization
            logger.info("✅ Email enricher ready")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize executive discovery engine: {e}")
            return False
    
    async def discover_executives(self, company_id: str, company_name: str, 
                                website_url: str) -> ExecutiveDiscoveryResult:
        """Main executive discovery workflow with multi-source engine integration"""
        start_time = time.time()
        
        if not self.initialized:
            logger.warning("Engine not initialized, attempting initialization...")
            if not await self.initialize():
                raise RuntimeError("Failed to initialize executive discovery engine")
        
        logger.info(f"Starting executive discovery for {company_name} ({website_url})")
        
        try:
            # Try multi-source engine first
            if self.multi_source_engine:
                logger.info("🚀 Using Multi-Source Executive Discovery Engine")
                self.stats['multi_source_usage'] += 1
                
                result = await self.multi_source_engine.discover_executives(
                    company_name, website_url
                )
                
                # If multi-source engine succeeds, use its results
                if result.executives:
                    # Convert MultiSourceResult to ExecutiveDiscoveryResult
                    executives = []
                    for candidate in result.executives:
                        executive = ExecutiveContact(
                            first_name=candidate.first_name,
                            last_name=candidate.last_name,
                            title=candidate.title,
                            email=candidate.email,
                            phone=candidate.phone,
                            linkedin_url=candidate.linkedin_url,
                            company=candidate.company,
                            confidence_score=candidate.confidence,
                            source=candidate.source.value,
                            verification_status=candidate.verification_status
                        )
                        executives.append(executive)
                    
                    # Store in database
                    await self._store_executives_in_database(company_id, executives)
                    
                    # Create compatible result
                    discovery_result = ExecutiveDiscoveryResult(
                        company_id=company_id,
                        company_name=company_name,
                        company_domain=urlparse(website_url).netloc.replace('www.', ''),
                        executives_found=executives,
                        primary_decision_maker=self._identify_primary_decision_maker(executives),
                        discovery_sources=[source.value for source in result.sources_used],
                        total_processing_time=result.processing_time,
                        success_rate=result.success_rate
                    )
                    
                    # Update statistics
                    processing_time = time.time() - start_time
                    self._update_statistics(discovery_result, processing_time)
                    
                    logger.info(
                        f"✅ Multi-Source discovery complete for {company_name}: "
                        f"{len(executives)} executives found in {processing_time:.2f}s"
                    )
                    
                    return discovery_result
                else:
                    logger.warning("Multi-Source engine found no executives, falling back to traditional method")
            
            # Fallback to traditional discovery method
            logger.info("🔄 Using Traditional Executive Discovery (Fallback)")
            self.stats['fallback_usage'] += 1
            
            # Normalize URL and extract domain
            normalized_url = self._normalize_url(website_url)
            domain = urlparse(normalized_url).netloc.replace('www.', '')
            
            # Discover executives from multiple sources
            if self.config.parallel_processing:
                executives = await self._enhanced_parallel_discovery(
                    company_name, normalized_url, domain
                )
            else:
                executives = await self._enhanced_sequential_discovery(
                    company_name, normalized_url, domain
                )
            
            # Post-processing pipeline
            executives = self._merge_and_deduplicate_executives(executives)
            executives = await self._enrich_contact_details(executives)
            executives = self._filter_by_confidence(executives)
            executives = self._prioritize_executives(executives)
            
            # Limit to max executives
            if len(executives) > self.config.max_executives_per_company:
                executives = executives[:self.config.max_executives_per_company]
            
            # Identify primary decision maker
            primary_decision_maker = self._identify_primary_decision_maker(executives)
            
            # Calculate success metrics
            processing_time = time.time() - start_time
            success_rate = self._calculate_success_rate(executives)
            used_sources = self._get_used_sources(executives)
            
            # Create result
            result = ExecutiveDiscoveryResult(
                company_id=company_id,
                company_name=company_name,
                company_domain=domain,
                executives_found=executives,
                primary_decision_maker=primary_decision_maker,
                discovery_sources=used_sources,
                total_processing_time=processing_time,
                success_rate=success_rate
            )
            
            # Store in database with proper UUID handling
            await self._store_executives_in_database(company_id, executives)
            
            # Update statistics
            self._update_statistics(result, processing_time)
            
            logger.info(
                f"Traditional discovery complete for {company_name}: "
                f"{len(executives)} executives found in {processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Executive discovery failed for {company_name}: {e}")
            
            # Return empty result on failure
            return ExecutiveDiscoveryResult(
                company_id=company_id,
                company_name=company_name,
                company_domain=urlparse(website_url).netloc.replace('www.', ''),
                executives_found=[],
                primary_decision_maker=None,
                discovery_sources=[],
                total_processing_time=processing_time,
                success_rate=0.0
            )
    
    async def _enhanced_parallel_discovery(self, company_name: str, website_url: str, domain: str) -> List[ExecutiveContact]:
        """Enhanced parallel discovery with timeouts and fallbacks"""
        tasks = []
        
        # LinkedIn discovery with timeout
        if self.config.linkedin_enabled and self.linkedin_scraper:
            linkedin_task = asyncio.create_task(
                asyncio.wait_for(
                    self._safe_linkedin_discovery(company_name, domain),
                    timeout=self.config.linkedin_timeout
                )
            )
            tasks.append(linkedin_task)
        
        # Website discovery with timeout
        if self.config.website_enabled:
            website_task = asyncio.create_task(
                asyncio.wait_for(
                    self._safe_website_discovery(website_url, company_name),
                    timeout=self.config.website_timeout
                )
            )
            tasks.append(website_task)
        
        if not tasks:
            return []
        
        try:
            # Execute with global timeout
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.processing_timeout
            )
            
            # Flatten results and filter out exceptions
            executives = []
            for result in results:
                if isinstance(result, list):
                    executives.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Discovery task failed: {result}")
            
            return executives
            
        except asyncio.TimeoutError:
            logger.warning(f"Executive discovery timeout for {company_name}")
            return []
    
    async def _enhanced_sequential_discovery(self, company_name: str, website_url: str, domain: str) -> List[ExecutiveContact]:
        """Enhanced sequential discovery with better error handling"""
        executives = []
        
        # LinkedIn discovery first (higher quality data)
        if self.config.linkedin_enabled and self.linkedin_scraper:
            try:
                linkedin_executives = await asyncio.wait_for(
                    self._safe_linkedin_discovery(company_name, domain),
                    timeout=self.config.linkedin_timeout
                )
                executives.extend(linkedin_executives)
                
                if linkedin_executives:
                    logger.info(f"LinkedIn discovery found {len(linkedin_executives)} executives")
                
                await asyncio.sleep(self.config.delay_between_sources)
            except asyncio.TimeoutError:
                logger.warning(f"LinkedIn discovery timeout for {company_name}")
            except Exception as e:
                logger.warning(f"LinkedIn discovery error for {company_name}: {e}")
        
        # Website discovery
        if self.config.website_enabled:
            try:
                website_executives = await asyncio.wait_for(
                    self._safe_website_discovery(website_url, company_name),
                    timeout=self.config.website_timeout
                )
                executives.extend(website_executives)
                
                if website_executives:
                    logger.info(f"Website discovery found {len(website_executives)} executives")
                    
            except asyncio.TimeoutError:
                logger.warning(f"Website discovery timeout for {company_name}")
            except Exception as e:
                logger.warning(f"Website discovery error for {company_name}: {e}")
        
        return executives
    
    async def _safe_linkedin_discovery(self, company_name: str, domain: str) -> List[ExecutiveContact]:
        """Safely execute LinkedIn discovery with error handling"""
        try:
            if self.linkedin_scraper:
                return await self.linkedin_scraper.discover_company_executives(company_name, domain)
        except Exception as e:
            logger.warning(f"LinkedIn discovery failed for {company_name}: {e}")
        
        return []
    
    async def _safe_website_discovery(self, website_url: str, company_name: str) -> List[ExecutiveContact]:
        """Safely execute website discovery with error handling"""
        try:
            return await self.website_scraper.discover_website_executives(website_url, company_name)
        except Exception as e:
            logger.warning(f"Website discovery failed for {company_name}: {e}")
        
        return []
    
    async def _enrich_contact_details(self, executives: List[ExecutiveContact]) -> List[ExecutiveContact]:
        """Enrich executive contact details with email patterns and verification"""
        if not self.config.enable_email_enrichment or not executives:
            return executives
        
        try:
            enriched_executives = []
            
            for executive in executives:
                # Enrich emails if not present
                if not executive.email:
                    email_candidates = await self.email_enricher.generate_executive_emails(
                        executive.first_name,
                        executive.last_name,
                        executive.company_domain,
                        executive.title
                    )
                    
                    if email_candidates:
                        # Use the highest confidence email
                        best_email = email_candidates[0]
                        executive.email = best_email['email']
                        executive.email_confidence = best_email['confidence']
                
                # Update data completeness score
                executive.data_completeness_score = self._calculate_completeness_score(executive)
                
                enriched_executives.append(executive)
            
            return enriched_executives
            
        except Exception as e:
            logger.warning(f"Email enrichment failed: {e}")
            return executives
    
    def _calculate_completeness_score(self, executive: ExecutiveContact) -> float:
        """Calculate data completeness score for an executive"""
        score = 0.0
        
        # Required fields (always present)
        score += 0.4  # Name and title
        
        # Optional contact fields
        if executive.email:
            score += 0.3
        if executive.phone:
            score += 0.2
        if executive.linkedin_url:
            score += 0.1
        
        return min(score, 1.0)
    
    def _filter_by_confidence(self, executives: List[ExecutiveContact]) -> List[ExecutiveContact]:
        """Filter executives by confidence threshold"""
        return [
            exec for exec in executives 
            if exec.overall_confidence >= self.config.confidence_threshold
        ]
    
    def _calculate_success_rate(self, executives: List[ExecutiveContact]) -> float:
        """Calculate overall success rate based on executives found and quality"""
        if not executives:
            return 0.0
        
        # Base success for finding any executives
        base_success = 0.25
        
        # Bonus for primary decision maker
        has_tier_1 = any(exec.seniority_tier == 'tier_1' for exec in executives)
        tier_1_bonus = 0.25 if has_tier_1 else 0.0
        
        # Bonus for contact details
        emails_found = sum(1 for exec in executives if exec.email)
        email_bonus = min(emails_found * 0.15, 0.30)
        
        # Bonus for LinkedIn profiles
        linkedin_found = sum(1 for exec in executives if exec.linkedin_url)
        linkedin_bonus = min(linkedin_found * 0.10, 0.20)
        
        total_success = base_success + tier_1_bonus + email_bonus + linkedin_bonus
        return min(total_success, 1.0)
    
    def _merge_and_deduplicate_executives(self, executives: List[ExecutiveContact]) -> List[ExecutiveContact]:
        """Intelligent merging and deduplication of executives from multiple sources"""
        if not executives:
            return []
        
        merged_executives = []
        
        for executive in executives:
            # Check for duplicates
            duplicate_index = self._find_duplicate_executive(executive, merged_executives)
            
            if duplicate_index is not None:
                # Merge with existing executive
                existing = merged_executives[duplicate_index]
                merged = self._merge_executive_data(existing, executive)
                merged_executives[duplicate_index] = merged
            else:
                # Add as new executive
                merged_executives.append(executive)
        
        logger.info(f"Merged {len(executives)} executives into {len(merged_executives)} unique executives")
        return merged_executives
    
    def _find_duplicate_executive(self, executive: ExecutiveContact, 
                                existing_executives: List[ExecutiveContact]) -> Optional[int]:
        """Find duplicate executive in existing list"""
        for i, existing in enumerate(existing_executives):
            # Check name similarity
            name_similarity = fuzz.ratio(
                executive.full_name.lower(), 
                existing.full_name.lower()
            )
            
            if name_similarity >= self.config.deduplication_similarity_threshold:
                return i
            
            # Also check first/last name combinations
            if (executive.first_name.lower() == existing.first_name.lower() and 
                executive.last_name.lower() == existing.last_name.lower()):
                return i
        
        return None
    
    def _merge_executive_data(self, existing: ExecutiveContact, new: ExecutiveContact) -> ExecutiveContact:
        """Merge data from two executive contacts, preferring higher quality data"""
        merged = ExecutiveContact(
            first_name=existing.first_name,
            last_name=existing.last_name,
            full_name=existing.full_name,
            title=self._choose_better_title(existing.title, new.title),
            seniority_tier=self._choose_better_seniority(existing.seniority_tier, new.seniority_tier),
            company_name=existing.company_name,
            company_domain=existing.company_domain
        )
        
        # Merge contact details (prefer higher confidence)
        if new.email and (not existing.email or new.email_confidence > existing.email_confidence):
            merged.email = new.email
            merged.email_confidence = new.email_confidence
        else:
            merged.email = existing.email
            merged.email_confidence = existing.email_confidence
        
        if new.phone and (not existing.phone or new.phone_confidence > existing.phone_confidence):
            merged.phone = new.phone
            merged.phone_confidence = new.phone_confidence
        else:
            merged.phone = existing.phone
            merged.phone_confidence = existing.phone_confidence
        
        # LinkedIn URL (prefer verified)
        if new.linkedin_url and (not existing.linkedin_url or new.linkedin_verified):
            merged.linkedin_url = new.linkedin_url
            merged.linkedin_verified = new.linkedin_verified
        else:
            merged.linkedin_url = existing.linkedin_url
            merged.linkedin_verified = existing.linkedin_verified
        
        # Merge discovery metadata
        merged.discovery_sources = list(set(existing.discovery_sources + new.discovery_sources))
        merged.discovery_method = f"{existing.discovery_method}+{new.discovery_method}"
        merged.data_completeness_score = max(existing.data_completeness_score, new.data_completeness_score)
        merged.overall_confidence = max(existing.overall_confidence, new.overall_confidence)
        merged.processing_time_ms = max(existing.processing_time_ms, new.processing_time_ms)
        
        return merged
    
    def _choose_better_title(self, title1: str, title2: str) -> str:
        """Choose the better title based on completeness and clarity"""
        if not title1:
            return title2
        if not title2:
            return title1
        
        # Prefer longer, more descriptive titles
        if len(title2) > len(title1) * 1.2:
            return title2
        
        return title1
    
    def _choose_better_seniority(self, tier1: str, tier2: str) -> str:
        """Choose the higher seniority tier"""
        tier_priority = {'tier_1': 1, 'tier_2': 2, 'tier_3': 3}
        
        priority1 = tier_priority.get(tier1, 4)
        priority2 = tier_priority.get(tier2, 4)
        
        return tier1 if priority1 <= priority2 else tier2
    
    def _prioritize_executives(self, executives: List[ExecutiveContact]) -> List[ExecutiveContact]:
        """Prioritize executives by seniority and data completeness"""
        if not executives:
            return []
        
        # Calculate priority score for each executive
        for executive in executives:
            priority_score = self._calculate_priority_score(executive)
            executive.priority_score = priority_score
        
        # Sort by priority score (higher is better)
        prioritized = sorted(executives, key=lambda x: getattr(x, 'priority_score', 0), reverse=True)
        
        return prioritized
    
    def _calculate_priority_score(self, executive: ExecutiveContact) -> float:
        """Calculate priority score based on seniority and data completeness"""
        score = 0.0
        
        # Seniority weight (60% of total score)
        seniority_weights = {'tier_1': 0.6, 'tier_2': 0.4, 'tier_3': 0.2}
        score += seniority_weights.get(executive.seniority_tier, 0.1)
        
        # Data completeness weight (40% of total score)
        completeness_score = 0.0
        
        if executive.email:
            completeness_score += 0.15
        if executive.phone:
            completeness_score += 0.10
        if executive.linkedin_url:
            completeness_score += 0.10
        if executive.linkedin_verified:
            completeness_score += 0.05
        
        score += completeness_score
        
        # Confidence bonus
        score += executive.overall_confidence * 0.1
        
        return score
    
    def _identify_primary_decision_maker(self, executives: List[ExecutiveContact]) -> Optional[ExecutiveContact]:
        """Identify the primary decision maker (highest ranking executive)"""
        if not executives:
            return None
        
        # Find highest tier executive
        tier_1_executives = [e for e in executives if e.seniority_tier == 'tier_1']
        if tier_1_executives:
            return tier_1_executives[0]  # Already sorted by priority
        
        tier_2_executives = [e for e in executives if e.seniority_tier == 'tier_2']
        if tier_2_executives:
            return tier_2_executives[0]
        
        # Fallback to highest priority executive
        return executives[0] if executives else None
    
    def _get_used_sources(self, executives: List[ExecutiveContact]) -> List[str]:
        """Get list of sources used in discovery"""
        sources = set()
        for executive in executives:
            sources.update(executive.discovery_sources)
        return list(sources)
    
    async def _store_executives_in_database(self, company_id: str, executives: List[ExecutiveContact]):
        """Store discovered executives in database with proper UUID handling"""
        try:
            with get_db_session() as session:
                # Convert company_id to UUID if it's a string
                if isinstance(company_id, str):
                    try:
                        company_uuid = uuid.UUID(company_id)
                    except ValueError:
                        # If company_id is not a valid UUID, generate one or use the string as-is
                        logger.warning(f"Invalid UUID format for company_id: {company_id}, generating new UUID")
                        company_uuid = uuid.uuid4()
                else:
                    company_uuid = company_id
                
                # Remove existing executives for this company
                session.query(ExecutiveContactDB).filter(
                    ExecutiveContactDB.company_id == company_uuid
                ).delete()
                
                # Add new executives
                for executive in executives:
                    db_executive = ExecutiveContactDB(
                        company_id=company_uuid,
                        first_name=executive.first_name,
                        last_name=executive.last_name,
                        full_name=executive.full_name,
                        title=executive.title,
                        seniority_tier=executive.seniority_tier,
                        email=executive.email,
                        email_confidence=executive.email_confidence,
                        phone=executive.phone,
                        phone_confidence=executive.phone_confidence,
                        linkedin_url=executive.linkedin_url,
                        linkedin_verified=executive.linkedin_verified,
                        discovery_sources=executive.discovery_sources,
                        discovery_method=executive.discovery_method,
                        data_completeness_score=executive.data_completeness_score,
                        overall_confidence=executive.overall_confidence,
                        processing_time_ms=executive.processing_time_ms
                    )
                    session.add(db_executive)
                
                session.commit()
                logger.info(f"Stored {len(executives)} executives in database for company {company_id}")
                
        except Exception as e:
            logger.error(f"Error storing executives in database: {e}")
            # Don't fail the entire discovery process for database errors
            pass
    
    def _update_statistics(self, result: ExecutiveDiscoveryResult, processing_time: float):
        """Update performance statistics"""
        self.stats['companies_processed'] += 1
        self.stats['executives_found'] += len(result.executives_found)
        
        # Update success rates
        linkedin_found = any('linkedin' in exec.discovery_sources for exec in result.executives_found)
        website_found = any('website' in exec.discovery_sources for exec in result.executives_found)
        
        # Simple running average for success rates
        companies = self.stats['companies_processed']
        self.stats['linkedin_success_rate'] = (
            (self.stats['linkedin_success_rate'] * (companies - 1) + (1 if linkedin_found else 0)) / companies
        )
        self.stats['website_success_rate'] = (
            (self.stats['website_success_rate'] * (companies - 1) + (1 if website_found else 0)) / companies
        )
        self.stats['overall_success_rate'] = (
            (self.stats['overall_success_rate'] * (companies - 1) + result.success_rate) / companies
        )
        self.stats['avg_processing_time'] = (
            (self.stats['avg_processing_time'] * (companies - 1) + processing_time) / companies
        )
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL to ensure proper format"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url.rstrip('/')
    
    def get_statistics(self) -> Dict:
        """Get current performance statistics"""
        return self.stats.copy()
    
    async def close(self):
        """Close all scrapers and cleanup resources"""
        if self.linkedin_scraper:
            await self.linkedin_scraper.close()
        
        logger.info("Executive discovery engine closed")

# Convenience functions for integration
async def discover_company_executives(company_id: str, company_name: str, 
                                    website_url: str, 
                                    config: Optional[ExecutiveDiscoveryConfig] = None) -> ExecutiveDiscoveryResult:
    """Convenience function to discover executives for a single company"""
    engine = ExecutiveDiscoveryEngine(config)
    
    try:
        await engine.initialize()
        result = await engine.discover_executives(company_id, company_name, website_url)
        return result
    finally:
        await engine.close()

async def batch_discover_executives(companies: List[Tuple[str, str, str]], 
                                  config: Optional[ExecutiveDiscoveryConfig] = None) -> List[ExecutiveDiscoveryResult]:
    """Batch discover executives for multiple companies"""
    engine = ExecutiveDiscoveryEngine(config)
    results = []
    
    try:
        await engine.initialize()
        
        for company_id, company_name, website_url in companies:
            try:
                result = await engine.discover_executives(company_id, company_name, website_url)
                results.append(result)
                
                # Add delay between companies
                if config and config.delay_between_companies > 0:
                    await asyncio.sleep(config.delay_between_companies)
                    
            except Exception as e:
                logger.error(f"Failed to process company {company_name}: {e}")
                continue
        
        return results
        
    finally:
        await engine.close() 