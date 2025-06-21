"""
Enhanced Executive Seniority Analyzer - Phase 5B Enhancement
Identifies executive titles and seniority levels with UK-specific patterns and context analysis.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TitleAnalysisResult:
    """Result of executive title analysis"""
    extracted_title: str
    seniority_tier: str
    confidence: float
    decision_maker: bool
    authority_level: int  # 1-10 scale
    extraction_method: str
    context: str

@dataclass
class SeniorityAnalysisResult:
    """Complete seniority analysis for all executives"""
    executives_analyzed: int
    titles_extracted: int
    decision_makers_identified: int
    tier_distribution: Dict[str, int]
    average_confidence: float
    extraction_success_rate: float

class ExecutiveSeniorityAnalyzer:
    """
    Enhanced executive seniority analyzer that identifies titles and authority levels
    using UK-specific business title patterns and context analysis.
    
    Phase 5B Enhancements:
    - UK-specific executive title recognition
    - Context-based title extraction
    - Improved seniority tier classification  
    - Decision maker identification with authority scoring
    - Title confidence scoring
    """
    
    def __init__(self):
        """Initialize analyzer with UK executive title patterns"""
        
        # UK Executive Title Hierarchy (Tier 1 = Highest Authority)
        self.uk_executive_titles = {
            'tier_1': {
                # Highest Authority - Ultimate Decision Makers
                'titles': [
                    'chief executive officer', 'ceo', 'managing director', 'md',
                    'executive director', 'founder', 'co-founder', 'owner', 'proprietor',
                    'chairman', 'chairwoman', 'chair', 'president', 'chief operating officer',
                    'coo', 'chief financial officer', 'cfo', 'chief technology officer',
                    'cto', 'chief marketing officer', 'cmo', 'director and owner',
                    'managing partner', 'senior partner', 'principal'
                ],
                'authority_level': 10,
                'decision_maker': True
            },
            'tier_2': {
                # Senior Management - High Authority
                'titles': [
                    'director', 'associate director', 'deputy director', 'assistant director',
                    'general manager', 'operations manager', 'business manager',
                    'regional manager', 'area manager', 'branch manager', 'head of',
                    'department manager', 'senior manager', 'project manager',
                    'business development manager', 'sales manager', 'marketing manager',
                    'finance manager', 'operations director', 'commercial director',
                    'technical director', 'sales director', 'marketing director',
                    'business development director', 'head of operations', 'head of sales',
                    'head of marketing', 'head of finance', 'head of hr', 'head of it'
                ],
                'authority_level': 7,
                'decision_maker': True
            },
            'tier_3': {
                # Middle Management - Moderate Authority
                'titles': [
                    'manager', 'senior manager', 'assistant manager', 'deputy manager',
                    'team manager', 'department head', 'section manager', 'supervisor',
                    'senior supervisor', 'team leader', 'team lead', 'senior team leader',
                    'project leader', 'senior', 'senior specialist', 'principal consultant',
                    'lead consultant', 'senior consultant', 'coordinator', 'administrator',
                    'senior administrator', 'officer', 'senior officer', 'analyst',
                    'senior analyst', 'specialist', 'senior specialist'
                ],
                'authority_level': 4,
                'decision_maker': False
            }
        }
        
        # Title extraction patterns (UK-specific contexts)
        self.title_patterns = [
            # Direct title assignments
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)[,\s]*[-–—]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            
            # Title: Name format
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)[:\s]*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            
            # Name, Title format
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)[,\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            
            # "Name is/was Title" format
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)[,\s]+(is|was)\s+(?:our|the|a)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            
            # "Title Name" format
            r'((?:Managing\s+)?(?:Executive\s+)?(?:Chief\s+)?(?:Senior\s+)?(?:Assistant\s+)?(?:Deputy\s+)?Director|Manager|CEO|MD|Chairman|Founder|Owner|Head\s+of\s+\w+)[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            
            # Company role descriptions
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)[,\s]+(?:who\s+is|serves\s+as|works\s+as)\s+(?:our|the|a)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        # Context indicators for title validation
        self.title_context_indicators = {
            'strong': [
                'managing director', 'executive director', 'ceo', 'founder', 'owner',
                'chairman', 'head of', 'director of', 'manager of'
            ],
            'medium': [
                'manager', 'director', 'supervisor', 'coordinator', 'administrator',
                'specialist', 'consultant', 'analyst', 'officer'
            ],
            'weak': [
                'team', 'senior', 'lead', 'principal', 'assistant', 'deputy'
            ]
        }
        
        # UK business context terms
        self.uk_business_terms = [
            'ltd', 'limited', 'plc', 'company', 'business', 'firm', 'enterprise',
            'services', 'solutions', 'group', 'holdings', 'partnership', 'associates'
        ]

    def analyze_executive_seniority(self, executives: List[Dict[str, Any]], 
                                  content: str = "") -> SeniorityAnalysisResult:
        """
        Analyze seniority levels for all executives.
        
        Args:
            executives: List of executive dictionaries with name and context
            content: Full website content for additional context
            
        Returns:
            SeniorityAnalysisResult with analysis statistics
        """
        logger.info(f"Analyzing seniority for {len(executives)} executives")
        
        analyzed_executives = []
        titles_extracted = 0
        decision_makers = 0
        tier_distribution = {'tier_1': 0, 'tier_2': 0, 'tier_3': 0}
        total_confidence = 0.0
        
        for executive in executives:
            name = executive.get('name', '')
            existing_title = executive.get('title', 'Unknown')
            context = executive.get('context', content)
            
            if not name:
                continue
            
            # Extract and analyze title
            title_result = self.extract_executive_title(name, existing_title, context)
            
            # Update executive with enhanced title information
            enhanced_executive = executive.copy()
            enhanced_executive.update({
                'title': title_result.extracted_title,
                'seniority_tier': title_result.seniority_tier,
                'decision_maker': title_result.decision_maker,
                'authority_level': title_result.authority_level,
                'title_confidence': title_result.confidence,
                'title_extraction_method': title_result.extraction_method
            })
            
            analyzed_executives.append(enhanced_executive)
            
            # Update statistics
            if title_result.extracted_title != 'Unknown':
                titles_extracted += 1
            
            if title_result.decision_maker:
                decision_makers += 1
            
            tier_distribution[title_result.seniority_tier] += 1
            total_confidence += title_result.confidence
        
        # Calculate metrics
        success_rate = (titles_extracted / len(executives)) if executives else 0
        avg_confidence = (total_confidence / len(executives)) if executives else 0
        
        result = SeniorityAnalysisResult(
            executives_analyzed=len(executives),
            titles_extracted=titles_extracted,
            decision_makers_identified=decision_makers,
            tier_distribution=tier_distribution,
            average_confidence=avg_confidence,
            extraction_success_rate=success_rate
        )
        
        logger.info(f"Seniority analysis complete: {titles_extracted}/{len(executives)} titles extracted, {decision_makers} decision makers identified")
        
        return result

    def extract_executive_title(self, name: str, existing_title: str = "Unknown", 
                               context: str = "") -> TitleAnalysisResult:
        """
        Extract executive title from context with enhanced UK patterns.
        
        Args:
            name: Executive name
            existing_title: Previously extracted title (if any)
            context: Text context containing potential title information
            
        Returns:
            TitleAnalysisResult with extracted title and analysis
        """
        # If we already have a good title, analyze it
        if existing_title and existing_title != "Unknown":
            tier_info = self._classify_title_tier(existing_title)
            return TitleAnalysisResult(
                extracted_title=existing_title,
                seniority_tier=tier_info['tier'],
                confidence=0.8,  # High confidence for pre-extracted titles
                decision_maker=tier_info['decision_maker'],
                authority_level=tier_info['authority_level'],
                extraction_method='pre_extracted',
                context=context[:100]
            )
        
        # Try to extract title from context
        extracted_title = self._extract_title_from_context(name, context)
        
        if extracted_title and extracted_title != "Unknown":
            tier_info = self._classify_title_tier(extracted_title)
            confidence = self._calculate_title_confidence(extracted_title, name, context)
            
            return TitleAnalysisResult(
                extracted_title=extracted_title,
                seniority_tier=tier_info['tier'],
                confidence=confidence,
                decision_maker=tier_info['decision_maker'],
                authority_level=tier_info['authority_level'],
                extraction_method='context_extraction',
                context=context[:100]
            )
        
        # Fallback: classify existing title or return default
        fallback_title = existing_title if existing_title != "Unknown" else "Staff Member"
        tier_info = self._classify_title_tier(fallback_title)
        
        return TitleAnalysisResult(
            extracted_title=fallback_title,
            seniority_tier='tier_3',  # Default to lowest tier
            confidence=0.2,  # Low confidence for fallback
            decision_maker=False,
            authority_level=1,
            extraction_method='fallback',
            context=context[:100]
        )

    def _extract_title_from_context(self, name: str, context: str) -> Optional[str]:
        """Extract title from context using pattern matching"""
        if not context:
            return None
        
        # Try each title pattern
        for pattern in self.title_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    candidate_name = match[0].strip()
                    candidate_title = match[-1].strip()  # Last item is usually the title
                    
                    # Check if the name matches our target executive
                    if self._names_match(name, candidate_name):
                        # Validate the title
                        if self._is_valid_title(candidate_title):
                            return candidate_title
        
        # Try simpler proximity-based extraction
        return self._extract_title_by_proximity(name, context)

    def _extract_title_by_proximity(self, name: str, context: str) -> Optional[str]:
        """Extract title based on proximity to name in context"""
        # Find name position in context
        name_pattern = re.escape(name)
        name_match = re.search(name_pattern, context, re.IGNORECASE)
        
        if not name_match:
            return None
        
        name_start = name_match.start()
        name_end = name_match.end()
        
        # Look for titles in surrounding text (100 chars each side)
        search_start = max(0, name_start - 100)
        search_end = min(len(context), name_end + 100)
        search_area = context[search_start:search_end]
        
        # Find potential titles in search area
        for tier_name, tier_data in self.uk_executive_titles.items():
            for title in tier_data['titles']:
                title_pattern = r'\b' + re.escape(title) + r'\b'
                if re.search(title_pattern, search_area, re.IGNORECASE):
                    return title.title()  # Return with proper capitalization
        
        return None

    def _names_match(self, target_name: str, candidate_name: str) -> bool:
        """Check if two names refer to the same person"""
        target_clean = re.sub(r'[^a-zA-Z\s]', '', target_name.lower()).strip()
        candidate_clean = re.sub(r'[^a-zA-Z\s]', '', candidate_name.lower()).strip()
        
        # Exact match
        if target_clean == candidate_clean:
            return True
        
        # Check if all words from target are in candidate or vice versa
        target_words = set(target_clean.split())
        candidate_words = set(candidate_clean.split())
        
        # Names match if they share at least 2 words (first name + last name)
        common_words = target_words.intersection(candidate_words)
        return len(common_words) >= 2

    def _is_valid_title(self, title: str) -> bool:
        """Validate if extracted string is a valid executive title"""
        title_lower = title.lower().strip()
        
        # Check against known title patterns
        for tier_data in self.uk_executive_titles.values():
            for known_title in tier_data['titles']:
                if known_title in title_lower or title_lower in known_title:
                    return True
        
        # Check for common title words
        title_words = ['director', 'manager', 'ceo', 'cfo', 'cto', 'head', 'chief', 
                      'senior', 'lead', 'coordinator', 'supervisor', 'officer']
        
        for word in title_words:
            if word in title_lower:
                return True
        
        # Reject if it's clearly not a title
        invalid_indicators = ['ltd', 'limited', 'company', 'plc', 'services', 'street', 
                             'road', 'avenue', 'telephone', 'email', 'website']
        
        for invalid in invalid_indicators:
            if invalid in title_lower:
                return False
        
        # Must be reasonable length for a title
        if len(title) < 3 or len(title) > 50:
            return False
        
        return True

    def _classify_title_tier(self, title: str) -> Dict[str, Any]:
        """Classify title into seniority tier and authority level"""
        title_lower = title.lower().strip()
        
        # Check each tier
        for tier_name, tier_data in self.uk_executive_titles.items():
            for known_title in tier_data['titles']:
                if known_title in title_lower:
                    return {
                        'tier': tier_name,
                        'decision_maker': tier_data['decision_maker'],
                        'authority_level': tier_data['authority_level']
                    }
        
        # Default classification for unknown titles
        return {
            'tier': 'tier_3',
            'decision_maker': False,
            'authority_level': 2
        }

    def _calculate_title_confidence(self, title: str, name: str, context: str) -> float:
        """Calculate confidence score for extracted title"""
        confidence = 0.0
        title_lower = title.lower()
        context_lower = context.lower()
        
        # Base confidence for known titles
        for tier_data in self.uk_executive_titles.values():
            for known_title in tier_data['titles']:
                if known_title in title_lower:
                    confidence += 0.6
                    break
        
        # Context validation
        context_strength = self._assess_context_strength(title, context)
        confidence += context_strength * 0.3
        
        # Proximity to name
        name_index = context_lower.find(name.lower())
        title_index = context_lower.find(title_lower)
        
        if name_index != -1 and title_index != -1:
            distance = abs(name_index - title_index)
            if distance < 50:
                confidence += 0.2
            elif distance < 100:
                confidence += 0.1
        
        return min(confidence, 1.0)

    def _assess_context_strength(self, title: str, context: str) -> float:
        """Assess strength of context for title validation"""
        title_lower = title.lower()
        context_lower = context.lower()
        
        strength = 0.0
        
        # Strong context indicators
        for indicator in self.title_context_indicators['strong']:
            if indicator in context_lower:
                strength += 0.4
                break
        
        # Medium context indicators
        for indicator in self.title_context_indicators['medium']:
            if indicator in context_lower:
                strength += 0.2
                break
        
        # Business context
        business_terms_found = sum(1 for term in self.uk_business_terms if term in context_lower)
        strength += min(business_terms_found * 0.1, 0.2)
        
        return min(strength, 1.0)

    def classify_decision_maker(self, title: str, seniority_tier: str) -> bool:
        """Determine if executive is a decision maker based on title and tier"""
        title_lower = title.lower()
        
        # Tier 1 and Tier 2 are generally decision makers
        if seniority_tier in ['tier_1', 'tier_2']:
            return True
        
        # Some Tier 3 roles can be decision makers
        decision_making_keywords = [
            'head', 'lead', 'principal', 'senior manager', 'department manager',
            'project manager', 'business manager'
        ]
        
        for keyword in decision_making_keywords:
            if keyword in title_lower:
                return True
        
        return False

    def get_seniority_summary(self, analysis_result: SeniorityAnalysisResult) -> Dict[str, Any]:
        """Generate summary of seniority analysis"""
        total = analysis_result.executives_analyzed
        
        return {
            'executives_analyzed': total,
            'titles_extracted': analysis_result.titles_extracted,
            'title_extraction_rate': (analysis_result.titles_extracted / total * 100) if total > 0 else 0,
            'decision_makers_identified': analysis_result.decision_makers_identified,
            'decision_maker_rate': (analysis_result.decision_makers_identified / total * 100) if total > 0 else 0,
            'tier_distribution': analysis_result.tier_distribution,
            'tier_1_percentage': (analysis_result.tier_distribution['tier_1'] / total * 100) if total > 0 else 0,
            'tier_2_percentage': (analysis_result.tier_distribution['tier_2'] / total * 100) if total > 0 else 0,
            'tier_3_percentage': (analysis_result.tier_distribution['tier_3'] / total * 100) if total > 0 else 0,
            'average_confidence': analysis_result.average_confidence,
            'extraction_success_rate': analysis_result.extraction_success_rate * 100
        } 