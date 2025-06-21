#!/usr/bin/env python3
"""
Phase 4A Improved Discovery System Test
Testing improved ML classification with better business name filtering
Target: Improve success rate from 20% to 60%+
"""

import asyncio
import sys
import os
import logging
import time
from datetime import datetime
from bs4 import BeautifulSoup
import requests

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from src.seo_leads.ai.improved_executive_classifier import ImprovedExecutiveClassifier
from src.seo_leads.models import ExecutiveContact

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test companies
TEST_COMPANIES = [
    {'name': 'GPJ Plumbing', 'website': 'https://gpjplumbing.co.uk'},
    {'name': '247 Plumbing and Gas', 'website': 'https://247plumbingandgas.co.uk'},
    {'name': 'Hancox Gas and Plumbing', 'website': 'https://hancoxgasandplumbing.co.uk'},
    {'name': 'Emergency Plumber Services', 'website': 'https://emergencyplumberservices.co.uk'},
    {'name': 'Metro Plumb Birmingham', 'website': 'https://metroplumbbirmingham.co.uk'}
]

class ImprovedPhase4AEngine:
    """Improved Phase 4A Engine with better filtering"""
    
    def __init__(self):
        self.classifier = ImprovedExecutiveClassifier()
    
    async def discover_executives(self, company_data):
        """Discover executives using improved system"""
        company_name = company_data['name']
        website_url = company_data['website']
        
        start_time = time.time()
        
        try:
            # Fetch content
            content = await self._fetch_content(website_url)
            if not content:
                return self._failed_result(company_name, start_time, "No content")
            
            # Extract text
            soup = BeautifulSoup(content, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Use improved classifier
            candidates = self.classifier.classify_executives(text_content, company_name)
            
            # Convert to ExecutiveContact objects
            executives = self._convert_to_executives(candidates, company_name, website_url)
            
            processing_time = time.time() - start_time
            
            return {
                'company_name': company_name,
                'website_url': website_url,
                'executives': executives,
                'candidates_found': len(candidates),
                'final_count': len(executives),
                'processing_time': processing_time,
                'success': len(executives) > 0,
                'error': None
            }
            
        except Exception as e:
            return self._failed_result(company_name, start_time, str(e))
    
    async def _fetch_content(self, url):
        """Fetch website content"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                return response.text
        except:
            pass
        
        return None
    
    def _convert_to_executives(self, candidates, company_name, website_url):
        """Convert candidates to ExecutiveContact objects"""
        executives = []
        domain = website_url.replace('https://', '').replace('http://', '').split('/')[0]
        
        for candidate in candidates:
            try:
                executive = ExecutiveContact(
                    first_name=candidate.first_name,
                    last_name=candidate.last_name,
                    full_name=candidate.full_name,
                    title=candidate.title or "Executive",
                    seniority_tier="tier_2",
                    company_name=company_name,
                    company_domain=domain,
                    overall_confidence=candidate.confidence_score,
                    discovery_sources=['website'],
                    discovery_method=candidate.extraction_method
                )
                executives.append(executive)
            except Exception as e:
                logger.warning(f"Failed to convert {candidate.full_name}: {e}")
        
        return executives
    
    def _failed_result(self, company_name, start_time, error):
        """Create failed result"""
        return {
            'company_name': company_name,
            'website_url': '',
            'executives': [],
            'candidates_found': 0,
            'final_count': 0,
            'processing_time': time.time() - start_time,
            'success': False,
            'error': error
        }

async def test_improved_system():
    """Test the improved Phase 4A system"""
    print("\n" + "="*80)
    print("🚀 PHASE 4A IMPROVED DISCOVERY SYSTEM TEST")
    print("="*80)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🏢 Companies: {len(TEST_COMPANIES)}")
    print(f"🎯 Target: 60%+ success rate (vs 20% current)")
    print(f"🔧 Improvement: Better business name filtering + content analysis")
    print("="*80)
    
    engine = ImprovedPhase4AEngine()
    results = []
    total_start = time.time()
    
    for i, company in enumerate(TEST_COMPANIES, 1):
        print(f"\n🏢 Testing {i}/{len(TEST_COMPANIES)}: {company['name']}")
        result = await engine.discover_executives(company)
        results.append(result)
        
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        print(f"   {status}: {result['final_count']} executives, {result['processing_time']:.2f}s")
        
        if result['executives']:
            for exec in result['executives'][:2]:  # Show top 2
                print(f"      • {exec.first_name} {exec.last_name} ({exec.overall_confidence:.2f})")
                if exec.title:
                    print(f"        Title: {exec.title}")
        
        if result['error']:
            print(f"      Error: {result['error']}")
    
    total_time = time.time() - total_start
    
    # Calculate results
    successful = sum(1 for r in results if r['success'])
    success_rate = (successful / len(TEST_COMPANIES)) * 100
    total_executives = sum(r['final_count'] for r in results)
    total_candidates = sum(r['candidates_found'] for r in results)
    
    print(f"\n📊 IMPROVED PHASE 4A RESULTS:")
    print("="*80)
    print(f"   • Total Companies: {len(TEST_COMPANIES)}")
    print(f"   • Successful Companies: {successful}")
    print(f"   • Success Rate: {success_rate:.1f}%")
    print(f"   • Total Candidates Found: {total_candidates}")
    print(f"   • Total Executives: {total_executives}")
    print(f"   • Processing Time: {total_time:.2f}s")
    print(f"   • Average Time: {total_time/len(TEST_COMPANIES):.2f}s")
    
    # Assessment
    baseline = 20  # Previous result
    improvement = success_rate - baseline
    
    if success_rate >= 60:
        print(f"\n🎉 EXCELLENT! Target achieved: {success_rate:.1f}%")
        print(f"📈 Improvement: +{improvement:.1f}% from baseline")
    elif success_rate >= 40:
        print(f"\n🟡 GOOD PROGRESS! Achieved: {success_rate:.1f}%")
        print(f"📈 Improvement: +{improvement:.1f}% from baseline")
        print(f"🎯 Need {60 - success_rate:.1f}% more for target")
    else:
        print(f"\n🔴 NEEDS MORE WORK: {success_rate:.1f}%")
        print(f"📈 Change: {improvement:+.1f}% from baseline")
    
    # Detailed analysis
    print(f"\n📋 DETAILED ANALYSIS:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['company_name']}: {result['candidates_found']} → {result['final_count']}")
    
    print("="*80)
    
    return success_rate >= 40  # Success if we're making good progress

if __name__ == "__main__":
    success = asyncio.run(test_improved_system())
    sys.exit(0 if success else 1) 