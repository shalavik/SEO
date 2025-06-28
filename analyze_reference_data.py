import pandas as pd
import json

def analyze_reference_data():
    """Analyze the reference test data from TestR.xlsx"""
    
    # Read the Excel file
    df = pd.read_excel('TestR.xlsx')
    
    print("🔍 REFERENCE DATA ANALYSIS - TestR.xlsx")
    print("=" * 60)
    print(f"📊 Total Records: {len(df)}")
    print(f"📊 Columns: {len(df.columns)}")
    
    print("\n📋 COLUMN ANALYSIS:")
    for col in df.columns:
        non_null = df[col].count()
        print(f"  {col}: {non_null}/{len(df)} values ({non_null/len(df)*100:.1f}%)")
    
    print("\n🏢 COMPANY ANALYSIS:")
    print("-" * 40)
    
    companies_by_website = {}
    
    for i, row in df.iterrows():
        company_name = row.get('Company Name', 'Unknown')
        website = row.get('Website', 'Unknown')
        first_name = row.get('Owner First Name', '')
        last_name = row.get('Owner Last Name', '')
        title = row.get('Title', '')
        email = row.get('Company Email', '')
        phone = row.get('Phone #', '')
        direct = row.get('Direct #', '')
        mobile = row.get('Mobile #', '')
        linkedin = row.get('Linkedin Profile URL', '')
        
        if website not in companies_by_website:
            companies_by_website[website] = {
                'company_name': company_name,
                'website': website,
                'executives': []
            }
        
        executive = {
            'first_name': first_name,
            'last_name': last_name,
            'full_name': f"{first_name} {last_name}".strip(),
            'title': title,
            'email': email,
            'phone': phone,
            'direct': direct,
            'mobile': mobile,
            'linkedin': linkedin
        }
        
        companies_by_website[website]['executives'].append(executive)
        
        print(f"{i+1:2d}. {company_name}")
        print(f"    🔗 Website: {website}")
        print(f"    👤 Executive: {first_name} {last_name} ({title})")
        print(f"    📧 Email: {email}")
        print(f"    📞 Phone: {phone}")
        if direct and str(direct) != 'nan':
            print(f"    📞 Direct: {direct}")
        if mobile and str(mobile) != 'nan':
            print(f"    📱 Mobile: {mobile}")
        if linkedin and str(linkedin) != 'nan':
            print(f"    🔗 LinkedIn: {linkedin}")
        print()
    
    # Analyze by unique companies
    print("\n🏭 UNIQUE COMPANIES ANALYSIS:")
    print("-" * 40)
    
    unique_companies = []
    for website, data in companies_by_website.items():
        unique_companies.append(data)
    
    print(f"📊 Total unique companies: {len(unique_companies)}")
    
    # Analyze executive distribution
    total_executives = sum(len(comp['executives']) for comp in unique_companies)
    companies_with_multiple_execs = sum(1 for comp in unique_companies if len(comp['executives']) > 1)
    
    print(f"👥 Total executives: {total_executives}")
    print(f"🏢 Companies with multiple executives: {companies_with_multiple_execs}")
    print(f"📊 Average executives per company: {total_executives/len(unique_companies):.1f}")
    
    # Contact information analysis
    executives_with_email = sum(1 for comp in unique_companies for exec in comp['executives'] if exec['email'] and str(exec['email']) != 'nan')
    executives_with_phone = sum(1 for comp in unique_companies for exec in comp['executives'] if exec['phone'] and str(exec['phone']) != 'nan')
    executives_with_linkedin = sum(1 for comp in unique_companies for exec in comp['executives'] if exec['linkedin'] and str(exec['linkedin']) != 'nan')
    
    print(f"\n📊 CONTACT INFORMATION COVERAGE:")
    print(f"📧 Executives with email: {executives_with_email}/{total_executives} ({executives_with_email/total_executives*100:.1f}%)")
    print(f"📞 Executives with phone: {executives_with_phone}/{total_executives} ({executives_with_phone/total_executives*100:.1f}%)")
    print(f"🔗 Executives with LinkedIn: {executives_with_linkedin}/{total_executives} ({executives_with_linkedin/total_executives*100:.1f}%)")
    
    # Generate URLs for testing
    test_urls = []
    for comp in unique_companies:
        if comp['website'] and str(comp['website']) != 'nan' and comp['website'] != 'Unknown':
            test_urls.append(comp['website'])
    
    print(f"\n🧪 TEST URLS EXTRACTED:")
    print(f"📊 Total URLs for testing: {len(test_urls)}")
    for i, url in enumerate(test_urls):
        print(f"  {i+1:2d}. {url}")
    
    # Save reference data for comparison
    reference_data = {
        'metadata': {
            'total_companies': len(unique_companies),
            'total_executives': total_executives,
            'companies_with_multiple_executives': companies_with_multiple_execs,
            'average_executives_per_company': total_executives/len(unique_companies),
            'contact_coverage': {
                'email_coverage': executives_with_email/total_executives,
                'phone_coverage': executives_with_phone/total_executives,
                'linkedin_coverage': executives_with_linkedin/total_executives
            }
        },
        'companies': unique_companies,
        'test_urls': test_urls
    }
    
    with open('reference_test_data.json', 'w') as f:
        json.dump(reference_data, f, indent=2, default=str)
    
    print(f"\n💾 Reference data saved to: reference_test_data.json")
    
    return reference_data

if __name__ == "__main__":
    reference_data = analyze_reference_data() 