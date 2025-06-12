"""
Make.com Webhook Integration

Sends qualified leads to Make.com automation scenarios with structured payload format
optimized for lead management workflows.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
from pydantic import BaseModel, Field, HttpUrl

from ..config import get_export_config
from ..models import UKCompany, PriorityTier, ContactSeniorityTier

logger = logging.getLogger(__name__)

class WebhookEventType(str, Enum):
    """Types of webhook events to send to Make.com"""
    NEW_LEAD = "new_lead"
    LEAD_UPDATED = "lead_updated"
    BATCH_COMPLETE = "batch_complete"
    HIGH_PRIORITY = "high_priority_alert"

class MakePayloadFormat(str, Enum):
    """Payload format options for Make.com"""
    FULL_LEAD = "full_lead"        # Complete lead data
    SUMMARY = "summary"            # Key fields only
    CRM_READY = "crm_ready"       # Optimized for CRM import
    ALERT = "alert"               # High-priority notifications

@dataclass
class WebhookPayload:
    """Structured payload for Make.com webhook"""
    
    # Event metadata
    event_type: str
    timestamp: str
    lead_id: str
    
    # Company core data
    company_name: str
    website: Optional[str]
    city: str
    sector: str
    source: str
    
    # Contact information
    contact_person: Optional[str]
    contact_role: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    contact_linkedin: Optional[str]
    contact_confidence: Optional[float]
    
    # Lead qualification
    lead_score: float
    priority_tier: str
    tier_label: str
    estimated_value: Optional[str]
    urgency: Optional[str]
    
    # SEO opportunity
    seo_score: Optional[float]
    critical_issues: List[str]
    improvement_potential: Optional[str]
    
    # Sales intelligence
    recommended_actions: List[str]
    talking_points: List[str]
    
    # Additional metadata
    processing_complete: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str, indent=2)


class MakeWebhookSender:
    """
    Handles sending webhook payloads to Make.com scenarios
    
    Features:
    - Retry logic with exponential backoff
    - Payload format optimization
    - Batch delivery for efficiency
    - Error handling and logging
    """
    
    def __init__(self, webhook_url: Optional[str] = None, secret: Optional[str] = None):
        self.config = get_export_config()
        self.webhook_url = webhook_url or self.config.make_webhook_url
        self.secret = secret or self.config.make_webhook_secret
        
        # Delivery settings (optimized for Make.com)
        self.max_retries = 5
        self.retry_delay = 1.0  # seconds - will use exponential backoff (1→2→4→8→16s)
        self.timeout = 10.0     # seconds (recommended for Make.com)
        
        # Rate limiting (respects Make.com limits)
        self.max_requests_per_minute = 60
        self.stream_delay = 0.15  # 150ms between streaming calls
        self.request_timestamps = []
        
        # Posting style configuration
        self.posting_style = "batch"  # "stream" or "batch"
        self.batch_size = 100  # Make.com recommended batch size
        self.max_execution_time = 35  # Leave 5s buffer from Make's 40s limit
        
        if not self.webhook_url:
            logger.warning("Make.com webhook URL not configured")
    
    async def send_lead(
        self, 
        company: UKCompany, 
        event_type: WebhookEventType = WebhookEventType.NEW_LEAD,
        format_type: MakePayloadFormat = MakePayloadFormat.FULL_LEAD
    ) -> bool:
        """
        Send a single lead to Make.com
        
        Args:
            company: UKCompany instance with complete lead data
            event_type: Type of webhook event
            format_type: Payload format optimization
            
        Returns:
            bool: True if successfully delivered, False otherwise
        """
        if not self.webhook_url:
            logger.error("Cannot send webhook: URL not configured")
            return False
        
        try:
            # Create payload
            payload = self._create_payload(company, event_type, format_type)
            
            # Apply rate limiting
            await self._apply_rate_limit()
            
            # Send with retry logic
            success = await self._send_with_retry(payload)
            
            if success:
                logger.info(f"Successfully sent {event_type.value} for {company.company_name} to Make.com")
            else:
                logger.error(f"Failed to send {event_type.value} for {company.company_name} to Make.com")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending webhook for {company.company_name}: {e}")
            return False
    
    async def send_batch(
        self, 
        companies: List[UKCompany], 
        event_type: WebhookEventType = WebhookEventType.NEW_LEAD,
        format_type: MakePayloadFormat = MakePayloadFormat.SUMMARY,
        posting_style: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send multiple leads with optimized posting style for Make.com
        
        Args:
            companies: List of UKCompany instances
            event_type: Type of webhook event
            format_type: Payload format optimization
            posting_style: "stream" or "batch" (defaults to instance setting)
            
        Returns:
            Dict with delivery statistics
        """
        if not self.webhook_url:
            logger.error("Cannot send batch: webhook URL not configured")
            return {"success": False, "error": "Webhook URL not configured"}
        
        # Determine posting style
        style = posting_style or self.posting_style
        logger.info(f"Sending {len(companies)} leads to Make.com using {style} posting style")
        
        # Filter companies by priority if specified
        filtered_companies = self._filter_companies_for_delivery(companies)
        
        results = {
            "total_attempted": len(filtered_companies),
            "successful": 0,
            "failed": 0,
            "errors": [],
            "delivered_ids": [],
            "posting_style": style
        }
        
        if style == "batch":
            # Batch posting: Send array of objects in single request
            await self._send_batch_posting(filtered_companies, event_type, format_type, results)
        else:
            # Stream posting: Send one JSON object per HTTP request
            await self._send_stream_posting(filtered_companies, event_type, format_type, results)
        
        # Send batch completion notification
        if results["successful"] > 0:
            await self._send_batch_completion(results)
        
        logger.info(f"Batch delivery complete: {results['successful']}/{results['total_attempted']} successful")
        return results
    
    async def send_high_priority_alert(self, company: UKCompany) -> bool:
        """
        Send immediate alert for high-priority leads (A-tier)
        
        Args:
            company: High-priority UKCompany instance
            
        Returns:
            bool: True if successfully delivered
        """
        if company.priority_tier != PriorityTier.A.value:
            logger.warning(f"Alert attempted for non-A-tier lead: {company.company_name}")
            return False
        
        logger.info(f"Sending high-priority alert for {company.company_name}")
        
        return await self.send_lead(
            company, 
            WebhookEventType.HIGH_PRIORITY, 
            MakePayloadFormat.ALERT
        )
    
    async def _send_batch_posting(
        self, 
        companies: List[UKCompany], 
        event_type: WebhookEventType,
        format_type: MakePayloadFormat,
        results: Dict[str, Any]
    ):
        """
        Send leads using batch posting style (array of objects in single request)
        Recommended for large volumes - minimizes HTTPS handshakes
        """
        if not companies:
            return
        
        # Process companies in chunks to respect Make.com execution limits
        chunk_size = min(self.batch_size, len(companies))
        
        for i in range(0, len(companies), chunk_size):
            chunk = companies[i:i + chunk_size]
            
            # Create batch payload
            batch_payload = []
            for company in chunk:
                payload = self._create_payload(company, event_type, format_type)
                batch_payload.append(payload.to_dict())
            
            # Send batch
            try:
                await self._apply_rate_limit()
                success = await self._send_batch_request(batch_payload)
                
                if success:
                    results["successful"] += len(chunk)
                    results["delivered_ids"].extend([c.id for c in chunk])
                    logger.info(f"Successfully sent batch of {len(chunk)} leads")
                else:
                    results["failed"] += len(chunk)
                    results["errors"].append(f"Failed to send batch of {len(chunk)} leads")
                    
            except Exception as e:
                logger.error(f"Error sending batch: {e}")
                results["failed"] += len(chunk)
                results["errors"].append(f"Batch error: {str(e)}")
    
    async def _send_stream_posting(
        self, 
        companies: List[UKCompany], 
        event_type: WebhookEventType,
        format_type: MakePayloadFormat,
        results: Dict[str, Any]
    ):
        """
        Send leads using stream posting style (one JSON object per HTTP request)
        Keeps payloads tiny, failures isolated
        """
        # Send leads individually with proper pacing
        for i, company in enumerate(companies):
            try:
                # Apply rate limiting and pacing
                await self._apply_rate_limit()
                if i > 0:  # Add delay between calls (except first)
                    await asyncio.sleep(self.stream_delay)
                
                success = await self.send_lead(company, event_type, format_type)
                
                if success:
                    results["successful"] += 1
                    results["delivered_ids"].append(company.id)
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Failed to send {company.company_name}")
                    
            except Exception as e:
                logger.error(f"Error sending {company.company_name}: {e}")
                results["failed"] += 1
                results["errors"].append(f"Stream error for {company.company_name}: {str(e)}")
    
    async def _send_batch_request(self, batch_payload: List[Dict[str, Any]]) -> bool:
        """Send batch payload with Make.com optimizations"""
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    headers = {
                        'Content-Type': 'application/json',
                        'User-Agent': 'UK-SEO-Leads-System/1.0'
                    }
                    
                    # Add security header if configured
                    if self.secret:
                        headers['X-Make-Token'] = self.secret
                    
                    async with session.post(
                        self.webhook_url,
                        json=batch_payload,  # Send as array
                        headers=headers
                    ) as response:
                        
                        if response.status == 200:
                            logger.debug(f"Batch webhook delivery successful: {len(batch_payload)} items")
                            return True
                        elif response.status in [429, 502, 503]:
                            # Transient errors - retry with exponential backoff
                            logger.warning(f"Transient error {response.status}, will retry attempt {attempt + 1}")
                        else:
                            # Non-transient error - don't retry
                            logger.error(f"Non-transient error {response.status}: {await response.text()}")
                            return False
                            
            except asyncio.TimeoutError:
                logger.warning(f"Batch webhook timeout on attempt {attempt + 1}")
            except Exception as e:
                logger.warning(f"Batch webhook error on attempt {attempt + 1}: {e}")
            
            # Exponential backoff: 1→2→4→8→16 seconds
            if attempt < self.max_retries:
                wait_time = self.retry_delay * (2 ** attempt)
                logger.info(f"Retrying batch webhook in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        return False
    
    def _create_payload(
        self, 
        company: UKCompany, 
        event_type: WebhookEventType,
        format_type: MakePayloadFormat
    ) -> WebhookPayload:
        """Create webhook payload from company data"""
        
        # Parse JSON fields safely
        critical_issues = []
        recommended_actions = []
        talking_points = []
        
        try:
            if company.critical_issues:
                critical_issues = company.critical_issues if isinstance(company.critical_issues, list) else json.loads(company.critical_issues)
        except (json.JSONDecodeError, TypeError):
            critical_issues = []
        
        try:
            if company.recommended_actions:
                recommended_actions = company.recommended_actions if isinstance(company.recommended_actions, list) else json.loads(company.recommended_actions)
        except (json.JSONDecodeError, TypeError):
            recommended_actions = []
        
        try:
            if company.talking_points:
                talking_points = company.talking_points if isinstance(company.talking_points, list) else json.loads(company.talking_points)
        except (json.JSONDecodeError, TypeError):
            talking_points = []
        
        # Calculate improvement potential
        improvement_potential = None
        if company.seo_overall_score is not None:
            if company.seo_overall_score < 50:
                improvement_potential = "High"
            elif company.seo_overall_score < 70:
                improvement_potential = "Medium"
            else:
                improvement_potential = "Low"
        
        payload = WebhookPayload(
            event_type=event_type.value,
            timestamp=datetime.utcnow().isoformat(),
            lead_id=company.id,
            
            # Company data
            company_name=company.company_name,
            website=company.website,
            city=company.city,
            sector=company.sector or "Unknown",
            source=company.source or "Unknown",
            
            # Contact data
            contact_person=company.contact_person,
            contact_role=company.contact_role,
            contact_email=company.email,
            contact_phone=company.phone,
            contact_linkedin=company.linkedin_url,
            contact_confidence=company.contact_confidence,
            
            # Lead qualification
            lead_score=company.lead_score or 0.0,
            priority_tier=company.priority_tier or "D",
            tier_label=company.tier_label or "Low Priority",
            estimated_value=company.estimated_value,
            urgency=company.urgency,
            
            # SEO data
            seo_score=company.seo_overall_score,
            critical_issues=critical_issues,
            improvement_potential=improvement_potential,
            
            # Sales intelligence
            recommended_actions=recommended_actions,
            talking_points=talking_points
        )
        
        # Optimize payload based on format type
        if format_type == MakePayloadFormat.SUMMARY:
            payload = self._optimize_for_summary(payload)
        elif format_type == MakePayloadFormat.CRM_READY:
            payload = self._optimize_for_crm(payload)
        elif format_type == MakePayloadFormat.ALERT:
            payload = self._optimize_for_alert(payload)
        
        return payload
    
    def _optimize_for_summary(self, payload: WebhookPayload) -> WebhookPayload:
        """Optimize payload for summary format (key fields only)"""
        # Keep only essential fields for summary
        payload.critical_issues = payload.critical_issues[:3]  # Top 3 issues
        payload.recommended_actions = payload.recommended_actions[:2]  # Top 2 actions
        payload.talking_points = payload.talking_points[:3]  # Top 3 points
        return payload
    
    def _optimize_for_crm(self, payload: WebhookPayload) -> WebhookPayload:
        """Optimize payload for CRM import"""
        # Ensure all contact fields are properly formatted
        if payload.contact_phone:
            # Clean phone number format
            payload.contact_phone = payload.contact_phone.replace(" ", "").replace("-", "")
        
        return payload
    
    def _optimize_for_alert(self, payload: WebhookPayload) -> WebhookPayload:
        """Optimize payload for high-priority alerts"""
        # Focus on urgency and value
        payload.recommended_actions = ["IMMEDIATE CONTACT RECOMMENDED"] + payload.recommended_actions[:2]
        return payload
    
    async def _send_with_retry(self, payload: WebhookPayload) -> bool:
        """Send webhook with retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    headers = {
                        'Content-Type': 'application/json',
                        'User-Agent': 'UK-SEO-Leads-System/1.0'
                    }
                    
                    # Add security header if configured  
                    if self.secret:
                        headers['X-Make-Token'] = self.secret
                    
                    async with session.post(
                        self.webhook_url,
                        json=payload.to_dict(),
                        headers=headers
                    ) as response:
                        
                        if response.status == 200:
                            response_data = await response.text()
                            logger.debug(f"Webhook delivery successful: {response.status}")
                            return True
                        elif response.status in [429, 502, 503]:
                            # Transient errors - retry with exponential backoff
                            logger.warning(f"Transient error {response.status}, will retry attempt {attempt + 1}")
                        else:
                            logger.warning(f"Webhook delivery failed: {response.status} - {await response.text()}")
                            
                            # Don't retry on client errors (4xx except 429)
                            if 400 <= response.status < 500 and response.status != 429:
                                return False
                            
            except asyncio.TimeoutError:
                logger.warning(f"Webhook timeout on attempt {attempt + 1}")
            except Exception as e:
                logger.warning(f"Webhook error on attempt {attempt + 1}: {e}")
            
            # Exponential backoff: 1→2→4→8→16 seconds
            if attempt < self.max_retries:
                wait_time = self.retry_delay * (2 ** attempt)
                logger.info(f"Retrying webhook in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        return False
    
    async def _apply_rate_limit(self):
        """Apply rate limiting to prevent overwhelming Make.com"""
        current_time = time.time()
        
        # Clean old timestamps
        cutoff_time = current_time - 60  # 1 minute ago
        self.request_timestamps = [ts for ts in self.request_timestamps if ts > cutoff_time]
        
        # Check if we need to wait
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.request_timestamps[0])
            if sleep_time > 0:
                logger.info(f"Rate limiting: waiting {sleep_time:.1f} seconds")
                await asyncio.sleep(sleep_time)
        
        # Record this request
        self.request_timestamps.append(current_time)
    
    def _filter_companies_for_delivery(self, companies: List[UKCompany]) -> List[UKCompany]:
        """Filter companies based on delivery criteria"""
        filtered = []
        
        for company in companies:
            # Only send qualified leads (score >= 50)
            if company.lead_score and company.lead_score >= 50.0:
                filtered.append(company)
            else:
                logger.debug(f"Skipping {company.company_name}: lead score too low ({company.lead_score})")
        
        return filtered
    
    async def _send_batch_completion(self, results: Dict[str, Any]):
        """Send batch completion notification"""
        try:
            completion_payload = {
                "event_type": WebhookEventType.BATCH_COMPLETE.value,
                "timestamp": datetime.utcnow().isoformat(),
                "batch_summary": {
                    "total_leads": results["total_attempted"],
                    "successful_deliveries": results["successful"],
                    "failed_deliveries": results["failed"],
                    "success_rate": (results["successful"] / results["total_attempted"]) * 100 if results["total_attempted"] > 0 else 0
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=completion_payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        logger.info("Batch completion notification sent successfully")
                    else:
                        logger.warning(f"Batch completion notification failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending batch completion notification: {e}")


# Convenience function for easy integration
async def send_lead_to_make(
    company: UKCompany, 
    event_type: WebhookEventType = WebhookEventType.NEW_LEAD,
    webhook_url: Optional[str] = None
) -> bool:
    """
    Convenience function to send a single lead to Make.com
    
    Args:
        company: UKCompany instance
        event_type: Type of webhook event
        webhook_url: Optional override webhook URL
        
    Returns:
        bool: True if successfully delivered
    """
    sender = MakeWebhookSender(webhook_url=webhook_url)
    return await sender.send_lead(company, event_type)


# Testing and validation functions
async def test_webhook_connection(webhook_url: Optional[str] = None) -> bool:
    """Test webhook connectivity with Make.com"""
    sender = MakeWebhookSender(webhook_url=webhook_url)
    
    test_payload = {
        "event_type": "connection_test",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "UK SEO Leads System - Connection Test",
        "system_info": {
            "version": "1.0",
            "environment": "testing"
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                sender.webhook_url,
                json=test_payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                
                if response.status == 200:
                    logger.info("✅ Webhook connection test successful")
                    return True
                else:
                    logger.error(f"❌ Webhook connection test failed: {response.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Webhook connection test error: {e}")
        return False


if __name__ == "__main__":
    # Test the webhook connection
    import asyncio
    
    async def main():
        print("Testing Make.com webhook connection...")
        success = await test_webhook_connection()
        if success:
            print("✅ Webhook is working correctly!")
        else:
            print("❌ Webhook connection failed. Check URL and network.")
    
    asyncio.run(main()) 