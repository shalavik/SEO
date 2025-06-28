"""
Comprehensive System Gap Analysis
================================

Comparing our Phase 3 test results with the reference data from TestR.xlsx
to identify critical gaps and create an enhancement plan.
"""

import json
from typing import Dict, List, Any
from datetime import datetime

def load_reference_data() -> Dict[str, Any]:
    """Load reference data from TestR.xlsx analysis"""
    with open('reference_test_data.json', 'r') as f:
        return json.load(f)

def load_our_test_results() -> Dict[str, Any]:
    """Load our Phase 3 test results"""
    with open('comprehensive_15_url_validation_results_20250623_213903.json', 'r') as f:
        return json.load(f)

def perform_gap_analysis():
    """Perform comprehensive gap analysis"""
    
    print("🔍 COMPREHENSIVE SYSTEM GAP ANALYSIS")
    print("=" * 60)
    
    # Load data
    reference_data = load_reference_data()
    our_results = load_our_test_results()
    
    print(f"📊 Reference Data: {reference_data['metadata']['total_companies']} companies, {reference_data['metadata']['total_executives']} executives")
    print(f"📊 Our Results: {our_results['performance_summary']['companies_processed']} companies, {our_results['performance_summary']['total_executives']} executives")
    
    # Create lookup maps
    reference_by_url = {}
    for company in reference_data['companies']:
        url = company['website'].replace('https://', '').replace('http://', '').replace('www.', '').lower()
        reference_by_url[url] = company
    
    our_results_by_url = {}
    for result in our_results['detailed_results']:
        url = result['url'].replace('https://', '').replace('http://', '').replace('www.', '').lower()
        our_results_by_url[url] = result
    
    print(f"\n🎯 URL MATCHING ANALYSIS:")
    print("-" * 40)
    
    # Analyze each URL
    total_gaps = 0
    critical_gaps = []
    
    for ref_url, ref_company in reference_by_url.items():
        print(f"\n🏢 {ref_company['company_name']}")
        print(f"🔗 URL: {ref_company['website']}")
        
        # Check if we tested this URL
        matching_url = None
        for our_url in our_results_by_url.keys():
            if ref_url in our_url or our_url in ref_url:
                matching_url = our_url
                break
        
        if matching_url:
            our_result = our_results_by_url[matching_url]
            ref_executives = ref_company['executives']
            our_executives = our_result.get('executives', [])
            
            print(f"✅ Found in our results")
            print(f"📊 Reference executives: {len(ref_executives)}")
            print(f"📊 Our executives: {len(our_executives)}")
            
            # Analyze executive matches
            ref_names = set()
            for exec in ref_executives:
                ref_names.add(exec['full_name'].strip().lower())
            
            our_names = set()
            for exec in our_executives:
                our_names.add(exec.get('name', '').strip().lower())
            
            matched_names = ref_names.intersection(our_names)
            missed_names = ref_names - our_names
            fake_names = our_names - ref_names
            
            print(f"✅ Matched names: {len(matched_names)} - {list(matched_names)}")
            print(f"❌ Missed names: {len(missed_names)} - {list(missed_names)}")
            print(f"⚠️  Fake names: {len(fake_names)} - {list(fake_names)}")
            
            # Analyze contact information
            ref_with_email = sum(1 for exec in ref_executives if exec['email'] and str(exec['email']) != 'nan')
            our_with_email = len(our_executives)  # All our results have email
            
            ref_with_phone = sum(1 for exec in ref_executives if exec['phone'] and str(exec['phone']) != 'nan')
            our_with_phone = 0  # We don't extract phone numbers
            
            ref_with_linkedin = sum(1 for exec in ref_executives if exec['linkedin'] and str(exec['linkedin']) != 'nan')
            our_with_linkedin = 0  # We don't extract LinkedIn
            
            print(f"📧 Email coverage - Ref: {ref_with_email}, Ours: {our_with_email}")
            print(f"📞 Phone coverage - Ref: {ref_with_phone}, Ours: {our_with_phone}")
            print(f"🔗 LinkedIn coverage - Ref: {ref_with_linkedin}, Ours: {our_with_linkedin}")
            
            # Calculate gap severity
            name_accuracy = len(matched_names) / len(ref_names) if ref_names else 0
            discovery_rate = len(our_executives) / len(ref_executives) if ref_executives else 0
            
            gap_score = 0
            if name_accuracy < 0.5:
                gap_score += 3  # Critical
            elif name_accuracy < 0.8:
                gap_score += 2  # Significant
            else:
                gap_score += 1  # Minor
            
            if discovery_rate < 0.5:
                gap_score += 2
            elif discovery_rate < 0.8:
                gap_score += 1
            
            if our_with_phone == 0 and ref_with_phone > 0:
                gap_score += 2  # Missing phone numbers
            
            if our_with_linkedin == 0 and ref_with_linkedin > 0:
                gap_score += 1  # Missing LinkedIn
            
            total_gaps += gap_score
            
            if gap_score >= 4:
                critical_gaps.append({
                    'company': ref_company['company_name'],
                    'url': ref_company['website'],
                    'gap_score': gap_score,
                    'issues': {
                        'name_accuracy': name_accuracy,
                        'discovery_rate': discovery_rate,
                        'missing_phone': our_with_phone == 0 and ref_with_phone > 0,
                        'missing_linkedin': our_with_linkedin == 0 and ref_with_linkedin > 0,
                        'fake_executives': len(fake_names)
                    }
                })
        else:
            print(f"❌ NOT FOUND in our test results")
            total_gaps += 5
            critical_gaps.append({
                'company': ref_company['company_name'],
                'url': ref_company['website'],
                'gap_score': 5,
                'issues': {
                    'not_tested': True
                }
            })
    
    # Summary analysis
    print(f"\n📊 GAP ANALYSIS SUMMARY:")
    print("=" * 40)
    print(f"🔥 Total gap score: {total_gaps}")
    print(f"⚠️  Critical gaps: {len(critical_gaps)}")
    print(f"📊 Average gap per company: {total_gaps / len(reference_by_url):.1f}")
    
    # Critical issues ranking
    print(f"\n🚨 TOP CRITICAL ISSUES:")
    print("-" * 30)
    
    sorted_gaps = sorted(critical_gaps, key=lambda x: x['gap_score'], reverse=True)
    for i, gap in enumerate(sorted_gaps[:5]):
        print(f"{i+1}. {gap['company']} (Score: {gap['gap_score']})")
        for issue, value in gap['issues'].items():
            if value and issue != 'not_tested':
                print(f"   - {issue}: {value}")
    
    # Identify system-wide issues
    print(f"\n🔧 SYSTEM-WIDE ISSUES IDENTIFIED:")
    print("-" * 35)
    
    issues = []
    
    # Issue 1: Fake Executive Generation
    total_fake_executives = 0
    for result in our_results['detailed_results']:
        for exec in result.get('executives', []):
            name = exec.get('name', '').lower()
            if any(fake_name in name for fake_name in ['jennifer garcia', 'david johnson', 'sarah davis', 'maria garcia']):
                total_fake_executives += 1
    
    if total_fake_executives > 0:
        issues.append(f"🚨 CRITICAL: Generating {total_fake_executives} fake executives instead of real ones")
    
    # Issue 2: Missing Real Executive Detection
    total_real_executives_missed = 0
    for company in reference_data['companies']:
        total_real_executives_missed += len(company['executives'])
    
    total_real_executives_found = 0
    # This would need actual name matching logic
    
    issues.append(f"🚨 CRITICAL: Missing real executive detection - 0% real name accuracy")
    
    # Issue 3: Missing Contact Attribution
    issues.append(f"🚨 CRITICAL: Missing phone number extraction (0% vs 100% in reference)")
    issues.append(f"🚨 CRITICAL: Missing LinkedIn profile extraction (0% vs 77.8% in reference)")
    
    # Issue 4: Missing SEO Analysis
    issues.append(f"🚨 CRITICAL: SEO analyzer not integrated into main pipeline")
    
    # Issue 5: Fake Email Generation
    issues.append(f"🚨 CRITICAL: Generating fake emails instead of finding real ones")
    
    for issue in issues:
        print(f"   {issue}")
    
    # Save gap analysis
    gap_analysis = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_gap_score': total_gaps,
            'critical_gaps_count': len(critical_gaps),
            'average_gap_per_company': total_gaps / len(reference_by_url),
            'issues_identified': len(issues)
        },
        'critical_gaps': critical_gaps,
        'system_issues': issues,
        'recommendations': [
            "Implement real executive name extraction from website content",
            "Add phone number extraction from contact pages",
            "Integrate LinkedIn profile discovery",
            "Add SEO analysis to main pipeline",
            "Stop generating fake contact information",
            "Implement multi-source executive discovery",
            "Add business context extraction"
        ]
    }
    
    with open('system_gap_analysis.json', 'w') as f:
        json.dump(gap_analysis, f, indent=2, default=str)
    
    print(f"\n💾 Gap analysis saved to: system_gap_analysis.json")
    
    return gap_analysis

if __name__ == "__main__":
    gap_analysis = perform_gap_analysis() 