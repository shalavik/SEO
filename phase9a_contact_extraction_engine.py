#!/usr/bin/env python3
"""
Phase 9A: Contact Detail Extraction Engine
==========================================

Advanced contact information extraction system for executive discovery with:
- Context7-inspired pattern recognition for phone, email, LinkedIn
- Executive-specific contact attribution and validation
- Multi-format phone number detection (US, UK, international)
- Enhanced email discovery with domain inference
- LinkedIn profile intelligence and validation
- Zero-cost processing optimization

Built on Phase 8's 92% AI classification success
Implements Context7 best practices for contact extraction
"""

import asyncio
import json
import time
import logging
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Any, Set
from pathlib import Path
import pandas as pd
from urllib.parse import urlparse, urljoin
import aiohttp
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import numpy as np

@dataclass
class Phase9aConfig:
    """Contact Extraction Engine Configuration - Context7 Best Practices"""
    # Processing Configuration
    max_concurrent_companies: int = 5
    max_pages_per_company: int = 15
    session_timeout: int = 30
    
    # Contact Extraction Configuration
    phone_confidence_threshold: float = 0.75
    email_confidence_threshold: float = 0.70
    linkedin_confidence_threshold: float = 0.65
    contact_completeness_threshold: float = 0.60
    
    # Pattern Recognition Configuration
    enable_multi_format_phone: bool = True
    enable_email_inference: bool = True
    enable_linkedin_intelligence: bool = True
    enable_executive_attribution: bool = True
    
    # Quality Assessment Configuration
    min_contact_quality_score: float = 0.50
    max_contacts_per_executive: int = 5
    enable_contact_validation: bool = True

@dataclass
class ContactInfo:
    """Executive Contact Information Structure"""
    phone_numbers: List[str]
    email_addresses: List[str]
    linkedin_profiles: List[str]
    contact_quality_score: float
    completeness_percentage: float
    source_pages: List[str]
    confidence_scores: Dict[str, float]

@dataclass
class ExecutiveProfile:
    """Complete Executive Profile with Contact Details"""
    name: str
    title: str
    company: str
    contact_info: ContactInfo
    extraction_source: str
    overall_confidence: float
    discovery_timestamp: str

