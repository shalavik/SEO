"""
Advanced Contact Attributor - Sophisticated Email/Phone to Person Linking
Uses multi-signal analysis including email signatures, contact sections, and context weighting
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ContactMatch:
    """Represents a contact attributed to a person with confidence scoring"""
    contact: str
    contact_type: str  # 'email' or 'phone'
    person_name: str
    confidence: float
    attribution_method: str
    context: str
    position: int

class AdvancedContactAttributor:
    """
    Advanced contact attribution using multiple signals and NLP techniques.
    Replaces simple proximity matching with sophisticated context analysis.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Email patterns with context capture
        self.email_pattern = re.compile(
            r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
        )
        
        # UK phone number patterns
        self.phone_patterns = [
            re.compile(r'\b(0[1-9]\d{8,9})\b'),  # UK landline
            re.compile(r'\b(07\d{9})\b'),         # UK mobile
            re.compile(r'\b(\+44\s?[1-9]\d{8,9})\b'),  # International
            re.compile(r'\b(0\d{3}\s?\d{3}\s?\d{4})\b'),  # Formatted landline
            re.compile(r'\b(0\d{4}\s?\d{6})\b'),  # Alternative format
        ]
        
        # Email signature patterns
        self.signature_patterns = [
            re.compile(r'([A-Z][a-z]+\s+[A-Z][a-z]+)[\s\r\n]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.MULTILINE),
            re.compile(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})[\s\r\n]+([A-Z][a-z]+\s+[A-Z][a-z]+)', re.MULTILINE),
            re.compile(r'([A-Z][a-z]+\s+[A-Z][a-z]+).*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.DOTALL),
        ]
        
        # Contact section indicators
        self.contact_section_indicators = [
            'contact', 'reach', 'get in touch', 'speak to', 'call', 'email',
            'for more information', 'enquiries', 'questions', 'quotes',
            'meet the team', 'our team', 'staff', 'directors'
        ]
        
        # Executive context boosters
        self.executive_contexts = [
            'director', 'manager', 'ceo', 'founder', 'owner', 'head',
            'chief', 'president', 'partner', 'principal', 'senior'
        ]
        
    def attribute_contacts_to_people(self, content: str, people: List[Dict]) -> List[Dict]:
        """
        Attribute emails and phone numbers to specific people using advanced analysis.
        
        Args:
            content: Website content to analyze
            people: List of validated people with names and positions
            
        Returns:
            List of people with attributed contact information
        """
        try:
            # Extract all contacts with their contexts
            emails_with_context = self._extract_emails_with_context(content)
            phones_with_context = self._extract_phones_with_context(content)
            
            self.logger.info(f"Found {len(emails_with_context)} emails and {len(phones_with_context)} phones")
            
            attributed_people = []
            
            for person in people:
                person_name = person.get('name', person.get('text', ''))
                
                # Find best email match for this person
                email_match = self._find_best_email_match(person_name, emails_with_context, content)
                
                # Find best phone match for this person
                phone_match = self._find_best_phone_match(person_name, phones_with_context, content)
                
                # Create attributed person record
                attributed_person = {
                    'name': person_name,
                    'email': email_match['email'] if email_match else None,
                    'email_confidence': email_match['confidence'] if email_match else 0.0,
                    'email_method': email_match['method'] if email_match else None,
                    'phone': phone_match['phone'] if phone_match else None,
                    'phone_confidence': phone_match['confidence'] if phone_match else 0.0,
                    'phone_method': phone_match['method'] if phone_match else None,
                    'overall_confidence': self._calculate_overall_confidence(email_match, phone_match),
                    'attribution_context': {
                        'email_context': email_match['context'] if email_match else None,
                        'phone_context': phone_match['context'] if phone_match else None
                    }
                }
                
                attributed_people.append(attributed_person)
            
            return attributed_people
            
        except Exception as e:
            self.logger.error(f"Error in contact attribution: {str(e)}")
            return people  # Return original people if attribution fails
    
    def _extract_emails_with_context(self, content: str) -> List[Dict]:
        """Extract all emails with surrounding context"""
        emails_with_context = []
        
        for match in self.email_pattern.finditer(content):
            email = match.group(1)
            position = match.start()
            
            # Get context around email
            context = self._get_context_around_position(content, position, 200)
            
            # Determine email context type
            context_type = self._classify_email_context(context)
            
            emails_with_context.append({
                'email': email,
                'position': position,
                'context': context,
                'context_type': context_type
            })
        
        return emails_with_context
    
    def _extract_phones_with_context(self, content: str) -> List[Dict]:
        """Extract all phone numbers with surrounding context"""
        phones_with_context = []
        
        for pattern in self.phone_patterns:
            for match in pattern.finditer(content):
                phone = self._normalize_phone_number(match.group(1))
                position = match.start()
                
                # Get context around phone
                context = self._get_context_around_position(content, position, 200)
                
                # Determine phone context type
                context_type = self._classify_phone_context(context)
                
                phones_with_context.append({
                    'phone': phone,
                    'position': position,
                    'context': context,
                    'context_type': context_type
                })
        
        return phones_with_context
    
    def _find_best_email_match(self, person_name: str, emails: List[Dict], content: str) -> Optional[Dict]:
        """Find the best email match for a person using multiple methods"""
        
        # Method 1: Email signature detection (highest confidence)
        signature_match = self._find_email_signature_match(person_name, emails, content)
        if signature_match and signature_match['confidence'] > 0.8:
            return signature_match
        
        # Method 2: Contact section analysis (medium confidence)
        contact_section_match = self._find_contact_section_email_match(person_name, emails)
        if contact_section_match and contact_section_match['confidence'] > 0.6:
            return contact_section_match
        
        # Method 3: Name-based email matching (medium confidence)
        name_based_match = self._find_name_based_email_match(person_name, emails)
        if name_based_match and name_based_match['confidence'] > 0.5:
            return name_based_match
        
        # Method 4: Proximity matching with context weighting (lower confidence)
        proximity_match = self._find_proximity_email_match(person_name, emails, content)
        if proximity_match and proximity_match['confidence'] > 0.3:
            return proximity_match
        
        return None
    
    def _find_best_phone_match(self, person_name: str, phones: List[Dict], content: str) -> Optional[Dict]:
        """Find the best phone match for a person"""
        
        # Method 1: Direct association in contact sections
        contact_match = self._find_contact_section_phone_match(person_name, phones)
        if contact_match and contact_match['confidence'] > 0.7:
            return contact_match
        
        # Method 2: Proximity matching with executive context
        proximity_match = self._find_proximity_phone_match(person_name, phones, content)
        if proximity_match and proximity_match['confidence'] > 0.4:
            return proximity_match
        
        return None
    
    def _find_email_signature_match(self, person_name: str, emails: List[Dict], content: str) -> Optional[Dict]:
        """Detect email signatures where name and email appear together"""
        
        for signature_pattern in self.signature_patterns:
            for match in signature_pattern.finditer(content):
                groups = match.groups()
                
                # Check if person name appears in signature
                for group in groups:
                    if self._names_match(person_name, group):
                        # Find corresponding email in groups
                        for email_group in groups:
                            if '@' in email_group:
                                # Find this email in our email list
                                for email_data in emails:
                                    if email_data['email'] == email_group:
                                        return {
                                            'email': email_group,
                                            'confidence': 0.9,
                                            'method': 'email_signature',
                                            'context': match.group(0)
                                        }
        
        return None
    
    def _find_contact_section_email_match(self, person_name: str, emails: List[Dict]) -> Optional[Dict]:
        """Find emails in contact sections mentioning the person"""
        
        for email_data in emails:
            context = email_data['context'].lower()
            
            # Check if this is a contact section
            is_contact_section = any(indicator in context for indicator in self.contact_section_indicators)
            
            if is_contact_section:
                # Check if person name appears in context
                if self._name_appears_in_context(person_name, context):
                    confidence = 0.7
                    
                    # Boost confidence if executive context
                    if any(exec_term in context for exec_term in self.executive_contexts):
                        confidence += 0.1
                    
                    return {
                        'email': email_data['email'],
                        'confidence': min(confidence, 0.9),
                        'method': 'contact_section',
                        'context': email_data['context']
                    }
        
        return None
    
    def _find_name_based_email_match(self, person_name: str, emails: List[Dict]) -> Optional[Dict]:
        """Match emails based on name patterns in email address"""
        
        name_parts = person_name.lower().split()
        if len(name_parts) != 2:
            return None
        
        first_name, last_name = name_parts
        
        for email_data in emails:
            email = email_data['email'].lower()
            local_part = email.split('@')[0]
            
            # Pattern 1: firstname.lastname@domain
            if f"{first_name}.{last_name}" in local_part:
                return {
                    'email': email_data['email'],
                    'confidence': 0.8,
                    'method': 'name_pattern_full',
                    'context': email_data['context']
                }
            
            # Pattern 2: firstinitiallastname@domain
            if f"{first_name[0]}{last_name}" in local_part:
                return {
                    'email': email_data['email'],
                    'confidence': 0.6,
                    'method': 'name_pattern_initial',
                    'context': email_data['context']
                }
            
            # Pattern 3: lastname@domain (for business owners)
            if last_name in local_part and len(local_part) <= len(last_name) + 3:
                return {
                    'email': email_data['email'],
                    'confidence': 0.5,
                    'method': 'name_pattern_surname',
                    'context': email_data['context']
                }
        
        return None
    
    def _find_proximity_email_match(self, person_name: str, emails: List[Dict], content: str) -> Optional[Dict]:
        """Find emails based on proximity to person name with context weighting"""
        
        person_positions = [m.start() for m in re.finditer(re.escape(person_name), content, re.IGNORECASE)]
        
        best_match = None
        best_score = 0
        
        for email_data in emails:
            email_position = email_data['position']
            
            # Calculate proximity scores to all person mentions
            min_distance = min([abs(email_position - pos) for pos in person_positions] or [float('inf')])
            
            if min_distance == float('inf'):
                continue
            
            # Calculate base proximity score (closer = higher score)
            proximity_score = max(0, 1 - (min_distance / 1000))  # Max distance of 1000 chars
            
            # Apply context weighting
            context_weight = self._calculate_context_weight(email_data['context'])
            
            total_score = proximity_score * context_weight
            
            if total_score > best_score and total_score > 0.3:
                best_score = total_score
                best_match = {
                    'email': email_data['email'],
                    'confidence': min(total_score, 0.7),  # Cap confidence for proximity matching
                    'method': 'proximity_weighted',
                    'context': email_data['context']
                }
        
        return best_match
    
    def _find_contact_section_phone_match(self, person_name: str, phones: List[Dict]) -> Optional[Dict]:
        """Find phones in contact sections mentioning the person"""
        
        for phone_data in phones:
            context = phone_data['context'].lower()
            
            # Check if this is a contact section
            is_contact_section = any(indicator in context for indicator in self.contact_section_indicators)
            
            if is_contact_section and self._name_appears_in_context(person_name, context):
                confidence = 0.6
                
                # Boost confidence if executive context
                if any(exec_term in context for exec_term in self.executive_contexts):
                    confidence += 0.1
                
                return {
                    'phone': phone_data['phone'],
                    'confidence': min(confidence, 0.8),
                    'method': 'contact_section',
                    'context': phone_data['context']
                }
        
        return None
    
    def _find_proximity_phone_match(self, person_name: str, phones: List[Dict], content: str) -> Optional[Dict]:
        """Find phones based on proximity to person name"""
        
        person_positions = [m.start() for m in re.finditer(re.escape(person_name), content, re.IGNORECASE)]
        
        best_match = None
        best_score = 0
        
        for phone_data in phones:
            phone_position = phone_data['position']
            
            # Calculate proximity scores
            min_distance = min([abs(phone_position - pos) for pos in person_positions] or [float('inf')])
            
            if min_distance == float('inf'):
                continue
            
            # Calculate proximity score
            proximity_score = max(0, 1 - (min_distance / 800))  # Shorter range for phone numbers
            
            # Apply context weighting
            context_weight = self._calculate_context_weight(phone_data['context'])
            
            total_score = proximity_score * context_weight
            
            if total_score > best_score and total_score > 0.4:
                best_score = total_score
                best_match = {
                    'phone': phone_data['phone'],
                    'confidence': min(total_score, 0.6),
                    'method': 'proximity_weighted',
                    'context': phone_data['context']
                }
        
        return best_match
    
    def _get_context_around_position(self, content: str, position: int, window: int) -> str:
        """Extract context around a position"""
        start = max(0, position - window)
        end = min(len(content), position + window)
        return content[start:end]
    
    def _classify_email_context(self, context: str) -> str:
        """Classify the context type for an email"""
        context_lower = context.lower()
        
        if any(indicator in context_lower for indicator in self.contact_section_indicators):
            return 'contact_section'
        elif 'signature' in context_lower or 'regards' in context_lower:
            return 'email_signature'
        elif any(exec_term in context_lower for exec_term in self.executive_contexts):
            return 'executive_context'
        else:
            return 'general'
    
    def _classify_phone_context(self, context: str) -> str:
        """Classify the context type for a phone number"""
        context_lower = context.lower()
        
        if any(indicator in context_lower for indicator in self.contact_section_indicators):
            return 'contact_section'
        elif any(exec_term in context_lower for exec_term in self.executive_contexts):
            return 'executive_context'
        else:
            return 'general'
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if two names refer to the same person"""
        return name1.lower().strip() == name2.lower().strip()
    
    def _name_appears_in_context(self, person_name: str, context: str) -> bool:
        """Check if person name appears in context"""
        name_parts = person_name.lower().split()
        context_lower = context.lower()
        
        # Check for full name
        if person_name.lower() in context_lower:
            return True
        
        # Check for partial name matches (both parts should appear)
        if len(name_parts) == 2:
            return all(part in context_lower for part in name_parts)
        
        return False
    
    def _calculate_context_weight(self, context: str) -> float:
        """Calculate weighting factor based on context type"""
        context_lower = context.lower()
        
        # High weight for contact sections
        if any(indicator in context_lower for indicator in self.contact_section_indicators):
            return 1.5
        
        # Medium weight for executive contexts
        if any(exec_term in context_lower for exec_term in self.executive_contexts):
            return 1.2
        
        # Low weight for general context
        return 0.8
    
    def _normalize_phone_number(self, phone: str) -> str:
        """Normalize phone number format"""
        # Remove spaces and format consistently
        clean_phone = re.sub(r'\s+', '', phone)
        
        # Convert +44 to 0
        if clean_phone.startswith('+44'):
            clean_phone = '0' + clean_phone[3:]
        
        return clean_phone
    
    def _calculate_overall_confidence(self, email_match: Optional[Dict], phone_match: Optional[Dict]) -> float:
        """Calculate overall confidence for a person's contact attribution"""
        email_conf = email_match['confidence'] if email_match else 0.0
        phone_conf = phone_match['confidence'] if phone_match else 0.0
        
        if email_conf > 0 and phone_conf > 0:
            # Both contacts found - weighted average with bonus
            return min((email_conf * 0.6 + phone_conf * 0.4) + 0.1, 1.0)
        elif email_conf > 0:
            # Email only
            return email_conf * 0.8
        elif phone_conf > 0:
            # Phone only
            return phone_conf * 0.7
        else:
            # No contacts
            return 0.0 