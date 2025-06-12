# PROJECT BRIEF - UK Company SEO Lead Generation System

## PROJECT OVERVIEW
**Name:** UK Company SEO Lead Generation System  
**Purpose:** Automatically identify UK-based companies with weak SEO and enrich their contact details for sales outreach  
**Target Market:** UK businesses with suboptimal SEO implementations  
**Business Goal:** Generate qualified leads for SEO services

## SCOPE & OBJECTIVES

### Primary Objectives
1. **Data Collection:** Scrape UK business directories (Yell.com, etc.) for company listings
2. **SEO Assessment:** Evaluate each company's SEO health using Google PageSpeed API
3. **Lead Qualification:** Filter companies with SEO scores < 70 or missing key SEO elements
4. **Contact Enrichment:** Extract contact information from company websites
5. **Data Export:** Prepare structured data for Make.com automation workflow

### Success Criteria
- Successfully scrape and process 1000+ UK company listings
- Accurately assess SEO health with <5% false positives
- Extract contact information with >80% success rate
- Deliver clean, structured data ready for outreach automation

## TECHNICAL REQUIREMENTS

### Core Technologies
- **Python:** Primary development language
- **Scraping:** requests/Playwright for robust web scraping
- **APIs:** Google PageSpeed API for SEO analysis
- **Data Processing:** pandas for data manipulation
- **Output:** JSON/CSV formats for Make.com integration

### Integration Points
- **Input:** Public UK business directories
- **Processing:** SEO analysis and contact extraction
- **Output:** HTTP webhook to Make.com OR file-based handoff

### Performance Requirements
- Rate limiting for API calls to avoid blocks
- Robust error handling and retry logic
- Scalable architecture for processing large datasets
- Efficient data storage and retrieval

## DELIVERABLES

### Phase 1: Cursor Development (This Project)
1. Web scraping module for UK business directories
2. SEO analysis engine using Google PageSpeed API
3. Contact information extraction system
4. Data filtering and quality assurance
5. Export functionality for Make.com integration

### Phase 2: Make.com Automation (External)
1. Lead enrichment with additional data sources
2. CRM integration for lead management
3. Automated outreach sequence setup
4. Performance tracking and analytics

## CONSTRAINTS & CONSIDERATIONS

### Technical Constraints
- Must respect website rate limits and robots.txt
- API quotas and usage limits for Google PageSpeed
- Data privacy and GDPR compliance for UK businesses
- Robust error handling for network issues

### Business Constraints
- Focus on UK market only
- Specific SEO criteria for lead qualification
- Integration requirements with Make.com platform
- Scalability for future expansion

## PROJECT TIMELINE
- **Development Phase:** 1-2 weeks (Cursor implementation)
- **Testing Phase:** 2-3 days (validation and optimization)
- **Integration Phase:** 1-2 days (Make.com handoff setup)
- **Total Estimated Duration:** 2-3 weeks

## RISK ASSESSMENT
- **Medium Risk:** Website structure changes affecting scraping
- **Medium Risk:** API rate limits impacting processing speed
- **Low Risk:** Data quality issues requiring manual review
- **Low Risk:** Integration compatibility with Make.com

## STAKEHOLDER ALIGNMENT
- **Developer:** Focus on robust, maintainable code
- **Business User:** Emphasis on lead quality and automation
- **End Users:** Clean, actionable data for outreach campaigns 