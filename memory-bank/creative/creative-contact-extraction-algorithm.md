🎨🎨🎨 ENTERING CREATIVE PHASE: ALGORITHM DESIGN 🎨🎨🎨

# CREATIVE PHASE: Contact Extraction Algorithm Design

## PROBLEM STATEMENT

Design an intelligent contact extraction algorithm that finds relevant contact information from UK company websites. The algorithm must:

1. **Discover contact pages** - Find `/contact`, `/about`, `/team`, `/staff` pages efficiently
2. **Extract contact details** - Names, roles, email addresses, LinkedIn profiles
3. **Assign confidence scores** - Rate the reliability of extracted information
4. **Handle varied formats** - Work across different website structures and designs
5. **Prioritize decision makers** - Focus on senior roles and business owners

### Core Requirements
- Extract: Contact person name, role/title, email (if available), LinkedIn profile
- Confidence scoring: 0.0-1.0 for each extracted field
- Performance: Process contact pages within 10-15 seconds per company
- Accuracy: 80%+ success rate for finding valid contact information

## OPTIONS ANALYSIS

### Option 1: Simple Page Pattern Matching
**Description**: Basic regex and text pattern matching on common contact page patterns

**Implementation**:
```python
def simple_contact_extract(website_url):
    contact_patterns = ['/contact', '/about', '/team', '/staff']
    name_patterns = [
        r'(?:CEO|Managing Director|Director|Manager).*?([A-Z][a-z]+ [A-Z][a-z]+)',
        r'([A-Z][a-z]+ [A-Z][a-z]+).*?(?:CEO|Managing Director)',
    ]
    
    for pattern in contact_patterns:
        try:
            page_content = requests.get(f"{website_url}{pattern}").text
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Extract names using patterns
            for pattern in name_patterns:
                matches = re.findall(pattern, soup.get_text())
                if matches:
                    return {
                        'contact_person': matches[0],
                        'confidence': 0.6,
                        'source_page': pattern
                    }
        except:
            continue
    
    return {'contact_person': None, 'confidence': 0.0}
```

**Pros**:
- Fast and lightweight
- Easy to implement and debug
- Low computational overhead
- Works on most basic websites

**Cons**:
- Limited accuracy with diverse website formats
- No role/title extraction sophistication
- Prone to false positives
- Doesn't handle modern JavaScript-heavy sites

**Complexity**: Low
**Implementation Time**: 1-2 days

### Option 2: Multi-Strategy Heuristic Extraction
**Description**: Combine multiple extraction strategies with weighted confidence scoring

**Implementation**:
```python
class ContactExtractor:
    def __init__(self):
        self.strategies = [
            StructuredDataStrategy(),  # JSON-LD, microdata
            ContactPageStrategy(),     # Dedicated contact pages
            AboutPageStrategy(),       # About/team pages
            FooterStrategy(),          # Footer contact info
            SocialLinksStrategy()      # LinkedIn profile links
        ]
        
        self.role_priorities = {
            'ceo': 1.0, 'managing director': 1.0, 'founder': 1.0,
            'director': 0.9, 'manager': 0.8, 'head of': 0.8,
            'owner': 0.9, 'partner': 0.8
        }
    
    def extract_contacts(self, website_url):
        candidates = []
        
        # Run all strategies
        for strategy in self.strategies:
            try:
                results = strategy.extract(website_url)
                candidates.extend(results)
            except Exception as e:
                continue
        
        # Score and rank candidates
        scored_candidates = []
        for candidate in candidates:
            score = self.calculate_confidence_score(candidate)
            if score > 0.3:  # Minimum threshold
                scored_candidates.append({**candidate, 'confidence': score})
        
        # Return best candidate
        if scored_candidates:
            return sorted(scored_candidates, key=lambda x: x['confidence'], reverse=True)[0]
        
        return self.fallback_extraction(website_url)
    
    def calculate_confidence_score(self, candidate):
        base_score = 0.5
        
        # Boost for senior roles
        role = candidate.get('role', '').lower()
        for priority_role, boost in self.role_priorities.items():
            if priority_role in role:
                base_score *= boost
                break
        
        # Boost for complete information
        if candidate.get('email'):
            base_score += 0.2
        if candidate.get('linkedin_url'):
            base_score += 0.1
        if candidate.get('phone'):
            base_score += 0.1
        
        # Penalty for extraction method reliability
        method_reliability = {
            'structured_data': 1.0,
            'contact_page': 0.9,
            'about_page': 0.8,
            'footer': 0.6,
            'social_links': 0.7
        }
        base_score *= method_reliability.get(candidate.get('method'), 0.5)
        
        return min(base_score, 1.0)
```

