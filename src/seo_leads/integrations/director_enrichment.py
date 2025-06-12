"""
Director Enrichment Integration

Integration module that connects the director enrichment service
with the main SEO leads system for seamless lead processing.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import UKCompanyLead, UKCompany
from ..database import Database
from ...enrichment_service.core.director_models import EnrichmentConfig
from ...enrichment_service.services.director_enrichment_engine import DirectorEnrichmentEngine

logger = logging.getLogger(__name__)


class DirectorEnrichmentIntegration:
    """Integration between SEO leads system and director enrichment"""
    
    def __init__(self, companies_house_api_key: str, config: Optional[EnrichmentConfig] = None):
        self.companies_house_api_key = companies_house_api_key
        self.config = config or EnrichmentConfig()
        self.engine = DirectorEnrichmentEngine(self.config, companies_house_api_key)
        
    async def enrich_qualified_leads(self, companies: List[UKCompany]) -> List[Dict[str, Any]]:
        """Enrich only qualified leads (Tier A and B) with director information"""
        enriched_results = []
        
        for company in companies:
            # Only enrich qualified leads to save budget
            if company.priority_tier in ['A', 'B'] and company.lead_score >= 60:
                try:
                    result = await self.engine.enrich_company_directors(
                        company_name=company.company_name,
                        lead_score=company.lead_score,
                        priority_tier=company.priority_tier,
                        website=company.website
                    )
                    
                    enriched_data = {
                        'company_id': company.id,
                        'company_name': company.company_name,
                        'enrichment_result': result.model_dump(),
                        'enriched_at': datetime.now().isoformat(),
                        'cost': result.total_cost,
                        'status': result.status
                    }
                    
                    enriched_results.append(enriched_data)
                    
                    logger.info(f"Enriched {company.company_name}: {len(result.director_profiles)} directors found")
                    
                except Exception as e:
                    logger.error(f"Error enriching {company.company_name}: {e}")
                    enriched_results.append({
                        'company_id': company.id,
                        'company_name': company.company_name,
                        'enrichment_result': None,
                        'enriched_at': datetime.now().isoformat(),
                        'cost': 0.0,
                        'status': 'failed',
                        'error': str(e)
                    })
            else:
                logger.info(f"Skipping {company.company_name} - does not meet enrichment criteria")
        
        return enriched_results
    
    async def enrich_single_company(self, company: UKCompany) -> Optional[Dict[str, Any]]:
        """Enrich a single company with director information"""
        try:
            result = await self.engine.enrich_company_directors(
                company_name=company.company_name,
                lead_score=company.lead_score or 70.0,
                priority_tier=company.priority_tier or 'B',
                website=company.website
            )
            
            return {
                'company_id': company.id,
                'company_name': company.company_name,
                'enrichment_result': result.model_dump(),
                'enriched_at': datetime.now().isoformat(),
                'cost': result.total_cost,
                'status': result.status
            }
            
        except Exception as e:
            logger.error(f"Error enriching {company.company_name}: {e}")
            return {
                'company_id': company.id,
                'company_name': company.company_name,
                'enrichment_result': None,
                'enriched_at': datetime.now().isoformat(),
                'cost': 0.0,
                'status': 'failed',
                'error': str(e)
            }
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status"""
        return self.engine.get_budget_status()
    
    def should_enrich_company(self, company: UKCompany) -> bool:
        """Determine if a company should be enriched based on qualification"""
        # Only enrich Tier A and B leads with good scores
        if company.priority_tier in ['A', 'B'] and (company.lead_score or 0) >= 60:
            return True
        
        # Also enrich high-scoring Tier C leads if budget allows
        if company.priority_tier == 'C' and (company.lead_score or 0) >= 80:
            budget_status = self.get_budget_status()
            if budget_status['remaining'] > 1.0:  # At least £1 remaining
                return True
        
        return False
    
    async def batch_enrich_from_database(self, db: Database, limit: int = 50) -> List[Dict[str, Any]]:
        """Batch enrich qualified companies from database"""
        # Get qualified companies that haven't been enriched yet
        query = """
        SELECT * FROM uk_companies 
        WHERE priority_tier IN ('A', 'B') 
        AND lead_score >= 60
        AND id NOT IN (
            SELECT DISTINCT company_id FROM director_enrichments 
            WHERE status = 'completed'
        )
        ORDER BY lead_score DESC, priority_tier ASC
        LIMIT ?
        """
        
        rows = db.execute_query(query, (limit,))
        companies = []
        
        for row in rows:
            # Create UKCompany object from row data
            company = UKCompany()
            for key, value in dict(row).items():
                if hasattr(company, key):
                    setattr(company, key, value)
            companies.append(company)
        
        logger.info(f"Found {len(companies)} qualified companies for enrichment")
        
        return await self.enrich_qualified_leads(companies)
    
    def save_enrichment_results(self, db: Database, results: List[Dict[str, Any]]):
        """Save enrichment results to database"""
        # Create table if it doesn't exist
        db.execute_query("""
        CREATE TABLE IF NOT EXISTS director_enrichments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT,
            company_name TEXT,
            enrichment_data TEXT,
            cost REAL,
            status TEXT,
            error_message TEXT,
            enriched_at TEXT,
            FOREIGN KEY (company_id) REFERENCES uk_companies (id)
        )
        """)
        
        # Insert results
        for result in results:
            db.execute_query("""
            INSERT INTO director_enrichments 
            (company_id, company_name, enrichment_data, cost, status, error_message, enriched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                result['company_id'],
                result['company_name'],
                str(result.get('enrichment_result', '')),
                result['cost'],
                result['status'],
                result.get('error', ''),
                result['enriched_at']
            ))
        
        logger.info(f"Saved {len(results)} enrichment results to database")
    
    def get_enriched_companies(self, db: Database) -> List[Dict[str, Any]]:
        """Get all enriched companies from database"""
        query = """
        SELECT c.*, de.enrichment_data, de.cost, de.enriched_at
        FROM uk_companies c
        JOIN director_enrichments de ON c.id = de.company_id
        WHERE de.status = 'completed'
        ORDER BY de.enriched_at DESC
        """
        
        rows = db.execute_query(query)
        return [dict(row) for row in rows]
    
    def get_enrichment_stats(self, db: Database) -> Dict[str, Any]:
        """Get enrichment statistics"""
        stats_query = """
        SELECT 
            COUNT(*) as total_enrichments,
            SUM(cost) as total_cost,
            AVG(cost) as avg_cost,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
        FROM director_enrichments
        """
        
        stats = dict(db.execute_query(stats_query)[0])
        
        # Get tier breakdown
        tier_query = """
        SELECT c.priority_tier, COUNT(*) as count, SUM(de.cost) as cost
        FROM director_enrichments de
        JOIN uk_companies c ON de.company_id = c.id
        WHERE de.status = 'completed'
        GROUP BY c.priority_tier
        """
        
        tier_stats = {row['priority_tier']: dict(row) for row in db.execute_query(tier_query)}
        
        return {
            'total_enrichments': stats['total_enrichments'],
            'total_cost': stats['total_cost'] or 0.0,
            'average_cost': stats['avg_cost'] or 0.0,
            'success_rate': (stats['successful'] / stats['total_enrichments'] * 100) if stats['total_enrichments'] > 0 else 0,
            'successful': stats['successful'],
            'failed': stats['failed'],
            'tier_breakdown': tier_stats
        }


class DirectorEnrichmentCLIIntegration:
    """CLI integration for director enrichment within the main SEO system"""
    
    def __init__(self, db: Database, companies_house_api_key: str):
        self.db = db
        self.integration = DirectorEnrichmentIntegration(companies_house_api_key)
    
    async def enrich_qualified_companies_command(self, limit: int = 50) -> Dict[str, Any]:
        """CLI command to enrich qualified companies"""
        print(f"🔍 Finding qualified companies for director enrichment (limit: {limit})...")
        
        results = await self.integration.batch_enrich_from_database(self.db, limit)
        
        if results:
            self.integration.save_enrichment_results(self.db, results)
            
            # Summary
            successful = len([r for r in results if r['status'] == 'completed'])
            total_cost = sum(r['cost'] for r in results)
            
            summary = {
                'total_processed': len(results),
                'successful': successful,
                'failed': len(results) - successful,
                'total_cost': total_cost,
                'average_cost': total_cost / len(results) if results else 0
            }
            
            print(f"✅ Enrichment completed:")
            print(f"   • Processed: {summary['total_processed']} companies")
            print(f"   • Successful: {summary['successful']}")
            print(f"   • Failed: {summary['failed']}")
            print(f"   • Total cost: £{summary['total_cost']:.2f}")
            print(f"   • Average cost: £{summary['average_cost']:.2f}")
            
            return summary
        else:
            print("ℹ️  No qualified companies found for enrichment")
            return {'total_processed': 0, 'successful': 0, 'failed': 0, 'total_cost': 0.0}
    
    def show_enrichment_stats(self) -> Dict[str, Any]:
        """Show enrichment statistics"""
        stats = self.integration.get_enrichment_stats(self.db)
        budget_status = self.integration.get_budget_status()
        
        print("📊 Director Enrichment Statistics:")
        print(f"   • Total enrichments: {stats['total_enrichments']}")
        print(f"   • Success rate: {stats['success_rate']:.1f}%")
        print(f"   • Total cost: £{stats['total_cost']:.2f}")
        print(f"   • Average cost: £{stats['average_cost']:.2f}")
        
        print("\n💰 Budget Status:")
        print(f"   • Monthly budget: £{budget_status['monthly_budget']:.2f}")
        print(f"   • Spent: £{budget_status['spent']:.2f}")
        print(f"   • Remaining: £{budget_status['remaining']:.2f}")
        print(f"   • Usage: {budget_status['percentage_used']:.1f}%")
        
        if stats['tier_breakdown']:
            print("\n🎯 Tier Breakdown:")
            for tier, data in stats['tier_breakdown'].items():
                print(f"   • Tier {tier}: {data['count']} companies, £{data['cost']:.2f}")
        
        return {**stats, 'budget_status': budget_status}
    
    def get_enriched_companies_summary(self) -> List[Dict[str, Any]]:
        """Get summary of enriched companies"""
        enriched_companies = self.integration.get_enriched_companies(self.db)
        
        summary = []
        for company in enriched_companies:
            # Parse enrichment data (simplified)
            enrichment_data = eval(company.get('enrichment_data', '{}')) if company.get('enrichment_data') else {}
            
            summary.append({
                'company_name': company['company_name'],
                'lead_score': company['lead_score'],
                'priority_tier': company['priority_tier'],
                'directors_found': len(enrichment_data.get('director_profiles', [])),
                'cost': company['cost'],
                'enriched_at': company['enriched_at']
            })
        
        return summary 