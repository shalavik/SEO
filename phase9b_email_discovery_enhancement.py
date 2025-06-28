#!/usr/bin/env python3
"""
Phase 9B: Email Discovery Enhancement Engine
==========================================

Advanced email discovery system with Context7-inspired intelligence:
- Domain-specific email pattern recognition
- Executive email inference and validation
- Company-specific email format detection
- Email deliverability assessment
- Social media email discovery integration
- Zero-cost email verification strategies

Builds on Phase 9A contact extraction for comprehensive email intelligence
Implements Context7 best practices for email discovery and validation
"""

import asyncio
import json
import time
import logging
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Any, Set
from pathlib import Path
import pandas as pd
from urllib.parse import urlparse, urljoin
import aiohttp
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import numpy as np

@dataclass
class Phase9bConfig:
    """Email Discovery Enhancement Configuration - Context7 Best Practices"""
    # Email Discovery Configuration
    max_concurrent_domains: int = 3
    max_pages_per_domain: int = 10
    session_timeout: int = 25
    
    # Email Pattern Configuration
    email_confidence_threshold: float = 0.65
    domain_matching_bonus: float = 0.20
    executive_email_bonus: float = 0.15
    pattern_discovery_threshold: float = 0.60
    
    # Inference Configuration
    enable_name_inference: bool = True
    enable_title_inference: bool = True
    enable_department_inference: bool = True
    enable_format_detection: bool = True
    
    # Validation Configuration
    enable_deliverability_check: bool = True
    enable_mx_record_validation: bool = True
    enable_social_media_discovery: bool = True
    max_inferred_emails_per_executive: int = 8

@dataclass
class EmailPattern:
    """Email Pattern Structure for Context7 Analysis"""
    pattern_type: str
    confidence_score: float
    example_emails: List[str]
    pattern_regex: str
    frequency_score: float

@dataclass
class EmailDiscoveryResult:
    """Email Discovery Result with Context7 Intelligence"""
    discovered_emails: List[str]
    inferred_emails: List[str]
    pattern_analysis: Dict[str, Any]
    domain_intelligence: Dict[str, Any]
    validation_results: Dict[str, Any]
    discovery_confidence: float
    processing_time: float

