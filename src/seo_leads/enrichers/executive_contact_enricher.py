"""
Executive Contact Enrichment Engine

Comprehensive contact enrichment system for executive discovery.
Transforms incomplete executive records into complete contact profiles.

Features:
- Email Discovery & Generation
- Phone Number Discovery & Validation
- LinkedIn Profile Matching
- Contact Information Verification
- Multi-source Contact Fusion
"""

import asyncio
import logging
import re
import time
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ..models import ExecutiveContact
from ..config import get_processing_config

logger = logging.getLogger(__name__)

@dataclass
class ContactEnrichmentResult:
    """Result of contact enrichment process"""
    original_contact: ExecutiveContact
    enriched_contact: ExecutiveContact
    enrichment_sources: List[str]
    confidence_improvement: float
    processing_time: float

@dataclass
class EmailCandidate:
    """Email candidate with confidence score"""
    email: str
    confidence: float
    source: str
    validation_status: str = "unknown"

@dataclass
class PhoneCandidate:
    """Phone candidate with confidence score"""
    phone: str
    confidence: float
    source: str
    format_type: str = "unknown"  # mobile, landline, etc.

class EmailDiscoveryEngine:
    """
    Advanced email discovery engine using multiple strategies.
    """
    
    def __init__(self):
        # Email pattern templates
        self.email_patterns = [
            "{first}@{domain}",
            "{first}.{last}@{domain}",
            "{first}_{last}@{domain}",
            "{first}{last}@{domain}",
            "{last}@{domain}",
            "{first_initial}{last}@{domain}",
            "{first}{last_initial}@{domain}",
            "{first_initial}.{last}@{domain}",
            "{first_initial}_{last}@{domain}"
        ]
        
        # Executive-specific patterns
        self.executive_patterns = [
            "ceo@{domain}",
            "director@{domain}",
            "manager@{domain}",
            "owner@{domain}",
            "founder@{domain}",
            "admin@{domain}",
            "info@{domain}",
            "contact@{domain}"
        ]
        
        # Common email validation patterns
        self.email_regex = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
    
    async def discover_executive_emails(self, executive: ExecutiveContact, 
                                      company_domain: str) -> List[EmailCandidate]:
        """
        Discover potential email addresses for an executive.
        
        Args:
            executive: ExecutiveContact object
            company_domain: Company domain for email generation
            
        Returns:
            List of EmailCandidate objects
        """
        candidates = []
        
        # Generate pattern-based emails
        pattern_emails = self._generate_pattern_emails(executive, company_domain)
        candidates.extend(pattern_emails)
        
        # Generate executive role-based emails
        role_emails = self._generate_role_based_emails(executive, company_domain)
        candidates.extend(role_emails)
        
        # Search for emails on company website
        website_emails = await self._search_website_emails(executive, company_domain)
        candidates.extend(website_emails)
        
        # Remove duplicates and sort by confidence
        unique_candidates = self._deduplicate_emails(candidates)
        return sorted(unique_candidates, key=lambda x: x.confidence, reverse=True)
    
    def _generate_pattern_emails(self, executive: ExecutiveContact, 
                               domain: str) -> List[EmailCandidate]:
        """Generate emails using common patterns"""
        candidates = []
        
        if not executive.first_name or not executive.last_name:
            return candidates
        
        # Normalize names
        first = executive.first_name.lower().strip()
        last = executive.last_name.lower().strip()
        first_initial = first[0] if first else ""
        last_initial = last[0] if last else ""
        
        # Generate emails from patterns
        for pattern in self.email_patterns:
            try:
                email = pattern.format(
                    first=first,
                    last=last,
                    first_initial=first_initial,
                    last_initial=last_initial,
                    domain=domain
                )
                
                if self._is_valid_email_format(email):
                    confidence = self._calculate_pattern_confidence(pattern, executive)
                    candidates.append(EmailCandidate(
                        email=email,
                        confidence=confidence,
                        source="pattern_generation"
                    ))
                    
            except Exception:
                continue
        
        return candidates
    
    def _generate_role_based_emails(self, executive: ExecutiveContact, 
                                  domain: str) -> List[EmailCandidate]:
        """Generate emails based on executive role"""
        candidates = []
        
        if not executive.title:
            return candidates
        
        title_lower = executive.title.lower()
        
        # Map titles to email patterns
        role_mappings = {
            'ceo': ['ceo', 'chief.executive'],
            'chief executive': ['ceo', 'chief.executive'],
            'founder': ['founder', 'ceo'],
            'owner': ['owner', 'ceo'],
            'managing director': ['md', 'managing.director', 'director'],
            'director': ['director'],
            'manager': ['manager'],
            'head of': ['head']
        }
        
        # Find matching roles
        for role, patterns in role_mappings.items():
            if role in title_lower:
                for pattern in patterns:
                    email = f"{pattern}@{domain}"
                    if self._is_valid_email_format(email):
                        confidence = 0.8 if role in ['ceo', 'founder', 'owner'] else 0.6
                        candidates.append(EmailCandidate(
                            email=email,
                            confidence=confidence,
                            source="role_based_generation"
                        ))
        
        # Add generic executive emails
        for pattern in self.executive_patterns:
            email = pattern.format(domain=domain)
            if self._is_valid_email_format(email):
                candidates.append(EmailCandidate(
                    email=email,
                    confidence=0.4,
                    source="generic_executive"
                ))
        
        return candidates
    
    async def _search_website_emails(self, executive: ExecutiveContact, 
                                   domain: str) -> List[EmailCandidate]:
        """Search for emails on company website"""
        candidates = []
        
        try:
            # Search common pages for email addresses
            pages_to_search = [
                f"https://{domain}",
                f"https://{domain}/contact",
                f"https://{domain}/about",
                f"https://{domain}/team",
                f"https://www.{domain}",
                f"https://www.{domain}/contact",
                f"https://www.{domain}/about"
            ]
            
            for url in pages_to_search:
                try:
                    response = requests.get(url, timeout=10, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    
                    if response.status_code == 200:
                        emails = self._extract_emails_from_content(response.text, domain)
                        for email in emails:
                            # Check if email might belong to executive
                            confidence = self._calculate_email_executive_relevance(
                                email, executive
                            )
                            if confidence > 0.3:
                                candidates.append(EmailCandidate(
                                    email=email,
                                    confidence=confidence,
                                    source="website_extraction"
                                ))
                    
                    # Rate limiting
                    await asyncio.sleep(1)
                    
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Website email search failed: {e}")
        
        return candidates
    
    def _extract_emails_from_content(self, content: str, domain: str) -> List[str]:
        """Extract email addresses from HTML content"""
        emails = []
        
        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')
        text_content = soup.get_text()
        
        # Find email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        found_emails = re.findall(email_pattern, text_content)
        
        # Filter emails from the target domain
        for email in found_emails:
            if domain in email.lower() and self._is_valid_email_format(email):
                emails.append(email.lower())
        
        return list(set(emails))  # Remove duplicates
    
    def _calculate_pattern_confidence(self, pattern: str, executive: ExecutiveContact) -> float:
        """Calculate confidence score for pattern-based email"""
        base_confidence = 0.6
        
        # Boost confidence for common patterns
        if pattern in ["{first}@{domain}", "{first}.{last}@{domain}"]:
            base_confidence = 0.8
        elif pattern in ["{first}_{last}@{domain}", "{first}{last}@{domain}"]:
            base_confidence = 0.7
        
        # Boost for senior executives
        if executive.seniority_tier == "tier_1":
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _calculate_email_executive_relevance(self, email: str, 
                                           executive: ExecutiveContact) -> float:
        """Calculate how relevant an email is to the executive"""
        if not email or not executive.first_name:
            return 0.0
        
        email_local = email.split('@')[0].lower()
        first_name = executive.first_name.lower()
        last_name = executive.last_name.lower() if executive.last_name else ""
        
        # Check for name matches
        if first_name in email_local:
            confidence = 0.8
            if last_name and last_name in email_local:
                confidence = 0.9
            return confidence
        
        # Check for executive role indicators
        executive_indicators = ['ceo', 'director', 'manager', 'owner', 'founder']
        if any(indicator in email_local for indicator in executive_indicators):
            return 0.7
        
        # Generic business emails
        generic_indicators = ['info', 'contact', 'admin', 'office']
        if any(indicator in email_local for indicator in generic_indicators):
            return 0.4
        
        return 0.2
    
    def _is_valid_email_format(self, email: str) -> bool:
        """Validate email format"""
        return bool(self.email_regex.match(email))
    
    def _deduplicate_emails(self, candidates: List[EmailCandidate]) -> List[EmailCandidate]:
        """Remove duplicate email candidates"""
        seen_emails = set()
        unique_candidates = []
        
        for candidate in candidates:
            if candidate.email not in seen_emails:
                seen_emails.add(candidate.email)
                unique_candidates.append(candidate)
        
        return unique_candidates


class PhoneDiscoveryEngine:
    """
    Phone number discovery engine for UK businesses.
    """
    
    def __init__(self):
        # UK phone number patterns
        self.uk_phone_patterns = [
            r'(\+44\s?)?(\(?0\d{4}\)?\s?\d{3}\s?\d{3})',  # UK landline
            r'(\+44\s?)?(\(?0\d{3}\)?\s?\d{3}\s?\d{4})',  # UK mobile
            r'(\+44\s?)?\d{2}\s?\d{4}\s?\d{4,6}',         # General UK
            r'0\d{10,11}',                                # Simple UK format
        ]
        
        self.phone_regex = re.compile('|'.join(self.uk_phone_patterns))
    
    async def discover_executive_phones(self, executive: ExecutiveContact, 
                                      company_domain: str) -> List[PhoneCandidate]:
        """
        Discover phone numbers for an executive.
        
        Args:
            executive: ExecutiveContact object
            company_domain: Company domain
            
        Returns:
            List of PhoneCandidate objects
        """
        candidates = []
        
        # Search website for phone numbers
        website_phones = await self._search_website_phones(company_domain)
        candidates.extend(website_phones)
        
        # Search LinkedIn profile if available
        if executive.linkedin_url:
            linkedin_phones = await self._search_linkedin_phones(executive.linkedin_url)
            candidates.extend(linkedin_phones)
        
        # Remove duplicates and validate
        unique_candidates = self._deduplicate_phones(candidates)
        validated_candidates = [c for c in unique_candidates if self._is_valid_uk_phone(c.phone)]
        
        return sorted(validated_candidates, key=lambda x: x.confidence, reverse=True)
    
    async def _search_website_phones(self, domain: str) -> List[PhoneCandidate]:
        """Search for phone numbers on company website"""
        candidates = []
        
        try:
            # Search common pages
            pages_to_search = [
                f"https://{domain}",
                f"https://{domain}/contact",
                f"https://www.{domain}",
                f"https://www.{domain}/contact"
            ]
            
            for url in pages_to_search:
                try:
                    response = requests.get(url, timeout=10, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    
                    if response.status_code == 200:
                        phones = self._extract_phones_from_content(response.text)
                        for phone in phones:
                            candidates.append(PhoneCandidate(
                                phone=phone,
                                confidence=0.7,
                                source="website_extraction",
                                format_type=self._identify_phone_type(phone)
                            ))
                    
                    await asyncio.sleep(1)
                    
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Website phone search failed: {e}")
        
        return candidates
    
    async def _search_linkedin_phones(self, linkedin_url: str) -> List[PhoneCandidate]:
        """Search for phone numbers on LinkedIn profile"""
        # Note: This would require LinkedIn scraping which has limitations
        # For now, return empty list
        return []
    
    def _extract_phones_from_content(self, content: str) -> List[str]:
        """Extract phone numbers from HTML content"""
        phones = []
        
        # Parse HTML and get text
        soup = BeautifulSoup(content, 'html.parser')
        text_content = soup.get_text()
        
        # Find phone patterns
        matches = self.phone_regex.findall(text_content)
        
        for match in matches:
            if isinstance(match, tuple):
                # Join tuple elements
                phone = ''.join(match).strip()
            else:
                phone = match.strip()
            
            if phone and self._is_valid_uk_phone(phone):
                # Normalize phone format
                normalized_phone = self._normalize_uk_phone(phone)
                phones.append(normalized_phone)
        
        return list(set(phones))  # Remove duplicates
    
    def _is_valid_uk_phone(self, phone: str) -> bool:
        """Validate UK phone number format"""
        if not phone:
            return False
        
        # Remove spaces and formatting
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Check UK patterns
        uk_patterns = [
            r'^\+44\d{10}$',      # +44 followed by 10 digits
            r'^0\d{10}$',         # 0 followed by 10 digits
            r'^0\d{9}$',          # 0 followed by 9 digits
        ]
        
        return any(re.match(pattern, clean_phone) for pattern in uk_patterns)
    
    def _normalize_uk_phone(self, phone: str) -> str:
        """Normalize UK phone number to standard format"""
        # Remove all non-digit characters except +
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # Convert +44 to 0
        if clean_phone.startswith('+44'):
            clean_phone = '0' + clean_phone[3:]
        
        # Add spaces for readability
        if len(clean_phone) == 11 and clean_phone.startswith('0'):
            if clean_phone[1] == '7':  # Mobile
                return f"{clean_phone[:4]} {clean_phone[4:7]} {clean_phone[7:]}"
            else:  # Landline
                return f"{clean_phone[:5]} {clean_phone[5:8]} {clean_phone[8:]}"
        
        return clean_phone
    
    def _identify_phone_type(self, phone: str) -> str:
        """Identify phone type (mobile/landline)"""
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        if clean_phone.startswith('07') or clean_phone.startswith('4407'):
            return "mobile"
        elif clean_phone.startswith('0') or clean_phone.startswith('44'):
            return "landline"
        
        return "unknown"
    
    def _deduplicate_phones(self, candidates: List[PhoneCandidate]) -> List[PhoneCandidate]:
        """Remove duplicate phone candidates"""
        seen_phones = set()
        unique_candidates = []
        
        for candidate in candidates:
            normalized = self._normalize_uk_phone(candidate.phone)
            if normalized not in seen_phones:
                seen_phones.add(normalized)
                candidate.phone = normalized  # Update with normalized version
                unique_candidates.append(candidate)
        
        return unique_candidates


class ExecutiveContactEnricher:
    """
    Main executive contact enrichment engine.
    """
    
    def __init__(self):
        self.email_engine = EmailDiscoveryEngine()
        self.phone_engine = PhoneDiscoveryEngine()
        self.config = get_processing_config()
    
    async def enrich_executive_contacts(self, executive: ExecutiveContact) -> ExecutiveContact:
        """
        Enrich executive contact with additional information.
        
        Args:
            executive: ExecutiveContact to enrich
            
        Returns:
            Enriched ExecutiveContact
        """
        start_time = time.time()
        
        # Extract company domain
        company_domain = self._extract_company_domain(executive)
        
        # Create enriched copy
        enriched = ExecutiveContact(
            full_name=executive.full_name,
            first_name=executive.first_name,
            last_name=executive.last_name,
            title=executive.title,
            email=executive.email,
            phone=executive.phone,
            linkedin_url=executive.linkedin_url,
            company_name=executive.company_name,
            seniority_tier=executive.seniority_tier,
            confidence=executive.confidence,
            discovery_sources=executive.discovery_sources.copy(),
            discovery_method=executive.discovery_method,
            processing_time_ms=executive.processing_time_ms
        )
        
        enrichment_sources = []
        
        # Enrich email if missing
        if not enriched.email:
            email_candidates = await self.email_engine.discover_executive_emails(
                executive, company_domain
            )
            if email_candidates:
                best_email = email_candidates[0]
                enriched.email = best_email.email
                enrichment_sources.append(f"email_{best_email.source}")
                # Boost confidence for email discovery
                enriched.confidence = min(1.0, enriched.confidence + 0.1)
        
        # Enrich phone if missing
        if not enriched.phone:
            phone_candidates = await self.phone_engine.discover_executive_phones(
                executive, company_domain
            )
            if phone_candidates:
                best_phone = phone_candidates[0]
                enriched.phone = best_phone.phone
                enrichment_sources.append(f"phone_{best_phone.source}")
                # Boost confidence for phone discovery
                enriched.confidence = min(1.0, enriched.confidence + 0.05)
        
        # Update discovery sources
        if enrichment_sources:
            enriched.discovery_sources.extend(enrichment_sources)
            enriched.discovery_method = f"{enriched.discovery_method}_enriched"
        
        # Update processing time
        processing_time = time.time() - start_time
        enriched.processing_time_ms += int(processing_time * 1000)
        
        logger.info(f"Contact enrichment completed for {executive.full_name}: "
                   f"email={'✓' if enriched.email else '✗'}, "
                   f"phone={'✓' if enriched.phone else '✗'}")
        
        return enriched
    
    def _extract_company_domain(self, executive: ExecutiveContact) -> str:
        """Extract company domain for contact generation"""
        # Try to extract from existing email
        if executive.email and '@' in executive.email:
            return executive.email.split('@')[1]
        
        # Try to extract from LinkedIn URL
        if executive.linkedin_url:
            # This would require more sophisticated domain extraction
            pass
        
        # Fallback: generate domain from company name
        if executive.company_name:
            # Simple domain generation (this could be improved)
            company_clean = re.sub(r'[^a-zA-Z0-9\s]', '', executive.company_name)
            company_clean = company_clean.lower().replace(' ', '')
            return f"{company_clean}.co.uk"  # Assume UK domain
        
        return "example.com"  # Fallback domain 