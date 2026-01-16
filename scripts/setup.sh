#!/bin/bash

# Setup script for BigQuery AI Service
# This script helps initialize the project

set -e

echo "🚀 BigQuery AI Service - Setup Script"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ -f .env ]; then
    echo -e "${YELLOW}⚠ .env file already exists${NC}"
    read -p "Do you want to overwrite it? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping .env creation"
    else
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file${NC}"
    fi
else
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
fi

# Create credentials directory
if [ ! -d "credentials" ]; then
    mkdir -p credentials
    echo -e "${GREEN}✓ Created credentials directory${NC}"
else
    echo -e "${BLUE}✓ Credentials directory already exists${NC}"
fi

# Create logs directory
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo -e "${GREEN}✓ Created logs directory${NC}"
else
    echo -e "${BLUE}✓ Logs directory already exists${NC}"
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo -e "${BLUE}Creating Python virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${BLUE}✓ Virtual environment already exists${NC}"
fi

# Install dependencies
echo ""
echo -e "${BLUE}Installing Python dependencies...${NC}"
./venv/bin/pip install --upgrade pip > /dev/null 2>&1
./venv/bin/pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Instructions
echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "1. Add your Google Cloud service account JSON:"
echo -e "   ${BLUE}cp /path/to/your-service-account.json credentials/service-account.json${NC}"
echo ""
echo "2. Update .env file with your configuration:"
echo -e "   ${BLUE}nano .env${NC}"
echo ""
echo "   Required variables:"
echo "   - GCP_PROJECT_ID=your-project-id"
echo "   - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json"
echo ""
echo "3. Run the development server:"
echo -e "   ${BLUE}make dev${NC}"
echo "   or"
echo -e "   ${BLUE}./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload${NC}"
echo ""
echo "4. Access the API:"
echo -e "   - API:        ${BLUE}http://localhost:8000${NC}"
echo -e "   - Docs:       ${BLUE}http://localhost:8000/docs${NC}"
echo -e "   - Health:     ${BLUE}http://localhost:8000/health${NC}"
echo ""
echo "5. For Docker deployment:"
echo -e "   ${BLUE}make docker-run${NC}"
echo ""
echo "6. For Kubernetes deployment:"
echo -e "   ${BLUE}make k8s-apply${NC}"
echo ""