**Pros**:
- Higher accuracy through multiple strategies
- Sophisticated confidence scoring
- Handles various website structures
- Prioritizes decision makers automatically

**Cons**:
- More complex implementation
- Slower processing time
- Requires maintenance of multiple strategies
- Higher computational overhead

**Complexity**: Medium
**Implementation Time**: 4-5 days

### Option 3: AI/NLP-Enhanced Extraction
**Description**: Use natural language processing and AI models for intelligent content understanding

**Implementation**:
```python
class AIContactExtractor:
    def __init__(self):
        self.nlp_model = spacy.load("en_core_web_sm")
        self.role_classifier = self.load_role_classifier()
        self.contact_page_detector = self.load_page_classifier()
    
    def extract_contacts(self, website_url):
        # 1. Intelligent page discovery
        relevant_pages = self.discover_contact_pages(website_url)
        
        # 2. Extract entities from each page
        all_candidates = []
        for page_url, page_content in relevant_pages:
            doc = self.nlp_model(page_content)
            
            # Extract person entities
            persons = [ent for ent in doc.ents if ent.label_ == "PERSON"]
            
            # Extract roles/titles using context
            for person in persons:
                context = self.extract_context(person, doc)
                role = self.classify_role(context)
                
                candidate = {
                    'contact_person': person.text,
                    'role': role,
                    'confidence': self.calculate_ai_confidence(person, role, context),
                    'source_page': page_url
                }
                all_candidates.append(candidate)
        
        # 3. Rank by relevance and seniority
        return self.rank_candidates(all_candidates)
    
    def discover_contact_pages(self, website_url):
        # Use ML model to classify pages by relevance
        sitemap_urls = self.get_sitemap_urls(website_url)
        
        relevant_pages = []
        for url in sitemap_urls:
            try:
                content = self.fetch_page_content(url)
                relevance_score = self.contact_page_detector.predict(content)
                
                if relevance_score > 0.7:
                    relevant_pages.append((url, content))
            except:
                continue
        
        return relevant_pages
```

**Pros**:
- Highest potential accuracy
- Intelligent page discovery
- Context-aware role extraction
- Adaptable to new website patterns

**Cons**:
- Complex implementation requiring ML expertise
- Significant computational overhead
- Requires training data and model management
- Overkill for current requirements

**Complexity**: High
**Implementation Time**: 1-2 weeks

### Option 4: Hybrid Rule-Based + Learning
**Description**: Start with rule-based system, gradually introduce learning components

**Implementation**:
```python
class HybridContactExtractor:
    def __init__(self):
        self.rule_engine = RuleBasedExtractor()
        self.pattern_learner = PatternLearner()
        self.confidence_calibrator = ConfidenceCalibrator()
    
    def extract_contacts(self, website_url):
        # Phase 1: Rule-based extraction
        rule_results = self.rule_engine.extract(website_url)
        
        # Phase 2: Apply learned patterns
        pattern_results = self.pattern_learner.enhance_extraction(
            website_url, rule_results
        )
        
        # Phase 3: Calibrate confidence based on historical accuracy
        final_results = self.confidence_calibrator.adjust_confidence(
            pattern_results
        )
        
        # Phase 4: Store extraction for learning
        self.pattern_learner.record_extraction(website_url, final_results)
        
        return final_results
```

