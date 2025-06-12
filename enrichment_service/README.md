# Lead Enrichment Service

A comprehensive lead enrichment service similar to Hunter.io, Clearbit, and Apollo.io, specifically designed for UK companies. Provides company data enrichment, email discovery, and contact validation.

## Features

### 🏢 Company Data Enrichment
- **Abstract API Integration**: Company firmographics, technology stack, and social presence
- **OpenCorporates Integration**: Official UK Companies House data and registration information
- **Data Normalization**: Unified company size, industry classifications, and employee data
- **Multi-provider Caching**: SQLite-based caching to minimize API costs

### 📧 Email Discovery & Verification
- **Pattern Generation**: 18+ common email patterns (first.last@domain, first@domain, etc.)
- **SMTP Verification**: Async email deliverability checking with MX record validation
- **Domain Analysis**: Catch-all detection, disposable email filtering, role account identification
- **Confidence Scoring**: Weighted scoring combining pattern likelihood and verification results

### 👥 Contact Enrichment
- **Name Parsing**: Extract first/last names from full names
- **Role Analysis**: Professional title and seniority level detection
- **Email Generation**: Generate most likely email addresses for contacts
- **Social Discovery**: LinkedIn and social media profile discovery

### ⚡ Performance & Reliability
- **Async Architecture**: Concurrent processing with rate limiting
- **Intelligent Caching**: Multi-level caching (verification, MX records, API responses)
- **Error Handling**: Graceful fallbacks and retry mechanisms
- **Batch Processing**: Efficient processing of multiple leads

## Installation

```bash
# Clone and navigate to the enrichment service
cd enrichment_service

# Install dependencies
pip install httpx aiohttp click rich tenacity aiosmtplib dnspython

# Set up environment variables (optional)
export ABSTRACT_API_KEY="your_abstract_api_key"
export OPENCORPORATES_API_KEY="your_opencorporates_api_key"
```

## Quick Start

### Single Lead Enrichment

```bash
# Basic company enrichment
python -m enrichment_service.cli enrich \
  --company "Bozboz" \
  --website "https://bozboz.co.uk" \
  --sector "web development" \
  --city "Brighton"

# With contact information
python -m enrichment_service.cli enrich \
  --company "Gene Commerce Limited" \
  --website "https://genecommerce.com" \
  --contact-name "John Smith" \
  --contact-role "CTO" \
  --verbose
```

### Email Discovery

```bash
# Discover email patterns for a domain
python -m enrichment_service.cli discover-emails \
  --domain "bozboz.co.uk" \
  --first-name "John" \
  --last-name "Smith" \
  --verify
```

### Batch Processing

```bash
# Process multiple leads from JSON file
python -m enrichment_service.cli batch \
  leads_input.json \
  --output enrichment_results \
  --batch-size 10 \
  --providers "abstract,opencorporates"
```

## Input Format

### Single Lead Input
```json
{
  "company_name": "Bozboz",
  "website": "https://bozboz.co.uk",
  "sector": "web development",
  "location": {"city": "Brighton"},
  "existing_contact": {
    "person": "John Smith",
    "role": "CTO"
  }
}
```

### Batch Input (Array of leads)
```json
[
  {
    "company_name": "Company A",
    "website": "https://example-a.com",
    "sector": "technology"
  },
  {
    "company_name": "Company B", 
    "website": "https://example-b.com",
    "sector": "retail"
  }
]
```

## Output Format

### Enriched Lead Structure
```json
{
  "input_data": { /* Original input */ },
  "company_enrichment": {
    "legal_name": "Bozboz Limited",
    "industry": "Web Development",
    "employee_count": 25,
    "size_category": "small",
    "founded_year": 2010,
    "company_number": "07123456",
    "confidence": 0.85
  },
  "contact_enrichments": [{
    "personal": {
      "full_name": "John Smith",
      "first_name": "John",
      "last_name": "Smith"
    },
    "professional": {
      "current_role": "CTO",
      "seniority_level": "c_level"
    },
    "email": "john.smith@bozboz.co.uk",
    "confidence": 0.78
  }],
  "email_discovery": {
    "domain": "bozboz.co.uk",
    "patterns": [{
      "pattern": "first.last",
      "confidence": 0.85,
      "examples": ["john.smith@bozboz.co.uk"]
    }],
    "catch_all": false,
    "mx_records": ["aspmx.l.google.com"],
    "confidence": 0.80
  },
  "status": "enriched",
  "confidence_score": 0.81,
  "processing_time_ms": 1250,
  "data_sources_used": ["abstract_api", "opencorporates", "email_discovery"]
}
```

## Configuration

### Environment Variables

```bash
# API Keys (optional but recommended)
ABSTRACT_API_KEY=your_abstract_key          # For company firmographics
OPENCORPORATES_API_KEY=your_opencorporates_key  # For official company data

# Rate Limiting
SMTP_TIMEOUT=10                              # SMTP verification timeout
MAX_CONCURRENT_VERIFICATIONS=3               # Concurrent email verifications
```

### Provider Configuration

```python
from enrichment_service import EnrichmentEngine

# Initialize with custom configuration
engine = EnrichmentEngine()

# Get provider statistics
stats = engine.get_provider_stats()
print(stats)

# Clear all caches
engine.clear_all_caches()
```

## Architecture

### Core Components

1. **EnrichmentEngine**: Main orchestration service
2. **Providers**: Data source integrations (Abstract API, OpenCorporates)
3. **Normalisers**: Data standardization and merging
4. **Strategies**: Email discovery and validation algorithms
5. **CLI**: Command-line interface for testing and batch processing

### Data Flow

