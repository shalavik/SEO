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

from .config import get_config, get_api_config, get_processing_config, get_export_config
from .database import initialize_database, get_db_session
from .models import UKCompany, UKCompanyLead, PriorityTier

__version__ = "1.0.0"
__author__ = "SEO Lead Generation System"

__all__ = [
    'get_config', 'get_api_config', 'get_processing_config', 'get_export_config',
    'initialize_database', 'get_db_session',
    'UKCompany', 'UKCompanyLead', 'PriorityTier'
] 