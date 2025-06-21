"""
Command Line Interface for UK Company SEO Lead Generation System

Provides commands for testing and running the complete pipeline:
- Database initialization
- Company data fetching  
- SEO analysis
- Contact extraction
- Lead qualification
- Data export
"""

import asyncio
import logging
import sys
from typing import Optional
import click
import time

from .config import get_config, get_processing_config
from .database import initialize_database, get_db_session, get_processing_metrics
from .fetchers import YellDirectoryFetcher
from .analyzers import SEOAnalyzer
from .processors import ContactExtractor, LeadQualifier
from .exporters import MakeExporter
from .models import UKCompany

logger = logging.getLogger(__name__)

@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(debug):
    """UK Company SEO Lead Generation System CLI"""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        click.echo("Debug logging enabled")

@cli.command()
def init():
    """Initialize database and configuration"""
    try:
        click.echo("Initializing UK Company SEO Lead Generation System...")
        
        # Initialize database
        db = initialize_database()
        click.echo("✅ Database initialized successfully")
        
        # Show configuration summary
        config = get_config()
        summary = config.get_summary()
        
        click.echo("\nConfiguration Summary:")
        click.echo(f"  Environment: {summary['environment']}")
        click.echo(f"  Database: {summary['database_type']}")
        click.echo(f"  Target cities: {summary['processing']['target_cities']}")
        click.echo(f"  Target sectors: {summary['processing']['target_sectors']}")
        
        # Show API status
        click.echo("\nAPI Configuration:")
        for api, configured in summary['api_keys_configured'].items():
            status = "✅ Configured" if configured else "❌ Missing"
            click.echo(f"  {api}: {status}")
        
        # Validate configuration
        warnings = config.validate()
        if warnings:
            click.echo("\nConfiguration Warnings:")
            for warning in warnings:
                click.echo(f"  ⚠️  {warning}")
        
        click.echo("\n🎉 System initialization complete!")
        
    except Exception as e:
        click.echo(f"❌ Error during initialization: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--cities', default=None, help='Comma-separated list of cities (default: all configured)')
@click.option('--sectors', default=None, help='Comma-separated list of sectors (default: all configured)')
@click.option('--limit', default=10, help='Limit companies per city/sector combination')
def fetch(cities, sectors, limit):
    """Fetch company data from UK directories"""
    try:
        click.echo("Starting company data fetch...")
        
        # Parse cities and sectors
        if cities:
            city_list = [city.strip() for city in cities.split(',')]
        else:
            config = get_processing_config()
            city_list = config.target_cities[:3]  # Limit to first 3 for demo
        
        if sectors:
            sector_list = [sector.strip() for sector in sectors.split(',')]
        else:
            config = get_processing_config()
            sector_list = config.target_sectors[:2]  # Limit to first 2 for demo
        
        click.echo(f"Target cities: {', '.join(city_list)}")
        click.echo(f"Target sectors: {', '.join(sector_list)}")
        
        async def run_fetch():
            # Try Yell.com first
            try:
                async with YellDirectoryFetcher() as fetcher:
                    fetcher.processing_config.max_companies_per_city = limit
                    companies_found = await fetcher.fetch_companies_batch(city_list, sector_list)
                    if companies_found > 0:
                        return companies_found, "Yell.com"
            except Exception as e:
                click.echo(f"⚠️  Yell.com failed: {e}")
            
            # Fallback to Yelp UK
            try:
                from .fetchers.yelp_uk_fetcher import YelpUKDirectoryFetcher
                click.echo("🔄 Trying Yelp UK as fallback...")
                async with YelpUKDirectoryFetcher() as fetcher:
                    fetcher.processing_config.max_companies_per_city = limit
                    companies_found = await fetcher.fetch_companies_batch(city_list, sector_list)
                    return companies_found, "Yelp UK"
            except Exception as e:
                click.echo(f"❌ Yelp UK also failed: {e}")
                return 0, "None"
        
        companies_found, source = asyncio.run(run_fetch())
        
        if companies_found > 0:
            click.echo(f"✅ Fetch complete! Found {companies_found} companies from {source}")
        else:
            click.echo("❌ No companies found from any source")
        
        # Show database stats
        with get_db_session() as session:
            total_companies = session.query(UKCompany).count()
            click.echo(f"📊 Total companies in database: {total_companies}")
        
    except Exception as e:
        click.echo(f"❌ Error during fetch: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--cities', default=None, help='Comma-separated list of cities (default: all configured)')
@click.option('--sectors', default=None, help='Comma-separated list of sectors (default: all configured)')
@click.option('--limit', default=10, help='Limit companies per city/sector combination')
@click.option('--sources', default=None, help='Comma-separated list of sources to try (default: all working sources)')
def fetch_multi(cities, sectors, limit, sources):
    """Fetch company data from multiple UK directories with automatic fallback"""
    try:
        click.echo("🌐 Starting multi-source company data fetch...")
        
        # Parse cities and sectors
        if cities:
            city_list = [city.strip() for city in cities.split(',')]
        else:
            config = get_processing_config()
            city_list = config.target_cities[:3]  # Limit to first 3 for demo
        
        if sectors:
            sector_list = [sector.strip() for sector in sectors.split(',')]
        else:
            config = get_processing_config()
            sector_list = config.target_sectors[:2]  # Limit to first 2 for demo
        
        # Parse sources to try
        if sources:
            source_list = [source.strip() for source in sources.split(',')]
        else:
            # Default to known working sources
            source_list = ['yelp', 'yell']  # Start with known working ones
        
        click.echo(f"Target cities: {', '.join(city_list)}")
        click.echo(f"Target sectors: {', '.join(sector_list)}")
        click.echo(f"Sources to try: {', '.join(source_list)}")
        
        async def run_multi_fetch():
            from .fetchers import get_fetcher
            from .fetchers.yelp_uk_fetcher import YelpUKDirectoryFetcher
            
            total_companies = 0
            successful_sources = []
            
            for source in source_list:
                try:
                    click.echo(f"\n🔍 Trying {source}...")
                    
                    if source == 'yelp':
                        # Use our working Yelp UK fetcher
                        async with YelpUKDirectoryFetcher() as fetcher:
                            fetcher.processing_config.max_companies_per_city = limit
                            companies_found = await fetcher.fetch_companies_batch(city_list, sector_list)
                            if companies_found > 0:
                                click.echo(f"   ✅ {source}: Found {companies_found} companies")
                                total_companies += companies_found
                                successful_sources.append(f"{source} ({companies_found})")
                            else:
                                click.echo(f"   ⚠️  {source}: No companies found")
                    
                    elif source == 'yell':
                        # Try Yell.com
                        async with YellDirectoryFetcher() as fetcher:
                            fetcher.processing_config.max_companies_per_city = limit
                            companies_found = await fetcher.fetch_companies_batch(city_list, sector_list)
                            if companies_found > 0:
                                click.echo(f"   ✅ {source}: Found {companies_found} companies")
                                total_companies += companies_found
                                successful_sources.append(f"{source} ({companies_found})")
                            else:
                                click.echo(f"   ⚠️  {source}: Blocked or no companies found")
                    
                    else:
                        # Try other sources
                        fetcher = get_fetcher(source)
                        async with fetcher:
                            fetcher.processing_config.max_companies_per_city = limit
                            companies_found = await fetcher.fetch_companies_batch(city_list, sector_list)
                            if companies_found > 0:
                                click.echo(f"   ✅ {source}: Found {companies_found} companies")
                                total_companies += companies_found
                                successful_sources.append(f"{source} ({companies_found})")
                            else:
                                click.echo(f"   ⚠️  {source}: No companies found")
                
                except Exception as e:
                    click.echo(f"   ❌ {source}: Failed - {e}")
                    continue
            
            return total_companies, successful_sources
        
        total_companies, successful_sources = asyncio.run(run_multi_fetch())
        
        if total_companies > 0:
            click.echo(f"\n✅ Multi-source fetch complete!")
            click.echo(f"📊 Total companies found: {total_companies}")
            click.echo(f"🎯 Successful sources: {', '.join(successful_sources)}")
        else:
            click.echo("\n❌ No companies found from any source")
        
        # Show database stats
        with get_db_session() as session:
            total_in_db = session.query(UKCompany).count()
            click.echo(f"📊 Total companies in database: {total_in_db}")
        
    except Exception as e:
        click.echo(f"❌ Error during multi-source fetch: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--batch-size', default=10, help='Number of companies to analyze per batch')
def analyze(batch_size):
    """Analyze SEO performance for companies"""
    try:
        click.echo(f"Starting SEO analysis (batch size: {batch_size})...")
        
        analyzer = SEOAnalyzer()
        analyzed_count = analyzer.analyze_batch(batch_size)
        
        click.echo(f"✅ SEO analysis complete! Analyzed {analyzed_count} companies")
        
    except Exception as e:
        click.echo(f"❌ Error during SEO analysis: {e}", err=True)
        sys.exit(1)

@cli.command()
def status():
    """Show system status and processing metrics"""
    try:
        click.echo("UK Company SEO Lead Generation System Status")
        click.echo("=" * 50)
        
        # Get processing metrics
        metrics = get_processing_metrics()
        
        click.echo(f"📊 Overall Statistics:")
        click.echo(f"  Total companies: {metrics.get('total_companies', 0)}")
        click.echo(f"  Processed: {metrics.get('processed_companies', 0)}")
        click.echo(f"  Success rate: {metrics.get('overall_success_rate', 0):.1f}%")
        
        # Show status breakdown
        status_breakdown = metrics.get('status_breakdown', {})
        if status_breakdown:
            click.echo(f"\n📋 Status Breakdown:")
            for status, count in status_breakdown.items():
                click.echo(f"  {status}: {count}")
        
        # Show stage metrics
        stage_metrics = metrics.get('stage_metrics', {})
        if stage_metrics:
            click.echo(f"\n🔄 Stage Progress:")
            for stage, data in stage_metrics.items():
                success_rate = data.get('success_rate', 0)
                processed = data.get('processed', 0)
                total = data.get('total', 0)
                click.echo(f"  {stage}: {processed}/{total} ({success_rate:.1f}%)")
        
    except Exception as e:
        click.echo(f"❌ Error getting status: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--limit', default=10, help='Number of companies to show')
@click.option('--status', default=None, help='Filter by status')
def list_companies(limit, status):
    """List companies in database"""
    try:
        with get_db_session() as session:
            # Build query
            query = session.query(UKCompany)
            
            if status:
                query = query.filter(UKCompany.status == status)
            
            companies = query.limit(limit).all()
            
            if not companies:
                click.echo("No companies found")
                return
            
            click.echo(f"📋 Companies (showing {len(companies)}):")
            click.echo("-" * 80)
            
            for company in companies:
                click.echo(f"🏢 {company.company_name}")
                click.echo(f"   📍 {company.city}, {company.sector}")
                if company.website:
                    click.echo(f"   🌐 {company.website}")
                if company.seo_overall_score:
                    click.echo(f"   📈 SEO Score: {company.seo_overall_score:.1f}")
                click.echo(f"   📊 Status: {company.status}")
                click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error listing companies: {e}", err=True)
        sys.exit(1)

@cli.command()
def test():
    """Run system tests"""
    try:
        click.echo("Running UK Company SEO Lead Generation System Tests...")
        
        # Test 1: Configuration
        click.echo("🧪 Test 1: Configuration loading...")
        config = get_config()
        click.echo("   ✅ Configuration loaded successfully")
        
        # Test 2: Database
        click.echo("🧪 Test 2: Database connection...")
        db = initialize_database()
        click.echo("   ✅ Database connection successful")
        
        # Test 3: Processing metrics
        click.echo("🧪 Test 3: Processing metrics...")
        metrics = get_processing_metrics()
        click.echo(f"   ✅ Metrics retrieved: {metrics.get('total_companies', 0)} companies")
        
        # Test 4: SEO analyzer initialization
        click.echo("🧪 Test 4: SEO analyzer...")
        analyzer = SEOAnalyzer()
        click.echo("   ✅ SEO analyzer initialized successfully")
        
        click.echo("\n🎉 All tests passed!")
        
    except Exception as e:
        click.echo(f"❌ Test failed: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--batch-size', default=20, help='Number of companies to process per batch')
def extract_contacts(batch_size):
    """Extract contact information from company websites"""
    try:
        click.echo(f"Starting contact extraction (batch size: {batch_size})...")
        
        extractor = ContactExtractor()
        extracted_count = extractor.extract_batch(batch_size)
        
        click.echo(f"✅ Contact extraction complete! Extracted {extracted_count} contacts")
        
    except Exception as e:
        click.echo(f"❌ Error during contact extraction: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--batch-size', default=50, help='Number of companies to qualify per batch')
def qualify(batch_size):
    """Qualify leads using multi-factor scoring"""
    try:
        click.echo(f"Starting lead qualification (batch size: {batch_size})...")
        
        qualifier = LeadQualifier()
        qualified_count = qualifier.qualify_batch(batch_size)
        
        click.echo(f"✅ Lead qualification complete! Qualified {qualified_count} leads")
        
    except Exception as e:
        click.echo(f"❌ Error during lead qualification: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--min-score', default=50.0, help='Minimum lead score to export')
@click.option('--format', default='both', help='Export format: json, csv, or both')
@click.option('--webhook/--no-webhook', default=True, help='Send to Make.com webhook')
def export(min_score, format, webhook):
    """Export qualified leads to Make.com"""
    try:
        click.echo(f"Starting export (min score: {min_score}, format: {format})...")
        
        exporter = MakeExporter()
        result = exporter.export_qualified_leads(min_score, format, webhook)
        
        if result['status'] == 'success':
            click.echo(f"✅ Export complete! Exported {result['count']} leads")
            
            for export_type, details in result.get('exports', {}).items():
                if 'filepath' in details:
                    click.echo(f"   📁 {export_type.upper()}: {details['filepath']}")
                if 'status' in details:
                    click.echo(f"   🌐 Webhook: {details['status']}")
        else:
            click.echo(f"❌ Export failed: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        click.echo(f"❌ Error during export: {e}", err=True)
        sys.exit(1)

@cli.command()
def pipeline():
    """Run complete pipeline: fetch → analyze → extract → qualify → export"""
    try:
        click.echo("🚀 Starting complete UK lead generation pipeline...")
        
        # Step 1: Fetch companies (small batch for demo)
        click.echo("\n📥 Step 1: Fetching companies...")
        async def run_fetch():
            # Try Yell.com first
            try:
                async with YellDirectoryFetcher() as fetcher:
                    fetcher.processing_config.max_companies_per_city = 5  # Small demo batch
                    companies_found = await fetcher.fetch_companies_batch(['Brighton'], ['retail'])
                    if companies_found > 0:
                        return companies_found, "Yell.com"
            except Exception as e:
                click.echo(f"⚠️  Yell.com failed: {e}")
            
            # Fallback to Yelp UK
            try:
                from .fetchers.yelp_uk_fetcher import YelpUKDirectoryFetcher
                click.echo("🔄 Trying Yelp UK as fallback...")
                async with YelpUKDirectoryFetcher() as fetcher:
                    fetcher.processing_config.max_companies_per_city = 5  # Small demo batch
                    companies_found = await fetcher.fetch_companies_batch(['Brighton'], ['retail'])
                    return companies_found, "Yelp UK"
            except Exception as e:
                click.echo(f"❌ Yelp UK also failed: {e}")
                return 0, "None"
        
        companies_found, source = asyncio.run(run_fetch())
        
        if companies_found > 0:
            click.echo(f"   ✅ Found {companies_found} companies from {source}")
        else:
            click.echo("❌ No companies found, stopping pipeline")
            return
        
        # Step 2: Analyze SEO
        click.echo("\n🔍 Step 2: Analyzing SEO...")
        analyzer = SEOAnalyzer()
        analyzed_count = analyzer.analyze_batch(companies_found)
        click.echo(f"   ✅ Analyzed {analyzed_count} companies")
        
        # Step 3: Extract contacts
        click.echo("\n📞 Step 3: Extracting contacts...")
        extractor = ContactExtractor()
        extracted_count = extractor.extract_batch(companies_found)
        click.echo(f"   ✅ Extracted {extracted_count} contacts")
        
        # Step 4: Qualify leads
        click.echo("\n🎯 Step 4: Qualifying leads...")
        qualifier = LeadQualifier()
        qualified_count = qualifier.qualify_batch(companies_found)
        click.echo(f"   ✅ Qualified {qualified_count} leads")
        
        # Step 5: Export
        click.echo("\n📤 Step 5: Exporting leads...")
        exporter = MakeExporter()
        result = exporter.export_qualified_leads(50.0, 'both', True)
        
        if result['status'] == 'success':
            click.echo(f"   ✅ Exported {result['count']} leads")
        else:
            click.echo(f"   ⚠️  Export: {result.get('status', 'failed')}")
        
        click.echo("\n🎉 Pipeline complete!")
        
    except Exception as e:
        click.echo(f"❌ Pipeline error: {e}", err=True)
        sys.exit(1)

@cli.command()
def list_sources():
    """List all available UK directory sources and their status"""
    try:
        click.echo("🌐 Available UK Business Directory Sources:")
        click.echo("=" * 60)
        
        from .fetchers import DIRECTORY_SOURCES
        
        # Known working sources
        working_sources = ['yelp']
        blocked_sources = ['yell', 'thomson', 'cylex', 'hotfrog']
        untested_sources = ['brownbook', 'ukcom', 'businessmagnet', 'tupalo', 'foursquare', '192']
        
        for source_name, fetcher_class in DIRECTORY_SOURCES.items():
            try:
                fetcher = fetcher_class()
                base_url = fetcher.get_base_url()
                
                if source_name in working_sources:
                    status = "✅ Working"
                elif source_name in blocked_sources:
                    status = "❌ Blocked/403"
                else:
                    status = "❓ Untested"
                
                click.echo(f"{source_name:12} | {base_url:35} | {status}")
                
            except Exception as e:
                click.echo(f"{source_name:12} | {'Error':35} | ❌ Failed: {e}")
        
        click.echo("\n📊 Summary:")
        click.echo(f"✅ Working: {len(working_sources)} sources")
        click.echo(f"❌ Blocked: {len(blocked_sources)} sources") 
        click.echo(f"❓ Untested: {len(untested_sources)} sources")
        
        click.echo("\n💡 Usage:")
        click.echo("  # Fetch from working sources:")
        click.echo("  python -m src.seo_leads.cli fetch-multi --sources yelp")
        click.echo("  # Test specific sources:")
        click.echo("  python -m src.seo_leads.cli fetch-multi --sources yelp,ukcom,tupalo")
        
    except Exception as e:
        click.echo(f"❌ Error listing sources: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--company-name', required=True, help='Company name to search for executives')
@click.option('--website-url', required=True, help='Company website URL')
@click.option('--linkedin-enabled/--no-linkedin', default=True, help='Enable LinkedIn scraping')
@click.option('--website-enabled/--no-website', default=True, help='Enable website scraping')
@click.option('--parallel/--sequential', default=True, help='Use parallel processing')
def discover_executives(company_name, website_url, linkedin_enabled, website_enabled, parallel):
    """Discover executive contacts for a single company"""
    try:
        import asyncio
        from .processors.executive_discovery import ExecutiveDiscoveryEngine, ExecutiveDiscoveryConfig
        from .processors.executive_email_enricher import ExecutiveEmailEnricher
        
        click.echo(f"🔍 Discovering executives for {company_name}...")
        click.echo(f"   Website: {website_url}")
        click.echo(f"   LinkedIn: {'✅' if linkedin_enabled else '❌'}")
        click.echo(f"   Website: {'✅' if website_enabled else '❌'}")
        click.echo(f"   Processing: {'Parallel' if parallel else 'Sequential'}")
        
        async def run_discovery():
            # Setup configuration
            config = ExecutiveDiscoveryConfig(
                linkedin_enabled=linkedin_enabled,
                website_enabled=website_enabled,
                parallel_processing=parallel,
                max_executives_per_company=10,
                processing_timeout=45.0
            )
            
            # Initialize discovery engine
            engine = ExecutiveDiscoveryEngine(config)
            await engine.initialize()
            
            try:
                # Discover executives
                result = await engine.discover_executives(
                    company_id=f"test-{int(time.time())}",
                    company_name=company_name,
                    website_url=website_url
                )
                
                # Display results
                click.echo(f"\n📊 Discovery Results:")
                click.echo(f"   ⏱️  Processing time: {result.total_processing_time:.2f} seconds")
                click.echo(f"   📈 Success rate: {result.success_rate:.1%}")
                click.echo(f"   🔍 Sources used: {', '.join(result.discovery_sources)}")
                click.echo(f"   👥 Executives found: {len(result.executives_found)}")
                
                if result.primary_decision_maker:
                    pdm = result.primary_decision_maker
                    click.echo(f"\n🎯 Primary Decision Maker:")
                    click.echo(f"   👤 Name: {pdm.full_name}")
                    click.echo(f"   💼 Title: {pdm.title}")
                    click.echo(f"   📧 Email: {pdm.email or 'Not found'}")
                    click.echo(f"   📱 Phone: {pdm.phone or 'Not found'}")
                    click.echo(f"   🔗 LinkedIn: {pdm.linkedin_url or 'Not found'}")
                    click.echo(f"   ⭐ Confidence: {pdm.overall_confidence:.1%}")
                
                if result.executives_found:
                    click.echo(f"\n👥 All Executives ({len(result.executives_found)}):")
                    for i, exec in enumerate(result.executives_found, 1):
                        tier_emoji = "🔥" if exec.seniority_tier == "tier_1" else "⚡" if exec.seniority_tier == "tier_2" else "💫"
                        email_status = "📧" if exec.email else "❌"
                        linkedin_status = "🔗" if exec.linkedin_url else "❌"
                        
                        click.echo(f"   {i}. {tier_emoji} {exec.full_name} - {exec.title}")
                        click.echo(f"      Sources: {', '.join(exec.discovery_sources)} | "
                                 f"Email: {email_status} | LinkedIn: {linkedin_status} | "
                                 f"Confidence: {exec.overall_confidence:.1%}")
                
                # Get engine statistics
                stats = engine.get_statistics()
                click.echo(f"\n📈 Engine Statistics:")
                click.echo(f"   Companies processed: {stats['companies_processed']}")
                click.echo(f"   Executives found: {stats['executives_found']}")
                click.echo(f"   LinkedIn success rate: {stats['linkedin_success_rate']:.1%}")
                click.echo(f"   Website success rate: {stats['website_success_rate']:.1%}")
                
                return result
                
            finally:
                await engine.close()
        
        result = asyncio.run(run_discovery())
        
        if result.executives_found:
            click.echo(f"\n✅ Executive discovery successful!")
        else:
            click.echo(f"\n⚠️  No executives found")
        
    except Exception as e:
        click.echo(f"❌ Error during executive discovery: {e}", err=True)
        import traceback
        click.echo(f"   {traceback.format_exc()}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--batch-size', default=5, help='Number of companies to process')
@click.option('--linkedin-enabled/--no-linkedin', default=True, help='Enable LinkedIn scraping')
@click.option('--website-enabled/--no-website', default=True, help='Enable website scraping')
def test_executive_discovery(batch_size, linkedin_enabled, website_enabled):
    """Test executive discovery on existing companies in database"""
    try:
        import asyncio
        from .processors.executive_discovery import ExecutiveDiscoveryEngine, ExecutiveDiscoveryConfig
        from .database import get_db_session
        from .models import UKCompany
        
        click.echo(f"🧪 Testing executive discovery on {batch_size} companies...")
        
        async def run_test():
            # Get companies from database
            with get_db_session() as session:
                companies = session.query(UKCompany).filter(
                    UKCompany.website_url.isnot(None)
                ).limit(batch_size).all()
                
                if not companies:
                    click.echo("❌ No companies found in database")
                    return
                
                click.echo(f"Found {len(companies)} companies to test")
            
            # Setup configuration
            config = ExecutiveDiscoveryConfig(
                linkedin_enabled=linkedin_enabled,
                website_enabled=website_enabled,
                parallel_processing=True,
                max_executives_per_company=5,
                processing_timeout=30.0,
                delay_between_companies=2.0
            )
            
            # Initialize discovery engine
            engine = ExecutiveDiscoveryEngine(config)
            await engine.initialize()
            
            try:
                results = []
                
                for i, company in enumerate(companies, 1):
                    click.echo(f"\n📊 Processing {i}/{len(companies)}: {company.company_name}")
                    
                    try:
                        result = await engine.discover_executives(
                            str(company.id),
                            company.company_name,
                            company.website_url
                        )
                        results.append(result)
                        
                        exec_count = len(result.executives_found)
                        pdm_found = "✅" if result.primary_decision_maker else "❌"
                        sources = ", ".join(result.discovery_sources)
                        
                        click.echo(f"   Results: {exec_count} executives | PDM: {pdm_found} | Sources: {sources}")
                        
                    except Exception as e:
                        click.echo(f"   ❌ Failed: {e}")
                        continue
                
                # Summary statistics
                total_executives = sum(len(r.executives_found) for r in results)
                companies_with_executives = sum(1 for r in results if r.executives_found)
                companies_with_pdm = sum(1 for r in results if r.primary_decision_maker)
                avg_processing_time = sum(r.total_processing_time for r in results) / len(results) if results else 0
                
                click.echo(f"\n📈 Test Summary:")
                click.echo(f"   Companies processed: {len(results)}")
                click.echo(f"   Total executives found: {total_executives}")
                click.echo(f"   Companies with executives: {companies_with_executives}/{len(results)} ({companies_with_executives/len(results)*100:.1f}%)")
                click.echo(f"   Companies with primary decision maker: {companies_with_pdm}/{len(results)} ({companies_with_pdm/len(results)*100:.1f}%)")
                click.echo(f"   Average processing time: {avg_processing_time:.2f} seconds")
                
                # Engine statistics
                stats = engine.get_statistics()
                click.echo(f"\n🎯 Engine Performance:")
                click.echo(f"   LinkedIn success rate: {stats['linkedin_success_rate']:.1%}")
                click.echo(f"   Website success rate: {stats['website_success_rate']:.1%}")
                click.echo(f"   Overall success rate: {stats['overall_success_rate']:.1%}")
                
                return results
                
            finally:
                await engine.close()
        
        results = asyncio.run(run_test())
        
        if results:
            click.echo(f"\n✅ Executive discovery test complete!")
        else:
            click.echo(f"\n⚠️  Test completed with no results")
        
    except Exception as e:
        click.echo(f"❌ Error during executive discovery test: {e}", err=True)
        import traceback
        click.echo(f"   {traceback.format_exc()}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli() 