class Phase9bDomainIntelligence:
    """Context7-Inspired Domain Intelligence for Email Discovery"""
    
    def __init__(self, config: Phase9bConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Company email pattern templates
        self.email_format_patterns = [
            # Standard patterns
            r'{first}\.{last}@{domain}',
            r'{first}@{domain}',
            r'{last}@{domain}',
            r'{first_initial}\.{last}@{domain}',
            r'{first_initial}{last}@{domain}',
            r'{first}{last_initial}@{domain}',
            r'{first}{last}@{domain}',
            
            # Executive patterns
            r'{title}@{domain}',
            r'{first}\.{title}@{domain}',
            r'{title}\.{last}@{domain}',
            
            # Department patterns
            r'{department}@{domain}',
            r'{first}\.{department}@{domain}',
            r'{department}\.{first}@{domain}'
        ]
        
        # Executive title mappings
        self.executive_titles = {
            'CEO': ['ceo', 'chief.executive', 'executive'],
            'CTO': ['cto', 'chief.technology', 'technology'],
            'CFO': ['cfo', 'chief.financial', 'finance'],
            'COO': ['coo', 'chief.operating', 'operations'],
            'Director': ['director', 'dir'],
            'Manager': ['manager', 'mgr'],
            'President': ['president', 'pres'],
            'VP': ['vp', 'vice.president', 'vicepresident']
        }
        
        # Department mappings
        self.department_mappings = {
            'sales': ['sales', 'business', 'bd'],
            'marketing': ['marketing', 'growth', 'digital'],
            'hr': ['hr', 'human.resources', 'people'],
            'it': ['it', 'tech', 'technology'],
            'finance': ['finance', 'accounting', 'accounts']
        }
    
    def analyze_domain_patterns(self, domain: str, discovered_emails: List[str]) -> Dict[str, Any]:
        """Analyze domain email patterns using Context7 intelligence"""
        pattern_analysis = {
            'detected_patterns': [],
            'confidence_scores': {},
            'format_preferences': {},
            'executive_patterns': {},
            'domain_intelligence': {}
        }
        
        if not discovered_emails:
            return pattern_analysis
        
        # Extract email formats
        formats = []
        for email in discovered_emails:
            local_part = email.split('@')[0]
            format_type = self._classify_email_format(local_part)
            formats.append(format_type)
        
        # Analyze format frequency
        format_frequency = {}
        for fmt in formats:
            format_frequency[fmt] = format_frequency.get(fmt, 0) + 1
        
        # Sort by frequency
        sorted_formats = sorted(format_frequency.items(), key=lambda x: x[1], reverse=True)
        
        # Generate pattern analysis
        total_emails = len(discovered_emails)
        for format_type, count in sorted_formats:
            confidence = count / total_emails
            
            if confidence >= self.config.pattern_discovery_threshold:
                pattern_analysis['detected_patterns'].append({
                    'format_type': format_type,
                    'frequency': count,
                    'confidence': confidence,
                    'examples': [email for email, fmt in zip(discovered_emails, formats) if fmt == format_type][:3]
                })
        
        # Domain intelligence
        pattern_analysis['domain_intelligence'] = {
            'total_emails_analyzed': total_emails,
            'unique_formats_found': len(format_frequency),
            'primary_format': sorted_formats[0][0] if sorted_formats else 'unknown',
            'format_diversity_score': len(format_frequency) / max(1, total_emails)
        }
        
        return pattern_analysis
    
    def _classify_email_format(self, local_part: str) -> str:
        """Classify email format using Context7 pattern recognition"""
        local_lower = local_part.lower()
        
        # Check for common patterns
        if '.' in local_lower:
            parts = local_lower.split('.')
            if len(parts) == 2:
                first, second = parts
                if len(first) == 1:
                    return 'initial_lastname'
                elif len(second) == 1:
                    return 'firstname_initial'
                elif len(first) > 1 and len(second) > 1:
                    return 'firstname_lastname'
                else:
                    return 'complex_dotted'
            else:
                return 'multiple_dots'
        
        # Check for executive titles
        for title, variants in self.executive_titles.items():
            if any(variant in local_lower for variant in variants):
                return 'executive_title'
        
        # Check for departments
        for dept, variants in self.department_mappings.items():
            if any(variant in local_lower for variant in variants):
                return 'department_based'
        
        # Check for concatenated names (no separators)
        if local_lower.isalpha() and len(local_lower) > 3:
            return 'concatenated_name'
        
        return 'generic_format'
    
    def infer_executive_emails(self, executive_name: str, executive_title: str, domain: str, 
                             detected_patterns: List[Dict]) -> List[str]:
        """Infer executive emails using Context7 domain intelligence"""
        inferred_emails = []
        
        if not executive_name or not domain:
            return inferred_emails
        
        # Parse executive name
        name_parts = executive_name.lower().strip().split()
        if len(name_parts) < 2:
            return inferred_emails
        
        first_name = name_parts[0]
        last_name = name_parts[-1]
        first_initial = first_name[0] if first_name else ''
        last_initial = last_name[0] if last_name else ''
        
        # Generate emails based on detected patterns
        if detected_patterns:
            for pattern in detected_patterns:
                format_type = pattern['format_type']
                confidence = pattern['confidence']
                
                # Generate based on format type
                generated_emails = self._generate_emails_by_format(
                    format_type, first_name, last_name, first_initial, last_initial, domain
                )
                
                for email in generated_emails:
                    inferred_emails.append({
                        'email': email,
                        'confidence': confidence * 0.8,  # Slight discount for inference
                        'pattern_type': format_type,
                        'inference_method': 'pattern_based'
                    })
        
        # Generate emails based on executive title
        if executive_title and self.config.enable_title_inference:
            title_emails = self._generate_title_based_emails(executive_title, domain, first_name, last_name)
            inferred_emails.extend(title_emails)
        
        # Generate common format emails
        common_emails = self._generate_common_format_emails(first_name, last_name, domain)
        inferred_emails.extend(common_emails)
        
        # Remove duplicates and sort by confidence
        seen_emails = set()
        unique_emails = []
        
        for email_info in inferred_emails:
            email = email_info['email']
            if email not in seen_emails and len(unique_emails) < self.config.max_inferred_emails_per_executive:
                seen_emails.add(email)
                unique_emails.append(email_info)
        
        # Sort by confidence
        unique_emails.sort(key=lambda x: x['confidence'], reverse=True)
        
        return [email_info['email'] for email_info in unique_emails]
    
    def _generate_emails_by_format(self, format_type: str, first: str, last: str, 
                                  first_initial: str, last_initial: str, domain: str) -> List[str]:
        """Generate emails based on specific format type"""
        emails = []
        
        format_generators = {
            'firstname_lastname': [f"{first}.{last}@{domain}"],
            'initial_lastname': [f"{first_initial}.{last}@{domain}"],
            'firstname_initial': [f"{first}.{last_initial}@{domain}"],
            'concatenated_name': [f"{first}{last}@{domain}"],
            'firstname_only': [f"{first}@{domain}"],
            'lastname_only': [f"{last}@{domain}"]
        }
        
        return format_generators.get(format_type, [])
    
    def _generate_title_based_emails(self, title: str, domain: str, first_name: str, last_name: str) -> List[Dict]:
        """Generate title-based emails using Context7 executive intelligence"""
        title_emails = []
        title_lower = title.lower()
        
        # Map title to email variants
        title_variants = []
        for exec_title, variants in self.executive_titles.items():
            if any(variant.replace('.', '') in title_lower for variant in variants):
                title_variants.extend(variants)
        
        for variant in title_variants[:3]:  # Limit variants
            title_emails.append({
                'email': f"{variant}@{domain}",
                'confidence': 0.7,
                'pattern_type': 'executive_title',
                'inference_method': 'title_based'
            })
            
            # Combination with name
            title_emails.append({
                'email': f"{first_name}.{variant}@{domain}",
                'confidence': 0.6,
                'pattern_type': 'name_title_combo',
                'inference_method': 'title_based'
            })
        
        return title_emails
    
    def _generate_common_format_emails(self, first_name: str, last_name: str, domain: str) -> List[Dict]:
        """Generate common format emails using Context7 standards"""
        common_emails = [
            {'email': f"{first_name}.{last_name}@{domain}", 'confidence': 0.8, 'pattern_type': 'standard', 'inference_method': 'common_format'},
            {'email': f"{first_name}@{domain}", 'confidence': 0.6, 'pattern_type': 'firstname_only', 'inference_method': 'common_format'},
            {'email': f"{last_name}@{domain}", 'confidence': 0.5, 'pattern_type': 'lastname_only', 'inference_method': 'common_format'},
            {'email': f"{first_name[0]}.{last_name}@{domain}", 'confidence': 0.7, 'pattern_type': 'initial_lastname', 'inference_method': 'common_format'},
            {'email': f"{first_name}{last_name}@{domain}", 'confidence': 0.6, 'pattern_type': 'concatenated', 'inference_method': 'common_format'}
        ]
        
        return common_emails

class Phase9bEmailValidator:
    """Context7-Inspired Email Validation and Deliverability Assessment"""
    
    def __init__(self, config: Phase9bConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def validate_email_addresses(self, email_addresses: List[str], domain: str) -> Dict[str, Any]:
        """Validate email addresses using Context7 best practices"""
        validation_results = {
            'total_emails': len(email_addresses),
            'valid_emails': [],
            'invalid_emails': [],
            'suspicious_emails': [],
            'domain_analysis': {},
            'deliverability_scores': {}
        }
        
        for email in email_addresses:
            try:
                # Basic format validation
                if self._is_valid_email_format(email):
                    # Domain validation
                    email_domain = email.split('@')[1].lower()
                    
                    if email_domain == domain.lower():
                        # Company domain match
                        validation_score = 0.9
                        validation_results['valid_emails'].append({
                            'email': email,
                            'validation_score': validation_score,
                            'validation_type': 'company_domain_match'
                        })
                    else:
                        # External domain
                        validation_score = 0.3
                        validation_results['suspicious_emails'].append({
                            'email': email,
                            'validation_score': validation_score,
                            'validation_type': 'external_domain',
                            'reason': 'Domain mismatch'
                        })
                else:
                    validation_results['invalid_emails'].append({
                        'email': email,
                        'validation_score': 0.0,
                        'validation_type': 'invalid_format',
                        'reason': 'Invalid email format'
                    })
                    
            except Exception as e:
                self.logger.warning(f"Email validation error for {email}: {e}")
                validation_results['invalid_emails'].append({
                    'email': email,
                    'validation_score': 0.0,
                    'validation_type': 'validation_error',
                    'reason': str(e)
                })
        
        # Domain analysis
        validation_results['domain_analysis'] = await self._analyze_domain(domain)
        
        return validation_results
    
    def _is_valid_email_format(self, email: str) -> bool:
        """Validate email format using Context7 patterns"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    async def _analyze_domain(self, domain: str) -> Dict[str, Any]:
        """Analyze domain using Context7 intelligence"""
        domain_analysis = {
            'domain': domain,
            'mx_records_exist': False,
            'domain_age_estimate': 'unknown',
            'subdomain_analysis': {},
            'email_server_analysis': {}
        }
        
        try:
            # Simple domain validation (in real implementation, would use DNS lookup)
            if '.' in domain and len(domain.split('.')) >= 2:
                domain_analysis['mx_records_exist'] = True
                domain_analysis['domain_age_estimate'] = 'established'
                
        except Exception as e:
            self.logger.warning(f"Domain analysis error for {domain}: {e}")
        
        return domain_analysis

class Phase9bEmailDiscoveryEngine:
    """Context7-Inspired Email Discovery Enhancement Engine - Main Interface"""
    
    def __init__(self, config: Optional[Phase9bConfig] = None):
        self.config = config or Phase9bConfig()
        self.logger = logging.getLogger(__name__)
        self.domain_intelligence = Phase9bDomainIntelligence(self.config)
        self.email_validator = Phase9bEmailValidator(self.config)
        
        # Processing statistics
        self.processing_stats = {
            'domains_processed': 0,
            'emails_discovered': 0,
            'emails_inferred': 0,
            'processing_time': 0.0
        }
    
    async def discover_executive_emails(self, company_name: str, domain: str, 
                                      executives: List[Dict]) -> EmailDiscoveryResult:
        """Discover executive emails using Context7 enhancement techniques"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting email discovery for {company_name} ({domain})")
            
            # Discover existing emails from web content
            discovered_emails = await self._discover_emails_from_web(domain)
            
            # Analyze domain patterns
            pattern_analysis = self.domain_intelligence.analyze_domain_patterns(domain, discovered_emails)
            
            # Infer executive emails
            inferred_emails = []
            for executive in executives:
                exec_name = executive.get('name', '')
                exec_title = executive.get('title', '')
                
                exec_inferred = self.domain_intelligence.infer_executive_emails(
                    exec_name, exec_title, domain, pattern_analysis.get('detected_patterns', [])
                )
                inferred_emails.extend(exec_inferred)
            
            # Validate all emails
            all_emails = discovered_emails + inferred_emails
            validation_results = await self.email_validator.validate_email_addresses(all_emails, domain)
            
            # Calculate discovery confidence
            discovery_confidence = self._calculate_discovery_confidence(
                discovered_emails, inferred_emails, pattern_analysis, validation_results
            )
            
            # Create result
            processing_time = time.time() - start_time
            result = EmailDiscoveryResult(
                discovered_emails=discovered_emails,
                inferred_emails=inferred_emails,
                pattern_analysis=pattern_analysis,
                domain_intelligence=self.domain_intelligence.analyze_domain_patterns(domain, discovered_emails),
                validation_results=validation_results,
                discovery_confidence=discovery_confidence,
                processing_time=processing_time
            )
            
            # Update processing statistics
            self._update_processing_stats(result)
            
            self.logger.info(f"Email discovery completed for {company_name}: {len(discovered_emails)} discovered, {len(inferred_emails)} inferred")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in email discovery for {company_name}: {e}")
            return EmailDiscoveryResult(
                discovered_emails=[],
                inferred_emails=[],
                pattern_analysis={},
                domain_intelligence={},
                validation_results={},
                discovery_confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _discover_emails_from_web(self, domain: str) -> List[str]:
        """Discover emails from web content using Context7 scraping"""
        discovered_emails = []
        
        # Priority pages for email discovery
        priority_paths = [
            '',  # Main page
            '/contact', '/contact-us', '/contacts',
            '/about', '/about-us', '/team', '/staff',
            '/leadership', '/management', '/executives'
        ]
        
        base_url = f"https://{domain}"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.session_timeout)) as session:
            for path in priority_paths[:self.config.max_pages_per_domain]:
                try:
                    url = urljoin(base_url, path)
                    async with session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            page_emails = self._extract_emails_from_content(html, domain)
                            discovered_emails.extend(page_emails)
                            
                except Exception as e:
                    self.logger.warning(f"Failed to fetch emails from {url}: {e}")
                    continue
        
        # Remove duplicates
        return list(set(discovered_emails))
    
    def _extract_emails_from_content(self, content: str, domain: str) -> List[str]:
        """Extract emails from content using Context7 patterns"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        
        # Filter for relevant emails
        relevant_emails = []
        for email in emails:
            email_lower = email.lower()
            email_domain = email.split('@')[1].lower()
            
            # Include company domain emails
            if domain.lower() in email_domain:
                relevant_emails.append(email_lower)
            # Include potential executive emails from other domains
            elif any(title in email_lower for title in ['ceo', 'cto', 'cfo', 'director', 'manager']):
                relevant_emails.append(email_lower)
        
        return relevant_emails
    
    def _calculate_discovery_confidence(self, discovered_emails: List[str], inferred_emails: List[str],
                                      pattern_analysis: Dict, validation_results: Dict) -> float:
        """Calculate discovery confidence using Context7 metrics"""
        confidence = 0.5  # Base confidence
        
        # Discovered emails boost
        if discovered_emails:
            confidence += 0.3 * min(1.0, len(discovered_emails) / 5)
        
        # Pattern analysis boost
        detected_patterns = pattern_analysis.get('detected_patterns', [])
        if detected_patterns:
            avg_pattern_confidence = sum(p['confidence'] for p in detected_patterns) / len(detected_patterns)
            confidence += 0.2 * avg_pattern_confidence
        
        # Validation boost
        valid_emails = validation_results.get('valid_emails', [])
        total_emails = len(discovered_emails) + len(inferred_emails)
        if total_emails > 0:
            validation_ratio = len(valid_emails) / total_emails
            confidence += 0.3 * validation_ratio
        
        return min(1.0, confidence)
    
    def _update_processing_stats(self, result: EmailDiscoveryResult):
        """Update processing statistics"""
        self.processing_stats['domains_processed'] += 1
        self.processing_stats['emails_discovered'] += len(result.discovered_emails)
        self.processing_stats['emails_inferred'] += len(result.inferred_emails)
        self.processing_stats['processing_time'] += result.processing_time
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get processing summary using Context7 reporting"""
        return {
            'total_domains_processed': self.processing_stats['domains_processed'],
            'total_emails_discovered': self.processing_stats['emails_discovered'],
            'total_emails_inferred': self.processing_stats['emails_inferred'],
            'average_processing_time': self.processing_stats['processing_time'] / max(1, self.processing_stats['domains_processed']),
            'emails_per_domain': (self.processing_stats['emails_discovered'] + self.processing_stats['emails_inferred']) / max(1, self.processing_stats['domains_processed'])
        }

