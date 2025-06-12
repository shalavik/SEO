"""
Email Discovery Strategy

Combines pattern generation, SMTP verification, and ranking logic
to find the most likely email addresses for contacts.
"""

import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from enrichment_service.core.models import (
    EmailDiscovery, EmailPattern, EmailCandidate, EmailValidation
)
from enrichment_service.utils.email_patterns import EmailPatternGenerator
from enrichment_service.services.smtp_verify import AsyncSMTPVerifier

class EmailDiscoveryStrategy:
    """Email discovery and validation strategy"""
    
    def __init__(self, smtp_timeout: int = 10, max_concurrent_verifications: int = 3):
        self.pattern_generator = EmailPatternGenerator()
        self.smtp_verifier = AsyncSMTPVerifier(
            timeout=smtp_timeout, 
            max_concurrent=max_concurrent_verifications
        )
        
        # Thresholds for confidence
        self.high_confidence_threshold = 0.8
        self.medium_confidence_threshold = 0.6
        self.verification_weight = 0.7  # Weight of SMTP verification in final score
        self.pattern_weight = 0.3      # Weight of pattern confidence
    
    async def discover_domain_patterns(self, domain: str, 
                                     known_emails: List[str] = None) -> EmailDiscovery:
        """Discover email patterns for a domain"""
        start_time = datetime.utcnow()
        
        if not known_emails:
            known_emails = []
        
        # Discover patterns from known emails
        discovered_patterns = self.pattern_generator.discover_domain_patterns(known_emails, domain)
        
        # Get MX records for the domain
        mx_records = await self.smtp_verifier._get_mx_records(domain)
        
        # Test for catch-all (if we have MX records)
        catch_all = None
        if mx_records:
            catch_all = await self._test_domain_catch_all(domain, mx_records[0])
        
        # Convert discovered patterns to our model format
        patterns = []
        for pattern_data in discovered_patterns:
            pattern = EmailPattern(
                pattern=pattern_data['pattern'],
                confidence=pattern_data['confidence'],
                examples=pattern_data['examples']
            )
            patterns.append(pattern)
        
        # Calculate overall domain confidence
        domain_confidence = self._calculate_domain_confidence(patterns, mx_records, catch_all)
        
        return EmailDiscovery(
            domain=domain,
            patterns=patterns,
            catch_all=catch_all,
            mx_records=mx_records,
            common_emails=known_emails,
            confidence=domain_confidence
        )
    
    async def generate_email_candidates(self, domain: str, first_name: str, last_name: str,
                                      known_patterns: List[EmailPattern] = None,
                                      verify_emails: bool = True,
                                      max_candidates: int = 10) -> List[EmailCandidate]:
        """Generate and rank email candidates for a person"""
        
        # Generate candidates using patterns
        pattern_candidates = self.pattern_generator.generate_email_candidates(
            first_name, last_name, domain, include_all_patterns=True
        )
        
        # Limit candidates
        pattern_candidates = pattern_candidates[:max_candidates]
        
        candidates = []
        
        for candidate_data in pattern_candidates:
            email = candidate_data['email']
            pattern_name = candidate_data['pattern']
            pattern_confidence = candidate_data['confidence']
            
            # Adjust confidence based on known domain patterns
            adjusted_confidence = self._adjust_confidence_for_domain(
                pattern_confidence, pattern_name, known_patterns
            )
            
            # Create initial candidate
            candidate = EmailCandidate(
                email=email,
                pattern_used=pattern_name,
                confidence=adjusted_confidence,
                source="pattern_generation"
            )
            
            # Verify email if requested
            if verify_emails:
                verification_result = await self.smtp_verifier.verify_email(
                    email, check_deliverability=True
                )
                
                # Convert to our validation model
                validation = self.smtp_verifier.to_email_validation(verification_result)
                candidate.validation = validation
                
                # Update confidence based on verification
                candidate.confidence = self._calculate_final_confidence(
                    pattern_confidence, verification_result
                )
                candidate.source = "pattern_and_verification"
            
            candidates.append(candidate)
        
        # Sort by confidence
        candidates.sort(key=lambda x: x.confidence, reverse=True)
        
        return candidates
    
    async def find_best_email(self, domain: str, first_name: str, last_name: str,
                            known_patterns: List[EmailPattern] = None,
                            confidence_threshold: float = 0.6) -> Optional[EmailCandidate]:
        """Find the single best email candidate"""
        
        candidates = await self.generate_email_candidates(
            domain, first_name, last_name, known_patterns, verify_emails=True, max_candidates=5
        )
        
        if not candidates:
            return None
        
        # Return the highest confidence candidate if it meets threshold
        best_candidate = candidates[0]
        if best_candidate.confidence >= confidence_threshold:
            return best_candidate
        
        return None
    
    async def enrich_contact_email(self, contact_data: Dict, domain: str,
                                 domain_patterns: List[EmailPattern] = None) -> Dict:
        """Enrich contact data with discovered email"""
        
        # Extract names from contact data
        first_name = contact_data.get('first_name') or contact_data.get('personal', {}).get('first_name')
        last_name = contact_data.get('last_name') or contact_data.get('personal', {}).get('last_name')
        full_name = contact_data.get('full_name') or contact_data.get('personal', {}).get('full_name')
        
        # Try to extract names from full name if individual names not available
        if not first_name and not last_name and full_name:
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = name_parts[-1]
        
        if not first_name or not last_name:
            return contact_data  # Can't generate emails without names
        
        # Find best email
        best_email = await self.find_best_email(
            domain, first_name, last_name, domain_patterns
        )
        
        if best_email:
            # Enrich contact data
            enriched_contact = contact_data.copy()
            enriched_contact['email'] = best_email.email
            enriched_contact['email_confidence'] = best_email.confidence
            enriched_contact['email_pattern'] = best_email.pattern_used
            enriched_contact['email_validation'] = best_email.validation.dict() if best_email.validation else None
            enriched_contact['email_source'] = best_email.source
            
            return enriched_contact
        
        return contact_data
    
    def _adjust_confidence_for_domain(self, pattern_confidence: float, 
                                    pattern_name: str, 
                                    known_patterns: List[EmailPattern]) -> float:
        """Adjust pattern confidence based on known domain patterns"""
        if not known_patterns:
            return pattern_confidence
        
        # Find matching domain pattern
        for domain_pattern in known_patterns:
            if domain_pattern.pattern == pattern_name:
                # Weighted average of pattern confidence and domain-specific confidence
                return (pattern_confidence * 0.3) + (domain_pattern.confidence * 0.7)
        
        # Pattern not found in domain patterns - reduce confidence
        return pattern_confidence * 0.8
    
    def _calculate_final_confidence(self, pattern_confidence: float, 
                                  verification_result) -> float:
        """Calculate final confidence combining pattern and verification results"""
        
        # Base confidence from pattern
        pattern_score = pattern_confidence
        
        # Verification score
        verification_score = 0.0
        if verification_result.is_valid and verification_result.is_deliverable:
            verification_score = 0.9
        elif verification_result.is_valid and verification_result.mx_records:
            verification_score = 0.7
        elif verification_result.is_valid:
            verification_score = 0.5
        
        # Penalties
        if verification_result.is_risky:
            verification_score *= 0.7
        if verification_result.disposable:
            verification_score *= 0.3
        if verification_result.role_account:
            verification_score *= 0.6
        
        # Weighted combination
        final_confidence = (
            pattern_score * self.pattern_weight + 
            verification_score * self.verification_weight
        )
        
        return min(final_confidence, 1.0)
    
    def _calculate_domain_confidence(self, patterns: List[EmailPattern], 
                                   mx_records: List[str], 
                                   catch_all: Optional[bool]) -> float:
        """Calculate overall confidence for domain email discovery"""
        
        base_confidence = 0.0
        
        # MX records boost confidence
        if mx_records:
            base_confidence += 0.3
        
        # Pattern data boosts confidence
        if patterns:
            # Average pattern confidence
            avg_pattern_confidence = sum(p.confidence for p in patterns) / len(patterns)
            base_confidence += avg_pattern_confidence * 0.5
        
        # Catch-all detection
        if catch_all is True:
            base_confidence *= 0.8  # Reduce confidence for catch-all domains
        elif catch_all is False:
            base_confidence += 0.2  # Boost confidence for non-catch-all
        
        return min(base_confidence, 1.0)
    
    async def _test_domain_catch_all(self, domain: str, mx_server: str) -> Optional[bool]:
        """Test if domain has catch-all email enabled"""
        try:
            # Test with a definitely non-existent email
            test_email = f"definitely-not-real-test-{datetime.utcnow().timestamp()}@{domain}"
            result = await self.smtp_verifier.verify_email(test_email, check_deliverability=True)
            
            # If it's deliverable, it's likely catch-all
            return result.is_deliverable
            
        except Exception:
            return None
    
    async def bulk_email_discovery(self, contacts: List[Dict], domain: str,
                                 domain_patterns: List[EmailPattern] = None) -> List[Dict]:
        """Discover emails for multiple contacts in parallel"""
        
        # Limit concurrent operations
        semaphore = asyncio.Semaphore(3)
        
        async def enrich_single_contact(contact):
            async with semaphore:
                return await self.enrich_contact_email(contact, domain, domain_patterns)
        
        # Process contacts concurrently
        tasks = [enrich_single_contact(contact) for contact in contacts]
        enriched_contacts = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_contacts = []
        for result in enriched_contacts:
            if isinstance(result, Exception):
                continue
            valid_contacts.append(result)
        
        return valid_contacts
    
    def get_verification_stats(self) -> Dict:
        """Get email verification statistics"""
        return self.smtp_verifier.get_cache_stats()
    
    def clear_caches(self):
        """Clear all caches"""
        self.smtp_verifier.clear_cache() 