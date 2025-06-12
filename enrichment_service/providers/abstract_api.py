"""
Abstract API Provider for Company Data Enrichment

Provides company data enrichment using Abstract API's Company Enrichment service.
Implements caching to SQLite to avoid duplicate API calls and preserve credits.
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
    CompanyTechnology, CompanySocial, ProviderResponse
)

class AbstractAPIProvider:
    """Abstract API provider for company data enrichment"""
    
    def __init__(self, api_key: str, cache_db_path: str = "enrichment_cache.db", 
                 cache_ttl_days: int = 30):
        self.api_key = api_key
        self.base_url = "https://api.abstractapi.com/v1/company"
        self.cache_db_path = cache_db_path
        self.cache_ttl_days = cache_ttl_days
        self._init_cache_db()
        
    def _init_cache_db(self):
        """Initialize SQLite cache database"""
        Path(self.cache_db_path).parent.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS abstract_cache (
                    id TEXT PRIMARY KEY,
                    domain TEXT NOT NULL,
                    company_name TEXT,
                    response_data TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            
            # Create index for faster lookups
            conn.execute("CREATE INDEX IF NOT EXISTS idx_domain ON abstract_cache(domain)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON abstract_cache(expires_at)")
            
    def _get_cache_key(self, domain: str, company_name: Optional[str] = None) -> str:
        """Generate cache key for request"""
        key_data = f"{domain}:{company_name or ''}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_response(self, domain: str, company_name: Optional[str] = None) -> Optional[Dict]:
        """Retrieve cached response if available and not expired"""
        cache_key = self._get_cache_key(domain, company_name)
        
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT response_data, success, error_message 
                FROM abstract_cache 
                WHERE id = ? AND expires_at > ?
            """, (cache_key, datetime.utcnow()))
            
            row = cursor.fetchone()
            if row:
                try:
                    return {
                        'data': json.loads(row['response_data']) if row['success'] else None,
                        'success': bool(row['success']),
                        'error': row['error_message']
                    }
                except json.JSONDecodeError:
                    # Invalid cached data, will re-fetch
                    pass
        
        return None
    
    def _cache_response(self, domain: str, company_name: Optional[str], 
                       response_data: Dict, success: bool, error: Optional[str] = None):
        """Cache API response"""
        cache_key = self._get_cache_key(domain, company_name)
        expires_at = datetime.utcnow() + timedelta(days=self.cache_ttl_days)
        
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO abstract_cache 
                (id, domain, company_name, response_data, success, error_message, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cache_key, domain, company_name,
                json.dumps(response_data) if response_data else "",
                success, error,
                datetime.utcnow(), expires_at
            ))
    
    def _cleanup_expired_cache(self):
        """Remove expired cache entries"""
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute("DELETE FROM abstract_cache WHERE expires_at < ?", (datetime.utcnow(),))
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _make_api_request(self, domain: str, company_name: Optional[str] = None) -> Dict:
        """Make API request to Abstract with retries"""
        params = {
            "api_key": self.api_key,
            "domain": domain
        }
        
        if company_name:
            params["company_name"] = company_name
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                return {
                    'data': data,
                    'success': True,
                    'error': None
                }
                
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
                return {
                    'data': None,
                    'success': False,
                    'error': error_msg
                }
            except Exception as e:
                return {
                    'data': None,
                    'success': False,
                    'error': str(e)
                }
    
    async def enrich_company(self, domain: str, company_name: Optional[str] = None) -> ProviderResponse:
        """Enrich company data using Abstract API"""
        start_time = datetime.utcnow()
        
        # Check cache first
        cached = self._get_cached_response(domain, company_name)
        if cached:
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return ProviderResponse(
                provider="abstract_api",
                success=cached['success'],
                data=cached['data'],
                error=cached['error'],
                credits_used=0,  # No credits used for cached response
                response_time_ms=processing_time
            )
        
        # Make API request
        result = await self._make_api_request(domain, company_name)
        
        # Cache the response
        self._cache_response(domain, company_name, result['data'], result['success'], result['error'])
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return ProviderResponse(
            provider="abstract_api",
            success=result['success'],
            data=result['data'],
            error=result['error'],
            credits_used=1 if result['success'] else 0,
            response_time_ms=processing_time
        )
    
    def _parse_abstract_response(self, data: Dict) -> CompanyEnrichment:
        """Parse Abstract API response into our CompanyEnrichment model"""
        if not data:
            return CompanyEnrichment(confidence=0.0)
        
        # Extract basic company info
        company_name = data.get('name', '')
        legal_name = data.get('legal_name', company_name)
        description = data.get('description', '')
        industry = data.get('industry', '')
        
        # Employee count and size
        employee_count = data.get('employees_count')
        employee_range = data.get('employees_range', '')
        size_category = self._determine_size_category(employee_count, employee_range)
        
        # Financial data
        financials = None
        if data.get('revenue') or data.get('funding'):
            financials = CompanyFinancials(
                annual_revenue=data.get('revenue'),
                revenue_range=data.get('revenue_range'),
                funding_total=data.get('funding', {}).get('total_amount'),
                last_funding_round=data.get('funding', {}).get('last_round_type'),
                last_funding_date=self._parse_date(data.get('funding', {}).get('last_round_date'))
            )
        
        # Technology stack
        tech_data = data.get('technologies', {})
        technology = CompanyTechnology(
            technologies=tech_data.get('all', []),
            cms=tech_data.get('cms'),
            ecommerce_platform=tech_data.get('ecommerce'),
            analytics_tools=tech_data.get('analytics', []),
            marketing_tools=tech_data.get('marketing', [])
        )
        
        # Social media
        social_data = data.get('social_media', {})
        social = CompanySocial(
            linkedin_url=social_data.get('linkedin'),
            twitter_handle=social_data.get('twitter'),
            facebook_url=social_data.get('facebook')
        )
        
        # Address
        address = None
        if data.get('address'):
            addr_data = data['address']
            address = {
                'street': addr_data.get('street'),
                'city': addr_data.get('city'),
                'region': addr_data.get('region'),
                'postal_code': addr_data.get('postal_code'),
                'country': addr_data.get('country')
            }
        
        # Calculate confidence based on data completeness
        confidence = self._calculate_confidence(data)
        
        return CompanyEnrichment(
            legal_name=legal_name,
            trading_names=[company_name] if company_name != legal_name else [],
            description=description,
            industry=industry,
            employee_count=employee_count,
            employee_range=employee_range,
            size_category=size_category,
            founded_year=data.get('founded_year'),
            phone=data.get('phone'),
            address=address,
            financials=financials,
            technology=technology,
            social=social,
            confidence=confidence
        )
    
    def _determine_size_category(self, employee_count: Optional[int], 
                                employee_range: str) -> Optional[CompanySize]:
        """Determine company size category from employee data"""
        if employee_count:
            if employee_count < 10:
                return CompanySize.MICRO
            elif employee_count < 50:
                return CompanySize.SMALL
            elif employee_count < 250:
                return CompanySize.MEDIUM
            elif employee_count < 1000:
                return CompanySize.LARGE
            else:
                return CompanySize.ENTERPRISE
        
        # Fallback to range parsing
        if employee_range:
            range_lower = employee_range.lower()
            if '1-9' in range_lower or 'micro' in range_lower:
                return CompanySize.MICRO
            elif '10-49' in range_lower or '10-50' in range_lower:
                return CompanySize.SMALL
            elif '50-249' in range_lower or '50-250' in range_lower:
                return CompanySize.MEDIUM
            elif '250-999' in range_lower or 'large' in range_lower:
                return CompanySize.LARGE
            elif '1000+' in range_lower or 'enterprise' in range_lower:
                return CompanySize.ENTERPRISE
        
        return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None
        
        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        except Exception:
            pass
        
        return None
    
    def _calculate_confidence(self, data: Dict) -> float:
        """Calculate confidence score based on data completeness"""
        total_fields = 0
        filled_fields = 0
        
        # Core fields (higher weight)
        core_fields = ['name', 'industry', 'description', 'employees_count']
        for field in core_fields:
            total_fields += 2  # Double weight for core fields
            if data.get(field):
                filled_fields += 2
        
        # Additional fields
        additional_fields = ['phone', 'address', 'founded_year', 'revenue', 'social_media', 'technologies']
        for field in additional_fields:
            total_fields += 1
            if data.get(field):
                filled_fields += 1
        
        return min(filled_fields / total_fields, 1.0) if total_fields > 0 else 0.0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    COUNT(CASE WHEN success = 1 THEN 1 END) as successful_entries,
                    COUNT(CASE WHEN expires_at > ? THEN 1 END) as active_entries
                FROM abstract_cache
            """, (datetime.utcnow(),))
            
            stats = cursor.fetchone()
            
            return {
                'total_cached_entries': stats[0],
                'successful_entries': stats[1],
                'active_entries': stats[2],
                'cache_hit_potential': f"{(stats[2] / max(stats[0], 1)) * 100:.1f}%"
            }
    
    async def clear_cache(self, expired_only: bool = True):
        """Clear cache entries"""
        with sqlite3.connect(self.cache_db_path) as conn:
            if expired_only:
                conn.execute("DELETE FROM abstract_cache WHERE expires_at < ?", (datetime.utcnow(),))
            else:
                conn.execute("DELETE FROM abstract_cache")
    
    async def enrichment_from_response(self, response: ProviderResponse) -> Optional[CompanyEnrichment]:
        """Convert provider response to CompanyEnrichment"""
        if not response.success or not response.data:
            return None
        
        return self._parse_abstract_response(response.data) 