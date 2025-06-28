#!/usr/bin/env python3
"""
8-Step Executive Discovery Orchestrator Test
Tests the comprehensive executive discovery implementation using Context7 patterns
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any

from src.seo_leads.orchestrators.executive_discovery_orchestrator import (
    ExecutiveDiscoveryOrchestrator,
    ExecutiveDiscoveryResult
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EightStepExecutiveDiscoveryTest:
    """Test runner for 8-Step Executive Discovery Orchestrator"""
    
    def __init__(self):
        self.orchestrator = ExecutiveDiscoveryOrchestrator()
        self.test_urls = [
            "https://supremeplumbers.com",
            "https://idealplumbingservices.com", 
            "https://2ndcitygas.com",
            "https://jacktheplumber.co.uk",
            "https://www.swiftemergencyplumber.co.uk"
        ]
        
    async def test_single_url(self, website_url: str) -> ExecutiveDiscoveryResult:
        """Test discovery for a single URL"""
        
        logger.info(f"🔍 Testing 8-step discovery for: {website_url}")
        start_time = time.time()
        
        try:
            result = await self.orchestrator.execute_comprehensive_discovery(website_url)
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Discovery completed in {processing_time:.2f}s")
            
            # Log step results
            for step in result.discovery_steps:
                status = "✅" if step.success else "❌"
                logger.info(f"  {status} Step {step.step_number}: {step.step_name} ({step.processing_time_ms}ms)")
            
            logger.info(f"📊 Results: {len(result.executives)} executives, confidence: {result.overall_confidence:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Test failed for {website_url}: {e}")
            raise
    
    async def test_batch_urls(self) -> List[ExecutiveDiscoveryResult]:
        """Test discovery for multiple URLs"""
        
        logger.info(f"🚀 Starting batch test with {len(self.test_urls)} URLs")
        batch_start_time = time.time()
        
        results = []
        
        for i, url in enumerate(self.test_urls, 1):
            logger.info(f"\n[{i}/{len(self.test_urls)}] Processing: {url}")
            
            try:
                result = await self.test_single_url(url)
                results.append(result)
                
                # Add delay between requests
                if i < len(self.test_urls):
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"Failed to process {url}: {e}")
                continue
        
        batch_time = time.time() - batch_start_time
        logger.info(f"\n🏁 Batch test completed in {batch_time:.2f}s")
        logger.info(f"📈 Success rate: {len(results)}/{len(self.test_urls)} ({len(results)/len(self.test_urls)*100:.1f}%)")
        
        return results
    
    def print_detailed_results(self, results: List[ExecutiveDiscoveryResult]):
        """Print detailed test results"""
        
        print("\n" + "="*80)
        print("🎯 8-STEP EXECUTIVE DISCOVERY ORCHESTRATOR TEST RESULTS")
        print("="*80)
        
        total_executives = sum(len(r.executives) for r in results)
        avg_confidence = sum(r.overall_confidence for r in results) / len(results) if results else 0
        
        print(f"\n📊 OVERALL METRICS:")
        print(f"   • Total Tests: {len(results)}")
        print(f"   • Total Executives Found: {total_executives}")
        print(f"   • Average Confidence: {avg_confidence:.2f}")
        
        print(f"\n📋 DETAILED RESULTS BY COMPANY:")
        for i, result in enumerate(results, 1):
            print(f"\n[{i}] {result.company_name} ({result.website_url})")
            print(f"    • Executives Found: {len(result.executives)}")
            print(f"    • Confidence: {result.overall_confidence:.2f}")
            print(f"    • Steps Completed: {len(result.discovery_steps)}")
        
        print("\n" + "="*80)

async def main():
    """Main test execution"""
    
    print("🚀 Starting 8-Step Executive Discovery Orchestrator Test")
    print("=" * 60)
    
    test_runner = EightStepExecutiveDiscoveryTest()
    
    try:
        # Run batch test
        results = await test_runner.test_batch_urls()
        
        # Print detailed results
        test_runner.print_detailed_results(results)
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\n❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
