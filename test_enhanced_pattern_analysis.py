#!/usr/bin/env python3
"""
Enhanced Pattern Analysis for Phase 4A
Analyzing successful extractions to improve success rate
"""

import asyncio
import sys
import os
import logging
from bs4 import BeautifulSoup
import requests

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from src.seo_leads.extractors.advanced_content_extractor import AdvancedContentExtractor
from src.seo_leads.ai.enhanced_executive_classifier import EnhancedExecutiveClassifier

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def analyze_successful_site():
    """Analyze the successful site to understand patterns"""
    print("🔍 ANALYZING SUCCESSFUL EXTRACTION PATTERNS")
    print("="*60)
    
    # Hancox Gas and Plumbing was successful
    company = "Hancox Gas and Plumbing"
    url = "https://hancoxgasandplumbing.co.uk"
    
    try:
        # Fetch content
        response = requests.get(url, timeout=30)
        html_content = response.text
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        
        print(f"📄 Content Analysis for {company}:")
        print(f"   HTML Length: {len(html_content):,} characters")
        print(f"   Text Length: {len(text_content):,} characters")
        
        # Analyze with advanced extractor
        extractor = AdvancedContentExtractor()
        extracted_executives = extractor.extract_executives_advanced(html_content, url, company)
        
        print(f"\n🏗️ Advanced Extractor Results: {len(extracted_executives)} executives")
        for i, exec in enumerate(extracted_executives, 1):
            print(f"   {i}. {exec.first_name} {exec.last_name}")
            print(f"      Title: {exec.title}")
            print(f"      Method: {exec.extraction_method}")
            print(f"      Confidence: {exec.confidence_score:.2f}")
            print(f"      Context: {exec.context[:100]}...")
        
        # Analyze with ML classifier
        classifier = EnhancedExecutiveClassifier()
        ml_candidates = classifier.classify_executives(text_content, company)
        
        print(f"\n🧠 ML Classifier Results: {len(ml_candidates)} candidates")
        for i, candidate in enumerate(ml_candidates, 1):
            print(f"   {i}. {candidate.first_name} {candidate.last_name}")
            print(f"      Title: {candidate.title}")
            print(f"      Method: {candidate.extraction_method}")
            print(f"      Confidence: {candidate.confidence_score:.2f}")
            print(f"      Person Prob: {candidate.person_probability:.2f}")
            print(f"      Exec Prob: {candidate.executive_probability:.2f}")
            print(f"      Features: {list(candidate.ml_features.keys())}")
        
        # Look for key text patterns
        print(f"\n📝 Key Text Patterns Found:")
        
        # Look for name patterns
        import re
        name_patterns = [
            r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b',  # First Last
            r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+),\s*([^.]+)',  # Name, Title
            r'([A-Z][a-z]+)\s+([A-Z][a-z]+)\s*[-–]\s*([^.]+)'  # Name - Title
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                print(f"   Pattern '{pattern}': {len(matches)} matches")
                for match in matches[:3]:  # Show first 3
                    print(f"      {match}")
        
        # Look for executive keywords
        executive_keywords = ['director', 'manager', 'owner', 'ceo', 'founder', 'proprietor', 'partner']
        found_keywords = []
        for keyword in executive_keywords:
            if keyword in text_content.lower():
                found_keywords.append(keyword)
        
        print(f"   Executive Keywords: {found_keywords}")
        
        # Look for contact patterns
        contact_patterns = [
            r'contact\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'speak\s+to\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'ask\s+for\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
        ]
        
        for pattern in contact_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                print(f"   Contact Pattern '{pattern}': {matches}")
        
        # Analyze specific sections
        print(f"\n📋 Section Analysis:")
        
        # Look for team/about sections
        team_sections = soup.find_all(['div', 'section'], class_=re.compile(r'(team|about|staff)', re.I))
        if team_sections:
            print(f"   Team/About sections: {len(team_sections)}")
            for section in team_sections[:2]:
                section_text = section.get_text(strip=True)[:200]
                print(f"      {section_text}...")
        
        # Look for specific text that led to successful extraction
        david_context = []
        for sentence in text_content.split('.'):
            if 'david' in sentence.lower() or 'hancox' in sentence.lower():
                david_context.append(sentence.strip())
        
        print(f"\n🎯 'David Hancox' Context Analysis:")
        for context in david_context[:5]:
            print(f"   • {context}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

async def test_pattern_improvements():
    """Test pattern improvements on other sites"""
    print("\n🧪 TESTING PATTERN IMPROVEMENTS")
    print("="*60)
    
    test_sites = [
        ("247 Plumbing and Gas", "https://247plumbingandgas.co.uk"),
        ("Emergency Plumber Services", "https://emergencyplumberservices.co.uk")
    ]
    
    classifier = EnhancedExecutiveClassifier()
    
    for company, url in test_sites:
        print(f"\n🏢 Testing: {company}")
        try:
            response = requests.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Try with lower confidence threshold
            candidates = classifier.classify_executives(text_content, company)
            
            print(f"   ML Candidates: {len(candidates)}")
            
            # Show all candidates regardless of confidence
            for candidate in candidates:
                print(f"   • {candidate.full_name} - {candidate.confidence_score:.2f}")
            
            # Look for potential names in raw text
            import re
            potential_names = re.findall(r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b', text_content)
            unique_names = list(set(potential_names))[:10]
            
            print(f"   Potential Names in Text: {len(unique_names)}")
            for first, last in unique_names:
                if len(first) > 2 and len(last) > 2:
                    print(f"   • {first} {last}")
                    
        except Exception as e:
            print(f"   ❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_successful_site())
    asyncio.run(test_pattern_improvements()) 