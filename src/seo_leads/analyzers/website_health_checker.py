"""
Website Health Checker - Phase 4B
Advanced website accessibility checking with fallback mechanisms
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from urllib.parse import urlparse
import aiohttp
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class WebsiteHealthStatus:
    """Website health and accessibility status"""
    url: str
    is_accessible: bool = False
    status_code: Optional[int] = None
    response_time: float = 0.0
    content_length: int = 0
    content_quality_score: float = 0.0
    has_meaningful_content: bool = False
    is_under_construction: bool = False
    error_type: str = ""
    error_message: str = ""
    alternative_urls: List[str] = field(default_factory=list)
    last_checked: datetime = field(default_factory=datetime.now)

class WebsiteHealthChecker:
    """Main website health checker"""
    
    async def check_website_health(self, url: str) -> Dict[str, Any]:
        """Check website health - required for workflow integration"""
        logger.info(f"🔍 Health check for: {url}")
        
        health_status = await self.comprehensive_health_check(url)
        
        # Convert to dictionary format expected by workflow
        return {
            'url': url,
            'is_accessible': health_status.is_accessible,
            'status_code': health_status.status_code,
            'response_time': health_status.response_time,
            'content_length': health_status.content_length,
            'content_quality_score': health_status.content_quality_score,
            'has_meaningful_content': health_status.has_meaningful_content,
            'is_under_construction': health_status.is_under_construction,
            'error_type': health_status.error_type,
            'error_message': health_status.error_message,
            'health_score': self._calculate_health_score(health_status),
            'recommendations': self._generate_health_recommendations(health_status),
            'last_checked': health_status.last_checked.isoformat()
        }
    
    async def comprehensive_health_check(self, url: str) -> WebsiteHealthStatus:
        """Perform comprehensive website health check"""
        logger.info(f"🔍 Health check for: {url}")
        
        status = WebsiteHealthStatus(url=url)
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(url) as response:
                    status.response_time = time.time() - start_time
                    status.status_code = response.status
                    
                    if response.status == 200:
                        content = await response.text()
                        status.content_length = len(content)
                        status.is_accessible = True
                        
                        # Analyze content quality
                        quality_analysis = self._analyze_content_quality(content)
                        status.content_quality_score = quality_analysis['quality_score']
                        status.has_meaningful_content = quality_analysis['has_meaningful_content']
                        status.is_under_construction = quality_analysis['is_under_construction']
                    else:
                        status.error_type = f"http_error_{response.status}"
                        status.error_message = f"HTTP {response.status}"
                        
        except asyncio.TimeoutError:
            status.error_type = "timeout"
            status.error_message = "Connection timeout"
            status.response_time = time.time() - start_time
        except Exception as e:
            status.error_type = "connection_error"
            status.error_message = str(e)
            status.response_time = time.time() - start_time
        
        return status
    
    def _analyze_content_quality(self, content: str) -> Dict[str, Any]:
        """Analyze content quality"""
        analysis = {
            'content_length': len(content),
            'quality_score': 0.0,
            'has_meaningful_content': False,
            'is_under_construction': False
        }
        
        # Basic quality scoring based on content length
        if analysis['content_length'] > 10000:
            analysis['quality_score'] = 1.0
        elif analysis['content_length'] > 5000:
            analysis['quality_score'] = 0.8
        elif analysis['content_length'] > 2000:
            analysis['quality_score'] = 0.6
        elif analysis['content_length'] > 500:
            analysis['quality_score'] = 0.4
        else:
            analysis['quality_score'] = 0.2
        
        # Check for meaningful content
        content_lower = content.lower()
        meaningful_indicators = [
            'about us', 'our services', 'contact us', 'our team',
            'experience', 'projects', 'testimonials'
        ]
        
        meaningful_count = sum(1 for indicator in meaningful_indicators if indicator in content_lower)
        if meaningful_count >= 3:
            analysis['has_meaningful_content'] = True
        
        # Check for under construction
        construction_indicators = [
            'under construction', 'coming soon', 'site under development'
        ]
        
        if any(indicator in content_lower for indicator in construction_indicators):
            analysis['is_under_construction'] = True
            analysis['quality_score'] *= 0.3
        
        return analysis

    def _calculate_health_score(self, status: WebsiteHealthStatus) -> float:
        """Calculate overall health score from 0.0 to 1.0"""
        if not status.is_accessible:
            return 0.0
        
        score = 0.0
        
        # Accessibility score (40%)
        if status.status_code == 200:
            score += 0.4
        elif 200 <= status.status_code < 300:
            score += 0.3
        elif 300 <= status.status_code < 400:
            score += 0.2
        
        # Performance score (30%)
        if status.response_time <= 2.0:
            score += 0.3
        elif status.response_time <= 5.0:
            score += 0.2
        elif status.response_time <= 10.0:
            score += 0.1
        
        # Content quality score (30%)
        score += status.content_quality_score * 0.3
        
        # Penalties
        if status.is_under_construction:
            score *= 0.5
        
        return min(score, 1.0)
    
    def _generate_health_recommendations(self, status: WebsiteHealthStatus) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []
        
        if not status.is_accessible:
            recommendations.append("Website is not accessible - check server configuration")
            return recommendations
        
        if status.status_code != 200:
            recommendations.append(f"Fix HTTP status code {status.status_code}")
        
        if status.response_time > 5.0:
            recommendations.append("Improve page load speed (currently > 5 seconds)")
        elif status.response_time > 3.0:
            recommendations.append("Consider optimizing page load speed")
        
        if status.content_quality_score < 0.5:
            recommendations.append("Add more meaningful content to improve user experience")
        
        if not status.has_meaningful_content:
            recommendations.append("Add essential business information (about, services, contact)")
        
        if status.is_under_construction:
            recommendations.append("Complete website development - currently shows under construction")
        
        if status.content_length < 1000:
            recommendations.append("Increase content length for better SEO")
        
        return recommendations

class EnhancedWebsiteFetcher:
    """Enhanced website fetcher with health checking"""
    
    def __init__(self):
        self.health_checker = WebsiteHealthChecker()
    
    async def fetch_with_fallbacks(self, url: str) -> Tuple[Optional[str], WebsiteHealthStatus]:
        """Fetch website content with fallback mechanisms"""
        logger.info(f"🌐 Enhanced fetch: {url}")
        
        # Check health status
        health_status = await self.health_checker.comprehensive_health_check(url)
        
        # If accessible and has good content
        if health_status.is_accessible and health_status.content_quality_score > 0.3:
            content = await self._fetch_content(url)
            if content:
                return content, health_status
        
        # No good content found
        logger.warning(f"❌ No accessible content found for: {url}")
        return None, health_status
    
    async def _fetch_content(self, url: str) -> Optional[str]:
        """Fetch website content"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
        except:
            pass
        return None 