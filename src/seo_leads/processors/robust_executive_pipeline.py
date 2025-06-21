"""
Robust Executive Pipeline - Integrated Executive Extraction System
Combines all components for accurate executive discovery with quality control
"""

import logging
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

# Import our robust components
from ..ai.semantic_name_extractor import SemanticNameExtractor, NameCandidate
from ..extractors.advanced_contact_attributor import AdvancedContactAttributor
from ..scrapers.real_linkedin_discoverer import RealLinkedInDiscoverer
from ..processors.executive_title_extractor import ExecutiveTitleExtractor

@dataclass
class ExecutiveProfile:
    """Complete executive profile with all extracted information"""
    name: str
    title: str
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    
    # Confidence scores
    name_confidence: float = 0.0
    title_confidence: float = 0.0
    email_confidence: float = 0.0
    phone_confidence: float = 0.0
    linkedin_confidence: float = 0.0
    overall_confidence: float = 0.0
    
    # Extraction metadata
    extraction_methods: Dict[str, str] = None
    validation_context: Dict[str, Any] = None

class RobustExecutivePipeline:
    """
    Robust executive extraction pipeline that integrates semantic name recognition,
    advanced contact attribution, real LinkedIn discovery, and context-based title extraction.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize all components
        self.name_extractor = SemanticNameExtractor()
        self.contact_attributor = AdvancedContactAttributor()
        self.linkedin_discoverer = RealLinkedInDiscoverer()
        self.title_extractor = ExecutiveTitleExtractor()
        
        # Quality control thresholds
        self.quality_thresholds = {
            'minimum_name_confidence': 0.6,
            'minimum_overall_confidence': 0.4,
            'maximum_executives_per_company': 10,
            'require_meaningful_title': True
        }
        
        # Performance tracking
        self.performance_metrics = {
            'total_processing_time': 0.0,
            'companies_processed': 0,
            'executives_found': 0,
            'quality_score': 0.0
        }
    
    def extract_executives(self, content: str, company_info: Dict) -> List[ExecutiveProfile]:
        """
        Extract complete executive profiles from website content.
        
        Args:
            content: Website content to analyze
            company_info: Company information including name, domain, etc.
            
        Returns:
            List of validated executive profiles
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting robust executive extraction for {company_info.get('name', 'Unknown')}")
            
            # Phase 1: Semantic Name Recognition
            self.logger.info("Phase 1: Extracting semantic names...")
            validated_names = self.name_extractor.extract_semantic_names(content)
            
            if not validated_names:
                self.logger.warning("No valid names found, returning empty results")
                return []
            
            self.logger.info(f"Found {len(validated_names)} validated names")
            
            # Phase 2: Advanced Contact Attribution
            self.logger.info("Phase 2: Attributing contacts to people...")
            people_with_contacts = self.contact_attributor.attribute_contacts_to_people(
                content, 
                [{'name': name.text, 'position': name.position} for name in validated_names]
            )
            
            # Phase 3: Executive Title Extraction
            self.logger.info("Phase 3: Extracting executive titles...")
            people_with_titles = self.title_extractor.extract_executive_titles(content, people_with_contacts)
            
            # Phase 4: LinkedIn Profile Discovery
            self.logger.info("Phase 4: Discovering LinkedIn profiles...")
            enriched_people = self.linkedin_discoverer.discover_linkedin_profiles(people_with_titles, company_info)
            
            # Phase 5: Quality Control and Executive Profile Creation
            self.logger.info("Phase 5: Quality control and profile creation...")
            executive_profiles = self._create_executive_profiles(enriched_people, validated_names)
            
            # Phase 6: Final Quality Filtering
            filtered_executives = self._apply_quality_filters(executive_profiles)
            
            # Update performance metrics
            processing_time = time.time() - start_time
            self._update_performance_metrics(processing_time, len(filtered_executives))
            
            self.logger.info(f"Extraction complete: {len(filtered_executives)} executives found in {processing_time:.2f}s")
            
            return filtered_executives
            
        except Exception as e:
            self.logger.error(f"Error in robust executive extraction: {str(e)}")
            return []
    
    def _create_executive_profiles(self, enriched_people: List[Dict], original_names: List[NameCandidate]) -> List[ExecutiveProfile]:
        """Create complete executive profiles from enriched data"""
        
        profiles = []
        
        # Create name confidence lookup
        name_confidence_map = {name.text: name.confidence for name in original_names}
        
        for person in enriched_people:
            name = person.get('name', '')
            
            if not name:
                continue
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(person, name_confidence_map)
            
            # Create executive profile
            profile = ExecutiveProfile(
                name=name,
                title=person.get('title', 'Unknown'),
                email=person.get('email'),
                phone=person.get('phone'),
                linkedin_url=person.get('linkedin_url'),
                
                # Confidence scores
                name_confidence=name_confidence_map.get(name, 0.0),
                title_confidence=person.get('title_confidence', 0.0),
                email_confidence=person.get('email_confidence', 0.0),
                phone_confidence=person.get('phone_confidence', 0.0),
                linkedin_confidence=person.get('linkedin_confidence', 0.0),
                overall_confidence=overall_confidence,
                
                # Extraction metadata
                extraction_methods={
                    'name_method': 'semantic_validation',
                    'title_method': person.get('title_extraction_method', 'unknown'),
                    'email_method': person.get('email_method'),
                    'phone_method': person.get('phone_method'),
                    'linkedin_method': person.get('linkedin_discovery_method')
                },
                
                validation_context={
                    'title_context': person.get('title_context', ''),
                    'attribution_context': person.get('attribution_context', {}),
                    'linkedin_validation': person.get('linkedin_validation', '')
                }
            )
            
            profiles.append(profile)
        
        return profiles
    
    def _calculate_overall_confidence(self, person: Dict, name_confidence_map: Dict) -> float:
        """Calculate overall confidence score for an executive profile"""
        
        name_conf = name_confidence_map.get(person.get('name', ''), 0.0)
        title_conf = person.get('title_confidence', 0.0)
        email_conf = person.get('email_confidence', 0.0)
        phone_conf = person.get('phone_confidence', 0.0)
        linkedin_conf = person.get('linkedin_confidence', 0.0)
        
        # Weighted average with bonuses for multiple data points
        base_score = (
            name_conf * 0.3 +           # Name is most important
            title_conf * 0.25 +         # Title is second most important
            email_conf * 0.2 +          # Email attribution
            phone_conf * 0.15 +         # Phone attribution
            linkedin_conf * 0.1         # LinkedIn discovery
        )
        
        # Bonus for having multiple contact methods
        contact_bonus = 0.0
        contact_count = sum([
            1 if email_conf > 0 else 0,
            1 if phone_conf > 0 else 0,
            1 if linkedin_conf > 0 else 0
        ])
        
        if contact_count >= 2:
            contact_bonus = 0.1
        elif contact_count >= 1:
            contact_bonus = 0.05
        
        # Bonus for meaningful title (not "Unknown")
        title_bonus = 0.05 if person.get('title', 'Unknown') != 'Unknown' else 0.0
        
        # Quality penalty for low individual scores
        quality_penalty = 0.0
        if name_conf < 0.5:
            quality_penalty -= 0.1
        if title_conf < 0.3 and person.get('title') != 'Unknown':
            quality_penalty -= 0.05
        
        total_confidence = base_score + contact_bonus + title_bonus + quality_penalty
        
        return max(0.0, min(1.0, total_confidence))
    
    def _apply_quality_filters(self, profiles: List[ExecutiveProfile]) -> List[ExecutiveProfile]:
        """Apply quality filters to ensure only high-quality executive profiles"""
        
        filtered_profiles = []
        
        for profile in profiles:
            # Filter 1: Minimum name confidence
            if profile.name_confidence < self.quality_thresholds['minimum_name_confidence']:
                self.logger.debug(f"Filtered {profile.name}: name confidence too low ({profile.name_confidence:.2f})")
                continue
            
            # Filter 2: Minimum overall confidence
            if profile.overall_confidence < self.quality_thresholds['minimum_overall_confidence']:
                self.logger.debug(f"Filtered {profile.name}: overall confidence too low ({profile.overall_confidence:.2f})")
                continue
            
            # Filter 3: Require meaningful title if enabled
            if (self.quality_thresholds['require_meaningful_title'] and 
                profile.title == 'Unknown' and 
                profile.title_confidence < 0.3):
                self.logger.debug(f"Filtered {profile.name}: no meaningful title")
                continue
            
            # Filter 4: Must have at least one contact method or high confidence
            has_contact = any([profile.email, profile.phone, profile.linkedin_url])
            if not has_contact and profile.overall_confidence < 0.7:
                self.logger.debug(f"Filtered {profile.name}: no contact information and low confidence")
                continue
            
            filtered_profiles.append(profile)
        
        # Filter 5: Limit maximum executives per company
        if len(filtered_profiles) > self.quality_thresholds['maximum_executives_per_company']:
            # Sort by confidence and take top executives
            filtered_profiles.sort(key=lambda x: x.overall_confidence, reverse=True)
            filtered_profiles = filtered_profiles[:self.quality_thresholds['maximum_executives_per_company']]
            self.logger.info(f"Limited to top {self.quality_thresholds['maximum_executives_per_company']} executives")
        
        return filtered_profiles
    
    def _update_performance_metrics(self, processing_time: float, executives_found: int):
        """Update performance tracking metrics"""
        
        self.performance_metrics['total_processing_time'] += processing_time
        self.performance_metrics['companies_processed'] += 1
        self.performance_metrics['executives_found'] += executives_found
        
        # Calculate quality score based on results
        if executives_found > 0:
            self.performance_metrics['quality_score'] = (
                self.performance_metrics['executives_found'] / 
                self.performance_metrics['companies_processed']
            )
    
    def generate_extraction_report(self, profiles: List[ExecutiveProfile], company_info: Dict) -> Dict:
        """Generate comprehensive extraction report"""
        
        if not profiles:
            return {
                'company': company_info.get('name', 'Unknown'),
                'extraction_status': 'no_executives_found',
                'executives_count': 0,
                'quality_metrics': {
                    'average_confidence': 0.0,
                    'contact_coverage': 0.0,
                    'title_coverage': 0.0
                },
                'recommendations': ['Improve content quality', 'Add more executive information']
            }
        
        # Calculate quality metrics
        confidences = [p.overall_confidence for p in profiles]
        avg_confidence = sum(confidences) / len(confidences)
        
        email_coverage = sum(1 for p in profiles if p.email) / len(profiles)
        phone_coverage = sum(1 for p in profiles if p.phone) / len(profiles)
        linkedin_coverage = sum(1 for p in profiles if p.linkedin_url) / len(profiles)
        title_coverage = sum(1 for p in profiles if p.title != 'Unknown') / len(profiles)
        
        # Generate recommendations
        recommendations = []
        if avg_confidence < 0.6:
            recommendations.append("Consider improving name and title information on website")
        if email_coverage < 0.3:
            recommendations.append("Add more email contact information")
        if title_coverage < 0.5:
            recommendations.append("Include executive titles and roles")
        if linkedin_coverage < 0.2:
            recommendations.append("Consider adding LinkedIn profile links")
        
        if not recommendations:
            recommendations.append("Excellent executive information quality")
        
        return {
            'company': company_info.get('name', 'Unknown'),
            'extraction_status': 'success',
            'executives_count': len(profiles),
            'quality_metrics': {
                'average_confidence': avg_confidence,
                'email_coverage': email_coverage,
                'phone_coverage': phone_coverage,
                'linkedin_coverage': linkedin_coverage,
                'title_coverage': title_coverage
            },
            'executives': [
                {
                    'name': p.name,
                    'title': p.title,
                    'email': p.email,
                    'phone': p.phone,
                    'linkedin_url': p.linkedin_url,
                    'confidence': p.overall_confidence,
                    'extraction_quality': self._get_quality_label(p.overall_confidence)
                }
                for p in sorted(profiles, key=lambda x: x.overall_confidence, reverse=True)
            ],
            'recommendations': recommendations,
            'extraction_methods': self._summarize_extraction_methods(profiles)
        }
    
    def _get_quality_label(self, confidence: float) -> str:
        """Get quality label for confidence score"""
        if confidence >= 0.8:
            return 'excellent'
        elif confidence >= 0.6:
            return 'good'
        elif confidence >= 0.4:
            return 'fair'
        else:
            return 'poor'
    
    def _summarize_extraction_methods(self, profiles: List[ExecutiveProfile]) -> Dict:
        """Summarize extraction methods used"""
        
        methods_summary = {
            'name_extraction': 'semantic_validation',
            'title_methods': {},
            'contact_methods': {},
            'linkedin_methods': {}
        }
        
        for profile in profiles:
            if profile.extraction_methods:
                # Count title extraction methods
                title_method = profile.extraction_methods.get('title_method', 'unknown')
                methods_summary['title_methods'][title_method] = methods_summary['title_methods'].get(title_method, 0) + 1
                
                # Count contact methods
                email_method = profile.extraction_methods.get('email_method')
                if email_method:
                    methods_summary['contact_methods'][email_method] = methods_summary['contact_methods'].get(email_method, 0) + 1
                
                # Count LinkedIn methods
                linkedin_method = profile.extraction_methods.get('linkedin_method')
                if linkedin_method:
                    methods_summary['linkedin_methods'][linkedin_method] = methods_summary['linkedin_methods'].get(linkedin_method, 0) + 1
        
        return methods_summary
    
    def get_performance_summary(self) -> Dict:
        """Get overall performance summary"""
        
        if self.performance_metrics['companies_processed'] == 0:
            return {
                'status': 'no_data',
                'message': 'No companies processed yet'
            }
        
        avg_processing_time = (
            self.performance_metrics['total_processing_time'] / 
            self.performance_metrics['companies_processed']
        )
        
        avg_executives_per_company = (
            self.performance_metrics['executives_found'] / 
            self.performance_metrics['companies_processed']
        )
        
        return {
            'status': 'active',
            'companies_processed': self.performance_metrics['companies_processed'],
            'total_executives_found': self.performance_metrics['executives_found'],
            'average_processing_time': avg_processing_time,
            'average_executives_per_company': avg_executives_per_company,
            'quality_score': self.performance_metrics['quality_score'],
            'performance_rating': self._get_performance_rating()
        }
    
    def _get_performance_rating(self) -> str:
        """Get overall performance rating"""
        
        quality_score = self.performance_metrics['quality_score']
        
        if quality_score >= 2.0:
            return 'excellent'
        elif quality_score >= 1.5:
            return 'good'
        elif quality_score >= 1.0:
            return 'fair'
        else:
            return 'needs_improvement'
    
    def export_profiles_to_dict(self, profiles: List[ExecutiveProfile]) -> List[Dict]:
        """Export executive profiles to dictionary format for JSON serialization"""
        
        return [
            {
                'name': profile.name,
                'title': profile.title,
                'email': profile.email,
                'phone': profile.phone,
                'linkedin_url': profile.linkedin_url,
                'confidence_scores': {
                    'name': profile.name_confidence,
                    'title': profile.title_confidence,
                    'email': profile.email_confidence,
                    'phone': profile.phone_confidence,
                    'linkedin': profile.linkedin_confidence,
                    'overall': profile.overall_confidence
                },
                'extraction_metadata': profile.extraction_methods,
                'validation_context': profile.validation_context
            }
            for profile in profiles
        ] 