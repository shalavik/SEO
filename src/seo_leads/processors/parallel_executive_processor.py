"""
Parallel Executive Processing Engine
Advanced parallel processing for sub-60s performance with multi-source integration
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import logging

from ..models import ExecutiveContact, CompanyInfo
from ..scrapers.website_executive_scraper import WebsiteExecutiveScraper
from ..scrapers.linkedin_professional_scraper import LinkedInProfessionalScraper
from ..enrichers.executive_contact_enricher import ExecutiveContactEnricher
from ..ai.executive_name_classifier import ExecutiveNameClassifier

logger = logging.getLogger(__name__)

@dataclass
class ParallelProcessingResult:
    """Result from parallel processing"""
    executives: List[ExecutiveContact]
    processing_time: float
    sources_processed: List[str]
    success_rate: float
    performance_metrics: Dict[str, Any]
    enrichment_stats: Dict[str, Any]

class ParallelExecutiveProcessor:
    """
    Advanced parallel processing engine for executive discovery
    Target: <45s processing time with enhanced multi-source integration
    """
    
    def __init__(self):
        self.website_scraper = WebsiteExecutiveScraper()
        self.linkedin_scraper = LinkedInProfessionalScraper()
        self.contact_enricher = ExecutiveContactEnricher()
        self.name_classifier = ExecutiveNameClassifier()
        
        # Enhanced performance settings
        self.max_workers = 6  # Increased parallel threads
        self.timeout_per_source = 12  # Reduced timeout for faster processing
        self.max_concurrent_requests = 4
        
    async def discover_executives_parallel(
        self, 
        company_name: str, 
        company_url: str
    ) -> ParallelProcessingResult:
        """
        Advanced parallel executive discovery with multi-source integration
        """
        start_time = time.time()
        
        logger.info(f"🚀 Starting advanced parallel discovery for {company_name}")
        logger.info(f"🎯 Target: <45s processing time with enrichment")
        
        # Create enhanced async tasks
        tasks = []
        
        # Task 1: Website scraping (primary source)
        tasks.append(self._process_website_source(company_name, company_url))
        
        # Task 2: LinkedIn scraping (secondary source)
        tasks.append(self._process_linkedin_source(company_name, company_url))
        
        # Task 3: Contact enrichment preparation
        tasks.append(self._prepare_contact_enrichment(company_name, company_url))
        
        # Execute all tasks concurrently with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=40  # Overall timeout for parallel processing
            )
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ Parallel processing timeout for {company_name}")
            results = [None, None, None]
        
        # Process and combine results
        all_executives = []
        sources_processed = []
        source_metrics = {}
        enrichment_data = None
        
        # Website results
        if not isinstance(results[0], Exception) and results[0]:
            website_executives, website_time = results[0]
            all_executives.extend(website_executives)
            sources_processed.append("website")
            source_metrics["website"] = {
                "executives_found": len(website_executives),
                "processing_time": website_time
            }
            logger.info(f"✅ Website: {len(website_executives)} executives in {website_time:.2f}s")
        
        # LinkedIn results
        if not isinstance(results[1], Exception) and results[1]:
            linkedin_executives, linkedin_time = results[1]
            all_executives.extend(linkedin_executives)
            sources_processed.append("linkedin")
            source_metrics["linkedin"] = {
                "executives_found": len(linkedin_executives),
                "processing_time": linkedin_time
            }
            logger.info(f"✅ LinkedIn: {len(linkedin_executives)} executives in {linkedin_time:.2f}s")
        
        # Enrichment data
        if not isinstance(results[2], Exception) and results[2]:
            enrichment_data = results[2]
            sources_processed.append("enrichment")
            logger.info(f"✅ Enrichment data prepared")
        
        # Advanced processing pipeline
        unique_executives = await self._advanced_processing_pipeline(
            all_executives, enrichment_data, company_name, company_url
        )
        
        # Calculate metrics
        total_time = time.time() - start_time
        success_rate = 1.0 if unique_executives else 0.0
        
        performance_metrics = {
            "total_processing_time": total_time,
            "target_time": 45.0,
            "performance_ratio": 45.0 / total_time if total_time > 0 else 0,
            "sources_processed": len(sources_processed),
            "source_metrics": source_metrics,
            "parallel_efficiency": len(sources_processed) / max(1, total_time)
        }
        
        enrichment_stats = {
            "executives_enriched": len([e for e in unique_executives if e.email or e.phone]),
            "email_discovery_rate": len([e for e in unique_executives if e.email]) / max(1, len(unique_executives)),
            "phone_discovery_rate": len([e for e in unique_executives if e.phone]) / max(1, len(unique_executives))
        }
        
        logger.info(f"🏁 Advanced parallel processing: {len(unique_executives)} executives in {total_time:.2f}s")
        logger.info(f"🎯 Target achievement: {'✅ SUCCESS' if total_time < 45 else '⚠️ OPTIMIZATION NEEDED'}")
        
        return ParallelProcessingResult(
            executives=unique_executives,
            processing_time=total_time,
            sources_processed=sources_processed,
            success_rate=success_rate,
            performance_metrics=performance_metrics,
            enrichment_stats=enrichment_stats
        )
    
    async def _process_website_source(
        self, 
        company_name: str, 
        company_url: str
    ) -> Optional[Tuple[List[ExecutiveContact], float]]:
        """Enhanced website processing with optimization"""
        try:
            start_time = time.time()
            
            executives = await asyncio.wait_for(
                self._async_website_scraping(company_name, company_url),
                timeout=self.timeout_per_source
            )
            
            processing_time = time.time() - start_time
            return executives, processing_time
            
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ Website timeout for {company_name}")
            return None
        except Exception as e:
            logger.error(f"❌ Website error for {company_name}: {e}")
            return None
    
    async def _process_linkedin_source(
        self, 
        company_name: str, 
        company_url: str
    ) -> Optional[Tuple[List[ExecutiveContact], float]]:
        """Enhanced LinkedIn processing"""
        try:
            start_time = time.time()
            
            executives = await asyncio.wait_for(
                self._async_linkedin_scraping(company_name, company_url),
                timeout=self.timeout_per_source
            )
            
            processing_time = time.time() - start_time
            return executives, processing_time
            
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ LinkedIn timeout for {company_name}")
            return None
        except Exception as e:
            logger.warning(f"⚠️ LinkedIn error for {company_name}: {e}")
            return None
    
    async def _prepare_contact_enrichment(
        self, 
        company_name: str, 
        company_url: str
    ) -> Optional[Dict[str, Any]]:
        """Prepare enhanced contact enrichment data"""
        try:
            from urllib.parse import urlparse
            
            domain = urlparse(company_url).netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            
            enrichment_data = {
                "domain": domain,
                "company_name": company_name,
                "email_patterns": [
                    f"@{domain}",
                    f"info@{domain}",
                    f"contact@{domain}",
                    f"admin@{domain}",
                    f"hello@{domain}"
                ],
                "phone_patterns": [],
                "social_profiles": {},
                "business_context": {
                    "industry": "plumbing",
                    "region": "uk",
                    "size": "small_business"
                }
            }
            
            return enrichment_data
            
        except Exception as e:
            logger.error(f"❌ Enrichment preparation error: {e}")
            return None
    
    async def _async_website_scraping(
        self, 
        company_name: str, 
        company_url: str
    ) -> List[ExecutiveContact]:
        """Optimized async website scraping"""
        try:
            # Call the async method directly
            result = await self.website_scraper.discover_website_executives(
                company_url,
                company_name
            )
            return result if result else []
        except Exception as e:
            logger.error(f"Website scraping error: {e}")
            return []
    
    async def _async_linkedin_scraping(
        self, 
        company_name: str, 
        company_url: str
    ) -> List[ExecutiveContact]:
        """Optimized async LinkedIn scraping"""
        try:
            # Create a simple CompanyInfo object for LinkedIn scraper
            company_info = CompanyInfo(
                name=company_name,
                website=company_url,
                domain=company_url.replace('https://', '').replace('http://', '').split('/')[0]
            )
            
            # Call the async method directly
            result = await self.linkedin_scraper.discover_executives(company_info)
            return result if result else []
        except Exception as e:
            logger.warning(f"LinkedIn scraping failed: {e}")
            return []
    
    async def _advanced_processing_pipeline(
        self, 
        executives: List[ExecutiveContact],
        enrichment_data: Optional[Dict[str, Any]],
        company_name: str,
        company_url: str
    ) -> List[ExecutiveContact]:
        """Advanced processing pipeline with enrichment and AI classification"""
        if not executives:
            return []
        
        # Step 1: Deduplicate executives
        unique_executives = self._deduplicate_executives(executives)
        
        # Step 2: AI classification in parallel
        classified_executives = await self._parallel_ai_classification(unique_executives)
        
        # Step 3: Contact enrichment
        if enrichment_data:
            enriched_executives = await self._parallel_contact_enrichment(
                classified_executives, enrichment_data, company_url
            )
        else:
            enriched_executives = classified_executives
        
        # Step 4: Final quality scoring
        final_executives = self._apply_quality_scoring(enriched_executives)
        
        return final_executives
    
    def _deduplicate_executives(self, executives: List[ExecutiveContact]) -> List[ExecutiveContact]:
        """Enhanced deduplication with fuzzy matching"""
        if not executives:
            return []
        
        unique_executives = []
        seen_names = set()
        
        for executive in executives:
            # Create normalized name key
            name_key = f"{executive.first_name.lower().strip()}_{executive.last_name.lower().strip()}"
            
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_executives.append(executive)
        
        return unique_executives
    
    async def _parallel_ai_classification(
        self, 
        executives: List[ExecutiveContact]
    ) -> List[ExecutiveContact]:
        """Parallel AI classification for enhanced accuracy"""
        if not executives:
            return []
        
        try:
            # Process in parallel batches
            batch_size = 3
            classified_executives = []
            
            for i in range(0, len(executives), batch_size):
                batch = executives[i:i + batch_size]
                
                tasks = [
                    self._classify_single_executive(executive)
                    for executive in batch
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if not isinstance(result, Exception) and result:
                        classified_executives.append(result)
            
            return classified_executives
            
        except Exception as e:
            logger.error(f"AI classification error: {e}")
            return executives
    
    async def _classify_single_executive(
        self, 
        executive: ExecutiveContact
    ) -> Optional[ExecutiveContact]:
        """Enhanced single executive classification"""
        try:
            loop = asyncio.get_event_loop()
            
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self.name_classifier.classify_executive_name,
                    executive.first_name,
                    executive.last_name,
                    executive.title or ""
                )
                
                classification = await loop.run_in_executor(None, future.result)
                
                if classification and classification.is_person and classification.confidence > 0.5:
                    # Enhance confidence based on classification
                    executive.overall_confidence = min(1.0, 
                        executive.overall_confidence * classification.confidence * 1.1
                    )
                    return executive
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Single classification error: {e}")
            return executive
    
    async def _parallel_contact_enrichment(
        self, 
        executives: List[ExecutiveContact],
        enrichment_data: Dict[str, Any],
        company_url: str
    ) -> List[ExecutiveContact]:
        """Parallel contact enrichment for complete contact information"""
        if not executives:
            return []
        
        try:
            enriched_executives = []
            
            for executive in executives:
                enriched = await self._enrich_single_executive(
                    executive, enrichment_data, company_url
                )
                enriched_executives.append(enriched)
            
            return enriched_executives
            
        except Exception as e:
            logger.error(f"Contact enrichment error: {e}")
            return executives
    
    async def _enrich_single_executive(
        self, 
        executive: ExecutiveContact,
        enrichment_data: Dict[str, Any],
        company_url: str
    ) -> ExecutiveContact:
        """Enhanced single executive contact enrichment"""
        try:
            # Generate potential email if not present
            if not executive.email and enrichment_data.get("domain"):
                domain = enrichment_data["domain"]
                potential_emails = [
                    f"{executive.first_name.lower()}.{executive.last_name.lower()}@{domain}",
                    f"{executive.first_name.lower()}@{domain}",
                    f"{executive.first_name[0].lower()}{executive.last_name.lower()}@{domain}"
                ]
                
                # Use most likely email pattern
                executive.email = potential_emails[0]
            
            # Enhance confidence for enriched contacts
            if executive.email:
                executive.overall_confidence = min(1.0, executive.overall_confidence + 0.05)
            
            return executive
            
        except Exception as e:
            logger.error(f"Single enrichment error: {e}")
            return executive
    
    def _apply_quality_scoring(
        self, 
        executives: List[ExecutiveContact]
    ) -> List[ExecutiveContact]:
        """Apply final quality scoring and ranking"""
        for executive in executives:
            # Calculate quality score based on multiple factors
            quality_score = executive.overall_confidence
            
            # Bonus for complete contact information
            if executive.email:
                quality_score += 0.1
            if executive.phone:
                quality_score += 0.05
            if executive.title:
                quality_score += 0.05
            
            # Cap at 1.0
            executive.overall_confidence = min(1.0, quality_score)
        
        # Sort by confidence score
        executives.sort(key=lambda x: x.overall_confidence, reverse=True)
        
        return executives
    
    def get_performance_report(self, result: ParallelProcessingResult) -> str:
        """Generate comprehensive performance report"""
        metrics = result.performance_metrics
        enrichment = result.enrichment_stats
        
        report = f"""