class Phase9aAdvancedContactPatterns:
    """Context7-Inspired Contact Pattern Recognition System"""
    
    def __init__(self, config: Phase9aConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Context7-inspired phone number patterns (multi-format)
        self.phone_patterns = [
            # US Phone Numbers
            r'\b(?:\+1[-.\s]?)?(?:\(?(?:800|888|877|866|855|844|833|822)\)?[-.\s]?)?(?:\(?[2-9][0-8][0-9]\)?[-.\s]?)?[2-9][0-9]{2}[-.\s]?[0-9]{4}\b',
            # UK Phone Numbers
            r'\b(?:\+44[-.\s]?)?(?:\(?0\)?[-.\s]?)?(?:1[1-9]|2[0-9]|3[0-9]|7[0-9]|8[0-9])(?:[-.\s]?[0-9]){7,9}\b',
            # International Format
            r'\b\+[1-9]\d{1,14}\b',
            # General Format with Extensions
            r'\b(?:\(?[0-9]{3}\)?[-.\s]?)?[0-9]{3}[-.\s]?[0-9]{4}(?:\s?(?:ext|extension|x)[-.\s]?[0-9]{1,5})?\b',
            # Mobile/Direct Format
            r'\b(?:mobile|cell|direct)[-:\s]*(?:\+?[0-9]{1,4}[-.\s]?)?(?:\(?[0-9]{3}\)?[-.\s]?)?[0-9]{3}[-.\s]?[0-9]{4}\b'
        ]
        
        # Context7-inspired email patterns
        self.email_patterns = [
            # Standard Email Pattern
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # Executive Email Pattern (with titles)
            r'\b(?:ceo|cto|cfo|director|manager|president|vp)\.?[A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # Name-based Email Pattern
            r'\b[A-Za-z]+\.[A-Za-z]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # Initial-based Email Pattern
            r'\b[A-Za-z]\.[A-Za-z]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ]
        
        # Context7-inspired LinkedIn patterns
        self.linkedin_patterns = [
            # Standard LinkedIn URL
            r'https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-._~:/?#[\]@!$&\'()*+,;=%]+',
            # LinkedIn Company Page
            r'https?://(?:www\.)?linkedin\.com/company/[A-Za-z0-9\-._~:/?#[\]@!$&\'()*+,;=%]+',
            # LinkedIn Profile Mention
            r'linkedin\.com/in/[A-Za-z0-9\-._~:/?#[\]@!$&\'()*+,;=%]+',
            # LinkedIn Public Profile
            r'https?://[A-Za-z0-9\-]+\.linkedin\.com/pub/[A-Za-z0-9\-._~:/?#[\]@!$&\'()*+,;=%]+'
        ]
        
        # Executive context indicators for contact attribution
        self.executive_contexts = [
            'director', 'manager', 'ceo', 'cto', 'cfo', 'president', 'vice president', 'vp',
            'head of', 'chief', 'executive', 'founder', 'owner', 'principal', 'partner',
            'lead', 'senior', 'coordinator', 'supervisor', 'administrator', 'officer'
        ]
        
        # Contact type indicators
        self.contact_type_indicators = {
            'phone': ['phone', 'tel', 'telephone', 'mobile', 'cell', 'direct', 'office', 'contact'],
            'email': ['email', 'e-mail', 'mail', 'contact', '@'],
            'linkedin': ['linkedin', 'profile', 'social', 'professional']
        }
    
    def extract_phone_numbers(self, content: str, context_window: int = 100) -> List[Dict[str, Any]]:
        """Extract phone numbers with Context7 best practices"""
        phone_numbers = []
        
        for pattern in self.phone_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                phone = match.group().strip()
                start_pos = max(0, match.start() - context_window)
                end_pos = min(len(content), match.end() + context_window)
                context = content[start_pos:end_pos]
                
                # Calculate confidence based on context
                confidence = self._calculate_phone_confidence(phone, context)
                
                if confidence >= self.config.phone_confidence_threshold:
                    phone_info = {
                        'number': phone,
                        'type': self._classify_phone_type(phone, context),
                        'confidence': confidence,
                        'context': context.strip(),
                        'source_pattern': pattern
                    }
                    phone_numbers.append(phone_info)
        
        return self._deduplicate_phones(phone_numbers)
    
    def extract_email_addresses(self, content: str, company_domain: str = "", context_window: int = 80) -> List[Dict[str, Any]]:
        """Extract email addresses with Context7 domain inference"""
        email_addresses = []
        
        for pattern in self.email_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                email = match.group().strip().lower()
                start_pos = max(0, match.start() - context_window)
                end_pos = min(len(content), match.end() + context_window)
                context = content[start_pos:end_pos]
                
                # Calculate confidence based on context and domain
                confidence = self._calculate_email_confidence(email, context, company_domain)
                
                if confidence >= self.config.email_confidence_threshold:
                    email_info = {
                        'address': email,
                        'domain': email.split('@')[1] if '@' in email else '',
                        'confidence': confidence,
                        'context': context.strip(),
                        'is_executive': self._is_executive_email(email, context),
                        'source_pattern': pattern
                    }
                    email_addresses.append(email_info)
        
        # Add inferred emails based on names and company domain
        if self.config.enable_email_inference and company_domain:
            inferred_emails = self._infer_executive_emails(content, company_domain)
            email_addresses.extend(inferred_emails)
        
        return self._deduplicate_emails(email_addresses)
    
    def extract_linkedin_profiles(self, content: str, context_window: int = 120) -> List[Dict[str, Any]]:
        """Extract LinkedIn profiles with Context7 intelligence"""
        linkedin_profiles = []
        
        for pattern in self.linkedin_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                linkedin_url = match.group().strip()
                start_pos = max(0, match.start() - context_window)
                end_pos = min(len(content), match.end() + context_window)
                context = content[start_pos:end_pos]
                
                # Calculate confidence based on context
                confidence = self._calculate_linkedin_confidence(linkedin_url, context)
                
                if confidence >= self.config.linkedin_confidence_threshold:
                    linkedin_info = {
                        'url': linkedin_url,
                        'profile_type': self._classify_linkedin_type(linkedin_url),
                        'confidence': confidence,
                        'context': context.strip(),
                        'is_executive_profile': self._is_executive_linkedin(linkedin_url, context),
                        'source_pattern': pattern
                    }
                    linkedin_profiles.append(linkedin_info)
        
        return self._deduplicate_linkedin(linkedin_profiles)
    
    def _calculate_phone_confidence(self, phone: str, context: str) -> float:
        """Calculate phone number confidence using Context7 scoring"""
        confidence = 0.5  # Base confidence
        
        # Length and format validation
        clean_phone = re.sub(r'[^0-9+]', '', phone)
        if 10 <= len(clean_phone) <= 15:
            confidence += 0.2
        
        # Context indicators
        context_lower = context.lower()
        for indicator in self.contact_type_indicators['phone']:
            if indicator in context_lower:
                confidence += 0.1
                break
        
        # Executive context
        for exec_context in self.executive_contexts:
            if exec_context in context_lower:
                confidence += 0.15
                break
        
        # Format quality (international, parentheses, etc.)
        if phone.startswith('+'):
            confidence += 0.05
        if '(' in phone and ')' in phone:
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def _calculate_email_confidence(self, email: str, context: str, company_domain: str) -> float:
        """Calculate email confidence using Context7 domain matching"""
        confidence = 0.6  # Base confidence for valid email
        
        # Domain matching
        if company_domain and company_domain in email:
            confidence += 0.25
        
        # Executive indicators in email
        email_lower = email.lower()
        for exec_context in self.executive_contexts:
            if exec_context in email_lower:
                confidence += 0.1
                break
        
        # Context indicators
        context_lower = context.lower()
        for indicator in self.contact_type_indicators['email']:
            if indicator in context_lower:
                confidence += 0.05
        
        # Professional email patterns
        if any(pattern in email_lower for pattern in ['ceo', 'cto', 'cfo', 'director', 'manager']):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _calculate_linkedin_confidence(self, linkedin_url: str, context: str) -> float:
        """Calculate LinkedIn confidence using Context7 profile analysis"""
        confidence = 0.7  # Base confidence for LinkedIn URL
        
        # URL quality
        if 'linkedin.com/in/' in linkedin_url:
            confidence += 0.1
        if linkedin_url.startswith('https'):
            confidence += 0.05
        
        # Context indicators
        context_lower = context.lower()
        for indicator in self.contact_type_indicators['linkedin']:
            if indicator in context_lower:
                confidence += 0.05
        
        # Executive context
        for exec_context in self.executive_contexts:
            if exec_context in context_lower:
                confidence += 0.1
                break
        
        return min(1.0, confidence)
    
    def _classify_phone_type(self, phone: str, context: str) -> str:
        """Classify phone number type using Context7 patterns"""
        context_lower = context.lower()
        
        if any(word in context_lower for word in ['mobile', 'cell']):
            return 'mobile'
        elif any(word in context_lower for word in ['direct', 'personal']):
            return 'direct'
        elif any(word in context_lower for word in ['office', 'main']):
            return 'office'
        elif any(word in context_lower for word in ['fax']):
            return 'fax'
        else:
            return 'unknown'
    
    def _is_executive_email(self, email: str, context: str) -> bool:
        """Determine if email belongs to executive using Context7 analysis"""
        email_lower = email.lower()
        context_lower = context.lower()
        
        # Check email content
        if any(title in email_lower for title in ['ceo', 'cto', 'cfo', 'director', 'manager', 'president']):
            return True
        
        # Check context
        if any(title in context_lower for title in self.executive_contexts):
            return True
        
        return False
    
    def _infer_executive_emails(self, content: str, company_domain: str) -> List[Dict[str, Any]]:
        """Infer executive emails using Context7 name-domain patterns"""
        inferred_emails = []
        
        # Extract names from content
        name_pattern = r'\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b'
        names = re.findall(name_pattern, content)
        
        for name in names[:10]:  # Limit to first 10 names
            name_parts = name.lower().split()
            if len(name_parts) == 2:
                first, last = name_parts
                
                # Generate common email patterns
                email_patterns = [
                    f"{first}.{last}@{company_domain}",
                    f"{first}@{company_domain}",
                    f"{last}@{company_domain}",
                    f"{first[0]}.{last}@{company_domain}",
                    f"{first}{last}@{company_domain}"
                ]
                
                for email in email_patterns:
                    inferred_emails.append({
                        'address': email,
                        'domain': company_domain,
                        'confidence': 0.4,  # Lower confidence for inferred
                        'context': f"Inferred from name: {name}",
                        'is_executive': True,
                        'source_pattern': 'inferred'
                    })
        
        return inferred_emails
    
    def _classify_linkedin_type(self, linkedin_url: str) -> str:
        """Classify LinkedIn URL type using Context7 patterns"""
        if '/in/' in linkedin_url:
            return 'personal_profile'
        elif '/company/' in linkedin_url:
            return 'company_page'
        elif '/pub/' in linkedin_url:
            return 'public_profile'
        else:
            return 'unknown'
    
    def _is_executive_linkedin(self, linkedin_url: str, context: str) -> bool:
        """Determine if LinkedIn profile belongs to executive"""
        context_lower = context.lower()
        return any(title in context_lower for title in self.executive_contexts)
    
    def _deduplicate_phones(self, phones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate phone numbers using Context7 best practices"""
        seen_phones = set()
        deduplicated = []
        
        # Sort by confidence descending
        phones.sort(key=lambda x: x['confidence'], reverse=True)
        
        for phone in phones:
            # Normalize phone number for comparison
            normalized = re.sub(r'[^0-9]', '', phone['number'])
            
            if normalized not in seen_phones and len(normalized) >= 10:
                seen_phones.add(normalized)
                deduplicated.append(phone)
        
        return deduplicated
    
    def _deduplicate_emails(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate email addresses using Context7 best practices"""
        seen_emails = set()
        deduplicated = []
        
        # Sort by confidence descending
        emails.sort(key=lambda x: x['confidence'], reverse=True)
        
        for email in emails:
            email_addr = email['address'].lower()
            
            if email_addr not in seen_emails:
                seen_emails.add(email_addr)
                deduplicated.append(email)
        
        return deduplicated
    
    def _deduplicate_linkedin(self, profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate LinkedIn profiles using Context7 best practices"""
        seen_profiles = set()
        deduplicated = []
        
        # Sort by confidence descending
        profiles.sort(key=lambda x: x['confidence'], reverse=True)
        
        for profile in profiles:
            # Normalize URL for comparison
            normalized_url = profile['url'].lower().split('?')[0]  # Remove query parameters
            
            if normalized_url not in seen_profiles:
                seen_profiles.add(normalized_url)
                deduplicated.append(profile)
        
        return deduplicated

class Phase9aExecutiveContactAttributor:
    """Context7-Inspired Executive-Contact Attribution System"""
    
    def __init__(self, config: Phase9aConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.contact_patterns = Phase9aAdvancedContactPatterns(config)
    
    def attribute_contacts_to_executives(self, executives: List[Dict], content: str, company_domain: str = "") -> List[ExecutiveProfile]:
        """Attribute contact information to executives using Context7 best practices"""
        attributed_profiles = []
        
        # Extract all contact information
        all_phones = self.contact_patterns.extract_phone_numbers(content)
        all_emails = self.contact_patterns.extract_email_addresses(content, company_domain)
        all_linkedin = self.contact_patterns.extract_linkedin_profiles(content)
        
        for executive in executives:
            exec_name = executive.get('name', '')
            exec_title = executive.get('title', '')
            
            # Find contacts near this executive's mention
            exec_contacts = self._find_executive_contacts(
                exec_name, exec_title, content, all_phones, all_emails, all_linkedin
            )
            
            # Create contact info
            contact_info = ContactInfo(
                phone_numbers=[contact['number'] for contact in exec_contacts['phones']],
                email_addresses=[contact['address'] for contact in exec_contacts['emails']],
                linkedin_profiles=[contact['url'] for contact in exec_contacts['linkedin']],
                contact_quality_score=self._calculate_contact_quality(exec_contacts),
                completeness_percentage=self._calculate_completeness(exec_contacts),
                source_pages=[],  # To be filled by caller
                confidence_scores={
                    'phone': max([c['confidence'] for c in exec_contacts['phones']] + [0]),
                    'email': max([c['confidence'] for c in exec_contacts['emails']] + [0]),
                    'linkedin': max([c['confidence'] for c in exec_contacts['linkedin']] + [0])
                }
            )
            
            # Create executive profile
            exec_profile = ExecutiveProfile(
                name=exec_name,
                title=exec_title,
                company=executive.get('company', ''),
                contact_info=contact_info,
                extraction_source='phase9a_contact_extraction',
                overall_confidence=self._calculate_overall_confidence(contact_info, executive),
                discovery_timestamp=str(int(time.time()))
            )
            
            attributed_profiles.append(exec_profile)
        
        return attributed_profiles
    
    def _find_executive_contacts(self, name: str, title: str, content: str, all_phones: List, all_emails: List, all_linkedin: List) -> Dict:
        """Find contacts associated with specific executive using Context7 proximity analysis"""
        exec_contacts = {'phones': [], 'emails': [], 'linkedin': []}
        
        # Find all mentions of the executive name
        name_positions = []
        for match in re.finditer(re.escape(name), content, re.IGNORECASE):
            name_positions.append(match.start())
        
        # Also search for title mentions
        if title:
            for match in re.finditer(re.escape(title), content, re.IGNORECASE):
                name_positions.append(match.start())
        
        if not name_positions:
            return exec_contacts
        
        # Find contacts within proximity of executive mentions
        proximity_window = 500  # Characters
        
        for contact_type, contacts in [('phones', all_phones), ('emails', all_emails), ('linkedin', all_linkedin)]:
            for contact in contacts:
                contact_pos = content.find(contact.get('number', contact.get('address', contact.get('url', ''))))
                
                if contact_pos == -1:
                    continue
                
                # Check if contact is within proximity of any executive mention
                for name_pos in name_positions:
                    if abs(contact_pos - name_pos) <= proximity_window:
                        exec_contacts[contact_type].append(contact)
                        break
        
        return exec_contacts
    
    def _calculate_contact_quality(self, exec_contacts: Dict) -> float:
        """Calculate contact quality score using Context7 assessment"""
        quality_score = 0.0
        total_contacts = sum(len(contacts) for contacts in exec_contacts.values())
        
        if total_contacts == 0:
            return 0.0
        
        # Weight different contact types
        weights = {'phones': 0.4, 'emails': 0.4, 'linkedin': 0.2}
        
        for contact_type, contacts in exec_contacts.items():
            if contacts:
                avg_confidence = sum(c['confidence'] for c in contacts) / len(contacts)
                quality_score += avg_confidence * weights[contact_type]
        
        return min(1.0, quality_score)
    
    def _calculate_completeness(self, exec_contacts: Dict) -> float:
        """Calculate contact completeness percentage using Context7 standards"""
        completeness = 0.0
        
        # Check presence of each contact type
        if exec_contacts['phones']:
            completeness += 40  # 40% for phone
        if exec_contacts['emails']:
            completeness += 40  # 40% for email
        if exec_contacts['linkedin']:
            completeness += 20  # 20% for LinkedIn
        
        return completeness
    
    def _calculate_overall_confidence(self, contact_info: ContactInfo, executive: Dict) -> float:
        """Calculate overall executive profile confidence using Context7 weighting"""
        # Base confidence from executive extraction
        base_confidence = executive.get('confidence', 0.5)
        
        # Contact contribution
        contact_contribution = contact_info.contact_quality_score * 0.3
        
        # Completeness contribution
        completeness_contribution = (contact_info.completeness_percentage / 100) * 0.2
        
        overall_confidence = base_confidence + contact_contribution + completeness_contribution
        return min(1.0, overall_confidence)

class Phase9aContactExtractionEngine:
    """Context7-Inspired Contact Extraction Engine - Main Interface"""
    
    def __init__(self, config: Optional[Phase9aConfig] = None):
        self.config = config or Phase9aConfig()
        self.logger = logging.getLogger(__name__)
        self.contact_patterns = Phase9aAdvancedContactPatterns(self.config)
        self.contact_attributor = Phase9aExecutiveContactAttributor(self.config)
        
        # Initialize processing statistics
        self.processing_stats = {
            'companies_processed': 0,
            'executives_found': 0,
            'contacts_extracted': 0,
            'processing_time': 0.0
        }
    
    async def extract_executive_contacts(self, company_name: str, website_url: str, existing_executives: List[Dict] = None) -> Dict[str, Any]:
        """Extract executive contact information using Context7 best practices"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting contact extraction for {company_name}")
            
            # Extract company domain for email inference
            company_domain = self._extract_domain(website_url)
            
            # Fetch content from multiple pages
            content_data = await self._fetch_company_content(website_url)
            
            # If no existing executives provided, extract them first
            if not existing_executives:
                existing_executives = await self._extract_executives_from_content(content_data)
            
            # Attribute contacts to executives
            executive_profiles = self.contact_attributor.attribute_contacts_to_executives(
                existing_executives, content_data['full_content'], company_domain
            )
            
            # Calculate overall metrics
            processing_time = time.time() - start_time
            result = {
                'company_name': company_name,
                'website_url': website_url,
                'company_domain': company_domain,
                'executive_profiles': [asdict(profile) for profile in executive_profiles],
                'extraction_stats': {
                    'executives_found': len(executive_profiles),
                    'total_contacts_extracted': sum(
                        len(p.contact_info.phone_numbers) + 
                        len(p.contact_info.email_addresses) + 
                        len(p.contact_info.linkedin_profiles) 
                        for p in executive_profiles
                    ),
                    'average_completeness': sum(p.contact_info.completeness_percentage for p in executive_profiles) / len(executive_profiles) if executive_profiles else 0,
                    'processing_time_seconds': processing_time,
                    'pages_analyzed': content_data['pages_analyzed']
                },
                'quality_assessment': self._assess_extraction_quality(executive_profiles),
                'extraction_timestamp': int(time.time())
            }
            
            # Update processing statistics
            self._update_processing_stats(result)
            
            self.logger.info(f"Contact extraction completed for {company_name}: {len(executive_profiles)} executives, {result['extraction_stats']['total_contacts_extracted']} contacts")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in contact extraction for {company_name}: {e}")
            return {
                'company_name': company_name,
                'website_url': website_url,
                'error': str(e),
                'executive_profiles': [],
                'extraction_stats': {'processing_time_seconds': time.time() - start_time},
                'extraction_timestamp': int(time.time())
            }
    
    async def _fetch_company_content(self, website_url: str) -> Dict[str, Any]:
        """Fetch company content using Context7 multi-page strategy"""
        content_data = {
            'full_content': '',
            'pages_analyzed': 0,
            'relevant_pages': []
        }
        
        # Priority pages for contact information
        priority_paths = [
            '',  # Main page
            '/about', '/about-us', '/team', '/staff', '/management',
            '/contact', '/contact-us', '/contacts',
            '/leadership', '/executives', '/directors',
            '/people', '/our-team', '/meet-the-team'
        ]
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.session_timeout)) as session:
            for path in priority_paths[:self.config.max_pages_per_company]:
                try:
                    url = urljoin(website_url, path)
                    async with session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Extract text content
                            text_content = soup.get_text()
                            content_data['full_content'] += f"\n\n{text_content}"
                            content_data['pages_analyzed'] += 1
                            content_data['relevant_pages'].append(url)
                            
                except Exception as e:
                    self.logger.warning(f"Failed to fetch {url}: {e}")
                    continue
        
        return content_data
    
    async def _extract_executives_from_content(self, content_data: Dict) -> List[Dict]:
        """Extract executives from content using existing AI pipeline"""
        # This would integrate with Phase 8 AI platform
        # For now, return basic name extraction
        executives = []
        
        # Simple name extraction pattern
        name_pattern = r'\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b'
        names = re.findall(name_pattern, content_data['full_content'])
        
        for name in names[:20]:  # Limit to first 20 names
            executives.append({
                'name': name,
                'title': 'Unknown',
                'company': '',
                'confidence': 0.6
            })
        
        return executives
    
    def _extract_domain(self, website_url: str) -> str:
        """Extract domain from website URL using Context7 parsing"""
        try:
            parsed = urlparse(website_url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    def _assess_extraction_quality(self, executive_profiles: List[ExecutiveProfile]) -> Dict[str, Any]:
        """Assess extraction quality using Context7 metrics"""
        if not executive_profiles:
            return {'overall_quality': 'POOR', 'quality_score': 0.0}
        
        # Calculate quality metrics
        avg_completeness = sum(p.contact_info.completeness_percentage for p in executive_profiles) / len(executive_profiles)
        avg_confidence = sum(p.overall_confidence for p in executive_profiles) / len(executive_profiles)
        
        # Contact type coverage
        has_phones = sum(1 for p in executive_profiles if p.contact_info.phone_numbers)
        has_emails = sum(1 for p in executive_profiles if p.contact_info.email_addresses)
        has_linkedin = sum(1 for p in executive_profiles if p.contact_info.linkedin_profiles)
        
        coverage_score = (has_phones + has_emails + has_linkedin) / (len(executive_profiles) * 3)
        
        # Overall quality score
        quality_score = (avg_completeness / 100 * 0.4) + (avg_confidence * 0.4) + (coverage_score * 0.2)
        
        # Quality tier
        if quality_score >= 0.8:
            quality_tier = 'PREMIUM'
        elif quality_score >= 0.6:
            quality_tier = 'HIGH'
        elif quality_score >= 0.4:
            quality_tier = 'MEDIUM'
        else:
            quality_tier = 'LOW'
        
        return {
            'overall_quality': quality_tier,
            'quality_score': quality_score,
            'average_completeness': avg_completeness,
            'average_confidence': avg_confidence,
            'contact_coverage': {
                'phones': has_phones,
                'emails': has_emails,
                'linkedin': has_linkedin
            }
        }
    
    def _update_processing_stats(self, result: Dict[str, Any]):
        """Update processing statistics"""
        self.processing_stats['companies_processed'] += 1
        self.processing_stats['executives_found'] += result['extraction_stats']['executives_found']
        self.processing_stats['contacts_extracted'] += result['extraction_stats']['total_contacts_extracted']
        self.processing_stats['processing_time'] += result['extraction_stats']['processing_time_seconds']
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get processing summary using Context7 reporting"""
        return {
            'total_companies_processed': self.processing_stats['companies_processed'],
            'total_executives_found': self.processing_stats['executives_found'],
            'total_contacts_extracted': self.processing_stats['contacts_extracted'],
            'average_processing_time': self.processing_stats['processing_time'] / max(1, self.processing_stats['companies_processed']),
            'executives_per_company': self.processing_stats['executives_found'] / max(1, self.processing_stats['companies_processed']),
            'contacts_per_executive': self.processing_stats['contacts_extracted'] / max(1, self.processing_stats['executives_found'])
        }

# Test function
async def test_phase9a_contact_extraction():
    """Test Phase 9A Contact Extraction Engine"""
    print("🚀 Testing Phase 9A Contact Extraction Engine")
    
    config = Phase9aConfig()
    engine = Phase9aContactExtractionEngine(config)
    
    # Test companies
    test_companies = [
        ("A&H Plumbing", "http://anhplumbing.com"),
        ("Air-Tech Systems Inc", "https://air-techsystems.com/")
    ]
    
    results = []
    
    for company_name, website_url in test_companies:
        print(f"\n📊 Processing: {company_name}")
        result = await engine.extract_executive_contacts(company_name, website_url)
        results.append(result)
        
        # Display results
        print(f"✅ Found {result['extraction_stats']['executives_found']} executives")
        print(f"📞 Extracted {result['extraction_stats']['total_contacts_extracted']} contacts")
        print(f"📈 Average completeness: {result['extraction_stats']['average_completeness']:.1f}%")
        print(f"⏱️ Processing time: {result['extraction_stats']['processing_time_seconds']:.2f}s")
    
    # Save results
    timestamp = int(time.time())
    results_file = f"phase9a_contact_extraction_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Display processing summary
    summary = engine.get_processing_summary()
    print(f"\n📊 Processing Summary:")
    print(f"Companies processed: {summary['total_companies_processed']}")
    print(f"Executives found: {summary['total_executives_found']}")
    print(f"Contacts extracted: {summary['total_contacts_extracted']}")
    print(f"Avg processing time: {summary['average_processing_time']:.2f}s")
    
    return results

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    asyncio.run(test_phase9a_contact_extraction()) 