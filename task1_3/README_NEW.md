# OptiSigns Knowledge Base Scraper

An intelligent web scraper that automatically extracts and converts OptiSigns support articles to markdown format. Features incremental updates, comprehensive logging, and production-ready deployment capabilities.

## 🎯 Purpose

This scraper automates the collection of OptiSigns customer support documentation by:
- **Discovering** all articles from the support site sidebar navigation
- **Extracting** clean content and converting to markdown format
- **Tracking** changes to process only new or updated articles
- **Organizing** output with consistent naming and metadata
- **Monitoring** execution with detailed logs and artifacts

## 🚀 Key Features

- **🔄 Incremental Updates**: Smart change detection using content hashing
- **📊 Detailed Analytics**: Comprehensive tracking of added, updated, and skipped articles
- **🐳 Production Ready**: Fully containerized with Docker and DigitalOcean deployment
- **⏰ Scheduled Execution**: Daily automated runs with monitoring
- **📈 Execution Artifacts**: JSON reports for each run with detailed metrics
- **🎯 Delta Processing**: Only processes new or changed content for efficiency

## 🏗️ Architecture

```
main.py              # Entry point with logging, stats, and error handling
├── scraper.py       # Core scraping logic with browser automation
├── config.py        # Configuration classes and utility functions
├── Dockerfile       # Container definition for deployment
├── docker-compose.yml # Local development environment
├── .do/app.yaml     # DigitalOcean App Platform specification
└── deploy.sh        # Automated deployment script
```

## 📁 Output Structure

```
scrape_output/              # Scraped articles in markdown format
├── article-title-1.md     # Individual articles with metadata headers
├── article-title-2.md
└── processed_articles.json # Tracking log for incremental updates

logs/                       # Application execution logs
├── scraper_20250123_140530.log
└── scraper_20250123_150630.log

artifacts/                  # Execution reports and monitoring data
├── latest.json            # Most recent run details
├── run_20250123_140530.json
└── run_20250123_150630.json
```

## 🛠️ Local Development

### Prerequisites
- Python 3.8+
- Docker (optional)

### Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Run the scraper:**
   ```bash
   python main.py
   ```

3. **Check results:**
   - Markdown files in `scrape_output/`
   - Logs in `logs/`
   - Run artifact in `artifacts/latest.json`

### Docker Development

```bash
# Build and run locally
docker-compose up --build

# Or with Docker directly
docker build -t optisigns-scraper .
docker run -v $(pwd)/output:/app/scrape_output optisigns-scraper
```

## ⚙️ Configuration

Configure via environment variables or defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `https://support.optisigns.com` | Target website URL |
| `OUTPUT_DIR` | `scrape_output` | Output directory for markdown files |
| `PAGES_TO_CRAWL` | `30` | Maximum articles to process per run |
| `HEADLESS` | `true` | Run browser in headless mode |
| `SORT_METHOD` | `alphabetical` | Article sorting: alphabetical, reverse, discovery_order |
| `INCREMENTAL_UPDATES` | `true` | Enable delta processing |
| `FORCE_UPDATE_ALL` | `false` | Force update all articles |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## 🎯 How It Works

### 1. Article Discovery
- Navigates to the main support page
- Extracts all article links from sidebar navigation
- Filters to ensure only article URLs are collected

### 2. Incremental Processing
- Loads previous run tracking data
- Generates content hash for each article
- Skips unchanged articles to optimize performance

### 3. Content Extraction
- Fetches article HTML using Playwright browser automation
- Cleans content by removing navigation, ads, and metadata
- Converts to clean markdown format

### 4. Intelligent Tracking
- Maintains JSON log of processed articles with hashes
- Tracks new articles, updated content, and skipped items
- Provides detailed statistics for each run

## 📊 Sample Execution Report

```json
{
  "timestamp": "2025-01-23T14:30:00.123456",
  "success": true,
  "duration_seconds": 45.67,
  "stats": {
    "added": 3,
    "updated": 2,
    "skipped": 25,
    "total_processed": 5
  },
  "config": {
    "pages_to_crawl": 30,
    "incremental_updates": true
  },
  "new_articles": ["https://support.optisigns.com/hc/en-us/articles/123"],
  "updated_articles": ["https://support.optisigns.com/hc/en-us/articles/456"]
}
```

## 🚀 Production Deployment

The scraper is designed for DigitalOcean App Platform with daily scheduling:

### Automated Deployment
```bash
chmod +x deploy.sh
./deploy.sh
```

### Manual Deployment
1. Update GitHub repository URL in `.do/app.yaml`
2. Deploy: `doctl apps create .do/app.yaml`
3. Monitor: DigitalOcean App Platform console

### Scheduled Execution
- **Frequency**: Daily at 2 AM UTC
- **Duration**: ~1-2 minutes for incremental updates
- **Cost**: ~$5-10/month on basic-xxs instance
- **Monitoring**: Available via DigitalOcean console and artifacts

## 📈 Monitoring & Logs

- **Application Logs**: Available in DigitalOcean App Platform console
- **Execution Artifacts**: JSON reports saved to `/artifacts/` with detailed metrics
- **Health Monitoring**: Success/failure status in run artifacts
- **Performance Tracking**: Duration, article counts, and error rates

## 🔧 Troubleshooting

### Common Issues
1. **No articles found**: Check website structure changes
2. **Browser timeout**: Increase `TIMEOUT` environment variable
3. **Permission errors**: Verify file system permissions in container
4. **Deployment fails**: Confirm GitHub repository URL in `.do/app.yaml`

### Debug Mode
Run with visible browser for debugging:
```bash
HEADLESS=false python main.py
```

## 🔗 Links

- **Daily Job Logs**: [See main README for DigitalOcean links](#)
- **Source Code**: Update GitHub URL in `.do/app.yaml`
- **Monitoring Dashboard**: DigitalOcean App Platform console
