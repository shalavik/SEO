"""
Simple SEO Analyzer - Phase 4A Integration

Basic SEO analysis for executive discovery engine support.
No external API dependencies - works standalone.
"""

import re
import logging
from typing import Dict
import requests
from bs4 import BeautifulSoup


class SEOAnalyzer:
    """Simple SEO analyzer for Phase 4A integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def analyze_website(self, url: str) -> Dict:
        """Comprehensive website SEO analysis - required for workflow integration"""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract SEO elements
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            meta_description = soup.find('meta', attrs={'name': 'description'})
            description_text = meta_description.get('content', '').strip() if meta_description else ""
            
            # Count content elements
            content_text = soup.get_text()
            word_count = len(content_text.split())
            
            # Check for contact information
            has_contact_info = bool(re.search(r'\d{3}[-.]?\d{3}[-.]?\d{4}', content_text))
            has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content_text))
            
            # SEO scoring
            title_score = min(len(title_text) / 60, 1.0) if title_text else 0.0
            description_score = min(len(description_text) / 160, 1.0) if description_text else 0.0
            content_score = min(word_count / 500, 1.0)
            contact_score = 0.8 if (has_contact_info and has_email) else 0.4 if (has_contact_info or has_email) else 0.0
            
            overall_score = (title_score * 0.2 + description_score * 0.2 + content_score * 0.4 + contact_score * 0.2)
            
            return {
                'url': url,
                'overall_score': round(overall_score, 2),
                'title': title_text,
                'title_score': round(title_score, 2),
                'meta_description': description_text,
                'description_score': round(description_score, 2),
                'word_count': word_count,
                'content_score': round(content_score, 2),
                'has_contact_info': has_contact_info,
                'has_email': has_email,
                'contact_score': round(contact_score, 2),
                'analysis_timestamp': 1234567890,
                'seo_recommendations': self._generate_seo_recommendations(title_text, description_text, word_count, has_contact_info)
            }
        except Exception as e:
            self.logger.error(f"SEO analysis failed for {url}: {e}")
            return {
                'url': url,
                'overall_score': 0.0,
                'title': "",
                'title_score': 0.0,
                'meta_description': "",
                'description_score': 0.0,
                'word_count': 0,
                'content_score': 0.0,
                'has_contact_info': False,
                'has_email': False,
                'contact_score': 0.0,
                'analysis_timestamp': 1234567890,
                'error': str(e),
                'seo_recommendations': []
            }
        
    def analyze_url(self, url: str) -> Dict:
        """Analyze URL for basic SEO metrics - legacy method"""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            return {
                'overall_score': 0.5,  # Basic score
                'title_score': 0.5,
                'content_score': 0.5,
                'has_contact_info': bool(re.search(r'\d{3}[-.]?\d{3}[-.]?\d{4}', soup.get_text())),
                'analysis_timestamp': 1234567890
            }
        except:
            return {
                'overall_score': 0.0,
                'title_score': 0.0,
                'content_score': 0.0,
                'has_contact_info': False,
                'analysis_timestamp': 1234567890
            }
    
    def _generate_seo_recommendations(self, title: str, description: str, word_count: int, has_contact: bool) -> list:
        """Generate SEO improvement recommendations"""
        recommendations = []
        
        if not title or len(title) < 30:
            recommendations.append("Add or improve page title (30-60 characters)")
        
        if not description or len(description) < 120:
            recommendations.append("Add or improve meta description (120-160 characters)")
        
        if word_count < 300:
            recommendations.append("Increase content length (minimum 300 words recommended)")
        
        if not has_contact:
            recommendations.append("Add clear contact information for better local SEO")
        
        return recommendations
