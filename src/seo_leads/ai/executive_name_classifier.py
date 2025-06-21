"""
AI-Powered Executive Name Classifier

Advanced NLP-based system for distinguishing between real person names and business names.
Critical component for transforming the 0% executive discovery success rate.

Features:
- Person vs Business Name Classification
- Executive Role Identification
- Seniority Tier Assignment
- Industry Context Analysis
- Confidence Score Calculation
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SeniorityTier(Enum):
    """Executive seniority tiers"""
    TIER_1 = "tier_1"  # CEO, Founder, Owner, Managing Director
    TIER_2 = "tier_2"  # Director, Manager, Head of Department
    TIER_3 = "tier_3"  # Supervisor, Coordinator, Specialist

@dataclass
class NameClassificationResult:
    """Result of name classification"""
    is_person: bool
    is_executive: bool
    confidence: float
    classification_reasons: List[str]
    suggested_corrections: Optional[str] = None

@dataclass
class ExecutiveClassificationResult:
    """Result of executive classification"""
    is_executive: bool
    seniority_tier: SeniorityTier
    confidence: float
    title_analysis: Dict[str, float]
    industry_relevance: float

class PersonNameClassifier:
    """
    Classifies whether a name represents a real person or a business entity.
    """
    
    def __init__(self):
        # Common UK first names for validation
        self.common_uk_first_names = {
            # Male names
            'jack', 'oliver', 'harry', 'george', 'noah', 'charlie', 'jacob', 'william', 'thomas', 'oscar',
            'james', 'henry', 'leo', 'alfie', 'joshua', 'freddie', 'archie', 'ethan', 'isaac', 'alexander',
            'mason', 'lucas', 'edward', 'harrison', 'jake', 'dylan', 'max', 'evan', 'samuel', 'arthur',
            'john', 'michael', 'david', 'robert', 'paul', 'mark', 'andrew', 'kenneth', 'steven', 'matthew',
            'daniel', 'christopher', 'anthony', 'donald', 'richard', 'charles', 'joseph', 'peter', 'ryan',
            'simon', 'martin', 'kevin', 'gary', 'alan', 'stuart', 'colin', 'graham', 'neil', 'ian',
            # Female names  
            'olivia', 'amelia', 'isla', 'ava', 'mia', 'isabella', 'sophia', 'grace', 'lily', 'freya',
            'emily', 'ivy', 'ella', 'rosie', 'evie', 'florence', 'poppy', 'charlotte', 'daisy', 'phoebe',
            'sarah', 'emma', 'laura', 'jessica', 'helen', 'michelle', 'lisa', 'jennifer', 'karen', 'susan',
            'claire', 'nicola', 'amanda', 'julie', 'samantha', 'rebecca', 'tracy', 'kelly', 'louise', 'donna'
        }
        
        # Business name indicators (strong signals it's NOT a person)
        self.business_indicators = {
            'ltd', 'limited', 'plc', 'company', 'co', 'corp', 'corporation', 'inc', 'incorporated',
            'services', 'solutions', 'systems', 'group', 'holdings', 'enterprises', 'associates',
            'partners', 'partnership', 'contractors', 'construction', 'building', 'developments',
            'plumbing', 'heating', 'electrical', 'engineering', 'maintenance', 'repairs', 'installations',
            'property', 'properties', 'management', 'consultancy', 'consulting', 'trading', 'supplies'
        }
        
        # Person name patterns
        self.person_name_patterns = [
            r'^[A-Z][a-z]{1,15}\s+[A-Z][a-z]{1,15}$',  # John Smith
            r'^[A-Z][a-z]{1,15}\s+[A-Z]\.\s+[A-Z][a-z]{1,15}$',  # John A. Smith
            r'^[A-Z]\.\s+[A-Z][a-z]{1,15}$',  # J. Smith
            r'^[A-Z][a-z]{1,15}\s+[A-Z][a-z]{1,15}\s+[A-Z][a-z]{1,15}$',  # John Michael Smith
            r'^[A-Z][a-z]{1,15}\s+Mc[A-Z][a-z]{1,15}$',  # John McDonald
            r'^[A-Z][a-z]{1,15}\s+O\'[A-Z][a-z]{1,15}$',  # John O'Connor
        ]
    
    async def classify_person_name(self, name: str, context: str = "") -> NameClassificationResult:
        """
        Classify whether a name represents a real person.
        
        Args:
            name: The name to classify
            context: Additional context (title, company info, etc.)
            
        Returns:
            NameClassificationResult with classification and confidence
        """
        if not name or len(name.strip()) < 2:
            return NameClassificationResult(
                is_person=False,
                is_executive=False,
                confidence=0.0,
                classification_reasons=["Name too short or empty"]
            )
        
        name = name.strip()
        reasons = []
        confidence_factors = []
        
        # Check for business indicators (strong negative signal)
        business_score = self._check_business_indicators(name)
        if business_score > 0.7:
            return NameClassificationResult(
                is_person=False,
                is_executive=False,
                confidence=business_score,
                classification_reasons=[f"Contains business indicators: {name}"]
            )
        
        # Check person name patterns
        pattern_score = self._check_person_patterns(name)
        confidence_factors.append(("pattern_match", pattern_score))
        if pattern_score > 0.8:
            reasons.append("Matches person name patterns")
        
        # Check first name recognition
        first_name_score = self._check_first_name(name)
        confidence_factors.append(("first_name", first_name_score))
        if first_name_score > 0.8:
            reasons.append("Recognized first name")
        
        # Check name structure
        structure_score = self._check_name_structure(name)
        confidence_factors.append(("structure", structure_score))
        if structure_score > 0.7:
            reasons.append("Valid name structure")
        
        # Context analysis
        context_score = self._analyze_context(name, context)
        confidence_factors.append(("context", context_score))
        if context_score > 0.6:
            reasons.append("Context supports person name")
        
        # Calculate overall confidence
        weights = {"pattern_match": 0.3, "first_name": 0.3, "structure": 0.2, "context": 0.2}
        overall_confidence = sum(score * weights.get(factor, 0.25) 
                               for factor, score in confidence_factors)
        
        # Apply business indicator penalty
        overall_confidence *= (1.0 - business_score * 0.5)
        
        is_person = overall_confidence >= 0.6
        
        # Check if it's an executive-level person
        is_executive = is_person and self._is_executive_context(context)
        
        return NameClassificationResult(
            is_person=is_person,
            is_executive=is_executive,
            confidence=min(1.0, overall_confidence),
            classification_reasons=reasons,
            suggested_corrections=self._suggest_corrections(name) if not is_person else None
        )
    
    def _check_business_indicators(self, name: str) -> float:
        """Check for business name indicators"""
        name_lower = name.lower()
        
        # Direct business indicators
        direct_matches = sum(1 for indicator in self.business_indicators 
                           if indicator in name_lower)
        
        if direct_matches > 0:
            return min(1.0, direct_matches * 0.4)
        
        # Pattern-based business indicators
        business_patterns = [
            r'\b(the\s+)?\w+\s+(plumbing|heating|electrical|construction|building)\b',
            r'\b\w+\s+(services|solutions|systems|group)\b',
            r'\b\w+\s+(ltd|limited|plc|co|corp|inc)\b',
        ]
        
        pattern_matches = sum(1 for pattern in business_patterns 
                            if re.search(pattern, name_lower))
        
        return min(1.0, pattern_matches * 0.3)
    
    def _check_person_patterns(self, name: str) -> float:
        """Check if name matches person name patterns"""
        pattern_matches = sum(1 for pattern in self.person_name_patterns 
                            if re.match(pattern, name))
        
        return min(1.0, pattern_matches * 0.5)
    
    def _check_first_name(self, name: str) -> float:
        """Check if first part of name is a recognized first name"""
        parts = name.split()
        if not parts:
            return 0.0
        
        first_part = parts[0].lower()
        
        # Exact match
        if first_part in self.common_uk_first_names:
            return 1.0
        
        # Partial match (nickname patterns)
        for known_name in self.common_uk_first_names:
            if (len(first_part) >= 3 and 
                (first_part.startswith(known_name[:3]) or known_name.startswith(first_part[:3]))):
                return 0.7
        
        # Check if it looks like a first name (capitalized, reasonable length)
        if (len(first_part) >= 2 and first_part[0].isupper() and 
            first_part[1:].islower() and len(first_part) <= 12):
            return 0.5
        
        return 0.0
    
    def _check_name_structure(self, name: str) -> float:
        """Check overall name structure"""
        parts = name.split()
        
        if len(parts) < 2:
            return 0.3  # Single names are less likely to be full person names
        
        if len(parts) > 4:
            return 0.2  # Very long names are often business names
        
        # Check each part
        valid_parts = 0
        for part in parts:
            if (len(part) >= 2 and part[0].isupper() and 
                (part[1:].islower() or part.endswith('.')) and 
                len(part) <= 15):
                valid_parts += 1
        
        return valid_parts / len(parts)
    
    def _analyze_context(self, name: str, context: str) -> float:
        """Analyze context to determine if name is likely a person"""
        if not context:
            return 0.5  # Neutral if no context
        
        context_lower = context.lower()
        
        # Positive indicators
        person_indicators = [
            'director', 'manager', 'ceo', 'founder', 'owner', 'head of',
            'mr', 'mrs', 'ms', 'dr', 'prof', 'sir', 'dame'
        ]
        
        person_score = sum(0.2 for indicator in person_indicators 
                         if indicator in context_lower)
        
        # Negative indicators
        business_indicators = [
            'company', 'ltd', 'limited', 'services', 'solutions',
            'plumbing', 'heating', 'construction'
        ]
        
        business_penalty = sum(0.3 for indicator in business_indicators 
                             if indicator in context_lower)
        
        return max(0.0, min(1.0, 0.5 + person_score - business_penalty))
    
    def _is_executive_context(self, context: str) -> bool:
        """Check if context suggests executive-level role"""
        if not context:
            return False
        
        context_lower = context.lower()
        executive_indicators = [
            'ceo', 'chief executive', 'founder', 'owner', 'managing director',
            'director', 'manager', 'head of', 'senior', 'principal', 'partner'
        ]
        
        return any(indicator in context_lower for indicator in executive_indicators)
    
    def _suggest_corrections(self, name: str) -> Optional[str]:
        """Suggest corrections for names that don't look like person names"""
        # If it looks like a business name with a person's name embedded
        parts = name.split()
        
        # Look for person name patterns within business names
        for i in range(len(parts) - 1):
            potential_name = f"{parts[i]} {parts[i+1]}"
            if self._check_person_patterns(potential_name) > 0.7:
                return potential_name
        
        return None


