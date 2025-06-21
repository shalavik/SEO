"""
Companies House API Integration - Phase 4B
Alternative data source for executive discovery
Provides director information from UK Companies House registry
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import aiohttp
import requests
from datetime import datetime, date
import json

logger = logging.getLogger(__name__)

@dataclass
class CompaniesHouseDirector:
    """Director information from Companies House"""
    name: str
    title: str = ""
    appointment_date: Optional[date] = None
    resignation_date: Optional[date] = None
    nationality: str = ""
    occupation: str = ""
    country_of_residence: str = ""
    date_of_birth: Optional[Dict[str, int]] = None  # {"month": 1, "year": 1980}
    address: Dict[str, str] = field(default_factory=dict)
    is_active: bool = True
    officer_role: str = ""
    links: Dict[str, str] = field(default_factory=dict)

@dataclass
class CompaniesHouseCompany:
    """Company information from Companies House"""
    company_number: str
    company_name: str
    company_status: str
    company_type: str
    incorporation_date: Optional[date] = None
    registered_office_address: Dict[str, str] = field(default_factory=dict)
    sic_codes: List[str] = field(default_factory=list)
    directors: List[CompaniesHouseDirector] = field(default_factory=list)
    website: str = ""
    phone: str = ""

class CompaniesHouseAPI:
    """Companies House API client for director discovery"""
    
    def __init__(self, api_key: Optional[str] = None):
        # Companies House provides a free API with rate limits
        # For production, you would need to register for an API key
        self.api_key = api_key or "dummy_key_for_testing"
        self.base_url = "https://api.company-information.service.gov.uk"
        self.session = None
        
        # Rate limiting
        self.rate_limit_delay = 0.6  # 100 requests per minute = 0.6s between requests
        self.last_request_time = 0
        
        # Cache for reducing API calls
        self.company_cache = {}
        self.director_cache = {}
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'Basic {self.api_key}',
                'Content-Type': 'application/json'
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def search_companies_by_name(self, company_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for companies by name"""
        await self._rate_limit()
        
        # Clean company name for search
        search_name = self._clean_company_name(company_name)
        
        url = f"{self.base_url}/search/companies"
        params = {
            'q': search_name,
            'items_per_page': limit
        }
        
        try:
            if self.session:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('items', [])
                    else:
                        logger.warning(f"Companies House search failed: {response.status}")
                        return []
            else:
                # Fallback to sync request
                response = requests.get(url, params=params, auth=(self.api_key, ''), timeout=30)
                if response.status_code == 200:
                    return response.json().get('items', [])
                else:
                    logger.warning(f"Companies House search failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Companies House search error: {e}")
            return []
    
    async def get_company_details(self, company_number: str) -> Optional[CompaniesHouseCompany]:
        """Get detailed company information including directors"""
        if company_number in self.company_cache:
            return self.company_cache[company_number]
        
        await self._rate_limit()
        
        url = f"{self.base_url}/company/{company_number}"
        
        try:
            if self.session:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        company = self._parse_company_data(data)
                        
                        # Get directors
                        directors = await self.get_company_directors(company_number)
                        company.directors = directors
                        
                        self.company_cache[company_number] = company
                        return company
                    else:
                        logger.warning(f"Company details failed: {response.status}")
                        return None
            else:
                response = requests.get(url, auth=(self.api_key, ''), timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    company = self._parse_company_data(data)
                    
                    # Get directors (sync)
                    directors = await self.get_company_directors(company_number)
                    company.directors = directors
                    
                    self.company_cache[company_number] = company
                    return company
                else:
                    logger.warning(f"Company details failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Company details error: {e}")
            return None
    
    async def get_company_directors(self, company_number: str) -> List[CompaniesHouseDirector]:
        """Get company directors"""
        if company_number in self.director_cache:
            return self.director_cache[company_number]
        
        await self._rate_limit()
        
        url = f"{self.base_url}/company/{company_number}/officers"
        
        try:
            if self.session:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        directors = self._parse_directors_data(data.get('items', []))
                        self.director_cache[company_number] = directors
                        return directors
                    else:
                        logger.warning(f"Directors request failed: {response.status}")
                        return []
            else:
                response = requests.get(url, auth=(self.api_key, ''), timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    directors = self._parse_directors_data(data.get('items', []))
                    self.director_cache[company_number] = directors
                    return directors
                else:
                    logger.warning(f"Directors request failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Directors request error: {e}")
            return []
    
    def _clean_company_name(self, company_name: str) -> str:
        """Clean company name for search"""
        # Remove common suffixes that might interfere with search
        suffixes_to_remove = [
            'ltd', 'limited', 'plc', 'llp', 'llc', 'inc', 'corp', 'co',
            'plumbing', 'services', 'heating', 'gas', 'solutions'
        ]
        
        cleaned = company_name.lower()
        for suffix in suffixes_to_remove:
            cleaned = cleaned.replace(suffix, '').strip()
        
        # Remove extra spaces
        cleaned = ' '.join(cleaned.split())
        
        return cleaned or company_name  # Fallback to original if cleaned is empty
    
    def _parse_company_data(self, data: Dict[str, Any]) -> CompaniesHouseCompany:
        """Parse company data from API response"""
        company = CompaniesHouseCompany(
            company_number=data.get('company_number', ''),
            company_name=data.get('company_name', ''),
            company_status=data.get('company_status', ''),
            company_type=data.get('type', ''),
            sic_codes=data.get('sic_codes', [])
        )
        
        # Parse incorporation date
        if 'date_of_creation' in data:
            try:
                company.incorporation_date = datetime.strptime(
                    data['date_of_creation'], '%Y-%m-%d'
                ).date()
            except:
                pass
        
        # Parse registered office address
        if 'registered_office_address' in data:
            company.registered_office_address = data['registered_office_address']
        
        return company
    
    def _parse_directors_data(self, items: List[Dict[str, Any]]) -> List[CompaniesHouseDirector]:
        """Parse directors data from API response"""
        directors = []
        
        for item in items:
            # Only include active directors
            if item.get('resigned_on'):
                continue
            
            director = CompaniesHouseDirector(
                name=item.get('name', ''),
                title=item.get('officer_role', ''),
                nationality=item.get('nationality', ''),
                occupation=item.get('occupation', ''),
                country_of_residence=item.get('country_of_residence', ''),
                officer_role=item.get('officer_role', ''),
                is_active=not bool(item.get('resigned_on')),
                links=item.get('links', {})
            )
            
            # Parse appointment date
            if 'appointed_on' in item:
                try:
                    director.appointment_date = datetime.strptime(
                        item['appointed_on'], '%Y-%m-%d'
                    ).date()
                except:
                    pass
            
            # Parse date of birth (partial)
            if 'date_of_birth' in item:
                director.date_of_birth = item['date_of_birth']
            
            # Parse address
            if 'address' in item:
                director.address = item['address']
            
            directors.append(director)
        
        return directors
    
    async def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()

class CompaniesHouseExecutiveExtractor:
    """Extract executives from Companies House data"""
    
    def __init__(self):
        self.api = CompaniesHouseAPI()
    
    async def find_executives_by_company_name(self, company_name: str) -> List[CompaniesHouseDirector]:
        """Find company executives using Companies House API"""
        logger.info(f"🏢 Searching Companies House for: {company_name}")
        
        try:
            async with self.api:
                # Search for companies
                companies = await self.api.search_companies_by_name(company_name, limit=5)
                
                if not companies:
                    logger.info(f"No companies found for: {company_name}")
                    return []
                
                # Find best match
                best_match = self._find_best_company_match(companies, company_name)
                
                if not best_match:
                    logger.info(f"No good match found for: {company_name}")
                    return []
                
                company_number = best_match['company_number']
                logger.info(f"Found company match: {best_match['title']} ({company_number})")
                
                # Get company details with directors
                company_details = await self.api.get_company_details(company_number)
                
                if company_details and company_details.directors:
                    logger.info(f"Found {len(company_details.directors)} directors")
                    return company_details.directors
                else:
                    logger.info("No directors found")
                    return []
                    
        except Exception as e:
            logger.error(f"Companies House extraction failed: {e}")
            return []
    
    def _find_best_company_match(self, companies: List[Dict[str, Any]], 
                                target_name: str) -> Optional[Dict[str, Any]]:
        """Find the best matching company"""
        target_lower = target_name.lower()
        best_match = None
        best_score = 0
        
        for company in companies:
            company_title = company.get('title', '').lower()
            
            # Calculate similarity score
            score = self._calculate_name_similarity(company_title, target_lower)
            
            # Prefer active companies
            if company.get('company_status') == 'active':
                score += 0.2
            
            # Prefer companies with plumbing-related SIC codes
            if self._has_plumbing_sic_codes(company):
                score += 0.1
            
            if score > best_score:
                best_score = score
                best_match = company
        
        # Only return if we have a reasonably good match
        return best_match if best_score > 0.5 else None
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between company names"""
        # Simple word overlap calculation
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _has_plumbing_sic_codes(self, company: Dict[str, Any]) -> bool:
        """Check if company has plumbing-related SIC codes"""
        plumbing_sic_codes = [
            '43220',  # Plumbing, heat and air-conditioning installation
            '43290',  # Other construction installation
            '95250',  # Repair of watches, clocks and jewellery
        ]
        
        company_sic_codes = company.get('sic_codes', [])
        return any(code in plumbing_sic_codes for code in company_sic_codes)

# Convenience function for testing
async def test_companies_house_integration(company_names: List[str]) -> Dict[str, Any]:
    """Test Companies House integration"""
    extractor = CompaniesHouseExecutiveExtractor()
    results = {}
    
    for company_name in company_names:
        logger.info(f"Testing: {company_name}")
        directors = await extractor.find_executives_by_company_name(company_name)
        results[company_name] = {
            'directors_found': len(directors),
            'directors': [
                {
                    'name': d.name,
                    'title': d.title,
                    'officer_role': d.officer_role,
                    'nationality': d.nationality,
                    'occupation': d.occupation
                }
                for d in directors
            ]
        }
    
    return results 