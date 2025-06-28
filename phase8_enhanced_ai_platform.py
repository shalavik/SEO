#!/usr/bin/env python3
"""
Phase 8: Enhanced AI-Powered Intelligence Platform
==================================================

Improved AI executive discovery with:
- Enhanced name extraction patterns
- Adjusted ML confidence thresholds
- Better Context7-inspired feature engineering
- Refined TF-IDF processing
- Improved real-world performance
- Advanced semantic analysis

Builds on Phase 8 foundation with practical improvements
"""

import asyncio
import json
import time
import logging
import numpy as np
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import aiohttp
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
from sklearn.preprocessing import StandardScaler
import pickle

@dataclass
class Phase8EnhancedConfig:
    """Enhanced AI Intelligence Platform Configuration"""
    # Processing Configuration
    max_concurrent_companies: int = 3
    max_pages_per_company: int = 15
    session_timeout: int = 25
    
    # Enhanced ML Configuration
    ml_confidence_threshold: float = 0.65  # Lowered for better recall
    tfidf_max_features: int = 5000
    tfidf_ngram_range: Tuple[int, int] = (1, 2)  # Simplified for better performance
    train_test_split_ratio: float = 0.25
    
    # Model Configuration
    enable_tfidf_vectorization: bool = True
    enable_enhanced_name_extraction: bool = True
    enable_context_analysis: bool = True
    enable_multi_pattern_matching: bool = True
    
    # Intelligence Features
    executive_name_min_confidence: float = 0.4  # Lower threshold for name extraction
    context_window_size: int = 50  # Words around names for context

