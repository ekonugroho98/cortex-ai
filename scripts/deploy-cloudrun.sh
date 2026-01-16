#!/bin/bash

# CortexAI Cloud Run Deployment Script
# This script automates deployment to Google Cloud Run

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${PROJECT_ID:-gen-lang-client-0716506049}"
REGION="${REGION:-asia-southeast1}"
SERVICE_NAME="${SERVICE_NAME:-cortex-ai}"
IMAGE_NAME="${IMAGE_NAME:-cortex-ai}"
REPO_NAME="${REPO_NAME:-cortex-ai}"

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}  CortexAI Cloud Run Deployment${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
echo -e "${YELLOW}Checking authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with gcloud${NC}"
    echo "Please run: gcloud auth login"
    exit 1
fi

# Set project
echo -e "${YELLOW}Setting project to: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable \
    bigquery.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com

echo -e "${GREEN}✓ APIs enabled${NC}"
echo ""

# Create Artifact Registry if it doesn't exist
echo -e "${YELLOW}Checking Artifact Registry...${NC}"
if ! gcloud artifacts repositories describe ${REPO_NAME} --location=${REGION} &> /dev/null; then
    echo -e "${YELLOW}Creating Artifact Registry: ${REPO_NAME}${NC}"
    gcloud artifacts repositories create ${REPO_NAME} \
        --repository-format=docker \
        --location=${REGION} \
        --description="CortexAI Docker images"
    echo -e "${GREEN}✓ Artifact Registry created${NC}"
else
    echo -e "${GREEN}✓ Artifact Registry already exists${NC}"
fi
echo ""

# Create secrets if they don't exist
echo -e "${YELLOW}Checking secrets...${NC}"

# Check for ANTHROPIC_API_KEY
if ! gcloud secrets describe cortex-ai-anthropic-key &> /dev/null; then
    echo -e "${RED}Warning: Secret 'cortex-ai-anthropic-key' not found${NC}"
    echo "Please create it with:"
    echo "  echo -n 'your-api-key' | gcloud secrets versions add cortex-ai-anthropic-key --data-file=-"
    read -p "Do you want to create it now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your Anthropic API key: " API_KEY
        echo -n "${API_KEY}" | gcloud secrets create cortex-ai-anthropic-key --data-file=-
        echo -e "${GREEN}✓ Secret created${NC}"
    fi
else
    echo -e "${GREEN}✓ Secret 'cortex-ai-anthropic-key' exists${NC}"
fi

# Check for GOOGLE_APPLICATION_CREDENTIALS
if ! gcloud secrets describe cortex-ai-sa-key &> /dev/null; then
    echo -e "${YELLOW}Secret 'cortex-ai-sa-key' not found${NC}"
    if [ -f "credentials/service-account.json" ]; then
        read -p "Do you want to upload service-account.json to Secret Manager? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            gcloud secrets create cortex-ai-sa-key --data-file=credentials/service-account.json
            echo -e "${GREEN}✓ Secret created${NC}"
        fi
    else
        echo "Please create it with:"
        echo "  gcloud secrets create cortex-ai-sa-key --data-file=credentials/service-account.json"
    fi
else
    echo -e "${GREEN}✓ Secret 'cortex-ai-sa-key' exists${NC}"
fi
echo ""

# Build and push Docker image
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${BUILD_ID:-latest}"
echo -e "${YELLOW}Building Docker image: ${IMAGE_URI}${NC}"

gcloud builds submit \
    --tag "${IMAGE_URI}" \
    --timeout="20m"

echo -e "${GREEN}✓ Docker image built and pushed${NC}"
echo ""

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image="${IMAGE_URI}" \
    --region=${REGION} \
    --platform=managed \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --max-instances=100 \
    --timeout=300s \
    --concurrency=10 \
    --set-env-vars=FASTAPI_ENV=production,GCP_PROJECT_ID=${PROJECT_ID},BIGQUERY_LOCATION=US,API_V1_PREFIX=/api/v1,LOG_LEVEL=INFO \
    --set-secrets=ANTHROPIC_API_KEY=cortex-ai-anthropic-key:latest,GOOGLE_APPLICATION_CREDENTIALS=cortex-ai-sa-key:latest

echo -e "${GREEN}✓ Deployment successful${NC}"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region=${REGION} \
    --format="value(status.url)")

echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""
echo -e "Service URL: ${GREEN}${SERVICE_URL}${NC}"
echo ""
echo -e "Test the deployment:"
echo -e "  curl ${SERVICE_URL}/health"
echo ""
echo -e "View logs:"
echo -e "  gcloud run logs tail ${SERVICE_NAME} --region=${REGION}"
echo ""
echo -e "View service details:"
echo -e "  gcloud run services describe ${SERVICE_NAME} --region=${REGION}"
echo ""
