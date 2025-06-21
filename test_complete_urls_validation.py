"""
Complete URL Validation Test - Test all 8 URLs provided by user
"""

import sys
import os
import json
import time
import requests
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Simple content fetcher
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

def test_all_provided_urls():
    """Test all 8 URLs provided by the user"""
    
    # Complete list of URLs from user
    test_urls = [
        "http://www.mjmplumbingservices.uk/",
        "http://rnplumbingandheating.co.uk/",
        "http://www.andrewrileyheating.co.uk/",
        "http://www.boldmereplumbingservices.co.uk/",
        "http://jmplumbingheating.co.uk/",
        "https://www.nunnplumbingandgas.co.uk/contact",
        "https://konigashomeservices.co.uk/",
        "http://www.ttsafegas.com/"
    ]
    
    print("🔧 COMPLETE URL VALIDATION TEST")
    print("=" * 70)
    print(f"Testing {len(test_urls)} URLs with robust executive extraction")
    print()
    
    # Initialize components
    fetcher = SimpleFetcher()
    
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
    
    print()
    
    results = {
        'test_summary': {
            'urls_tested': len(test_urls),
            'test_timestamp': datetime.now().isoformat(),
            'total_executives_found': 0,
            'total_emails_found': 0,
            'total_phones_found': 0,
            'quality_issues_detected': []
        },
        'detailed_results': []
    }
    
    total_executives = 0
    total_emails = 0
    total_phones = 0
    quality_issues = []
    
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
            
            # Semantic Name Extraction
            print(f"🧠 Semantic name extraction...")
            name_start = time.time()
            validated_names = semantic_extractor.extract_semantic_names(content)
            name_time = time.time() - name_start
            
            executives_found = len(validated_names)
            total_executives += executives_found
            
            print(f"   Found {executives_found} validated executives:")
            for name in validated_names:
                print(f"     • {name.text} (confidence: {name.confidence:.2f})")
                print(f"       Reasons: {', '.join(name.validation_reasons[:2])}")
                
                # Quality check for false positives
                name_lower = name.text.lower()
                problematic_terms = ['price', 'guarantee', 'service', 'quality', 'emergency', 'heating', 'plumbing']
                for term in problematic_terms:
                    if term in name_lower:
                        quality_issues.append({
                            'url': url,
                            'issue': f"Potential false positive: '{name.text}' contains '{term}'"
                        })
                        print(f"       ⚠️  QUALITY ISSUE: Potential false positive")
            
            # Contact Attribution
            emails_found = 0
            phones_found = 0
            attributed_people = []
            
            if contact_attributor and validated_names:
                print(f"📧 Contact attribution...")
                contact_start = time.time()
                
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
            
            total_emails += emails_found
            total_phones += phones_found
            
            # Store results
            total_time = time.time() - start_time
            
            url_result = {
                'url': url,
                'processing_time': total_time,
                'extraction_results': {
                    'executives_found': executives_found,
                    'emails_attributed': emails_found,
                    'phones_attributed': phones_found
                },
                'executives_data': [
                    {
                        'name': person.get('name', ''),
                        'email': person.get('email'),
                        'phone': person.get('phone'),
                        'confidence': getattr(next((n for n in validated_names if n.text == person.get('name')), None), 'confidence', 0.0)
                    }
                    for person in (attributed_people if attributed_people else [{'name': name.text} for name in validated_names])
                ],
                'semantic_validation': [
                    {
                        'name': name.text,
                        'confidence': name.confidence,
                        'validation_reasons': name.validation_reasons
                    }
                    for name in validated_names
                ]
            }
            
            results['detailed_results'].append(url_result)
            
            print(f"📊 Results: {executives_found} execs, {emails_found} emails, {phones_found} phones")
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
    results['test_summary']['quality_issues_detected'] = quality_issues
    
    # Print final summary
    print()
    print("🎯 COMPLETE URL VALIDATION RESULTS")
    print("=" * 70)
    print(f"📊 EXTRACTION SUMMARY:")
    print(f"   Total Executives Found: {total_executives}")
    print(f"   Total Emails Attributed: {total_emails}")
    print(f"   Total Phones Attributed: {total_phones}")
    print()
    
    # Quality assessment
    if quality_issues:
        print("⚠️  QUALITY ISSUES DETECTED:")
        for issue in quality_issues:
            print(f"   • {issue['issue']}")
        print()
    
    if total_executives > 0:
        contact_rate = (total_emails + total_phones) / total_executives
        print(f"📈 PERFORMANCE:")
        print(f"   Executive Discovery Rate: {total_executives / len(results['detailed_results']):.2f} per URL")
        print(f"   Contact Attribution Rate: {contact_rate:.2f} per executive")
        print(f"   Quality Issues: {len(quality_issues)} detected")
        
        if len(quality_issues) == 0:
            print("✅ HIGH QUALITY: No false positives detected")
        elif len(quality_issues) <= 2:
            print("⚠️  MEDIUM QUALITY: Few quality issues detected")
        else:
            print("❌ LOW QUALITY: Multiple quality issues detected")
    
    # Save results
    timestamp = int(time.time())
    results_file = f'complete_url_validation_results_{timestamp}.json'
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"💾 Complete results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    try:
        results = test_all_provided_urls()
        
        if results:
            summary = results['test_summary']
            print(f"\n🔥 FINAL SUMMARY:")
            print(f"   URLs Tested: {summary['urls_tested']}")
            print(f"   Executives Found: {summary['total_executives_found']}")
            print(f"   Contacts Attributed: {summary['total_emails_found'] + summary['total_phones_found']}")
            print(f"   Quality Issues: {len(summary['quality_issues_detected'])}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc() 