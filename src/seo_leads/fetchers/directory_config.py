"""
Directory Configuration for UK Business Directory Scrapers

Centralized configuration and metadata for all supported UK business directories.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class DirectoryConfig:
    """Configuration for a business directory"""
    name: str
    base_url: str
    description: str
    coverage: str  # Geographic coverage
    specialties: List[str]  # Business types this directory excels at
    rate_limit_ms: int  # Milliseconds between requests
    max_pages: int  # Maximum pages to scrape per search
    reliability: str  # High, Medium, Low
    data_quality: str  # Excellent, Good, Fair
    website_availability: str  # Often, Sometimes, Rarely
    

# Directory configurations
DIRECTORY_CONFIGS = {
    'yell': DirectoryConfig(
        name="Yell.com",
        base_url="https://www.yell.com",
        description="UK's largest business directory with comprehensive coverage",
        coverage="National UK",
        specialties=["All sectors", "Local businesses", "Service providers"],
        rate_limit_ms=2000,
        max_pages=10,
        reliability="High",
        data_quality="Excellent",
        website_availability="Often"
    ),
    
    'thomson': DirectoryConfig(
        name="Thomson Local",
        base_url="https://www.thomsonlocal.com",
        description="Established UK business directory with long history",
        coverage="National UK",
        specialties=["Local services", "Tradespeople", "Professional services"],
        rate_limit_ms=1500,
        max_pages=8,
        reliability="High",
        data_quality="Good",
        website_availability="Sometimes"
    ),
    
    'yelp': DirectoryConfig(
        name="Yelp UK",
        base_url="https://www.yelp.co.uk",
        description="Review-based business directory with detailed business info",
        coverage="Major UK cities",
        specialties=["Restaurants", "Retail", "Entertainment", "Services"],
        rate_limit_ms=2500,
        max_pages=6,
        reliability="Medium",
        data_quality="Good",
        website_availability="Sometimes"
    ),
    
    'cylex': DirectoryConfig(
        name="Cylex UK",
        base_url="https://www.cylex-uk.co.uk",
        description="European business directory with UK coverage",
        coverage="National UK",
        specialties=["Professional services", "B2B companies", "Manufacturing"],
        rate_limit_ms=1800,
        max_pages=7,
        reliability="Medium",
        data_quality="Good",
        website_availability="Sometimes"
    ),
    
    'hotfrog': DirectoryConfig(
        name="Hotfrog UK",
        base_url="https://www.hotfrog.co.uk",
        description="Global business directory with dedicated UK section",
        coverage="National UK",
        specialties=["SME businesses", "Professional services", "Technology"],
        rate_limit_ms=2000,
        max_pages=8,
        reliability="Medium",
        data_quality="Good",
        website_availability="Often"
    ),
    
    'brownbook': DirectoryConfig(
        name="Brownbook UK",
        base_url="https://uk.brownbook.net",
        description="Multi-category business directory with UK coverage",
        coverage="National UK",
        specialties=["Diverse industries", "Local businesses", "Services"],
        rate_limit_ms=1500,
        max_pages=6,
        reliability="Medium",
        data_quality="Fair",
        website_availability="Rarely"
    ),
    
    'ukcom': DirectoryConfig(
        name="UK.COM",
        base_url="https://www.uk.com",
        description="UK-specific business directory",
        coverage="National UK",
        specialties=["Local businesses", "Services", "Retail"],
        rate_limit_ms=1800,
        max_pages=7,
        reliability="Medium",
        data_quality="Good",
        website_availability="Sometimes"
    ),
    
    'businessmagnet': DirectoryConfig(
        name="Business Magnet",
        base_url="https://www.businessmagnet.co.uk",
        description="UK business directory with comprehensive listings",
        coverage="National UK",
        specialties=["B2B services", "Professional services", "Manufacturing"],
        rate_limit_ms=2000,
        max_pages=6,
        reliability="Medium",
        data_quality="Fair",
        website_availability="Rarely"
    ),
    
    'tupalo': DirectoryConfig(
        name="Tupalo UK",
        base_url="https://tupalo.co.uk",
        description="Social business directory with UK coverage",
        coverage="Major UK cities",
        specialties=["Restaurants", "Entertainment", "Retail", "Services"],
        rate_limit_ms=1500,
        max_pages=5,
        reliability="Low",
        data_quality="Fair",
        website_availability="Rarely"
    ),
    
    'foursquare': DirectoryConfig(
        name="Foursquare UK",
        base_url="https://foursquare.com",
        description="Location-based business data and listings",
        coverage="Major UK cities",
        specialties=["Restaurants", "Retail", "Entertainment", "Services"],
        rate_limit_ms=3000,
        max_pages=5,
        reliability="Medium",
        data_quality="Good",
        website_availability="Rarely"
    ),
    
    '192': DirectoryConfig(
        name="192.com",
        base_url="https://www.192.com",
        description="Comprehensive UK business directory with extensive coverage",
        coverage="National UK",
        specialties=["All sectors", "Local businesses", "Professional services"],
        rate_limit_ms=2000,
        max_pages=8,
        reliability="High",
        data_quality="Good",
        website_availability="Sometimes"
    )
}


# Priority groups for different use cases
PRIORITY_GROUPS = {
    'high_quality': ['yell', 'thomson', '192', 'hotfrog'],
    'good_coverage': ['yell', 'thomson', '192', 'cylex', 'ukcom'],
    'website_rich': ['yell', 'hotfrog', 'thomson'],
    'restaurant_focused': ['yelp', 'foursquare', 'tupalo', 'yell'],
    'b2b_focused': ['cylex', 'businessmagnet', 'yell', 'thomson'],
    'professional_services': ['thomson', 'cylex', 'yell', 'ukcom'],
    'all_sources': list(DIRECTORY_CONFIGS.keys())
}


def get_config(source: str) -> DirectoryConfig:
    """Get configuration for a directory source"""
    if source not in DIRECTORY_CONFIGS:
        available = ', '.join(DIRECTORY_CONFIGS.keys())
        raise ValueError(f"Unknown source '{source}'. Available: {available}")
    return DIRECTORY_CONFIGS[source]


def get_sources_by_priority(priority_group: str) -> List[str]:
    """Get list of sources for a priority group"""
    if priority_group not in PRIORITY_GROUPS:
        available = ', '.join(PRIORITY_GROUPS.keys())
        raise ValueError(f"Unknown priority group '{priority_group}'. Available: {available}")
    return PRIORITY_GROUPS[priority_group]


def get_recommended_sources(sector: Optional[str] = None, 
                          quality_focus: bool = True) -> List[str]:
    """
    Get recommended sources based on sector and quality requirements
    
    Args:
        sector: Target business sector (e.g., 'restaurant', 'professional')
        quality_focus: Whether to prioritize high-quality sources
        
    Returns:
        List of recommended source names
    """
    if quality_focus:
        base_sources = PRIORITY_GROUPS['high_quality']
    else:
        base_sources = PRIORITY_GROUPS['good_coverage']
    
    # Add sector-specific sources
    if sector:
        sector_lower = sector.lower()
        if 'restaurant' in sector_lower or 'food' in sector_lower:
            base_sources.extend(['yelp', 'foursquare'])
        elif 'professional' in sector_lower or 'legal' in sector_lower:
            base_sources.extend(['cylex', 'ukcom'])
        elif 'retail' in sector_lower or 'shop' in sector_lower:
            base_sources.extend(['yelp', 'ukcom'])
    
    # Remove duplicates while preserving order
    seen = set()
    result = []
    for source in base_sources:
        if source not in seen:
            seen.add(source)
            result.append(source)
    
    return result


# UK Cities for testing and common searches
UK_MAJOR_CITIES = [
    'London', 'Birmingham', 'Manchester', 'Glasgow', 'Liverpool',
    'Leeds', 'Sheffield', 'Edinburgh', 'Bristol', 'Cardiff',
    'Leicester', 'Coventry', 'Bradford', 'Belfast', 'Nottingham',
    'Hull', 'Newcastle', 'Stoke-on-Trent', 'Southampton', 'Derby',
    'Portsmouth', 'Brighton', 'Plymouth', 'Northampton', 'Reading',
    'Luton', 'Wolverhampton', 'Bolton', 'Bournemouth', 'Norwich'
]

# Common business sectors for UK market
UK_BUSINESS_SECTORS = [
    'restaurant', 'retail', 'construction', 'professional services',
    'healthcare', 'technology', 'automotive', 'education', 'hospitality',
    'financial services', 'manufacturing', 'real estate', 'legal',
    'marketing', 'consulting', 'fitness', 'beauty', 'entertainment'
] 