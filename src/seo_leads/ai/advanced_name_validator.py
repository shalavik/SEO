"""
Advanced Name Validator - Phase 4A Component

Basic name validation for real executive discovery.
Filters out service terms and validates name patterns.
"""

import re
import logging
from typing import List, Dict
from dataclasses import dataclass, field


@dataclass
class NameValidationResult:
    """Result of name validation analysis"""
    is_valid: bool = False
    confidence_score: float = 0.0
    validation_factors: Dict[str, float] = field(default_factory=dict)
    rejection_reasons: List[str] = field(default_factory=list)
    name_quality: str = "unknown"
    is_service_term: bool = False


class AdvancedNameValidator:
    """Advanced validation engine for executive names"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
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

    def analyze_name_validity(self, name: str) -> NameValidationResult:
        """Detailed analysis of name validity"""
        result = NameValidationResult()
        
        if self.validate_name_pattern(name):
            result.is_valid = True
            result.confidence_score = 0.8
            result.name_quality = "good"
        else:
            result.is_valid = False
            result.confidence_score = 0.2
            result.name_quality = "poor"
            result.rejection_reasons = ["Invalid name pattern or contains service terms"]
            
        return result

    def get_name_quality_score(self, name: str) -> float:
        """Get quality score for a name"""
        return 0.8 if self.is_real_executive_name(name) else 0.2
