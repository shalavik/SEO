"""
Director Enrichment CLI

Command-line interface for the cost-optimized director enrichment system.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core.director_models import EnrichmentConfig
from .services.director_enrichment_engine import DirectorEnrichmentEngine

console = Console()


def load_config() -> EnrichmentConfig:
    """Load enrichment configuration"""
    return EnrichmentConfig()


def get_companies_house_api_key() -> str:
    """Get Companies House API key from environment"""
    api_key = os.getenv('COMPANIES_HOUSE_API_KEY')
    if not api_key:
        console.print("[red]Error: COMPANIES_HOUSE_API_KEY environment variable not set[/red]")
        console.print("Get your free API key from: https://developer.company-information.service.gov.uk/")
        raise click.Abort()
    return api_key


def display_director_result(result, output_format: str = "table"):
    """Display director enrichment result"""
    if output_format == "json":
        console.print(json.dumps(result.model_dump(), indent=2, default=str))
        return
    
    # Rich table display
    console.print(f"\n[bold blue]Director Enrichment Results for: {result.input_company}[/bold blue]")
    
    # Status panel
    status_color = "green" if result.status == "completed" else "red" if result.status == "failed" else "yellow"
    status_panel = Panel(
        f"Status: [{status_color}]{result.status.upper()}[/{status_color}]\n"
        f"Processing Time: {result.total_processing_time_ms}ms\n"
        f"Total Cost: £{result.total_cost:.2f}",
        title="Processing Summary",
        border_style=status_color
    )
    console.print(status_panel)
    
    if result.error_message:
        console.print(f"[red]Error: {result.error_message}[/red]")
        return
    
    # Enrichment decision
    if result.enrichment_decision:
        decision = result.enrichment_decision
        decision_table = Table(title="Enrichment Decision")
        decision_table.add_column("Property", style="cyan")
        decision_table.add_column("Value", style="white")
        
        decision_table.add_row("Tier", decision.tier.value)
        decision_table.add_row("Budget", f"£{decision.budget:.2f}")
        decision_table.add_row("Priority", decision.priority)
        decision_table.add_row("Max Processing Time", f"{decision.max_processing_time}s")
        decision_table.add_row("Estimated Cost", f"£{decision.estimated_cost:.2f}")
        decision_table.add_row("Allowed Sources", ", ".join([s.value for s in decision.allowed_sources]))
        
        console.print(decision_table)
    
    # Directors found
    if result.director_profiles:
        directors_table = Table(title=f"Directors Found ({len(result.director_profiles)})")
        directors_table.add_column("Name", style="bold white")
        directors_table.add_column("Role", style="cyan")
        directors_table.add_column("Active", style="green")
        directors_table.add_column("Confidence", style="yellow")
        directors_table.add_column("LinkedIn", style="blue")
        directors_table.add_column("Email Hints", style="magenta")
        
        for profile in result.director_profiles:
            director = profile.director
            linkedin_status = "✓" if profile.linkedin_profile else "✗"
            email_hints = len(profile.contact_hints)
            
            directors_table.add_row(
                director.full_name,
                director.role.value.replace('-', ' ').title(),
                "✓" if director.is_active else "✗",
                f"{profile.confidence_score:.2f}",
                linkedin_status,
                str(email_hints)
            )
        
        console.print(directors_table)
        
        # Primary director highlight
        if result.primary_director:
            primary = result.primary_director
            primary_panel = Panel(
                f"[bold]{primary.director.full_name}[/bold]\n"
                f"Role: {primary.director.role.value.replace('-', ' ').title()}\n"
                f"Confidence: {primary.confidence_score:.2f}\n"
                f"LinkedIn: {'Available' if primary.linkedin_profile else 'Not found'}\n"
                f"Contact Hints: {len(primary.contact_hints)}",
                title="🎯 Primary Director",
                border_style="green"
            )
            console.print(primary_panel)
    
    # Confidence report
    if result.confidence_report:
        report = result.confidence_report
        confidence_table = Table(title="Confidence Assessment")
        confidence_table.add_column("Metric", style="cyan")
        confidence_table.add_column("Score", style="white")
        confidence_table.add_column("Status", style="green")
        
        def get_status(score):
            if score >= 0.8:
                return "[green]Excellent[/green]"
            elif score >= 0.6:
                return "[yellow]Good[/yellow]"
            elif score >= 0.4:
                return "[orange3]Fair[/orange3]"
            else:
                return "[red]Poor[/red]"
        
        confidence_table.add_row("Overall", f"{report.overall_confidence:.2f}", get_status(report.overall_confidence))
        confidence_table.add_row("Director ID", f"{report.director_identified:.2f}", get_status(report.director_identified))
        confidence_table.add_row("Email Available", f"{report.email_available:.2f}", get_status(report.email_available))
        confidence_table.add_row("Phone Available", f"{report.phone_available:.2f}", get_status(report.phone_available))
        confidence_table.add_row("LinkedIn Profile", f"{report.linkedin_profile:.2f}", get_status(report.linkedin_profile))
        
        console.print(confidence_table)
        
        if report.data_gaps:
            console.print(f"[yellow]Data Gaps:[/yellow] {', '.join(report.data_gaps)}")
        
        if report.recommended_actions:
            console.print(f"[blue]Recommendations:[/blue]")
            for action in report.recommended_actions:
                console.print(f"  • {action}")


def display_budget_status(budget_status):
    """Display budget status"""
    budget_table = Table(title="💰 Budget Status")
    budget_table.add_column("Metric", style="cyan")
    budget_table.add_column("Value", style="white")
    
    budget_table.add_row("Monthly Budget", f"£{budget_status['monthly_budget']:.2f}")
    budget_table.add_row("Spent", f"£{budget_status['spent']:.2f}")
    budget_table.add_row("Remaining", f"£{budget_status['remaining']:.2f}")
    budget_table.add_row("Usage", f"{budget_status['percentage_used']:.1f}%")
    budget_table.add_row("Leads Processed", str(budget_status['leads_processed']))
    budget_table.add_row("Avg Cost/Lead", f"£{budget_status['average_cost_per_lead']:.2f}")
    
    console.print(budget_table)
    
    # Tier breakdown
    tier_table = Table(title="Tier Breakdown")
    tier_table.add_column("Tier", style="cyan")
    tier_table.add_column("Budget", style="white")
    tier_table.add_column("Spent", style="yellow")
    tier_table.add_column("Count", style="green")
    
    for tier, data in budget_status['tier_breakdown'].items():
        tier_table.add_row(
            f"Tier {tier}",
            f"£{data['budget']:.2f}",
            f"£{data['spent']:.2f}",
            str(data['count'])
        )
    
    console.print(tier_table)


@click.group()
def cli():
    """Director Enrichment CLI - Cost-optimized director discovery and contact enrichment"""
    pass


@cli.command()
@click.argument('company_name')
@click.option('--score', type=float, default=70.0, help='Lead qualification score (0-100)')
@click.option('--tier', type=click.Choice(['A', 'B', 'C']), default='B', help='Priority tier')
@click.option('--website', help='Company website URL')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def enrich(company_name: str, score: float, tier: str, website: Optional[str], output_format: str):
    """Enrich a single company with director information"""
    
    async def run_enrichment():
        config = load_config()
        api_key = get_companies_house_api_key()
        
        engine = DirectorEnrichmentEngine(config, api_key)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Enriching {company_name}...", total=None)
            
            result = await engine.enrich_company_directors(
                company_name=company_name,
                lead_score=score,
                priority_tier=tier,
                website=website
            )
            
            progress.remove_task(task)
        
        display_director_result(result, output_format)
    
    asyncio.run(run_enrichment())


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', type=click.Path(), help='Output file path')
@click.option('--format', 'output_format', type=click.Choice(['json', 'csv']), default='json', help='Output format')
def batch(input_file: str, output: Optional[str], output_format: str):
    """Batch enrich companies from JSON file"""
    
    async def run_batch():
        config = load_config()
        api_key = get_companies_house_api_key()
        
        engine = DirectorEnrichmentEngine(config, api_key)
        
        # Load input data
        with open(input_file, 'r') as f:
            companies = json.load(f)
        
        results = []
        
        with Progress(console=console) as progress:
            task = progress.add_task("Processing companies...", total=len(companies))
            
            for company_data in companies:
                company_name = company_data.get('company_name', company_data.get('name'))
                score = company_data.get('score', 70.0)
                tier = company_data.get('tier', 'B')
                website = company_data.get('website')
                
                result = await engine.enrich_company_directors(
                    company_name=company_name,
                    lead_score=score,
                    priority_tier=tier,
                    website=website
                )
                
                results.append(result.model_dump())
                progress.advance(task)
        
        # Save results
        if output:
            with open(output, 'w') as f:
                if output_format == 'json':
                    json.dump(results, f, indent=2, default=str)
                else:
                    # CSV output would need additional formatting
                    json.dump(results, f, indent=2, default=str)
            
            console.print(f"[green]Results saved to {output}[/green]")
        else:
            console.print(json.dumps(results, indent=2, default=str))
    
    asyncio.run(run_batch())


@cli.command()
def budget():
    """Show current budget status and usage"""
    
    async def show_budget():
        config = load_config()
        api_key = get_companies_house_api_key()
        
        engine = DirectorEnrichmentEngine(config, api_key)
        budget_status = engine.get_budget_status()
        
        display_budget_status(budget_status)
    
    asyncio.run(show_budget())


@cli.command()
@click.option('--companies-house-key', help='Test Companies House API key')
def test(companies_house_key: Optional[str]):
    """Test the director enrichment system"""
    
    async def run_test():
        if companies_house_key:
            os.environ['COMPANIES_HOUSE_API_KEY'] = companies_house_key
        
        config = load_config()
        api_key = get_companies_house_api_key()
        
        engine = DirectorEnrichmentEngine(config, api_key)
        
        # Test with a known UK company
        test_company = "Bozboz Limited"
        
        console.print(f"[blue]Testing director enrichment with: {test_company}[/blue]")
        
        result = await engine.enrich_company_directors(
            company_name=test_company,
            lead_score=75.0,
            priority_tier='B'
        )
        
        display_director_result(result)
        
        # Show budget status
        console.print("\n" + "="*50)
        budget_status = engine.get_budget_status()
        display_budget_status(budget_status)
    
    asyncio.run(run_test())


if __name__ == '__main__':
    cli() 