#!/bin/bash

# CortexAI GKE Deployment Script
# This script automates deployment to Google Kubernetes Engine

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${PROJECT_ID:-gen-lang-client-0716506049}"
CLUSTER_NAME="${CLUSTER_NAME:-cortex-ai-cluster}"
REGION="${REGION:-asia-southeast1}"
NAMESPACE="${NAMESPACE:-cortex-ai}"

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}  CortexAI GKE Deployment${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    echo "Install with: gcloud components install kubectl"
    exit 1
fi

# Set project
echo -e "${YELLOW}Setting project to: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable \
    container.googleapis.com \
    bigquery.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com

echo -e "${GREEN}✓ APIs enabled${NC}"
echo ""

# Check if cluster exists
echo -e "${YELLOW}Checking GKE cluster...${NC}"
if ! gcloud container clusters describe ${CLUSTER_NAME} --region=${REGION} &> /dev/null; then
    echo -e "${YELLOW}Creating GKE cluster: ${CLUSTER_NAME}${NC}"
    gcloud container clusters create ${CLUSTER_NAME} \
        --region=${REGION} \
        --num-nodes=2 \
        --machine-type=e2-medium \
        --disk-type=pd-standard \
        --disk-size=100GB \
        --enable-autoscaling \
        --min-nodes=1 \
        --max-nodes=5 \
        --enable-autorepair \
        --enable-autoupgrade \
        --scopes=cloud-platform

    echo -e "${GREEN}✓ Cluster created${NC}"
else
    echo -e "${GREEN}✓ Cluster already exists${NC}"
fi
echo ""

# Get cluster credentials
echo -e "${YELLOW}Getting cluster credentials...${NC}"
gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}
echo -e "${GREEN}✓ Credentials configured${NC}"
echo ""

# Create namespace
echo -e "${YELLOW}Creating namespace: ${NAMESPACE}${NC}"
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓ Namespace ready${NC}"
echo ""

# Create Docker registry secret
echo -e "${YELLOW}Configuring Docker registry secret...${NC}"
if ! kubectl get secret docker-registry-secret -n ${NAMESPACE} &> /dev/null; then
    echo -e "${YELLOW}Please provide your Artifact Registry credentials${NC}"
    read -p "Enter your GCP JSON key file path: " KEY_FILE
    cat ${KEY_FILE} | docker login -u _json_key_base64 --password-stdin https://${REGION}-docker.pkg.dev
    kubectl create secret docker-registry docker-registry-secret \
        --docker-server=https://${REGION}-docker.pkg.dev \
        --docker-username=_json_key_base64 \
        --docker-password="$(cat ${KEY_FILE} | base64)" \
        -n ${NAMESPACE}
    echo -e "${GREEN}✓ Docker registry secret created${NC}"
else
    echo -e "${GREEN}✓ Docker registry secret exists${NC}"
fi
echo ""

# Create secrets from Secret Manager
echo -e "${YELLOW}Creating Kubernetes secrets from Secret Manager...${NC}"

# ANTHROPIC_API_KEY
if kubectl get secret cortex-ai-secrets -n ${NAMESPACE} &> /dev/null; then
    kubectl delete secret cortex-ai-secrets -n ${NAMESPACE}
fi

kubectl create secret generic cortex-ai-secrets \
    --from-literal=ANTHROPIC_API_KEY="$(gcloud secrets versions access latest --secret=cortex-ai-anthropic-key)" \
    --from-literal=GOOGLE_APPLICATION_CREDENTIALS="$(gcloud secrets versions access latest --secret=cortex-ai-sa-key)" \
    -n ${NAMESPACE}

echo -e "${GREEN}✓ Secrets created${NC}"
echo ""

# Build and push Docker image
REPO_NAME="${REPO_NAME:-cortex-ai}"
IMAGE_NAME="${IMAGE_NAME:-cortex-ai}"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${BUILD_ID:-latest}"

echo -e "${YELLOW}Building Docker image: ${IMAGE_URI}${NC}"
gcloud builds submit \
    --tag "${IMAGE_URI}" \
    --timeout="20m"

echo -e "${GREEN}✓ Docker image built and pushed${NC}"
echo ""

# Update deployment with new image
echo -e "${YELLOW}Deploying to GKE...${NC}"

# Update the image in k8s/deployment.yaml
sed "s|IMAGE_PLACEHOLDER|${IMAGE_URI}|g" k8s/deployment.yaml | kubectl apply -n ${NAMESPACE} -f -

# Apply ConfigMap
echo -e "${YELLOW}Applying ConfigMap...${NC}"
kubectl apply -n ${NAMESPACE} -f k8s/configmap.yaml

# Apply Service
echo -e "${YELLOW}Applying Service...${NC}"
kubectl apply -n ${NAMESPACE} -f k8s/service.yaml

# Apply Ingress (optional)
if [ -f "k8s/ingress.yaml" ]; then
    echo -e "${YELLOW}Applying Ingress...${NC}"
    kubectl apply -n ${NAMESPACE} -f k8s/ingress.yaml
fi

# Apply HPA
echo -e "${YELLOW}Applying Horizontal Pod Autoscaler...${NC}"
kubectl apply -n ${NAMESPACE} -f k8s/hpa.yaml

echo -e "${GREEN}✓ Deployment successful${NC}"
echo ""

# Wait for deployment to be ready
echo -e "${YELLOW}Waiting for deployment to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s \
    deployment/cortex-ai -n ${NAMESPACE}

echo -e "${GREEN}✓ Deployment is ready${NC}"
echo ""

# Get service URL
if kubectl get service cortex-ai -n ${NAMESPACE} &> /dev/null; then
    EXTERNAL_IP=$(kubectl get service cortex-ai -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -n "$EXTERNAL_IP" ]; then
        echo -e "${BLUE}==================================================${NC}"
        echo -e "${GREEN}  Deployment Complete!${NC}"
        echo -e "${BLUE}==================================================${NC}"
        echo ""
        echo -e "External IP: ${GREEN}${EXTERNAL_IP}${NC}"
        echo ""
        echo -e "Access your application at:"
        echo -e "  http://${EXTERNAL_IP}:80"
        echo ""
    fi
fi

# Show pod status
echo -e "${YELLOW}Pod status:${NC}"
kubectl get pods -n ${NAMESPACE} -l app=cortex-ai

echo ""
echo -e "View logs:"
echo -e "  kubectl logs -n ${NAMESPACE} -l app=cortex-ai --tail=100 -f"
echo ""
echo -e "Get shell access to a pod:"
echo -e "  kubectl exec -it -n ${NAMESPACE} \$(kubectl get pod -n ${NAMESPACE} -l app=cortex-ai -o jsonpath='{.items[0].metadata.name}') -- sh"
echo ""
