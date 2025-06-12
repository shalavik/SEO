"""
Lead Enrichment Engine

Main orchestration service that combines all providers and strategies
to deliver comprehensive lead enrichment similar to Hunter.io/Clearbit/Apollo.io.
"""

import asyncio
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from enrichment_service.core.models import (
    EnrichmentInput, EnrichmentResult, EnrichmentStatus, 
    CompanyEnrichment, ContactEnrichment, EmailDiscovery,
    ContactPersonal, ContactProfessional, ProviderResponse
)
from enrichment_service.providers.abstract_api import AbstractAPIProvider
from enrichment_service.providers.opencorporates import OpenCorporatesProvider
from enrichment_service.normalisers.firmographic import FirmographicNormaliser
from enrichment_service.strategies.email_guess import EmailDiscoveryStrategy

class EnrichmentEngine:
    """Main enrichment engine orchestrating all providers and strategies"""
    
    def __init__(self):
        # Initialize providers
        self.abstract_api = self._init_abstract_api()
        self.opencorporates = self._init_opencorporates()
        
        # Initialize normalisers and strategies
        self.firmographic_normaliser = FirmographicNormaliser()
        self.email_strategy = EmailDiscoveryStrategy()
        
        # Provider weights for confidence calculation
        self.provider_weights = {
            'abstract_api': 0.8,
            'opencorporates': 0.9,  # Higher weight for official data
            'email_discovery': 0.7
        }
    
    def _init_abstract_api(self) -> Optional[AbstractAPIProvider]:
        """Initialize Abstract API provider"""
        api_key = os.getenv('ABSTRACT_API_KEY')
        if api_key:
            return AbstractAPIProvider(api_key)
        return None
    
    def _init_opencorporates(self) -> OpenCorporatesProvider:
        """Initialize OpenCorporates provider"""
        api_key = os.getenv('OPENCORPORATES_API_KEY')  # Optional
        return OpenCorporatesProvider(api_key)
    
    async def enrich_lead(self, input_data: EnrichmentInput, 
                         providers: Optional[List[str]] = None) -> EnrichmentResult:
        """Enrich a single lead with comprehensive data"""
        start_time = datetime.utcnow()
        
        try:
            # Extract domain for API calls
            domain = input_data.domain
            if not domain and input_data.website:
                from urllib.parse import urlparse
                parsed = urlparse(str(input_data.website))
                domain = parsed.netloc
            
            if not domain:
                return EnrichmentResult(
                    input_data=input_data,
                    status=EnrichmentStatus.FAILED,
                    error_message="No domain available for enrichment",
                    data_sources_used=[]
                )
            
            # Phase 1: Company Enrichment
            company_enrichments = await self._enrich_company_data(
                input_data.company_name, domain, providers
            )
            
            # Phase 2: Email Discovery
            email_discovery = await self._discover_domain_emails(domain)
            
            # Phase 3: Contact Enrichment
            contact_enrichments = await self._enrich_contact_data(
                input_data, domain, email_discovery
            )
            
            # Normalize and merge company data
            merged_company = None
            if company_enrichments:
                merged_company = self.firmographic_normaliser.normalise_company_data(
                    *company_enrichments
                )
            
            # Calculate overall confidence
            confidence_score = self._calculate_overall_confidence(
                merged_company, contact_enrichments, email_discovery
            )
            
            # Determine status
            status = EnrichmentStatus.ENRICHED if confidence_score > 0.3 else EnrichmentStatus.PARTIAL
            
            # Collect data sources used
            data_sources_used = self._collect_data_sources(
                company_enrichments, contact_enrichments, email_discovery
            )
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return EnrichmentResult(
                input_data=input_data,
                company_enrichment=merged_company,
                contact_enrichments=contact_enrichments,
                email_discovery=email_discovery,
                status=status,
                confidence_score=confidence_score,
                processing_time_ms=processing_time,
                data_sources_used=data_sources_used
            )
            
        except Exception as e:
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return EnrichmentResult(
                input_data=input_data,
                status=EnrichmentStatus.FAILED,
                error_message=str(e),
                processing_time_ms=processing_time,
                data_sources_used=[]
            )
    
    async def _enrich_company_data(self, company_name: str, domain: str,
                                 providers: Optional[List[str]]) -> List[CompanyEnrichment]:
        """Enrich company data using multiple providers"""
        enrichments = []
        
        # Abstract API enrichment
        if self.abstract_api and (not providers or 'abstract' in providers):
            try:
                response = await self.abstract_api.enrich_company(domain, company_name)
                if response.success:
                    enrichment = await self.abstract_api.enrichment_from_response(response)
                    if enrichment:
                        enrichments.append(enrichment)
            except Exception as e:
                # Log error but continue with other providers
                pass
        
        # OpenCorporates enrichment
        if self.opencorporates and (not providers or 'opencorporates' in providers):
            try:
                response = await self.opencorporates.enrich_company(company_name)
                if response.success:
                    enrichment = await self.opencorporates.enrichment_from_response(response)
                    if enrichment:
                        enrichments.append(enrichment)
            except Exception as e:
                # Log error but continue with other providers
                pass
        
        return enrichments
    
    async def _discover_domain_emails(self, domain: str) -> Optional[EmailDiscovery]:
        """Discover email patterns for the domain"""
        try:
            return await self.email_strategy.discover_domain_patterns(domain)
        except Exception as e:
            return None
    
    async def _enrich_contact_data(self, input_data: EnrichmentInput, domain: str,
                                 email_discovery: Optional[EmailDiscovery]) -> List[ContactEnrichment]:
        """Enrich contact data"""
        contact_enrichments = []
        
        # If we have existing contact data, enrich it
        if input_data.existing_contact:
            try:
                existing_contact = input_data.existing_contact
                
                # Extract contact information
                person_name = existing_contact.get('person', '')
                role = existing_contact.get('role', '')
                
                if person_name:
                    # Parse name
                    name_parts = person_name.split()
                    first_name = name_parts[0] if name_parts else ''
                    last_name = name_parts[-1] if len(name_parts) > 1 else ''
                    
                    # Create contact personal info
                    personal = ContactPersonal(
                        full_name=person_name,
                        first_name=first_name,
                        last_name=last_name
                    )
                    
                    # Create professional info
                    professional = ContactProfessional(
                        current_role=role
                    ) if role else None
                    
                    # Calculate confidence
                    confidence = 0.7
                    
                    contact_enrichment = ContactEnrichment(
                        personal=personal,
                        professional=professional,
                        confidence=confidence,
                        data_sources=['input_data']
                    )
                    
                    contact_enrichments.append(contact_enrichment)
                    
            except Exception as e:
                # Log error but continue
                pass
        
        return contact_enrichments
    
    def _calculate_overall_confidence(self, company_enrichment: Optional[CompanyEnrichment],
                                    contact_enrichments: List[ContactEnrichment],
                                    email_discovery: Optional[EmailDiscovery]) -> float:
        """Calculate overall enrichment confidence"""
        
        confidence_components = []
        
        # Company enrichment confidence
        if company_enrichment:
            confidence_components.append((company_enrichment.confidence, 0.5))
        
        # Contact enrichment confidence
        if contact_enrichments:
            avg_contact_confidence = sum(c.confidence for c in contact_enrichments) / len(contact_enrichments)
            confidence_components.append((avg_contact_confidence, 0.3))
        
        # Email discovery confidence
        if email_discovery:
            confidence_components.append((email_discovery.confidence, 0.2))
        
        # Calculate weighted average
        if confidence_components:
            total_weighted = sum(conf * weight for conf, weight in confidence_components)
            total_weight = sum(weight for _, weight in confidence_components)
            return total_weighted / total_weight
        
        return 0.0
    
    def _collect_data_sources(self, company_enrichments: List[CompanyEnrichment],
                            contact_enrichments: List[ContactEnrichment],
                            email_discovery: Optional[EmailDiscovery]) -> List[str]:
        """Collect all data sources used in enrichment"""
        sources = set()
        
        # Add provider sources based on successful enrichments
        if company_enrichments:
            if self.abstract_api:
                sources.add('abstract_api')
            if self.opencorporates:
                sources.add('opencorporates')
        
        if contact_enrichments:
            for contact in contact_enrichments:
                sources.update(contact.data_sources)
        
        if email_discovery:
            sources.add('email_discovery')
        
        return list(sources) 