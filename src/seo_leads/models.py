"""
Core data models for UK Company SEO Lead Generation System

Based on creative design decisions:
- Multi-factor scoring with business context
- Comprehensive contact extraction
- Lead prioritization with tier classification
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, HttpUrl, Field, validator
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from dataclasses import dataclass, field
import json

Base = declarative_base()

# Enums for type safety
class CompanySize(str, Enum):
    MICRO = "micro"      # 1-4 employees
    SMALL = "small"      # 5-19 employees  
    MEDIUM = "medium"    # 20-99 employees
    LARGE = "large"      # 100+ employees

class ProcessingStatus(str, Enum):
    SCRAPED = "scraped"
    CONTACTS_EXTRACTED = "contacts_extracted"
    SEO_ANALYZED = "seo_analyzed"
    QUALIFIED = "qualified"
    EXPORTED = "exported"
    FAILED = "failed"

class PriorityTier(str, Enum):
    A = "A"  # Hot Lead (80+)
    B = "B"  # Warm Lead (65-79)
    C = "C"  # Qualified Lead (50-64)
    D = "D"  # Low Priority (<50)

class ContactSeniorityTier(str, Enum):
    TIER_1 = "tier_1"  # CEO, Founder, Managing Director
    TIER_2 = "tier_2"  # Director, Head of, General Manager
    TIER_3 = "tier_3"  # Manager, Lead, Senior roles

# SQLAlchemy Models
class UKCompany(Base):
    """UK Company database model with comprehensive lead data"""
    __tablename__ = "uk_companies"
    
    id = Column(String, primary_key=True)
    company_name = Column(String, nullable=False, index=True)
    website = Column(String, index=True)
    
    # Location data
    city = Column(String, index=True)
    region = Column(String)
    address = Column(Text)
    
    # Business intelligence
    sector = Column(String, index=True)
    employees = Column(Integer)
    size_category = Column(String)  # CompanySize enum
    
    # Data source
    source = Column(String, index=True)  # Directory source (e.g., "Yell.com", "Thomson Local")
    
    # Processing status
    status = Column(String, default=ProcessingStatus.SCRAPED.value, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Contact information
    contact_person = Column(String)
    contact_role = Column(String)
    contact_seniority_tier = Column(String)  # ContactSeniorityTier enum
    linkedin_url = Column(String)
    email = Column(String)
    phone = Column(String)
    contact_confidence = Column(Float)
    contact_extraction_method = Column(String)
    
    # SEO analysis results
    seo_overall_score = Column(Float, index=True)
    pagespeed_score = Column(Float)
    mobile_friendly = Column(Boolean)
    meta_description_missing = Column(Boolean)
    h1_tags_present = Column(Boolean)
    ssl_certificate = Column(Boolean)
    load_time = Column(Float)
    critical_issues = Column(JSON)  # List of critical SEO issues
    
    # Lead qualification
    lead_score = Column(Float, index=True)
    priority_tier = Column(String, index=True)  # PriorityTier enum
    tier_label = Column(String)
    factor_breakdown = Column(JSON)  # Detailed scoring breakdown
    estimated_value = Column(String)
    urgency = Column(String)
    recommended_actions = Column(JSON)  # List of recommended actions
    talking_points = Column(JSON)  # List of talking points for outreach
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Executives relationship
    executives = relationship("ExecutiveContactDB", back_populates="company")

class ProcessingStatus(Base):
    """Track processing status across pipeline stages"""
    __tablename__ = "processing_status"
    
    stage = Column(String, primary_key=True)
    total_companies = Column(Integer, default=0)
    processed_companies = Column(Integer, default=0)
    failed_companies = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)

# Pydantic Models for validation and API

class CompanyLocation(BaseModel):
    """Company location data"""
    city: str
    region: Optional[str] = None
    country: str = "UK"

class BusinessInfo(BaseModel):
    """Company business intelligence"""
    sector: str
    employees: Optional[int] = None
    size_category: Optional[CompanySize] = None
    growth_indicators: Dict[str, Any] = {}

class ContactInfo(BaseModel):
    """Contact extraction results with confidence scoring"""
    person: Optional[str] = None
    role: Optional[str] = None
    seniority_tier: Optional[ContactSeniorityTier] = None
    linkedin_url: Optional[HttpUrl] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    extraction_method: Optional[str] = None
    
    @validator('confidence')
    def validate_confidence(cls, v):
        return round(v, 3)

class SEOPerformance(BaseModel):
    """SEO performance metrics"""
    pagespeed_score: Optional[float] = Field(None, ge=0, le=100)
    load_time: Optional[float] = None
    mobile_friendly: Optional[bool] = None

class SEOContent(BaseModel):
    """SEO content analysis"""
    meta_description_missing: Optional[bool] = None
    h1_tags_present: Optional[bool] = None
    ssl_certificate: Optional[bool] = None

class SEOAnalysis(BaseModel):
    """Complete SEO analysis results"""
    overall_score: float = Field(ge=0, le=100)
    performance: SEOPerformance
    content: SEOContent
    critical_issues: List[str] = []
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)

class FactorBreakdown(BaseModel):
    """Individual factor contribution to lead score"""
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    contribution: float

class LeadQualification(BaseModel):
    """Lead qualification and scoring results"""
    final_score: float = Field(ge=0, le=100)
    priority_tier: PriorityTier
    tier_label: str
    factor_breakdown: Dict[str, FactorBreakdown]
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    
    # Additional fields for production pipeline compatibility
    estimated_value: Optional[float] = None
    urgency: Optional[str] = None
    talking_points: List[str] = []
    recommended_actions: List[str] = []

class OutreachIntelligence(BaseModel):
    """Outreach automation intelligence"""
    urgency: str  # high, medium, low
    estimated_value: str
    recommended_actions: List[str] = []
    talking_points: List[str] = []
    follow_up_schedule: Dict[str, str] = {}

class UKCompanyLead(BaseModel):
    """Complete UK company lead with all analysis"""
    company: Dict[str, Any]  # Company basic info
    contact: ContactInfo
    seo_analysis: SEOAnalysis
    lead_qualification: LeadQualification
    outreach_intelligence: OutreachIntelligence
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PipelineMetrics(BaseModel):
    """Pipeline processing metrics"""
    total_companies: int = 0
    by_stage: Dict[str, int] = {}
    success_rates: Dict[str, float] = {}
    estimated_completion: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Lead scoring constants based on creative design decisions
SCORING_WEIGHTS = {
    'seo': 0.35,                 # SEO improvement potential (renamed for consistency)
    'business': 0.25,            # Company size and revenue potential  
    'sector': 0.20,              # SEO importance in industry
    'growth': 0.10,              # Business growth signals
    'contact': 0.10              # Decision maker accessibility
}

SECTOR_SEO_DEPENDENCY = {
    'retail': 95, 'e-commerce': 100, 'professional-services': 85,
    'hospitality': 80, 'real-estate': 90, 'healthcare': 75,
    'education': 70, 'legal': 85, 'financial': 75,
    'web-development': 90, 'digital-marketing': 100,
    'consulting': 80, 'manufacturing': 60
}

SENIOR_ROLE_PATTERNS = {
    'tier_1': {
        'patterns': ['ceo', 'chief executive', 'managing director', 'founder', 'owner'],
        'confidence_multiplier': 1.0
    },
    'tier_2': {
        'patterns': ['director', 'head of', 'general manager', 'partner'],
        'confidence_multiplier': 0.9
    },
    'tier_3': {
        'patterns': ['manager', 'lead', 'senior', 'supervisor'],
        'confidence_multiplier': 0.7
    }
}

# Executive Contact Models
@dataclass
class ExecutiveContact:
    """Enhanced contact model for decision makers"""
    # Identity (required fields first)
    first_name: str
    last_name: str
    full_name: str
    title: str
    seniority_tier: str  # tier_1, tier_2, tier_3
    company_name: str
    company_domain: str
    
    # Contact Details (optional fields with defaults)
    email: Optional[str] = None
    email_confidence: float = 0.0
    phone: Optional[str] = None
    phone_confidence: float = 0.0
    linkedin_url: Optional[str] = None
    linkedin_verified: bool = False
    
    # Discovery Metadata
    discovery_sources: List[str] = field(default_factory=list)  # ['website', 'linkedin']
    discovery_method: str = ""
    data_completeness_score: float = 0.0
    overall_confidence: float = 0.0
    processing_time_ms: int = 0
    extracted_at: datetime = field(default_factory=datetime.utcnow)

@dataclass 
class ExecutiveDiscoveryResult:
    """Result of executive discovery process"""
    company_id: str
    company_name: str
    company_domain: str
    executives_found: List[ExecutiveContact]
    primary_decision_maker: Optional[ExecutiveContact]
    discovery_sources: List[str]
    total_processing_time: float
    success_rate: float
    discovery_timestamp: datetime = field(default_factory=datetime.utcnow)

# Executive Role Patterns
EXECUTIVE_PATTERNS = {
    'tier_1': [
        'Chief Executive Officer', 'CEO', 'Managing Director', 'MD',
        'Founder', 'Co-Founder', 'Owner', 'Principal', 'President'
    ],
    'tier_2': [
        'Director', 'Executive Director', 'Operations Director',
        'Sales Director', 'Marketing Director', 'Finance Director',
        'Commercial Director', 'Business Development Director'
    ],
    'tier_3': [
        'Manager', 'General Manager', 'Operations Manager',
        'Senior Manager', 'Team Lead', 'Department Head',
        'Business Manager', 'Regional Manager'
    ]
}

# LinkedIn Discovery Models
@dataclass
class LinkedInProfile:
    """LinkedIn profile data structure"""
    profile_url: str
    full_name: str
    title: str
    company_name: str
    location: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    connections: Optional[int] = None
    profile_image_url: Optional[str] = None
    verified: bool = False
    extracted_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class LinkedInCompanyData:
    """LinkedIn company page data"""
    company_url: str
    company_name: str
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    employee_count: Optional[int] = None
    employees: List[LinkedInProfile] = field(default_factory=list)
    executives: List[LinkedInProfile] = field(default_factory=list)

# Website Discovery Models  
@dataclass
class WebsiteExecutive:
    """Executive found on company website"""
    full_name: str
    title: str
    bio: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    image_url: Optional[str] = None
    page_url: str = ""
    confidence: float = 0.0

# Enhanced Database Models (extend existing UKCompany)
class ExecutiveContactDB(Base):
    """Database model for executive contacts"""
    __tablename__ = "executive_contacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('uk_companies.id'), nullable=False)
    
    # Identity
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False)
    title = Column(String(200), nullable=False)
    seniority_tier = Column(String(20), nullable=False)  # tier_1, tier_2, tier_3
    
    # Contact Details
    email = Column(String(255))
    email_confidence = Column(Float, default=0.0)
    phone = Column(String(50))
    phone_confidence = Column(Float, default=0.0)
    linkedin_url = Column(String(500))
    linkedin_verified = Column(Boolean, default=False)
    
    # Discovery Metadata
    discovery_sources = Column(JSON)  # ['website', 'linkedin']
    discovery_method = Column(String(100))
    data_completeness_score = Column(Float, default=0.0)
    overall_confidence = Column(Float, default=0.0)
    processing_time_ms = Column(Integer, default=0)
    
    # Timestamps
    extracted_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("UKCompany", back_populates="executives") 

@dataclass
class ContactInfo:
    """Contact information for executives discovered from websites"""
    phone: str = ""
    email: str = ""
    linkedin: str = ""
    address: str = ""
    website: str = ""
    social_media: Dict[str, str] = field(default_factory=dict)
    
    def has_any_contact(self) -> bool:
        """Check if any contact information is available"""
        return bool(self.phone or self.email or self.linkedin)
    
    def get_contact_completeness(self) -> float:
        """Get contact completeness score (0.0 to 1.0)"""
        contacts = [self.phone, self.email, self.linkedin]
        filled_contacts = sum(1 for contact in contacts if contact)
        return filled_contacts / len(contacts)

@dataclass
class BusinessContext:
    """Business context information extracted from website"""
    business_type: str = ""
    industry: str = ""
    service_areas: List[str] = field(default_factory=list)
    company_size: str = ""
    founded_year: Optional[int] = None
    annual_revenue: str = ""
    specialties: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    
    def is_hvac_business(self) -> bool:
        """Check if business is HVAC-related"""
        hvac_terms = ['hvac', 'heating', 'cooling', 'air conditioning']
        return any(term in self.business_type.lower() for term in hvac_terms)
    
    def is_plumbing_business(self) -> bool:
        """Check if business is plumbing-related"""
        plumbing_terms = ['plumbing', 'plumber', 'pipe', 'drain']
        return any(term in self.business_type.lower() for term in plumbing_terms)
    
    def is_electrical_business(self) -> bool:
        """Check if business is electrical-related"""
        electrical_terms = ['electrical', 'electrician', 'electric']
        return any(term in self.business_type.lower() for term in electrical_terms)

@dataclass
class Executive:
    """
    Executive information discovered from website content
    Enhanced for Phase 4A real discovery (no fake generation)
    """
    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    title: str = ""
    department: str = ""
    company: str = ""
    contact_info: Optional[ContactInfo] = None
    business_context: Optional[BusinessContext] = None
    confidence: float = 0.0
    source: str = ""  # Source of discovery (e.g., 'real_website_content')
    discovery_method: str = ""  # Method used to find executive
    validation_score: float = 0.0
    discovery_timestamp: datetime = field(default_factory=datetime.now)
    
    # Phase 4A specific fields
    is_validated_real: bool = False  # Validated as real person (not fake)
    extraction_patterns: List[str] = field(default_factory=list)
    source_page_url: str = ""
    content_context: str = ""
    
    def __post_init__(self):
        """Initialize contact_info if not provided"""
        if self.contact_info is None:
            self.contact_info = ContactInfo()
        if self.business_context is None:
            self.business_context = BusinessContext()
    
    def get_display_name(self) -> str:
        """Get formatted display name"""
        if self.full_name:
            return self.full_name
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return "Unknown Executive"
    
    def get_title_display(self) -> str:
        """Get formatted title display"""
        if self.title:
            return self.title
        else:
            return "Executive"
    
    def has_contact_info(self) -> bool:
        """Check if executive has any contact information"""
        return self.contact_info and self.contact_info.has_any_contact()
    
    def is_high_confidence(self) -> bool:
        """Check if executive discovery has high confidence"""
        return self.confidence >= 0.7
    
    def is_validated(self) -> bool:
        """Check if executive has been validated as real"""
        return self.is_validated_real and self.validation_score >= 0.6
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert executive to dictionary for JSON serialization"""
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'title': self.title,
            'department': self.department,
            'company': self.company,
            'contact_info': {
                'phone': self.contact_info.phone if self.contact_info else '',
                'email': self.contact_info.email if self.contact_info else '',
                'linkedin': self.contact_info.linkedin if self.contact_info else '',
                'address': self.contact_info.address if self.contact_info else '',
                'website': self.contact_info.website if self.contact_info else ''
            },
            'business_context': {
                'business_type': self.business_context.business_type if self.business_context else '',
                'industry': self.business_context.industry if self.business_context else '',
                'service_areas': self.business_context.service_areas if self.business_context else []
            },
            'confidence': self.confidence,
            'source': self.source,
            'discovery_method': self.discovery_method,
            'validation_score': self.validation_score,
            'is_validated_real': self.is_validated_real,
            'extraction_patterns': self.extraction_patterns,
            'source_page_url': self.source_page_url,
            'discovery_timestamp': self.discovery_timestamp.isoformat() if self.discovery_timestamp else ''
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Executive':
        """Create Executive from dictionary"""
        contact_info = ContactInfo(
            phone=data.get('contact_info', {}).get('phone', ''),
            email=data.get('contact_info', {}).get('email', ''),
            linkedin=data.get('contact_info', {}).get('linkedin', ''),
            address=data.get('contact_info', {}).get('address', ''),
            website=data.get('contact_info', {}).get('website', '')
        )
        
        business_context = BusinessContext(
            business_type=data.get('business_context', {}).get('business_type', ''),
            industry=data.get('business_context', {}).get('industry', ''),
            service_areas=data.get('business_context', {}).get('service_areas', [])
        )
        
        # Parse timestamp
        timestamp_str = data.get('discovery_timestamp', '')
        discovery_timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
        
        return cls(
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            full_name=data.get('full_name', ''),
            title=data.get('title', ''),
            department=data.get('department', ''),
            company=data.get('company', ''),
            contact_info=contact_info,
            business_context=business_context,
            confidence=data.get('confidence', 0.0),
            source=data.get('source', ''),
            discovery_method=data.get('discovery_method', ''),
            validation_score=data.get('validation_score', 0.0),
            is_validated_real=data.get('is_validated_real', False),
            extraction_patterns=data.get('extraction_patterns', []),
            source_page_url=data.get('source_page_url', ''),
            discovery_timestamp=discovery_timestamp
        )

