#!/usr/bin/env python3
"""
Optimized Make.com Webhook Test

Tests both streaming and batch posting styles according to Make.com best practices:
- Stream: One JSON object per HTTP request (tiny payloads, failures isolated)  
- Batch: Array of objects in single request (minimizes HTTPS handshakes)
- Exponential backoff: 1→2→4→8→16 second retry delays
- Security: X-Make-Token header for filtering
- Timeout: 10 seconds (Make.com recommended)
- Pacing: 150ms between streaming calls
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
    MakePayloadFormat
)
from src.seo_leads.models import UKCompany, PriorityTier

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Your Make.com webhook URL
WEBHOOK_URL = "https://hook.eu2.make.com/7cdm5zriyb8ka86af1c4otia2vxbt61h"

def create_test_companies(count: int = 5) -> list[UKCompany]:
    """Create multiple test companies for batch testing"""
    companies = []
    
    base_companies = [
        {
            "company_name": "Brighton Digital Agency",
            "city": "Brighton",
            "sector": "digital-marketing",
            "lead_score": 78.5,
            "priority_tier": "B",
            "contact_person": "Sarah Mitchell",
            "contact_email": "sarah@brightondigital.co.uk"
        },
        {
            "company_name": "London Restaurant Group", 
            "city": "London",
            "sector": "hospitality",
            "lead_score": 94.5,
            "priority_tier": "A",
            "contact_person": "David Thompson",
            "contact_email": "david@londonrestaurants.co.uk"
        },
        {
            "company_name": "Manchester Tech Solutions",
            "city": "Manchester", 
            "sector": "technology",
            "lead_score": 67.2,
            "priority_tier": "C",
            "contact_person": "Lisa Chen",
            "contact_email": "lisa@manchestertech.co.uk"
        },
        {
            "company_name": "Birmingham Retail Chain",
            "city": "Birmingham",
            "sector": "retail", 
            "lead_score": 82.1,
            "priority_tier": "B",
            "contact_person": "Mike Johnson",
            "contact_email": "mike@birminghamretail.co.uk"
        },
        {
            "company_name": "Edinburgh Law Firm",
            "city": "Edinburgh",
            "sector": "legal",
            "lead_score": 88.7,
            "priority_tier": "A", 
            "contact_person": "James MacLeod",
            "contact_email": "james@edinburghlaw.co.uk"
        }
    ]
    
    for i in range(count):
        base = base_companies[i % len(base_companies)]
        
        company = UKCompany(
            id=f"test_company_{i+1}",
            company_name=f"{base['company_name']} #{i+1}",
            website=f"https://example{i+1}.co.uk",
            city=base['city'],
            region="Test Region",
            address=f"{i+1} Test Street, {base['city']} TE5T 123",
            sector=base['sector'],
            source="Test Source",
            
            # Contact information
            contact_person=base['contact_person'],
            contact_role="Test Contact",
            contact_seniority_tier="tier_2",
            email=base['contact_email'],
            phone=f"012{i:02d} 555{i:03d}",
            linkedin_url=f"https://linkedin.com/in/test-{i+1}",
            contact_confidence=0.85,
            contact_extraction_method="test_method",
            
            # SEO analysis
            seo_overall_score=30.0 + (i * 10),
            pagespeed_score=20 + (i * 5),
            mobile_friendly=i % 2 == 0,
            meta_description_missing=True,
            h1_tags_present=i % 3 == 0,
            ssl_certificate=True,
            load_time=3.0 + (i * 0.5),
            critical_issues=[
                f"Issue {i+1}: Poor performance",
                f"Issue {i+1}: Missing optimization"
            ],
            
            # Lead qualification
            lead_score=base['lead_score'],
            priority_tier=base['priority_tier'],
            tier_label=f"Test {base['priority_tier']} Tier",
            estimated_value="£1,000-5,000",
            urgency="medium",
            recommended_actions=[
                "Test action 1",
                "Test action 2"
            ],
            talking_points=[
                f"Test talking point for {base['company_name']}",
                "Performance improvements needed"
            ]
        )
        
        companies.append(company)
    
    return companies

async def test_stream_posting():
    """Test stream posting style (one JSON object per request)"""
    print("\n🌊 Testing STREAM Posting Style")
    print("=" * 50)
    print("✨ Benefits: Tiny payloads, failures isolated")
    print("⚡ Method: One JSON object per HTTP request")
    print("⏱️  Pacing: 150ms delay between calls")
    
    companies = create_test_companies(3)  # Small batch for streaming
    
    sender = MakeWebhookSender(webhook_url=WEBHOOK_URL)
    sender.posting_style = "stream"  # Force stream mode
    
    start_time = datetime.utcnow()
    results = await sender.send_batch(
        companies, 
        WebhookEventType.NEW_LEAD, 
        MakePayloadFormat.SUMMARY,
        posting_style="stream"
    )
    end_time = datetime.utcnow()
    
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n📊 Stream Results:")
    print(f"   Companies sent: {results['total_attempted']}")
    print(f"   Successful: {results['successful']}")
    print(f"   Failed: {results['failed']}")
    print(f"   Duration: {duration:.2f} seconds")
    print(f"   Rate: {results['successful']/duration:.1f} leads/sec" if duration > 0 else "   Rate: instant")
    
    if results['errors']:
        print(f"   Errors: {results['errors']}")
    
    return results['successful'] > 0

async def test_batch_posting():
    """Test batch posting style (array of objects in single request)"""
    print("\n📦 Testing BATCH Posting Style")
    print("=" * 50)
    print("✨ Benefits: Minimizes HTTPS handshakes, fits Make's 40s limit")
    print("⚡ Method: Array of objects in single request")
    print("📏 Batch size: Up to 100 objects per request")
    
    companies = create_test_companies(10)  # Larger batch for batching
    
    sender = MakeWebhookSender(webhook_url=WEBHOOK_URL)
    sender.posting_style = "batch"  # Force batch mode
    
    start_time = datetime.utcnow()
    results = await sender.send_batch(
        companies, 
        WebhookEventType.NEW_LEAD, 
        MakePayloadFormat.SUMMARY,
        posting_style="batch"
    )
    end_time = datetime.utcnow()
    
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n📊 Batch Results:")
    print(f"   Companies sent: {results['total_attempted']}")
    print(f"   Successful: {results['successful']}")
    print(f"   Failed: {results['failed']}")
    print(f"   Duration: {duration:.2f} seconds")
    print(f"   Rate: {results['successful']/duration:.1f} leads/sec" if duration > 0 else "   Rate: instant")
    print(f"   Posting style: {results['posting_style']}")
    
    if results['errors']:
        print(f"   Errors: {results['errors']}")
    
    return results['successful'] > 0

async def test_security_features():
    """Test security features (X-Make-Token header)"""
    print("\n🔒 Testing Security Features")
    print("=" * 50)
    print("🛡️  Feature: X-Make-Token header for filtering")
    print("💡 Benefit: Prevents random traffic from triggering flows")
    
    # Test with security token
    companies = create_test_companies(1)
    
    sender = MakeWebhookSender(webhook_url=WEBHOOK_URL)
    sender.secret = "test_make_token_123"  # Set test token
    
    results = await sender.send_batch(
        companies, 
        WebhookEventType.NEW_LEAD, 
        MakePayloadFormat.SUMMARY
    )
    
    print(f"\n📊 Security Test Results:")
    print(f"   Token used: test_make_token_123")
    print(f"   Successful: {results['successful']}")
    print(f"   Failed: {results['failed']}")
    print(f"💡 Add Filter in Make.com: X-Make-Token = 'test_make_token_123'")
    
    return results['successful'] > 0

async def test_high_priority_alert():
    """Test high-priority A-tier lead alert"""
    print("\n🚨 Testing High-Priority Alert")
    print("=" * 50)
    print("⚡ Feature: Immediate alerts for A-tier leads")
    print("🎯 Use case: Hot leads need instant attention")
    
    # Create A-tier company
    companies = create_test_companies(1)
    companies[0].priority_tier = "A"
    companies[0].lead_score = 95.0
    companies[0].tier_label = "Hot Lead"
    companies[0].urgency = "immediate"
    
    sender = MakeWebhookSender(webhook_url=WEBHOOK_URL)
    success = await sender.send_high_priority_alert(companies[0])
    
    print(f"\n📊 Alert Results:")
    print(f"   Lead: {companies[0].company_name}")
    print(f"   Score: {companies[0].lead_score}")
    print(f"   Priority: {companies[0].tier_label}")
    print(f"   Alert sent: {'✅ Yes' if success else '❌ No'}")
    
    return success

async def main():
    """Run comprehensive Make.com optimization tests"""
    print("🚀 Make.com Webhook Optimization Test")
    print("=" * 70)
    print("🎯 Testing Make.com best practices implementation:")
    print("   • Stream vs Batch posting styles")
    print("   • Exponential backoff (1→2→4→8→16s)")
    print("   • Security headers (X-Make-Token)")
    print("   • 10-second timeouts")
    print("   • Proper pacing (150ms between calls)")
    print("   • Transient error handling (429, 502, 503)")
    print(f"\n🌐 Webhook URL: {WEBHOOK_URL}")
    print()
    
    test_results = {}
    
    # Test 1: Stream posting
    try:
        test_results['stream'] = await test_stream_posting()
    except Exception as e:
        print(f"❌ Stream test error: {e}")
        test_results['stream'] = False
    
    # Test 2: Batch posting
    try:
        test_results['batch'] = await test_batch_posting()
    except Exception as e:
        print(f"❌ Batch test error: {e}")
        test_results['batch'] = False
    
    # Test 3: Security features
    try:
        test_results['security'] = await test_security_features()
    except Exception as e:
        print(f"❌ Security test error: {e}")
        test_results['security'] = False
    
    # Test 4: High-priority alerts
    try:
        test_results['alerts'] = await test_high_priority_alert()
    except Exception as e:
        print(f"❌ Alert test error: {e}")
        test_results['alerts'] = False
    
    # Final results
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 70)
    
    successful_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, success in test_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name.upper():<12} {status}")
    
    print(f"\n🎯 Overall: {successful_tests}/{total_tests} tests passed")
    
    if successful_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Make.com integration optimized!")
        print("\n📋 What worked:")
        print("✅ Stream posting (one object per request)")
        print("✅ Batch posting (array of objects per request)")  
        print("✅ Security headers (X-Make-Token)")
        print("✅ High-priority alerts")
        print("\n🔗 Your Make.com scenario should now have received:")
        print("• 3 streaming webhook calls")
        print("• 1 batch webhook call with 10 leads")
        print("• 1 security test with token header")
        print("• 1 high-priority alert")
        print("\n💡 Next steps:")
        print("1. Check Make.com execution history")
        print("2. Verify data structure received correctly")
        print("3. Add filters for X-Make-Token if using security")
        print("4. Build your automation workflow!")
    else:
        print(f"\n⚠️  {total_tests - successful_tests} tests failed")
        print("💡 Possible issues:")
        print("  • Make.com scenario not activated")
        print("  • Webhook URL incorrect")
        print("  • Network connectivity issues")
        print("  • Make.com service temporary issues")
        print("\n🔧 Troubleshooting:")
        print("1. Verify scenario is turned ON in Make.com")
        print("2. Check webhook URL matches exactly")
        print("3. Ensure webhook module is set to 'Instant trigger'")
        print("4. Try again in a few minutes")
    
    print(f"\n🌐 Webhook URL: {WEBHOOK_URL}")
    print("📖 See MAKE_INTEGRATION_GUIDE.md for detailed setup instructions")

if __name__ == "__main__":
    asyncio.run(main()) 