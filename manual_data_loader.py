"""
Manual Data Loader - Component 1 of Comprehensive 20-URL Validation Project

This module loads and structures the manually collected reference data from 1Testfinal.xlsx
for comparison against our system's executive extraction results.

Author: AI Assistant
Date: 2025-01-19
Project: SEO Lead Generation - Comprehensive Validation Framework
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ManualDataLoader:
    """
    Loads and structures manual reference data from Excel file for validation comparison.
    
    The Excel file (1Testfinal.xlsx) contains manually verified executive information
    that serves as the ground truth for validating our automated extraction system.
    """
    
    def __init__(self, excel_file_path: str = "1Testfinal.xlsx"):
        """
        Initialize the Manual Data Loader.
        
        Args:
            excel_file_path (str): Path to the Excel file containing manual data
        """
        self.excel_file_path = excel_file_path
        self.raw_data = None
        self.structured_data = None
        self.url_mapping = {}
        
    def load_reference_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load and structure reference data from Excel file, grouped by website URL.
        
        Returns:
            Dict[str, List[Dict]]: Dictionary with URLs as keys and lists of executives as values
        """
        try:
            # Load Excel file
            logger.info(f"Loading reference data from {self.excel_file_path}")
            self.raw_data = pd.read_excel(self.excel_file_path)
            
            logger.info(f"Loaded {len(self.raw_data)} rows from Excel file")
            logger.info(f"Columns: {list(self.raw_data.columns)}")
            
            # Structure data by URL
            self.structured_data = self._structure_by_url()
            
            # Create URL mapping for lookup
            self._create_url_mapping()
            
            logger.info(f"Structured data for {len(self.structured_data)} unique URLs")
            return self.structured_data
            
        except Exception as e:
            logger.error(f"Error loading reference data: {str(e)}")
            raise
    
    def _structure_by_url(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Structure the raw data by website URL.
        
        Returns:
            Dict[str, List[Dict]]: URL-keyed dictionary with executive data
        """
        structured = {}
        
        for _, row in self.raw_data.iterrows():
            # Clean and normalize URL
            url = self._normalize_url(row['Website'])
            
            # Create executive record
            executive = {
                'company_name': row['Company Name'],
                'website': url,
                'first_name': row['Owner First Name'],
                'last_name': row['Owner Last Name'],
                'full_name': f"{row['Owner First Name']} {row['Owner Last Name']}".strip(),
                'title': row['Title'],
                'email': row['Company Email'] if pd.notna(row['Company Email']) else None,
                'phone': row['Phone #'] if pd.notna(row['Phone #']) else None,
                'direct_phone': row['Direct #'] if pd.notna(row['Direct #']) else None,
                'mobile': row['Mobile #'] if pd.notna(row['Mobile #']) else None,
                'linkedin_url': row['Linkedin Profile URL'] if pd.notna(row['Linkedin Profile URL']) else None,
                'address': {
                    'street': row['Street'] if pd.notna(row['Street']) else None,
                    'city': row['City'] if pd.notna(row['City']) else None,
                    'state': row['Province/State'] if pd.notna(row['Province/State']) else None,
                    'zip_code': row['Zip Code'] if pd.notna(row['Zip Code']) else None
                },
                'employee_count': row['~Employee Count'] if pd.notna(row['~Employee Count']) else None,
                'contractor_market': row['Contractor Market'] if pd.notna(row['Contractor Market']) else None,
                'age_range': row["Owner's ~Age"] if pd.notna(row["Owner's ~Age"]) else None,
                'source': 'manual_verification'
            }
            
            # Add to structured data
            if url not in structured:
                structured[url] = []
            structured[url].append(executive)
        
        return structured
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL for consistent comparison.
        
        Args:
            url (str): Raw URL from Excel
            
        Returns:
            str: Normalized URL
        """
        if pd.isna(url) or not url:
            return ""
        
        url = str(url).strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        # Remove trailing slash
        url = url.rstrip('/')
        
        # Convert to lowercase for consistency
        url = url.lower()
        
        return url
    
    def _create_url_mapping(self):
        """Create mapping for URL variations and lookup."""
        self.url_mapping = {}
        
        for url in self.structured_data.keys():
            # Map the main URL
            self.url_mapping[url] = url
            
            # Map variations (with/without www, with/without protocol)
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Create variations
            variations = [
                url,
                url.replace('http://', 'https://'),
                url.replace('https://', 'http://'),
                domain,
                'www.' + domain if not domain.startswith('www.') else domain.replace('www.', ''),
                parsed.netloc.replace('www.', '') if domain.startswith('www.') else 'www.' + parsed.netloc
            ]
            
            for variation in variations:
                self.url_mapping[variation] = url
    
    def get_reference_executives(self, url: str) -> List[Dict[str, Any]]:
        """
        Get manual executives for a specific URL.
        
        Args:
            url (str): Website URL to lookup
            
        Returns:
            List[Dict]: List of executive records for the URL
        """
        # Normalize the input URL
        normalized_url = self._normalize_url(url)
        
        # Try direct lookup
        if normalized_url in self.structured_data:
            return self.structured_data[normalized_url]
        
        # Try URL mapping lookup
        if normalized_url in self.url_mapping:
            mapped_url = self.url_mapping[normalized_url]
            return self.structured_data.get(mapped_url, [])
        
        # Try fuzzy matching for similar URLs
        return self._fuzzy_url_match(normalized_url)
    
    def _fuzzy_url_match(self, url: str) -> List[Dict[str, Any]]:
        """
        Attempt fuzzy matching for URL lookup.
        
        Args:
            url (str): URL to match
            
        Returns:
            List[Dict]: Matching executives or empty list
        """
        parsed_target = urlparse(url)
        target_domain = parsed_target.netloc.replace('www.', '')
        
        for reference_url in self.structured_data.keys():
            parsed_ref = urlparse(reference_url)
            ref_domain = parsed_ref.netloc.replace('www.', '')
            
            if target_domain == ref_domain:
                logger.info(f"Fuzzy matched {url} to {reference_url}")
                return self.structured_data[reference_url]
        
        logger.warning(f"No reference data found for URL: {url}")
        return []
    
    def get_all_urls(self) -> List[str]:
        """
        Get list of all URLs in the reference data.
        
        Returns:
            List[str]: List of all website URLs
        """
        if self.structured_data is None:
            self.load_reference_data()
        
        return list(self.structured_data.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the loaded reference data.
        
        Returns:
            Dict[str, Any]: Statistics about the reference data
        """
        if self.structured_data is None:
            self.load_reference_data()
        
        total_executives = sum(len(execs) for execs in self.structured_data.values())
        
        # Count executives with various contact types
        executives_with_email = 0
        executives_with_linkedin = 0
        executives_with_phone = 0
        executives_with_direct_phone = 0
        executives_with_mobile = 0
        
        for executives in self.structured_data.values():
            for exec_data in executives:
                if exec_data.get('email'):
                    executives_with_email += 1
                if exec_data.get('linkedin_url'):
                    executives_with_linkedin += 1
                if exec_data.get('phone'):
                    executives_with_phone += 1
                if exec_data.get('direct_phone'):
                    executives_with_direct_phone += 1
                if exec_data.get('mobile'):
                    executives_with_mobile += 1
        
        return {
            'total_unique_urls': len(self.structured_data),
            'total_executives': total_executives,
            'executives_with_email': executives_with_email,
            'executives_with_linkedin': executives_with_linkedin,
            'executives_with_phone': executives_with_phone,
            'executives_with_direct_phone': executives_with_direct_phone,
            'executives_with_mobile': executives_with_mobile,
            'email_coverage_percentage': (executives_with_email / total_executives) * 100,
            'linkedin_coverage_percentage': (executives_with_linkedin / total_executives) * 100,
            'phone_coverage_percentage': (executives_with_phone / total_executives) * 100
        }
    
    def export_structured_data(self, output_file: str = "manual_reference_data.json"):
        """
        Export structured data to JSON file for inspection.
        
        Args:
            output_file (str): Output JSON file path
        """
        import json
        
        if self.structured_data is None:
            self.load_reference_data()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.structured_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported structured reference data to {output_file}")


def main():
    """Test the Manual Data Loader with the Excel file."""
    try:
        # Initialize loader
        loader = ManualDataLoader()
        
        # Load reference data
        reference_data = loader.load_reference_data()
        
        # Print statistics
        stats = loader.get_statistics()
        print("\n=== MANUAL REFERENCE DATA STATISTICS ===")
        print(f"Total unique URLs: {stats['total_unique_urls']}")
        print(f"Total executives: {stats['total_executives']}")
        print(f"Executives with email: {stats['executives_with_email']} ({stats['email_coverage_percentage']:.1f}%)")
        print(f"Executives with LinkedIn: {stats['executives_with_linkedin']} ({stats['linkedin_coverage_percentage']:.1f}%)")
        print(f"Executives with phone: {stats['executives_with_phone']} ({stats['phone_coverage_percentage']:.1f}%)")
        
        # Print URLs for testing
        print("\n=== URLS FOR TESTING ===")
        urls = loader.get_all_urls()
        for i, url in enumerate(urls, 1):
            execs = loader.get_reference_executives(url)
            print(f"{i:2d}. {url} ({len(execs)} executives)")
        
        # Export structured data
        loader.export_structured_data()
        
        print(f"\n✅ Manual Data Loader completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 