"""
Contact Information Extractor

Multi-strategy heuristic extraction with confidence scoring.
Extracts contact details from company websites using multiple approaches.

Based on creative design decisions:
- Multi-strategy extraction across contact pages, about pages, team pages
- Confidence scoring for extracted contacts
- Senior role pattern matching for decision makers
"""

import asyncio
import logging
import re
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page

from ..config import get_api_config, get_processing_config
from ..database import get_db_session
from ..models import UKCompany, ContactInfo, ContactSeniorityTier, SENIOR_ROLE_PATTERNS

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """Result of contact extraction attempt"""
    contact_info: Optional[ContactInfo] = None
    extraction_method: str = ""
    confidence: float = 0.0
    pages_searched: List[str] = None
    
    def __post_init__(self):
        if self.pages_searched is None:
            self.pages_searched = []

class ContactExtractor:
    """
    Multi-strategy contact extraction with confidence scoring
    
    Features:
    - Contact page discovery and parsing
    - About page and team page analysis
    - LinkedIn profile detection
    - Email and phone extraction with validation
    - Senior role pattern matching
    """
    
    def __init__(self):
        self.api_config = get_api_config()
        self.processing_config = get_processing_config()
        
        # Contact page patterns
        self.contact_page_patterns = [
            '/contact', '/contact-us', '/contact-us/', '/contacts',
            '/get-in-touch', '/reach-out', '/about/contact'
        ]
        
        # About page patterns  
        self.about_page_patterns = [
            '/about', '/about-us', '/about-us/', '/our-story',
            '/our-team', '/team', '/staff', '/people', '/leadership'
        ]
        
        # Email regex patterns
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
        ]
        
        # Phone regex patterns (UK focus)
        self.phone_patterns = [
            r'(\+44\s?)?(\(?0\d{4}\)?\s?\d{3}\s?\d{3})',  # UK landline
            r'(\+44\s?)?(\(?0\d{3}\)?\s?\d{3}\s?\d{4})',  # UK mobile
            r'(\+44\s?)?\d{2}\s?\d{4}\s?\d{4,6}',         # General UK
        ]
        
        # LinkedIn patterns
        self.linkedin_patterns = [
            r'linkedin\.com/in/([A-Za-z0-9\-_]+)',
            r'linkedin\.com/company/([A-Za-z0-9\-_]+)'
        ]
    
    async def extract_contacts(self, company_id: str, website_url: str) -> Optional[ExtractionResult]:
        """
        Extract contact information from company website
        
        Args:
            company_id: Unique company identifier
            website_url: Company website URL
            
        Returns:
            ExtractionResult with contact info and confidence score
        """
        try:
            logger.info(f"Extracting contacts for {website_url}")
            
            # Normalize URL
            base_url = self._normalize_url(website_url)
            
            # Multi-strategy extraction
            strategies = [
                self._extract_from_contact_pages,
                self._extract_from_about_pages, 
                self._extract_from_homepage,
                self._extract_from_footer
            ]
            
            best_result = None
            highest_confidence = 0.0
            all_pages_searched = []
            
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(
                    headless=self.api_config.headless_browser
                )
                context = await browser.new_context(
                    user_agent=self.api_config.browser_user_agent
                )
                page = await context.new_page()
                
                try:
                    for strategy in strategies:
                        try:
                            result = await strategy(page, base_url)
                            
                            if result and result.contact_info:
                                all_pages_searched.extend(result.pages_searched)
                                
                                if result.confidence > highest_confidence:
                                    highest_confidence = result.confidence
                                    best_result = result
                                
                                # Stop if we found high confidence contact
                                if result.confidence >= 0.8:
                                    break
                                    
                        except Exception as e:
                            logger.debug(f"Strategy failed: {e}")
                            continue
                    
                finally:
                    await browser.close()
            
            if best_result:
                best_result.pages_searched = list(set(all_pages_searched))
                
                # Update database
                self._update_company_contact_data(company_id, best_result)
                
                logger.info(f"Contact extraction complete for {website_url}: "
                          f"Confidence {best_result.confidence:.2f}")
            else:
                logger.info(f"No contacts found for {website_url}")
            
            return best_result
            
        except Exception as e:
            logger.error(f"Error extracting contacts for {website_url}: {e}")
            return None
    
    async def _extract_from_contact_pages(self, page: Page, base_url: str) -> Optional[ExtractionResult]:
        """Extract contacts from dedicated contact pages"""
        contact_urls = []
        
        # Build potential contact URLs
        for pattern in self.contact_page_patterns:
            contact_urls.append(urljoin(base_url, pattern))
        
        # Also try to discover contact links from homepage
        try:
            await page.goto(base_url, timeout=30000)
            await page.wait_for_load_state('domcontentloaded')
            
            # Look for contact links
            contact_links = await page.query_selector_all('a[href*="contact"]')
            for link in contact_links[:3]:  # Limit to first 3
                href = await link.get_attribute('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if full_url not in contact_urls:
                        contact_urls.append(full_url)
        except:
            pass
        
        # Try each contact URL
        for contact_url in contact_urls[:5]:  # Limit to 5 attempts
            try:
                await page.goto(contact_url, timeout=30000)
                await page.wait_for_load_state('domcontentloaded')
                
                content = await page.content()
                contact_info = self._parse_contact_content(content, contact_url)
                
                if contact_info:
                    return ExtractionResult(
                        contact_info=contact_info,
                        extraction_method="contact_page",
                        confidence=0.9,  # High confidence for dedicated contact pages
                        pages_searched=[contact_url]
                    )
                    
            except Exception as e:
                logger.debug(f"Failed to load contact page {contact_url}: {e}")
                continue
        
        return None
    
    async def _extract_from_about_pages(self, page: Page, base_url: str) -> Optional[ExtractionResult]:
        """Extract contacts from about/team pages"""
        about_urls = []
        
        # Build potential about URLs
        for pattern in self.about_page_patterns:
            about_urls.append(urljoin(base_url, pattern))
        
        # Try each about URL
        for about_url in about_urls[:5]:
            try:
                await page.goto(about_url, timeout=30000)
                await page.wait_for_load_state('domcontentloaded')
                
                content = await page.content()
                contact_info = self._parse_team_content(content, about_url)
                
                if contact_info:
                    return ExtractionResult(
                        contact_info=contact_info,
                        extraction_method="about_page",
                        confidence=0.7,  # Medium confidence for about pages
                        pages_searched=[about_url]
                    )
                    
            except Exception as e:
                logger.debug(f"Failed to load about page {about_url}: {e}")
                continue
        
        return None
    
    async def _extract_from_homepage(self, page: Page, base_url: str) -> Optional[ExtractionResult]:
        """Extract contacts from homepage"""
        try:
            await page.goto(base_url, timeout=30000)
            await page.wait_for_load_state('domcontentloaded')
            
            content = await page.content()
            contact_info = self._parse_contact_content(content, base_url)
            
            if contact_info:
                return ExtractionResult(
                    contact_info=contact_info,
                    extraction_method="homepage",
                    confidence=0.6,  # Lower confidence for homepage
                    pages_searched=[base_url]
                )
        except Exception as e:
            logger.debug(f"Failed to extract from homepage: {e}")
        
        return None
    
    async def _extract_from_footer(self, page: Page, base_url: str) -> Optional[ExtractionResult]:
        """Extract contacts from footer area"""
        try:
            await page.goto(base_url, timeout=30000)
            await page.wait_for_load_state('domcontentloaded')
            
            # Focus on footer elements
            footer_content = ""
            footer_selectors = ['footer', '.footer', '#footer', '.contact-info']
            
            for selector in footer_selectors:
                try:
                    footer_element = await page.query_selector(selector)
                    if footer_element:
                        footer_content += await footer_element.inner_text()
                except:
                    continue
            
            if footer_content:
                contact_info = self._parse_footer_content(footer_content, base_url)
                
                if contact_info:
                    return ExtractionResult(
                        contact_info=contact_info,
                        extraction_method="footer",
                        confidence=0.5,  # Lower confidence for footer
                        pages_searched=[base_url]
                    )
        except Exception as e:
            logger.debug(f"Failed to extract from footer: {e}")
        
        return None
    
    def _parse_contact_content(self, html_content: str, page_url: str) -> Optional[ContactInfo]:
        """Parse contact information from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract emails
        emails = self._extract_emails(soup.get_text())
        
        # Extract phones
        phones = self._extract_phones(soup.get_text())
        
        # Extract LinkedIn
        linkedin_url = self._extract_linkedin(html_content)
        
        # Extract names and roles
        person_info = self._extract_person_info(soup)
        
        if emails or phones or linkedin_url or person_info:
            return ContactInfo(
                person=person_info.get('name'),
                role=person_info.get('role'),
                seniority_tier=person_info.get('seniority_tier'),
                email=emails[0] if emails else None,
                phone=phones[0] if phones else None,
                linkedin_url=linkedin_url,
                confidence=self._calculate_confidence(emails, phones, linkedin_url, person_info),
                extraction_method="content_parsing"
            )
        
        return None
    
    def _parse_team_content(self, html_content: str, page_url: str) -> Optional[ContactInfo]:
        """Parse team/about page for senior contacts"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for team member sections
        team_sections = soup.find_all(['div', 'section'], class_=re.compile(r'team|staff|member|bio'))
        
        best_contact = None
        highest_seniority = 0
        
        for section in team_sections:
            person_info = self._extract_person_info(section)
            
            if person_info and person_info.get('seniority_tier'):
                # Prioritize higher seniority
                seniority_score = self._get_seniority_score(person_info['seniority_tier'])
                
                if seniority_score > highest_seniority:
                    highest_seniority = seniority_score
                    
                    # Extract contact details from this section
                    section_text = section.get_text()
                    emails = self._extract_emails(section_text)
                    phones = self._extract_phones(section_text)
                    linkedin_url = self._extract_linkedin(str(section))
                    
                    best_contact = ContactInfo(
                        person=person_info.get('name'),
                        role=person_info.get('role'),
                        seniority_tier=person_info.get('seniority_tier'),
                        email=emails[0] if emails else None,
                        phone=phones[0] if phones else None,
                        linkedin_url=linkedin_url,
                        confidence=self._calculate_confidence(emails, phones, linkedin_url, person_info),
                        extraction_method="team_page_parsing"
                    )
        
        return best_contact
    
    def _parse_footer_content(self, footer_text: str, page_url: str) -> Optional[ContactInfo]:
        """Parse footer content for basic contact info"""
        # Extract emails and phones from footer
        emails = self._extract_emails(footer_text)
        phones = self._extract_phones(footer_text)
        
        if emails or phones:
            return ContactInfo(
                email=emails[0] if emails else None,
                phone=phones[0] if phones else None,
                confidence=0.4,  # Lower confidence for footer contacts
                extraction_method="footer_parsing"
            )
        
        return None
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        emails = []
        
        for pattern in self.email_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            emails.extend(matches)
        
        # Filter out common non-contact emails
        filtered_emails = []
        exclude_patterns = ['noreply', 'no-reply', 'support', 'info', 'hello', 'admin']
        
        for email in emails:
            if isinstance(email, tuple):
                email = email[0] if email else ""
            
            email = email.lower().strip()
            
            # Skip if contains exclude patterns or is too generic
            if not any(pattern in email for pattern in exclude_patterns):
                if '@' in email and '.' in email.split('@')[1]:
                    filtered_emails.append(email)
        
        return list(set(filtered_emails))[:3]  # Return up to 3 unique emails
    
    def _extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers from text"""
        phones = []
        
        for pattern in self.phone_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    phone = ''.join(match)
                else:
                    phone = match
                
                # Clean up phone number
                phone = re.sub(r'[^\d+\(\)\s\-]', '', phone)
                if phone and len(phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) >= 10:
                    phones.append(phone.strip())
        
        return list(set(phones))[:2]  # Return up to 2 unique phones
    
    def _extract_linkedin(self, html_content: str) -> Optional[str]:
        """Extract LinkedIn URLs from HTML"""
        for pattern in self.linkedin_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                # Return first LinkedIn profile (not company page)
                for match in matches:
                    if 'company' not in match.lower():
                        return f"https://linkedin.com/in/{match}"
        return None
    
    def _extract_person_info(self, soup) -> Dict[str, str]:
        """Extract person name and role information"""
        info = {}
        
        # Look for name patterns
        name_selectors = [
            'h1', 'h2', 'h3', '.name', '.person-name', '.team-name',
            '.bio-name', '.contact-name', '.staff-name'
        ]
        
        for selector in name_selectors:
            elements = soup.select(selector)
            for element in elements[:3]:  # Check first 3
                text = element.get_text(strip=True)
                if self._looks_like_person_name(text):
                    info['name'] = text
                    break
            if 'name' in info:
                break
        
        # Look for role/title patterns
        role_selectors = [
            '.title', '.role', '.position', '.job-title', '.bio-title',
            'p', 'span', 'div'
        ]
        
        for selector in role_selectors:
            elements = soup.select(selector)
            for element in elements[:5]:  # Check first 5
                text = element.get_text(strip=True).lower()
                
                # Check against senior role patterns
                for tier, data in SENIOR_ROLE_PATTERNS.items():
                    for pattern in data['patterns']:
                        if pattern in text:
                            info['role'] = element.get_text(strip=True)
                            info['seniority_tier'] = tier
                            return info
        
        return info
    
    def _looks_like_person_name(self, text: str) -> bool:
        """Check if text looks like a person's name"""
        if not text or len(text) > 50:
            return False
        
        # Simple heuristics
        words = text.split()
        if len(words) < 2 or len(words) > 4:
            return False
        
        # Check for name-like patterns
        if all(word.istitle() or word.isupper() for word in words):
            return True
        
        return False
    
    def _get_seniority_score(self, seniority_tier: str) -> int:
        """Get numerical score for seniority tier"""
        scores = {
            'tier_1': 3,  # CEO, Founder, etc.
            'tier_2': 2,  # Director, Head of, etc.
            'tier_3': 1   # Manager, Lead, etc.
        }
        return scores.get(seniority_tier, 0)
    
    def _calculate_confidence(self, emails: List[str], phones: List[str], 
                            linkedin_url: Optional[str], person_info: Dict) -> float:
        """Calculate confidence score for extracted contact"""
        confidence = 0.0
        
        # Base scores
        if emails:
            confidence += 0.4
        if phones:
            confidence += 0.2
        if linkedin_url:
            confidence += 0.2
        if person_info.get('name'):
            confidence += 0.1
        if person_info.get('role'):
            confidence += 0.1
        
        # Seniority bonus
        seniority_tier = person_info.get('seniority_tier')
        if seniority_tier:
            multiplier = SENIOR_ROLE_PATTERNS.get(seniority_tier, {}).get('confidence_multiplier', 1.0)
            confidence *= multiplier
        
        return min(1.0, confidence)
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for processing"""
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        return url.rstrip('/')
    
    def _update_company_contact_data(self, company_id: str, result: ExtractionResult):
        """Update company record with contact extraction results"""
        try:
            with get_db_session() as session:
                company = session.query(UKCompany).filter_by(id=company_id).first()
                
                if company and result.contact_info:
                    contact = result.contact_info
                    
                    # Update contact fields
                    company.contact_person = contact.person
                    company.contact_role = contact.role
                    company.contact_seniority_tier = contact.seniority_tier
                    company.email = contact.email
                    company.phone = contact.phone
                    company.linkedin_url = contact.linkedin_url
                    company.contact_confidence = contact.confidence
                    company.contact_extraction_method = result.extraction_method
                    
                    # Update status
                    if company.status == 'scraped':
                        company.status = 'contacts_extracted'
                    
                    session.commit()
                    logger.debug(f"Updated contact data for company {company_id}")
                
        except Exception as e:
            logger.error(f"Error updating company contact data: {e}")
    
    def extract_batch(self, batch_size: int = 20) -> int:
        """Extract contacts for a batch of companies"""
        try:
            with get_db_session() as session:
                # Get companies needing contact extraction
                companies = session.query(UKCompany).filter(
                    UKCompany.status == 'scraped',
                    UKCompany.website.isnot(None)
                ).limit(batch_size).all()
                
                if not companies:
                    logger.info("No companies found needing contact extraction")
                    return 0
                
                logger.info(f"Starting contact extraction for {len(companies)} companies")
                extracted_count = 0
                
                for company in companies:
                    try:
                        # Run extraction
                        result = asyncio.run(
                            self.extract_contacts(company.id, company.website)
                        )
                        
                        if result and result.contact_info:
                            extracted_count += 1
                            logger.info(f"Extracted contact for {company.company_name}: "
                                      f"Confidence {result.confidence:.2f}")
                        
                        # Rate limiting
                        time.sleep(3)  # 3 second delay between companies
                        
                    except Exception as e:
                        logger.error(f"Error extracting contact for {company.company_name}: {e}")
                        continue
                
                logger.info(f"Contact extraction batch complete: {extracted_count}/{len(companies)} extracted")
                return extracted_count
                
        except Exception as e:
            logger.error(f"Error in contact extraction batch: {e}")
            return 0

# Convenience function
def extract_contacts_batch(batch_size: int = 20) -> int:
    """Convenience function to extract contacts for a batch of companies"""
    extractor = ContactExtractor()
    return extractor.extract_batch(batch_size) 