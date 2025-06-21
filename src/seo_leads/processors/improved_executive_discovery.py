"""
Improved Executive Discovery Engine

Enhanced version with better pattern recognition for small businesses:
- Advanced name extraction from business names
- Multiple website content analysis strategies  
- Improved Google search with anti-detection
- Enhanced confidence scoring
"""

import asyncio
import logging
import re
import time
from typing import List, Optional, Dict, Set
from dataclasses import dataclass
from urllib.parse import urlparse

from ..models import ExecutiveContact
from ..enrichers.companies_house_enricher import CompaniesHouseEnricher
from ..enrichers.google_search_enricher import GoogleSearchEnricher
from ..scrapers.website_executive_scraper import WebsiteExecutiveScraper
from .enhanced_executive_discovery import EnhancedDiscoveryConfig, ExecutiveDiscoveryResult

logger = logging.getLogger(__name__)

@dataclass
class ImprovedDiscoveryConfig(EnhancedDiscoveryConfig):
    """Enhanced configuration with improved detection settings"""
    
    # Enhanced pattern recognition
    enable_business_name_analysis: bool = True
    enable_advanced_website_patterns: bool = True
    enable_context_analysis: bool = True
    
    # Small business specific settings
    personified_business_detection: bool = True
    single_person_business_boost: float = 0.3  # Confidence boost for likely single-person businesses
    
    # Enhanced confidence thresholds
    min_confidence_tier_1: float = 0.6  # High confidence executives
    min_confidence_tier_2: float = 0.4  # Medium confidence executives
    min_confidence_tier_3: float = 0.2  # Low confidence but still valuable
    
    # Processing optimizations
    max_website_content_analysis: int = 3000  # Max characters to analyze
    enable_meta_description_analysis: bool = True
    enable_page_title_analysis: bool = True

