#!/usr/bin/env python3
"""
OptiSigns Scraper - Main Entry Point
Wraps the scraper with enhanced logging, error handling, and scheduling support.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from config import ScraperConfig, ScraperUtils
from scraper import OptiSignsScraper


class ScraperRunner:
    """Main runner class that wraps the scraper with enhanced functionality."""

    def __init__(self):
        # Setup logging system and track execution metrics
        self.setup_logging()
        self.start_time = time.time()
        # Initialize statistics tracking for scraping operations
        self.stats = {
            "added": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "total_processed": 0,
        }

    def setup_logging(self):
        """Setup logging configuration."""
        # Get log level from environment variable
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Configure logging format and handlers for both file and console output
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(
                    log_dir / f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                ),
                logging.StreamHandler(sys.stdout),
            ],
        )

        self.logger = logging.getLogger(__name__)

    def get_config(self) -> ScraperConfig:
        """Get scraper configuration from environment variables or defaults."""
        # Load all configuration parameters from environment variables
        # with fallback defaults for each setting
        return ScraperConfig(
            base_url=os.getenv("BASE_URL", "https://support.optisigns.com"),
            output_dir=os.getenv("OUTPUT_DIR", "scrape_output"),
            pages_to_crawl=int(os.getenv("PAGES_TO_CRAWL", "30")),
            headless=os.getenv("HEADLESS", "true").lower() == "true",
            article_sort_method=os.getenv("SORT_METHOD", "alphabetical"),
            enable_incremental_updates=os.getenv("INCREMENTAL_UPDATES", "true").lower()
            == "true",
            force_update_all=os.getenv("FORCE_UPDATE_ALL", "false").lower() == "true",
            timeout=int(os.getenv("TIMEOUT", "60000")),
        )

    def calculate_stats(self, scraper: OptiSignsScraper):
        """Calculate processing statistics."""
        # Get tracking data from the scraper
        tracker = scraper.article_tracker

        # Count new and updated articles
        self.stats["added"] = len(tracker.new_articles)
        self.stats["updated"] = len(tracker.updated_articles)

        # Calculate skipped articles (total found minus processed)
        total_articles = len(scraper.article_urls)
        processed = self.stats["added"] + self.stats["updated"]
        self.stats["skipped"] = max(
            0, min(scraper.config.pages_to_crawl, total_articles) - processed
        )
        self.stats["total_processed"] = processed

    def save_run_artifact(self, scraper: OptiSignsScraper, success: bool):
        """Save run artifact with detailed information."""
        # Create artifacts directory for storing execution reports
        artifact_dir = Path("artifacts")
        artifact_dir.mkdir(exist_ok=True)

        run_time = time.time() - self.start_time

        # Create comprehensive execution report
        artifact = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "duration_seconds": round(run_time, 2),
            "stats": self.stats,
            "config": {
                "base_url": scraper.config.base_url,
                "output_dir": str(scraper.config.output_dir),
                "pages_to_crawl": scraper.config.pages_to_crawl,
                "incremental_updates": scraper.config.enable_incremental_updates,
                "force_update_all": scraper.config.force_update_all,
            },
            "new_articles": list(scraper.article_tracker.new_articles),
            "updated_articles": list(scraper.article_tracker.updated_articles),
            "total_articles_found": len(scraper.article_urls),
            "environment": {"python_version": sys.version, "platform": sys.platform},
        }

        artifact_file = (
            artifact_dir / f'run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )

        try:
            # Save timestamped artifact file
            with open(artifact_file, "w", encoding="utf-8") as f:
                json.dump(artifact, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Run artifact saved: {artifact_file}")

            # Also save as latest.json for easy access to most recent run
            latest_file = artifact_dir / "latest.json"
            with open(latest_file, "w", encoding="utf-8") as f:
                json.dump(artifact, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Failed to save run artifact: {e}")

    def log_summary(self):
        """Log execution summary."""
        run_time = time.time() - self.start_time

        self.logger.info("=" * 60)
        self.logger.info("SCRAPING SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total execution time: {run_time:.2f} seconds")
        self.logger.info(f"Articles added: {self.stats['added']}")
        self.logger.info(f"Articles updated: {self.stats['updated']}")
        self.logger.info(f"Articles skipped: {self.stats['skipped']}")
        self.logger.info(f"Total processed: {self.stats['total_processed']}")
        self.logger.info(f"Errors: {self.stats['errors']}")
        self.logger.info("=" * 60)

    async def run(self):
        """Main execution method."""
        self.logger.info("Starting OptiSigns scraper...")

        try:
            # Load configuration from environment variables
            config = self.get_config()
            self.logger.info(
                f"Configuration loaded: {config.pages_to_crawl} pages, incremental: {config.enable_incremental_updates}"
            )

            # Initialize and run the core scraper
            scraper = OptiSignsScraper(config)
            await scraper.run()

            # Calculate processing statistics
            self.calculate_stats(scraper)

            # Save execution report for monitoring
            self.save_run_artifact(scraper, True)

            # Display summary information
            self.log_summary()

            self.logger.info("Scraping completed successfully!")
            return 0

        except Exception as e:
            # Handle any errors during execution
            self.stats["errors"] = 1
            self.logger.error(f"Scraping failed: {e}", exc_info=True)

            # Attempt to save error artifact for debugging
            try:
                if "scraper" in locals():
                    self.save_run_artifact(locals()["scraper"], False)
            except:
                pass

            return 1


def main():
    """Entry point for the application."""
    runner = ScraperRunner()
    exit_code = asyncio.run(runner.run())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
