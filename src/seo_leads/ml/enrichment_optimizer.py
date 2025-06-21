"""
ML Enrichment Optimizer

P3.2 IMPLEMENTATION: Machine learning-based enrichment strategy optimization
Features:
- Success pattern learning from historical data
- Industry-specific strategy optimization
- Predictive source selection
- Automated strategy adjustment
- Zero-cost architecture (local ML models)
"""

import logging
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import pickle
import os

logger = logging.getLogger(__name__)

@dataclass
class EnrichmentAttempt:
    """Record of an enrichment attempt"""
    company_name: str
    company_domain: str
    industry: Optional[str]
    source: str  # 'google', 'linkedin', 'website', 'companies_house', etc.
    success: bool
    processing_time: float
    confidence_score: float
    executives_found: int
    timestamp: float
    error_type: Optional[str] = None

@dataclass
class OptimizationStrategy:
    """Optimized enrichment strategy"""
    company_profile: Dict[str, Any]
    recommended_sources: List[str]
    source_priorities: Dict[str, float]
    expected_success_rate: float
    estimated_processing_time: float
    confidence: float

class MLEnrichmentOptimizer:
    """P3.2: ML-based enrichment strategy optimization"""
    
    def __init__(self, data_file: str = "enrichment_history.pkl"):
        self.data_file = data_file
        self.enrichment_history: List[EnrichmentAttempt] = []
        self.success_patterns: Dict[str, Any] = {}
        self.industry_strategies: Dict[str, Dict] = {}
        self.source_performance: Dict[str, Dict] = {}
        
        self._load_historical_data()
        self._initialize_patterns()
        
        logger.info("P3.2: ML Enrichment Optimizer initialized")
    
    def _load_historical_data(self):
        """Load historical enrichment data"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'rb') as f:
                    data = pickle.load(f)
                    self.enrichment_history = data.get('history', [])
                    self.success_patterns = data.get('patterns', {})
                    self.industry_strategies = data.get('industry_strategies', {})
                    self.source_performance = data.get('source_performance', {})
                logger.info(f"P3.2: Loaded {len(self.enrichment_history)} historical records")
            else:
                logger.info("P3.2: No historical data found, starting fresh")
        except Exception as e:
            logger.warning(f"P3.2: Failed to load historical data: {e}")
    
    def _save_historical_data(self):
        """Save historical enrichment data"""
        try:
            data = {
                'history': self.enrichment_history,
                'patterns': self.success_patterns,
                'industry_strategies': self.industry_strategies,
                'source_performance': self.source_performance
            }
            with open(self.data_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.warning(f"P3.2: Failed to save historical data: {e}")
    
    def _initialize_patterns(self):
        """Initialize success patterns from historical data"""
        if not self.enrichment_history:
            # Initialize with default patterns
            self.success_patterns = {
                'source_success_rates': {
                    'website': 0.85,
                    'google': 0.60,
                    'linkedin': 0.45,
                    'companies_house': 0.30,
                    'business_directories': 0.25
                },
                'industry_preferences': {
                    'plumbing': ['website', 'business_directories', 'google'],
                    'electrical': ['website', 'google', 'linkedin'],
                    'construction': ['website', 'linkedin', 'companies_house'],
                    'default': ['website', 'google', 'linkedin']
                },
                'processing_time_estimates': {
                    'website': 15.0,
                    'google': 8.0,
                    'linkedin': 12.0,
                    'companies_house': 5.0,
                    'business_directories': 10.0
                }
            }
        else:
            self._analyze_historical_patterns()
    
    def _analyze_historical_patterns(self):
        """Analyze historical data to extract patterns"""
        # Analyze source success rates
        source_stats = defaultdict(lambda: {'attempts': 0, 'successes': 0, 'total_time': 0.0})
        
        for attempt in self.enrichment_history:
            stats = source_stats[attempt.source]
            stats['attempts'] += 1
            if attempt.success:
                stats['successes'] += 1
            stats['total_time'] += attempt.processing_time
        
        # Calculate success rates and average times
        source_success_rates = {}
        processing_time_estimates = {}
        
        for source, stats in source_stats.items():
            if stats['attempts'] > 0:
                source_success_rates[source] = stats['successes'] / stats['attempts']
                processing_time_estimates[source] = stats['total_time'] / stats['attempts']
        
        # Analyze industry-specific patterns
        industry_preferences = defaultdict(lambda: defaultdict(int))
        
        for attempt in self.enrichment_history:
            if attempt.industry and attempt.success:
                industry_preferences[attempt.industry][attempt.source] += 1
        
        # Convert to sorted preferences
        industry_strategies = {}
        for industry, sources in industry_preferences.items():
            sorted_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)
            industry_strategies[industry] = [source for source, count in sorted_sources]
        
        self.success_patterns = {
            'source_success_rates': source_success_rates,
            'industry_preferences': industry_strategies,
            'processing_time_estimates': processing_time_estimates
        }
    
    def record_enrichment_attempt(self, attempt: EnrichmentAttempt):
        """Record an enrichment attempt for learning"""
        self.enrichment_history.append(attempt)
        
        # Update patterns incrementally
        self._update_patterns_incremental(attempt)
        
        # Save data periodically
        if len(self.enrichment_history) % 10 == 0:
            self._save_historical_data()
        
        logger.debug(f"P3.2: Recorded enrichment attempt for {attempt.company_name}")
    
    def _update_patterns_incremental(self, attempt: EnrichmentAttempt):
        """Update patterns incrementally with new data"""
        # Update source performance
        if attempt.source not in self.source_performance:
            self.source_performance[attempt.source] = {
                'attempts': 0, 'successes': 0, 'total_time': 0.0, 'success_rate': 0.0
            }
        
        perf = self.source_performance[attempt.source]
        perf['attempts'] += 1
        if attempt.success:
            perf['successes'] += 1
        perf['total_time'] += attempt.processing_time
        perf['success_rate'] = perf['successes'] / perf['attempts']
        perf['avg_time'] = perf['total_time'] / perf['attempts']
        
        # Update success patterns
        if 'source_success_rates' not in self.success_patterns:
            self.success_patterns['source_success_rates'] = {}
        
        self.success_patterns['source_success_rates'][attempt.source] = perf['success_rate']
        
        if 'processing_time_estimates' not in self.success_patterns:
            self.success_patterns['processing_time_estimates'] = {}
        
        self.success_patterns['processing_time_estimates'][attempt.source] = perf['avg_time']
    
    def optimize_strategy(self, company_name: str, company_domain: str, 
                         industry: Optional[str] = None, 
                         time_budget: float = 60.0) -> OptimizationStrategy:
        """P3.2: Optimize enrichment strategy for a company"""
        try:
            # Create company profile
            company_profile = {
                'name': company_name,
                'domain': company_domain,
                'industry': industry,
                'time_budget': time_budget
            }
            
            # Get industry-specific preferences
            industry_sources = self._get_industry_sources(industry)
            
            # Calculate source priorities based on success rates and time constraints
            source_priorities = self._calculate_source_priorities(industry_sources, time_budget)
            
            # Select recommended sources
            recommended_sources = self._select_optimal_sources(source_priorities, time_budget)
            
            # Estimate success rate and processing time
            expected_success_rate = self._estimate_success_rate(recommended_sources)
            estimated_processing_time = self._estimate_processing_time(recommended_sources)
            
            # Calculate strategy confidence
            confidence = self._calculate_strategy_confidence(company_profile, recommended_sources)
            
            return OptimizationStrategy(
                company_profile=company_profile,
                recommended_sources=recommended_sources,
                source_priorities=source_priorities,
                expected_success_rate=expected_success_rate,
                estimated_processing_time=estimated_processing_time,
                confidence=confidence
            )
            
        except Exception as e:
            logger.warning(f"P3.2: Strategy optimization failed for {company_name}: {e}")
            return self._create_default_strategy(company_name, company_domain, industry, time_budget)
    
    def _get_industry_sources(self, industry: Optional[str]) -> List[str]:
        """Get preferred sources for industry"""
        if not industry:
            return self.success_patterns.get('industry_preferences', {}).get('default', 
                ['website', 'google', 'linkedin', 'companies_house'])
        
        industry_lower = industry.lower()
        
        # Check for exact match
        if industry_lower in self.success_patterns.get('industry_preferences', {}):
            return self.success_patterns['industry_preferences'][industry_lower]
        
        # Check for partial matches
        for known_industry, sources in self.success_patterns.get('industry_preferences', {}).items():
            if industry_lower in known_industry or known_industry in industry_lower:
                return sources
        
        # Default sources
        return ['website', 'google', 'linkedin', 'companies_house']
    
    def _calculate_source_priorities(self, sources: List[str], time_budget: float) -> Dict[str, float]:
        """Calculate priority scores for sources"""
        priorities = {}
        success_rates = self.success_patterns.get('source_success_rates', {})
        time_estimates = self.success_patterns.get('processing_time_estimates', {})
        
        for source in sources:
            success_rate = success_rates.get(source, 0.5)  # Default 50%
            time_estimate = time_estimates.get(source, 10.0)  # Default 10s
            
            # Calculate efficiency score (success rate / time)
            efficiency = success_rate / max(time_estimate, 1.0)
            
            # Apply time budget constraint
            time_penalty = 1.0
            if time_estimate > time_budget * 0.5:  # If source takes >50% of budget
                time_penalty = 0.7
            
            priority = efficiency * time_penalty * success_rate
            priorities[source] = priority
        
        return priorities
    
    def _select_optimal_sources(self, source_priorities: Dict[str, float], time_budget: float) -> List[str]:
        """Select optimal sources within time budget"""
        # Sort sources by priority
        sorted_sources = sorted(source_priorities.items(), key=lambda x: x[1], reverse=True)
        
        selected_sources = []
        estimated_time = 0.0
        time_estimates = self.success_patterns.get('processing_time_estimates', {})
        
        for source, priority in sorted_sources:
            source_time = time_estimates.get(source, 10.0)
            
            # Check if we can fit this source in the budget
            if estimated_time + source_time <= time_budget:
                selected_sources.append(source)
                estimated_time += source_time
            
            # Always include at least one source
            if not selected_sources:
                selected_sources.append(source)
                break
        
        return selected_sources
    
    def _estimate_success_rate(self, sources: List[str]) -> float:
        """Estimate overall success rate for selected sources"""
        success_rates = self.success_patterns.get('source_success_rates', {})
        
        # Calculate combined success rate (1 - product of failure rates)
        failure_rate = 1.0
        for source in sources:
            source_success_rate = success_rates.get(source, 0.5)
            failure_rate *= (1.0 - source_success_rate)
        
        return 1.0 - failure_rate
    
    def _estimate_processing_time(self, sources: List[str]) -> float:
        """Estimate total processing time for selected sources"""
        time_estimates = self.success_patterns.get('processing_time_estimates', {})
        
        total_time = 0.0
        for source in sources:
            total_time += time_estimates.get(source, 10.0)
        
        return total_time
    
    def _calculate_strategy_confidence(self, company_profile: Dict, sources: List[str]) -> float:
        """Calculate confidence in the optimization strategy"""
        confidence = 0.0
        
        # Base confidence from historical data volume
        history_confidence = min(0.4, len(self.enrichment_history) / 100.0)
        confidence += history_confidence
        
        # Industry-specific confidence
        industry = company_profile.get('industry')
        if industry and industry.lower() in self.success_patterns.get('industry_preferences', {}):
            confidence += 0.3
        else:
            confidence += 0.1
        
        # Source coverage confidence
        source_coverage = len(sources) / 5.0  # Assume 5 is max useful sources
        confidence += min(0.3, source_coverage)
        
        return min(1.0, confidence)
    
    def _create_default_strategy(self, company_name: str, company_domain: str, 
                                industry: Optional[str], time_budget: float) -> OptimizationStrategy:
        """Create default strategy when optimization fails"""
        return OptimizationStrategy(
            company_profile={
                'name': company_name,
                'domain': company_domain,
                'industry': industry,
                'time_budget': time_budget
            },
            recommended_sources=['website', 'google', 'linkedin'],
            source_priorities={'website': 0.8, 'google': 0.6, 'linkedin': 0.4},
            expected_success_rate=0.7,
            estimated_processing_time=35.0,
            confidence=0.3
        )
    
    def get_optimization_statistics(self) -> Dict:
        """Get optimization statistics"""
        return {
            'total_attempts': len(self.enrichment_history),
            'sources_tracked': len(self.source_performance),
            'industries_learned': len(self.success_patterns.get('industry_preferences', {})),
            'success_patterns_available': bool(self.success_patterns),
            'data_file_exists': os.path.exists(self.data_file)
        }
    
    def export_patterns(self) -> Dict:
        """Export learned patterns for analysis"""
        return {
            'success_patterns': self.success_patterns,
            'source_performance': self.source_performance,
            'industry_strategies': self.industry_strategies,
            'total_attempts': len(self.enrichment_history)
        }

# Test function
async def test_ml_optimizer():
    """Test the ML enrichment optimizer"""
    print("🤖 Testing P3.2 ML Enrichment Optimizer...")
    
    optimizer = MLEnrichmentOptimizer()
    
    # Simulate some historical data
    test_attempts = [
        EnrichmentAttempt("Jack The Plumber", "jacktheplumber.co.uk", "plumbing", 
                         "website", True, 15.2, 0.9, 1, time.time()),
        EnrichmentAttempt("Birmingham Electrical", "bham-electric.co.uk", "electrical", 
                         "google", True, 8.5, 0.7, 1, time.time()),
        EnrichmentAttempt("London Construction", "london-build.co.uk", "construction", 
                         "linkedin", False, 12.0, 0.3, 0, time.time()),
    ]
    
    for attempt in test_attempts:
        optimizer.record_enrichment_attempt(attempt)
    
    # Test strategy optimization
    test_companies = [
        ("Test Plumber", "testplumber.co.uk", "plumbing"),
        ("Electric Solutions", "electric-sol.co.uk", "electrical"),
        ("Build Corp", "buildcorp.co.uk", "construction"),
        ("Unknown Business", "unknown.co.uk", None)
    ]
    
    for name, domain, industry in test_companies:
        strategy = optimizer.optimize_strategy(name, domain, industry, 60.0)
        print(f"Company: {name} ({industry})")
        print(f"  → Recommended sources: {strategy.recommended_sources}")
        print(f"  → Expected success rate: {strategy.expected_success_rate:.2f}")
        print(f"  → Estimated time: {strategy.estimated_processing_time:.1f}s")
        print(f"  → Confidence: {strategy.confidence:.2f}")
        print()
    
    stats = optimizer.get_optimization_statistics()
    print(f"📊 Optimization Statistics: {stats}")
    print("🎉 P3.2 ML Optimizer test complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ml_optimizer()) 