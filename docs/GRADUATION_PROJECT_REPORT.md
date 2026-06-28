# NexaMind AI Platform: A Multi-Agent Enterprise Operations System
**Graduation Project Thesis & Technical Report**

---

## Executive Summary & Abstract
Modern enterprise environments generate vast, highly siloed datasets spanning financial logs, HR records, sales pipelines, supply chain schedules, and support ticket databases. Navigating this heterogeneous data landscape requires deep domain knowledge, specialized analytical skills, and substantial manual effort. 

**NexaMind** is a state-of-the-art, multi-agent AI platform designed to automate and orchestrate complex business operations. Built on a containerized microservices architecture, NexaMind employs **20 specialized domain agents** coordinated by a central intelligent router. Using a combination of SQL execution tools, mathematical calculators, and Vector Retrieval-Augmented Generation (RAG), the platform processes unstructured natural language queries, automatically routes them to the appropriate domain specialist, retrieves live enterprise data from PostgreSQL and ChromaDB, and synthesizes structured business responses. NexaMind implements robust multi-tenancy, JWT-based security boundaries, caching layers, and high-performance LLM routing to provide a scalable, secure, and production-ready solution for enterprise decision support.

---

## 1. Business Problem & Solution Overview
In large enterprise systems, data is fragmented across legacy databases, web portals, and unindexed document repositories. This fragmentation leads to:
- **Decision Latency**: Business analysts must write custom queries or compile spreadsheets manually to answer cross-functional questions.
- **Siloed Context**: A question about customer churn requires combining support ticket sentiments (Support) with sales pipelines (Sales) and subscription revenues (Finance).
- **Security Vulnerabilities**: Enforcing multi-tenant security boundaries at scale across diverse APIs is error-prone.

NexaMind solves these challenges by providing a natural language interface that wraps around live enterprise data. Instead of raw SQL or complex dashboard filters, a business leader can type *"Are we at risk of missing our revenue forecast due to customer churn?"* NexaMind's orchestrator automatically parses the query, identifies the dependencies, routes to the relevant specialists, queries the Postgres database securely using parameterized SQL, queries ChromaDB for policy documents, and generates a unified, grounded report.

---

## 2. Microservices System Architecture
NexaMind is engineered as a distributed, loosely coupled microservices network. This ensures horizontal scaling, fault tolerance, and isolated upgrades.

```mermaid
graph TD
    User([Web Browser GUI]) <--> |HTTP/REST / JWT| Orchestrator[Agent Orchestrator :8000]
    Orchestrator <--> |HTTP| Auth[Auth Service :8001]
    Orchestrator <--> |HTTP| LLM[LLM Gateway :8002]
    Orchestrator <--> |HTTP| RAG[RAG Service :8003]
    RAG <--> |gRPC/HTTP| ChromaDB[(ChromaDB :8010)]
    Orchestrator <--> |SQL| Postgres[(PostgreSQL :5433)]
    Orchestrator <--> |RESP| Redis[(Redis :6379)]
    Auth <--> |SQL| Postgres
```

### 2.1 Agent Orchestrator (`port 8000`)
The central service of the platform. It handles the Web GUI, user sessions, chat routing, agent execution loop, and tool execution.
- **Router**: Uses semantic parsing and keyword maps to classify user intents and delegate them to specific agents.
- **Agent Loop**: Implements ReAct (Reasoning and Acting) execution loops, allowing agents to execute multiple tools (e.g. database query -> math calculation) sequentially before responding.
- **Web GUI**: A premium responsive dashboard built with Glassmorphic CSS, visual theme configurations, connection diagnostics, Chat Hub workspace, and Agent registry grids.

### 2.2 Authentication Service (`port 8001`)
Manages security, multi-tenancy boundaries, user accounts, and API keys.
- Enforces strict tenant isolation by generating JWT tokens signed with SHA-256 containing `tenant_id` claims.
- Every API request to the database or vector store requires a valid `X-Tenant-Id` header, which is cross-referenced with the JWT claims to block cross-tenant data leaks.

### 2.3 LLM Gateway Service (`port 8002`)
Acts as a unified middleware layer interfacing with AI models (Anthropic Claude, OpenAI GPT-4, Groq LLaMA).
- **Resiliency**: Handles rate limiting, automatic retries with exponential backoff, and model fallback logic.
- **Prompt Caching**: Caches long system prompt structures using Redis to reduce token costs and request latency.

