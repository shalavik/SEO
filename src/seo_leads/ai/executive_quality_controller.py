"""
Executive Quality Controller - Phase 1 Critical Fixes Implementation

This module implements the critical improvements identified in the comprehensive validation:
1. False positive reduction through strict confidence thresholding
2. Executive context validation and title verification  
3. Enhanced name variation recognition
4. Domain email cross-referencing for validation

Based on validation results showing 55.6% false positive rate and 20% discovery rate.
Target: Reduce false positives to <15% while maintaining discovery capabilities.

Author: AI Assistant
Date: 2025-01-23
Version: 1.0.0 - Phase 1 Implementation
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from difflib import SequenceMatcher
import email_validator
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@dataclass
class QualityValidationResult:
    """Result of executive quality validation"""
    is_valid: bool
    confidence_score: float
    validation_reasons: List[str] = field(default_factory=list)
    warning_flags: List[str] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)

@dataclass
class ExecutiveCandidate:
    """Enhanced executive candidate with validation metadata"""
    name: str
    title: str
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    
    # Validation metadata
    extraction_context: str = ""
    confidence_score: float = 0.0
    validation_signals: List[str] = field(default_factory=list)
    source_section: str = ""
    
    # Quality assessment
    quality_result: Optional[QualityValidationResult] = None

class ExecutiveNameVariationDatabase:
    """Comprehensive name variation database for improved matching"""
    
    def __init__(self):
        self.name_variations = {
            # Common English name variations  
            "Alexander": ["Alex", "Al", "Lex", "Sandy"],
            "Andrew": ["Andy", "Drew"],
            "Anthony": ["Tony", "Ant"],
            "Benjamin": ["Ben", "Benny", "Benji"],
            "Christopher": ["Chris", "Christie", "Kit"],
            "Daniel": ["Dan", "Danny", "Dani"],
            "David": ["Dave", "Davey", "Davy"],
            "Edward": ["Ed", "Eddie", "Ted", "Teddy"],
            "Frederick": ["Fred", "Freddy", "Freddie"],
            "Gregory": ["Greg", "Gregg"],
            "James": ["Jim", "Jimmy", "Jamie"],
            "Jonathan": ["Jon", "Johnny"],
            "Joseph": ["Joe", "Joey"],
            "Kenneth": ["Ken", "Kenny"],
            "Kevin": ["Kev"],
            "Lawrence": ["Larry", "Lance"],
            "Matthew": ["Matt", "Matty"],
            "Michael": ["Mike", "Mick", "Mickey"],
            "Nicholas": ["Nick", "Nicky"],
            "Patrick": ["Pat", "Paddy"],
            "Peter": ["Pete", "Petey"],
            "Richard": ["Rich", "Rick", "Ricky", "Dick"],
            "Robert": ["Rob", "Bob", "Bobby", "Robbie"],
            "Samuel": ["Sam", "Sammy"],
            "Stephen": ["Steve", "Stevie"],
            "Thomas": ["Tom", "Tommy"],
            "Timothy": ["Tim", "Timmy"],
            "Vincent": ["Vince", "Vinny"],
            "William": ["Will", "Bill", "Billy", "Willie"],
            
            # Female names
            "Catherine": ["Kate", "Katie", "Cathy", "Cat"],
            "Christine": ["Chris", "Christie", "Tina"],
            "Deborah": ["Deb", "Debbie"],
            "Elizabeth": ["Liz", "Beth", "Betty", "Eliza"],
            "Jennifer": ["Jen", "Jenny"],
            "Margaret": ["Maggie", "Peggy", "Margie"],
            "Patricia": ["Pat", "Patty", "Trish"],
            "Rebecca": ["Becky", "Becca"],
            "Sandra": ["Sandy"],
            "Susan": ["Sue", "Suzy", "Susie"],
            
            # Additional variations from validation data
            "Douglas": ["Doug", "Dougie"],
            "Troy": ["Troye"],
            "Peter": ["Pete", "Petey"],
            "John": ["Johnny", "Jon", "Jack"],  # Vernon case
        }
        
        # Create reverse mapping
        self.reverse_variations = {}
        for full_name, variations in self.name_variations.items():
            for variation in variations:
                if variation not in self.reverse_variations:
                    self.reverse_variations[variation] = []
                self.reverse_variations[variation].append(full_name)
            # Add self-reference
            self.reverse_variations[full_name] = [full_name]
    
    def get_variations(self, name: str) -> List[str]:
        """Get all variations of a given name"""
        name_title = name.title()
        variations = set()
        
        # Direct variations
        variations.update(self.name_variations.get(name_title, []))
        
        # Reverse variations  
        variations.update(self.reverse_variations.get(name_title, []))
        
        # Add original name
        variations.add(name_title)
        
        return list(variations)
    
    def are_name_variations(self, name1: str, name2: str, threshold: float = 0.8) -> bool:
        """Check if two names are variations of each other"""
        name1_clean = name1.title().strip()
        name2_clean = name2.title().strip()
        
        if name1_clean == name2_clean:
            return True
        
        # Check variation database
        variations1 = set(self.get_variations(name1_clean))
        variations2 = set(self.get_variations(name2_clean))
        
        if variations1.intersection(variations2):
            return True
        
        # Fuzzy matching fallback
        similarity = SequenceMatcher(None, name1_clean, name2_clean).ratio()
        return similarity >= threshold

class ExecutiveTitleValidator:
    """Validates executive titles for industry appropriateness and authenticity"""
    
    def __init__(self):
        self.valid_executive_titles = {
            'primary_executives': [
                'owner', 'co-owner', 'director', 'managing director', 'ceo', 
                'chief executive', 'chief executive officer', 'founder', 
                'co-founder', 'proprietor', 'principal', 'partner', 'president'
            ],
            'management_titles': [
                'manager', 'general manager', 'operations manager', 
                'business manager', 'office manager', 'admin manager',
                'contracts manager', 'project manager'
            ],
            'technical_titles': [
                'senior plumber', 'master plumber', 'lead plumber',
                'qualified plumber', 'certified plumber', 'licensed plumber',
                'gas safe engineer', 'heating engineer', 'plumbing engineer',
                'boiler engineer', 'bathroom fitter', 'installation engineer'
            ],
            'family_business': [
                'son', 'daughter', 'jr', 'junior', 'sr', 'senior', 'iii', 'iv'
            ]
        }
        
        self.invalid_indicators = [
            'customer', 'client', 'review', 'testimonial', 'rating',
            'employee', 'worker', 'staff member', 'helper', 'assistant',
            'apprentice', 'trainee', 'student', 'intern'
        ]
    
    def validate_title(self, title: str, context: str = "") -> Tuple[bool, float, List[str]]:
        """
        Validate if a title is appropriate for an executive
        
        Returns:
            Tuple of (is_valid, confidence, reasons)
        """
        if not title:
            return False, 0.0, ["No title provided"]
        
        title_lower = title.lower().strip()
        context_lower = context.lower()
        
        reasons = []
        confidence = 0.0
        
        # Check for invalid indicators
        for invalid in self.invalid_indicators:
            if invalid in title_lower or invalid in context_lower:
                return False, 0.0, [f"Contains invalid indicator: {invalid}"]
        
        # Check primary executives (highest confidence)
        for primary_title in self.valid_executive_titles['primary_executives']:
            if primary_title in title_lower:
                confidence = max(confidence, 0.9)
                reasons.append(f"Primary executive title: {primary_title}")
        
        # Check management titles
        for mgmt_title in self.valid_executive_titles['management_titles']:
            if mgmt_title in title_lower:
                confidence = max(confidence, 0.7)
                reasons.append(f"Management title: {mgmt_title}")
        
        # Check technical titles
        for tech_title in self.valid_executive_titles['technical_titles']:
            if tech_title in title_lower:
                confidence = max(confidence, 0.6)
                reasons.append(f"Technical leadership title: {tech_title}")
        
        # Check family business indicators
        for family_title in self.valid_executive_titles['family_business']:
            if family_title in title_lower:
                confidence = max(confidence, 0.5)
                reasons.append(f"Family business indicator: {family_title}")
        
        is_valid = confidence >= 0.5
        
        if not is_valid and confidence == 0.0:
            reasons.append("Title does not match known executive patterns")
        
        return is_valid, confidence, reasons

class ContextualExecutiveValidator:
    """Validates executives based on contextual evidence and cross-references"""
    
    def __init__(self):
        self.name_db = ExecutiveNameVariationDatabase()
        self.title_validator = ExecutiveTitleValidator()
        
        # Positive context indicators
        self.positive_context_patterns = [
            r'\b(owner|director|manager|founder|ceo)\b',
            r'\b(established|founded|started)\s+by\b',
            r'\b(contact|speak\s+to|ask\s+for|reach)\s+\w+\b',
            r'\b(years?\s+of\s+experience|qualified|certified|licensed)\b',
            r'\b(family\s+business|generations?|since\s+\d{4})\b'
        ]
        
        # Negative context indicators  
        self.negative_context_patterns = [
            r'\b(customer|client|review|testimonial)\b',
            r'\b(said|states|commented|mentioned)\b',
            r'\b(★|stars?|rating|satisfied)\b',
            r'\b(quote|quotation|estimate)\b'
        ]
    
    def validate_executive_context(self, candidate: ExecutiveCandidate, 
                                 domain: str = "") -> QualityValidationResult:
        """
        Comprehensive validation of executive candidate
        
        Args:
            candidate: Executive candidate to validate
            domain: Company domain for email validation
            
        Returns:
            QualityValidationResult with validation outcome
        """
        validation_reasons = []
        warning_flags = []
        rejection_reasons = []
        confidence_adjustments = []
        
        base_confidence = candidate.confidence_score
        
        # 1. Name validation
        name_valid, name_confidence, name_reasons = self._validate_name(candidate.name)
        validation_reasons.extend(name_reasons)
        if not name_valid:
            rejection_reasons.append("Invalid name format")
        confidence_adjustments.append(('name', name_confidence))
        
        # 2. Title validation
        title_valid, title_confidence, title_reasons = self.title_validator.validate_title(
            candidate.title, candidate.extraction_context
        )
        validation_reasons.extend(title_reasons)
        if not title_valid:
            rejection_reasons.append("Invalid or inappropriate title")
        confidence_adjustments.append(('title', title_confidence))
        
        # 3. Context validation
        context_score, context_reasons = self._validate_extraction_context(candidate.extraction_context)
        validation_reasons.extend(context_reasons)
        confidence_adjustments.append(('context', context_score))
        
        # 4. Email validation (if provided)
        if candidate.email:
            email_valid, email_reasons = self._validate_email_context(candidate.email, domain)
            validation_reasons.extend(email_reasons)
            if not email_valid:
                warning_flags.append("Email domain mismatch or invalid format")
        
        # 5. Cross-reference validation
        cross_ref_score, cross_ref_reasons = self._cross_reference_validation(candidate)
        validation_reasons.extend(cross_ref_reasons)
        confidence_adjustments.append(('cross_reference', cross_ref_score))
        
        # Calculate final confidence score
        final_confidence = self._calculate_weighted_confidence(
            base_confidence, confidence_adjustments
        )
        
        # Apply quality thresholds (Phase 1 critical fix)
        is_valid = self._apply_quality_thresholds(
            final_confidence, candidate, rejection_reasons
        )
        
        return QualityValidationResult(
            is_valid=is_valid,
            confidence_score=final_confidence,
            validation_reasons=validation_reasons,
            warning_flags=warning_flags,
            rejection_reasons=rejection_reasons
        )
    
    def _validate_name(self, name: str) -> Tuple[bool, float, List[str]]:
        """Validate name format and authenticity"""
        if not name or len(name.strip()) < 3:
            return False, 0.0, ["Name too short or empty"]
        
        reasons = []
        confidence = 0.0
        
        # Basic format validation
        name_parts = name.strip().split()
        if len(name_parts) < 2:
            return False, 0.0, ["Name must have at least first and last name"]
        
        if len(name_parts) > 4:
            return False, 0.0, ["Name has too many parts (likely not a person)"]
        
        # Check for business name patterns
        business_indicators = ['ltd', 'limited', 'inc', 'incorporated', 'llc', 'plc', 
                             'company', 'services', 'solutions', 'group', 'enterprises']
        
        name_lower = name.lower()
        for indicator in business_indicators:
            if indicator in name_lower:
                return False, 0.0, [f"Contains business indicator: {indicator}"]
        
        # Validate individual name parts
        for part in name_parts:
            if not re.match(r'^[A-Za-z][A-Za-z\'-]*$', part):
                return False, 0.0, [f"Invalid name part format: {part}"]
        
        # Check name authenticity (basic patterns)
        first_name = name_parts[0]
        last_name = name_parts[-1]
        
        # Reasonable name length
        if len(first_name) < 2 or len(last_name) < 2:
            return False, 0.0, ["Name parts too short"]
        
        if len(first_name) > 20 or len(last_name) > 20:
            warning_flag = True
            confidence = 0.6
            reasons.append("Unusually long name parts")
        else:
            confidence = 0.8
            reasons.append("Valid name format")
        
        return True, confidence, reasons
    
    def _validate_extraction_context(self, context: str) -> Tuple[float, List[str]]:
        """Validate the context in which the executive was found"""
        if not context:
            return 0.3, ["No extraction context provided"]
        
        context_lower = context.lower()
        reasons = []
        score = 0.5  # Base score
        
        # Check for positive context indicators
        positive_matches = 0
        for pattern in self.positive_context_patterns:
            if re.search(pattern, context_lower):
                positive_matches += 1
                score += 0.1
                reasons.append(f"Positive context indicator found")
        
        # Check for negative context indicators
        negative_matches = 0
        for pattern in self.negative_context_patterns:
            if re.search(pattern, context_lower):
                negative_matches += 1
                score -= 0.2
                reasons.append(f"Negative context indicator found")
        
        # Ensure score stays within bounds
        score = max(0.0, min(1.0, score))
        
        if positive_matches > negative_matches:
            reasons.append("Context supports executive identification")
        elif negative_matches > positive_matches:
            reasons.append("Context suggests non-executive reference")
        else:
            reasons.append("Neutral context")
        
        return score, reasons
    
    def _validate_email_context(self, email: str, domain: str) -> Tuple[bool, List[str]]:
        """Validate email in context of company domain"""
        reasons = []
        
        try:
            # Basic email format validation
            email_validator.validate_email(email)
            reasons.append("Valid email format")
        except:
            return False, ["Invalid email format"]
        
        if not domain:
            return True, reasons + ["No domain provided for validation"]
        
        # Extract email domain
        email_domain = email.split('@')[-1].lower()
        domain_clean = domain.replace('www.', '').replace('http://', '').replace('https://', '').lower()
        
        # Check domain alignment
        if email_domain == domain_clean:
            reasons.append("Email domain matches company domain")
            return True, reasons
        elif email_domain in domain_clean or domain_clean in email_domain:
            reasons.append("Email domain closely matches company domain")
            return True, reasons
        else:
            reasons.append(f"Email domain ({email_domain}) doesn't match company domain ({domain_clean})")
            return False, reasons
    
    def _cross_reference_validation(self, candidate: ExecutiveCandidate) -> Tuple[float, List[str]]:
        """Cross-reference validation using multiple data points"""
        reasons = []
        score = 0.5
        
        # Check for consistency between name and email
        if candidate.email:
            email_local = candidate.email.split('@')[0].lower()
            name_parts = [part.lower() for part in candidate.name.split()]
            
            name_in_email = any(part in email_local for part in name_parts if len(part) > 2)
            if name_in_email:
                score += 0.2
                reasons.append("Name consistent with email address")
            else:
                score -= 0.1
                reasons.append("Name not reflected in email address")
        
        # Check for title-name consistency
        if candidate.title and any(word in candidate.title.lower() for word in candidate.name.lower().split()):
            score += 0.1
            reasons.append("Name appears in title context")
        
        # Validate against known patterns
        if len(candidate.validation_signals) > 0:
            score += min(0.2, len(candidate.validation_signals) * 0.05)
            reasons.append(f"Has {len(candidate.validation_signals)} validation signals")
        
        return max(0.0, min(1.0, score)), reasons
    
    def _calculate_weighted_confidence(self, base_confidence: float, 
                                     adjustments: List[Tuple[str, float]]) -> float:
        """Calculate weighted confidence score from multiple validation factors"""
        weights = {
            'name': 0.25,
            'title': 0.30,
            'context': 0.25,
            'cross_reference': 0.20
        }
        
        weighted_score = base_confidence * 0.3  # Base weight
        
        for factor, score in adjustments:
            if factor in weights:
                weighted_score += score * weights[factor]
        
        return max(0.0, min(1.0, weighted_score))
    
    def _apply_quality_thresholds(self, confidence: float, candidate: ExecutiveCandidate, 
                                rejection_reasons: List[str]) -> bool:
        """Apply Phase 1 quality thresholds to reduce false positives"""
        
        # Critical threshold: reject low confidence candidates
        if confidence < 0.4:
            rejection_reasons.append(f"Confidence {confidence:.3f} below minimum threshold 0.4")
            return False
        
        # Reject if no meaningful title
        if not candidate.title or len(candidate.title.strip()) < 3:
            rejection_reasons.append("No meaningful title provided")
            return False
        
        # Reject obvious non-executives
        negative_patterns = ['customer', 'client', 'review', 'testimonial']
        context_lower = candidate.extraction_context.lower()
        for pattern in negative_patterns:
            if pattern in context_lower:
                rejection_reasons.append(f"Context contains negative pattern: {pattern}")
                return False
        
        return True

class ExecutiveQualityController:
    """Main controller for executive quality management - Phase 1 Implementation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validator = ContextualExecutiveValidator()
        
        # Phase 1 quality settings
        self.quality_settings = {
            'minimum_confidence': 0.4,  # Reduced from potential 0.6 to balance discovery
            'enable_strict_validation': True,
            'max_executives_per_company': 5,  # Prevent flooding
            'require_title_validation': True,
            'enable_domain_validation': True
        }
        
        # Performance tracking
        self.metrics = {
            'candidates_processed': 0,
            'candidates_accepted': 0,
            'candidates_rejected': 0,
            'rejection_reasons': {},
            'average_confidence': 0.0
        }
    
    def validate_executive_candidates(self, candidates: List[ExecutiveCandidate], 
                                    company_domain: str = "") -> List[ExecutiveCandidate]:
        """
        Apply Phase 1 quality control to executive candidates
        
        Args:
            candidates: List of executive candidates to validate
            company_domain: Company domain for email validation
            
        Returns:
            List of validated, high-quality executive candidates
        """
        self.logger.info(f"Validating {len(candidates)} executive candidates")
        
        validated_candidates = []
        confidence_scores = []
        
        for candidate in candidates:
            self.metrics['candidates_processed'] += 1
            
            # Apply comprehensive validation
            quality_result = self.validator.validate_executive_context(candidate, company_domain)
            candidate.quality_result = quality_result
            
            confidence_scores.append(quality_result.confidence_score)
            
            if quality_result.is_valid:
                validated_candidates.append(candidate)
                self.metrics['candidates_accepted'] += 1
                self.logger.debug(f"✅ Accepted: {candidate.name} ({candidate.title}) - "
                                f"Confidence: {quality_result.confidence_score:.3f}")
            else:
                self.metrics['candidates_rejected'] += 1
                self.logger.debug(f"❌ Rejected: {candidate.name} ({candidate.title}) - "
                                f"Reasons: {'; '.join(quality_result.rejection_reasons)}")
                
                # Track rejection reasons
                for reason in quality_result.rejection_reasons:
                    self.metrics['rejection_reasons'][reason] = (
                        self.metrics['rejection_reasons'].get(reason, 0) + 1
                    )
        
        # Update average confidence
        if confidence_scores:
            self.metrics['average_confidence'] = sum(confidence_scores) / len(confidence_scores)
        
        # Apply company-level limits
        if len(validated_candidates) > self.quality_settings['max_executives_per_company']:
            # Sort by confidence and take top candidates
            validated_candidates.sort(key=lambda x: x.quality_result.confidence_score, reverse=True)
            validated_candidates = validated_candidates[:self.quality_settings['max_executives_per_company']]
            self.logger.info(f"Limited to top {self.quality_settings['max_executives_per_company']} candidates")
        
        acceptance_rate = (len(validated_candidates) / len(candidates)) * 100 if candidates else 0
        self.logger.info(f"Validation complete: {len(validated_candidates)}/{len(candidates)} "
                        f"candidates accepted ({acceptance_rate:.1f}%)")
        
        return validated_candidates
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get current quality control metrics"""
        acceptance_rate = 0.0
        if self.metrics['candidates_processed'] > 0:
            acceptance_rate = (self.metrics['candidates_accepted'] / 
                             self.metrics['candidates_processed']) * 100
        
        return {
            'candidates_processed': self.metrics['candidates_processed'],
            'candidates_accepted': self.metrics['candidates_accepted'],
            'candidates_rejected': self.metrics['candidates_rejected'],
            'acceptance_rate_percent': acceptance_rate,
            'average_confidence': self.metrics['average_confidence'],
            'top_rejection_reasons': dict(sorted(
                self.metrics['rejection_reasons'].items(), 
                key=lambda x: x[1], reverse=True
            )[:5]),
            'quality_settings': self.quality_settings
        }
    
    def reset_metrics(self):
        """Reset quality control metrics"""
        self.metrics = {
            'candidates_processed': 0,
            'candidates_accepted': 0,
            'candidates_rejected': 0,
            'rejection_reasons': {},
            'average_confidence': 0.0
        } 