"""
Advanced Result Comparator - Component 3 of Comprehensive 20-URL Validation Project

This module implements sophisticated comparison logic between system-extracted executives
and manually verified reference data, using fuzzy matching algorithms for robust comparison.

Author: AI Assistant
Date: 2025-01-19
Project: SEO Lead Generation - Comprehensive Validation Framework
"""

import re
import difflib
import logging
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MatchType(Enum):
    """Types of matches between system and manual data."""
    EXACT_MATCH = "exact_match"
    STRONG_MATCH = "strong_match"
    PARTIAL_MATCH = "partial_match"
    WEAK_MATCH = "weak_match"
    NO_MATCH = "no_match"

@dataclass
class ComparisonResult:
    """Result of comparing a system executive with manual data."""
    system_executive: Dict[str, Any]
    manual_executive: Optional[Dict[str, Any]]
    match_type: MatchType
    overall_confidence: float
    field_scores: Dict[str, float]
    match_reasons: List[str]
    url: str

@dataclass
class URLComparisonResult:
    """Result of comparing all executives for a specific URL."""
    url: str
    system_executives: List[Dict[str, Any]]
    manual_executives: List[Dict[str, Any]]
    matches: List[ComparisonResult]
    missing_executives: List[Dict[str, Any]]
    false_positives: List[Dict[str, Any]]
    discovery_rate: float
    attribution_rate: float

