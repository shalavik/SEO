"""
UK Company SEO Lead Generation System

A comprehensive system for identifying UK companies with weak SEO performance
and extracting their contact details for outreach automation.

Main modules:
- fetchers: Data collection from UK directories  
- analyzers: SEO performance analysis
- processors: Contact extraction and lead qualification
- exporters: Data export and integration
"""

try:
    from .config import get_credential_manager, get_api_headers, is_api_available
except ImportError:
    # Graceful degradation if config modules aren't available
    def get_credential_manager():
        return None
    def get_api_headers(provider):
        return {}
    def is_api_available(provider):
        return False

try:
    from .database import initialize_database, get_db_session
except ImportError:
    # Graceful degradation if database modules aren't available
    def initialize_database():
        pass
    def get_db_session():
        return None

try:
    from .models import UKCompany, UKCompanyLead, PriorityTier
except ImportError:
    # Graceful degradation if models aren't available
    UKCompany = None
    UKCompanyLead = None
    PriorityTier = None

__version__ = "1.0.0"
__author__ = "SEO Lead Generation System"

__all__ = [
    'get_credential_manager', 'get_api_headers', 'is_api_available',
    'initialize_database', 'get_db_session',
    'UKCompany', 'UKCompanyLead', 'PriorityTier'
] 