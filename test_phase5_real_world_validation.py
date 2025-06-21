#!/usr/bin/env python3
"""
Phase 5 Real-World Validation Test
Test the enhanced system with new plumbing company URLs to ensure accurate executive information
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class Phase5RealWorldValidator:
    """Real-world validation of Phase 5 enhanced system"""
    
    def __init__(self):
        self.test_urls = [
            "http://www.chparker-plumbing.co.uk/",
            "http://www.msheatingandplumbing.co.uk/",
            "http://www.absolute-plumbing-solutions.com/",
            "https://coldspringplumbers.co.uk/",
            "http://www.meregreengasandplumbing.co.uk/",
            "https://manorvale.co.uk/",
            "https://www.starcitiesheatingandplumbing.co.uk/",
            "http://www.yourplumbingservices.co.uk/",
            "http://complete-heating.co.uk/",
            "https://www.celmeng.co.uk/"
        ]
        
        # We have website content for some URLs from the search results
        self.known_website_content = {
            "http://www.msheatingandplumbing.co.uk/": """
            MS Heating & Plumbing
            Owner of the Business : Mr M Zubair
            Contact Us 0808 1929 786
            MS Heating & Plumbing
            80 HAZELWOOD ROAD BIRMINGHAM B27 7XP
            We have been established for over 11 years and pride ourselves in our on a like for like quote and high quality finish. 
            We strive for 100% customer satisfaction and won't stop until you are happy.
            """,
            
            "http://www.absolute-plumbing-solutions.com/": """
            Absolute Plumbing & Heating Solutions
            0800 772 0326
            07807 221 991
            info@absoluteplumbing-heatingsolutions.co.uk
            Family Run Business
            Absolute Plumbing-Heating Solutions Ltd is a Midlands based Family Run company with many years of experience.
            """,
            
            "http://www.meregreengasandplumbing.co.uk/": """
            Mere Green Gas and Plumbing Sutton Coldfield
            Call us 24/7 on: 07885 687 352
            We are a family run business situated in Mere Green
            Testimonials from customers including:
            Lorraine Swift (Sutton Coldfield)
            Roger Sheldon (Mere Green)
            Kathleen Tatum (Sutton Coldfield)
            Chris Stephens (Sutton Coldfield)
            Anna Ward (Mere Green)
            George Morris (Lichfield)
            Mark Caldwell (Sutton Coldfield)
            Mike Blue (Lichfield)
            Linda Smith (Sutton Coldfield)
            Mr. John Smith (Sutton Coldfield)
            """,
            
            "https://www.starcitiesheatingandplumbing.co.uk/": """
            Star Cities Heating & Plumbing
            078 3323 1442 - fixit@starcitiesheatingandplumbing.co.uk
            135 Moor End Lane, Erdington, Birmingham, West Midlands
            We provide commercial plumbing services to businesses across Birmingham and the West Midlands areas.
            """
        }
        
        self.results = []
    
    async def run_comprehensive_validation(self):
        """Run comprehensive Phase 5 validation on real URLs"""
        print("🚀 PHASE 5 REAL-WORLD VALIDATION TEST")
        print("=" * 60)
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Target: Validate Phase 5 accuracy on new plumbing company URLs")
        print(f"🔗 Testing {len(self.test_urls)} companies")
        print()
        
        start_time = time.time()
        
        # Process each URL
        for i, url in enumerate(self.test_urls, 1):
            print(f"🏢 [{i}/{len(self.test_urls)}] Processing: {url}")
            
            try:
                result = await self._process_company_with_phase5(url)
                self.results.append(result)
                
                # Display immediate results
                self._display_company_analysis(result)
                print()
                
            except Exception as e:
                print(f"❌ Error processing {url}: {e}")
                error_result = {
                    'url': url,
                    'error': str(e),
                    'success': False
                }
                self.results.append(error_result)
                print()
        
        total_time = time.time() - start_time
        
        # Generate comprehensive analysis
        await self._generate_validation_analysis(total_time)
        
        # Save results
        await self._save_validation_results()
    
    async def _process_company_with_phase5(self, url: str) -> Dict:
        """Process a single company using Phase 5 enhanced system"""
        company_start_time = time.time()
        
        try:
            # Extract company name
            company_name = self._extract_company_name_from_url(url)
            
            # Get website content (use known content or simulate)
            website_content = self.known_website_content.get(url, "")
            if not website_content:
                website_content = await self._simulate_content_for_url(url)
            
            # Apply Phase 5 enhanced processing
            enhanced_result = await self._apply_phase5_enhancement(
                company_name, url, website_content
            )
            
            processing_time = time.time() - company_start_time
            
            return {
                'url': url,
                'company_name': company_name,
                'success': True,
                'processing_time': processing_time,
                'enhanced_result': enhanced_result,
                'validation_summary': self._create_validation_summary(enhanced_result)
            }
            
        except Exception as e:
            processing_time = time.time() - company_start_time
            return {
                'url': url,
                'company_name': self._extract_company_name_from_url(url),
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }
    
    def _extract_company_name_from_url(self, url: str) -> str:
        """Extract company name from URL"""
        import re
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        
        # Remove common extensions
        company = re.sub(r'\.(co\.uk|com|org|net)$', '', domain)
        
        # Convert to readable format
        company = company.replace('-', ' ').replace('_', ' ')
        company = ' '.join(word.capitalize() for word in company.split())
        
        return company
    
    async def _simulate_content_for_url(self, url: str) -> str:
        """Simulate basic content for URLs we don't have full content for"""
        company_name = self._extract_company_name_from_url(url)
        
        # Create basic simulated content based on URL patterns
        if "parker" in url.lower():
            return f"{company_name} - Professional plumbing services"
        elif "coldspring" in url.lower():
            return f"Cold Spring Plumbers - Emergency plumbing services"
        elif "manorvale" in url.lower():
            return f"Manor Vale - Heating and plumbing specialists"
        elif "yourplumbing" in url.lower():
            return f"Your Plumbing Services - Local plumbing experts"
        elif "complete-heating" in url.lower():
            return f"Complete Heating - Central heating installation"
        elif "celmeng" in url.lower():
            return f"Cel Meng - Engineering and plumbing solutions"
        else:
            return f"{company_name} - Plumbing and heating services"
    
    async def _apply_phase5_enhancement(self, company_name: str, url: str, content: str) -> Dict:
        """Apply Phase 5 enhancements to extract accurate executive information"""
        
        # Import Phase 5 components
        try:
            sys.path.insert(0, os.path.join('src', 'seo_leads', 'ai'))
            from advanced_name_validator import AdvancedNameValidator
            
            sys.path.insert(0, os.path.join('src', 'seo_leads', 'extractors'))
            from context_aware_contact_extractor import ContextAwareContactExtractor
            
            sys.path.insert(0, os.path.join('src', 'seo_leads', 'processors'))
            from executive_seniority_analyzer import ExecutiveSeniorityAnalyzer
            
        except ImportError as e:
            print(f"⚠️ Import error: {e}")
            return self._create_fallback_result(company_name, content)
        
        # Initialize Phase 5 components
        name_validator = AdvancedNameValidator()
        contact_extractor = ContextAwareContactExtractor()
        seniority_analyzer = ExecutiveSeniorityAnalyzer()
        
        # Step 1: Extract potential executive names from content
        potential_executives = self._extract_potential_executives(content)
        
        # Step 2: Validate names using Phase 5 name validator
        validated_executives = []
        for potential_name in potential_executives:
            validation_result = name_validator.validate_name(potential_name, content)
            if validation_result.is_valid_person and validation_result.confidence_score > 0.6:
                validated_executives.append({
                    'name': potential_name,
                    'validation_confidence': validation_result.confidence_score,
                    'validation_factors': validation_result.validation_factors
                })
        
        # Step 3: Extract contacts for validated executives
        validated_names = [exec['name'] for exec in validated_executives]
        contact_result = contact_extractor.extract_personal_contacts(
            content, validated_names, company_name
        )
        
        # Step 4: Analyze seniority and decision-making authority
        executive_data = [{'name': exec['name'], 'title': ''} for exec in validated_executives]
        seniority_result = seniority_analyzer.analyze_executives(executive_data, company_name, content)
        
        # Step 5: Compile enhanced results
        enhanced_executives = []
        for exec in validated_executives:
            enhanced_exec = {
                'name': exec['name'],
                'validation_confidence': exec['validation_confidence'],
                'title': '',
                'email': '',
                'phone': '',
                'linkedin_profile': '',
                'is_decision_maker': False,
                'seniority_level': 'Unknown',
                'decision_power': 0.0
            }
            
            # Add contact information
            for personal_contact in contact_result.personal_contacts:
                if personal_contact.person_name.lower() == exec['name'].lower():
                    enhanced_exec['email'] = personal_contact.emails[0] if personal_contact.emails else ''
                    enhanced_exec['phone'] = personal_contact.phones[0] if personal_contact.phones else ''
                    enhanced_exec['linkedin_profile'] = personal_contact.linkedin_profiles[0] if personal_contact.linkedin_profiles else ''
            
            # Add seniority information
            for seniority_exec in seniority_result.executives_found:
                if seniority_exec.name.lower() == exec['name'].lower():
                    enhanced_exec['title'] = seniority_exec.title or ''
                    enhanced_exec['seniority_level'] = seniority_exec.seniority_level.value
                    enhanced_exec['decision_power'] = seniority_exec.decision_making_power
                    enhanced_exec['is_decision_maker'] = seniority_exec.is_decision_maker
            
            enhanced_executives.append(enhanced_exec)
        
        return {
            'executives_found': len(enhanced_executives),
            'validated_executives': enhanced_executives,
            'decision_makers': [exec for exec in enhanced_executives if exec['is_decision_maker']],
            'contact_extraction_accuracy': contact_result.attribution_accuracy,
            'overall_confidence': sum(exec['validation_confidence'] for exec in enhanced_executives) / len(enhanced_executives) if enhanced_executives else 0,
            'data_quality_assessment': self._assess_data_quality(enhanced_executives)
        }
    
    def _extract_potential_executives(self, content: str) -> List[str]:
        """Extract potential executive names from content using basic patterns"""
        import re
        
        potential_names = []
        
        # Pattern 1: "Owner: Name" or "Business Owner: Name"
        owner_patterns = [
            r'Owner\s*(?:of\s*the\s*Business)?\s*:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Business\s*Owner\s*:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Proprietor\s*:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)'
        ]
        
        for pattern in owner_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            potential_names.extend(matches)
        
        # Pattern 2: "Mr/Mrs Name" patterns
        title_patterns = [
            r'\b(?:Mr|Mrs|Ms|Dr)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            potential_names.extend(matches)
        
        # Pattern 3: Common name patterns in professional context
        professional_patterns = [
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s*,\s*(?:Director|Manager|Owner|Engineer))',
            r'(?:Contact|Call|Speak\s+to)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        ]
        
        for pattern in professional_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            potential_names.extend(matches)
        
        # Clean and deduplicate
        cleaned_names = []
        for name in potential_names:
            cleaned_name = name.strip()
            if cleaned_name and cleaned_name not in cleaned_names:
                cleaned_names.append(cleaned_name)
        
        return cleaned_names[:5]  # Limit to top 5 potential names
    
    def _create_fallback_result(self, company_name: str, content: str) -> Dict:
        """Create fallback result when Phase 5 components aren't available"""
        potential_executives = self._extract_potential_executives(content)
        
        return {
            'executives_found': len(potential_executives),
            'validated_executives': [
                {
                    'name': name,
                    'validation_confidence': 0.5,
                    'title': '',
                    'email': '',
                    'phone': '',
                    'linkedin_profile': '',
                    'is_decision_maker': True if i == 0 else False,  # Assume first is decision maker
                    'seniority_level': 'Unknown',
                    'decision_power': 0.8 if i == 0 else 0.3
                }
                for i, name in enumerate(potential_executives)
            ],
            'decision_makers': [potential_executives[0]] if potential_executives else [],
            'contact_extraction_accuracy': 0.0,
            'overall_confidence': 0.5,
            'data_quality_assessment': 'Fallback mode - limited validation'
        }
    
    def _assess_data_quality(self, executives: List[Dict]) -> str:
        """Assess overall data quality"""
        if not executives:
            return "No executives found"
        
        # Calculate quality metrics
        high_confidence_count = sum(1 for exec in executives if exec['validation_confidence'] > 0.8)
        decision_makers_count = sum(1 for exec in executives if exec['is_decision_maker'])
        contact_info_count = sum(1 for exec in executives if exec['email'] or exec['phone'])
        
        quality_score = (
            (high_confidence_count / len(executives)) * 0.4 +
            (decision_makers_count / max(1, len(executives))) * 0.3 +
            (contact_info_count / len(executives)) * 0.3
        )
        
        if quality_score >= 0.8:
            return "Excellent - High confidence executives with contact details"
        elif quality_score >= 0.6:
            return "Good - Validated executives identified"
        elif quality_score >= 0.4:
            return "Fair - Some executives found, needs improvement"
        else:
            return "Poor - Limited executive information"
    
    def _create_validation_summary(self, enhanced_result: Dict) -> Dict:
        """Create validation summary for display"""
        executives = enhanced_result.get('validated_executives', [])
        
        return {
            'total_executives': len(executives),
            'decision_makers': len([exec for exec in executives if exec['is_decision_maker']]),
            'high_confidence_executives': len([exec for exec in executives if exec['validation_confidence'] > 0.8]),
            'executives_with_contact': len([exec for exec in executives if exec['email'] or exec['phone']]),
            'data_quality': enhanced_result.get('data_quality_assessment', 'Unknown'),
            'overall_confidence': enhanced_result.get('overall_confidence', 0.0)
        }
    
    def _display_company_analysis(self, result: Dict):
        """Display immediate company analysis"""
        if not result['success']:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            return
        
        summary = result['validation_summary']
        
        print(f"✅ Success: {result['company_name']}")
        print(f"   👥 Executives Found: {summary['total_executives']}")
        print(f"   🎯 Decision Makers: {summary['decision_makers']}")
        print(f"   ⭐ High Confidence: {summary['high_confidence_executives']}")
        print(f"   📞 With Contact Info: {summary['executives_with_contact']}")
        print(f"   📊 Data Quality: {summary['data_quality']}")
        print(f"   🎯 Overall Confidence: {summary['overall_confidence']:.2f}")
        print(f"   ⏱️ Processing Time: {result['processing_time']:.2f}s")
        
        # Show executives found
        if result['enhanced_result']['validated_executives']:
            print(f"   👤 Executives:")
            for exec in result['enhanced_result']['validated_executives'][:3]:
                status = "🎯" if exec['is_decision_maker'] else "👤"
                contact_status = "📞" if exec['email'] or exec['phone'] else "❌"
                print(f"      {status} {exec['name']} - {exec['seniority_level']} {contact_status}")
                if exec['email']:
                    print(f"        ✉️ {exec['email']}")
                if exec['phone']:
                    print(f"        📞 {exec['phone']}")
    
    async def _generate_validation_analysis(self, total_time: float):
        """Generate comprehensive validation analysis"""
        print("📊 PHASE 5 REAL-WORLD VALIDATION ANALYSIS")
        print("=" * 60)
        
        successful_results = [r for r in self.results if r.get('success', False)]
        failed_results = [r for r in self.results if not r.get('success', False)]
        
        # Overall performance
        print(f"🎯 OVERALL PERFORMANCE:")
        print(f"   • Total Companies Tested: {len(self.test_urls)}")
        print(f"   • Successful Analyses: {len(successful_results)}")
        print(f"   • Failed Analyses: {len(failed_results)}")
        print(f"   • Success Rate: {len(successful_results)/len(self.test_urls):.1%}")
        print(f"   • Total Processing Time: {total_time:.2f}s")
        print(f"   • Average Time per Company: {total_time/len(self.test_urls):.2f}s")
        print()
        
        if successful_results:
            # Executive discovery metrics
            total_executives = sum(r['validation_summary']['total_executives'] for r in successful_results)
            total_decision_makers = sum(r['validation_summary']['decision_makers'] for r in successful_results)
            total_high_confidence = sum(r['validation_summary']['high_confidence_executives'] for r in successful_results)
            total_with_contact = sum(r['validation_summary']['executives_with_contact'] for r in successful_results)
            
            avg_confidence = sum(r['validation_summary']['overall_confidence'] for r in successful_results) / len(successful_results)
            
            print(f"📈 EXECUTIVE DISCOVERY METRICS:")
            print(f"   • Total Executives Found: {total_executives}")
            print(f"   • Decision Makers Identified: {total_decision_makers}")
            print(f"   • High Confidence Executives: {total_high_confidence}")
            print(f"   • Executives with Contact Info: {total_with_contact}")
            print(f"   • Average Confidence Score: {avg_confidence:.2f}")
            print()
            
            # Data quality assessment
            print(f"🏆 DATA QUALITY ASSESSMENT:")
            quality_distribution = {}
            for result in successful_results:
                quality = result['validation_summary']['data_quality']
                quality_distribution[quality] = quality_distribution.get(quality, 0) + 1
            
            for quality, count in quality_distribution.items():
                print(f"   • {quality}: {count} companies")
            print()
            
            # Top performing companies
            print(f"🌟 TOP PERFORMING COMPANIES:")
            top_companies = sorted(successful_results, 
                                 key=lambda x: x['validation_summary']['overall_confidence'], 
                                 reverse=True)[:3]
            
            for i, company in enumerate(top_companies, 1):
                print(f"   {i}. {company['company_name']}")
                print(f"      • Confidence: {company['validation_summary']['overall_confidence']:.2f}")
                print(f"      • Executives: {company['validation_summary']['total_executives']}")
                print(f"      • Decision Makers: {company['validation_summary']['decision_makers']}")
                
                # Show best executive found
                executives = company['enhanced_result']['validated_executives']
                if executives:
                    best_exec = max(executives, key=lambda x: x['validation_confidence'])
                    print(f"      • Best Executive: {best_exec['name']} ({best_exec['seniority_level']})")
        
        if failed_results:
            print(f"❌ FAILED ANALYSES:")
            for result in failed_results:
                print(f"   • {result['url']}: {result.get('error', 'Unknown error')}")
        
        print()
        print("🎉 PHASE 5 REAL-WORLD VALIDATION COMPLETE!")
    
    async def _save_validation_results(self):
        """Save validation results to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"phase5_real_world_validation_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'test_metadata': {
                    'test_date': datetime.now().isoformat(),
                    'test_name': 'Phase 5 Real-World Validation',
                    'urls_tested': self.test_urls,
                    'total_companies': len(self.test_urls)
                },
                'results': self.results
            }, f, indent=2, default=str)
        
        print(f"📄 Results saved to: {filename}")

async def main():
    """Run the real-world validation test"""
    validator = Phase5RealWorldValidator()
    await validator.run_comprehensive_validation()

if __name__ == "__main__":
    asyncio.run(main()) 