import datetime
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import html2text


@dataclass
class ScraperConfig:
    """Configuration class for the web scraper with all necessary settings."""

    base_url: str = "https://support.optisigns.com"
    output_dir: str = "scrape_output"
    pages_to_crawl: int = 30  # Number of articles to convert to markdown
    headless: bool = True
    article_sort_method: str = (
        "alphabetical"  # "alphabetical", "reverse", or "discovery_order"
    )

    # Incremental update settings for processing only changed content
    enable_incremental_updates: bool = True  # Only process new/updated articles
    processed_articles_log: str = (
        "processed_articles.json"  # Log file to track processed articles
    )
    force_update_all: bool = False  # Force update all articles regardless of changes

    # Browser and request configuration
    http_headers: dict = None  # Optional HTTP headers for requests
    timeout: int = 60000  # Default timeout for page loading in milliseconds

    # Content filtering settings
    unwanted_selectors: list[str] = None  # Selectors to remove from article content

    def __post_init__(self):
        # Convert output directory to Path object and create if needed
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.processed_articles_log = self.output_dir / self.processed_articles_log

        # Validate and clean base URL
        self.base_url = self.base_url.rstrip("/")
        if not self.base_url.startswith("http"):
            raise ValueError("Base URL must start with 'http' or 'https'")

        # Set default HTTP headers if not provided
        if self.http_headers is None:
            self.http_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }

        # Set default unwanted selectors for content cleanup
        if self.unwanted_selectors is None:
            self.unwanted_selectors = [
                ".article-votes",
                ".article-meta",
                ".comments",
                ".share-buttons",
                "nav",
                "footer",
                "aside",
                ".related-articles",
                ".breadcrumbs",
            ]


class ScraperUtils:
    """Utility functions for the web scraper."""

    @staticmethod
    def format_datetime() -> str:
        """
        Format datetime to [YYYY-MM-DD HH:MM:SS] format.
        """
        return datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

    @staticmethod
    def slugify(text: str) -> str:
        """
        Cleans text for slug creation, replacing spaces/special chars with hyphens.
        """
        text = str(text).lower()
        text = re.sub(r"[^a-z0-9\s-]", "", text)
        text = re.sub(r"[\s_-]+", "-", text)
        text = re.sub(r"^-+|-+$", "", text)
        return text

    @staticmethod
    def get_content_hash(content: str) -> str:
        """
        Generate a hash of the content to detect changes.
        """
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    @staticmethod
    def is_article_url(url: str) -> bool:
        """
        Check if a URL is an article URL.
        Article URLs typically contain '/articles/' in their path.
        """
        return "/articles/" in url

    @staticmethod
    def create_html2text_converter() -> html2text.HTML2Text:
        """
        Create and configure html2text converter for better markdown conversion.
        """
        h = html2text.HTML2Text()
        h.body_width = 0  # Do not wrap lines
        h.ignore_links = False  # Keep links
        h.ignore_images = False  # Keep image links
        h.single_line_break = True  # Treat single newlines as spaces
        h.unicode_snob = True  # Handle Unicode characters gracefully
        h.bypass_tables = False  # Convert tables to markdown
        return h


class ArticleTracker:
    """Handles tracking of processed articles for incremental updates."""

    def __init__(self, config: ScraperConfig):
        self.config = config
        # Load previously processed articles from disk
        self.processed_articles = self.load_processed_articles()
        # Track new and updated articles during current run
        self.new_articles = set()
        self.updated_articles = set()

    def load_processed_articles(self) -> dict:
        """
        Load the log of previously processed articles.
        Returns a dictionary with URL as key and metadata as value.
        """
        if not self.config.processed_articles_log.exists():
            return {}

        try:
            with open(self.config.processed_articles_log, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print(
                f"{ScraperUtils.format_datetime()} Warning: Could not load processed articles log, starting fresh"
            )
            return {}

    def save_processed_articles(self):
        """
        Save the log of processed articles to disk.
        """
        try:
            with open(self.config.processed_articles_log, "w", encoding="utf-8") as f:
                json.dump(self.processed_articles, f, indent=2, ensure_ascii=False)
            print(
                f"{ScraperUtils.format_datetime()} Saved processed articles log: {len(self.processed_articles)} entries"
            )
        except Exception as e:
            print(
                f"{ScraperUtils.format_datetime()} Error saving processed articles log: {e}"
            )

    def should_process_article(
        self, article_url: str, content_hash: str = None
    ) -> tuple[bool, str]:
        """
        Determine if an article should be processed based on incremental update settings.

        Returns:
            tuple: (should_process: bool, reason: str)
        """
        # Force update all articles if configured
        if self.config.force_update_all:
            return True, "force_update_all enabled"

        # Process all articles if incremental updates are disabled
        if not self.config.enable_incremental_updates:
            return True, "incremental_updates disabled"

        # Process new articles that haven't been seen before
        if article_url not in self.processed_articles:
            return True, "new article"

        # Process articles with changed content (different hash)
        if (
            content_hash
            and self.processed_articles[article_url].get("content_hash") != content_hash
        ):
            return True, "content changed"

        # Skip articles that haven't changed
        return False, "already processed and unchanged"

    def track_article(
        self,
        article_url: str,
        filename: str,
        content_hash: str,
        file_path: str,
        update_reason: str,
    ):
        """
        Track an article in the processed articles log and update counters.
        """
        # Store article metadata in processed articles log
        self.processed_articles[article_url] = {
            "filename": filename,
            "content_hash": content_hash,
            "last_processed": ScraperUtils.format_datetime(),
            "file_path": file_path,
        }

        # Update tracking counters for reporting
        if article_url not in self.processed_articles or update_reason == "new article":
            self.new_articles.add(article_url)
        elif update_reason == "content changed":
            self.updated_articles.add(article_url)

    def print_summary(self, total_articles_to_process: int):
        """
        Print summary of incremental update statistics.
        """
        if self.config.enable_incremental_updates:
            print(f"{ScraperUtils.format_datetime()} Incremental Update Summary:")
            print(f"  - New articles: {len(self.new_articles)}")
            print(f"  - Updated articles: {len(self.updated_articles)}")
            print(
                f"  - Total articles skipped (unchanged): {total_articles_to_process - len(self.new_articles) - len(self.updated_articles)}"
            )
        else:
            print(
                f"{ScraperUtils.format_datetime()} Incremental updates are disabled. All articles were processed."
            )
