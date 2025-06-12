"""
Lead Enrichment Service

Hunter.io/Clearbit/Apollo.io style lead enrichment for UK companies.
"""

__version__ = "0.1.0"

from enrichment_service.core.models import (
    EnrichmentInput, EnrichmentResult, EnrichmentStatus,
    CompanyEnrichment, ContactEnrichment, EmailDiscovery
)
from enrichment_service.services.enrichment_engine import EnrichmentEngine

__all__ = [
    'EnrichmentInput',
    'EnrichmentResult', 
    'EnrichmentStatus',
    'CompanyEnrichment',
    'ContactEnrichment',
    'EmailDiscovery',
    'EnrichmentEngine'
] 