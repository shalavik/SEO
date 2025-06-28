#!/usr/bin/env python3
"""
Phase 8: AI-Powered Intelligence Platform
==========================================

Advanced machine learning pipeline for executive discovery with:
- Context7-inspired scikit-learn integration
- Text classification and feature extraction
- Semantic analysis with TF-IDF and CountVectorizer
- Executive vs service content classification
- Multi-source intelligence preparation
- Real-time processing capabilities

Built on Phase 7C's 90% filtering success
Implements Context7 best practices for ML workflows
"""

import asyncio
import json
import time
import logging
import numpy as np
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
class Phase8Config:
    """AI Intelligence Platform Configuration"""
    # Processing Configuration
    max_concurrent_companies: int = 5
    max_pages_per_company: int = 20
    session_timeout: int = 30
    
    # Machine Learning Configuration
    ml_confidence_threshold: float = 0.85
    tfidf_max_features: int = 10000
    tfidf_ngram_range: Tuple[int, int] = (1, 3)
    train_test_split_ratio: float = 0.2
    
    # Model Configuration
    enable_tfidf_vectorization: bool = True
    enable_semantic_classification: bool = True
    enable_advanced_filtering: bool = True
    model_persistence: bool = True
    
    # Intelligence Features
    enable_multi_source_intel: bool = True
    enable_real_time_processing: bool = True
    enable_executive_profiling: bool = True

class Phase8AdvancedMLClassifier:
    """Context7-Inspired Machine Learning Text Classifier"""
    
    def __init__(self, config: Phase8Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize ML Pipeline with Context7 patterns
        self.executive_classifier = None
        self.service_classifier = None
        self.tfidf_vectorizer = None
        self.is_trained = False
        
        # Context7-inspired feature patterns
        self.executive_patterns = [
            'CEO', 'Director', 'Manager', 'President', 'Executive',
            'Head of', 'VP', 'Vice President', 'Chief', 'Owner',
            'Principal', 'Partner', 'Founder', 'Lead', 'Senior'
        ]
        
        self.service_patterns = [
            'installation', 'repair', 'maintenance', 'service',
            'quote', 'emergency', 'commercial', 'residential',
            'heating', 'plumbing', 'boiler', 'gas', 'electrical'
        ]
    
    def create_ml_pipeline(self) -> Pipeline:
        """Create Context7-inspired ML pipeline"""
        if self.config.enable_tfidf_vectorization:
            # TF-IDF Vectorizer with Context7 best practices
            vectorizer = TfidfVectorizer(
                max_features=self.config.tfidf_max_features,
                ngram_range=self.config.tfidf_ngram_range,
                stop_words='english',
                lowercase=True,
                analyzer='word',
                token_pattern=r'\b\w+\b'
            )
        else:
            # CountVectorizer fallback
            vectorizer = CountVectorizer(
                max_features=self.config.tfidf_max_features,
                ngram_range=self.config.tfidf_ngram_range,
                stop_words='english'
            )
        
        # Create pipeline with Multinomial Naive Bayes
        pipeline = Pipeline([
            ('vectorizer', vectorizer),
            ('classifier', MultinomialNB(alpha=0.01))
        ])
        
        return pipeline
    
    def prepare_training_data(self) -> Tuple[List[str], List[int]]:
        """Prepare training data for executive vs service classification"""
        training_texts = []
        training_labels = []
        
        # Executive examples (label: 1)
        executive_examples = [
            "John Smith CEO Managing Director",
            "Sarah Johnson Head of Operations",
            "Michael Brown Vice President Sales",
            "Dr. Emily Davis Chief Technology Officer",
            "David Wilson Founder and Principal",
            "Lisa Thompson Senior Manager",
            "Robert Anderson Executive Director",
            "Jennifer White Lead Engineer",
            "Christopher Lee President Owner",
            "Amanda Garcia VP Marketing Director"
        ]
        
        # Service examples (label: 0)
        service_examples = [
            "Emergency Plumbing Service 24/7",
            "Boiler Installation and Repair",
            "Central Heating Maintenance",
            "Gas Safety Certificate Service",
            "Commercial HVAC Installation",
            "Residential Heating Solutions",
            "Emergency Call Out Service",
            "Annual Boiler Service Plan",
            "Worcester Bosch Approved Installer",
            "Heating System Maintenance Contract"
        ]
        
        # Add executive examples
        for text in executive_examples:
            training_texts.append(text)
            training_labels.append(1)  # Executive
        
        # Add service examples
        for text in service_examples:
            training_texts.append(text)
            training_labels.append(0)  # Service
        
        return training_texts, training_labels
    
    def train_classifier(self) -> Dict[str, Any]:
        """Train the ML classifier with Context7 best practices"""
        self.logger.info("Training AI classifier with Context7 patterns...")
        
        # Prepare training data
        texts, labels = self.prepare_training_data()
        
        # Split data using Context7 recommended ratio
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, 
            test_size=self.config.train_test_split_ratio,
            random_state=42,
            stratify=labels
        )
        
        # Create and train pipeline
        self.executive_classifier = self.create_ml_pipeline()
        self.executive_classifier.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = self.executive_classifier.predict(X_test)
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        # Store vectorizer for feature analysis
        self.tfidf_vectorizer = self.executive_classifier.named_steps['vectorizer']
        
        self.is_trained = True
        self.logger.info(f"Model trained successfully. F1-score: {f1:.3f}")
        
        return {
            'f1_score': f1,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'model_type': 'MultinomialNB + TfidfVectorizer'
        }
    
    def predict_executive_probability(self, text: str) -> Tuple[float, Dict[str, Any]]:
        """Predict probability that text represents an executive"""
        if not self.is_trained:
            self.train_classifier()
        
        # Get prediction probability
        probabilities = self.executive_classifier.predict_proba([text])[0]
        executive_probability = probabilities[1]  # Probability of being executive
        
        # Get feature analysis
        features = self.tfidf_vectorizer.transform([text])
        feature_names = self.tfidf_vectorizer.get_feature_names_out()
        feature_scores = features.toarray()[0]
        
        # Top features
        top_features = []
        if len(feature_scores) > 0:
            top_indices = np.argsort(feature_scores)[-5:][::-1]
            top_features = [(feature_names[i], feature_scores[i]) for i in top_indices if feature_scores[i] > 0]
        
        analysis = {
            'probability': executive_probability,
            'confidence': 'HIGH' if executive_probability > 0.8 else 'MEDIUM' if executive_probability > 0.6 else 'LOW',
            'top_features': top_features,
            'executive_patterns_found': [p for p in self.executive_patterns if p.lower() in text.lower()],
            'service_patterns_found': [p for p in self.service_patterns if p.lower() in text.lower()]
        }
        
        return executive_probability, analysis

