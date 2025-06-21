"""
Executive Title Classifier

P3.1 IMPLEMENTATION: AI-powered executive title classification
Features:
- Executive role detection and classification
- Seniority tier prediction
- Industry-specific title recognition
- Confidence scoring for title classifications
- Zero-cost architecture (rule-based ML)
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SeniorityLevel(Enum):
    """Executive seniority levels"""
    TIER_1 = "tier_1"  # CEO, Founder, Managing Director
    TIER_2 = "tier_2"  # Director, Head of, General Manager  
    TIER_3 = "tier_3"  # Manager, Lead, Senior roles
    UNKNOWN = "unknown"

@dataclass
class TitleClassificationResult:
    """Result of title classification"""
    original_title: str
    normalized_title: str
    seniority_level: SeniorityLevel
    confidence: float
    executive_type: str  # 'ceo', 'founder', 'director', 'manager', 'owner'
    industry_context: Optional[str]
    classification_features: Dict[str, any]

class ExecutiveTitleClassifier:
    """P3.1: AI-powered executive title classification"""
    
    def __init__(self):
        self.title_patterns = self._initialize_title_patterns()
        self.industry_contexts = self._initialize_industry_contexts()
        self.seniority_weights = self._initialize_seniority_weights()
        
        logger.info("P3.1: Executive Title Classifier initialized")
    
    def _initialize_title_patterns(self) -> Dict:
        """Initialize title recognition patterns"""
        return {
            'tier_1': {
                'ceo': [
                    r'\bchief executive officer\b',
                    r'\bceo\b',
                    r'\bchief exec\b'
                ],
                'founder': [
                    r'\bfounder\b',
                    r'\bco-founder\b',
                    r'\bco founder\b',
                    r'\bfounding\s+\w+\b'
                ],
                'managing_director': [
                    r'\bmanaging director\b',
                    r'\bmd\b',
                    r'\bmanaging dir\b'
                ],
                'owner': [
                    r'\bowner\b',
                    r'\bproprietor\b',
                    r'\bprincipal\b'
                ],
                'president': [
                    r'\bpresident\b',
                    r'\bpres\b'
                ]
            },
            'tier_2': {
                'director': [
                    r'\bdirector\b',
                    r'\bdir\b',
                    r'\bexecutive director\b',
                    r'\boperations director\b',
                    r'\bsales director\b'
                ],
                'head_of': [
                    r'\bhead of\b',
                    r'\bhead\s+\w+\b',
                    r'\bchief\s+\w+\b'
                ],
                'general_manager': [
                    r'\bgeneral manager\b',
                    r'\bgm\b',
                    r'\bgen manager\b'
                ],
                'vice_president': [
                    r'\bvice president\b',
                    r'\bvp\b',
                    r'\bv\.p\.\b'
                ]
            },
            'tier_3': {
                'manager': [
                    r'\bmanager\b',
                    r'\bmgr\b',
                    r'\bproject manager\b',
                    r'\barea manager\b'
                ],
                'senior': [
                    r'\bsenior\s+\w+\b',
                    r'\bsr\s+\w+\b',
                    r'\blead\s+\w+\b'
                ],
                'supervisor': [
                    r'\bsupervisor\b',
                    r'\bsuperintendent\b',
                    r'\bforeman\b'
                ]
            }
        }
    
    def _initialize_industry_contexts(self) -> Dict:
        """Initialize industry-specific contexts"""
        return {
            'plumbing': {
                'titles': ['plumber', 'master plumber', 'plumbing engineer'],
                'modifiers': ['master', 'certified', 'licensed']
            },
            'electrical': {
                'titles': ['electrician', 'electrical engineer', 'electrical contractor'],
                'modifiers': ['master', 'certified', 'licensed']
            },
            'construction': {
                'titles': ['contractor', 'builder', 'construction manager'],
                'modifiers': ['general', 'licensed', 'certified']
            },
            'heating': {
                'titles': ['heating engineer', 'hvac technician', 'boiler engineer'],
                'modifiers': ['certified', 'gas safe', 'qualified']
            },
            'roofing': {
                'titles': ['roofer', 'roofing contractor', 'roofing specialist'],
                'modifiers': ['certified', 'licensed', 'approved']
            }
        }
    
    def _initialize_seniority_weights(self) -> Dict:
        """Initialize seniority scoring weights"""
        return {
            'tier_1_keywords': {
                'ceo': 1.0, 'founder': 1.0, 'managing': 0.9, 'owner': 0.8,
                'president': 0.9, 'principal': 0.7, 'proprietor': 0.8
            },
            'tier_2_keywords': {
                'director': 0.8, 'head': 0.7, 'general': 0.6, 'vice': 0.7,
                'executive': 0.6, 'operations': 0.5, 'sales': 0.5
            },
            'tier_3_keywords': {
                'manager': 0.5, 'senior': 0.4, 'lead': 0.4, 'supervisor': 0.3,
                'foreman': 0.3, 'superintendent': 0.4
            }
        }
    
    def classify_title(self, title: str, company_context: str = "") -> TitleClassificationResult:
        """P3.1: Classify executive title with AI-powered analysis"""
        try:
            # Normalize title
            normalized = self._normalize_title(title)
            
            # Detect industry context
            industry = self._detect_industry_context(title, company_context)
            
            # Classify seniority level
            seniority, exec_type, confidence, features = self._classify_seniority(normalized, industry)
            
            return TitleClassificationResult(
                original_title=title,
                normalized_title=normalized,
                seniority_level=seniority,
                confidence=confidence,
                executive_type=exec_type,
                industry_context=industry,
                classification_features=features
            )
            
        except Exception as e:
            logger.warning(f"P3.1: Title classification failed for '{title}': {e}")
            return self._create_unknown_result(title)
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for classification"""
        if not title:
            return ""
        
        # Convert to lowercase
        normalized = title.lower().strip()
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = [
            r'^(the|a|an)\s+',
            r'^(mr|mrs|ms|dr|prof)\s+',
        ]
        
        suffixes_to_remove = [
            r'\s+(ltd|limited|plc|inc|corp)$',
            r'\s+(at|@)\s+.+$',  # Remove company names after @
        ]
        
        for prefix in prefixes_to_remove:
            normalized = re.sub(prefix, '', normalized)
        
        for suffix in suffixes_to_remove:
            normalized = re.sub(suffix, '', normalized)
        
        # Clean up whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _detect_industry_context(self, title: str, company_context: str) -> Optional[str]:
        """Detect industry context from title and company info"""
        combined_text = f"{title} {company_context}".lower()
        
        for industry, data in self.industry_contexts.items():
            # Check for industry-specific titles
            for industry_title in data['titles']:
                if industry_title in combined_text:
                    return industry
            
            # Check for industry modifiers
            for modifier in data['modifiers']:
                if modifier in combined_text and industry in combined_text:
                    return industry
        
        return None
    
    def _classify_seniority(self, title: str, industry: Optional[str]) -> Tuple[SeniorityLevel, str, float, Dict]:
        """Classify seniority level using pattern matching and scoring"""
        features = {
            'matched_patterns': [],
            'keyword_scores': {},
            'industry_boost': 0.0,
            'pattern_confidence': 0.0
        }
        
        best_tier = SeniorityLevel.UNKNOWN
        best_type = 'unknown'
        best_confidence = 0.0
        
        # Check each tier
        for tier_name, tier_patterns in self.title_patterns.items():
            tier_confidence = 0.0
            tier_type = 'unknown'
            
            for exec_type, patterns in tier_patterns.items():
                type_confidence = 0.0
                
                for pattern in patterns:
                    if re.search(pattern, title, re.IGNORECASE):
                        match_confidence = 0.8  # Base confidence for pattern match
                        type_confidence = max(type_confidence, match_confidence)
                        features['matched_patterns'].append(f"{tier_name}:{exec_type}:{pattern}")
                
                if type_confidence > tier_confidence:
                    tier_confidence = type_confidence
                    tier_type = exec_type
            
            # Add keyword-based scoring
            keyword_confidence = self._calculate_keyword_confidence(title, tier_name)
            tier_confidence = max(tier_confidence, keyword_confidence)
            
            if tier_confidence > best_confidence:
                best_confidence = tier_confidence
                best_tier = SeniorityLevel(tier_name) if tier_name != 'unknown' else SeniorityLevel.UNKNOWN
                best_type = tier_type
        
        # Industry-specific adjustments
        if industry:
            industry_boost = self._calculate_industry_boost(title, industry)
            best_confidence += industry_boost
            features['industry_boost'] = industry_boost
        
        # Ensure confidence is within bounds
        best_confidence = min(1.0, max(0.0, best_confidence))
        features['pattern_confidence'] = best_confidence
        
        return best_tier, best_type, best_confidence, features
    
    def _calculate_keyword_confidence(self, title: str, tier: str) -> float:
        """Calculate confidence based on keyword presence"""
        if tier not in self.seniority_weights:
            return 0.0
        
        max_confidence = 0.0
        keywords = self.seniority_weights[f"{tier}_keywords"]
        
        for keyword, weight in keywords.items():
            if keyword in title.lower():
                confidence = weight * 0.6  # Scale down keyword-only matches
                max_confidence = max(max_confidence, confidence)
        
        return max_confidence
    
    def _calculate_industry_boost(self, title: str, industry: str) -> float:
        """Calculate industry-specific confidence boost"""
        if industry not in self.industry_contexts:
            return 0.0
        
        boost = 0.0
        industry_data = self.industry_contexts[industry]
        
        # Check for industry titles
        for industry_title in industry_data['titles']:
            if industry_title in title.lower():
                boost += 0.1
        
        # Check for industry modifiers
        for modifier in industry_data['modifiers']:
            if modifier in title.lower():
                boost += 0.05
        
        return min(0.2, boost)  # Cap industry boost at 0.2
    
    def _create_unknown_result(self, title: str) -> TitleClassificationResult:
        """Create result for unknown/failed classification"""
        return TitleClassificationResult(
            original_title=title,
            normalized_title=title.lower(),
            seniority_level=SeniorityLevel.UNKNOWN,
            confidence=0.0,
            executive_type='unknown',
            industry_context=None,
            classification_features={'error': True}
        )
    
    def batch_classify_titles(self, titles: List[str], contexts: List[str] = None) -> List[TitleClassificationResult]:
        """Batch classify multiple titles"""
        if contexts is None:
            contexts = [""] * len(titles)
        
        results = []
        for i, title in enumerate(titles):
            context = contexts[i] if i < len(contexts) else ""
            result = self.classify_title(title, context)
            results.append(result)
        
        return results
    
    def get_classification_statistics(self) -> Dict:
        """Get classification statistics"""
        total_patterns = sum(
            len(patterns) for tier_patterns in self.title_patterns.values()
            for patterns in tier_patterns.values()
        )
        
        return {
            "total_patterns": total_patterns,
            "tier_1_patterns": sum(len(p) for p in self.title_patterns['tier_1'].values()),
            "tier_2_patterns": sum(len(p) for p in self.title_patterns['tier_2'].values()),
            "tier_3_patterns": sum(len(p) for p in self.title_patterns['tier_3'].values()),
            "industries_supported": len(self.industry_contexts),
            "keyword_weights": len(self.seniority_weights)
        }

# Test function
async def test_title_classifier():
    """Test the executive title classifier"""
    print("🎯 Testing P3.1 Executive Title Classifier...")
    
    classifier = ExecutiveTitleClassifier()
    
    test_cases = [
        ("Master Plumber", "Jack The Plumber"),
        ("CEO", "Tech Solutions Ltd"),
        ("Founder & Managing Director", "Birmingham Services"),
        ("Head of Operations", "Construction Company"),
        ("Senior Manager", "Electrical Services"),
        ("Plumbing Engineer", "Heating Solutions"),
        ("Director", "Professional Services"),
        ("Owner", "Local Business")
    ]
    
    for title, context in test_cases:
        result = classifier.classify_title(title, context)
        print(f"Title: '{title}' | Context: '{context}'")
        print(f"  → Normalized: '{result.normalized_title}'")
        print(f"  → Seniority: {result.seniority_level.value}")
        print(f"  → Type: {result.executive_type}")
        print(f"  → Confidence: {result.confidence:.2f}")
        print(f"  → Industry: {result.industry_context}")
        print()
    
    stats = classifier.get_classification_statistics()
    print(f"📊 Classification Statistics: {stats}")
    print("🎉 P3.1 Title Classifier test complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_title_classifier()) 