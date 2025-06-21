#!/usr/bin/env python3
"""
Custom URL Testing Script for Executive Extraction System
Allows testing with user-selected URLs using the robust pipeline
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from typing import List, Dict, Any
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from seo_leads.processors.robust_executive_pipeline import RobustExecutivePipeline
    from seo_leads.fetchers.base_fetcher import BaseFetcher
    from seo_leads.processors.content_extractor import ContentExtractor
    from seo_leads.analyzers.seo_analyzer import SEOAnalyzer
except ImportError as e:
    print(f"Import error: {e}")
    print("Falling back to basic imports...")
    
    # Fallback imports
    try:
        from src.seo_leads.processors.robust_executive_pipeline import RobustExecutivePipeline
        from src.seo_leads.fetchers.base_fetcher import BaseFetcher
        from src.seo_leads.processors.content_extractor import ContentExtractor
        from src.seo_leads.analyzers.seo_analyzer import SEOAnalyzer
    except ImportError as e2:
        print(f"Fallback import also failed: {e2}")
        print("Please ensure the system is properly installed")
        sys.exit(1)


class CustomURLTester:
    """Test the executive extraction system with custom URLs"""
    
    def __init__(self):
        self.pipeline = RobustExecutivePipeline()
        self.fetcher = BaseFetcher()
        self.content_extractor = ContentExtractor()
        self.seo_analyzer = SEOAnalyzer()
        
    async def test_single_url(self, url: str) -> Dict[str, Any]:
        """Test a single URL and return detailed results"""
        print(f"\n🔍 Testing: {url}")
        start_time = time.time()
        
        try:
            # Fetch content
            print("  📥 Fetching content...")
            response = await self.fetcher.fetch(url)
            if not response or not response.get('content'):
                return {
                    'url': url,
                    'status': 'failed',
                    'error': 'Failed to fetch content',
                    'processing_time': time.time() - start_time
                }
            
            content = response['content']
            
            # Extract basic company info
            print("  🏢 Extracting company info...")
            extracted_data = self.content_extractor.extract_content(content, url)
            company_name = extracted_data.get('company_name', 'Unknown Company')
            
            # Extract executives using robust pipeline
            print("  👔 Extracting executives...")
            executives = await self.pipeline.extract_executives(url, content)
            
            # Calculate metrics
            processing_time = time.time() - start_time
            
            result = {
                'url': url,
                'company_name': company_name,
                'status': 'success',
                'processing_time': round(processing_time, 2),
                'extraction_timestamp': datetime.now().isoformat(),
                'executives_found': len(executives),
                'executives': executives,
                'quality_metrics': self._calculate_quality_metrics(executives)
            }
            
            print(f"  ✅ Complete: {len(executives)} executives found in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return {
                'url': url,
                'status': 'error',
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _calculate_quality_metrics(self, executives: List[Dict]) -> Dict[str, Any]:
        """Calculate quality metrics for the extracted executives"""
        if not executives:
            return {
                'total_executives': 0,
                'executives_with_emails': 0,
                'executives_with_phones': 0,
                'executives_with_linkedin': 0,
                'executives_with_meaningful_titles': 0,
                'high_quality_executives': 0,
                'average_confidence': 0.0
            }
        
        total = len(executives)
        with_emails = sum(1 for exec in executives if exec.get('email'))
        with_phones = sum(1 for exec in executives if exec.get('phone'))
        with_linkedin = sum(1 for exec in executives if exec.get('linkedin_url'))
        with_titles = sum(1 for exec in executives if exec.get('title') and exec.get('title') != 'Unknown')
        
        # High quality = has name + email/phone + meaningful title
        high_quality = sum(1 for exec in executives 
                          if exec.get('name') and 
                             (exec.get('email') or exec.get('phone')) and 
                             exec.get('title') and exec.get('title') != 'Unknown')
        
        confidences = [exec.get('overall_confidence', 0) for exec in executives]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'total_executives': total,
            'executives_with_emails': with_emails,
            'executives_with_phones': with_phones,
            'executives_with_linkedin': with_linkedin,
            'executives_with_meaningful_titles': with_titles,
            'high_quality_executives': high_quality,
            'average_confidence': round(avg_confidence, 3)
        }
    
    async def test_multiple_urls(self, urls: List[str]) -> Dict[str, Any]:
        """Test multiple URLs and return comprehensive results"""
        print(f"\n🚀 Starting test of {len(urls)} URLs...")
        print("=" * 60)
        
        start_time = time.time()
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}]", end=" ")
            result = await self.test_single_url(url)
            results.append(result)
            
            # Show progress
            if result['status'] == 'success':
                execs = result['executives_found']
                print(f"  📊 Progress: {i}/{len(urls)} complete ({execs} executives)")
            else:
                print(f"  ⚠️  Progress: {i}/{len(urls)} complete (failed)")
        
        total_time = time.time() - start_time
        
        # Calculate overall metrics
        successful_results = [r for r in results if r['status'] == 'success']
        total_executives = sum(r['executives_found'] for r in successful_results)
        
        # Aggregate quality metrics
        all_executives = []
        for result in successful_results:
            all_executives.extend(result.get('executives', []))
        
        overall_metrics = self._calculate_quality_metrics(all_executives)
        
        summary = {
            'test_summary': {
                'test_name': 'Custom URL Executive Extraction Test',
                'test_timestamp': datetime.now().isoformat(),
                'pipeline_used': 'robust_pipeline',
                'total_urls_tested': len(urls),
                'successful_extractions': len(successful_results),
                'failed_extractions': len(urls) - len(successful_results),
                'success_rate': f"{(len(successful_results)/len(urls)*100):.1f}%",
                'total_processing_time': f"{total_time:.2f} seconds",
                'average_time_per_url': f"{total_time/len(urls):.2f} seconds"
            },
            'metrics': {
                'total_executives_found': total_executives,
                'average_per_url': f"{total_executives/len(successful_results):.1f}" if successful_results else "0.0",
                'email_discovery_rate': f"{(overall_metrics['executives_with_emails']/total_executives*100):.1f}%" if total_executives else "0.0%",
                'phone_discovery_rate': f"{(overall_metrics['executives_with_phones']/total_executives*100):.1f}%" if total_executives else "0.0%",
                'linkedin_discovery_rate': f"{(overall_metrics['executives_with_linkedin']/total_executives*100):.1f}%" if total_executives else "0.0%",
                'meaningful_title_rate': f"{(overall_metrics['executives_with_meaningful_titles']/total_executives*100):.1f}%" if total_executives else "0.0%",
                'high_quality_rate': f"{(overall_metrics['high_quality_executives']/total_executives*100):.1f}%" if total_executives else "0.0%"
            },
            'detailed_results': results
        }
        
        return summary
    
    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """Save test results to JSON file"""
        if filename is None:
            timestamp = int(time.time())
            filename = f"custom_url_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        return filename


def get_urls_from_user() -> List[str]:
    """Get URLs from user input"""
    print("\n🔗 URL Input Options:")
    print("1. Enter URLs one by one")
    print("2. Paste multiple URLs (separated by newlines)")
    print("3. Load from file")
    
    choice = input("\nChoose option (1-3): ").strip()
    
    urls = []
    
    if choice == "1":
        print("\nEnter URLs one by one (press Enter with empty line to finish):")
        while True:
            url = input("URL: ").strip()
            if not url:
                break
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            urls.append(url)
    
    elif choice == "2":
        print("\nPaste all URLs (press Enter twice to finish):")
        lines = []
        while True:
            line = input().strip()
            if not line and lines:
                break
            if line:
                lines.append(line)
        
        for line in lines:
            url = line.strip()
            if url and not url.startswith('#'):  # Skip comments
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                urls.append(url)
    
    elif choice == "3":
        filename = input("Enter filename: ").strip()
        try:
            with open(filename, 'r') as f:
                for line in f:
                    url = line.strip()
                    if url and not url.startswith('#'):  # Skip comments and empty lines
                        if not url.startswith(('http://', 'https://')):
                            url = 'https://' + url
                        urls.append(url)
        except FileNotFoundError:
            print(f"File {filename} not found!")
            return get_urls_from_user()
    
    else:
        print("Invalid choice!")
        return get_urls_from_user()
    
    return urls


def display_results_summary(results: Dict[str, Any]):
    """Display a nice summary of test results"""
    summary = results['test_summary']
    metrics = results['metrics']
    
    print("\n" + "=" * 60)
    print("🎯 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"📊 URLs Tested: {summary['total_urls_tested']}")
    print(f"✅ Success Rate: {summary['success_rate']}")
    print(f"⏱️  Total Time: {summary['total_processing_time']}")
    print(f"⚡ Avg Time/URL: {summary['average_time_per_url']}")
    
    print(f"\n👔 EXECUTIVE DISCOVERY:")
    print(f"   Total Found: {metrics['total_executives_found']}")
    print(f"   Average per URL: {metrics['average_per_url']}")
    
    print(f"\n📞 CONTACT DISCOVERY:")
    print(f"   Email Rate: {metrics['email_discovery_rate']}")
    print(f"   Phone Rate: {metrics['phone_discovery_rate']}")
    print(f"   LinkedIn Rate: {metrics['linkedin_discovery_rate']}")
    
    print(f"\n🏆 QUALITY METRICS:")
    print(f"   Meaningful Titles: {metrics['meaningful_title_rate']}")
    print(f"   High Quality Executives: {metrics['high_quality_rate']}")
    
    # Show individual results
    print(f"\n📋 INDIVIDUAL RESULTS:")
    for result in results['detailed_results']:
        status_icon = "✅" if result['status'] == 'success' else "❌"
        if result['status'] == 'success':
            execs = result['executives_found']
            time_taken = result['processing_time']
            print(f"   {status_icon} {result['url']} - {execs} executives ({time_taken}s)")
        else:
            print(f"   {status_icon} {result['url']} - {result.get('error', 'Failed')}")


async def main():
    """Main function to run the custom URL tester"""
    print("🚀 Executive Extraction System - Custom URL Tester")
    print("=" * 60)
    print("This script tests the robust executive extraction pipeline")
    print("with URLs of your choice.\n")
    
    # Get URLs from user
    urls = get_urls_from_user()
    
    if not urls:
        print("❌ No URLs provided!")
        return
    
    print(f"\n✅ Got {len(urls)} URLs to test:")
    for i, url in enumerate(urls, 1):
        print(f"   {i}. {url}")
    
    # Confirm before testing
    confirm = input(f"\nProceed with testing {len(urls)} URLs? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Test cancelled.")
        return
    
    # Run the tests
    tester = CustomURLTester()
    results = await tester.test_multiple_urls(urls)
    
    # Display results
    display_results_summary(results)
    
    # Save results
    filename = tester.save_results(results)
    print(f"\n💾 Results saved to: {filename}")
    
    # Option to show detailed executive data
    show_details = input("\nShow detailed executive data? (y/N): ").strip().lower()
    if show_details in ['y', 'yes']:
        print("\n" + "=" * 60)
        print("👔 DETAILED EXECUTIVE DATA")
        print("=" * 60)
        
        for result in results['detailed_results']:
            if result['status'] == 'success' and result['executives']:
                print(f"\n🏢 {result['company_name']} ({result['url']})")
                for i, exec in enumerate(result['executives'], 1):
                    print(f"   {i}. {exec.get('name', 'Unknown')}")
                    print(f"      Title: {exec.get('title', 'Unknown')}")
                    print(f"      Email: {exec.get('email', 'Not found')}")
                    print(f"      Phone: {exec.get('phone', 'Not found')}")
                    print(f"      LinkedIn: {exec.get('linkedin_url', 'Not found')}")
                    print(f"      Confidence: {exec.get('overall_confidence', 0):.3f}")
                    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
