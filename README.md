# NexaMind AI Platform

Graduation project - AI-powered multi-agent platform for enterprise business operations.

The idea is to have specialized AI agents for different business departments (Finance, HR, Operations, Sales, Support) that can answer questions and give recommendations based on real company data.

## What it does

You send a natural language message like *"which employees might leave next quarter?"* and the system figures out which agent to use, queries the database, and gives you a useful answer.

There are 20 agents total, 4 per module:

| Module | Agents |
|--------|--------|
| Finance | Forecaster, Anomaly Detector, Budget Advisor, Reporter |
| HR | Talent Scout, Retention Guard, Growth Coach, Culture Builder |
| Operations | Demand Planner, Supply Optimizer, Logistics Coordinator, Quality Guardian |
| Sales | Revenue Forecaster, Churn Guardian, Deal Strategist, Sales Coach |
| Support | Ticket Resolver, Sentiment Analyst, Knowledge Curator, Quality Analyst |

## System Architecture

```
User → Agent Orchestrator (port 8000)
           ↓
       [Router] - figures out which agent to use based on keywords
           ↓
       [Agent] - queries database + calls LLM
           ↓
       LLM Gateway (port 8002) → Anthropic / OpenAI
       RAG Service (port 8003) → ChromaDB (vector search)
       Auth Service (port 8001) → JWT tokens

Database: PostgreSQL with pgvector extension
Cache: Redis
```

## How to run it

### Requirements
- Docker and Docker Compose
- API key for Anthropic (recommended) or OpenAI
- OpenAI API key for embeddings (even if using Anthropic for chat)

### Setup

```bash
# 1. copy env file and add your API keys
cp .env.example .env
# edit .env - add ANTHROPIC_API_KEY and OPENAI_API_KEY

# 2. build and start everything
docker compose -f docker/docker-compose.yml up --build -d

# 3. check everything is running
bash scripts/health_check.sh
```

### Register a tenant and add test data

```bash
# register
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "slug": "testco",
    "admin_email": "admin@test.com",
    "admin_password": "Password123!",
    "admin_full_name": "Admin"
  }'

# save the tenant id from the response, then seed data:
export TENANT_ID=<paste-id-here>
python3 scripts/seed_synthetic_data.py --tenant-id $TENANT_ID
python3 scripts/seed_prompts.py --tenant-id $TENANT_ID
```

### Try it out

```bash
# finance question
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: $TENANT_ID" \
  -d '{"message": "what are our biggest expenses and where can we save money?"}'

# HR question  
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: $TENANT_ID" \
  -d '{"message": "which employees are at risk of leaving?"}'

# sales question
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: $TENANT_ID" \
  -d '{"message": "forecast our revenue for next quarter"}'
```

You can also force a specific agent:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: $TENANT_ID" \
  -d '{"message": "analyze this", "agent": "detector_agent"}'
```

## API docs

After starting, go to:
- http://localhost:8000/docs - main orchestrator
- http://localhost:8001/docs - auth service
- http://localhost:8002/docs - LLM gateway
- http://localhost:8003/docs - RAG service

## Project structure

```
nexamind-ai-platform/
├── docker/                  # docker configs for all services
├── services/
│   ├── auth-service/        # handles login, JWT tokens, API keys
│   ├── llm-gateway/         # connects to OpenAI/Anthropic APIs
│   ├── rag-service/         # document upload and semantic search
│   └── agent-orchestrator/  # main service with all 20 agents
│       ├── agents/          # one file per agent (20 total)
│       ├── tools/           # reusable tools (sql, calculation, etc)
│       ├── prompts/         # system prompts for each agent
│       ├── memory/          # short and long term memory
│       └── orchestrator/    # routing logic
├── migrations/              # database migrations
├── scripts/                 # helper scripts for setup
└── docs/                    # API documentation
```

## Database

PostgreSQL with pgvector extension for vector similarity search.
30 tables total covering all modules.

Main tables:
- tenants, users, api_keys - authentication
- agents, agent_conversations, agent_sessions - agent management
- financial_transactions, forecasts, anomalies - finance
- employees, attrition_risks, development_plans - HR
- inventory_items, demand_forecasts, suppliers - operations
- deals, customer_churn_risks, sales_targets - sales
- support_tickets, knowledge_articles, ticket_responses - support

## Technologies used

- **FastAPI** - web framework for all services
- **PostgreSQL + pgvector** - database with vector search
- **ChromaDB** - vector database for RAG
- **Redis** - caching and session storage
- **Anthropic Claude / OpenAI GPT** - LLM providers
- **Docker** - containerization
- **SQLAlchemy** - database ORM
- **JWT** - authentication

## Known issues / limitations

- the keyword routing is simple and can misclassify sometimes
- no proper logging setup yet (using print statements in places)
- email tool only works if you configure SMTP
- rate limiting is per-minute only, could be more sophisticated
- tests are not complete yet

## Notes

Built as part of my graduation project. The goal was to show how multi-agent AI systems can be applied to real enterprise use cases.
