#!/usr/bin/env python3
"""
Cascade Debt Data Scraper

This script automates the download of loan tape and financial data from
the Cascade Debt platform using Playwright for browser automation.

Usage:
    python scripts/scrape_cascade.py [--loan-tape] [--financials] [--all]

Options:
    --loan-tape     Download loan tape export
    --financials    Download financial statements
    --all           Download all available data sources
    --output-dir    Output directory (default: data/cascade)

Environment Variables:
    CASCADE_USERNAME    Cascade Debt username
    CASCADE_PASSWORD    Cascade Debt password
    CASCADE_PID         Portfolio ID (default: abaco)
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import asyncio
from playwright.async_api import async_playwright, Browser, Page

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CASCADE_BASE_URL = "https://app.cascadedebt.com"
CASCADE_LOGIN_URL = f"{CASCADE_BASE_URL}/login"
CASCADE_ANALYTICS_URL = f"{CASCADE_BASE_URL}/analytics/risk/overview"


class CascadeScraper:
    """Automated scraper for Cascade Debt platform."""
    
    def __init__(self, username: str, password: str, pid: str = "abaco"):
        self.username = username
        self.password = password
        self.pid = pid
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def initialize(self):
        """Initialize browser and page."""
        logger.info("Initializing Playwright browser")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
    
    async def cleanup(self):
        """Clean up browser resources."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        logger.info("Browser cleanup complete")
    
    async def login(self) -> bool:
        """Login to Cascade Debt platform.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            logger.info(f"Navigating to {CASCADE_LOGIN_URL}")
            await self.page.goto(CASCADE_LOGIN_URL)
            
            # Wait for login form
            await self.page.wait_for_selector('input[type="email"], input[name="email"]', timeout=10000)
            
            # Fill in credentials
            logger.info(f"Logging in as {self.username}")
            await self.page.fill('input[type="email"], input[name="email"]', self.username)
            await self.page.fill('input[type="password"], input[name="password"]', self.password)
            
            # Submit form
            await self.page.click('button[type="submit"]')
            
            # Wait for navigation to complete
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            
            # Verify login success
            current_url = self.page.url
            if 'login' not in current_url.lower():
                logger.info("Login successful")
                return True
            else:
                logger.error("Login failed - still on login page")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    async def download_loan_tape(self, output_dir: Path) -> Optional[Path]:
        """Download loan tape export from Cascade.
        
        Args:
            output_dir: Directory to save downloaded file
            
        Returns:
            Path to downloaded file, or None if failed
        """
        try:
            # Navigate to analytics page with portfolio ID
            analytics_url = f"{CASCADE_ANALYTICS_URL}?pid={self.pid}"
            logger.info(f"Navigating to {analytics_url}")
            await self.page.goto(analytics_url)
            
            # Wait for page to load
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            
            # Look for Export button
            logger.info("Looking for Export button")
            export_button = await self.page.wait_for_selector(
                'button:has-text("Export"), a:has-text("Export")',
                timeout=10000
            )
            
            # Set up download handler
            async with self.page.expect_download() as download_info:
                await export_button.click()
                
                # Look for CSV option
                csv_button = await self.page.wait_for_selector(
                    'text="CSV", button:has-text("CSV")',
                    timeout=5000
                )
                await csv_button.click()
            
            # Get download
            download = await download_info.value
            
            # Generate filename with today's date
            today = datetime.now().strftime("%Y%m%d")
            filename = f"loan_tape_{today}.csv"
            output_path = output_dir / filename
            
            # Save download
            await download.save_as(output_path)
            logger.info(f"Downloaded loan tape to {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to download loan tape: {e}")
            return None
    
    async def download_financials(self, output_dir: Path) -> Optional[Path]:
        """Download financial statements from Cascade.
        
        Args:
            output_dir: Directory to save downloaded file
            
        Returns:
            Path to downloaded file, or None if failed
        """
        try:
            # Navigate to financials section
            financials_url = f"{CASCADE_BASE_URL}/analytics/financials?pid={self.pid}"
            logger.info(f"Navigating to {financials_url}")
            await self.page.goto(financials_url)
            
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            
            # Look for Export button
            export_button = await self.page.wait_for_selector(
                'button:has-text("Export")',
                timeout=10000
            )
            
            # Set up download handler
            async with self.page.expect_download() as download_info:
                await export_button.click()
                csv_button = await self.page.wait_for_selector(
                    'text="CSV"',
                    timeout=5000
                )
                await csv_button.click()
            
            # Get download
            download = await download_info.value
            
            # Generate filename
            today = datetime.now().strftime("%Y%m%d")
            filename = f"financials_{today}.csv"
            output_path = output_dir / filename
            
            # Save download
            await download.save_as(output_path)
            logger.info(f"Downloaded financials to {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to download financials: {e}")
            return None


async def main():
    """Main execution function."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Automate Cascade Debt data downloads"
    )
    parser.add_argument(
        "--loan-tape",
        action="store_true",
        help="Download loan tape export"
    )
    parser.add_argument(
        "--financials",
        action="store_true",
        help="Download financial statements"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all available data"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/cascade"),
        help="Output directory for downloads"
    )
    
    args = parser.parse_args()
    
    # Get credentials from environment
    username = os.getenv("CASCADE_USERNAME")
    password = os.getenv("CASCADE_PASSWORD")
    pid = os.getenv("CASCADE_PID", "abaco")
    
    if not username or not password:
        logger.error("CASCADE_USERNAME and CASCADE_PASSWORD must be set")
        return 1
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine what to download
    download_loan_tape = args.loan_tape or args.all
    download_financials = args.financials or args.all
    
    # If nothing specified, download loan tape by default
    if not (download_loan_tape or download_financials):
        download_loan_tape = True
    
    # Run scraper
    try:
        async with CascadeScraper(username, password, pid) as scraper:
            # Login
            if not await scraper.login():
                logger.error("Login failed, exiting")
                return 1
            
            # Download requested data
            if download_loan_tape:
                loan_tape_path = await scraper.download_loan_tape(args.output_dir)
                if not loan_tape_path:
                    logger.error("Loan tape download failed")
                    return 1
            
            if download_financials:
                financials_path = await scraper.download_financials(args.output_dir)
                if not financials_path:
                    logger.error("Financials download failed")
                    return 1
            
        logger.info("All downloads completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Scraper failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
