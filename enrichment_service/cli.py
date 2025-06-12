"""
CLI for Lead Enrichment Service

Provides command-line interface for testing and enriching individual leads.
"""

import asyncio
import json
import sys
from typing import Dict, Any, Optional
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.tree import Tree

from enrichment_service.core.models import EnrichmentInput, EnrichmentResult
from enrichment_service.services.enrichment_engine import EnrichmentEngine

console = Console()

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Lead Enrichment Service CLI
    
    Hunter.io/Clearbit/Apollo.io style lead enrichment for UK companies.
    """
    pass

@cli.command()
@click.option('--company', '-c', required=True, help='Company name')
@click.option('--website', '-w', help='Company website URL')
@click.option('--domain', '-d', help='Company domain (alternative to website)')
@click.option('--city', help='Company city location')
@click.option('--sector', '-s', help='Business sector')
@click.option('--contact-name', help='Existing contact name')
@click.option('--contact-role', help='Existing contact role')
@click.option('--output', '-o', type=click.Path(), help='Output file path (JSON)')
@click.option('--format', 'output_format', 
              type=click.Choice(['json', 'table', 'tree']), 
              default='table', help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--providers', help='Comma-separated list of providers to use')
def enrich(company: str, website: Optional[str], domain: Optional[str], 
           city: Optional[str], sector: Optional[str], contact_name: Optional[str],
           contact_role: Optional[str], output: Optional[str], 
           output_format: str, verbose: bool, providers: Optional[str]):
    """Enrich a single lead with company and contact information."""
    
    # Build enrichment input
    enrichment_input = EnrichmentInput(
        company_name=company,
        website=website,
        domain=domain,
        location={'city': city} if city else None,
        sector=sector,
        existing_contact={
            'person': contact_name,
            'role': contact_role
        } if contact_name or contact_role else None
    )
    
    # Parse providers
    provider_list = providers.split(',') if providers else None
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Enriching lead...", total=None)
        
        try:
            # Run enrichment
            result = asyncio.run(_enrich_lead(enrichment_input, provider_list, verbose))
            
            # Display results
            if output_format == 'json':
                _display_json(result)
            elif output_format == 'tree':
                _display_tree(result)
            else:
                _display_table(result)
            
            # Save to file if requested
            if output:
                _save_result(result, output)
                console.print(f"\n✅ Results saved to {output}")
                
        except Exception as e:
            console.print(f"\n❌ Enrichment failed: {str(e)}", style="red")
            if verbose:
                console.print_exception()
            sys.exit(1)

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output directory')
@click.option('--batch-size', '-b', default=10, help='Batch processing size')
@click.option('--providers', help='Comma-separated list of providers to use')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def batch(input_file: str, output: Optional[str], batch_size: int, 
          providers: Optional[str], verbose: bool):
    """Enrich leads from JSON file in batches."""
    
    input_path = Path(input_file)
    
    try:
        with open(input_path, 'r') as f:
            leads_data = json.load(f)
        
        # Convert to EnrichmentInput objects
        leads = []
        if isinstance(leads_data, list) and 'leads' in leads_data[0]:
            # Handle SEO leads format
            for item in leads_data:
                for lead in item['leads']:
                    company_data = lead.get('company', {})
                    enrichment_input = EnrichmentInput(
                        company_name=company_data.get('name', ''),
                        website=company_data.get('website'),
                        location=company_data.get('location'),
                        sector=company_data.get('business', {}).get('sector'),
                        existing_contact=lead.get('contact')
                    )
                    leads.append(enrichment_input)
        else:
            # Handle direct input format
            for lead_data in leads_data:
                leads.append(EnrichmentInput(**lead_data))
        
        console.print(f"📊 Processing {len(leads)} leads in batches of {batch_size}")
        
        # Process in batches
        results = []
        provider_list = providers.split(',') if providers else None
        
        with Progress(console=console) as progress:
            task = progress.add_task("Processing batches...", total=len(leads))
            
            for i in range(0, len(leads), batch_size):
                batch_leads = leads[i:i + batch_size]
                batch_results = asyncio.run(_enrich_batch(batch_leads, provider_list, verbose))
                results.extend(batch_results)
                progress.advance(task, len(batch_leads))
        
        # Save results
        output_dir = Path(output) if output else Path('enrichment_results')
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"enriched_leads_{len(results)}.json"
        with open(output_file, 'w') as f:
            json.dump([r.model_dump() for r in results], f, indent=2, default=str)
        
        console.print(f"\n✅ Processed {len(results)} leads, saved to {output_file}")
        
        # Show summary
        successful = sum(1 for r in results if r.status == 'enriched')
        failed = len(results) - successful
        
        summary_table = Table(title="Batch Processing Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="magenta")
        summary_table.add_row("Total Processed", str(len(results)))
        summary_table.add_row("Successful", str(successful))
        summary_table.add_row("Failed", str(failed))
        summary_table.add_row("Success Rate", f"{(successful/len(results)*100):.1f}%")
        
        console.print(summary_table)
        
    except Exception as e:
        console.print(f"\n❌ Batch processing failed: {str(e)}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)

@cli.command()
@click.option('--domain', '-d', required=True, help='Domain to discover emails for')
@click.option('--first-name', '-f', help='First name for email generation')
@click.option('--last-name', '-l', help='Last name for email generation')
@click.option('--verify', is_flag=True, help='Verify generated emails via SMTP')
@click.option('--output', '-o', type=click.Path(), help='Output file path (JSON)')
def discover_emails(domain: str, first_name: Optional[str], last_name: Optional[str],
                   verify: bool, output: Optional[str]):
    """Discover email patterns and generate potential emails for a domain."""
    
    try:
        result = asyncio.run(_discover_domain_emails(domain, first_name, last_name, verify))
        
        # Display results
        console.print(Panel(f"🔍 Email Discovery Results for {domain}", style="blue"))
        
        if result.patterns:
            pattern_table = Table(title="Discovered Patterns")
            pattern_table.add_column("Pattern", style="cyan")
            pattern_table.add_column("Confidence", style="green")
            pattern_table.add_column("Examples", style="yellow")
            
            for pattern in result.patterns:
                examples = ", ".join(pattern.examples[:3])
                if len(pattern.examples) > 3:
                    examples += f" (+{len(pattern.examples)-3} more)"
                pattern_table.add_row(
                    pattern.pattern,
                    f"{pattern.confidence:.2%}",
                    examples
                )
            
            console.print(pattern_table)
        
        # Save results
        if output:
            _save_result(result, output)
            console.print(f"\n✅ Results saved to {output}")
            
    except Exception as e:
        console.print(f"\n❌ Email discovery failed: {str(e)}", style="red")
        sys.exit(1)

async def _enrich_lead(enrichment_input: EnrichmentInput, providers: Optional[list], 
                      verbose: bool) -> EnrichmentResult:
    """Enrich a single lead."""
    if verbose:
        console.print(f"Input: {enrichment_input.model_dump()}")
        used_providers = providers or ['email_discovery']
        console.print(f"Used providers: {used_providers}")
        
    engine = EnrichmentEngine()
    result = await engine.enrich_lead(enrichment_input, providers)
    
    if verbose:
        processing_time = getattr(result, 'processing_time_ms', 0)
        console.print(f"Processing time: {processing_time}ms")
        
    return result

async def _enrich_batch(leads: list, providers: Optional[list], 
                       verbose: bool) -> list:
    """Enrich a batch of leads"""
    from enrichment_service.services.enrichment_engine import EnrichmentEngine
    
    engine = EnrichmentEngine()
    results = []
    
    for lead in leads:
        try:
            result = await engine.enrich_lead(lead, providers=providers)
            results.append(result)
        except Exception as e:
            if verbose:
                console.print(f"Failed to enrich {lead.company_name}: {e}")
            # Create failed result
            from enrichment_service.core.models import EnrichmentResult, EnrichmentStatus
            failed_result = EnrichmentResult(
                input_data=lead,
                status=EnrichmentStatus.FAILED,
                error_message=str(e)
            )
            results.append(failed_result)
    
    return results

async def _discover_domain_emails(domain: str, first_name: Optional[str], 
                                 last_name: Optional[str], verify: bool):
    """Discover emails for a domain"""
    from enrichment_service.strategies.email_guess import EmailDiscoveryStrategy
    
    strategy = EmailDiscoveryStrategy()
    result = await strategy.discover_domain_patterns(domain)
    
    if first_name and last_name:
        candidates = await strategy.generate_email_candidates(
            domain, first_name, last_name, verify_emails=verify
        )
        # Add candidates to result somehow
        console.print(f"\nGenerated {len(candidates)} email candidates")
        for candidate in candidates[:5]:  # Show top 5
            console.print(f"  {candidate.email} (confidence: {candidate.confidence:.2%})")
    
    return result

def _display_json(result: EnrichmentResult):
    """Display result as JSON"""
    syntax = Syntax(
        json.dumps(result.model_dump(), indent=2, default=str),
        "json",
        theme="monokai",
        line_numbers=True
    )
    console.print(syntax)

def _display_table(result: EnrichmentResult):
    """Display result as formatted table"""
    console.print(Panel(f"🚀 Enrichment Results", style="green"))
    
    # Company info
    if result.company_enrichment:
        company_table = Table(title="Company Information")
        company_table.add_column("Field", style="cyan")
        company_table.add_column("Value", style="magenta")
        
        comp = result.company_enrichment
        company_table.add_row("Legal Name", comp.legal_name or "N/A")
        company_table.add_row("Industry", comp.industry or "N/A")
        company_table.add_row("Employees", str(comp.employee_count) if comp.employee_count else "N/A")
        company_table.add_row("Founded", str(comp.founded_year) if comp.founded_year else "N/A")
        company_table.add_row("Confidence", f"{comp.confidence:.2%}")
        
        console.print(company_table)
    
    # Contact info
    if result.contact_enrichments:
        for i, contact in enumerate(result.contact_enrichments):
            contact_table = Table(title=f"Contact {i+1}")
            contact_table.add_column("Field", style="cyan")
            contact_table.add_column("Value", style="magenta")
            
            contact_table.add_row("Name", contact.personal.full_name)
            if contact.professional:
                contact_table.add_row("Role", contact.professional.current_role or "N/A")
                contact_table.add_row("Department", contact.professional.department or "N/A")
            if contact.email:
                contact_table.add_row("Email", contact.email)
            contact_table.add_row("Confidence", f"{contact.confidence:.2%}")
            
            console.print(contact_table)
    
    # Status and metrics
    status_table = Table(title="Processing Status")
    status_table.add_column("Metric", style="cyan")
    status_table.add_column("Value", style="magenta")
    
    status_table.add_row("Status", result.status.value)
    status_table.add_row("Overall Confidence", f"{result.confidence_score:.2%}")
    status_table.add_row("Processing Time", f"{result.processing_time_ms}ms" if result.processing_time_ms else "N/A")
    status_table.add_row("Data Sources", ", ".join(result.data_sources_used))
    
    console.print(status_table)

def _display_tree(result: EnrichmentResult):
    """Display result as tree structure"""
    tree = Tree("🚀 Enrichment Result")
    
    # Input branch
    input_branch = tree.add("📥 Input")
    input_branch.add(f"Company: {result.input_data.company_name}")
    if result.input_data.website:
        input_branch.add(f"Website: {result.input_data.website}")
    if result.input_data.sector:
        input_branch.add(f"Sector: {result.input_data.sector}")
    
    # Company enrichment branch
    if result.company_enrichment:
        comp_branch = tree.add("🏢 Company Enrichment")
        comp = result.company_enrichment
        if comp.legal_name:
            comp_branch.add(f"Legal Name: {comp.legal_name}")
        if comp.industry:
            comp_branch.add(f"Industry: {comp.industry}")
        if comp.employee_count:
            comp_branch.add(f"Employees: {comp.employee_count}")
        comp_branch.add(f"Confidence: {comp.confidence:.2%}")
    
    # Contact enrichment branch
    if result.contact_enrichments:
        contact_branch = tree.add("👥 Contact Enrichments")
        for i, contact in enumerate(result.contact_enrichments):
            contact_item = contact_branch.add(f"Contact {i+1}: {contact.personal.full_name}")
            if contact.professional and contact.professional.current_role:
                contact_item.add(f"Role: {contact.professional.current_role}")
            if contact.email:
                contact_item.add(f"Email: {contact.email}")
            contact_item.add(f"Confidence: {contact.confidence:.2%}")
    
    # Status branch
    status_branch = tree.add("📊 Status")
    status_branch.add(f"Status: {result.status.value}")
    status_branch.add(f"Confidence: {result.confidence_score:.2%}")
    if result.processing_time_ms:
        status_branch.add(f"Processing Time: {result.processing_time_ms}ms")
    status_branch.add(f"Sources: {', '.join(result.data_sources_used)}")
    
    console.print(tree)

def _save_result(result, output_path: str):
    """Save result to file"""
    with open(output_path, 'w') as f:
        json.dump(result.dict(), f, indent=2, default=str)

def main():
    """Main CLI entry point"""
    cli()

if __name__ == '__main__':
    main() 