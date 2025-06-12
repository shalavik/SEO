"""
Async SMTP Email Verifier

Verifies email addresses using SMTP without sending actual emails.
Implements timeouts, retry logic, and rate limiting.
"""

import asyncio
import socket
import ssl
import re
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

import aiosmtplib
import dns.resolver
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from enrichment_service.core.models import EmailValidation

@dataclass
class SMTPVerificationResult:
    """SMTP verification result"""
    email: str
    is_valid: bool
    is_deliverable: bool
    is_risky: bool
    verification_method: str
    mx_records: bool = False
    catch_all: Optional[bool] = None
    disposable: bool = False
    role_account: bool = False
    error_message: Optional[str] = None
    response_time_ms: Optional[int] = None

class AsyncSMTPVerifier:
    """Async SMTP email verifier with rate limiting and caching"""
    
    def __init__(self, timeout: int = 10, max_concurrent: int = 5):
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Cache for results and MX records
        self.verification_cache = {}
        self.mx_cache = {}
        self.cache_ttl = timedelta(hours=24)
        
        # Rate limiting per domain
        self.domain_last_check = {}
        self.domain_min_interval = timedelta(seconds=2)
        
        # Known disposable email domains
        self.disposable_domains = self._load_disposable_domains()
        
        # Known role account patterns
        self.role_patterns = [
            'admin', 'administrator', 'info', 'contact', 'support', 'help',
            'sales', 'marketing', 'noreply', 'no-reply', 'postmaster',
            'webmaster', 'hostmaster', 'abuse', 'security', 'privacy',
            'legal', 'hr', 'careers', 'jobs', 'billing', 'accounts'
        ]
    
    async def verify_email(self, email: str, check_deliverability: bool = True) -> SMTPVerificationResult:
        """Verify a single email address"""
        start_time = datetime.utcnow()
        
        # Basic format validation
        if not self._is_valid_email_format(email):
            return SMTPVerificationResult(
                email=email,
                is_valid=False,
                is_deliverable=False,
                is_risky=True,
                verification_method="syntax",
                error_message="Invalid email format"
            )
        
        email = email.lower().strip()
        domain = email.split('@')[1]
        
        # Check cache
        cache_key = f"{email}:{check_deliverability}"
        if cache_key in self.verification_cache:
            cached_result, cached_time = self.verification_cache[cache_key]
            if datetime.utcnow() - cached_time < self.cache_ttl:
                return cached_result
        
        # Check if disposable email
        is_disposable = self._is_disposable_email(domain)
        
        # Check if role account
        is_role = self._is_role_account(email)
        
        # Get MX records
        mx_records = await self._get_mx_records(domain)
        has_mx = bool(mx_records)
        
        if not has_mx:
            result = SMTPVerificationResult(
                email=email,
                is_valid=True,  # Format is valid
                is_deliverable=False,
                is_risky=True,
                verification_method="mx_lookup",
                mx_records=False,
                disposable=is_disposable,
                role_account=is_role,
                error_message="No MX records found"
            )
        else:
            # Perform SMTP verification if requested
            if check_deliverability:
                result = await self._smtp_verify(email, mx_records[0])
            else:
                result = SMTPVerificationResult(
                    email=email,
                    is_valid=True,
                    is_deliverable=True,  # Assume deliverable if MX exists
                    is_risky=False,
                    verification_method="mx_lookup",
                    mx_records=True
                )
            
            # Update with additional checks
            result.disposable = is_disposable
            result.role_account = is_role
            result.mx_records = has_mx
            
            # Adjust risk assessment
            if is_disposable or is_role:
                result.is_risky = True
        
        # Calculate response time
        response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        result.response_time_ms = response_time
        
        # Cache result
        self.verification_cache[cache_key] = (result, datetime.utcnow())
        
        return result
    
    async def verify_emails_batch(self, emails: List[str], 
                                check_deliverability: bool = True) -> List[SMTPVerificationResult]:
        """Verify multiple emails concurrently"""
        async with self.semaphore:
            tasks = [
                self.verify_email(email, check_deliverability) 
                for email in emails
            ]
            return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _get_mx_records(self, domain: str) -> List[str]:
        """Get MX records for domain"""
        if domain in self.mx_cache:
            mx_records, cached_time = self.mx_cache[domain]
            if datetime.utcnow() - cached_time < self.cache_ttl:
                return mx_records
        
        try:
            # Use asyncio to run DNS query in thread pool
            loop = asyncio.get_event_loop()
            mx_records = await loop.run_in_executor(
                None, self._dns_mx_lookup, domain
            )
            
            # Cache results
            self.mx_cache[domain] = (mx_records, datetime.utcnow())
            return mx_records
            
        except Exception as e:
            return []
    
    def _dns_mx_lookup(self, domain: str) -> List[str]:
        """Synchronous DNS MX lookup"""
        try:
            mx_records = []
            answers = dns.resolver.resolve(domain, 'MX')
            for answer in answers:
                mx_records.append(str(answer.exchange))
            return sorted(mx_records, key=lambda x: answers[mx_records.index(x)].preference)
        except Exception:
            return []
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        retry=retry_if_exception_type((aiosmtplib.SMTPException, socket.error, asyncio.TimeoutError))
    )
    async def _smtp_verify(self, email: str, mx_server: str) -> SMTPVerificationResult:
        """Perform SMTP verification"""
        domain = email.split('@')[1]
        
        # Rate limiting per domain
        await self._enforce_rate_limit(domain)
        
        try:
            # Connect to SMTP server
            smtp = aiosmtplib.SMTP(
                hostname=mx_server,
                port=25,
                timeout=self.timeout
            )
            
            async with smtp:
                # Establish connection
                await smtp.connect()
                
                # HELO/EHLO
                await smtp.helo('mail-checker.example.com')
                
                # MAIL FROM
                await smtp.mail('test@example.com')
                
                # RCPT TO - this is where we check deliverability
                try:
                    await smtp.rcpt(email)
                    # If we get here, email is likely deliverable
                    deliverable = True
                    catch_all = None
                    error_msg = None
                    
                except aiosmtplib.SMTPRecipientsRefused as e:
                    # Email rejected
                    deliverable = False
                    error_msg = str(e)
                    catch_all = False
                    
                except aiosmtplib.SMTPResponseException as e:
                    # Various SMTP responses
                    code = e.code
                    if code in [250, 251, 252]:  # Accepted responses
                        deliverable = True
                        catch_all = code == 252  # 252 indicates catch-all
                        error_msg = None
                    elif code in [450, 451, 452]:  # Temporary failures
                        deliverable = False
                        error_msg = f"Temporary failure: {e.message}"
                    else:  # Permanent failures
                        deliverable = False
                        error_msg = f"Permanent failure: {e.message}"
                        catch_all = False
                
                # Test for catch-all by trying a random email
                if catch_all is None:
                    catch_all = await self._test_catch_all(smtp, domain)
                
                return SMTPVerificationResult(
                    email=email,
                    is_valid=True,
                    is_deliverable=deliverable,
                    is_risky=not deliverable,
                    verification_method="smtp",
                    mx_records=True,
                    catch_all=catch_all,
                    error_message=error_msg
                )
                
        except (aiosmtplib.SMTPException, socket.error, asyncio.TimeoutError) as e:
            return SMTPVerificationResult(
                email=email,
                is_valid=True,
                is_deliverable=False,
                is_risky=True,
                verification_method="smtp",
                mx_records=True,
                error_message=f"SMTP error: {str(e)}"
            )
        except Exception as e:
            return SMTPVerificationResult(
                email=email,
                is_valid=True,
                is_deliverable=False,
                is_risky=True,
                verification_method="smtp",
                mx_records=True,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def _test_catch_all(self, smtp: aiosmtplib.SMTP, domain: str) -> bool:
        """Test if domain has catch-all enabled"""
        try:
            # Try a random email that definitely doesn't exist
            random_email = f"definitely-not-real-{datetime.utcnow().timestamp()}@{domain}"
            await smtp.rcpt(random_email)
            return True  # If accepted, it's likely catch-all
        except aiosmtplib.SMTPException:
            return False  # If rejected, no catch-all
    
    async def _enforce_rate_limit(self, domain: str):
        """Enforce rate limiting per domain"""
        now = datetime.utcnow()
        if domain in self.domain_last_check:
            time_since_last = now - self.domain_last_check[domain]
            if time_since_last < self.domain_min_interval:
                sleep_time = (self.domain_min_interval - time_since_last).total_seconds()
                await asyncio.sleep(sleep_time)
        
        self.domain_last_check[domain] = now
    
    def _is_valid_email_format(self, email: str) -> bool:
        """Validate email format"""
        if not email or '@' not in email:
            return False
        
        pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _is_disposable_email(self, domain: str) -> bool:
        """Check if domain is a disposable email provider"""
        return domain.lower() in self.disposable_domains
    
    def _is_role_account(self, email: str) -> bool:
        """Check if email appears to be a role account"""
        local_part = email.split('@')[0].lower()
        
        # Check exact matches
        if local_part in self.role_patterns:
            return True
        
        # Check if starts with role pattern
        for pattern in self.role_patterns:
            if local_part.startswith(pattern):
                return True
        
        return False
    
    def _load_disposable_domains(self) -> Set[str]:
        """Load known disposable email domains"""
        # Common disposable email domains
        return {
            '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
            'tempmail.org', 'throwaway.email', 'temp-mail.org',
            'dispostable.com', 'yopmail.com', 'maildrop.cc',
            'temp-mail.io', 'mohmal.com', 'sharklasers.com'
        }
    
    def to_email_validation(self, result: SMTPVerificationResult) -> EmailValidation:
        """Convert SMTPVerificationResult to EmailValidation model"""
        return EmailValidation(
            is_valid=result.is_valid,
            is_deliverable=result.is_deliverable,
            is_risky=result.is_risky,
            validation_method=result.verification_method,
            mx_records=result.mx_records,
            catch_all=result.catch_all,
            disposable=result.disposable,
            role_account=result.role_account
        )
    
    def clear_cache(self):
        """Clear verification and MX caches"""
        self.verification_cache.clear()
        self.mx_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'verification_cache_size': len(self.verification_cache),
            'mx_cache_size': len(self.mx_cache),
            'domains_rate_limited': len(self.domain_last_check)
        } 