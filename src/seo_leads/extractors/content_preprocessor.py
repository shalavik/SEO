"""
Content Preprocessor for Executive Discovery - Phase 5B Enhancement
Cleans HTML content and identifies executive-relevant sections before name extraction.
"""

import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class ContentPreprocessor:
    """
    Preprocesses website content to improve executive name extraction accuracy.
    
    Key Features:
    - HTML tag removal and text cleaning
    - Executive content section identification
    - HTML artifact filtering
    - Context area detection for better attribution
    """
    
    def __init__(self):
        """Initialize content preprocessor with patterns and filters"""
        
        # HTML tags and artifacts to exclude from name extraction
        self.html_excludes = {
            'html_tags': ['DOCTYPE', 'html', 'head', 'body', 'meta', 'link', 'script', 'style'],
            'css_classes': ['nav', 'menu', 'footer', 'header', 'sidebar', 'widget'],
            'technical_terms': ['charset', 'viewport', 'javascript', 'css', 'font-face'],
            'web_frameworks': ['WordPress', 'Wix', 'Squarespace', 'Shopify', 'React', 'Angular']
        }
        
        # Executive section indicators
        self.executive_sections = [
            'about us', 'team', 'management', 'leadership', 'directors', 'staff',
            'meet the team', 'our team', 'who we are', 'management team',
            'executive team', 'board of directors', 'company directors',
            'key personnel', 'senior management', 'leadership team'
        ]
        
        # Context areas for contact attribution
        self.contact_contexts = [
            'contact', 'get in touch', 'reach us', 'contact us', 'call us',
            'email us', 'phone', 'telephone', 'mobile', 'office'
        ]

    def clean_html_content(self, content: str) -> Dict[str, Any]:
        """
        Clean HTML content and extract text suitable for executive discovery.
        
        Args:
            content: Raw HTML content from website
            
        Returns:
            Dict containing cleaned text and metadata
        """
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "noscript"]):
                script.decompose()
            
            # Extract title for context
            title = soup.find('title')
            page_title = title.get_text().strip() if title else ""
            
            # Get main text content
            text_content = soup.get_text()
            
            # Clean the text
            cleaned_text = self._clean_text_content(text_content)
            
            # Identify executive sections
            executive_sections = self.identify_executive_sections(cleaned_text)
            
            # Identify contact sections  
            contact_sections = self.identify_contact_sections(cleaned_text)
            
            return {
                'cleaned_text': cleaned_text,
                'page_title': page_title,
                'executive_sections': executive_sections,
                'contact_sections': contact_sections,
                'total_length': len(cleaned_text),
                'sections_found': len(executive_sections) + len(contact_sections)
            }
            
        except Exception as e:
            logger.warning(f"HTML cleaning failed: {e}")
            # Fallback to basic text cleaning
            return {
                'cleaned_text': self._clean_text_content(content),
                'page_title': "",
                'executive_sections': [],
                'contact_sections': [],
                'total_length': len(content),
                'sections_found': 0
            }

    def _clean_text_content(self, text: str) -> str:
        """Clean raw text content from HTML artifacts"""
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common HTML artifacts
        text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', text)  # HTML entities
        text = re.sub(r'[{}[\]()]+', ' ', text)  # Brackets and braces
        text = re.sub(r'[|]+', ' ', text)  # Pipe characters
        
        # Remove technical terms that might be confused as names
        for term_category in self.html_excludes.values():
            for term in term_category:
                # Case insensitive removal with word boundaries
                pattern = r'\b' + re.escape(term) + r'\b'
                text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # Clean up spacing
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def identify_executive_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        Identify sections of content that likely contain executive information.
        
        Args:
            content: Cleaned text content
            
        Returns:
            List of executive sections with context
        """
        sections = []
        content_lower = content.lower()
        
        for section_indicator in self.executive_sections:
            # Find section indicators
            matches = []
            start = 0
            
            while True:
                index = content_lower.find(section_indicator, start)
                if index == -1:
                    break
                    
                # Extract context around the section (500 chars each side)
                section_start = max(0, index - 500)
                section_end = min(len(content), index + 500)
                section_text = content[section_start:section_end]
                
                matches.append({
                    'indicator': section_indicator,
                    'position': index,
                    'context': section_text,
                    'length': len(section_text)
                })
                
                start = index + len(section_indicator)
            
            sections.extend(matches)
        
        # Sort by position and remove duplicates
        sections = sorted(sections, key=lambda x: x['position'])
        
        # Merge overlapping sections
        merged_sections = self._merge_overlapping_sections(sections)
        
        logger.info(f"Identified {len(merged_sections)} executive sections")
        return merged_sections

    def identify_contact_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        Identify sections that likely contain contact information.
        
        Args:
            content: Cleaned text content
            
        Returns:
            List of contact sections with context
        """
        sections = []
        content_lower = content.lower()
        
        for contact_indicator in self.contact_contexts:
            # Find contact section indicators
            matches = []
            start = 0
            
            while True:
                index = content_lower.find(contact_indicator, start)
                if index == -1:
                    break
                    
                # Extract context around contact section (300 chars each side)
                section_start = max(0, index - 300)
                section_end = min(len(content), index + 300)
                section_text = content[section_start:section_end]
                
                matches.append({
                    'indicator': contact_indicator,
                    'position': index,
                    'context': section_text,
                    'length': len(section_text)
                })
                
                start = index + len(contact_indicator)
            
            sections.extend(matches)
        
        # Sort and merge
        sections = sorted(sections, key=lambda x: x['position'])
        merged_sections = self._merge_overlapping_sections(sections)
        
        logger.info(f"Identified {len(merged_sections)} contact sections")
        return merged_sections

    def _merge_overlapping_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge overlapping content sections to avoid duplication"""
        if not sections:
            return []
        
        merged = [sections[0]]
        
        for section in sections[1:]:
            last_merged = merged[-1]
            
            # Check if sections overlap (within 100 characters)
            if section['position'] - (last_merged['position'] + len(last_merged['context'])) < 100:
                # Merge sections
                merged_context = last_merged['context'] + " " + section['context']
                last_merged['context'] = merged_context
                last_merged['length'] = len(merged_context)
                last_merged['indicator'] += f", {section['indicator']}"
            else:
                merged.append(section)
        
        return merged

    def filter_html_artifacts_from_names(self, names: List[str]) -> List[str]:
        """
        Filter out HTML artifacts from extracted name candidates.
        
        Args:
            names: List of potential executive names
            
        Returns:
            Filtered list of valid names
        """
        filtered_names = []
        
        for name in names:
            if self._is_valid_executive_name(name):
                filtered_names.append(name)
            else:
                logger.debug(f"Filtered out HTML artifact: {name}")
        
        return filtered_names

    def _is_valid_executive_name(self, name: str) -> bool:
        """
        Validate if a string could be a valid executive name.
        
        Args:
            name: Candidate name string
            
        Returns:
            True if valid name, False if HTML artifact
        """
        name = name.strip()
        
        # Basic length and format checks
        if len(name) < 3 or len(name) > 50:
            return False
        
        # Check against HTML excludes
        name_lower = name.lower()
        
        # Exclude HTML tags
        for html_tag in self.html_excludes['html_tags']:
            if html_tag.lower() in name_lower:
                return False
        
        # Exclude CSS classes
        for css_class in self.html_excludes['css_classes']:
            if css_class.lower() in name_lower:
                return False
        
        # Exclude technical terms
        for tech_term in self.html_excludes['technical_terms']:
            if tech_term.lower() in name_lower:
                return False
        
        # Exclude web frameworks
        for framework in self.html_excludes['web_frameworks']:
            if framework.lower() in name_lower:
                return False
        
        # Must contain letters
        if not re.search(r'[a-zA-Z]', name):
            return False
        
        # Should not be all caps (likely a heading or technical term)
        if name.isupper() and len(name) > 5:
            return False
        
        # Should not contain multiple consecutive special characters
        if re.search(r'[^a-zA-Z\s]{2,}', name):
            return False
        
        # Valid name candidate
        return True

    def extract_name_context_pairs(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract potential names with their surrounding context for attribution.
        
        Args:
            content: Cleaned text content
            
        Returns:
            List of name-context pairs for contact attribution
        """
        # Simple name pattern (First Last format)
        name_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
        
        name_contexts = []
        
        for match in re.finditer(name_pattern, content):
            name = match.group(1)
            start_pos = match.start()
            end_pos = match.end()
            
            # Skip if it's an HTML artifact
            if not self._is_valid_executive_name(name):
                continue
            
            # Extract context around the name (200 chars each side)
            context_start = max(0, start_pos - 200)
            context_end = min(len(content), end_pos + 200)
            context = content[context_start:context_end]
            
            name_contexts.append({
                'name': name,
                'position': start_pos,
                'context': context,
                'context_start': context_start,
                'context_end': context_end
            })
        
        logger.info(f"Extracted {len(name_contexts)} name-context pairs")
        return name_contexts 