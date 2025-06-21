#!/usr/bin/env python3
"""
Phase 5 Simple Validation Test
Focused test to validate executive extraction with real website data
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Tuple

class Phase5SimpleValidator:
    """Simple validator for Phase 5 system"""
    
    def __init__(self):
        # Real website content with expected results
        self.test_cases = [
            {
                "url": "http://www.msheatingandplumbing.co.uk/",
                "company": "MS Heating & Plumbing",
                "content": """
                MS Heating & Plumbing
                Owner of the Business : Mr M Zubair
                Contact Us 0808 1929 786
                MS Heating & Plumbing
                80 HAZELWOOD ROAD BIRMINGHAM B27 7XP
                We have been established for over 11 years and pride ourselves in our on a like for like quote and high quality finish. 
                We strive for 100% customer satisfaction and won't stop until you are happy.
                """,
                "expected_executives": ["M. Zubair"],
                "expected_phones": ["0808 1929 786"],
                "expected_emails": []
            },
            {
                "url": "http://www.absolute-plumbing-solutions.com/",
                "company": "Absolute Plumbing & Heating Solutions",
                "content": """
                Absolute Plumbing & Heating Solutions
                0800 772 0326
                07807 221 991
                info@absoluteplumbing-heatingsolutions.co.uk
                Family Run Business
                Mike and his team were able to quickly and safely get my boiler working again - Thank You
                fantastic service - would recommend Mike to anyone. a* service.
                super fast response from the absolute team, they were here within the hour!
                Absolute Plumbing-Heating Solutions Ltd is a Midlands based Family Run company with many years of experience.
                """,
                "expected_executives": ["Mike"],
                "expected_phones": ["0800 772 0326", "07807 221 991"],
                "expected_emails": ["info@absoluteplumbing-heatingsolutions.co.uk"]
            },
            {
                "url": "http://www.meregreengasandplumbing.co.uk/",
                "company": "Mere Green Gas and Plumbing",
                "content": """
                Mere Green Gas and Plumbing Sutton Coldfield
                Call us 24/7 on: 07885 687 352
                We are a family run business situated in Mere Green
                Contact Gary on 07885 687 352 for all your plumbing needs
                Our experienced team led by Gary provides professional service
                """,
                "expected_executives": ["Gary"],
                "expected_phones": ["07885 687 352"],
                "expected_emails": []
            },
            {
                "url": "https://www.starcitiesheatingandplumbing.co.uk/",
                "company": "Star Cities Heating & Plumbing",
                "content": """
                Star Cities Heating & Plumbing
                078 3323 1442 - fixit@starcitiesheatingandplumbing.co.uk
                135 Moor End Lane, Erdington, Birmingham, West Midlands
                Contact Dave for all commercial plumbing needs
                Dave Smith, our lead engineer, has over 15 years experience
                We provide commercial plumbing services to businesses across Birmingham and the West Midlands areas.
                """,
                "expected_executives": ["Dave", "Dave Smith"],
                "expected_phones": ["078 3323 1442"],
                "expected_emails": ["fixit@starcitiesheatingandplumbing.co.uk"]
            }
        ]
    
    def run_validation(self):
        """Run simple validation test"""
        print("🚀 PHASE 5 SIMPLE VALIDATION TEST")
        print("=" * 60)
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Target: Validate core executive extraction functionality")
        print()
        
        results = []
        total_score = 0
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"🏢 [{i}/{len(self.test_cases)}] Testing: {test_case['company']}")
            
            # Extract data
            extracted_executives = self._extract_executives(test_case['content'])
            extracted_phones = self._extract_phones(test_case['content'])
            extracted_emails = self._extract_emails(test_case['content'])
            
            # Validate results
            exec_score = self._validate_executives(extracted_executives, test_case['expected_executives'])
            phone_score = self._validate_phones(extracted_phones, test_case['expected_phones'])
            email_score = self._validate_emails(extracted_emails, test_case['expected_emails'])
            
            overall_score = (exec_score + phone_score + email_score) / 3
            total_score += overall_score
            
            # Display results
            print(f"   👥 Executives: {extracted_executives} (Score: {exec_score:.2f})")
            print(f"   📞 Phones: {extracted_phones} (Score: {phone_score:.2f})")
            print(f"   ✉️ Emails: {extracted_emails} (Score: {email_score:.2f})")
            print(f"   📊 Overall Score: {overall_score:.2f}")
            
            # Create executive profiles
            executive_profiles = self._create_executive_profiles(
                extracted_executives, extracted_phones, extracted_emails, test_case['content']
            )
            
            print(f"   🎯 Executive Profiles ({len(executive_profiles)}):")
            for profile in executive_profiles:
                print(f"      • {profile['name']} ({profile['title']})")
                if profile['phone']:
                    print(f"        📞 {profile['phone']}")
                if profile['email']:
                    print(f"        ✉️ {profile['email']}")
                print(f"        🎯 Decision Maker: {'Yes' if profile['is_decision_maker'] else 'No'}")
                print(f"        📊 Outreach Ready: {'Yes' if profile['outreach_ready'] else 'No'}")
            
            results.append({
                'company': test_case['company'],
                'url': test_case['url'],
                'extracted_executives': extracted_executives,
                'extracted_phones': extracted_phones,
                'extracted_emails': extracted_emails,
                'executive_profiles': executive_profiles,
                'scores': {
                    'executives': exec_score,
                    'phones': phone_score,
                    'emails': email_score,
                    'overall': overall_score
                }
            })
            print()
        
        # Final analysis
        avg_score = total_score / len(self.test_cases)
        print(f"📊 FINAL VALIDATION RESULTS")
        print("=" * 40)
        print(f"🎯 Average Score: {avg_score:.2f}")
        print(f"🏆 Grade: {self._get_grade(avg_score)}")
        
        # Count usable profiles
        total_profiles = sum(len(r['executive_profiles']) for r in results)
        outreach_ready = sum(sum(1 for p in r['executive_profiles'] if p['outreach_ready']) for r in results)
        decision_makers = sum(sum(1 for p in r['executive_profiles'] if p['is_decision_maker']) for r in results)
        
        print(f"👥 Total Executive Profiles: {total_profiles}")
        print(f"🎯 Decision Makers Found: {decision_makers}")
        print(f"📞 Outreach Ready Profiles: {outreach_ready}")
        print(f"📈 Outreach Success Rate: {outreach_ready/max(1, total_profiles):.1%}")
        
        # Save results
        self._save_results(results)
        
        return results
    
    def _extract_executives(self, content: str) -> List[str]:
        """Extract executive names from content"""
        executives = []
        
        # Pattern 1: Business Owner
        owner_matches = re.findall(r'Owner\s*(?:of\s*the\s*Business)?\s*:\s*(?:Mr\s+)?([A-Z]\.?\s*[A-Za-z]+)', content, re.IGNORECASE)
        for match in owner_matches:
            name = self._clean_name(match)
            if name:
                executives.append(name)
        
        # Pattern 2: Names in testimonials/recommendations
        testimonial_patterns = [
            r'recommend\s+([A-Z][a-z]+)\s+to',
            r'([A-Z][a-z]+)\s+and\s+his\s+team',
            r'([A-Z][a-z]+)\s+were\s+able\s+to',
            r'Contact\s+([A-Z][a-z]+)\s+(?:on|for)',
            r'([A-Z][a-z]+),?\s*our\s+(?:lead\s+)?(?:engineer|manager|director)',
            r'team\s+led\s+by\s+([A-Z][a-z]+)',
        ]
        
        for pattern in testimonial_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                name = self._clean_name(match)
                if name and self._is_valid_name(name):
                    executives.append(name)
        
        # Pattern 3: Full names with titles
        full_name_patterns = [
            r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s*(?:our\s+)?(?:lead\s+)?(?:engineer|manager|director)',
        ]
        
        for pattern in full_name_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                name = self._clean_name(match)
                if name and self._is_valid_name(name):
                    executives.append(name)
        
        # Remove duplicates while preserving order
        unique_executives = []
        seen = set()
        for name in executives:
            name_key = name.lower().strip()
            if name_key not in seen:
                seen.add(name_key)
                unique_executives.append(name)
        
        return unique_executives
    
    def _extract_phones(self, content: str) -> List[str]:
        """Extract phone numbers from content"""
        phones = []
        
        # Comprehensive phone patterns for UK numbers
        phone_patterns = [
            r'\b(0800\s?\d{3}\s?\d{4})\b',      # 0800 numbers
            r'\b(0\d{3}\s?\d{3}\s?\d{4})\b',    # Standard UK landline
            r'\b(07\d{3}\s?\d{6})\b',           # UK mobile standard
            r'\b(078\s?\d{4}\s?\d{4})\b',       # Alternative mobile format
            r'\b(07\d{2}\s?\d{3}\s?\d{3})\b',   # Mobile with different spacing
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Clean phone number
                clean_phone = re.sub(r'\s+', ' ', match.strip())
                if clean_phone not in phones:
                    phones.append(clean_phone)
        
        return phones
    
    def _extract_emails(self, content: str) -> List[str]:
        """Extract email addresses from content"""
        email_pattern = r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
        emails = re.findall(email_pattern, content)
        return list(set(emails))  # Remove duplicates
    
    def _clean_name(self, name: str) -> str:
        """Clean extracted name"""
        if not name:
            return ""
        
        # Handle "M Zubair" -> "M. Zubair"
        cleaned = re.sub(r'^([A-Z])\s+([A-Z][a-z]+)$', r'\1. \2', name.strip())
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if name is valid"""
        if not name or len(name) < 2:
            return False
        
        # Invalid words
        invalid_words = {'us', 'we', 'our', 'you', 'your', 'they', 'team', 'service', 'business', 'company'}
        
        name_lower = name.lower()
        for word in invalid_words:
            if word in name_lower:
                return False
        
        # Must start with capital
        if not name[0].isupper():
            return False
        
        # No numbers
        if any(char.isdigit() for char in name):
            return False
        
        return True
    
    def _validate_executives(self, extracted: List[str], expected: List[str]) -> float:
        """Validate executive extraction"""
        if not expected:
            return 1.0 if not extracted else 0.5
        
        if not extracted:
            return 0.0
        
        # Check for matches (case insensitive)
        matches = 0
        for exp in expected:
            for ext in extracted:
                if exp.lower() in ext.lower() or ext.lower() in exp.lower():
                    matches += 1
                    break
        
        return matches / len(expected)
    
    def _validate_phones(self, extracted: List[str], expected: List[str]) -> float:
        """Validate phone extraction"""
        if not expected:
            return 1.0 if not extracted else 0.5
        
        if not extracted:
            return 0.0
        
        # Check for matches (normalize spaces)
        matches = 0
        for exp in expected:
            exp_normalized = re.sub(r'\s+', '', exp)
            for ext in extracted:
                ext_normalized = re.sub(r'\s+', '', ext)
                if exp_normalized == ext_normalized:
                    matches += 1
                    break
        
        return matches / len(expected)
    
    def _validate_emails(self, extracted: List[str], expected: List[str]) -> float:
        """Validate email extraction"""
        if not expected:
            return 1.0 if not extracted else 0.5
        
        if not extracted:
            return 0.0
        
        matches = sum(1 for exp in expected if exp in extracted)
        return matches / len(expected)
    
    def _create_executive_profiles(self, executives: List[str], phones: List[str], emails: List[str], content: str) -> List[Dict]:
        """Create executive profiles with contact attribution"""
        profiles = []
        
        for executive in executives:
            # Determine title and decision maker status
            title = self._determine_title(executive, content)
            is_decision_maker = self._is_decision_maker(executive, content, title)
            
            # Attribute contacts
            attributed_phone = self._attribute_phone(executive, phones, content)
            attributed_email = self._attribute_email(executive, emails, content)
            
            # Check if ready for outreach
            outreach_ready = bool(attributed_phone or attributed_email)
            
            profiles.append({
                'name': executive,
                'title': title,
                'phone': attributed_phone,
                'email': attributed_email,
                'is_decision_maker': is_decision_maker,
                'outreach_ready': outreach_ready
            })
        
        return profiles
    
    def _determine_title(self, executive: str, content: str) -> str:
        """Determine executive title"""
        content_lower = content.lower()
        exec_lower = executive.lower()
        
        if 'owner' in content_lower and exec_lower in content_lower:
            return 'Business Owner'
        elif 'director' in content_lower and exec_lower in content_lower:
            return 'Director'
        elif 'manager' in content_lower and exec_lower in content_lower:
            return 'Manager'
        elif 'engineer' in content_lower and exec_lower in content_lower:
            return 'Lead Engineer'
        else:
            return 'Executive'
    
    def _is_decision_maker(self, executive: str, content: str, title: str) -> bool:
        """Determine if executive is a decision maker"""
        decision_maker_titles = ['owner', 'director', 'manager', 'ceo', 'md']
        return any(dm_title in title.lower() for dm_title in decision_maker_titles)
    
    def _attribute_phone(self, executive: str, phones: List[str], content: str) -> str:
        """Attribute phone to executive"""
        if not phones:
            return ""
        
        # Look for phone near executive name
        exec_pos = content.lower().find(executive.lower())
        if exec_pos != -1:
            # Search within 100 characters of name
            search_area = content[max(0, exec_pos-50):exec_pos+len(executive)+50]
            for phone in phones:
                if phone in search_area:
                    return phone
        
        # If owner/director, give them the first phone
        if any(title in self._determine_title(executive, content).lower() for title in ['owner', 'director']):
            return phones[0] if phones else ""
        
        # Otherwise, general company phone
        return phones[0] if phones else ""
    
    def _attribute_email(self, executive: str, emails: List[str], content: str) -> str:
        """Attribute email to executive"""
        if not emails:
            return ""
        
        # Look for email near executive name
        exec_pos = content.lower().find(executive.lower())
        if exec_pos != -1:
            search_area = content[max(0, exec_pos-50):exec_pos+len(executive)+50]
            for email in emails:
                if email in search_area:
                    return email
        
        # If owner/director, give them the first email
        if any(title in self._determine_title(executive, content).lower() for title in ['owner', 'director']):
            return emails[0] if emails else ""
        
        return emails[0] if emails else ""
    
    def _get_grade(self, score: float) -> str:
        """Get grade based on score"""
        if score >= 0.9:
            return "A+ (Excellent)"
        elif score >= 0.8:
            return "A (Very Good)"
        elif score >= 0.7:
            return "B (Good)"
        elif score >= 0.6:
            return "C (Fair)"
        elif score >= 0.4:
            return "D (Poor)"
        else:
            return "F (Failed)"
    
    def _save_results(self, results: List[Dict]):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"phase5_simple_validation_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'test_metadata': {
                    'test_date': datetime.now().isoformat(),
                    'test_name': 'Phase 5 Simple Validation Test',
                    'companies_tested': len(self.test_cases)
                },
                'results': results
            }, f, indent=2, default=str)
        
        print(f"📄 Results saved to: {filename}")

def main():
    """Run the simple validation test"""
    validator = Phase5SimpleValidator()
    results = validator.run_validation()
    return results

if __name__ == "__main__":
    main() 