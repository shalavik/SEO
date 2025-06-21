"""
Multi-Source Validation Engine - Phase 5
Cross-validates executive data across multiple sources for accuracy
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time

logger = logging.getLogger(__name__)

class ValidationStatus(Enum):
    """Validation status for executive data"""
    VALIDATED = "Validated"
    PARTIALLY_VALIDATED = "Partially Validated"
    CONFLICTING = "Conflicting Data"
    INSUFFICIENT_DATA = "Insufficient Data"
    INVALID = "Invalid"

class ConfidenceLevel(Enum):
    """Confidence levels for validated data"""
    HIGH = "High Confidence (90%+)"
    MEDIUM = "Medium Confidence (70-89%)"
    LOW = "Low Confidence (50-69%)"
    VERY_LOW = "Very Low Confidence (<50%)"

@dataclass
class ValidationSource:
    """Source of validation data"""
    source_name: str
    source_type: str  # 'website', 'companies_house', 'linkedin', 'directory'
    data_extracted: Dict[str, any]
    extraction_confidence: float
    last_updated: float = field(default_factory=time.time)

@dataclass
class ValidationResult:
    """Result of cross-source validation"""
    executive_name: str
    validated_data: Dict[str, any]
    validation_status: ValidationStatus
    confidence_level: ConfidenceLevel
    confidence_score: float
    sources_used: List[ValidationSource]
    validation_notes: List[str]
    conflicts_found: List[str]
    recommended_action: str

@dataclass
class ComprehensiveValidationReport:
    """Complete validation report for all executives"""
    company_name: str
    total_executives_processed: int
    validation_results: List[ValidationResult]
    overall_data_quality: float
    validation_summary: Dict[str, int]
    processing_time: float

class MultiSourceValidationEngine:
    """Cross-validates executive data across multiple sources"""
    
    def __init__(self):
        # Validation weights for different source types
        self.source_weights = {
            'companies_house': 1.0,  # Official government data
            'website_about': 0.9,    # Company's own information
            'website_contact': 0.8,  # Company contact pages
            'linkedin': 0.7,         # Professional profiles
            'business_directory': 0.6, # Third-party directories
            'social_media': 0.5,     # Social media profiles
            'extracted_content': 0.4  # General content extraction
        }
        
        # Data field importance weights
        self.field_weights = {
            'name': 1.0,
            'title': 0.9,
            'email': 0.8,
            'phone': 0.8,
            'linkedin_profile': 0.7,
            'company': 0.6,
            'department': 0.5
        }
        
        # Validation rules
        self.validation_rules = {
            'name': self._validate_name_consistency,
            'title': self._validate_title_consistency,
            'email': self._validate_email_consistency,
            'phone': self._validate_phone_consistency,
            'linkedin_profile': self._validate_linkedin_consistency
        }
        
        # Statistics
        self.validation_stats = {
            'total_validations': 0,
            'high_confidence_results': 0,
            'medium_confidence_results': 0,
            'low_confidence_results': 0,
            'validation_failures': 0,
            'conflicts_detected': 0
        }
    
    async def validate_executives(self, executives_data: List[Dict], 
                                validation_sources: List[ValidationSource],
                                company_name: str = "") -> ComprehensiveValidationReport:
        """Validate executive data across multiple sources"""
        logger.info(f"🔍 Cross-validating {len(executives_data)} executives across {len(validation_sources)} sources")
        
        start_time = time.time()
        self.validation_stats['total_validations'] += 1
        
        validation_results = []
        
        # Process each executive
        for exec_data in executives_data:
            result = await self._validate_single_executive(exec_data, validation_sources)
            validation_results.append(result)
        
        # Calculate overall metrics
        overall_quality = self._calculate_overall_data_quality(validation_results)
        validation_summary = self._create_validation_summary(validation_results)
        processing_time = time.time() - start_time
        
        # Update statistics
        for result in validation_results:
            if result.confidence_level == ConfidenceLevel.HIGH:
                self.validation_stats['high_confidence_results'] += 1
            elif result.confidence_level == ConfidenceLevel.MEDIUM:
                self.validation_stats['medium_confidence_results'] += 1
            elif result.confidence_level == ConfidenceLevel.LOW:
                self.validation_stats['low_confidence_results'] += 1
            
            if result.validation_status == ValidationStatus.INVALID:
                self.validation_stats['validation_failures'] += 1
            
            if result.conflicts_found:
                self.validation_stats['conflicts_detected'] += 1
        
        logger.info(f"✅ Validation complete: {len(validation_results)} executives processed in {processing_time:.2f}s")
        
        return ComprehensiveValidationReport(
            company_name=company_name,
            total_executives_processed=len(executives_data),
            validation_results=validation_results,
            overall_data_quality=overall_quality,
            validation_summary=validation_summary,
            processing_time=processing_time
        )
    
    async def _validate_single_executive(self, exec_data: Dict, 
                                       sources: List[ValidationSource]) -> ValidationResult:
        """Validate a single executive across sources"""
        executive_name = exec_data.get('name', 'Unknown')
        logger.debug(f"🔍 Validating: {executive_name}")
        
        # Collect all source data for this executive
        relevant_sources = self._find_relevant_sources(exec_data, sources)
        
        # Cross-validate each data field
        validated_data = {}
        validation_notes = []
        conflicts_found = []
        
        for field_name in self.field_weights.keys():
            if field_name in exec_data:
                validation_result = await self._validate_field(
                    field_name, exec_data[field_name], relevant_sources
                )
                
                validated_data[field_name] = validation_result['validated_value']
                validation_notes.extend(validation_result['notes'])
                conflicts_found.extend(validation_result['conflicts'])
        
        # Calculate overall confidence
        confidence_score = self._calculate_confidence_score(validated_data, relevant_sources)
        confidence_level = self._determine_confidence_level(confidence_score)
        
        # Determine validation status
        validation_status = self._determine_validation_status(
            validated_data, relevant_sources, conflicts_found
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(validation_status, confidence_level, conflicts_found)
        
        return ValidationResult(
            executive_name=executive_name,
            validated_data=validated_data,
            validation_status=validation_status,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            sources_used=relevant_sources,
            validation_notes=validation_notes,
            conflicts_found=conflicts_found,
            recommended_action=recommendation
        )
    
    def _find_relevant_sources(self, exec_data: Dict, 
                             all_sources: List[ValidationSource]) -> List[ValidationSource]:
        """Find sources relevant to this executive"""
        relevant_sources = []
        exec_name = exec_data.get('name', '').lower()
        
        for source in all_sources:
            # Check if source contains data about this executive
            source_data = source.data_extracted
            
            # Look for name matches in various fields
            name_found = False
            for key, value in source_data.items():
                if isinstance(value, str) and exec_name in value.lower():
                    name_found = True
                    break
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and exec_name in item.lower():
                            name_found = True
                            break
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, str) and exec_name in sub_value.lower():
                            name_found = True
                            break
            
            if name_found:
                relevant_sources.append(source)
        
        return relevant_sources
    
    async def _validate_field(self, field_name: str, field_value: any, 
                            sources: List[ValidationSource]) -> Dict[str, any]:
        """Validate a specific field across sources"""
        validation_func = self.validation_rules.get(field_name, self._validate_generic_field)
        return await validation_func(field_value, sources)
    
    async def _validate_name_consistency(self, name: str, 
                                       sources: List[ValidationSource]) -> Dict[str, any]:
        """Validate name consistency across sources"""
        source_names = []
        notes = []
        conflicts = []
        
        # Collect names from all sources
        for source in sources:
            source_data = source.data_extracted
            
            # Look for name fields
            name_fields = ['name', 'executive_name', 'contact_name', 'director_name']
            for field in name_fields:
                if field in source_data:
                    source_name = source_data[field]
                    if isinstance(source_name, str):
                        source_names.append((source_name, source.source_name, source.source_type))
        
        # Analyze name consistency
        if len(source_names) <= 1:
            notes.append(f"Limited name validation: only {len(source_names)} source(s)")
            return {
                'validated_value': name,
                'notes': notes,
                'conflicts': conflicts
            }
        
        # Check for conflicts
        normalized_names = [self._normalize_name(n[0]) for n in source_names]
        base_name = self._normalize_name(name)
        
        consistent_names = sum(1 for n in normalized_names if self._names_match(base_name, n))
        
        if consistent_names >= len(normalized_names) * 0.7:  # 70% agreement
            notes.append(f"Name validated across {consistent_names}/{len(normalized_names)} sources")
            validated_name = name  # Keep original
        else:
            conflicts.append(f"Name inconsistency: {[n[0] for n in source_names]}")
            # Choose most common or highest weighted source
            validated_name = self._choose_best_name(source_names)
        
        return {
            'validated_value': validated_name,
            'notes': notes,
            'conflicts': conflicts
        }
    
    async def _validate_title_consistency(self, title: str, 
                                        sources: List[ValidationSource]) -> Dict[str, any]:
        """Validate job title consistency"""
        source_titles = []
        notes = []
        conflicts = []
        
        # Collect titles from sources
        for source in sources:
            source_data = source.data_extracted
            title_fields = ['title', 'job_title', 'position', 'role']
            
            for field in title_fields:
                if field in source_data:
                    source_title = source_data[field]
                    if isinstance(source_title, str):
                        source_titles.append((source_title, source.source_name, source.source_type))
        
        # Analyze title consistency
        if not source_titles:
            notes.append("No title validation sources available")
            return {
                'validated_value': title,
                'notes': notes,
                'conflicts': conflicts
            }
        
        # Check for semantic similarity
        similar_titles = sum(1 for t in source_titles 
                           if self._titles_similar(title, t[0]))
        
        if similar_titles >= len(source_titles) * 0.6:  # 60% agreement
            notes.append(f"Title validated across {similar_titles}/{len(source_titles)} sources")
            validated_title = title
        else:
            conflicts.append(f"Title variations: {[t[0] for t in source_titles]}")
            # Choose most authoritative source
            validated_title = self._choose_best_title(source_titles)
        
        return {
            'validated_value': validated_title,
            'notes': notes,
            'conflicts': conflicts
        }
    
    async def _validate_email_consistency(self, email: str, 
                                        sources: List[ValidationSource]) -> Dict[str, any]:
        """Validate email consistency"""
        source_emails = []
        notes = []
        conflicts = []
        
        # Collect emails from sources
        for source in sources:
            source_data = source.data_extracted
            email_fields = ['email', 'email_address', 'contact_email']
            
            for field in email_fields:
                if field in source_data:
                    source_email = source_data[field]
                    if isinstance(source_email, str) and '@' in source_email:
                        source_emails.append((source_email.lower(), source.source_name, source.source_type))
        
        # Analyze email consistency
        email_lower = email.lower()
        matching_emails = sum(1 for e in source_emails if e[0] == email_lower)
        
        if matching_emails > 0:
            notes.append(f"Email validated across {matching_emails} source(s)")
            validated_email = email
        else:
            if source_emails:
                conflicts.append(f"Email mismatch: found {[e[0] for e in source_emails]}")
                # Choose highest weighted source
                validated_email = self._choose_best_email(source_emails)
            else:
                notes.append("No email validation sources available")
                validated_email = email
        
        return {
            'validated_value': validated_email,
            'notes': notes,
            'conflicts': conflicts
        }
    
    async def _validate_phone_consistency(self, phone: str, 
                                        sources: List[ValidationSource]) -> Dict[str, any]:
        """Validate phone number consistency"""
        source_phones = []
        notes = []
        conflicts = []
        
        # Normalize original phone
        normalized_original = self._normalize_phone(phone)
        
        # Collect phones from sources
        for source in sources:
            source_data = source.data_extracted
            phone_fields = ['phone', 'telephone', 'mobile', 'contact_number']
            
            for field in phone_fields:
                if field in source_data:
                    source_phone = source_data[field]
                    if isinstance(source_phone, str):
                        normalized_phone = self._normalize_phone(source_phone)
                        if normalized_phone:
                            source_phones.append((normalized_phone, source.source_name, source.source_type))
        
        # Analyze phone consistency
        matching_phones = sum(1 for p in source_phones if p[0] == normalized_original)
        
        if matching_phones > 0:
            notes.append(f"Phone validated across {matching_phones} source(s)")
            validated_phone = phone
        else:
            if source_phones:
                conflicts.append(f"Phone mismatch: found {[p[0] for p in source_phones]}")
                validated_phone = self._choose_best_phone(source_phones)
            else:
                notes.append("No phone validation sources available")
                validated_phone = phone
        
        return {
            'validated_value': validated_phone,
            'notes': notes,
            'conflicts': conflicts
        }
    
    async def _validate_linkedin_consistency(self, linkedin_url: str, 
                                           sources: List[ValidationSource]) -> Dict[str, any]:
        """Validate LinkedIn profile consistency"""
        source_profiles = []
        notes = []
        conflicts = []
        
        # Normalize original URL
        normalized_original = self._normalize_linkedin_url(linkedin_url)
        
        # Collect LinkedIn profiles from sources
        for source in sources:
            source_data = source.data_extracted
            linkedin_fields = ['linkedin', 'linkedin_profile', 'linkedin_url', 'profile_url']
            
            for field in linkedin_fields:
                if field in source_data:
                    source_profile = source_data[field]
                    if isinstance(source_profile, str) and 'linkedin.com' in source_profile:
                        normalized_profile = self._normalize_linkedin_url(source_profile)
                        if normalized_profile:
                            source_profiles.append((normalized_profile, source.source_name, source.source_type))
        
        # Analyze LinkedIn consistency
        matching_profiles = sum(1 for p in source_profiles if p[0] == normalized_original)
        
        if matching_profiles > 0:
            notes.append(f"LinkedIn profile validated across {matching_profiles} source(s)")
            validated_linkedin = linkedin_url
        else:
            if source_profiles:
                conflicts.append(f"LinkedIn profile mismatch: found {[p[0] for p in source_profiles]}")
                validated_linkedin = self._choose_best_linkedin(source_profiles)
            else:
                notes.append("No LinkedIn validation sources available")
                validated_linkedin = linkedin_url
        
        return {
            'validated_value': validated_linkedin,
            'notes': notes,
            'conflicts': conflicts
        }
    
    async def _validate_generic_field(self, field_value: any, 
                                    sources: List[ValidationSource]) -> Dict[str, any]:
        """Generic field validation"""
        return {
            'validated_value': field_value,
            'notes': ["Generic validation - no specific rules"],
            'conflicts': []
        }
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        if not name:
            return ""
        
        # Remove titles, punctuation, normalize spacing
        import re
        clean = re.sub(r'\b(mr|mrs|ms|dr|prof|sir|lady)\b', '', name.lower())
        clean = re.sub(r'[^\w\s]', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if two normalized names match"""
        if not name1 or not name2:
            return False
        
        # Split into parts
        parts1 = set(name1.split())
        parts2 = set(name2.split())
        
        # Check for significant overlap
        overlap = len(parts1.intersection(parts2))
        min_parts = min(len(parts1), len(parts2))
        
        return overlap >= min_parts * 0.7  # 70% overlap
    
    def _titles_similar(self, title1: str, title2: str) -> bool:
        """Check if two job titles are semantically similar"""
        if not title1 or not title2:
            return False
        
        # Normalize titles
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()
        
        # Direct match
        if t1 == t2:
            return True
        
        # Key word matching
        import re
        words1 = set(re.findall(r'\w+', t1))
        words2 = set(re.findall(r'\w+', t2))
        
        # Remove common words
        common_words = {'the', 'and', 'of', 'at', 'in', 'for', 'to', 'a', 'an'}
        words1 -= common_words
        words2 -= common_words
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1.intersection(words2))
        return overlap >= min(len(words1), len(words2)) * 0.5
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number"""
        if not phone:
            return ""
        
        # Remove all non-digits and +
        import re
        clean = re.sub(r'[^\d+]', '', phone)
        
        # Normalize UK numbers
        if clean.startswith('0'):
            clean = '+44' + clean[1:]
        elif clean.startswith('44'):
            clean = '+' + clean
        
        return clean
    
    def _normalize_linkedin_url(self, url: str) -> str:
        """Normalize LinkedIn URL"""
        if not url:
            return ""
        
        # Extract profile ID
        import re
        match = re.search(r'linkedin\.com/in/([^/?]+)', url.lower())
        if match:
            return f"linkedin.com/in/{match.group(1)}"
        
        return url.lower()
    
    def _choose_best_name(self, source_names: List[Tuple[str, str, str]]) -> str:
        """Choose the best name from conflicting sources"""
        if not source_names:
            return ""
        
        # Weight by source type
        weighted_names = []
        for name, source_name, source_type in source_names:
            weight = self.source_weights.get(source_type, 0.5)
            weighted_names.append((name, weight))
        
        # Choose highest weighted
        best_name = max(weighted_names, key=lambda x: x[1])
        return best_name[0]
    
    def _choose_best_title(self, source_titles: List[Tuple[str, str, str]]) -> str:
        """Choose the best title from conflicting sources"""
        return self._choose_best_name(source_titles)
    
    def _choose_best_email(self, source_emails: List[Tuple[str, str, str]]) -> str:
        """Choose the best email from conflicting sources"""
        return self._choose_best_name(source_emails)
    
    def _choose_best_phone(self, source_phones: List[Tuple[str, str, str]]) -> str:
        """Choose the best phone from conflicting sources"""
        return self._choose_best_name(source_phones)
    
    def _choose_best_linkedin(self, source_profiles: List[Tuple[str, str, str]]) -> str:
        """Choose the best LinkedIn profile from conflicting sources"""
        return self._choose_best_name(source_profiles)
    
    def _calculate_confidence_score(self, validated_data: Dict, 
                                  sources: List[ValidationSource]) -> float:
        """Calculate overall confidence score"""
        if not validated_data or not sources:
            return 0.0
        
        total_weight = 0.0
        weighted_confidence = 0.0
        
        # Weight by field importance and source quality
        for field, value in validated_data.items():
            field_weight = self.field_weights.get(field, 0.5)
            
            # Calculate source confidence for this field
            field_source_confidence = 0.0
            relevant_sources = 0
            
            for source in sources:
                if field in source.data_extracted:
                    source_weight = self.source_weights.get(source.source_type, 0.5)
                    field_source_confidence += source.extraction_confidence * source_weight
                    relevant_sources += 1
            
            if relevant_sources > 0:
                avg_source_confidence = field_source_confidence / relevant_sources
                weighted_confidence += field_weight * avg_source_confidence
                total_weight += field_weight
        
        if total_weight == 0:
            return 0.0
        
        base_confidence = weighted_confidence / total_weight
        
        # Boost for multiple sources
        source_diversity_boost = min(0.2, len(sources) * 0.05)
        
        return min(1.0, base_confidence + source_diversity_boost)
    
    def _determine_confidence_level(self, confidence_score: float) -> ConfidenceLevel:
        """Determine confidence level from score"""
        if confidence_score >= 0.9:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.7:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= 0.5:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _determine_validation_status(self, validated_data: Dict,
                                   sources: List[ValidationSource],
                                   conflicts: List[str]) -> ValidationStatus:
        """Determine overall validation status"""
        if not validated_data:
            return ValidationStatus.INSUFFICIENT_DATA
        
        if len(conflicts) > len(validated_data) * 0.5:  # More than 50% conflicts
            return ValidationStatus.CONFLICTING
        
        if len(sources) >= 2 and not conflicts:
            return ValidationStatus.VALIDATED
        
        if len(sources) >= 1:
            return ValidationStatus.PARTIALLY_VALIDATED
        
        return ValidationStatus.INSUFFICIENT_DATA
    
    def _generate_recommendation(self, status: ValidationStatus,
                               confidence: ConfidenceLevel,
                               conflicts: List[str]) -> str:
        """Generate action recommendation"""
        if status == ValidationStatus.VALIDATED and confidence == ConfidenceLevel.HIGH:
            return "✅ Use data with high confidence"
        
        elif status == ValidationStatus.VALIDATED and confidence == ConfidenceLevel.MEDIUM:
            return "✅ Use data with medium confidence"
        
        elif status == ValidationStatus.PARTIALLY_VALIDATED:
            return "⚠️ Use with caution - limited validation"
        
        elif status == ValidationStatus.CONFLICTING:
            return "❌ Manual review required - conflicting sources"
        
        elif status == ValidationStatus.INSUFFICIENT_DATA:
            return "❌ Insufficient data - require additional sources"
        
        else:
            return "❌ Do not use - validation failed"
    
    def _calculate_overall_data_quality(self, results: List[ValidationResult]) -> float:
        """Calculate overall data quality score"""
        if not results:
            return 0.0
        
        total_confidence = sum(r.confidence_score for r in results)
        return total_confidence / len(results)
    
    def _create_validation_summary(self, results: List[ValidationResult]) -> Dict[str, int]:
        """Create validation summary statistics"""
        summary = {
            'validated': 0,
            'partially_validated': 0,
            'conflicting': 0,
            'insufficient_data': 0,
            'invalid': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'very_low_confidence': 0
        }
        
        for result in results:
            # Count by status
            if result.validation_status == ValidationStatus.VALIDATED:
                summary['validated'] += 1
            elif result.validation_status == ValidationStatus.PARTIALLY_VALIDATED:
                summary['partially_validated'] += 1
            elif result.validation_status == ValidationStatus.CONFLICTING:
                summary['conflicting'] += 1
            elif result.validation_status == ValidationStatus.INSUFFICIENT_DATA:
                summary['insufficient_data'] += 1
            elif result.validation_status == ValidationStatus.INVALID:
                summary['invalid'] += 1
            
            # Count by confidence
            if result.confidence_level == ConfidenceLevel.HIGH:
                summary['high_confidence'] += 1
            elif result.confidence_level == ConfidenceLevel.MEDIUM:
                summary['medium_confidence'] += 1
            elif result.confidence_level == ConfidenceLevel.LOW:
                summary['low_confidence'] += 1
            elif result.confidence_level == ConfidenceLevel.VERY_LOW:
                summary['very_low_confidence'] += 1
        
        return summary
    
    def get_validation_statistics(self) -> Dict[str, any]:
        """Get validation statistics"""
        stats = self.validation_stats.copy()
        if stats['total_validations'] > 0:
            total_results = (stats['high_confidence_results'] + 
                           stats['medium_confidence_results'] + 
                           stats['low_confidence_results'])
            
            if total_results > 0:
                stats['high_confidence_rate'] = (stats['high_confidence_results'] / total_results) * 100
                stats['validation_success_rate'] = ((stats['high_confidence_results'] + 
                                                   stats['medium_confidence_results']) / total_results) * 100
            else:
                stats['high_confidence_rate'] = 0.0
                stats['validation_success_rate'] = 0.0
        else:
            stats['high_confidence_rate'] = 0.0
            stats['validation_success_rate'] = 0.0
        
        return stats 