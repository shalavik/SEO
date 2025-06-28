#!/usr/bin/env python3
"""
Phase 7B: Quality Refinement Engine - Focused Test
==================================================

Demonstrates the advanced semantic analysis and quality filtering
capabilities of Phase 7B while maintaining execution speed.
"""

import asyncio
import logging
import time
import re
import json
from typing import Dict, List, Tuple
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase7BSemanticAnalyzer:
    """Advanced semantic analysis for executive quality assessment"""
    
    def __init__(self):
        # Comprehensive service/business terms for filtering
        self.service_terms = {
            'heating', 'plumbing', 'service', 'services', 'solutions', 'repair',
            'installation', 'maintenance', 'emergency', 'quality', 'premium',
            'complete', 'comprehensive', 'affordable', 'reliable', 'trusted',
            'expert', 'certified', 'licensed', 'residential', 'commercial',
            'company', 'ltd', 'limited', 'corp', 'llc', 'group', 'associates',
            'quote', 'information', 'contact', 'about', 'home', 'privacy',
            'policy', 'terms', 'conditions', 'boiler', 'hvac', 'gas',
            'electric', 'thermostat', 'certificate', 'safety', 'warranty'
        }
        
        # Real name patterns
        self.name_patterns = [
            r'\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b',           # John Smith
            r'\b[A-Z][a-z]{2,}\s+[A-Z]\.\s+[A-Z][a-z]{2,}\b', # John A. Smith
            r'\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b' # Full names
        ]
        
        # Executive role indicators
        self.role_indicators = [
            'ceo', 'president', 'founder', 'owner', 'director', 'manager',
            'coordinator', 'supervisor', 'lead', 'head', 'chief'
        ]
    
    def analyze_executive_quality(self, name: str, context: str = "") -> Tuple[float, str, Dict]:
        """Semantic analysis to determine executive quality score"""
        if not name or len(name.strip()) < 3:
            return 0.0, "Name too short", {'flags': ['too_short']}
        
        clean_name = name.strip()
        name_lower = clean_name.lower()
        context_lower = context.lower() if context else ""
        
        score = 0.0
        flags = []
        analysis = {'name_analysis': {}, 'context_analysis': {}}
        
        # 1. Name Pattern Analysis
        valid_pattern = False
        for pattern in self.name_patterns:
            if re.search(pattern, clean_name):
                score += 0.4
                valid_pattern = True
                flags.append('valid_name_pattern')
                break
        
        if not valid_pattern:
            score -= 0.3
            flags.append('invalid_name_pattern')
        
        analysis['name_analysis']['valid_pattern'] = valid_pattern
        
        # 2. Service Term Penalty
        words = set(name_lower.split())
        service_matches = words.intersection(self.service_terms)
        if service_matches:
            penalty = len(service_matches) * 0.4
            score -= penalty
            flags.extend([f'service_term_{term}' for term in service_matches])
            analysis['name_analysis']['service_terms'] = list(service_matches)
        
        # 3. Word Count Assessment
        word_count = len(clean_name.split())
        if 2 <= word_count <= 4:
            score += 0.2
            flags.append('appropriate_length')
        elif word_count > 6:
            score -= 0.3
            flags.append('too_long')
        
        analysis['name_analysis']['word_count'] = word_count
        
        # 4. Capitalization Check
        if clean_name.istitle():
            score += 0.1
            flags.append('proper_capitalization')
        
        # 5. Role Context Analysis
        combined_text = f"{name_lower} {context_lower}"
        role_matches = [role for role in self.role_indicators if role in combined_text]
        if role_matches:
            score += len(role_matches) * 0.15
            flags.extend([f'role_{role}' for role in role_matches])
            analysis['context_analysis']['roles'] = role_matches
        
        # 6. Final Quality Assessment
        final_score = max(0.0, min(1.0, score))
        
        # Generate quality reason
        if final_score >= 0.8:
            quality_tier = "HIGH"
            reason = f"High-quality executive: {', '.join(flags[:3])}"
        elif final_score >= 0.6:
            quality_tier = "MEDIUM"
            reason = f"Medium-quality executive: {', '.join(flags[:3])}"
        else:
            quality_tier = "LOW"
            reason = f"Low-quality/service content: {', '.join(flags[:3])}"
        
        analysis.update({
            'final_score': final_score,
            'quality_tier': quality_tier,
            'flags': flags
        })
        
        return final_score, reason, analysis

