"""
Smart Lead Filter Service

Intelligent filtering system that determines enrichment strategy based on:
- Lead qualification scores
- Available budget
- Cost optimization goals
- Processing priorities
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from ..core.director_models import (
    EnrichmentDecision, EnrichmentTier, DataSource, EnrichmentConfig,
    CostTrackingEntry, MonthlyBudget
)

logger = logging.getLogger(__name__)


class CostTracker:
    """Track API costs and budget usage"""
    
    def __init__(self, config: EnrichmentConfig):
        self.config = config
        self.monthly_budget = config.monthly_budget
        self.tier_budgets = config.tier_budgets
        self.cost_history: List[CostTrackingEntry] = []
        
    def get_current_month(self) -> str:
        """Get current month string for tracking"""
        return datetime.now().strftime("%Y-%m")
    
    def get_monthly_spending(self, month: Optional[str] = None) -> float:
        """Get total spending for a specific month"""
        if month is None:
            month = self.get_current_month()
            
        month_costs = [
            entry.cost for entry in self.cost_history
            if entry.timestamp.strftime("%Y-%m") == month
        ]
        return sum(month_costs)
    
    def get_remaining_budget(self, month: Optional[str] = None) -> float:
        """Get remaining budget for the month"""
        spent = self.get_monthly_spending(month)
        return max(0.0, self.monthly_budget - spent)
    
    def get_tier_spending(self, tier: EnrichmentTier, month: Optional[str] = None) -> Dict[str, float]:
        """Get spending breakdown for a specific tier"""
        if month is None:
            month = self.get_current_month()
            
        tier_entries = [
            entry for entry in self.cost_history
            if entry.tier == tier and entry.timestamp.strftime("%Y-%m") == month
        ]
        
        total_spent = sum(entry.cost for entry in tier_entries)
        total_count = len(tier_entries)
        avg_cost = total_spent / total_count if total_count > 0 else 0.0
        
        return {
            "spent": total_spent,
            "count": total_count,
            "average_cost": avg_cost
        }
    
    def track_cost(self, entry: CostTrackingEntry):
        """Track a new cost entry"""
        self.cost_history.append(entry)
        logger.info(f"Tracked cost: {entry.provider} - £{entry.cost:.2f} for {entry.company_name}")
    
    def can_afford_enrichment(self, tier: EnrichmentTier, estimated_cost: float) -> bool:
        """Check if we can afford a specific enrichment"""
        remaining_budget = self.get_remaining_budget()
        tier_budget = self.tier_budgets.get(tier.value, 0.0)
        
        return (remaining_budget >= estimated_cost and 
                estimated_cost <= tier_budget)
    
    def get_monthly_report(self, month: Optional[str] = None) -> MonthlyBudget:
        """Generate monthly budget report"""
        if month is None:
            month = self.get_current_month()
            
        spent = self.get_monthly_spending(month)
        remaining = self.get_remaining_budget(month)
        
        month_entries = [
            entry for entry in self.cost_history
            if entry.timestamp.strftime("%Y-%m") == month
        ]
        
        leads_processed = len(set(entry.lead_id for entry in month_entries))
        avg_cost = spent / leads_processed if leads_processed > 0 else 0.0
        
        # Tier breakdown
        tier_breakdown = {}
        for tier in ["A", "B", "C"]:
            tier_enum = EnrichmentTier(tier)
            tier_data = self.get_tier_spending(tier_enum, month)
            tier_breakdown[tier] = {
                "budget": self.tier_budgets.get(tier, 0.0),
                "spent": tier_data["spent"],
                "count": tier_data["count"]
            }
        
        return MonthlyBudget(
            month=month,
            total_budget=self.monthly_budget,
            spent=spent,
            remaining=remaining,
            leads_processed=leads_processed,
            average_cost_per_lead=avg_cost,
            tier_breakdown=tier_breakdown
        )


class SmartLeadFilter:
    """Intelligent lead filtering for cost-optimized enrichment"""
    
    def __init__(self, config: EnrichmentConfig):
        self.config = config
        self.cost_tracker = CostTracker(config)
        
    def determine_enrichment_tier(self, lead_score: float, priority_tier: str) -> EnrichmentTier:
        """Determine enrichment tier based on lead qualification"""
        if lead_score >= 80 and priority_tier == "A":
            return EnrichmentTier.TIER_A
        elif lead_score >= 60 and priority_tier in ["A", "B"]:
            return EnrichmentTier.TIER_B
        elif lead_score >= 40:
            return EnrichmentTier.TIER_C
        else:
            return EnrichmentTier.TIER_D
    
    def estimate_enrichment_cost(self, tier: EnrichmentTier, 
                                data_gaps: List[str]) -> float:
        """Estimate cost for enrichment based on tier and data gaps"""
        base_costs = {
            "email_verification": 0.10,
            "phone_lookup": 0.25,
            "linkedin_premium": 0.50,
            "abstract_api_company": 0.15,
            "hunter_io_email": 0.20
        }
        
        if tier == EnrichmentTier.TIER_C or tier == EnrichmentTier.TIER_D:
            return 0.0  # Free sources only
        
        estimated_cost = 0.0
        
        # Estimate based on likely data gaps
        if "email" in data_gaps:
            estimated_cost += base_costs["email_verification"]
        if "phone" in data_gaps:
            estimated_cost += base_costs["phone_lookup"]
        if "linkedin_premium" in data_gaps:
            estimated_cost += base_costs["linkedin_premium"]
        
        # Cap at tier budget
        tier_budget = self.config.tier_budgets.get(tier.value, 0.0)
        return min(estimated_cost, tier_budget)
    
    def select_allowed_sources(self, tier: EnrichmentTier, 
                              budget: float) -> List[DataSource]:
        """Select allowed data sources based on tier and budget"""
        allowed_sources = self.config.free_sources.copy()
        
        if tier in [EnrichmentTier.TIER_A, EnrichmentTier.TIER_B] and budget > 0:
            # Add paid sources based on budget
            if budget >= 0.10:
                allowed_sources.append(DataSource.EMAIL_VERIFICATION)
            if budget >= 0.15:
                allowed_sources.append(DataSource.ABSTRACT_API)
            if budget >= 0.20:
                allowed_sources.append(DataSource.HUNTER_IO)
        
        return allowed_sources
    
    def should_enrich_lead(self, lead_score: float, priority_tier: str) -> bool:
        """Determine if a lead should be enriched at all"""
        # Only enrich Tier A and B leads, or high-scoring Tier C
        tier = self.determine_enrichment_tier(lead_score, priority_tier)
        
        if tier in [EnrichmentTier.TIER_A, EnrichmentTier.TIER_B]:
            return True
        elif tier == EnrichmentTier.TIER_C and lead_score >= 50:
            return True  # Free enrichment for decent Tier C leads
        else:
            return False
    
    def create_enrichment_decision(self, lead_score: float, 
                                 priority_tier: str,
                                 company_name: str,
                                 estimated_data_gaps: List[str] = None) -> Optional[EnrichmentDecision]:
        """Create enrichment decision for a lead"""
        
        if not self.should_enrich_lead(lead_score, priority_tier):
            logger.info(f"Lead {company_name} (score: {lead_score}) does not qualify for enrichment")
            return None
        
        tier = self.determine_enrichment_tier(lead_score, priority_tier)
        base_budget = self.config.tier_budgets.get(tier.value, 0.0)
        
        # Check remaining monthly budget
        remaining_budget = self.cost_tracker.get_remaining_budget()
        available_budget = min(base_budget, remaining_budget)
        
        if tier in [EnrichmentTier.TIER_A, EnrichmentTier.TIER_B] and available_budget < 0.10:
            logger.warning(f"Insufficient budget for {tier.value} enrichment. Falling back to free sources.")
            tier = EnrichmentTier.TIER_C
            available_budget = 0.0
        
        # Estimate cost based on data gaps
        estimated_cost = self.estimate_enrichment_cost(tier, estimated_data_gaps or [])
        
        # Adjust budget if estimated cost exceeds available
        if estimated_cost > available_budget:
            estimated_cost = available_budget
        
        # Select allowed sources
        allowed_sources = self.select_allowed_sources(tier, available_budget)
        
        # Set processing time limits
        max_processing_time = self.config.max_processing_time.get(tier.value, 30)
        
        # Determine priority
        priority_map = {
            EnrichmentTier.TIER_A: "high",
            EnrichmentTier.TIER_B: "medium", 
            EnrichmentTier.TIER_C: "low",
            EnrichmentTier.TIER_D: "minimal"
        }
        
        decision = EnrichmentDecision(
            tier=tier,
            budget=available_budget,
            priority=priority_map[tier],
            allowed_sources=allowed_sources,
            max_processing_time=max_processing_time,
            estimated_cost=estimated_cost
        )
        
        logger.info(f"Enrichment decision for {company_name}: {tier.value} tier, £{available_budget:.2f} budget")
        return decision
    
    def get_budget_status(self) -> Dict[str, any]:
        """Get current budget status"""
        monthly_report = self.cost_tracker.get_monthly_report()
        
        return {
            "monthly_budget": self.config.monthly_budget,
            "spent": monthly_report.spent,
            "remaining": monthly_report.remaining,
            "percentage_used": (monthly_report.spent / self.config.monthly_budget) * 100,
            "leads_processed": monthly_report.leads_processed,
            "average_cost_per_lead": monthly_report.average_cost_per_lead,
            "tier_breakdown": monthly_report.tier_breakdown
        }
    
    def optimize_batch_enrichment(self, leads: List[Dict]) -> List[EnrichmentDecision]:
        """Optimize enrichment decisions for a batch of leads"""
        decisions = []
        remaining_budget = self.cost_tracker.get_remaining_budget()
        
        # Sort leads by score (highest first) for budget allocation
        sorted_leads = sorted(leads, key=lambda x: x.get('score', 0), reverse=True)
        
        for lead in sorted_leads:
            decision = self.create_enrichment_decision(
                lead_score=lead.get('score', 0),
                priority_tier=lead.get('tier', 'C'),
                company_name=lead.get('company_name', 'Unknown'),
                estimated_data_gaps=lead.get('data_gaps', [])
            )
            
            if decision:
                # Check if we still have budget
                if remaining_budget >= decision.estimated_cost:
                    decisions.append(decision)
                    remaining_budget -= decision.estimated_cost
                else:
                    # Downgrade to free-only enrichment
                    free_decision = EnrichmentDecision(
                        tier=EnrichmentTier.TIER_C,
                        budget=0.0,
                        priority="free_only",
                        allowed_sources=self.config.free_sources,
                        max_processing_time=30,
                        estimated_cost=0.0
                    )
                    decisions.append(free_decision)
        
        logger.info(f"Batch optimization: {len(decisions)} enrichment decisions created")
        return decisions 