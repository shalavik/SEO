"""
Real LinkedIn Discoverer - Genuine LinkedIn Profile Discovery
Uses actual Google search to find real LinkedIn profiles instead of fabricating URLs
"""

import re
import time
import requests
import logging
from typing import List, Dict, Optional
from urllib.parse import urlencode, urlparse
from dataclasses import dataclass

@dataclass
class LinkedInProfile:
    """Represents a discovered LinkedIn profile with validation"""
    url: str
    name: str
    title: str
    company: str
    confidence: float
    discovery_method: str
    validation_status: str

class RealLinkedInDiscoverer:
    """
    Real LinkedIn profile discovery using actual web search and validation.
    Replaces fake URL construction with genuine profile discovery.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # User agents for web requests
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        
        # LinkedIn URL patterns for validation
        self.linkedin_patterns = [
            re.compile(r'https?://(?:www\.)?linkedin\.com/in/([^/?]+)', re.IGNORECASE),
            re.compile(r'https?://(?:uk\.)?linkedin\.com/in/([^/?]+)', re.IGNORECASE),
        ]
        
        # Search engines and their parameters
        self.search_engines = {
            'google': {
                'url': 'https://www.google.com/search',
                'params': {
                    'num': '10',
                    'hl': 'en',
                    'lr': 'lang_en'
                }
            },
            'bing': {
                'url': 'https://www.bing.com/search',
                'params': {
                    'count': '10'
                }
            }
        }
        
        # Common UK business terms to filter search results
        self.business_terms = [
            'ltd', 'limited', 'plc', 'company', 'services', 'solutions',
            'group', 'contractors', 'specialists', 'engineers'
        ]
        
    def discover_linkedin_profiles(self, people: List[Dict], company_info: Dict) -> List[Dict]:
        """
        Discover real LinkedIn profiles for a list of people.
        
        Args:
            people: List of people with names and other details
            company_info: Company information including name and domain
            
        Returns:
            List of people with discovered LinkedIn profiles
        """
        try:
            company_name = company_info.get('name', '')
            company_domain = company_info.get('domain', '')
            
            enriched_people = []
            
            for person in people:
                person_name = person.get('name', '')
                
                if not person_name or len(person_name.split()) != 2:
                    # Skip invalid names
                    enriched_people.append({
                        **person,
                        'linkedin_url': None,
                        'linkedin_confidence': 0.0,
                        'linkedin_discovery_method': 'skipped_invalid_name'
                    })
                    continue
                
                # Attempt LinkedIn discovery
                linkedin_result = self._search_linkedin_profile(person_name, company_name, company_domain)
                
                # Add LinkedIn data to person
                enriched_person = {
                    **person,
                    'linkedin_url': linkedin_result['url'] if linkedin_result else None,
                    'linkedin_confidence': linkedin_result['confidence'] if linkedin_result else 0.0,
                    'linkedin_discovery_method': linkedin_result['method'] if linkedin_result else 'not_found',
                    'linkedin_title': linkedin_result['title'] if linkedin_result else None,
                    'linkedin_validation': linkedin_result['validation'] if linkedin_result else 'not_attempted'
                }
                
                enriched_people.append(enriched_person)
                
                # Rate limiting to avoid being blocked
                time.sleep(2)
            
            self.logger.info(f"LinkedIn discovery completed for {len(people)} people")
            return enriched_people
            
        except Exception as e:
            self.logger.error(f"Error in LinkedIn discovery: {str(e)}")
            # Return original people with empty LinkedIn data
            return [
                {
                    **person,
                    'linkedin_url': None,
                    'linkedin_confidence': 0.0,
                    'linkedin_discovery_method': 'error'
                }
                for person in people
            ]
    
    def _search_linkedin_profile(self, person_name: str, company_name: str, company_domain: str) -> Optional[Dict]:
        """
        Search for a person's LinkedIn profile using multiple methods.
        
        Args:
            person_name: Full name of the person
            company_name: Name of the company
            company_domain: Company domain for validation
            
        Returns:
            LinkedIn profile information or None
        """
        
        # Method 1: Search with company name
        if company_name:
            result = self._perform_linkedin_search(person_name, company_name)
            if result and result['confidence'] > 0.7:
                return result
        
        # Method 2: Search with domain
        if company_domain:
            domain_clean = company_domain.replace('www.', '').replace('.com', '').replace('.co.uk', '')
            result = self._perform_linkedin_search(person_name, domain_clean)
            if result and result['confidence'] > 0.6:
                return result
        
        # Method 3: General search (lower confidence)
        result = self._perform_linkedin_search(person_name, '')
        if result and result['confidence'] > 0.5:
            return result
        
        return None
    
    def _perform_linkedin_search(self, person_name: str, company_context: str) -> Optional[Dict]:
        """
        Perform actual web search for LinkedIn profiles.
        
        Args:
            person_name: Person's name to search for
            company_context: Company name or identifier for context
            
        Returns:
            Search result with LinkedIn profile data
        """
        try:
            # Construct search query
            if company_context:
                search_query = f'"{person_name}" {company_context} site:linkedin.com/in'
            else:
                search_query = f'"{person_name}" site:linkedin.com/in'
            
            # Try Google search first
            search_results = self._google_search(search_query)
            
            if not search_results:
                # Fallback to Bing search
                search_results = self._bing_search(search_query)
            
            if not search_results:
                return None
            
            # Analyze search results for LinkedIn profiles
            best_match = self._analyze_linkedin_search_results(search_results, person_name, company_context)
            
            if best_match:
                # Validate the LinkedIn URL
                validation_result = self._validate_linkedin_profile(best_match['url'])
                
                return {
                    'url': best_match['url'],
                    'confidence': best_match['confidence'] * validation_result['confidence_multiplier'],
                    'method': f"search_{best_match['source']}",
                    'title': best_match.get('title', ''),
                    'validation': validation_result['status']
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in LinkedIn search for {person_name}: {str(e)}")
            return None
    
    def _google_search(self, query: str) -> List[Dict]:
        """
        Perform Google search (simplified approach).
        Note: This is a basic implementation. Production systems should use Google Custom Search API.
        """
        try:
            # This is a simplified search approach
            # In production, use Google Custom Search API or similar service
            
            search_url = self.search_engines['google']['url']
            params = {
                'q': query,
                **self.search_engines['google']['params']
            }
            
            headers = {
                'User-Agent': self.user_agents[0]
            }
            
            # Note: This approach may be blocked by Google
            # For production, implement proper API-based search
            response = requests.get(search_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return self._parse_google_results(response.text)
            
            return []
            
        except Exception as e:
            self.logger.warning(f"Google search failed: {str(e)}")
            return []
    
    def _bing_search(self, query: str) -> List[Dict]:
        """
        Perform Bing search as fallback.
        Note: This is a basic implementation. Production systems should use Bing Search API.
        """
        try:
            search_url = self.search_engines['bing']['url']
            params = {
                'q': query,
                **self.search_engines['bing']['params']
            }
            
            headers = {
                'User-Agent': self.user_agents[1]
            }
            
            response = requests.get(search_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return self._parse_bing_results(response.text)
            
            return []
            
        except Exception as e:
            self.logger.warning(f"Bing search failed: {str(e)}")
            return []
    
    def _parse_google_results(self, html_content: str) -> List[Dict]:
        """
        Parse Google search results to extract LinkedIn URLs.
        Note: This is a simplified parser for demonstration.
        """
        results = []
        
        # Extract LinkedIn URLs from HTML
        for pattern in self.linkedin_patterns:
            matches = pattern.finditer(html_content)
            for match in matches:
                linkedin_url = match.group(0)
                
                # Extract profile ID
                profile_id = match.group(1)
                
                # Try to extract title/description from surrounding context
                title = self._extract_title_from_context(html_content, match.start())
                
                results.append({
                    'url': linkedin_url,
                    'profile_id': profile_id,
                    'title': title,
                    'source': 'google'
                })
        
        return results[:5]  # Return top 5 results
    
    def _parse_bing_results(self, html_content: str) -> List[Dict]:
        """Parse Bing search results to extract LinkedIn URLs."""
        results = []
        
        for pattern in self.linkedin_patterns:
            matches = pattern.finditer(html_content)
            for match in matches:
                linkedin_url = match.group(0)
                profile_id = match.group(1)
                title = self._extract_title_from_context(html_content, match.start())
                
                results.append({
                    'url': linkedin_url,
                    'profile_id': profile_id,
                    'title': title,
                    'source': 'bing'
                })
        
        return results[:5]
    
    def _extract_title_from_context(self, html_content: str, position: int) -> str:
        """Extract title/description from HTML context around LinkedIn URL"""
        try:
            # Get context around the URL
            start = max(0, position - 200)
            end = min(len(html_content), position + 200)
            context = html_content[start:end]
            
            # Look for common title patterns
            title_patterns = [
                r'<title[^>]*>([^<]+)</title>',
                r'<h[1-6][^>]*>([^<]+)</h[1-6]>',
                r'title="([^"]+)"',
                r'alt="([^"]+)"'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if len(title) > 10 and 'linkedin' not in title.lower():
                        return title
            
            return ''
            
        except Exception:
            return ''
    
    def _analyze_linkedin_search_results(self, search_results: List[Dict], person_name: str, company_context: str) -> Optional[Dict]:
        """
        Analyze search results to find the best LinkedIn profile match.
        
        Args:
            search_results: List of LinkedIn URLs found in search
            person_name: Original person name to match against
            company_context: Company context for matching
            
        Returns:
            Best matching profile or None
        """
        if not search_results:
            return None
        
        best_match = None
        best_score = 0
        
        name_parts = person_name.lower().split()
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[-1] if len(name_parts) > 1 else ''
        
        for result in search_results:
            score = 0
            profile_id = result['profile_id'].lower()
            title = result.get('title', '').lower()
            
            # Score 1: Name matching in profile ID
            if first_name in profile_id and last_name in profile_id:
                score += 0.6
            elif first_name in profile_id or last_name in profile_id:
                score += 0.3
            
            # Score 2: Name matching in title
            if person_name.lower() in title:
                score += 0.3
            elif first_name in title and last_name in title:
                score += 0.2
            
            # Score 3: Company context matching
            if company_context and company_context.lower() in title:
                score += 0.2
            
            # Score 4: Profile ID quality (not generic)
            if not any(term in profile_id for term in self.business_terms):
                score += 0.1
            
            # Penalty for generic profile IDs
            if len(profile_id) < 3 or profile_id.isdigit():
                score -= 0.3
            
            if score > best_score:
                best_score = score
                best_match = {
                    'url': result['url'],
                    'confidence': min(score, 1.0),
                    'source': result['source'],
                    'title': result.get('title', '')
                }
        
        # Only return if confidence is reasonable
        if best_match and best_match['confidence'] > 0.4:
            return best_match
        
        return None
    
    def _validate_linkedin_profile(self, linkedin_url: str) -> Dict:
        """
        Validate that a LinkedIn URL is accessible and contains a real profile.
        
        Args:
            linkedin_url: LinkedIn URL to validate
            
        Returns:
            Validation result with status and confidence multiplier
        """
        try:
            # Basic URL format validation
            if not any(pattern.match(linkedin_url) for pattern in self.linkedin_patterns):
                return {
                    'status': 'invalid_format',
                    'confidence_multiplier': 0.0
                }
            
            # Try to access the URL (with caution)
            headers = {
                'User-Agent': self.user_agents[0]
            }
            
            response = requests.head(linkedin_url, headers=headers, timeout=5, allow_redirects=True)
            
            if response.status_code == 200:
                return {
                    'status': 'accessible',
                    'confidence_multiplier': 1.0
                }
            elif response.status_code == 403:
                # LinkedIn blocks automated access, but URL might be valid
                return {
                    'status': 'blocked_but_likely_valid',
                    'confidence_multiplier': 0.8
                }
            else:
                return {
                    'status': 'not_accessible',
                    'confidence_multiplier': 0.5
                }
            
        except Exception as e:
            self.logger.warning(f"LinkedIn validation failed for {linkedin_url}: {str(e)}")
            return {
                'status': 'validation_failed',
                'confidence_multiplier': 0.6
            }
    
    def get_discovery_summary(self, enriched_people: List[Dict]) -> Dict:
        """Generate summary of LinkedIn discovery results"""
        
        total_people = len(enriched_people)
        found_profiles = sum(1 for person in enriched_people if person.get('linkedin_url'))
        high_confidence = sum(1 for person in enriched_people if person.get('linkedin_confidence', 0) > 0.7)
        
        discovery_methods = {}
        for person in enriched_people:
            method = person.get('linkedin_discovery_method', 'unknown')
            discovery_methods[method] = discovery_methods.get(method, 0) + 1
        
        return {
            'total_people': total_people,
            'profiles_found': found_profiles,
            'discovery_rate': found_profiles / total_people if total_people > 0 else 0,
            'high_confidence_profiles': high_confidence,
            'discovery_methods': discovery_methods,
            'average_confidence': sum(person.get('linkedin_confidence', 0) for person in enriched_people) / total_people if total_people > 0 else 0
        } 