#!/usr/bin/env python3
"""
Test Data Setup Script
Adds sample companies to database for end-to-end testing
"""

import sys
import uuid
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from seo_leads.database import get_db_session
from seo_leads.models import UKCompany

def add_test_companies():
    """Add test companies to database"""
    
    test_companies = [
        {
            'company_name': 'Brighton Digital Solutions',
            'website': 'https://example.com',
            'city': 'Brighton',
            'sector': 'technology',
            'address': '123 High Street, Brighton',
            'phone': '01273 123456',
            'employees': 15,
            'size_category': 'small',
            'status': 'scraped'
        },
        {
            'company_name': 'Sussex Web Design', 
            'website': 'https://sussexwebdesign.co.uk',
            'city': 'Brighton',
            'sector': 'technology',
            'address': '456 North Street, Brighton',
            'employees': 8,
            'size_category': 'small',
            'status': 'scraped'
        },
        {
            'company_name': 'Brighton Marketing Agency',
            'website': 'https://brightonmarketing.com',
            'city': 'Brighton', 
            'sector': 'marketing',
            'address': '789 West Street, Brighton',
            'employees': 25,
            'size_category': 'medium',
            'status': 'scraped'
        },
        {
            'company_name': 'Local Retail Store',
            'website': 'https://localretail.co.uk',
            'city': 'Brighton',
            'sector': 'retail',
            'address': '321 Queen Street, Brighton',
            'employees': 5,
            'size_category': 'micro',
            'status': 'scraped'
        },
        {
            'company_name': 'Professional Services Ltd',
            'website': 'https://profservices.co.uk',
            'city': 'Brighton',
            'sector': 'professional_services',
            'address': '654 King Street, Brighton',
            'employees': 50,
            'size_category': 'medium',
            'status': 'scraped'
        }
    ]
    
    with get_db_session() as session:
        for company_data in test_companies:
            company = UKCompany(
                id=str(uuid.uuid4()),
                **company_data
            )
            session.add(company)
        session.commit()
        
    print(f'✅ Added {len(test_companies)} test companies to database')
    return len(test_companies)

if __name__ == '__main__':
    add_test_companies() 