"""
Enhanced Executive Classifier - Phase 4A
Advanced ML-based executive identification and classification
Target: Improve accuracy from 40% to 70%+ success rate
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
import spacy
from spacy.matcher import Matcher
from spacy.tokens import Span, Doc
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
import pickle
import os
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ExecutiveCandidate:
    """Enhanced executive candidate with ML features"""
    first_name: str
    last_name: str
    full_name: str
    title: str = ""
    context: str = ""
    confidence_score: float = 0.0
    ml_features: Dict[str, Any] = field(default_factory=dict)
    validation_signals: List[str] = field(default_factory=list)
    person_probability: float = 0.0
    executive_probability: float = 0.0
    extraction_method: str = ""

class ExecutiveTitleClassifier:
    """Classifier for executive titles and roles"""
    
    def __init__(self):
        self.title_hierarchy = {
            'c_level': {
                'titles': ['ceo', 'chief executive', 'chief executive officer', 'managing director', 'md'],
                'weight': 1.0,
                'confidence_boost': 0.3
            },
            'director': {
                'titles': ['director', 'executive director', 'operations director', 'business director'],
                'weight': 0.9,
                'confidence_boost': 0.25
            },
            'owner': {
                'titles': ['owner', 'business owner', 'company owner', 'proprietor', 'founder'],
                'weight': 0.95,
                'confidence_boost': 0.3
            },
            'partner': {
                'titles': ['partner', 'business partner', 'senior partner', 'managing partner'],
                'weight': 0.85,
                'confidence_boost': 0.2
            },
            'manager': {
                'titles': ['manager', 'general manager', 'business manager', 'operations manager', 'office manager'],
                'weight': 0.7,
                'confidence_boost': 0.15
            },
            'senior_technical': {
                'titles': ['master plumber', 'senior plumber', 'lead plumber', 'principal engineer', 'chief engineer'],
                'weight': 0.6,
                'confidence_boost': 0.1
            },
            'qualified_professional': {
                'titles': ['gas safe engineer', 'heating engineer', 'plumbing engineer', 'qualified plumber', 'certified plumber'],
                'weight': 0.5,
                'confidence_boost': 0.05
            }
        }
    
    def classify_title(self, title: str) -> Tuple[str, float, float]:
        """Classify executive title and return category, weight, and confidence boost"""
        if not title:
            return "unknown", 0.0, 0.0
        
        title_lower = title.lower().strip()
        
        for category, info in self.title_hierarchy.items():
            for exec_title in info['titles']:
                if exec_title in title_lower:
                    return category, info['weight'], info['confidence_boost']
        
        # Check for partial matches or variations
        for category, info in self.title_hierarchy.items():
            for exec_title in info['titles']:
                title_words = set(exec_title.split())
                input_words = set(title_lower.split())
                
                # If 50% or more words match
                overlap = len(title_words.intersection(input_words))
                if overlap / len(title_words) >= 0.5:
                    return category, info['weight'] * 0.8, info['confidence_boost'] * 0.8
        
        return "other", 0.3, 0.0

class AdvancedNameExtractor:
    """Advanced name extraction using spaCy and custom patterns"""
    
    def __init__(self):
        self.nlp = None
        self.matcher = None
        self.title_classifier = ExecutiveTitleClassifier()
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize spaCy models and matchers"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.matcher = Matcher(self.nlp.vocab)
            self._setup_custom_patterns()
            logger.info("✅ spaCy models loaded successfully")
        except OSError:
            logger.warning("⚠️ spaCy model not available, using fallback methods")
            self._initialize_fallback()
    
    def _initialize_fallback(self):
        """Initialize fallback methods when spaCy is not available"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('maxent_ne_chunker', quiet=True)
            nltk.download('words', quiet=True)
            nltk.download('stopwords', quiet=True)
            logger.info("✅ NLTK fallback initialized")
        except Exception as e:
            logger.error(f"❌ Fallback initialization failed: {e}")
    
    def _setup_custom_patterns(self):
        """Setup custom spaCy patterns for executive name extraction"""
        if not self.matcher:
            return
        
        # Pattern 1: Name followed by title
        pattern1 = [
            {"IS_TITLE": True},  # First name (capitalized)
            {"IS_TITLE": True},  # Last name (capitalized)
            {"LOWER": {"IN": ["-", "–", "—", ",", ":"]}},  # Separator
            {"IS_ALPHA": True, "OP": "+"}  # Title words
        ]
        
        # Pattern 2: Title followed by name
        pattern2 = [
            {"LOWER": {"IN": ["director", "manager", "owner", "ceo", "founder"]}},
            {"IS_TITLE": True},  # First name
            {"IS_TITLE": True}   # Last name
        ]
        
        # Pattern 3: Contact person patterns
        pattern3 = [
            {"LOWER": {"IN": ["contact", "speak", "ask", "call", "email"]}},
            {"LOWER": {"IN": ["to", "for"]}, "OP": "?"},
            {"IS_TITLE": True},  # First name
            {"IS_TITLE": True}   # Last name
        ]
        
        self.matcher.add("EXECUTIVE_PATTERN_1", [pattern1])
        self.matcher.add("EXECUTIVE_PATTERN_2", [pattern2])
        self.matcher.add("CONTACT_PATTERN", [pattern3])
    
    def extract_executives_advanced(self, text: str) -> List[ExecutiveCandidate]:
        """Extract executive candidates using advanced ML techniques"""
        if self.nlp:
            return self._extract_with_spacy_advanced(text)
        else:
            return self._extract_with_nltk_fallback(text)
    
    def _extract_with_spacy_advanced(self, text: str) -> List[ExecutiveCandidate]:
        """Advanced extraction using spaCy NER and custom patterns"""
        doc = self.nlp(text)
        candidates = []
        
        # Method 1: Named Entity Recognition
        ner_candidates = self._extract_from_ner(doc, text)
        candidates.extend(ner_candidates)
        
        # Method 2: Custom pattern matching
        pattern_candidates = self._extract_from_patterns(doc, text)
        candidates.extend(pattern_candidates)
        
        # Method 3: Contextual extraction
        context_candidates = self._extract_from_context(doc, text)
        candidates.extend(context_candidates)
        
        return self._process_and_deduplicate(candidates, text)
    
    def _extract_from_ner(self, doc: Doc, original_text: str) -> List[ExecutiveCandidate]:
        """Extract using spaCy Named Entity Recognition"""
        candidates = []
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name_parts = ent.text.strip().split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = ' '.join(name_parts[1:])
                    
                    # Get context around the entity
                    start_char = max(0, ent.start_char - 100)
                    end_char = min(len(original_text), ent.end_char + 100)
                    context = original_text[start_char:end_char]
                    
                    # Extract title from context
                    title = self._extract_title_from_context(ent.text, context)
                    
                    # Calculate features
                    features = self._calculate_ml_features(ent.text, context, title)
                    
                    candidate = ExecutiveCandidate(
                        first_name=first_name,
                        last_name=last_name,
                        full_name=ent.text,
                        title=title,
                        context=context,
                        ml_features=features,
                        extraction_method="spacy_ner",
                        person_probability=0.8  # High probability from NER
                    )
                    
                    candidates.append(candidate)
        
        return candidates
    
    def _extract_from_patterns(self, doc: Doc, original_text: str) -> List[ExecutiveCandidate]:
        """Extract using custom spaCy patterns"""
        candidates = []
        matches = self.matcher(doc)
        
        for match_id, start, end in matches:
            span = doc[start:end]
            match_text = span.text
            
            # Extract name and title from pattern match
            name, title = self._parse_pattern_match(match_text, span)
            
            if name and len(name.split()) >= 2:
                name_parts = name.split()
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])
                
                # Get broader context
                start_char = max(0, span.start_char - 150)
                end_char = min(len(original_text), span.end_char + 150)
                context = original_text[start_char:end_char]
                
                features = self._calculate_ml_features(name, context, title)
                
                candidate = ExecutiveCandidate(
                    first_name=first_name,
                    last_name=last_name,
                    full_name=name,
                    title=title,
                    context=context,
                    ml_features=features,
                    extraction_method="pattern_matching",
                    person_probability=0.7
                )
                
                candidates.append(candidate)
        
        return candidates
    
    def _extract_from_context(self, doc: Doc, original_text: str) -> List[ExecutiveCandidate]:
        """Extract names from executive context clues"""
        candidates = []
        
        # Look for sentences with executive indicators
        executive_indicators = [
            'director', 'manager', 'owner', 'ceo', 'founder', 'proprietor',
            'partner', 'chief', 'head', 'lead', 'senior', 'principal'
        ]
        
        for sent in doc.sents:
            sent_text = sent.text.lower()
            
            # Check if sentence contains executive indicators
            if any(indicator in sent_text for indicator in executive_indicators):
                # Look for person names in this sentence
                for ent in sent.ents:
                    if ent.label_ == "PERSON":
                        name_parts = ent.text.strip().split()
                        if len(name_parts) >= 2:
                            first_name = name_parts[0]
                            last_name = ' '.join(name_parts[1:])
                            
                            # Extract title from sentence
                            title = self._extract_title_from_sentence(sent.text, ent.text)
                            
                            features = self._calculate_ml_features(ent.text, sent.text, title)
                            
                            candidate = ExecutiveCandidate(
                                first_name=first_name,
                                last_name=last_name,
                                full_name=ent.text,
                                title=title,
                                context=sent.text,
                                ml_features=features,
                                extraction_method="context_extraction",
                                person_probability=0.9  # High probability due to context
                            )
                            
                            candidates.append(candidate)
        
        return candidates
    
    def _extract_title_from_context(self, name: str, context: str) -> str:
        """Extract executive title from context around name"""
        name_index = context.lower().find(name.lower())
        if name_index == -1:
            return ""
        
        # Look before and after the name
        before_text = context[:name_index].lower()
        after_text = context[name_index + len(name):].lower()
        
        # Common title patterns
        title_patterns = [
            rf'{re.escape(name.lower())}\s*[-–—,:]\s*([^.]+?)(?:\.|$)',
            rf'([^.]+?)\s+{re.escape(name.lower())}',
            rf'{re.escape(name.lower())}\s+is\s+(?:the\s+)?([^.]+?)(?:\.|$)',
            rf'{re.escape(name.lower())}\s+(?:works\s+as|serves\s+as)\s+([^.]+?)(?:\.|$)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, context.lower())
            if match:
                potential_title = match.group(1).strip()
                if self._is_valid_title(potential_title):
                    return potential_title
        
        return ""
    
    def _extract_title_from_sentence(self, sentence: str, name: str) -> str:
        """Extract title from a sentence containing the name"""
        sentence_lower = sentence.lower()
        name_lower = name.lower()
        
        # Pattern: "Name, Title" or "Name - Title"
        title_pattern = rf'{re.escape(name_lower)}\s*[-–—,:]\s*([^.]+?)(?:\.|$)'
        match = re.search(title_pattern, sentence_lower)
        if match:
            return match.group(1).strip()
        
        # Pattern: "Title Name"
        title_before_pattern = rf'(\w+(?:\s+\w+)*)\s+{re.escape(name_lower)}'
        match = re.search(title_before_pattern, sentence_lower)
        if match:
            potential_title = match.group(1).strip()
            if self._is_valid_title(potential_title):
                return potential_title
        
        return ""
    
    def _is_valid_title(self, title: str) -> bool:
        """Check if extracted title is a valid executive title"""
        if not title or len(title) < 3:
            return False
        
        title_lower = title.lower()
        
        # Check against known titles
        category, weight, boost = self.title_classifier.classify_title(title)
        if weight > 0.3:
            return True
        
        # Additional validation
        invalid_indicators = [
            'plumbing', 'heating', 'gas', 'services', 'emergency', 'qualified',
            'certified', 'ltd', 'limited', 'company', 'business', 'website',
            'phone', 'email', 'address', 'contact', 'call', 'visit'
        ]
        
        return not any(indicator in title_lower for indicator in invalid_indicators)
    
    def _calculate_ml_features(self, name: str, context: str, title: str) -> Dict[str, Any]:
        """Calculate ML features for executive classification"""
        features = {}
        
        # Name features
        features['name_length'] = len(name)
        features['has_middle_initial'] = bool(re.search(r'\b[A-Z]\.\s', name))
        features['name_complexity'] = len(name.split())
        
        # Title features
        title_category, title_weight, title_boost = self.title_classifier.classify_title(title)
        features['title_category'] = title_category
        features['title_weight'] = title_weight
        features['title_boost'] = title_boost
        
        # Context features
        features['context_length'] = len(context)
        features['has_contact_info'] = bool(re.search(r'@|phone|tel|mobile', context.lower()))
        features['has_executive_keywords'] = bool(re.search(
            r'\b(director|manager|owner|ceo|founder|chief|head|lead|senior)\b', 
            context.lower()
        ))
        
        # Business context
        features['plumbing_context'] = bool(re.search(
            r'\b(plumb|heating|gas|boiler|drain|pipe|water)\b', 
            context.lower()
        ))
        
        # Validation signals
        features['in_team_section'] = 'team' in context.lower() or 'staff' in context.lower()
        features['in_about_section'] = 'about' in context.lower() or 'story' in context.lower()
        features['in_contact_section'] = 'contact' in context.lower()
        
        return features
    
    def _parse_pattern_match(self, match_text: str, span: Span) -> Tuple[str, str]:
        """Parse name and title from pattern match"""
        # Simple parsing for now - can be enhanced
        parts = match_text.split()
        
        # Look for capitalized words (likely names)
        name_parts = []
        title_parts = []
        
        in_name = True
        for part in parts:
            if part[0].isupper() and part.isalpha() and in_name:
                name_parts.append(part)
            elif part in ['-', '–', '—', ',', ':']:
                in_name = False
            elif not in_name:
                title_parts.append(part)
        
        name = ' '.join(name_parts) if len(name_parts) >= 2 else ""
        title = ' '.join(title_parts)
        
        return name, title
    
    def _extract_with_nltk_fallback(self, text: str) -> List[ExecutiveCandidate]:
        """Fallback extraction using NLTK when spaCy is not available"""
        try:
            from nltk import ne_chunk, pos_tag, word_tokenize
            
            candidates = []
            sentences = sent_tokenize(text)
            
            for sentence in sentences:
                tokens = word_tokenize(sentence)
                pos_tags = pos_tag(tokens)
                chunks = ne_chunk(pos_tags, binary=False)
                
                for chunk in chunks:
                    if hasattr(chunk, 'label') and chunk.label() == 'PERSON':
                        name_tokens = [token for token, pos in chunk.leaves()]
                        if len(name_tokens) >= 2:
                            first_name = name_tokens[0]
                            last_name = ' '.join(name_tokens[1:])
                            full_name = ' '.join(name_tokens)
                            
                            title = self._extract_title_from_context(full_name, sentence)
                            features = self._calculate_ml_features(full_name, sentence, title)
                            
                            candidate = ExecutiveCandidate(
                                first_name=first_name,
                                last_name=last_name,
                                full_name=full_name,
                                title=title,
                                context=sentence,
                                ml_features=features,
                                extraction_method="nltk_fallback",
                                person_probability=0.6
                            )
                            
                            candidates.append(candidate)
            
            return self._process_and_deduplicate(candidates, text)
            
        except Exception as e:
            logger.error(f"NLTK fallback extraction failed: {e}")
            return []
    
    def _process_and_deduplicate(self, candidates: List[ExecutiveCandidate], original_text: str) -> List[ExecutiveCandidate]:
        """Process candidates and remove duplicates"""
        # Calculate final scores
        for candidate in candidates:
            candidate.executive_probability = self._calculate_executive_probability(candidate)
            candidate.confidence_score = self._calculate_final_confidence(candidate)
            candidate.validation_signals = self._get_validation_signals(candidate, original_text)
        
        # Deduplicate by name similarity
        unique_candidates = []
        seen_names = set()
        
        for candidate in candidates:
            name_key = f"{candidate.first_name.lower()}_{candidate.last_name.lower()}"
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_candidates.append(candidate)
        
        # Sort by confidence
        unique_candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return unique_candidates
    
    def _calculate_executive_probability(self, candidate: ExecutiveCandidate) -> float:
        """Calculate probability that this person is an executive"""
        probability = 0.5  # Base probability
        
        # Title-based scoring
        if candidate.ml_features.get('title_weight', 0) > 0.7:
            probability += 0.3
        elif candidate.ml_features.get('title_weight', 0) > 0.5:
            probability += 0.2
        elif candidate.ml_features.get('title_weight', 0) > 0.3:
            probability += 0.1
        
        # Context-based scoring
        if candidate.ml_features.get('has_executive_keywords', False):
            probability += 0.2
        
        if candidate.ml_features.get('in_team_section', False):
            probability += 0.1
        
        if candidate.ml_features.get('has_contact_info', False):
            probability += 0.1
        
        return min(1.0, max(0.0, probability))
    
    def _calculate_final_confidence(self, candidate: ExecutiveCandidate) -> float:
        """Calculate final confidence score"""
        # Combine person probability, executive probability, and features
        base_score = (candidate.person_probability + candidate.executive_probability) / 2
        
        # Add title boost
        title_boost = candidate.ml_features.get('title_boost', 0)
        
        # Add method reliability
        method_weights = {
            'spacy_ner': 0.1,
            'pattern_matching': 0.05,
            'context_extraction': 0.08,
            'nltk_fallback': 0.02
        }
        method_boost = method_weights.get(candidate.extraction_method, 0)
        
        final_score = base_score + title_boost + method_boost
        return min(1.0, max(0.0, final_score))
    
    def _get_validation_signals(self, candidate: ExecutiveCandidate, original_text: str) -> List[str]:
        """Get validation signals for the candidate"""
        signals = []
        
        if candidate.ml_features.get('has_executive_keywords', False):
            signals.append('executive_keywords')
        
        if candidate.ml_features.get('has_contact_info', False):
            signals.append('contact_info')
        
        if candidate.ml_features.get('in_team_section', False):
            signals.append('team_section')
        
        if candidate.ml_features.get('title_weight', 0) > 0.7:
            signals.append('high_authority_title')
        elif candidate.ml_features.get('title_weight', 0) > 0.5:
            signals.append('executive_title')
        
        if candidate.ml_features.get('plumbing_context', False):
            signals.append('industry_context')
        
        return signals

class EnhancedExecutiveClassifier:
    """Main enhanced executive classifier"""
    
    def __init__(self):
        self.name_extractor = AdvancedNameExtractor()
        self.title_classifier = ExecutiveTitleClassifier()
    
    def classify_executives(self, content: str, company_name: str = "") -> List[ExecutiveCandidate]:
        """Main method to classify executives from content"""
        logger.info(f"🧠 Starting enhanced ML classification for {company_name or 'company'}")
        
        # Extract executive candidates
        candidates = self.name_extractor.extract_executives_advanced(content)
        
        # Filter and enhance candidates
        filtered_candidates = self._filter_candidates(candidates, company_name)
        
        # Final quality check
        final_candidates = self._final_quality_check(filtered_candidates)
        
        logger.info(f"✅ Enhanced classification complete: {len(final_candidates)} high-quality candidates")
        return final_candidates
    
    def _filter_candidates(self, candidates: List[ExecutiveCandidate], company_name: str) -> List[ExecutiveCandidate]:
        """Filter candidates based on quality thresholds"""
        filtered = []
        
        for candidate in candidates:
            # Minimum confidence threshold
            if candidate.confidence_score < 0.3:
                continue
            
            # Check for business name patterns
            if self._is_business_name(candidate, company_name):
                continue
            
            # Check name quality
            if not self._is_quality_name(candidate):
                continue
            
            filtered.append(candidate)
        
        return filtered
    
    def _is_business_name(self, candidate: ExecutiveCandidate, company_name: str) -> bool:
        """Check if candidate name is actually a business name"""
        full_name = candidate.full_name.lower()
        
        # Check against company name
        if company_name and company_name.lower() in full_name:
            return True
        
        # Check for business indicators
        business_keywords = [
            'plumbing', 'heating', 'gas', 'services', 'emergency', 'ltd', 'limited',
            'company', 'business', 'qualified', 'certified', 'professional'
        ]
        
        return any(keyword in full_name for keyword in business_keywords)
    
    def _is_quality_name(self, candidate: ExecutiveCandidate) -> bool:
        """Check if candidate has a quality person name"""
        # Check name length and format
        if len(candidate.first_name) < 2 or len(candidate.last_name) < 2:
            return False
        
        # Check for reasonable name patterns
        if not re.match(r'^[A-Za-z][a-z]*$', candidate.first_name):
            return False
        
        if not re.match(r'^[A-Za-z][a-z]*(?:[-\s][A-Za-z][a-z]*)*$', candidate.last_name):
            return False
        
        return True
    
    def _final_quality_check(self, candidates: List[ExecutiveCandidate]) -> List[ExecutiveCandidate]:
        """Final quality check and ranking"""
        # Sort by confidence score
        candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Return top candidates (limit to maintain quality)
        return candidates[:20] 