class Phase8EnhancedNameExtractor:
    """Enhanced name extraction with Context7-inspired patterns"""
    
    def __init__(self, config: Phase8EnhancedConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Enhanced name patterns with Context7 inspiration
        self.name_patterns = [
            # Standard name patterns
            r'\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b',  # John Smith
            r'\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b',  # John Peter Smith
            r'\bMr\.?\s+[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b',  # Mr. John Smith
            r'\bMs\.?\s+[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b',  # Ms. Jane Smith
            r'\bDr\.?\s+[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b',  # Dr. Mike Johnson
        ]
        
        # Executive context indicators
        self.executive_contexts = [
            'director', 'manager', 'ceo', 'president', 'vice president', 'vp',
            'head of', 'chief', 'executive', 'founder', 'owner', 'principal',
            'partner', 'lead', 'senior', 'coordinator', 'supervisor', 'administrator'
        ]
        
        # Service content indicators (to filter out)
        self.service_indicators = [
            'service', 'installation', 'repair', 'maintenance', 'emergency',
            'quote', 'estimate', 'contact us', 'call now', 'available',
            'specialist', 'expert', 'certified', 'approved', 'qualified'
        ]
    
    def extract_potential_names(self, content: str) -> List[Dict[str, Any]]:
        """Extract potential names with enhanced patterns and context"""
        potential_names = []
        
        # Clean content
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        
        for pattern in self.name_patterns:
            matches = re.finditer(pattern, content)
            
            for match in matches:
                name = match.group().strip()
                start_pos = match.start()
                end_pos = match.end()
                
                # Extract context around the name
                context_start = max(0, start_pos - self.config.context_window_size * 6)  # Approximate word size
                context_end = min(len(content), end_pos + self.config.context_window_size * 6)
                context = content[context_start:context_end]
                
                # Calculate name confidence based on patterns
                confidence = self.calculate_name_confidence(name, context)
                
                if confidence >= self.config.executive_name_min_confidence:
                    potential_names.append({
                        'name': name,
                        'context': context,
                        'confidence': confidence,
                        'position': start_pos,
                        'pattern_matched': pattern
                    })
        
        # Remove duplicates and sort by confidence
        unique_names = self.deduplicate_names(potential_names)
        unique_names.sort(key=lambda x: x['confidence'], reverse=True)
        
        return unique_names
    
    def calculate_name_confidence(self, name: str, context: str) -> float:
        """Calculate confidence score for extracted name"""
        confidence = 0.5  # Base confidence
        
        name_lower = name.lower()
        context_lower = context.lower()
        
        # Boost confidence for executive contexts
        for exec_context in self.executive_contexts:
            if exec_context in context_lower:
                confidence += 0.2
                break
        
        # Reduce confidence for service contexts
        service_penalty = 0
        for service in self.service_indicators:
            if service in context_lower:
                service_penalty += 0.1
        
        confidence -= min(service_penalty, 0.3)  # Cap penalty
        
        # Boost for proper name patterns
        if len(name.split()) == 2:  # First Last
            confidence += 0.1
        elif len(name.split()) == 3:  # First Middle Last or Title First Last
            confidence += 0.05
        
        # Reduce for too short or too long names
        if len(name) < 6 or len(name) > 30:
            confidence -= 0.1
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))
    
    def deduplicate_names(self, names: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate names"""
        seen_names = set()
        unique_names = []
        
        for name_data in names:
            name_normalized = name_data['name'].lower().strip()
            if name_normalized not in seen_names:
                seen_names.add(name_normalized)
                unique_names.append(name_data)
        
        return unique_names

class Phase8EnhancedMLClassifier:
    """Enhanced ML classifier with improved training data"""
    
    def __init__(self, config: Phase8EnhancedConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.executive_classifier = None
        self.tfidf_vectorizer = None
        self.is_trained = False
        
    def create_enhanced_training_data(self) -> Tuple[List[str], List[int]]:
        """Create enhanced training data with more examples"""
        training_texts = []
        training_labels = []
        
        # Expanded executive examples (label: 1)
        executive_examples = [
            "John Smith CEO Managing Director Operations",
            "Sarah Johnson Head of Operations Business Development",
            "Michael Brown Vice President Sales Marketing",
            "Dr. Emily Davis Chief Technology Officer Engineering",
            "David Wilson Founder Principal Partner",
            "Lisa Thompson Senior Manager Administration",
            "Robert Anderson Executive Director Finance",
            "Jennifer White Lead Engineer Technical Manager",
            "Christopher Lee President Owner Founder",
            "Amanda Garcia VP Marketing Director Communications",
            "Mark Robinson General Manager Operations",
            "Susan Davis Director Human Resources",
            "James Wilson Senior Vice President",
            "Maria Rodriguez Executive Assistant Manager",
            "Thomas Anderson Chief Executive Officer",
            "Patricia Lee Managing Director Finance",
            "Richard Johnson Head of Engineering",
            "Elizabeth Brown VP Operations Manager",
            "William Garcia Director Business Development",
            "Linda Martinez Senior Manager Customer Service"
        ]
        
        # Expanded service examples (label: 0)
        service_examples = [
            "Emergency Plumbing Service 24/7 Available Now",
            "Boiler Installation and Repair Specialists Expert",
            "Central Heating Maintenance Annual Service Plan",
            "Gas Safety Certificate Inspection Service Available",
            "Commercial HVAC Installation Experts Certified",
            "Residential Heating Solutions Provider Local",
            "Emergency Call Out Service Available Immediate",
            "Annual Boiler Service Plan Maintenance Contract",
            "Worcester Bosch Approved Installer Certified",
            "Heating System Maintenance Contract Service",
            "Professional Plumbing Services Expert Installation",
            "Emergency Heating Repair Service 24 Hour",
            "Boiler Replacement Service Specialist Installation",
            "Gas Appliance Service Maintenance Repair",
            "Central Heating Installation Expert Service",
            "Commercial Plumbing Solutions Professional Service",
            "Residential HVAC Service Repair Installation",
            "Emergency Gas Service Call Out Available",
            "Heating Maintenance Service Annual Contract",
            "Professional Installation Service Expert Technician"
        ]
        
        # Add examples to training data
        for text in executive_examples:
            training_texts.append(text)
            training_labels.append(1)  # Executive
        
        for text in service_examples:
            training_texts.append(text)
            training_labels.append(0)  # Service
        
        return training_texts, training_labels
    
    def create_enhanced_pipeline(self) -> Pipeline:
        """Create enhanced ML pipeline with optimized parameters"""
        vectorizer = TfidfVectorizer(
            max_features=self.config.tfidf_max_features,
            ngram_range=self.config.tfidf_ngram_range,
            stop_words='english',
            lowercase=True,
            analyzer='word',
            token_pattern=r'\b\w+\b',
            min_df=1,  # Include rare terms
            max_df=0.95  # Exclude very common terms
        )
        
        # Use Logistic Regression for better probability estimates
        classifier = LogisticRegression(
            random_state=42,
            max_iter=1000,
            class_weight='balanced'  # Handle class imbalance
        )
        
        pipeline = Pipeline([
            ('vectorizer', vectorizer),
            ('classifier', classifier)
        ])
        
        return pipeline
    
    def train_enhanced_classifier(self) -> Dict[str, Any]:
        """Train enhanced classifier with improved data"""
        self.logger.info("Training enhanced AI classifier...")
        
        texts, labels = self.create_enhanced_training_data()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels,
            test_size=self.config.train_test_split_ratio,
            random_state=42,
            stratify=labels
        )
        
        # Train pipeline
        self.executive_classifier = self.create_enhanced_pipeline()
        self.executive_classifier.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.executive_classifier.predict(X_test)
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        self.tfidf_vectorizer = self.executive_classifier.named_steps['vectorizer']
        self.is_trained = True
        
        self.logger.info(f"Enhanced model trained. F1-score: {f1:.3f}")
        
        return {
            'f1_score': f1,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'model_type': 'LogisticRegression + TfidfVectorizer Enhanced'
        }
    
    def predict_enhanced_probability(self, text: str, context: str = "") -> Tuple[float, Dict[str, Any]]:
        """Enhanced prediction with context analysis"""
        if not self.is_trained:
            self.train_enhanced_classifier()
        
        # Combine text with context for better prediction
        combined_text = f"{text} {context}".strip()
        
        # Get prediction
        probabilities = self.executive_classifier.predict_proba([combined_text])[0]
        executive_probability = probabilities[1]
        
        # Enhanced analysis
        analysis = {
            'probability': executive_probability,
            'confidence': self.get_confidence_level(executive_probability),
            'combined_text_used': combined_text,
            'text_length': len(combined_text),
            'prediction_method': 'enhanced_ml'
        }
        
        return executive_probability, analysis
    
    def get_confidence_level(self, probability: float) -> str:
        """Get confidence level based on probability"""
        if probability >= 0.8:
            return 'HIGH'
        elif probability >= 0.6:
            return 'MEDIUM'
        else:
            return 'LOW'

class Phase8EnhancedIntelligencePlatform:
    """Enhanced AI Intelligence Platform"""
    
    def __init__(self, config: Phase8EnhancedConfig):
        self.config = config
        self.name_extractor = Phase8EnhancedNameExtractor(config)
        self.ml_classifier = Phase8EnhancedMLClassifier(config)
        self.logger = logging.getLogger(__name__)
        
        self.session = None
        self.processed_companies = []
    
    async def initialize(self):
        """Initialize enhanced platform"""
        self.logger.info("Initializing Phase 8 Enhanced AI Intelligence Platform...")
        
        # Train enhanced ML model
        training_results = self.ml_classifier.train_enhanced_classifier()
        self.logger.info(f"Enhanced ML training: {training_results}")
        
        # Initialize session
        timeout = aiohttp.ClientTimeout(total=self.config.session_timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        self.logger.info("Enhanced AI Intelligence Platform ready")
    
    async def analyze_company_enhanced(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced company analysis with improved name extraction"""
        company_name = company_data.get('company_name', 'Unknown')
        company_url = company_data.get('website', '')
        
        self.logger.info(f"Enhanced AI analysis for: {company_name}")
        
        result = {
            'company_name': company_name,
            'website': company_url,
            'analysis_timestamp': int(time.time()),
            'enhanced_executives': [],
            'extraction_metrics': {},
            'ai_insights': {},
            'processing_details': {}
        }
        
        try:
            # Extract content
            content_data = await self.extract_enhanced_content(company_url)
            
            # Enhanced executive detection
            executives = await self.detect_executives_enhanced(content_data)
            
            # Calculate metrics
            metrics = self.calculate_enhanced_metrics(executives, content_data)
            
            result.update({
                'enhanced_executives': executives,
                'extraction_metrics': metrics,
                'status': 'SUCCESS',
                'pages_processed': len(content_data.get('pages', [])),
                'total_names_extracted': sum(len(page.get('potential_names', [])) for page in content_data.get('pages', []))
            })
            
        except Exception as e:
            self.logger.error(f"Enhanced analysis failed for {company_name}: {str(e)}")
            result.update({
                'status': 'FAILED',
                'error': str(e),
                'enhanced_executives': []
            })
        
        return result
    
    async def extract_enhanced_content(self, url: str) -> Dict[str, Any]:
        """Enhanced content extraction with name detection"""
        if not url or not url.startswith(('http://', 'https://')):
            return {'pages': [], 'error': 'Invalid URL'}
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract main content
                    main_content = soup.get_text(separator=' ', strip=True)
                    
                    # Extract potential names from main page
                    potential_names = self.name_extractor.extract_potential_names(main_content)
                    
                    pages_data = [{
                        'url': url,
                        'content': main_content,
                        'title': soup.title.string if soup.title else '',
                        'type': 'homepage',
                        'potential_names': potential_names
                    }]
                    
                    # Process additional pages if main page has few names
                    if len(potential_names) < 3:
                        relevant_links = self.find_enhanced_links(soup, url)
                        
                        for link_url in relevant_links[:5]:  # Process fewer additional pages
                            try:
                                async with self.session.get(link_url) as link_response:
                                    if link_response.status == 200:
                                        link_html = await link_response.text()
                                        link_soup = BeautifulSoup(link_html, 'html.parser')
                                        link_content = link_soup.get_text(separator=' ', strip=True)
                                        
                                        link_names = self.name_extractor.extract_potential_names(link_content)
                                        
                                        pages_data.append({
                                            'url': link_url,
                                            'content': link_content,
                                            'title': link_soup.title.string if link_soup.title else '',
                                            'type': self.classify_page_type(link_url),
                                            'potential_names': link_names
                                        })
                            except Exception as e:
                                self.logger.debug(f"Failed to process link {link_url}: {str(e)}")
                                continue
                    
                    return {'pages': pages_data}
                    
        except Exception as e:
            self.logger.error(f"Enhanced content extraction failed for {url}: {str(e)}")
            return {'pages': [], 'error': str(e)}
    
    def find_enhanced_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find enhanced relevant links"""
        high_priority_keywords = ['about', 'team', 'staff', 'management', 'directors']
        medium_priority_keywords = ['contact', 'leadership', 'company']
        
        high_priority_links = []
        medium_priority_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            href_lower = href.lower()
            
            # Process URL
            if href.startswith('/'):
                full_url = base_url.rstrip('/') + href
            elif href.startswith('http'):
                full_url = href
            else:
                continue
            
            # Prioritize links
            if any(keyword in href_lower for keyword in high_priority_keywords):
                if full_url not in high_priority_links:
                    high_priority_links.append(full_url)
            elif any(keyword in href_lower for keyword in medium_priority_keywords):
                if full_url not in medium_priority_links:
                    medium_priority_links.append(full_url)
        
        # Return high priority first
        return high_priority_links[:3] + medium_priority_links[:2]
    
    def classify_page_type(self, url: str) -> str:
        """Enhanced page type classification"""
        url_lower = url.lower()
        
        type_mapping = {
            'about': ['about', 'company', 'history'],
            'team': ['team', 'staff', 'people'],
            'management': ['management', 'director', 'executive', 'leadership'],
            'contact': ['contact', 'reach', 'touch']
        }
        
        for page_type, keywords in type_mapping.items():
            if any(keyword in url_lower for keyword in keywords):
                return page_type
        
        return 'general'
    
    async def detect_executives_enhanced(self, content_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced executive detection with improved ML"""
        executives = []
        
        for page in content_data.get('pages', []):
            page_names = page.get('potential_names', [])
            page_type = page.get('type', 'general')
            page_content = page.get('content', '')
            
            for name_data in page_names:
                name = name_data['name']
                context = name_data['context']
                extraction_confidence = name_data['confidence']
                
                # Get ML prediction
                ml_probability, ml_analysis = self.ml_classifier.predict_enhanced_probability(name, context)
                
                # Combined confidence score
                combined_confidence = (extraction_confidence * 0.4) + (ml_probability * 0.6)
                
                if combined_confidence >= self.config.ml_confidence_threshold:
                    executive = {
                        'name': name,
                        'source_page': page.get('url', ''),
                        'page_type': page_type,
                        'extraction_confidence': extraction_confidence,
                        'ml_probability': ml_probability,
                        'combined_confidence': combined_confidence,
                        'context_snippet': context[:200],  # First 200 chars
                        'ml_analysis': ml_analysis,
                        'quality_tier': self.determine_enhanced_quality_tier(combined_confidence),
                        'extraction_method': 'enhanced_ai'
                    }
                    executives.append(executive)
        
        # Deduplicate and sort
        executives = self.deduplicate_enhanced_executives(executives)
        executives.sort(key=lambda x: x['combined_confidence'], reverse=True)
        
        return executives
    
    def determine_enhanced_quality_tier(self, confidence: float) -> str:
        """Enhanced quality tier determination"""
        if confidence >= 0.85:
            return 'PREMIUM'
        elif confidence >= 0.75:
            return 'HIGH'
        elif confidence >= 0.65:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def deduplicate_enhanced_executives(self, executives: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhanced deduplication"""
        seen_names = set()
        unique_executives = []
        
        for exec_data in executives:
            name_key = exec_data['name'].lower().strip()
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_executives.append(exec_data)
        
        return unique_executives
    
    def calculate_enhanced_metrics(self, executives: List[Dict[str, Any]], content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate enhanced metrics"""
        total_executives = len(executives)
        avg_combined_confidence = np.mean([e['combined_confidence'] for e in executives]) if executives else 0.0
        
        quality_distribution = {}
        for tier in ['PREMIUM', 'HIGH', 'MEDIUM', 'LOW']:
            quality_distribution[tier] = len([e for e in executives if e.get('quality_tier') == tier])
        
        return {
            'total_executives_found': total_executives,
            'average_combined_confidence': round(avg_combined_confidence, 3),
            'quality_distribution': quality_distribution,
            'pages_with_names': len([p for p in content_data.get('pages', []) if p.get('potential_names')]),
            'total_potential_names': sum(len(p.get('potential_names', [])) for p in content_data.get('pages', [])),
            'extraction_success_rate': round(total_executives / max(1, sum(len(p.get('potential_names', [])) for p in content_data.get('pages', []))), 3)
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

async def test_phase8_enhanced_platform():
    """Test the enhanced Phase 8 platform"""
    print("🚀 PHASE 8: ENHANCED AI-POWERED INTELLIGENCE PLATFORM TEST")
    print("=" * 70)
    
    config = Phase8EnhancedConfig()
    
    test_companies = [
        {
            'company_name': 'Celm Engineering',
            'website': 'https://celmeng.co.uk'
        },
        {
            'company_name': 'MS Heating & Plumbing',
            'website': 'https://msheatingandplumbing.co.uk'
        }
    ]
    
    platform = Phase8EnhancedIntelligencePlatform(config)
    await platform.initialize()
    
    results = []
    start_time = time.time()
    
    try:
        for company in test_companies:
            result = await platform.analyze_company_enhanced(company)
            results.append(result)
            
            print(f"\n🏢 Company: {company['company_name']}")
            print(f"   Enhanced Executives Found: {len(result.get('enhanced_executives', []))}")
            print(f"   Pages Processed: {result.get('pages_processed', 0)}")
            print(f"   Names Extracted: {result.get('total_names_extracted', 0)}")
            
            for i, exec_data in enumerate(result.get('enhanced_executives', [])[:5]):
                conf = exec_data['combined_confidence']
                tier = exec_data['quality_tier']
                print(f"   🤖 Executive {i+1}: {exec_data['name']} (Conf: {conf:.3f}, {tier})")
    
    finally:
        await platform.cleanup()
    
    total_time = time.time() - start_time
    total_executives = sum(len(r.get('enhanced_executives', [])) for r in results)
    
    print(f"\n🎯 ENHANCED PHASE 8 RESULTS:")
    print(f"   Companies Processed: {len(results)}")
    print(f"   Total Processing Time: {total_time:.1f} seconds")
    print(f"   Enhanced Executives Found: {total_executives}")
    print(f"   Processing Speed: {len(results)/total_time*3600:.0f} companies/hour")
    
    # Save results
    results_data = {
        'phase': 'Phase 8 Enhanced AI Intelligence Platform',
        'timestamp': int(time.time()),
        'config': asdict(config),
        'companies_processed': len(results),
        'total_executives_found': total_executives,
        'processing_time_seconds': round(total_time, 2),
        'processing_speed_per_hour': round(len(results)/total_time*3600, 0),
        'results': results
    }
    
    results_file = f"phase8_enhanced_ai_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"   Results saved to: {results_file}")
    return results_data

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_phase8_enhanced_platform()) 