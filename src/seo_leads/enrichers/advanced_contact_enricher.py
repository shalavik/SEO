"""
Advanced Contact Enrichment System
Comprehensive contact discovery and validation for executives
"""

import re
import requests
import time
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import dns.resolver
from email_validator import validate_email, EmailNotValidError

from ..models.executive_contact import ExecutiveContact

logger = logging.getLogger(__name__)

@dataclass
class ContactEnrichmentResult:
    """Result from contact enrichment process"""
    email_found: bool
    phone_found: bool
    linkedin_found: bool
    email_confidence: float
    phone_confidence: float
    linkedin_confidence: float
    enrichment_sources: List[str]
    validation_results: Dict[str, bool]

class AdvancedContactEnricher:
    """
    Advanced contact enrichment system for executive contacts
    Discovers and validates email, phone, and LinkedIn profiles
    """
    
    def __init__(self):
        # Email pattern templates
        self.email_patterns = [
            "{first}.{last}@{domain}",
            "{first}@{domain}",
            "{first}{last}@{domain}",
            "{first_initial}{last}@{domain}",
            "{first_initial}.{last}@{domain}",
            "{last}@{domain}",
            "info@{domain}",
            "contact@{domain}",
            "admin@{domain}"
        ]
        
        # UK phone number patterns
        self.uk_phone_patterns = [
            r'\b(?:0|\+44\s?)\d{2,4}\s?\d{3,4}\s?\d{3,4}\b',  # Standard UK format
            r'\b(?:0|\+44\s?)(?:1|2|3|7|8)\d{8,9}\b',         # UK mobile/landline
            r'\b(?:0|\+44\s?)800\s?\d{6}\b',                  # Freephone
            r'\b(?:0|\+44\s?)845\s?\d{6}\b',                  # Local rate
            r'\b(?:0|\+44\s?)20\s?\d{4}\s?\d{4}\b'            # London
        ]
        
        # LinkedIn profile patterns
        self.linkedin_patterns = [
            r'linkedin\.com/in/([a-zA-Z0-9\-]+)',
            r'uk\.linkedin\.com/in/([a-zA-Z0-9\-]+)',
            r'linkedin\.com/pub/([a-zA-Z0-9\-]+)'
        ]
        
        # Common contact page URLs
        self.contact_page_urls = [
            "/contact",
            "/contact-us",
            "/about",
            "/about-us",
            "/team",
            "/staff",
            "/management",
            "/directors",
            "/leadership"
        ]
        
        # Request session for efficiency
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def enrich_executive_contact(
        self, 
        executive: ExecutiveContact, 
        company_url: str,
        company_name: str
    ) -> Tuple[ExecutiveContact, ContactEnrichmentResult]:
        """
        Enrich executive contact with comprehensive contact information
        
        Args:
            executive: Executive contact to enrich
            company_url: Company website URL
            company_name: Company name
            
        Returns:
            Tuple of enriched executive and enrichment result
        """
        logger.info(f"🔍 Enriching contact for {executive.first_name} {executive.last_name}")
        
        enrichment_result = ContactEnrichmentResult(
            email_found=False,
            phone_found=False,
            linkedin_found=False,
            email_confidence=0.0,
            phone_confidence=0.0,
            linkedin_confidence=0.0,
            enrichment_sources=[],
            validation_results={}
        )
        
        # Extract domain from company URL
        domain = self._extract_domain(company_url)
        if not domain:
            logger.warning(f"Could not extract domain from {company_url}")
            return executive, enrichment_result
        
        # Step 1: Email discovery and validation
        if not executive.email:
            email_result = self._discover_and_validate_email(
                executive.first_name, 
                executive.last_name, 
                domain,
                company_url
            )
            
            if email_result['email']:
                executive.email = email_result['email']
                enrichment_result.email_found = True
                enrichment_result.email_confidence = email_result['confidence']
                enrichment_result.enrichment_sources.extend(email_result['sources'])
                enrichment_result.validation_results['email'] = email_result['validated']
                
                logger.info(f"✅ Email discovered: {executive.email}")
        
        # Step 2: Phone number discovery
        if not executive.phone:
            phone_result = self._discover_phone_number(
                executive.first_name,
                executive.last_name,
                company_url
            )
            
            if phone_result['phone']:
                executive.phone = phone_result['phone']
                enrichment_result.phone_found = True
                enrichment_result.phone_confidence = phone_result['confidence']
                enrichment_result.enrichment_sources.extend(phone_result['sources'])
                enrichment_result.validation_results['phone'] = phone_result['validated']
                
                logger.info(f"✅ Phone discovered: {executive.phone}")
        
        # Step 3: LinkedIn profile discovery
        if not executive.linkedin_profile:
            linkedin_result = self._discover_linkedin_profile(
                executive.first_name,
                executive.last_name,
                company_name,
                company_url
            )
            
            if linkedin_result['profile']:
                executive.linkedin_profile = linkedin_result['profile']
                enrichment_result.linkedin_found = True
                enrichment_result.linkedin_confidence = linkedin_result['confidence']
                enrichment_result.enrichment_sources.extend(linkedin_result['sources'])
                enrichment_result.validation_results['linkedin'] = linkedin_result['validated']
                
                logger.info(f"✅ LinkedIn discovered: {executive.linkedin_profile}")
        
        # Step 4: Update overall confidence based on enrichment
        original_confidence = executive.overall_confidence
        enrichment_boost = self._calculate_enrichment_boost(enrichment_result)
        executive.overall_confidence = min(1.0, original_confidence + enrichment_boost)
        
        logger.info(f"📈 Confidence boosted: {original_confidence:.2f} → {executive.overall_confidence:.2f}")
        
        return executive, enrichment_result
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception as e:
            logger.error(f"Domain extraction error: {e}")
            return None
    
    def _discover_and_validate_email(
        self, 
        first_name: str, 
        last_name: str, 
        domain: str,
        company_url: str
    ) -> Dict:
        """Discover and validate email addresses"""
        result = {
            'email': None,
            'confidence': 0.0,
            'validated': False,
            'sources': []
        }
        
        # Generate potential email addresses
        potential_emails = self._generate_email_candidates(
            first_name, last_name, domain
        )
        
        # Method 1: Website scraping for email
        scraped_emails = self._scrape_website_emails(company_url, first_name, last_name)
        if scraped_emails:
            potential_emails = scraped_emails + potential_emails
            result['sources'].append('website_scraping')
        
        # Method 2: Validate email candidates
        for email in potential_emails:
            validation_result = self._validate_email_address(email)
            
            if validation_result['valid']:
                result['email'] = email
                result['confidence'] = validation_result['confidence']
                result['validated'] = True
                result['sources'].append('email_validation')
                break
        
        # Method 3: Pattern-based confidence if no validation
        if not result['email'] and potential_emails:
            # Use most likely pattern
            result['email'] = potential_emails[0]
            result['confidence'] = 0.6  # Medium confidence for pattern-based
            result['sources'].append('pattern_generation')
        
        return result
    
    def _generate_email_candidates(
        self, 
        first_name: str, 
        last_name: str, 
        domain: str
    ) -> List[str]:
        """Generate potential email address candidates"""
        candidates = []
        
        first_clean = re.sub(r'[^a-zA-Z]', '', first_name.lower())
        last_clean = re.sub(r'[^a-zA-Z]', '', last_name.lower())
        
        if not first_clean or not last_clean:
            return candidates
        
        # Generate emails from patterns
        for pattern in self.email_patterns:
            try:
                email = pattern.format(
                    first=first_clean,
                    last=last_clean,
                    first_initial=first_clean[0] if first_clean else '',
                    domain=domain
                )
                candidates.append(email)
            except (KeyError, IndexError):
                continue
        
        return candidates
    
    def _scrape_website_emails(
        self, 
        company_url: str, 
        first_name: str, 
        last_name: str
    ) -> List[str]:
        """Scrape website for email addresses"""
        emails = []
        
        try:
            # Check contact pages
            for contact_path in self.contact_page_urls:
                contact_url = urljoin(company_url, contact_path)
                
                try:
                    response = self.session.get(contact_url, timeout=10)
                    if response.status_code == 200:
                        page_emails = self._extract_emails_from_content(
                            response.text, first_name, last_name
                        )
                        emails.extend(page_emails)
                        
                        if emails:  # Found emails, no need to check more pages
                            break
                            
                except requests.RequestException:
                    continue
                    
                time.sleep(0.5)  # Rate limiting
                
        except Exception as e:
            logger.error(f"Website email scraping error: {e}")
        
        return emails
    
    def _extract_emails_from_content(
        self, 
        content: str, 
        first_name: str, 
        last_name: str
    ) -> List[str]:
        """Extract relevant emails from webpage content"""
        # Email regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        found_emails = re.findall(email_pattern, content)
        relevant_emails = []
        
        first_lower = first_name.lower()
        last_lower = last_name.lower()
        
        for email in found_emails:
            email_lower = email.lower()
            
            # Check if email contains person's name
            if (first_lower in email_lower or 
                last_lower in email_lower or
                first_lower[0] in email_lower):  # First initial
                relevant_emails.append(email)
        
        return relevant_emails
    
    def _validate_email_address(self, email: str) -> Dict:
        """Validate email address using multiple methods"""
        result = {
            'valid': False,
            'confidence': 0.0,
            'validation_methods': []
        }
        
        try:
            # Method 1: Syntax validation
            validated_email = validate_email(email)
            result['validation_methods'].append('syntax')
            
            # Method 2: Domain validation
            domain = email.split('@')[1]
            if self._validate_domain(domain):
                result['validation_methods'].append('domain')
                result['confidence'] += 0.3
            
            # Method 3: MX record check
            if self._check_mx_record(domain):
                result['validation_methods'].append('mx_record')
                result['confidence'] += 0.4
            
            result['valid'] = True
            result['confidence'] = min(1.0, result['confidence'] + 0.3)  # Base confidence
            
        except EmailNotValidError:
            result['confidence'] = 0.1  # Very low confidence for invalid syntax
        except Exception as e:
            logger.error(f"Email validation error: {e}")
            result['confidence'] = 0.2  # Low confidence for validation errors
        
        return result
    
    def _validate_domain(self, domain: str) -> bool:
        """Validate domain exists and is reachable"""
        try:
            response = self.session.head(f"http://{domain}", timeout=5)
            return response.status_code < 400
        except:
            return False
    
    def _check_mx_record(self, domain: str) -> bool:
        """Check if domain has MX record"""
        try:
            dns.resolver.resolve(domain, 'MX')
            return True
        except:
            return False
    
    def _discover_phone_number(
        self, 
        first_name: str, 
        last_name: str, 
        company_url: str
    ) -> Dict:
        """Discover phone numbers from website"""
        result = {
            'phone': None,
            'confidence': 0.0,
            'validated': False,
            'sources': []
        }
        
        try:
            # Scrape contact pages for phone numbers
            for contact_path in self.contact_page_urls:
                contact_url = urljoin(company_url, contact_path)
                
                try:
                    response = self.session.get(contact_url, timeout=10)
                    if response.status_code == 200:
                        phones = self._extract_phone_numbers(response.text)
                        
                        if phones:
                            # Use first valid UK phone number
                            result['phone'] = phones[0]
                            result['confidence'] = 0.7
                            result['validated'] = self._validate_uk_phone(phones[0])
                            result['sources'].append('website_scraping')
                            break
                            
                except requests.RequestException:
                    continue
                    
                time.sleep(0.5)  # Rate limiting
                
        except Exception as e:
            logger.error(f"Phone discovery error: {e}")
        
        return result
    
    def _extract_phone_numbers(self, content: str) -> List[str]:
        """Extract UK phone numbers from content"""
        phones = []
        
        for pattern in self.uk_phone_patterns:
            matches = re.findall(pattern, content)
            phones.extend(matches)
        
        # Clean and format phone numbers
        cleaned_phones = []
        for phone in phones:
            cleaned = self._clean_phone_number(phone)
            if cleaned and len(cleaned) >= 10:  # Minimum UK phone length
                cleaned_phones.append(cleaned)
        
        return cleaned_phones
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and format UK phone number"""
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Convert to standard UK format
        if cleaned.startswith('+44'):
            return cleaned
        elif cleaned.startswith('44'):
            return '+' + cleaned
        elif cleaned.startswith('0'):
            return '+44' + cleaned[1:]
        else:
            return '+44' + cleaned
    
    def _validate_uk_phone(self, phone: str) -> bool:
        """Validate UK phone number format"""
        # Basic UK phone validation
        if not phone.startswith('+44'):
            return False
        
        # Remove +44 and check length
        number = phone[3:]
        return len(number) >= 10 and number.isdigit()
    
    def _discover_linkedin_profile(
        self, 
        first_name: str, 
        last_name: str, 
        company_name: str,
        company_url: str
    ) -> Dict:
        """Discover LinkedIn profile"""
        result = {
            'profile': None,
            'confidence': 0.0,
            'validated': False,
            'sources': []
        }
        
        try:
            # Method 1: Search website for LinkedIn links
            linkedin_urls = self._scrape_linkedin_links(company_url)
            
            if linkedin_urls:
                # Find profile matching the person
                matching_profile = self._match_linkedin_profile(
                    linkedin_urls, first_name, last_name
                )
                
                if matching_profile:
                    result['profile'] = matching_profile
                    result['confidence'] = 0.8
                    result['validated'] = True
                    result['sources'].append('website_scraping')
            
            # Method 2: Generate potential LinkedIn URL
            if not result['profile']:
                potential_url = self._generate_linkedin_url(first_name, last_name)
                if potential_url:
                    result['profile'] = potential_url
                    result['confidence'] = 0.4  # Lower confidence for generated
                    result['sources'].append('url_generation')
                    
        except Exception as e:
            logger.error(f"LinkedIn discovery error: {e}")
        
        return result
    
    def _scrape_linkedin_links(self, company_url: str) -> List[str]:
        """Scrape LinkedIn profile links from website"""
        linkedin_urls = []
        
        try:
            # Check multiple pages for LinkedIn links
            pages_to_check = [company_url] + [
                urljoin(company_url, path) for path in self.contact_page_urls
            ]
            
            for page_url in pages_to_check:
                try:
                    response = self.session.get(page_url, timeout=10)
                    if response.status_code == 200:
                        for pattern in self.linkedin_patterns:
                            matches = re.findall(pattern, response.text, re.IGNORECASE)
                            for match in matches:
                                full_url = f"https://linkedin.com/in/{match}"
                                if full_url not in linkedin_urls:
                                    linkedin_urls.append(full_url)
                                    
                except requests.RequestException:
                    continue
                    
                time.sleep(0.5)  # Rate limiting
                
        except Exception as e:
            logger.error(f"LinkedIn scraping error: {e}")
        
        return linkedin_urls
    
    def _match_linkedin_profile(
        self, 
        linkedin_urls: List[str], 
        first_name: str, 
        last_name: str
    ) -> Optional[str]:
        """Match LinkedIn profile to person name"""
        first_lower = first_name.lower()
        last_lower = last_name.lower()
        
        for url in linkedin_urls:
            url_lower = url.lower()
            
            # Check if URL contains person's name
            if (first_lower in url_lower and last_lower in url_lower) or \
               (first_lower in url_lower and first_lower[0] in url_lower):
                return url
        
        # Return first URL if no specific match (fallback)
        return linkedin_urls[0] if linkedin_urls else None
    
    def _generate_linkedin_url(self, first_name: str, last_name: str) -> str:
        """Generate potential LinkedIn URL"""
        first_clean = re.sub(r'[^a-zA-Z]', '', first_name.lower())
        last_clean = re.sub(r'[^a-zA-Z]', '', last_name.lower())
        
        if first_clean and last_clean:
            return f"https://linkedin.com/in/{first_clean}-{last_clean}"
        
        return None
    
    def _calculate_enrichment_boost(self, enrichment_result: ContactEnrichmentResult) -> float:
        """Calculate confidence boost from enrichment"""
        boost = 0.0
        
        if enrichment_result.email_found:
            boost += 0.1 * enrichment_result.email_confidence
        
        if enrichment_result.phone_found:
            boost += 0.05 * enrichment_result.phone_confidence
        
        if enrichment_result.linkedin_found:
            boost += 0.05 * enrichment_result.linkedin_confidence
        
        return min(0.2, boost)  # Cap boost at 0.2
    
    def batch_enrich_contacts(
        self, 
        executives: List[ExecutiveContact], 
        company_url: str,
        company_name: str
    ) -> List[Tuple[ExecutiveContact, ContactEnrichmentResult]]:
        """Enrich multiple executive contacts in batch"""
        results = []
        
        for executive in executives:
            enriched_executive, enrichment_result = self.enrich_executive_contact(
                executive, company_url, company_name
            )
            results.append((enriched_executive, enrichment_result))
            
            # Rate limiting between requests
            time.sleep(1)
        
        return results
    
    def get_enrichment_report(
        self, 
        results: List[ContactEnrichmentResult]
    ) -> str:
        """Generate enrichment performance report"""
        if not results:
            return "No enrichment results to report"
        
        total = len(results)
        emails_found = sum(1 for r in results if r.email_found)
        phones_found = sum(1 for r in results if r.phone_found)
        linkedin_found = sum(1 for r in results if r.linkedin_found)
        
        # Average confidences
        avg_email_conf = sum(r.email_confidence for r in results if r.email_found) / max(1, emails_found)
        avg_phone_conf = sum(r.phone_confidence for r in results if r.phone_found) / max(1, phones_found)
        avg_linkedin_conf = sum(r.linkedin_confidence for r in results if r.linkedin_found) / max(1, linkedin_found)
        
        # Source analysis
        all_sources = []
        for result in results:
            all_sources.extend(result.enrichment_sources)
        
        source_counts = {}
        for source in all_sources:
            source_counts[source] = source_counts.get(source, 0) + 1
        
        report = f"""
📧 ADVANCED CONTACT ENRICHMENT REPORT

📊 ENRICHMENT SUMMARY:
• Total Executives Processed: {total}
• Emails Discovered: {emails_found} ({emails_found/total:.1%})
• Phones Discovered: {phones_found} ({phones_found/total:.1%})
• LinkedIn Profiles: {linkedin_found} ({linkedin_found/total:.1%})

🎯 CONFIDENCE SCORES:
• Average Email Confidence: {avg_email_conf:.2f}
• Average Phone Confidence: {avg_phone_conf:.2f}
• Average LinkedIn Confidence: {avg_linkedin_conf:.2f}

🔍 ENRICHMENT SOURCES:
"""
        
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            report += f"• {source.replace('_', ' ').title()}: {count} uses\n"
        
        # Validation success rates
        validated_emails = sum(1 for r in results if r.validation_results.get('email', False))
        validated_phones = sum(1 for r in results if r.validation_results.get('phone', False))
        
        report += f"""
✅ VALIDATION RESULTS:
• Email Validation Success: {validated_emails}/{emails_found} ({validated_emails/max(1,emails_found):.1%})
• Phone Validation Success: {validated_phones}/{phones_found} ({validated_phones/max(1,phones_found):.1%})
"""
        
        return report 