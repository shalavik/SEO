#!/usr/bin/env python3
"""
Test script for P2.1 Alternative Search Enricher
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.seo_leads.enrichers.alternative_search_enricher import AlternativeSearchEnricher

async def test_alternative_search():
    """Test the alternative search enricher"""
    print("🔍 Testing P2.1 Alternative Search Enricher...")
    
    try:
        enricher = AlternativeSearchEnricher()
        print("✅ Alternative search enricher initialized")
        
        # Test with Jack The Plumber
        executives = await enricher.discover_executives(
            'Jack The Plumber', 
            'jacktheplumber.co.uk', 
            'plumbing'
        )
        
        print(f"🎯 Found {len(executives)} executives:")
        for exec in executives:
            print(f"- {exec.full_name} ({exec.title}) - Confidence: {exec.confidence:.2f}")
            print(f"  Sources: {exec.discovery_sources}")
        
        return len(executives) > 0
        
    except Exception as e:
        print(f"❌ Alternative search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_alternative_search())
    if success:
        print("✅ P2.1 Alternative Search Test PASSED")
    else:
        print("❌ P2.1 Alternative Search Test FAILED") 