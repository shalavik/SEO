"""
Executive Contact Discovery Orchestrator - 8-Step Implementation
Implements comprehensive executive discovery using Context7 Playwright patterns
Enhanced for actual URL handling and robots.txt bypass
FIXED: Now extracts real executive information instead of placeholder data
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from urllib.parse import urlparse, urljoin
import re
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from playwright.async_api import async_playwright, Page
import aiohttp
from bs4 import BeautifulSoup

# Import Companies House enricher for official UK government data
try:
    from ..enrichers.companies_house_enricher import CompaniesHouseEnricher
except ImportError:
    logger.warning("Companies House enricher not available")
    CompaniesHouseEnricher = None

# Import Phase9a Contact Extraction Engine for real data
try:
    from phase9a_contact_extraction_engine import Phase9aContactExtractionEngine, Phase9aConfig
except ImportError:
    logger.warning("Phase9a Contact Extraction Engine not available, using fallback")
    Phase9aContactExtractionEngine = None
    Phase9aConfig = None

logger = logging.getLogger(__name__)

@dataclass
class ExecutiveContact:
    """Executive contact information"""
    name: str = ""
    title: str = ""
    company_name: str = ""
    website_url: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    confidence_score: float = 0.0
    discovery_sources: List[str] = field(default_factory=list)
    discovery_method: str = ""
    validation_notes: str = ""

@dataclass
class DiscoveryStep:
    """Individual discovery step result with validation"""
    step_number: int
    step_name: str
    source: str
    success: bool
    confidence: float
    data_found: Dict[str, Any]
    validation_results: Dict[str, bool]
    fallback_triggered: bool
    processing_time_ms: int
    error_message: Optional[str] = None

@dataclass
class CompanyIdentification:
    """Company identification data from website"""
    name: str
    domain: str
    website_url: str
    actual_url: str  # The actual URL that worked
    extracted_address: Optional[str] = None
    phone: Optional[str] = None
    confidence: float = 0.0
    extraction_method: str = ""
    validation_flags: Dict[str, bool] = field(default_factory=dict)

@dataclass
class ExecutiveDiscoveryResult:
    """Main result container"""
    company_name: str
    website_url: str
    actual_working_url: str  # The URL that actually worked
    companies_house_verified: bool
    discovery_steps: List[DiscoveryStep] 
    executives: List[ExecutiveContact]
    overall_confidence: float
    validation_summary: Dict[str, Any]

class ExecutiveDiscoveryOrchestrator:
    """Master Executive Discovery Orchestrator implementing 8-step discovery logic with REAL data extraction"""
    
    def __init__(self):
        logger.info("Initializing 8-Step Executive Discovery Orchestrator with REAL executive data extraction")
        
        # Initialize Phase9a Contact Extraction Engine for real data
        if Phase9aContactExtractionEngine:
            self.contact_engine = Phase9aContactExtractionEngine(Phase9aConfig())
            logger.info("Phase9a Contact Extraction Engine initialized for real executive discovery")
        else:
            self.contact_engine = None
            logger.warning("Phase9a engine not available, using enhanced fallback extraction")
        
        # Initialize Companies House enricher for official UK data
        if CompaniesHouseEnricher:
            self.companies_house_enricher = CompaniesHouseEnricher()
            logger.info("Companies House enricher initialized for official UK company data")
        else:
            self.companies_house_enricher = None
            logger.warning("Companies House enricher not available")
        
    def _normalize_url(self, url: str) -> str:
        """Normalize URL but preserve actual working format"""
        url = url.strip()
        
        # Don't modify URLs that are already complete and working
        if url.startswith(('http://', 'https://')):
            return url
            
        # Only add protocol if missing
        if not url.startswith(('http://', 'https://')):
            # Try HTTPS first, then HTTP as fallback
            return f"https://{url}"
            
        return url
    
    async def _try_url_variations(self, original_url: str) -> List[str]:
        """Generate URL variations to try, preserving actual working URLs"""
        variations = []
        
        # Always start with the original URL as provided
        variations.append(original_url)
        
        # Only add variations if the original URL seems to be a simplified domain
        parsed = urlparse(original_url)
        
        # If it's just a domain without path, try some common variations
        if not parsed.path or parsed.path == '/':
            domain = parsed.netloc or parsed.path
            
            # Add protocol variations
            variations.extend([
                f"https://{domain}",
                f"http://{domain}",
                f"https://www.{domain}",
                f"http://www.{domain}"
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for url in variations:
            if url not in seen:
                seen.add(url)
                unique_variations.append(url)
                
        return unique_variations
        
    async def execute_comprehensive_discovery(self, website_url: str) -> ExecutiveDiscoveryResult:
        """Execute all 8 steps with validation and fallbacks - NOW WITH REAL EXECUTIVE DATA"""
        
        start_time = time.time()
        discovery_steps = []
        actual_working_url = website_url
        
        logger.info(f"Starting 8-step REAL executive discovery for {website_url}")
        
        try:
            # Step 1: Identify Company on Website
            step_start = time.time()
            company_data = await self._step1_identify_company(website_url)
            step_time = int((time.time() - step_start) * 1000)
            
            # Update actual working URL
            actual_working_url = company_data.actual_url
            
            discovery_steps.append(DiscoveryStep(
                step_number=1,
                step_name="Identify Company on Website",
                source="website_extraction",
                success=company_data.confidence > 0.3,
                confidence=company_data.confidence,
                data_found={
                    'company_name': company_data.name, 
                    'domain': company_data.domain,
                    'actual_url': company_data.actual_url,
                    'extraction_method': company_data.extraction_method
                },
                validation_results={'name_extracted': bool(company_data.name)},
                fallback_triggered=company_data.extraction_method == "domain_fallback",
                processing_time_ms=step_time
            ))
            
            # Step 2: Companies House Official Directors Lookup
            step_start = time.time()
            companies_house_executives, ch_verified = await self._step2_companies_house_verification(company_data.name)
            step_time = int((time.time() - step_start) * 1000)
            
            discovery_steps.append(DiscoveryStep(
                step_number=2,
                step_name="Retrieve Official Company Info",
                source="companies_house",
                success=len(companies_house_executives) > 0,
                confidence=1.0 if len(companies_house_executives) > 0 else 0.0,
                data_found={
                    'directors_found': len(companies_house_executives),
                    'company_verified': ch_verified,
                    'official_data_source': 'UK_Government_Companies_House'
                },
                validation_results={'companies_house_verified': ch_verified},
                fallback_triggered=len(companies_house_executives) == 0,
                processing_time_ms=step_time
            ))
            
            # Step 3-8: REAL Executive Discovery using Phase9a Engine
            step_start = time.time()
            website_executives = await self._steps3to8_real_executive_discovery(company_data.name, actual_working_url)
            step_time = int((time.time() - step_start) * 1000)
            
            # Merge Companies House executives with website-discovered executives
            all_executives = self._merge_companies_house_and_website_executives(
                companies_house_executives, website_executives, company_data.name
            )
            
            logger.info(f"8-step REAL executive discovery complete for {company_data.name} (URL: {actual_working_url})")
            logger.info(f"Found {len(all_executives)} real executives with contact information")
            
            return ExecutiveDiscoveryResult(
                company_name=company_data.name,
                website_url=website_url,
                actual_working_url=actual_working_url,
                companies_house_verified=ch_verified,
                discovery_steps=discovery_steps,
                executives=all_executives,
                overall_confidence=company_data.confidence,
                validation_summary={
                    'steps_completed': len(discovery_steps), 
                    'real_executives_found': len(all_executives),
                    'companies_house_directors': len(companies_house_executives),
                    'website_executives': len(website_executives)
                }
            )
            
        except Exception as e:
            logger.error(f"8-step orchestration failed: {e}")
            
            return ExecutiveDiscoveryResult(
                company_name=urlparse(website_url).netloc or website_url,
                website_url=website_url,
                actual_working_url=actual_working_url,
                companies_house_verified=False,
                discovery_steps=discovery_steps,
                executives=[],
                overall_confidence=0.0,
                validation_summary={'orchestration_error': str(e)}
            )
    
    async def _steps3to8_real_executive_discovery(self, company_name: str, website_url: str) -> List[ExecutiveContact]:
        """Steps 3-8: Extract REAL executive information using Phase9a engine and enhanced extraction"""
        
        executives = []
        
        try:
            logger.info(f"Extracting REAL executive data for {company_name}")
            
            if self.contact_engine:
                # Use Phase9a Contact Extraction Engine for real data
                logger.info("Using Phase9a Contact Extraction Engine for real executive discovery")
                result = await self.contact_engine.extract_executive_contacts(company_name, website_url)
                
                if result and 'executive_profiles' in result:
                    for profile in result['executive_profiles']:
                        # Convert Phase9a profile to ExecutiveContact
                        exec_contact = self._convert_phase9a_profile(profile, company_name, website_url)
                        if exec_contact:
                            executives.append(exec_contact)
                            
                    logger.info(f"Phase9a engine found {len(executives)} executives")
            
            # Fallback: Enhanced direct extraction if Phase9a didn't find enough
            if len(executives) < 2:
                logger.info("Using enhanced fallback extraction to find more executives")
                fallback_executives = await self._enhanced_fallback_extraction(company_name, website_url)
                executives.extend(fallback_executives)
            
            # Final validation and confidence scoring
            executives = self._validate_and_score_executives(executives)
            
            logger.info(f"Total REAL executives found: {len(executives)}")
            for exec in executives:
                logger.info(f"  - {exec.name} ({exec.title}) - Email: {exec.email}, Phone: {exec.phone}, LinkedIn: {exec.linkedin_url}")
            
            return executives
            
        except Exception as e:
            logger.error(f"Real executive discovery failed: {e}")
            return []
    
    def _convert_phase9a_profile(self, profile: Dict, company_name: str, website_url: str) -> Optional[ExecutiveContact]:
        """Convert Phase9a executive profile to ExecutiveContact with enhanced validation"""
        try:
            contact_info = profile.get('contact_info', {})
            name = profile.get('name', '').strip()
            title = profile.get('title', '').strip()
            
            # Enhanced name validation - filter out obvious non-person names
            if not self._is_valid_person_name(name):
                return None
            
            # Extract contact details
            emails = contact_info.get('email_addresses', [])
            phones = contact_info.get('phone_numbers', [])
            linkedin_profiles = contact_info.get('linkedin_profiles', [])
            
            exec_contact = ExecutiveContact(
                name=name,
                title=title if title and title != "Unknown" else self._infer_title_from_name(name),
                company_name=company_name,
                website_url=website_url,
                email=emails[0] if emails else None,
                phone=phones[0] if phones else None,
                linkedin_url=linkedin_profiles[0] if linkedin_profiles else None,
                confidence_score=profile.get('overall_confidence', 0.7),
                discovery_sources=["phase9a_contact_engine"],
                discovery_method="phase9a_real_extraction",
                validation_notes=f"Phase9a extraction - Completeness: {contact_info.get('completeness_percentage', 0)}%"
            )
            
            return exec_contact
            
        except Exception as e:
            logger.warning(f"Failed to convert Phase9a profile: {e}")
            return None
    
    def _is_valid_person_name(self, name: str) -> bool:
        """STRICT validation for person names - MUST be actual human names only"""
        if not name or len(name.strip()) < 3:
            return False
            
        name = name.strip()
        
        # STRICT FILTERING - Reject anything that looks like website content
        case_insensitive_patterns = [
            # Service/business terms - EXPANDED
            r'\b(plumbing|heating|services|ltd|limited|company|corp|inc|llc|drainage|boiler|pipe|water|gas|radiator|bathroom|kitchen|installation|repair|emergency|commercial|residential)\b',
            r'\b(customer|service|quality|pricing|estimate|free|quote|call|phone|contact|email|website|online|click|view|learn|more|info|about|home)\b',
            r'\b(facebook|twitter|instagram|linkedin|google|youtube|social|media|share|follow|like|post|review|rating)\b',
            r'\b(birmingham|midlands|sutton|coldfield|kings|heath|south|north|east|west|area|region|local|national)\b',
            r'\b(schedule|appointment|booking|quick|fast|same|day|hour|time|now|today|tomorrow|weekend)\b',
            r'\b(approved|certified|qualified|registered|licensed|insured|guaranteed|professional|expert|specialist)\b',
            r'\b(efficiency|energy|solar|hot|cold|warm|temperature|pressure|flow|leak|burst|block|drain)\b',
            # Technical terms
            r'\b(cylinders|unvented|underfloor|radiators|thermostats|valves|pumps|tanks|systems|solutions)\b',
            # Navigation/UI elements  
            r'\b(menu|navigation|header|footer|sidebar|content|page|section|link|button|form|search)\b',
            r'\b(gallery|photos|images|videos|testimonials|reviews|feedback|comments|blog|news)\b',
            # Generic phrases that appear on websites
            r'\b(why|choose|what|how|when|where|who|help|support|team|staff|people|members)\b',
            r'\b(useful|helpful|important|essential|necessary|required|recommended|suggested)\b',
            # Single common words that aren't names
            r'^(the|and|or|but|with|from|to|of|in|on|at|by|for|as|is|are|was|were|be|been|have|has|had|do|does|did|will|would|could|should|may|might|can|must)$',
        ]
        
        case_sensitive_patterns = [
            # Numbers, special characters, or mixed case issues
            r'\d',
            r'[^\w\s\-\']',
            r'\b[A-Z]{2,}\b',  # All caps words (likely abbreviations) - CASE SENSITIVE
        ]
        
        # Check case-insensitive patterns
        for pattern in case_insensitive_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False
        
        # Check case-sensitive patterns
        for pattern in case_sensitive_patterns:
            if re.search(pattern, name):  # No IGNORECASE flag
                return False
        
        # Must have EXACTLY 2 words for first/last name (no more, no less)
        name_parts = name.split()
        if len(name_parts) != 2:
            return False
        
        # Each part must be a proper name (2-20 chars, starts with capital, all letters)
        for part in name_parts:
            if len(part) < 2 or len(part) > 20:
                return False
            if not part[0].isupper():
                return False
            if not part.isalpha():
                return False
            if part.lower() in ['the', 'and', 'or', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 'from', 'to']:
                return False
        
        # STRICT: Only allow names that start with common UK first names
        first_name = name_parts[0].lower()
        common_uk_first_names = {
            'james', 'john', 'david', 'michael', 'paul', 'andrew', 'mark', 'richard', 'robert', 'peter',
            'stephen', 'christopher', 'matthew', 'daniel', 'anthony', 'simon', 'kevin', 'gary', 'ian',
            'jonathan', 'nicholas', 'martin', 'stuart', 'graham', 'ben', 'tom', 'sam', 'alex', 'max',
            'adam', 'steve', 'mike', 'dave', 'chris', 'dan', 'matt', 'andy', 'rob', 'tim', 'alan',
            'sarah', 'emma', 'claire', 'lisa', 'helen', 'susan', 'karen', 'nicola', 'rachel', 'jane',
            'julie', 'rebecca', 'amanda', 'michelle', 'caroline', 'louise', 'elizabeth', 'anna', 'kate',
            'fiona', 'joanne', 'victoria', 'samantha', 'jennifer', 'laura', 'stephanie', 'maria',
            'barry', 'neil', 'craig', 'jason', 'lee', 'mark', 'scott', 'dean', 'wayne', 'colin',
            'derek', 'keith', 'trevor', 'gordon', 'brian', 'terry', 'roger', 'maurice', 'owen',
            'ryan', 'luke', 'jake', 'kyle', 'connor', 'jamie', 'lewis', 'cameron', 'adam', 'josh'
        }
        
        # BALANCED APPROACH: Prefer common UK names but allow others that look legitimate
        if first_name in common_uk_first_names:
            # High confidence for known UK names
            return len(name) >= 6 and len(name) <= 40
        else:
            # Additional validation for less common names - must look very much like real names
            
            # Allow some common international names that might run UK businesses
            international_first_names = {
                'ahmed', 'ali', 'abdul', 'muhammad', 'mohammed', 'hassan', 'omar', 'yusuf', 'ibrahim',
                'raj', 'amit', 'sunil', 'ravi', 'vijay', 'kumar', 'pradeep', 'sandeep', 'deepak', 'rakesh',
                'luigi', 'marco', 'antonio', 'giuseppe', 'francesco', 'giovanni', 'alessandro', 'andrea',
                'pierre', 'jean', 'philippe', 'michel', 'thierry', 'patrick', 'francois', 'laurent',
                'stefan', 'peter', 'andreas', 'thomas', 'michael', 'alexander', 'christian', 'wolfgang',
                'jose', 'carlos', 'antonio', 'manuel', 'fernando', 'francisco', 'rafael', 'miguel'
            }
            
            if first_name in international_first_names:
                return len(name) >= 6 and len(name) <= 40
            
            # For unknown names, require very strict validation
            # Must look like legitimate personal names (no obvious business terms)
            name_lower = name.lower()
            
            # Reject if it contains obvious business/service indicators
            business_indicators = [
                'plumb', 'heat', 'serv', 'emerg', 'repair', 'install', 'drain', 'water', 'gas',
                'boiler', 'pipe', 'bath', 'kitchen', 'commercial', 'residential', 'company',
                'business', 'enterprise', 'solutions', 'systems'
            ]
            
            for indicator in business_indicators:
                if indicator in name_lower:
                    return False
            
            # Additional surname validation for unknown first names
            last_name = name_parts[1].lower()
            common_uk_surnames = {
                'smith', 'jones', 'taylor', 'brown', 'williams', 'wilson', 'johnson', 'davies', 'robinson', 'wright',
                'thompson', 'evans', 'walker', 'white', 'roberts', 'green', 'hall', 'wood', 'jackson', 'clarke',
                'patel', 'khan', 'lewis', 'james', 'phillips', 'mason', 'mitchell', 'rose', 'davis', 'rodgers',
                'parker', 'turner', 'cook', 'cooper', 'hill', 'ward', 'morris', 'moore', 'clark', 'lee',
                'king', 'baker', 'harrison', 'morgan', 'allen', 'clarke', 'murphy', 'hughes', 'edwards', 'stone',
                'miller', 'anderson', 'martin', 'bell', 'reid', 'campbell', 'young', 'scott', 'murray', 'watson'
            }
            
            # Allow if surname is recognizable, even with uncommon first name
            if last_name in common_uk_surnames:
                return len(name) >= 6 and len(name) <= 40
            
            # Final check: does it at least look like a real name pattern?
            # (This catches legitimate names we might not have in our lists)
            if (len(first_name) >= 3 and len(last_name) >= 3 and 
                first_name.isalpha() and last_name.isalpha() and
                first_name[0].isupper() and last_name[0].isupper() and
                len(name) >= 6 and len(name) <= 40):
                return True
            
            return False
    
    def _infer_title_from_name(self, name: str) -> str:
        """Infer likely executive title based on name patterns and context"""
        
        # Common title indicators in UK businesses
        if any(indicator in name.lower() for indicator in ['director', 'manager', 'ceo', 'md']):
            return "Director"
        
        # Default titles for small UK businesses
        default_titles = ["Managing Director", "Director", "Owner", "Manager"]
        return default_titles[0]  # Most common for UK SMEs
    
    async def _enhanced_fallback_extraction(self, company_name: str, website_url: str) -> List[ExecutiveContact]:
        """Enhanced fallback extraction for real executive data with improved name detection"""
        
        executives = []
        
        try:
            logger.info(f"Running enhanced fallback extraction for {company_name}")
            
            # Fetch comprehensive content from multiple pages
            content_data = await self._fetch_comprehensive_content(website_url)
            
            # Use multiple extraction strategies
            strategies = [
                self._extract_from_about_team_pages,
                self._extract_from_contact_pages,
                self._extract_from_structured_data
            ]
            
            all_raw_executives = []
            
            for strategy in strategies:
                try:
                    raw_executives = strategy(content_data['content'], website_url)
                    all_raw_executives.extend(raw_executives)
                except Exception as e:
                    logger.debug(f"Strategy failed: {e}")
                    continue
            
            # Deduplicate and validate executives
            unique_executives = self._deduplicate_executives(all_raw_executives)
            
            # Extract contact information for each validated executive
            for raw_exec in unique_executives[:5]:  # Limit to top 5
                exec_contact = await self._enrich_executive_with_contacts(
                    raw_exec, content_data['content'], company_name, website_url
                )
                if exec_contact:
                    executives.append(exec_contact)
            
            logger.info(f"Enhanced fallback found {len(executives)} additional executives")
            
            return executives
            
        except Exception as e:
            logger.error(f"Enhanced fallback extraction failed: {e}")
            return []
    
    def _extract_from_about_team_pages(self, content: str, website_url: str) -> List[Dict]:
        """Extract executives specifically from about/team page content"""
        
        executives = []
        
        # Look for team/about page sections
        team_sections = re.findall(
            r'(?:team|about|management|leadership|directors|staff|people).*?(?=(?:team|about|contact|services|home|\Z))',
            content.lower(), re.DOTALL
        )
        
        for section in team_sections:
            # Enhanced patterns for UK business executives
            executive_patterns = [
                # Name + Title patterns
                r'([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,20})\s*[,\-\s]*(?:is\s+(?:the\s+)?|works\s+as\s+)?([Dd]irector|[Mm]anager|[Cc]EO|[Mm]D|[Oo]wner|[Ff]ounder)',
                r'([Dd]irector|[Mm]anager|[Cc]EO|[Mm]D|[Oo]wner|[Ff]ounder)[,\-\s]*([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,20})',
                # Professional bio patterns
                r'([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,20})\s+has\s+(?:over\s+)?\d+\s+years?\s+(?:of\s+)?experience',
                r'([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,20})\s+(?:founded|established|started)\s+(?:the\s+)?company',
                # Contact patterns
                r'(?:contact|speak\s+to|call)\s+([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,20})',
            ]
            
            for pattern in executive_patterns:
                matches = re.finditer(pattern, section, re.IGNORECASE)
                
                for match in matches:
                    if 'director' in pattern.lower() or 'manager' in pattern.lower():
                        # Pattern with title first
                        title = match.group(1).strip()
                        name = match.group(2).strip()
                    else:
                        # Pattern with name first
                        name = match.group(1).strip()
                        title = match.group(2).strip() if len(match.groups()) > 1 else "Director"
                    
                    if self._is_valid_person_name(name):
                        executives.append({
                            'name': name,
                            'title': title.title(),
                            'confidence': 0.8,
                            'source': 'about_team_extraction'
                        })
        
        return executives
    
    def _extract_from_contact_pages(self, content: str, website_url: str) -> List[Dict]:
        """Extract executives from contact page content"""
        
        executives = []
        
        # Look for contact sections
        contact_sections = re.findall(
            r'(?:contact|get\s+in\s+touch|reach\s+out|speak\s+to).*?(?=(?:services|about|home|\Z))',
            content.lower(), re.DOTALL
        )
        
        for section in contact_sections:
            # Patterns for contact persons
            patterns = [
                r'(?:speak\s+to|contact|call)\s+([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,20})',
                r'([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,20})\s*[,\-\s]*(?:director|manager|owner)',
                r'(?:Mr|Mrs|Ms)\s+([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,20})',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, section, re.IGNORECASE)
                
                for match in matches:
                    name = match.group(1).strip()
                    
                    if self._is_valid_person_name(name):
                        executives.append({
                            'name': name,
                            'title': "Director",  # Default for contact persons
                            'confidence': 0.7,
                            'source': 'contact_extraction'
                        })
        
        return executives
    
    def _extract_from_structured_data(self, content: str, website_url: str) -> List[Dict]:
        """Extract executives from structured data like schema.org markup"""
        
        executives = []
        
        # Look for JSON-LD structured data
        json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        json_scripts = re.findall(json_ld_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for script in json_scripts:
            try:
                import json
                data = json.loads(script.strip())
                
                # Look for person or organization data
                if isinstance(data, dict):
                    if data.get('@type') == 'Person':
                        name = data.get('name', '')
                        job_title = data.get('jobTitle', 'Director')
                        
                        if self._is_valid_person_name(name):
                            executives.append({
                                'name': name,
                                'title': job_title,
                                'confidence': 0.9,
                                'source': 'structured_data'
                            })
                    
                    elif data.get('@type') == 'Organization':
                        # Look for founder or employees
                        founder = data.get('founder', {})
                        if isinstance(founder, dict) and founder.get('name'):
                            name = founder.get('name')
                            if self._is_valid_person_name(name):
                                executives.append({
                                    'name': name,
                                    'title': 'Founder',
                                    'confidence': 0.9,
                                    'source': 'structured_data'
                                })
                        
                        employees = data.get('employee', [])
                        if not isinstance(employees, list):
                            employees = [employees]
                        
                        for employee in employees:
                            if isinstance(employee, dict) and employee.get('name'):
                                name = employee.get('name')
                                job_title = employee.get('jobTitle', 'Director')
                                
                                if self._is_valid_person_name(name):
                                    executives.append({
                                        'name': name,
                                        'title': job_title,
                                        'confidence': 0.9,
                                        'source': 'structured_data'
                                    })
            
            except (json.JSONDecodeError, KeyError):
                continue
        
        return executives
    
    def _deduplicate_executives(self, executives: List[Dict]) -> List[Dict]:
        """Deduplicate executives based on name similarity"""
        
        unique_executives = []
        seen_names = set()
        
        # Sort by confidence (highest first)
        executives.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        for exec_data in executives:
            name = exec_data['name'].lower().strip()
            
            # Check for exact matches or very similar names
            is_duplicate = False
            for seen_name in seen_names:
                # Calculate similarity
                similarity = self._calculate_name_similarity(name, seen_name)
                if similarity > 0.8:  # 80% similarity threshold
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_names.add(name)
                unique_executives.append(exec_data)
        
        return unique_executives
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names"""
        # Simple similarity based on common words
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _extract_executives_from_content(self, content: str) -> List[Dict]:
        """Extract executives from content using enhanced patterns - IMPROVED VERSION"""
        
        executives = []
        
        # More targeted executive title patterns for UK businesses
        executive_patterns = [
            # Senior executive titles
            (r'(Chief Executive Officer|CEO)', 'CEO'),
            (r'(Managing Director|MD)', 'Managing Director'),
            (r'(Operations Director)', 'Operations Director'),
            (r'(Sales Director)', 'Sales Director'),
            (r'(Technical Director)', 'Technical Director'),
            (r'(Finance Director)', 'Finance Director'),
            (r'(Executive Director)', 'Executive Director'),
            
            # Management titles
            (r'(General Manager)', 'General Manager'),
            (r'(Operations Manager)', 'Operations Manager'),
            (r'(Sales Manager)', 'Sales Manager'),
            (r'(Business Manager)', 'Business Manager'),
            
            # Business owner titles
            (r'(Owner)', 'Owner'),
            (r'(Founder)', 'Founder'),
            (r'(Co-Founder)', 'Co-Founder'),
            (r'(Principal)', 'Principal'),
            (r'(Proprietor)', 'Proprietor'),
        ]
        
        # Look for proper name + title combinations
        for title_pattern, title_name in executive_patterns:
            # Pattern: Proper Name + Title
            pattern = rf'\b([A-Z][a-z]{{2,15}}\s+[A-Z][a-z]{{2,20}})\s*[,\-\s]*(?:is\s+(?:the\s+)?|works\s+as\s+)?{title_pattern}'
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                name = match.group(1).strip()
                
                # Validate name quality
                if self._is_valid_person_name(name):
                    executives.append({
                        'name': name,
                        'title': title_name,
                        'confidence': 0.8
                    })
            
            # Pattern: Title + Proper Name  
            pattern = rf'{title_pattern}\s*[,\-\s]*([A-Z][a-z]{{2,15}}\s+[A-Z][a-z]{{2,20}})\b'
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                name = match.group(2).strip() if len(match.groups()) > 1 else match.group(1).strip()
                
                if self._is_valid_person_name(name):
                    executives.append({
                        'name': name,
                        'title': title_name,
                        'confidence': 0.8
                    })
        
        # Look for "Contact [Name]" patterns
        contact_patterns = [
            r'(?:contact|speak\s+to|call)\s+([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,20})',
            r'([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,20})\s*[,\-\s]*(?:is\s+)?(?:available|here\s+to\s+help)',
        ]
        
        for pattern in contact_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                name = match.group(1).strip()
                
                if self._is_valid_person_name(name):
                    executives.append({
                        'name': name,
                        'title': 'Director',  # Default for contact persons
                        'confidence': 0.6
                    })
        
        # Deduplicate executives
        seen_names = set()
        unique_executives = []
        for exec in executives:
            name_key = exec['name'].lower()
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_executives.append(exec)
        
        logger.info(f"Extracted {len(unique_executives)} potential executives from content")
        return unique_executives[:8]  # Limit to top 8
    
    def _is_valid_executive_name(self, name: str) -> bool:
        """Validate if a name looks like a real person's name - ENHANCED VERSION"""
        return self._is_valid_person_name(name)  # Use the enhanced validation
    
    async def _fetch_comprehensive_content(self, website_url: str) -> Dict[str, Any]:
        """Fetch comprehensive content from multiple pages for executive discovery"""
        
        content_data = {
            'content': '',
            'pages_analyzed': 0
        }
        
        # Priority pages for executive information
        priority_paths = [
            '',  # Homepage
            '/about', '/about-us', '/team', '/staff', '/management',
            '/leadership', '/executives', '/directors', '/board',
            '/people', '/our-team', '/meet-the-team', '/contact',
            '/company', '/organization', '/who-we-are'
        ]
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--ignore-certificate-errors',
                    '--ignore-ssl-errors',
                    '--ignore-certificate-errors-spki-list'
                ]
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                ignore_https_errors=True,
                bypass_csp=True,
                java_script_enabled=True
            )
            
            # Robots.txt bypass
            async def handle_route(route):
                if route.request.url.endswith('/robots.txt'):
                    await route.abort()
                else:
                    await route.continue_()
            await context.route("**/*", handle_route)
            
            page = await context.new_page()
            
            for path in priority_paths[:8]:  # Limit to 8 pages for performance
                try:
                    url = urljoin(website_url, path)
                    
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    
                    if response and response.status < 400:
                        # Extract page content
                        text_content = await page.evaluate("() => document.body.innerText")
                        html_content = await page.content()
                        
                        content_data['content'] += f"\n\n=== PAGE: {url} ===\n{text_content}\n\n=== HTML: ===\n{html_content}\n\n"
                        content_data['pages_analyzed'] += 1
                        
                        # Stop if we have enough content
                        if len(content_data['content']) > 50000:  # 50KB limit
                            break
                        
                except Exception as e:
                    logger.debug(f"Failed to fetch {url}: {e}")
                    continue
            
            await browser.close()
        
        logger.info(f"Fetched content from {content_data['pages_analyzed']} pages")
        return content_data
    
    async def _enrich_executive_with_contacts(self, exec_data: Dict, content: str, company_name: str, website_url: str) -> Optional[ExecutiveContact]:
        """Enrich executive with contact information from content"""
        
        try:
            name = exec_data['name']
            title = exec_data['title']
            
            # Extract contact information near the executive's name
            email = self._find_executive_email(name, content, website_url)
            phone = self._find_executive_phone(name, content)
            linkedin = self._find_executive_linkedin(name, content)
            
            # Calculate confidence based on contact completeness
            contact_count = sum(1 for contact in [email, phone, linkedin] if contact)
            confidence = exec_data['confidence'] + (contact_count * 0.1)
            
            exec_contact = ExecutiveContact(
                name=name,
                title=title,
                company_name=company_name,
                website_url=website_url,
                email=email,
                phone=phone,
                linkedin_url=linkedin,
                confidence_score=min(confidence, 1.0),
                discovery_sources=["enhanced_content_extraction"],
                discovery_method="fallback_real_extraction",
                validation_notes=f"Contacts found: {contact_count}/3"
            )
            
            return exec_contact
            
        except Exception as e:
            logger.warning(f"Failed to enrich executive {exec_data.get('name', 'Unknown')}: {e}")
            return None
    
    def _find_executive_email(self, name: str, content: str, website_url: str) -> Optional[str]:
        """Enhanced email extraction with better pattern matching"""
        
        # Extract domain for context
        domain = website_url.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
        company_domain = domain.split('.')[0] if '.' in domain else domain
        
        # Enhanced email patterns
        email_patterns = [
            # Direct name-based emails
            rf'\b{re.escape(name.lower().replace(" ", ""))}@[\w\.-]+\.\w+',
            rf'\b{re.escape(name.lower().replace(" ", "."))}@[\w\.-]+\.\w+',
            rf'\b{re.escape(name.split()[0].lower())}\.{re.escape(name.split()[1].lower())}@[\w\.-]+\.\w+',
            rf'\b{re.escape(name.split()[0].lower())}{re.escape(name.split()[1].lower())}@[\w\.-]+\.\w+',
            # First name only
            rf'\b{re.escape(name.split()[0].lower())}@[\w\.-]+\.\w+',
            # Company-specific patterns
            rf'\b[\w\.-]*@{re.escape(domain)}',
            rf'\b[\w\.-]*@[\w\.-]*{re.escape(company_domain)}[\w\.-]*\.\w+',
            # General business emails
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Z|a-z]{2,}',
        ]
        
        for pattern in email_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                email = match.group().lower()
                # Validate email format and relevance
                if self._is_valid_business_email(email, name, domain):
                    return email
        
        return None
    
    def _is_valid_business_email(self, email: str, name: str, domain: str) -> bool:
        """Validate if email is a legitimate business email"""
        email_lower = email.lower()
        
        # Skip obvious spam/generic emails
        spam_indicators = ['noreply', 'donotreply', 'info@example', 'test@', 'admin@test', 'user@domain']
        for indicator in spam_indicators:
            if indicator in email_lower:
                return False
        
        # Prefer emails from the company domain
        if domain in email_lower:
            return True
        
        # Check if email contains name components
        name_parts = [part.lower() for part in name.split()]
        for part in name_parts:
            if len(part) > 2 and part in email_lower:
                return True
        
        # Accept professional email domains
        professional_domains = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com', 'live.com']
        email_domain = email_lower.split('@')[1] if '@' in email_lower else ''
        
        return email_domain in professional_domains or len(email_domain.split('.')) >= 2
    
    def _find_executive_phone(self, name: str, content: str) -> Optional[str]:
        """Find phone number for specific executive"""
        
        # UK phone patterns
        phone_patterns = [
            r'(\+44\s?)?(\(?0\d{4}\)?\s?\d{3}\s?\d{3})',  # UK landline
            r'(\+44\s?)?(\(?0\d{3}\)?\s?\d{3}\s?\d{4})',  # UK mobile
            r'(\+44\s?)?\d{2}\s?\d{4}\s?\d{4,6}',         # General UK
        ]
        
        # Find content around the name
        name_pos = content.lower().find(name.lower())
        if name_pos != -1:
            context_start = max(0, name_pos - 300)
            context_end = min(len(content), name_pos + len(name) + 300)
            context = content[context_start:context_end]
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, context)
                if matches:
                    # Return the first valid phone number
                    phone = ''.join(matches[0]) if isinstance(matches[0], tuple) else matches[0]
                    return phone.strip()
        
        return None
    
    def _find_executive_linkedin(self, name: str, content: str) -> Optional[str]:
        """Enhanced LinkedIn profile extraction"""
        
        # LinkedIn URL patterns
        linkedin_patterns = [
            # Direct LinkedIn URLs
            r'https?://(?:www\.)?linkedin\.com/in/[\w\-]+/?',
            r'linkedin\.com/in/[\w\-]+/?',
            # Profile mentions
            rf'linkedin\.com/in/[\w\-]*{re.escape(name.lower().replace(" ", "-"))}[\w\-]*/?',
            rf'linkedin\.com/in/[\w\-]*{re.escape(name.lower().replace(" ", ""))}[\w\-]*/?',
            rf'linkedin\.com/in/[\w\-]*{re.escape(name.split()[0].lower())}[\w\-]*/?',
            # General LinkedIn mentions with names nearby
            r'(?:(?:linkedin|connect|profile)(?:\s+(?:with|on|at))?(?:\s+me)?(?:\s+on)?)\s*:?\s*(https?://(?:www\.)?linkedin\.com/in/[\w\-]+/?)',
        ]
        
        for pattern in linkedin_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                linkedin_url = match.group()
                if 'linkedin.com/in/' in linkedin_url.lower():
                    # Clean up the URL
                    if not linkedin_url.startswith('http'):
                        linkedin_url = 'https://' + linkedin_url
                    
                    # Validate it looks like a real profile
                    if self._is_valid_linkedin_url(linkedin_url, name):
                        return linkedin_url
        
        # Look for LinkedIn mentions near the executive's name
        name_context_patterns = [
            rf'{re.escape(name)}.{{0,50}}(?:linkedin|connect|profile)',
            rf'(?:linkedin|connect|profile).{{0,50}}{re.escape(name)}',
        ]
        
        for pattern in name_context_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                context = match.group()
                # Look for LinkedIn URLs in this context
                linkedin_match = re.search(r'https?://(?:www\.)?linkedin\.com/in/[\w\-]+/?', context)
                if linkedin_match:
                    return linkedin_match.group()
        
        return None
    
    def _is_valid_linkedin_url(self, url: str, name: str) -> bool:
        """Validate if LinkedIn URL is legitimate"""
        url_lower = url.lower()
        
        # Basic format check
        if 'linkedin.com/in/' not in url_lower:
            return False
        
        # Extract profile identifier
        profile_id = url_lower.split('linkedin.com/in/')[1].split('/')[0]
        
        # Skip obviously fake profiles
        fake_indicators = ['example', 'test', 'user', 'profile', 'sample', 'demo']
        for indicator in fake_indicators:
            if indicator in profile_id:
                return False
        
        # Prefer profiles that contain name components
        name_parts = [part.lower() for part in name.split()]
        for part in name_parts:
            if len(part) > 2 and (part in profile_id or part.replace('a', '').replace('e', '') in profile_id):
                return True
        
        # Accept if it looks like a real profile (has reasonable length and format)
        return len(profile_id) >= 3 and len(profile_id) <= 50 and profile_id.replace('-', '').isalnum()
    
    def _validate_and_score_executives(self, executives: List[ExecutiveContact]) -> List[ExecutiveContact]:
        """Validate and score executives based on contact completeness"""
        
        validated_executives = []
        
        for exec in executives:
            # Skip if no name
            if not exec.name or len(exec.name.strip()) < 3:
                continue
            
            # Calculate contact score
            contact_score = 0
            if exec.email:
                contact_score += 0.4
            if exec.phone:
                contact_score += 0.3
            if exec.linkedin_url:
                contact_score += 0.3
            
            # Update confidence based on contact completeness
            exec.confidence_score = min(exec.confidence_score + contact_score, 1.0)
            
            # Only include executives with reasonable confidence
            if exec.confidence_score >= 0.5:
                validated_executives.append(exec)
        
        # Sort by confidence score (highest first)
        validated_executives.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return validated_executives[:8]  # Limit to top 8 executives
    
    async def _step1_identify_company(self, website_url: str) -> CompanyIdentification:
        """Step 1: Identify Company on Website using enhanced URL handling and robots.txt bypass"""
        
        normalized_url = self._normalize_url(website_url)
        parsed_url = urlparse(normalized_url)
        domain = parsed_url.netloc or parsed_url.path
        
        company_data = CompanyIdentification(
            name="",
            domain=domain,
            website_url=website_url,
            actual_url=normalized_url,
            extraction_method="enhanced_playwright_scraping"
        )
        
        # Try different URL variations to find the working one
        url_variations = await self._try_url_variations(normalized_url)
        
        for attempt_url in url_variations:
            try:
                logger.info(f"Attempting to extract from: {attempt_url}")
                
                async with async_playwright() as playwright:
                    browser = await playwright.chromium.launch(
                        headless=True,
                        args=[
                            '--no-sandbox',
                            '--disable-web-security',
                            '--disable-features=VizDisplayCompositor',
                            '--ignore-certificate-errors',
                            '--ignore-ssl-errors',
                            '--ignore-certificate-errors-spki-list'
                        ]
                    )
                    
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        ignore_https_errors=True,
                        bypass_csp=True,
                        java_script_enabled=True
                    )
                    
                    # IMPORTANT: Ignore robots.txt by intercepting requests
                    async def handle_route(route):
                        url = route.request.url
                        # Block robots.txt requests to effectively ignore them
                        if url.endswith('/robots.txt'):
                            await route.abort()
                        else:
                            await route.continue_()
                    
                    # Route all requests through our handler to ignore robots.txt
                    await context.route("**/*", handle_route)
                    
                    page = await context.new_page()
                    
                    # Enhanced navigation with retry logic
                    try:
                        response = await page.goto(
                            attempt_url, 
                            wait_until="domcontentloaded", 
                            timeout=30000
                        )
                        
                        # Check if we got a successful response
                        if response and response.status < 400:
                            logger.info(f"Successfully loaded: {attempt_url} (Status: {response.status})")
                            
                            # Update the actual working URL
                            company_data.actual_url = attempt_url
                            
                            # Extract company name using enhanced patterns
                            title = await page.title()
                            if title and 3 < len(title) < 100:
                                # Clean up title to extract company name
                                company_name = re.sub(r'\s*[-|–]\s*.+$', '', title).strip()
                                company_name = re.sub(r'\s*\|\s*.+$', '', company_name).strip()
                                company_data.name = company_name
                            else:
                                # Fallback: try meta description or domain
                                meta_desc = await page.get_attribute('meta[name="description"]', 'content')
                                if meta_desc and len(meta_desc) > 10:
                                    # Extract potential company name from description
                                    words = meta_desc.split()[:5]  # First 5 words
                                    company_data.name = ' '.join(words).strip()
                                else:
                                    # Final fallback to domain
                                    company_data.name = domain.replace('www.', '').replace('.com', '').replace('.co.uk', '')
                            
                            # Try to extract additional info with enhanced selectors
                            try:
                                # Look for phone numbers with multiple patterns
                                phone_selectors = [
                                    'a[href^="tel:"]',
                                    '*[class*="phone"]',
                                    '*[class*="contact"]',
                                    '*:has-text("Tel:")',
                                    '*:has-text("Phone:")',
                                    '*:has-text("Call:")'
                                ]
                                
                                for selector in phone_selectors:
                                    try:
                                        phone_element = await page.query_selector(selector)
                                        if phone_element:
                                            if selector.startswith('a[href^="tel:"]'):
                                                href = await phone_element.get_attribute('href')
                                                if href:
                                                    company_data.phone = href.replace('tel:', '').strip()
                                                    break
                                            else:
                                                text = await phone_element.text_content()
                                                if text and re.search(r'\d{10,}', text):
                                                    company_data.phone = text.strip()
                                                    break
                                    except:
                                        continue
                            except:
                                pass
                            
                            # Set confidence based on extraction quality
                            if len(company_data.name) > 10 and not any(x in company_data.name.lower() for x in ['error', 'not found', 'coming soon']):
                                company_data.confidence = 0.8
                            elif len(company_data.name) > 3:
                                company_data.confidence = 0.6
                            else:
                                company_data.confidence = 0.3
                            
                            company_data.extraction_method = "enhanced_successful_extraction"
                            
                            await browser.close()
                            return company_data
                        
                    except Exception as nav_error:
                        logger.warning(f"Navigation failed for {attempt_url}: {nav_error}")
                        continue
                    finally:
                        await browser.close()
                        
            except Exception as e:
                logger.warning(f"Browser setup failed for {attempt_url}: {e}")
                continue
        
        # If all URLs failed, use domain fallback
        logger.warning(f"All URL variations failed, using domain fallback for {website_url}")
        company_data.name = domain.replace('www.', '').replace('.com', '').replace('.co.uk', '')
        company_data.confidence = 0.3
        company_data.extraction_method = "domain_fallback"
        company_data.actual_url = normalized_url
        
        return company_data
    
    async def _step2_companies_house_verification(self, company_name: str) -> tuple[List[ExecutiveContact], bool]:
        """Step 2: Retrieve official company information and directors from Companies House"""
        
        companies_house_executives = []
        companies_house_verified = False
        
        try:
            if not self.companies_house_enricher:
                logger.warning("Companies House enricher not available, skipping official data lookup")
                return companies_house_executives, companies_house_verified
            
            logger.info(f"Looking up official directors for {company_name} in Companies House")
            
            # Use Companies House enricher to discover executives
            ch_executives = await self.companies_house_enricher.discover_executives(company_name)
            
            if ch_executives:
                logger.info(f"Companies House found {len(ch_executives)} official directors for {company_name}")
                companies_house_verified = True
                
                # Convert to our ExecutiveContact format and mark as official
                for exec_contact in ch_executives:
                    # Mark as Companies House verified with highest confidence
                    exec_contact.confidence_score = 1.0  # Official government data = highest confidence
                    exec_contact.discovery_sources.append("companies_house_official")
                    exec_contact.discovery_method = "companies_house_api"
                    exec_contact.validation_notes = f"Official UK Government director data - Verified by Companies House"
                    
                    companies_house_executives.append(exec_contact)
                
                logger.info(f"Successfully retrieved {len(companies_house_executives)} official directors from Companies House")
            else:
                logger.info(f"No official directors found in Companies House for {company_name}")
            
        except Exception as e:
            logger.error(f"Companies House lookup failed for {company_name}: {e}")
        
        return companies_house_executives, companies_house_verified
    
    def _merge_companies_house_and_website_executives(
        self, 
        ch_executives: List[ExecutiveContact], 
        website_executives: List[ExecutiveContact],
        company_name: str
    ) -> List[ExecutiveContact]:
        """Merge Companies House directors with website-discovered executives, giving priority to official data"""
        
        merged_executives = []
        
        # Step 1: Add all Companies House executives first (highest authority)
        for ch_exec in ch_executives:
            merged_executives.append(ch_exec)
            logger.info(f"Added official director: {ch_exec.name} ({ch_exec.title}) - Companies House verified")
        
        # Step 2: Add website executives that don't duplicate Companies House data
        for web_exec in website_executives:
            # Check if this executive is already represented in Companies House data
            is_duplicate = False
            
            for ch_exec in ch_executives:
                # Check name similarity (allowing for slight variations)
                name_similarity = self._calculate_name_similarity(ch_exec.name, web_exec.name)
                if name_similarity > 0.8:  # 80% similarity threshold
                    # This is likely the same person - enrich Companies House data with website contact info
                    if web_exec.email and not ch_exec.email:
                        ch_exec.email = web_exec.email
                        ch_exec.discovery_sources.append("website_contact_enrichment")
                        logger.info(f"Enriched Companies House director {ch_exec.name} with email: {web_exec.email}")
                    
                    if web_exec.phone and not ch_exec.phone:
                        ch_exec.phone = web_exec.phone
                        ch_exec.discovery_sources.append("website_contact_enrichment")
                        logger.info(f"Enriched Companies House director {ch_exec.name} with phone: {web_exec.phone}")
                    
                    if web_exec.linkedin_url and not ch_exec.linkedin_url:
                        ch_exec.linkedin_url = web_exec.linkedin_url
                        ch_exec.discovery_sources.append("website_contact_enrichment")
                        logger.info(f"Enriched Companies House director {ch_exec.name} with LinkedIn: {web_exec.linkedin_url}")
                    
                    is_duplicate = True
                    break
            
            # If not a duplicate, add as additional executive (e.g., employees, managers not registered as directors)
            if not is_duplicate:
                # Mark as website-discovered to distinguish from official directors
                web_exec.discovery_sources.append("website_extraction")
                web_exec.validation_notes = f"Website-discovered executive (not registered as Companies House director)"
                merged_executives.append(web_exec)
                logger.info(f"Added website executive: {web_exec.name} ({web_exec.title}) - Website discovery")
        
        logger.info(f"Final executive list: {len(merged_executives)} total executives ({len(ch_executives)} official directors + {len(merged_executives) - len(ch_executives)} website-discovered)")
        
        return merged_executives