```
Input Lead → Company Enrichment → Email Discovery → Contact Enrichment → Normalized Output
     ↓              ↓                    ↓               ↓
  Domain Extraction  ↓                    ↓               ↓
     ↓         Abstract API          MX Lookup      Name Parsing
     ↓         OpenCorporates        SMTP Verify    Role Analysis
     ↓         Caching              Pattern Gen     Email Generation
```

### Confidence Scoring

The service uses weighted confidence scoring:

- **Company Data**: 50% weight (Abstract API: 0.8, OpenCorporates: 0.9)
- **Contact Data**: 30% weight (based on data completeness)
- **Email Discovery**: 20% weight (MX records + pattern confidence)

Final scores are normalized to 0-1 range with status classification:
- `enriched`: confidence > 0.3
- `partial`: confidence 0.1-0.3  
- `failed`: confidence < 0.1

## Integration Examples

### Python Integration

```python
import asyncio
from enrichment_service import EnrichmentEngine, EnrichmentInput

async def enrich_leads():
    engine = EnrichmentEngine()
    
    # Single lead enrichment
    input_data = EnrichmentInput(
        company_name="Bozboz",
        website="https://bozboz.co.uk",
        sector="web development"
    )
    
    result = await engine.enrich_lead(input_data)
    print(f"Confidence: {result.confidence_score:.2%}")
    print(f"Company: {result.company_enrichment.legal_name}")
    
    # Batch processing
    batch_inputs = [input_data]  # Multiple inputs
    results = await engine.enrich_lead_batch(batch_inputs, max_concurrent=5)
    
    return results

# Run enrichment
results = asyncio.run(enrich_leads())
```

### Integration with Existing SEO Leads

```python
# Convert existing SEO leads to enrichment format
def convert_seo_to_enrichment(seo_lead):
    company_data = seo_lead['company']
    contact_data = seo_lead.get('contact', {})
    
    return EnrichmentInput(
        company_name=company_data['name'],
        website=company_data.get('website'),
        sector=company_data.get('business', {}).get('sector'),
        location=company_data.get('location'),
        existing_contact={
            'person': contact_data.get('person'),
            'role': contact_data.get('role')
        } if contact_data.get('person') else None
    )

# Enrich existing leads
enriched_leads = []
for seo_lead in existing_seo_leads:
    enrichment_input = convert_seo_to_enrichment(seo_lead)
    result = await engine.enrich_lead(enrichment_input)
    enriched_leads.append(result)
```

## Performance Optimizations

### Caching Strategy

1. **API Response Caching**: 30-day cache for Abstract API, 90-day for OpenCorporates
2. **MX Record Caching**: 24-hour cache for DNS lookups
3. **SMTP Verification Caching**: 24-hour cache for email verification results

### Rate Limiting

- **Abstract API**: Respects API rate limits with exponential backoff
- **OpenCorporates**: 2-second delays between requests
- **SMTP Verification**: Domain-based rate limiting (2-second intervals)
- **Concurrent Processing**: Configurable semaphores for batch processing

### Credit Optimization

The service maximizes API credit efficiency:

- **Cache-first Strategy**: Check cache before making API calls
- **Intelligent Fallbacks**: Use free providers when possible
- **Batch Optimization**: Group requests efficiently
- **Error Recovery**: Retry mechanisms for transient failures

## Monitoring & Analytics

### Built-in Metrics

```python
# Get comprehensive statistics
stats = engine.get_provider_stats()

# Sample output:
{
  "abstract_api": {
    "total_cached_entries": 150,
    "successful_entries": 142,
    "cache_hit_potential": "94.7%"
  },
  "opencorporates": {
    "total_cached_entries": 89,
    "name_searches": 45,
    "number_lookups": 44
  },
  "email_discovery": {
    "verification_cache_size": 234,
    "mx_cache_size": 67,
    "domains_rate_limited": 23
  }
}
```

### Success Metrics

Track enrichment effectiveness:
- **Coverage Rate**: % of leads successfully enriched
- **Confidence Distribution**: Quality metrics across confidence bands
- **Provider Performance**: Success rates by data source
- **Processing Speed**: Average enrichment time per lead

## Comparison to Commercial Services

| Feature | Our Service | Hunter.io | Clearbit | Apollo.io |
|---------|-------------|-----------|----------|-----------|
| Company Data | ✅ Abstract + OpenCorporates | ❌ Limited | ✅ Comprehensive | ✅ Good |
| Email Discovery | ✅ Pattern + SMTP | ✅ Excellent | ✅ Good | ✅ Excellent |
| UK Focus | ✅ Specialized | ❌ Global | ❌ Global | ❌ Global |
| API Costs | 💰 Low (cached) | 💰💰 Medium | 💰💰💰 High | 💰💰 Medium |
| Customization | ✅ Full Control | ❌ Limited | ❌ SaaS Only | ❌ Limited |
| Real-time | ✅ Async Processing | ✅ Yes | ✅ Yes | ✅ Yes |

## Development Status

### Completed (Phase 0-2)
- ✅ Project scaffolding and CLI
- ✅ Company lookup (Abstract API + OpenCorporates)
- ✅ Email discovery (pattern generation + SMTP verification)
- ✅ Data normalization and confidence scoring
- ✅ Batch processing and caching

### Future Enhancements (Phase 3+)
- 🔄 SEO scoring integration
- 🔄 Business qualification scoring
- 🔄 CRM integration endpoints
- 🔄 Real-time webhook delivery
- 🔄 Advanced contact discovery (LinkedIn, etc.)

## Contributing

This enrichment service is designed to complement the existing UK Company SEO Lead Generation System, providing Hunter.io/Clearbit/Apollo.io functionality specifically optimized for UK businesses.

For integration with the main SEO system, see the existing codebase in `src/seo_leads/`. 