"""
Enhanced Advanced Name Validator - Phase 5B Enhancement
Validates executive names and filters HTML artifacts with UK census data patterns.
"""

import re
import logging
from typing import Set, Dict, List, Tuple, Optional
from dataclasses import dataclass
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class NameValidationResult:
    """Result of name validation process"""
    name: str
    is_valid: bool
    confidence: float
    validation_reasons: List[str]
    name_type: str  # 'executive', 'location', 'service', 'html_artifact'

class AdvancedNameValidator:
    """
    Enhanced name validator that distinguishes real human names from locations,
    services, and HTML artifacts using UK census data patterns.
    
    Phase 5B Enhancements:
    - HTML artifact filtering
    - Technical term exclusion
    - Improved UK name pattern recognition
    - Context-based validation
    """
    
    def __init__(self):
        """Initialize validator with UK name patterns and exclusion lists"""
        
        # Common UK first names (top 100 for efficiency)
        self.uk_first_names = {
            'james', 'john', 'robert', 'michael', 'william', 'david', 'richard', 'charles',
            'joseph', 'thomas', 'christopher', 'daniel', 'paul', 'mark', 'donald', 'george',
            'kenneth', 'steven', 'edward', 'brian', 'ronald', 'anthony', 'kevin', 'jason',
            'matthew', 'gary', 'timothy', 'jose', 'larry', 'jeffrey', 'frank', 'scott',
            'eric', 'stephen', 'andrew', 'raymond', 'gregory', 'joshua', 'jerry', 'dennis',
            'walter', 'patrick', 'peter', 'harold', 'douglas', 'henry', 'carl', 'arthur',
            'ryan', 'roger', 'joe', 'juan', 'jack', 'albert', 'jonathan', 'justin',
            'terry', 'austin', 'bobby', 'eugene', 'louis', 'wayne', 'ralph', 'mason',
            'roy', 'benjamin', 'adam', 'harry', 'fred', 'gerald', 'sean', 'harold',
            'mary', 'patricia', 'jennifer', 'linda', 'elizabeth', 'barbara', 'susan',
            'jessica', 'sarah', 'karen', 'nancy', 'lisa', 'betty', 'dorothy', 'sandra',
            'ashley', 'kimberly', 'emily', 'donna', 'margaret', 'carol', 'michelle',
            'laura', 'sarah', 'kimberly', 'deborah', 'dorothy', 'lisa', 'nancy', 'karen',
            'helen', 'sandra', 'donna', 'carol', 'ruth', 'sharon', 'michelle', 'laura',
            'emily', 'kimberly', 'deborah', 'dorothy', 'amy', 'angela', 'ashley', 'brenda'
        }
        
        # Common UK surnames (top 100)
        self.uk_surnames = {
            'smith', 'jones', 'taylor', 'williams', 'brown', 'davies', 'evans', 'wilson',
            'thomas', 'roberts', 'johnson', 'lewis', 'walker', 'robinson', 'wood', 'thompson',
            'white', 'watson', 'jackson', 'wright', 'green', 'harris', 'cooper', 'king',
            'lee', 'martin', 'clarke', 'james', 'morgan', 'hughes', 'edwards', 'hill',
            'moore', 'clark', 'harrison', 'scott', 'young', 'morris', 'hall', 'ward',
            'turner', 'carter', 'phillips', 'mitchell', 'patel', 'adams', 'campbell',
            'anderson', 'allen', 'cook', 'bailey', 'parker', 'miller', 'davis', 'murphy',
            'price', 'bell', 'baker', 'griffiths', 'kelly', 'simpson', 'marshall', 'collins',
            'bennett', 'cox', 'richardson', 'fox', 'gray', 'rose', 'chapman', 'hunt',
            'robertson', 'shaw', 'reynolds', 'lloyd', 'ellis', 'richards', 'russell',
            'wilkinson', 'khan', 'graham', 'stewart', 'reid', 'murray', 'powell', 'palmer',
            'holmes', 'rogers', 'stevens', 'walsh', 'hunter', 'thomson', 'matthews', 'ross'
        }
        
        # HTML artifacts and technical terms to exclude
        self.html_artifacts = {
            'html_tags': {
                'doctype', 'html', 'head', 'body', 'meta', 'link', 'script', 'style',
                'div', 'span', 'nav', 'header', 'footer', 'section', 'article', 'aside',
                'main', 'figure', 'img', 'video', 'audio', 'canvas', 'iframe', 'embed'
            },
            'attributes': {
                'charset', 'viewport', 'content', 'property', 'equiv', 'lang', 'dir',
                'class', 'id', 'style', 'src', 'href', 'alt', 'title', 'role', 'aria'
            },
            'technical_terms': {
                'javascript', 'css', 'html', 'php', 'mysql', 'apache', 'nginx', 'jquery',
                'bootstrap', 'wordpress', 'wix', 'squarespace', 'shopify', 'magento',
                'drupal', 'joomla', 'analytics', 'gtm', 'facebook', 'twitter', 'linkedin',
                'instagram', 'youtube', 'google', 'microsoft', 'apple', 'android', 'ios'
            },
            'css_classes': {
                'container', 'wrapper', 'content', 'sidebar', 'widget', 'menu', 'nav',
                'button', 'btn', 'form', 'input', 'text', 'image', 'gallery', 'slider',
                'carousel', 'modal', 'popup', 'tooltip', 'dropdown', 'accordion', 'tab'
            }
        }
        
        # Location indicators (UK cities, regions)
        self.uk_locations = {
            'london', 'manchester', 'birmingham', 'leeds', 'liverpool', 'sheffield',
            'bristol', 'glasgow', 'edinburgh', 'cardiff', 'belfast', 'newcastle',
            'nottingham', 'leicester', 'coventry', 'bradford', 'stoke', 'wolverhampton',
            'plymouth', 'derby', 'southampton', 'swansea', 'dundee', 'aberdeen',
            'england', 'scotland', 'wales', 'ireland', 'yorkshire', 'lancashire',
            'midlands', 'essex', 'kent', 'surrey', 'hampshire', 'hertfordshire'
        }
        
        # Service/business terms
        self.service_terms = {
            'plumbing', 'heating', 'electrical', 'services', 'ltd', 'limited', 'company',
            'solutions', 'systems', 'installation', 'repair', 'maintenance', 'emergency',
            'commercial', 'residential', 'domestic', 'industrial', 'professional',
            'qualified', 'certified', 'approved', 'registered', 'experienced', 'reliable'
        }

    def validate_executive_name(self, name: str, context: str = "") -> NameValidationResult:
        """
        Enhanced validation of executive names with context awareness.
        
        Args:
            name: Candidate executive name
            context: Surrounding text context for validation
            
        Returns:
            NameValidationResult with validation details
        """
        name = name.strip()
        validation_reasons = []
        confidence = 0.0
        
        # Basic format validation
        if not self._basic_format_check(name):
            return NameValidationResult(
                name=name,
                is_valid=False,
                confidence=0.0,
                validation_reasons=["Failed basic format check"],
                name_type="invalid"
            )
        
        # Check for HTML artifacts
        if self._is_html_artifact(name):
            return NameValidationResult(
                name=name,
                is_valid=False,
                confidence=0.0,
                validation_reasons=["Identified as HTML artifact"],
                name_type="html_artifact"
            )
        
        # Check for location names
        if self._is_location_name(name):
            return NameValidationResult(
                name=name,
                is_valid=False,
                confidence=0.2,
                validation_reasons=["Identified as location name"],
                name_type="location"
            )
        
        # Check for service terms
        if self._is_service_term(name):
            return NameValidationResult(
                name=name,
                is_valid=False,
                confidence=0.1,
                validation_reasons=["Identified as service term"],
                name_type="service"
            )
        
        # Validate as human name
        name_validation = self._validate_human_name(name)
        confidence += name_validation['confidence']
        validation_reasons.extend(name_validation['reasons'])
        
        # Context validation
        if context:
            context_validation = self._validate_context(name, context)
            confidence += context_validation['confidence']
            validation_reasons.extend(context_validation['reasons'])
        
        # Final confidence calculation
        final_confidence = min(confidence, 1.0)
        is_valid = final_confidence >= 0.6
        
        return NameValidationResult(
            name=name,
            is_valid=is_valid,
            confidence=final_confidence,
            validation_reasons=validation_reasons,
            name_type="executive" if is_valid else "uncertain"
        )

    def filter_html_artifacts(self, names: List[str]) -> List[str]:
        """
        Filter out HTML artifacts from a list of name candidates.
        
        Args:
            names: List of potential names
            
        Returns:
            Filtered list with HTML artifacts removed
        """
        filtered_names = []
        
        for name in names:
            if not self._is_html_artifact(name):
                filtered_names.append(name)
            else:
                logger.debug(f"Filtered HTML artifact: {name}")
        
        return filtered_names

    def batch_validate_names(self, names: List[str], context: str = "") -> List[NameValidationResult]:
        """
        Validate multiple names in batch for efficiency.
        
        Args:
            names: List of candidate names
            context: Shared context for validation
            
        Returns:
            List of validation results
        """
        results = []
        
        for name in names:
            result = self.validate_executive_name(name, context)
            results.append(result)
        
        # Sort by confidence score
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        return results

    def _basic_format_check(self, name: str) -> bool:
        """Basic format validation for names"""
        # Length check
        if len(name) < 3 or len(name) > 50:
            return False
        
        # Must contain letters
        if not re.search(r'[a-zA-Z]', name):
            return False
        
        # Should not be all numbers
        if name.isdigit():
            return False
        
        # Should not contain excessive special characters
        if len(re.findall(r'[^a-zA-Z\s\'-]', name)) > 2:
            return False
        
        return True

    def _is_html_artifact(self, name: str) -> bool:
        """Check if name is an HTML artifact"""
        name_lower = name.lower().strip()
        
        # Check HTML tags
        for tag in self.html_artifacts['html_tags']:
            if tag in name_lower:
                return True
        
        # Check HTML attributes
        for attr in self.html_artifacts['attributes']:
            if attr in name_lower:
                return True
        
        # Check technical terms
        for term in self.html_artifacts['technical_terms']:
            if term in name_lower:
                return True
        
        # Check CSS classes
        for css_class in self.html_artifacts['css_classes']:
            if css_class in name_lower:
                return True
        
        # Check for HTML-like patterns
        if re.search(r'[<>{}[\]()="\'/\\]', name):
            return True
        
        # Check for multiple consecutive uppercase letters (often HTML)
        if re.search(r'[A-Z]{3,}', name):
            return True
        
        return False

    def _is_location_name(self, name: str) -> bool:
        """Check if name is a UK location"""
        name_lower = name.lower().strip()
        
        # Direct location match
        for location in self.uk_locations:
            if location in name_lower:
                return True
        
        # Common location patterns
        location_patterns = [
            r'\b\w+shire\b', r'\b\w+ford\b', r'\b\w+ton\b', r'\b\w+ham\b',
            r'\b\w+bury\b', r'\b\w+chester\b', r'\b\w+mouth\b'
        ]
        
        for pattern in location_patterns:
            if re.search(pattern, name_lower):
                return True
        
        return False

    def _is_service_term(self, name: str) -> bool:
        """Check if name is a service/business term"""
        name_lower = name.lower().strip()
        
        for service_term in self.service_terms:
            if service_term in name_lower:
                return True
        
        return False

    def _validate_human_name(self, name: str) -> Dict[str, any]:
        """Validate if name matches human name patterns"""
        confidence = 0.0
        reasons = []
        
        # Split into parts
        name_parts = name.split()
        
        if len(name_parts) == 2:
            first_name, last_name = name_parts
            confidence += 0.3
            reasons.append("Has first and last name format")
            
            # Check against UK name databases
            if first_name.lower() in self.uk_first_names:
                confidence += 0.3
                reasons.append("First name matches UK census data")
            
            if last_name.lower() in self.uk_surnames:
                confidence += 0.3
                reasons.append("Surname matches UK census data")
            
            # Name pattern validation
            if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+$', name):
                confidence += 0.1
                reasons.append("Matches proper name capitalization")
        
        elif len(name_parts) == 3:
            # First Middle Last or First Last Suffix
            confidence += 0.2
            reasons.append("Has three-part name format")
            
            if name_parts[0].lower() in self.uk_first_names:
                confidence += 0.2
                reasons.append("First name matches UK data")
            
            if name_parts[-1].lower() in self.uk_surnames:
                confidence += 0.2
                reasons.append("Last name matches UK data")
        
        return {
            'confidence': confidence,
            'reasons': reasons
        }

    def _validate_context(self, name: str, context: str) -> Dict[str, any]:
        """Validate name based on surrounding context"""
        confidence = 0.0
        reasons = []
        context_lower = context.lower()
        
        # Executive title indicators
        executive_titles = [
            'ceo', 'managing director', 'director', 'manager', 'founder', 'owner',
            'chairman', 'md', 'head of', 'chief', 'senior', 'lead', 'principal'
        ]
        
        for title in executive_titles:
            if title in context_lower:
                confidence += 0.2
                reasons.append(f"Context contains executive title: {title}")
                break
        
        # Contact information proximity
        contact_indicators = ['email', 'phone', 'tel', 'mobile', '@', '.com', '.co.uk']
        for indicator in contact_indicators:
            if indicator in context_lower:
                confidence += 0.1
                reasons.append("Near contact information")
                break
        
        # Team/about section indicators
        team_indicators = ['team', 'about', 'staff', 'management', 'leadership']
        for indicator in team_indicators:
            if indicator in context_lower:
                confidence += 0.1
                reasons.append(f"In {indicator} section")
                break
        
        return {
            'confidence': min(confidence, 0.4),  # Cap context contribution
            'reasons': reasons
        }

    def get_validation_summary(self, results: List[NameValidationResult]) -> Dict[str, any]:
        """Generate summary statistics for validation results"""
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        
        name_types = {}
        for result in results:
            name_types[result.name_type] = name_types.get(result.name_type, 0) + 1
        
        avg_confidence = sum(r.confidence for r in results) / total if total > 0 else 0
        
        return {
            'total_names': total,
            'valid_names': valid,
            'validation_rate': (valid / total * 100) if total > 0 else 0,
            'average_confidence': avg_confidence,
            'name_type_distribution': name_types,
            'html_artifacts_filtered': name_types.get('html_artifact', 0)
        } 