class ExecutiveTitleClassifier:
    """
    Classifies executive titles and determines seniority levels.
    """
    
    def __init__(self):
        # Executive title patterns by seniority tier
        self.tier_1_patterns = [
            r'\b(chief\s+executive|ceo)\b',
            r'\b(founder|co-founder)\b',
            r'\b(owner|proprietor)\b',
            r'\b(managing\s+director|md)\b',
            r'\b(president|chairman)\b',
            r'\b(principal|senior\s+partner)\b'
        ]
        
        self.tier_2_patterns = [
            r'\b(director|dir)\b',
            r'\b(manager|mgr)\b',
            r'\b(head\s+of|department\s+head)\b',
            r'\b(senior\s+\w+|sr\s+\w+)\b',
            r'\b(partner|associate\s+director)\b',
            r'\b(vice\s+president|vp)\b'
        ]
        
        self.tier_3_patterns = [
            r'\b(supervisor|team\s+leader)\b',
            r'\b(coordinator|specialist)\b',
            r'\b(lead\s+\w+|senior\s+\w+)\b',
            r'\b(assistant\s+manager|deputy)\b',
            r'\b(officer|administrator)\b'
        ]
        
        # Industry-specific executive patterns
        self.industry_patterns = {
            'plumbing': {
                'tier_1': ['master plumber', 'plumbing contractor', 'business owner'],
                'tier_2': ['senior plumber', 'plumbing manager', 'project manager'],
                'tier_3': ['plumbing supervisor', 'team leader', 'site supervisor']
            },
            'construction': {
                'tier_1': ['construction director', 'project director', 'site director'],
                'tier_2': ['construction manager', 'project manager', 'site manager'],
                'tier_3': ['site supervisor', 'foreman', 'team leader']
            }
        }
    
    async def classify_executive_role(self, title: str, industry: str = "") -> ExecutiveClassificationResult:
        """
        Classify executive role and determine seniority tier.
        
        Args:
            title: Job title to classify
            industry: Industry context for specialized classification
            
        Returns:
            ExecutiveClassificationResult with seniority and confidence
        """
        if not title:
            return ExecutiveClassificationResult(
                is_executive=False,
                seniority_tier=SeniorityTier.TIER_3,
                confidence=0.0,
                title_analysis={},
                industry_relevance=0.0
            )
        
        title_lower = title.lower().strip()
        
        # Check each tier
        tier_scores = {
            SeniorityTier.TIER_1: self._check_tier_patterns(title_lower, self.tier_1_patterns),
            SeniorityTier.TIER_2: self._check_tier_patterns(title_lower, self.tier_2_patterns),
            SeniorityTier.TIER_3: self._check_tier_patterns(title_lower, self.tier_3_patterns)
        }
        
        # Industry-specific analysis
        industry_relevance = self._analyze_industry_relevance(title_lower, industry)
        if industry and industry in self.industry_patterns:
            industry_scores = self._check_industry_patterns(title_lower, industry)
            # Boost scores based on industry relevance
            for tier, score in industry_scores.items():
                if tier in tier_scores:
                    tier_scores[tier] = max(tier_scores[tier], score)
        
        # Determine best tier
        best_tier = max(tier_scores.keys(), key=lambda t: tier_scores[t])
        best_score = tier_scores[best_tier]
        
        # Check if it's executive level
        is_executive = best_score >= 0.5
        
        return ExecutiveClassificationResult(
            is_executive=is_executive,
            seniority_tier=best_tier,
            confidence=best_score,
            title_analysis={tier.value: score for tier, score in tier_scores.items()},
            industry_relevance=industry_relevance
        )
    
    def _check_tier_patterns(self, title: str, patterns: List[str]) -> float:
        """Check title against tier patterns"""
        matches = sum(1 for pattern in patterns if re.search(pattern, title))
        return min(1.0, matches * 0.5)
    
    def _analyze_industry_relevance(self, title: str, industry: str) -> float:
        """Analyze how relevant the title is to the industry"""
        if not industry:
            return 0.5
        
        industry_keywords = {
            'plumbing': ['plumb', 'heating', 'gas', 'boiler', 'pipe'],
            'construction': ['construction', 'building', 'contractor', 'site'],
            'electrical': ['electrical', 'electric', 'electrician', 'wiring'],
            'engineering': ['engineer', 'engineering', 'technical', 'design']
        }
        
        keywords = industry_keywords.get(industry.lower(), [])
        matches = sum(1 for keyword in keywords if keyword in title)
        
        return min(1.0, matches * 0.3)
    
    def _check_industry_patterns(self, title: str, industry: str) -> Dict[SeniorityTier, float]:
        """Check industry-specific patterns"""
        patterns = self.industry_patterns.get(industry, {})
        scores = {}
        
        for tier_name, tier_titles in patterns.items():
            tier_enum = SeniorityTier(f"tier_{tier_name.split('_')[1]}")
            matches = sum(1 for pattern in tier_titles if pattern in title)
            scores[tier_enum] = min(1.0, matches * 0.7)
        
        return scores


