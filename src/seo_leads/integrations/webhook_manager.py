"""
Webhook Management System

Handles webhook delivery queuing, monitoring, retry logic, and delivery analytics
for external integrations like Make.com.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from ..models import UKCompany
from .make_webhook import MakeWebhookSender, WebhookEventType, MakePayloadFormat

logger = logging.getLogger(__name__)

class DeliveryStatus(str, Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    ABANDONED = "abandoned"

@dataclass
class WebhookEvent:
    """Webhook event for delivery queue"""
    id: str
    company: UKCompany
    event_type: WebhookEventType
    format_type: MakePayloadFormat
    created_at: datetime
    attempts: int = 0
    status: DeliveryStatus = DeliveryStatus.PENDING
    last_attempt: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if not self.id:
            # Generate unique ID based on company and timestamp
            self.id = f"{self.company.id}_{self.event_type.value}_{int(self.created_at.timestamp())}"

@dataclass 
class DeliveryMetrics:
    """Webhook delivery analytics"""
    total_events: int = 0
    delivered: int = 0
    failed: int = 0
    pending: int = 0
    success_rate: float = 0.0
    average_delivery_time: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def update_success_rate(self):
        """Calculate current success rate"""
        total_completed = self.delivered + self.failed
        if total_completed > 0:
            self.success_rate = (self.delivered / total_completed) * 100
        else:
            self.success_rate = 0.0


class WebhookManager:
    """
    Manages webhook delivery queue and analytics
    
    Features:
    - Intelligent queuing and batching
    - Retry logic with exponential backoff
    - Priority handling for A-tier leads
    - Delivery analytics and monitoring
    - Error recovery and alerting
    """
    
    def __init__(self, webhook_url: Optional[str] = None, max_queue_size: int = 1000):
        self.sender = MakeWebhookSender(webhook_url=webhook_url)
        self.max_queue_size = max_queue_size
        
        # Delivery queue
        self.priority_queue = deque()  # A-tier leads (immediate)
        self.normal_queue = deque()    # B/C/D-tier leads (batched)
        self.retry_queue = deque()     # Failed deliveries for retry
        
        # Event tracking
        self.events: Dict[str, WebhookEvent] = {}
        self.metrics = DeliveryMetrics()
        
        # Processing state
        self.is_processing = False
        self.processing_task: Optional[asyncio.Task] = None
        
        # Configuration
        self.batch_size = 10
        self.batch_interval = 30  # seconds
        self.max_retries = 3
        self.retry_delays = [30, 300, 1800]  # 30s, 5m, 30m
        
        # Callbacks
        self.delivery_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
    
    async def queue_lead(
        self, 
        company: UKCompany, 
        event_type: WebhookEventType = WebhookEventType.NEW_LEAD,
        format_type: MakePayloadFormat = MakePayloadFormat.FULL_LEAD,
        priority: bool = False
    ) -> str:
        """
        Add lead to delivery queue
        
        Args:
            company: UKCompany instance
            event_type: Webhook event type
            format_type: Payload format
            priority: Force high priority delivery
            
        Returns:
            str: Event ID for tracking
        """
        # Create webhook event
        event = WebhookEvent(
            id="",  # Will be generated in __post_init__
            company=company,
            event_type=event_type,
            format_type=format_type,
            created_at=datetime.utcnow()
        )
        
        # Store event for tracking
        self.events[event.id] = event
        self.metrics.total_events += 1
        self.metrics.pending += 1
        
        # Determine queue priority
        is_high_priority = (
            priority or 
            company.priority_tier == "A" or 
            event_type == WebhookEventType.HIGH_PRIORITY
        )
        
        # Add to appropriate queue
        if is_high_priority:
            self.priority_queue.append(event)
            logger.info(f"Added high-priority lead {company.company_name} to webhook queue")
            
            # Trigger immediate processing for high-priority
            if not self.is_processing:
                asyncio.create_task(self._process_priority_queue())
        else:
            self.normal_queue.append(event)
            logger.debug(f"Added lead {company.company_name} to normal webhook queue")
        
        # Check queue limits
        await self._manage_queue_size()
        
        # Start processing if not already running
        if not self.is_processing:
            await self.start_processing()
        
        return event.id
    
    async def queue_batch(
        self, 
        companies: List[UKCompany], 
        event_type: WebhookEventType = WebhookEventType.NEW_LEAD,
        format_type: MakePayloadFormat = MakePayloadFormat.SUMMARY
    ) -> List[str]:
        """
        Add multiple leads to delivery queue
        
        Args:
            companies: List of UKCompany instances
            event_type: Webhook event type
            format_type: Payload format optimization
            
        Returns:
            List[str]: Event IDs for tracking
        """
        event_ids = []
        
        for company in companies:
            # Auto-detect priority based on tier
            priority = company.priority_tier == "A"
            
            event_id = await self.queue_lead(
                company, 
                event_type, 
                format_type, 
                priority
            )
            event_ids.append(event_id)
        
        logger.info(f"Queued batch of {len(companies)} leads for webhook delivery")
        return event_ids
    
    async def start_processing(self):
        """Start webhook delivery processing"""
        if self.is_processing:
            logger.debug("Webhook processing already running")
            return
        
        self.is_processing = True
        logger.info("Starting webhook delivery processing")
        
        # Start processing tasks
        self.processing_task = asyncio.create_task(self._processing_loop())
    
    async def stop_processing(self):
        """Stop webhook delivery processing"""
        if not self.is_processing:
            return
        
        logger.info("Stopping webhook delivery processing")
        self.is_processing = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
    
    async def _processing_loop(self):
        """Main processing loop for webhook delivery"""
        try:
            while self.is_processing:
                # Process priority queue first
                await self._process_priority_queue()
                
                # Process retry queue
                await self._process_retry_queue()
                
                # Process normal queue in batches
                await self._process_normal_queue()
                
                # Update metrics
                self._update_metrics()
                
                # Wait before next cycle
                await asyncio.sleep(5)  # Check every 5 seconds
                
        except asyncio.CancelledError:
            logger.info("Webhook processing loop cancelled")
        except Exception as e:
            logger.error(f"Error in webhook processing loop: {e}")
            # Restart processing after error
            await asyncio.sleep(10)
            if self.is_processing:
                self.processing_task = asyncio.create_task(self._processing_loop())
    
    async def _process_priority_queue(self):
        """Process high-priority webhook deliveries immediately"""
        while self.priority_queue and self.is_processing:
            event = self.priority_queue.popleft()
            await self._deliver_event(event)
    
    async def _process_normal_queue(self):
        """Process normal queue in batches"""
        if not self.normal_queue:
            return
        
        # Check if it's time for batch processing
        if len(self.normal_queue) >= self.batch_size:
            await self._process_batch()
    
    async def _process_retry_queue(self):
        """Process failed deliveries for retry"""
        retry_ready = []
        
        # Find events ready for retry
        while self.retry_queue:
            event = self.retry_queue.popleft()
            
            if self._is_retry_ready(event):
                retry_ready.append(event)
            else:
                self.retry_queue.append(event)  # Put back in queue
                break  # Stop processing if first event isn't ready
        
        # Process retry-ready events
        for event in retry_ready:
            await self._deliver_event(event)
    
    async def _process_batch(self):
        """Process a batch of normal priority events"""
        batch = []
        
        # Collect batch
        for _ in range(min(self.batch_size, len(self.normal_queue))):
            if self.normal_queue:
                batch.append(self.normal_queue.popleft())
        
        if not batch:
            return
        
        logger.info(f"Processing webhook batch of {len(batch)} events")
        
        # Process batch concurrently
        tasks = [self._deliver_event(event) for event in batch]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _deliver_event(self, event: WebhookEvent):
        """Deliver a single webhook event"""
        event.attempts += 1
        event.last_attempt = datetime.utcnow()
        event.status = DeliveryStatus.RETRYING if event.attempts > 1 else DeliveryStatus.PENDING
        
        try:
            # Deliver webhook
            success = await self.sender.send_lead(
                event.company, 
                event.event_type, 
                event.format_type
            )
            
            if success:
                event.status = DeliveryStatus.DELIVERED
                self.metrics.delivered += 1
                self.metrics.pending -= 1
                
                # Call delivery callbacks
                for callback in self.delivery_callbacks:
                    try:
                        await callback(event)
                    except Exception as e:
                        logger.error(f"Error in delivery callback: {e}")
                
                logger.debug(f"Successfully delivered webhook for {event.company.company_name}")
            else:
                await self._handle_delivery_failure(event)
                
        except Exception as e:
            event.error_message = str(e)
            await self._handle_delivery_failure(event)
    
    async def _handle_delivery_failure(self, event: WebhookEvent):
        """Handle failed webhook delivery"""
        if event.attempts >= self.max_retries:
            # Abandon after max retries
            event.status = DeliveryStatus.ABANDONED
            self.metrics.failed += 1
            self.metrics.pending -= 1
            
            logger.error(f"Abandoned webhook delivery for {event.company.company_name} after {event.attempts} attempts")
            
            # Call error callbacks
            for callback in self.error_callbacks:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in error callback: {e}")
        else:
            # Queue for retry
            event.status = DeliveryStatus.FAILED
            self.retry_queue.append(event)
            
            logger.warning(f"Webhook delivery failed for {event.company.company_name}, attempt {event.attempts}/{self.max_retries}")
    
    def _is_retry_ready(self, event: WebhookEvent) -> bool:
        """Check if event is ready for retry"""
        if event.attempts == 0 or not event.last_attempt:
            return True
        
        # Calculate retry delay based on attempt number
        retry_delay_index = min(event.attempts - 1, len(self.retry_delays) - 1)
        retry_delay = self.retry_delays[retry_delay_index]
        
        time_since_last = (datetime.utcnow() - event.last_attempt).total_seconds()
        return time_since_last >= retry_delay
    
    async def _manage_queue_size(self):
        """Manage queue size to prevent memory issues"""
        total_queued = len(self.priority_queue) + len(self.normal_queue) + len(self.retry_queue)
        
        if total_queued > self.max_queue_size:
            # Remove oldest normal queue items first
            removed = 0
            while len(self.normal_queue) > 0 and total_queued > self.max_queue_size:
                old_event = self.normal_queue.popleft()
                old_event.status = DeliveryStatus.ABANDONED
                self.metrics.failed += 1
                self.metrics.pending -= 1
                removed += 1
                total_queued -= 1
            
            if removed > 0:
                logger.warning(f"Removed {removed} events from webhook queue due to size limit")
    
    def _update_metrics(self):
        """Update delivery metrics"""
        self.metrics.update_success_rate()
        self.metrics.last_updated = datetime.utcnow()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current webhook manager status"""
        return {
            "is_processing": self.is_processing,
            "queue_sizes": {
                "priority": len(self.priority_queue),
                "normal": len(self.normal_queue), 
                "retry": len(self.retry_queue)
            },
            "metrics": {
                "total_events": self.metrics.total_events,
                "delivered": self.metrics.delivered,
                "failed": self.metrics.failed,
                "pending": self.metrics.pending,
                "success_rate": self.metrics.success_rate
            },
            "webhook_url": self.sender.webhook_url[:50] + "..." if self.sender.webhook_url else None
        }
    
    def get_event_status(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific event"""
        event = self.events.get(event_id)
        if not event:
            return None
        
        return {
            "id": event.id,
            "company_name": event.company.company_name,
            "event_type": event.event_type.value,
            "status": event.status.value,
            "attempts": event.attempts,
            "created_at": event.created_at.isoformat(),
            "last_attempt": event.last_attempt.isoformat() if event.last_attempt else None,
            "error_message": event.error_message
        }
    
    def add_delivery_callback(self, callback: Callable):
        """Add callback for successful deliveries"""
        self.delivery_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """Add callback for delivery errors"""
        self.error_callbacks.append(callback)


# Global webhook manager instance
webhook_manager: Optional[WebhookManager] = None

def get_webhook_manager() -> WebhookManager:
    """Get global webhook manager instance"""
    global webhook_manager
    if webhook_manager is None:
        webhook_manager = WebhookManager()
    return webhook_manager


# Convenience functions
async def queue_lead_for_delivery(
    company: UKCompany, 
    priority: bool = False
) -> str:
    """Queue a lead for webhook delivery"""
    manager = get_webhook_manager()
    return await manager.queue_lead(company, priority=priority)

async def queue_batch_for_delivery(companies: List[UKCompany]) -> List[str]:
    """Queue multiple leads for webhook delivery"""
    manager = get_webhook_manager()
    return await manager.queue_batch(companies)

def get_delivery_status() -> Dict[str, Any]:
    """Get current delivery status"""
    manager = get_webhook_manager()
    return manager.get_status() 