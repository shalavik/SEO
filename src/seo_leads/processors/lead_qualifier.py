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
import time
import json

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
    
    async def qualify_lead(self, company_data: Dict) -> Optional[LeadQualification]:
        """
        Qualify a lead using multi-factor analysis
        
        Args:
            company_data: Dictionary containing company information and analysis results
            
        Returns:
            LeadQualification object with scores and recommendations
        """
        try:
            start_time = time.time()
            
            # Generate unique company ID for database operations
            company_id = str(hash(f"{company_data.get('company_name', '')}{company_data.get('website', '')}"))
            
            # Extract SEO analysis
            seo_analysis = company_data.get('seo_analysis')
            if not seo_analysis:
                logger.warning(f"No SEO analysis found for {company_data.get('company_name', 'Unknown')}")
                return None
            
            # Extract contact information
            contact_info = company_data.get('contact_info', {})
            
            # Create a serializable company dict for database storage
            db_company_data = {
                'id': company_id,
                'company_name': company_data.get('company_name', ''),
                'website': company_data.get('website', ''),
                'city': company_data.get('city', ''),
                'region': company_data.get('region', ''),
                'sector': company_data.get('sector', ''),
                'source': 'enhanced_pipeline',
                'status': 'processing',
                
                # Contact information
                'contact_person': contact_info.get('person'),
                'contact_role': contact_info.get('role'),
                'contact_seniority_tier': contact_info.get('seniority_tier'),
                'email': contact_info.get('email'),
                'phone': contact_info.get('phone'),
                'contact_confidence': float(contact_info.get('confidence', 0.0)),
                
                # SEO Analysis - extract primitive values
                'seo_overall_score': float(seo_analysis.overall_score) if seo_analysis else 0.0,
                'pagespeed_score': float(seo_analysis.performance.pagespeed_score) if seo_analysis and seo_analysis.performance else 0.0,
                'mobile_friendly': bool(seo_analysis.performance.mobile_friendly) if seo_analysis and seo_analysis.performance else False,
                'meta_description_missing': bool(seo_analysis.content.meta_description_missing) if seo_analysis and seo_analysis.content else True,
                'h1_tags_present': bool(seo_analysis.content.h1_tags_present) if seo_analysis and seo_analysis.content else False,
                'ssl_certificate': bool(seo_analysis.content.ssl_certificate) if seo_analysis and seo_analysis.content else False,
                'load_time': float(seo_analysis.performance.load_time) if seo_analysis and seo_analysis.performance else 0.0,
                'critical_issues': ','.join(seo_analysis.critical_issues) if seo_analysis and seo_analysis.critical_issues else '',
            }
            
            # Check if company already exists in database
            existing_company = await self._get_company_by_id(company_id)
            
            if existing_company:
                logger.debug(f"Company {company_data.get('company_name')} already exists in database")
                # Update existing company with new data
                await self._update_company_data(company_id, db_company_data)
            else:
                # Create new company record
                await self._create_company_record(db_company_data)
            
            # Calculate qualification scores
            seo_score = self._calculate_seo_score(seo_analysis)
            business_score = self._calculate_business_score(company_data)
            sector_score = self._calculate_sector_score(company_data.get('sector', ''))
            growth_score = self._calculate_growth_score(company_data)
            contact_score = self._calculate_contact_score(contact_info)
            
            # Calculate weighted final score
            final_score = (
                seo_score * self.scoring_weights['seo'] +
                business_score * self.scoring_weights['business'] +
                sector_score * self.scoring_weights['sector'] +
                growth_score * self.scoring_weights['growth'] +
                contact_score * self.scoring_weights['contact']
            )
            
            # Determine priority tier
            priority_tier = self._determine_priority_tier(final_score)
            
            # Generate outreach intelligence
            talking_points = self._generate_talking_points(company_data, seo_analysis, priority_tier)
            recommended_actions = self._generate_recommended_actions(priority_tier, seo_analysis, contact_info)
            
            # Create proper FactorBreakdown objects
            from ..models import FactorBreakdown
            factor_breakdown = {
                'seo': FactorBreakdown(
                    score=seo_score,
                    weight=self.scoring_weights['seo'],
                    contribution=seo_score * self.scoring_weights['seo']
                ),
                'business': FactorBreakdown(
                    score=business_score,
                    weight=self.scoring_weights['business'],
                    contribution=business_score * self.scoring_weights['business']
                ),
                'sector': FactorBreakdown(
                    score=sector_score,
                    weight=self.scoring_weights['sector'],
                    contribution=sector_score * self.scoring_weights['sector']
                ),
                'growth': FactorBreakdown(
                    score=growth_score,
                    weight=self.scoring_weights['growth'],
                    contribution=growth_score * self.scoring_weights['growth']
                ),
                'contact': FactorBreakdown(
                    score=contact_score,
                    weight=self.scoring_weights['contact'],
                    contribution=contact_score * self.scoring_weights['contact']
                )
            }
            
            # Create qualification result
            qualification = LeadQualification(
                final_score=final_score,
                priority_tier=priority_tier,
                tier_label=priority_tier.name,
                factor_breakdown=factor_breakdown,
                estimated_value=self._estimate_lead_value(priority_tier),
                urgency=self._calculate_urgency(priority_tier, seo_analysis),
                talking_points=talking_points,
                recommended_actions=recommended_actions
            )
            
            # Update database with qualification results
            qualification_data = {
                'lead_score': float(final_score),
                'priority_tier': priority_tier.value,
                'tier_label': priority_tier.name,
                'factor_breakdown': json.dumps({
                    'seo_score': seo_score,
                    'business_score': business_score,
                    'sector_score': sector_score,
                    'growth_score': growth_score,
                    'contact_score': contact_score
                }),
                'estimated_value': float(self._estimate_lead_value(priority_tier)),
                'urgency': self._calculate_urgency(priority_tier, seo_analysis),
                'recommended_actions': json.dumps(recommended_actions),
                'talking_points': json.dumps(talking_points),
                'status': 'qualified'
            }
            
            await self._update_company_qualification(company_id, qualification_data)
            
            processing_time = time.time() - start_time
            logger.info(f"Lead qualification complete for {company_data.get('company_name')}: {final_score:.1f} (Tier {priority_tier.value}) in {processing_time:.2f}s")
            
            return qualification
            
        except Exception as e:
            logger.error(f"Error qualifying lead {company_data.get('company_name', 'Unknown')}: {e}")
            
            # Update database with error status if we have a company_id
            if 'company_id' in locals():
                try:
                    await self._update_company_error(company_id, str(e))
                except Exception as db_error:
                    logger.error(f"Failed to update error status in database: {db_error}")
            
            return None

    async def _get_company_by_id(self, company_id: str) -> Optional[UKCompany]:
        """Get company by ID from database"""
        try:
            with get_db_session() as session:
                company = session.query(UKCompany).filter(UKCompany.id == company_id).first()
                return company
        except Exception as e:
            logger.error(f"Database error getting company {company_id}: {e}")
            return None

    async def _create_company_record(self, company_data: Dict) -> bool:
        """Create new company record in database"""
        try:
            with get_db_session() as session:
                # Create new company with proper datetime handling
                company_data['created_at'] = datetime.utcnow()
                company_data['updated_at'] = datetime.utcnow()
                
                company = UKCompany(**company_data)
                session.add(company)
                session.commit()
                
                logger.debug(f"Created company record: {company_data.get('company_name')}")
                return True
                
        except Exception as e:
            logger.error(f"Database error creating company: {e}")
            return False

    async def _update_company_data(self, company_id: str, company_data: Dict) -> bool:
        """Update existing company record with new data"""
        try:
            with get_db_session() as session:
                # Update existing company
                company_data['updated_at'] = datetime.utcnow()
                
                session.query(UKCompany).filter(UKCompany.id == company_id).update(company_data)
                session.commit()
                
                logger.debug(f"Updated company record: {company_id}")
                return True
                
        except Exception as e:
            logger.error(f"Database error updating company {company_id}: {e}")
            return False

    async def _update_company_qualification(self, company_id: str, qualification_data: Dict) -> bool:
        """Update company with qualification results"""
        try:
            with get_db_session() as session:
                # Update with qualification data
                qualification_data['updated_at'] = datetime.utcnow()
                
                session.query(UKCompany).filter(UKCompany.id == company_id).update(qualification_data)
                session.commit()
                
                logger.debug(f"Updated qualification for company: {company_id}")
                return True
                
        except Exception as e:
            logger.error(f"Database error updating qualification for {company_id}: {e}")
            return False

    async def _update_company_error(self, company_id: str, error_message: str) -> bool:
        """Update company with error status"""
        try:
            with get_db_session() as session:
                session.query(UKCompany).filter(UKCompany.id == company_id).update({
                    'status': 'error',
                    'error_message': error_message,
                    'updated_at': datetime.utcnow()
                })
                session.commit()
                
                logger.debug(f"Updated error status for company: {company_id}")
                return True
                
        except Exception as e:
            logger.error(f"Database error updating error for {company_id}: {e}")
            return False
    
    def _calculate_seo_score(self, seo_analysis) -> float:
        """Calculate SEO opportunity score based on analysis results"""
        if not seo_analysis:
            return 0.0
        
        score = 0.0
        max_score = 100.0
        
        # Overall SEO score (40% weight)
        if hasattr(seo_analysis, 'overall_score'):
            # Convert to opportunity score (lower SEO = higher opportunity)
            seo_opportunity = max(0, 100 - float(seo_analysis.overall_score))
            score += (seo_opportunity / 100) * 40
        
        # Performance issues (30% weight)
        if hasattr(seo_analysis, 'performance') and seo_analysis.performance:
            perf = seo_analysis.performance
            if hasattr(perf, 'pagespeed_score') and perf.pagespeed_score < 70:
                score += 30
            if hasattr(perf, 'load_time') and perf.load_time > 3:
                score += 10
            if hasattr(perf, 'mobile_friendly') and not perf.mobile_friendly:
                score += 20
        
        # Content issues (30% weight) 
        if hasattr(seo_analysis, 'content') and seo_analysis.content:
            content = seo_analysis.content
            if hasattr(content, 'meta_description_missing') and content.meta_description_missing:
                score += 10
            if hasattr(content, 'h1_tags_present') and not content.h1_tags_present:
                score += 10
            if hasattr(content, 'ssl_certificate') and not content.ssl_certificate:
                score += 10
        
        return min(score, max_score)

    def _calculate_business_score(self, company_data: Dict) -> float:
        """Calculate business attractiveness score"""
        score = 50.0  # Base score
        
        # Company name quality (indicates professionalism)
        company_name = company_data.get('company_name', '')
        if len(company_name) > 5 and not any(char.isdigit() for char in company_name):
            score += 20
        
        # Website presence
        website = company_data.get('website', '')
        if website and website.startswith('http'):
            score += 20
            # Professional domain
            if any(domain in website for domain in ['.co.uk', '.com', '.org']):
                score += 10
        
        return min(score, 100.0)

    def _calculate_sector_score(self, sector: str) -> float:
        """Calculate sector fit score based on SEO service demand"""
        # High-demand sectors for SEO services
        high_value_sectors = {
            'construction': 85,
            'legal': 90,
            'medical': 85,
            'dental': 80,
            'automotive': 75,
            'real_estate': 80,
            'retail': 70,
            'restaurant': 65,
            'fitness': 70,
            'beauty': 65
        }
        
        if not sector:
            return 50.0
        
        sector_lower = sector.lower()
        for sector_type, score in high_value_sectors.items():
            if sector_type in sector_lower:
                return float(score)
        
        return 50.0  # Default for unknown sectors

    def _calculate_growth_score(self, company_data: Dict) -> float:
        """Calculate growth potential score"""
        score = 50.0  # Base score
        
        # Assume established businesses have growth potential
        website = company_data.get('website', '')
        if website:
            score += 20
        
        # Location factor (major cities have more competition/opportunity)
        city = company_data.get('city', '').lower()
        major_cities = ['london', 'birmingham', 'manchester', 'leeds', 'liverpool', 'bristol']
        if any(city_name in city for city_name in major_cities):
            score += 20
        
        return min(score, 100.0)

    def _calculate_contact_score(self, contact_info: Dict) -> float:
        """Calculate contact quality score"""
        if not contact_info:
            return 0.0
        
        score = 0.0
        
        # Executive contact found
        if contact_info.get('person'):
            score += 40
        
        # Seniority level
        seniority = contact_info.get('seniority_tier', '')
        if 'tier_1' in str(seniority):  # Top executives
            score += 30
        elif 'tier_2' in str(seniority):  # Mid-level
            score += 20
        elif 'tier_3' in str(seniority):  # Entry-level
            score += 10
        
        # Contact confidence
        confidence = float(contact_info.get('confidence', 0))
        score += confidence * 0.3  # Up to 30 points based on confidence
        
        return min(score, 100.0)

    def _determine_priority_tier(self, final_score: float):
        """Determine priority tier based on final score"""
        from ..models import PriorityTier
        
        if final_score >= 85:
            return PriorityTier.A  # Hot Lead (80+)
        elif final_score >= 70:
            return PriorityTier.B  # Warm Lead (65-79)
        elif final_score >= 55:
            return PriorityTier.C  # Qualified Lead (50-64)
        else:
            return PriorityTier.D  # Low Priority (<50)

    def _generate_talking_points(self, company_data: Dict, seo_analysis, priority_tier) -> List[str]:
        """Generate personalized talking points for outreach"""
        talking_points = []
        company_name = company_data.get('company_name', 'your company')
        
        # SEO-specific talking points
        if seo_analysis:
            if hasattr(seo_analysis, 'overall_score') and seo_analysis.overall_score < 60:
                talking_points.append(f"I noticed {company_name} has significant SEO improvement opportunities that could drive more local customers")
            
            if hasattr(seo_analysis, 'performance') and seo_analysis.performance:
                if hasattr(seo_analysis.performance, 'pagespeed_score') and seo_analysis.performance.pagespeed_score < 70:
                    talking_points.append(f"Your website's loading speed could be costing you potential customers - we can help improve this significantly")
                
                if hasattr(seo_analysis.performance, 'mobile_friendly') and not seo_analysis.performance.mobile_friendly:
                    talking_points.append(f"With most customers searching on mobile, optimizing {company_name}'s mobile experience could boost your visibility")
        
        # Sector-specific talking points
        sector = company_data.get('sector', '').lower()
        if 'construction' in sector or 'plumbing' in sector:
            talking_points.append("Local tradespeople who rank well on Google often see 40-60% more service calls")
        elif 'legal' in sector:
            talking_points.append("Law firms with strong SEO typically generate 3x more qualified leads than competitors")
        elif 'medical' in sector or 'dental' in sector:
            talking_points.append("Healthcare practices ranking on page 1 of Google see significantly more new patient inquiries")
        
        # Priority-based talking points
        from ..models import PriorityTier
        if priority_tier == PriorityTier.A:  # Hot Lead
            talking_points.append("Given your strong business foundation, SEO improvements could deliver substantial ROI within 90 days")
        elif priority_tier == PriorityTier.B:  # Warm Lead
            talking_points.append("Your business has great potential - strategic SEO could help you dominate local search results")
        
        return talking_points[:3]  # Limit to top 3 talking points

    def _generate_recommended_actions(self, priority_tier, seo_analysis, contact_info: Dict) -> List[str]:
        """Generate recommended actions based on lead quality"""
        actions = []
        
        from ..models import PriorityTier
        
        # Priority-based actions
        if priority_tier == PriorityTier.A:  # Hot Lead
            actions.extend([
                "Schedule immediate discovery call",
                "Prepare comprehensive SEO audit proposal",
                "Research competitor landscape for presentation"
            ])
        elif priority_tier == PriorityTier.B:  # Warm Lead
            actions.extend([
                "Send personalized email with specific recommendations",
                "Follow up within 48 hours",
                "Prepare quick wins SEO strategy"
            ])
        elif priority_tier == PriorityTier.C:  # Qualified Lead
            actions.extend([
                "Add to nurture sequence",
                "Send educational content about SEO benefits",
                "Schedule follow-up in 2 weeks"
            ])
        else:  # Low Priority
            actions.extend([
                "Add to long-term nurture campaign",
                "Monitor for business growth indicators"
            ])
        
        # Contact-specific actions
        if contact_info.get('person'):
            actions.append(f"Personalize outreach to {contact_info.get('person')}")
        
        # SEO-specific actions
        if seo_analysis and hasattr(seo_analysis, 'critical_issues') and seo_analysis.critical_issues:
            actions.append("Highlight critical SEO issues in initial outreach")
        
        return actions[:4]  # Limit to top 4 actions

    def _estimate_lead_value(self, priority_tier) -> float:
        """Estimate potential lead value based on tier"""
        from ..models import PriorityTier
        
        value_estimates = {
            PriorityTier.A: 5000.0,      # £5,000 potential value (Hot Lead)
            PriorityTier.B: 3000.0,      # £3,000 potential value (Warm Lead)
            PriorityTier.C: 1500.0,      # £1,500 potential value (Qualified Lead)
            PriorityTier.D: 500.0        # £500 potential value (Low Priority)
        }
        
        return value_estimates.get(priority_tier, 1000.0)

    def _calculate_urgency(self, priority_tier, seo_analysis) -> str:
        """Calculate urgency level for follow-up"""
        from ..models import PriorityTier
        
        if priority_tier == PriorityTier.A:  # Hot Lead
            return "immediate"
        elif priority_tier == PriorityTier.B:  # Warm Lead
            return "high"
        elif priority_tier == PriorityTier.C:  # Qualified Lead
            return "medium"
        else:  # Low Priority
            return "low"

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