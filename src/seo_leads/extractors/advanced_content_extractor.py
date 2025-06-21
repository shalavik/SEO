"""
Advanced Content Extractor for Executive Discovery
Phase 4A: Enhanced Content Extraction System
Target: Improve success rate from 40% to 70%+
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from bs4 import BeautifulSoup, Tag
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from nltk.corpus import stopwords
import spacy
from spacy import displacy
import requests
import time

logger = logging.getLogger(__name__)

@dataclass
class ExtractedExecutive:
    """Enhanced executive information with extraction metadata"""
    first_name: str
    last_name: str
    title: str = ""
    email: str = ""
    phone: str = ""
    context: str = ""
    extraction_method: str = ""
    confidence_score: float = 0.0
    source_section: str = ""
    page_url: str = ""
    validation_signals: List[str] = field(default_factory=list)

@dataclass
class ExtractionContext:
    """Context information for extraction process"""
    company_name: str
    industry: str = "plumbing"
    region: str = "uk"
    website_structure: Dict[str, Any] = field(default_factory=dict)
    content_quality: float = 0.0
    extraction_timestamp: float = 0.0

class PlumbingIndustryPatterns:
    """Industry-specific patterns for plumbing businesses"""
    
    # Executive titles common in plumbing industry
    EXECUTIVE_TITLES = {
        'high_priority': [
            'owner', 'director', 'managing director', 'ceo', 'chief executive',
            'founder', 'proprietor', 'principal', 'partner', 'boss'
        ],
        'medium_priority': [
            'manager', 'general manager', 'operations manager', 'business manager',
            'office manager', 'senior plumber', 'master plumber', 'lead plumber'
        ],
        'professional': [
            'gas safe engineer', 'heating engineer', 'plumbing engineer',
            'qualified plumber', 'certified plumber', 'licensed plumber'
        ]
    }
    
    # Common business structures in UK plumbing
    BUSINESS_PATTERNS = [
        r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\s+Plumbing\b',
        r'\b([A-Z][a-z]+)\s+Plumbing\s+Services\b',
        r'\b([A-Z][a-z]+)\s+&\s+([A-Z][a-z]+)\s+Plumbing\b',
        r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\s+Gas\s+&\s+Plumbing\b'
    ]
    
    # UK naming patterns
    UK_NAME_PATTERNS = [
        r'\b([A-Z][a-z]{2,15})\s+([A-Z][a-z]{2,15})\b',  # Standard First Last
        r'\b([A-Z][a-z]+)\s+([A-Z]\.\s+)?([A-Z][a-z]+)\b',  # First M. Last
        r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+[-][A-Z][a-z]+)\b'  # Hyphenated surnames
    ]
    
    # Contact context indicators
    CONTACT_INDICATORS = [
        'contact', 'reach', 'call', 'email', 'speak to', 'ask for',
        'director', 'owner', 'manager', 'in charge', 'responsible'
    ]

class AdvancedHTMLParser:
    """Advanced HTML parsing with multiple extraction strategies"""
    
    def __init__(self):
        self.patterns = PlumbingIndustryPatterns()
        
    def extract_executive_sections(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
        """Extract sections likely to contain executive information"""
        executive_sections = []
        
        # Strategy 1: Look for dedicated team/about sections
        team_sections = self._find_team_sections(soup)
        executive_sections.extend(team_sections)
        
        # Strategy 2: Look for contact sections with names
        contact_sections = self._find_contact_sections(soup)
        executive_sections.extend(contact_sections)
        
        # Strategy 3: Look for about/story sections
        about_sections = self._find_about_sections(soup)
        executive_sections.extend(about_sections)
        
        # Strategy 4: Scan entire page for executive patterns
        full_page_sections = self._scan_full_page(soup)
        executive_sections.extend(full_page_sections)
        
        logger.info(f"Found {len(executive_sections)} potential executive sections")
        return executive_sections
    
    def _find_team_sections(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Find team/staff sections"""
        team_selectors = [
            'section[id*="team"]', 'div[id*="team"]', 'section[class*="team"]',
            'div[class*="team"]', 'section[id*="staff"]', 'div[id*="staff"]',
            'section[class*="staff"]', 'div[class*="staff"]', 'section[id*="about"]',
            'div[id*="about"]', 'section[class*="about"]', 'div[class*="about"]'
        ]
        
        sections = []
        for selector in team_selectors:
            elements = soup.select(selector)
            for element in elements:
                sections.append({
                    'type': 'team_section',
                    'content': element.get_text(strip=True),
                    'html': str(element),
                    'confidence': 0.8,
                    'selector': selector
                })
        
        return sections
    
    def _find_contact_sections(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Find contact sections with potential executive information"""
        contact_selectors = [
            'section[id*="contact"]', 'div[id*="contact"]', 
            'section[class*="contact"]', 'div[class*="contact"]',
            'footer', 'address', 'div[class*="footer"]'
        ]
        
        sections = []
        for selector in contact_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if any(indicator in text.lower() for indicator in self.patterns.CONTACT_INDICATORS):
                    sections.append({
                        'type': 'contact_section',
                        'content': text,
                        'html': str(element),
                        'confidence': 0.6,
                        'selector': selector
                    })
        
        return sections
    
    def _find_about_sections(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Find about/story sections"""
        about_selectors = [
            'section[id*="about"]', 'div[id*="about"]',
            'section[class*="about"]', 'div[class*="about"]',
            'section[id*="story"]', 'div[id*="story"]',
            'section[class*="story"]', 'div[class*="story"]'
        ]
        
        sections = []
        for selector in about_selectors:
            elements = soup.select(selector)
            for element in elements:
                sections.append({
                    'type': 'about_section',
                    'content': element.get_text(strip=True),
                    'html': str(element),
                    'confidence': 0.5,
                    'selector': selector
                })
        
        return sections
    
    def _scan_full_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Scan entire page for executive patterns"""
        # Get all text content
        full_text = soup.get_text(separator=' ', strip=True)
        
        # Split into paragraphs
        paragraphs = full_text.split('\n')
        
        sections = []
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph.strip()) > 20:  # Meaningful content
                # Check for executive indicators
                has_title = any(title in paragraph.lower() for title_list in self.patterns.EXECUTIVE_TITLES.values() for title in title_list)
                has_name_pattern = any(re.search(pattern, paragraph) for pattern in self.patterns.UK_NAME_PATTERNS)
                
                if has_title or has_name_pattern:
                    sections.append({
                        'type': 'full_page_scan',
                        'content': paragraph.strip(),
                        'html': paragraph.strip(),
                        'confidence': 0.4,
                        'selector': f'paragraph_{i}'
                    })
        
        return sections

class MLExecutiveClassifier:
    """ML-based executive name recognition and classification"""
    
    def __init__(self):
        self.nlp = None
        self.patterns = PlumbingIndustryPatterns()
        self._initialize_nlp()
    
    def _initialize_nlp(self):
        """Initialize NLP models"""
        try:
            # Try to load spaCy English model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
        except OSError:
            logger.warning("spaCy model not found, using NLTK fallback")
            # Download required NLTK data
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)
                nltk.download('maxent_ne_chunker', quiet=True)
                nltk.download('words', quiet=True)
                nltk.download('stopwords', quiet=True)
            except Exception as e:
                logger.error(f"NLTK download failed: {e}")
    
    def extract_person_names(self, text: str) -> List[Tuple[str, str, float]]:
        """Extract person names with confidence scores"""
        if self.nlp:
            return self._extract_with_spacy(text)
        else:
            return self._extract_with_nltk(text)
    
    def _extract_with_spacy(self, text: str) -> List[Tuple[str, str, float]]:
        """Extract names using spaCy NER"""
        doc = self.nlp(text)
        names = []
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name_parts = ent.text.strip().split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = ' '.join(name_parts[1:])
                    confidence = self._calculate_name_confidence(first_name, last_name, text)
                    names.append((first_name, last_name, confidence))
        
        return names
    
    def _extract_with_nltk(self, text: str) -> List[Tuple[str, str, float]]:
        """Extract names using NLTK NER"""
        try:
            sentences = sent_tokenize(text)
            names = []
            
            for sentence in sentences:
                tokens = word_tokenize(sentence)
                pos_tags = pos_tag(tokens)
                chunks = ne_chunk(pos_tags, binary=False)
                
                for chunk in chunks:
                    if hasattr(chunk, 'label') and chunk.label() == 'PERSON':
                        name_tokens = [token for token, pos in chunk.leaves()]
                        if len(name_tokens) >= 2:
                            first_name = name_tokens[0]
                            last_name = ' '.join(name_tokens[1:])
                            confidence = self._calculate_name_confidence(first_name, last_name, text)
                            names.append((first_name, last_name, confidence))
            
            return names
        except Exception as e:
            logger.error(f"NLTK extraction failed: {e}")
            return []
    
    def _calculate_name_confidence(self, first_name: str, last_name: str, context: str) -> float:
        """Calculate confidence score for extracted name"""
        confidence = 0.5  # Base confidence
        
        # Check if it's a real person name vs business name
        if self._is_business_name(first_name, last_name):
            confidence -= 0.3
        
        # Check for executive title context
        title_context = self._find_title_context(first_name, last_name, context)
        if title_context:
            confidence += 0.2
        
        # Check for contact context
        contact_context = self._find_contact_context(first_name, last_name, context)
        if contact_context:
            confidence += 0.1
        
        # Check UK name patterns
        if self._matches_uk_patterns(first_name, last_name):
            confidence += 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _is_business_name(self, first_name: str, last_name: str) -> bool:
        """Check if extracted name is actually a business name"""
        business_indicators = [
            'ltd', 'limited', 'plumbing', 'services', 'heating', 'gas',
            'emergency', 'qualified', 'certified', 'professional'
        ]
        
        full_name = f"{first_name} {last_name}".lower()
        return any(indicator in full_name for indicator in business_indicators)
    
    def _find_title_context(self, first_name: str, last_name: str, context: str) -> Optional[str]:
        """Find executive title in context"""
        full_name = f"{first_name} {last_name}"
        
        # Look for title patterns around the name
        name_index = context.lower().find(full_name.lower())
        if name_index == -1:
            return None
        
        # Check text around the name (±50 characters)
        start = max(0, name_index - 50)
        end = min(len(context), name_index + len(full_name) + 50)
        surrounding_text = context[start:end].lower()
        
        for title_list in self.patterns.EXECUTIVE_TITLES.values():
            for title in title_list:
                if title in surrounding_text:
                    return title
        
        return None
    
    def _find_contact_context(self, first_name: str, last_name: str, context: str) -> bool:
        """Check if name appears in contact context"""
        full_name = f"{first_name} {last_name}"
        name_index = context.lower().find(full_name.lower())
        
        if name_index == -1:
            return False
        
        # Check surrounding text for contact indicators
        start = max(0, name_index - 100)
        end = min(len(context), name_index + len(full_name) + 100)
        surrounding_text = context[start:end].lower()
        
        return any(indicator in surrounding_text for indicator in self.patterns.CONTACT_INDICATORS)
    
    def _matches_uk_patterns(self, first_name: str, last_name: str) -> bool:
        """Check if name matches UK naming patterns"""
        full_name = f"{first_name} {last_name}"
        return any(re.match(pattern, full_name) for pattern in self.patterns.UK_NAME_PATTERNS)

class IndustrySpecificExtractor:
    """Industry-specific extraction patterns for plumbing businesses"""
    
    def __init__(self):
        self.patterns = PlumbingIndustryPatterns()
        self.ml_classifier = MLExecutiveClassifier()
    
    def extract_plumbing_executives(self, content: str, context: ExtractionContext) -> List[ExtractedExecutive]:
        """Extract executives using plumbing industry-specific patterns"""
        executives = []
        
        # Method 1: ML-based person name extraction
        ml_names = self.ml_classifier.extract_person_names(content)
        for first_name, last_name, confidence in ml_names:
            title = self._extract_executive_title(first_name, last_name, content)
            email = self._extract_email_for_person(first_name, last_name, content)
            phone = self._extract_phone_for_person(first_name, last_name, content)
            
            executive = ExtractedExecutive(
                first_name=first_name,
                last_name=last_name,
                title=title,
                email=email,
                phone=phone,
                context=self._get_name_context(first_name, last_name, content),
                extraction_method="ml_ner",
                confidence_score=confidence,
                validation_signals=self._get_validation_signals(first_name, last_name, content)
            )
            executives.append(executive)
        
        # Method 2: Pattern-based extraction for plumbing-specific roles
        pattern_executives = self._extract_by_patterns(content, context)
        executives.extend(pattern_executives)
        
        # Method 3: Business structure analysis
        structure_executives = self._extract_from_business_structure(content, context)
        executives.extend(structure_executives)
        
        return self._deduplicate_and_rank(executives)
    
    def _extract_executive_title(self, first_name: str, last_name: str, content: str) -> str:
        """Extract executive title for a person"""
        full_name = f"{first_name} {last_name}"
        name_index = content.lower().find(full_name.lower())
        
        if name_index == -1:
            return ""
        
        # Look for title patterns around the name
        start = max(0, name_index - 100)
        end = min(len(content), name_index + len(full_name) + 100)
        surrounding_text = content[start:end]
        
        # Check for title patterns
        title_patterns = [
            rf'{re.escape(full_name)},?\s+([^.]+?)(?:\.|$)',
            rf'([^.]+?)\s+{re.escape(full_name)}',
            rf'{re.escape(full_name)}\s+-\s+([^.]+?)(?:\.|$)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, surrounding_text, re.IGNORECASE)
            if match:
                potential_title = match.group(1).strip()
                if self._is_valid_title(potential_title):
                    return potential_title
        
        return ""
    
    def _is_valid_title(self, title: str) -> bool:
        """Check if extracted title is valid"""
        title_lower = title.lower()
        
        # Check against known executive titles
        for title_list in self.patterns.EXECUTIVE_TITLES.values():
            if any(exec_title in title_lower for exec_title in title_list):
                return True
        
        # Check for general professional titles
        professional_indicators = ['manager', 'director', 'owner', 'engineer', 'specialist']
        return any(indicator in title_lower for indicator in professional_indicators)
    
    def _extract_email_for_person(self, first_name: str, last_name: str, content: str) -> str:
        """Extract email address for a specific person"""
        # Look for email patterns near the person's name
        full_name = f"{first_name} {last_name}"
        name_index = content.lower().find(full_name.lower())
        
        if name_index == -1:
            return ""
        
        # Search around the name for email patterns
        start = max(0, name_index - 200)
        end = min(len(content), name_index + len(full_name) + 200)
        surrounding_text = content[start:end]
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, surrounding_text)
        
        if emails:
            return emails[0]
        
        return ""
    
    def _extract_phone_for_person(self, first_name: str, last_name: str, content: str) -> str:
        """Extract phone number for a specific person"""
        # Look for UK phone patterns near the person's name
        full_name = f"{first_name} {last_name}"
        name_index = content.lower().find(full_name.lower())
        
        if name_index == -1:
            return ""
        
        # Search around the name for phone patterns
        start = max(0, name_index - 200)
        end = min(len(content), name_index + len(full_name) + 200)
        surrounding_text = content[start:end]
        
        # UK phone patterns
        phone_patterns = [
            r'\b(?:0|\+44)\s?(?:1|2|7|8)\d{8,9}\b',
            r'\b\d{11}\b',
            r'\b\d{5}\s?\d{6}\b'
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, surrounding_text)
            if phones:
                return phones[0]
        
        return ""
    
    def _get_name_context(self, first_name: str, last_name: str, content: str) -> str:
        """Get context around the person's name"""
        full_name = f"{first_name} {last_name}"
        name_index = content.lower().find(full_name.lower())
        
        if name_index == -1:
            return ""
        
        start = max(0, name_index - 100)
        end = min(len(content), name_index + len(full_name) + 100)
        return content[start:end].strip()
    
    def _get_validation_signals(self, first_name: str, last_name: str, content: str) -> List[str]:
        """Get validation signals for the extracted name"""
        signals = []
        context = self._get_name_context(first_name, last_name, content)
        
        # Check for various validation signals
        if any(title in context.lower() for title_list in self.patterns.EXECUTIVE_TITLES.values() for title in title_list):
            signals.append("executive_title")
        
        if any(indicator in context.lower() for indicator in self.patterns.CONTACT_INDICATORS):
            signals.append("contact_context")
        
        if '@' in context:
            signals.append("email_present")
        
        if re.search(r'\b\d{10,11}\b', context):
            signals.append("phone_present")
        
        return signals
    
    def _extract_by_patterns(self, content: str, context: ExtractionContext) -> List[ExtractedExecutive]:
        """Extract executives using pattern matching"""
        executives = []
        
        # Pattern for "Name - Title" format
        name_title_pattern = r'([A-Z][a-z]+)\s+([A-Z][a-z]+)\s*[-–]\s*([^.\n]+)'
        matches = re.findall(name_title_pattern, content)
        
        for first_name, last_name, title in matches:
            if self._is_valid_title(title):
                executive = ExtractedExecutive(
                    first_name=first_name,
                    last_name=last_name,
                    title=title.strip(),
                    extraction_method="pattern_matching",
                    confidence_score=0.7,
                    context=f"{first_name} {last_name} - {title}"
                )
                executives.append(executive)
        
        return executives
    
    def _extract_from_business_structure(self, content: str, context: ExtractionContext) -> List[ExtractedExecutive]:
        """Extract executives from business structure patterns"""
        executives = []
        
        # Look for family business patterns common in plumbing
        for pattern in self.patterns.BUSINESS_PATTERNS:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    for name in match:
                        if name and len(name) > 2:
                            executive = ExtractedExecutive(
                                first_name=name,
                                last_name="",  # Will be enhanced later
                                title="Business Owner",
                                extraction_method="business_structure",
                                confidence_score=0.6,
                                context=f"Business pattern: {pattern}"
                            )
                            executives.append(executive)
        
        return executives
    
    def _deduplicate_and_rank(self, executives: List[ExtractedExecutive]) -> List[ExtractedExecutive]:
        """Remove duplicates and rank by confidence"""
        # Deduplicate by name similarity
        unique_executives = []
        seen_names = set()
        
        for executive in executives:
            name_key = f"{executive.first_name.lower()}_{executive.last_name.lower()}"
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_executives.append(executive)
        
        # Sort by confidence score
        unique_executives.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return unique_executives

class AdvancedContentExtractor:
    """Main advanced content extraction coordinator"""
    
    def __init__(self):
        self.html_parser = AdvancedHTMLParser()
        self.industry_extractor = IndustrySpecificExtractor()
        
    def extract_executives_advanced(self, html_content: str, url: str, company_name: str) -> List[ExtractedExecutive]:
        """Main method for advanced executive extraction"""
        logger.info(f"🚀 Starting advanced content extraction for {company_name}")
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Create extraction context
        context = ExtractionContext(
            company_name=company_name,
            industry="plumbing",
            region="uk",
            extraction_timestamp=time.time()
        )
        
        # Extract executive sections
        sections = self.html_parser.extract_executive_sections(soup, url)
        
        all_executives = []
        
        # Process each section
        for section in sections:
            section_executives = self.industry_extractor.extract_plumbing_executives(
                section['content'], context
            )
            
            # Add section metadata
            for executive in section_executives:
                executive.source_section = section['type']
                executive.page_url = url
                # Boost confidence based on section type
                if section['type'] == 'team_section':
                    executive.confidence_score = min(1.0, executive.confidence_score + 0.1)
                elif section['type'] == 'contact_section':
                    executive.confidence_score = min(1.0, executive.confidence_score + 0.05)
            
            all_executives.extend(section_executives)
        
        # Final deduplication and ranking
        final_executives = self._final_processing(all_executives, context)
        
        logger.info(f"✅ Advanced extraction complete: {len(final_executives)} executives found")
        return final_executives
    
    def _final_processing(self, executives: List[ExtractedExecutive], context: ExtractionContext) -> List[ExtractedExecutive]:
        """Final processing and quality assurance"""
        # Remove obvious business names
        filtered_executives = []
        for executive in executives:
            if not self._is_obvious_business_name(executive):
                filtered_executives.append(executive)
        
        # Enhanced confidence scoring
        for executive in filtered_executives:
            executive.confidence_score = self._calculate_final_confidence(executive, context)
        
        # Sort by confidence and limit results
        filtered_executives.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Return top 15 results to maintain quality
        return filtered_executives[:15]
    
    def _is_obvious_business_name(self, executive: ExtractedExecutive) -> bool:
        """Filter out obvious business names"""
        full_name = f"{executive.first_name} {executive.last_name}".lower()
        
        business_keywords = [
            'plumbing', 'heating', 'gas', 'services', 'emergency', 'ltd', 'limited',
            'qualified', 'certified', 'professional', 'company', 'business'
        ]
        
        return any(keyword in full_name for keyword in business_keywords)
    
    def _calculate_final_confidence(self, executive: ExtractedExecutive, context: ExtractionContext) -> float:
        """Calculate final confidence score"""
        base_confidence = executive.confidence_score
        
        # Boost for validation signals
        signal_boost = len(executive.validation_signals) * 0.05
        
        # Boost for complete information
        completeness_boost = 0
        if executive.email:
            completeness_boost += 0.1
        if executive.phone:
            completeness_boost += 0.05
        if executive.title:
            completeness_boost += 0.05
        
        # Boost for extraction method
        method_boost = 0
        if executive.extraction_method == "ml_ner":
            method_boost = 0.1
        elif executive.extraction_method == "pattern_matching":
            method_boost = 0.05
        
        final_confidence = base_confidence + signal_boost + completeness_boost + method_boost
        return min(1.0, max(0.0, final_confidence)) 