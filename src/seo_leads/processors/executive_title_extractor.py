"""
Executive Title Extractor - Context-Based Title Recognition
Uses sophisticated pattern matching and context analysis to extract meaningful executive titles
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class TitleMatch:
    """Represents an extracted title with context and confidence"""
    title: str
    confidence: float
    extraction_method: str
    context: str
    position: int

class ExecutiveTitleExtractor:
    """
    Advanced executive title extraction using context analysis and UK business patterns.
    Replaces generic "Unknown" titles with meaningful extracted titles.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # UK Executive titles organized by seniority
        self.executive_titles = {
            'senior_executive': [
                'chief executive officer', 'ceo', 'managing director', 'md',
                'executive director', 'founder', 'owner', 'proprietor',
                'chairman', 'chairwoman', 'president', 'vice president'
            ],
            'senior_management': [
                'director', 'head of', 'general manager', 'operations manager',
                'business manager', 'senior manager', 'area manager',
                'regional manager', 'branch manager', 'department head'
            ],
            'middle_management': [
                'manager', 'supervisor', 'team leader', 'coordinator',
                'administrator', 'assistant manager', 'deputy manager',
                'office manager', 'project manager', 'contract manager'
            ],
            'technical_leadership': [
                'chief engineer', 'head engineer', 'senior engineer',
                'lead engineer', 'principal engineer', 'consulting engineer',
                'project engineer', 'site engineer', 'design engineer'
            ],
            'specialist_roles': [
                'consultant', 'specialist', 'advisor', 'expert',
                'technician', 'surveyor', 'inspector', 'estimator'
            ]
        }
        
        # Title patterns with context requirements
        self.title_patterns = [
            # Direct title patterns
            re.compile(r'(?:^|\s)([A-Z][a-z]+\s+(?:Director|Manager|Engineer|Consultant))', re.IGNORECASE),
            re.compile(r'(?:^|\s)((?:Managing|Executive|Operations|General)\s+Director)', re.IGNORECASE),
            re.compile(r'(?:^|\s)((?:Chief|Head|Senior|Lead)\s+[A-Z][a-z]+)', re.IGNORECASE),
            
            # Name + title patterns
            re.compile(r'([A-Z][a-z]+\s+[A-Z][a-z]+)[,\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
            
            # Contact section patterns
            re.compile(r'contact[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)[,\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
            
            # About section patterns
            re.compile(r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+is\s+(?:the\s+|our\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
        ]
        
        # Context indicators for title validation
        self.title_contexts = {
            'contact_section': [
                'contact', 'reach', 'speak to', 'get in touch', 'call',
                'email', 'for more information', 'enquiries'
            ],
            'about_section': [
                'about', 'team', 'staff', 'our people', 'meet the',
                'directors', 'management', 'leadership'
            ],
            'experience_section': [
                'experience', 'qualified', 'years', 'expertise',
                'specializing', 'services', 'established'
            ]
        }
        
        # Words that invalidate titles (not executive titles)
        self.title_exclusions = {
            'services', 'solutions', 'systems', 'products', 'equipment',
            'installation', 'repair', 'maintenance', 'cleaning', 'testing',
            'hours', 'days', 'months', 'years', 'time', 'today', 'now',
            'area', 'areas', 'location', 'locations', 'covered', 'covering',
            'company', 'business', 'limited', 'ltd', 'plc', 'group'
        }
        
        # Title confidence scoring weights
        self.confidence_weights = {
            'exact_title_match': 0.8,
            'senior_executive_context': 0.7,
            'management_context': 0.6,
            'technical_context': 0.5,
            'contact_section_bonus': 0.2,
            'about_section_bonus': 0.15,
            'exclusion_penalty': -0.5
        }
    
    def extract_executive_titles(self, content: str, people: List[Dict]) -> List[Dict]:
        """
        Extract executive titles for identified people.
        
        Args:
            content: Website content to analyze
            people: List of people with names and positions
            
        Returns:
            List of people with extracted titles and confidence scores
        """
        try:
            # Pre-process content for better title extraction
            clean_content = self._preprocess_content(content)
            
            # Extract all potential titles from content
            title_candidates = self._extract_title_candidates(clean_content)
            
            people_with_titles = []
            
            for person in people:
                person_name = person.get('name', '')
                
                if not person_name:
                    people_with_titles.append({
                        **person,
                        'title': 'Unknown',
                        'title_confidence': 0.0,
                        'title_extraction_method': 'no_name'
                    })
                    continue
                
                # Find best title match for this person
                title_match = self._find_best_title_match(person_name, title_candidates, clean_content)
                
                if title_match and title_match.confidence > 0.4:
                    people_with_titles.append({
                        **person,
                        'title': title_match.title,
                        'title_confidence': title_match.confidence,
                        'title_extraction_method': title_match.extraction_method,
                        'title_context': title_match.context
                    })
                else:
                    # Try fallback methods
                    fallback_title = self._extract_fallback_title(person_name, clean_content)
                    
                    people_with_titles.append({
                        **person,
                        'title': fallback_title['title'],
                        'title_confidence': fallback_title['confidence'],
                        'title_extraction_method': fallback_title['method'],
                        'title_context': fallback_title.get('context', '')
                    })
            
            self.logger.info(f"Title extraction completed for {len(people)} people")
            return people_with_titles
            
        except Exception as e:
            self.logger.error(f"Error in title extraction: {str(e)}")
            # Return original people with Unknown titles
            return [
                {
                    **person,
                    'title': 'Unknown',
                    'title_confidence': 0.0,
                    'title_extraction_method': 'error'
                }
                for person in people
            ]
    
    def _preprocess_content(self, content: str) -> str:
        """Clean and preprocess content for better title extraction"""
        
        # Remove HTML artifacts and normalize whitespace
        clean_content = re.sub(r'<[^>]+>', ' ', content)
        clean_content = re.sub(r'\s+', ' ', clean_content)
        
        # Remove common website elements that interfere with title extraction
        noise_patterns = [
            r'call\s+now', r'click\s+here', r'book\s+online',
            r'free\s+quote', r'emergency\s+call', r'24/7',
            r'opening\s+hours?', r'contact\s+us\s+today'
        ]
        
        for pattern in noise_patterns:
            clean_content = re.sub(pattern, ' ', clean_content, flags=re.IGNORECASE)
        
        return clean_content
    
    def _extract_title_candidates(self, content: str) -> List[TitleMatch]:
        """Extract all potential title candidates from content"""
        
        title_candidates = []
        
        # Method 1: Direct title pattern matching
        for pattern in self.title_patterns:
            for match in pattern.finditer(content):
                groups = match.groups()
                
                if len(groups) >= 2:
                    potential_name = groups[0].strip()
                    potential_title = groups[1].strip()
                    
                    # Validate that this looks like a title
                    if self._is_valid_title(potential_title):
                        position = match.start()
                        context = self._get_context_around_position(content, position, 150)
                        
                        title_candidates.append(TitleMatch(
                            title=potential_title,
                            confidence=self._calculate_title_confidence(potential_title, context),
                            extraction_method='pattern_match',
                            context=context,
                            position=position
                        ))
        
        # Method 2: Known executive title scanning
        for title_category, titles in self.executive_titles.items():
            for title in titles:
                pattern = re.compile(rf'\b{re.escape(title)}\b', re.IGNORECASE)
                
                for match in pattern.finditer(content):
                    position = match.start()
                    context = self._get_context_around_position(content, position, 150)
                    
                    title_candidates.append(TitleMatch(
                        title=title.title(),
                        confidence=self._calculate_title_confidence(title, context),
                        extraction_method=f'known_title_{title_category}',
                        context=context,
                        position=position
                    ))
        
        # Remove duplicates and sort by confidence
        unique_titles = self._remove_duplicate_titles(title_candidates)
        
        return sorted(unique_titles, key=lambda x: x.confidence, reverse=True)
    
    def _find_best_title_match(self, person_name: str, title_candidates: List[TitleMatch], content: str) -> Optional[TitleMatch]:
        """Find the best title match for a specific person"""
        
        best_match = None
        best_score = 0
        
        name_parts = person_name.lower().split()
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[-1] if len(name_parts) > 1 else ''
        
        for title_candidate in title_candidates:
            # Calculate proximity score to person name
            proximity_score = self._calculate_name_title_proximity(person_name, title_candidate, content)
            
            # Calculate context relevance score
            context_score = self._calculate_context_relevance(title_candidate.context, person_name)
            
            # Calculate overall score
            total_score = (
                title_candidate.confidence * 0.5 +
                proximity_score * 0.3 +
                context_score * 0.2
            )
            
            if total_score > best_score and total_score > 0.4:
                best_score = total_score
                best_match = TitleMatch(
                    title=title_candidate.title,
                    confidence=total_score,
                    extraction_method=f"matched_{title_candidate.extraction_method}",
                    context=title_candidate.context,
                    position=title_candidate.position
                )
        
        return best_match
    
    def _extract_fallback_title(self, person_name: str, content: str) -> Dict:
        """Extract title using fallback methods when primary extraction fails"""
        
        # Method 1: Look for name in specific contexts
        context_patterns = [
            rf'{re.escape(person_name)}\s+is\s+(?:the\s+|our\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            rf'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+{re.escape(person_name)}',
            rf'{re.escape(person_name)}[,\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        for pattern in context_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                potential_title = match.group(1).strip()
                
                if self._is_valid_title(potential_title):
                    confidence = 0.6 if self._is_known_executive_title(potential_title) else 0.4
                    
                    return {
                        'title': potential_title.title(),
                        'confidence': confidence,
                        'method': 'fallback_context',
                        'context': match.group(0)
                    }
        
        # Method 2: Infer from company context
        inferred_title = self._infer_title_from_company_context(content)
        if inferred_title:
            return {
                'title': inferred_title,
                'confidence': 0.3,
                'method': 'fallback_inference',
                'context': 'Company context'
            }
        
        # Default fallback
        return {
            'title': 'Director',  # Common UK business title
            'confidence': 0.2,
            'method': 'default_fallback'
        }
    
    def _is_valid_title(self, title: str) -> bool:
        """Check if a string represents a valid executive title"""
        
        title_lower = title.lower().strip()
        
        # Must be reasonable length
        if len(title_lower) < 2 or len(title_lower) > 50:
            return False
        
        # Must not contain exclusion terms
        if any(exclusion in title_lower for exclusion in self.title_exclusions):
            return False
        
        # Must not be all numbers
        if title_lower.isdigit():
            return False
        
        # Must not contain common non-title words
        non_title_indicators = [
            'hours', 'days', 'phone', 'email', 'website', 'address',
            'street', 'road', 'postcode', 'available', 'emergency'
        ]
        
        if any(indicator in title_lower for indicator in non_title_indicators):
            return False
        
        # Should contain some title-like characteristics
        title_indicators = [
            'director', 'manager', 'officer', 'head', 'chief',
            'senior', 'lead', 'principal', 'consultant', 'specialist',
            'engineer', 'technician', 'supervisor', 'coordinator'
        ]
        
        return any(indicator in title_lower for indicator in title_indicators)
    
    def _is_known_executive_title(self, title: str) -> bool:
        """Check if title appears in our known executive titles"""
        title_lower = title.lower()
        
        for category_titles in self.executive_titles.values():
            if any(known_title in title_lower for known_title in category_titles):
                return True
        
        return False
    
    def _calculate_title_confidence(self, title: str, context: str) -> float:
        """Calculate confidence score for a title based on title and context"""
        
        confidence = 0.0
        title_lower = title.lower()
        context_lower = context.lower()
        
        # Base confidence from title recognition
        if self._is_known_executive_title(title):
            confidence += self.confidence_weights['exact_title_match']
        else:
            confidence += 0.4  # Unknown but valid-looking title
        
        # Context bonuses
        for context_type, indicators in self.title_contexts.items():
            if any(indicator in context_lower for indicator in indicators):
                if context_type == 'contact_section':
                    confidence += self.confidence_weights['contact_section_bonus']
                elif context_type == 'about_section':
                    confidence += self.confidence_weights['about_section_bonus']
                break
        
        # Seniority bonuses
        if any(senior_title in title_lower for senior_title in self.executive_titles['senior_executive']):
            confidence += self.confidence_weights['senior_executive_context']
        elif any(mgmt_title in title_lower for mgmt_title in self.executive_titles['senior_management']):
            confidence += self.confidence_weights['management_context']
        
        # Exclusion penalties
        if any(exclusion in title_lower for exclusion in self.title_exclusions):
            confidence += self.confidence_weights['exclusion_penalty']
        
        return min(confidence, 1.0)
    
    def _calculate_name_title_proximity(self, person_name: str, title_candidate: TitleMatch, content: str) -> float:
        """Calculate how close a title is to a person's name in the content"""
        
        name_positions = [m.start() for m in re.finditer(re.escape(person_name), content, re.IGNORECASE)]
        
        if not name_positions:
            return 0.0
        
        title_position = title_candidate.position
        min_distance = min(abs(title_position - pos) for pos in name_positions)
        
        # Score based on proximity (closer = higher score)
        if min_distance <= 50:
            return 1.0
        elif min_distance <= 150:
            return 0.8
        elif min_distance <= 300:
            return 0.6
        elif min_distance <= 500:
            return 0.4
        else:
            return 0.2
    
    def _calculate_context_relevance(self, context: str, person_name: str) -> float:
        """Calculate how relevant the context is for title extraction"""
        
        context_lower = context.lower()
        relevance_score = 0.0
        
        # Check if person name appears in context
        if person_name.lower() in context_lower:
            relevance_score += 0.5
        
        # Check for executive contexts
        for context_type, indicators in self.title_contexts.items():
            if any(indicator in context_lower for indicator in indicators):
                relevance_score += 0.3
                break
        
        # Check for executive title words
        executive_words = ['director', 'manager', 'chief', 'head', 'senior', 'lead']
        if any(word in context_lower for word in executive_words):
            relevance_score += 0.2
        
        return min(relevance_score, 1.0)
    
    def _infer_title_from_company_context(self, content: str) -> Optional[str]:
        """Infer likely title based on company type and context"""
        
        content_lower = content.lower()
        
        # For small service companies, likely titles
        service_indicators = ['plumbing', 'electrical', 'heating', 'maintenance']
        if any(service in content_lower for service in service_indicators):
            
            # If it mentions "family business" or "established", likely owner/director
            if 'family' in content_lower or 'established' in content_lower:
                return 'Director'
            
            # If technical focus, likely engineer
            if 'engineer' in content_lower or 'qualified' in content_lower:
                return 'Engineer'
            
            # Default for service companies
            return 'Manager'
        
        return None
    
    def _get_context_around_position(self, content: str, position: int, window: int) -> str:
        """Extract context around a position"""
        start = max(0, position - window)
        end = min(len(content), position + window)
        return content[start:end]
    
    def _remove_duplicate_titles(self, title_candidates: List[TitleMatch]) -> List[TitleMatch]:
        """Remove duplicate titles, keeping the highest confidence version"""
        
        seen_titles = {}
        
        for candidate in title_candidates:
            title_key = candidate.title.lower().strip()
            
            if title_key not in seen_titles or candidate.confidence > seen_titles[title_key].confidence:
                seen_titles[title_key] = candidate
        
        return list(seen_titles.values())
    
    def get_extraction_summary(self, people_with_titles: List[Dict]) -> Dict:
        """Generate summary of title extraction results"""
        
        if not people_with_titles:
            return {
                'total_people': 0,
                'titles_extracted': 0,
                'extraction_rate': 0.0,
                'average_confidence': 0.0,
                'methods_used': []
            }
        
        total_people = len(people_with_titles)
        meaningful_titles = sum(1 for person in people_with_titles if person.get('title', 'Unknown') != 'Unknown')
        
        confidences = [person.get('title_confidence', 0.0) for person in people_with_titles]
        average_confidence = sum(confidences) / len(confidences)
        
        methods = [person.get('title_extraction_method', 'unknown') for person in people_with_titles]
        unique_methods = list(set(methods))
        
        return {
            'total_people': total_people,
            'titles_extracted': meaningful_titles,
            'extraction_rate': meaningful_titles / total_people,
            'average_confidence': average_confidence,
            'methods_used': unique_methods,
            'title_distribution': self._get_title_distribution(people_with_titles)
        }
    
    def _get_title_distribution(self, people_with_titles: List[Dict]) -> Dict:
        """Get distribution of extracted titles"""
        
        title_counts = {}
        
        for person in people_with_titles:
            title = person.get('title', 'Unknown')
            title_counts[title] = title_counts.get(title, 0) + 1
        
        return title_counts 