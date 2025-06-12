#!/usr/bin/env python3
"""
Simple Make.com Webhook Test

Tests the webhook with minimal payload to verify connectivity and data format.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Your Make.com webhook URL
WEBHOOK_URL = "https://hook.eu2.make.com/7cdm5zriyb8ka86af1c4otia2vxbt61h"

async def test_simple_payload():
    """Test with simple payload format"""
    print("🔗 Testing simple payload...")
    
    # Simple payload structure
    payload = {
        "test": True,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Hello from UK SEO Leads System"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                WEBHOOK_URL,
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                
                response_text = await response.text()
                print(f"Status: {response.status}")
                print(f"Response: {response_text}")
                
                if response.status == 200:
                    print("✅ Simple payload test successful!")
                    return True
                else:
                    print(f"❌ Simple payload test failed: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_lead_payload():
    """Test with lead-like payload"""
    print("\n📤 Testing lead payload...")
    
    # Lead-like payload
    payload = {
        "event_type": "new_lead",
        "timestamp": datetime.utcnow().isoformat(),
        "company_name": "Test Company Ltd",
        "website": "https://testcompany.co.uk",
        "city": "London",
        "contact_person": "John Smith", 
        "contact_email": "john@testcompany.co.uk",
        "lead_score": 85.0,
        "priority": "High",
        "seo_issues": [
            "Slow page speed",
            "Missing meta descriptions",
            "Poor mobile experience"
        ],
        "estimated_value": "£5,000-10,000"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                WEBHOOK_URL,
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                
                response_text = await response.text()
                print(f"Status: {response.status}")
                print(f"Response: {response_text}")
                
                if response.status == 200:
                    print("✅ Lead payload test successful!")
                    return True
                else:
                    print(f"❌ Lead payload test failed: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_form_data():
    """Test with form data instead of JSON"""
    print("\n📝 Testing form data...")
    
    # Form data payload
    data = {
        'company_name': 'Test Company Form',
        'email': 'test@example.com',
        'lead_score': '90',
        'message': 'Test from webhook integration'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                WEBHOOK_URL,
                data=data
            ) as response:
                
                response_text = await response.text()
                print(f"Status: {response.status}")
                print(f"Response: {response_text}")
                
                if response.status == 200:
                    print("✅ Form data test successful!")
                    return True
                else:
                    print(f"❌ Form data test failed: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_raw_text():
    """Test with raw text payload"""
    print("\n📄 Testing raw text...")
    
    text_data = "Test message from UK SEO Leads System"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                WEBHOOK_URL,
                data=text_data,
                headers={'Content-Type': 'text/plain'}
            ) as response:
                
                response_text = await response.text()
                print(f"Status: {response.status}")
                print(f"Response: {response_text}")
                
                if response.status == 200:
                    print("✅ Raw text test successful!")
                    return True
                else:
                    print(f"❌ Raw text test failed: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Run webhook tests with different payload formats"""
    print("🚀 Make.com Webhook Format Test")
    print("=" * 50)
    print(f"Testing webhook: {WEBHOOK_URL}")
    print()
    
    tests = [
        ("Simple JSON", test_simple_payload),
        ("Lead JSON", test_lead_payload), 
        ("Form Data", test_form_data),
        ("Raw Text", test_raw_text)
    ]
    
    successful_tests = []
    
    for test_name, test_func in tests:
        try:
            print(f"🧪 {test_name} Test")
            print("-" * 30)
            success = await test_func()
            if success:
                successful_tests.append(test_name)
            print()
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
            print()
    
    # Results
    print("=" * 50)
    print("📊 Test Results")
    print("=" * 50)
    
    if successful_tests:
        print(f"✅ Successful formats: {', '.join(successful_tests)}")
        print(f"✅ {len(successful_tests)}/{len(tests)} tests passed")
        print("\n💡 Your Make.com webhook is working!")
        print("💡 Check your Make.com scenario to see which format received data.")
    else:
        print("❌ All tests failed!")
        print("💡 Possible issues:")
        print("  • Webhook URL might be incorrect")
        print("  • Make.com scenario might not be active")
        print("  • Network connectivity issues")
        print("  • Make.com server issues")
    
    print(f"\n🌐 Webhook URL: {WEBHOOK_URL}")

if __name__ == "__main__":
    asyncio.run(main()) 