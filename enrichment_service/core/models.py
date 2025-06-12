"""
Core data models for Lead Enrichment Service

Pydantic schemas for lead enrichment pipeline with Hunter.io/Clearbit/Apollo.io style functionality.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, HttpUrl, Field, validator
from decimal import Decimal

class EnrichmentStatus(str, Enum):
    """Enrichment processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    ENRICHED = "enriched"
    FAILED = "failed"
    PARTIAL = "partial"

class CompanySize(str, Enum):
    """Company size categories"""
    MICRO = "micro"      # 1-9 employees
    SMALL = "small"      # 10-49 employees  
    MEDIUM = "medium"    # 50-249 employees
    LARGE = "large"      # 250+ employees
    ENTERPRISE = "enterprise"  # 1000+ employees

class SeniorityLevel(str, Enum):
    """Contact seniority levels"""
    C_LEVEL = "c_level"          # CEO, CTO, CFO, etc.
    VP_LEVEL = "vp_level"        # VP, SVP, EVP
    DIRECTOR = "director"        # Director level
    MANAGER = "manager"          # Manager level
    SENIOR = "senior"            # Senior individual contributor
    INDIVIDUAL = "individual"     # Individual contributor
    UNKNOWN = "unknown"

class ConfidenceLevel(str, Enum):
    """Confidence levels for enriched data"""
    HIGH = "high"      # 90-100%
    MEDIUM = "medium"  # 70-89%
    LOW = "low"        # 50-69%
    VERY_LOW = "very_low"  # <50%

# Input Models
class EnrichmentInput(BaseModel):
    """Input lead data for enrichment"""
    company_name: str
    website: Optional[HttpUrl] = None
    domain: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    sector: Optional[str] = None
    existing_contact: Optional[Dict[str, Any]] = None
    
    @validator('domain', pre=True)
    def extract_domain_from_website(cls, v, values):
        """Extract domain from website if not provided"""
        if not v and 'website' in values and values['website']:
            from urllib.parse import urlparse
            parsed = urlparse(str(values['website']))
            return parsed.netloc.lower()
        return v

# Company Enrichment Models
class CompanyFinancials(BaseModel):
    """Company financial information"""
    annual_revenue: Optional[str] = None
    revenue_range: Optional[str] = None
    funding_total: Optional[str] = None
    last_funding_round: Optional[str] = None
    last_funding_date: Optional[datetime] = None
    market_cap: Optional[str] = None

class CompanyTechnology(BaseModel):
    """Company technology stack"""
    technologies: List[str] = []
    cms: Optional[str] = None
    ecommerce_platform: Optional[str] = None
    analytics_tools: List[str] = []
    marketing_tools: List[str] = []
    
class CompanySocial(BaseModel):
    """Company social media presence"""
    linkedin_url: Optional[HttpUrl] = None
    twitter_handle: Optional[str] = None
    facebook_url: Optional[HttpUrl] = None
    instagram_handle: Optional[str] = None
    youtube_url: Optional[HttpUrl] = None
    
class CompanyEnrichment(BaseModel):
    """Enriched company information"""
    company_number: Optional[str] = None  # UK Companies House number
    legal_name: Optional[str] = None
    trading_names: List[str] = []
    description: Optional[str] = None
    industry: Optional[str] = None
    sic_codes: List[str] = []
    employee_count: Optional[int] = None
    employee_range: Optional[str] = None
    size_category: Optional[CompanySize] = None
    founded_year: Optional[int] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    financials: Optional[CompanyFinancials] = None
    technology: Optional[CompanyTechnology] = None
    social: Optional[CompanySocial] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Contact Enrichment Models
class ContactPersonal(BaseModel):
    """Personal contact information"""
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    title: Optional[str] = None
    gender: Optional[str] = None
    age_range: Optional[str] = None

