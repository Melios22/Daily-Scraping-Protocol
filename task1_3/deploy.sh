#!/bin/bash

# OptiSigns Scraper - DigitalOcean Deployment Script
# This script automates the deployment of the scraper to DigitalOcean App Platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="optisigns-scraper"
SPEC_FILE=".do/app.yaml"
GITHUB_REPO="Melios22/Daily-Scraping-Protocol"

echo -e "${BLUE}🚀 OptiSigns Scraper - DigitalOcean Deployment${NC}"
echo "=============================================="

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo -e "${RED}❌ Error: doctl CLI is not installed${NC}"
    echo -e "${YELLOW}💡 Install it from: https://docs.digitalocean.com/reference/doctl/how-to/install/${NC}"
    exit 1
fi

# Check if user is authenticated
if ! doctl auth list &> /dev/null; then
    echo -e "${RED}❌ Error: Not authenticated with DigitalOcean${NC}"
    echo -e "${YELLOW}💡 Run: doctl auth init${NC}"
    exit 1
fi

echo -e "${GREEN}✅ doctl CLI found and authenticated${NC}"

# Check if spec file exists
if [ ! -f "$SPEC_FILE" ]; then
    echo -e "${RED}❌ Error: App specification file not found: $SPEC_FILE${NC}"
    echo -e "${YELLOW}💡 Make sure you're running this from the task1_3 directory${NC}"
    exit 1
fi

echo -e "${GREEN}✅ App specification file found${NC}"

# Verify GitHub repository in spec file
if grep -q "your-username/optisigns-scraper" "$SPEC_FILE"; then
    echo -e "${RED}❌ Error: GitHub repository not updated in $SPEC_FILE${NC}"
    echo -e "${YELLOW}💡 Please update the repo URL from 'your-username/optisigns-scraper' to '$GITHUB_REPO'${NC}"
    exit 1
fi

echo -e "${GREEN}✅ GitHub repository configuration verified${NC}"

# Check if app already exists
echo -e "${BLUE}🔍 Checking if app already exists...${NC}"
EXISTING_APP=$(doctl apps list --format ID,Name --no-header | grep "$APP_NAME" | awk '{print $1}' || true)

if [ -n "$EXISTING_APP" ]; then
    echo -e "${YELLOW}⚠️  App '$APP_NAME' already exists (ID: $EXISTING_APP)${NC}"
    echo -e "${BLUE}🔄 Updating existing app...${NC}"
    
    # Update existing app
    doctl apps update "$EXISTING_APP" --spec "$SPEC_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ App updated successfully!${NC}"
        APP_ID="$EXISTING_APP"
    else
        echo -e "${RED}❌ Failed to update app${NC}"
        exit 1
    fi
else
    echo -e "${BLUE}🆕 Creating new app...${NC}"
    
    # Create new app
    CREATE_OUTPUT=$(doctl apps create "$SPEC_FILE" --format ID --no-header)
    
    if [ $? -eq 0 ]; then
        APP_ID="$CREATE_OUTPUT"
        echo -e "${GREEN}✅ App created successfully! (ID: $APP_ID)${NC}"
    else
        echo -e "${RED}❌ Failed to create app${NC}"
        exit 1
    fi
fi

# Wait a moment for the app to initialize
echo -e "${BLUE}⏳ Waiting for app to initialize...${NC}"
sleep 5

# Show app details
echo -e "${BLUE}📋 App Details:${NC}"
doctl apps get "$APP_ID" --format Name,Status,CreatedAt,UpdatedAt

# Show deployment status
echo -e "${BLUE}🔄 Checking deployment status...${NC}"
DEPLOYMENT_STATUS=$(doctl apps get "$APP_ID" --format Status --no-header)
echo -e "${BLUE}Status: $DEPLOYMENT_STATUS${NC}"

# Provide useful links and next steps
echo ""
echo -e "${GREEN}🎉 Deployment initiated successfully!${NC}"
echo "=============================================="
echo -e "${BLUE}📊 Monitoring Links:${NC}"
echo "• DigitalOcean Console: https://cloud.digitalocean.com/apps/"
echo "• App ID: $APP_ID"
echo "• App Name: $APP_NAME"
echo ""
echo -e "${BLUE}📋 Useful Commands:${NC}"
echo "• Check status: doctl apps get $APP_ID"
echo "• View logs: doctl apps logs $APP_ID --type job"
echo "• Follow logs: doctl apps logs $APP_ID --type job --follow"
echo "• Update app: doctl apps update $APP_ID --spec $SPEC_FILE"
echo ""
echo -e "${BLUE}⏰ Schedule Information:${NC}"
echo "• The scraper job is scheduled to run daily at 2 AM UTC"
echo "• First run will occur at the next scheduled time"
echo "• You can monitor execution in the DigitalOcean console"
echo ""
echo -e "${BLUE}🔧 Configuration:${NC}"
echo "• Source Directory: /task1_3"
echo "• GitHub Repository: $GITHUB_REPO"
echo "• Instance Size: basic-xxs (cost optimized)"
echo "• Max Articles: 50 per run (configured in app.yaml)"
echo ""
echo -e "${YELLOW}💡 Next Steps:${NC}"
echo "1. Monitor the first deployment in DigitalOcean console"
echo "2. Check job logs after the first scheduled run"
echo "3. Verify artifacts and output are generated correctly"
echo "4. Update monitoring links in your README with the actual app URL"
echo ""
echo -e "${GREEN}🚀 Deployment complete! Your scraper is now scheduled to run daily.${NC}"
