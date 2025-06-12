"""
Firmographic Data Normaliser

Unifies company data from different providers into consistent formats.
Handles industry codes, employee counts, company sizes, and other firmographic data.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from enrichment_service.core.models import CompanySize, CompanyEnrichment

class FirmographicNormaliser:
    """Normalise firmographic data from multiple sources"""
    
    def __init__(self):
        # Industry mappings
        self.sic_to_industry = self._load_sic_mappings()
        self.industry_aliases = self._load_industry_aliases()
        
        # Employee count patterns
        self.employee_patterns = [
            (r'(\d+)-(\d+)', 'range'),
            (r'(\d+)\+', 'minimum'),
            (r'over\s+(\d+)', 'minimum'),
            (r'under\s+(\d+)', 'maximum'),
            (r'(\d+)', 'exact')
        ]
    
    def normalise_company_data(self, *company_data: CompanyEnrichment) -> CompanyEnrichment:
        """Merge and normalise multiple company enrichment results"""
        if not company_data:
            return CompanyEnrichment(confidence=0.0)
        
        # Start with the highest confidence data as base
        sorted_data = sorted(company_data, key=lambda x: x.confidence, reverse=True)
        base_company = sorted_data[0]
        
        # Merge data from other sources
        merged = CompanyEnrichment(
            company_number=self._merge_field('company_number', *company_data),
            legal_name=self._merge_field('legal_name', *company_data),
            trading_names=self._merge_list_field('trading_names', *company_data),
            description=self._merge_field('description', *company_data),
            industry=self._normalise_industry(*company_data),
            sic_codes=self._merge_list_field('sic_codes', *company_data),
            employee_count=self._normalise_employee_count(*company_data),
            employee_range=self._normalise_employee_range(*company_data),
            size_category=self._normalise_company_size(*company_data),
            founded_year=self._merge_field('founded_year', *company_data),
            phone=self._merge_field('phone', *company_data),
            address=self._merge_address(*company_data),
            confidence=self._calculate_merged_confidence(*company_data),
            last_updated=datetime.utcnow()
        )
        
        return merged
    
    def _merge_field(self, field_name: str, *companies: CompanyEnrichment) -> Optional[Any]:
        """Merge a single field from multiple sources, preferring non-empty values"""
        for company in companies:
            value = getattr(company, field_name)
            if value is not None and value != '':
                return value
        return None
    
    def _merge_list_field(self, field_name: str, *companies: CompanyEnrichment) -> List[str]:
        """Merge list fields from multiple sources, removing duplicates"""
        merged_list = []
        seen = set()
        
        for company in companies:
            values = getattr(company, field_name) or []
            for value in values:
                if value and value not in seen:
                    merged_list.append(value)
                    seen.add(value)
        
        return merged_list
    
    def _normalise_industry(self, *companies: CompanyEnrichment) -> Optional[str]:
        """Normalise industry from multiple sources"""
        industries = []
        sic_codes = []
        
        # Collect all industry data
        for company in companies:
            if company.industry:
                industries.append(company.industry)
            if company.sic_codes:
                sic_codes.extend(company.sic_codes)
        
        # Prefer explicit industry classifications
        if industries:
            # Normalise to standard industry names
            normalised = self._standardise_industry_name(industries[0])
            return normalised
        
        # Fallback to SIC code mapping
        if sic_codes:
            industry_from_sic = self._map_sic_to_industry(sic_codes[0])
            if industry_from_sic:
                return industry_from_sic
        
        return None
    
    def _normalise_employee_count(self, *companies: CompanyEnrichment) -> Optional[int]:
        """Normalise employee count from multiple sources"""
        # Direct employee count (most reliable)
        for company in companies:
            if company.employee_count is not None:
                return company.employee_count
        
        # Parse from employee range
        for company in companies:
            if company.employee_range:
                count = self._parse_employee_count_from_range(company.employee_range)
                if count:
                    return count
        
        # Estimate from company size
        for company in companies:
            if company.size_category:
                return self._estimate_count_from_size(company.size_category)
        
        return None
    
    def _normalise_employee_range(self, *companies: CompanyEnrichment) -> Optional[str]:
        """Normalise employee range from multiple sources"""
        # Use explicit range if available
        for company in companies:
            if company.employee_range:
                return self._standardise_employee_range(company.employee_range)
        
        # Generate from employee count
        for company in companies:
            if company.employee_count is not None:
                return self._generate_range_from_count(company.employee_count)
        
        # Generate from size category
        for company in companies:
            if company.size_category:
                return self._generate_range_from_size(company.size_category)
        
        return None
    
    def _normalise_company_size(self, *companies: CompanyEnrichment) -> Optional[CompanySize]:
        """Normalise company size from multiple sources"""
        # Use explicit size category if available
        for company in companies:
            if company.size_category:
                return company.size_category
        
        # Determine from employee count
        for company in companies:
            if company.employee_count is not None:
                return self._determine_size_from_count(company.employee_count)
        
        # Parse from employee range
        for company in companies:
            if company.employee_range:
                count = self._parse_employee_count_from_range(company.employee_range)
                if count:
                    return self._determine_size_from_count(count)
        
        return None
    
    def _merge_address(self, *companies: CompanyEnrichment) -> Optional[Dict[str, str]]:
        """Merge address information from multiple sources"""
        merged_address = {}
        
        for company in companies:
            if company.address:
                for key, value in company.address.items():
                    if value and key not in merged_address:
                        merged_address[key] = value
        
        return merged_address if merged_address else None
    
    def _calculate_merged_confidence(self, *companies: CompanyEnrichment) -> float:
        """Calculate confidence for merged data"""
        if not companies:
            return 0.0
        
        # Weight by data completeness and source confidence
        total_weight = 0.0
        weighted_confidence = 0.0
        
        for company in companies:
            # Calculate data completeness
            completeness = self._calculate_data_completeness(company)
            weight = completeness * company.confidence
            
            weighted_confidence += weight * company.confidence
            total_weight += weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def _calculate_data_completeness(self, company: CompanyEnrichment) -> float:
        """Calculate how complete the company data is"""
        fields = [
            company.legal_name, company.industry, company.employee_count,
            company.founded_year, company.address, company.phone
        ]
        
        filled_fields = sum(1 for field in fields if field)
        return filled_fields / len(fields)
    
    # Helper methods for industry normalisation
    def _standardise_industry_name(self, industry: str) -> str:
        """Standardise industry name to common format"""
        industry = industry.lower().strip()
        
        # Check aliases
        for standard_name, aliases in self.industry_aliases.items():
            if industry in aliases:
                return standard_name.title()
        
        return industry.title()
    
    def _map_sic_to_industry(self, sic_code: str) -> Optional[str]:
        """Map SIC code to industry name"""
        # Remove any non-numeric characters
        clean_code = re.sub(r'[^\d]', '', sic_code)
        
        if clean_code in self.sic_to_industry:
            return self.sic_to_industry[clean_code]
        
        # Try prefix matching for broader categories
        for length in range(4, 1, -1):
            prefix = clean_code[:length]
            if prefix in self.sic_to_industry:
                return self.sic_to_industry[prefix]
        
        return None
    
    # Helper methods for employee data
    def _parse_employee_count_from_range(self, employee_range: str) -> Optional[int]:
        """Parse employee count from range string"""
        for pattern, range_type in self.employee_patterns:
            match = re.search(pattern, employee_range.lower())
            if match:
                if range_type == 'range':
                    # Take midpoint of range
                    low, high = int(match.group(1)), int(match.group(2))
                    return (low + high) // 2
                elif range_type == 'minimum':
                    # Add 50% to minimum for estimate
                    return int(int(match.group(1)) * 1.5)
                elif range_type == 'maximum':
                    # Take 50% of maximum
                    return int(int(match.group(1)) * 0.5)
                elif range_type == 'exact':
                    return int(match.group(1))
        
        return None
    
    def _estimate_count_from_size(self, size: CompanySize) -> int:
        """Estimate employee count from company size category"""
        size_estimates = {
            CompanySize.MICRO: 5,
            CompanySize.SMALL: 25,
            CompanySize.MEDIUM: 125,
            CompanySize.LARGE: 500,
            CompanySize.ENTERPRISE: 2000
        }
        return size_estimates.get(size, 25)
    
    def _standardise_employee_range(self, employee_range: str) -> str:
        """Standardise employee range format"""
        # Extract numbers and create standard format
        numbers = re.findall(r'\d+', employee_range)
        if len(numbers) == 2:
            return f"{numbers[0]}-{numbers[1]} employees"
        elif len(numbers) == 1:
            if 'over' in employee_range.lower() or '+' in employee_range:
                return f"{numbers[0]}+ employees"
            elif 'under' in employee_range.lower():
                return f"Under {numbers[0]} employees"
            else:
                return f"{numbers[0]} employees"
        
        return employee_range
    
    def _generate_range_from_count(self, count: int) -> str:
        """Generate employee range from exact count"""
        if count < 10:
            return "1-9 employees"
        elif count < 50:
            return "10-49 employees"
        elif count < 250:
            return "50-249 employees"
        elif count < 1000:
            return "250-999 employees"
        else:
            return "1000+ employees"
    
    def _generate_range_from_size(self, size: CompanySize) -> str:
        """Generate employee range from size category"""
        size_ranges = {
            CompanySize.MICRO: "1-9 employees",
            CompanySize.SMALL: "10-49 employees",
            CompanySize.MEDIUM: "50-249 employees",
            CompanySize.LARGE: "250-999 employees",
            CompanySize.ENTERPRISE: "1000+ employees"
        }
        return size_ranges.get(size, "Unknown")
    
    def _determine_size_from_count(self, count: int) -> CompanySize:
        """Determine company size from employee count"""
        if count < 10:
            return CompanySize.MICRO
        elif count < 50:
            return CompanySize.SMALL
        elif count < 250:
            return CompanySize.MEDIUM
        elif count < 1000:
            return CompanySize.LARGE
        else:
            return CompanySize.ENTERPRISE
    
    # Data mappings
    def _load_sic_mappings(self) -> Dict[str, str]:
        """Load SIC code to industry mappings"""
        return {
            # Services
            '62': 'Computer Programming',
            '63': 'Information Services',
            '64': 'Financial Services',
            '68': 'Real Estate',
            '69': 'Legal Services',
            '70': 'Consulting',
            '73': 'Advertising',
            '74': 'Professional Services'
        }
    
    def _load_industry_aliases(self) -> Dict[str, List[str]]:
        """Load industry name aliases for standardisation"""
        return {
            'Technology': ['tech', 'it', 'software', 'computing', 'digital'],
            'Healthcare': ['health', 'medical', 'pharmaceutical', 'biotech'],
            'Financial Services': ['finance', 'banking', 'fintech', 'insurance'],
            'Retail': ['retail', 'ecommerce', 'e-commerce', 'shopping'],
            'Consulting': ['consulting', 'advisory', 'professional services'],
            'Real Estate': ['real estate', 'property', 'construction']
        } 