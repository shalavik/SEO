#!/usr/bin/env python3
"""
Phase 4C Comprehensive Test - 10 URL Production System Test
Tests the complete Phase 4C production integration system with 10 plumbing company URLs
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
from dataclasses import asdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import Phase 4C components
try:
    from src.seo_leads.processors.phase4b_alternative_engine import Phase4BAlternativeEngine, Phase4BResults
    from src.seo_leads.gateways.api_gateway import APIGateway, RequestPriority
    from src.seo_leads.cache.intelligent_cache import IntelligentCacheManager
    from src.seo_leads.config.credential_manager import get_credential_manager
    from src.seo_leads.models import ExecutiveContact
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info("Running in simplified mode without Phase 4C components")

# Test URLs provided by user
TEST_URLS = [
    ("GPJ Plumbing", "http://gpj-plumbing.co.uk/"),
    ("Emergency Plumber Services", "https://www.emergencyplumber.services/"),
    ("247 Plumbing and Gas", "https://247plumbingandgas.co.uk/"),
    ("Hancox Gas and Plumbing", "http://www.hancoxgasandplumbing.co.uk/"),
    ("Metro Plumb Birmingham", "https://metroplumb.co.uk/locations/metro-plumb-birmingham/"),
    ("TJ Works", "https://www.tjworks.co.uk/"),
    ("Afterglow Heating", "https://afterglowheating.co.uk/"),
    ("AS Plumbing Heating", "http://asplumbingheating.com/"),
    ("MKH Plumbing Birmingham", "https://www.facebook.com/MKHPBirmingham/"),
    ("Maximum Heat Emergency Plumber", "http://www.maximumheatemergencyplumberbirmingham.co.uk/")
]

class Phase4CComprehensiveTest:
    """Phase 4C Comprehensive Testing Engine"""
    
    def __init__(self):
        self.test_start_time = None
        self.test_results = []
        self.api_gateway = None
        self.cache_manager = None
        self.alternative_engine = None
        
        # Test metrics
        self.total_companies_tested = 0
        self.successful_discoveries = 0
        self.total_executives_found = 0
        self.processing_times = []
        
        # Phase 4C specific metrics
        self.api_calls_made = 0
        self.cache_hits = 0
        self.companies_house_successes = 0
        self.social_media_successes = 0
        self.fallback_content_successes = 0
    
    async def initialize_phase4c_components(self):
        """Initialize Phase 4C production components"""
        logger.info("🚀 Initializing Phase 4C Production Components")
        
        try:
            # Initialize API Gateway
            self.api_gateway = APIGateway(max_concurrent_requests=10)
            await self.api_gateway.start()
            logger.info("✅ API Gateway initialized")
            
            # Initialize Intelligent Cache Manager
            self.cache_manager = IntelligentCacheManager()
            await self.cache_manager.start()
            logger.info("✅ Intelligent Cache Manager initialized")
            
            # Initialize Phase 4B Alternative Engine (with Phase 4C enhancements)
            self.alternative_engine = Phase4BAlternativeEngine()
            logger.info("✅ Phase 4B Alternative Engine initialized")
            
            # Initialize Credential Manager
            credential_manager = get_credential_manager()
            logger.info("✅ Credential Manager initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Phase 4C components: {e}")
            return False
    
    async def test_single_company(self, company_name: str, company_url: str) -> Dict[str, Any]:
        """Test a single company with Phase 4C system"""
        logger.info(f"🔍 Testing Company: {company_name}")
        start_time = time.time()
        
        try:
            # Run Phase 4B Alternative Discovery with Phase 4C enhancements
            if self.alternative_engine:
                result = await self.alternative_engine.discover_executives_alternative_sources(
                    company_name, company_url
                )
                
                # Process results
                processing_time = time.time() - start_time
                self.processing_times.append(processing_time)
                
                if result.total_executives_found > 0:
                    self.successful_discoveries += 1
                    self.total_executives_found += result.total_executives_found
                
                # Update Phase 4C metrics
                if result.companies_house_results and result.companies_house_results.executives_found:
                    self.companies_house_successes += 1
                
                if result.social_media_results and result.social_media_results.executives_found:
                    self.social_media_successes += 1
                
                if result.fallback_content_results and result.fallback_content_results.executives_found:
                    self.fallback_content_successes += 1
                
                # Convert to serializable format
                return {
                    'company_name': company_name,
                    'company_url': company_url,
                    'processing_time': processing_time,
                    'executives_found': result.total_executives_found,
                    'unique_executives': [asdict(exec) for exec in result.unique_executives] if result.unique_executives else [],
                    'website_health': {
                        'status': result.website_health.status.value if result.website_health else 'unknown',
                        'accessible': result.website_health.accessible if result.website_health else False,
                        'content_length': result.website_health.content_length if result.website_health else 0,
                        'response_time': result.website_health.response_time if result.website_health else 0.0
                    },
                    'source_results': {
                        'companies_house': {
                            'found': len(result.companies_house_results.executives_found) if result.companies_house_results else 0,
                            'confidence': result.companies_house_results.confidence_score if result.companies_house_results else 0.0,
                            'processing_time': result.companies_house_results.processing_time if result.companies_house_results else 0.0
                        },
                        'social_media': {
                            'found': len(result.social_media_results.executives_found) if result.social_media_results else 0,
                            'confidence': result.social_media_results.confidence_score if result.social_media_results else 0.0,
                            'processing_time': result.social_media_results.processing_time if result.social_media_results else 0.0
                        },
                        'fallback_content': {
                            'found': len(result.fallback_content_results.executives_found) if result.fallback_content_results else 0,
                            'confidence': result.fallback_content_results.confidence_score if result.fallback_content_results else 0.0,
                            'processing_time': result.fallback_content_results.processing_time if result.fallback_content_results else 0.0
                        }
                    },
                    'quality_metrics': {
                        'best_source': result.best_source,
                        'overall_confidence': result.overall_confidence,
                        'data_quality_score': result.data_quality_score,
                        'source_diversity_score': result.source_diversity_score,
                        'verification_score': result.verification_score
                    },
                    'success': result.total_executives_found > 0,
                    'error': None
                }
            else:
                # Fallback testing without Phase 4C components
                return await self.test_company_fallback(company_name, company_url)
                
        except Exception as e:
            logger.error(f"❌ Error testing {company_name}: {e}")
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            
            return {
                'company_name': company_name,
                'company_url': company_url,
                'processing_time': processing_time,
                'executives_found': 0,
                'unique_executives': [],
                'website_health': {'status': 'error', 'accessible': False},
                'source_results': {},
                'quality_metrics': {},
                'success': False,
                'error': str(e)
            }
    
    async def test_company_fallback(self, company_name: str, company_url: str) -> Dict[str, Any]:
        """Fallback testing method if Phase 4C components unavailable"""
        logger.info(f"🔄 Fallback testing for {company_name}")
        start_time = time.time()
        
        # Simple website accessibility test
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(company_url, timeout=10) as response:
                    content = await response.text()
                    processing_time = time.time() - start_time
                    
                    return {
                        'company_name': company_name,
                        'company_url': company_url,
                        'processing_time': processing_time,
                        'executives_found': 0,
                        'unique_executives': [],
                        'website_health': {
                            'status': 'accessible' if response.status == 200 else 'error',
                            'accessible': response.status == 200,
                            'content_length': len(content),
                            'response_time': processing_time
                        },
                        'source_results': {'fallback_only': True},
                        'quality_metrics': {'testing_mode': 'fallback'},
                        'success': response.status == 200,
                        'error': None if response.status == 200 else f"HTTP {response.status}"
                    }
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                'company_name': company_name,
                'company_url': company_url,
                'processing_time': processing_time,
                'executives_found': 0,
                'unique_executives': [],
                'website_health': {'status': 'error', 'accessible': False},
                'source_results': {},
                'quality_metrics': {},
                'success': False,
                'error': str(e)
            }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test on all 10 URLs"""
        logger.info("🚀 Starting Phase 4C Comprehensive Test - 10 URLs")
        self.test_start_time = time.time()
        
        # Initialize Phase 4C components
        phase4c_available = await self.initialize_phase4c_components()
        
        # Test all companies
        logger.info(f"🔍 Testing {len(TEST_URLS)} companies...")
        self.total_companies_tested = len(TEST_URLS)
        
        # Run tests concurrently (but limit concurrency to avoid overwhelming systems)
        semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent tests
        
        async def test_with_semaphore(company_data):
            async with semaphore:
                return await self.test_single_company(company_data[0], company_data[1])
        
        # Execute all tests
        self.test_results = await asyncio.gather(
            *[test_with_semaphore(company_data) for company_data in TEST_URLS],
            return_exceptions=True
        )
        
        # Handle any exceptions
        for i, result in enumerate(self.test_results):
            if isinstance(result, Exception):
                company_name, company_url = TEST_URLS[i]
                self.test_results[i] = {
                    'company_name': company_name,
                    'company_url': company_url,
                    'processing_time': 0.0,
                    'executives_found': 0,
                    'unique_executives': [],
                    'website_health': {'status': 'error', 'accessible': False},
                    'source_results': {},
                    'quality_metrics': {},
                    'success': False,
                    'error': str(result)
                }
        
        # Calculate final metrics
        total_test_time = time.time() - self.test_start_time
        average_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0.0
        success_rate = (self.successful_discoveries / self.total_companies_tested) * 100 if self.total_companies_tested > 0 else 0.0
        
        # Compile comprehensive results
        comprehensive_results = {
            'test_metadata': {
                'test_name': 'Phase 4C Comprehensive Test - 10 URLs',
                'test_date': datetime.now().isoformat(),
                'phase4c_components_available': phase4c_available,
                'total_test_time': total_test_time,
                'system_version': 'Phase 4C Production Integration'
            },
            'test_configuration': {
                'urls_tested': len(TEST_URLS),
                'concurrent_limit': 3,
                'timeout_per_request': 30,
                'api_gateway_enabled': self.api_gateway is not None,
                'intelligent_cache_enabled': self.cache_manager is not None,
                'alternative_sources_enabled': self.alternative_engine is not None
            },
            'overall_metrics': {
                'total_companies_tested': self.total_companies_tested,
                'successful_discoveries': self.successful_discoveries,
                'success_rate_percentage': success_rate,
                'total_executives_found': self.total_executives_found,
                'average_executives_per_company': self.total_executives_found / self.total_companies_tested if self.total_companies_tested > 0 else 0.0,
                'average_processing_time': average_processing_time,
                'total_processing_time': total_test_time
            },
            'phase4c_metrics': {
                'companies_house_successes': self.companies_house_successes,
                'social_media_successes': self.social_media_successes,
                'fallback_content_successes': self.fallback_content_successes,
                'api_calls_made': self.api_calls_made,
                'cache_hits': self.cache_hits
            },
            'individual_results': self.test_results,
            'summary_analysis': {
                'most_successful_source': self._analyze_most_successful_source(),
                'website_accessibility_rate': self._calculate_accessibility_rate(),
                'quality_distribution': self._analyze_quality_distribution(),
                'performance_analysis': self._analyze_performance()
            }
        }
        
        # Cleanup
        await self.cleanup()
        
        return comprehensive_results
    
    def _analyze_most_successful_source(self) -> str:
        """Analyze which source was most successful"""
        if self.companies_house_successes >= max(self.social_media_successes, self.fallback_content_successes):
            return "companies_house"
        elif self.social_media_successes >= self.fallback_content_successes:
            return "social_media"
        else:
            return "fallback_content"
    
    def _calculate_accessibility_rate(self) -> float:
        """Calculate website accessibility rate"""
        accessible_count = sum(1 for result in self.test_results 
                             if isinstance(result, dict) and 
                             result.get('website_health', {}).get('accessible', False))
        return (accessible_count / len(self.test_results)) * 100 if self.test_results else 0.0
    
    def _analyze_quality_distribution(self) -> Dict[str, int]:
        """Analyze quality distribution of results"""
        high_quality = sum(1 for result in self.test_results 
                          if isinstance(result, dict) and 
                          result.get('quality_metrics', {}).get('overall_confidence', 0) > 0.8)
        medium_quality = sum(1 for result in self.test_results 
                           if isinstance(result, dict) and 
                           0.5 < result.get('quality_metrics', {}).get('overall_confidence', 0) <= 0.8)
        low_quality = len(self.test_results) - high_quality - medium_quality
        
        return {
            'high_quality': high_quality,
            'medium_quality': medium_quality,
            'low_quality': low_quality
        }
    
    def _analyze_performance(self) -> Dict[str, float]:
        """Analyze performance metrics"""
        if not self.processing_times:
            return {'min_time': 0.0, 'max_time': 0.0, 'avg_time': 0.0}
        
        return {
            'min_processing_time': min(self.processing_times),
            'max_processing_time': max(self.processing_times),
            'average_processing_time': sum(self.processing_times) / len(self.processing_times)
        }
    
    async def cleanup(self):
        """Cleanup Phase 4C components"""
        try:
            if self.api_gateway:
                await self.api_gateway.stop()
                logger.info("✅ API Gateway stopped")
            
            if self.cache_manager:
                await self.cache_manager.stop()
                logger.info("✅ Cache Manager stopped")
                
        except Exception as e:
            logger.error(f"⚠️ Cleanup error: {e}")

async def main():
    """Main test execution function"""
    logger.info("🚀 Phase 4C Comprehensive Test - Starting")
    
    # Initialize and run test
    test_engine = Phase4CComprehensiveTest()
    results = await test_engine.run_comprehensive_test()
    
    # Generate JSON output file
    timestamp = int(time.time())
    output_filename = f"phase4c_comprehensive_test_results_{timestamp}.json"
    
    with open(output_filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print summary
    logger.info("🎉 Phase 4C Comprehensive Test - Complete")
    logger.info(f"📄 Results saved to: {output_filename}")
    logger.info(f"📊 Summary: {results['overall_metrics']['successful_discoveries']}/{results['overall_metrics']['total_companies_tested']} successful discoveries")
    logger.info(f"⏱️ Total time: {results['overall_metrics']['total_processing_time']:.2f}s")
    logger.info(f"🎯 Success rate: {results['overall_metrics']['success_rate_percentage']:.1f}%")
    
    print(f"\n✅ Test Complete! Results saved to: {output_filename}")
    return output_filename

if __name__ == "__main__":
    # Run the comprehensive test
    output_file = asyncio.run(main()) 