class AdvancedResultComparator:
    """
    Sophisticated comparison engine between system results and manual reference data.
    
    Uses advanced fuzzy matching algorithms with name variation handling,
    email attribution validation, LinkedIn profile verification, and weighted scoring.
    """
    
    def __init__(self):
        """Initialize the Advanced Result Comparator."""
        # Field weights for overall confidence calculation
        self.field_weights = {
            'name': 0.35,      # Reduced due to variation handling
            'email': 0.35,     # Most reliable unique identifier
            'linkedin': 0.20,  # Professional verification
            'title': 0.10      # Context validation
        }
        
        # Name variation database for fuzzy matching
        self.name_variations = {
            'michael': ['mike', 'mick', 'mickey'],
            'michael/mike': ['michael', 'mike'],
            'edward': ['ed', 'eddie', 'eddy'],
            'edward/ed': ['edward', 'ed'],
            'douglas': ['doug', 'dougie'],
            'william': ['bill', 'billy', 'will', 'willie'],
            'robert': ['rob', 'bob', 'bobby', 'robbie'],
            'richard': ['rick', 'dick', 'richie'],
            'james': ['jim', 'jimmy', 'jamie'],
            'john': ['jack', 'johnny'],
            'anthony': ['tony', 'ant'],
            'christopher': ['chris', 'christie'],
            'matthew': ['matt', 'matty'],
            'andrew': ['andy', 'drew'],
            'daniel': ['dan', 'danny'],
            'david': ['dave', 'davey'],
            'joseph': ['joe', 'joey'],
            'charles': ['charlie', 'chuck'],
            'thomas': ['tom', 'tommy'],
            'nicholas': ['nick', 'nicky'],
            'benjamin': ['ben', 'benny'],
            'alexander': ['alex', 'lex'],
            'stephen': ['steve', 'stevie'],
            'timothy': ['tim', 'timmy'],
            'ronald': ['ron', 'ronnie'],
            'samuel': ['sam', 'sammy'],
            'gregory': ['greg', 'greggy'],
            'kenneth': ['ken', 'kenny'],
            'joshua': ['josh']
        }
        
        # Common title variations
        self.title_variations = {
            'owner': ['owner', 'business owner', 'company owner'],
            'president': ['president', 'pres', 'ceo', 'chief executive'],
            'director': ['director', 'dir', 'managing director'],
            'manager': ['manager', 'mgr', 'general manager'],
            'vice president': ['vice president', 'vp', 'v.p.', 'vice-president'],
            'co-owner': ['co-owner', 'co owner', 'coowner', 'joint owner'],
            'founder': ['founder', 'co-founder', 'cofounder']
        }
    
    def compare_executives(self, system_executives: List[Dict[str, Any]], 
                          manual_executives: List[Dict[str, Any]], 
                          url: str) -> URLComparisonResult:
        """
        Compare lists of executives from system vs manual data for a URL.
        
        Args:
            system_executives: List of executives found by our system
            manual_executives: List of manually verified executives
            url: Website URL being compared
            
        Returns:
            URLComparisonResult: Comprehensive comparison results
        """
        logger.info(f"Comparing executives for {url}: {len(system_executives)} system vs {len(manual_executives)} manual")
        
        matches = []
        used_manual_indices = set()
        
        # For each system executive, find best manual match
        for system_exec in system_executives:
            best_match = self._find_best_match(system_exec, manual_executives, used_manual_indices)
            matches.append(best_match)
            
            # Mark manual executive as used if it was a good match
            if (best_match.manual_executive and 
                best_match.match_type not in [MatchType.NO_MATCH, MatchType.WEAK_MATCH]):
                
                manual_index = manual_executives.index(best_match.manual_executive)
                used_manual_indices.add(manual_index)
        
        # Identify missing executives (manual executives not matched)
        missing_executives = [
            manual_executives[i] for i in range(len(manual_executives))
            if i not in used_manual_indices
        ]
        
        # Identify false positives (system executives with no good match)
        false_positives = [
            match.system_executive for match in matches
            if match.match_type in [MatchType.NO_MATCH, MatchType.WEAK_MATCH]
        ]
        
        # Calculate metrics
        discovery_rate = self._calculate_discovery_rate(matches, manual_executives)
        attribution_rate = self._calculate_attribution_rate(matches)
        
        return URLComparisonResult(
            url=url,
            system_executives=system_executives,
            manual_executives=manual_executives,
            matches=matches,
            missing_executives=missing_executives,
            false_positives=false_positives,
            discovery_rate=discovery_rate,
            attribution_rate=attribution_rate
        )
    
    def _find_best_match(self, system_exec: Dict[str, Any], 
                        manual_executives: List[Dict[str, Any]], 
                        used_indices: set) -> ComparisonResult:
        """
        Find the best matching manual executive for a system executive.
        
        Args:
            system_exec: System-extracted executive
            manual_executives: List of manual executives
            used_indices: Set of already-used manual executive indices
            
        Returns:
            ComparisonResult: Best match result
        """
        best_score = 0.0
        best_match = None
        best_field_scores = {}
        best_reasons = []
        
        for i, manual_exec in enumerate(manual_executives):
            if i in used_indices:
                continue
            
            # Calculate match score
            field_scores, reasons = self._calculate_match_scores(system_exec, manual_exec)
            overall_score = sum(score * self.field_weights.get(field, 0) 
                              for field, score in field_scores.items())
            
            if overall_score > best_score:
                best_score = overall_score
                best_match = manual_exec
                best_field_scores = field_scores
                best_reasons = reasons
        
        # Determine match type based on score
        match_type = self._determine_match_type(best_score, best_field_scores)
        
        return ComparisonResult(
            system_executive=system_exec,
            manual_executive=best_match,
            match_type=match_type,
            overall_confidence=best_score,
            field_scores=best_field_scores,
            match_reasons=best_reasons,
            url=system_exec.get('url', '')
        )
    
    def _calculate_match_scores(self, system_exec: Dict[str, Any], 
                               manual_exec: Dict[str, Any]) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate detailed match scores for all fields.
        
        Args:
            system_exec: System executive data
            manual_exec: Manual executive data
            
        Returns:
            Tuple of field scores dict and match reasons list
        """
        field_scores = {}
        reasons = []
        
        # Name matching
        name_score, name_reason = self._fuzzy_name_match(
            system_exec.get('name', ''), 
            manual_exec.get('full_name', '')
        )
        field_scores['name'] = name_score
        if name_reason:
            reasons.append(name_reason)
        
        # Email matching
        email_score, email_reason = self._exact_email_match(
            system_exec.get('email', ''), 
            manual_exec.get('email', '')
        )
        field_scores['email'] = email_score
        if email_reason:
            reasons.append(email_reason)
        
        # LinkedIn matching
        linkedin_score, linkedin_reason = self._linkedin_url_match(
            system_exec.get('linkedin_url', ''), 
            manual_exec.get('linkedin_url', '')
        )
        field_scores['linkedin'] = linkedin_score
        if linkedin_reason:
            reasons.append(linkedin_reason)
        
        # Title matching
        title_score, title_reason = self._fuzzy_title_match(
            system_exec.get('title', ''), 
            manual_exec.get('title', '')
        )
        field_scores['title'] = title_score
        if title_reason:
            reasons.append(title_reason)
        
        return field_scores, reasons
    
    def _fuzzy_name_match(self, name1: str, name2: str) -> Tuple[float, str]:
        """
        Advanced name matching with variation handling.
        
        Args:
            name1: First name to compare
            name2: Second name to compare
            
        Returns:
            Tuple of match score (0.0-1.0) and reason string
        """
        if not name1 or not name2:
            return 0.0, ""
        
        # Normalize names
        n1_parts = self._normalize_name(name1)
        n2_parts = self._normalize_name(name2)
        
        # Check for exact match
        if n1_parts == n2_parts:
            return 1.0, f"Exact name match: {name1} = {name2}"
        
        # Check for known variations
        variation_score = self._check_name_variations(n1_parts, n2_parts)
        if variation_score > 0.8:
            return variation_score, f"Name variation match: {name1} ≈ {name2}"
        
        # Fuzzy matching with multiple algorithms
        jaro_score = self._jaro_winkler_similarity(name1.lower(), name2.lower())
        levenshtein_score = 1 - (self._levenshtein_distance(name1.lower(), name2.lower()) / max(len(name1), len(name2)))
        
        # Sequence matching for better word-level comparison
        sequence_score = difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
        
        # Take best score
        best_score = max(jaro_score, levenshtein_score, sequence_score, variation_score)
        
        if best_score > 0.6:
            return best_score, f"Fuzzy name match: {name1} ≈ {name2} (score: {best_score:.2f})"
        
        return best_score, ""
    
    def _normalize_name(self, name: str) -> List[str]:
        """
        Normalize a name into component parts.
        
        Args:
            name: Name string to normalize
            
        Returns:
            List of normalized name parts
        """
        if not name:
            return []
        
        # Remove special characters and normalize spacing
        normalized = re.sub(r'[^\w\s/-]', '', name.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Split into parts
        parts = normalized.split()
        
        # Handle slash-separated names like "Michael/Mike"
        expanded_parts = []
        for part in parts:
            if '/' in part:
                expanded_parts.extend(part.split('/'))
            else:
                expanded_parts.append(part)
        
        return [p.strip() for p in expanded_parts if p.strip()]
    
    def _check_name_variations(self, parts1: List[str], parts2: List[str]) -> float:
        """
        Check for known name variations between two name part lists.
        
        Args:
            parts1: First name parts
            parts2: Second name parts
            
        Returns:
            Variation match score (0.0-1.0)
        """
        if not parts1 or not parts2:
            return 0.0
        
        matched_parts = 0
        total_parts = max(len(parts1), len(parts2))
        
        for part1 in parts1:
            for part2 in parts2:
                # Check direct match
                if part1 == part2:
                    matched_parts += 1
                    continue
                
                # Check variation database
                for canonical, variations in self.name_variations.items():
                    if (part1 in variations and part2 in variations) or \
                       (part1 == canonical and part2 in variations) or \
                       (part2 == canonical and part1 in variations):
                        matched_parts += 1
                        break
        
        return min(matched_parts / total_parts, 1.0)
    
    def _exact_email_match(self, email1: str, email2: str) -> Tuple[float, str]:
        """
        Email matching with domain validation.
        
        Args:
            email1: First email to compare
            email2: Second email to compare
            
        Returns:
            Tuple of match score (0.0-1.0) and reason string
        """
        if not email1 or not email2:
            return 0.0, ""
        
        # Exact match gets full score
        if email1.lower() == email2.lower():
            return 1.0, f"Exact email match: {email1}"
        
        # Check domain similarity for partial credit
        try:
            domain1 = email1.split('@')[-1].lower() if '@' in email1 else ''
            domain2 = email2.split('@')[-1].lower() if '@' in email2 else ''
            
            if domain1 and domain2 and domain1 == domain2:
                return 0.3, f"Same domain: {domain1}"
        except:
            pass
        
        return 0.0, ""
    
    def _linkedin_url_match(self, url1: str, url2: str) -> Tuple[float, str]:
        """
        LinkedIn URL matching with profile ID extraction.
        
        Args:
            url1: First LinkedIn URL
            url2: Second LinkedIn URL
            
        Returns:
            Tuple of match score (0.0-1.0) and reason string
        """
        if not url1 or not url2:
            return 0.0, ""
        
        # Extract profile identifiers
        profile1 = self._extract_linkedin_profile_id(url1)
        profile2 = self._extract_linkedin_profile_id(url2)
        
        if profile1 and profile2:
            if profile1 == profile2:
                return 1.0, f"Exact LinkedIn match: {profile1}"
            
            # Check for similar profile names using fuzzy matching
            similarity = difflib.SequenceMatcher(None, profile1, profile2).ratio()
            if similarity > 0.8:
                return similarity, f"Similar LinkedIn profiles: {profile1} ≈ {profile2}"
        
        return 0.0, ""
    
    def _extract_linkedin_profile_id(self, url: str) -> str:
        """
        Extract LinkedIn profile identifier from URL.
        
        Args:
            url: LinkedIn URL
            
        Returns:
            Profile identifier string
        """
        if not url or 'linkedin.com' not in url.lower():
            return ""
        
        # Extract profile name from URL
        # Examples: /in/mike-cozad-41314834/ -> mike-cozad-41314834
        match = re.search(r'/in/([^/?]+)', url)
        if match:
            return match.group(1).rstrip('/')
        
        return ""
    
    def _fuzzy_title_match(self, title1: str, title2: str) -> Tuple[float, str]:
        """
        Title matching with business role understanding.
        
        Args:
            title1: First title to compare
            title2: Second title to compare
            
        Returns:
            Tuple of match score (0.0-1.0) and reason string
        """
        if not title1 or not title2:
            return 0.0, ""
        
        t1_normalized = title1.lower().strip()
        t2_normalized = title2.lower().strip()
        
        # Exact match
        if t1_normalized == t2_normalized:
            return 1.0, f"Exact title match: {title1}"
        
        # Check title variations
        for canonical, variations in self.title_variations.items():
            if (t1_normalized in variations and t2_normalized in variations) or \
               (t1_normalized == canonical and t2_normalized in variations) or \
               (t2_normalized == canonical and t1_normalized in variations):
                return 0.9, f"Title variation match: {title1} ≈ {title2}"
        
        # Fuzzy matching
        similarity = difflib.SequenceMatcher(None, t1_normalized, t2_normalized).ratio()
        if similarity > 0.6:
            return similarity, f"Fuzzy title match: {title1} ≈ {title2} (score: {similarity:.2f})"
        
        return 0.0, ""
    
    def _determine_match_type(self, overall_score: float, field_scores: Dict[str, float]) -> MatchType:
        """
        Determine match type based on overall score and field scores.
        
        Args:
            overall_score: Overall confidence score
            field_scores: Individual field scores
            
        Returns:
            MatchType: Classification of match quality
        """
        name_score = field_scores.get('name', 0.0)
        email_score = field_scores.get('email', 0.0)
        
        if overall_score >= 0.9 or (name_score >= 0.9 and email_score >= 0.9):
            return MatchType.EXACT_MATCH
        elif overall_score >= 0.7 or (name_score >= 0.8 and email_score >= 0.3):
            return MatchType.STRONG_MATCH
        elif overall_score >= 0.5 or name_score >= 0.6:
            return MatchType.PARTIAL_MATCH
        elif overall_score >= 0.3:
            return MatchType.WEAK_MATCH
        else:
            return MatchType.NO_MATCH
    
    def _calculate_discovery_rate(self, matches: List[ComparisonResult], 
                                 manual_executives: List[Dict[str, Any]]) -> float:
        """
        Calculate the discovery rate (how many manual executives were found).
        
        Args:
            matches: List of comparison results
            manual_executives: List of manual executives
            
        Returns:
            Discovery rate as percentage (0.0-100.0)
        """
        if not manual_executives:
            return 100.0
        
        good_matches = sum(1 for match in matches 
                          if match.match_type not in [MatchType.NO_MATCH, MatchType.WEAK_MATCH])
        
        return (good_matches / len(manual_executives)) * 100.0
    
    def _calculate_attribution_rate(self, matches: List[ComparisonResult]) -> float:
        """
        Calculate the contact attribution rate for found executives.
        
        Args:
            matches: List of comparison results
            
        Returns:
            Attribution rate as percentage (0.0-100.0)
        """
        good_matches = [match for match in matches 
                       if match.match_type not in [MatchType.NO_MATCH, MatchType.WEAK_MATCH]]
        
        if not good_matches:
            return 0.0
        
        with_contact = sum(1 for match in good_matches
                          if match.system_executive.get('email') or 
                             match.system_executive.get('phone'))
        
        return (with_contact / len(good_matches)) * 100.0
    
    # Helper methods for fuzzy string matching
    
    def _jaro_winkler_similarity(self, s1: str, s2: str) -> float:
        """Calculate Jaro-Winkler similarity between two strings."""
        if not s1 or not s2:
            return 0.0
        
        if s1 == s2:
            return 1.0
        
        len1, len2 = len(s1), len(s2)
        max_dist = (max(len1, len2) // 2) - 1
        
        if max_dist < 1:
            return 1.0 if s1 == s2 else 0.0
        
        # Find matches
        matches1 = [False] * len1
        matches2 = [False] * len2
        matches = 0
        transpositions = 0
        
        # Identify matches
        for i in range(len1):
            start = max(0, i - max_dist)
            end = min(i + max_dist + 1, len2)
            
            for j in range(start, end):
                if matches2[j] or s1[i] != s2[j]:
                    continue
                matches1[i] = matches2[j] = True
                matches += 1
                break
        
        if matches == 0:
            return 0.0
        
        # Count transpositions
        k = 0
        for i in range(len1):
            if not matches1[i]:
                continue
            while not matches2[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1
        
        jaro = (matches/len1 + matches/len2 + (matches - transpositions/2)/matches) / 3.0
        
        # Apply Winkler prefix scaling
        prefix = 0
        for i in range(min(len1, len2, 4)):
            if s1[i] == s2[i]:
                prefix += 1
            else:
                break
        
        return jaro + (0.1 * prefix * (1 - jaro))
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]


def main():
    """Test the Advanced Result Comparator."""
    # Test data
    system_executives = [
        {
            'name': 'Mike Cozad',
            'title': 'Owner',
            'email': 'mcozad@advairac.com',
            'linkedin_url': 'https://www.linkedin.com/in/mike-cozad-41314834/',
            'url': 'http://anhplumbing.com'
        }
    ]
    
    manual_executives = [
        {
            'full_name': 'Michael/Mike Cozad',
            'title': 'Owner/President',
            'email': 'mcozad@advairac.com',
            'linkedin_url': 'https://www.linkedin.com/in/mike-cozad-41314834/',
            'source': 'manual_verification'
        }
    ]
    
    # Test comparison
    comparator = AdvancedResultComparator()
    result = comparator.compare_executives(system_executives, manual_executives, 'http://anhplumbing.com')
    
    print("\n=== ADVANCED RESULT COMPARATOR TEST ===")
    print(f"URL: {result.url}")
    print(f"Discovery Rate: {result.discovery_rate:.1f}%")
    print(f"Attribution Rate: {result.attribution_rate:.1f}%")
    print(f"Matches: {len(result.matches)}")
    print(f"Missing: {len(result.missing_executives)}")
    print(f"False Positives: {len(result.false_positives)}")
    
    for i, match in enumerate(result.matches):
        print(f"\nMatch {i+1}:")
        print(f"  Type: {match.match_type.value}")
        print(f"  Confidence: {match.overall_confidence:.3f}")
        print(f"  Field Scores: {match.field_scores}")
        print(f"  Reasons: {match.match_reasons}")
    
    print("\n✅ Advanced Result Comparator test completed!")


if __name__ == "__main__":
    main() 