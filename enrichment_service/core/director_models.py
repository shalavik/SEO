"""
Director-focused enrichment data models

Specialized models for targeting company directors and decision-makers
with cost-optimized enrichment strategies.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field, HttpUrl


class DirectorRole(str, Enum):
    """Standard director roles"""
    CEO = "ceo"
    MANAGING_DIRECTOR = "managing-director"
    DIRECTOR = "director"
    EXECUTIVE_DIRECTOR = "executive-director"
    NON_EXECUTIVE_DIRECTOR = "non-executive-director"
    CHAIRMAN = "chairman"
    CHIEF_FINANCIAL_OFFICER = "cfo"
    CHIEF_OPERATING_OFFICER = "coo"


class EnrichmentTier(str, Enum):
    """Lead enrichment tiers based on qualification scores"""
    TIER_A = "A"  # Hot leads (≥80 score) - Full budget £5.00
    TIER_B = "B"  # Warm leads (≥60 score) - Limited budget £2.00
    TIER_C = "C"  # Qualified leads (<60 score) - Free only
    TIER_D = "D"  # Low priority - Free only


class DataSource(str, Enum):
    """Available data sources for enrichment"""
    COMPANIES_HOUSE = "companies_house"
    OPENCORPORATES = "opencorporates"
    LINKEDIN_SCRAPER = "linkedin_scraper"
    PUBLIC_REGISTRIES = "public_registries"
    ABSTRACT_API = "abstract_api"
    HUNTER_IO = "hunter_io"
    EMAIL_VERIFICATION = "email_verification"


@dataclass
class EnrichmentDecision:
    """Decision on how to enrich a specific lead"""
    tier: EnrichmentTier
    budget: float
    priority: str
    allowed_sources: List[DataSource]
    max_processing_time: int
    estimated_cost: float = 0.0


class Address(BaseModel):
    """Address information"""
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None


class EmailCandidate(BaseModel):
    """Email candidate with confidence scoring"""
    email: str
    confidence: float = Field(ge=0.0, le=1.0)
    source: DataSource
    pattern_type: str  # "first.last", "first", "director", etc.
    verified: bool = False
    verification_result: Optional[str] = None


class VerifiedEmail(BaseModel):
    """Verified email with SMTP validation"""
    email: str
    confidence: float = Field(ge=0.0, le=1.0)
    verification_status: str  # "valid", "invalid", "risky", "unknown"
    mx_records: List[str] = []
    smtp_response: Optional[str] = None
    verified_at: datetime


class PhoneNumber(BaseModel):
    """Phone number with validation"""
    number: str
    country_code: Optional[str] = None
    type: Optional[str] = None  # "mobile", "landline", "office"
    confidence: float = Field(ge=0.0, le=1.0)
    source: DataSource
    verified: bool = False


class LinkedInProfile(BaseModel):
    """LinkedIn profile information"""
    profile_url: HttpUrl
    full_name: str
    headline: Optional[str] = None
    current_position: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    connections: Optional[int] = None
    about: Optional[str] = None
    contact_info_available: bool = False
    premium_account: bool = False
    confidence: float = Field(ge=0.0, le=1.0)


class ContactHints(BaseModel):
    """Contact hints extracted from various sources"""
    email_patterns: List[str] = []
    phone_patterns: List[str] = []
    social_profiles: List[HttpUrl] = []
    website_contact_pages: List[HttpUrl] = []
    confidence: float = Field(ge=0.0, le=1.0)
    extraction_method: str


class Director(BaseModel):
    """Company director information"""
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: DirectorRole
    company_number: Optional[str] = None
    appointment_date: Optional[date] = None
    resignation_date: Optional[date] = None
    nationality: Optional[str] = None
    occupation: Optional[str] = None
    address: Optional[Address] = None
    date_of_birth: Optional[date] = None  # Month/year only for privacy
    is_active: bool = True


class DirectorProfile(BaseModel):
    """Complete director profile with enrichment data"""
    director: Director
    
    # Contact information
    email_candidates: List[EmailCandidate] = []
    verified_emails: List[VerifiedEmail] = []
    phone_numbers: List[PhoneNumber] = []
    linkedin_profile: Optional[LinkedInProfile] = None
    contact_hints: List[ContactHints] = []
    
    # Enrichment metadata
    confidence_score: float = Field(ge=0.0, le=1.0)
    data_sources: List[DataSource] = []
    processing_time_ms: int = 0
    total_cost: float = 0.0
    cost_breakdown: Dict[str, float] = {}
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)


class ConfidenceReport(BaseModel):
    """Assessment of data completeness and confidence"""
    overall_confidence: float = Field(ge=0.0, le=1.0)
    director_identified: float = Field(ge=0.0, le=1.0)
    email_available: float = Field(ge=0.0, le=1.0)
    phone_available: float = Field(ge=0.0, le=1.0)
    linkedin_profile: float = Field(ge=0.0, le=1.0)
    
    data_gaps: List[str] = []
    needs_paid_enhancement: bool = False
    recommended_actions: List[str] = []
    estimated_enhancement_cost: float = 0.0


class FreeDataBundle(BaseModel):
    """Data collected from free sources"""
    directors: List[Director] = []
    linkedin_profiles: List[LinkedInProfile] = []
    contact_hints: List[ContactHints] = []
    email_candidates: List[EmailCandidate] = []
    phone_candidates: List[PhoneNumber] = []
    
    processing_time_ms: int = 0
    sources_used: List[DataSource] = []
    errors: List[str] = []


class EnhancedDataBundle(BaseModel):
    """Data after paid enhancement"""
    free_data: FreeDataBundle
    verified_emails: List[VerifiedEmail] = []
    enhanced_phone_numbers: List[PhoneNumber] = []
    premium_linkedin_data: Optional[LinkedInProfile] = None
    
    enhancement_cost: float = 0.0
    enhancement_sources: List[DataSource] = []
    enhancement_time_ms: int = 0


class DirectorEnrichmentResult(BaseModel):
    """Final result of director enrichment process"""
    input_company: str
    input_website: Optional[HttpUrl] = None
    
    # Results
    director_profiles: List[DirectorProfile] = []
    primary_director: Optional[DirectorProfile] = None
    
    # Processing metadata
    enrichment_decision: EnrichmentDecision
    confidence_report: ConfidenceReport
    processing_summary: Dict[str, Any] = {}
    
    # Performance metrics
    total_processing_time_ms: int = 0
    total_cost: float = 0.0
    cost_breakdown: Dict[str, float] = {}
    
    # Status
    status: str = "completed"  # "completed", "partial", "failed"
    error_message: Optional[str] = None
    
    # Timestamps
    started_at: datetime
    completed_at: datetime = Field(default_factory=datetime.now)


class CostTrackingEntry(BaseModel):
    """Individual cost tracking entry"""
    timestamp: datetime = Field(default_factory=datetime.now)
    lead_id: str
    company_name: str
    tier: EnrichmentTier
    provider: DataSource
    cost: float
    success: bool
    processing_time_ms: int


class MonthlyBudget(BaseModel):
    """Monthly budget tracking"""
    month: str  # "2025-06"
    total_budget: float
    spent: float = 0.0
    remaining: float
    leads_processed: int = 0
    average_cost_per_lead: float = 0.0
    
    tier_breakdown: Dict[str, Dict[str, float]] = {
        "A": {"budget": 0.0, "spent": 0.0, "count": 0},
        "B": {"budget": 0.0, "spent": 0.0, "count": 0},
        "C": {"budget": 0.0, "spent": 0.0, "count": 0}
    }


class EnrichmentConfig(BaseModel):
    """Configuration for director enrichment"""
    # Budget settings
    monthly_budget: float = 50.00
    tier_budgets: Dict[str, float] = {
        "A": 5.00,  # Hot leads
        "B": 2.00,  # Warm leads
        "C": 0.00   # Free only
    }
    
    # Processing settings
    max_processing_time: Dict[str, int] = {
        "A": 60,  # seconds
        "B": 45,
        "C": 30
    }
    
    # Source priorities
    free_sources: List[DataSource] = [
        DataSource.COMPANIES_HOUSE,
        DataSource.OPENCORPORATES,
        DataSource.LINKEDIN_SCRAPER,
        DataSource.PUBLIC_REGISTRIES
    ]
    
    paid_sources: List[DataSource] = [
        DataSource.ABSTRACT_API,
        DataSource.HUNTER_IO,
        DataSource.EMAIL_VERIFICATION
    ]
    
    # Rate limiting
    linkedin_rate_limit: int = 10  # requests per minute
    companies_house_rate_limit: int = 600  # requests per 5 minutes
    
    # Confidence thresholds
    min_confidence_for_paid_enhancement: float = 0.8
    min_director_confidence: float = 0.7
    min_email_confidence: float = 0.6 