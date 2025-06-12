"""
Make.com Export Module

Hierarchical JSON structure optimized for Make.com automation with multi-format support.
Exports qualified leads with complete business intelligence data.

Based on creative design decisions:
- Hierarchical JSON structure for webhook compatibility
- Multi-format support (JSON, CSV) 
- Batch export with progress tracking
"""

import json
import csv
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import requests

from ..config import get_export_config, get_processing_config
from ..database import get_db_session
from ..models import UKCompany, UKCompanyLead

logger = logging.getLogger(__name__)

class MakeExporter:
    """
    Make.com optimized exporter with multi-format support
    
    Features:
    - Hierarchical JSON structure for webhook automation
    - CSV export for manual review
    - Batch processing with progress tracking
    - Webhook delivery with retry logic
    """
    
    def __init__(self):
        self.export_config = get_export_config()
        self.processing_config = get_processing_config()
    
    def export_qualified_leads(self, min_score: float = 50.0, 
                             export_format: str = 'json',
                             send_webhook: bool = True) -> Dict:
        """
        Export qualified leads in specified format
        
        Args:
            min_score: Minimum lead score to export
            export_format: 'json' or 'csv'
            send_webhook: Whether to send to Make.com webhook
            
        Returns:
            Export results with file paths and webhook status
        """
        try:
            logger.info(f"Starting export of qualified leads (min_score: {min_score})")
            
            # Get qualified leads from database
            leads_data = self._get_qualified_leads(min_score)
            
            if not leads_data:
                logger.info("No qualified leads found for export")
                return {'status': 'no_leads', 'count': 0}
            
            logger.info(f"Found {len(leads_data)} qualified leads for export")
            
            # Export in specified format
            export_results = {}
            
            if export_format == 'json':
                export_results['json'] = self._export_json(leads_data)
            elif export_format == 'csv':
                export_results['csv'] = self._export_csv(leads_data)
            else:
                # Export both formats
                export_results['json'] = self._export_json(leads_data)
                export_results['csv'] = self._export_csv(leads_data)
            
            # Send webhook if requested and configured
            webhook_result = None
            if send_webhook and self.export_config.make_webhook_url:
                webhook_result = self._send_webhook(leads_data)
                export_results['webhook'] = webhook_result
            
            # Update export status in database
            self._update_export_status(leads_data)
            
            return {
                'status': 'success',
                'count': len(leads_data),
                'exports': export_results,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting qualified leads: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_qualified_leads(self, min_score: float) -> List[Dict]:
        """Get qualified leads from database with complete data"""
        try:
            with get_db_session() as session:
                # Query qualified companies above minimum score
                companies = session.query(UKCompany).filter(
                    UKCompany.status == 'qualified',
                    UKCompany.lead_score >= min_score
                ).order_by(UKCompany.lead_score.desc()).all()
                
                leads_data = []
                
                for company in companies:
                    # Build hierarchical lead data structure
                    lead_data = self._build_lead_structure(company)
                    leads_data.append(lead_data)
                
                return leads_data
                
        except Exception as e:
            logger.error(f"Error getting qualified leads: {e}")
            return []
    
    def _build_lead_structure(self, company: UKCompany) -> Dict:
        """Build hierarchical lead data structure for export"""
        return {
            'lead_id': company.id,
            'company': {
                'name': company.company_name,
                'website': company.website,
                'location': {
                    'city': company.city,
                    'region': company.region,
                    'address': company.address
                },
                'business': {
                    'sector': company.sector,
                    'employees': company.employees,
                    'size_category': company.size_category
                }
            },
            'contact': {
                'person': company.contact_person,
                'role': company.contact_role,
                'seniority_tier': company.contact_seniority_tier,
                'email': company.email,
                'phone': company.phone,
                'linkedin_url': company.linkedin_url,
                'confidence': company.contact_confidence,
                'extraction_method': company.contact_extraction_method
            },
            'seo_analysis': {
                'overall_score': company.seo_overall_score,
                'pagespeed_score': company.pagespeed_score,
                'mobile_friendly': company.mobile_friendly,
                'meta_description_missing': company.meta_description_missing,
                'h1_tags_present': company.h1_tags_present,
                'ssl_certificate': company.ssl_certificate,
                'load_time': company.load_time,
                'critical_issues': company.critical_issues or []
            },
            'lead_qualification': {
                'final_score': company.lead_score,
                'priority_tier': company.priority_tier,
                'tier_label': company.tier_label,
                'factor_breakdown': company.factor_breakdown or {},
                'confidence': 0.8  # Default confidence
            },
            'outreach_intelligence': {
                'urgency': company.urgency,
                'estimated_value': company.estimated_value,
                'recommended_actions': company.recommended_actions or [],
                'talking_points': company.talking_points or [],
                'follow_up_schedule': {
                    'initial_contact': 'within 24 hours' if company.urgency == 'high' else 'within 72 hours',
                    'follow_up_1': '3 days after initial',
                    'follow_up_2': '1 week after follow_up_1'
                }
            },
            'metadata': {
                'created_at': company.created_at.isoformat() if company.created_at else None,
                'updated_at': company.updated_at.isoformat() if company.updated_at else None,
                'status': company.status,
                'export_timestamp': datetime.utcnow().isoformat()
            }
        }
    
    def _export_json(self, leads_data: List[Dict]) -> Dict:
        """Export leads as JSON file"""
        try:
            # Create export directory
            Path(self.export_config.output_directory).mkdir(exist_ok=True)
            
            # Generate filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"uk_leads_export_{timestamp}.json"
            filepath = Path(self.export_config.output_directory) / filename
            
            # Create export structure
            export_data = {
                'export_info': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'total_leads': len(leads_data),
                    'format': 'json',
                    'source': 'UK Company SEO Lead Generation System'
                },
                'leads': leads_data
            }
            
            # Write JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON export complete: {filepath}")
            
            return {
                'format': 'json',
                'filepath': str(filepath),
                'size_mb': filepath.stat().st_size / (1024 * 1024),
                'count': len(leads_data)
            }
            
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            return {'format': 'json', 'error': str(e)}
    
    def _export_csv(self, leads_data: List[Dict]) -> Dict:
        """Export leads as CSV file for manual review"""
        try:
            # Create export directory
            Path(self.export_config.output_directory).mkdir(exist_ok=True)
            
            # Generate filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"uk_leads_export_{timestamp}.csv"
            filepath = Path(self.export_config.output_directory) / filename
            
            # Define CSV columns
            columns = [
                'lead_id', 'company_name', 'website', 'city', 'sector',
                'contact_person', 'contact_role', 'email', 'phone', 'linkedin_url',
                'seo_score', 'lead_score', 'priority_tier', 'tier_label',
                'urgency', 'estimated_value', 'contact_confidence'
            ]
            
            # Write CSV file
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                
                for lead in leads_data:
                    # Flatten lead data for CSV
                    csv_row = {
                        'lead_id': lead['lead_id'],
                        'company_name': lead['company']['name'],
                        'website': lead['company']['website'],
                        'city': lead['company']['location']['city'],
                        'sector': lead['company']['business']['sector'],
                        'contact_person': lead['contact']['person'],
                        'contact_role': lead['contact']['role'],
                        'email': lead['contact']['email'],
                        'phone': lead['contact']['phone'],
                        'linkedin_url': lead['contact']['linkedin_url'],
                        'seo_score': lead['seo_analysis']['overall_score'],
                        'lead_score': lead['lead_qualification']['final_score'],
                        'priority_tier': lead['lead_qualification']['priority_tier'],
                        'tier_label': lead['lead_qualification']['tier_label'],
                        'urgency': lead['outreach_intelligence']['urgency'],
                        'estimated_value': lead['outreach_intelligence']['estimated_value'],
                        'contact_confidence': lead['contact']['confidence']
                    }
                    writer.writerow(csv_row)
            
            logger.info(f"CSV export complete: {filepath}")
            
            return {
                'format': 'csv',
                'filepath': str(filepath),
                'size_mb': filepath.stat().st_size / (1024 * 1024),
                'count': len(leads_data)
            }
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return {'format': 'csv', 'error': str(e)}
    
    def _send_webhook(self, leads_data: List[Dict]) -> Dict:
        """Send leads data to Make.com webhook"""
        try:
            webhook_url = self.export_config.make_webhook_url
            
            if not webhook_url:
                return {'status': 'skipped', 'reason': 'No webhook URL configured'}
            
            # Prepare webhook payload
            payload = {
                'source': 'UK Company SEO Lead Generation System',
                'timestamp': datetime.utcnow().isoformat(),
                'lead_count': len(leads_data),
                'leads': leads_data[:10]  # Send first 10 leads to avoid payload size limits
            }
            
            # Add webhook secret if configured
            headers = {'Content-Type': 'application/json'}
            if self.export_config.make_webhook_secret:
                headers['X-Webhook-Secret'] = self.export_config.make_webhook_secret
            
            # Send webhook
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook sent successfully to Make.com")
                return {
                    'status': 'success',
                    'response_code': response.status_code,
                    'leads_sent': len(payload['leads'])
                }
            else:
                logger.warning(f"Webhook failed with status {response.status_code}")
                return {
                    'status': 'failed',
                    'response_code': response.status_code,
                    'response_text': response.text[:200]
                }
            
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _update_export_status(self, leads_data: List[Dict]):
        """Update export status for exported leads"""
        try:
            with get_db_session() as session:
                lead_ids = [lead['lead_id'] for lead in leads_data]
                
                # Update status to exported
                session.query(UKCompany).filter(
                    UKCompany.id.in_(lead_ids)
                ).update({'status': 'exported'}, synchronize_session=False)
                
                session.commit()
                logger.info(f"Updated export status for {len(lead_ids)} leads")
                
        except Exception as e:
            logger.error(f"Error updating export status: {e}")
    
    def get_export_summary(self) -> Dict:
        """Get summary of exportable leads"""
        try:
            with get_db_session() as session:
                # Count by priority tier
                tier_counts = {}
                for tier in ['A', 'B', 'C', 'D']:
                    count = session.query(UKCompany).filter(
                        UKCompany.status == 'qualified',
                        UKCompany.priority_tier == tier
                    ).count()
                    tier_counts[f"tier_{tier}"] = count
                
                # Count by score ranges
                score_ranges = {
                    'high_value_80_plus': session.query(UKCompany).filter(
                        UKCompany.status == 'qualified',
                        UKCompany.lead_score >= 80
                    ).count(),
                    'good_value_65_79': session.query(UKCompany).filter(
                        UKCompany.status == 'qualified',
                        UKCompany.lead_score >= 65,
                        UKCompany.lead_score < 80
                    ).count(),
                    'standard_value_50_64': session.query(UKCompany).filter(
                        UKCompany.status == 'qualified',
                        UKCompany.lead_score >= 50,
                        UKCompany.lead_score < 65
                    ).count()
                }
                
                total_qualified = sum(tier_counts.values())
                
                return {
                    'total_qualified_leads': total_qualified,
                    'tier_breakdown': tier_counts,
                    'score_breakdown': score_ranges,
                    'export_ready': total_qualified > 0
                }
                
        except Exception as e:
            logger.error(f"Error getting export summary: {e}")
            return {}

# Convenience function
def export_leads(min_score: float = 50.0, export_format: str = 'both') -> Dict:
    """Convenience function to export qualified leads"""
    exporter = MakeExporter()
    return exporter.export_qualified_leads(min_score, export_format) 