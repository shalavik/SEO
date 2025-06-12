"""
Lead Qualification System

Multi-factor scoring matrix with business intelligence and tier classification.
Qualifies leads based on SEO opportunity, business size, sector fit, and contact quality.

Based on creative design decisions:
- Multi-factor scoring (SEO 35%, Business Size 25%, Sector Fit 20%, Growth 10%, Contact 10%)
- A-D tier classification with business context
- Outreach intelligence generation
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..config import get_processing_config
from ..database import get_db_session
from ..models import (
    UKCompany, LeadQualification, FactorBreakdown, OutreachIntelligence, 
    PriorityTier, SCORING_WEIGHTS, SECTOR_SEO_DEPENDENCY
)

logger = logging.getLogger(__name__)

class LeadQualifier:
    """
    Multi-factor lead qualification with tier classification
    
    Features:
    - SEO opportunity assessment (35% weight)
    - Business size evaluation (25% weight) 
    - Sector fit analysis (20% weight)
    - Growth indicators (10% weight)
    - Contact quality scoring (10% weight)
    - A-D tier classification
    - Outreach intelligence generation
    """
    
    def __init__(self):
        self.processing_config = get_processing_config()
        self.scoring_weights = SCORING_WEIGHTS
    
    def qualify_lead(self, company_id: str) -> Optional[LeadQualification]:
        """
        Qualify a single lead using multi-factor scoring
        
        Args:
            company_id: Unique company identifier
            
        Returns:
            LeadQualification with scores and tier classification
        """
        try:
            with get_db_session() as session:
                company = session.query(UKCompany).filter_by(id=company_id).first()
                
                if not company:
                    logger.error(f"Company {company_id} not found")
                    return None
                
                logger.info(f"Qualifying lead for {company.company_name}")
                
                # Calculate individual factor scores
                factors = {
                    'seo_opportunity': self._score_seo_opportunity(company),
                    'business_size': self._score_business_size(company), 
                    'sector_fit': self._score_sector_fit(company),
                    'growth_indicators': self._score_growth_indicators(company),
                    'contact_quality': self._score_contact_quality(company)
                }
                
                # Calculate weighted final score
                final_score = 0.0
                factor_breakdown = {}
                
                for factor, score_data in factors.items():
                    weight = self.scoring_weights[factor]
                    contribution = score_data['score'] * weight
                    final_score += contribution
                    
                    factor_breakdown[factor] = FactorBreakdown(
                        score=score_data['score'],
                        weight=weight,
                        contribution=contribution
                    )
                
                # Determine priority tier
                priority_tier, tier_label = self._determine_tier(final_score)
                
                # Create qualification result
                qualification = LeadQualification(
                    final_score=final_score,
                    priority_tier=priority_tier,
                    tier_label=tier_label,
                    factor_breakdown=factor_breakdown,
                    confidence=self._calculate_qualification_confidence(factors)
                )
                
                # Generate outreach intelligence
                outreach_intel = self._generate_outreach_intelligence(company, qualification)
                
                # Update database
                self._update_company_qualification_data(company, qualification, outreach_intel)
                
                logger.info(f"Lead qualification complete for {company.company_name}: "
                          f"Score {final_score:.1f}, Tier {tier_label}")
                
                return qualification
                
        except Exception as e:
            logger.error(f"Error qualifying lead {company_id}: {e}")
            return None
    
    def _score_seo_opportunity(self, company: UKCompany) -> Dict:
        """Score SEO improvement opportunity (35% weight)"""
        if not company.seo_overall_score:
            return {'score': 0.0, 'reason': 'No SEO analysis available'}
        
        seo_score = company.seo_overall_score
        
        # Invert score - lower SEO = higher opportunity
        if seo_score <= 30:
            opportunity_score = 100  # Terrible SEO = Great opportunity
        elif seo_score <= 50:
            opportunity_score = 80   # Poor SEO = Good opportunity  
        elif seo_score <= 70:
            opportunity_score = 60   # Mediocre SEO = Moderate opportunity
        else:
            opportunity_score = 20   # Good SEO = Low opportunity
        
        # Boost score if critical issues present
        if company.critical_issues and len(company.critical_issues) > 3:
            opportunity_score = min(100, opportunity_score + 20)
        
        reason = f"SEO score {seo_score:.1f} indicates {'high' if opportunity_score >= 80 else 'moderate' if opportunity_score >= 60 else 'low'} opportunity"
        
        return {'score': opportunity_score, 'reason': reason}
    
    def _score_business_size(self, company: UKCompany) -> Dict:
        """Score business size and revenue potential (25% weight)"""
        size_scores = {
            'large': 90,    # High budget, big impact
            'medium': 70,   # Good budget, solid opportunity
            'small': 50,    # Limited budget, quick wins
            'micro': 30     # Very limited budget
        }
        
        if company.employees:
            if company.employees >= 100:
                size = 'large'
            elif company.employees >= 20:
                size = 'medium'
            elif company.employees >= 5:
                size = 'small'
            else:
                size = 'micro'
        else:
            # Estimate based on company size category if available
            size = company.size_category or 'small'  # Default to small
        
        score = size_scores.get(size, 50)
        reason = f"Company size '{size}' ({company.employees or 'unknown'} employees)"
        
        return {'score': score, 'reason': reason}
    
    def _score_sector_fit(self, company: UKCompany) -> Dict:
        """Score sector SEO dependency and fit (20% weight)"""
        if not company.sector:
            return {'score': 50, 'reason': 'Unknown sector'}
        
        # Get sector SEO dependency
        dependency = SECTOR_SEO_DEPENDENCY.get(company.sector, 75)  # Default 75
        
        # Convert dependency to score (higher dependency = higher score)
        if dependency >= 90:
            score = 95      # Critical SEO dependency
        elif dependency >= 80:
            score = 80      # High SEO dependency
        elif dependency >= 70:
            score = 65      # Moderate SEO dependency
        else:
            score = 45      # Lower SEO dependency
        
        reason = f"Sector '{company.sector}' has {dependency}% SEO dependency"
        
        return {'score': score, 'reason': reason}
    
    def _score_growth_indicators(self, company: UKCompany) -> Dict:
        """Score business growth indicators (10% weight)"""
        score = 50  # Default neutral score
        indicators = []
        
        # Website quality indicates investment
        if company.website and not company.meta_description_missing:
            score += 15
            indicators.append("professional website")
        
        # Social media presence
        if company.linkedin_url:
            score += 10
            indicators.append("LinkedIn presence")
        
        # Modern tech adoption
        if company.ssl_certificate:
            score += 10
            indicators.append("SSL certificate")
        
        # Mobile optimization
        if company.mobile_friendly:
            score += 15
            indicators.append("mobile-friendly site")
        
        score = min(100, score)
        reason = f"Growth indicators: {', '.join(indicators) if indicators else 'limited indicators'}"
        
        return {'score': score, 'reason': reason}
    
    def _score_contact_quality(self, company: UKCompany) -> Dict:
        """Score contact information quality (10% weight)"""
        score = 0
        contact_elements = []
        
        # Contact confidence from extraction
        if company.contact_confidence:
            score += company.contact_confidence * 50  # Scale to 0-50
        
        # Email availability
        if company.email:
            score += 25
            contact_elements.append("email")
        
        # Phone availability  
        if company.phone:
            score += 15
            contact_elements.append("phone")
        
        # LinkedIn profile
        if company.linkedin_url:
            score += 10
            contact_elements.append("LinkedIn")
        
        # Decision maker identification
        if company.contact_person and company.contact_role:
            score += 20
            contact_elements.append("decision maker identified")
        
        score = min(100, score)
        reason = f"Contact quality: {', '.join(contact_elements) if contact_elements else 'limited contact info'}"
        
        return {'score': score, 'reason': reason}
    
    def _determine_tier(self, final_score: float) -> Tuple[PriorityTier, str]:
        """Determine priority tier based on final score"""
        if final_score >= 80:
            return PriorityTier.A, "Hot Lead - Immediate Action"
        elif final_score >= 65:
            return PriorityTier.B, "Warm Lead - High Priority"
        elif final_score >= 50:
            return PriorityTier.C, "Qualified Lead - Standard Priority"
        else:
            return PriorityTier.D, "Low Priority - Long Term"
    
    def _calculate_qualification_confidence(self, factors: Dict) -> float:
        """Calculate confidence in qualification based on data quality"""
        confidence = 0.8  # Base confidence
        
        # Reduce confidence if key data missing
        if not factors['seo_opportunity']['score']:
            confidence -= 0.2
        
        if not factors['contact_quality']['score']:
            confidence -= 0.1
        
        return max(0.5, confidence)
    
    def _generate_outreach_intelligence(self, company: UKCompany, 
                                      qualification: LeadQualification) -> OutreachIntelligence:
        """Generate outreach automation intelligence"""
        
        # Determine urgency
        if qualification.priority_tier == PriorityTier.A:
            urgency = "high"
        elif qualification.priority_tier == PriorityTier.B:
            urgency = "medium"
        else:
            urgency = "low"
        
        # Estimate value
        if qualification.final_score >= 80:
            estimated_value = "£2,000-5,000/month"
        elif qualification.final_score >= 65:
            estimated_value = "£1,000-3,000/month"
        elif qualification.final_score >= 50:
            estimated_value = "£500-1,500/month"
        else:
            estimated_value = "£300-800/month"
        
        # Generate recommended actions
        actions = []
        if company.seo_overall_score and company.seo_overall_score < 50:
            actions.append("Offer free SEO audit")
        if company.meta_description_missing:
            actions.append("Highlight missing meta descriptions")
        if not company.mobile_friendly:
            actions.append("Emphasize mobile optimization")
        if company.load_time and company.load_time > 3:
            actions.append("Focus on page speed improvements")
        
        # Generate talking points
        talking_points = []
        if company.sector:
            talking_points.append(f"Industry expertise in {company.sector}")
        if company.city:
            talking_points.append(f"Local SEO for {company.city} market")
        if company.seo_overall_score:
            talking_points.append(f"Current SEO score {company.seo_overall_score:.0f}/100 - significant room for improvement")
        
        return OutreachIntelligence(
            urgency=urgency,
            estimated_value=estimated_value,
            recommended_actions=actions,
            talking_points=talking_points,
            follow_up_schedule={
                "initial_contact": "within 24 hours" if urgency == "high" else "within 72 hours",
                "follow_up_1": "3 days after initial",
                "follow_up_2": "1 week after follow_up_1"
            }
        )
    
    def _update_company_qualification_data(self, company: UKCompany, 
                                         qualification: LeadQualification,
                                         outreach_intel: OutreachIntelligence):
        """Update company record with qualification results"""
        try:
            with get_db_session() as session:
                # Refresh company object in current session
                company = session.merge(company)
                
                # Update qualification fields
                company.lead_score = qualification.final_score
                company.priority_tier = qualification.priority_tier.value
                company.tier_label = qualification.tier_label
                
                # Store factor breakdown as JSON
                factor_data = {}
                for factor, breakdown in qualification.factor_breakdown.items():
                    factor_data[factor] = {
                        'score': breakdown.score,
                        'weight': breakdown.weight,
                        'contribution': breakdown.contribution
                    }
                company.factor_breakdown = factor_data
                
                # Store outreach intelligence
                company.estimated_value = outreach_intel.estimated_value
                company.urgency = outreach_intel.urgency
                company.recommended_actions = outreach_intel.recommended_actions
                company.talking_points = outreach_intel.talking_points
                
                # Update status
                if company.status in ['seo_analyzed', 'contacts_extracted']:
                    company.status = 'qualified'
                
                session.commit()
                logger.debug(f"Updated qualification data for company {company.id}")
                
        except Exception as e:
            logger.error(f"Error updating company qualification data: {e}")
    
    def qualify_batch(self, batch_size: int = 50) -> int:
        """Qualify a batch of leads"""
        try:
            with get_db_session() as session:
                # Get companies needing qualification
                companies = session.query(UKCompany).filter(
                    UKCompany.status.in_(['seo_analyzed', 'contacts_extracted']),
                    UKCompany.seo_overall_score.isnot(None)
                ).limit(batch_size).all()
                
                if not companies:
                    logger.info("No companies found needing qualification")
                    return 0
                
                logger.info(f"Starting lead qualification for {len(companies)} companies")
                qualified_count = 0
                
                for company in companies:
                    try:
                        qualification = self.qualify_lead(company.id)
                        
                        if qualification:
                            qualified_count += 1
                            logger.info(f"Qualified {company.company_name}: "
                                      f"Score {qualification.final_score:.1f}, "
                                      f"Tier {qualification.tier_label}")
                        
                    except Exception as e:
                        logger.error(f"Error qualifying {company.company_name}: {e}")
                        continue
                
                logger.info(f"Lead qualification complete: {qualified_count}/{len(companies)} qualified")
                return qualified_count
                
        except Exception as e:
            logger.error(f"Error in lead qualification batch: {e}")
            return 0

# Convenience function
def qualify_leads_batch(batch_size: int = 50) -> int:
    """Convenience function to qualify a batch of leads"""
    qualifier = LeadQualifier()
    return qualifier.qualify_batch(batch_size) 