**Pros**:
- Evolutionary improvement over time
- Starts with reliable rule-based foundation
- Builds learning capability for future enhancement
- Good balance of accuracy and implementation complexity

**Cons**:
- More complex initial architecture
- Requires feedback mechanism
- Longer development timeline
- Risk of over-engineering

**Complexity**: Medium-High
**Implementation Time**: 6-7 days

🎨 CREATIVE CHECKPOINT: Algorithm Options Evaluated 🎨

## DECISION

**Chosen Option: Option 2 - Multi-Strategy Heuristic Extraction**

### Rationale

After evaluating all options against our requirements and constraints:

1. **Accuracy vs Complexity**: Provides significant accuracy improvement without AI complexity
2. **Implementation Timeline**: Fits within our 4-5 day contact extraction development window
3. **Maintainability**: Multiple strategies can be updated independently
4. **Performance**: Processes pages within our 10-15 second target
5. **Confidence Scoring**: Sophisticated scoring enables quality filtering
6. **Extensibility**: Easy to add new extraction strategies as needed

### Implementation Plan

#### Strategy Architecture
```python
class ContactExtractionEngine:
    def __init__(self):
        self.strategies = {
            'structured_data': StructuredDataStrategy(),
            'contact_form': ContactFormStrategy(),
            'about_page': AboutPageStrategy(),
            'team_page': TeamPageStrategy(),
            'footer': FooterContactStrategy(),
            'linkedin_links': LinkedInStrategy()
        }
        
        self.confidence_weights = {
            'role_seniority': 0.4,      # Senior roles get higher scores
            'information_completeness': 0.3,  # More fields = higher confidence
            'extraction_method': 0.2,   # Some methods more reliable
            'content_quality': 0.1      # Clear, well-formatted content
        }
```

#### Senior Role Detection
```python
SENIOR_ROLE_PATTERNS = {
    'tier_1': {  # Highest priority
        'patterns': ['ceo', 'chief executive', 'managing director', 'founder', 'owner'],
        'confidence_multiplier': 1.0
    },
    'tier_2': {  # High priority
        'patterns': ['director', 'head of', 'general manager', 'partner'],
        'confidence_multiplier': 0.9
    },
    'tier_3': {  # Medium priority
        'patterns': ['manager', 'lead', 'senior', 'supervisor'],
        'confidence_multiplier': 0.7
    }
}
```

#### Expected Output Format
```json
{
  "company_id": "uk-company-123",
  "contact_extraction": {
    "contact_person": "John Smith",
    "contact_role": "Managing Director", 
    "linkedin_url": "https://linkedin.com/in/johnsmith",
    "email": null,
    "phone": "+44 20 1234 5678",
    "confidence": 0.85,
    "extraction_details": {
      "source_page": "/about",
      "method": "about_page",
      "role_tier": "tier_1",
      "completeness_score": 0.8
    }
  }
}
```

### Validation Criteria
- [ ] 80%+ success rate for extracting valid contact names
- [ ] 70%+ accuracy for role/title extraction
- [ ] Confidence scores correlate with actual accuracy
- [ ] Process contact pages within 10-15 seconds
- [ ] Handle at least 6 different website structures effectively

🎨🎨🎨 EXITING CREATIVE PHASE - DECISION MADE 🎨🎨🎨

## SUMMARY

**Decision**: Multi-Strategy Heuristic Contact Extraction
**Key Innovation**: Weighted confidence scoring across multiple extraction methods
**Implementation Priority**: Medium (supports lead enrichment)
**Dependencies**: Web scraping infrastructure, pattern matching, confidence calibration

This algorithm will provide reliable contact extraction with actionable confidence scores, enabling quality filtering and personalized outreach. 