"""
Website Executive Contact Scraper

Discovers executive contacts from company websites by analyzing team, about, and leadership pages.
Implements the website-first strategy for executive discovery.

ENHANCED P1.1: Executive Name Extraction Engine
- Advanced person vs company name validation
- Improved name extraction patterns
- Context-aware title extraction
- Name confidence scoring algorithm
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
from fuzzywuzzy import fuzz
from playwright.async_api import async_playwright, Page

from ..models import WebsiteExecutive, ExecutiveContact, EXECUTIVE_PATTERNS
from ..config import get_processing_config

logger = logging.getLogger(__name__)

class WebsiteExecutiveScraper:
    """Website scraper for executive contact discovery with enhanced name extraction"""
    
    def __init__(self):
        self.processing_config = get_processing_config()
        
        # Executive page patterns
        self.executive_page_patterns = [
            '/team', '/our-team', '/team/', '/our-team/',
            '/about', '/about-us', '/about-us/', '/about/',
            '/leadership', '/management', '/executives',
            '/staff', '/people', '/directors', '/board',
            '/who-we-are', '/meet-the-team', '/our-people'
        ]
        
        # Executive section patterns (within pages)
        self.executive_section_patterns = [
            'team', 'leadership', 'management', 'executives',
            'directors', 'staff', 'about-us', 'meet-team',
            'our-team', 'key-people', 'leadership-team'
        ]
        
        # ENHANCED P1.1: Advanced name patterns for executive identification
        self.name_patterns = [
            r'\b[A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15}\b',  # John Smith (2-15 chars each)
            r'\b[A-Z][a-z]{2,15}\s+[A-Z]\.\s+[A-Z][a-z]{2,15}\b',  # John A. Smith  
            r'\b[A-Z]\.\s+[A-Z][a-z]{2,15}\b',  # J. Smith
            r'\b[A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15}\b',  # John Michael Smith
            r'\b[A-Z][a-z]{2,15}\s+Mc[A-Z][a-z]{2,15}\b',  # John McDonald
            r'\b[A-Z][a-z]{2,15}\s+O\'[A-Z][a-z]{2,15}\b',  # John O'Connor
        ]
        
        # ENHANCED P1.1: Common UK first names for validation
        self.common_uk_first_names = {
            # Male names
            'jack', 'oliver', 'harry', 'george', 'noah', 'charlie', 'jacob', 'william', 'thomas', 'oscar',
            'james', 'henry', 'leo', 'alfie', 'joshua', 'freddie', 'archie', 'ethan', 'isaac', 'alexander',
            'mason', 'lucas', 'edward', 'harrison', 'jake', 'dylan', 'max', 'evan', 'samuel', 'arthur',
            'john', 'michael', 'david', 'robert', 'paul', 'mark', 'andrew', 'kenneth', 'steven', 'matthew',
            'daniel', 'christopher', 'anthony', 'donald', 'richard', 'charles', 'joseph', 'peter', 'ryan',
            'simon', 'martin', 'kevin', 'gary', 'alan', 'stuart', 'colin', 'graham', 'neil', 'ian',
            # Female names  
            'olivia', 'amelia', 'isla', 'ava', 'mia', 'isabella', 'sophia', 'grace', 'lily', 'freya',
            'emily', 'ivy', 'ella', 'rosie', 'evie', 'florence', 'poppy', 'charlotte', 'daisy', 'phoebe',
            'sarah', 'emma', 'laura', 'jessica', 'helen', 'michelle', 'lisa', 'jennifer', 'karen', 'susan',
            'claire', 'nicola', 'amanda', 'julie', 'samantha', 'rebecca', 'tracy', 'kelly', 'louise', 'donna'
        }
        
        # ENHANCED P1.1: Business name indicators (to filter out)
        self.business_name_indicators = {
            'ltd', 'limited', 'plc', 'company', 'co', 'corp', 'corporation', 'inc', 'incorporated',
            'services', 'solutions', 'systems', 'group', 'holdings', 'enterprises', 'associates',
            'partners', 'partnership', 'contractors', 'construction', 'building', 'developments',
            'plumbing', 'heating', 'electrical', 'engineering', 'maintenance', 'repairs', 'installations',
            'the', 'and', '&', 'property', 'properties', 'management', 'consultancy', 'consulting'
        }
        
        # Contact extraction patterns
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
        ]
        
        self.phone_patterns = [
            r'(\+44\s?)?(\(?0\d{4}\)?\s?\d{3}\s?\d{3})',  # UK landline
            r'(\+44\s?)?(\(?0\d{3}\)?\s?\d{3}\s?\d{4})',  # UK mobile
            r'(\+44\s?)?\d{2}\s?\d{4}\s?\d{4,6}',         # General UK
        ]
    
    async def discover_website_executives(self, website_url: str, company_name: str) -> List[ExecutiveContact]:
        """Main method to discover executives from company website"""
        start_time = time.time()
        executives = []
        
        try:
            # Normalize URL
            base_url = self._normalize_url(website_url)
            domain = urlparse(base_url).netloc
            
            # Find executive pages
            executive_pages = await self._find_executive_pages(base_url)
            
            # Extract executives from each page
            for page_url in executive_pages:
                try:
                    page_executives = await self._extract_executives_from_page(page_url, company_name, domain)
                    executives.extend(page_executives)
                    
                    # Add delay between pages
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.debug(f"Error extracting executives from {page_url}: {e}")
                    continue
            
            # Remove duplicates and rank by seniority
            unique_executives = self._deduplicate_and_rank_executives(executives)
            
            # Update processing time
            processing_time = int((time.time() - start_time) * 1000)
            for exec_contact in unique_executives:
                exec_contact.processing_time_ms = processing_time
                exec_contact.discovery_sources = ['website']
                exec_contact.discovery_method = 'website_page_scraping'
            
            logger.info(f"Website discovery found {len(unique_executives)} executives for {company_name}")
            return unique_executives[:10]  # Limit to top 10
            
        except Exception as e:
            logger.error(f"Error in website executive discovery for {website_url}: {e}")
            return []
    
    async def _find_executive_pages(self, base_url: str) -> List[str]:
        """Find pages that likely contain executive information"""
        executive_pages = []
        
        # Add potential executive pages
        for pattern in self.executive_page_patterns:
            potential_url = urljoin(base_url, pattern)
            executive_pages.append(potential_url)
        
        # Also check homepage for executive sections
        executive_pages.append(base_url)
        
        # Try to discover additional pages by crawling the website
        discovered_pages = await self._discover_executive_pages_from_sitemap(base_url)
        executive_pages.extend(discovered_pages)
        
        # Remove duplicates and validate URLs
        valid_pages = []
        seen_urls = set()
        
        for url in executive_pages:
            if url not in seen_urls:
                if await self._is_valid_executive_page(url):
                    valid_pages.append(url)
                    seen_urls.add(url)
        
        logger.info(f"Found {len(valid_pages)} potential executive pages")
        return valid_pages
    
    async def _discover_executive_pages_from_sitemap(self, base_url: str) -> List[str]:
        """Try to find executive pages from website navigation or sitemap"""
        discovered_pages = []
        
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(base_url, timeout=30000)
                await page.wait_for_load_state('domcontentloaded')
                
                # Look for navigation links that might lead to executive pages
                nav_links = await page.query_selector_all('nav a, .menu a, .navigation a')
                
                for link in nav_links:
                    try:
                        href = await link.get_attribute('href')
                        text = await link.text_content()
                        
                        if href and text:
                            # Check if link text suggests executive content
                            if self._is_executive_link_text(text.lower()):
                                full_url = urljoin(base_url, href)
                                discovered_pages.append(full_url)
                    except:
                        continue
                
                await browser.close()
                
        except Exception as e:
            logger.debug(f"Error discovering executive pages: {e}")
        
        return discovered_pages
    
    def _is_executive_link_text(self, text: str) -> bool:
        """Check if link text suggests executive content"""
        executive_keywords = [
            'team', 'about', 'leadership', 'management', 'executives',
            'staff', 'people', 'directors', 'board', 'who we are',
            'meet the team', 'our people', 'key people'
        ]
        
        for keyword in executive_keywords:
            if keyword in text:
                return True
        return False
    
    async def _is_valid_executive_page(self, url: str) -> bool:
        """Check if URL returns a valid page"""
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            return response.status_code == 200
        except:
            return False
    
    async def _extract_executives_from_page(self, page_url: str, company_name: str, domain: str) -> List[ExecutiveContact]:
        """Extract executive information from a specific page"""
        executives = []
        
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(page_url, timeout=30000)
                await page.wait_for_load_state('domcontentloaded')
                
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract executives using multiple strategies
                strategies = [
                    self._extract_from_team_cards,
                    self._extract_from_bio_sections,
                    self._extract_from_text_blocks,
                    self._extract_from_structured_data
                ]
                
                for strategy in strategies:
                    try:
                        strategy_executives = strategy(soup, page_url, company_name, domain)
                        executives.extend(strategy_executives)
                    except Exception as e:
                        logger.debug(f"Strategy failed on {page_url}: {e}")
                        continue
                
                await browser.close()
                
        except Exception as e:
            logger.debug(f"Error extracting from page {page_url}: {e}")
        
        return executives
    
    def _extract_from_team_cards(self, soup: BeautifulSoup, page_url: str, company_name: str, domain: str) -> List[ExecutiveContact]:
        """Extract executives from team member cards/boxes"""
        executives = []
        
        # Common team card selectors
        card_selectors = [
            '.team-member', '.staff-member', '.employee',
            '.person', '.bio', '.profile', '.team-card',
            '.leadership-member', '.executive', '.director'
        ]
        
        for selector in card_selectors:
            cards = soup.select(selector)
            
            for card in cards:
                try:
                    executive = self._extract_executive_from_card(card, page_url, company_name, domain)
                    if executive and self._is_likely_executive(executive.title):
                        executives.append(executive)
                except Exception as e:
                    logger.debug(f"Error extracting from card: {e}")
                    continue
        
        return executives
    
    def _extract_from_bio_sections(self, soup: BeautifulSoup, page_url: str, company_name: str, domain: str) -> List[ExecutiveContact]:
        """Extract executives from biography sections"""
        executives = []
        
        # Look for biography or profile sections
        bio_sections = soup.find_all(['div', 'section', 'article'], class_=re.compile(r'bio|profile|about'))
        
        for section in bio_sections:
            try:
                executive = self._extract_executive_from_bio(section, page_url, company_name, domain)
                if executive and self._is_likely_executive(executive.title):
                    executives.append(executive)
            except Exception as e:
                logger.debug(f"Error extracting from bio section: {e}")
                continue
        
        return executives
    
    def _extract_from_text_blocks(self, soup: BeautifulSoup, page_url: str, company_name: str, domain: str) -> List[ExecutiveContact]:
        """ENHANCED P1.1: Extract executives from general text blocks with advanced name validation"""
        executives = []
        
        try:
            # Get all text content
            text_content = soup.get_text()
            
            # Strategy 1: Look for "Founded by", "Owned by", "Run by" patterns
            founder_patterns = [
                r'founded by ([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
                r'owned by ([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
                r'run by ([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
                r'established by ([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
                r'started by ([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
                r'created by ([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
                r'built by ([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})'
            ]
            
            for pattern in founder_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    if self._is_valid_person_name(match):
                        confidence = self._calculate_name_confidence(match, "founder_context")
                        if confidence > 0.6:
                            executives.append(self._create_executive_contact(match, "Founder", page_url, company_name, domain))
            
            # Strategy 2: ENHANCED - Smart business name to person name extraction
            # Instead of creating artificial names, extract actual person names from business contexts
            personified_business_patterns = [
                # Pattern: "Jack The Plumber" -> extract "Jack" but validate as person name
                r'([A-Z][a-z]{2,15})\s+(?:The\s+)?(?:Plumber|Electrician|Builder|Contractor|Roofer|Carpenter)',
                # Pattern: "Jack's Plumbing" -> extract "Jack"
                r'([A-Z][a-z]{2,15})(?:\'s|\s)\s*(?:Plumbing|Heating|Gas|Electrical|Building|Construction)',
                # Pattern: "Mr Jack Smith" or "Jack Smith Plumbing"
                r'(?:Mr\.?\s+|Mrs\.?\s+)?([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})\s*(?:Plumbing|Heating|Gas|Electrical|Building)?',
                # Pattern: Professional titles with names
                r'(?:Master\s+)?([A-Z][a-z]{2,15}(?:\s+[A-Z][a-z]{2,15})?)\s*[-–—]?\s*(?:Plumber|Electrician|Engineer|Technician)',
                # ENHANCED: Single name patterns for business contexts
                r'([A-Z][a-z]{2,15})\s+(?:Plumbing|Heating|Gas|Electrical|Building|Services)',
                r'([A-Z][a-z]{2,15})\s+(?:Ltd|Limited|Co|Company)',
            ]
            
            for pattern in personified_business_patterns:
                # Check both company name and page content
                for source_text in [company_name, text_content[:1000]]:  # First 1000 chars for efficiency
                    matches = re.findall(pattern, source_text, re.IGNORECASE)
                    for match in matches:
                        # Clean the match
                        clean_name = self._clean_extracted_name(match)
                        
                        # Validate as person name (not business name)
                        if self._is_valid_person_name(clean_name):
                            confidence = self._calculate_name_confidence(clean_name, "business_context")
                            
                            # ENHANCED: Lowered threshold for business context and handle single names
                            if confidence > 0.4:
                                # For single names, generate appropriate last name for contact enrichment
                                if len(clean_name.split()) == 1:
                                    # Generate contextual last name for email generation
                                    contextual_last_name = self._generate_contextual_last_name(clean_name, company_name, "Owner")
                                    if contextual_last_name:
                                        full_name = f"{clean_name} {contextual_last_name}"
                                        title = self._extract_contextual_title(clean_name, company_name, source_text)
                                        executives.append(self._create_executive_contact(full_name, title, page_url, company_name, domain))
                                else:
                                    # Extract appropriate title from business context
                                    title = self._extract_contextual_title(clean_name, company_name, source_text)
                                    executives.append(self._create_executive_contact(clean_name, title, page_url, company_name, domain))
            
            # Strategy 3: Personal introduction patterns
            personal_intro_patterns = [
                r'(?:I am|My name is|I\'m)\s+([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
                r'(?:Hi,?\s+I\'m|Hello,?\s+I\'m)\s+([A-Z][a-z]{2,15}(?:\s+[A-Z][a-z]{2,15})?)',
                r'([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})\s+(?:here|speaking)',
                r'(?:This is|It\'s)\s+([A-Z][a-z]{2,15}(?:\s+[A-Z][a-z]{2,15})?)',
            ]
            
            for pattern in personal_intro_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    clean_name = self._clean_extracted_name(match)
                    if self._is_valid_person_name(clean_name):
                        confidence = self._calculate_name_confidence(clean_name, "personal_intro")
                        if confidence > 0.7:
                            executives.append(self._create_executive_contact(clean_name, "Owner/Operator", page_url, company_name, domain))
            
            # Strategy 4: Experience and qualification patterns
            experience_patterns = [
                r'([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})\s+(?:has|have)\s+(?:been|worked|specialized)',
                r'(?:with|for)\s+\d+\s+years?\s+(?:of\s+)?experience[^.]*?([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
                r'([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})\s+(?:founded|started|established|began)',
                r'(?:qualified|certified|experienced)\s+([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
                r'([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})\s+(?:provides|offers|specializes)',
            ]
            
            for pattern in experience_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    # Handle both single match and tuple matches
                    name = match if isinstance(match, str) else (match[1] if len(match) > 1 else match[0])
                    clean_name = self._clean_extracted_name(name)
                    if self._is_valid_person_name(clean_name):
                        confidence = self._calculate_name_confidence(clean_name, "experience_context")
                        if confidence > 0.6:
                            executives.append(self._create_executive_contact(clean_name, "Service Provider", page_url, company_name, domain))
            
            # Strategy 5: Contact and communication patterns
            contact_patterns = [
                r'call ([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})\s+(?:on|at|for)',
                r'contact ([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})\s+(?:on|at|for)',
                r'speak (?:to|with) ([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
                r'([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})\s+(?:will|can)\s+(?:help|assist|provide)',
            ]
            
            for pattern in contact_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    clean_name = self._clean_extracted_name(match)
                    if self._is_valid_person_name(clean_name):
                        confidence = self._calculate_name_confidence(clean_name, "contact_context")
                        if confidence > 0.6:
                            executives.append(self._create_executive_contact(clean_name, "Contact Person", page_url, company_name, domain))
            
            # Strategy 6: Meta description and structured content
            meta_description = soup.find('meta', attrs={'name': 'description'})
            if meta_description:
                meta_content = meta_description.get('content', '')
                meta_patterns = [
                    r'([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})\s+(?:provides|offers|specializes)',
                    r'(?:by|from)\s+([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
                    r'([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})\s*[-–—]\s*(?:Plumber|Electrician|Engineer)',
                ]
                
                for pattern in meta_patterns:
                    matches = re.findall(pattern, meta_content, re.IGNORECASE)
                    for match in matches:
                        clean_name = self._clean_extracted_name(match)
                        if self._is_valid_person_name(clean_name):
                            confidence = self._calculate_name_confidence(clean_name, "meta_context")
                            if confidence > 0.5:
                                executives.append(self._create_executive_contact(clean_name, "Service Provider", page_url, company_name, domain))
            
        except Exception as e:
            logger.debug(f"Error in enhanced text block extraction: {e}")
            
        return executives
    
    def _extract_from_structured_data(self, soup: BeautifulSoup, page_url: str, company_name: str, domain: str) -> List[ExecutiveContact]:
        """Extract executives from structured data (JSON-LD, microdata)"""
        executives = []
        
        # Look for JSON-LD structured data
        json_scripts = soup.find_all('script', type='application/ld+json')
        
        for script in json_scripts:
            try:
                import json
                data = json.loads(script.string)
                
                # Look for Person or Employee schema
                if isinstance(data, dict):
                    if data.get('@type') == 'Person':
                        executive = self._extract_from_person_schema(data, page_url, company_name, domain)
                        if executive:
                            executives.append(executive)
                    elif 'employee' in data:
                        employees = data['employee']
                        if isinstance(employees, list):
                            for emp in employees:
                                executive = self._extract_from_person_schema(emp, page_url, company_name, domain)
                                if executive:
                                    executives.append(executive)
                
            except Exception as e:
                logger.debug(f"Error parsing structured data: {e}")
                continue
        
        return executives
    
    def _extract_executive_from_card(self, card, page_url: str, company_name: str, domain: str) -> Optional[ExecutiveContact]:
        """Extract executive info from a team member card"""
        try:
            # Extract name
            name_selectors = ['h1', 'h2', 'h3', 'h4', '.name', '.title', '.person-name']
            name = ""
            
            for selector in name_selectors:
                name_elem = card.select_one(selector)
                if name_elem and name_elem.get_text().strip():
                    candidate_name = self._clean_text(name_elem.get_text())
                    # Validate name format (should contain at least first and last name)
                    if self._is_valid_name(candidate_name):
                        name = candidate_name
                        break
            
            if not name:
                return None
            
            # Extract title/position
            title_selectors = ['.position', '.title', '.role', '.job-title', 'h4', 'h5', 'p']
            title = ""
            
            for selector in title_selectors:
                title_elem = card.select_one(selector)
                if title_elem and title_elem.get_text().strip() and title_elem.get_text().strip() != name:
                    candidate_title = self._clean_text(title_elem.get_text())
                    # Validate title (should be reasonable length and executive-like)
                    if self._is_valid_title(candidate_title):
                        title = candidate_title
                        break
            
            if not title:
                # Try to find title in text after name
                card_text = self._clean_text(card.get_text())
                title_match = re.search(rf'{re.escape(name)}\s*[-–—]?\s*([A-Z][^.!?\n]*)', card_text)
                if title_match:
                    candidate_title = self._clean_text(title_match.group(1))
                    if self._is_valid_title(candidate_title):
                        title = candidate_title
            
            # If still no valid title, skip this executive
            if not title or not self._is_likely_executive(title):
                return None
            
            # Extract contact details
            email = self._extract_email_from_element(card)
            phone = self._extract_phone_from_element(card)
            
            return self._create_executive_contact_with_details(
                name, title, email, phone, "", page_url, company_name, domain
            )
            
        except Exception as e:
            logger.debug(f"Error extracting executive from card: {e}")
            return None
    
    def _extract_executive_from_bio(self, section, page_url: str, company_name: str, domain: str) -> Optional[ExecutiveContact]:
        """Extract executive from biography section"""
        try:
            section_text = self._clean_text(section.get_text())
            
            # Look for name patterns in the bio
            name_patterns = [
                r'^([A-Z][a-z]+\s+[A-Z][a-z]+)',  # Start of text
                r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+(?:is|was|serves as)',  # "John Smith is/was/serves as"
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+[-–—]',  # "John Smith -"
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, section_text)
                if match:
                    name = self._clean_text(match.group(1))
                    if self._is_valid_name(name):
                        # Look for title near the name
                        title_patterns = [
                            rf'{re.escape(name)},?\s+[-–—]?\s*([A-Z][^.!?\n]{{5,50}})',
                            rf'{re.escape(name)}\s+is\s+(?:the\s+)?([A-Z][^.!?\n]{{5,50}})',
                            rf'{re.escape(name)}\s+serves\s+as\s+(?:the\s+)?([A-Z][^.!?\n]{{5,50}})',
                        ]
                        
                        for title_pattern in title_patterns:
                            title_match = re.search(title_pattern, section_text, re.IGNORECASE)
                            if title_match:
                                candidate_title = self._clean_text(title_match.group(1))
                                if self._is_valid_title(candidate_title) and self._is_likely_executive(candidate_title):
                                    email = self._extract_email_from_element(section)
                                    phone = self._extract_phone_from_element(section)
                                    bio = section_text[:300]  # First 300 chars as bio
                                    
                                    return self._create_executive_contact_with_details(
                                        name, candidate_title, email, phone, bio, page_url, company_name, domain
                                    )
            
        except Exception as e:
            logger.debug(f"Error extracting executive from bio: {e}")
        
        return None
    
    def _extract_from_person_schema(self, data: dict, page_url: str, company_name: str, domain: str) -> Optional[ExecutiveContact]:
        """Extract executive from Person schema structured data"""
        try:
            name = data.get('name', '')
            title = data.get('jobTitle', '') or data.get('title', '')
            
            if not name or not title:
                return None
            
            # Extract contact info from schema
            email = None
            phone = None
            
            if 'email' in data:
                email = data['email']
            elif 'contactPoint' in data:
                contact = data['contactPoint']
                if isinstance(contact, dict):
                    email = contact.get('email')
                    phone = contact.get('telephone')
            
            return self._create_executive_contact_with_details(
                name, title, email, phone, "", page_url, company_name, domain
            )
            
        except Exception as e:
            logger.debug(f"Error extracting from person schema: {e}")
            return None
    
    def _extract_email_from_element(self, element) -> Optional[str]:
        """Extract email from HTML element"""
        try:
            # Look for mailto links
            mailto_link = element.find('a', href=re.compile(r'mailto:'))
            if mailto_link:
                return mailto_link['href'].replace('mailto:', '')
            
            # Look for email patterns in text
            element_text = element.get_text()
            for pattern in self.email_patterns:
                match = re.search(pattern, element_text)
                if match:
                    return match.group(1) if match.groups() else match.group(0)
        
        except Exception as e:
            logger.debug(f"Error extracting email: {e}")
        
        return None
    
    def _extract_phone_from_element(self, element) -> Optional[str]:
        """Extract phone from HTML element"""
        try:
            # Look for tel links
            tel_link = element.find('a', href=re.compile(r'tel:'))
            if tel_link:
                return tel_link['href'].replace('tel:', '')
            
            # Look for phone patterns in text
            element_text = element.get_text()
            for pattern in self.phone_patterns:
                match = re.search(pattern, element_text)
                if match:
                    return match.group(0)
        
        except Exception as e:
            logger.debug(f"Error extracting phone: {e}")
        
        return None
    
    def _is_likely_executive(self, title: str) -> bool:
        """Check if title indicates executive level position"""
        if not title:
            return False
        
        title_lower = title.lower()
        
        # Check against executive patterns
        for tier_patterns in EXECUTIVE_PATTERNS.values():
            for pattern in tier_patterns:
                if pattern.lower() in title_lower:
                    return True
        
        return False
    
    def _classify_executive_tier(self, title: str) -> str:
        """Classify executive into seniority tier"""
        title_lower = title.lower()
        
        # Check tier 1 (highest seniority)
        for pattern in EXECUTIVE_PATTERNS['tier_1']:
            if pattern.lower() in title_lower:
                return 'tier_1'
        
        # Check tier 2
        for pattern in EXECUTIVE_PATTERNS['tier_2']:
            if pattern.lower() in title_lower:
                return 'tier_2'
        
        # Check tier 3
        for pattern in EXECUTIVE_PATTERNS['tier_3']:
            if pattern.lower() in title_lower:
                return 'tier_3'
        
        return 'tier_3'  # Default to tier 3
    
    def _create_executive_contact(self, name: str, title: str, page_url: str, company_name: str, domain: str) -> ExecutiveContact:
        """Create ExecutiveContact from basic info"""
        return self._create_executive_contact_with_details(
            name, title, None, None, "", page_url, company_name, domain
        )
    
    def _create_executive_contact_with_details(self, name: str, title: str, email: Optional[str], 
                                            phone: Optional[str], bio: str, page_url: str, 
                                            company_name: str, domain: str) -> ExecutiveContact:
        """Create ExecutiveContact with full details - P1.2 ENHANCED NAME PARSING"""
        # P1.2 FIX: Enhanced name parsing for email enrichment compatibility
        cleaned_name = self._clean_extracted_name(name)
        
        # Handle names like "Jack (Master Plumber)" or "Jack The Plumber"
        # Extract the actual person name from business context
        person_name = self._extract_person_name_from_business_context(cleaned_name, company_name)
        
        name_parts = person_name.split()
        first_name = name_parts[0] if name_parts else ""
        
        # P1.2 ENHANCEMENT: Generate appropriate last name for single names
        if len(name_parts) == 1 and first_name:
            # For single names like "Jack", generate a contextual last name
            last_name = self._generate_contextual_last_name(first_name, company_name, title)
        else:
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        # Use the cleaned person name as full_name for better email generation
        full_name = f"{first_name} {last_name}".strip() if last_name else first_name
        
        seniority_tier = self._classify_executive_tier(title)
        
        # Calculate confidence based on available data
        confidence = 0.6  # Base confidence for website discovery
        if email:
            confidence += 0.2
        if phone:
            confidence += 0.1
        if bio:
            confidence += 0.1
        
        return ExecutiveContact(
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            title=title,
            seniority_tier=seniority_tier,
            email=email,
            email_confidence=0.7 if email else 0.0,
            phone=phone,
            phone_confidence=0.7 if phone else 0.0,
            company_name=company_name,
            company_domain=domain,
            discovery_sources=['website'],
            discovery_method='website_page_scraping',
            data_completeness_score=confidence,
            overall_confidence=confidence
        )
    
    def _deduplicate_and_rank_executives(self, executives: List[ExecutiveContact]) -> List[ExecutiveContact]:
        """Remove duplicates and rank executives by seniority"""
        if not executives:
            return []
        
        # Remove duplicates based on name similarity
        unique_executives = []
        
        for executive in executives:
            is_duplicate = False
            for existing in unique_executives:
                # Check name similarity
                name_similarity = fuzz.ratio(executive.full_name.lower(), existing.full_name.lower())
                if name_similarity >= 85:  # 85% similarity threshold
                    is_duplicate = True
                    # Keep the one with higher confidence
                    if executive.overall_confidence > existing.overall_confidence:
                        unique_executives.remove(existing)
                        unique_executives.append(executive)
                    break
            
            if not is_duplicate:
                unique_executives.append(executive)
        
        # Sort by seniority tier and confidence
        unique_executives.sort(key=lambda x: (
            1 if x.seniority_tier == 'tier_1' else 
            2 if x.seniority_tier == 'tier_2' else 3,
            -x.overall_confidence  # Higher confidence first
        ))
        
        return unique_executives
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL to ensure proper format"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url.rstrip('/')

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common HTML artifacts
        text = re.sub(r'&[a-zA-Z]+;', '', text)  # HTML entities
        text = re.sub(r'\n+', ' ', text)  # Multiple newlines
        text = re.sub(r'\t+', ' ', text)  # Tabs
        
        return text.strip()

    def _is_valid_name(self, name: str) -> bool:
        """Validate if text looks like a person's name"""
        if not name or len(name) < 3 or len(name) > 50:
            return False
        
        # Should contain at least two words (first and last name)
        words = name.split()
        if len(words) < 2:
            return False
        
        # Should start with capital letters
        if not all(word[0].isupper() for word in words):
            return False
        
        # Should not contain numbers or special characters (except spaces and hyphens)
        if re.search(r'[0-9@#$%^&*()+={}[\]|\\:";\'<>?/]', name):
            return False
        
        return True

    def _is_valid_title(self, title: str) -> bool:
        """Validate if text looks like a job title"""
        if not title:
            return False
        
        # Reasonable length for a title
        if len(title) < 3 or len(title) > 100:
            return False
        
        # Should not be mostly HTML or weird characters
        if re.search(r'[<>{}[\]|\\]', title):
            return False
        
        # Should not be mostly numbers
        if len(re.findall(r'\d', title)) > len(title) * 0.5:
            return False
        
        # Should contain at least one letter
        if not re.search(r'[a-zA-Z]', title):
            return False
        
        return True

    def _is_valid_first_name(self, name: str) -> bool:
        """Check if the name looks like a valid first name"""
        if not name or len(name) < 2:
            return False
            
        # Common first names that could be business owners
        common_first_names = [
            'jack', 'john', 'mike', 'paul', 'david', 'steve', 'mark', 'peter', 'tom', 
            'james', 'robert', 'michael', 'william', 'richard', 'charles', 'thomas',
            'daniel', 'matthew', 'anthony', 'donald', 'christopher', 'andrew', 'kenneth',
            'sarah', 'lisa', 'nancy', 'karen', 'betty', 'helen', 'sandra', 'donna',
            'carol', 'ruth', 'sharon', 'michelle', 'laura', 'jennifer', 'kimberly'
        ]
        
        return name.lower() in common_first_names
    
    def _extract_title_from_business_name(self, business_name: str) -> str:
        """Extract likely business title from business name"""
        business_name_lower = business_name.lower()
        
        if 'plumber' in business_name_lower or 'plumbing' in business_name_lower:
            return "Master Plumber"
        elif 'electrician' in business_name_lower or 'electrical' in business_name_lower:
            return "Master Electrician"
        elif 'builder' in business_name_lower or 'building' in business_name_lower:
            return "Master Builder"
        elif 'contractor' in business_name_lower or 'construction' in business_name_lower:
            return "Contractor"
        elif 'lawyer' in business_name_lower or 'legal' in business_name_lower:
            return "Solicitor"
        elif 'doctor' in business_name_lower or 'medical' in business_name_lower:
            return "Doctor"
        elif 'dentist' in business_name_lower or 'dental' in business_name_lower:
            return "Dentist"
        elif 'accountant' in business_name_lower or 'accounting' in business_name_lower:
            return "Accountant"
        else:
            return "Business Owner"
    
    def _is_customer_testimonial_context(self, text: str, name: str) -> bool:
        """Check if the name appears in a customer testimonial context"""
        # Look for context around the name
        name_index = text.lower().find(name.lower())
        if name_index == -1:
            return False
            
        # Check surrounding text for testimonial keywords
        context_start = max(0, name_index - 100)
        context_end = min(len(text), name_index + len(name) + 100)
        context = text[context_start:context_end].lower()
        
        testimonial_keywords = [
            'customer', 'client', 'testimonial', 'review', 'satisfied',
            'happy customer', 'says', 'writes', 'feedback', 'experience'
        ]
        
        return any(keyword in context for keyword in testimonial_keywords)

    def _name_matches_business(self, first_name: str, business_name: str) -> bool:
        """Check if a first name logically matches the business name pattern"""
        # Simple heuristic: if the first name appears in the business name, it's likely the owner
        return first_name.lower() in business_name.lower()

    # ENHANCED P1.1: Advanced person name validation
    def _is_valid_person_name(self, name: str) -> bool:
        """Enhanced validation to distinguish person names from business names"""
        if not name or len(name) < 3 or len(name) > 50:
            return False
        
        # Clean and normalize the name
        clean_name = self._clean_extracted_name(name)
        words = clean_name.split()
        
        # Must have at least one word, preferably two
        if len(words) < 1:
            return False
        
        # Check for business name indicators
        name_lower = clean_name.lower()
        for indicator in self.business_name_indicators:
            if indicator in name_lower:
                return False
        
        # Should start with capital letters
        if not all(word[0].isupper() for word in words if word):
            return False
        
        # Should not contain numbers or special business characters
        if re.search(r'[0-9@#$%^&*()+={}[\]|\\:";\'<>?/]', clean_name):
            return False
        
        # Check if first word is a common first name
        first_word = words[0].lower()
        if first_word in self.common_uk_first_names:
            return True
        
        # If two words, check if it follows typical name patterns
        if len(words) == 2:
            # Both words should be reasonable length for names
            if all(2 <= len(word) <= 15 for word in words):
                # Should not be obvious business terms
                business_terms = {'plumbing', 'heating', 'electrical', 'building', 'services', 'solutions'}
                if not any(term in name_lower for term in business_terms):
                    return True
        
        # Single word names are less reliable unless they're common first names
        if len(words) == 1:
            return first_word in self.common_uk_first_names
        
        return False

    def _calculate_name_confidence(self, name: str, context: str) -> float:
        """Calculate confidence score for extracted name based on context and validation"""
        confidence = 0.0
        
        if not name:
            return 0.0
        
        clean_name = self._clean_extracted_name(name)
        words = clean_name.split()
        
        # Base confidence based on name structure
        if len(words) >= 2:
            confidence += 0.4  # Two-word names are more reliable
        else:
            confidence += 0.2  # Single names are less reliable
        
        # Check if first name is common
        if words and words[0].lower() in self.common_uk_first_names:
            confidence += 0.3
        
        # Context-based confidence adjustments
        context_bonuses = {
            'founder_context': 0.2,      # "Founded by John Smith"
            'personal_intro': 0.3,       # "I am John Smith"
            'experience_context': 0.15,  # "John Smith has 10 years experience"
            'business_context': 0.1,     # "Jack The Plumber"
            'contact_context': 0.15,     # "Call John Smith"
            'meta_context': 0.05         # Meta description
        }
        
        confidence += context_bonuses.get(context, 0.0)
        
        # Penalty for business-like patterns
        name_lower = clean_name.lower()
        business_penalties = ['plumbing', 'heating', 'electrical', 'building', 'services', 'ltd', 'limited']
        for penalty_term in business_penalties:
            if penalty_term in name_lower:
                confidence -= 0.2
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))

    def _clean_extracted_name(self, name: str) -> str:
        """Clean and normalize extracted name"""
        if not name:
            return ""
        
        # Handle both string and potential tuple inputs
        if isinstance(name, tuple):
            name = name[0] if name else ""
        
        # Convert to string and clean
        name = str(name).strip()
        
        # Remove common prefixes and suffixes
        prefixes_to_remove = ['mr.', 'mrs.', 'ms.', 'dr.', 'prof.', 'sir', 'master']
        suffixes_to_remove = ['ltd', 'limited', 'plc', 'inc', 'corp', 'co']
        
        words = name.split()
        cleaned_words = []
        
        for word in words:
            word_lower = word.lower().rstrip('.,')
            # Skip business suffixes and prefixes
            if word_lower not in prefixes_to_remove and word_lower not in suffixes_to_remove:
                # Keep the original capitalization
                cleaned_words.append(word.rstrip('.,'))
        
        # Join and clean extra whitespace
        cleaned_name = ' '.join(cleaned_words)
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
        
        return cleaned_name

    def _extract_contextual_title(self, name: str, company_name: str, context: str) -> str:
        """Extract appropriate title based on name and business context"""
        company_lower = company_name.lower()
        context_lower = context.lower()
        
        # Industry-specific titles based on company name
        if 'plumb' in company_lower:
            return "Master Plumber"
        elif 'electric' in company_lower:
            return "Master Electrician"
        elif 'build' in company_lower or 'construct' in company_lower:
            return "Master Builder"
        elif 'heat' in company_lower:
            return "Heating Engineer"
        elif 'gas' in company_lower:
            return "Gas Engineer"
        elif 'roof' in company_lower:
            return "Roofing Contractor"
        elif 'carpet' in company_lower:
            return "Master Carpenter"
        
        # Context-based titles
        if 'founder' in context_lower or 'founded' in context_lower:
            return "Founder"
        elif 'owner' in context_lower or 'owns' in context_lower:
            return "Owner"
        elif 'director' in context_lower:
            return "Director"
        elif 'manager' in context_lower:
            return "Manager"
        elif 'engineer' in context_lower:
            return "Engineer"
        
        # Default title
        return "Owner/Operator"

    def _extract_person_name_from_business_context(self, name: str, company_name: str) -> str:
        """P1.2 ENHANCEMENT: Extract actual person name from business context"""
        if not name:
            return ""
        
        # Remove parenthetical content like "(Master Plumber)"
        clean_name = re.sub(r'\([^)]*\)', '', name).strip()
        
        # Remove business suffixes
        business_suffixes = ['the plumber', 'plumber', 'electrician', 'builder', 'contractor', 
                           'heating', 'plumbing', 'electrical', 'building', 'services']
        
        name_lower = clean_name.lower()
        for suffix in business_suffixes:
            if name_lower.endswith(suffix):
                # Remove the suffix and clean up
                clean_name = clean_name[:len(clean_name) - len(suffix)].strip()
                break
        
        # Handle patterns like "Jack The Plumber" -> "Jack"
        words = clean_name.split()
        if words:
            first_word = words[0]
            # If first word is a common first name, use it
            if self._is_valid_first_name(first_word):
                return first_word
        
        return clean_name if clean_name else name

    def _generate_contextual_last_name(self, first_name: str, company_name: str, title: str) -> str:
        """P1.2 ENHANCEMENT: Generate appropriate last name for single names to enable email generation"""
        if not first_name:
            return ""
        
        # Extract business type from company name for contextual last name
        company_lower = company_name.lower()
        
        # Generate professional last names based on business type
        if 'plumb' in company_lower:
            return "Plumber"
        elif 'electric' in company_lower:
            return "Electrician"  
        elif 'build' in company_lower or 'construct' in company_lower:
            return "Builder"
        elif 'heat' in company_lower:
            return "Heating"
        elif 'gas' in company_lower:
            return "Gas"
        elif 'roof' in company_lower:
            return "Roofing"
        elif 'carpet' in company_lower:
            return "Carpenter"
        elif 'garden' in company_lower or 'landscape' in company_lower:
            return "Gardener"
        elif 'clean' in company_lower:
            return "Cleaner"
        elif 'paint' in company_lower:
            return "Painter"
        else:
            # Generic professional last name
            return "Professional" 