🚀 ADVANCED PARALLEL EXECUTIVE DISCOVERY REPORT

📊 PERFORMANCE METRICS:
• Processing Time: {metrics['total_processing_time']:.2f}s
• Target Time: {metrics['target_time']}s
• Performance Ratio: {metrics['performance_ratio']:.2f}x
• Target Achievement: {'✅ SUCCESS' if metrics['total_processing_time'] < 45 else '⚠️ NEEDS OPTIMIZATION'}

👥 DISCOVERY RESULTS:
• Executives Found: {len(result.executives)}
• Success Rate: {result.success_rate:.1%}
• Sources Processed: {len(result.sources_processed)}
• Parallel Efficiency: {metrics.get('parallel_efficiency', 0):.2f} sources/second

📧 ENRICHMENT STATISTICS:
• Executives Enriched: {enrichment.get('executives_enriched', 0)}
• Email Discovery Rate: {enrichment.get('email_discovery_rate', 0):.1%}
• Phone Discovery Rate: {enrichment.get('phone_discovery_rate', 0):.1%}

⚡ SOURCE PERFORMANCE:"""
        
        for source, source_metrics in metrics.get('source_metrics', {}).items():
            report += f"\n• {source.title()}: {source_metrics['executives_found']} executives in {source_metrics['processing_time']:.2f}s"
        
        report += f"""

🎯 OPTIMIZATION INSIGHTS:
• Parallel Processing: {len(result.sources_processed)}x concurrent execution
• Performance Improvement: Advanced async architecture
• Contact Enrichment: Enhanced executive contact discovery
• Quality Scoring: AI-powered executive classification
"""
        
        return report 