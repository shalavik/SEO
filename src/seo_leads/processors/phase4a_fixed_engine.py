"""
Phase 4A Enhanced Multi-Source Executive Discovery Engine - Fixed Version
Advanced ML-powered executive discovery with proper model integration
Target: 70%+ success rate improvement
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import aiohttp
from bs4 import BeautifulSoup
import requests

from ..extractors.advanced_content_extractor import AdvancedContentExtractor
from ..ai.enhanced_executive_classifier import EnhancedExecutiveClassifier
from ..models import ExecutiveContact

logger = logging.getLogger(__name__)

@dataclass
class Phase4AResult:
    """Phase 4A discovery result"""
    company_name: str
    website_url: str
    executives: List[ExecutiveContact]
    processing_time: float
    success: bool
    ml_candidates_found: int
    final_executives_count: int
    extraction_methods: List[str]
    confidence_distribution: Dict[str, int]
    error_message: str = ""

class Phase4AFixedEngine:
    """Phase 4A Enhanced Executive Discovery Engine - Fixed Version"""
    
    def __init__(self):
        self.advanced_extractor = AdvancedContentExtractor()
        self.ml_classifier = EnhancedExecutiveClassifier()
        self.min_confidence = 0.4
    
    async def discover_executives(self, company_data: Dict[str, Any]) -> Phase4AResult:
        """Main discovery method"""
        company_name = company_data.get('name', 'Unknown Company')
        website_url = company_data.get('website', '')
        
        logger.info(f"🚀 Phase 4A Fixed Discovery: {company_name}")
        start_time = time.time()
        
        try:
            # Step 1: Fetch website content
            content = await self._fetch_content(website_url)
            if not content:
                return self._failed_result(company_name, website_url, start_time, "Failed to fetch content")
            
            # Step 2: Advanced extraction
            extracted_executives = self.advanced_extractor.extract_executives_advanced(
                content, website_url, company_name
            )
            
            # Step 3: ML classification
            text_content = BeautifulSoup(content, 'html.parser').get_text(separator=' ', strip=True)
            ml_candidates = self.ml_classifier.classify_executives(text_content, company_name)
            
            # Step 4: Convert to ExecutiveContact objects
            final_executives = self._convert_to_executives(ml_candidates, company_name, website_url)
            
            # Step 5: Quality filtering
            filtered_executives = self._filter_quality(final_executives, company_name)
            
            processing_time = time.time() - start_time
            
            result = Phase4AResult(
                company_name=company_name,
                website_url=website_url,
                executives=filtered_executives,
                processing_time=processing_time,
                success=len(filtered_executives) > 0,
                ml_candidates_found=len(ml_candidates),
                final_executives_count=len(filtered_executives),
                extraction_methods=list(set([exec.extraction_method for exec in extracted_executives])),
                confidence_distribution=self._calc_confidence_dist(filtered_executives)
            )
            
            logger.info(f"✅ Phase 4A Fixed: {len(filtered_executives)} executives found in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Phase 4A Fixed failed for {company_name}: {e}")
            return self._failed_result(company_name, website_url, start_time, str(e))
    
    async def _fetch_content(self, website_url: str) -> Optional[str]:
        """Fetch website content"""
        if not website_url:
            return None
        
        if not website_url.startswith(('http://', 'https://')):
            website_url = f'https://{website_url}'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            # Try async first
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(website_url, headers=headers) as response:
                    if response.status == 200:
                        return await response.text()
        except:
            pass
        
        try:
            # Fallback to sync
            response = requests.get(website_url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.text
        except:
            pass
        
        return None
    
    def _convert_to_executives(self, candidates, company_name: str, website_url: str) -> List[ExecutiveContact]:
        """Convert ML candidates to ExecutiveContact objects"""
        executives = []
        domain = website_url.replace('https://', '').replace('http://', '').split('/')[0]
        
        for candidate in candidates:
            try:
                executive = ExecutiveContact(
                    first_name=candidate.first_name,
                    last_name=candidate.last_name,
                    full_name=candidate.full_name,
                    title=candidate.title or "Executive",
                    seniority_tier="tier_2",
                    company_name=company_name,
                    company_domain=domain,
                    email=getattr(candidate, 'email', None),
                    phone=getattr(candidate, 'phone', None),
                    overall_confidence=candidate.confidence_score,
                    discovery_sources=['website'],
                    discovery_method=candidate.extraction_method
                )
                executives.append(executive)
            except Exception as e:
                logger.warning(f"⚠️ Failed to convert {candidate.full_name}: {e}")
        
        return executives
    
    def _filter_quality(self, executives: List[ExecutiveContact], company_name: str) -> List[ExecutiveContact]:
        """Filter executives by quality"""
        # Filter by confidence
        qualified = [e for e in executives if e.overall_confidence >= self.min_confidence]
        
        # Remove business names
        filtered = []
        for exec in qualified:
            full_name = f"{exec.first_name} {exec.last_name}".lower()
            
            # Check for business keywords
            business_keywords = ['plumbing', 'heating', 'gas', 'services', 'ltd', 'limited']
            if not any(keyword in full_name for keyword in business_keywords):
                filtered.append(exec)
        
        # Sort by confidence
        filtered.sort(key=lambda x: x.overall_confidence, reverse=True)
        
        return filtered[:10]  # Limit to top 10
    
    def _calc_confidence_dist(self, executives: List[ExecutiveContact]) -> Dict[str, int]:
        """Calculate confidence distribution"""
        dist = {'high': 0, 'medium': 0, 'low': 0}
        for exec in executives:
            if exec.overall_confidence >= 0.7:
                dist['high'] += 1
            elif exec.overall_confidence >= 0.5:
                dist['medium'] += 1
            else:
                dist['low'] += 1
        return dist
    
    def _failed_result(self, company_name: str, website_url: str, start_time: float, error: str) -> Phase4AResult:
        """Create failed result"""
        return Phase4AResult(
            company_name=company_name,
            website_url=website_url,
            executives=[],
            processing_time=time.time() - start_time,
            success=False,
            ml_candidates_found=0,
            final_executives_count=0,
            extraction_methods=[],
            confidence_distribution={'high': 0, 'medium': 0, 'low': 0},
            error_message=error
        )

# Test function
async def test_phase4a_fixed(companies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Test Phase 4A Fixed Engine"""
    engine = Phase4AFixedEngine()
    
    results = []
    start_time = time.time()
    
    for company in companies:
        result = await engine.discover_executives(company)
        results.append(result)
        
        status = "✅ SUCCESS" if result.success else "❌ FAILED"
        logger.info(f"{status}: {result.company_name} - {result.final_executives_count} executives")
    
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r.success)
    success_rate = (successful / len(companies)) * 100
    total_executives = sum(r.final_executives_count for r in results)
    
    return {
        'test_summary': {
            'total_companies': len(companies),
            'successful_companies': successful,
            'success_rate_percentage': round(success_rate, 2),
            'total_executives_found': total_executives,
            'total_processing_time': round(total_time, 2),
            'target_achievement': 'ACHIEVED' if success_rate >= 70 else 'IN_PROGRESS' if success_rate >= 50 else 'NEEDS_WORK'
        },
        'detailed_results': results
    } 