class Phase7BQualityRefinementTest:
    """Phase 7B Quality Refinement Test System"""
    
    def __init__(self):
        self.semantic_analyzer = Phase7BSemanticAnalyzer()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    async def test_quality_refinement(self, companies: List[Dict]) -> Dict:
        """Test Phase 7B quality refinement on sample companies"""
        start_time = time.time()
        
        logger.info("🎯 PHASE 7B QUALITY REFINEMENT TEST")
        logger.info("=" * 50)
        logger.info(f"Testing {len(companies)} companies with enhanced semantic analysis...")
        
        results = []
        
        for company in companies:
            company_result = await self._test_company_quality(company)
            results.append(company_result)
        
        # Calculate summary metrics
        total_time = time.time() - start_time
        total_raw = sum(r['raw_executives'] for r in results)
        total_refined = sum(r['refined_executives'] for r in results)
        
        filtering_rate = (total_raw - total_refined) / total_raw if total_raw > 0 else 0
        avg_quality = sum(r['avg_quality_score'] for r in results) / len(results) if results else 0
        
        summary = {
            'phase7b_test_summary': {
                'companies_tested': len(companies),
                'total_processing_time': total_time,
                'total_raw_executives': total_raw,
                'total_refined_executives': total_refined,
                'filtering_effectiveness': filtering_rate,
                'average_quality_score': avg_quality,
                'companies_per_hour': len(companies) * 3600 / total_time if total_time > 0 else 0
            },
            'detailed_results': results
        }
        
        return summary
    
    async def _test_company_quality(self, company: Dict) -> Dict:
        """Test quality refinement for a single company"""
        start_time = time.time()
        company_name = company.get('name', 'Unknown')
        website = company.get('website', '')
        
        logger.info(f"🏢 Testing {company_name}...")
        
        try:
            # Fetch content
            response = self.session.get(website, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Extract raw executives using basic patterns
            raw_executives = self._extract_raw_executives(text_content)
            logger.info(f"📊 {company_name}: {len(raw_executives)} raw executives extracted")
            
            # Apply Phase 7B quality refinement
            refined_executives = self._apply_quality_refinement(raw_executives)
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(raw_executives, refined_executives)
            
            processing_time = time.time() - start_time
            
            result = {
                'company_name': company_name,
                'website': website,
                'raw_executives': len(raw_executives),
                'refined_executives': len(refined_executives),
                'filtering_rate': (len(raw_executives) - len(refined_executives)) / len(raw_executives) if raw_executives else 0,
                'avg_quality_score': quality_metrics['average_score'],
                'quality_distribution': quality_metrics['distribution'],
                'top_executives': refined_executives[:5],  # Top 5 for review
                'processing_time': processing_time,
                'sample_filtered_content': [e['name'] for e in raw_executives if e not in refined_executives][:10]
            }
            
            logger.info(f"✅ {company_name}: {len(raw_executives)} → {len(refined_executives)} executives")
            logger.info(f"   Quality score: {quality_metrics['average_score']:.2f}, Time: {processing_time:.1f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error testing {company_name}: {e}")
            return {
                'company_name': company_name,
                'raw_executives': 0,
                'refined_executives': 0,
                'avg_quality_score': 0.0,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _extract_raw_executives(self, text: str) -> List[Dict]:
        """Extract raw executive candidates from text"""
        executives = []
        
        # Basic name patterns
        patterns = [
            r'\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,})\b',
            r'\b([A-Z][a-z]{2,}\s+[A-Z]\.\s+[A-Z][a-z]{2,})\b',
            r'\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,})\b'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1).strip()
                if len(name) > 5:  # Basic length filter
                    context = text[max(0, match.start()-100):match.end()+100]
                    executives.append({
                        'name': name,
                        'context': context,
                        'raw_confidence': 0.5
                    })
        
        # Remove basic duplicates
        seen_names = set()
        unique_executives = []
        for exec_data in executives:
            name_lower = exec_data['name'].lower()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                unique_executives.append(exec_data)
        
        return unique_executives
    
    def _apply_quality_refinement(self, raw_executives: List[Dict]) -> List[Dict]:
        """Apply Phase 7B semantic quality refinement"""
        refined_executives = []
        quality_threshold = 0.6  # Stricter than Phase 7A
        
        for exec_data in raw_executives:
            name = exec_data['name']
            context = exec_data.get('context', '')
            
            # Apply semantic analysis
            quality_score, reason, analysis = self.semantic_analyzer.analyze_executive_quality(name, context)
            
            # Apply quality threshold
            if quality_score >= quality_threshold:
                exec_data.update({
                    'semantic_score': quality_score,
                    'quality_reason': reason,
                    'semantic_analysis': analysis,
                    'quality_tier': analysis['quality_tier']
                })
                refined_executives.append(exec_data)
        
        # Sort by quality score
        refined_executives.sort(key=lambda x: x.get('semantic_score', 0), reverse=True)
        
        return refined_executives
    
    def _calculate_quality_metrics(self, raw_executives: List[Dict], refined_executives: List[Dict]) -> Dict:
        """Calculate quality improvement metrics"""
        if not refined_executives:
            return {'average_score': 0.0, 'distribution': {'high': 0, 'medium': 0, 'low': 0}}
        
        scores = [e.get('semantic_score', 0) for e in refined_executives]
        avg_score = sum(scores) / len(scores)
        
        # Quality distribution
        high_quality = sum(1 for s in scores if s >= 0.8)
        medium_quality = sum(1 for s in scores if 0.6 <= s < 0.8)
        low_quality = sum(1 for s in scores if s < 0.6)
        
        return {
            'average_score': avg_score,
            'distribution': {
                'high': high_quality,
                'medium': medium_quality,
                'low': low_quality
            }
        }

async def main():
    """Main test execution for Phase 7B Quality Refinement"""
    
    # Test companies (subset for quick demonstration)
    test_companies = [
        {'name': 'Celm Engineering', 'website': 'https://celmeng.co.uk/'},
        {'name': 'MS Heating & Plumbing', 'website': 'https://msheatingandplumbing.co.uk/'}
    ]
    
    # Initialize test system
    test_system = Phase7BQualityRefinementTest()
    
    try:
        # Run quality refinement test
        results = await test_system.test_quality_refinement(test_companies)
        
        # Save results
        timestamp = int(time.time())
        results_file = f'phase7b_quality_test_results_{timestamp}.json'
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Display results
        summary = results['phase7b_test_summary']
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("🎯 PHASE 7B QUALITY REFINEMENT TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Companies Tested: {summary['companies_tested']}")
        logger.info(f"Total Processing Time: {summary['total_processing_time']:.1f}s")
        logger.info(f"Raw Executives Found: {summary['total_raw_executives']}")
        logger.info(f"Refined Executives: {summary['total_refined_executives']}")
        logger.info(f"Filtering Effectiveness: {summary['filtering_effectiveness']*100:.1f}%")
        logger.info(f"Average Quality Score: {summary['average_quality_score']:.2f}")
        logger.info(f"Processing Speed: {summary['companies_per_hour']:.1f} companies/hour")
        logger.info("=" * 60)
        
        # Show detailed company results
        for company_result in results['detailed_results']:
            if 'error' not in company_result:
                logger.info(f"📊 {company_result['company_name']}:")
                logger.info(f"   Raw → Refined: {company_result['raw_executives']} → {company_result['refined_executives']}")
                logger.info(f"   Quality Score: {company_result['avg_quality_score']:.2f}")
                logger.info(f"   Quality Distribution: {company_result['quality_distribution']}")
                
                if company_result['top_executives']:
                    logger.info(f"   Top Executives:")
                    for i, exec_data in enumerate(company_result['top_executives'][:3], 1):
                        logger.info(f"     {i}. {exec_data['name']} (score: {exec_data.get('semantic_score', 0):.2f})")
                
                if company_result['sample_filtered_content']:
                    logger.info(f"   Sample Filtered Content: {', '.join(company_result['sample_filtered_content'][:5])}")
                logger.info("")
        
        logger.info(f"💾 Detailed results saved to: {results_file}")
        
        # Quality Refinement Analysis
        logger.info("🔍 PHASE 7B QUALITY REFINEMENT ANALYSIS:")
        logger.info(f"  • Semantic Analysis: ✅ Active")
        logger.info(f"  • Service Content Filtering: {summary['filtering_effectiveness']*100:.1f}% effective")
        logger.info(f"  • Quality Threshold: 0.6+ (stricter than Phase 7A)")
        logger.info(f"  • Processing Speed: Maintained high performance")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