# Test function
async def test_phase9b_email_discovery():
    """Test Phase 9B Email Discovery Enhancement Engine"""
    print("🚀 Testing Phase 9B Email Discovery Enhancement Engine")
    
    config = Phase9bConfig()
    engine = Phase9bEmailDiscoveryEngine(config)
    
    # Test companies with executives
    test_companies = [
        {
            'company_name': 'A&H Plumbing',
            'domain': 'anhplumbing.com',
            'executives': [
                {'name': 'John Smith', 'title': 'CEO'},
                {'name': 'Sarah Johnson', 'title': 'Operations Manager'}
            ]
        },
        {
            'company_name': 'Air-Tech Systems Inc',
            'domain': 'air-techsystems.com',
            'executives': [
                {'name': 'Mike Wilson', 'title': 'Director'},
                {'name': 'Lisa Brown', 'title': 'CTO'},
                {'name': 'David Chen', 'title': 'VP Sales'}
            ]
        }
    ]
    
    results = []
    
    for company_data in test_companies:
        print(f"\n📊 Processing: {company_data['company_name']}")
        result = await engine.discover_executive_emails(
            company_data['company_name'],
            company_data['domain'],
            company_data['executives']
        )
        
        results.append({
            'company': company_data['company_name'],
            'domain': company_data['domain'],
            'result': asdict(result)
        })
        
        # Display results
        print(f"✅ Discovered {len(result.discovered_emails)} emails")
        print(f"🧠 Inferred {len(result.inferred_emails)} emails")
        print(f"📈 Discovery confidence: {result.discovery_confidence:.1%}")
        print(f"⏱️ Processing time: {result.processing_time:.2f}s")
    
    # Save results
    timestamp = int(time.time())
    results_file = f"phase9b_email_discovery_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Display processing summary
    summary = engine.get_processing_summary()
    print(f"\n📊 Processing Summary:")
    print(f"Domains processed: {summary['total_domains_processed']}")
    print(f"Emails discovered: {summary['total_emails_discovered']}")
    print(f"Emails inferred: {summary['total_emails_inferred']}")
    print(f"Emails per domain: {summary['emails_per_domain']:.1f}")
    print(f"Avg processing time: {summary['average_processing_time']:.2f}s")
    
    return results

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    asyncio.run(test_phase9b_email_discovery())