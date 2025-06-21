# ROBUST EXECUTIVE EXTRACTION PLAN - LEVEL 4 COMPLEXITY

**Status:** PLAN MODE - CORE ISSUES ANALYSIS COMPLETE  
**Priority:** CRITICAL - FUNDAMENTAL SYSTEM REBUILD REQUIRED  
**Date:** June 19, 2025

---

## 🔍 **ROOT CAUSE ANALYSIS - CURRENT SYSTEM FAILURES**

### **Critical Finding: Current System is 0% Accurate**

**Evidence from Test Results:**
```json
"executives": [
  {"name": "Commercial Plumbing", "title": "Unknown"},
  {"name": "Call Now", "title": "Unknown"}, 
  {"name": "Opening Hours", "title": "Unknown"},
  {"name": "Alarm Systems", "title": "Unknown"},
  {"name": "Serving Stourbridge", "title": "Unknown"}
]
```

### **Core Problems Identified:**

#### **Problem 1: Fundamentally Flawed Name Extraction**
- **Current Method:** Regex `[A-Z][a-z]+\s+[A-Z][a-z]+` (ANY two capitalized words)
- **Result:** Extracts service terms, locations, and random phrases as "names"
- **Examples:** "Commercial Plumbing", "Call Now", "Opening Hours"
- **Accuracy:** 0% - No actual human names detected

#### **Problem 2: No Semantic Understanding**
- **Issue:** No logic to distinguish human names from business terms
- **Impact:** Cannot tell difference between "John Smith" and "Boiler Services"
- **Root Cause:** Pattern matching without semantic validation

#### **Problem 3: Contact Attribution is Guesswork**
- **Current Method:** Simple proximity search within 200 characters
- **Result:** Random email assignment with no validation
- **Example:** "rhope@hotmail.co.uk" assigned to "Us Richard" and "Today Richard"
- **Accuracy:** Meaningless confidence scores (0.4 for everything)

