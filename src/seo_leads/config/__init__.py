"""
Configuration package for SEO leads system

This package contains configuration and credential management components.
"""

from .credential_manager import (
    get_credential_manager,
    get_api_headers,
    is_api_available,
    APIProvider,
    CredentialType,
    CredentialManager
)

# Import config functions from the main config module
try:
    from ..config import (
        get_api_config,
        get_processing_config,
        get_export_config,
        get_config,
        get_db_config
    )
except ImportError:
    # Fallback functions if main config not available
    def get_api_config():
        from ..config import APIConfig
        return APIConfig()
    
    def get_processing_config():
        from ..config import ProcessingConfig
        return ProcessingConfig()
    
    def get_export_config():
        from ..config import ExportConfig
        return ExportConfig()
    
    def get_config():
        from ..config import Config
        return Config()
    
    def get_db_config():
        from ..config import DatabaseConfig
        return DatabaseConfig()

__all__ = [
    'get_credential_manager',
    'get_api_headers', 
    'is_api_available',
    'APIProvider',
    'CredentialType',
    'CredentialManager',
    'get_api_config',
    'get_processing_config',
    'get_export_config',
    'get_config',
    'get_db_config'
] 