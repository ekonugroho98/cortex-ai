# Makefile for BigQuery AI Service
# Provides convenient commands for development and deployment

.PHONY: help install run test build docker-build docker-push k8s-apply k8s-delete clean

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
VENV := venv
DOCKER_IMAGE := bigquery-ai-service
DOCKER_TAG := latest
REGISTRY := your-registry.com

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)BigQuery AI Service - Makefile$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(GREEN)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

install: ## Install dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

run: ## Run the FastAPI server locally
	@echo "$(GREEN)Starting FastAPI server...$(NC)"
	$(VENV)/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev: install ## Install dependencies and run server
	@echo "$(GREEN)Starting development server...$(NC)"
	$(VENV)/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

test: ## Run tests
	@echo "$(GREEN)Running tests...$(NC)"
	$(VENV)/bin/pytest tests/ -v

lint: ## Run linting
	@echo "$(GREEN)Running linter...$(NC)"
	$(VENV)/bin/pylint app/

format: ## Format code with black
	@echo "$(GREEN)Formatting code...$(NC)"
	$(VENV)/bin/black app/

##@ Docker

docker-build: ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "$(GREEN)✓ Docker image built: $(DOCKER_IMAGE):$(DOCKER_TAG)$(NC)"

docker-push: docker-build ## Build and push Docker image to registry
	@echo "$(GREEN)Pushing Docker image to registry...$(NC)"
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	docker push $(REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "$(GREEN)✓ Docker image pushed$(NC)"

docker-run: ## Run Docker container locally
	@echo "$(GREEN)Running Docker container...$(NC)"
	docker-compose up --build

docker-stop: ## Stop Docker containers
	@echo "$(GREEN)Stopping Docker containers...$(NC)"
	docker-compose down

##@ Kubernetes

k8s-create-ns: ## Create Kubernetes namespace
	@echo "$(GREEN)Creating namespace...$(NC)"
	kubectl apply -f k8s/namespace.yaml

k8s-apply: k8s-create-ns ## Deploy to Kubernetes
	@echo "$(GREEN)Deploying to Kubernetes...$(NC)"
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/secret.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/hpa.yaml
	@echo "$(GREEN)✓ Deployed to Kubernetes$(NC)"
	@echo "$(BLUE)To check status: kubectl get pods -n bigquery-ai-service$(NC)"

k8s-ingress: ## Apply Ingress (optional)
	@echo "$(GREEN)Applying Ingress...$(NC)"
	kubectl apply -f k8s/ingress.yaml
	@echo "$(GREEN)✓ Ingress applied$(NC)"

k8s-delete: ## Delete Kubernetes resources
	@echo "$(RED)Deleting Kubernetes resources...$(NC)"
	kubectl delete -f k8s/
	@echo "$(RED)✓ Kubernetes resources deleted$(NC)"

k8s-logs: ## View logs from Kubernetes pods
	kubectl logs -f -n bigquery-ai-service -l app=bigquery-service

k8s-status: ## Check Kubernetes deployment status
	@echo "$(BLUE)Kubernetes Status:$(NC)"
	kubectl get all -n bigquery-ai-service

##@ Utilities

clean: ## Clean up generated files
	@echo "$(RED)Cleaning up...$(NC)"
	rm -rf $(VENV)
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	rm -rf logs/*
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

init: install ## Initialize project (create .env from example)
	@echo "$(GREEN)Initializing project...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✓ Created .env file$(NC)"; \
		echo "$(BLUE)Please update .env with your configuration$(NC)"; \
	else \
		echo "$(BLUE).env file already exists$(NC)"; \
	fi

setup: init ## Full setup: create .env, install dependencies, create credentials directory
	@echo "$(GREEN)Setting up project...$(NC)"
	@mkdir -p credentials logs
	@echo "$(GREEN)✓ Created directories$(NC)"
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  1. Add your Google Cloud service account JSON to credentials/service-account.json"
	@echo "  2. Update .env with your GCP project ID and other settings"
	@echo "  3. Run 'make dev' to start the development server"
