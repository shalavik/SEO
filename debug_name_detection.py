"""
Debug Name Detection - Analyze why semantic extraction isn't finding names
"""

import re
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def analyze_website_content():
    """Analyze the provided website content to see what names should be detected"""
    
    # Content from the websites provided
    websites_content = {
        "MJM Plumbing Services": """
        24 Hour Emergency Call Out Available 07949 371 269
        MJM PLUMBING SERVICES
        """,
        
        "R&N Plumbing": """
        R & N Plumbing And Heating
        9 Pensford Road, Northfield Birmingham. B31 3AD
        info@rnplumbingandheating.co.uk
        07595 260746
        """,
        
        "Andrew Riley Heating": """
        Andrew Riley heating plumbing & gas
        Contact us: 0121 439 7129
        email: admin@andrewrileyheating.co.uk
        Andrew Riley heating, plumbing & gas is a family business
        """,
        
        "J M Plumbing & Heating": """
        J M Plumbing & Heating
        58 Dalbury Road, Birmingham, B28 0NF
        07817 927067
        jnmcmanus@hotmail.co.uk
        James was kind, helpful and very professional
        James and Rob have just replaced our old boiler
        Jim is extremely polite and helpful
        """,
        
        "Nunn Plumbing": """
        Nunn Plumbing and Gas
        154 Birdbrook Road, BIRMINGHAM, B44 8RX
        07946 497365
        nunnpandg@gmail.com
        """
    }
    
    print("🔍 DEBUGGING NAME DETECTION")
    print("=" * 50)
    
    # Basic regex pattern (what the old system used)
    old_pattern = re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b')
    
    # Load our semantic extractor
    try:
        from seo_leads.ai.semantic_name_extractor import SemanticNameExtractor
        extractor = SemanticNameExtractor()
        print("✅ Semantic extractor loaded")
    except Exception as e:
        print(f"❌ Failed to load extractor: {e}")
        return
    
    for company, content in websites_content.items():
        print(f"\n🏢 Analyzing: {company}")
        print("-" * 30)
        
        # What old regex would find
        old_matches = old_pattern.findall(content)
        print(f"📊 Old regex would find: {old_matches}")
        
        # What our semantic extractor finds
        semantic_names = extractor.extract_semantic_names(content)
        print(f"🧠 Semantic extractor found: {len(semantic_names)} names")
        
        for name in semantic_names:
            print(f"  • {name.text} (confidence: {name.confidence:.2f})")
            print(f"    Reasons: {name.validation_reasons}")
        
        # Manual analysis - what SHOULD be found
        expected_names = []
        if "Andrew Riley" in content:
            expected_names.append("Andrew Riley")
        if "James" in content and any(surname in content for surname in ["McManus", "james"]):
            expected_names.append("James McManus")
        
        print(f"🎯 Expected names: {expected_names}")
        
        # Check if names are in our UK databases
        print("🔍 Database analysis:")
        for expected in expected_names:
            parts = expected.split()
            if len(parts) == 2:
                first, last = parts
                first_in_db = first.lower() in extractor.uk_first_names
                last_in_db = last.lower() in extractor.uk_surnames
                print(f"  {expected}: first_name={first_in_db}, surname={last_in_db}")

def test_confidence_thresholds():
    """Test different confidence thresholds to see if we're being too strict"""
    
    print("\n🎛️ TESTING CONFIDENCE THRESHOLDS")
    print("=" * 50)
    
    test_content = """
    Andrew Riley heating plumbing & gas is a family business, serving our local surrounding areas.
    Contact us: tel: 0121 439 7129 & 077 2926 2276
    email: admin@andrewrileyheating.co.uk
    James McManus from J M Plumbing & Heating
    """
    
    try:
        from seo_leads.ai.semantic_name_extractor import SemanticNameExtractor
        extractor = SemanticNameExtractor()
    except Exception as e:
        print(f"❌ Failed to load extractor: {e}")
        return
    
    # Test with different confidence thresholds
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    
    for threshold in thresholds:
        print(f"\n🎯 Testing threshold: {threshold}")
        
        # Temporarily modify the threshold by getting all candidates and filtering
        candidates = extractor._extract_name_candidates(test_content)
        
        found_names = []
        for candidate in candidates:
            validation = extractor._validate_human_name(candidate, test_content)
            if validation['is_human'] and validation['confidence'] > threshold:
                found_names.append({
                    'name': candidate['text'],
                    'confidence': validation['confidence'],
                    'reasons': validation['reasons']
                })
        
        print(f"   Found {len(found_names)} names:")
        for name_data in found_names:
            print(f"     • {name_data['name']} ({name_data['confidence']:.2f})")

def check_name_database_coverage():
    """Check if our UK name databases have good coverage"""
    
    print("\n📚 CHECKING NAME DATABASE COVERAGE")
    print("=" * 50)
    
    try:
        from seo_leads.ai.semantic_name_extractor import SemanticNameExtractor
        extractor = SemanticNameExtractor()
    except Exception as e:
        print(f"❌ Failed to load extractor: {e}")
        return
    
    # Test names that should be in UK databases
    test_names = [
        ("Andrew", "first_name"),
        ("James", "first_name"), 
        ("Riley", "surname"),
        ("McManus", "surname"),
        ("Nunn", "surname"),
        ("Robert", "first_name"),
        ("Michael", "first_name")
    ]
    
    print("Testing name database coverage:")
    for name, name_type in test_names:
        if name_type == "first_name":
            in_db = name.lower() in extractor.uk_first_names
            print(f"  {name} (first): {'✅' if in_db else '❌'} in database")
        else:
            in_db = name.lower() in extractor.uk_surnames
            print(f"  {name} (surname): {'✅' if in_db else '❌'} in database")
    
    print(f"\nDatabase stats:")
    print(f"  First names: {len(extractor.uk_first_names)}")
    print(f"  Surnames: {len(extractor.uk_surnames)}")

if __name__ == "__main__":
    analyze_website_content()
    test_confidence_thresholds()
    check_name_database_coverage() 