"""
AI-Powered Name Recognition Engine

P3.1 IMPLEMENTATION: Advanced name recognition using NLP
Features:
- spaCy NER for person name extraction
- Context-aware name validation
- Business vs person name classification
- Confidence scoring based on linguistic patterns
- Zero-cost architecture (local NLP models)
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Optional spacy import
try:
    import spacy
    from spacy.matcher import Matcher
    SPACY_AVAILABLE = True
except ImportError:
    spacy = None
    Matcher = None
    SPACY_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class NameRecognitionResult:
    """Result of AI name recognition"""
    original_text: str
    extracted_name: str
    confidence: float
    is_person_name: bool
    name_type: str  # 'person', 'business', 'mixed', 'unknown'
    linguistic_features: Dict[str, any]
    extraction_method: str

class NameRecognitionEngine:
    """P3.1: AI-powered name recognition using spaCy NLP"""
    
    def __init__(self):
        self.nlp = None
        self.matcher = None
        self.person_indicators = None
        self.business_indicators = None
        self._initialize_nlp()
        
        logger.info("P3.1: AI Name Recognition Engine initialized")
    
    def _initialize_nlp(self):
        """Initialize spaCy NLP model and patterns"""
        # Always initialize linguistic indicators
        self.person_indicators = {
            'titles': ['mr', 'mrs', 'ms', 'dr', 'prof', 'sir', 'dame'],
            'roles': ['ceo', 'founder', 'director', 'manager', 'owner', 'partner'],
            'common_first_names': [
                'james', 'john', 'robert', 'michael', 'william', 'david', 'richard', 'charles',
                'joseph', 'thomas', 'mary', 'patricia', 'jennifer', 'linda', 'elizabeth',
                'barbara', 'susan', 'jessica', 'sarah', 'karen', 'jack', 'steve', 'mark',
                'paul', 'andrew', 'joshua', 'kenneth', 'kevin', 'brian', 'george', 'edward'
            ],
            'common_surnames': [
                'smith', 'johnson', 'williams', 'brown', 'jones', 'garcia', 'miller',
                'davis', 'rodriguez', 'martinez', 'hernandez', 'lopez', 'gonzalez',
                'wilson', 'anderson', 'thomas', 'taylor', 'moore', 'jackson', 'martin'
            ]
        }
        
        self.business_indicators = {
            'suffixes': ['ltd', 'limited', 'plc', 'llc', 'inc', 'corp', 'co', 'company'],
            'types': ['services', 'solutions', 'group', 'systems', 'technologies', 'consulting'],
            'industries': ['plumbing', 'electrical', 'construction', 'building', 'roofing', 
                          'heating', 'cleaning', 'maintenance', 'repair', 'installation']
        }
        
        if not SPACY_AVAILABLE:
            logger.info("P3.1: spaCy not available, using fallback mode")
            self.nlp = None
            return
            
        try:
            # Try to load English model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("P3.1: spaCy English model loaded successfully")
        except OSError:
            logger.warning("P3.1: spaCy English model not found, using fallback")
            # Fallback to basic processing without NER
            self.nlp = None
        
        if self.nlp:
            self.matcher = Matcher(self.nlp.vocab)
            self._setup_patterns()
    
    def _setup_patterns(self):
        """Setup linguistic patterns for name recognition"""
        # Person name patterns
        person_patterns = [
            [{"POS": "PROPN"}, {"POS": "PROPN"}],  # John Smith
            [{"POS": "PROPN"}, {"POS": "PROPN"}, {"POS": "PROPN"}],  # John Michael Smith
            [{"TEXT": {"REGEX": r"^[A-Z][a-z]+$"}}, {"TEXT": {"REGEX": r"^[A-Z][a-z]+$"}}],  # Capitalized words
        ]
        
        # Business name patterns
        business_patterns = [
            [{"LOWER": {"IN": ["ltd", "limited", "plc", "llc", "inc", "corp"]}}],
            [{"LOWER": {"IN": ["services", "solutions", "group", "company", "co"]}}],
            [{"LOWER": {"IN": ["plumbing", "electrical", "construction", "building"]}}],
        ]
        
        if self.matcher:
            self.matcher.add("PERSON_NAME", person_patterns)
            self.matcher.add("BUSINESS_NAME", business_patterns)
    
    def recognize_name(self, text: str, context: str = "") -> NameRecognitionResult:
        """P3.1: AI-powered name recognition with context awareness"""
        try:
            # Clean input text
            cleaned_text = self._clean_text(text)
            
            if not cleaned_text:
                return self._create_empty_result(text)
            
            # Use spaCy NER if available
            if self.nlp:
                return self._spacy_recognition(cleaned_text, context, text)
            else:
                return self._fallback_recognition(cleaned_text, context, text)
                
        except Exception as e:
            logger.warning(f"P3.1: Name recognition failed for '{text}': {e}")
            return self._create_empty_result(text)
    
    def _spacy_recognition(self, text: str, context: str, original: str) -> NameRecognitionResult:
        """Advanced recognition using spaCy NLP"""
        doc = self.nlp(text)
        
        # Extract named entities
        person_entities = [ent for ent in doc.ents if ent.label_ == "PERSON"]
        org_entities = [ent for ent in doc.ents if ent.label_ in ["ORG", "GPE"]]
        
        # Use matcher patterns
        matches = self.matcher(doc)
        
        # Analyze linguistic features
        linguistic_features = {
            'has_person_entities': len(person_entities) > 0,
            'has_org_entities': len(org_entities) > 0,
            'person_entities': [ent.text for ent in person_entities],
            'org_entities': [ent.text for ent in org_entities],
            'pos_tags': [(token.text, token.pos_) for token in doc],
            'pattern_matches': len(matches)
        }
        
        # Determine best extraction
        if person_entities:
            # Use first person entity
            extracted_name = person_entities[0].text
            confidence = self._calculate_person_confidence(extracted_name, context, linguistic_features)
            is_person = True
            name_type = 'person'
            method = 'spacy_ner'
        elif self._looks_like_person_name(text):
            # Fallback to heuristic analysis
            extracted_name = self._extract_person_name_heuristic(text)
            confidence = self._calculate_person_confidence(extracted_name, context, linguistic_features)
            is_person = True
            name_type = 'person'
            method = 'spacy_heuristic'
        else:
            # Likely business name
            extracted_name = text
            confidence = 0.3  # Low confidence for business names
            is_person = False
            name_type = 'business'
            method = 'spacy_business'
        
        return NameRecognitionResult(
            original_text=original,
            extracted_name=extracted_name,
            confidence=confidence,
            is_person_name=is_person,
            name_type=name_type,
            linguistic_features=linguistic_features,
            extraction_method=method
        )
    
    def _fallback_recognition(self, text: str, context: str, original: str) -> NameRecognitionResult:
        """Fallback recognition without spaCy"""
        # Basic heuristic analysis
        is_person = self._looks_like_person_name(text)
        
        if is_person:
            extracted_name = self._extract_person_name_heuristic(text)
            confidence = self._calculate_basic_confidence(extracted_name, context)
            name_type = 'person'
        else:
            extracted_name = text
            confidence = 0.2
            name_type = 'business'
        
        linguistic_features = {
            'fallback_mode': True,
            'word_count': len(text.split()),
            'has_common_names': self._has_common_names(text)
        }
        
        return NameRecognitionResult(
            original_text=original,
            extracted_name=extracted_name,
            confidence=confidence,
            is_person_name=is_person,
            name_type=name_type,
            linguistic_features=linguistic_features,
            extraction_method='fallback_heuristic'
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for processing"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common prefixes/suffixes that interfere with name recognition
        prefixes_to_remove = [
            r'^(about|meet|contact|our)\s+',
            r'^(the|a|an)\s+',
        ]
        
        for prefix in prefixes_to_remove:
            cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    def _looks_like_person_name(self, text: str) -> bool:
        """Heuristic to determine if text looks like a person name"""
        words = text.lower().split()
        
        # Check for business indicators
        for word in words:
            if word in self.business_indicators['suffixes']:
                return False
            if word in self.business_indicators['types']:
                return False
            if word in self.business_indicators['industries']:
                return False
        
        # Check for person indicators
        person_score = 0
        
        # Check for common first names
        if words and words[0] in self.person_indicators['common_first_names']:
            person_score += 3
        
        # Check for common surnames
        if len(words) > 1 and words[-1] in self.person_indicators['common_surnames']:
            person_score += 2
        
        # Check for titles
        for word in words:
            if word in self.person_indicators['titles']:
                person_score += 2
        
        # Check word count (person names typically 2-3 words)
        if 2 <= len(words) <= 3:
            person_score += 1
        
        # Check capitalization pattern
        if all(word[0].isupper() and word[1:].islower() for word in words if word):
            person_score += 1
        
        return person_score >= 3
    
    def _extract_person_name_heuristic(self, text: str) -> str:
        """Extract person name using heuristics"""
        words = text.split()
        
        # Remove titles
        filtered_words = []
        for word in words:
            if word.lower() not in self.person_indicators['titles']:
                filtered_words.append(word)
        
        # Take first 2-3 words as name
        if len(filtered_words) >= 2:
            return ' '.join(filtered_words[:3])
        elif len(filtered_words) == 1:
            return filtered_words[0]
        else:
            return text
    
    def _calculate_person_confidence(self, name: str, context: str, features: Dict) -> float:
        """Calculate confidence score for person name"""
        confidence = 0.0
        
        # Base confidence from linguistic features
        if features.get('has_person_entities', False):
            confidence += 0.4
        
        # Word pattern analysis
        words = name.lower().split()
        if 2 <= len(words) <= 3:
            confidence += 0.2
        
        # Common name check
        if words and words[0] in self.person_indicators['common_first_names']:
            confidence += 0.2
        
        if len(words) > 1 and words[-1] in self.person_indicators['common_surnames']:
            confidence += 0.2
        
        # Context analysis
        context_lower = context.lower()
        for role in self.person_indicators['roles']:
            if role in context_lower:
                confidence += 0.1
                break
        
        # Capitalization pattern
        if all(word[0].isupper() and word[1:].islower() for word in name.split() if word):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _calculate_basic_confidence(self, name: str, context: str) -> float:
        """Basic confidence calculation without spaCy"""
        confidence = 0.0
        
        words = name.lower().split()
        
        # Word count
        if 2 <= len(words) <= 3:
            confidence += 0.3
        
        # Common names
        if words and words[0] in self.person_indicators['common_first_names']:
            confidence += 0.3
        
        # Context
        context_lower = context.lower()
        for role in self.person_indicators['roles']:
            if role in context_lower:
                confidence += 0.2
                break
        
        return min(1.0, confidence)
    
    def _has_common_names(self, text: str) -> bool:
        """Check if text contains common names"""
        words = text.lower().split()
        return any(word in self.person_indicators['common_first_names'] for word in words)
    
    def _create_empty_result(self, original: str) -> NameRecognitionResult:
        """Create empty result for failed recognition"""
        return NameRecognitionResult(
            original_text=original,
            extracted_name=original,
            confidence=0.0,
            is_person_name=False,
            name_type='unknown',
            linguistic_features={},
            extraction_method='failed'
        )
    
    def batch_recognize_names(self, texts: List[str], contexts: List[str] = None) -> List[NameRecognitionResult]:
        """Batch process multiple names"""
        if contexts is None:
            contexts = [""] * len(texts)
        
        results = []
        for i, text in enumerate(texts):
            context = contexts[i] if i < len(contexts) else ""
            result = self.recognize_name(text, context)
            results.append(result)
        
        return results
    
    def get_statistics(self) -> Dict:
        """Get name recognition statistics"""
        return {
            "nlp_model_available": self.nlp is not None,
            "spacy_model": "en_core_web_sm" if self.nlp else None,
            "person_indicators_count": len(self.person_indicators['common_first_names']),
            "business_indicators_count": len(self.business_indicators['suffixes']),
            "patterns_loaded": self.matcher is not None
        }

# Test function
async def test_name_recognition():
    """Test the name recognition engine"""
    print("🧠 Testing P3.1 AI Name Recognition Engine...")
    
    engine = NameRecognitionEngine()
    
    test_cases = [
        ("Jack Plumber", "Master Plumber"),
        ("Plumbing Birmingham", "Plumbing Services"),
        ("John Smith", "CEO"),
        ("ABC Services Ltd", "Company"),
        ("Dr. Sarah Johnson", "Medical Director"),
        ("Birmingham Heating Solutions", "Heating Company")
    ]
    
    for text, context in test_cases:
        result = engine.recognize_name(text, context)
        print(f"Input: '{text}' | Context: '{context}'")
        print(f"  → Extracted: '{result.extracted_name}'")
        print(f"  → Is Person: {result.is_person_name}")
        print(f"  → Confidence: {result.confidence:.2f}")
        print(f"  → Type: {result.name_type}")
        print(f"  → Method: {result.extraction_method}")
        print()
    
    print("🎉 P3.1 Name Recognition Engine test complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_name_recognition()) 