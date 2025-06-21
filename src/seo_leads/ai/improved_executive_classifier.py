"""
Improved Executive Classifier - Phase 4A Enhanced
Based on pattern analysis insights from successful extractions
Focus on better business name filtering and low-content site handling
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import spacy
from spacy.matcher import Matcher

logger = logging.getLogger(__name__)

@dataclass
class ImprovedExecutiveCandidate:
    """Improved executive candidate with enhanced validation"""
    first_name: str
    last_name: str
    full_name: str
    title: str = ""
    context: str = ""
    confidence_score: float = 0.0
    person_probability: float = 0.0
    executive_probability: float = 0.0
    extraction_method: str = ""
    validation_score: float = 0.0
    business_name_score: float = 0.0  # Lower is better (less likely business name)

class BusinessNameFilter:
    """Enhanced business name detection and filtering"""
    
    def __init__(self):
        # Common business/service words that appear in plumbing company names
        self.business_keywords = {
            'services': ['services', 'service', 'plumbing', 'heating', 'gas', 'boiler'],
            'locations': ['birmingham', 'london', 'manchester', 'leeds', 'bristol', 'sutton', 'coldfield'],
            'descriptors': ['emergency', 'professional', 'qualified', 'certified', 'registered'],
            'business_types': ['ltd', 'limited', 'company', 'co', 'contractors', 'engineers'],
            'website_elements': ['home', 'about', 'contact', 'quote', 'menu', 'site', 'page'],
            'generic': ['coming', 'soon', 'under', 'construction', 'facebook', 'twitter', 'linkedin']
        }
        
        # Real person name indicators
        self.person_indicators = {
            'common_first_names': [
                'david', 'john', 'michael', 'james', 'robert', 'william', 'richard', 'thomas',
                'mark', 'paul', 'andrew', 'christopher', 'daniel', 'matthew', 'stephen',
                'sarah', 'emma', 'lisa', 'helen', 'karen', 'rachel', 'laura', 'michelle'
            ],
            'name_patterns': [
                r'^[A-Z][a-z]{2,}$',  # Proper capitalization, 3+ letters
                r'^[A-Z][a-z]+-[A-Z][a-z]+$',  # Hyphenated names like Mary-Jane
                r"^[A-Z][a-z]+('[A-Z][a-z]+)?$"  # Names with apostrophes like O'Connor
            ]
        }
    
    def calculate_business_score(self, first_name: str, last_name: str, context: str = "") -> float:
        """Calculate business name probability (0.0 = person, 1.0 = business)"""
        full_name = f"{first_name} {last_name}".lower()
        score = 0.0
        
        # Check for business keywords in name
        for category, keywords in self.business_keywords.items():
            for keyword in keywords:
                if keyword in full_name:
                    if category == 'services':
                        score += 0.3
                    elif category == 'locations':
                        score += 0.2
                    elif category == 'website_elements':
                        score += 0.4
                    elif category == 'generic':
                        score += 0.5
                    else:
                        score += 0.25
        
        # Penalize if doesn't match person name patterns
        first_matches_pattern = any(re.match(pattern, first_name) for pattern in self.person_indicators['name_patterns'])
        last_matches_pattern = any(re.match(pattern, last_name) for pattern in self.person_indicators['name_patterns'])
        
        if not first_matches_pattern:
            score += 0.2
        if not last_matches_pattern:
            score += 0.2
        
        # Boost if common first name
        if first_name.lower() in self.person_indicators['common_first_names']:
            score -= 0.3
        
        # Check for obvious business combinations
        business_combinations = [
            'gas safe', 'emergency plumber', 'heating engineer', 'boiler service',
            'plumbing service', 'coming soon', 'under construction', 'site under'
        ]
        
        for combo in business_combinations:
            if combo in full_name:
                score += 0.6
        
        return min(1.0, max(0.0, score))
    
    def is_likely_person(self, first_name: str, last_name: str, context: str = "") -> bool:
        """Determine if name is likely a real person"""
        business_score = self.calculate_business_score(first_name, last_name, context)
        return business_score < 0.4

class ContentQualityAnalyzer:
    """Analyze content quality and adjust extraction strategy"""
    
    def analyze_content_quality(self, content: str) -> Dict[str, Any]:
        """Analyze content quality and characteristics"""
        analysis = {
            'content_length': len(content),
            'word_count': len(content.split()),
            'is_minimal': len(content) < 1000,
            'is_under_construction': self._is_under_construction(content),
            'has_meaningful_content': self._has_meaningful_content(content),
            'content_score': 0.0
        }
        
        # Calculate content score
        if analysis['content_length'] > 5000:
            analysis['content_score'] = 1.0
        elif analysis['content_length'] > 2000:
            analysis['content_score'] = 0.8
        elif analysis['content_length'] > 1000:
            analysis['content_score'] = 0.6
        elif analysis['content_length'] > 500:
            analysis['content_score'] = 0.4
        else:
            analysis['content_score'] = 0.2
        
        # Adjust for construction sites
        if analysis['is_under_construction']:
            analysis['content_score'] *= 0.3
        
        return analysis
    
    def _is_under_construction(self, content: str) -> bool:
        """Check if site is under construction"""
        construction_indicators = [
            'under construction', 'coming soon', 'site under development',
            'page not found', 'under maintenance', 'website unavailable'
        ]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in construction_indicators)
    
    def _has_meaningful_content(self, content: str) -> bool:
        """Check if content has meaningful information"""
        # Look for signs of real business content
        meaningful_indicators = [
            'about us', 'our services', 'contact us', 'experience', 'qualified',
            'professional', 'testimonials', 'projects', 'gallery'
        ]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in meaningful_indicators)

class ImprovedExecutiveClassifier:
    """Improved executive classifier with enhanced business filtering"""
    
    def __init__(self):
        self.nlp = None
        self.business_filter = BusinessNameFilter()
        self.content_analyzer = ContentQualityAnalyzer()
        self._initialize_nlp()
    
    def _initialize_nlp(self):
        """Initialize spaCy model"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("✅ Improved classifier: spaCy loaded")
        except OSError:
            logger.warning("⚠️ spaCy not available, using fallback")
    
    def classify_executives(self, content: str, company_name: str = "") -> List[ImprovedExecutiveCandidate]:
        """Main classification method with improved filtering"""
        logger.info(f"🧠 Improved classification starting for {company_name}")
        
        # Analyze content quality
        content_analysis = self.content_analyzer.analyze_content_quality(content)
        logger.info(f"📄 Content quality score: {content_analysis['content_score']:.2f}")
        
        # Extract candidates using spaCy
        candidates = self._extract_candidates_spacy(content, content_analysis)
        
        # Apply improved filtering
        filtered_candidates = self._apply_improved_filtering(candidates, company_name, content_analysis)
        
        # Final ranking
        final_candidates = self._rank_candidates(filtered_candidates)
        
        logger.info(f"✅ Improved classification: {len(final_candidates)} quality candidates")
        return final_candidates
    
    def _extract_candidates_spacy(self, content: str, content_analysis: Dict[str, Any]) -> List[ImprovedExecutiveCandidate]:
        """Extract candidates using spaCy NER"""
        candidates = []
        
        if not self.nlp:
            return candidates
        
        doc = self.nlp(content)
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name_parts = ent.text.strip().split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = ' '.join(name_parts[1:])
                    
                    # Get context
                    start_char = max(0, ent.start_char - 100)
                    end_char = min(len(content), ent.end_char + 100)
                    context = content[start_char:end_char]
                    
                    # Calculate business name score
                    business_score = self.business_filter.calculate_business_score(
                        first_name, last_name, context
                    )
                    
                    # Extract title from context
                    title = self._extract_title_from_context(ent.text, context)
                    
                    candidate = ImprovedExecutiveCandidate(
                        first_name=first_name,
                        last_name=last_name,
                        full_name=ent.text,
                        title=title,
                        context=context,
                        extraction_method="improved_spacy_ner",
                        person_probability=0.8,  # High from NER
                        business_name_score=business_score
                    )
                    
                    candidates.append(candidate)
        
        return candidates
    
    def _extract_title_from_context(self, name: str, context: str) -> str:
        """Extract title from context"""
        # Look for title patterns around the name
        title_patterns = [
            rf'{re.escape(name.lower())}\s*[-–—,:]\s*([^.]+?)(?:\.|$)',
            rf'([^.]+?)\s+{re.escape(name.lower())}',
            rf'{re.escape(name.lower())}\s+is\s+(?:the\s+)?([^.]+?)(?:\.|$)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, context.lower())
            if match:
                potential_title = match.group(1).strip()
                if self._is_valid_title(potential_title):
                    return potential_title
        
        return ""
    
    def _is_valid_title(self, title: str) -> bool:
        """Check if title is valid"""
        if not title or len(title) < 3:
            return False
        
        valid_titles = [
            'director', 'manager', 'owner', 'ceo', 'founder', 'proprietor',
            'partner', 'engineer', 'specialist', 'supervisor', 'foreman'
        ]
        
        title_lower = title.lower()
        return any(valid_title in title_lower for valid_title in valid_titles)
    
    def _apply_improved_filtering(self, candidates: List[ImprovedExecutiveCandidate], 
                                company_name: str, content_analysis: Dict[str, Any]) -> List[ImprovedExecutiveCandidate]:
        """Apply improved filtering logic"""
        filtered = []
        
        for candidate in candidates:
            # Filter out obvious business names
            if candidate.business_name_score > 0.6:
                logger.debug(f"Filtered business name: {candidate.full_name} (score: {candidate.business_name_score:.2f})")
                continue
            
            # Filter out names that match company name
            if company_name and company_name.lower() in candidate.full_name.lower():
                logger.debug(f"Filtered company name match: {candidate.full_name}")
                continue
            
            # Check if likely a real person
            if not self.business_filter.is_likely_person(candidate.first_name, candidate.last_name, candidate.context):
                logger.debug(f"Filtered non-person: {candidate.full_name}")
                continue
            
            # Calculate final confidence
            candidate.confidence_score = self._calculate_confidence(candidate, content_analysis)
            
            # Only include candidates with reasonable confidence
            if candidate.confidence_score >= 0.4:
                filtered.append(candidate)
        
        return filtered
    
    def _calculate_confidence(self, candidate: ImprovedExecutiveCandidate, content_analysis: Dict[str, Any]) -> float:
        """Calculate final confidence score"""
        base_confidence = candidate.person_probability
        
        # Adjust for business name score (lower is better)
        business_penalty = candidate.business_name_score * 0.3
        confidence = base_confidence - business_penalty
        
        # Boost for valid title
        if candidate.title:
            confidence += 0.1
        
        # Boost for good content quality
        content_boost = content_analysis['content_score'] * 0.2
        confidence += content_boost
        
        # Boost for common first names
        if candidate.first_name.lower() in self.business_filter.person_indicators['common_first_names']:
            confidence += 0.15
        
        return min(1.0, max(0.0, confidence))
    
    def _rank_candidates(self, candidates: List[ImprovedExecutiveCandidate]) -> List[ImprovedExecutiveCandidate]:
        """Rank candidates by quality"""
        # Sort by confidence score
        candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Return top candidates
        return candidates[:10] 