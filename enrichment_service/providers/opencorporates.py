"""
OpenCorporates Provider for UK/EU Company Data

Provides official company registration data using OpenCorporates API
for UK Companies House and EU company registries.
"""

import asyncio
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from enrichment_service.core.models import (
    CompanyEnrichment, CompanySize, CompanyFinancials, 
    ProviderResponse
)

class OpenCorporatesProvider:
    """OpenCorporates provider for official company data"""
    
    def __init__(self, api_key: Optional[str] = None, cache_db_path: str = "enrichment_cache.db", 
                 cache_ttl_days: int = 90):  # Longer cache for official data
        self.api_key = api_key
        self.base_url = "https://api.opencorporates.com/v0.1"
        self.cache_db_path = cache_db_path
        self.cache_ttl_days = cache_ttl_days
        self._init_cache_db()
        
        # UK-specific endpoints
        self.uk_search_url = f"{self.base_url}/companies/search"
        self.uk_company_url = f"{self.base_url}/companies/gb"
        
    def _init_cache_db(self):
        """Initialize SQLite cache database"""
        Path(self.cache_db_path).parent.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS opencorporates_cache (
                    id TEXT PRIMARY KEY,
                    search_term TEXT NOT NULL,
                    search_type TEXT NOT NULL,
                    company_number TEXT,
                    jurisdiction TEXT,
                    response_data TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_oc_search ON opencorporates_cache(search_term, search_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_oc_expires ON opencorporates_cache(expires_at)")
    
    async def enrich_company(self, company_name: str, 
                           company_number: Optional[str] = None,
                           jurisdiction: str = 'gb') -> ProviderResponse:
        """Enrich company data using OpenCorporates"""
        
        # If we have company number, use it directly
        if company_number:
            return await self.get_company_by_number(company_number, jurisdiction)
        
        # Otherwise, search by name first
        search_result = await self.search_company_by_name(company_name, jurisdiction)
        
        if not search_result.success or not search_result.data:
            return search_result
        
        # Extract company number from search results
        companies = search_result.data.get('results', {}).get('companies', [])
        if not companies:
            return ProviderResponse(
                provider="opencorporates",
                success=False,
                data=None,
                error="No companies found in search results",
                credits_used=search_result.credits_used,
                response_time_ms=search_result.response_time_ms
            )
        
        # Get detailed data for the best match
        best_match = companies[0].get('company', {})
        found_company_number = best_match.get('company_number')
        found_jurisdiction = best_match.get('jurisdiction_code', jurisdiction)
        
        if found_company_number:
            detail_result = await self.get_company_by_number(found_company_number, found_jurisdiction)
            # Combine credits used
            detail_result.credits_used += search_result.credits_used
            return detail_result
        
        # Return search result if no company number found
        return search_result
    
    async def enrichment_from_response(self, response: ProviderResponse) -> Optional[CompanyEnrichment]:
        """Convert provider response to CompanyEnrichment"""
        if not response.success or not response.data:
            return None
        
        return self._parse_opencorporates_response(response.data)
    
    def _parse_opencorporates_response(self, data: Dict) -> CompanyEnrichment:
        """Parse OpenCorporates response into our CompanyEnrichment model"""
        if not data:
            return CompanyEnrichment(confidence=0.0)
        
        # Handle both search results and detailed company data
        company_data = None
        if 'results' in data and 'companies' in data['results']:
            # Search result format
            companies = data['results']['companies']
            if companies:
                company_data = companies[0].get('company', {})
        elif 'results' in data and 'company' in data['results']:
            # Detail result format
            company_data = data['results']['company']
        elif 'company' in data:
            # Direct company data
            company_data = data['company']
        
        if not company_data:
            return CompanyEnrichment(confidence=0.0)
        
        # Extract basic info
        legal_name = company_data.get('name', '')
        company_number = company_data.get('company_number', '')
        
        # Calculate confidence
        confidence = self._calculate_oc_confidence(company_data)
        
        return CompanyEnrichment(
            company_number=company_number,
            legal_name=legal_name,
            confidence=confidence
        ) 