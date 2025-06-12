"""
Director Enrichment Engine

Main orchestration service that coordinates:
- Smart lead filtering
- Free data collection (Companies House, LinkedIn)
- Paid enhancement decisions
- Cost tracking and optimization
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..core.director_models import (
    DirectorEnrichmentResult, DirectorProfile, Director, EnrichmentDecision,
    ConfidenceReport, FreeDataBundle, EnhancedDataBundle, DataSource,
    EnrichmentConfig, CostTrackingEntry, EmailCandidate, VerifiedEmail,
    PhoneNumber, ContactHints
)
from ..services.smart_lead_filter import SmartLeadFilter
from ..providers.companies_house import CompaniesHouseService
from ..providers.linkedin_scraper import LinkedInScraperService

logger = logging.getLogger(__name__)


class ConfidenceAssessor:
    """Assess data completeness and confidence"""
    
    def __init__(self):
        pass
    
    def assess_director_confidence(self, director: Director) -> float:
        """Assess confidence in director identification"""
        confidence = 0.0
        
        # Name completeness
        if director.full_name:
            confidence += 0.3
        if director.first_name and director.last_name:
            confidence += 0.2
        
        # Role clarity
        if director.role:
            confidence += 0.2
        
        # Company association
        if director.company_number:
            confidence += 0.2
        
        # Activity status
        if director.is_active:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def assess_contact_confidence(self, profile: DirectorProfile) -> Dict[str, float]:
        """Assess confidence in contact information"""
        email_confidence = 0.0
        phone_confidence = 0.0
        linkedin_confidence = 0.0
        
        # Email confidence
        if profile.verified_emails:
            email_confidence = max(email.confidence for email in profile.verified_emails)
        elif profile.email_candidates:
            email_confidence = max(email.confidence for email in profile.email_candidates) * 0.7
        
        # Phone confidence
        if profile.phone_numbers:
            phone_confidence = max(phone.confidence for phone in profile.phone_numbers)
        
        # LinkedIn confidence
        if profile.linkedin_profile:
            linkedin_confidence = profile.linkedin_profile.confidence
        
        return {
            "email": email_confidence,
            "phone": phone_confidence,
            "linkedin": linkedin_confidence
        }
    
    def create_confidence_report(self, profiles: List[DirectorProfile]) -> ConfidenceReport:
        """Create comprehensive confidence report"""
        if not profiles:
            return ConfidenceReport(
                overall_confidence=0.0,
                director_identified=0.0,
                email_available=0.0,
                phone_available=0.0,
                linkedin_profile=0.0,
                data_gaps=["No directors found"],
                needs_paid_enhancement=False,
                recommended_actions=["Retry with different search terms"],
                estimated_enhancement_cost=0.0
            )
        
        # Calculate averages
        director_confidences = [self.assess_director_confidence(p.director) for p in profiles]
        avg_director_confidence = sum(director_confidences) / len(director_confidences)
        
        contact_confidences = [self.assess_contact_confidence(p) for p in profiles]
        avg_email_confidence = sum(c["email"] for c in contact_confidences) / len(contact_confidences)
        avg_phone_confidence = sum(c["phone"] for c in contact_confidences) / len(contact_confidences)
        avg_linkedin_confidence = sum(c["linkedin"] for c in contact_confidences) / len(contact_confidences)
        
        overall_confidence = (
            avg_director_confidence * 0.4 +
            avg_email_confidence * 0.3 +
            avg_phone_confidence * 0.2 +
            avg_linkedin_confidence * 0.1
        )
        
        # Identify data gaps
        data_gaps = []
        if avg_email_confidence < 0.7:
            data_gaps.append("email")
        if avg_phone_confidence < 0.5:
            data_gaps.append("phone")
        if avg_linkedin_confidence < 0.6:
            data_gaps.append("linkedin_premium")
        
        # Determine if paid enhancement is needed
        needs_paid_enhancement = len(data_gaps) > 0 and overall_confidence < 0.8
        
        # Recommend actions
        recommended_actions = []
        if "email" in data_gaps:
            recommended_actions.append("Use paid email verification service")
        if "phone" in data_gaps:
            recommended_actions.append("Use phone lookup service")
        if "linkedin_premium" in data_gaps:
            recommended_actions.append("Access LinkedIn premium data")
        
        # Estimate enhancement cost
        enhancement_cost = 0.0
        if "email" in data_gaps:
            enhancement_cost += 0.10
        if "phone" in data_gaps:
            enhancement_cost += 0.25
        if "linkedin_premium" in data_gaps:
            enhancement_cost += 0.50
        
        return ConfidenceReport(
            overall_confidence=overall_confidence,
            director_identified=avg_director_confidence,
            email_available=avg_email_confidence,
            phone_available=avg_phone_confidence,
            linkedin_profile=avg_linkedin_confidence,
            data_gaps=data_gaps,
            needs_paid_enhancement=needs_paid_enhancement,
            recommended_actions=recommended_actions,
            estimated_enhancement_cost=enhancement_cost
        )


class FreeDataCollector:
    """Collect data from free sources in parallel"""
    
    def __init__(self, companies_house_api_key: str, linkedin_rate_limit: int = 10):
        self.companies_house = CompaniesHouseService(companies_house_api_key)
        self.linkedin_scraper = LinkedInScraperService(linkedin_rate_limit)
    
    async def collect_free_data(self, company_name: str) -> FreeDataBundle:
        """Collect data from all free sources in parallel"""
        start_time = datetime.now()
        
        # Run all free sources in parallel
        tasks = [
            self.companies_house.find_company_directors(company_name),
            # Add other free sources here
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        all_directors = []
        all_linkedin_profiles = []
        all_contact_hints = []
        all_email_candidates = []
        all_phone_candidates = []
        all_sources = []
        all_errors = []
        
        for result in results:
            if isinstance(result, Exception):
                all_errors.append(str(result))
                continue
            
            if isinstance(result, FreeDataBundle):
                all_directors.extend(result.directors)
                all_linkedin_profiles.extend(result.linkedin_profiles)
                all_contact_hints.extend(result.contact_hints)
                all_email_candidates.extend(result.email_candidates)
                all_phone_candidates.extend(result.phone_candidates)
                all_sources.extend(result.sources_used)
                all_errors.extend(result.errors)
        
        # Get LinkedIn profiles for directors
        if all_directors:
            try:
                linkedin_data = await self.linkedin_scraper.find_director_profiles(
                    all_directors, company_name
                )
                all_linkedin_profiles.extend(linkedin_data.linkedin_profiles)
                all_contact_hints.extend(linkedin_data.contact_hints)
                all_sources.extend(linkedin_data.sources_used)
                all_errors.extend(linkedin_data.errors)
            except Exception as e:
                all_errors.append(f"LinkedIn scraping error: {e}")
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return FreeDataBundle(
            directors=all_directors,
            linkedin_profiles=all_linkedin_profiles,
            contact_hints=all_contact_hints,
            email_candidates=all_email_candidates,
            phone_candidates=all_phone_candidates,
            processing_time_ms=processing_time,
            sources_used=list(set(all_sources)),
            errors=all_errors
        )


class DirectorEnrichmentEngine:
    """Main director enrichment orchestration engine"""
    
    def __init__(self, config: EnrichmentConfig, companies_house_api_key: str):
        self.config = config
        self.lead_filter = SmartLeadFilter(config)
        self.free_collector = FreeDataCollector(companies_house_api_key, config.linkedin_rate_limit)
        self.confidence_assessor = ConfidenceAssessor()
    
    def _create_director_profiles(self, free_data: FreeDataBundle) -> List[DirectorProfile]:
        """Create director profiles from free data"""
        profiles = []
        
        for director in free_data.directors:
            # Find matching LinkedIn profile
            linkedin_profile = None
            for profile in free_data.linkedin_profiles:
                if director.full_name.lower() in profile.full_name.lower():
                    linkedin_profile = profile
                    break
            
            # Collect contact hints
            contact_hints = free_data.contact_hints
            
            # Calculate confidence
            confidence_score = self.confidence_assessor.assess_director_confidence(director)
            
            # Determine data sources
            data_sources = free_data.sources_used
            
            profile = DirectorProfile(
                director=director,
                email_candidates=[],
                verified_emails=[],
                phone_numbers=[],
                linkedin_profile=linkedin_profile,
                contact_hints=contact_hints,
                confidence_score=confidence_score,
                data_sources=data_sources,
                processing_time_ms=free_data.processing_time_ms,
                total_cost=0.0,
                cost_breakdown={}
            )
            
            profiles.append(profile)
        
        return profiles
    
    def _select_primary_director(self, profiles: List[DirectorProfile]) -> Optional[DirectorProfile]:
        """Select the primary director (highest ranking)"""
        if not profiles:
            return None
        
        # Sort by role priority and confidence
        role_priority = {
            'ceo': 1,
            'managing-director': 2,
            'executive-director': 3,
            'chairman': 4,
            'chief-financial-officer': 5,
            'chief-operating-officer': 6,
            'director': 7,
            'non-executive-director': 8
        }
        
        def sort_key(profile):
            role_score = role_priority.get(profile.director.role.value, 9)
            confidence_score = 1.0 - profile.confidence_score  # Lower is better
            return (role_score, confidence_score)
        
        sorted_profiles = sorted(profiles, key=sort_key)
        return sorted_profiles[0]
    
    async def enrich_company_directors(self, company_name: str, 
                                     lead_score: float,
                                     priority_tier: str,
                                     website: Optional[str] = None) -> DirectorEnrichmentResult:
        """Main enrichment method"""
        start_time = datetime.now()
        
        try:
            # Step 1: Create enrichment decision
            decision = self.lead_filter.create_enrichment_decision(
                lead_score=lead_score,
                priority_tier=priority_tier,
                company_name=company_name
            )
            
            if not decision:
                return DirectorEnrichmentResult(
                    input_company=company_name,
                    input_website=website,
                    director_profiles=[],
                    primary_director=None,
                    enrichment_decision=decision,
                    confidence_report=ConfidenceReport(
                        overall_confidence=0.0,
                        director_identified=0.0,
                        email_available=0.0,
                        phone_available=0.0,
                        linkedin_profile=0.0,
                        data_gaps=["Lead does not qualify for enrichment"],
                        needs_paid_enhancement=False,
                        recommended_actions=[],
                        estimated_enhancement_cost=0.0
                    ),
                    status="skipped",
                    error_message="Lead does not qualify for enrichment",
                    started_at=start_time,
                    total_processing_time_ms=0,
                    total_cost=0.0
                )
            
            # Step 2: Collect free data
            logger.info(f"Collecting free data for {company_name}")
            free_data = await self.free_collector.collect_free_data(company_name)
            
            # Step 3: Create director profiles
            director_profiles = self._create_director_profiles(free_data)
            
            # Step 4: Select primary director
            primary_director = self._select_primary_director(director_profiles)
            
            # Step 5: Final confidence assessment
            final_confidence_report = self.confidence_assessor.create_confidence_report(director_profiles)
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return DirectorEnrichmentResult(
                input_company=company_name,
                input_website=website,
                director_profiles=director_profiles,
                primary_director=primary_director,
                enrichment_decision=decision,
                confidence_report=final_confidence_report,
                processing_summary={
                    "directors_found": len(director_profiles),
                    "linkedin_profiles": len(free_data.linkedin_profiles),
                    "verified_emails": 0,
                    "phone_numbers": 0,
                    "free_sources": len(free_data.sources_used),
                    "paid_sources": 0
                },
                total_processing_time_ms=processing_time,
                total_cost=0.0,
                cost_breakdown={},
                status="completed",
                started_at=start_time
            )
            
        except Exception as e:
            logger.error(f"Error enriching {company_name}: {e}")
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return DirectorEnrichmentResult(
                input_company=company_name,
                input_website=website,
                director_profiles=[],
                primary_director=None,
                enrichment_decision=decision if 'decision' in locals() else None,
                confidence_report=ConfidenceReport(
                    overall_confidence=0.0,
                    director_identified=0.0,
                    email_available=0.0,
                    phone_available=0.0,
                    linkedin_profile=0.0,
                    data_gaps=["Processing error"],
                    needs_paid_enhancement=False,
                    recommended_actions=["Retry enrichment"],
                    estimated_enhancement_cost=0.0
                ),
                status="failed",
                error_message=str(e),
                started_at=start_time,
                total_processing_time_ms=processing_time,
                total_cost=0.0
            )
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status"""
        return self.lead_filter.get_budget_status() 