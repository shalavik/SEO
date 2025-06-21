#!/usr/bin/env python3
"""
Alternative Search Enricher

P2.1 GOOGLE BYPASS STRATEGIES
Implements multiple search engines and bypass techniques to overcome Google 429 blocking.
Provides fallback search capabilities with enhanced executive discovery patterns.

Features:
- DuckDuckGo search integration
- Bing search integration  
- StartPage search integration
- User-agent rotation
- Request header randomization
- Rate limiting optimization
- Search result parsing and executive extraction
"""

import asyncio
import logging
import random
import re
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urljoin
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

from ..models import ExecutiveContact
from ..config import get_processing_config

logger = logging.getLogger(__name__)

@dataclass
class SearchEngine:
    """Search engine configuration"""
    name: str
    base_url: str
    search_path: str
    result_selector: str
    title_selector: str
    snippet_selector: str
    user_agents: List[str]
    rate_limit: float  # seconds between requests
    max_results: int = 10

@dataclass
class SearchResult:
    """Search result data"""
    title: str
    url: str
    snippet: str
    search_engine: str
    confidence: float = 0.0

class AlternativeSearchEnricher:
    """P2.1 ENHANCED: Alternative search engines with Google bypass strategies"""
    
    def __init__(self):
        self.processing_config = get_processing_config()
        
        # P2.1: Multiple search engines for Google bypass
        self.search_engines = {
            'duckduckgo': SearchEngine(
                name='DuckDuckGo',
                base_url='https://duckduckgo.com',
                search_path='/html/',
                result_selector='div[data-result-index]',
                title_selector='h2 a',
                snippet_selector='div[data-result-snippet]',
                user_agents=[
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                ],
                rate_limit=1.5,
                max_results=8
            ),
            'bing': SearchEngine(
                name='Bing',
                base_url='https://www.bing.com',
                search_path='/search',
                result_selector='li.b_algo',
                title_selector='h2 a',
                snippet_selector='div.b_caption p',
                user_agents=[
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
                ],
                rate_limit=1.2,
                max_results=10
            ),
            'startpage': SearchEngine(
                name='StartPage',
                base_url='https://www.startpage.com',
                search_path='/sp/search',
                result_selector='div.w-gl__result',
                title_selector='h3 a',
                snippet_selector='p.w-gl__description',
                user_agents=[
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                ],
                rate_limit=2.0,
                max_results=8
            )
        }
        
        # P2.1: Enhanced executive search patterns
        self.executive_patterns = [
            # CEO/Founder patterns
            '"{company_name}" CEO founder owner',
            '"{company_name}" managing director',
            '"{company_name}" director owner',
            'site:{domain} CEO founder',
            'site:{domain} managing director',
            
            # Industry-specific patterns
            '"{company_name}" master plumber owner',
            '"{company_name}" qualified electrician owner',
            '"{company_name}" chartered engineer',
            '"{company_name}" business owner contact',
            
            # Contact patterns
            '"{company_name}" contact owner manager',
            'site:{domain} "speak to" owner',
            'site:{domain} "contact" director',
            
            # LinkedIn patterns
            'site:linkedin.com/in "{company_name}" CEO',
            'site:linkedin.com/in "{company_name}" director',
            'site:linkedin.com/in "{company_name}" founder',
            
            # Social media patterns
            'site:twitter.com "{company_name}" owner',
            'site:facebook.com "{company_name}" owner'
        ]
        
        # P2.1: Executive extraction patterns
        self.name_extraction_patterns = [
            # Direct name patterns
            r'(?:CEO|Director|Founder|Owner|Manager)[\s:,-]+([A-Z][a-z]{{2,15}}\s+[A-Z][a-z]{{2,15}})',
            r'([A-Z][a-z]{{2,15}}\s+[A-Z][a-z]{{2,15}})[\s,]+(?:CEO|Director|Founder|Owner|Manager)',
            r'Contact[\s:,-]+([A-Z][a-z]{{2,15}}\s+[A-Z][a-z]{{2,15}})',
            r'Speak to[\s:,-]+([A-Z][a-z]{{2,15}}\s+[A-Z][a-z]{{2,15}})',
            
            # LinkedIn patterns
            r'linkedin\.com/in/([a-z-]+)',
            r'([A-Z][a-z]{{2,15}}\s+[A-Z][a-z]{{2,15}}).*?(?:at|@)\s*{company_name}',
            
            # Business context patterns
            r'{company_name}.*?(?:run by|owned by|founded by)[\s:,-]+([A-Z][a-z]{{2,15}}\s+[A-Z][a-z]{{2,15}})',
            r'([A-Z][a-z]{{2,15}}\s+[A-Z][a-z]{{2,15}}).*?(?:runs|owns|founded)\s*{company_name}'
        ]
        
        # Request session with connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        logger.info("Alternative Search Enricher initialized with P2.1 Google bypass strategies")
    
    async def discover_executives(self, company_name: str, domain: str, 
                                industry: str = None) -> List[ExecutiveContact]:
        """P2.1 ENHANCED: Discover executives using alternative search engines"""
        logger.info(f"🔍 P2.1: Starting alternative search discovery for: {company_name}")
        
        all_executives = []
        search_results = []
        
        # Try each search engine in order of preference
        for engine_name, engine in self.search_engines.items():
            try:
                logger.debug(f"Trying {engine.name} search for {company_name}")
                
                # Generate search queries for this engine
                queries = self._generate_search_queries(company_name, domain, industry)
                
                # Search with this engine
                engine_results = await self._search_with_engine(
                    engine, queries[:3], company_name  # Limit to top 3 queries per engine
                )
                
                search_results.extend(engine_results)
                
                # Extract executives from results
                engine_executives = self._extract_executives_from_results(
                    engine_results, company_name, domain
                )
                
                all_executives.extend(engine_executives)
                
                logger.info(f"{engine.name}: Found {len(engine_executives)} executives from {len(engine_results)} results")
                
                # Rate limiting between engines
                await asyncio.sleep(engine.rate_limit)
                
                # If we found good results, we can be less aggressive with other engines
                if len(engine_executives) >= 2:
                    logger.debug(f"Found sufficient results from {engine.name}, reducing search intensity")
                    break
                    
            except Exception as e:
                logger.warning(f"Search failed with {engine.name}: {e}")
                continue
        
        # Deduplicate and score executives
        unique_executives = self._deduplicate_executives(all_executives)
        scored_executives = self._score_executive_confidence(unique_executives, search_results)
        
        logger.info(f"🎯 P2.1: Alternative search found {len(scored_executives)} unique executives")
        return scored_executives
    
    def _generate_search_queries(self, company_name: str, domain: str, 
                               industry: str = None) -> List[str]:
        """Generate optimized search queries for executive discovery"""
        queries = []
        
        # Clean domain for search
        clean_domain = domain.replace('www.', '').replace('http://', '').replace('https://', '')
        
        for pattern in self.executive_patterns:
            try:
                query = pattern.format(
                    company_name=company_name,
                    domain=clean_domain
                )
                queries.append(query)
            except KeyError:
                # Skip patterns that don't match available variables
                continue
        
        # Add industry-specific queries if available
        if industry:
            industry_queries = [
                f'"{company_name}" {industry} owner director',
                f'"{company_name}" {industry} manager contact',
                f'site:{clean_domain} {industry} expert'
            ]
            queries.extend(industry_queries)
        
        # Prioritize queries (most specific first)
        prioritized_queries = []
        
        # 1. Site-specific queries (highest priority)
        site_queries = [q for q in queries if 'site:' in q and 'linkedin' not in q]
        prioritized_queries.extend(site_queries)
        
        # 2. Company name + role queries
        role_queries = [q for q in queries if 'CEO' in q or 'director' in q or 'founder' in q]
        prioritized_queries.extend(role_queries)
        
        # 3. LinkedIn queries
        linkedin_queries = [q for q in queries if 'linkedin' in q]
        prioritized_queries.extend(linkedin_queries)
        
        # 4. Other queries
        other_queries = [q for q in queries if q not in prioritized_queries]
        prioritized_queries.extend(other_queries)
        
        return prioritized_queries[:10]  # Limit to top 10 queries
    
    async def _search_with_engine(self, engine: SearchEngine, queries: List[str], 
                                company_name: str) -> List[SearchResult]:
        """Perform search with specific search engine"""
        results = []
        
        for query in queries:
            try:
                # Random user agent for each request
                headers = {
                    'User-Agent': random.choice(engine.user_agents),
                    'Referer': engine.base_url,
                    'DNT': '1',
                    'Cache-Control': 'no-cache'
                }
                
                # Build search URL
                if engine.name == 'DuckDuckGo':
                    search_url = f"{engine.base_url}{engine.search_path}?q={quote_plus(query)}"
                elif engine.name == 'Bing':
                    search_url = f"{engine.base_url}{engine.search_path}?q={quote_plus(query)}&count={engine.max_results}"
                elif engine.name == 'StartPage':
                    search_url = f"{engine.base_url}{engine.search_path}?query={quote_plus(query)}&num={engine.max_results}"
                
                logger.debug(f"Searching {engine.name}: {query}")
                
                # Make request with timeout
                response = self.session.get(
                    search_url,
                    headers=headers,
                    timeout=10,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    # Parse results
                    query_results = self._parse_search_results(response.text, engine, query)
                    results.extend(query_results)
                    
                    logger.debug(f"Found {len(query_results)} results for query: {query}")
                else:
                    logger.warning(f"{engine.name} returned status {response.status_code} for query: {query}")
                
                # Rate limiting between queries
                await asyncio.sleep(engine.rate_limit)
                
            except Exception as e:
                logger.debug(f"Query failed on {engine.name}: {query} - {e}")
                continue
        
        return results
    
    def _parse_search_results(self, html: str, engine: SearchEngine, query: str) -> List[SearchResult]:
        """Parse search results from HTML"""
        results = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            result_elements = soup.select(engine.result_selector)
            
            for element in result_elements[:engine.max_results]:
                try:
                    # Extract title
                    title_elem = element.select_one(engine.title_selector)
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # Extract URL
                    url = ""
                    if title_elem and title_elem.get('href'):
                        url = title_elem['href']
                    elif title_elem and title_elem.parent and title_elem.parent.get('href'):
                        url = title_elem.parent['href']
                    
                    # Extract snippet
                    snippet_elem = element.select_one(engine.snippet_selector)
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    if title and url:
                        result = SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                            search_engine=engine.name
                        )
                        results.append(result)
                        
                except Exception as e:
                    logger.debug(f"Failed to parse result element: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Failed to parse {engine.name} results: {e}")
        
        return results
    
    def _extract_executives_from_results(self, results: List[SearchResult], 
                                       company_name: str, domain: str) -> List[ExecutiveContact]:
        """Extract executive information from search results"""
        executives = []
        
        for result in results:
            try:
                # Combine title and snippet for analysis
                text_content = f"{result.title} {result.snippet}".lower()
                
                # Extract names using patterns
                extracted_names = self._extract_names_from_text(
                    text_content, company_name
                )
                
                for name_data in extracted_names:
                    # Create executive contact
                    executive = ExecutiveContact(
                        first_name=name_data['first_name'],
                        last_name=name_data['last_name'],
                        full_name=name_data['full_name'],
                        title=name_data.get('title', 'Executive'),
                        company_name=company_name,
                        email=None,
                        phone=None,
                        bio=result.snippet[:200],
                        discovery_sources=[f"alternative_search_{result.search_engine}"],
                        confidence=name_data.get('confidence', 0.5),
                        seniority_tier=self._determine_seniority_tier(name_data.get('title', '')),
                        company_domain=domain
                    )
                    
                    executives.append(executive)
                    
            except Exception as e:
                logger.debug(f"Failed to extract executives from result: {e}")
                continue
        
        return executives
    
    def _extract_names_from_text(self, text: str, company_name: str) -> List[Dict]:
        """Extract person names from text using enhanced patterns"""
        extracted_names = []
        
        # Prepare company name for pattern matching
        company_clean = re.sub(r'[^\w\s]', '', company_name.lower())
        
        for pattern in self.name_extraction_patterns:
            try:
                # Format pattern with company name if needed
                if '{company_name}' in pattern:
                    formatted_pattern = pattern.format(company_name=company_clean)
                else:
                    formatted_pattern = pattern
                
                matches = re.finditer(formatted_pattern, text, re.IGNORECASE)
                
                for match in matches:
                    if match.groups():
                        name_text = match.group(1).strip()
                        
                        # Validate name
                        if self._is_valid_person_name(name_text):
                            name_parts = name_text.split()
                            if len(name_parts) >= 2:
                                name_data = {
                                    'first_name': name_parts[0],
                                    'last_name': ' '.join(name_parts[1:]),
                                    'full_name': name_text,
                                    'title': self._extract_title_from_context(text, name_text),
                                    'confidence': self._calculate_name_confidence(name_text, text)
                                }
                                extracted_names.append(name_data)
                                
            except Exception as e:
                logger.debug(f"Pattern matching failed: {e}")
                continue
        
        return extracted_names
    
    def _is_valid_person_name(self, name: str) -> bool:
        """Validate if text looks like a person's name"""
        if not name or len(name) < 3 or len(name) > 50:
            return False
        
        # Should contain at least two words
        words = name.split()
        if len(words) < 2:
            return False
        
        # Should start with capital letters
        if not all(word[0].isupper() for word in words):
            return False
        
        # Should not contain numbers or special characters
        if re.search(r'[0-9@#$%^&*()+={}[\]|\\:";\'<>?/]', name):
            return False
        
        # Should not be common business words
        business_words = ['limited', 'ltd', 'company', 'services', 'solutions', 'group', 'plumbing', 'electrical']
        name_lower = name.lower()
        if any(word in name_lower for word in business_words):
            return False
        
        return True
    
    def _extract_title_from_context(self, text: str, name: str) -> str:
        """Extract executive title from surrounding context"""
        # Look for title patterns around the name
        title_patterns = [
            r'(?:CEO|Chief Executive Officer)',
            r'(?:Managing Director|MD)',
            r'(?:Director)',
            r'(?:Founder)',
            r'(?:Owner)',
            r'(?:Manager)',
            r'(?:Master Plumber)',
            r'(?:Qualified Electrician)',
            r'(?:Chartered Engineer)'
        ]
        
        # Search in text around the name
        name_index = text.lower().find(name.lower())
        if name_index != -1:
            # Look 100 characters before and after the name
            context = text[max(0, name_index-100):name_index+len(name)+100]
            
            for pattern in title_patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    return match.group(0)
        
        return "Executive"
    
    def _calculate_name_confidence(self, name: str, context: str) -> float:
        """Calculate confidence score for extracted name"""
        confidence = 0.5  # Base confidence
        
        # Boost for common name patterns
        if re.match(r'^[A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15}$', name):
            confidence += 0.2
        
        # Boost for title context
        title_keywords = ['ceo', 'director', 'founder', 'owner', 'manager']
        if any(keyword in context.lower() for keyword in title_keywords):
            confidence += 0.15
        
        # Boost for contact context
        contact_keywords = ['contact', 'speak to', 'call', 'email']
        if any(keyword in context.lower() for keyword in contact_keywords):
            confidence += 0.1
        
        # Boost for LinkedIn context
        if 'linkedin' in context.lower():
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _determine_seniority_tier(self, title: str) -> str:
        """Determine executive seniority tier from title"""
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in ['ceo', 'chief executive', 'founder', 'owner']):
            return 'tier_1'
        elif any(keyword in title_lower for keyword in ['director', 'managing director', 'md']):
            return 'tier_2'
        elif any(keyword in title_lower for keyword in ['manager', 'head of']):
            return 'tier_3'
        else:
            return 'tier_4'
    
    def _deduplicate_executives(self, executives: List[ExecutiveContact]) -> List[ExecutiveContact]:
        """Remove duplicate executives based on name similarity"""
        if not executives:
            return []
        
        unique_executives = []
        
        for executive in executives:
            is_duplicate = False
            
            for existing in unique_executives:
                # Check name similarity
                name_similarity = fuzz.ratio(
                    executive.full_name.lower(),
                    existing.full_name.lower()
                )
                
                if name_similarity > 85:  # 85% similarity threshold
                    is_duplicate = True
                    # Keep the one with higher confidence
                    if executive.confidence > existing.confidence:
                        unique_executives.remove(existing)
                        unique_executives.append(executive)
                    break
            
            if not is_duplicate:
                unique_executives.append(executive)
        
        return unique_executives
    
    def _score_executive_confidence(self, executives: List[ExecutiveContact], 
                                  search_results: List[SearchResult]) -> List[ExecutiveContact]:
        """Score executive confidence based on search result quality"""
        for executive in executives:
            # Base confidence from extraction
            base_confidence = executive.confidence
            
            # Boost for multiple source confirmation
            source_count = len(executive.discovery_sources)
            if source_count > 1:
                base_confidence += 0.1 * (source_count - 1)
            
            # Boost for high-quality sources
            if any('linkedin' in source for source in executive.discovery_sources):
                base_confidence += 0.15
            
            # Boost for seniority tier
            if executive.seniority_tier == 'tier_1':
                base_confidence += 0.1
            elif executive.seniority_tier == 'tier_2':
                base_confidence += 0.05
            
            # Cap at 1.0
            executive.confidence = min(1.0, base_confidence)
        
        # Sort by confidence (highest first)
        executives.sort(key=lambda x: x.confidence, reverse=True)
        
        return executives

# Usage example and testing
async def test_alternative_search():
    """Test function for alternative search enricher"""
    async with AlternativeSearchEnricher() as enricher:
        executives = await enricher.discover_executives("Jack The Plumber", "jacktheplumber.co.uk")
        
        print(f"Found {len(executives)} executives:")
        for exec in executives:
            print(f"- {exec.full_name} ({exec.title}) - Confidence: {exec.confidence}")

if __name__ == "__main__":
    asyncio.run(test_alternative_search()) 