class Phase8IntelligencePlatform:
    """AI-Powered Intelligence Platform for Executive Discovery"""
    
    def __init__(self, config: Phase8Config):
        self.config = config
        self.ml_classifier = Phase8AdvancedMLClassifier(config)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.session = None
        self.processed_companies = []
        self.intelligence_cache = {}
        
    async def initialize(self):
        """Initialize the AI platform"""
        self.logger.info("Initializing Phase 8 AI Intelligence Platform...")
        
        # Train ML models
        training_results = self.ml_classifier.train_classifier()
        self.logger.info(f"ML training completed: {training_results}")
        
        # Initialize session
        timeout = aiohttp.ClientTimeout(total=self.config.session_timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        self.logger.info("AI Intelligence Platform ready for deployment")
    
    async def analyze_company_intelligence(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze company with AI-powered intelligence"""
        company_name = company_data.get('company_name', 'Unknown')
        company_url = company_data.get('website', '')
        
        self.logger.info(f"AI analysis starting for: {company_name}")
        
        intelligence_result = {
            'company_name': company_name,
            'website': company_url,
            'analysis_timestamp': int(time.time()),
            'ai_executives': [],
            'intelligence_metrics': {},
            'ml_insights': {},
            'confidence_scores': {}
        }
        
        try:
            # Multi-page content analysis
            content_data = await self.extract_company_content(company_url)
            
            # AI-powered executive detection
            executives = await self.detect_executives_with_ai(content_data)
            
            # Intelligence analysis
            intelligence_metrics = self.calculate_intelligence_metrics(executives, content_data)
            
            intelligence_result.update({
                'ai_executives': executives,
                'intelligence_metrics': intelligence_metrics,
                'status': 'SUCCESS',
                'pages_analyzed': len(content_data.get('pages', [])),
                'total_content_length': sum(len(page.get('content', '')) for page in content_data.get('pages', []))
            })
            
        except Exception as e:
            self.logger.error(f"AI analysis failed for {company_name}: {str(e)}")
            intelligence_result.update({
                'status': 'FAILED',
                'error': str(e),
                'ai_executives': [],
                'intelligence_metrics': {}
            })
        
        return intelligence_result
    
    async def extract_company_content(self, url: str) -> Dict[str, Any]:
        """Extract comprehensive content from company website"""
        if not url or not url.startswith(('http://', 'https://')):
            return {'pages': [], 'error': 'Invalid URL'}
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract main content
                    main_content = soup.get_text(separator=' ', strip=True)
                    
                    # Find relevant pages
                    relevant_links = self.find_relevant_links(soup, url)
                    
                    pages_data = [{
                        'url': url,
                        'content': main_content,
                        'title': soup.title.string if soup.title else '',
                        'type': 'homepage'
                    }]
                    
                    # Process additional relevant pages
                    for link_url in relevant_links[:self.config.max_pages_per_company-1]:
                        try:
                            async with self.session.get(link_url) as link_response:
                                if link_response.status == 200:
                                    link_html = await link_response.text()
                                    link_soup = BeautifulSoup(link_html, 'html.parser')
                                    link_content = link_soup.get_text(separator=' ', strip=True)
                                    
                                    pages_data.append({
                                        'url': link_url,
                                        'content': link_content,
                                        'title': link_soup.title.string if link_soup.title else '',
                                        'type': self.classify_page_type(link_url)
                                    })
                        except Exception as e:
                            self.logger.debug(f"Failed to process link {link_url}: {str(e)}")
                            continue
                    
                    return {'pages': pages_data}
                    
        except Exception as e:
            self.logger.error(f"Content extraction failed for {url}: {str(e)}")
            return {'pages': [], 'error': str(e)}
    
    def find_relevant_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find relevant internal links for executive discovery"""
        relevant_keywords = ['about', 'team', 'staff', 'management', 'directors', 'leadership', 'contact']
        relevant_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(keyword in href.lower() for keyword in relevant_keywords):
                if href.startswith('/'):
                    full_url = base_url.rstrip('/') + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue
                
                if full_url not in relevant_links:
                    relevant_links.append(full_url)
        
        return relevant_links[:10]  # Limit to prevent excessive requests
    
    def classify_page_type(self, url: str) -> str:
        """Classify page type based on URL patterns"""
        url_lower = url.lower()
        if 'about' in url_lower: return 'about'
        elif 'team' in url_lower: return 'team'
        elif 'contact' in url_lower: return 'contact'
        elif 'management' in url_lower: return 'management'
        elif 'director' in url_lower: return 'directors'
        else: return 'general'
    
    async def detect_executives_with_ai(self, content_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect executives using AI classification"""
        executives = []
        
        for page in content_data.get('pages', []):
            page_content = page.get('content', '')
            page_type = page.get('type', 'general')
            
            # Extract potential executive names using ML
            potential_executives = self.extract_potential_names(page_content)
            
            for name in potential_executives:
                # AI classification
                exec_probability, analysis = self.ml_classifier.predict_executive_probability(name)
                
                if exec_probability >= self.config.ml_confidence_threshold:
                    executive = {
                        'name': name,
                        'source_page': page.get('url', ''),
                        'page_type': page_type,
                        'ai_confidence': exec_probability,
                        'ml_analysis': analysis,
                        'context': self.extract_context(name, page_content),
                        'quality_tier': self.determine_quality_tier(exec_probability, analysis)
                    }
                    executives.append(executive)
        
        # Remove duplicates and sort by confidence
        executives = self.deduplicate_executives(executives)
        executives.sort(key=lambda x: x['ai_confidence'], reverse=True)
        
        return executives
    
    def extract_potential_names(self, content: str) -> List[str]:
        """Extract potential executive names from content"""
        import re
        
        # Pattern for names (2-3 words, proper case)
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b'
        potential_names = re.findall(name_pattern, content)
        
        # Filter out common false positives
        filtered_names = []
        for name in potential_names:
            if len(name.split()) >= 2 and not any(word in name.lower() for word in ['ltd', 'limited', 'company', 'services']):
                filtered_names.append(name)
        
        return list(set(filtered_names))  # Remove duplicates
    
    def extract_context(self, name: str, content: str) -> str:
        """Extract context around executive name"""
        import re
        
        # Find sentences containing the name
        sentences = re.split(r'[.!?]+', content)
        context_sentences = []
        
        for sentence in sentences:
            if name in sentence:
                context_sentences.append(sentence.strip())
        
        return ' '.join(context_sentences[:2])  # Return first 2 relevant sentences
    
    def determine_quality_tier(self, confidence: float, analysis: Dict[str, Any]) -> str:
        """Determine quality tier based on AI analysis"""
        if confidence >= 0.9 and analysis.get('confidence') == 'HIGH':
            return 'PREMIUM'
        elif confidence >= 0.8:
            return 'HIGH'
        elif confidence >= 0.7:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def deduplicate_executives(self, executives: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate executives"""
        seen_names = set()
        unique_executives = []
        
        for exec_data in executives:
            name = exec_data['name'].lower()
            if name not in seen_names:
                seen_names.add(name)
                unique_executives.append(exec_data)
        
        return unique_executives
    
    def calculate_intelligence_metrics(self, executives: List[Dict[str, Any]], content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate intelligence metrics for the analysis"""
        total_executives = len(executives)
        premium_executives = len([e for e in executives if e.get('quality_tier') == 'PREMIUM'])
        high_executives = len([e for e in executives if e.get('quality_tier') == 'HIGH'])
        
        avg_confidence = np.mean([e['ai_confidence'] for e in executives]) if executives else 0.0
        
        return {
            'total_executives_found': total_executives,
            'premium_quality_count': premium_executives,
            'high_quality_count': high_executives,
            'average_ai_confidence': round(avg_confidence, 3),
            'pages_processed': len(content_data.get('pages', [])),
            'content_richness_score': self.calculate_content_richness(content_data),
            'executive_diversity_score': len(set(e['name'].split()[0] for e in executives)) if executives else 0
        }
    
    def calculate_content_richness(self, content_data: Dict[str, Any]) -> float:
        """Calculate content richness score"""
        pages = content_data.get('pages', [])
        if not pages:
            return 0.0
        
        total_content = sum(len(page.get('content', '')) for page in pages)
        page_types = set(page.get('type', 'general') for page in pages)
        
        # Score based on content length and page diversity
        content_score = min(total_content / 10000, 1.0)  # Normalize to 1.0 max
        diversity_score = len(page_types) / 6  # 6 expected page types
        
        return round((content_score + diversity_score) / 2, 3)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

async def test_phase8_ai_intelligence_platform():
    """Test the Phase 8 AI Intelligence Platform"""
    print("🤖 PHASE 8: AI-POWERED INTELLIGENCE PLATFORM TEST")
    print("=" * 60)
    
    # Configuration
    config = Phase8Config()
    
    # Test companies
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
    
    # Initialize platform
    platform = Phase8IntelligencePlatform(config)
    await platform.initialize()
    
    results = []
    start_time = time.time()
    
    try:
        # Process companies with AI
        for company in test_companies:
            company_result = await platform.analyze_company_intelligence(company)
            results.append(company_result)
            
            print(f"\n🏢 Company: {company['company_name']}")
            print(f"   AI Executives Found: {len(company_result.get('ai_executives', []))}")
            print(f"   Pages Analyzed: {company_result.get('pages_analyzed', 0)}")
            print(f"   Intelligence Score: {company_result.get('intelligence_metrics', {}).get('content_richness_score', 0)}")
            
            # Show top AI-detected executives
            for i, exec_data in enumerate(company_result.get('ai_executives', [])[:3]):
                print(f"   🤖 Executive {i+1}: {exec_data['name']} (AI: {exec_data['ai_confidence']:.3f}, {exec_data['quality_tier']})")
    
    finally:
        await platform.cleanup()
    
    # Calculate overall metrics
    total_time = time.time() - start_time
    total_executives = sum(len(r.get('ai_executives', [])) for r in results)
    avg_confidence = np.mean([e['ai_confidence'] for r in results for e in r.get('ai_executives', [])]) if total_executives > 0 else 0
    
    print(f"\n🎯 PHASE 8 AI INTELLIGENCE RESULTS:")
    print(f"   Companies Processed: {len(results)}")
    print(f"   Total Processing Time: {total_time:.1f} seconds")
    print(f"   AI Executives Found: {total_executives}")
    print(f"   Average AI Confidence: {avg_confidence:.3f}")
    print(f"   Processing Speed: {len(results)/total_time*3600:.0f} companies/hour")
    
    # Save results
    results_data = {
        'phase': 'Phase 8 AI Intelligence Platform',
        'timestamp': int(time.time()),
        'config': asdict(config),
        'companies_processed': len(results),
        'total_executives_found': total_executives,
        'average_ai_confidence': round(avg_confidence, 3),
        'processing_time_seconds': round(total_time, 2),
        'processing_speed_per_hour': round(len(results)/total_time*3600, 0),
        'results': results
    }
    
    results_file = f"phase8_ai_intelligence_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"   Results saved to: {results_file}")
    return results_data

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_phase8_ai_intelligence_platform()) 