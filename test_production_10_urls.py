#!/usr/bin/env python3
"""
Production Test - 10 URL Executive Discovery System Test
Tests the production executive discovery system with 10 plumbing company URLs
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

# Import available components
from src.seo_leads.processors.improved_executive_discovery import ImprovedExecutiveDiscoveryEngine, ImprovedDiscoveryConfig
from src.seo_leads.models import ExecutiveContact

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

class ProductionExecutiveTest:
    """Production Executive Discovery Testing Engine"""
    
    def __init__(self):
        # Initialize discovery engine with optimized settings
        config = ImprovedDiscoveryConfig(
            website_enabled=True,
            google_search_enabled=True,
            companies_house_enabled=True,
            enable_business_name_analysis=True,
            enable_advanced_website_patterns=True,
            enable_context_analysis=True,
            max_executives_per_company=10,
            min_confidence_tier_1=0.6,
            min_confidence_tier_2=0.4,
            min_confidence_tier_3=0.2
        )
        
        self.discovery_engine = ImprovedExecutiveDiscoveryEngine(config)
        
        # Test metrics
        self.test_start_time = None
        self.test_results = []
        self.total_companies_tested = 0
        self.successful_discoveries = 0
        self.total_executives_found = 0
        self.processing_times = []
        
        # Source-specific metrics
        self.business_name_successes = 0
        self.website_successes = 0
        self.google_search_successes = 0
        self.companies_house_successes = 0
    
    async def test_single_company(self, company_name: str, company_url: str) -> Dict[str, Any]:
        """Test executive discovery for a single company"""
        logger.info(f"🔍 Testing Company: {company_name}")
        start_time = time.time()
        
        try:
            # Run improved executive discovery
            result = await self.discovery_engine.discover_executives(
                company_name=company_name,
                website_url=company_url,
                company_id=f"test_{len(self.test_results) + 1}"
            )
            
            # Process results
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            
            executives_found = len(result.executives_found)
            if executives_found > 0:
                self.successful_discoveries += 1
                self.total_executives_found += executives_found
            
            # Track source successes (simplified since source tracking is internal)
            if executives_found > 0:
                # Check for patterns that suggest different sources
                for exec in result.executives_found:
                    if "Business Owner" in exec.title or "Family Business" in exec.title:
                        self.business_name_successes += 1
                    elif exec.discovery_method == "website_scraping":
                        self.website_successes += 1
                    elif exec.discovery_method == "google_search":
                        self.google_search_successes += 1
                    elif exec.discovery_method == "companies_house":
                        self.companies_house_successes += 1
            
            # Convert executives to serializable format
            executives_data = []
            for exec in result.executives_found:
                exec_dict = asdict(exec)
                # Convert datetime objects to strings
                for key, value in exec_dict.items():
                    if hasattr(value, 'isoformat'):
                        exec_dict[key] = value.isoformat()
                executives_data.append(exec_dict)
            
            # Create comprehensive result
            return {
                'company_name': company_name,
                'company_url': company_url,
                'company_id': result.company_id,
                'company_domain': result.company_domain,
                'processing_time': processing_time,
                'executives_found': executives_found,
                'executives_data': executives_data,
                'primary_decision_maker': asdict(result.primary_decision_maker) if result.primary_decision_maker else None,
                'discovery_sources': result.discovery_sources,
                'success_rate': result.success_rate,
                'total_processing_time': result.total_processing_time,
                'confidence_analysis': self._analyze_confidence_distribution(result.executives_found),
                'title_analysis': self._analyze_title_distribution(result.executives_found),
                'discovery_method_analysis': self._analyze_discovery_methods(result.executives_found),
                'success': executives_found > 0,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"❌ Error testing {company_name}: {e}")
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            
            return {
                'company_name': company_name,
                'company_url': company_url,
                'company_id': f"error_{len(self.test_results) + 1}",
                'company_domain': "",
                'processing_time': processing_time,
                'executives_found': 0,
                'executives_data': [],
                'primary_decision_maker': None,
                'discovery_sources': [],
                'success_rate': 0.0,
                'total_processing_time': processing_time,
                'confidence_analysis': {},
                'title_analysis': {},
                'discovery_method_analysis': {},
                'success': False,
                'error': str(e)
            }
    
    def _analyze_confidence_distribution(self, executives: List[ExecutiveContact]) -> Dict[str, int]:
        """Analyze confidence score distribution"""
        if not executives:
            return {'high': 0, 'medium': 0, 'low': 0}
        
        high = sum(1 for exec in executives if exec.confidence_score >= 0.7)
        medium = sum(1 for exec in executives if 0.4 <= exec.confidence_score < 0.7)
        low = sum(1 for exec in executives if exec.confidence_score < 0.4)
        
        return {'high': high, 'medium': medium, 'low': low}
    
    def _analyze_title_distribution(self, executives: List[ExecutiveContact]) -> Dict[str, int]:
        """Analyze title distribution"""
        if not executives:
            return {}
        
        title_counts = {}
        for exec in executives:
            title = exec.title or "Unknown"
            title_counts[title] = title_counts.get(title, 0) + 1
        
        return title_counts
    
    def _analyze_discovery_methods(self, executives: List[ExecutiveContact]) -> Dict[str, int]:
        """Analyze discovery method distribution"""
        if not executives:
            return {}
        
        method_counts = {}
        for exec in executives:
            method = exec.discovery_method or "unknown"
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return method_counts
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test on all 10 URLs"""
        logger.info("🚀 Starting Production Executive Discovery Test - 10 URLs")
        self.test_start_time = time.time()
        
        # Test all companies
        logger.info(f"🔍 Testing {len(TEST_URLS)} companies...")
        self.total_companies_tested = len(TEST_URLS)
        
        # Run tests with controlled concurrency
        semaphore = asyncio.Semaphore(2)  # Limit to 2 concurrent tests to be respectful
        
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
                    'company_id': f"exception_{i}",
                    'company_domain': "",
                    'processing_time': 0.0,
                    'executives_found': 0,
                    'executives_data': [],
                    'primary_decision_maker': None,
                    'discovery_sources': [],
                    'success_rate': 0.0,
                    'total_processing_time': 0.0,
                    'confidence_analysis': {},
                    'title_analysis': {},
                    'discovery_method_analysis': {},
                    'success': False,
                    'error': str(result)
                }
        
        # Calculate final metrics
        total_test_time = time.time() - self.test_start_time
        average_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0.0
        success_rate = (self.successful_discoveries / self.total_companies_tested) * 100 if self.total_companies_tested > 0 else 0.0
        
        # Get engine statistics
        engine_stats = self.discovery_engine.get_statistics()
        
        # Compile comprehensive results
        comprehensive_results = {
            'test_metadata': {
                'test_name': 'Production Executive Discovery Test - 10 URLs',
                'test_date': datetime.now().isoformat(),
                'total_test_time': total_test_time,
                'system_version': 'Improved Executive Discovery Engine',
                'discovery_config': {
                    'website_enabled': True,
                    'google_search_enabled': True,
                    'companies_house_enabled': True,
                    'business_name_analysis': True,
                    'advanced_patterns': True,
                    'context_analysis': True
                }
            },
            'test_configuration': {
                'urls_tested': len(TEST_URLS),
                'concurrent_limit': 2,
                'max_executives_per_company': 10,
                'confidence_tiers': '0.6/0.4/0.2'
            },
            'overall_metrics': {
                'total_companies_tested': self.total_companies_tested,
                'successful_discoveries': self.successful_discoveries,
                'success_rate_percentage': success_rate,
                'total_executives_found': self.total_executives_found,
                'average_executives_per_company': self.total_executives_found / self.total_companies_tested if self.total_companies_tested > 0 else 0.0,
                'average_processing_time': average_processing_time,
                'total_processing_time': total_test_time,
                'fastest_discovery': min(self.processing_times) if self.processing_times else 0.0,
                'slowest_discovery': max(self.processing_times) if self.processing_times else 0.0
            },
            'source_performance': {
                'business_name_successes': self.business_name_successes,
                'website_successes': self.website_successes,
                'google_search_successes': self.google_search_successes,
                'companies_house_successes': self.companies_house_successes
            },
            'engine_statistics': engine_stats,
            'individual_results': self.test_results,
            'aggregate_analysis': {
                'total_confidence_distribution': self._aggregate_confidence_analysis(),
                'total_title_distribution': self._aggregate_title_analysis(),
                'total_discovery_method_distribution': self._aggregate_method_analysis(),
                'website_accessibility_analysis': self._analyze_website_accessibility(),
                'performance_analysis': self._analyze_performance_patterns()
            }
        }
        
        return comprehensive_results
    
    def _aggregate_confidence_analysis(self) -> Dict[str, int]:
        """Aggregate confidence analysis across all results"""
        total = {'high': 0, 'medium': 0, 'low': 0}
        for result in self.test_results:
            if isinstance(result, dict) and 'confidence_analysis' in result:
                conf = result['confidence_analysis']
                total['high'] += conf.get('high', 0)
                total['medium'] += conf.get('medium', 0)
                total['low'] += conf.get('low', 0)
        return total
    
    def _aggregate_title_analysis(self) -> Dict[str, int]:
        """Aggregate title analysis across all results"""
        total_titles = {}
        for result in self.test_results:
            if isinstance(result, dict) and 'title_analysis' in result:
                for title, count in result['title_analysis'].items():
                    total_titles[title] = total_titles.get(title, 0) + count
        return total_titles
    
    def _aggregate_method_analysis(self) -> Dict[str, int]:
        """Aggregate discovery method analysis across all results"""
        total_methods = {}
        for result in self.test_results:
            if isinstance(result, dict) and 'discovery_method_analysis' in result:
                for method, count in result['discovery_method_analysis'].items():
                    total_methods[method] = total_methods.get(method, 0) + count
        return total_methods
    
    def _analyze_website_accessibility(self) -> Dict[str, Any]:
        """Analyze website accessibility patterns"""
        accessible = sum(1 for result in self.test_results 
                        if isinstance(result, dict) and not result.get('error'))
        total = len(self.test_results)
        
        return {
            'accessible_websites': accessible,
            'inaccessible_websites': total - accessible,
            'accessibility_rate': (accessible / total) * 100 if total > 0 else 0.0
        }
    
    def _analyze_performance_patterns(self) -> Dict[str, Any]:
        """Analyze performance patterns"""
        if not self.processing_times:
            return {}
        
        # Companies with fast discovery (< 5 seconds)
        fast_discoveries = sum(1 for t in self.processing_times if t < 5.0)
        # Companies with slow discovery (> 15 seconds)
        slow_discoveries = sum(1 for t in self.processing_times if t > 15.0)
        
        return {
            'fast_discoveries': fast_discoveries,
            'slow_discoveries': slow_discoveries,
            'medium_discoveries': len(self.processing_times) - fast_discoveries - slow_discoveries,
            'performance_distribution': {
                'under_5s': fast_discoveries,
                '5_to_15s': len(self.processing_times) - fast_discoveries - slow_discoveries,
                'over_15s': slow_discoveries
            }
        }

