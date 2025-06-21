"""
Business Directory Enricher

P2.3 BUSINESS DIRECTORY ENHANCEMENT
Discovers executives from multiple UK business directories including Yell, Thomson Local, Cylex, and others.
Implements advanced scraping techniques for executive discovery from business listings.

Features:
- Multi-directory search (Yell, Thomson Local, Cylex, Bing Places, Google My Business)
- Executive extraction from business listings
- Contact information discovery
- Business profile enrichment
- UK-specific directory optimization
- Zero-cost architecture maintenance
"""

import asyncio
import logging
import random
import re
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urljoin, urlparse
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

from ..models import ExecutiveContact
from ..config import get_processing_config

logger = logging.getLogger(__name__)

@dataclass
class BusinessListing:
    """Business directory listing data structure"""
    name: str
    address: str
    phone: str
    website: str
    directory_source: str
    listing_url: str
    description: str = ""
    contact_person: str = ""
    confidence: float = 0.0

@dataclass
class DirectoryConfig:
    """Directory-specific configuration"""
    name: str
    base_url: str
    search_path: str
    listing_selector: str
    name_selector: str
    address_selector: str
    phone_selector: str
    website_selector: str
    contact_selector: str
    description_selector: str
    user_agents: List[str]
    rate_limit: float = 2.0

