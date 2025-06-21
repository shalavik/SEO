"""
Secure Credential Management System for Phase 4C Production Integration

This module provides enterprise-grade credential management with:
- Secure API key storage with environment variable integration
- Automated credential validation and rotation capabilities
- Security audit logging and monitoring
- Graceful degradation when APIs are unavailable
- Support for multiple API providers (Companies House, Twitter, LinkedIn, Facebook)
"""

import os
import logging
import json
from typing import Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import base64
from pathlib import Path

# Configure logging for security audit trail
security_logger = logging.getLogger('credential_security')
security_logger.setLevel(logging.INFO)

class APIProvider(Enum):
    """Supported API providers for credential management"""
    COMPANIES_HOUSE = "companies_house"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    
class CredentialType(Enum):
    """Types of credentials supported"""
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    OAUTH2_TOKEN = "oauth2_token"
    CLIENT_CREDENTIALS = "client_credentials"

@dataclass
class APICredential:
    """Secure credential container with metadata"""
    provider: APIProvider
    credential_type: CredentialType
    value: str
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_validated: Optional[datetime] = None
    is_valid: bool = True
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if credential is expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def needs_rotation(self, rotation_days: int = 30) -> bool:
        """Check if credential needs rotation"""
        if self.created_at is None:
            return True
        return datetime.now() - self.created_at > timedelta(days=rotation_days)
    
    def get_masked_value(self) -> str:
        """Get masked credential for logging (security)"""
        if len(self.value) <= 8:
            return "*" * len(self.value)
        return self.value[:4] + "*" * (len(self.value) - 8) + self.value[-4:]

