# 🚀 CortexAI GCP Deployment Guide

Complete guide for deploying CortexAI to Google Cloud Platform.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Option A: Cloud Run Deployment (Recommended)](#option-a-cloud-run-deployment)
4. [Option B: GKE Deployment](#option-b-gke-deployment)
5. [Post-Deployment Setup](#post-deployment-setup)
6. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)

---

## 📦 Prerequisites

### Required Tools

```bash
# Install Google Cloud SDK
# macOS
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Windows
# Download from: https://cloud.google.com/sdk/docs/install
```

### Authenticate and Configure

```bash
# Authenticate with GCP
gcloud auth login

# Set your project
export PROJECT_ID="gen-lang-client-0716506049"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
gcloud services enable \
    bigquery.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    container.googleapis.com
```

### Create Secrets

```bash
# 1. Upload Anthropic API Key
echo -n "your-anthropic-api-key" | \
  gcloud secrets versions add cortex-ai-anthropic-key --data-file=-

# 2. Upload Service Account Key
gcloud secrets create cortex-ai-sa-key \
  --data-file=credentials/service-account.json

# Verify secrets
gcloud secrets list
```

---

## 🎯 Deployment Options

### Quick Comparison

| Feature | Cloud Run | GKE |
|---------|-----------|-----|
| **Difficulty** | ⭐ Easy | ⭐⭐⭐ Advanced |
| **Cost** | Pay per use | Fixed cluster cost |
| **Scaling** | 0 → ∞ auto | Manual + HPA |
| **Management** | Serverless | Managed nodes |
| **Best For** | Development, MVP, Low-Medium traffic | Production, High traffic |
| **Est. Cost** | $10-50/mo | $100-300/mo |

**Recommendation**: Start with **Cloud Run**, upgrade to GKE when needed.

---

## ☁️ Option A: Cloud Run Deployment

### Step 1: Automated Deployment (Recommended)

```bash
# Make script executable
chmod +x scripts/deploy-cloudrun.sh

# Run deployment
./scripts/deploy-cloudrun.sh
```

### Step 2: Manual Deployment

#### A. Create Artifact Registry

```bash
export REGION="asia-southeast1"
export REPO_NAME="cortex-ai"

gcloud artifacts repositories create ${REPO_NAME} \
  --repository-format=docker \
  --location=${REGION} \
  --description="CortexAI Docker images"
```

#### B. Build and Push Image

```bash
# Build with Cloud Build
gcloud builds submit \
  --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/cortex-ai:latest

# Or build locally
docker build -t cortex-ai:latest .
docker tag cortex-ai:latest ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/cortex-ai:latest
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/cortex-ai:latest
```

#### C. Deploy to Cloud Run

```bash
gcloud run deploy cortex-ai \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/cortex-ai:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --max-instances=100 \
  --timeout=300s \
  --concurrency=10 \
  --set-env-vars=FASTAPI_ENV=production,GCP_PROJECT_ID=${PROJECT_ID},BIGQUERY_LOCATION=US \
  --set-secrets=ANTHROPIC_API_KEY=cortex-ai-anthropic-key:latest,GOOGLE_APPLICATION_CREDENTIALS=cortex-ai-sa-key:latest
```

#### D. Get Service URL

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe cortex-ai \
  --region=${REGION} \
  --format="value(status.url)")

echo "Service URL: ${SERVICE_URL}"

# Test health endpoint
curl ${SERVICE_URL}/health
```

---

## 🎮 Option B: GKE Deployment

### Step 1: Automated Deployment

```bash
# Make script executable
chmod +x scripts/deploy-gke.sh

# Run deployment
./scripts/deploy-gke.sh
```

### Step 2: Manual Deployment

#### A. Create GKE Cluster

```bash
export CLUSTER_NAME="cortex-ai-cluster"
export REGION="asia-southeast1"

gcloud container clusters create ${CLUSTER_NAME} \
  --region=${REGION} \
  --num-nodes=2 \
  --machine-type=e2-medium \
  --disk-size=100GB \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=5 \
  --enable-autorepair \
  --enable-autoupgrade
```

#### B. Configure kubectl

```bash
# Get cluster credentials
gcloud container clusters get-credentials ${CLUSTER_NAME} --region=${REGION}

# Verify connection
kubectl cluster-info
```

#### C. Create Namespace

```bash
kubectl create namespace cortex-ai
```

#### D. Create Secrets

```bash
# Create secret from Secret Manager
kubectl create secret generic cortex-ai-secrets \
  --from-literal=ANTHROPIC_API_KEY="$(gcloud secrets versions access latest --secret=cortex-ai-anthropic-key)" \
  --from-literal=GOOGLE_APPLICATION_CREDENTIALS="$(gcloud secrets versions access latest --secret=cortex-ai-sa-key)" \
  -n cortex-ai
```

#### E. Build and Push Image

```bash
export IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/cortex-ai/cortex-ai:latest"

gcloud builds submit --tag ${IMAGE_URI}
```

#### F. Update Deployment Image

```bash
# Update deployment.yaml with image URI
sed "s|IMAGE_PLACEHOLDER|${IMAGE_URI}|g" k8s/deployment.yaml | \
  kubectl apply -n cortex-ai -f -
```

#### G. Apply Kubernetes Manifests

```bash
# Apply ConfigMap
kubectl apply -n cortex-ai -f k8s/configmap.yaml

# Apply Service
kubectl apply -n cortex-ai -f k8s/service.yaml

# Apply HPA
kubectl apply -n cortex-ai -f k8s/hpa.yaml

# Apply Ingress (optional)
kubectl apply -n cortex-ai -f k8s/ingress.yaml
```

#### H. Verify Deployment

```bash
# Check pods
kubectl get pods -n cortex-ai

# Check service
kubectl get svc -n cortex-ai

# Get external IP
kubectl get service cortex-ai -n cortex-ai \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

---

## 🔧 Post-Deployment Setup

### 1. Setup Custom Domain

#### Cloud Run

```bash
# Map custom domain
gcloud run domain mappings create cortex-ai.yourdomain.com \
  --service=cortex-ai \
  --region=${REGION}
```

#### GKE with Cloud Armor

```bash
# Create static IP
gcloud compute addresses create cortex-ai-ip --region=${REGION}

# Update ingress.yaml with the IP
kubectl apply -f k8s/ingress.yaml
```

### 2. Setup Monitoring

```bash
# Cloud Monitoring
# Create log-based metrics
gcloud logging metrics create cortex-ai-errors \
  --description="CortexAI Error Count" \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="cortex-ai" AND severity>=ERROR'

# Create alerting policy
gcloud alpha monitoring policies create --policy-from-file=monitoring/alert-policy.yaml
```

### 3. Setup CI/CD

```bash
# Trigger Cloud Build on git push
gcloud beta builds triggers create github \
  --name=cortex-ai-trigger \
  --repo-owner=ekonugroho98 \
  --repo-name=cortex-ai \
  --branch-pattern=main \
  --build-config=cloudbuild.yaml
```

---

## 🔍 Monitoring and Troubleshooting

### Cloud Run

```bash
# View logs
gcloud run logs tail cortex-ai --region=${REGION}

# View service details
gcloud run services describe cortex-ai --region=${REGION}

# View revisions
gcloud run revisions list --service=cortex-ai --region=${REGION}

# Rollback to previous revision
gcloud run services update cortex-ai \
  --region=${REGION} \
  --revision=<previous-revision-id>
```

### GKE

```bash
# View logs
kubectl logs -n cortex-ai -l app=cortex-ai --tail=100 -f

# Get pod status
kubectl get pods -n cortex-ai

# Describe pod
kubectl describe pod -n cortex-ai -l app=cortex-ai

# Exec into pod
kubectl exec -it -n cortex-ai \
  $(kubectl get pod -n cortex-ai -l app=cortex-ai -o jsonpath='{.items[0].metadata.name}') \
  -- sh

# Restart deployment
kubectl rollout restart deployment/cortex-ai -n cortex-ai

# Check HPA status
kubectl get hpa -n cortex-ai
```

### Cloud Logging

```bash
# View recent logs
gcloud logging read \
  'resource.type="cloud_run_revision"' \
  --limit=50 \
  --freshness=1h

# Export logs
gcloud logging read \
  'resource.type="cloud_run_revision"' \
  --freshness=24h \
  --format=json > logs.json
```

---

## 💰 Cost Optimization

### Cloud Run Optimization

```bash
# Set minimum instances to 0 (scale to zero)
gcloud run services update cortex-ai \
  --region=${REGION} \
  --min-instances=0 \
  --max-instances=10

# Use smaller instance size
gcloud run services update cortex-ai \
  --region=${REGION} \
  --memory=256Mi \
  --cpu=0.5

# Set appropriate timeout
gcloud run services update cortex-ai \
  --region=${REGION} \
  --timeout=60s
```

### GKE Optimization

```bash
# Use preemptible nodes
gcloud container clusters update ${CLUSTER_NAME} \
  --region=${REGION} \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=3

# Use node auto-provisioning
gcloud container clusters update ${CLUSTER_NAME} \
  --region=${REGION} \
  --enable-autoprovisioning \
  --max-cpu=10 \
  --max-memory=50
```

---

## 🔐 Security Best Practices

1. **Use Secret Manager** for all sensitive data
2. **Enable IAM authentication** instead of allowing unauthenticated access
3. **Setup VPC Service Controls** for private BigQuery access
4. **Enable Cloud Armor** for DDoS protection
5. **Regular security scans**
   ```bash
   gcloud artifacts docker images scan \
     ${REGION}-docker.pkg.dev/${PROJECT_ID}/cortex-ai/cortex-ai:latest
   ```
6. **Use Binary Authorization** for image policy

---

## 📞 Support

For issues or questions:
- Check Cloud Logging for errors
- Review deployment logs
- Verify IAM permissions
- Check BigQuery quota limits

---

## 🎯 Next Steps

1. ✅ Deploy to Cloud Run (dev/staging)
2. ✅ Test all endpoints
3. ✅ Setup monitoring and alerting
4. ✅ Configure custom domain
5. ✅ Setup CI/CD pipeline
6. ✅ Migrate to GKE (if needed)
7. ✅ Setup multi-region deployment
8. ✅ Implement A/B testing

---

**Last Updated**: 2025-01-16
**Version**: 1.0.0
