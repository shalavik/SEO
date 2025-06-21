"""
Advanced Contact Attribution Engine
Links executives to their specific contact details using sophisticated attribution algorithms
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from urllib.parse import urlparse
import difflib

@dataclass
class ContactInfo:
    """Contact information with attribution metadata"""
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    attribution_confidence: float = 0.0
    attribution_method: str = "unknown"
    context: str = ""

@dataclass
class EnrichedExecutive:
    """Executive with attributed contact information"""
    name: str
    title: Optional[str] = None
    contact_info: ContactInfo = field(default_factory=ContactInfo)
    discovery_confidence: float = 0.0
    discovery_source: str = "unknown"
    overall_quality_score: float = 0.0

class AdvancedContactAttributor:
    """
    Advanced contact attribution using multiple sophisticated strategies
    Designed to increase contact attribution from 25% to 70%+
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Email patterns for attribution
        self.email_patterns = [
            # Direct name patterns
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            # Email in signatures
            r'email:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'e-?mail:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        ]
        
        # Phone patterns (UK format)
        self.phone_patterns = [
            r'(\+44\s?[0-9\s]{10,})',  # +44 format
            r'(0[0-9\s]{10,})',        # 0 prefix format
            r'(\([0-9]{3,5}\)\s?[0-9\s]{6,})',  # (area) format
            r'([0-9]{3,5}\s?[0-9]{3,4}\s?[0-9]{3,4})',  # spaced format
        ]
        
        # Common UK name prefixes and suffixes
        self.name_variations = {
            'james': ['jim', 'jimmy', 'jamie'],
            'robert': ['rob', 'bob', 'bobby'],
            'william': ['will', 'bill', 'billy'],
            'richard': ['rick', 'dick', 'richie'],
            'michael': ['mike', 'mick', 'mickey'],
            'david': ['dave', 'davie'],
            'andrew': ['andy', 'drew'],
            'anthony': ['tony'],
            'christopher': ['chris'],
            'stephen': ['steve', 'stevie'],
            'thomas': ['tom', 'tommy'],
            'peter': ['pete']
        }
    
    def attribute_contacts_to_executives(self, executives: List, content: str, company_domain: str) -> List[EnrichedExecutive]:
        """
        Main attribution method that processes all executives
        """
        try:
            self.logger.info(f"Starting contact attribution for {len(executives)} executives")
            
            # Extract all contacts from content
            all_emails = self._extract_all_emails(content)
            all_phones = self._extract_all_phones(content)
            
            self.logger.info(f"Found {len(all_emails)} emails and {len(all_phones)} phones in content")
            
            enriched_executives = []
            
            for executive in executives:
                enriched = EnrichedExecutive(
                    name=executive.name,
                    discovery_confidence=executive.confidence,
                    discovery_source=executive.source_strategy
                )
                
                # Apply attribution strategies
                contact_info = self._attribute_contact_to_executive(
                    executive, content, all_emails, all_phones, company_domain
                )
                
                enriched.contact_info = contact_info
                enriched.overall_quality_score = self._calculate_quality_score(enriched)
                
                enriched_executives.append(enriched)
            
            # Sort by quality score
            enriched_executives.sort(key=lambda x: x.overall_quality_score, reverse=True)
            
            self.logger.info(f"Completed attribution for {len(enriched_executives)} executives")
            return enriched_executives
            
        except Exception as e:
            self.logger.error(f"Contact attribution failed: {str(e)}")
            return []
    
    def _attribute_contact_to_executive(self, executive, content: str, all_emails: List[str], 
                                      all_phones: List[str], company_domain: str) -> ContactInfo:
        """
        Attribute specific contact information to an executive using multiple strategies
        """
        contact_info = ContactInfo()
        
        # Strategy 1: Direct email pattern matching
        email_result = self._find_direct_email_match(executive.name, all_emails, company_domain)
        if email_result:
            contact_info.email = email_result[0]
            contact_info.attribution_confidence = max(contact_info.attribution_confidence, email_result[1])
            contact_info.attribution_method = email_result[2]
        
        # Strategy 2: Email signature analysis
        if not contact_info.email:
            signature_result = self._find_email_in_signature(executive.name, content)
            if signature_result:
                contact_info.email = signature_result[0]
                contact_info.attribution_confidence = max(contact_info.attribution_confidence, signature_result[1])
                contact_info.attribution_method = signature_result[2]
        
        # Strategy 3: Proximity-based email attribution
        if not contact_info.email:
            proximity_result = self._find_email_by_proximity(executive.name, content, all_emails)
            if proximity_result:
                contact_info.email = proximity_result[0]
                contact_info.attribution_confidence = max(contact_info.attribution_confidence, proximity_result[1])
                contact_info.attribution_method = proximity_result[2]
        
        # Strategy 4: Phone attribution using similar methods
        phone_result = self._find_phone_for_executive(executive.name, content, all_phones)
        if phone_result:
            contact_info.phone = phone_result[0]
            if contact_info.attribution_confidence < phone_result[1]:
                contact_info.attribution_confidence = phone_result[1]
                contact_info.attribution_method = phone_result[2]
        
        # Strategy 5: LinkedIn profile discovery
        linkedin_result = self._find_linkedin_profile(executive.name, content, company_domain)
        if linkedin_result:
            contact_info.linkedin_url = linkedin_result[0]
            if contact_info.attribution_confidence < linkedin_result[1]:
                contact_info.attribution_confidence = linkedin_result[1]
                contact_info.attribution_method = linkedin_result[2]
        
        return contact_info
    
    def _find_direct_email_match(self, executive_name: str, all_emails: List[str], 
                                company_domain: str) -> Optional[Tuple[str, float, str]]:
        """
        Find direct email matches based on name patterns
        """
        try:
            name_parts = executive_name.lower().split()
            if len(name_parts) != 2:
                return None
            
            first_name, last_name = name_parts
            
            # Generate possible email patterns
            possible_patterns = [
                f"{first_name}@",
                f"{last_name}@",
                f"{first_name}.{last_name}@",
                f"{first_name[0]}.{last_name}@",
                f"{first_name}.{last_name[0]}@",
                f"{first_name}{last_name}@",
                f"{first_name[0]}{last_name}@",
                f"{last_name}.{first_name}@",
                f"{last_name}{first_name}@"
            ]
            
            # Add nickname variations
            if first_name in self.name_variations:
                for nickname in self.name_variations[first_name]:
                    possible_patterns.extend([
                        f"{nickname}@",
                        f"{nickname}.{last_name}@",
                        f"{nickname}{last_name}@"
                    ])
            
            # Check each email against patterns
            for email in all_emails:
                email_lower = email.lower()
                for pattern in possible_patterns:
                    if pattern in email_lower:
                        # Higher confidence if it's on the company domain
                        confidence = 0.9 if company_domain in email_lower else 0.7
                        return (email, confidence, "direct_pattern_match")
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Direct email match failed: {str(e)}")
            return None
    
    def _find_email_in_signature(self, executive_name: str, content: str) -> Optional[Tuple[str, float, str]]:
        """
        Find email in signature context near the executive's name
        """
        try:
            name_parts = executive_name.split()
            
            # Look for signature patterns around the name
            signature_patterns = [
                rf'{re.escape(executive_name)}.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}})',
                rf'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}}).*?{re.escape(executive_name)}',
                rf'regards,?\s*{re.escape(executive_name)}.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}})',
                rf'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}}).*?regards,?\s*{re.escape(executive_name)}'
            ]
            
            for pattern in signature_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    email = match.group(1)
                    if self._is_valid_email(email):
                        return (email, 0.85, "signature_analysis")
            
            # Also check for each name part separately in case of variations
            for name_part in name_parts:
                if len(name_part) > 2:  # Skip very short names
                    pattern = rf'{re.escape(name_part)}.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}})'
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        email = match.group(1)
                        if self._is_valid_email(email):
                            return (email, 0.6, "partial_name_signature")
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Signature email search failed: {str(e)}")
            return None
    
    def _find_email_by_proximity(self, executive_name: str, content: str, 
                                all_emails: List[str]) -> Optional[Tuple[str, float, str]]:
        """
        Find email by proximity analysis - closest email to name mention
        """
        try:
            if not all_emails:
                return None
            
            # Find all positions of the executive's name
            name_positions = []
            for match in re.finditer(re.escape(executive_name), content, re.IGNORECASE):
                name_positions.append(match.start())
            
            if not name_positions:
                return None
            
            # Find all email positions
            email_positions = {}
            for email in all_emails:
                for match in re.finditer(re.escape(email), content, re.IGNORECASE):
                    email_positions[email] = match.start()
            
            # Calculate minimum distance for each email
            closest_email = None
            min_distance = float('inf')
            
            for email, email_pos in email_positions.items():
                for name_pos in name_positions:
                    distance = abs(email_pos - name_pos)
                    if distance < min_distance:
                        min_distance = distance
                        closest_email = email
            
            if closest_email and min_distance < 500:  # Within 500 characters
                # Confidence decreases with distance
                confidence = max(0.3, 0.8 - (min_distance / 1000))
                return (closest_email, confidence, "proximity_analysis")
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Proximity email search failed: {str(e)}")
            return None
    
    def _find_phone_for_executive(self, executive_name: str, content: str, 
                                 all_phones: List[str]) -> Optional[Tuple[str, float, str]]:
        """
        Find phone number for executive using similar attribution strategies
        """
        try:
            # Strategy 1: Phone in signature context
            signature_patterns = [
                rf'{re.escape(executive_name)}.*?(\+44\s?[0-9\s]{{10,}}|0[0-9\s]{{10,}})',
                rf'(\+44\s?[0-9\s]{{10,}}|0[0-9\s]{{10,}}).*?{re.escape(executive_name)}'
            ]
            
            for pattern in signature_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    phone = match.group(1).strip()
                    if self._is_valid_phone(phone):
                        return (phone, 0.8, "signature_phone")
            
            # Strategy 2: Proximity analysis for phones
            if all_phones:
                name_positions = []
                for match in re.finditer(re.escape(executive_name), content, re.IGNORECASE):
                    name_positions.append(match.start())
                
                if name_positions:
                    phone_positions = {}
                    for phone in all_phones:
                        for match in re.finditer(re.escape(phone), content, re.IGNORECASE):
                            phone_positions[phone] = match.start()
                    
                    closest_phone = None
                    min_distance = float('inf')
                    
                    for phone, phone_pos in phone_positions.items():
                        for name_pos in name_positions:
                            distance = abs(phone_pos - name_pos)
                            if distance < min_distance:
                                min_distance = distance
                                closest_phone = phone
                    
                    if closest_phone and min_distance < 300:  # Closer proximity for phones
                        confidence = max(0.4, 0.7 - (min_distance / 600))
                        return (closest_phone, confidence, "phone_proximity")
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Phone attribution failed: {str(e)}")
            return None
    
    def _find_linkedin_profile(self, executive_name: str, content: str, 
                              company_domain: str) -> Optional[Tuple[str, float, str]]:
        """
        Find LinkedIn profile for executive
        """
        try:
            # Look for LinkedIn URLs in content
            linkedin_pattern = r'linkedin\.com/in/([a-zA-Z0-9\-]+)'
            matches = re.finditer(linkedin_pattern, content, re.IGNORECASE)
            
            name_parts = executive_name.lower().split()
            if len(name_parts) != 2:
                return None
            
            first_name, last_name = name_parts
            
            for match in matches:
                profile_id = match.group(1).lower()
                
                # Check if profile ID contains name parts
                if (first_name in profile_id and last_name in profile_id) or \
                   (first_name.replace(' ', '-') in profile_id) or \
                   (last_name in profile_id and len(last_name) > 3):
                    
                    full_url = f"https://linkedin.com/in/{match.group(1)}"
                    return (full_url, 0.7, "linkedin_profile_match")
            
            # If no direct match, try to construct potential LinkedIn URL
            potential_profiles = [
                f"{first_name}-{last_name}",
                f"{first_name}{last_name}",
                f"{first_name[0]}{last_name}",
                f"{first_name}.{last_name}"
            ]
            
            # Add nickname variations
            if first_name in self.name_variations:
                for nickname in self.name_variations[first_name]:
                    potential_profiles.extend([
                        f"{nickname}-{last_name}",
                        f"{nickname}{last_name}"
                    ])
            
            # For now, return None - in a full implementation, we could validate these URLs
            # by making HTTP requests to check if they exist
            
            return None
            
        except Exception as e:
            self.logger.warning(f"LinkedIn profile search failed: {str(e)}")
            return None
    
    def _extract_all_emails(self, content: str) -> List[str]:
        """Extract all email addresses from content"""
        emails = set()
        
        for pattern in self.email_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                email = match.group(1) if len(match.groups()) > 0 else match.group(0)
                if self._is_valid_email(email):
                    emails.add(email.lower())
        
        return list(emails)
    
    def _extract_all_phones(self, content: str) -> List[str]:
        """Extract all phone numbers from content"""
        phones = set()
        
        for pattern in self.phone_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                phone = match.group(0)
                cleaned_phone = self._clean_phone_number(phone)
                if self._is_valid_phone(cleaned_phone):
                    phones.add(cleaned_phone)
        
        return list(phones)
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        if not email or len(email) < 5:
            return False
        
        # Basic email validation
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_regex, email))
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format (UK)"""
        if not phone:
            return False
        
        # Remove all non-digit characters for validation
        digits_only = re.sub(r'[^\d]', '', phone)
        
        # UK phone numbers should have 10-11 digits (excluding country code)
        if len(digits_only) < 10 or len(digits_only) > 13:
            return False
        
        return True
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and standardize phone number format"""
        # Remove extra spaces and non-essential characters
        cleaned = re.sub(r'[^\d\+\(\)\s\-]', '', phone)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _calculate_quality_score(self, executive: EnrichedExecutive) -> float:
        """
        Calculate overall quality score for an executive
        """
        score = 0.0
        
        # Base score from discovery confidence
        score += executive.discovery_confidence * 0.3
        
        # Contact attribution bonus
        if executive.contact_info.email:
            score += 0.4
        if executive.contact_info.phone:
            score += 0.3
        if executive.contact_info.linkedin_url:
            score += 0.2
        
        # Attribution confidence bonus
        score += executive.contact_info.attribution_confidence * 0.2
        
        # Title bonus (if we have title information)
        if executive.title and executive.title != "Unknown":
            score += 0.1
        
        return min(1.0, score)