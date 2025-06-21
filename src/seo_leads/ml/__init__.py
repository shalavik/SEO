"""
Machine Learning Optimization Module

P3.2: ML-based enrichment strategy optimization
Features:
- Success pattern learning
- Industry-specific strategy optimization
- Predictive source selection
- Automated strategy adjustment
- Zero-cost architecture (local ML models)
"""

from .enrichment_optimizer import MLEnrichmentOptimizer
from .pattern_recognition import PatternRecognitionEngine

__all__ = [
    'MLEnrichmentOptimizer',
    'PatternRecognitionEngine'
] 