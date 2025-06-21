"""
Test Robust Executive Pipeline - Comprehensive System Validation
Tests the complete robust executive extraction system on real plumbing/heating company websites
"""

import sys
import os
import json
import time
import requests
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Simple content fetcher to avoid import issues
class SimpleFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def fetch_website_content(self, url):
        try:
            print(f"   📡 Fetching: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                print(f"   ✅ Status: {response.status_code}, Length: {len(response.text)} chars")
                return response.text
            else:
                print(f"   ❌ Status: {response.status_code}")
                return None
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return None

def test_robust_executive_system():
    """
    Test the complete robust executive extraction system
    """
    
    # Test URLs - Real plumbing/heating companies
    test_urls = [
        "http://www.mjmplumbingservices.uk/",
        "http://rnplumbingandheating.co.uk/",
        "http://www.andrewrileyheating.co.uk/",
        "http://www.boldmereplumbingservices.co.uk/",
        "http://jmplumbingheating.co.uk/",
        "https://www.nunnplumbingandgas.co.uk/contact"
    ]
    
    print("🔧 ROBUST EXECUTIVE PIPELINE VALIDATION TEST")
    print("=" * 70)
    print(f"Testing {len(test_urls)} real plumbing/heating company URLs")
    print(f"Validating complete semantic extraction system")
    print()
    
    # Initialize components
    fetcher = SimpleFetcher()
    
    # Import our robust components
    try:
        from seo_leads.ai.semantic_name_extractor import SemanticNameExtractor
        semantic_extractor = SemanticNameExtractor()
        print("✅ Semantic Name Extractor loaded")
    except Exception as e:
        print(f"❌ Failed to load Semantic Name Extractor: {e}")
        return None
    
    try:
        from seo_leads.extractors.advanced_contact_attributor import AdvancedContactAttributor
        contact_attributor = AdvancedContactAttributor()
        print("✅ Advanced Contact Attributor loaded")
    except Exception as e:
        print(f"❌ Failed to load Contact Attributor: {e}")
        contact_attributor = None
    
    try:
        from seo_leads.processors.executive_title_extractor import ExecutiveTitleExtractor
        title_extractor = ExecutiveTitleExtractor()
        print("✅ Executive Title Extractor loaded")
    except Exception as e:
        print(f"❌ Failed to load Title Extractor: {e}")
        title_extractor = None
    
    try:
        from seo_leads.scrapers.real_linkedin_discoverer import RealLinkedInDiscoverer
        linkedin_discoverer = RealLinkedInDiscoverer()
        print("✅ Real LinkedIn Discoverer loaded")
    except Exception as e:
        print(f"❌ Failed to load LinkedIn Discoverer: {e}")
        linkedin_discoverer = None
    
    print()
    
    results = {
        'test_summary': {
            'urls_tested': len(test_urls),
            'test_timestamp': datetime.now().isoformat(),
            'total_executives_found': 0,
            'total_emails_found': 0,
            'total_phones_found': 0,
            'total_titles_extracted': 0,
            'system_performance': {}
        },
        'detailed_results': []
    }
    
    total_executives = 0
    total_emails = 0
    total_phones = 0
    total_titles = 0
    
    for i, url in enumerate(test_urls, 1):
        print(f"🌐 Testing URL {i}/{len(test_urls)}: {url}")
        
        try:
            # Fetch content
            start_time = time.time()
            content = fetcher.fetch_website_content(url)
            fetch_time = time.time() - start_time
            
            if not content:
                print(f"❌ Failed to fetch content")
                continue
            
            # Phase 1: Semantic Name Extraction
            print(f"🧠 Phase 1: Semantic name extraction...")
            name_start = time.time()
            validated_names = semantic_extractor.extract_semantic_names(content)
            name_time = time.time() - name_start
            
            executives_found = len(validated_names)
            total_executives += executives_found
            
            print(f"   Found {executives_found} validated executives:")
            for name in validated_names:
                print(f"     • {name.text} (confidence: {name.confidence:.2f})")
                print(f"       Reasons: {', '.join(name.validation_reasons[:2])}")
            
            # Phase 2: Contact Attribution (if available)
            emails_found = 0
            phones_found = 0
            attributed_people = []
            
            if contact_attributor and validated_names:
                print(f"📧 Phase 2: Contact attribution...")
                contact_start = time.time()
                
                # Convert validated names to expected format
                people_for_attribution = [
                    {'name': name.text, 'position': name.position} 
                    for name in validated_names
                ]
                
                attributed_people = contact_attributor.attribute_contacts_to_people(
                    content, people_for_attribution
                )
                contact_time = time.time() - contact_start
                
                for person in attributed_people:
                    if person.get('email'):
                        emails_found += 1
                    if person.get('phone'):
                        phones_found += 1
                
                print(f"   Attributed {emails_found} emails, {phones_found} phones")
            
            # Phase 3: Title Extraction (if available)
            titles_found = 0
            people_with_titles = attributed_people if attributed_people else [
                {'name': name.text} for name in validated_names
            ]
            
            if title_extractor and validated_names:
                print(f"👔 Phase 3: Title extraction...")
                title_start = time.time()
                
                people_with_titles = title_extractor.extract_executive_titles(
                    content, people_with_titles
                )
                title_time = time.time() - title_start
                
                for person in people_with_titles:
                    if person.get('title') and person.get('title') != 'Unknown':
                        titles_found += 1
                
                print(f"   Extracted {titles_found} meaningful titles")
            
            # Phase 4: LinkedIn Discovery (optional, may be rate-limited)
            linkedin_found = 0
            if linkedin_discoverer and validated_names and len(validated_names) <= 2:  # Limit to avoid rate limiting
                print(f"🔗 Phase 4: LinkedIn discovery (limited)...")
                try:
                    company_info = {'name': 'Plumbing Services', 'domain': url}
                    enriched_people = linkedin_discoverer.discover_linkedin_profiles(
                        people_with_titles[:2], company_info  # Only test first 2
                    )
                    
                    for person in enriched_people:
                        if person.get('linkedin_url'):
                            linkedin_found += 1
                    
                    print(f"   Found {linkedin_found} LinkedIn profiles")
                    people_with_titles = enriched_people
                except Exception as e:
                    print(f"   ⚠️ LinkedIn discovery skipped: {str(e)}")
            
            total_emails += emails_found
            total_phones += phones_found
            total_titles += titles_found
            
            # Calculate processing time
            total_time = time.time() - start_time
            
            # Store results
            url_result = {
                'url': url,
                'content_length': len(content),
                'processing_times': {
                    'fetch_time': fetch_time,
                    'name_extraction_time': name_time,
                    'contact_attribution_time': contact_time if 'contact_time' in locals() else 0,
                    'title_extraction_time': title_time if 'title_time' in locals() else 0,
                    'total_time': total_time
                },
                'extraction_results': {
                    'executives_found': executives_found,
                    'emails_attributed': emails_found,
                    'phones_attributed': phones_found,
                    'titles_extracted': titles_found,
                    'linkedin_profiles': linkedin_found
                },
                'executives_data': [
                    {
                        'name': person.get('name', ''),
                        'title': person.get('title', 'Unknown'),
                        'email': person.get('email'),
                        'phone': person.get('phone'),
                        'linkedin_url': person.get('linkedin_url'),
                        'confidence_scores': {
                            'name': getattr(next((n for n in validated_names if n.text == person.get('name')), None), 'confidence', 0.0),
                            'title': person.get('title_confidence', 0.0),
                            'email': person.get('email_confidence', 0.0),
                            'phone': person.get('phone_confidence', 0.0)
                        }
                    }
                    for person in people_with_titles
                ],
                'semantic_validation': [
                    {
                        'name': name.text,
                        'confidence': name.confidence,
                        'validation_reasons': name.validation_reasons,
                        'context_snippet': name.context[:100] + "..." if len(name.context) > 100 else name.context
                    }
                    for name in validated_names
                ]
            }
            
            results['detailed_results'].append(url_result)
            
            print(f"📊 Results: {executives_found} execs, {emails_found} emails, {phones_found} phones, {titles_found} titles")
            print(f"⏱️  Processing time: {total_time:.2f}s")
            print("-" * 70)
            
        except Exception as e:
            print(f"❌ Error processing {url}: {str(e)}")
            print("-" * 70)
            continue
    
    # Calculate overall results
    results['test_summary']['total_executives_found'] = total_executives
    results['test_summary']['total_emails_found'] = total_emails
    results['test_summary']['total_phones_found'] = total_phones
    results['test_summary']['total_titles_extracted'] = total_titles
    
    # Calculate performance metrics
    if len(results['detailed_results']) > 0:
        avg_processing_time = sum(r['processing_times']['total_time'] for r in results['detailed_results']) / len(results['detailed_results'])
        executive_discovery_rate = total_executives / len(results['detailed_results'])
        contact_attribution_rate = (total_emails + total_phones) / max(total_executives, 1)
        title_extraction_rate = total_titles / max(total_executives, 1)
        
        results['test_summary']['system_performance'] = {
            'average_processing_time': avg_processing_time,
            'executive_discovery_rate': executive_discovery_rate,
            'contact_attribution_rate': contact_attribution_rate,
            'title_extraction_rate': title_extraction_rate,
            'overall_quality_score': (executive_discovery_rate + contact_attribution_rate + title_extraction_rate) / 3
        }
    
    # Print final summary
    print()
    print("🎯 ROBUST EXECUTIVE PIPELINE TEST RESULTS")
    print("=" * 70)
    print(f"📊 EXTRACTION SUMMARY:")
    print(f"   Total Executives Found: {total_executives}")
    print(f"   Total Emails Attributed: {total_emails}")
    print(f"   Total Phones Attributed: {total_phones}")
    print(f"   Total Titles Extracted: {total_titles}")
    print()
    
    if len(results['detailed_results']) > 0:
        perf = results['test_summary']['system_performance']
        print(f"📈 PERFORMANCE METRICS:")
        print(f"   Average Processing Time: {perf['average_processing_time']:.2f}s")
        print(f"   Executive Discovery Rate: {perf['executive_discovery_rate']:.2f} per URL")
        print(f"   Contact Attribution Rate: {perf['contact_attribution_rate']:.2f} per executive")
        print(f"   Title Extraction Rate: {perf['title_extraction_rate']:.2f} per executive")
        print(f"   Overall Quality Score: {perf['overall_quality_score']:.2f}/1.0")
        print()
    
    # Quality assessment
    if total_executives > 0:
        print("✅ SUCCESS: System is extracting real executives")
        if total_emails > 0 or total_phones > 0:
            print("✅ SUCCESS: Contact attribution is working")
        if total_titles > 0:
            print("✅ SUCCESS: Title extraction is working")
    else:
        print("⚠️  WARNING: No executives found - may need parameter tuning")
    
    # Save results
    timestamp = int(time.time())
    results_file = f'robust_executive_pipeline_test_results_{timestamp}.json'
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"💾 Complete results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    try:
        results = test_robust_executive_system()
        
        if results:
            summary = results['test_summary']
            print(f"\n🔥 QUICK SUMMARY:")
            print(f"   URLs Tested: {summary['urls_tested']}")
            print(f"   Executives Found: {summary['total_executives_found']}")
            print(f"   Contacts Attributed: {summary['total_emails_found'] + summary['total_phones_found']}")
            print(f"   System Quality: {summary.get('system_performance', {}).get('overall_quality_score', 0):.2f}/1.0")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc() 