#### **Problem 4: LinkedIn URLs are Fabricated**
- **Current Method:** Constructing fake LinkedIn URLs from extracted "names"
- **Result:** "https://linkedin.com/in/commercial-plumbing" (doesn't exist)
- **Impact:** 100% fake LinkedIn coverage providing no value

#### **Problem 5: No Title Extraction**
- **Current Method:** Basic pattern search with no context understanding
- **Result:** 100% "Unknown" titles
- **Impact:** Cannot identify decision makers or seniority

---

## 🎯 **ROBUST SOLUTION ARCHITECTURE**

### **Phase 1: Semantic Human Name Recognition**

#### **Approach: Multi-Layer Name Validation**
```python
class SemanticNameExtractor:
    def __init__(self):
        # Layer 1: UK Name Databases
        self.uk_first_names = load_comprehensive_uk_names()  # 1000+ names
        self.uk_surnames = load_comprehensive_uk_surnames()  # 500+ surnames
        
        # Layer 2: Exclusion Databases  
        self.service_terms = [
            'plumbing', 'electrical', 'heating', 'services', 'solutions',
            'installation', 'repair', 'maintenance', 'commercial', 'residential'
        ]
        self.action_terms = [
            'call', 'contact', 'email', 'phone', 'click', 'book', 'schedule'
        ]
        self.location_indicators = [
            'street', 'road', 'avenue', 'drive', 'lane', 'close', 'way'
        ]
        
        # Layer 3: Context Patterns
        self.executive_contexts = [
            'director', 'manager', 'ceo', 'founder', 'owner', 'head of'
        ]
    
    def extract_human_names(self, content: str) -> List[Dict]:
        """Extract only actual human names with confidence scoring"""
        candidates = self._extract_name_candidates(content)
        validated_names = []
        
        for candidate in candidates:
            validation = self._validate_human_name(candidate, content)
            if validation['is_human'] and validation['confidence'] > 0.7:
                validated_names.append({
                    'name': candidate,
                    'confidence': validation['confidence'],
                    'validation_reasons': validation['reasons'],
                    'context': validation['context']
                })
        
        return validated_names
    
    def _validate_human_name(self, name: str, content: str) -> Dict:
        """Multi-factor human name validation"""
        confidence = 0.0
        reasons = []
        
        name_parts = name.split()
        if len(name_parts) != 2:
            return {'is_human': False, 'confidence': 0.0}
        
        first_name, last_name = name_parts
        
        # Factor 1: UK Name Database Match (40% weight)
        if first_name.lower() in self.uk_first_names:
            confidence += 0.4
            reasons.append("First name in UK database")
        
        if last_name.lower() in self.uk_surnames:
            confidence += 0.3
            reasons.append("Surname in UK database")
        
        # Factor 2: Exclusion Filters (negative weight)
        for service_term in self.service_terms:
            if service_term in name.lower():
                confidence -= 0.5
                reasons.append(f"Contains service term: {service_term}")
        
        for action_term in self.action_terms:
            if action_term in name.lower():
                confidence -= 0.6
                reasons.append(f"Contains action term: {action_term}")
        
        # Factor 3: Executive Context (20% weight)
        context_snippet = self._get_name_context(name, content, 100)
        for exec_context in self.executive_contexts:
            if exec_context in context_snippet.lower():
                confidence += 0.2
                reasons.append(f"Found in executive context: {exec_context}")
                break
        
        # Factor 4: Name Pattern Validation (10% weight)
        if self._has_proper_name_pattern(name):
            confidence += 0.1
            reasons.append("Proper name capitalization pattern")
        
        return {
            'is_human': confidence > 0.7,
            'confidence': min(confidence, 1.0),
            'reasons': reasons,
            'context': context_snippet
        }
```

### **Phase 2: Advanced Contact Attribution**

#### **Approach: Multi-Signal Contact Linking**
```python
class AdvancedContactAttributor:
    def __init__(self):
        self.email_patterns = [
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        ]
        self.phone_patterns = [
            r'\b0[1-9]\d{8,9}\b',  # UK landline
            r'\b07\d{9}\b',        # UK mobile
            r'\+44\s?[1-9]\d{8,9}\b'  # International
        ]
    
    def attribute_contacts(self, content: str, validated_names: List[Dict]) -> List[Dict]:
        """Sophisticated contact attribution using multiple signals"""
        
        # Extract all contacts with context
        emails_with_context = self._extract_emails_with_context(content)
        phones_with_context = self._extract_phones_with_context(content)
        
        attributed_executives = []
        
        for name_data in validated_names:
            name = name_data['name']
            
            # Attribution Method 1: Email Signature Detection
            email_match = self._find_email_signature_match(name, emails_with_context)
            
            # Attribution Method 2: Contact Section Analysis  
            if not email_match:
                email_match = self._find_contact_section_match(name, emails_with_context)
            
            # Attribution Method 3: Proximity with Context Weighting
            if not email_match:
                email_match = self._find_proximity_match(name, emails_with_context)
            
            # Same process for phone numbers
            phone_match = self._find_phone_attribution(name, phones_with_context)
            
            executive = {
                'name': name,
                'email': email_match['email'] if email_match else None,
                'email_confidence': email_match['confidence'] if email_match else 0.0,
                'phone': phone_match['phone'] if phone_match else None,
                'phone_confidence': phone_match['confidence'] if phone_match else 0.0,
                'attribution_method': email_match['method'] if email_match else 'none'
            }
            
            attributed_executives.append(executive)
        
        return attributed_executives
    
    def _find_email_signature_match(self, name: str, emails_context: List[Dict]) -> Dict:
        """Find email through signature pattern detection"""
        
        # Look for patterns like:
        # "Best regards, John Smith\njohn@company.com"
        # "Contact John Smith: john@company.com"
        
        signature_patterns = [
            rf'(?:regards|best|sincerely),?\s*{re.escape(name)}\s*[:\n\r]*\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}})',
            rf'{re.escape(name)}\s*[:\-–]\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}})',
            rf'contact\s+{re.escape(name)}\s*[:\-–]\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}})'
        ]
        
        for email_data in emails_context:
            context = email_data['context']
            for pattern in signature_patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    return {
                        'email': match.group(1),
                        'confidence': 0.9,
                        'method': 'signature_detection'
                    }
        
        return None
```

### **Phase 3: Real LinkedIn Discovery**

#### **Approach: Actual Web Search with Validation**
```python
class RealLinkedInDiscoverer:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.search_delay = 2.0  # Rate limiting
    
    async def discover_linkedin_profile(self, name: str, company_domain: str) -> Dict:
        """Actually search for and validate LinkedIn profiles"""
        
        company_name = self._extract_company_name(company_domain)
        search_queries = [
            f'"{name}" "{company_name}" site:linkedin.com/in',
            f'"{name}" {company_domain} site:linkedin.com/in',
            f'{name.replace(" ", " ")} linkedin',
        ]
        
        for query in search_queries:
            try:
                # Perform actual Google search
                search_results = await self._google_search(query)
                linkedin_url = self._extract_linkedin_url(search_results)
                
                if linkedin_url:
                    # Validate the profile actually exists
                    is_valid = await self._validate_linkedin_profile(linkedin_url)
                    if is_valid:
                        return {
                            'linkedin_url': linkedin_url,
                            'verified': True,
                            'discovery_method': 'google_search',
                            'confidence': 0.8
                        }
                
                await asyncio.sleep(self.search_delay)
                
            except Exception as e:
                continue
        
        return {
            'linkedin_url': None,
            'verified': False,
            'discovery_method': 'not_found',
            'confidence': 0.0
        }
    
    async def _google_search(self, query: str) -> str:
        """Perform actual Google search"""
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.text()
        
        return ""
    
    async def _validate_linkedin_profile(self, url: str) -> bool:
        """Actually check if LinkedIn profile exists"""
        try:
            async with self.session.get(url) as response:
                return response.status == 200
        except:
            return False
```

### **Phase 4: Context-Based Title Extraction**

#### **Approach: Executive Section Focus with Pattern Matching**
```python
class ContextTitleExtractor:
    def __init__(self):
        self.executive_titles = {
            'tier_1': ['ceo', 'chief executive', 'managing director', 'md', 'founder', 'owner'],
            'tier_2': ['director', 'general manager', 'head of', 'manager'],
            'tier_3': ['senior', 'lead', 'coordinator', 'administrator']
        }
        
        self.section_indicators = [
            'about us', 'our team', 'management', 'leadership', 'directors',
            'meet the team', 'staff', 'key personnel'
        ]
    
    def extract_titles(self, content: str, validated_names: List[Dict]) -> List[Dict]:
        """Extract real titles from executive sections"""
        
        # Focus on executive sections
        executive_sections = self._extract_executive_sections(content)
        
        enhanced_executives = []
        
        for name_data in validated_names:
            name = name_data['name']
            
            # Method 1: Direct title-name patterns
            title = self._find_direct_title_pattern(name, executive_sections)
            
            # Method 2: Context-based title inference
            if not title:
                title = self._infer_title_from_context(name, executive_sections)
            
            # Method 3: Section-based title extraction
            if not title:
                title = self._extract_section_title(name, executive_sections)
            
            enhanced_executive = name_data.copy()
            enhanced_executive.update({
                'title': title if title else 'Staff Member',
                'seniority_tier': self._classify_seniority(title if title else 'Staff Member'),
                'title_confidence': 0.8 if title else 0.2
            })
            
            enhanced_executives.append(enhanced_executive)
        
        return enhanced_executives
```

### **Phase 5: Quality Control and Validation**

#### **Approach: Multi-Stage Validation Pipeline**
```python
class QualityController:
    def validate_executive_data(self, executives: List[Dict]) -> Dict:
        """Comprehensive quality validation"""
        
        validation_results = {
            'total_executives': len(executives),
            'quality_metrics': {},
            'validation_flags': [],
            'confidence_distribution': {}
        }
        
        # Validate name quality
        real_names = sum(1 for exec in executives if self._is_real_human_name(exec['name']))
        validation_results['quality_metrics']['name_accuracy'] = real_names / len(executives)
        
        # Validate contact attribution
        with_contacts = sum(1 for exec in executives if exec.get('email') or exec.get('phone'))
        validation_results['quality_metrics']['contact_coverage'] = with_contacts / len(executives)
        
        # Validate LinkedIn accuracy
        verified_linkedin = sum(1 for exec in executives if exec.get('linkedin_verified'))
        validation_results['quality_metrics']['linkedin_accuracy'] = verified_linkedin / len(executives)
        
        # Validate title recognition
        with_titles = sum(1 for exec in executives if exec.get('title', 'Unknown') != 'Unknown')
        validation_results['quality_metrics']['title_recognition'] = with_titles / len(executives)
        
        return validation_results
```

---

## 📊 **SUCCESS CRITERIA (Measurable & Realistic)**

### **Primary Success Metrics:**
1. **Name Accuracy:** >80% of extracted names must be actual human names (not service terms)
2. **Contact Attribution:** >40% of executives must have at least one attributed contact
3. **LinkedIn Verification:** >20% must have verified LinkedIn profiles (or explicit None if not found)
4. **Title Recognition:** >50% must have meaningful titles (not "Unknown")
5. **Overall Quality Score:** >60% average confidence across all data points

### **Quality Gates:**
- **Gate 1:** No service terms like "Commercial Plumbing" extracted as names
- **Gate 2:** Contact attribution confidence >0.6 when attribution exists
- **Gate 3:** LinkedIn URLs must be validated (exist) or explicitly None
- **Gate 4:** Title extraction must use context, not pattern guessing

---

## 🔧 **CREATIVE IMPLEMENTATION CHALLENGES**

### **Creative Challenge 1: Semantic Name Recognition**
**Problem:** Distinguish "John Smith" from "Commercial Plumbing" semantically
**Creative Solution:** Multi-layer validation with UK name databases + context analysis

### **Creative Challenge 2: Contact Attribution Algorithm**
**Problem:** Link "john@company.com" to "John Smith" with high confidence
**Creative Solution:** Email signature parsing + contact section analysis + proximity weighting

### **Creative Challenge 3: Real LinkedIn Discovery**
**Problem:** Find actual LinkedIn profiles without expensive APIs
**Creative Solution:** Intelligent Google search + result validation + rate limiting

---

## 📋 **IMPLEMENTATION ROADMAP**

### **Phase 1 (Day 1): Semantic Name Extractor**
- Build UK name databases (1000+ first names, 500+ surnames)
- Implement multi-factor name validation
- Create service term exclusion filters
- Test on current problem cases

### **Phase 2 (Day 2): Advanced Contact Attributor**
- Implement email signature detection
- Build contact section analysis
- Create proximity weighting algorithm
- Validate attribution accuracy

### **Phase 3 (Day 3): Real LinkedIn Discoverer**
- Implement Google search integration
- Build LinkedIn URL validation
- Create rate limiting mechanism
- Test profile discovery accuracy

### **Phase 4 (Day 4): Context Title Extractor**
- Focus on executive section extraction
- Implement UK executive title patterns
- Build context-based title inference
- Test title recognition accuracy

### **Phase 5 (Day 5): Quality Controller**
- Implement validation pipeline
- Create quality metrics calculation
- Build confidence scoring system
- Test overall system accuracy

### **Phase 6 (Day 6): Integration Testing**
- Test on original 9 problematic URLs
- Manual verification of results
- Performance optimization
- Production readiness assessment

---

## 🎯 **EXPECTED OUTCOMES**

**Before (Current System):**
```json
"executives": [
  {"name": "Commercial Plumbing", "title": "Unknown", "email": null, "linkedin_url": "fake"}
]
```

**After (Robust System):**
```json
"executives": [
  {
    "name": "Richard Hope", 
    "title": "Owner",
    "email": "rhope@hotmail.co.uk",
    "phone": "01234567890",
    "linkedin_url": "https://linkedin.com/in/richard-hope-plumbing",
    "name_confidence": 0.92,
    "contact_confidence": 0.87,
    "linkedin_verified": true
  }
]
```

---

**PLAN STATUS:** COMPLETE - READY FOR BUILD MODE IMPLEMENTATION  
**NEXT PHASE:** BUILD MODE with focus on semantic accuracy over pattern matching 