class ImprovedExecutiveDiscoveryEngine:
    """Improved executive discovery with enhanced small business detection"""
    
    def __init__(self, config: ImprovedDiscoveryConfig = None):
        self.config = config or ImprovedDiscoveryConfig()
        
        # Initialize enrichers
        self.companies_house_enricher = CompaniesHouseEnricher()
        self.google_search_enricher = GoogleSearchEnricher()
        self.website_scraper = WebsiteExecutiveScraper()
        
        # Statistics tracking
        self.stats = {
            'total_companies_processed': 0,
            'executives_found': 0,
            'business_name_detections': 0,
            'website_detections': 0,
            'google_detections': 0,
            'companies_house_detections': 0,
        }
        
        # Pattern cache for performance
        self._pattern_cache = {}
    
    async def discover_executives(self, company_name: str, website_url: str, company_id: str = None) -> ExecutiveDiscoveryResult:
        """Improved executive discovery with enhanced pattern recognition"""
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Starting improved executive discovery for: {company_name}")
            
            all_executives = []
            source_results = {}
            
            # Phase 1: Business name analysis (NEW)
            if self.config.enable_business_name_analysis:
                name_executives = await self._analyze_business_name(company_name, website_url)
                source_results['business_name'] = name_executives
                all_executives.extend(name_executives)
                logger.info(f"Business Name Analysis: {len(name_executives)} executives found")
                self.stats['business_name_detections'] += len(name_executives)
            
            # Phase 2: Enhanced website analysis
            if self.config.website_enabled:
                website_executives = await self._enhanced_website_discovery(company_name, website_url)
                source_results['website'] = website_executives
                all_executives.extend(website_executives)
                logger.info(f"Enhanced Website: {len(website_executives)} executives found")
                self.stats['website_detections'] += len(website_executives)
            
            # Phase 3: Google search (existing with improvements)
            if self.config.google_search_enabled:
                google_executives = await self._discover_from_google_search(company_name, self._extract_domain(website_url))
                source_results['google_search'] = google_executives
                all_executives.extend(google_executives)
                logger.info(f"Google Search: {len(google_executives)} executives found")
                self.stats['google_detections'] += len(google_executives)
            
            # Phase 4: Companies House (existing)
            if self.config.companies_house_enabled:
                ch_executives = await self._discover_from_companies_house(company_name, self._extract_domain(website_url))
                source_results['companies_house'] = ch_executives
                all_executives.extend(ch_executives)
                logger.info(f"Companies House: {len(ch_executives)} executives found")
                self.stats['companies_house_detections'] += len(ch_executives)
            
            logger.info(f"Raw discovery results: {len(all_executives)} executives from all sources")
            
            # Enhanced post-processing
            executives = self._merge_and_deduplicate_executives(all_executives)
            executives = await self._enhance_with_context_analysis(executives, company_name, website_url)
            executives = self._apply_confidence_boosting(executives, company_name)
            executives = self._filter_by_enhanced_confidence(executives)
            executives = self._prioritize_executives(executives)
            
            # Limit results
            executives = executives[:self.config.max_executives_per_company]
            
            # Update statistics
            self.stats['total_companies_processed'] += 1
            self.stats['executives_found'] += len(executives)
            
            processing_time = time.time() - start_time
            
            result = ExecutiveDiscoveryResult(
                company_id=company_id or company_name,
                company_name=company_name,
                company_domain=self._extract_domain(website_url),
                executives_found=executives,
                primary_decision_maker=self._identify_primary_decision_maker(executives),
                discovery_sources=list(source_results.keys()),
                total_processing_time=processing_time,
                success_rate=len(executives) / max(1, self.config.max_executives_per_company)
            )
            
            logger.info(f"✅ Improved discovery complete: {len(executives)} executives found in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in improved executive discovery: {e}")
            processing_time = time.time() - start_time
            
            return ExecutiveDiscoveryResult(
                company_id=company_id or company_name,
                company_name=company_name,
                company_domain=self._extract_domain(website_url),
                executives_found=[],
                primary_decision_maker=None,
                discovery_sources=[],
                total_processing_time=processing_time,
                success_rate=0.0
            )
    
    async def _analyze_business_name(self, company_name: str, website_url: str) -> List[ExecutiveContact]:
        """Analyze business name to extract likely owner information"""
        executives = []
        
        try:
            # Pattern 1: First name in business name
            name_patterns = [
                r'^([A-Z][a-z]{2,})\s+(?:The\s+)?(?:Plumber|Electrician|Builder|Contractor|Roofer|Carpenter)',
                r'^([A-Z][a-z]{2,})\s*\'s\s+(?:Plumbing|Electrical|Building|Construction|Heating|Gas)',
                r'^([A-Z][a-z]{2,})\s+(?:Plumbing|Electrical|Heating|Gas|Building|Construction)',
                r'^([A-Z][a-z]{2,})\s+&\s+(?:Sons?|Daughters?|Co|Company)',
                r'^([A-Z][a-z]{2,})\s+(?:and|&)\s+(?:Heating|Plumbing|Gas|Electrical)',
                r'([A-Z][a-z]{2,})\s+(?:Plumbing|Heating)\s+(?:and|&)\s+(?:Heating|Gas)',
            ]
            
            for pattern in name_patterns:
                matches = re.findall(pattern, company_name, re.IGNORECASE)
                for match in matches:
                    if self._is_valid_first_name(match):
                        # Determine title based on business type
                        title = self._extract_title_from_business_name(company_name)
                        if not title:
                            title = "Business Owner"
                        
                        # Create executive with higher confidence for name-based businesses
                        executive = self._create_executive_from_business_name(
                            match, title, company_name, website_url, confidence_boost=0.4
                        )
                        executives.append(executive)
            
            # Pattern 2: Family business indicators
            family_patterns = [
                r'([A-Z][a-z]+)\s+(?:&\s+)?(?:Sons?|Daughters?|Family|Brothers?)',
                r'([A-Z][a-z]+)\s+(?:Family\s+)?(?:Business|Enterprise|Services)',
            ]
            
            for pattern in family_patterns:
                matches = re.findall(pattern, company_name, re.IGNORECASE)
                for match in matches:
                    if self._is_valid_first_name(match):
                        executive = self._create_executive_from_business_name(
                            match, "Family Business Owner", company_name, website_url, confidence_boost=0.3
                        )
                        executives.append(executive)
            
            # Pattern 3: Professional service patterns
            professional_patterns = [
                r'([A-Z][a-z]+)\s+(?:Associates|Consulting|Services|Solutions)',
                r'([A-Z][a-z]+)\s+(?:Legal|Medical|Dental|Accounting)',
                r'Dr\.?\s+([A-Z][a-z]+)',
                r'Mr\.?\s+([A-Z][a-z]+)',
            ]
            
            for pattern in professional_patterns:
                matches = re.findall(pattern, company_name, re.IGNORECASE)
                for match in matches:
                    if self._is_valid_first_name(match):
                        title = "Professional Services Owner"
                        if "Dr." in company_name:
                            title = "Doctor/Owner"
                        elif "Legal" in company_name:
                            title = "Lawyer/Owner"
                        
                        executive = self._create_executive_from_business_name(
                            match, title, company_name, website_url, confidence_boost=0.5
                        )
                        executives.append(executive)
            
        except Exception as e:
            logger.debug(f"Error in business name analysis: {e}")
        
        return executives
    
    async def _enhanced_website_discovery(self, company_name: str, website_url: str) -> List[ExecutiveContact]:
        """Enhanced website discovery with additional patterns"""
        try:
            # Use existing website scraper but with enhanced post-processing
            base_executives = await self.website_scraper.discover_website_executives(website_url, company_name)
            
            # Additional website analysis
            enhanced_executives = await self._additional_website_analysis(website_url, company_name)
            
            # Combine and enhance
            all_executives = base_executives + enhanced_executives
            return self._enhance_website_executives(all_executives, company_name)
            
        except Exception as e:
            logger.debug(f"Error in enhanced website discovery: {e}")
            return []
    
    async def _additional_website_analysis(self, website_url: str, company_name: str) -> List[ExecutiveContact]:
        """Additional website content analysis patterns"""
        executives = []
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(website_url, timeout=15) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Analyze meta description
                        if self.config.enable_meta_description_analysis:
                            meta_executives = self._analyze_meta_description(content, company_name, website_url)
                            executives.extend(meta_executives)
                        
                        # Analyze page title
                        if self.config.enable_page_title_analysis:
                            title_executives = self._analyze_page_title(content, company_name, website_url)
                            executives.extend(title_executives)
                        
                        # Advanced content patterns
                        if self.config.enable_context_analysis:
                            context_executives = self._analyze_content_context(content, company_name, website_url)
                            executives.extend(context_executives)
                            
        except Exception as e:
            logger.debug(f"Error in additional website analysis: {e}")
        
        return executives
    
    def _analyze_meta_description(self, html_content: str, company_name: str, website_url: str) -> List[ExecutiveContact]:
        """Analyze meta description for executive information"""
        executives = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                content = meta_desc.get('content')
                
                # Patterns specific to meta descriptions
                patterns = [
                    r'([A-Z][a-z]+ [A-Z][a-z]+)\s+(?:provides|offers|specializes)',
                    r'(?:by|from)\s+([A-Z][a-z]+ [A-Z][a-z]+)',
                    r'([A-Z][a-z]+ [A-Z][a-z]+)\s*[-–—]\s*(?:Expert|Professional|Specialist)',
                    r'(?:Call|Contact)\s+([A-Z][a-z]+ [A-Z][a-z]+)',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if self._is_valid_name(match):
                            executive = self._create_enhanced_executive(
                                match, "Service Provider", company_name, website_url, 
                                source="meta_description", confidence=0.5
                            )
                            executives.append(executive)
                            
        except Exception as e:
            logger.debug(f"Error analyzing meta description: {e}")
        
        return executives
    
    def _analyze_page_title(self, html_content: str, company_name: str, website_url: str) -> List[ExecutiveContact]:
        """Analyze page title for executive information"""
        executives = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            title_tag = soup.find('title')
            if title_tag:
                title_content = title_tag.get_text()
                
                # Title patterns
                patterns = [
                    r'([A-Z][a-z]+ [A-Z][a-z]+)\s*[-–—|]',
                    r'^([A-Z][a-z]+)\s+(?:The\s+)?(?:Plumber|Electrician)',
                    r'([A-Z][a-z]+)\s*\'s\s+(?:Plumbing|Electrical)',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, title_content, re.IGNORECASE)
                    for match in matches:
                        name = match if isinstance(match, str) else match[0]
                        if self._is_valid_first_name(name) or self._is_valid_name(name):
                            title = self._extract_title_from_business_name(company_name) or "Business Owner"
                            executive = self._create_enhanced_executive(
                                name, title, company_name, website_url,
                                source="page_title", confidence=0.6
                            )
                            executives.append(executive)
                            
        except Exception as e:
            logger.debug(f"Error analyzing page title: {e}")
        
        return executives
    
    def _analyze_content_context(self, html_content: str, company_name: str, website_url: str) -> List[ExecutiveContact]:
        """Analyze content context for implicit executive information"""
        executives = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Get clean text content (first 3000 chars for performance)
            text_content = soup.get_text()[:self.config.max_website_content_analysis]
            
            # Context patterns
            context_patterns = [
                r'(?:I|We)\s+(?:am|are)\s+([A-Z][a-z]+ [A-Z][a-z]+)',
                r'(?:My|Our)\s+name\s+is\s+([A-Z][a-z]+ [A-Z][a-z]+)',
                r'([A-Z][a-z]+ [A-Z][a-z]+)\s+(?:has|have)\s+(?:been|worked)',
                r'(?:with|by)\s+([A-Z][a-z]+ [A-Z][a-z]+)\s+(?:who|providing)',
                r'([A-Z][a-z]+ [A-Z][a-z]+)\s+(?:founded|established|started)',
                r'(?:qualified|certified|experienced)\s+([A-Z][a-z]+ [A-Z][a-z]+)',
            ]
            
            for pattern in context_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    if self._is_valid_name(match):
                        # Determine confidence based on context
                        confidence = 0.4
                        if 'founded' in pattern or 'established' in pattern:
                            confidence = 0.6
                        elif 'qualified' in pattern or 'certified' in pattern:
                            confidence = 0.5
                        
                        executive = self._create_enhanced_executive(
                            match, "Owner/Operator", company_name, website_url,
                            source="content_context", confidence=confidence
                        )
                        executives.append(executive)
                        
        except Exception as e:
            logger.debug(f"Error analyzing content context: {e}")
        
        return executives
    
    async def _enhance_with_context_analysis(self, executives: List[ExecutiveContact], company_name: str, website_url: str) -> List[ExecutiveContact]:
        """Enhance executives with additional context analysis"""
        if not executives:
            return executives
        
        # Add context-based confidence boosting
        for executive in executives:
            # Boost confidence if name matches business name
            if self._name_matches_business_pattern(executive, company_name):
                executive.overall_confidence = min(0.95, executive.overall_confidence + 0.2)
                executive.discovery_sources.append("business_name_match")
            
            # Boost confidence for single-person business indicators
            if self._is_likely_single_person_business(company_name):
                executive.overall_confidence = min(0.90, executive.overall_confidence + self.config.single_person_business_boost)
                executive.discovery_sources.append("single_person_business")
        
        return executives
    
    def _apply_confidence_boosting(self, executives: List[ExecutiveContact], company_name: str) -> List[ExecutiveContact]:
        """Apply confidence boosting based on business analysis"""
        for executive in executives:
            original_confidence = executive.overall_confidence
            
            # Business name matching boost
            if self._name_appears_in_business_name(executive, company_name):
                executive.overall_confidence += 0.3
            
            # Single person business boost
            if self._is_likely_single_person_business(company_name):
                executive.overall_confidence += 0.2
            
            # Multiple source boost
            if len(executive.discovery_sources) > 1:
                executive.overall_confidence += 0.1
            
            # Cap at 0.95
            executive.overall_confidence = min(0.95, executive.overall_confidence)
            
            if executive.overall_confidence > original_confidence:
                logger.debug(f"Boosted confidence for {executive.first_name} {executive.last_name}: {original_confidence:.2f} → {executive.overall_confidence:.2f}")
        
        return executives
    
    def _filter_by_enhanced_confidence(self, executives: List[ExecutiveContact]) -> List[ExecutiveContact]:
        """Filter executives using tiered confidence thresholds"""
        filtered = []
        
        for executive in executives:
            tier = executive.seniority_tier
            confidence = executive.overall_confidence
            
            if tier == "tier_1" and confidence >= self.config.min_confidence_tier_1:
                filtered.append(executive)
            elif tier == "tier_2" and confidence >= self.config.min_confidence_tier_2:
                filtered.append(executive)
            elif tier == "tier_3" and confidence >= self.config.min_confidence_tier_3:
                filtered.append(executive)
        
        logger.info(f"Confidence filtering: {len(executives)} → {len(filtered)} executives")
        return filtered
    
    # Helper methods
    def _create_executive_from_business_name(self, name: str, title: str, company_name: str, website_url: str, confidence_boost: float = 0.0) -> ExecutiveContact:
        """Create executive contact from business name analysis"""
        return ExecutiveContact(
            first_name=name,
            last_name="[Business Owner]",
            title=title,
            company_name=company_name,
            discovery_source="business_name_analysis",
            discovery_sources=["business_name_analysis"],
            overall_confidence=0.5 + confidence_boost,
            data_completeness_score=0.4,
            seniority_tier="tier_1"  # Business owners are tier 1
        )
    
    def _create_enhanced_executive(self, name: str, title: str, company_name: str, website_url: str, source: str, confidence: float) -> ExecutiveContact:
        """Create enhanced executive contact with specified confidence"""
        name_parts = name.split() if isinstance(name, str) else [name, ""]
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        return ExecutiveContact(
            first_name=first_name,
            last_name=last_name,
            title=title,
            company_name=company_name,
            discovery_source=source,
            discovery_sources=[source],
            overall_confidence=confidence,
            data_completeness_score=confidence * 0.8,
            seniority_tier=self._classify_executive_tier(title)
        )
    
    def _is_valid_first_name(self, name: str) -> bool:
        """Check if text is a valid first name"""
        if not name or len(name) < 3:
            return False
        
        # Check if it's a real name (not a business term)
        business_terms = {
            'plumbing', 'heating', 'gas', 'electrical', 'building', 'construction',
            'services', 'ltd', 'limited', 'company', 'co', 'the', 'and', 'sons',
            'daughters', 'family', 'professional', 'expert', 'specialist'
        }
        
        return (name.isalpha() and 
                name[0].isupper() and 
                name.lower() not in business_terms)
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if text is a valid full name"""
        if not name:
            return False
        
        parts = name.split()
        return (len(parts) >= 2 and 
                all(self._is_valid_first_name(part) for part in parts))
    
    def _extract_title_from_business_name(self, business_name: str) -> str:
        """Extract likely job title from business name"""
        title_mappings = {
            'plumbing': 'Master Plumber',
            'heating': 'Heating Engineer',
            'gas': 'Gas Engineer',
            'electrical': 'Electrician',
            'building': 'Builder',
            'construction': 'Construction Manager',
            'roofing': 'Roofer',
            'carpentry': 'Carpenter',
        }
        
        business_lower = business_name.lower()
        for keyword, title in title_mappings.items():
            if keyword in business_lower:
                return title
        
        return "Business Owner"
    
    def _name_matches_business_pattern(self, executive: ExecutiveContact, business_name: str) -> bool:
        """Check if executive name matches business name pattern"""
        first_name = executive.first_name.lower()
        business_lower = business_name.lower()
        
        # Direct name match
        if first_name in business_lower:
            return True
        
        # Possessive form match (Jack's Plumbing)
        if f"{first_name}'s" in business_lower:
            return True
        
        return False
    
    def _name_appears_in_business_name(self, executive: ExecutiveContact, business_name: str) -> bool:
        """Check if any part of the name appears in business name"""
        first_name = executive.first_name.lower()
        last_name = executive.last_name.lower().replace('[business owner]', '')
        business_lower = business_name.lower()
        
        return first_name in business_lower or (last_name and last_name in business_lower)
    
    def _is_likely_single_person_business(self, business_name: str) -> bool:
        """Determine if this is likely a single-person business"""
        single_person_indicators = [
            r'^[A-Z][a-z]+\s+(?:The\s+)?(?:Plumber|Electrician|Builder)',
            r'^[A-Z][a-z]+\s*\'s\s+',
            r'^[A-Z][a-z]+\s+(?:Plumbing|Electrical|Heating)',
            r'(?:Mr\.?|Mrs\.?)\s+[A-Z][a-z]+',
        ]
        
        return any(re.search(pattern, business_name, re.IGNORECASE) for pattern in single_person_indicators)
    
    def _classify_executive_tier(self, title: str) -> str:
        """Classify executive tier based on title"""
        title_lower = title.lower()
        
        tier_1_titles = ['owner', 'founder', 'ceo', 'president', 'managing director', 'business owner', 'master']
        tier_2_titles = ['manager', 'director', 'engineer', 'specialist']
        
        if any(t1 in title_lower for t1 in tier_1_titles):
            return "tier_1"
        elif any(t2 in title_lower for t2 in tier_2_titles):
            return "tier_2"
        else:
            return "tier_3"
    
    # Additional methods from base class
    async def _discover_from_companies_house(self, company_name: str, website_domain: str) -> List[ExecutiveContact]:
        """Discover executives from Companies House"""
        try:
            return await self.companies_house_enricher.discover_executives(company_name, website_domain)
        except Exception as e:
            logger.debug(f"Companies House discovery failed: {e}")
            return []
    
    async def _discover_from_google_search(self, company_name: str, website_domain: str) -> List[ExecutiveContact]:
        """Discover executives from Google Search"""
        try:
            return await self.google_search_enricher.discover_executives(company_name, website_domain)
        except Exception as e:
            logger.debug(f"Google Search discovery failed: {e}")
            return []
    
    def _merge_and_deduplicate_executives(self, executives: List[ExecutiveContact]) -> List[ExecutiveContact]:
        """Merge and deduplicate executives from multiple sources"""
        if not executives:
            return []
        
        # Simple deduplication based on name similarity
        unique_executives = []
        seen_names = set()
        
        for executive in executives:
            name_key = f"{executive.first_name.lower()} {executive.last_name.lower()}"
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_executives.append(executive)
            else:
                # Merge with existing executive if confidence is higher
                for existing in unique_executives:
                    existing_key = f"{existing.first_name.lower()} {existing.last_name.lower()}"
                    if existing_key == name_key and executive.overall_confidence > existing.overall_confidence:
                        # Replace with higher confidence version
                        unique_executives.remove(existing)
                        unique_executives.append(executive)
                        break
        
        logger.info(f"Deduplication: {len(executives)} → {len(unique_executives)} executives")
        return unique_executives
    
    def _enhance_website_executives(self, executives: List[ExecutiveContact], company_name: str) -> List[ExecutiveContact]:
        """Enhance website-discovered executives with additional context"""
        for executive in executives:
            # Boost confidence if executive name matches business pattern
            if self._name_matches_business_pattern(executive, company_name):
                executive.overall_confidence = min(0.9, executive.overall_confidence + 0.2)
                if "business_name_match" not in executive.discovery_sources:
                    executive.discovery_sources.append("business_name_match")
        
        return executives
    
    def _prioritize_executives(self, executives: List[ExecutiveContact]) -> List[ExecutiveContact]:
        """Prioritize executives based on confidence and tier"""
        return sorted(executives, key=lambda e: (
            e.seniority_tier == "tier_1",  # Tier 1 first
            e.overall_confidence,          # Then by confidence
            e.data_completeness_score      # Then by data completeness
        ), reverse=True)
    
    def _identify_primary_decision_maker(self, executives: List[ExecutiveContact]) -> Optional[ExecutiveContact]:
        """Identify the primary decision maker"""
        if not executives:
            return None
        
        # Prioritize tier 1 executives with high confidence
        tier_1_executives = [e for e in executives if e.seniority_tier == "tier_1" and e.overall_confidence >= 0.6]
        if tier_1_executives:
            return tier_1_executives[0]
        
        # Fallback to highest confidence executive
        return max(executives, key=lambda e: e.overall_confidence)
    
    def _extract_domain(self, website_url: str) -> str:
        """Extract domain from website URL"""
        try:
            parsed = urlparse(website_url)
            return parsed.netloc or website_url
        except:
            return website_url
    
    def get_statistics(self) -> Dict:
        """Get discovery statistics"""
        total_processed = self.stats['total_companies_processed']
        if total_processed == 0:
            return self.stats
        
        return {
            **self.stats,
            'average_executives_per_company': self.stats['executives_found'] / total_processed,
            'business_name_success_rate': self.stats['business_name_detections'] / total_processed,
            'website_success_rate': self.stats['website_detections'] / total_processed,
            'google_success_rate': self.stats['google_detections'] / total_processed,
            'companies_house_success_rate': self.stats['companies_house_detections'] / total_processed,
        } 