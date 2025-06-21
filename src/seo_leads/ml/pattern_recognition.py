"""
Pattern Recognition Engine

P3.2 IMPLEMENTATION: Advanced pattern recognition for enrichment optimization
Features:
- Success pattern detection
- Company type classification
- Enrichment source effectiveness analysis
- Predictive modeling for source selection
- Zero-cost architecture (local pattern analysis)
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict, Counter
import json
import math

logger = logging.getLogger(__name__)

@dataclass
class CompanyPattern:
    """Detected pattern for a company"""
    company_name: str
    company_domain: str
    detected_patterns: List[str]
    industry_classification: str
    size_estimate: str
    complexity_score: float
    recommended_approach: str

@dataclass
class SuccessPattern:
    """Pattern associated with successful enrichment"""
    pattern_id: str
    pattern_type: str  # 'domain', 'name', 'industry', 'size'
    pattern_value: str
    success_rate: float
    sample_size: int
    confidence: float
    associated_sources: List[str]

class PatternRecognitionEngine:
    """P3.2: Advanced pattern recognition for enrichment optimization"""
    
    def __init__(self):
        self.domain_patterns = self._initialize_domain_patterns()
        self.name_patterns = self._initialize_name_patterns()
        self.industry_patterns = self._initialize_industry_patterns()
        self.success_patterns: List[SuccessPattern] = []
        self.pattern_cache: Dict[str, CompanyPattern] = {}
        
        logger.info("P3.2: Pattern Recognition Engine initialized")
    
    def _initialize_domain_patterns(self) -> Dict:
        """Initialize domain-based patterns"""
        return {
            'local_indicators': [
                r'\b(birmingham|london|manchester|leeds|bristol|liverpool|glasgow|edinburgh)\b',
                r'\b(north|south|east|west|central)\b',
                r'\b(local|area|regional)\b'
            ],
            'business_types': {
                'plumbing': [r'plumb', r'drain', r'pipe', r'boiler', r'heating'],
                'electrical': [r'electric', r'spark', r'wire', r'power', r'lighting'],
                'construction': [r'build', r'construct', r'develop', r'property', r'homes'],
                'roofing': [r'roof', r'tile', r'slate', r'gutter', r'chimney'],
                'cleaning': [r'clean', r'carpet', r'window', r'domestic', r'commercial']
            },
            'size_indicators': {
                'micro': [r'solo', r'one', r'single', r'individual'],
                'small': [r'family', r'local', r'independent', r'small'],
                'medium': [r'group', r'team', r'services', r'solutions'],
                'large': [r'ltd', r'limited', r'plc', r'corp', r'company']
            }
        }
    
    def _initialize_name_patterns(self) -> Dict:
        """Initialize company name patterns"""
        return {
            'personal_business': [
                r'^[A-Z][a-z]+\s+(The\s+)?[A-Z][a-z]+$',  # "John The Plumber"
                r'^[A-Z][a-z]+\'?s\s+[A-Z][a-z]+',  # "Smith's Plumbing"
                r'^[A-Z][a-z]+\s+&\s+[A-Z][a-z]+',  # "Smith & Sons"
            ],
            'professional_services': [
                r'\b(services|solutions|systems|consulting|professional)\b',
                r'\b(expert|specialist|professional|certified)\b'
            ],
            'corporate_indicators': [
                r'\b(ltd|limited|plc|corp|inc|company|group)\b',
                r'\b(international|national|global|worldwide)\b'
            ],
            'quality_indicators': [
                r'\b(premium|quality|professional|expert|master|certified)\b',
                r'\b(approved|accredited|licensed|qualified)\b'
            ]
        }
    
    def _initialize_industry_patterns(self) -> Dict:
        """Initialize industry classification patterns"""
        return {
            'plumbing': {
                'keywords': ['plumb', 'drain', 'pipe', 'boiler', 'heating', 'bathroom', 'kitchen'],
                'services': ['installation', 'repair', 'maintenance', 'emergency'],
                'certifications': ['gas safe', 'corgi', 'ciphe']
            },
            'electrical': {
                'keywords': ['electric', 'electrical', 'spark', 'wire', 'power', 'lighting'],
                'services': ['installation', 'testing', 'inspection', 'rewiring'],
                'certifications': ['niceic', 'elecsa', 'napit', 'part p']
            },
            'construction': {
                'keywords': ['build', 'construct', 'develop', 'property', 'homes', 'extension'],
                'services': ['building', 'renovation', 'refurbishment', 'development'],
                'certifications': ['nhbc', 'fmb', 'citb']
            },
            'roofing': {
                'keywords': ['roof', 'roofing', 'tile', 'slate', 'gutter', 'chimney'],
                'services': ['installation', 'repair', 'maintenance', 'replacement'],
                'certifications': ['nfrc', 'competent person']
            }
        }
    
    def analyze_company_patterns(self, company_name: str, company_domain: str, 
                                additional_context: str = "") -> CompanyPattern:
        """P3.2: Analyze company to detect patterns"""
        try:
            # Check cache first
            cache_key = f"{company_name}:{company_domain}"
            if cache_key in self.pattern_cache:
                return self.pattern_cache[cache_key]
            
            # Combine all text for analysis
            full_text = f"{company_name} {company_domain} {additional_context}".lower()
            
            # Detect patterns
            detected_patterns = []
            
            # Domain patterns
            domain_patterns = self._detect_domain_patterns(full_text)
            detected_patterns.extend(domain_patterns)
            
            # Name patterns
            name_patterns = self._detect_name_patterns(company_name)
            detected_patterns.extend(name_patterns)
            
            # Industry classification
            industry = self._classify_industry(full_text)
            
            # Size estimation
            size_estimate = self._estimate_company_size(full_text, company_name)
            
            # Complexity score
            complexity_score = self._calculate_complexity_score(detected_patterns, industry, size_estimate)
            
            # Recommended approach
            recommended_approach = self._recommend_approach(detected_patterns, industry, complexity_score)
            
            result = CompanyPattern(
                company_name=company_name,
                company_domain=company_domain,
                detected_patterns=detected_patterns,
                industry_classification=industry,
                size_estimate=size_estimate,
                complexity_score=complexity_score,
                recommended_approach=recommended_approach
            )
            
            # Cache result
            self.pattern_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.warning(f"P3.2: Pattern analysis failed for {company_name}: {e}")
            return self._create_default_pattern(company_name, company_domain)
    
    def _detect_domain_patterns(self, text: str) -> List[str]:
        """Detect domain-based patterns"""
        patterns = []
        
        # Local business indicators
        for pattern in self.domain_patterns['local_indicators']:
            if re.search(pattern, text, re.IGNORECASE):
                patterns.append(f"local_business:{pattern}")
        
        # Business type indicators
        for business_type, keywords in self.domain_patterns['business_types'].items():
            for keyword in keywords:
                if keyword in text:
                    patterns.append(f"business_type:{business_type}")
                    break
        
        # Size indicators
        for size, indicators in self.domain_patterns['size_indicators'].items():
            for indicator in indicators:
                if re.search(indicator, text, re.IGNORECASE):
                    patterns.append(f"size_indicator:{size}")
                    break
        
        return patterns
    
    def _detect_name_patterns(self, company_name: str) -> List[str]:
        """Detect company name patterns"""
        patterns = []
        
        # Personal business patterns
        for pattern in self.name_patterns['personal_business']:
            if re.search(pattern, company_name, re.IGNORECASE):
                patterns.append(f"name_type:personal_business")
                break
        
        # Professional services
        for pattern in self.name_patterns['professional_services']:
            if re.search(pattern, company_name, re.IGNORECASE):
                patterns.append(f"name_type:professional_services")
                break
        
        # Corporate indicators
        for pattern in self.name_patterns['corporate_indicators']:
            if re.search(pattern, company_name, re.IGNORECASE):
                patterns.append(f"name_type:corporate")
                break
        
        # Quality indicators
        for pattern in self.name_patterns['quality_indicators']:
            if re.search(pattern, company_name, re.IGNORECASE):
                patterns.append(f"quality_indicator:high")
                break
        
        return patterns
    
    def _classify_industry(self, text: str) -> str:
        """Classify company industry"""
        industry_scores = {}
        
        for industry, data in self.industry_patterns.items():
            score = 0
            
            # Check keywords
            for keyword in data['keywords']:
                if keyword in text:
                    score += 2
            
            # Check services
            for service in data['services']:
                if service in text:
                    score += 1
            
            # Check certifications
            for cert in data['certifications']:
                if cert in text:
                    score += 3
            
            if score > 0:
                industry_scores[industry] = score
        
        if industry_scores:
            return max(industry_scores, key=industry_scores.get)
        else:
            return 'general'
    
    def _estimate_company_size(self, text: str, company_name: str) -> str:
        """Estimate company size"""
        size_scores = {
            'micro': 0,
            'small': 0,
            'medium': 0,
            'large': 0
        }
        
        # Check size indicators in domain patterns
        for size, indicators in self.domain_patterns['size_indicators'].items():
            for indicator in indicators:
                if re.search(indicator, text, re.IGNORECASE):
                    size_scores[size] += 1
        
        # Additional heuristics
        if len(company_name.split()) <= 2:
            size_scores['micro'] += 1
        
        if 'ltd' in text or 'limited' in text:
            size_scores['medium'] += 2
            size_scores['large'] += 1
        
        if 'group' in text or 'international' in text:
            size_scores['large'] += 3
        
        # Return size with highest score
        if any(size_scores.values()):
            return max(size_scores, key=size_scores.get)
        else:
            return 'small'  # Default assumption
    
    def _calculate_complexity_score(self, patterns: List[str], industry: str, size: str) -> float:
        """Calculate enrichment complexity score"""
        complexity = 0.0
        
        # Base complexity by size
        size_complexity = {
            'micro': 0.2,
            'small': 0.4,
            'medium': 0.6,
            'large': 0.8
        }
        complexity += size_complexity.get(size, 0.4)
        
        # Industry complexity
        industry_complexity = {
            'plumbing': 0.3,
            'electrical': 0.4,
            'construction': 0.6,
            'roofing': 0.3,
            'general': 0.5
        }
        complexity += industry_complexity.get(industry, 0.5)
        
        # Pattern-based adjustments
        for pattern in patterns:
            if 'corporate' in pattern:
                complexity += 0.2
            elif 'personal_business' in pattern:
                complexity -= 0.1
            elif 'local_business' in pattern:
                complexity -= 0.1
        
        return min(1.0, max(0.1, complexity))
    
    def _recommend_approach(self, patterns: List[str], industry: str, complexity: float) -> str:
        """Recommend enrichment approach based on patterns"""
        # High complexity companies
        if complexity > 0.7:
            return 'comprehensive'  # Use all sources
        
        # Personal/local businesses
        if any('personal_business' in p or 'local_business' in p for p in patterns):
            return 'local_focused'  # Focus on website and directories
        
        # Corporate businesses
        if any('corporate' in p for p in patterns):
            return 'corporate_focused'  # Focus on LinkedIn and Companies House
        
        # Industry-specific approaches
        if industry in ['plumbing', 'electrical', 'roofing']:
            return 'trades_focused'  # Focus on directories and website
        elif industry == 'construction':
            return 'professional_focused'  # Focus on LinkedIn and website
        
        return 'balanced'  # Default balanced approach
    
    def _create_default_pattern(self, company_name: str, company_domain: str) -> CompanyPattern:
        """Create default pattern when analysis fails"""
        return CompanyPattern(
            company_name=company_name,
            company_domain=company_domain,
            detected_patterns=['default'],
            industry_classification='general',
            size_estimate='small',
            complexity_score=0.5,
            recommended_approach='balanced'
        )
    
    def learn_success_pattern(self, company_pattern: CompanyPattern, 
                             successful_sources: List[str], success_rate: float):
        """Learn from successful enrichment patterns"""
        try:
            # Create success patterns for each detected pattern
            for pattern in company_pattern.detected_patterns:
                pattern_id = f"{pattern}:{company_pattern.industry_classification}"
                
                # Check if pattern already exists
                existing_pattern = None
                for sp in self.success_patterns:
                    if sp.pattern_id == pattern_id:
                        existing_pattern = sp
                        break
                
                if existing_pattern:
                    # Update existing pattern
                    total_samples = existing_pattern.sample_size + 1
                    weighted_success_rate = (
                        (existing_pattern.success_rate * existing_pattern.sample_size + success_rate) 
                        / total_samples
                    )
                    existing_pattern.success_rate = weighted_success_rate
                    existing_pattern.sample_size = total_samples
                    existing_pattern.confidence = min(1.0, total_samples / 10.0)
                    
                    # Update associated sources
                    for source in successful_sources:
                        if source not in existing_pattern.associated_sources:
                            existing_pattern.associated_sources.append(source)
                else:
                    # Create new pattern
                    new_pattern = SuccessPattern(
                        pattern_id=pattern_id,
                        pattern_type=pattern.split(':')[0] if ':' in pattern else 'general',
                        pattern_value=pattern.split(':')[1] if ':' in pattern else pattern,
                        success_rate=success_rate,
                        sample_size=1,
                        confidence=0.1,
                        associated_sources=successful_sources.copy()
                    )
                    self.success_patterns.append(new_pattern)
            
            logger.debug(f"P3.2: Learned success pattern for {company_pattern.company_name}")
            
        except Exception as e:
            logger.warning(f"P3.2: Failed to learn success pattern: {e}")
    
    def predict_best_sources(self, company_pattern: CompanyPattern) -> List[Tuple[str, float]]:
        """Predict best sources based on learned patterns"""
        source_scores = defaultdict(float)
        
        # Score sources based on matching patterns
        for pattern in company_pattern.detected_patterns:
            pattern_id = f"{pattern}:{company_pattern.industry_classification}"
            
            # Find matching success patterns
            for success_pattern in self.success_patterns:
                if success_pattern.pattern_id == pattern_id:
                    weight = success_pattern.confidence * success_pattern.success_rate
                    
                    for source in success_pattern.associated_sources:
                        source_scores[source] += weight
        
        # Apply approach-based scoring
        approach_bonuses = self._get_approach_bonuses(company_pattern.recommended_approach)
        for source, bonus in approach_bonuses.items():
            source_scores[source] += bonus
        
        # Sort by score
        sorted_sources = sorted(source_scores.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_sources[:5]  # Return top 5 sources
    
    def _get_approach_bonuses(self, approach: str) -> Dict[str, float]:
        """Get source bonuses based on recommended approach"""
        bonuses = {
            'comprehensive': {'website': 0.2, 'google': 0.2, 'linkedin': 0.2, 'companies_house': 0.1},
            'local_focused': {'website': 0.3, 'business_directories': 0.3, 'google': 0.1},
            'corporate_focused': {'linkedin': 0.3, 'companies_house': 0.3, 'website': 0.1},
            'trades_focused': {'business_directories': 0.3, 'website': 0.2, 'google': 0.1},
            'professional_focused': {'linkedin': 0.2, 'website': 0.2, 'google': 0.1},
            'balanced': {'website': 0.1, 'google': 0.1, 'linkedin': 0.1}
        }
        
        return bonuses.get(approach, bonuses['balanced'])
    
    def get_pattern_statistics(self) -> Dict:
        """Get pattern recognition statistics"""
        return {
            'cached_patterns': len(self.pattern_cache),
            'success_patterns_learned': len(self.success_patterns),
            'domain_patterns': len(self.domain_patterns),
            'name_patterns': len(self.name_patterns),
            'industry_patterns': len(self.industry_patterns)
        }

# Test function
async def test_pattern_recognition():
    """Test the pattern recognition engine"""
    print("🔍 Testing P3.2 Pattern Recognition Engine...")
    
    engine = PatternRecognitionEngine()
    
    test_companies = [
        ("Jack The Plumber", "jacktheplumber.co.uk", "Master plumber in Birmingham"),
        ("Birmingham Electrical Ltd", "bham-electric.co.uk", "Professional electrical services"),
        ("Smith & Sons Construction", "smithsons.co.uk", "Family construction business"),
        ("Premium Roofing Solutions", "premium-roof.co.uk", "Quality roofing specialists"),
        ("ABC Services Group", "abcservices.co.uk", "Multi-service company")
    ]
    
    for name, domain, context in test_companies:
        pattern = engine.analyze_company_patterns(name, domain, context)
        print(f"Company: {name}")
        print(f"  → Industry: {pattern.industry_classification}")
        print(f"  → Size: {pattern.size_estimate}")
        print(f"  → Complexity: {pattern.complexity_score:.2f}")
        print(f"  → Approach: {pattern.recommended_approach}")
        print(f"  → Patterns: {pattern.detected_patterns}")
        
        # Test source prediction
        predicted_sources = engine.predict_best_sources(pattern)
        print(f"  → Predicted sources: {predicted_sources}")
        print()
    
    stats = engine.get_pattern_statistics()
    print(f"📊 Pattern Recognition Statistics: {stats}")
    print("🎉 P3.2 Pattern Recognition test complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_pattern_recognition()) 