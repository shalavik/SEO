"""
Executive Email Enricher

Enhanced email generation and verification for executive contacts.
P1.2 ENHANCEMENT: Improved email generation with domain-specific strategies
P2.4 ENHANCEMENT: Advanced email verification and validation

Features:
- Multiple email pattern generation
- Domain-specific email strategies
- P2.4: Email verification and validation
- P2.4: MX record validation
- P2.4: Domain validation
- P2.4: Enhanced confidence scoring
- Zero-cost architecture (no external APIs)
"""

import asyncio
import logging
import re
import socket
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import dns.resolver
import dns.exception

from ..models import ExecutiveContact
from ..config import get_processing_config

logger = logging.getLogger(__name__)

@dataclass
class EmailValidationResult:
    """P2.4: Email validation result structure"""
    email: str
    is_valid_format: bool = False
    domain_exists: bool = False
    mx_record_exists: bool = False
    confidence: float = 0.0
    validation_notes: List[str] = None
    
    def __post_init__(self):
        if self.validation_notes is None:
            self.validation_notes = []

class ExecutiveEmailEnricher:
    """Enhanced email enricher with P1.2 and P2.4 improvements"""
    
    def __init__(self):
        self.processing_config = get_processing_config()
        
        # P1.2: Email generation patterns
        self.email_patterns = [
            "{first}.{last}@{domain}",
            "{first}@{domain}",
            "{first}{last}@{domain}",
            "{first_initial}{last}@{domain}",
            "{first_initial}.{last}@{domain}",
            "{last}@{domain}",
            "{first}_{last}@{domain}",
            "{first}-{last}@{domain}",
            "{last}.{first}@{domain}",
            "{last}{first_initial}@{domain}"
        ]
        
        # P2.4: Email validation patterns
        self.email_format_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        
        # P2.4: Common invalid email patterns
        self.invalid_patterns = [
            r'.*noreply.*',
            r'.*no-reply.*',
            r'.*donotreply.*',
            r'.*test.*@.*',
            r'.*example.*@.*',
            r'.*admin.*@.*',
            r'.*info.*@.*',
            r'.*support.*@.*',
            r'.*sales.*@.*',
            r'.*contact.*@.*'
        ]
        
        # P2.4: Domain validation cache
        self.domain_cache = {}
        self.mx_cache = {}
        
        # P2.4: Rate limiting for DNS queries
        self.last_dns_query = 0
        self.dns_delay = 0.1  # 100ms between DNS queries
        
        logger.info("Enrichment service email strategy initialized")
    
    async def enrich_single_executive_email(self, executive: ExecutiveContact, domain: str) -> ExecutiveContact:
        """P1.2 ENHANCED: Generate and verify email for a single executive"""
        try:
            # Generate potential email addresses
            potential_emails = self._generate_email_addresses(executive, domain)
            
            # P2.4 ENHANCEMENT: Validate and score emails
            validated_emails = []
            for email in potential_emails:
                validation_result = await self._validate_email(email)
                if validation_result.is_valid_format:
                    validated_emails.append((email, validation_result))
            
            if validated_emails:
                # Sort by confidence and select best email
                validated_emails.sort(key=lambda x: x[1].confidence, reverse=True)
                best_email, validation_result = validated_emails[0]
                
                # Update executive with best email
                executive.email = best_email
                executive.email_confidence = validation_result.confidence
                
                logger.info(f"Discovered email {best_email} for {executive.full_name} (confidence: {validation_result.confidence:.2f})")
                
                # P2.4: Add validation metadata
                if hasattr(executive, 'email_validation_notes'):
                    executive.email_validation_notes = validation_result.validation_notes
                
            return executive
            
        except Exception as e:
            logger.warning(f"Email enrichment failed for {executive.full_name}: {e}")
            return executive
    
    def _generate_email_addresses(self, executive: ExecutiveContact, domain: str) -> List[str]:
        """Generate potential email addresses for executive"""
        emails = []
        
        try:
            # Clean names for email generation
            first_name = self._clean_name_for_email(executive.first_name)
            last_name = self._clean_name_for_email(executive.last_name)
            first_initial = first_name[0].lower() if first_name else ""
            
            # Clean domain
            clean_domain = domain.lower().replace('www.', '').strip()
            
            # Generate emails using patterns
            for pattern in self.email_patterns:
                try:
                    email = pattern.format(
                        first=first_name,
                        last=last_name,
                        first_initial=first_initial,
                        domain=clean_domain
                    )
                    
                    if email and email not in emails:
                        emails.append(email)
                        
                except (KeyError, IndexError):
                    continue
            
            # P1.2: Add seniority-based email patterns
            if executive.seniority_tier in ['tier_1', 'tier_2']:
                # Senior executives often have simpler emails
                priority_patterns = [
                    f"{first_name}@{clean_domain}",
                    f"{last_name}@{clean_domain}",
                    f"{first_initial}{last_name}@{clean_domain}"
                ]
                
                for email in priority_patterns:
                    if email and email not in emails:
                        emails.insert(0, email)  # Insert at beginning for priority
            
            return emails[:10]  # Limit to top 10 candidates
            
        except Exception as e:
            logger.debug(f"Email generation failed: {e}")
            return []
    
    def _clean_name_for_email(self, name: str) -> str:
        """Clean name for email address generation"""
        if not name:
            return ""
        
        # Remove special characters and convert to lowercase
        cleaned = re.sub(r'[^a-zA-Z]', '', name).lower()
        
        # Limit length
        return cleaned[:20] if cleaned else ""
    
    async def _validate_email(self, email: str) -> EmailValidationResult:
        """P2.4 ENHANCED: Validate email address with comprehensive checks"""
        result = EmailValidationResult(email=email)
        
        try:
            # Step 1: Format validation
            result.is_valid_format = self._validate_email_format(email)
            if not result.is_valid_format:
                result.validation_notes.append("Invalid email format")
                return result
            
            # Step 2: Check for invalid patterns
            if self._is_invalid_email_pattern(email):
                result.validation_notes.append("Matches invalid email pattern")
                result.confidence = 0.1
                return result
            
            # Step 3: Domain validation
            domain = email.split('@')[1]
            result.domain_exists = await self._validate_domain(domain)
            
            # Step 4: MX record validation
            if result.domain_exists:
                result.mx_record_exists = await self._validate_mx_record(domain)
            
            # Step 5: Calculate confidence score
            result.confidence = self._calculate_email_confidence(result)
            
            # Step 6: Add validation notes
            self._add_validation_notes(result)
            
            return result
            
        except Exception as e:
            logger.debug(f"Email validation failed for {email}: {e}")
            result.validation_notes.append(f"Validation error: {str(e)}")
            return result
    
    def _validate_email_format(self, email: str) -> bool:
        """Validate email format using regex"""
        if not email or len(email) > 254:
            return False
        
        return bool(self.email_format_pattern.match(email))
    
    def _is_invalid_email_pattern(self, email: str) -> bool:
        """Check if email matches invalid patterns"""
        email_lower = email.lower()
        
        for pattern in self.invalid_patterns:
            if re.match(pattern, email_lower):
                return True
        
        return False
    
    async def _validate_domain(self, domain: str) -> bool:
        """P2.4: Validate domain existence"""
        if domain in self.domain_cache:
            return self.domain_cache[domain]
        
        try:
            await self._enforce_dns_rate_limit()
            
            # Try to resolve domain
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._resolve_domain, 
                domain
            )
            
            self.domain_cache[domain] = result
            return result
            
        except Exception as e:
            logger.debug(f"Domain validation failed for {domain}: {e}")
            self.domain_cache[domain] = False
            return False
    
    def _resolve_domain(self, domain: str) -> bool:
        """Resolve domain using DNS"""
        try:
            # Try A record
            dns.resolver.resolve(domain, 'A')
            return True
        except dns.exception.DNSException:
            try:
                # Try AAAA record (IPv6)
                dns.resolver.resolve(domain, 'AAAA')
                return True
            except dns.exception.DNSException:
                return False
    
    async def _validate_mx_record(self, domain: str) -> bool:
        """P2.4: Validate MX record existence"""
        if domain in self.mx_cache:
            return self.mx_cache[domain]
        
        try:
            await self._enforce_dns_rate_limit()
            
            # Try to resolve MX record
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._resolve_mx_record, 
                domain
            )
            
            self.mx_cache[domain] = result
            return result
            
        except Exception as e:
            logger.debug(f"MX validation failed for {domain}: {e}")
            self.mx_cache[domain] = False
            return False
    
    def _resolve_mx_record(self, domain: str) -> bool:
        """Resolve MX record using DNS"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except dns.exception.DNSException:
            return False
    
    def _calculate_email_confidence(self, result: EmailValidationResult) -> float:
        """P2.4: Calculate email confidence score"""
        confidence = 0.0
        
        # Base confidence for valid format
        if result.is_valid_format:
            confidence += 0.3
        
        # Boost for domain existence
        if result.domain_exists:
            confidence += 0.4
        
        # Boost for MX record
        if result.mx_record_exists:
            confidence += 0.3
        
        # Pattern-based adjustments
        email_lower = result.email.lower()
        
        # Boost for common executive patterns
        if any(pattern in email_lower for pattern in ['ceo', 'director', 'founder', 'owner']):
            confidence += 0.1
        
        # Boost for simple patterns (first@domain, last@domain)
        if '@' in result.email:
            local_part = result.email.split('@')[0]
            if len(local_part) <= 10 and '.' not in local_part:
                confidence += 0.05
        
        # Penalty for complex patterns
        if '.' in result.email.split('@')[0] and '_' in result.email.split('@')[0]:
            confidence -= 0.05
        
        # Cap confidence at 1.0
        return min(1.0, max(0.0, confidence))
    
    def _add_validation_notes(self, result: EmailValidationResult):
        """Add validation notes to result"""
        if result.is_valid_format:
            result.validation_notes.append("Valid email format")
        
        if result.domain_exists:
            result.validation_notes.append("Domain exists")
        else:
            result.validation_notes.append("Domain does not exist")
        
        if result.mx_record_exists:
            result.validation_notes.append("MX record exists")
        else:
            result.validation_notes.append("No MX record found")
        
        if result.confidence >= 0.8:
            result.validation_notes.append("High confidence email")
        elif result.confidence >= 0.6:
            result.validation_notes.append("Medium confidence email")
        else:
            result.validation_notes.append("Low confidence email")
    
    async def _enforce_dns_rate_limit(self):
        """Enforce rate limiting for DNS queries"""
        current_time = time.time()
        time_since_last = current_time - self.last_dns_query
        
        if time_since_last < self.dns_delay:
            sleep_time = self.dns_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_dns_query = time.time()
    
    async def enrich_executives_emails(self, executives: List[ExecutiveContact], domain: str) -> List[ExecutiveContact]:
        """Enrich multiple executives with email addresses"""
        enriched_executives = []
        
        for executive in executives:
            enriched_executive = await self.enrich_single_executive_email(executive, domain)
            enriched_executives.append(enriched_executive)
            
            # Small delay between enrichments
            await asyncio.sleep(0.1)
        
        return enriched_executives
    
    def get_email_statistics(self) -> Dict:
        """Get email enrichment statistics"""
        return {
            "domain_cache_size": len(self.domain_cache),
            "mx_cache_size": len(self.mx_cache),
            "valid_domains": sum(1 for v in self.domain_cache.values() if v),
            "valid_mx_records": sum(1 for v in self.mx_cache.values() if v)
        }

# Usage example
async def test_email_enrichment():
    """Test function for email enrichment"""
    enricher = ExecutiveEmailEnricher()
    
    # Create test executive
    executive = ExecutiveContact(
        first_name="Jack",
        last_name="Plumber",
        full_name="Jack Plumber",
        title="Master Plumber",
        company_name="Jack The Plumber",
        email=None,
        phone=None,
        bio="",
        discovery_sources=["test"],
        confidence=0.8,
        seniority_tier="tier_1",
        company_domain="jacktheplumber.co.uk"
    )
    
    # Enrich with email
    enriched = await enricher.enrich_single_executive_email(executive, "jacktheplumber.co.uk")
    
    print(f"Generated email: {enriched.email}")
    print(f"Email confidence: {enriched.email_confidence}")

if __name__ == "__main__":
    asyncio.run(test_email_enrichment()) 