class CredentialManager:
    """Enterprise-grade credential management system"""
    
    def __init__(self, env_file_path: Optional[str] = None):
        """
        Initialize credential manager
        
        Args:
            env_file_path: Optional path to .env file for development
        """
        self.env_file_path = env_file_path or ".env"
        self.credentials: Dict[APIProvider, APICredential] = {}
        self.fallback_enabled = True
        self.audit_enabled = True
        
        # Load environment variables
        self._load_environment()
        
        # Initialize credentials
        self._initialize_credentials()
        
        security_logger.info("CredentialManager initialized", extra={
            'event': 'credential_manager_init',
            'providers_configured': len(self.credentials),
            'fallback_enabled': self.fallback_enabled
        })
    
    def _load_environment(self):
        """Load environment variables from file if available"""
        if os.path.exists(self.env_file_path):
            try:
                with open(self.env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
                security_logger.info(f"Loaded environment from {self.env_file_path}")
            except Exception as e:
                security_logger.warning(f"Failed to load environment file: {e}")
    
    def _initialize_credentials(self):
        """Initialize credentials from environment variables"""
        credential_configs = {
            APIProvider.COMPANIES_HOUSE: {
                'env_key': 'COMPANIES_HOUSE_API_KEY',
                'type': CredentialType.API_KEY,
                'required': True
            },
            APIProvider.TWITTER: {
                'env_key': 'TWITTER_BEARER_TOKEN',
                'type': CredentialType.BEARER_TOKEN,
                'required': False
            },
            APIProvider.LINKEDIN: {
                'env_key': 'LINKEDIN_ACCESS_TOKEN',
                'type': CredentialType.OAUTH2_TOKEN,
                'required': False
            },
            APIProvider.FACEBOOK: {
                'env_key': 'FACEBOOK_ACCESS_TOKEN',
                'type': CredentialType.OAUTH2_TOKEN,
                'required': False
            }
        }
        
        for provider, config in credential_configs.items():
            credential_value = os.getenv(config['env_key'])
            
            if credential_value:
                credential = APICredential(
                    provider=provider,
                    credential_type=config['type'],
                    value=credential_value,
                    metadata={'env_key': config['env_key']}
                )
                self.credentials[provider] = credential
                
                self._audit_log('credential_loaded', {
                    'provider': provider.value,
                    'type': config['type'].value,
                    'masked_value': credential.get_masked_value()
                })
                
            elif config['required']:
                security_logger.warning(
                    f"Required credential missing for {provider.value}",
                    extra={'provider': provider.value, 'env_key': config['env_key']}
                )
    
    def get_credential(self, provider: APIProvider) -> Optional[APICredential]:
        """
        Get credential for specified provider with validation
        
        Args:
            provider: API provider to get credential for
            
        Returns:
            APICredential if available and valid, None otherwise
        """
        credential = self.credentials.get(provider)
        
        if not credential:
            self._audit_log('credential_not_found', {'provider': provider.value})
            return None
        
        if credential.is_expired():
            self._audit_log('credential_expired', {
                'provider': provider.value,
                'expired_at': credential.expires_at.isoformat() if credential.expires_at else None
            })
            return None
        
        if not credential.is_valid:
            self._audit_log('credential_invalid', {
                'provider': provider.value,
                'error_count': credential.error_count
            })
            return None
        
        # Update last access time
        credential.last_validated = datetime.now()
        
        self._audit_log('credential_accessed', {
            'provider': provider.value,
            'masked_value': credential.get_masked_value()
        })
        
        return credential
    
    def validate_credential(self, provider: APIProvider) -> Tuple[bool, Optional[str]]:
        """
        Validate credential for provider
        
        Args:
            provider: API provider to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        credential = self.credentials.get(provider)
        
        if not credential:
            return False, f"No credential configured for {provider.value}"
        
        if credential.is_expired():
            return False, f"Credential expired for {provider.value}"
        
        # Basic validation - check if credential looks valid
        if len(credential.value.strip()) < 10:
            credential.is_valid = False
            credential.error_count += 1
            return False, f"Credential appears invalid for {provider.value}"
        
        credential.last_validated = datetime.now()
        credential.is_valid = True
        
        self._audit_log('credential_validated', {
            'provider': provider.value,
            'validation_result': 'success'
        })
        
        return True, None
    
    def mark_credential_invalid(self, provider: APIProvider, error_message: str):
        """
        Mark credential as invalid due to API error
        
        Args:
            provider: API provider with invalid credential
            error_message: Error message from API
        """
        credential = self.credentials.get(provider)
        if credential:
            credential.is_valid = False
            credential.error_count += 1
            
            self._audit_log('credential_marked_invalid', {
                'provider': provider.value,
                'error_message': error_message,
                'error_count': credential.error_count
            })
            
            # Auto-disable if too many errors
            if credential.error_count >= 5:
                security_logger.warning(
                    f"Credential disabled due to repeated errors: {provider.value}",
                    extra={'provider': provider.value, 'error_count': credential.error_count}
                )
    
    def get_authentication_headers(self, provider: APIProvider) -> Dict[str, str]:
        """
        Get authentication headers for API requests
        
        Args:
            provider: API provider to get headers for
            
        Returns:
            Dictionary of headers for authentication
        """
        credential = self.get_credential(provider)
        
        if not credential:
            return {}
        
        if provider == APIProvider.COMPANIES_HOUSE:
            return {'Authorization': f'Bearer {credential.value}'}
        
        elif provider == APIProvider.TWITTER:
            return {'Authorization': f'Bearer {credential.value}'}
        
        elif provider == APIProvider.LINKEDIN:
            return {'Authorization': f'Bearer {credential.value}'}
        
        elif provider == APIProvider.FACEBOOK:
            return {'Authorization': f'Bearer {credential.value}'}
        
        return {}
    
    def is_provider_available(self, provider: APIProvider) -> bool:
        """
        Check if provider is available for use
        
        Args:
            provider: API provider to check
            
        Returns:
            True if provider has valid credentials, False otherwise
        """
        credential = self.get_credential(provider)
        return credential is not None and credential.is_valid
    
    def get_available_providers(self) -> list[APIProvider]:
        """Get list of available providers with valid credentials"""
        available = []
        for provider in APIProvider:
            if self.is_provider_available(provider):
                available.append(provider)
        return available
    
    def get_fallback_providers(self, primary_provider: APIProvider) -> list[APIProvider]:
        """
        Get fallback providers when primary provider fails
        
        Args:
            primary_provider: Primary provider that failed
            
        Returns:
            List of alternative providers
        """
        if not self.fallback_enabled:
            return []
        
        # Define fallback relationships
        fallback_map = {
            APIProvider.COMPANIES_HOUSE: [],  # No fallback for official government data
            APIProvider.TWITTER: [APIProvider.LINKEDIN, APIProvider.FACEBOOK],
            APIProvider.LINKEDIN: [APIProvider.TWITTER, APIProvider.FACEBOOK],
            APIProvider.FACEBOOK: [APIProvider.TWITTER, APIProvider.LINKEDIN]
        }
        
        potential_fallbacks = fallback_map.get(primary_provider, [])
        available_fallbacks = [p for p in potential_fallbacks if self.is_provider_available(p)]
        
        return available_fallbacks
    
    def get_credential_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all credentials"""
        status = {
            'total_providers': len(APIProvider),
            'configured_providers': len(self.credentials),
            'valid_providers': len(self.get_available_providers()),
            'fallback_enabled': self.fallback_enabled,
            'audit_enabled': self.audit_enabled,
            'providers': {}
        }
        
        for provider in APIProvider:
            credential = self.credentials.get(provider)
            if credential:
                status['providers'][provider.value] = {
                    'configured': True,
                    'valid': credential.is_valid,
                    'expired': credential.is_expired(),
                    'needs_rotation': credential.needs_rotation(),
                    'error_count': credential.error_count,
                    'last_validated': credential.last_validated.isoformat() if credential.last_validated else None,
                    'masked_value': credential.get_masked_value()
                }
            else:
                status['providers'][provider.value] = {
                    'configured': False,
                    'valid': False,
                    'expired': False,
                    'needs_rotation': False,
                    'error_count': 0,
                    'last_validated': None,
                    'masked_value': None
                }
        
        return status
    
    def _audit_log(self, event_type: str, details: Dict[str, Any]):
        """Log security audit event"""
        if not self.audit_enabled:
            return
        
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        }
        
        security_logger.info(f"Security audit: {event_type}", extra=audit_entry)
    
    def export_credential_summary(self) -> str:
        """Export credential summary for debugging (sensitive data masked)"""
        status = self.get_credential_status()
        
        summary = []
        summary.append("=== CREDENTIAL MANAGER STATUS ===")
        summary.append(f"Total Providers: {status['total_providers']}")
        summary.append(f"Configured: {status['configured_providers']}")
        summary.append(f"Valid: {status['valid_providers']}")
        summary.append(f"Fallback Enabled: {status['fallback_enabled']}")
        summary.append("")
        
        for provider_name, provider_status in status['providers'].items():
            summary.append(f"{provider_name.upper()}:")
            summary.append(f"  Configured: {provider_status['configured']}")
            summary.append(f"  Valid: {provider_status['valid']}")
            summary.append(f"  Expired: {provider_status['expired']}")
            summary.append(f"  Error Count: {provider_status['error_count']}")
            if provider_status['masked_value']:
                summary.append(f"  Credential: {provider_status['masked_value']}")
            summary.append("")
        
        return "\n".join(summary)

# Global credential manager instance
_credential_manager: Optional[CredentialManager] = None

def get_credential_manager() -> CredentialManager:
    """Get global credential manager instance (singleton pattern)"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager

def get_api_headers(provider: APIProvider) -> Dict[str, str]:
    """Convenience function to get authentication headers"""
    return get_credential_manager().get_authentication_headers(provider)

def is_api_available(provider: APIProvider) -> bool:
    """Convenience function to check API availability"""
    return get_credential_manager().is_provider_available(provider) 