class SeniorityTierClassifier:
    """
    Classifies executive seniority tiers based on title and context.
    """
    
    async def classify_seniority(self, title: str, context: str = "") -> SeniorityTier:
        """
        Classify seniority tier based on title and context.
        
        Args:
            title: Job title
            context: Additional context
            
        Returns:
            SeniorityTier enum value
        """
        if not title:
            return SeniorityTier.TIER_3
        
        title_lower = title.lower()
        
        # Tier 1: Top executives
        tier1_keywords = [
            'ceo', 'chief executive', 'founder', 'owner', 'managing director',
            'president', 'chairman', 'principal'
        ]
        
        if any(keyword in title_lower for keyword in tier1_keywords):
            return SeniorityTier.TIER_1
        
        # Tier 2: Senior management
        tier2_keywords = [
            'director', 'manager', 'head of', 'senior', 'vice president',
            'partner', 'associate director'
        ]
        
        if any(keyword in title_lower for keyword in tier2_keywords):
            return SeniorityTier.TIER_2
        
        # Default to Tier 3
        return SeniorityTier.TIER_3


class ExecutiveNameClassifier:
    """
    Main AI-powered executive name classifier combining all classification components.
    """
    
    def __init__(self):
        self.person_classifier = PersonNameClassifier()
        self.title_classifier = ExecutiveTitleClassifier()
        self.seniority_classifier = SeniorityTierClassifier()
    
    async def classify_executive_candidate(self, name: str, title: str = "", 
                                         context: str = "", industry: str = "") -> Dict[str, any]:
        """
        Comprehensive executive classification.
        
        Args:
            name: Candidate name
            title: Job title
            context: Additional context
            industry: Industry context
            
        Returns:
            Complete classification result
        """
        # Person name classification
        name_result = await self.person_classifier.classify_person_name(name, context)
        
        # Executive title classification
        title_result = await self.title_classifier.classify_executive_role(title, industry)
        
        # Seniority classification
        seniority = await self.seniority_classifier.classify_seniority(title, context)
        
        # Combined confidence calculation
        combined_confidence = self._calculate_combined_confidence(
            name_result, title_result, context
        )
        
        return {
            'is_executive': name_result.is_person and title_result.is_executive,
            'is_person': name_result.is_person,
            'seniority_tier': seniority.value,
            'confidence': combined_confidence,
            'name_classification': name_result,
            'title_classification': title_result,
            'classification_reasons': self._get_combined_reasons(name_result, title_result)
        }
    
    def _calculate_combined_confidence(self, name_result: NameClassificationResult,
                                     title_result: ExecutiveClassificationResult,
                                     context: str) -> float:
        """Calculate combined confidence score"""
        # Base confidence from name and title
        base_confidence = (name_result.confidence * 0.6 + title_result.confidence * 0.4)
        
        # Context bonus
        context_bonus = 0.1 if context and len(context) > 10 else 0.0
        
        # Executive bonus
        executive_bonus = 0.1 if title_result.is_executive else 0.0
        
        return min(1.0, base_confidence + context_bonus + executive_bonus)
    
    def _get_combined_reasons(self, name_result: NameClassificationResult,
                            title_result: ExecutiveClassificationResult) -> List[str]:
        """Get combined classification reasons"""
        reasons = []
        reasons.extend(name_result.classification_reasons)
        
        if title_result.is_executive:
            reasons.append(f"Executive title detected: {title_result.seniority_tier.value}")
        
        if title_result.industry_relevance > 0.5:
            reasons.append("Industry-relevant title")
        
        return reasons 