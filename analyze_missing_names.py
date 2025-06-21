"""
Analyze Missing Names - Understand why certain names aren't being detected
"""

import re
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def analyze_missing_names():
    """Analyze content from websites to understand what names we should find"""
    
    # Known content from the websites that should contain names
    website_analyses = {
        "J M Plumbing & Heating": {
            "url": "http://jmplumbingheating.co.uk/",
            "content_snippets": [
                "James was kind, helpful and very professional",
                "James and Rob have just replaced our old boiler", 
                "Jim is extremely polite and helpful",
                "jnmcmanus@hotmail.co.uk"  # J N McManus email
            ],
            "expected_names": ["James McManus", "Rob"],
            "analysis": "Reviews mention James/Jim multiple times, email suggests J.N. McManus"
        },
        
        "MJM Plumbing Services": {
            "url": "http://www.mjmplumbingservices.uk/",
            "content_snippets": [
                "MJM PLUMBING SERVICES",
                "07949 371 269"
            ],
            "expected_names": [],
            "analysis": "MJM likely initials, no clear personal names visible"
        },
        
        "Nunn Plumbing": {
            "url": "https://www.nunnplumbingandgas.co.uk/contact",
            "content_snippets": [
                "Nunn Plumbing and Gas",
                "nunnpandg@gmail.com"
            ],
            "expected_names": ["Mr Nunn", "Mrs Nunn"],
            "analysis": "Company name suggests family business, but no first names visible"
        },
        
        "R&N Plumbing": {
            "url": "http://rnplumbingandheating.co.uk/",
            "content_snippets": [
                "R & N Plumbing and Heating", 
                "info@rnplumbingandheating.co.uk"
            ],
            "expected_names": [],
            "analysis": "R&N likely initials, found Michael Torbert correctly"
        }
    }
    
    print("🔍 MISSING NAMES ANALYSIS")
    print("=" * 60)
    
    # Load our semantic extractor
    try:
        from seo_leads.ai.semantic_name_extractor import SemanticNameExtractor
        extractor = SemanticNameExtractor()
        print("✅ Semantic extractor loaded")
    except Exception as e:
        print(f"❌ Failed to load extractor: {e}")
        return
    
    for company, data in website_analyses.items():
        print(f"\n🏢 {company}")
        print("-" * 40)
        print(f"📍 URL: {data['url']}")
        print(f"🎯 Expected: {data['expected_names']}")
        print(f"📝 Analysis: {data['analysis']}")
        
        # Test content snippets individually
        for i, snippet in enumerate(data['content_snippets'], 1):
            print(f"\n   📄 Snippet {i}: \"{snippet}\"")
            
            # Old regex approach
            old_pattern = re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b')
            old_matches = old_pattern.findall(snippet)
            print(f"   📊 Old regex: {old_matches}")
            
            # Our semantic extraction
            semantic_names = extractor.extract_semantic_names(snippet)
            print(f"   🧠 Semantic: {[name.text for name in semantic_names]}")
            
            # Check why names might be missed
            if 'James' in snippet or 'Jim' in snippet:
                print(f"   🔍 James/Jim analysis:")
                
                # Check if James is in database
                james_in_db = 'james' in extractor.uk_first_names
                print(f"     - James in UK first names: {james_in_db}")
                
                # Check for surname clues
                if 'McManus' in snippet or 'jnmcmanus' in snippet:
                    mcmanus_in_db = 'mcmanus' in extractor.uk_surnames
                    print(f"     - McManus in UK surnames: {mcmanus_in_db}")
                    
                # Test manual name construction
                if 'James' in snippet:
                    test_names = ['James McManus', 'James Roberts', 'James Smith']
                    for test_name in test_names:
                        validation = extractor._validate_human_name(
                            {'text': test_name, 'position': 0}, 
                            snippet
                        )
                        print(f"     - Test '{test_name}': {validation['is_human']} (conf: {validation['confidence']:.2f})")

def test_name_completion_strategies():
    """Test strategies for completing partial names"""
    
    print("\n🔧 NAME COMPLETION STRATEGIES")
    print("=" * 60)
    
    test_cases = [
        {
            'context': "James was kind, helpful and very professional. Thank you James.",
            'partial_name': 'James',
            'email_clue': 'jnmcmanus@hotmail.co.uk',
            'expected': 'James McManus'
        },
        {
            'context': "James and Rob have just replaced our old boiler",
            'partial_name': 'Rob',
            'email_clue': None,
            'expected': 'Rob [Unknown]'
        }
    ]
    
    try:
        from seo_leads.ai.semantic_name_extractor import SemanticNameExtractor
        extractor = SemanticNameExtractor()
    except Exception as e:
        print(f"❌ Failed to load extractor: {e}")
        return
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {case['partial_name']}")
        print(f"   Context: \"{case['context']}\"")
        print(f"   Email clue: {case['email_clue']}")
        print(f"   Expected: {case['expected']}")
        
        # Strategy 1: Extract from email
        if case['email_clue']:
            email_parts = case['email_clue'].split('@')[0]
            print(f"   📧 Email analysis: {email_parts}")
            
            # Try to extract surname from email
            if 'mcmanus' in email_parts.lower():
                full_name = f"{case['partial_name']} McManus"
                validation = extractor._validate_human_name(
                    {'text': full_name, 'position': 0},
                    case['context']
                )
                print(f"   ✅ Email-derived name: {full_name} (valid: {validation['is_human']}, conf: {validation['confidence']:.2f})")
        
        # Strategy 2: Common surname completion
        common_surnames = ['Smith', 'Jones', 'Brown', 'Wilson', 'Taylor']
        for surname in common_surnames:
            full_name = f"{case['partial_name']} {surname}"
            validation = extractor._validate_human_name(
                {'text': full_name, 'position': 0},
                case['context']
            )
            if validation['is_human']:
                print(f"   🔄 Common surname test: {full_name} (conf: {validation['confidence']:.2f})")
                break

def recommend_improvements():
    """Recommend specific improvements for better name detection"""
    
    print("\n💡 IMPROVEMENT RECOMMENDATIONS")
    print("=" * 60)
    
    recommendations = [
        {
            'issue': 'Single names not detected (James, Rob)',
            'solution': 'Add single-name detection with email/context-based surname completion',
            'priority': 'High'
        },
        {
            'issue': 'Email-based name hints ignored',
            'solution': 'Extract surnames from email addresses (jnmcmanus -> J.N. McManus)',
            'priority': 'High'
        },
        {
            'issue': 'Review text names not linked to business',
            'solution': 'Parse customer reviews to identify business owners/staff',
            'priority': 'Medium'
        },
        {
            'issue': 'Company name surnames not detected',
            'solution': 'Extract likely surnames from company names (Nunn Plumbing -> Mr/Ms Nunn)',
            'priority': 'Medium'
        }
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. 🎯 {rec['issue']}")
        print(f"   💡 Solution: {rec['solution']}")
        print(f"   📊 Priority: {rec['priority']}")
        print()

if __name__ == "__main__":
    analyze_missing_names()
    test_name_completion_strategies()
    recommend_improvements() 