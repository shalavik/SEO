"""
Email Pattern Generator

Generates potential email combinations based on common patterns
used in business email addresses.
"""

import re
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass

@dataclass
class EmailPattern:
    """Email pattern definition"""
    name: str
    template: str
    confidence: float
    description: str

class EmailPatternGenerator:
    """Generate email address patterns and candidates"""
    
    def __init__(self):
        self.common_patterns = self._load_common_patterns()
        self.separator_chars = ['.', '-', '_', '']
        
    def _load_common_patterns(self) -> List[EmailPattern]:
        """Load common email patterns with confidence scores"""
        return [
            EmailPattern("first.last", "{first}.{last}@{domain}", 0.85, "First name dot last name"),
            EmailPattern("first_last", "{first}_{last}@{domain}", 0.75, "First name underscore last name"),
            EmailPattern("first-last", "{first}-{last}@{domain}", 0.70, "First name dash last name"),
            EmailPattern("firstlast", "{first}{last}@{domain}", 0.65, "First name last name concatenated"),
            EmailPattern("first", "{first}@{domain}", 0.60, "First name only"),
            EmailPattern("last.first", "{last}.{first}@{domain}", 0.55, "Last name dot first name"),
            EmailPattern("last_first", "{last}_{first}@{domain}", 0.50, "Last name underscore first name"),
            EmailPattern("last-first", "{last}-{first}@{domain}", 0.45, "Last name dash first name"),
            EmailPattern("lastfirst", "{last}{first}@{domain}", 0.40, "Last name first name concatenated"),
            EmailPattern("first.l", "{first}.{last_initial}@{domain}", 0.50, "First name dot last initial"),
            EmailPattern("first_l", "{first}_{last_initial}@{domain}", 0.45, "First name underscore last initial"),
            EmailPattern("f.last", "{first_initial}.{last}@{domain}", 0.45, "First initial dot last name"),
            EmailPattern("f_last", "{first_initial}_{last}@{domain}", 0.40, "First initial underscore last name"),
            EmailPattern("f.l", "{first_initial}.{last_initial}@{domain}", 0.30, "First initial dot last initial"),
            EmailPattern("f_l", "{first_initial}_{last_initial}@{domain}", 0.25, "First initial underscore last initial"),
            EmailPattern("last", "{last}@{domain}", 0.35, "Last name only"),
            EmailPattern("firstl", "{first}{last_initial}@{domain}", 0.35, "First name last initial"),
            EmailPattern("flast", "{first_initial}{last}@{domain}", 0.30, "First initial last name"),
        ]
    
    def generate_email_candidates(self, first_name: str, last_name: str, 
                                domain: str, include_all_patterns: bool = False) -> List[Dict]:
        """Generate email candidates based on name and domain"""
        if not first_name or not last_name or not domain:
            return []
        
        # Clean and normalize inputs
        first_clean = self._clean_name(first_name)
        last_clean = self._clean_name(last_name)
        domain_clean = self._clean_domain(domain)
        
        candidates = []
        seen_emails = set()
        
        # Generate from patterns
        for pattern in self.common_patterns:
            # Skip low confidence patterns unless requested
            if not include_all_patterns and pattern.confidence < 0.4:
                continue
                
            email = self._apply_pattern(pattern, first_clean, last_clean, domain_clean)
            if email and email not in seen_emails:
                candidates.append({
                    'email': email,
                    'pattern': pattern.name,
                    'confidence': pattern.confidence,
                    'description': pattern.description
                })
                seen_emails.add(email)
        
        # Sort by confidence
        candidates.sort(key=lambda x: x['confidence'], reverse=True)
        
        return candidates
    
    def generate_pattern_variations(self, base_pattern: str, first_name: str, 
                                  last_name: str, domain: str) -> List[str]:
        """Generate variations of a specific pattern"""
        first_clean = self._clean_name(first_name)
        last_clean = self._clean_name(last_name)
        domain_clean = self._clean_domain(domain)
        
        variations = []
        seen = set()
        
        # Try different separators
        for separator in self.separator_chars:
            # Try different case combinations
            for first_case in [first_clean.lower(), first_clean.capitalize()]:
                for last_case in [last_clean.lower(), last_clean.capitalize()]:
                    # Apply pattern variations
                    if 'first.last' in base_pattern:
                        email = f"{first_case}{separator}{last_case}@{domain_clean}"
                    elif 'first' in base_pattern and 'last' not in base_pattern:
                        email = f"{first_case}@{domain_clean}"
                    elif 'last' in base_pattern and 'first' not in base_pattern:
                        email = f"{last_case}@{domain_clean}"
                    else:
                        continue
                    
                    if email not in seen:
                        variations.append(email)
                        seen.add(email)
        
        return variations
    
    def discover_domain_patterns(self, known_emails: List[str], domain: str) -> List[Dict]:
        """Discover email patterns from known emails for a domain"""
        if not known_emails:
            return []
        
        pattern_counts = {}
        pattern_examples = {}
        
        for email in known_emails:
            if not self._is_valid_email_format(email):
                continue
                
            email_domain = email.split('@')[-1].lower()
            if email_domain != domain.lower():
                continue
            
            local_part = email.split('@')[0]
            detected_patterns = self._detect_patterns_in_email(local_part)
            
            for pattern_name in detected_patterns:
                pattern_counts[pattern_name] = pattern_counts.get(pattern_name, 0) + 1
                if pattern_name not in pattern_examples:
                    pattern_examples[pattern_name] = []
                if email not in pattern_examples[pattern_name]:
                    pattern_examples[pattern_name].append(email)
        
        # Calculate confidence based on frequency
        total_emails = len(known_emails)
        discovered_patterns = []
        
        for pattern_name, count in pattern_counts.items():
            confidence = min(count / total_emails, 1.0)
            pattern_info = self._get_pattern_info(pattern_name)
            
            discovered_patterns.append({
                'pattern': pattern_name,
                'confidence': confidence,
                'count': count,
                'examples': pattern_examples[pattern_name][:3],  # Limit examples
                'description': pattern_info.get('description', pattern_name)
            })
        
        # Sort by confidence
        discovered_patterns.sort(key=lambda x: x['confidence'], reverse=True)
        
        return discovered_patterns
    
    def _apply_pattern(self, pattern: EmailPattern, first: str, last: str, domain: str) -> str:
        """Apply a pattern template to generate an email"""
        try:
            email = pattern.template.format(
                first=first.lower(),
                last=last.lower(),
                first_initial=first[0].lower() if first else '',
                last_initial=last[0].lower() if last else '',
                domain=domain.lower()
            )
            return email if self._is_valid_email_format(email) else None
        except (IndexError, KeyError):
            return None
    
    def _clean_name(self, name: str) -> str:
        """Clean and normalize a name"""
        if not name:
            return ""
        
        # Remove special characters and spaces
        cleaned = re.sub(r'[^a-zA-Z]', '', name)
        return cleaned.strip()
    
    def _clean_domain(self, domain: str) -> str:
        """Clean and normalize a domain"""
        if not domain:
            return ""
        
        # Remove protocol and www
        domain = re.sub(r'^https?://', '', domain)
        domain = re.sub(r'^www\.', '', domain)
        
        # Remove path and query parameters
        domain = domain.split('/')[0]
        domain = domain.split('?')[0]
        
        return domain.lower().strip()
    
    def _is_valid_email_format(self, email: str) -> bool:
        """Basic email format validation"""
        if not email or '@' not in email:
            return False
        
        pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _detect_patterns_in_email(self, local_part: str) -> List[str]:
        """Detect patterns in an email local part"""
        detected = []
        
        # Look for common separators
        if '.' in local_part:
            parts = local_part.split('.')
            if len(parts) == 2:
                detected.append('first.last')
            elif len(parts) == 2 and len(parts[1]) == 1:
                detected.append('first.l')
            elif len(parts) == 2 and len(parts[0]) == 1:
                detected.append('f.last')
        
        if '_' in local_part:
            parts = local_part.split('_')
            if len(parts) == 2:
                detected.append('first_last')
        
        if '-' in local_part:
            parts = local_part.split('-')
            if len(parts) == 2:
                detected.append('first-last')
        
        # Check for concatenated patterns
        if not any(sep in local_part for sep in ['.', '_', '-']):
            if len(local_part) > 3:  # Likely concatenated names
                detected.append('firstlast')
            elif len(local_part) <= 3:  # Likely initials
                detected.append('f.l')
        
        # Single name patterns
        if len(local_part.split('.')) == 1 and len(local_part.split('_')) == 1:
            detected.append('first')  # Could be first or last
        
        return detected if detected else ['unknown']
    
    def _get_pattern_info(self, pattern_name: str) -> Dict:
        """Get information about a pattern"""
        for pattern in self.common_patterns:
            if pattern.name == pattern_name:
                return {
                    'template': pattern.template,
                    'confidence': pattern.confidence,
                    'description': pattern.description
                }
        
        return {
            'template': pattern_name,
            'confidence': 0.1,
            'description': f"Custom pattern: {pattern_name}"
        }
    
    def rank_email_candidates(self, candidates: List[str], domain_patterns: List[Dict]) -> List[Dict]:
        """Rank email candidates based on domain patterns"""
        if not domain_patterns:
            # Default ranking based on common patterns
            return [{'email': email, 'confidence': 0.5, 'rank': i+1} 
                   for i, email in enumerate(candidates)]
        
        ranked_candidates = []
        
        for email in candidates:
            local_part = email.split('@')[0]
            detected_patterns = self._detect_patterns_in_email(local_part)
            
            # Calculate confidence based on domain patterns
            max_confidence = 0.0
            for pattern_data in domain_patterns:
                if pattern_data['pattern'] in detected_patterns:
                    max_confidence = max(max_confidence, pattern_data['confidence'])
            
            ranked_candidates.append({
                'email': email,
                'confidence': max_confidence,
                'detected_patterns': detected_patterns
            })
        
        # Sort by confidence
        ranked_candidates.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Add rank
        for i, candidate in enumerate(ranked_candidates):
            candidate['rank'] = i + 1
        
        return ranked_candidates 