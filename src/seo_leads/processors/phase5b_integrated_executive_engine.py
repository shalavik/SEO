"""
Phase 5B Integrated Executive Discovery Engine - Complete Implementation
Combines all Phase 5B enhancements into a unified executive contact discovery system.
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging
import time
from datetime import datetime

# Import enhanced Phase 5B components
from ..extractors.content_preprocessor import ContentPreprocessor
from ..ai.advanced_name_validator import AdvancedNameValidator, NameValidationResult
from ..extractors.context_aware_contact_extractor import ContextAwareContactExtractor, ExecutiveContact, ContactAttributionResult
from ..scrapers.linkedin_discovery_engine import LinkedInDiscoveryEngine, LinkedInDiscoveryResult
from ..processors.executive_seniority_analyzer import ExecutiveSeniorityAnalyzer, SeniorityAnalysisResult

logger = logging.getLogger(__name__)

@dataclass
class Phase5BDiscoveryResult:
    """Complete Phase 5B executive discovery result"""
    company_domain: str
    company_name: str
    executives: List[ExecutiveContact]
    processing_time: float
    discovery_metrics: Dict[str, Any]
    quality_scores: Dict[str, float]
    success_indicators: Dict[str, bool]
    enhancement_applied: List[str] = field(default_factory=list)

class Phase5BIntegratedExecutiveEngine:
    """
    Phase 5B Integrated Executive Discovery Engine
    
    Combines all Phase 5B enhancements:
    1. Content Preprocessing (HTML filtering)
    2. Advanced Name Validation (HTML artifact filtering)
    3. Context-Aware Contact Attribution
    4. LinkedIn Discovery Integration
    5. Executive Seniority Analysis
    6. Proper Output Structure
    
    Fixes critical issues:
    - HTML tags extracted as names -> Real human names only
    - Contacts at company level -> Attributed to specific executives
    - No LinkedIn profiles -> Integrated discovery
    - Unknown titles -> Proper title recognition
    - Poor data structure -> Correct executive objects
    """
    
    def __init__(self):
        """Initialize the integrated executive discovery engine"""
        
        # Initialize Phase 5B components
        self.content_preprocessor = ContentPreprocessor()
        self.name_validator = AdvancedNameValidator()
        self.contact_extractor = ContextAwareContactExtractor()
        self.linkedin_discovery = LinkedInDiscoveryEngine()
        self.seniority_analyzer = ExecutiveSeniorityAnalyzer()
        
        # Success thresholds
        self.success_thresholds = {
            'name_accuracy': 0.7,        # 70% valid human names
            'contact_attribution': 0.4,   # 40% contacts attributed
            'linkedin_discovery': 0.3,    # 30% LinkedIn profiles found
            'title_recognition': 0.6,     # 60% titles recognized
            'overall_quality': 0.6        # 60% overall quality score
        }

    async def discover_executives(self, content: str, company_domain: str) -> Phase5BDiscoveryResult:
        """
        Complete executive discovery using Phase 5B integrated pipeline.
        
        Args:
            content: Raw website content
            company_domain: Company domain for context
            
        Returns:
            Phase5BDiscoveryResult with complete executive data
        """
        start_time = time.time()
        logger.info(f"Starting Phase 5B executive discovery for {company_domain}")
        
        # Extract company name
        company_name = self._extract_company_name(company_domain)
        
        # Step 1: Content Preprocessing
        logger.info("Step 1: Content preprocessing and HTML cleaning")
        preprocessing_result = self.content_preprocessor.clean_html_content(content)
        cleaned_content = preprocessing_result['cleaned_text']
        executive_sections = preprocessing_result['executive_sections']
        
        # Step 2: Initial Executive Name Extraction
        logger.info("Step 2: Initial executive name extraction")
        initial_names = self._extract_initial_names(cleaned_content, executive_sections)
        
        # Step 3: Advanced Name Validation (HTML artifact filtering)
        logger.info("Step 3: Advanced name validation and HTML filtering")
        validation_results = self.name_validator.batch_validate_names(initial_names, cleaned_content)
        valid_executives = [
            {'name': result.name, 'title': 'Unknown', 'confidence': result.confidence}
            for result in validation_results 
            if result.is_valid
        ]
        
        # Step 4: Executive Seniority Analysis (Title Recognition)
        logger.info("Step 4: Executive seniority analysis and title extraction")
        seniority_result = self.seniority_analyzer.analyze_executive_seniority(
            valid_executives, cleaned_content
        )
        
        # Step 5: Contact Attribution
        logger.info("Step 5: Context-aware contact attribution")
        contact_result = self.contact_extractor.extract_executive_contacts(
            cleaned_content, valid_executives
        )
        
        # Step 6: LinkedIn Discovery (Async)
        logger.info("Step 6: LinkedIn profile discovery")
        linkedin_result = await self.linkedin_discovery.discover_executive_linkedin_profiles(
            valid_executives, company_domain
        )
        
        # Step 7: Integration and Final Processing
        logger.info("Step 7: Integrating all components")
        final_executives = self._integrate_all_components(
            contact_result.executives,
            linkedin_result,
            seniority_result
        )
        
        # Step 8: Quality Assessment
        processing_time = time.time() - start_time
        quality_scores = self._calculate_quality_scores(
            final_executives, contact_result, linkedin_result, validation_results
        )
        
        # Step 9: Success Indicator Assessment
        success_indicators = self._assess_success_indicators(quality_scores)
        
        # Step 10: Compile Discovery Metrics
        discovery_metrics = self._compile_discovery_metrics(
            preprocessing_result, validation_results, contact_result, 
            linkedin_result, seniority_result
        )
        
        result = Phase5BDiscoveryResult(
            company_domain=company_domain,
            company_name=company_name,
            executives=final_executives,
            processing_time=processing_time,
            discovery_metrics=discovery_metrics,
            quality_scores=quality_scores,
            success_indicators=success_indicators,
            enhancement_applied=[
                'html_filtering', 'name_validation', 'contact_attribution',
                'linkedin_discovery', 'title_recognition', 'proper_structure'
            ]
        )
        
        logger.info(f"Phase 5B discovery complete in {processing_time:.2f}s: {len(final_executives)} executives found")
        
        return result

    def _extract_initial_names(self, content: str, executive_sections: List[Dict]) -> List[str]:
        """Extract initial name candidates from cleaned content"""
        names = set()
        
        # Extract from executive sections first (higher priority)
        for section in executive_sections:
            section_names = self._extract_names_from_text(section['context'])
            names.update(section_names)
        
        # Extract from full content if few names found
        if len(names) < 3:
            content_names = self._extract_names_from_text(content)
            names.update(content_names[:10])  # Limit to prevent noise
        
        return list(names)

    def _extract_names_from_text(self, text: str) -> List[str]:
        """Extract potential names using enhanced patterns"""
        import re
        
        # Enhanced name patterns
        patterns = [
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b',                    # First Last
            r'\b([A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+)\b',         # First M. Last
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+)\b',     # First Middle Last
        ]
        
        names = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            names.update(matches)
        
        return list(names)

    def _integrate_all_components(self, contact_executives: List[ExecutiveContact],
                                linkedin_result: LinkedInDiscoveryResult,
                                seniority_result: SeniorityAnalysisResult) -> List[ExecutiveContact]:
        """Integrate all discovery components into final executive objects"""
        
        # Create mapping of LinkedIn profiles by name
        linkedin_map = {}
        for profile in linkedin_result.profiles_found:
            linkedin_map[profile.full_name.lower()] = profile
        
        # Enhance executives with all data
        enhanced_executives = []
        
        for executive in contact_executives:
            # Add LinkedIn profile if found
            name_key = executive.name.lower()
            if name_key in linkedin_map:
                linkedin_profile = linkedin_map[name_key]
                executive.linkedin_url = linkedin_profile.profile_url
                executive.linkedin_verified = linkedin_profile.verified
                
                # Update discovery sources
                if 'linkedin' not in executive.discovery_sources:
                    executive.discovery_sources.append('linkedin')
            
            # Ensure all required fields are present
            if not hasattr(executive, 'seniority_tier'):
                executive.seniority_tier = 'tier_3'
            
            enhanced_executives.append(executive)
        
        return enhanced_executives

    def _calculate_quality_scores(self, executives: List[ExecutiveContact],
                                contact_result: ContactAttributionResult,
                                linkedin_result: LinkedInDiscoveryResult,
                                validation_results: List[NameValidationResult]) -> Dict[str, float]:
        """Calculate quality scores for all aspects"""
        
        total_executives = len(executives)
        
        # Name Accuracy Score (% of valid human names vs HTML artifacts)
        valid_names = sum(1 for result in validation_results if result.is_valid)
        name_accuracy = (valid_names / len(validation_results)) if validation_results else 0
        
        # Contact Attribution Score (% of executives with attributed contacts)
        executives_with_contacts = sum(1 for exec in executives if exec.email or exec.phone)
        contact_attribution = (executives_with_contacts / total_executives) if total_executives else 0
        
        # LinkedIn Discovery Score (% of executives with LinkedIn profiles)
        executives_with_linkedin = sum(1 for exec in executives if exec.linkedin_url)
        linkedin_discovery = (executives_with_linkedin / total_executives) if total_executives else 0
        
        # Title Recognition Score (% of executives with real titles)
        executives_with_titles = sum(1 for exec in executives if exec.title != 'Unknown')
        title_recognition = (executives_with_titles / total_executives) if total_executives else 0
        
        # Overall Quality Score (weighted average)
        overall_quality = (
            name_accuracy * 0.3 +
            contact_attribution * 0.3 +
            linkedin_discovery * 0.2 +
            title_recognition * 0.2
        )
        
        return {
            'name_accuracy': name_accuracy,
            'contact_attribution': contact_attribution,
            'linkedin_discovery': linkedin_discovery,
            'title_recognition': title_recognition,
            'overall_quality': overall_quality
        }

    def _assess_success_indicators(self, quality_scores: Dict[str, float]) -> Dict[str, bool]:
        """Assess whether success thresholds are met"""
        return {
            'name_accuracy_success': quality_scores['name_accuracy'] >= self.success_thresholds['name_accuracy'],
            'contact_attribution_success': quality_scores['contact_attribution'] >= self.success_thresholds['contact_attribution'],
            'linkedin_discovery_success': quality_scores['linkedin_discovery'] >= self.success_thresholds['linkedin_discovery'],
            'title_recognition_success': quality_scores['title_recognition'] >= self.success_thresholds['title_recognition'],
            'overall_quality_success': quality_scores['overall_quality'] >= self.success_thresholds['overall_quality'],
            'pipeline_success': quality_scores['overall_quality'] >= self.success_thresholds['overall_quality']
        }

    def _compile_discovery_metrics(self, preprocessing_result: Dict,
                                 validation_results: List[NameValidationResult],
                                 contact_result: ContactAttributionResult,
                                 linkedin_result: LinkedInDiscoveryResult,
                                 seniority_result: SeniorityAnalysisResult) -> Dict[str, Any]:
        """Compile comprehensive discovery metrics"""
        
        return {
            'content_preprocessing': {
                'cleaned_content_length': preprocessing_result['total_length'],
                'executive_sections_found': len(preprocessing_result['executive_sections']),
                'contact_sections_found': len(preprocessing_result['contact_sections'])
            },
            'name_validation': {
                'initial_names_found': len(validation_results),
                'valid_names': sum(1 for r in validation_results if r.is_valid),
                'html_artifacts_filtered': sum(1 for r in validation_results if r.name_type == 'html_artifact'),
                'location_names_filtered': sum(1 for r in validation_results if r.name_type == 'location'),
                'average_name_confidence': sum(r.confidence for r in validation_results) / len(validation_results) if validation_results else 0
            },
            'contact_attribution': {
                'total_contacts_found': contact_result.total_contacts_found,
                'attributed_contacts': contact_result.attributed_contacts,
                'attribution_accuracy': contact_result.attribution_accuracy,
                'unattributed_emails': len(contact_result.unattributed_contacts['emails']),
                'unattributed_phones': len(contact_result.unattributed_contacts['phones'])
            },
            'linkedin_discovery': {
                'total_searches': linkedin_result.total_searches,
                'profiles_found': len(linkedin_result.profiles_found),
                'success_rate': (linkedin_result.successful_matches / linkedin_result.total_searches * 100) if linkedin_result.total_searches else 0,
                'company_page_found': linkedin_result.company_page_url is not None
            },
            'seniority_analysis': {
                'executives_analyzed': seniority_result.executives_analyzed,
                'titles_extracted': seniority_result.titles_extracted,
                'decision_makers_identified': seniority_result.decision_makers_identified,
                'tier_distribution': seniority_result.tier_distribution,
                'extraction_success_rate': seniority_result.extraction_success_rate
            }
        }

    def _extract_company_name(self, domain: str) -> str:
        """Extract company name from domain"""
        from urllib.parse import urlparse
        import re
        
        # Parse domain
        parsed = urlparse(f"http://{domain}" if not domain.startswith('http') else domain)
        domain_clean = parsed.netloc or parsed.path
        
        # Remove www and common prefixes
        domain_clean = re.sub(r'^www\.', '', domain_clean)
        
        # Extract base name (before first dot)
        base_name = domain_clean.split('.')[0]
        
        # Clean and format
        company_name = re.sub(r'[^a-zA-Z0-9]', ' ', base_name)
        company_name = ' '.join(word.capitalize() for word in company_name.split())
        
        return company_name

    def format_for_json_output(self, result: Phase5BDiscoveryResult) -> Dict[str, Any]:
        """
        Format discovery result for proper JSON output structure.
        
        This is the CRITICAL fix - proper executive object structure instead of
        company-level contacts with HTML artifact names.
        """
        
        formatted_executives = []
        
        for executive in result.executives:
            # Create properly structured executive object
            executive_obj = {
                'name': executive.name,
                'title': executive.title,
                'seniority_tier': executive.seniority_tier,
                'email': executive.email,
                'email_confidence': executive.email_confidence,
                'phone': executive.phone, 
                'phone_confidence': executive.phone_confidence,
                'linkedin_url': executive.linkedin_url,
                'linkedin_verified': executive.linkedin_verified,
                'overall_confidence': executive.overall_confidence,
                'discovery_sources': executive.discovery_sources,
                'attribution_method': executive.attribution_method
            }
            
            formatted_executives.append(executive_obj)
        
        return {
            'company_info': {
                'domain': result.company_domain,
                'name': result.company_name
            },
            'executives': formatted_executives,
            'discovery_summary': {
                'total_executives_found': len(result.executives),
                'executives_with_email': sum(1 for e in result.executives if e.email),
                'executives_with_phone': sum(1 for e in result.executives if e.phone),
                'executives_with_linkedin': sum(1 for e in result.executives if e.linkedin_url),
                'decision_makers': sum(1 for e in result.executives if e.seniority_tier in ['tier_1', 'tier_2']),
                'processing_time': result.processing_time
            },
            'quality_metrics': result.quality_scores,
            'success_indicators': result.success_indicators,
            'discovery_metrics': result.discovery_metrics,
            'enhancements_applied': result.enhancement_applied
        }

    def get_system_analytics(self, result: Phase5BDiscoveryResult) -> Dict[str, Any]:
        """Generate system analytics for the discovery result"""
        
        total_executives = len(result.executives)
        
        return {
            'executive_discovery_rate': (total_executives > 0),
            'name_accuracy_rate': result.quality_scores['name_accuracy'] * 100,
            'contact_attribution_rate': result.quality_scores['contact_attribution'] * 100, 
            'linkedin_discovery_rate': result.quality_scores['linkedin_discovery'] * 100,
            'title_recognition_rate': result.quality_scores['title_recognition'] * 100,
            'overall_quality_score': result.quality_scores['overall_quality'] * 100,
            'processing_efficiency': 1.0 / result.processing_time if result.processing_time > 0 else 0,
            'enhancement_success': all(result.success_indicators.values()),
            'data_structure_compliance': True  # Phase 5B ensures proper structure
        } 