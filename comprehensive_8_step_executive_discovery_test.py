#!/usr/bin/env python3
"""
Comprehensive 8-Step Executive Discovery Orchestrator Production Test
Tests the complete implementation with real UK plumbing company URLs
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

class Comprehensive8StepExecutiveDiscoveryTest:
    """Comprehensive test runner for 8-Step Executive Discovery Orchestrator"""
    
    def __init__(self):
        self.orchestrator = ExecutiveDiscoveryOrchestrator()
        
        # Use the actual testing.txt URLs for production validation
        self.test_urls = [
            "https://supremeplumbers.com",
            "https://idealplumbingservices.com",
            "https://2ndcitygas.com", 
            "https://jacktheplumber.co.uk",
            "https://www.swiftemergencyplumber.co.uk",
            "https://mkplumbingbirmingham.co.uk",
            "https://rescueplumbing.co.uk",
            "https://gdplumbingandheating.co.uk",
            "https://mattplumbingandheating.com",
            "https://summitplumbingandheating.co.uk"
        ]
        
    async def test_single_url_comprehensive(self, website_url: str) -> Dict[str, Any]:
        """Comprehensive test for a single URL with detailed analysis"""
        
        logger.info(f"🔍 Starting comprehensive 8-step discovery for: {website_url}")
        start_time = time.time()
        
        try:
            result = await self.orchestrator.execute_comprehensive_discovery(website_url)
            
            processing_time = time.time() - start_time
            
            # Detailed step analysis
            step_analysis = {}
            for step in result.discovery_steps:
                step_analysis[f"step_{step.step_number}"] = {
                    'name': step.step_name,
                    'source': step.source,
                    'success': step.success,
                    'confidence': step.confidence,
                    'processing_time_ms': step.processing_time_ms,
                    'fallback_triggered': step.fallback_triggered,
                    'data_found': step.data_found,
                    'validation_results': step.validation_results,
                    'error_message': step.error_message
                }
            
            # Executive analysis
            executive_analysis = []
            for exec_contact in result.executives:
                executive_analysis.append({
                    'name': exec_contact.name,
                    'title': exec_contact.title,
                    'confidence_score': exec_contact.confidence_score,
                    'discovery_sources': exec_contact.discovery_sources,
                    'discovery_method': exec_contact.discovery_method,
                    'has_email': bool(exec_contact.email),
                    'has_phone': bool(exec_contact.phone),
                    'has_linkedin': bool(exec_contact.linkedin_url),
                    'validation_notes': exec_contact.validation_notes
                })
            
            comprehensive_result = {
                'url': website_url,
                'company_name': result.company_name,
                'companies_house_verified': result.companies_house_verified,
                'overall_confidence': result.overall_confidence,
                'total_processing_time_seconds': processing_time,
                'executives_found': len(result.executives),
                'steps_completed': len(result.discovery_steps),
                'validation_summary': result.validation_summary,
                'step_analysis': step_analysis,
                'executive_analysis': executive_analysis
            }
            
            # Log step results
            for step in result.discovery_steps:
                status = "✅" if step.success else "❌"
                logger.info(f"  {status} Step {step.step_number}: {step.step_name} ({step.processing_time_ms}ms)")
            
            logger.info(f"✅ Discovery completed in {processing_time:.2f}s")
            logger.info(f"📊 Results: {len(result.executives)} executives, confidence: {result.overall_confidence:.2f}")
            
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"❌ Comprehensive test failed for {website_url}: {e}")
            
            return {
                'url': website_url,
                'error': str(e),
                'success': False,
                'total_processing_time_seconds': time.time() - start_time
            }
    
    async def run_comprehensive_batch_test(self) -> Dict[str, Any]:
        """Run comprehensive test for all URLs"""
        
        logger.info(f"🚀 Starting comprehensive 8-step discovery test with {len(self.test_urls)} URLs")
        batch_start_time = time.time()
        
        results = []
        
        for i, url in enumerate(self.test_urls, 1):
            logger.info(f"\n[{i}/{len(self.test_urls)}] Processing: {url}")
            
            try:
                result = await self.test_single_url_comprehensive(url)
                results.append(result)
                
                # Add delay between requests for politeness
                if i < len(self.test_urls):
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"Failed to process {url}: {e}")
                results.append({
                    'url': url,
                    'error': str(e),
                    'success': False
                })
                continue
        
        batch_time = time.time() - batch_start_time
        
        # Analyze batch results
        successful_results = [r for r in results if 'error' not in r]
        total_executives = sum(r.get('executives_found', 0) for r in successful_results)
        
        batch_analysis = {
            'test_metadata': {
                'test_name': 'Comprehensive 8-Step Executive Discovery Test',
                'timestamp': datetime.now().isoformat(),
                'total_urls': len(self.test_urls),
                'batch_processing_time_seconds': batch_time
            },
            'overall_metrics': {
                'total_tests': len(results),
                'successful_tests': len(successful_results),
                'success_rate_percentage': len(successful_results) / len(results) * 100,
                'total_executives_found': total_executives,
                'average_executives_per_company': total_executives / len(successful_results) if successful_results else 0
            },
            'detailed_results': results
        }
        
        logger.info(f"\n🏁 Comprehensive batch test completed in {batch_time:.2f}s")
        logger.info(f"📈 Success rate: {len(successful_results)}/{len(results)} ({len(successful_results)/len(results)*100:.1f}%)")
        logger.info(f"👥 Total executives found: {total_executives}")
        
        return batch_analysis
    
    def print_comprehensive_results(self, analysis: Dict[str, Any]):
        """Print comprehensive test results"""
        
        print("\n" + "="*100)
        print("🎯 COMPREHENSIVE 8-STEP EXECUTIVE DISCOVERY ORCHESTRATOR TEST RESULTS")
        print("="*100)
        
        metadata = analysis['test_metadata']
        metrics = analysis['overall_metrics']
        
        print(f"\n📊 TEST METADATA:")
        print(f"   • Test Name: {metadata['test_name']}")
        print(f"   • Timestamp: {metadata['timestamp']}")
        print(f"   • Total URLs: {metadata['total_urls']}")
        print(f"   • Batch Processing Time: {metadata['batch_processing_time_seconds']:.2f}s")
        
        print(f"\n📈 OVERALL PERFORMANCE METRICS:")
        print(f"   • Total Tests: {metrics['total_tests']}")
        print(f"   • Successful Tests: {metrics['successful_tests']}")
        print(f"   • Success Rate: {metrics['success_rate_percentage']:.1f}%")
        print(f"   • Total Executives Found: {metrics['total_executives_found']}")
        print(f"   • Average Executives per Company: {metrics['average_executives_per_company']:.1f}")
        
        print(f"\n📋 DETAILED RESULTS BY COMPANY:")
        for i, result in enumerate(analysis['detailed_results'], 1):
            if 'error' in result:
                print(f"\n[{i}] {result['url']} - ❌ ERROR: {result['error']}")
            else:
                print(f"\n[{i}] {result['company_name']} ({result['url']})")
                print(f"    • Executives Found: {result['executives_found']}")
                print(f"    • Overall Confidence: {result['overall_confidence']:.2f}")
                print(f"    • Processing Time: {result['total_processing_time_seconds']:.2f}s")
                print(f"    • Steps Completed: {result['steps_completed']}")
        
        print("\n" + "="*100)
    
    async def save_comprehensive_results(self, analysis: Dict[str, Any]):
        """Save comprehensive results to JSON file"""
        
        timestamp = int(time.time())
        filename = f"comprehensive_8_step_executive_discovery_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Comprehensive results saved to: {filename}")
        print(f"\n💾 Comprehensive results saved to: {filename}")

async def main():
    """Main comprehensive test execution"""
    
    print("🚀 Starting Comprehensive 8-Step Executive Discovery Orchestrator Test")
    print("=" * 80)
    
    test_runner = Comprehensive8StepExecutiveDiscoveryTest()
    
    try:
        # Run comprehensive batch test
        analysis = await test_runner.run_comprehensive_batch_test()
        
        # Print comprehensive results
        test_runner.print_comprehensive_results(analysis)
        
        # Save results to files
        await test_runner.save_comprehensive_results(analysis)
        
        print("\n✅ Comprehensive test completed successfully!")
        
    except Exception as e:
        logger.error(f"Comprehensive test execution failed: {e}")
        print(f"\n❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
