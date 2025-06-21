"""
Semantic Name Extractor - Advanced Human Name Recognition
Replaces flawed regex approach with semantic validation using UK databases
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class NameCandidate:
    """Represents a potential human name with validation metadata"""
    text: str
    confidence: float
    validation_reasons: List[str]
    context: str
    position: int

class SemanticNameExtractor:
    """
    Advanced semantic name extraction using UK name databases and context analysis.
    Replaces regex pattern matching with intelligent name recognition.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # UK Census Data - Most common first names
        self.uk_first_names = {
            'james', 'john', 'robert', 'michael', 'david', 'william', 'richard', 'thomas',
            'christopher', 'daniel', 'paul', 'mark', 'steven', 'andrew', 'peter',
            'joshua', 'kenneth', 'kevin', 'brian', 'george', 'timothy', 'ronald', 'jason',
            'edward', 'ryan', 'jacob', 'gary', 'nicholas', 'eric', 'jonathan',
            'stephen', 'larry', 'justin', 'scott', 'brandon', 'benjamin', 'samuel', 'frank',
            'matthew', 'anthony', 'alexander', 'patrick', 'jack', 'dennis', 'jerry', 'tyler',
            'aaron', 'henry', 'douglas', 'nathaniel', 'zachary', 'noah', 'adam',
            'arthur', 'austin', 'walter', 'harold', 'sean', 'carl', 'albert',
            'wayne', 'louis', 'ralph', 'roy', 'eugene', 'philip', 'nathan',
            'simon', 'oliver', 'harry', 'charlie', 'lewis', 'isaac', 'oscar', 'alfie',
            'archie', 'max', 'theo', 'freddie', 'finley', 'ethan', 'logan',
            'muhammad', 'harrison', 'sebastian', 'mason', 'reuben', 'riley', 'kai',
            'mary', 'patricia', 'jennifer', 'linda', 'elizabeth', 'barbara', 'susan',
            'jessica', 'sarah', 'karen', 'lisa', 'nancy', 'betty', 'helen', 'sandra',
            'donna', 'carol', 'ruth', 'sharon', 'michelle', 'laura', 'kimberly',
            'deborah', 'dorothy', 'emily', 'amy', 'angela', 'brenda', 'emma', 'olivia',
            'cynthia', 'marie', 'janet', 'catherine', 'frances', 'christine', 'samantha',
            'debra', 'rachel', 'carolyn', 'virginia', 'maria', 'heather', 'diane',
            'julie', 'joyce', 'victoria', 'kelly', 'christina', 'joan', 'evelyn',
            'lauren', 'judith', 'megan', 'cheryl', 'andrea', 'hannah', 'jacqueline',
            'martha', 'gloria', 'teresa', 'sara', 'janice', 'julia', 'kathryn',
            'anne', 'alice', 'louise', 'grace', 'sophie', 'lily', 'ruby', 'chloe',
            'charlotte', 'mia', 'lucy', 'amelia', 'ella', 'evie', 'ava', 'poppy',
            'isabelle', 'freya', 'zoe', 'phoebe', 'millie'
        }
        
        # UK Surnames - Common British surnames (expanded for better coverage)
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
            'holmes', 'rogers', 'stevens', 'walsh', 'hunter', 'thomson', 'matthews',
            'ross', 'owen', 'mason', 'knight', 'kennedy', 'butler', 'saunders', 'hope',
            # Additional surnames found in plumbing/heating businesses
            'riley', 'mcmanus', 'nunn', 'andrews', 'clarke', 'kelly', 'riley', 'mccann',
            'davidson', 'fletcher', 'gordon', 'hamilton', 'henderson', 'lawson', 'mcdonald',
            'morrison', 'newman', 'paterson', 'simpson', 'watts', 'wells', 'armstrong',
            'barker', 'bishop', 'black', 'butler', 'cameron', 'carroll', 'ferguson',
            'gibson', 'grant', 'harvey', 'hayes', 'johnston', 'jordan', 'shaw'
        }
        
        # Service terms to exclude (not human names) - EXPANDED
        self.service_exclusions = {
            'plumbing', 'electrical', 'heating', 'boiler', 'installation', 'repair',
            'maintenance', 'emergency', 'commercial', 'residential', 'domestic',
            'services', 'solutions', 'company', 'limited', 'contractors', 'specialists',
            'call', 'contact', 'email', 'phone', 'click', 'book', 'schedule',
            'request', 'quote', 'estimate', 'free', 'today', 'now', 'hours',
            # Business terms that are not names
            'price', 'guarantee', 'quality', 'service', 'professional', 'reliable',
            'fast', 'quick', 'best', 'top', 'leading', 'certified', 'licensed',
            'insured', 'experienced', 'trusted', 'expert', 'skilled', 'qualified',
            # Common false positives
            'low price', 'high quality', 'best service', 'top rated', 'free estimate'
        }
        
        # Business/marketing terms that often get mistaken for names
        self.marketing_terms = {
            'low', 'high', 'best', 'top', 'great', 'excellent', 'amazing', 'outstanding',
            'premium', 'deluxe', 'standard', 'basic', 'advanced', 'professional',
            'certified', 'licensed', 'approved', 'registered', 'accredited'
        }
        
        # Executive context indicators (boost confidence)
        self.executive_contexts = {
            'director', 'manager', 'ceo', 'founder', 'owner', 'head', 'chief'
        }
        
        # Common name patterns
        self.name_pattern = re.compile(r'\b[A-Z][a-z]{1,15}\s+[A-Z][a-z]{1,20}\b')
        
        # Common UK nicknames mapping
        self.nickname_mapping = {
            'jim': 'james', 'jimmy': 'james', 'jamie': 'james',
            'bob': 'robert', 'rob': 'robert', 'robbie': 'robert',
            'bill': 'william', 'will': 'william', 'willie': 'william',
            'dick': 'richard', 'rick': 'richard', 'richie': 'richard',
            'mike': 'michael', 'mick': 'michael', 'mickey': 'michael',
            'dave': 'david', 'davie': 'david',
            'steve': 'stephen', 'stevie': 'stephen',
            'pete': 'peter', 'andy': 'andrew', 'tony': 'anthony',
            'tom': 'thomas', 'tommy': 'thomas', 'chris': 'christopher'
        }
        
    def extract_semantic_names(self, content: str) -> List[NameCandidate]:
        """Extract human names using semantic validation instead of basic regex."""
        try:
            # Phase 1: Extract full two-word names (existing approach)
            candidates = self._extract_name_candidates(content)
            validated_names = []
            
            for candidate in candidates:
                validation = self._validate_human_name(candidate, content)
                if validation['is_human'] and validation['confidence'] > 0.5:
                    validated_names.append(NameCandidate(
                        text=candidate['text'],
                        confidence=validation['confidence'],
                        validation_reasons=validation['reasons'],
                        context=validation['context'],
                        position=candidate['position']
                    ))
            
            # Phase 2: Single name detection with surname completion
            single_names = self._extract_single_names_with_completion(content)
            validated_names.extend(single_names)
            
            unique_names = self._remove_duplicates(validated_names)
            return sorted(unique_names, key=lambda x: x.confidence, reverse=True)[:10]
            
        except Exception as e:
            self.logger.error(f"Error in semantic name extraction: {str(e)}")
            return []
    
    def _extract_name_candidates(self, content: str) -> List[Dict]:
        """Extract potential name candidates using pattern matching"""
        candidates = []
        matches = self.name_pattern.finditer(content)
        
        for match in matches:
            candidate_text = match.group().strip()
            position = match.start()
            
            if 4 <= len(candidate_text) <= 40:
                candidates.append({'text': candidate_text, 'position': position})
        
        return candidates
    
    def _validate_human_name(self, candidate: Dict, content: str) -> Dict:
        """Apply sophisticated validation to determine if candidate is a human name."""
        name_text = candidate['text']
        position = candidate['position']
        confidence = 0.0
        reasons = []
        
        name_parts = name_text.split()
        if len(name_parts) != 2:
            return {'is_human': False, 'confidence': 0.0, 'reasons': ['Not exactly two words'], 'context': ''}
        
        first_name, last_name = name_parts
        first_lower = first_name.lower()
        last_lower = last_name.lower()
        name_lower = name_text.lower()
        
        # UK Name Database Validation
        first_name_in_db = first_lower in self.uk_first_names
        last_name_in_db = last_lower in self.uk_surnames
        
        if first_name_in_db:
            confidence += 0.45
            reasons.append(f"'{first_name}' found in UK first names database")
        
        if last_name_in_db:
            confidence += 0.35
            reasons.append(f"'{last_name}' found in UK surnames database")
        
        # Enhanced Service Term Exclusion - Check for marketing/business terms
        excluded = False
        
        # Check if full name is in service exclusions
        if name_lower in self.service_exclusions:
            confidence -= 0.9
            reasons.append(f"Full name '{name_text}' is a service term")
            excluded = True
        
        # Check individual parts for marketing/business terms
        if first_lower in self.marketing_terms or last_lower in self.marketing_terms:
            confidence -= 0.7
            reasons.append(f"Contains marketing term")
            excluded = True
        
        # Check individual parts for service terms
        for part in [first_lower, last_lower]:
            if part in self.service_exclusions:
                confidence -= 0.8
                reasons.append(f"Contains service term: '{part}'")
                excluded = True
        
        # Additional check for common false positive patterns
        false_positive_patterns = [
            'low price', 'high quality', 'best service', 'free estimate',
            'emergency call', 'quick response', 'same day'
        ]
        
        for pattern in false_positive_patterns:
            if pattern in name_lower:
                confidence -= 0.9
                reasons.append(f"Matches false positive pattern: '{pattern}'")
                excluded = True
        
        # Executive Context Analysis
        context = self._get_context_around_name(content, position, 150)
        context_lower = context.lower()
        
        for exec_term in self.executive_contexts:
            if exec_term in context_lower:
                confidence += 0.2
                reasons.append(f"Found in executive context: '{exec_term}'")
                break
        
        # Name Pattern Quality
        if self._has_proper_name_characteristics(name_text):
            confidence += 0.15
            reasons.append("Has proper name characteristics")
        
        # Business Context Boost
        business_indicators = ['contact', 'director', 'owner', 'founded', 'family business', 'proprietor']
        for indicator in business_indicators:
            if indicator in context_lower:
                confidence += 0.1
                reasons.append(f"Found in business context: '{indicator}'")
                break
        
        # STRICT VALIDATION: Require at least one name in database AND not excluded
        is_human = (
            (first_name_in_db or last_name_in_db) and  # At least one name in database
            not excluded and  # Not a service/marketing term
            confidence > 0.5  # Minimum confidence threshold
        )
        
        confidence = min(confidence, 1.0)
        
        return {
            'is_human': is_human,
            'confidence': confidence,
            'reasons': reasons,
            'context': context
        }
    
    def _get_context_around_name(self, content: str, position: int, window: int) -> str:
        """Extract context around a name position"""
        start = max(0, position - window)
        end = min(len(content), position + window)
        return content[start:end]
    
    def _has_proper_name_characteristics(self, name: str) -> bool:
        """Check if name has proper capitalization and structure"""
        parts = name.split()
        if len(parts) != 2:
            return False
        
        for part in parts:
            if not part[0].isupper() or not part[1:].islower():
                return False
        
        if any(char.isdigit() or not char.isalnum() for char in name.replace(' ', '')):
            return False
        
        return True
    
    def _remove_duplicates(self, names: List[NameCandidate]) -> List[NameCandidate]:
        """Remove duplicate names, keeping the highest confidence version"""
        seen_names = {}
        
        for name_candidate in names:
            name_key = name_candidate.text.lower()
            
            if name_key not in seen_names or name_candidate.confidence > seen_names[name_key].confidence:
                seen_names[name_key] = name_candidate
        
        return list(seen_names.values())
    
    def get_extraction_summary(self, names: List[NameCandidate]) -> Dict:
        """Generate summary of extraction results"""
        if not names:
            return {
                'total_names': 0,
                'average_confidence': 0.0,
                'high_confidence_count': 0,
                'validation_methods': []
            }
        
        total_confidence = sum(name.confidence for name in names)
        high_confidence_count = sum(1 for name in names if name.confidence > 0.8)
        
        all_reasons = []
        for name in names:
            all_reasons.extend(name.validation_reasons)
        
        unique_methods = list(set(all_reasons))
        
        return {
            'total_names': len(names),
            'average_confidence': total_confidence / len(names),
            'high_confidence_count': high_confidence_count,
            'validation_methods': unique_methods,
            'names_by_confidence': [
                {
                    'name': name.text,
                    'confidence': name.confidence,
                    'reasons': name.validation_reasons
                }
                for name in sorted(names, key=lambda x: x.confidence, reverse=True)
            ]
        }
    
    def _extract_single_names_with_completion(self, content: str) -> List[NameCandidate]:
        """Extract single first names and complete them with surnames from context/email"""
        validated_single_names = []
        
        # Extract email addresses for surname hints
        email_surnames = self._extract_surnames_from_emails(content)
        
        # Find single first names in review/business contexts
        single_name_pattern = re.compile(r'\b([A-Z][a-z]{2,15})\s+(?:was|is|has|and|from|of|the|arrived|came)\b')
        matches = single_name_pattern.finditer(content)
        
        for match in matches:
            first_name = match.group(1)
            position = match.start()
            
            # Check if it's a valid UK first name (including nicknames)
            name_to_check = first_name.lower()
            if name_to_check in self.nickname_mapping:
                # Use the full name instead of nickname
                proper_first_name = self.nickname_mapping[name_to_check].title()
            elif name_to_check in self.uk_first_names:
                proper_first_name = first_name
            else:
                continue  # Skip if not a recognized name
            
            # Try to complete with email-derived surname
            for email_surname in email_surnames:
                full_name = f"{proper_first_name} {email_surname}"
                
                # Validate the completed name
                validation = self._validate_human_name(
                    {'text': full_name, 'position': position}, 
                    content
                )
                
                if validation['is_human']:
                    validated_single_names.append(NameCandidate(
                        text=full_name,
                        confidence=validation['confidence'] * 0.9,  # Slight penalty for completion
                        validation_reasons=validation['reasons'] + ['Completed from single name + email'],
                        context=validation['context'],
                        position=position
                    ))
                    break  # Use first successful completion
        
        # Look for names in review contexts (different pattern)
        review_pattern = re.compile(r'\b([A-Z][a-z]{2,15})\s+(?:arrived|came|was|is)\s+(?:very|extremely|really|so)\s+(?:polite|helpful|professional|kind|friendly)\b')
        review_matches = review_pattern.finditer(content)
        
        for match in review_matches:
            first_name = match.group(1)
            position = match.start()
            
            # Handle nicknames
            name_to_check = first_name.lower()
            if name_to_check in self.nickname_mapping:
                proper_first_name = self.nickname_mapping[name_to_check].title()
            elif name_to_check in self.uk_first_names:
                proper_first_name = first_name
            else:
                continue
            
            # Try email completion first
            for email_surname in email_surnames:
                full_name = f"{proper_first_name} {email_surname}"
                validation = self._validate_human_name(
                    {'text': full_name, 'position': position}, 
                    content
                )
                
                if validation['is_human']:
                    validated_single_names.append(NameCandidate(
                        text=full_name,
                        confidence=validation['confidence'] * 0.85,  # Penalty for completion
                        validation_reasons=validation['reasons'] + ['Found in review context + email completion'],
                        context=validation['context'],
                        position=position
                    ))
                    break
        
        return validated_single_names
    
    def _extract_surnames_from_emails(self, content: str) -> List[str]:
        """Extract potential surnames from email addresses"""
        surnames = []
        
        # Find email addresses
        email_pattern = re.compile(r'\b([a-zA-Z0-9]+[a-zA-Z0-9._-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b')
        emails = email_pattern.findall(content)
        
        for email in emails:
            local_part = email.split('@')[0].lower()
            
            # Pattern 1: firstnamesurname@domain (e.g., jnmcmanus@domain)
            if len(local_part) > 4:
                # Try to extract surname from end
                potential_surnames = []
                
                # Look for known surname patterns
                for surname in self.uk_surnames:
                    if local_part.endswith(surname.lower()) and len(surname) >= 4:
                        # Proper capitalization for Scottish/Irish names
                        proper_surname = self._proper_capitalize_surname(surname)
                        potential_surnames.append(proper_surname)
                
                # Add potential surnames
                surnames.extend(potential_surnames)
            
            # Pattern 2: first.last@domain
            if '.' in local_part:
                parts = local_part.split('.')
                if len(parts) == 2:
                    potential_surname = parts[1]
                    if potential_surname.lower() in self.uk_surnames:
                        proper_surname = self._proper_capitalize_surname(potential_surname)
                        surnames.append(proper_surname)
        
        return list(set(surnames))  # Remove duplicates
    
    def _proper_capitalize_surname(self, surname: str) -> str:
        """Properly capitalize surnames, especially Scottish/Irish names"""
        surname_lower = surname.lower()
        
        # Scottish/Irish name patterns
        if surname_lower.startswith('mc') and len(surname_lower) > 2:
            return 'Mc' + surname_lower[2:].capitalize()
        elif surname_lower.startswith('mac') and len(surname_lower) > 3:
            return 'Mac' + surname_lower[3:].capitalize()
        elif surname_lower.startswith("o'") and len(surname_lower) > 2:
            return "O'" + surname_lower[2:].capitalize()
        else:
            return surname.capitalize() 