class ContactProfessional(BaseModel):
    """Professional contact information"""
    current_role: Optional[str] = None
    department: Optional[str] = None
    seniority_level: Optional[SeniorityLevel] = None
    years_in_role: Optional[int] = None
    years_at_company: Optional[int] = None
    previous_companies: List[str] = []
    skills: List[str] = []
    
class ContactSocial(BaseModel):
    """Contact social media profiles"""
    linkedin_url: Optional[HttpUrl] = None
    twitter_handle: Optional[str] = None
    github_username: Optional[str] = None
    
class EmailValidation(BaseModel):
    """Email validation results"""
    is_valid: bool
    is_deliverable: bool
    is_risky: bool
    validation_method: str  # smtp, syntax, domain, etc.
    mx_records: bool = False
    catch_all: Optional[bool] = None
    disposable: bool = False
    role_account: bool = False
    
class ContactEnrichment(BaseModel):
    """Enriched contact information"""
    personal: ContactPersonal
    professional: Optional[ContactProfessional] = None
    social: Optional[ContactSocial] = None
    email: Optional[str] = None
    email_validation: Optional[EmailValidation] = None
    phone: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    data_sources: List[str] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Email Discovery Models
class EmailPattern(BaseModel):
    """Email pattern for domain"""
    pattern: str  # e.g., "first.last", "first", "firstl", etc.
    confidence: float = Field(ge=0.0, le=1.0)
    examples: List[str] = []
    
class EmailDiscovery(BaseModel):
    """Email discovery results for a domain"""
    domain: str
    patterns: List[EmailPattern] = []
    catch_all: Optional[bool] = None
    mx_records: List[str] = []
    common_emails: List[str] = []
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    
class EmailCandidate(BaseModel):
    """Potential email candidate"""
    email: str
    pattern_used: str
    confidence: float = Field(ge=0.0, le=1.0)
    validation: Optional[EmailValidation] = None
    source: str  # pattern, verification, etc.

# Enrichment Results
class EnrichmentResult(BaseModel):
    """Complete enrichment result"""
    input_data: EnrichmentInput
    company_enrichment: Optional[CompanyEnrichment] = None
    contact_enrichments: List[ContactEnrichment] = []
    email_discovery: Optional[EmailDiscovery] = None
    email_candidates: List[EmailCandidate] = []
    status: EnrichmentStatus
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.0)
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    data_sources_used: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Integration with existing SEO lead structure
class EnrichedLead(BaseModel):
    """Extended lead with enrichment data"""
    lead_id: str
    company: Dict[str, Any]  # Original company data
    contact: Dict[str, Any]  # Original contact data
    seo_analysis: Dict[str, Any]  # Original SEO data
    lead_qualification: Dict[str, Any]  # Original qualification
    outreach_intelligence: Dict[str, Any]  # Original outreach
    metadata: Dict[str, Any]  # Original metadata
    
    # Enrichment additions
    enrichment_result: Optional[EnrichmentResult] = None
    enrichment_status: EnrichmentStatus = EnrichmentStatus.PENDING
    enrichment_timestamp: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Batch processing models
class EnrichmentBatch(BaseModel):
    """Batch enrichment request"""
    batch_id: str
    leads: List[EnrichmentInput]
    options: Dict[str, Any] = {}
    priority: int = Field(ge=1, le=10, default=5)
    webhook_url: Optional[HttpUrl] = None
    
class BatchResult(BaseModel):
    """Batch enrichment results"""
    batch_id: str
    total_leads: int
    processed: int
    successful: int
    failed: int
    results: List[EnrichmentResult]
    processing_time_ms: int
    started_at: datetime
    completed_at: Optional[datetime] = None

# Provider Models
class ProviderCredits(BaseModel):
    """Provider API credits/usage"""
    provider: str
    credits_remaining: Optional[int] = None
    credits_used: int = 0
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None
    
class ProviderResponse(BaseModel):
    """Generic provider API response"""
    provider: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    credits_used: int = 0
    response_time_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow) 