#!/usr/bin/env python3
"""
Phase 5 Enhanced Extraction Test
Fixed version that properly extracts executives from real website content
"""

import asyncio
import json
import time
import sys
import os
import re
from datetime import datetime
from typing import List, Dict, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class Phase5EnhancedExtractor:
    """Enhanced Phase 5 extractor with improved real-world patterns"""
    
    def __init__(self):
        # Known website content from the search results
        self.website_data = {
            "http://www.msheatingandplumbing.co.uk/": {
                "content": """
                MS Heating & Plumbing
                Owner of the Business : Mr M Zubair
                Contact Us 0808 1929 786
                MS Heating & Plumbing
                80 HAZELWOOD ROAD BIRMINGHAM B27 7XP
                We have been established for over 11 years and pride ourselves in our on a like for like quote and high quality finish. 
                We strive for 100% customer satisfaction and won't stop until you are happy.
                """,
                "company_name": "MS Heating & Plumbing"
            },
            
            "http://www.absolute-plumbing-solutions.com/": {
                "content": """
                Absolute Plumbing & Heating Solutions
                0800 772 0326
                07807 221 991
                info@absoluteplumbing-heatingsolutions.co.uk
                Family Run Business
                Absolute Plumbing-Heating Solutions Ltd is a Midlands based Family Run company with many years of experience.
                We deal with all aspects of plumbing work in both the domestic and commercial sectors.
                Our highly motivated and dedicated team are friendly and responsive and have passion in the jobs they undertake.
                """,
                "company_name": "Absolute Plumbing & Heating Solutions"
            },
            
            "http://www.meregreengasandplumbing.co.uk/": {
                "content": """
                Mere Green Gas and Plumbing Sutton Coldfield
                Call us 24/7 on: 07885 687 352
                We are a family run business situated in Mere Green
                Worcester Bosch accredited partners
                Testimonials from customers including:
                Lorraine Swift (Sutton Coldfield) - customer testimonial
                Roger Sheldon (Mere Green) - customer testimonial  
                Kathleen Tatum (Sutton Coldfield) - customer testimonial
                Chris Stephens (Sutton Coldfield) - customer testimonial
                Anna Ward (Mere Green) - customer testimonial
                George Morris (Lichfield) - customer testimonial
                Mark Caldwell (Sutton Coldfield) - customer testimonial
                Mike Blue (Lichfield) - customer testimonial
                Linda Smith (Sutton Coldfield) - customer testimonial
                Mr. John Smith (Sutton Coldfield) - customer testimonial
                """,
                "company_name": "Mere Green Gas and Plumbing"
            },
            
            "https://www.starcitiesheatingandplumbing.co.uk/": {
                "content": """
                Star Cities Heating & Plumbing
                078 3323 1442 - fixit@starcitiesheatingandplumbing.co.uk
                135 Moor End Lane, Erdington, Birmingham, West Midlands
                We provide commercial plumbing services to businesses across Birmingham and the West Midlands areas.
                Our plumbers & engineers do a good job done each and every time, you can rely on us - that is our promise to you.
                """,
                "company_name": "Star Cities Heating & Plumbing"
            }
        }
        
        self.results = []
    
    async def run_enhanced_extraction_test(self):
        """Run enhanced extraction test on known website data"""
        print("🚀 PHASE 5 ENHANCED EXTRACTION TEST")
        print("=" * 60)
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Target: Extract accurate executive information from real website content")
        print(f"🔗 Testing {len(self.website_data)} companies with known content")
        print()
        
        start_time = time.time()
        
        # Process each company with known content
        for url, data in self.website_data.items():
            print(f"🏢 Processing: {data['company_name']}")
            print(f"🔗 URL: {url}")
            
            try:
                result = await self._process_company_enhanced(url, data)
                self.results.append(result)
                
                # Display detailed results
                self._display_enhanced_analysis(result)
                print()
                
            except Exception as e:
                print(f"❌ Error processing {url}: {e}")
                print()
        
        total_time = time.time() - start_time
        
        # Generate comprehensive analysis
        await self._generate_enhanced_analysis(total_time)
        
        # Save results
        await self._save_enhanced_results()
    
    async def _process_company_enhanced(self, url: str, data: Dict) -> Dict:
        """Process company with enhanced extraction methods"""
        company_start_time = time.time()
        
        company_name = data['company_name']
        content = data['content']
        
        print(f"   📄 Content length: {len(content)} characters")
        
        # Step 1: Enhanced executive extraction
        potential_executives = self._extract_executives_enhanced(content, company_name)
        print(f"   👤 Potential executives found: {len(potential_executives)}")
        
        # Step 2: Apply Phase 5 validation if available
        validated_executives = await self._apply_phase5_validation(potential_executives, content, company_name)
        print(f"   ✅ Validated executives: {len(validated_executives)}")
        
        # Step 3: Extract contact information
        contact_info = self._extract_contact_information(content)
        print(f"   📞 Contact info found: {len(contact_info)} items")
        
        # Step 4: Attribute contacts to executives
        enhanced_executives = self._attribute_contacts_to_executives(validated_executives, contact_info, content)
        
        processing_time = time.time() - company_start_time
        
        return {
            'url': url,
            'company_name': company_name,
            'success': True,
            'processing_time': processing_time,
            'content_length': len(content),
            'potential_executives': potential_executives,
            'validated_executives': validated_executives,
            'enhanced_executives': enhanced_executives,
            'contact_info': contact_info,
            'analysis': self._analyze_extraction_quality(enhanced_executives, contact_info)
        }
    
    def _extract_executives_enhanced(self, content: str, company_name: str) -> List[Dict]:
        """Enhanced executive extraction with better patterns"""
        executives = []
        
        # Pattern 1: Business Owner patterns
        owner_patterns = [
            r'Owner\s*(?:of\s*the\s*Business)?\s*:\s*(?:Mr\s+)?([A-Z]\s*[A-Za-z]+)',
            r'Business\s*Owner\s*:\s*(?:Mr\s+)?([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)',
            r'Proprietor\s*:\s*(?:Mr\s+)?([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)'
        ]
        
        for pattern in owner_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                name = self._clean_extracted_name(match)
                if name and self._is_likely_person_name(name):
                    executives.append({
                        'name': name,
                        'title': 'Business Owner',
                        'extraction_method': 'owner_pattern',
                        'confidence': 0.9
                    })
        
        # Pattern 2: Director/Manager patterns
        director_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*,?\s*(?:Managing\s+)?Director',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*,?\s*Manager',
            r'Director\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'Manager\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        ]
        
        for pattern in director_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                name = self._clean_extracted_name(match)
                if name and self._is_likely_person_name(name):
                    executives.append({
                        'name': name,
                        'title': 'Director/Manager',
                        'extraction_method': 'director_pattern',
                        'confidence': 0.8
                    })
        
        # Pattern 3: Contact person patterns
        contact_patterns = [
            r'Contact\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'Call\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'Speak\s+(?:to\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        ]
        
        for pattern in contact_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                name = self._clean_extracted_name(match)
                if name and self._is_likely_person_name(name):
                    executives.append({
                        'name': name,
                        'title': 'Contact Person',
                        'extraction_method': 'contact_pattern',
                        'confidence': 0.7
                    })
        
        # Pattern 4: Mr/Mrs patterns
        title_patterns = [
            r'\b(?:Mr|Mrs|Ms|Dr)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                name = self._clean_extracted_name(match)
                if name and self._is_likely_person_name(name):
                    executives.append({
                        'name': name,
                        'title': 'Executive',
                        'extraction_method': 'title_pattern',
                        'confidence': 0.8
                    })
        
        # Deduplicate executives
        unique_executives = []
        seen_names = set()
        
        for exec in executives:
            name_key = exec['name'].lower().strip()
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_executives.append(exec)
        
        return unique_executives
    
    def _clean_extracted_name(self, raw_name: str) -> str:
        """Clean extracted name"""
        if not raw_name:
            return ""
        
        # Handle names with single letters (like "M Zubair")
        cleaned = raw_name.strip()
        
        # Replace single letter followed by space with proper format
        cleaned = re.sub(r'^([A-Z])\s+([A-Z][a-z]+)$', r'\1. \2', cleaned)
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned
    
    def _is_likely_person_name(self, name: str) -> bool:
        """Check if extracted text is likely a person name"""
        if not name or len(name) < 2:
            return False
        
        # Common business terms that are NOT names
        business_terms = [
            'heating', 'plumbing', 'gas', 'boiler', 'services', 'solutions',
            'emergency', 'repair', 'installation', 'company', 'business',
            'contact', 'call', 'phone', 'email', 'address', 'location'
        ]
        
        name_lower = name.lower()
        for term in business_terms:
            if term in name_lower:
                return False
        
        # Check for reasonable name patterns
        # Must start with capital letter
        if not name[0].isupper():
            return False
        
        # Should not be all caps (likely business name)
        if name.isupper() and len(name) > 3:
            return False
        
        # Should not contain numbers
        if any(char.isdigit() for char in name):
            return False
        
        return True
    
    async def _apply_phase5_validation(self, executives: List[Dict], content: str, company_name: str) -> List[Dict]:
        """Apply Phase 5 validation if components are available"""
        try:
            # Try to import Phase 5 name validator
            sys.path.insert(0, os.path.join('src', 'seo_leads', 'ai'))
            from advanced_name_validator import AdvancedNameValidator
            
            validator = AdvancedNameValidator()
            validated = []
            
            for exec in executives:
                validation_result = validator.validate_name(exec['name'], content)
                if validation_result.is_valid_person:
                    exec['phase5_validation'] = {
                        'is_valid': True,
                        'confidence': validation_result.confidence_score,
                        'factors': validation_result.validation_factors
                    }
                    validated.append(exec)
                else:
                    exec['phase5_validation'] = {
                        'is_valid': False,
                        'confidence': validation_result.confidence_score,
                        'rejection_reasons': validation_result.rejection_reasons
                    }
            
            print(f"   🔍 Phase 5 validation: {len(validated)}/{len(executives)} names validated")
            return validated
            
        except ImportError:
            print(f"   ⚠️ Phase 5 components not available, using basic validation")
            # Basic validation fallback
            validated = []
            for exec in executives:
                if exec['confidence'] > 0.6:
                    exec['phase5_validation'] = {
                        'is_valid': True,
                        'confidence': exec['confidence'],
                        'method': 'basic_fallback'
                    }
                    validated.append(exec)
            return validated
    
    def _extract_contact_information(self, content: str) -> List[Dict]:
        """Extract contact information from content"""
        contact_info = []
        
        # Extract phone numbers
        phone_patterns = [
            r'(\+44\s?\d{2,4}\s?\d{3}\s?\d{3,4})',  # UK international
            r'(0\d{2,4}\s?\d{3}\s?\d{3,4})',       # UK national
            r'(07\d{3}\s?\d{6})',                   # UK mobile
            r'(\d{4}\s?\d{3}\s?\d{4})'              # General format
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                contact_info.append({
                    'type': 'phone',
                    'value': match,
                    'context': self._get_context_around_match(content, match)
                })
        
        # Extract email addresses
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        email_matches = re.findall(email_pattern, content)
        
        for email in email_matches:
            contact_info.append({
                'type': 'email',
                'value': email,
                'context': self._get_context_around_match(content, email)
            })
        
        return contact_info
    
    def _get_context_around_match(self, content: str, match: str) -> str:
        """Get context around a matched string"""
        try:
            pos = content.find(match)
            if pos != -1:
                start = max(0, pos - 50)
                end = min(len(content), pos + len(match) + 50)
                return content[start:end].strip()
        except:
            pass
        return ""
    
    def _attribute_contacts_to_executives(self, executives: List[Dict], contact_info: List[Dict], content: str) -> List[Dict]:
        """Attribute contact information to specific executives"""
        enhanced_executives = []
        
        for exec in executives:
            enhanced_exec = exec.copy()
            enhanced_exec['contact_details'] = {
                'phones': [],
                'emails': [],
                'attribution_method': 'none'
            }
            
            # Look for contacts near the executive's name
            name = exec['name']
            name_pos = content.lower().find(name.lower())
            
            if name_pos != -1:
                # Search within 200 characters of the name
                search_start = max(0, name_pos - 100)
                search_end = min(len(content), name_pos + len(name) + 100)
                search_area = content[search_start:search_end]
                
                # Find contacts in this area
                for contact in contact_info:
                    if contact['value'] in search_area:
                        if contact['type'] == 'phone':
                            enhanced_exec['contact_details']['phones'].append(contact['value'])
                        elif contact['type'] == 'email':
                            enhanced_exec['contact_details']['emails'].append(contact['value'])
                        enhanced_exec['contact_details']['attribution_method'] = 'proximity'
            
            # If no specific attribution, use general company contacts
            if not enhanced_exec['contact_details']['phones'] and not enhanced_exec['contact_details']['emails']:
                # Add general company contacts
                for contact in contact_info[:2]:  # Limit to first 2 contacts
                    if contact['type'] == 'phone':
                        enhanced_exec['contact_details']['phones'].append(contact['value'])
                    elif contact['type'] == 'email':
                        enhanced_exec['contact_details']['emails'].append(contact['value'])
                enhanced_exec['contact_details']['attribution_method'] = 'general_company'
            
            enhanced_executives.append(enhanced_exec)
        
        return enhanced_executives
    
    def _analyze_extraction_quality(self, executives: List[Dict], contact_info: List[Dict]) -> Dict:
        """Analyze quality of extraction"""
        if not executives:
            return {
                'quality_score': 0.0,
                'quality_grade': 'F - No executives found',
                'issues': ['No executives identified'],
                'recommendations': ['Improve name extraction patterns', 'Check content quality']
            }
        
        # Calculate quality metrics
        high_confidence_execs = sum(1 for exec in executives if exec.get('confidence', 0) > 0.8)
        execs_with_contacts = sum(1 for exec in executives 
                                if exec.get('contact_details', {}).get('phones') or 
                                   exec.get('contact_details', {}).get('emails'))
        
        validated_execs = sum(1 for exec in executives 
                            if exec.get('phase5_validation', {}).get('is_valid', False))
        
        quality_score = (
            (high_confidence_execs / len(executives)) * 0.3 +
            (execs_with_contacts / len(executives)) * 0.4 +
            (validated_execs / len(executives)) * 0.3
        )
        
        # Determine grade
        if quality_score >= 0.9:
            grade = 'A+ - Excellent'
        elif quality_score >= 0.8:
            grade = 'A - Very Good'
        elif quality_score >= 0.7:
            grade = 'B - Good'
        elif quality_score >= 0.6:
            grade = 'C - Fair'
        elif quality_score >= 0.4:
            grade = 'D - Poor'
        else:
            grade = 'F - Very Poor'
        
        # Identify issues and recommendations
        issues = []
        recommendations = []
        
        if high_confidence_execs / len(executives) < 0.7:
            issues.append('Low confidence in name extraction')
            recommendations.append('Improve name validation patterns')
        
        if execs_with_contacts / len(executives) < 0.5:
            issues.append('Limited contact information attribution')
            recommendations.append('Enhance contact attribution methods')
        
        if len(contact_info) == 0:
            issues.append('No contact information found')
            recommendations.append('Improve contact extraction patterns')
        
        return {
            'quality_score': quality_score,
            'quality_grade': grade,
            'executives_found': len(executives),
            'high_confidence_count': high_confidence_execs,
            'with_contacts_count': execs_with_contacts,
            'validated_count': validated_execs,
            'contact_items_found': len(contact_info),
            'issues': issues,
            'recommendations': recommendations
        }
    
    def _display_enhanced_analysis(self, result: Dict):
        """Display detailed analysis results"""
        analysis = result['analysis']
        
        print(f"   📊 Quality Score: {analysis['quality_score']:.2f}")
        print(f"   🏆 Quality Grade: {analysis['quality_grade']}")
        print(f"   ⏱️ Processing Time: {result['processing_time']:.2f}s")
        print()
        
        print(f"   👥 EXECUTIVES FOUND ({len(result['enhanced_executives'])}):")
        for i, exec in enumerate(result['enhanced_executives'], 1):
            validation = exec.get('phase5_validation', {})
            contact_details = exec.get('contact_details', {})
            
            validation_status = "✅" if validation.get('is_valid', False) else "❌"
            contact_status = "📞" if contact_details.get('phones') or contact_details.get('emails') else "❌"
            
            print(f"      {i}. {exec['name']} ({exec['title']})")
            print(f"         Validation: {validation_status} Confidence: {exec['confidence']:.2f}")
            print(f"         Contacts: {contact_status} Method: {exec['extraction_method']}")
            
            if contact_details.get('phones'):
                print(f"         📞 Phones: {', '.join(contact_details['phones'])}")
            if contact_details.get('emails'):
                print(f"         ✉️ Emails: {', '.join(contact_details['emails'])}")
        
        if result['enhanced_executives']:
            print()
            print(f"   📞 CONTACT INFO FOUND ({len(result['contact_info'])}):")
            for contact in result['contact_info']:
                print(f"      • {contact['type'].title()}: {contact['value']}")
        
        if analysis['issues']:
            print()
            print(f"   ⚠️ ISSUES IDENTIFIED:")
            for issue in analysis['issues']:
                print(f"      • {issue}")
        
        if analysis['recommendations']:
            print()
            print(f"   💡 RECOMMENDATIONS:")
            for rec in analysis['recommendations']:
                print(f"      • {rec}")
    
    async def _generate_enhanced_analysis(self, total_time: float):
        """Generate comprehensive analysis"""
        print("📊 PHASE 5 ENHANCED EXTRACTION ANALYSIS")
        print("=" * 60)
        
        successful_results = [r for r in self.results if r.get('success', False)]
        
        # Overall metrics
        total_executives = sum(len(r['enhanced_executives']) for r in successful_results)
        total_contacts = sum(len(r['contact_info']) for r in successful_results)
        
        avg_quality = sum(r['analysis']['quality_score'] for r in successful_results) / len(successful_results) if successful_results else 0
        
        print(f"🎯 OVERALL PERFORMANCE:")
        print(f"   • Companies Processed: {len(successful_results)}")
        print(f"   • Total Executives Found: {total_executives}")
        print(f"   • Total Contact Items: {total_contacts}")
        print(f"   • Average Quality Score: {avg_quality:.2f}")
        print(f"   • Total Processing Time: {total_time:.2f}s")
        print()
        
        # Quality distribution
        quality_grades = {}
        for result in successful_results:
            grade = result['analysis']['quality_grade'].split(' - ')[0]
            quality_grades[grade] = quality_grades.get(grade, 0) + 1
        
        print(f"🏆 QUALITY DISTRIBUTION:")
        for grade in ['A+', 'A', 'B', 'C', 'D', 'F']:
            if grade in quality_grades:
                print(f"   • {grade}: {quality_grades[grade]} companies")
        print()
        
        # Best performing company
        if successful_results:
            best_company = max(successful_results, key=lambda x: x['analysis']['quality_score'])
            print(f"🌟 BEST PERFORMING COMPANY:")
            print(f"   • {best_company['company_name']}")
            print(f"   • Quality Score: {best_company['analysis']['quality_score']:.2f}")
            print(f"   • Executives Found: {len(best_company['enhanced_executives'])}")
            print(f"   • Contact Items: {len(best_company['contact_info'])}")
        
        print()
        print("🎉 PHASE 5 ENHANCED EXTRACTION COMPLETE!")
    
    async def _save_enhanced_results(self):
        """Save enhanced results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"phase5_enhanced_extraction_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'test_metadata': {
                    'test_date': datetime.now().isoformat(),
                    'test_name': 'Phase 5 Enhanced Extraction Test',
                    'companies_tested': len(self.website_data)
                },
                'results': self.results
            }, f, indent=2, default=str)
        
        print(f"📄 Results saved to: {filename}")

async def main():
    """Run the enhanced extraction test"""
    extractor = Phase5EnhancedExtractor()
    await extractor.run_enhanced_extraction_test()

if __name__ == "__main__":
    asyncio.run(main()) 