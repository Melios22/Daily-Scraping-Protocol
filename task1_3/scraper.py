import asyncio
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from config import ArticleTracker, ScraperConfig, ScraperUtils
from playwright.async_api import async_playwright


class OptiSignsScraper:
    def __init__(self, config: ScraperConfig):
        """
        Initializes the OptiSignsScraper.

        Args:
            config (ScraperConfig): The configuration object for the scraper.
        """
        self.config = config
        # Initialize article tracking for incremental updates
        self.article_tracker = ArticleTracker(config)

        # Create HTML to markdown converter with custom settings
        self.h2t = ScraperUtils.create_html2text_converter()

        # Ensure the output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        # Store discovered article URLs
        self.article_urls = set()

        # Display initialization information
        print(f"{ScraperUtils.format_datetime()} Scraper initialized with settings:")
        print(f"  Base URL: {self.config.base_url}")
        print(f"  Output Directory: {self.config.output_dir}")
        print(f"  Articles to Process: {self.config.pages_to_crawl}")
        print(f"  Article Sort Method: {self.config.article_sort_method}")
        print(f"  Incremental Updates: {self.config.enable_incremental_updates}")
        print(f"  Force Update All: {self.config.force_update_all}")
        print(f"  Headless Mode: {self.config.headless}")
        print(
            f"  Previously processed articles: {len(self.article_tracker.processed_articles)}\n"
        )

    async def _fetch_page_content(self, page, url: str) -> str | None:
        """
        Navigates to a URL and returns its HTML content.
        Handles common HTTP headers for better scraping behavior.
        """
        try:
            # Set browser headers to appear more like a real browser
            await page.set_extra_http_headers(self.config.http_headers)
            await page.goto(
                url, wait_until="domcontentloaded", timeout=self.config.timeout
            )

            # Wait for dynamic content to load completely
            await page.wait_for_timeout(1500)

            return await page.content()
        except Exception as e:
            print(f"{ScraperUtils.format_datetime()} Error fetching {url}: {e}")
            return None

    async def _crawl_for_article_urls(self, page):
        """
        Extract all article URLs from the left sidebar navigation.

        How it works:
        1. Visit the main support page
        2. Extract all article links from the left sidebar
        3. No need to crawl multiple pages - all links are in the sidebar
        """
        print(
            f"{ScraperUtils.format_datetime()} Starting to collect article URLs from sidebar..."
        )

        # Navigate to the main support articles page
        main_url = self.config.base_url + "/hc/en-us/articles"
        print(f"{ScraperUtils.format_datetime()} Visiting main page: {main_url}")

        # Fetch the page content
        html_content = await self._fetch_page_content(page, main_url)
        if not html_content:
            print(
                f"{ScraperUtils.format_datetime()} Error: Could not fetch main page content"
            )
            return

        # Parse HTML and extract article links from sidebar
        soup = BeautifulSoup(html_content, "html.parser")
        self._extract_sidebar_links(soup)

        print(
            f"{ScraperUtils.format_datetime()} Finished collecting URLs. Found {len(self.article_urls)} article URLs from sidebar."
        )

    def _extract_sidebar_links(self, soup: BeautifulSoup):
        """
        Extract article URLs from the left sidebar navigation.

        Args:
            soup: BeautifulSoup object of the main page
        """
        # Try multiple sidebar selectors to find the navigation menu
        sidebar_selectors = [
            ".knowledge-tree",  # Primary selector based on your finding
            "nav.sidebar",
            ".sidebar",
            ".navigation-sidebar",
            ".side-nav",
            ".article-list",
            '[class*="sidebar"]',
            '[class*="navigation"]',
        ]

        sidebar_found = False

        # Try each selector until we find the sidebar
        for selector in sidebar_selectors:
            sidebar = soup.select_one(selector)
            if sidebar:
                print(
                    f"{ScraperUtils.format_datetime()} Found sidebar using selector: {selector}"
                )
                sidebar_found = True

                # Extract all article links from the sidebar
                for link in sidebar.find_all("a", href=True):
                    href = link["href"]
                    # full_url = urljoin(self.config.base_url, href)
                    full_url = href

                    # Filter to only include articles from our target domain
                    if not full_url.startswith(self.config.base_url):
                        continue

                    # Check if this is a valid article URL
                    if ScraperUtils.is_article_url(full_url):
                        if full_url not in self.article_urls:
                            self.article_urls.add(full_url)

                print(
                    f"{ScraperUtils.format_datetime()} Found {len(self.article_urls)} articles in sidebar"
                )
                break

        # Fallback strategy if sidebar not found with common selectors
        if not sidebar_found:
            print(
                f"{ScraperUtils.format_datetime()} Warning: Could not find sidebar with common selectors. Trying to find all article links on page..."
            )
            # Search entire page for article links as backup
            for link in soup.find_all("a", href=True):
                href = link["href"]
                full_url = urljoin(self.config.base_url, href)

                # Only process links within our target domain
                if not full_url.startswith(self.config.base_url):
                    continue

                # Check if this is an article URL
                if ScraperUtils.is_article_url(full_url):
                    if full_url not in self.article_urls:
                        self.article_urls.add(full_url)
                        if len(self.article_urls) % 10 == 0:
                            print(
                                f"{ScraperUtils.format_datetime()} Found {len(self.article_urls)} article URLs so far."
                            )

    async def _process_and_save_article(
        self, page, article_url: str, article_index: int
    ):
        """
        Fetches an individual article, cleans its HTML, converts to markdown, and saves it.
        Includes incremental update functionality to skip unchanged articles.
        """
        print(
            f"\n{ScraperUtils.format_datetime()} Processing article {article_index+1}: {article_url}"
        )
        # Fetch the article's HTML content
        html_content = await self._fetch_page_content(page, article_url)

        if not html_content:
            return False

        # Create content hash for change detection in incremental updates
        content_hash = ScraperUtils.get_content_hash(html_content)

        # Check if we should process this article based on incremental update settings
        should_process, reason = self.article_tracker.should_process_article(
            article_url, content_hash
        )
        if not should_process:
            print(
                f"{ScraperUtils.format_datetime()} Skipping article {article_index+1}: {reason}"
            )
            return True  # Return True as it's not an error, just skipped

        # Parse HTML content
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract the main article content using various selectors
        article_content_div = self._find_article_content(soup, article_url)
        if not article_content_div:
            return False

        # Convert HTML content to clean markdown format
        markdown_content = self._convert_to_markdown(article_content_div)

        # Save the processed article to file and update tracking
        return self._save_article_to_file(
            soup, article_url, article_index, markdown_content, content_hash, reason
        )

    def _find_article_content(self, soup: BeautifulSoup, article_url: str):
        """
        Find the main article content from the HTML soup.
        Uses body content directly for simplicity.
        """
        if soup.body:
            return soup.body

        print(
            f"{ScraperUtils.format_datetime()} Error: No body content found for {article_url}, skipping."
        )
        return None

    def _convert_to_markdown(self, content_element) -> str:
        """
        Convert HTML content to clean markdown format.
        """
        # Remove unwanted elements
        for selector in self.config.unwanted_selectors:
            for unwanted in content_element.select(selector):
                unwanted.decompose()

        return self.h2t.handle(str(content_element))

    def _save_article_to_file(
        self,
        soup: BeautifulSoup,
        article_url: str,
        article_index: int,
        markdown_content: str,
        content_hash: str,
        update_reason: str,
    ) -> bool:
        """
        Save the article content to a markdown file and update tracking.
        """
        # Extract and clean the article title for filename
        title = self._extract_title(soup, article_url)
        slug = ScraperUtils.slugify(title)

        # Create fallback filename if title processing fails
        if not slug:
            slug = f"article-{article_index}-{hash(article_url) % 10000}"

        file_name = f"{slug}.md"
        file_path = self.config.output_dir / file_name

        # Create markdown file with metadata header
        header = f"---\nurl: {article_url}\ndate_scraped: {ScraperUtils.format_datetime()}\n---\n\n"
        final_content = header + markdown_content

        # Write the markdown file to disk
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        # Update article tracking for incremental updates
        self.article_tracker.track_article(
            article_url, file_name, content_hash, str(file_path), update_reason
        )

        action = "Updated" if update_reason == "content changed" else "Saved"
        print(f"{ScraperUtils.format_datetime()} {action}: {file_path}")
        return True

    def _extract_title(self, soup: BeautifulSoup, article_url: str) -> str:
        """
        Extract the article title from HTML, with fallbacks.
        """
        title_tag = soup.find("title")
        if title_tag:
            # Clean " - OptiSigns" from the title
            return title_tag.get_text().replace(" - OptiSigns", "").strip()
        else:
            # Fallback to URL path if no title tag is found
            return article_url.split("/")[-1]

    async def run(self):
        """
        Executes the main scraping process: extracting URLs from sidebar and then processing articles.
        """
        async with async_playwright() as p:
            # Launch browser with headless/visible mode based on config
            browser = await p.chromium.launch(headless=self.config.headless)
            page = await browser.new_page()

            # Step 1: Extract all article URLs from the sidebar navigation
            await self._crawl_for_article_urls(page)

            # Step 2: Sort articles for reproducibility and select which ones to process
            articles_processed = 0

            # Convert URL set to list and sort based on configured method
            article_list = list(self.article_urls)

            if self.config.article_sort_method == "alphabetical":
                article_list = sorted(article_list)
                sort_desc = "sorted alphabetically"
            elif self.config.article_sort_method == "reverse":
                article_list = sorted(article_list, reverse=True)
                sort_desc = "sorted reverse alphabetically"
            else:  # discovery_order
                sort_desc = "in discovery order"

            # Limit the number of articles to process based on configuration
            articles_to_process = article_list[: self.config.pages_to_crawl]

            print(f"-" * 50)
            print(
                f"\n{ScraperUtils.format_datetime()} Found {len(article_list)} total articles, {sort_desc}."
            )
            print(
                f"{ScraperUtils.format_datetime()} Processing first {len(articles_to_process)} articles for reproducibility..."
            )

            # Process each selected article
            for i, article_url in enumerate(articles_to_process):
                success = await self._process_and_save_article(page, article_url, i)
                if success:
                    articles_processed += 1

                # Small delay between articles to be respectful to the server
                await asyncio.sleep(2)

            await browser.close()

            # Save the processed articles log for future incremental updates
            self.article_tracker.save_processed_articles()

            # Display completion summary with incremental update information
            print(
                f"\n{ScraperUtils.format_datetime()} Task complete! Successfully processed {articles_processed} out of {len(articles_to_process)} articles and saved them to '{self.config.output_dir}'."
            )

            # Print incremental update summary statistics
            self.article_tracker.print_summary(len(articles_to_process))


# Example usage
if __name__ == "__main__":
    # Create a configuration for the scraper
    config = ScraperConfig(
        base_url="https://support.optisigns.com",
        article_sort_method="alphabetical",  # Sort articles alphabetically
        output_dir="pages_output",  # Directory to save markdown files
        pages_to_crawl=1,  # Number of articles to convert to markdown
        headless=True,  # Set to False to see the browser (for debugging)
        enable_incremental_updates=True,  # Enable daily updates
        force_update_all=False,  # Do not force update all articles
    )

    # Create and run the scraper
    scraper = OptiSignsScraper(config)

    asyncio.run(scraper.run())