### 2.4 RAG Service (`port 8003`)
Handles unstructured document ingestion, chunking, vector embedding generation, and vector store retrieval.
- **ChromaDB Integration**: Communicates with ChromaDB on port 8010 to index enterprise wikis, employee handbooks, and policy manuals.
- **Query Vectorizer**: Generates 1536-dimensional embeddings (using `text-embedding-3-small` or local sentence-transformers) to perform cosine-similarity matches.

---

## 3. Database Architecture & Schema Design
The platform uses **PostgreSQL 16** with the **pgvector** extension to house structured relational data alongside vector embeddings.

### 3.1 Domain Data Model (30 Tables)
The database structure is partitioned into 6 distinct modules:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                SYSTEM & AUTH                                │
│  - tenants              - users                  - api_keys                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
         ┌──────────────┬──────────────┼──────────────┬──────────────┐
         ▼              ▼              ▼              ▼              ▼
    ┌─────────┐   ┌──────────┐   ┌───────────┐  ┌───────────┐  ┌───────────┐
    │ FINANCE │   │    HR    │   │OPERATIONS │  │   SALES   │  │  SUPPORT  │
    └─────────┘   └──────────┘   └───────────┘  └───────────┘  └───────────┘
```

#### 1. System & Authentication
- `tenants`: Master list of registered corporate workspaces (ID, name, slug).
- `users`: User profiles, hashed credentials, and role mappings.
- `api_keys`: Tokens for external application integrations.
- `agent_conversations`: Holds multi-turn chat logs (ID, user_id, title).
- `agent_sessions`: Active sessions and token contexts.

#### 2. Finance Module Tables
- `financial_transactions`: Ledger of all incomes and expenses (amount, currency, category, counterparty).
- `forecasts`: Statistical predictions generated by models.
- `anomalies`: Flagged outlier transactions requiring audit.
- `budgets`: Set limits for departments and categories.

#### 3. Human Resources Module Tables
- `employees`: Demographic, salary, role, and department data.
- `attrition_risks`: Estimated risk scores and key drivers for employee departures.
- `development_plans`: Structured training and career milestones.
- `engagement_surveys`: Scores and sentiment from employee feedback surveys.

#### 4. Operations & Supply Chain Tables
- `inventory_items`: Current stock levels, SKU IDs, costs, and reorder points.
- `suppliers`: Lead times, reliability ratings, and payment terms.
- `purchase_orders`: Inbound stock orders and fulfillment statuses.
- `demand_forecasts`: Projected stock requirements based on sales patterns.

#### 5. Sales & Customer Pipeline Tables
- `deals`: Sales pipeline details (stage, probability, contract value, close date, deal owner).
- `customer_churn_risks`: Churn risk scores, risk levels, and revenue-at-risk valuations.
- `sales_targets`: Quota levels and attainment metrics by agent/territory.
- `accounts`: Enterprise customer profiles and subscription tiers.

#### 6. Support Desk & Service Tables
- `support_tickets`: Customer support requests (priority, status, category, sentiment score).
- `knowledge_articles`: Unstructured text documents ingested into the RAG vector space.
- `ticket_responses`: Historical resolution logs and agent replies.
- `sla_metrics`: SLA compliance tracking records.

---

## 4. The 20 Specialized Agents
Each department contains 4 agents. Each agent is configured with a tailored system prompt, custom database access limits (read-only views), and specific tool sets.

| Module | Agent Name | Primary Responsibility | Primary Tools Used |
| :--- | :--- | :--- | :--- |
| **Finance** | **Revenue Forecaster** | Generates cash flow and income projections. | SQL Database, Calculator |
| | **Anomaly Detector** | Scans ledger transactions to flag fraud/outliers. | SQL Database, Isolation Forest |
| | **Budget Advisor** | Recommends cost-cutting and burn rate adjustments. | SQL Database, Calculator |
| | **Financial Reporter** | Compiles balance sheets and income statements. | SQL Database, Excel Exporter |
| **HR** | **Talent Scout** | Recommends hiring targets and source channels. | SQL Database, RAG Service |
| | **Retention Guard** | Identifies top attrition risks and mitigations. | SQL Database, Calculator |
| | **Growth Coach** | Synthesizes employee career development plans. | SQL Database, RAG Service |
| | **Culture Builder** | Analyzes survey results to outline team wellness plans. | SQL Database, Sentiment Tool |
| **Operations**| **Demand Planner** | Estimates SKU and product manufacturing volumes. | SQL Database, Calculator |
| | **Supply Optimizer** | Scores suppliers and adjusts raw material order logs. | SQL Database |
| | **Logistics Coordinator**| Reviews shipping routes, lead times, and transit logs. | SQL Database, Geo Distance |
| | **Quality Guardian** | Evaluates product defects and returns. | SQL Database, Calculator |
| **Sales** | **Revenue Forecaster** | Forecasts monthly and quarterly sales pipelines. | SQL Database, Calculator |
| | **Churn Guardian** | Computes account health and churn interventions. | SQL Database, Calculator |
| | **Deal Strategist** | Suggests close tactics based on buyer profile. | SQL Database, RAG Service |
| | **Sales Coach** | Identifies rep quota bottlenecks and training needs. | SQL Database |
| **Support** | **Ticket Resolver** | Drafts support responses based on historical tickets. | SQL Database, RAG Service |
| | **Sentiment Analyst** | Reviews customer tickets to identify high-escalation cases. | SQL Database, Sentiment Tool |
| | **Knowledge Curator** | Extracts Q&A from resolved tickets to build docs. | RAG Service, DB Writer |
| | **Quality Analyst** | Evaluates customer satisfaction scores (CSAT). | SQL Database, Calculator |

---

## 5. Execution Pipeline & Routing Logic
NexaMind uses an agentic pipeline to translate human input into database actions securely.

### 5.1 Step-by-Step Flow
1. **User Query**: User submits a query in the Chat Hub.
2. **Tenant Verification**: The orchestrator extracts the `tenant_id` from the JWT context.
3. **Intent Classification & Routing**:
   - The central router evaluates the query keywords or calls a lightweight semantic classification model.
   - Example: *"What was our subscription revenue last month?"* routes to `Budget Advisor` or `Financial Reporter`.
4. **Tool Call Formulation**:
   - The selected specialist agent initializes. It reads its system prompt detailing the PostgreSQL schema for the relevant tables.
   - The LLM generates a SQL query restricted to the current `tenant_id`:
     `SELECT amount, category FROM financial_transactions WHERE tenant_id = '0b657cee...' AND transaction_date >= '2026-05-01';`
5. **Safe Database Execution**:
   - The Orchestrator runs the SQL query against PostgreSQL.
   - It captures the tabular results and sends them back to the LLM agent context.
6. **Synthesis & Presentation**:
   - The agent calculates summaries (e.g. sums values, checks trends) and writes a markdown summary.
   - The UI renders the final answer.

```
[User Input]
     │
     ▼