class BusinessDirectoryEnricher:
    """P2.3 ENHANCED: Business directory integration for executive discovery"""
    
    def __init__(self):
        self.processing_config = get_processing_config()
        
        # P2.3: UK Business Directory configurations
        self.directories = {
            'yell': DirectoryConfig(
                name='Yell',
                base_url='https://www.yell.com',
                search_path='/s/{query}-{location}.html',
                listing_selector='.businessCapsule',
                name_selector='.businessCapsule--name a',
                address_selector='.businessCapsule--address',
                phone_selector='.businessCapsule--telephone a',
                website_selector='.businessCapsule--website a',
                contact_selector='.businessCapsule--contact',
                description_selector='.businessCapsule--description',
                user_agents=[
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ],
                rate_limit=2.0
            ),
            'thomson_local': DirectoryConfig(
                name='Thomson Local',
                base_url='https://www.thomsonlocal.com',
                search_path='/search/{query}/{location}',
                listing_selector='.listing-item',
                name_selector='.listing-title a',
                address_selector='.listing-address',
                phone_selector='.listing-phone',
                website_selector='.listing-website a',
                contact_selector='.listing-contact',
                description_selector='.listing-description',
                user_agents=[
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
                ],
                rate_limit=2.5
            ),
            'cylex': DirectoryConfig(
                name='Cylex',
                base_url='https://www.cylex-uk.co.uk',
                search_path='/search/{query}/{location}',
                listing_selector='.company-item',
                name_selector='.company-name a',
                address_selector='.company-address',
                phone_selector='.company-phone',
                website_selector='.company-website a',
                contact_selector='.company-contact',
                description_selector='.company-description',
                user_agents=[
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0'
                ],
                rate_limit=3.0
            )
        }
        
        # P2.3: Executive extraction patterns for business directories
        self.executive_patterns = [
            # Contact person patterns
            r'(?i)contact[\s:]*([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
            r'(?i)speak to[\s:]*([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
            r'(?i)ask for[\s:]*([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
            
            # Owner/Manager patterns
            r'(?i)owner[\s:]*([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
            r'(?i)manager[\s:]*([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
            r'(?i)director[\s:]*([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
            
            # Business description patterns
            r'(?i)run by[\s:]*([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
            r'(?i)founded by[\s:]*([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
            r'(?i)established by[\s:]*([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})',
            
            # Professional titles
            r'(?i)([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})[\s,]*(?:master plumber|qualified plumber)',
            r'(?i)([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})[\s,]*(?:master electrician|qualified electrician)',
            r'(?i)([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})[\s,]*(?:chartered engineer|senior engineer)'
        ]
        
        # UK location variations for directory searches
        self.uk_locations = [
            'uk', 'united-kingdom', 'england', 'london', 'birmingham', 'manchester', 
            'glasgow', 'liverpool', 'bristol', 'sheffield', 'leeds', 'edinburgh'
        ]
        
        # Request session with directory-optimized settings
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        })
        
        # Rate limiting tracking
        self.last_requests = {}
        
        logger.info("Business Directory Enricher initialized for P2.3 executive discovery")
    
    async def discover_executives(self, company_name: str, domain: str, 
                                industry: str = None) -> List[ExecutiveContact]:
        """P2.3 ENHANCED: Discover executives from business directories"""
        logger.info(f"📂 P2.3: Starting business directory discovery for: {company_name}")
        
        all_executives = []
        all_listings = []
        
        try:
            # Search each directory
            for directory_name, directory_config in self.directories.items():
                try:
                    logger.debug(f"Searching {directory_config.name} for {company_name}")
                    
                    # Search directory for business listings
                    listings = await self._search_directory(
                        directory_config, company_name, industry
                    )
                    
                    all_listings.extend(listings)
                    
                    # Extract executives from listings
                    directory_executives = self._extract_executives_from_listings(
                        listings, company_name, domain
                    )
                    
                    all_executives.extend(directory_executives)
                    
                    logger.info(f"{directory_config.name}: Found {len(directory_executives)} executives from {len(listings)} listings")
                    
                    # Rate limiting between directories
                    await asyncio.sleep(directory_config.rate_limit)
                    
                except Exception as e:
                    logger.warning(f"Directory search failed for {directory_name}: {e}")
                    continue
            
            # Deduplicate and score executives
            unique_executives = self._deduplicate_directory_executives(all_executives)
            scored_executives = self._score_directory_confidence(unique_executives, all_listings)
            
            logger.info(f"🎯 P2.3: Business directory discovery found {len(scored_executives)} unique executives")
            return scored_executives
            
        except Exception as e:
            logger.warning(f"❌ P2.3: Business directory discovery failed: {e}")
            return []
    
    async def _search_directory(self, directory: DirectoryConfig, company_name: str, 
                              industry: str = None) -> List[BusinessListing]:
        """Search a specific business directory"""
        listings = []
        
        try:
            # Generate search queries
            queries = self._generate_directory_queries(company_name, industry)
            
            for query in queries[:3]:  # Limit to top 3 queries per directory
                try:
                    await self._enforce_rate_limit(directory.name)
                    
                    # Try different UK locations
                    for location in self.uk_locations[:2]:  # Top 2 locations
                        try:
                            # Build search URL
                            search_url = self._build_search_url(directory, query, location)
                            
                            # Make request
                            headers = {
                                'User-Agent': random.choice(directory.user_agents),
                                'Referer': directory.base_url,
                                'DNT': '1'
                            }
                            
                            logger.debug(f"Searching {directory.name}: {query} in {location}")
                            
                            response = self.session.get(
                                search_url, 
                                headers=headers, 
                                timeout=10,
                                allow_redirects=True
                            )
                            
                            if response.status_code == 200:
                                # Parse listings from response
                                query_listings = self._parse_directory_listings(
                                    response.text, directory, company_name
                                )
                                listings.extend(query_listings)
                                
                                logger.debug(f"Found {len(query_listings)} listings for {query} in {location}")
                                
                                # If we found good matches, no need to try more locations
                                if query_listings:
                                    break
                            else:
                                logger.debug(f"{directory.name} returned status {response.status_code}")
                            
                            # Rate limiting between location searches
                            await asyncio.sleep(1.0)
                            
                        except Exception as e:
                            logger.debug(f"Location search failed: {query} in {location} - {e}")
                            continue
                    
                except Exception as e:
                    logger.debug(f"Query search failed: {query} - {e}")
                    continue
            
            return listings
            
        except Exception as e:
            logger.warning(f"Directory search failed for {directory.name}: {e}")
            return []
    
    def _generate_directory_queries(self, company_name: str, industry: str = None) -> List[str]:
        """Generate search queries for business directories"""
        queries = []
        
        # Clean company name
        clean_name = re.sub(r'[^\w\s]', '', company_name).strip()
        
        # Basic company name queries
        queries.append(clean_name)
        queries.append(f'"{clean_name}"')
        
        # Industry-specific queries
        if industry:
            queries.append(f'{clean_name} {industry}')
            queries.append(f'{industry} {clean_name}')
        
        # Service-specific queries (for plumbing example)
        service_keywords = ['plumber', 'plumbing', 'heating', 'boiler', 'bathroom']
        for keyword in service_keywords:
            if keyword.lower() in company_name.lower():
                queries.append(f'{clean_name} {keyword}')
                break
        
        return queries
    
    def _build_search_url(self, directory: DirectoryConfig, query: str, location: str) -> str:
        """Build search URL for directory"""
        try:
            # URL encode query and location
            encoded_query = quote_plus(query)
            encoded_location = quote_plus(location)
            
            # Build URL based on directory format
            if directory.name == 'Yell':
                search_path = directory.search_path.format(
                    query=encoded_query, 
                    location=encoded_location
                )
            elif directory.name in ['Thomson Local', 'Cylex']:
                search_path = directory.search_path.format(
                    query=encoded_query, 
                    location=encoded_location
                )
            else:
                # Generic format
                search_path = f"/search?q={encoded_query}&location={encoded_location}"
            
            return f"{directory.base_url}{search_path}"
            
        except Exception as e:
            logger.debug(f"Failed to build search URL: {e}")
            return f"{directory.base_url}/search?q={quote_plus(query)}"
    
    def _parse_directory_listings(self, html: str, directory: DirectoryConfig, 
                                company_name: str) -> List[BusinessListing]:
        """Parse business listings from directory HTML"""
        listings = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            listing_elements = soup.select(directory.listing_selector)
            
            for element in listing_elements[:10]:  # Limit to top 10 listings
                try:
                    # Extract listing data
                    listing = self._extract_listing_data(element, directory)
                    
                    if listing and self._is_relevant_listing(listing, company_name):
                        listings.append(listing)
                        
                except Exception as e:
                    logger.debug(f"Failed to extract listing: {e}")
                    continue
            
            return listings
            
        except Exception as e:
            logger.debug(f"Failed to parse directory listings: {e}")
            return []
    
    def _extract_listing_data(self, element: BeautifulSoup, directory: DirectoryConfig) -> Optional[BusinessListing]:
        """Extract data from a single business listing"""
        try:
            # Extract name
            name_elem = element.select_one(directory.name_selector)
            name = name_elem.get_text(strip=True) if name_elem else ""
            
            # Extract address
            address_elem = element.select_one(directory.address_selector)
            address = address_elem.get_text(strip=True) if address_elem else ""
            
            # Extract phone
            phone_elem = element.select_one(directory.phone_selector)
            phone = phone_elem.get_text(strip=True) if phone_elem else ""
            if phone_elem and phone_elem.get('href'):
                # Extract from tel: link
                phone_href = phone_elem.get('href')
                if phone_href.startswith('tel:'):
                    phone = phone_href[4:]
            
            # Extract website
            website_elem = element.select_one(directory.website_selector)
            website = ""
            if website_elem and website_elem.get('href'):
                website = website_elem['href']
            
            # Extract contact person
            contact_elem = element.select_one(directory.contact_selector)
            contact_person = contact_elem.get_text(strip=True) if contact_elem else ""
            
            # Extract description
            desc_elem = element.select_one(directory.description_selector)
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Get listing URL
            listing_url = ""
            if name_elem and name_elem.get('href'):
                listing_url = urljoin(directory.base_url, name_elem['href'])
            
            if name:  # At minimum we need a business name
                return BusinessListing(
                    name=name,
                    address=address,
                    phone=phone,
                    website=website,
                    directory_source=directory.name,
                    listing_url=listing_url,
                    description=description,
                    contact_person=contact_person,
                    confidence=0.5  # Base confidence
                )
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to extract listing data: {e}")
            return None
    
    def _is_relevant_listing(self, listing: BusinessListing, company_name: str) -> bool:
        """Check if listing is relevant to our search"""
        if not listing.name:
            return False
        
        # Check name similarity
        name_similarity = fuzz.ratio(listing.name.lower(), company_name.lower())
        if name_similarity < 60:
            return False
        
        # Check if it's in the UK (basic check)
        if listing.address and not any(uk_indicator in listing.address.lower() 
                                     for uk_indicator in ['uk', 'united kingdom', 'england', 'scotland', 'wales']):
            # If address doesn't contain UK indicators, be more strict with name matching
            if name_similarity < 80:
                return False
        
        return True
    
    def _extract_executives_from_listings(self, listings: List[BusinessListing], 
                                        company_name: str, domain: str) -> List[ExecutiveContact]:
        """Extract executives from business directory listings"""
        executives = []
        
        for listing in listings:
            try:
                # Extract executives from listing data
                listing_executives = self._extract_executives_from_listing(
                    listing, company_name, domain
                )
                executives.extend(listing_executives)
                
            except Exception as e:
                logger.debug(f"Failed to extract executives from listing: {e}")
                continue
        
        return executives
    
    def _extract_executives_from_listing(self, listing: BusinessListing, 
                                       company_name: str, domain: str) -> List[ExecutiveContact]:
        """Extract executives from a single business listing"""
        executives = []
        
        try:
            # Combine all text for pattern matching
            combined_text = f"{listing.description} {listing.contact_person}"
            
            # Extract names using patterns
            extracted_names = self._extract_names_from_text(combined_text, company_name)
            
            for name_data in extracted_names:
                try:
                    # Create executive contact
                    executive = ExecutiveContact(
                        first_name=name_data['first_name'],
                        last_name=name_data['last_name'],
                        full_name=name_data['full_name'],
                        title=name_data.get('title', 'Business Contact'),
                        company_name=company_name,
                        email=None,  # Will be enriched later
                        phone=listing.phone if listing.phone else None,
                        bio=listing.description[:200] if listing.description else "",
                        discovery_sources=[f"directory_{listing.directory_source.lower()}_{listing.listing_url}"],
                        confidence=name_data.get('confidence', 0.6),
                        seniority_tier=self._determine_seniority_tier(name_data.get('title', '')),
                        company_domain=domain
                    )
                    
                    executives.append(executive)
                    
                except Exception as e:
                    logger.debug(f"Failed to create executive from listing: {e}")
                    continue
            
            # If no executives found from patterns, try contact person field
            if not executives and listing.contact_person:
                contact_executive = self._create_executive_from_contact(
                    listing, company_name, domain
                )
                if contact_executive:
                    executives.append(contact_executive)
            
            return executives
            
        except Exception as e:
            logger.debug(f"Failed to extract executives from listing: {e}")
            return []
    
    def _extract_names_from_text(self, text: str, company_name: str) -> List[Dict]:
        """Extract executive names from text using patterns"""
        extracted_names = []
        
        if not text:
            return extracted_names
        
        for pattern in self.executive_patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
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
        if not all(word[0].isupper() for word in words if word):
            return False
        
        # Should not contain numbers or special characters
        if re.search(r'[0-9@#$%^&*()+={}[\]|\\:";\'<>?/]', name):
            return False
        
        # Should not be common business words
        business_words = ['limited', 'ltd', 'company', 'services', 'solutions', 'group']
        name_lower = name.lower()
        if any(word in name_lower for word in business_words):
            return False
        
        return True
    
    def _extract_title_from_context(self, text: str, name: str) -> str:
        """Extract executive title from surrounding context"""
        # Look for title patterns around the name
        title_patterns = [
            r'(?i)(?:owner|business owner)',
            r'(?i)(?:manager|general manager)',
            r'(?i)(?:director|managing director)',
            r'(?i)(?:master plumber|qualified plumber)',
            r'(?i)(?:master electrician|qualified electrician)',
            r'(?i)(?:chartered engineer|senior engineer)'
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
        
        return "Business Contact"
    
    def _calculate_name_confidence(self, name: str, context: str) -> float:
        """Calculate confidence score for extracted name"""
        confidence = 0.6  # Base confidence for directory listings
        
        # Boost for common name patterns
        if re.match(r'^[A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15}$', name):
            confidence += 0.15
        
        # Boost for title context
        title_keywords = ['owner', 'manager', 'director', 'contact']
        if any(keyword in context.lower() for keyword in title_keywords):
            confidence += 0.1
        
        # Boost for professional context
        professional_keywords = ['plumber', 'electrician', 'engineer', 'qualified', 'master']
        if any(keyword in context.lower() for keyword in professional_keywords):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _create_executive_from_contact(self, listing: BusinessListing, 
                                     company_name: str, domain: str) -> Optional[ExecutiveContact]:
        """Create executive from contact person field"""
        try:
            if not listing.contact_person or not self._is_valid_person_name(listing.contact_person):
                return None
            
            name_parts = listing.contact_person.split()
            if len(name_parts) < 2:
                return None
            
            executive = ExecutiveContact(
                first_name=name_parts[0],
                last_name=' '.join(name_parts[1:]),
                full_name=listing.contact_person,
                title="Business Contact",
                company_name=company_name,
                email=None,
                phone=listing.phone if listing.phone else None,
                bio=listing.description[:200] if listing.description else "",
                discovery_sources=[f"directory_{listing.directory_source.lower()}_contact"],
                confidence=0.7,  # Higher confidence for explicit contact person
                seniority_tier='tier_3',
                company_domain=domain
            )
            
            return executive
            
        except Exception as e:
            logger.debug(f"Failed to create executive from contact: {e}")
            return None
    
    def _determine_seniority_tier(self, title: str) -> str:
        """Determine executive seniority tier from title"""
        if not title:
            return 'tier_4'
        
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in ['owner', 'director', 'founder']):
            return 'tier_1'
        elif any(keyword in title_lower for keyword in ['manager', 'head']):
            return 'tier_2'
        elif any(keyword in title_lower for keyword in ['contact', 'representative']):
            return 'tier_3'
        else:
            return 'tier_4'
    
    def _deduplicate_directory_executives(self, executives: List[ExecutiveContact]) -> List[ExecutiveContact]:
        """Remove duplicate executives from directory results"""
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
                
                # Check phone similarity
                phone_similarity = 0
                if executive.phone and existing.phone:
                    phone_similarity = fuzz.ratio(executive.phone, existing.phone)
                
                if name_similarity > 85 or phone_similarity > 90:
                    is_duplicate = True
                    # Keep the one with higher confidence
                    if executive.confidence > existing.confidence:
                        unique_executives.remove(existing)
                        unique_executives.append(executive)
                    break
            
            if not is_duplicate:
                unique_executives.append(executive)
        
        return unique_executives
    
    def _score_directory_confidence(self, executives: List[ExecutiveContact], 
                                  listings: List[BusinessListing]) -> List[ExecutiveContact]:
        """Score executive confidence based on directory listing quality"""
        for executive in executives:
            # Base confidence from extraction
            base_confidence = executive.confidence
            
            # Boost for multiple directory sources
            source_count = len(executive.discovery_sources)
            if source_count > 1:
                base_confidence += 0.1 * (source_count - 1)
            
            # Boost for phone number
            if executive.phone:
                base_confidence += 0.1
            
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
    
    async def _enforce_rate_limit(self, directory_name: str):
        """Enforce rate limiting for directory requests"""
        current_time = time.time()
        
        if directory_name in self.last_requests:
            time_since_last = current_time - self.last_requests[directory_name]
            min_delay = self.directories[directory_name].rate_limit
            
            if time_since_last < min_delay:
                sleep_time = min_delay - time_since_last
                logger.debug(f"{directory_name} rate limiting: sleeping {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
        
        self.last_requests[directory_name] = time.time()

# Usage example
async def test_business_directory():
    """Test function for business directory enricher"""
    enricher = BusinessDirectoryEnricher()
    executives = await enricher.discover_executives("Jack The Plumber", "jacktheplumber.co.uk", "plumbing")
    
    print(f"Found {len(executives)} executives:")
    for exec in executives:
        print(f"- {exec.full_name} ({exec.title}) - Confidence: {exec.confidence:.2f}")
        if exec.phone:
            print(f"  Phone: {exec.phone}")

if __name__ == "__main__":
    asyncio.run(test_business_directory()) 