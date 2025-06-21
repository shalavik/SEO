"""
Enhanced Context-Aware Contact Extractor - Phase 5B Enhancement
Attributes contact details to specific individuals through proximity analysis and context scoring.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExecutiveContact:
    """Enhanced executive contact model with proper attribution structure"""
    name: str
    title: str = "Unknown"
    seniority_tier: str = "tier_3"
    email: Optional[str] = None
    email_confidence: float = 0.0
    phone: Optional[str] = None
    phone_confidence: float = 0.0
    linkedin_url: Optional[str] = None
    linkedin_verified: bool = False
    attribution_method: str = ""
    discovery_sources: List[str] = field(default_factory=list)
    overall_confidence: float = 0.0
    context: str = ""

@dataclass
class ContactAttributionResult:
    """Result of contact attribution analysis"""
    executives: List[ExecutiveContact]
    attribution_success: bool
    attribution_accuracy: float
    total_contacts_found: int
    attributed_contacts: int
    unattributed_contacts: Dict[str, List[str]]

class ContextAwareContactExtractor:
    """
    Enhanced contact extractor that attributes emails and phones to specific executives
    through proximity analysis, email signature detection, and context scoring.
    
    Phase 5B Enhancements:
    - Proper executive object structure
    - Contact attribution to individuals
    - Confidence scoring per attribution
    - Multiple attribution methods
    """
    
    def __init__(self):
        """Initialize contact extractor with attribution patterns"""
        
        # Email patterns (enhanced)
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            r'[Ee]mail:?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            r'[Cc]ontact:?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
        ]
        
        # UK phone patterns (comprehensive)
        self.phone_patterns = [
            r'\b0[1-9]\d{8,9}\b',                    # UK landline
            r'\b07\d{9}\b',                          # UK mobile
            r'\+44\s?[1-9]\d{8,9}\b',               # International format
            r'\b\d{5}\s\d{6}\b',                    # Spaced format
            r'\b\d{4}\s\d{3}\s\d{4}\b',            # Alternative spacing
            r'[Tt]el:?\s*(\+?44\s?[1-9]\d{8,9})',  # Tel: prefix
            r'[Pp]hone:?\s*(\+?44\s?[1-9]\d{8,9})', # Phone: prefix
            r'[Mm]obile:?\s*(07\d{9})'              # Mobile: prefix
        ]
        
        # Executive title patterns for context
        self.executive_titles = {
            'tier_1': [
                'ceo', 'chief executive officer', 'managing director', 'md', 'founder',
                'co-founder', 'owner', 'proprietor', 'chairman', 'chairwoman', 'director'
            ],
            'tier_2': [
                'general manager', 'operations manager', 'business manager', 'regional manager',
                'head of', 'department manager', 'senior manager', 'project manager'
            ],
            'tier_3': [
                'manager', 'supervisor', 'team leader', 'senior', 'lead', 'coordinator',
                'administrator', 'officer', 'specialist', 'consultant'
            ]
        }
        
        # Attribution context indicators
        self.attribution_indicators = {
            'direct': ['email', 'e-mail', 'contact', 'reach', 'call', 'phone', 'tel'],
            'signature': ['regards', 'best', 'sincerely', 'yours', 'from', 'sent by'],
            'proximity': [':', '-', '|', 'at', 'on', 'via']
        }

    def extract_executive_contacts(self, content: str, executives: List[Dict[str, str]] = None) -> ContactAttributionResult:
        """
        Extract and attribute contact details to specific executives.
        
        Args:
            content: Website content to analyze
            executives: Pre-extracted executive names and titles
            
        Returns:
            ContactAttributionResult with properly attributed contacts
        """
        logger.info("Starting enhanced contact extraction with attribution")
        
        # Extract all emails and phones from content
        all_emails = self._extract_all_emails(content)
        all_phones = self._extract_all_phones(content)
        
        logger.info(f"Found {len(all_emails)} emails, {len(all_phones)} phones")
        
        # If no executives provided, try to extract names from content
        if not executives:
            executives = self._extract_executive_names_from_content(content)
        
        # Create executive contact objects
        executive_contacts = []
        attributed_emails = set()
        attributed_phones = set()
        
        for exec_data in executives:
            name = exec_data.get('name', '')
            title = exec_data.get('title', 'Unknown')
            
            # Skip invalid names
            if not name or len(name.split()) < 2:
                continue
            
            # Create executive contact object
            exec_contact = ExecutiveContact(
                name=name,
                title=title,
                seniority_tier=self._classify_seniority(title)
            )
            
            # Attempt contact attribution
            attribution_result = self._attribute_contacts_to_executive(
                content, name, all_emails, all_phones
            )
            
            # Update executive with attributed contacts
            if attribution_result['email']:
                exec_contact.email = attribution_result['email']
                exec_contact.email_confidence = attribution_result['email_confidence']
                attributed_emails.add(attribution_result['email'])
            
            if attribution_result['phone']:
                exec_contact.phone = attribution_result['phone']
                exec_contact.phone_confidence = attribution_result['phone_confidence']
                attributed_phones.add(attribution_result['phone'])
            
            exec_contact.attribution_method = attribution_result['method']
            exec_contact.overall_confidence = attribution_result['overall_confidence']
            exec_contact.context = attribution_result['context']
            exec_contact.discovery_sources = ['website_content']
            
            executive_contacts.append(exec_contact)
        
        # Calculate attribution statistics
        total_contacts = len(all_emails) + len(all_phones)
        attributed_contacts = len(attributed_emails) + len(attributed_phones)
        attribution_accuracy = (attributed_contacts / total_contacts) if total_contacts > 0 else 0
        
        # Unattributed contacts
        unattributed_emails = [email for email in all_emails if email not in attributed_emails]
        unattributed_phones = [phone for phone in all_phones if phone not in attributed_phones]
        
        unattributed_contacts = {
            'emails': unattributed_emails,
            'phones': unattributed_phones
        }
        
        result = ContactAttributionResult(
            executives=executive_contacts,
            attribution_success=attributed_contacts > 0,
            attribution_accuracy=attribution_accuracy,
            total_contacts_found=total_contacts,
            attributed_contacts=attributed_contacts,
            unattributed_contacts=unattributed_contacts
        )
        
        logger.info(f"Attribution complete: {attributed_contacts}/{total_contacts} contacts attributed ({attribution_accuracy:.2%})")
        
        return result

    def _extract_all_emails(self, content: str) -> List[str]:
        """Extract all email addresses from content"""
        emails = set()
        
        for pattern in self.email_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Handle tuple results from groups
                email = match if isinstance(match, str) else match[0] if match else ""
                if email and self._is_valid_email(email):
                    emails.add(email.lower())
        
        return list(emails)

    def _extract_all_phones(self, content: str) -> List[str]:
        """Extract all phone numbers from content"""
        phones = set()
        
        for pattern in self.phone_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Handle tuple results from groups
                phone = match if isinstance(match, str) else match[0] if match else ""
                if phone and self._is_valid_uk_phone(phone):
                    phones.add(self._normalize_phone(phone))
        
        return list(phones)

    def _extract_executive_names_from_content(self, content: str) -> List[Dict[str, str]]:
        """Extract executive names and titles from content when not provided"""
        executives = []
        
        # Enhanced name pattern with title context
        name_title_patterns = [
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)[,\s]*[-–—]?\s*(CEO|Managing Director|Director|Manager|Founder|Owner)',
            r'(CEO|Managing Director|Director|Manager|Founder|Owner)[:\s]*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)[,\s]+(is|was)\s+(our|the|a)\s+(CEO|Managing Director|Director|Manager|Founder|Owner)',
        ]
        
        for pattern in name_title_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    name, title = match
                    # Determine which is name and which is title
                    if any(word in name.lower() for word in ['ceo', 'director', 'manager', 'founder', 'owner']):
                        name, title = title, name
                    
                    executives.append({
                        'name': name.strip(),
                        'title': title.strip()
                    })
        
        # Fallback: extract just names and guess titles from context
        if not executives:
            name_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
            names = re.findall(name_pattern, content)
            
            for name in names[:5]:  # Limit to top 5 potential names
                executives.append({
                    'name': name,
                    'title': 'Unknown'
                })
        
        return executives

    def _attribute_contacts_to_executive(self, content: str, executive_name: str, 
                                       all_emails: List[str], all_phones: List[str]) -> Dict[str, Any]:
        """
        Attribute specific contacts to an executive using proximity analysis.
        
        Args:
            content: Full website content
            executive_name: Name of executive to find contacts for
            all_emails: All emails found on site
            all_phones: All phones found on site
            
        Returns:
            Attribution result with contact details and confidence
        """
        result = {
            'email': None,
            'email_confidence': 0.0,
            'phone': None,
            'phone_confidence': 0.0,
            'method': 'none',
            'overall_confidence': 0.0,
            'context': ''
        }
        
        # Find executive name positions in content
        name_positions = []
        for match in re.finditer(re.escape(executive_name), content, re.IGNORECASE):
            name_positions.append({
                'start': match.start(),
                'end': match.end(),
                'match': match.group()
            })
        
        if not name_positions:
            return result
        
        # For each name occurrence, check proximity to contacts
        best_email_match = None
        best_phone_match = None
        best_email_confidence = 0.0
        best_phone_confidence = 0.0
        attribution_context = ""
        
        for name_pos in name_positions:
            # Extract context around name (400 chars each side)
            context_start = max(0, name_pos['start'] - 400)
            context_end = min(len(content), name_pos['end'] + 400)
            context = content[context_start:context_end]
            
            # Check for emails in context
            for email in all_emails:
                if email in context.lower():
                    confidence = self._calculate_attribution_confidence(
                        executive_name, email, context, 'email'
                    )
                    if confidence > best_email_confidence:
                        best_email_match = email
                        best_email_confidence = confidence
                        attribution_context = context
            
            # Check for phones in context
            for phone in all_phones:
                # Normalize phone for comparison
                phone_variants = [phone, phone.replace(' ', ''), phone.replace('+44', '0')]
                for variant in phone_variants:
                    if variant in context:
                        confidence = self._calculate_attribution_confidence(
                            executive_name, phone, context, 'phone'
                        )
                        if confidence > best_phone_confidence:
                            best_phone_match = phone
                            best_phone_confidence = confidence
                            if not attribution_context:
                                attribution_context = context
        
        # Update result with best matches
        if best_email_match:
            result['email'] = best_email_match
            result['email_confidence'] = best_email_confidence
        
        if best_phone_match:
            result['phone'] = best_phone_match
            result['phone_confidence'] = best_phone_confidence
        
        # Determine attribution method
        if best_email_confidence > 0.7 or best_phone_confidence > 0.7:
            result['method'] = 'high_confidence_proximity'
        elif best_email_confidence > 0.4 or best_phone_confidence > 0.4:
            result['method'] = 'proximity_analysis'
        elif best_email_match or best_phone_match:
            result['method'] = 'weak_proximity'
        
        # Calculate overall confidence
        result['overall_confidence'] = max(best_email_confidence, best_phone_confidence)
        result['context'] = attribution_context[:200]  # Truncate for storage
        
        return result

    def _calculate_attribution_confidence(self, name: str, contact: str, context: str, contact_type: str) -> float:
        """Calculate confidence score for contact attribution"""
        confidence = 0.0
        context_lower = context.lower()
        name_lower = name.lower()
        
        # Base proximity score
        name_index = context_lower.find(name_lower)
        contact_index = context_lower.find(contact.lower())
        
        if name_index != -1 and contact_index != -1:
            distance = abs(name_index - contact_index)
            # Closer = higher confidence
            if distance < 50:
                confidence += 0.6
            elif distance < 100:
                confidence += 0.4
            elif distance < 200:
                confidence += 0.2
            else:
                confidence += 0.1
        
        # Direct attribution indicators
        direct_patterns = [
            f'{name_lower}.*{contact.lower()}',
            f'{contact.lower()}.*{name_lower}',
            f'{name_lower}[:\s-]*{contact.lower()}',
            f'{contact.lower()}[:\s-]*{name_lower}'
        ]
        
        for pattern in direct_patterns:
            if re.search(pattern, context_lower):
                confidence += 0.3
                break
        
        # Email signature patterns (for emails)
        if contact_type == 'email':
            signature_indicators = ['regards', 'best', 'sincerely', 'yours truly', 'from']
            for indicator in signature_indicators:
                if indicator in context_lower:
                    confidence += 0.2
                    break
        
        # Contact section indicators
        contact_indicators = ['contact', 'reach', 'email', 'phone', 'call', 'get in touch']
        for indicator in contact_indicators:
            if indicator in context_lower:
                confidence += 0.1
                break
        
        return min(confidence, 1.0)

    def _classify_seniority(self, title: str) -> str:
        """Classify executive seniority tier based on title"""
        title_lower = title.lower()
        
        for tier_name, titles in self.executive_titles.items():
            for exec_title in titles:
                if exec_title in title_lower:
                    return tier_name
        
        return 'tier_3'  # Default to lowest tier

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        return bool(re.match(email_pattern, email))

    def _is_valid_uk_phone(self, phone: str) -> bool:
        """Validate UK phone number format"""
        # Remove spaces and formatting
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        
        # UK phone patterns
        uk_patterns = [
            r'^0[1-9]\d{8,9}$',      # UK landline
            r'^07\d{9}$',            # UK mobile
            r'^\+44[1-9]\d{8,9}$',   # International
        ]
        
        for pattern in uk_patterns:
            if re.match(pattern, cleaned):
                return True
        
        return False

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number format"""
        # Remove common formatting
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Convert international to UK format
        if cleaned.startswith('+44'):
            cleaned = '0' + cleaned[3:]
        
        return cleaned

    def get_attribution_summary(self, result: ContactAttributionResult) -> Dict[str, Any]:
        """Generate summary of attribution results"""
        executives_with_contacts = sum(1 for exec in result.executives 
                                     if exec.email or exec.phone)
        
        avg_confidence = sum(exec.overall_confidence for exec in result.executives) / len(result.executives) if result.executives else 0
        
        return {
            'total_executives': len(result.executives),
            'executives_with_contacts': executives_with_contacts,
            'attribution_rate': (executives_with_contacts / len(result.executives) * 100) if result.executives else 0,
            'overall_attribution_accuracy': result.attribution_accuracy * 100,
            'average_confidence': avg_confidence,
            'total_contacts_found': result.total_contacts_found,
            'attributed_contacts': result.attributed_contacts,
            'unattributed_emails': len(result.unattributed_contacts['emails']),
            'unattributed_phones': len(result.unattributed_contacts['phones'])
        } 