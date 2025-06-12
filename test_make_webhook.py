#!/usr/bin/env python3
"""
Test Make.com Webhook Integration

Tests the webhook connection and sends sample lead data to your Make.com scenario.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from src.seo_leads.integrations.make_webhook import (
    MakeWebhookSender, 
    WebhookEventType, 
    MakePayloadFormat,
    test_webhook_connection
)
from src.seo_leads.models import UKCompany, PriorityTier

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Your Make.com webhook URL
WEBHOOK_URL = "https://hook.eu2.make.com/7cdm5zriyb8ka86af1c4otia2vxbt61h"

def create_sample_company() -> UKCompany:
    """Create a sample company for testing"""
    company = UKCompany(
        id="test_company_123",
        company_name="Brighton Digital Solutions",
        website="https://brightondigital.co.uk",
        city="Brighton",
        region="East Sussex",
        address="123 North Street, Brighton BN1 1RF",
        sector="digital-marketing",
        source="Yelp UK",
        
        # Contact information
        contact_person="Sarah Mitchell",
        contact_role="Marketing Director", 
        contact_seniority_tier="tier_2",
        email="sarah@brightondigital.co.uk",
        phone="01273 555123",
        linkedin_url="https://linkedin.com/in/sarah-mitchell-marketing",
        contact_confidence=0.85,
        contact_extraction_method="linkedin_scraping",
        
        # SEO analysis
        seo_overall_score=34.5,
        pagespeed_score=28,
        mobile_friendly=False,
        meta_description_missing=True,
        h1_tags_present=False,
        ssl_certificate=True,
        load_time=4.8,
        critical_issues=[
            "No meta descriptions on key pages",
            "Poor mobile performance (28/100)",
            "Slow page load times (4.8s average)",
            "Missing H1 tags on product pages",
            "Images not optimized for web"
        ],
        
        # Lead qualification
        lead_score=78.5,
        priority_tier=PriorityTier.B.value,
        tier_label="Warm Lead",
        factor_breakdown={
            "seo_opportunity": {"score": 85, "weight": 0.35, "contribution": 29.75},
            "business_size": {"score": 70, "weight": 0.25, "contribution": 17.5},
            "sector_fit": {"score": 90, "weight": 0.20, "contribution": 18.0},
            "growth_indicators": {"score": 65, "weight": 0.10, "contribution": 6.5},
            "contact_quality": {"score": 87, "weight": 0.10, "contribution": 8.7}
        },
        estimated_value="£2,500-5,000",
        urgency="high",
        recommended_actions=[
            "SEO audit presentation",
            "Mobile optimization proposal", 
            "Page speed improvement plan",
            "Content strategy consultation"
        ],
        talking_points=[
            "Your website loads 70% slower than industry average",
            "Missing meta descriptions are costing you search visibility",
            "Mobile users can't properly navigate your site",
            "We helped similar agencies increase leads by 40% with SEO fixes",
            "Your competitors are ranking higher for key search terms"
        ]
    )
    
    return company

def create_high_priority_company() -> UKCompany:
    """Create a high-priority A-tier company for testing"""
    company = UKCompany(
        id="high_priority_456",
        company_name="Elite Restaurant Group",
        website="https://eliterestaurants.co.uk",
        city="London", 
        region="Greater London",
        address="45 Covent Garden, London WC2E 8RF",
        sector="hospitality",
        source="Yell.com",
        
        # Contact information
        contact_person="David Thompson",
        contact_role="CEO & Founder",
        contact_seniority_tier="tier_1",
        email="david@eliterestaurants.co.uk", 
        phone="020 7946 0123",
        linkedin_url="https://linkedin.com/in/david-thompson-restaurants",
        contact_confidence=0.92,
        contact_extraction_method="company_website",
        
        # SEO analysis  
        seo_overall_score=28.0,
        pagespeed_score=19,
        mobile_friendly=False,
        meta_description_missing=True,
        h1_tags_present=False,
        ssl_certificate=False,
        load_time=6.2,
        critical_issues=[
            "No SSL certificate - major security issue",
            "Extremely slow loading (6.2s)",
            "Mobile site completely broken",
            "No meta descriptions or titles",
            "Missing Google My Business optimization"
        ],
        
        # Lead qualification
        lead_score=94.5,
        priority_tier=PriorityTier.A.value,
        tier_label="Hot Lead",
        estimated_value="£15,000-25,000",
        urgency="immediate",
        recommended_actions=[
            "URGENT: SSL certificate installation",
            "Emergency mobile site fix",
            "Google My Business optimization",
            "Local SEO campaign launch"
        ],
        talking_points=[
            "CRITICAL: Your site has no SSL - customers see security warnings",
            "You're losing 80% of mobile customers due to broken site",
            "Competitors dominate Google searches for your restaurant types",
            "We can fix critical issues and boost bookings within 30 days"
        ]
    )
    
    return company

async def test_basic_connection():
    """Test basic webhook connection"""
    print("🔗 Testing Make.com webhook connection...")
    
    success = await test_webhook_connection(WEBHOOK_URL)
    if success:
        print("✅ Webhook connection successful!")
        return True
    else:
        print("❌ Webhook connection failed!")
        return False

async def test_sample_lead():
    """Test sending a sample lead"""
    print("\n📤 Testing sample lead delivery...")
    
    # Create sample company
    company = create_sample_company()
    
    # Send to Make.com
    sender = MakeWebhookSender(webhook_url=WEBHOOK_URL)
    success = await sender.send_lead(company, WebhookEventType.NEW_LEAD, MakePayloadFormat.FULL_LEAD)
    
    if success:
        print("✅ Sample lead sent successfully!")
        print(f"   Company: {company.company_name}")
        print(f"   Lead Score: {company.lead_score}")
        print(f"   Priority: {company.tier_label}")
        return True
    else:
        print("❌ Failed to send sample lead!")
        return False

async def test_high_priority_alert():
    """Test high-priority alert"""
    print("\n🚨 Testing high-priority alert...")
    
    # Create A-tier company
    company = create_high_priority_company()
    
    # Send high-priority alert
    sender = MakeWebhookSender(webhook_url=WEBHOOK_URL)
    success = await sender.send_high_priority_alert(company)
    
    if success:
        print("✅ High-priority alert sent successfully!")
        print(f"   Company: {company.company_name}")
        print(f"   Lead Score: {company.lead_score}")
        print(f"   Urgency: {company.urgency}")
        return True
    else:
        print("❌ Failed to send high-priority alert!")
        return False

async def test_batch_delivery():
    """Test batch delivery"""
    print("\n📦 Testing batch delivery...")
    
    # Create multiple sample companies
    companies = [
        create_sample_company(),
        create_high_priority_company()
    ]
    
    # Modify IDs to make them unique
    companies[0].id = "batch_test_1"
    companies[0].company_name = "Test Company 1"
    companies[1].id = "batch_test_2" 
    companies[1].company_name = "Test Company 2"
    
    # Send batch
    sender = MakeWebhookSender(webhook_url=WEBHOOK_URL)
    results = await sender.send_batch(companies, WebhookEventType.NEW_LEAD, MakePayloadFormat.SUMMARY)
    
    print(f"✅ Batch delivery complete!")
    print(f"   Total attempted: {results['total_attempted']}")
    print(f"   Successful: {results['successful']}")
    print(f"   Failed: {results['failed']}")
    
    return results['successful'] > 0

async def main():
    """Run all webhook tests"""
    print("🚀 Make.com Webhook Integration Test")
    print("=" * 50)
    print(f"Webhook URL: {WEBHOOK_URL}")
    print()
    
    all_tests_passed = True
    
    # Test 1: Basic connection
    try:
        connection_success = await test_basic_connection()
        all_tests_passed = all_tests_passed and connection_success
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        all_tests_passed = False
    
    # Test 2: Sample lead
    if all_tests_passed:
        try:
            lead_success = await test_sample_lead()
            all_tests_passed = all_tests_passed and lead_success
        except Exception as e:
            print(f"❌ Sample lead test error: {e}")
            all_tests_passed = False
    
    # Test 3: High-priority alert
    if all_tests_passed:
        try:
            alert_success = await test_high_priority_alert()
            all_tests_passed = all_tests_passed and alert_success
        except Exception as e:
            print(f"❌ High-priority alert test error: {e}")
            all_tests_passed = False
    
    # Test 4: Batch delivery
    if all_tests_passed:
        try:
            batch_success = await test_batch_delivery()
            all_tests_passed = all_tests_passed and batch_success
        except Exception as e:
            print(f"❌ Batch delivery test error: {e}")
            all_tests_passed = False
    
    # Final results
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! Make.com integration is working perfectly!")
        print("\n📋 What was tested:")
        print("✅ Webhook connectivity")
        print("✅ Sample lead delivery (B-tier)")
        print("✅ High-priority alert (A-tier)")  
        print("✅ Batch delivery")
        print("\n🔗 Your Make.com scenario should have received:")
        print("• Connection test payload")
        print("• Sample lead with complete data")
        print("• High-priority alert")
        print("• Batch completion notification")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Check the error messages above and verify your webhook URL.")
    
    print(f"\n🌐 Webhook URL used: {WEBHOOK_URL}")
    print("💡 Check your Make.com scenario to see the received data!")

if __name__ == "__main__":
    asyncio.run(main()) 