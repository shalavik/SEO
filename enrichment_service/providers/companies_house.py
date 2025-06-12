"""
Companies House API Integration

Free UK government API for official company and director information.
Rate limit: 600 requests per 5 minutes.
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from urllib.parse import quote

from ..core.director_models import (
    Director, DirectorRole, Address, DataSource, FreeDataBundle
)

logger = logging.getLogger(__name__)


class CompaniesHouseAPI:
    """Companies House API client for director lookup"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.company-information.service.gov.uk"
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = asyncio.Semaphore(10)  # 10 concurrent requests
        
    async def __aenter__(self):
        """Async context manager entry"""
        auth = aiohttp.BasicAuth(self.api_key, '')
        self.session = aiohttp.ClientSession(
            auth=auth,
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'UK-SEO-Lead-Generator/1.0',
                'Accept': 'application/json'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def search_companies(self, company_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for companies by name"""
        async with self.rate_limiter:
            url = f"{self.base_url}/search/companies"
            params = {
                'q': company_name,
                'items_per_page': limit
            }
            
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('items', [])
                    else:
                        logger.warning(f"Companies House search failed: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Error searching companies: {e}")
                return []
    
    async def get_company_profile(self, company_number: str) -> Optional[Dict[str, Any]]:
        """Get detailed company profile"""
        async with self.rate_limiter:
            url = f"{self.base_url}/company/{company_number}"
            
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Company profile fetch failed: {response.status}")
                        return None
            except Exception as e:
                logger.error(f"Error fetching company profile: {e}")
                return None
    
    async def get_company_officers(self, company_number: str) -> List[Dict[str, Any]]:
        """Get company officers (directors)"""
        async with self.rate_limiter:
            url = f"{self.base_url}/company/{company_number}/officers"
            params = {'items_per_page': 35}  # Max allowed
            
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('items', [])
                    else:
                        logger.warning(f"Officers fetch failed: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Error fetching officers: {e}")
                return []


class CompaniesHouseService:
    """Service for director lookup via Companies House"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def _parse_director_role(self, officer_role: str) -> DirectorRole:
        """Parse officer role to standard director role"""
        role_mapping = {
            'director': DirectorRole.DIRECTOR,
            'ceo': DirectorRole.CEO,
            'chief-executive-officer': DirectorRole.CEO,
            'managing-director': DirectorRole.MANAGING_DIRECTOR,
            'executive-director': DirectorRole.EXECUTIVE_DIRECTOR,
            'non-executive-director': DirectorRole.NON_EXECUTIVE_DIRECTOR,
            'chairman': DirectorRole.CHAIRMAN,
            'chairwoman': DirectorRole.CHAIRMAN,
            'chief-financial-officer': DirectorRole.CHIEF_FINANCIAL_OFFICER,
            'chief-operating-officer': DirectorRole.CHIEF_OPERATING_OFFICER,
        }
        
        role_lower = officer_role.lower().replace(' ', '-')
        return role_mapping.get(role_lower, DirectorRole.DIRECTOR)
    
    def _parse_address(self, address_data: Dict[str, Any]) -> Optional[Address]:
        """Parse address from Companies House data"""
        if not address_data:
            return None
            
        return Address(
            line1=address_data.get('address_line_1'),
            line2=address_data.get('address_line_2'),
            city=address_data.get('locality'),
            county=address_data.get('region'),
            postcode=address_data.get('postal_code'),
            country=address_data.get('country')
        )
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
            
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(date_str, '%Y-%m').date()
            except ValueError:
                logger.warning(f"Could not parse date: {date_str}")
                return None
    
    def _parse_director(self, officer_data: Dict[str, Any], company_number: str) -> Director:
        """Parse officer data to Director object"""
        name = officer_data.get('name', '')
        
        # Extract first and last name
        first_name = None
        last_name = None
        if ',' in name:
            # Format: "SMITH, John"
            parts = name.split(',', 1)
            last_name = parts[0].strip().title()
            first_name = parts[1].strip().title() if len(parts) > 1 else None
        else:
            # Format: "John Smith"
            parts = name.split()
            if len(parts) >= 2:
                first_name = parts[0].title()
                last_name = ' '.join(parts[1:]).title()
            else:
                last_name = name.title()
        
        # Parse role
        role = self._parse_director_role(officer_data.get('officer_role', 'director'))
        
        # Parse dates
        appointment_date = self._parse_date(officer_data.get('appointed_on'))
        resignation_date = self._parse_date(officer_data.get('resigned_on'))
        
        # Parse address
        address = self._parse_address(officer_data.get('address'))
        
        # Determine if active
        is_active = resignation_date is None
        
        return Director(
            full_name=name.title(),
            first_name=first_name,
            last_name=last_name,
            role=role,
            company_number=company_number,
            appointment_date=appointment_date,
            resignation_date=resignation_date,
            nationality=officer_data.get('nationality'),
            occupation=officer_data.get('occupation'),
            address=address,
            is_active=is_active
        )
    
    def _filter_active_directors(self, directors: List[Director]) -> List[Director]:
        """Filter for active directors only"""
        return [d for d in directors if d.is_active]
    
    def _prioritize_directors(self, directors: List[Director]) -> List[Director]:
        """Sort directors by importance (CEO, MD, Directors)"""
        role_priority = {
            DirectorRole.CEO: 1,
            DirectorRole.MANAGING_DIRECTOR: 2,
            DirectorRole.EXECUTIVE_DIRECTOR: 3,
            DirectorRole.CHAIRMAN: 4,
            DirectorRole.CHIEF_FINANCIAL_OFFICER: 5,
            DirectorRole.CHIEF_OPERATING_OFFICER: 6,
            DirectorRole.DIRECTOR: 7,
            DirectorRole.NON_EXECUTIVE_DIRECTOR: 8
        }
        
        return sorted(directors, key=lambda d: role_priority.get(d.role, 9))
    
    async def find_company_directors(self, company_name: str) -> FreeDataBundle:
        """Find directors for a company"""
        start_time = datetime.now()
        directors = []
        errors = []
        
        try:
            async with CompaniesHouseAPI(self.api_key) as api:
                # Search for company
                companies = await api.search_companies(company_name, limit=5)
                
                if not companies:
                    errors.append(f"No companies found for '{company_name}'")
                    return FreeDataBundle(
                        directors=[],
                        processing_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                        sources_used=[DataSource.COMPANIES_HOUSE],
                        errors=errors
                    )
                
                # Try to find exact or close match
                best_match = None
                for company in companies:
                    if company.get('title', '').lower() == company_name.lower():
                        best_match = company
                        break
                
                if not best_match:
                    # Use first result if no exact match
                    best_match = companies[0]
                    logger.info(f"Using closest match: {best_match.get('title')} for '{company_name}'")
                
                company_number = best_match.get('company_number')
                if not company_number:
                    errors.append("No company number found")
                    return FreeDataBundle(
                        directors=[],
                        processing_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                        sources_used=[DataSource.COMPANIES_HOUSE],
                        errors=errors
                    )
                
                # Get officers
                officers = await api.get_company_officers(company_number)
                
                if not officers:
                    errors.append(f"No officers found for company {company_number}")
                    return FreeDataBundle(
                        directors=[],
                        processing_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                        sources_used=[DataSource.COMPANIES_HOUSE],
                        errors=errors
                    )
                
                # Parse directors
                all_directors = [
                    self._parse_director(officer, company_number)
                    for officer in officers
                ]
                
                # Filter and prioritize
                active_directors = self._filter_active_directors(all_directors)
                directors = self._prioritize_directors(active_directors)
                
                logger.info(f"Found {len(directors)} active directors for {company_name}")
                
        except Exception as e:
            logger.error(f"Error in Companies House lookup: {e}")
            errors.append(str(e))
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return FreeDataBundle(
            directors=directors,
            processing_time_ms=processing_time,
            sources_used=[DataSource.COMPANIES_HOUSE],
            errors=errors
        )
    
    async def get_director_by_company_number(self, company_number: str) -> FreeDataBundle:
        """Get directors by company number directly"""
        start_time = datetime.now()
        directors = []
        errors = []
        
        try:
            async with CompaniesHouseAPI(self.api_key) as api:
                officers = await api.get_company_officers(company_number)
                
                if officers:
                    all_directors = [
                        self._parse_director(officer, company_number)
                        for officer in officers
                    ]
                    
                    active_directors = self._filter_active_directors(all_directors)
                    directors = self._prioritize_directors(active_directors)
                    
                    logger.info(f"Found {len(directors)} directors for company {company_number}")
                else:
                    errors.append(f"No officers found for company {company_number}")
                    
        except Exception as e:
            logger.error(f"Error fetching directors by company number: {e}")
            errors.append(str(e))
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return FreeDataBundle(
            directors=directors,
            processing_time_ms=processing_time,
            sources_used=[DataSource.COMPANIES_HOUSE],
            errors=errors
        ) 