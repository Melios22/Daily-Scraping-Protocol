# OptiSigns Scraper

A containerized web scraper for OptiSigns support articles with scheduling capabilities for DigitalOcean Platform.

## Features

- 🔄 **Incremental Updates**: Detects new/updated articles using content hashing
- 📊 **Detailed Logging**: Comprehensive logging with statistics (added, updated, skipped)
- 🐳 **Dockerized**: Fully containerized for easy deployment
- ⏰ **Scheduled Execution**: Runs once per day on DigitalOcean
- 📈 **Run Artifacts**: Saves detailed execution reports
- 🎯 **Delta Processing**: Only processes new or changed content

## Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Run the scraper:**
   ```bash
   python main.py
   ```

### Docker

1. **Build and run with Docker:**
   ```bash
   docker build -t optisigns-scraper .
   docker run -v $(pwd)/output:/app/optisigns_articles_markdown optisigns-scraper
   ```

2. **Or use Docker Compose:**
   ```bash
   docker-compose up --build
   ```

## DigitalOcean Deployment

### Prerequisites

1. Install [doctl CLI](https://docs.digitalocean.com/reference/doctl/how-to/install/)
2. Authenticate: `doctl auth init`
3. Push code to GitHub repository

### Deploy

1. **Update the GitHub repository URL in `.do/app.yaml`:**
   ```yaml
   github:
     repo: your-username/optisigns-scraper
     branch: main
   ```

2. **Deploy using the script:**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Or deploy manually:**
   ```bash
   doctl apps create .do/app.yaml
   ```

### Monitoring

- **App Dashboard**: https://cloud.digitalocean.com/apps/
- **Job Logs**: Available in the DigitalOcean console under your app
- **Run Artifacts**: Check the `/artifacts/latest.json` endpoint

## Configuration

Environment variables can be set in `.do/app.yaml` or locally:

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `https://support.optisigns.com` | Target website URL |
| `OUTPUT_DIR` | `scrape_output` | Output directory for markdown files |
| `PAGES_TO_CRAWL` | `50` | Maximum number of articles to process |
| `HEADLESS` | `true` | Run browser in headless mode |
| `SORT_METHOD` | `alphabetical` | Article sorting method |
| `INCREMENTAL_UPDATES` | `true` | Enable delta processing |
| `FORCE_UPDATE_ALL` | `false` | Force update all articles |
| `LOG_LEVEL` | `INFO` | Logging level |

## Architecture

```
main.py              # Entry point with logging and stats
├── scraper.py       # Core scraping logic
├── config.py        # Configuration and utilities
├── Dockerfile       # Container definition
├── .do/app.yaml     # DigitalOcean app specification
└── artifacts/       # Execution reports and logs
    └── latest.json  # Most recent run details
```

## Output Structure

```
optisigns_articles_markdown/    # Scraped articles in markdown
logs/                          # Application logs
artifacts/                     # Run reports
├── latest.json               # Latest run details
└── run_YYYYMMDD_HHMMSS.json # Historical runs
```

## Sample Run Artifact

```json
{
  "timestamp": "2025-01-22T10:30:00.123456",
  "success": true,
  "duration_seconds": 45.67,
  "stats": {
    "added": 3,
    "updated": 2,
    "skipped": 45,
    "total_processed": 5
  },
  "new_articles": ["url1", "url2", "url3"],
  "updated_articles": ["url4", "url5"]
}
```

## Scheduled Execution

The DigitalOcean job runs daily at 2 AM UTC and:

1. ✅ **Re-scrapes** all available articles
2. ✅ **Detects changes** using content hashing and Last-Modified headers
3. ✅ **Processes only delta** (new/updated articles)
4. ✅ **Logs counts** of added, updated, and skipped articles
5. ✅ **Saves artifacts** with detailed execution reports

## Cost Optimization

- Uses smallest DigitalOcean instance (`basic-xxs`)
- Runs only once per day
- Efficient incremental processing
- Estimated cost: ~$5-10/month

## Links

- **Job Logs**: Available in DigitalOcean App Platform console
- **Run Artifacts**: Access via app URL `/artifacts/latest.json`
- **GitHub Repository**: Update in `.do/app.yaml`

## Troubleshooting

1. **Deployment fails**: Check GitHub repository URL in `.do/app.yaml`
2. **Job doesn't run**: Verify cron schedule format in app specification
3. **Browser issues**: Ensure all Playwright dependencies are installed
4. **Permission errors**: Check file permissions and user setup in Docker

## Support

For issues or questions:
1. Check the logs in DigitalOcean console
2. Review the run artifacts for detailed execution info
3. Verify environment variables configuration