@dataclass
class CompanyInfo:
    """Company information for lead generation"""
    name: str = ""
    website: str = ""
    industry: str = ""
    business_type: str = ""
    phone: str = ""
    address: str = ""
    service_areas: List[str] = field(default_factory=list)
    founded_year: Optional[int] = None
    employee_count: str = ""
    annual_revenue: str = ""
    description: str = ""
    
    def get_primary_service_area(self) -> str:
        """Get primary service area"""
        return self.service_areas[0] if self.service_areas else ""

@dataclass
class LeadResult:
    """Complete lead result including company and executives"""
    company: CompanyInfo
    executives: List[Executive] = field(default_factory=list)
    discovery_metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    confidence_score: float = 0.0
    validation_status: str = "pending"
    
    def get_executive_count(self) -> int:
        """Get number of discovered executives"""
        return len(self.executives)
    
    def get_validated_executives(self) -> List[Executive]:
        """Get only validated real executives"""
        return [exec for exec in self.executives if exec.is_validated()]
    
    def has_contact_info(self) -> bool:
        """Check if any executives have contact information"""
        return any(exec.has_contact_info() for exec in self.executives)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert lead result to dictionary"""
        return {
            'company': {
                'name': self.company.name,
                'website': self.company.website,
                'industry': self.company.industry,
                'business_type': self.company.business_type,
                'phone': self.company.phone,
                'address': self.company.address,
                'service_areas': self.company.service_areas
            },
            'executives': [exec.to_dict() for exec in self.executives],
            'discovery_metadata': self.discovery_metadata,
            'processing_time': self.processing_time,
            'confidence_score': self.confidence_score,
            'validation_status': self.validation_status,
            'executive_count': self.get_executive_count(),
            'validated_executive_count': len(self.get_validated_executives()),
            'has_contact_info': self.has_contact_info()
        } 