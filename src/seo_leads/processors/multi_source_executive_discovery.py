"""
Multi-Source Executive Discovery Engine
Comprehensive executive discovery using 5 parallel strategies for maximum coverage
"""

import re
import asyncio
import logging
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

@dataclass
class ExecutiveCandidate:
    """Represents a potential executive with discovery metadata"""
    name: str
    source_strategy: str
    confidence: float
    context: str
    position_in_content: int
    additional_info: Dict = field(default_factory=dict)
    
@dataclass
class CompanyInfo:
    """Company information for context"""
    name: str
    domain: str
    url: str
    industry: str = "Unknown"

class MultiSourceExecutiveDiscovery:
    """
    Advanced executive discovery using multiple parallel strategies
    Designed to increase discovery rate from 50% to 80%+
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # UK executive title patterns
        self.executive_titles = {
            'ceo', 'chief executive', 'managing director', 'md', 'director',
            'founder', 'co-founder', 'owner', 'proprietor', 'partner',
            'manager', 'head', 'lead', 'senior', 'principal', 'supervisor',
            'operations manager', 'general manager', 'business manager',
            'sales director', 'technical director', 'finance director'
        }
        
        # Name patterns for UK names
        self.name_pattern = re.compile(r'\b([A-Z][a-z]{1,15})\s+([A-Z][a-z]{1,20})\b')
        
        # Team/About page indicators
        self.team_indicators = [
            'team', 'about', 'staff', 'management', 'directors', 'leadership',
            'our team', 'meet the team', 'about us', 'who we are', 'management team'
        ]
        
        # Contact page indicators
        self.contact_indicators = [
            'contact', 'get in touch', 'reach us', 'contact us', 'speak to',
            'call us', 'email us', 'contact details', 'contact information'
        ]
        
    async def discover_executives(self, url: str, content: str, company_info: CompanyInfo) -> List[ExecutiveCandidate]:
        """
        Main discovery method using 5 parallel strategies
        """
        try:
            self.logger.info(f"Starting multi-source executive discovery for: {url}")
            
            # Run all 5 strategies in parallel
            discovery_tasks = [
                self._extract_from_team_pages(content, company_info),
                self._extract_from_contact_pages(content, company_info),
                self._extract_from_signatures(content, company_info),
                self._extract_from_social_links(url, content, company_info),
                self._extract_from_companies_house(company_info)
            ]
            
            results = await asyncio.gather(*discovery_tasks, return_exceptions=True)
            
            # Collect all candidates
            all_candidates = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.warning(f"Strategy {i+1} failed: {str(result)}")
                    continue
                all_candidates.extend(result)
            
            # Merge and deduplicate
            final_executives = self._merge_and_deduplicate(all_candidates)
            
            self.logger.info(f"Discovered {len(final_executives)} executives from {len(all_candidates)} candidates")
            return final_executives
            
        except Exception as e:
            self.logger.error(f"Executive discovery failed for {url}: {str(e)}")
            return []
    
    async def _extract_from_team_pages(self, content: str, company_info: CompanyInfo) -> List[ExecutiveCandidate]:
        """
        Strategy 1: Extract executives from dedicated team/about pages
        """
        candidates = []
        
        try:
            # Look for team sections
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find team/about sections
            team_sections = []
            for indicator in self.team_indicators:
                # Find sections with team indicators in headings
                headings = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=re.compile(indicator, re.IGNORECASE))
                for heading in headings:
                    # Get the section content after the heading
                    section_content = self._get_section_content(heading)
                    if section_content:
                        team_sections.append(section_content)
                
                # Find divs/sections with team classes or IDs
                sections = soup.find_all(['div', 'section'], {'class': re.compile(indicator, re.IGNORECASE)})
                sections.extend(soup.find_all(['div', 'section'], {'id': re.compile(indicator, re.IGNORECASE)}))
                team_sections.extend([section.get_text() for section in sections])
            
            # Extract names from team sections
            for section_text in team_sections:
                names = self._extract_names_with_context(section_text, "team_page")
                for name, context, position in names:
                    candidates.append(ExecutiveCandidate(
                        name=name,
                        source_strategy="team_page",
                        confidence=0.8,  # High confidence for team pages
                        context=context,
                        position_in_content=position,
                        additional_info={"section_type": "team"}
                    ))
            
        except Exception as e:
            self.logger.warning(f"Team page extraction failed: {str(e)}")
        
        return candidates
    
    async def _extract_from_contact_pages(self, content: str, company_info: CompanyInfo) -> List[ExecutiveCandidate]:
        """
        Strategy 2: Extract executives from contact pages and contact sections
        """
        candidates = []
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find contact sections
            contact_sections = []
            for indicator in self.contact_indicators:
                # Contact headings
                headings = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=re.compile(indicator, re.IGNORECASE))
                for heading in headings:
                    section_content = self._get_section_content(heading)
                    if section_content:
                        contact_sections.append(section_content)
                
                # Contact divs/sections
                sections = soup.find_all(['div', 'section'], {'class': re.compile(indicator, re.IGNORECASE)})
                sections.extend(soup.find_all(['div', 'section'], {'id': re.compile(indicator, re.IGNORECASE)}))
                contact_sections.extend([section.get_text() for section in sections])
            
            # Look for "Contact [Name]" patterns
            contact_patterns = [
                r'contact\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'speak\s+to\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'call\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'email\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
            ]
            
            for section_text in contact_sections:
                # Extract contact-specific patterns
                for pattern in contact_patterns:
                    matches = re.finditer(pattern, section_text, re.IGNORECASE)
                    for match in matches:
                        name = match.group(1)
                        context = section_text[max(0, match.start()-50):match.end()+50]
                        
                        candidates.append(ExecutiveCandidate(
                            name=name,
                            source_strategy="contact_page",
                            confidence=0.9,  # Very high confidence for contact patterns
                            context=context,
                            position_in_content=match.start(),
                            additional_info={"pattern": pattern}
                        ))
                
                # Also extract general names from contact sections
                names = self._extract_names_with_context(section_text, "contact_page")
                for name, context, position in names:
                    candidates.append(ExecutiveCandidate(
                        name=name,
                        source_strategy="contact_page",
                        confidence=0.7,
                        context=context,
                        position_in_content=position,
                        additional_info={"section_type": "contact"}
                    ))
            
        except Exception as e:
            self.logger.warning(f"Contact page extraction failed: {str(e)}")
        
        return candidates
    
    async def _extract_from_signatures(self, content: str, company_info: CompanyInfo) -> List[ExecutiveCandidate]:
        """
        Strategy 3: Extract executives from email signatures and footer information
        """
        candidates = []
        
        try:
            # Look for signature patterns
            signature_patterns = [
                r'regards,?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'best\s+regards,?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'yours\s+sincerely,?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'kind\s+regards,?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*,?\s*(director|manager|ceo|md)',
                r'(director|manager|ceo|md)\s*:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)'
            ]
            
            for pattern in signature_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Extract name from the appropriate group
                    if 'director' in pattern or 'manager' in pattern:
                        name = match.group(2) if len(match.groups()) > 1 else match.group(1)
                    else:
                        name = match.group(1)
                    
                    context = content[max(0, match.start()-100):match.end()+100]
                    
                    candidates.append(ExecutiveCandidate(
                        name=name,
                        source_strategy="signature",
                        confidence=0.8,
                        context=context,
                        position_in_content=match.start(),
                        additional_info={"signature_type": "email"}
                    ))
            
            # Look for footer executive information
            soup = BeautifulSoup(content, 'html.parser')
            footers = soup.find_all('footer')
            footers.extend(soup.find_all(['div'], {'class': re.compile('footer', re.IGNORECASE)}))
            
            for footer in footers:
                footer_text = footer.get_text()
                names = self._extract_names_with_context(footer_text, "footer")
                for name, context, position in names:
                    candidates.append(ExecutiveCandidate(
                        name=name,
                        source_strategy="signature",
                        confidence=0.6,
                        context=context,
                        position_in_content=position,
                        additional_info={"section_type": "footer"}
                    ))
            
        except Exception as e:
            self.logger.warning(f"Signature extraction failed: {str(e)}")
        
        return candidates
    
    async def _extract_from_social_links(self, url: str, content: str, company_info: CompanyInfo) -> List[ExecutiveCandidate]:
        """
        Strategy 4: Extract executives from social media links and profiles
        """
        candidates = []
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find social media links
            social_links = []
            social_patterns = [
                r'linkedin\.com/in/([^/\s"\']+)',
                r'twitter\.com/([^/\s"\']+)',
                r'facebook\.com/([^/\s"\']+)'
            ]
            
            # Extract from href attributes
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                for pattern in social_patterns:
                    match = re.search(pattern, href, re.IGNORECASE)
                    if match:
                        social_links.append((href, match.group(1)))
            
            # Extract from text content
            for pattern in social_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    social_links.append((match.group(0), match.group(1)))
            
            # Analyze social profiles for executive names
            for social_url, profile_id in social_links:
                # Try to extract name from profile ID
                if 'linkedin.com/in/' in social_url:
                    # LinkedIn profiles often have name-based URLs
                    name_candidate = self._extract_name_from_profile_id(profile_id)
                    if name_candidate:
                        candidates.append(ExecutiveCandidate(
                            name=name_candidate,
                            source_strategy="social_media",
                            confidence=0.7,
                            context=f"LinkedIn profile: {social_url}",
                            position_in_content=0,
                            additional_info={"social_platform": "linkedin", "profile_url": social_url}
                        ))
            
        except Exception as e:
            self.logger.warning(f"Social media extraction failed: {str(e)}")
        
        return candidates
    
    async def _extract_from_companies_house(self, company_info: CompanyInfo) -> List[ExecutiveCandidate]:
        """
        Strategy 5: Extract executives from Companies House API (UK company registration data)
        """
        candidates = []
        
        try:
            # This would integrate with Companies House API
            # For now, we'll implement a placeholder that could be enhanced with API access
            
            # Extract company name for potential director search
            company_name = company_info.name
            if company_name and len(company_name) > 3:
                # Placeholder for Companies House integration
                # In a full implementation, this would query the Companies House API
                # for director information based on company name or number
                
                self.logger.info(f"Companies House lookup for: {company_name} (placeholder)")
                
                # For now, return empty list - this would be enhanced with actual API integration
                pass
            
        except Exception as e:
            self.logger.warning(f"Companies House extraction failed: {str(e)}")
        
        return candidates
    
    def _extract_names_with_context(self, text: str, source: str) -> List[Tuple[str, str, int]]:
        """
        Extract names with surrounding context from text
        Returns list of (name, context, position) tuples
        """
        names_with_context = []
        
        matches = self.name_pattern.finditer(text)
        for match in matches:
            name = match.group().strip()
            position = match.start()
            
            # Get context around the name
            context_start = max(0, position - 100)
            context_end = min(len(text), position + 100)
            context = text[context_start:context_end].strip()
            
            # Basic validation - skip obvious non-names
            if self._is_likely_name(name, context):
                names_with_context.append((name, context, position))
        
        return names_with_context
    
    def _is_likely_name(self, name: str, context: str) -> bool:
        """
        Basic validation to filter out obvious non-names
        """
        name_lower = name.lower()
        context_lower = context.lower()
        
        # Skip obvious service terms
        service_terms = {
            'plumbing', 'heating', 'emergency', 'service', 'repair', 'installation',
            'commercial', 'residential', 'call', 'contact', 'email', 'phone'
        }
        
        for term in service_terms:
            if term in name_lower:
                return False
        
        # Skip location names
        location_terms = {
            'birmingham', 'london', 'manchester', 'leeds', 'liverpool',
            'street', 'road', 'avenue', 'lane', 'close'
        }
        
        for term in location_terms:
            if term in name_lower:
                return False
        
        return True
    
    def _get_section_content(self, heading_element) -> Optional[str]:
        """
        Extract content from a section starting with a heading
        """
        try:
            content_parts = []
            current = heading_element.next_sibling
            
            # Collect content until next heading or end of section
            while current and current.name not in ['h1', 'h2', 'h3', 'h4']:
                if hasattr(current, 'get_text'):
                    text = current.get_text().strip()
                    if text:
                        content_parts.append(text)
                current = current.next_sibling
            
            return ' '.join(content_parts) if content_parts else None
            
        except Exception:
            return None
    
    def _extract_name_from_profile_id(self, profile_id: str) -> Optional[str]:
        """
        Try to extract a real name from a social media profile ID
        """
        try:
            # Clean the profile ID
            profile_id = profile_id.lower().strip()
            
            # Skip obvious non-name profiles
            skip_patterns = ['company', 'business', 'official', 'page', 'group']
            if any(pattern in profile_id for pattern in skip_patterns):
                return None
            
            # Try to extract name from common patterns
            # Pattern: firstname-lastname or firstname.lastname
            if '-' in profile_id or '.' in profile_id:
                separator = '-' if '-' in profile_id else '.'
                parts = profile_id.split(separator)
                if len(parts) == 2:
                    first_name = parts[0].capitalize()
                    last_name = parts[1].capitalize()
                    if len(first_name) > 1 and len(last_name) > 1:
                        return f"{first_name} {last_name}"
            
            return None
            
        except Exception:
            return None
    
    def _merge_and_deduplicate(self, candidates: List[ExecutiveCandidate]) -> List[ExecutiveCandidate]:
        """
        Merge similar candidates and remove duplicates
        """
        if not candidates:
            return []
        
        # Group by normalized name
        name_groups = {}
        for candidate in candidates:
            normalized_name = self._normalize_name(candidate.name)
            if normalized_name not in name_groups:
                name_groups[normalized_name] = []
            name_groups[normalized_name].append(candidate)
        
        # Merge each group
        merged_candidates = []
        for normalized_name, group in name_groups.items():
            if len(group) == 1:
                merged_candidates.append(group[0])
            else:
                # Merge multiple candidates for the same name
                merged = self._merge_candidate_group(group)
                merged_candidates.append(merged)
        
        # Sort by confidence
        merged_candidates.sort(key=lambda x: x.confidence, reverse=True)
        
        return merged_candidates
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize name for comparison (remove extra spaces, standardize case)
        """
        return ' '.join(name.strip().split()).title()
    
    def _merge_candidate_group(self, candidates: List[ExecutiveCandidate]) -> ExecutiveCandidate:
        """
        Merge multiple candidates for the same person
        """
        # Use the candidate with highest confidence as base
        base_candidate = max(candidates, key=lambda x: x.confidence)
        
        # Combine information from all candidates
        all_strategies = [c.source_strategy for c in candidates]
        all_contexts = [c.context for c in candidates]
        
        # Calculate merged confidence (higher if found in multiple sources)
        confidence_boost = min(0.2, len(candidates) * 0.05)
        merged_confidence = min(1.0, base_candidate.confidence + confidence_boost)
        
        return ExecutiveCandidate(
            name=base_candidate.name,
            source_strategy=', '.join(set(all_strategies)),
            confidence=merged_confidence,
            context='; '.join(all_contexts[:3]),  # Limit context length
            position_in_content=base_candidate.position_in_content,
            additional_info={
                'merged_from': len(candidates),
                'all_strategies': all_strategies,
                **base_candidate.additional_info
            }
        ) 