async def main():
    """Main test execution function"""
    logger.info("🚀 Production Executive Discovery Test - Starting")
    
    # Initialize and run test
    test_engine = ProductionExecutiveTest()
    results = await test_engine.run_comprehensive_test()
    
    # Generate JSON output file
    timestamp = int(time.time())
    output_filename = f"production_executive_discovery_results_{timestamp}.json"
    
    with open(output_filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print comprehensive summary
    logger.info("🎉 Production Executive Discovery Test - Complete")
    logger.info(f"📄 Results saved to: {output_filename}")
    logger.info(f"📊 Summary: {results['overall_metrics']['successful_discoveries']}/{results['overall_metrics']['total_companies_tested']} successful discoveries")
    logger.info(f"👥 Total executives found: {results['overall_metrics']['total_executives_found']}")
    logger.info(f"⏱️ Total time: {results['overall_metrics']['total_processing_time']:.2f}s")
    logger.info(f"🎯 Success rate: {results['overall_metrics']['success_rate_percentage']:.1f}%")
    logger.info(f"⚡ Average time per company: {results['overall_metrics']['average_processing_time']:.2f}s")
    
    # Print detailed breakdown
    print(f"\n✅ Production Test Complete!")
    print(f"📄 Results file: {output_filename}")
    print(f"📊 {results['overall_metrics']['successful_discoveries']}/{results['overall_metrics']['total_companies_tested']} companies had executive discoveries")
    print(f"👥 {results['overall_metrics']['total_executives_found']} total executives discovered")
    print(f"🎯 {results['overall_metrics']['success_rate_percentage']:.1f}% success rate")
    print(f"⏱️ {results['overall_metrics']['total_processing_time']:.1f}s total processing time")
    
    return output_filename

if __name__ == "__main__":
    # Run the comprehensive test
    output_file = asyncio.run(main()) 