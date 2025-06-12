"""
Configuration management for UK Company SEO Lead Generation System

Centralizes all configuration settings with environment variable support
and validation for external API keys and rate limits.
"""

import os
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

# Environment configuration
ENV = os.environ.get('ENVIRONMENT', 'development')
DEBUG = ENV == 'development' or os.environ.get('DEBUG', '').lower() == 'true'

@dataclass
class APIConfig:
    """API configuration and rate limiting"""
    
    # Google PageSpeed API
    google_api_key: Optional[str] = None
    pagespeed_requests_per_hour: int = 25
    pagespeed_retry_attempts: int = 3
    pagespeed_retry_delay: int = 60  # seconds
    
    # Rate limiting for directory scraping
    yell_requests_per_minute: int = 10
    yell_page_delay: float = 6.0  # seconds between requests
    yell_max_pages: int = 50
    
    # Browser automation settings
    headless_browser: bool = True
    browser_timeout: int = 30
    browser_user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    def __post_init__(self):
        # Load API key from environment
        self.google_api_key = os.environ.get('GOOGLE_API_KEY')
        
        # Validate required settings
        if not self.google_api_key and ENV == 'production':
            logging.warning("Google API key not configured - SEO analysis will be limited")

@dataclass 
class DatabaseConfig:
    """Database configuration"""
    
    url: str = "sqlite:///./uk_company_leads.db"
    echo_sql: bool = DEBUG
    pool_size: int = 20
    max_overflow: int = 30
    
    def __post_init__(self):
        # Load database URL from environment
        env_url = os.environ.get('DATABASE_URL')
        if env_url:
            self.url = env_url

@dataclass
class ProcessingConfig:
    """Data processing and pipeline configuration"""
    
    # Batch processing settings
    batch_size: int = 50
    max_concurrent_workers: int = 5
    
    # Scraping configuration
    max_companies_per_city: int = 200
    target_cities: List[str] = field(default_factory=lambda: [
        'London', 'Manchester', 'Birmingham', 'Leeds', 'Liverpool',
        'Sheffield', 'Bristol', 'Newcastle', 'Leicester', 'Nottingham',
        'Southampton', 'Brighton', 'Plymouth', 'Stoke-on-Trent', 'Wolverhampton'
    ])
    
    # Target business sectors (high SEO dependency)
    target_sectors: List[str] = field(default_factory=lambda: [
        'retail', 'e-commerce', 'professional-services', 'hospitality',
        'real-estate', 'healthcare', 'legal', 'consulting', 'web-development',
        'digital-marketing', 'education', 'financial'
    ])
    
    # Contact extraction settings
    contact_confidence_threshold: float = 0.6
    max_contact_search_depth: int = 3  # pages deep
    
    # Lead qualification settings
    minimum_lead_score: float = 50.0
    high_priority_threshold: float = 80.0
    
    # Error handling
    max_retry_attempts: int = 3
    error_cooldown_minutes: int = 15

@dataclass
class ExportConfig:
    """Export and integration configuration"""
    
    # Make.com webhook configuration
    make_webhook_url: Optional[str] = None
    make_webhook_secret: Optional[str] = None
    
    # Export formats
    export_formats: List[str] = field(default_factory=lambda: ['json', 'csv'])
    output_directory: str = "./exports"
    
    # Data retention
    retain_raw_data: bool = True
    archive_after_days: int = 30
    
    def __post_init__(self):
        # Load webhook settings from environment
        self.make_webhook_url = os.environ.get('MAKE_WEBHOOK_URL')
        self.make_webhook_secret = os.environ.get('MAKE_WEBHOOK_SECRET')
        
        # Create output directory
        Path(self.output_directory).mkdir(exist_ok=True)

@dataclass
class LoggingConfig:
    """Logging configuration"""
    
    level: str = "INFO" if ENV == 'production' else "DEBUG"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    def __post_init__(self):
        # Set log file path
        if ENV == 'production':
            self.file_path = "./logs/seo_leads.log"
            Path("./logs").mkdir(exist_ok=True)

