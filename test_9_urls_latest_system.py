#!/usr/bin/env python3
"""
Latest System Test - 9 URLs with Phase 5 Accuracy Enhancements
Tests the complete pipeline including all Phase 5 accuracy improvements.
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

from seo_leads.processors.phase5_enhanced_executive_engine import Phase5EnhancedExecutiveEngine
from seo_leads.processors.contact_extractor import ContactExtractor
from seo_leads.processors.lead_qualifier import LeadQualifier
from seo_leads.analyzers.seo_analyzer import SEOAnalyzer
from seo_leads.models import Company

class Latest9URLTestPipeline:
    """Test pipeline for 9 URLs with latest Phase 5 enhancements"""
    
    def __init__(self):
        """Initialize test pipeline with all Phase 5 components"""
        self.phase5_engine = Phase5EnhancedExecutiveEngine()
        self.contact_extractor = ContactExtractor()
        self.lead_qualifier = LeadQualifier()
        self.seo_analyzer = SEOAnalyzer()
        
        # Test URLs
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
        
        self.results = {
            "test_metadata": {
                "test_name": "Latest System 9 URLs Phase 5 Accuracy Test",
                "test_date": datetime.now().isoformat(),
                "total_urls": len(self.test_urls),
                "phase5_components": [
                    "Advanced Name Validation Engine",
                    "Context-Aware Contact Extractor", 
                    "Executive Seniority Analyzer",
                    "LinkedIn Discovery Engine",
                    "Multi-Source Validation Engine"
                ]
            },
            "companies": [],
            "phase5_analytics": {
                "name_validation_accuracy": 0,
                "contact_attribution_accuracy": 0,
                "executive_discovery_rate": 0,
                "decision_maker_identification": 0,
                "data_quality_score": 0
            },
            "test_summary": {}
        }

    async def test_single_url(self, url: str, index: int) -> Dict[str, Any]:
        """Test single URL with full Phase 5 pipeline"""
        print(f"\n🧪 Testing URL {index+1}/9: {url}")
        
        try:
            # Step 1: Basic company extraction
            company = Company(
                name=f"Company_{index+1}",
                website=url,
                industry="Plumbing/Electrical Services"
            )
            
            print(f"   📝 Company created: {company.name}")
            
            # Step 2: Contact extraction with attribution
            contacts = await self.contact_extractor.extract_contacts(url)
            print(f"   📞 Contacts extracted: {len(contacts)}")
            
            # Step 3: Phase 5 Enhanced Executive Discovery
            phase5_result = await self.phase5_engine.discover_executives(url)
            print(f"   👥 Phase 5 executive discovery completed")
            
            # Step 4: SEO Analysis
            seo_analysis = await self.seo_analyzer.analyze_website(url)
            print(f"   📊 SEO analysis completed: Score {seo_analysis.overall_score}")
            
            # Step 5: Lead qualification
            qualification = self.lead_qualifier.qualify_lead(company, contacts)
            print(f"   ⭐ Lead qualification: {qualification.quality_tier}")
            
            # Compile comprehensive result
            result = {
                "url": url,
                "company_name": company.name,
                "status": "success",
                "basic_contacts": [
                    {
                        "type": contact.contact_type,
                        "value": contact.value,
                        "confidence": contact.confidence
                    } for contact in contacts
                ],
                "phase5_results": {
                    "executives_found": len(phase5_result.get("executives", [])),
                    "name_validation_results": phase5_result.get("name_validation", {}),
                    "contact_attribution": phase5_result.get("contact_attribution", {}),
                    "seniority_analysis": phase5_result.get("seniority_analysis", {}),
                    "linkedin_discovery": phase5_result.get("linkedin_discovery", {}),
                    "data_validation": phase5_result.get("data_validation", {}),
                    "executives": phase5_result.get("executives", [])
                },
                "seo_analysis": {
                    "overall_score": seo_analysis.overall_score,
                    "content_quality": seo_analysis.content_quality,
                    "technical_seo": seo_analysis.technical_seo,
                    "local_seo": seo_analysis.local_seo
                },
                "lead_qualification": {
                    "quality_tier": qualification.quality_tier,
                    "score": qualification.score,
                    "decision_makers": qualification.decision_makers,
                    "contact_completeness": qualification.contact_completeness
                },
                "processing_time": 0.0
            }
            
            return result
            
        except Exception as e:
            print(f"   ❌ Error processing {url}: {str(e)}")
            return {
                "url": url,
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    async def run_comprehensive_test(self):
        """Run complete test pipeline on all 9 URLs"""
        print("🚀 STARTING LATEST SYSTEM TEST - 9 URLs WITH PHASE 5 ENHANCEMENTS")
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
        
        self.results["test_summary"] = {
            "total_processing_time": total_time,
            "average_time_per_url": total_time / len(self.test_urls),
            "successful_extractions": sum(1 for r in self.results["companies"] if r["status"] == "success"),
            "failed_extractions": sum(1 for r in self.results["companies"] if r["status"] == "error"),
            "success_rate": (sum(1 for r in self.results["companies"] if r["status"] == "success") / len(self.test_urls)) * 100
        }
        
        print("\n" + "=" * 80)
        print("🎯 TEST COMPLETION SUMMARY")
        print(f"✅ Successfully processed: {self.results['test_summary']['successful_extractions']}/9 URLs")
        print(f"❌ Failed processing: {self.results['test_summary']['failed_extractions']}/9 URLs")
        print(f"📊 Success rate: {self.results['test_summary']['success_rate']:.1f}%")
        print(f"⏱️ Total time: {total_time:.2f} seconds")
        print(f"⚡ Average per URL: {self.results['test_summary']['average_time_per_url']:.2f} seconds")

    def _calculate_phase5_analytics(self):
        """Calculate Phase 5 accuracy analytics"""
        successful_results = [r for r in self.results["companies"] if r["status"] == "success"]
        
        if not successful_results:
            return
        
        # Name validation accuracy
        valid_names = sum(1 for r in successful_results 
                         if r.get("phase5_results", {}).get("name_validation_results", {}).get("validation_success", False))
        self.results["phase5_analytics"]["name_validation_accuracy"] = (valid_names / len(successful_results)) * 100
        
        # Contact attribution accuracy
        attributed_contacts = sum(1 for r in successful_results 
                                if r.get("phase5_results", {}).get("contact_attribution", {}).get("attribution_success", False))
        self.results["phase5_analytics"]["contact_attribution_accuracy"] = (attributed_contacts / len(successful_results)) * 100
        
        # Executive discovery rate
        exec_discoveries = sum(1 for r in successful_results 
                             if r.get("phase5_results", {}).get("executives_found", 0) > 0)
        self.results["phase5_analytics"]["executive_discovery_rate"] = (exec_discoveries / len(successful_results)) * 100
        
        # Decision maker identification
        decision_makers = sum(1 for r in successful_results 
                            if r.get("lead_qualification", {}).get("decision_makers", 0) > 0)
        self.results["phase5_analytics"]["decision_maker_identification"] = (decision_makers / len(successful_results)) * 100
        
        # Data quality score (average)
        quality_scores = [r.get("phase5_results", {}).get("data_validation", {}).get("quality_score", 0) 
                         for r in successful_results]
        self.results["phase5_analytics"]["data_quality_score"] = sum(quality_scores) / len(quality_scores) if quality_scores else 0

    def save_results(self, filename: str = None):
        """Save test results to JSON file"""
        if filename is None:
            timestamp = int(datetime.now().timestamp())
            filename = f"latest_9_url_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Results saved to: {filename}")
        return filename

async def main():
    """Main test execution"""
    print("🔬 LATEST SYSTEM TEST - 9 URLs WITH PHASE 5 ACCURACY ENHANCEMENTS")
    print("Testing comprehensive pipeline with all latest improvements")
    print()
    
    pipeline = Latest9URLTestPipeline()
    
    try:
        await pipeline.run_comprehensive_test()
        filename = pipeline.save_results()
        
        # Display key metrics
        print("\n🎯 PHASE 5 ACCURACY METRICS:")
        analytics = pipeline.results["phase5_analytics"]
        print(f"   Name Validation Accuracy: {analytics['name_validation_accuracy']:.1f}%")
        print(f"   Contact Attribution Accuracy: {analytics['contact_attribution_accuracy']:.1f}%")
        print(f"   Executive Discovery Rate: {analytics['executive_discovery_rate']:.1f}%")
        print(f"   Decision Maker Identification: {analytics['decision_maker_identification']:.1f}%")
        print(f"   Data Quality Score: {analytics['data_quality_score']:.1f}/100")
        
        print(f"\n✅ Complete results saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main()) 