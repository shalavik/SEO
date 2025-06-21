"""
AI-Powered Enhancement Module

P3.1: AI-powered name recognition and executive title classification
P3.2: Machine learning optimization for enrichment strategies

Features:
- NLP-based name recognition using spaCy
- Executive title classification
- Pattern recognition and learning
- Zero-cost architecture (no external AI APIs)
"""

from .name_recognition_engine import NameRecognitionEngine
from .executive_title_classifier import ExecutiveTitleClassifier

__all__ = [
    'NameRecognitionEngine',
    'ExecutiveTitleClassifier'
] 