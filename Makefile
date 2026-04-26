.PHONY: help build up down restart logs ps shell seed health clean

DOCKER_COMPOSE = docker compose -f docker/docker-compose.yml
TENANT_ID ?= $(shell cat .tenant-id 2>/dev/null || echo "")

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker images
	$(DOCKER_COMPOSE) build

up: ## Start all services
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Services starting..."
	@echo "   Orchestrator:  http://localhost:8000"
	@echo "   Auth Service:  http://localhost:8001"
	@echo "   LLM Gateway:   http://localhost:8002"
	@echo "   RAG Service:   http://localhost:8003"
	@echo "   ChromaDB:      http://localhost:8010"
	@echo ""
	@echo "Run 'make health' to check status"

up-build: ## Build and start all services
	$(DOCKER_COMPOSE) up -d --build

down: ## Stop all services
	$(DOCKER_COMPOSE) down

down-v: ## Stop all services and remove volumes (DESTRUCTIVE)
	$(DOCKER_COMPOSE) down -v

restart: ## Restart all services
	$(DOCKER_COMPOSE) restart

logs: ## View logs (all services)
	$(DOCKER_COMPOSE) logs -f

logs-orchestrator: ## View orchestrator logs
	$(DOCKER_COMPOSE) logs -f agent-orchestrator

logs-auth: ## View auth service logs
	$(DOCKER_COMPOSE) logs -f auth-service

logs-llm: ## View LLM gateway logs
	$(DOCKER_COMPOSE) logs -f llm-gateway

ps: ## Show service status
	$(DOCKER_COMPOSE) ps

health: ## Run health check
	@bash scripts/health_check.sh

register: ## Register a new tenant (use: make register NAME=acme SLUG=acme EMAIL=admin@acme.com PASS=secret)
	@curl -s -X POST http://localhost:8001/api/v1/auth/register \
		-H "Content-Type: application/json" \
		-d '{"name":"$(or $(NAME),Demo Company)","slug":"$(or $(SLUG),demo)","admin_email":"$(or $(EMAIL),admin@demo.com)","admin_password":"$(or $(PASS),Admin123!)","admin_full_name":"Admin User"}' | python3 -m json.tool

seed: ## Seed synthetic data (requires TENANT_ID env var)
	@if [ -z "$(TENANT_ID)" ]; then echo "Error: Set TENANT_ID env var"; exit 1; fi
	python3 scripts/seed_synthetic_data.py --tenant-id $(TENANT_ID) --db-url postgresql://nexamind:nexamind_secret@localhost:5432/nexamind
	python3 scripts/seed_prompts.py --tenant-id $(TENANT_ID) --db-url postgresql://nexamind:nexamind_secret@localhost:5432/nexamind

shell-postgres: ## Open PostgreSQL shell
	$(DOCKER_COMPOSE) exec postgres psql -U nexamind nexamind

shell-redis: ## Open Redis shell
	$(DOCKER_COMPOSE) exec redis redis-cli

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

test: ## Run tests
	pytest tests/ -v --tb=short

format: ## Format Python code
	black services/ scripts/
	ruff check --fix services/ scripts/

api-docs: ## Open API documentation
	@echo "Opening API docs..."
	@python3 -c "import webbrowser; webbrowser.open('http://localhost:8000/docs')"

# Quick demo commands
demo-finance: ## Run a finance demo query
	@curl -s -X POST http://localhost:8000/api/v1/chat \
		-H "Content-Type: application/json" \
		-H "X-Tenant-Id: $(or $(TENANT_ID),demo)" \
		-d '{"message":"What are our top spending categories and where can we reduce costs?"}' | python3 -m json.tool

demo-hr: ## Run an HR demo query
	@curl -s -X POST http://localhost:8000/api/v1/chat \
		-H "Content-Type: application/json" \
		-H "X-Tenant-Id: $(or $(TENANT_ID),demo)" \
		-d '{"message":"Which employees are at highest attrition risk this quarter?"}' | python3 -m json.tool

demo-sales: ## Run a sales demo query
	@curl -s -X POST http://localhost:8000/api/v1/chat \
		-H "Content-Type: application/json" \
		-H "X-Tenant-Id: $(or $(TENANT_ID),demo)" \
		-d '{"message":"Forecast our revenue for next quarter based on current pipeline"}' | python3 -m json.tool
