"""
Test Enhanced Name Detection - Specifically test single name + email completion
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_enhanced_detection():
    """Test the enhanced name detection with real-world examples"""
    
    print("🔧 ENHANCED NAME DETECTION TEST")
    print("=" * 50)
    
    # Load our enhanced semantic extractor
    try:
        from seo_leads.ai.semantic_name_extractor import SemanticNameExtractor
        extractor = SemanticNameExtractor()
        print("✅ Enhanced semantic extractor loaded")
    except Exception as e:
        print(f"❌ Failed to load extractor: {e}")
        return
    
    # Test cases that should now work with enhanced detection
    test_cases = [
        {
            'name': 'James + Email Completion',
            'content': '''
            James was kind, helpful and very professional. Thank you James.
            Contact us at jnmcmanus@hotmail.co.uk for all your plumbing needs.
            ''',
            'expected': ['James McManus'],
            'description': 'Single name James + email jnmcmanus should combine to James McManus'
        },
        
        {
            'name': 'James Review Context', 
            'content': '''
            James arrived on time and was very professional. 
            James and Rob have just replaced our old boiler.
            Contact: jnmcmanus@hotmail.co.uk
            ''',
            'expected': ['James McManus'],
            'description': 'James in review context with email completion'
        },
        
        {
            'name': 'Jim Alternative Name',
            'content': '''
            Jim is extremely polite and helpful. Nothing was too much trouble.
            Email us at jnmcmanus@hotmail.co.uk
            ''',
            'expected': ['Jim McManus'],  # Should work if Jim is treated as James
            'description': 'Jim as nickname for James with email completion'
        },
        
        {
            'name': 'Andrew Riley (Existing)',
            'content': '''
            Andrew Riley heating plumbing & gas is a family business.
            Contact us: admin@andrewrileyheating.co.uk
            ''',
            'expected': ['Andrew Riley'],
            'description': 'Existing full name detection should still work'
        },
        
        {
            'name': 'Multiple Names',
            'content': '''
            Andrew Riley heating is run by Andrew Riley.
            Our reviews say James was very professional.
            Contact: jnmcmanus@hotmail.co.uk or admin@andrewrileyheating.co.uk
            ''',
            'expected': ['Andrew Riley', 'James McManus'],
            'description': 'Multiple names with different detection methods'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"   📝 {test_case['description']}")
        print(f"   🎯 Expected: {test_case['expected']}")
        
        # Run enhanced extraction
        validated_names = extractor.extract_semantic_names(test_case['content'])
        
        found_names = [name.text for name in validated_names]
        print(f"   🧠 Found: {found_names}")
        
        # Check results
        for expected_name in test_case['expected']:
            if expected_name in found_names:
                print(f"   ✅ SUCCESS: Found '{expected_name}'")
                # Get confidence and reasons
                for name in validated_names:
                    if name.text == expected_name:
                        print(f"      Confidence: {name.confidence:.2f}")
                        print(f"      Reasons: {name.validation_reasons[:2]}")
            else:
                print(f"   ❌ MISSING: Expected '{expected_name}' not found")
        
        # Check for unexpected names
        for found_name in found_names:
            if found_name not in test_case['expected']:
                print(f"   ⚠️  UNEXPECTED: Found '{found_name}' (not expected)")
    
    print(f"\n🎯 ENHANCED DETECTION SUMMARY")
    print("=" * 50)
    
    # Test email surname extraction specifically
    print("\n📧 EMAIL SURNAME EXTRACTION TEST")
    test_emails = [
        "jnmcmanus@hotmail.co.uk",
        "admin@andrewrileyheating.co.uk", 
        "info@smithplumbing.com",
        "contact@example.com"
    ]
    
    for email in test_emails:
        surnames = extractor._extract_surnames_from_emails(f"Contact us at {email}")
        print(f"   {email} → {surnames}")

if __name__ == "__main__":
    test_enhanced_detection() 