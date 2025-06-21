#!/usr/bin/env python3
"""
Phase 5 Enhanced 9 URLs Test - Using Phase 5 Executive Engine
Tests the 9 URLs with Phase 5 accuracy enhancements for executive discovery.
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
import traceback

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class Phase5Enhanced9URLTest:
    """Enhanced test using Phase 5 components"""
    
    def __init__(self):
        """Initialize Phase 5 enhanced test"""
        self.test_urls = [
            "https://sitelift.site/richardhopeplumbingservices/",
            "https://www.am-electrical.co.uk/waterheater/",
            "https://www.trustatrader.com/traders/hgs-plumbing-heating-plumbers-selly-oak",
            "https://davisplumbing1.wixsite.com/davisplumbing",
            "http://mccannsheatingandplumbing.co.uk/",
            "http://www.fandpplumbing.co.uk/",
            "http://www.birminghamemergencyplumberforceheat.co.uk/",
            "https://www.pheaseyheating.co.uk/",
            "http://www.emergeplumbing.co.uk/"
        ]
        
        # Initialize Phase 5 components
        try:
            from seo_leads.processors.phase5_enhanced_executive_engine import Phase5EnhancedExecutiveEngine
            self.phase5_engine = Phase5EnhancedExecutiveEngine()
            self.phase5_available = True
            print("✅ Phase 5 Enhanced Executive Engine loaded successfully")
        except Exception as e:
            print(f"⚠️ Phase 5 engine not available: {e}")
            self.phase5_available = False
        
        self.results = {
            "test_metadata": {
                "test_name": "Phase 5 Enhanced 9 URLs Executive Discovery Test",
                "test_date": datetime.now().isoformat(),
                "total_urls": len(self.test_urls),
                "phase5_available": self.phase5_available,
                "components": [
                    "Advanced Name Validation Engine",
                    "Context-Aware Contact Extractor",
                    "Executive Seniority Analyzer", 
                    "LinkedIn Discovery Engine",
                    "Multi-Source Validation Engine"
                ]
            },
            "companies": [],
            "phase5_analytics": {
                "executive_discovery_rate": 0,
                "name_validation_accuracy": 0,
                "contact_attribution_rate": 0,
                "decision_maker_identification": 0,
                "linkedin_discovery_rate": 0,
                "data_quality_average": 0
            },
            "test_summary": {}
        }

    def extract_company_name(self, url: str) -> str:
        """Extract company name from URL"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace('www.', '')
        
        name_mapping = {
            "sitelift.site": "Richard Hope Plumbing Services",
            "am-electrical.co.uk": "AM Electrical",
            "trustatrader.com": "HGS Plumbing & Heating",
            "davisplumbing1.wixsite.com": "Davis Plumbing",
            "mccannsheatingandplumbing.co.uk": "McCann's Heating and Plumbing",
            "fandpplumbing.co.uk": "F&P Plumbing",
            "birminghamemergencyplumberforceheat.co.uk": "Birmingham Emergency Plumber Force Heat",
            "pheaseyheating.co.uk": "Pheasey Heating",
            "emergeplumbing.co.uk": "Emerge Plumbing"
        }
        
        for domain_key, name in name_mapping.items():
            if domain_key in domain:
                return name
        
        return f"Company from {domain}"

    async def test_single_url(self, url: str, index: int) -> Dict[str, Any]:
        """Test single URL with Phase 5 enhanced executive discovery"""
        print(f"\n🧪 Testing URL {index+1}/9: {url}")
        
        try:
            company_name = self.extract_company_name(url)
            print(f"   📝 Company: {company_name}")
            
            if not self.phase5_available:
                # Fallback to basic analysis
                return await self.basic_analysis(url, company_name)
            
            # Phase 5 Enhanced Executive Discovery
            print(f"   🚀 Running Phase 5 enhanced executive discovery...")
            phase5_result = await self.phase5_engine.discover_executives(url)
            
            # Extract detailed results
            executives = phase5_result.get("executives", [])
            name_validation = phase5_result.get("name_validation", {})
            contact_attribution = phase5_result.get("contact_attribution", {})
            seniority_analysis = phase5_result.get("seniority_analysis", {})
            linkedin_discovery = phase5_result.get("linkedin_discovery", {})
            data_validation = phase5_result.get("data_validation", {})
            
            print(f"   👥 Executives found: {len(executives)}")
            print(f"   ✅ Name validation: {name_validation.get('validation_success', False)}")
            print(f"   📞 Contact attribution: {contact_attribution.get('attribution_success', False)}")
            
            # Compile comprehensive result
            result = {
                "url": url,
                "company_name": company_name,
                "status": "success",
                "phase5_executive_discovery": {
                    "executives_found": len(executives),
                    "executives": executives,
                    "name_validation": name_validation,
                    "contact_attribution": contact_attribution,
                    "seniority_analysis": seniority_analysis,
                    "linkedin_discovery": linkedin_discovery,
                    "data_validation": data_validation
                },
                "discovery_summary": {
                    "decision_makers_identified": sum(1 for exec in executives if exec.get("seniority_tier") == "tier_1"),
                    "contacts_attributed": sum(1 for exec in executives if exec.get("email") or exec.get("phone")),
                    "linkedin_profiles_found": sum(1 for exec in executives if exec.get("linkedin_url")),
                    "overall_confidence": data_validation.get("overall_confidence", 0),
                    "data_quality_score": data_validation.get("quality_score", 0)
                },
                "processing_time": 0.0
            }
            
            return result
            
        except Exception as e:
            print(f"   ❌ Error processing {url}: {str(e)}")
            return {
                "url": url,
                "company_name": company_name,
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    async def basic_analysis(self, url: str, company_name: str) -> Dict[str, Any]:
        """Basic analysis when Phase 5 not available"""
        print(f"   📋 Running basic analysis (Phase 5 not available)")
        
        return {
            "url": url,
            "company_name": company_name,
            "status": "basic_fallback",
            "message": "Phase 5 enhanced engine not available - basic analysis performed",
            "phase5_executive_discovery": {
                "executives_found": 0,
                "executives": [],
                "error": "Phase 5 engine not loaded"
            },
            "processing_time": 0.0
        }

    async def run_enhanced_test(self):
        """Run Phase 5 enhanced test on all 9 URLs"""
        print("🚀 STARTING PHASE 5 ENHANCED 9 URLs EXECUTIVE DISCOVERY TEST")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # Process all URLs
        for i, url in enumerate(self.test_urls):
            url_start = datetime.now()
            result = await self.test_single_url(url, i)
            url_end = datetime.now()
            
            if 'processing_time' in result:
                result['processing_time'] = (url_end - url_start).total_seconds()
            
            self.results["companies"].append(result)
        
        # Calculate Phase 5 analytics
        self._calculate_phase5_analytics()
        
        # Generate test summary
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        successful = sum(1 for r in self.results["companies"] if r["status"] == "success")
        failed = sum(1 for r in self.results["companies"] if r["status"] == "error")
        fallback = sum(1 for r in self.results["companies"] if r["status"] == "basic_fallback")
        
        self.results["test_summary"] = {
            "total_processing_time": total_time,
            "average_time_per_url": total_time / len(self.test_urls),
            "successful_extractions": successful,
            "failed_extractions": failed,
            "fallback_extractions": fallback,
            "success_rate": (successful / len(self.test_urls)) * 100 if successful > 0 else 0
        }
        
        print("\n" + "=" * 80)
        print("🎯 PHASE 5 ENHANCED TEST SUMMARY")
        print(f"✅ Successfully processed: {successful}/9 URLs")
        print(f"📋 Fallback analysis: {fallback}/9 URLs")
        print(f"❌ Failed processing: {failed}/9 URLs")
        print(f"📊 Success rate: {self.results['test_summary']['success_rate']:.1f}%")
        print(f"⏱️ Total time: {total_time:.2f} seconds")
        print(f"⚡ Average per URL: {self.results['test_summary']['average_time_per_url']:.2f} seconds")

    def _calculate_phase5_analytics(self):
        """Calculate Phase 5 specific analytics"""
        successful_results = [r for r in self.results["companies"] if r["status"] == "success"]
        
        if not successful_results:
            return
        
        total = len(successful_results)
        
        # Executive discovery rate
        exec_found = sum(1 for r in successful_results 
                        if r.get("phase5_executive_discovery", {}).get("executives_found", 0) > 0)
        self.results["phase5_analytics"]["executive_discovery_rate"] = (exec_found / total) * 100
        
        # Name validation accuracy
        name_valid = sum(1 for r in successful_results 
                        if r.get("phase5_executive_discovery", {}).get("name_validation", {}).get("validation_success", False))
        self.results["phase5_analytics"]["name_validation_accuracy"] = (name_valid / total) * 100
        
        # Contact attribution rate
        contact_attributed = sum(1 for r in successful_results 
                               if r.get("discovery_summary", {}).get("contacts_attributed", 0) > 0)
        self.results["phase5_analytics"]["contact_attribution_rate"] = (contact_attributed / total) * 100
        
        # Decision maker identification
        decision_makers = sum(1 for r in successful_results 
                            if r.get("discovery_summary", {}).get("decision_makers_identified", 0) > 0)
        self.results["phase5_analytics"]["decision_maker_identification"] = (decision_makers / total) * 100
        
        # LinkedIn discovery rate
        linkedin_found = sum(1 for r in successful_results 
                           if r.get("discovery_summary", {}).get("linkedin_profiles_found", 0) > 0)
        self.results["phase5_analytics"]["linkedin_discovery_rate"] = (linkedin_found / total) * 100
        
        # Data quality average
        quality_scores = [r.get("discovery_summary", {}).get("data_quality_score", 0) 
                         for r in successful_results]
        self.results["phase5_analytics"]["data_quality_average"] = sum(quality_scores) / len(quality_scores) if quality_scores else 0

    def save_results(self, filename: str = None):
        """Save Phase 5 test results to JSON file"""
        if filename is None:
            timestamp = int(datetime.now().timestamp())
            filename = f"phase5_enhanced_9_url_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Results saved to: {filename}")
        return filename

async def main():
    """Main test execution"""
    print("🔬 PHASE 5 ENHANCED 9 URLs EXECUTIVE DISCOVERY TEST")
    print("Testing with Phase 5 accuracy enhancements and executive discovery")
    print()
    
    test = Phase5Enhanced9URLTest()
    
    try:
        await test.run_enhanced_test()
        filename = test.save_results()
        
        # Display Phase 5 analytics
        if test.phase5_available:
            print("\n🎯 PHASE 5 ACCURACY ANALYTICS:")
            analytics = test.results["phase5_analytics"]
            print(f"   Executive Discovery Rate: {analytics['executive_discovery_rate']:.1f}%")
            print(f"   Name Validation Accuracy: {analytics['name_validation_accuracy']:.1f}%")
            print(f"   Contact Attribution Rate: {analytics['contact_attribution_rate']:.1f}%")
            print(f"   Decision Maker Identification: {analytics['decision_maker_identification']:.1f}%")
            print(f"   LinkedIn Discovery Rate: {analytics['linkedin_discovery_rate']:.1f}%")
            print(f"   Data Quality Average: {analytics['data_quality_average']:.1f}/100")
        
        print(f"\n✅ Complete results saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main()) 