[JWT Auth Boundary] ──► Extracts tenant_id
     │
     ▼
[General Router] ──► Selects Specialist Agent (e.g. Budget Advisor)
     │
     ▼
[Specialist Agent] ──► Builds tenant-scoped SQL Query
     │
     ▼
[SQL Executor] ──► Queries PostgreSQL Database
     │
     ▼
[Response Synthesizer] ──► Combines SQL Data + System Context
     │
     ▼
[Markdown Result] ──► Renders in Web UI
```

---

## 6. Installation, Configuration & Deployment

### 6.1 Setup Environment Variables
Create `/run/media/abdallahahmed/M/nexamind-ai-platform/.env`:
```env
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-proj-...
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=app
```

### 6.2 Spin up Containers
Run the Docker compose stack:
```bash
make up
```

### 6.3 Register Tenant & Seed Data
Register a default tenant and seed postgres tables and ChromaDB vector embeddings:
```bash
# Register tenant
curl -s -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"NexaMind Demo","slug":"demo","admin_email":"admin@demo.com","admin_password":"Admin123!","admin_full_name":"Admin User"}'

# Export the returned tenant UUID
export TENANT_ID="0b657cee-f923-42bf-8cae-3841ecc391df"

# Seed data using Python 3.14 on the host pointing to database port 5433
python3 scripts/seed_synthetic_data.py --tenant-id $TENANT_ID --db-url postgresql://postgres:postgres@localhost:5433/app
python3 scripts/seed_prompts.py --tenant-id $TENANT_ID --db-url postgresql://postgres:postgres@localhost:5433/app
```

---

## 7. Conclusion & Future Directions
NexaMind demonstrates the viability of utilizing distributed, multi-agent AI systems for unified enterprise command centers. 
- **Security**: The multi-tenant architecture effectively prevents cross-tenant data leaks.
- **Accuracy**: Routing to specialized agents with focused system prompts yields higher accuracy and fewer hallucinations than using a single monolithic general-purpose agent.

### Future Improvements
1. **Dynamic Agent Collaboration**: Enable agents to spawn sub-tasks and exchange data directly (e.g. Sales Churn agent messaging the Support ticket resolver).
2. **Auto-tuning Routing Classifier**: Transition keyword-based routing into an online-trained classifier using logged query embeddings.
3. **Advanced SQL Sandboxing**: Implement read-only database connections and automated query safety scanners to prevent SQL injection or destructive updates.
