#!/usr/bin/env python3
"""
HTML Content Analysis Test

Direct analysis of HTML content to understand why executives are not being found.
"""

import asyncio
import logging
import sys
from pathlib import Path
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def analyze_html_content():
    """Analyze HTML content from Jack The Plumber about page"""
    
    test_url = "https://jacktheplumber.co.uk/about"
    
    logger.info(f"🔍 Analyzing HTML content from: {test_url}")
    
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(test_url, timeout=30000)
            await page.wait_for_load_state('domcontentloaded')
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Get clean text content
            text_content = soup.get_text()
            
            logger.info(f"📄 Total content length: {len(content)} chars")
            logger.info(f"📄 Text content length: {len(text_content)} chars")
            
            # Show first 1000 characters of text content
            logger.info(f"📝 Text content preview:\n{text_content[:1000]}...")
            
            # Look for potential names in the content
            # Common name patterns
            name_patterns = [
                r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # First Last
                r'\b[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+\b',  # First M. Last
                r'\b[A-Z]\. [A-Z][a-z]+\b',  # J. Smith
            ]
            
            found_names = set()
            for pattern in name_patterns:
                matches = re.findall(pattern, text_content)
                found_names.update(matches)
            
            # Filter out common false positives
            filtered_names = []
            false_positives = ['Privacy Policy', 'Terms Conditions', 'Cookie Policy', 'United Kingdom', 'South London', 'Gas Safe', 'Emergency Plumber']
            
            for name in found_names:
                if name not in false_positives and not any(fp in name for fp in false_positives):
                    filtered_names.append(name)
            
            logger.info(f"👤 Potential names found: {filtered_names}")
            
            # Look for executive titles
            title_patterns = [
                r'\b(CEO|CTO|CFO|COO|President|Director|Manager|Owner|Founder|Partner)\b',
                r'\b(Managing Director|Executive Director|General Manager)\b',
                r'\b(Head of|Chief|Senior|Lead)\b',
                r'\b(Proprietor|Principal|Chairman|MD)\b'
            ]
            
            found_titles = set()
            for pattern in title_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                found_titles.update([match.lower() for match in matches])
            
            logger.info(f"💼 Potential titles found: {list(found_titles)}")
            
            # Look for contact information
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            phone_pattern = r'(\+44|0)[0-9\s\-\(\)]{8,15}'
            
            emails = re.findall(email_pattern, text_content)
            phones = re.findall(phone_pattern, text_content)
            
            logger.info(f"📧 Emails found: {emails}")
            logger.info(f"📞 Phones found: {phones}")
            
            # Check for team card structures
            team_selectors = [
                '.team-member', '.staff-member', '.employee',
                '.person', '.bio', '.profile', '.team-card',
                '.leadership-member', '.executive', '.director'
            ]
            
            logger.info("🔍 Checking for team card structures:")
            for selector in team_selectors:
                cards = soup.select(selector)
                if cards:
                    logger.info(f"  Found {len(cards)} elements with selector: {selector}")
                    
            # Check for specific text patterns that might indicate executive presence
            executive_keywords = ['founder', 'owner', 'director', 'manager', 'ceo', 'proprietor', 'principal']
            logger.info("🔍 Looking for executive keywords in text:")
            for keyword in executive_keywords:
                if keyword.lower() in text_content.lower():
                    # Find context around the keyword
                    pattern = rf'.{{0,50}}{re.escape(keyword)}.{{0,50}}'
                    matches = re.findall(pattern, text_content, re.IGNORECASE)
                    for match in matches[:3]:  # Show first 3 matches
                        logger.info(f"  '{keyword}' context: ...{match.strip()}...")
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_html_content()) 