class Config:
    """Main configuration class that aggregates all settings"""
    
    def __init__(self):
        self.api = APIConfig()
        self.database = DatabaseConfig()
        self.processing = ProcessingConfig()
        self.export = ExportConfig()
        self.logging = LoggingConfig()
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure application logging"""
        log_config = self.logging
        
        # Create formatter
        formatter = logging.Formatter(log_config.format)
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_config.level))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler (if configured)
        if log_config.file_path:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_config.file_path,
                maxBytes=log_config.max_file_size,
                backupCount=log_config.backup_count
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of warnings/errors"""
        warnings = []
        
        # API validation
        if not self.api.google_api_key:
            warnings.append("Google API key not configured - SEO analysis will be limited")
        
        # Export validation
        if not self.export.make_webhook_url and ENV == 'production':
            warnings.append("Make.com webhook URL not configured - export will be file-only")
        
        # Processing validation
        if self.processing.batch_size > 100:
            warnings.append("Large batch size may cause memory issues")
        
        if self.processing.max_concurrent_workers > 10:
            warnings.append("High concurrent workers may hit rate limits")
        
        return warnings
    
    def get_summary(self) -> Dict:
        """Get configuration summary for debugging"""
        return {
            'environment': ENV,
            'debug': DEBUG,
            'database_type': 'sqlite' if self.database.url.startswith('sqlite') else 'external',
            'api_keys_configured': {
                'google_api': bool(self.api.google_api_key),
                'make_webhook': bool(self.export.make_webhook_url)
            },
            'processing': {
                'batch_size': self.processing.batch_size,
                'target_cities': len(self.processing.target_cities),
                'target_sectors': len(self.processing.target_sectors)
            },
            'rate_limits': {
                'google_api_per_hour': self.api.pagespeed_requests_per_hour,
                'yell_per_minute': self.api.yell_requests_per_minute
            }
        }

# Global configuration instance
config = Config()

# Convenience functions
def get_config() -> Config:
    """Get global configuration instance"""
    return config

def get_api_config() -> APIConfig:
    """Get API configuration"""
    return config.api

def get_db_config() -> DatabaseConfig:
    """Get database configuration"""
    return config.database

def get_processing_config() -> ProcessingConfig:
    """Get processing configuration"""
    return config.processing

def get_export_config() -> ExportConfig:
    """Get export configuration"""
    return config.export

# Environment variables documentation
ENV_DOCS = """
Environment Variables for UK Company SEO Lead Generation System:

REQUIRED:
- GOOGLE_API_KEY: Google PageSpeed Insights API key

OPTIONAL:
- DATABASE_URL: Database connection string (default: SQLite)
- MAKE_WEBHOOK_URL: Make.com webhook endpoint
- MAKE_WEBHOOK_SECRET: Make.com webhook secret
- ENVIRONMENT: production|development (default: development)
- DEBUG: true|false (default: false in production)

Example .env file:
GOOGLE_API_KEY=your_google_api_key_here
MAKE_WEBHOOK_URL=https://hook.make.com/your_webhook_id
MAKE_WEBHOOK_SECRET=your_webhook_secret
ENVIRONMENT=production
DEBUG=false
"""

if __name__ == "__main__":
    # Configuration testing and validation
    print("UK Company SEO Lead Generation - Configuration")
    print("=" * 50)
    
    # Show configuration summary
    summary = config.get_summary()
    print(f"Environment: {summary['environment']}")
    print(f"Debug Mode: {summary['debug']}")
    print(f"Database: {summary['database_type']}")
    print()
    
    # Show API status
    print("API Configuration:")
    for api, configured in summary['api_keys_configured'].items():
        status = "✅ Configured" if configured else "❌ Missing"
        print(f"  {api}: {status}")
    print()
    
    # Show processing settings
    proc = summary['processing']
    print(f"Processing: {proc['batch_size']} batch size, {proc['target_cities']} cities, {proc['target_sectors']} sectors")
    print()
    
    # Validate configuration
    warnings = config.validate()
    if warnings:
        print("Configuration Warnings:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
    else:
        print("✅ Configuration validation passed")
    
    print("\nEnvironment Variables Help:")
    print(ENV_DOCS) 