"""
Enhanced Name Extractor - Phase 1 Discovery Rate Improvement

This module implements enhanced executive name detection to improve discovery rate from 20% to 45%+ 
by expanding pattern recognition, improving content analysis, and adding industry-specific detection.

Key improvements:
1. Expanded executive title patterns including industry-specific titles
2. Enhanced content section analysis (About Us, Team, Contact)
3. Improved name entity recognition with validation
4. Better context understanding and family business pattern recognition

Based on validation showing missed executives in key sections and poor pattern matching.

Author: AI Assistant  
Date: 2025-01-23
Version: 1.0.0 - Phase 1 Implementation
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
import spacy
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from nltk.tree import Tree
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

@dataclass
class NameCandidate:
    """Enhanced name candidate with detailed extraction metadata"""
    first_name: str
    last_name: str
    full_name: str
    title: str = ""
    confidence: float = 0.0
    
    # Extraction metadata
    extraction_method: str = ""
    source_section: str = ""
    context_snippet: str = ""
    position_in_text: int = 0
    
    # Validation signals
    has_title_context: bool = False
    has_contact_context: bool = False
    appears_multiple_times: bool = False
    domain_email_match: bool = False
    
    # Quality indicators
    name_quality_score: float = 0.0
    context_quality_score: float = 0.0

class ExecutivePatternDatabase:
    """Comprehensive database of executive patterns for improved detection"""
    
    def __init__(self):
        # Expanded executive title patterns (critical for discovery improvement)
        self.executive_titles = {
            'primary_executive': [
                # Traditional titles
                'owner', 'co-owner', 'director', 'managing director', 'ceo', 'chief executive',
                'chief executive officer', 'founder', 'co-founder', 'proprietor', 'principal',
                'partner', 'president', 'vice president', 'chairman', 'chairwoman',
                
                # Industry leadership
                'head', 'lead', 'senior partner', 'executive director', 'general manager',
                'regional manager', 'area manager', 'branch manager', 'operations director',
                'technical director', 'sales director', 'business owner', 'company owner'
            ],
            
            'plumbing_specific': [
                # Plumbing industry specific titles
                'master plumber', 'senior plumber', 'lead plumber', 'principal plumber',
                'qualified plumber', 'certified plumber', 'licensed plumber',
                'gas safe engineer', 'heating engineer', 'plumbing engineer',
                'boiler engineer', 'bathroom specialist', 'installation manager',
                'plumbing contractor', 'heating contractor', 'gas engineer',
                'corgi registered', 'city & guilds qualified'
            ],
            
            'management_titles': [
                'manager', 'general manager', 'operations manager', 'business manager',
                'office manager', 'project manager', 'contracts manager', 'site manager',
                'service manager', 'customer service manager', 'admin manager',
                'facilities manager', 'maintenance manager'
            ],
            
            'family_business_indicators': [
                'son', 'daughter', 'jr', 'junior', 'sr', 'senior', 'iii', 'iv', 'v',
                'father', 'dad', 'grandfather', 'family', 'established by', 'founded by',
                'generations', 'family business', 'family owned', 'family run'
            ]
        }
        
        # Context patterns that indicate executive presence
        self.executive_context_patterns = [
            # Direct identification patterns
            r'\b(?:owner|director|manager|founder|ceo|principal)\s+(?:of\s+)?(?:the\s+)?company\b',
            r'\b(?:established|founded|started)\s+(?:in\s+\d{4}\s+)?by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
            r'\b(?:contact|speak\s+to|ask\s+for|reach)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+is\s+the|\s+has\s+been\s+the|\s+works\s+as)\s+(?:owner|director|manager)\b',
            r'\bwith\s+(?:over\s+)?\d+\s+years?\s+(?:of\s+)?experience[,\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
            
            # Quote attribution patterns (common in testimonials/about sections)
            r'"[^"]+"\s*[-–—]\s*([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s*,\s*(?:owner|director|manager))?',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*(?:says?|states?|explains?|comments?)',
            
            # Professional qualification patterns
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+is\s+)?(?:\s+a\s+)?(?:qualified|certified|licensed|gas\s+safe)\b',
            r'\b(?:qualified|certified|licensed)\s+(?:plumber|engineer)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
        ]
        
        # Section priority weights for extraction
        self.section_weights = {
            'about': 0.9,
            'team': 0.85,
            'leadership': 0.9,
            'management': 0.85,
            'directors': 0.9,
            'contact': 0.7,
            'footer': 0.6,
            'testimonials': 0.4,  # Lower weight due to customer quotes
            'services': 0.3,
            'home': 0.5
        }

class ContentSectionAnalyzer:
    """Analyzes different content sections for executive information"""
    
    def __init__(self):
        self.patterns = ExecutivePatternDatabase()
        
        # Section identification patterns
        self.section_identifiers = {
            'about': [
                'about us', 'about', 'our story', 'company history', 'who we are',
                'background', 'our company', 'company info', 'company information'
            ],
            'team': [
                'our team', 'meet the team', 'team', 'staff', 'our staff',
                'meet our team', 'team members', 'our people'
            ],
            'leadership': [
                'leadership', 'management', 'directors', 'executives',
                'leadership team', 'management team', 'our directors'
            ],
            'contact': [
                'contact', 'contact us', 'get in touch', 'reach us',
                'contact information', 'contact details'
            ]
        }
    
    def analyze_html_sections(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Analyze HTML content by sections to find executive information
        
        Returns:
            List of section analysis results with executive candidates
        """
        sections = []
        
        # Find specific sections by ID/Class
        sections.extend(self._find_structured_sections(soup))
        
        # Analyze navigation menus for section identification
        sections.extend(self._analyze_navigation_structure(soup))
        
        # Full content analysis as fallback
        sections.extend(self._analyze_full_content(soup))
        
        return sections
    
    def _find_structured_sections(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Find sections with explicit ID/class structure"""
        structured_sections = []
        
        # Common section selectors
        selectors = [
            # ID-based selectors
            '[id*="about"]', '[id*="team"]', '[id*="leadership"]', '[id*="management"]',
            '[id*="directors"]', '[id*="contact"]', '[id*="staff"]',
            
            # Class-based selectors  
            '[class*="about"]', '[class*="team"]', '[class*="leadership"]', '[class*="management"]',
            '[class*="directors"]', '[class*="contact"]', '[class*="staff"]',
            
            # Semantic HTML
            'section', 'article', 'aside', 'header', 'footer', 'main'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                section_type = self._identify_section_type(element)
                if section_type:
                    content = element.get_text(separator=' ', strip=True)
                    if len(content) > 50:  # Meaningful content
                        structured_sections.append({
                            'type': section_type,
                            'content': content,
                            'html': str(element)[:500],  # Truncated for memory
                            'weight': self.patterns.section_weights.get(section_type, 0.5),
                            'extraction_method': 'structured_html'
                        })
        
        return structured_sections
    
    def _identify_section_type(self, element: Tag) -> Optional[str]:
        """Identify section type from HTML element"""
        # Check ID and class attributes
        element_id = element.get('id', '').lower()
        element_class = ' '.join(element.get('class', [])).lower()
        element_text = element.get_text().lower()[:200]  # First 200 chars
        
        combined_attrs = f"{element_id} {element_class} {element_text}"
        
        for section_type, identifiers in self.section_identifiers.items():
            for identifier in identifiers:
                if identifier in combined_attrs:
                    return section_type
        
        return None
    
    def _analyze_navigation_structure(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Analyze navigation to understand site structure"""
        nav_sections = []
        
        # Find navigation elements
        nav_elements = soup.find_all(['nav', 'menu']) + soup.select('[class*="nav"]', '[id*="nav"]')
        
        for nav in nav_elements:
            links = nav.find_all('a')
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                
                # Check if link points to relevant sections
                for section_type, identifiers in self.section_identifiers.items():
                    if any(identifier in text or identifier in href.lower() for identifier in identifiers):
                        # Try to find the target section
                        target_section = self._find_target_section(soup, href, text)
                        if target_section:
                            nav_sections.append(target_section)
        
        return nav_sections
    
    def _find_target_section(self, soup: BeautifulSoup, href: str, link_text: str) -> Optional[Dict[str, Any]]:
        """Find target section based on navigation link"""
        # Try to find section by anchor
        if href.startswith('#'):
            target_id = href[1:]
            target_element = soup.find(id=target_id)
            if target_element:
                content = target_element.get_text(separator=' ', strip=True)
                if len(content) > 50:
                    section_type = self._identify_section_type(target_element) or 'unknown'
                    return {
                        'type': section_type,
                        'content': content,
                        'html': str(target_element)[:500],
                        'weight': self.patterns.section_weights.get(section_type, 0.5),
                        'extraction_method': 'navigation_linked'
                    }
        
        return None
    
    def _analyze_full_content(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Analyze full content when structured sections aren't found"""
        full_text = soup.get_text(separator='\n', strip=True)
        paragraphs = [p.strip() for p in full_text.split('\n') if len(p.strip()) > 30]
        
        content_sections = []
        
        for i, paragraph in enumerate(paragraphs):
            # Check for executive-related content
            paragraph_lower = paragraph.lower()
            
            # Look for executive indicators in paragraph
            has_executive_content = any(
                title in paragraph_lower 
                for title_list in self.patterns.executive_titles.values() 
                for title in title_list
            )
            
            if has_executive_content:
                # Determine section type based on context
                section_type = 'content_paragraph'
                weight = 0.4
                
                # Try to identify section based on surrounding content
                context_window = ' '.join(paragraphs[max(0, i-2):i+3]).lower()
                for section_type_candidate, identifiers in self.section_identifiers.items():
                    if any(identifier in context_window for identifier in identifiers):
                        section_type = section_type_candidate
                        weight = self.patterns.section_weights.get(section_type, 0.4)
                        break
                
                content_sections.append({
                    'type': section_type,
                    'content': paragraph,
                    'html': '',
                    'weight': weight,
                    'extraction_method': 'content_analysis'
                })
        
        return content_sections

class EnhancedNameExtractor:
    """Enhanced name extraction with improved pattern recognition and validation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.patterns = ExecutivePatternDatabase()
        self.section_analyzer = ContentSectionAnalyzer()
        
        # Initialize NLP tools
        self._initialize_nlp_tools()
        
        # Name validation patterns
        self.name_validation_patterns = {
            'valid_name_chars': re.compile(r'^[A-Za-z\s\'-\.]+$'),
            'first_name_pattern': re.compile(r'^[A-Z][a-z]{1,20}$'),
            'last_name_pattern': re.compile(r'^[A-Z][a-z\'-]{1,25}$'),
            'hyphenated_name': re.compile(r'^[A-Z][a-z]+-[A-Z][a-z]+$'),
            'business_name_indicators': re.compile(r'\b(?:ltd|limited|inc|incorporated|llc|plc|company|services|solutions|group|enterprises)\b', re.IGNORECASE)
        }
    
    def _initialize_nlp_tools(self):
        """Initialize NLP processing tools"""
        try:
            # Load spaCy English model
            self.nlp = spacy.load("en_core_web_sm")
            
            # Download NLTK data if not present
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt')
            
            try:
                nltk.data.find('taggers/averaged_perceptron_tagger')
            except LookupError:
                nltk.download('averaged_perceptron_tagger')
            
            try:
                nltk.data.find('chunkers/maxent_ne_chunker')
            except LookupError:
                nltk.download('maxent_ne_chunker')
            
            try:
                nltk.data.find('corpora/words')
            except LookupError:
                nltk.download('words')
                
        except Exception as e:
            self.logger.warning(f"NLP initialization warning: {e}")
            self.nlp = None
    
    def extract_enhanced_names(self, html_content: str, company_info: Dict[str, Any]) -> List[NameCandidate]:
        """
        Extract executive names using enhanced pattern recognition and section analysis
        
        Args:
            html_content: HTML content to analyze
            company_info: Company information for context
            
        Returns:
            List of validated name candidates with confidence scores
        """
        self.logger.info("Starting enhanced name extraction")
        
        try:
            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Phase 1: Section-based analysis
            sections = self.section_analyzer.analyze_html_sections(soup)
            self.logger.info(f"Found {len(sections)} content sections for analysis")
            
            # Phase 2: Multi-method name extraction
            all_candidates = []
            
            # Method 1: Pattern-based extraction from sections
            for section in sections:
                section_candidates = self._extract_from_section(section, company_info)
                all_candidates.extend(section_candidates)
            
            # Method 2: NLP-based extraction
            if self.nlp:
                nlp_candidates = self._extract_with_spacy(html_content, company_info)
                all_candidates.extend(nlp_candidates)
            
            # Method 3: NLTK-based extraction (fallback)
            nltk_candidates = self._extract_with_nltk(html_content, company_info)
            all_candidates.extend(nltk_candidates)
            
            # Method 4: Regex pattern extraction
            regex_candidates = self._extract_with_regex_patterns(html_content, company_info)
            all_candidates.extend(regex_candidates)
            
            # Phase 3: Validation and deduplication
            validated_candidates = self._validate_and_deduplicate(all_candidates, company_info)
            
            self.logger.info(f"Enhanced extraction complete: {len(validated_candidates)} validated candidates")
            return validated_candidates
            
        except Exception as e:
            self.logger.error(f"Error in enhanced name extraction: {e}")
            return []
    
    def _extract_from_section(self, section: Dict[str, Any], company_info: Dict[str, Any]) -> List[NameCandidate]:
        """Extract names from a specific content section"""
        candidates = []
        content = section['content']
        section_type = section['type']
        weight = section.get('weight', 0.5)
        
        # Use executive context patterns
        for pattern in self.patterns.executive_context_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Extract name from pattern groups
                name_groups = [group for group in match.groups() if group and len(group.strip()) > 3]
                for name_group in name_groups:
                    candidate = self._create_name_candidate(
                        name_group.strip(),
                        extraction_method=f"pattern_match_{section_type}",
                        source_section=section_type,
                        context_snippet=content[max(0, match.start()-50):match.end()+50],
                        base_confidence=weight * 0.8
                    )
                    if candidate:
                        candidates.append(candidate)
        
        # Look for title-adjacent names
        title_adjacent_candidates = self._find_title_adjacent_names(content, section_type, weight)
        candidates.extend(title_adjacent_candidates)
        
        return candidates
    
    def _find_title_adjacent_names(self, content: str, section_type: str, weight: float) -> List[NameCandidate]:
        """Find names that appear adjacent to executive titles"""
        candidates = []
        
        # Create comprehensive title pattern
        all_titles = []
        for title_list in self.patterns.executive_titles.values():
            all_titles.extend(title_list)
        
        title_pattern = '|'.join(re.escape(title) for title in all_titles)
        
        # Pattern: Name followed by title
        name_title_pattern = rf'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s*[,-]?\s*(?:{title_pattern})\b'
        matches = re.finditer(name_title_pattern, content, re.IGNORECASE)
        
        for match in matches:
            name = match.group(1).strip()
            matched_title = match.group(0).replace(name, '').strip(' ,-')
            
            candidate = self._create_name_candidate(
                name,
                title=matched_title,
                extraction_method=f"title_adjacent_{section_type}",
                source_section=section_type,
                context_snippet=content[max(0, match.start()-30):match.end()+30],
                base_confidence=weight * 0.9  # High confidence for title-adjacent
            )
            if candidate:
                candidate.has_title_context = True
                candidates.append(candidate)
        
        # Pattern: Title followed by name
        title_name_pattern = rf'\b(?:{title_pattern})\s*[:-]?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
        matches = re.finditer(title_name_pattern, content, re.IGNORECASE)
        
        for match in matches:
            name = match.group(1).strip()
            matched_title = match.group(0).replace(name, '').strip(' :-')
            
            candidate = self._create_name_candidate(
                name,
                title=matched_title,
                extraction_method=f"title_preceded_{section_type}",
                source_section=section_type,
                context_snippet=content[max(0, match.start()-30):match.end()+30],
                base_confidence=weight * 0.9
            )
            if candidate:
                candidate.has_title_context = True
                candidates.append(candidate)
        
        return candidates
    
    def _extract_with_spacy(self, content: str, company_info: Dict[str, Any]) -> List[NameCandidate]:
        """Extract names using spaCy NER"""
        if not self.nlp:
            return []
        
        candidates = []
        
        # Clean content for processing
        text_content = BeautifulSoup(content, 'html.parser').get_text(separator=' ', strip=True)
        
        # Process with spaCy
        doc = self.nlp(text_content[:1000000])  # Limit text size
        
        for ent in doc.ents:
            if ent.label_ == "PERSON" and len(ent.text.split()) >= 2:
                # Validate name format
                if self._is_valid_person_name(ent.text):
                    candidate = self._create_name_candidate(
                        ent.text,
                        extraction_method="spacy_ner",
                        source_section="full_content",
                        context_snippet=str(ent.sent)[:100],
                        base_confidence=0.7
                    )
                    if candidate:
                        candidates.append(candidate)
        
        return candidates
    
    def _extract_with_nltk(self, content: str, company_info: Dict[str, Any]) -> List[NameCandidate]:
        """Extract names using NLTK NER"""
        candidates = []
        
        try:
            # Clean content
            text_content = BeautifulSoup(content, 'html.parser').get_text(separator=' ', strip=True)
            
            # Tokenize sentences
            sentences = sent_tokenize(text_content[:500000])  # Limit for performance
            
            for sentence in sentences[:100]:  # Limit sentences
                # Tokenize words
                words = word_tokenize(sentence)
                
                # POS tagging
                pos_tags = pos_tag(words)
                
                # Named entity chunking
                ne_tree = ne_chunk(pos_tags)
                
                # Extract person names
                for chunk in ne_tree:
                    if isinstance(chunk, Tree) and chunk.label() == 'PERSON':
                        name_words = [word for word, pos in chunk.leaves()]
                        full_name = ' '.join(name_words)
                        
                        if len(name_words) >= 2 and self._is_valid_person_name(full_name):
                            candidate = self._create_name_candidate(
                                full_name,
                                extraction_method="nltk_ner",
                                source_section="full_content",
                                context_snippet=sentence[:100],
                                base_confidence=0.6
                            )
                            if candidate:
                                candidates.append(candidate)
            
        except Exception as e:
            self.logger.warning(f"NLTK extraction error: {e}")
        
        return candidates
    
    def _extract_with_regex_patterns(self, content: str, company_info: Dict[str, Any]) -> List[NameCandidate]:
        """Extract names using regex patterns"""
        candidates = []
        text_content = BeautifulSoup(content, 'html.parser').get_text(separator=' ', strip=True)
        
        # Basic name patterns
        name_patterns = [
            r'\b([A-Z][a-z]{2,15})\s+([A-Z][a-z]{2,20})\b',  # First Last
            r'\b([A-Z][a-z]+)\s+([A-Z]\.\s+)?([A-Z][a-z]+)\b',  # First M. Last
            r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+-[A-Z][a-z]+)\b'  # Hyphenated surnames
        ]
        
        for pattern in name_patterns:
            matches = re.finditer(pattern, text_content)
            for match in matches:
                groups = match.groups()
                # Construct full name from groups
                name_parts = [part for part in groups if part and part.strip()]
                full_name = ' '.join(name_parts).replace('  ', ' ')
                
                if self._is_valid_person_name(full_name):
                    candidate = self._create_name_candidate(
                        full_name,
                        extraction_method="regex_pattern",
                        source_section="full_content",
                        context_snippet=text_content[max(0, match.start()-50):match.end()+50],
                        base_confidence=0.5
                    )
                    if candidate:
                        candidates.append(candidate)
        
        return candidates
    
    def _create_name_candidate(self, name: str, title: str = "", extraction_method: str = "",
                             source_section: str = "", context_snippet: str = "",
                             base_confidence: float = 0.5) -> Optional[NameCandidate]:
        """Create and validate a name candidate"""
        
        # Basic validation
        if not self._is_valid_person_name(name):
            return None
        
        # Parse name parts
        name_parts = name.strip().split()
        if len(name_parts) < 2:
            return None
        
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:])
        
        # Calculate confidence score
        confidence = self._calculate_name_confidence(first_name, last_name, context_snippet, base_confidence)
        
        # Calculate quality scores
        name_quality = self._assess_name_quality(first_name, last_name)
        context_quality = self._assess_context_quality(context_snippet)
        
        candidate = NameCandidate(
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}",
            title=title,
            confidence=confidence,
            extraction_method=extraction_method,
            source_section=source_section,
            context_snippet=context_snippet,
            has_title_context=bool(title),
            name_quality_score=name_quality,
            context_quality_score=context_quality
        )
        
        return candidate
    
    def _is_valid_person_name(self, name: str) -> bool:
        """Validate if a name appears to be a real person name"""
        if not name or len(name.strip()) < 3:
            return False
        
        # Check for valid characters
        if not self.name_validation_patterns['valid_name_chars'].match(name):
            return False
        
        # Check for business name indicators
        if self.name_validation_patterns['business_name_indicators'].search(name):
            return False
        
        # Check name parts
        name_parts = name.strip().split()
        if len(name_parts) < 2 or len(name_parts) > 4:
            return False
        
        # Validate first and last name patterns
        first_name = name_parts[0]
        last_name = name_parts[-1]
        
        # Basic format validation
        if not (first_name[0].isupper() and last_name[0].isupper()):
            return False
        
        # Length validation
        if len(first_name) < 2 or len(last_name) < 2:
            return False
        
        if len(first_name) > 20 or len(last_name) > 25:
            return False
        
        return True
    
    def _calculate_name_confidence(self, first_name: str, last_name: str, 
                                 context: str, base_confidence: float) -> float:
        """Calculate confidence score for extracted name"""
        confidence = base_confidence
        
        # Name quality factors
        if len(first_name) >= 3 and len(last_name) >= 3:
            confidence += 0.1
        
        # Context quality factors
        context_lower = context.lower()
        
        # Positive indicators
        positive_indicators = ['director', 'owner', 'manager', 'founder', 'ceo', 'established', 'contact']
        for indicator in positive_indicators:
            if indicator in context_lower:
                confidence += 0.1
                break
        
        # Negative indicators
        negative_indicators = ['customer', 'client', 'review', 'said', 'commented']
        for indicator in negative_indicators:
            if indicator in context_lower:
                confidence -= 0.2
                break
        
        return max(0.0, min(1.0, confidence))
    
    def _assess_name_quality(self, first_name: str, last_name: str) -> float:
        """Assess the quality/authenticity of a name"""
        score = 0.5
        
        # Length appropriateness
        if 3 <= len(first_name) <= 12 and 3 <= len(last_name) <= 15:
            score += 0.2
        
        # Character patterns
        if first_name.isalpha() and last_name.replace('-', '').replace("'", '').isalpha():
            score += 0.2
        
        # Common name patterns
        if self.name_validation_patterns['first_name_pattern'].match(first_name):
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_context_quality(self, context: str) -> float:
        """Assess the quality of extraction context"""
        if not context:
            return 0.3
        
        score = 0.5
        context_lower = context.lower()
        
        # Executive context indicators
        executive_words = ['owner', 'director', 'manager', 'founder', 'ceo', 'established', 'experience']
        executive_count = sum(1 for word in executive_words if word in context_lower)
        score += min(0.3, executive_count * 0.1)
        
        # Negative context indicators
        negative_words = ['customer', 'client', 'review', 'testimonial']
        negative_count = sum(1 for word in negative_words if word in context_lower)
        score -= min(0.4, negative_count * 0.2)
        
        return max(0.0, min(1.0, score))
    
    def _validate_and_deduplicate(self, candidates: List[NameCandidate], 
                                company_info: Dict[str, Any]) -> List[NameCandidate]:
        """Validate and deduplicate name candidates"""
        
        # Group similar names
        name_groups = {}
        for candidate in candidates:
            name_key = self._normalize_name_for_grouping(candidate.full_name)
            if name_key not in name_groups:
                name_groups[name_key] = []
            name_groups[name_key].append(candidate)
        
        # Select best candidate from each group
        validated_candidates = []
        for name_key, group in name_groups.items():
            if len(group) == 1:
                # Single candidate
                if group[0].confidence >= 0.3:  # Minimum threshold
                    validated_candidates.append(group[0])
            else:
                # Multiple candidates - select best
                best_candidate = max(group, key=lambda x: (
                    x.confidence * 0.4 + 
                    x.name_quality_score * 0.3 + 
                    x.context_quality_score * 0.3
                ))
                
                # Mark as appearing multiple times
                best_candidate.appears_multiple_times = True
                best_candidate.confidence = min(1.0, best_candidate.confidence + 0.1)
                
                if best_candidate.confidence >= 0.3:
                    validated_candidates.append(best_candidate)
        
        # Sort by confidence
        validated_candidates.sort(key=lambda x: x.confidence, reverse=True)
        
        # Limit to reasonable number per company
        max_candidates = 10
        if len(validated_candidates) > max_candidates:
            validated_candidates = validated_candidates[:max_candidates]
        
        return validated_candidates
    
    def _normalize_name_for_grouping(self, name: str) -> str:
        """Normalize name for grouping similar names"""
        # Remove extra spaces, convert to lowercase
        normalized = ' '.join(name.lower().split())
        
        # Remove common prefixes/suffixes
        prefixes_suffixes = ['mr', 'mrs', 'ms', 'dr', 'jr', 'sr', 'iii', 'iv']
        words = normalized.split()
        filtered_words = [word for word in words if word not in prefixes_suffixes]
        
        return ' '.join(filtered_words) 