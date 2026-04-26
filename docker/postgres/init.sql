-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- CORE TABLES
-- ============================================================

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'starter',
    status VARCHAR(50) DEFAULT 'active',
    max_users INTEGER DEFAULT 10,
    max_api_calls_per_month INTEGER DEFAULT 10000,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    permissions JSONB DEFAULT '[]',
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id),
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMPTZ,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    scopes JSONB DEFAULT '["read","write"]',
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- AGENT TABLES
-- ============================================================

CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    module VARCHAR(50) NOT NULL,
    description TEXT,
    capabilities JSONB DEFAULT '[]',
    tools JSONB DEFAULT '[]',
    model_config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    version VARCHAR(20) DEFAULT '1.0.0',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    agent_name VARCHAR(100) REFERENCES agents(name),
    status VARCHAR(50) DEFAULT 'active',
    context JSONB DEFAULT '{}',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

CREATE TABLE agent_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES agent_sessions(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    agent_name VARCHAR(100),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    tokens_used INTEGER DEFAULT 0,
    latency_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agent_collaborations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES agent_sessions(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    initiator_agent VARCHAR(100),
    target_agent VARCHAR(100),
    task TEXT,
    result JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE agent_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES agent_conversations(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    categories JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agent_memory_long_term (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    agent_name VARCHAR(100),
    memory_type VARCHAR(50),
    key VARCHAR(255),
    value JSONB,
    embedding vector(1536),
    importance_score FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, agent_name, key)
);

-- ============================================================
-- FINANCE MODULE
-- ============================================================

CREATE TABLE financial_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    category VARCHAR(100),
    subcategory VARCHAR(100),
    description TEXT,
    account_id VARCHAR(100),
    counterparty VARCHAR(255),
    transaction_type VARCHAR(50),
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    forecast_type VARCHAR(100) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    granularity VARCHAR(20) DEFAULT 'monthly',
    values JSONB NOT NULL,
    confidence_intervals JSONB,
    methodology VARCHAR(100),
    assumptions TEXT,
    accuracy_metrics JSONB,
    created_by_agent VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE anomalies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    transaction_id UUID REFERENCES financial_transactions(id) ON DELETE SET NULL,
    anomaly_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    score FLOAT,
    description TEXT,
    context JSONB,
    recommended_action TEXT,
    status VARCHAR(50) DEFAULT 'open',
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE budget_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    category VARCHAR(100),
    current_spend DECIMAL(15,2),
    recommended_budget DECIMAL(15,2),
    potential_savings DECIMAL(15,2),
    reasoning TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    impact_score FLOAT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- HR MODULE
-- ============================================================

CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id VARCHAR(100) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    department VARCHAR(100),
    job_title VARCHAR(255),
    manager_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    hire_date DATE,
    salary DECIMAL(12,2),
    performance_score FLOAT,
    engagement_score FLOAT,
    skills JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, employee_id)
);

CREATE TABLE attrition_risks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    risk_score FLOAT NOT NULL,
    risk_level VARCHAR(20),
    risk_factors JSONB DEFAULT '[]',
    retention_strategies JSONB DEFAULT '[]',
    predicted_departure_date DATE,
    manager_alerted BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE development_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    title VARCHAR(255),
    objectives JSONB DEFAULT '[]',
    skill_gaps JSONB DEFAULT '[]',
    recommended_training JSONB DEFAULT '[]',
    milestones JSONB DEFAULT '[]',
    target_date DATE,
    progress FLOAT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE engagement_surveys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    survey_date DATE NOT NULL,
    overall_score FLOAT,
    responses JSONB DEFAULT '{}',
    sentiment VARCHAR(20),
    themes JSONB DEFAULT '[]',
    is_anonymous BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- OPERATIONS MODULE
-- ============================================================

CREATE TABLE inventory_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    unit_cost DECIMAL(12,4),
    current_stock INTEGER DEFAULT 0,
    reorder_point INTEGER,
    reorder_quantity INTEGER,
    lead_time_days INTEGER,
    location VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, sku)
);

CREATE TABLE demand_forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    item_id UUID REFERENCES inventory_items(id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    horizon_days INTEGER NOT NULL,
    predicted_demand JSONB NOT NULL,
    confidence_intervals JSONB,
    seasonality_factors JSONB,
    model_used VARCHAR(100),
    accuracy FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255),
    reliability_score FLOAT,
    lead_time_days INTEGER,
    payment_terms VARCHAR(100),
    categories JSONB DEFAULT '[]',
    performance_history JSONB DEFAULT '[]',
    is_preferred BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE quality_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    item_id UUID REFERENCES inventory_items(id) ON DELETE SET NULL,
    measurement_date DATE NOT NULL,
    defect_rate FLOAT,
    defect_types JSONB DEFAULT '[]',
    batch_id VARCHAR(100),
    supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    corrective_actions JSONB DEFAULT '[]',
    quality_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SALES MODULE
-- ============================================================

CREATE TABLE deals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    deal_name VARCHAR(255) NOT NULL,
    customer_name VARCHAR(255),
    customer_id VARCHAR(100),
    stage VARCHAR(100),
    amount DECIMAL(15,2),
    probability FLOAT,
    expected_close_date DATE,
    owner VARCHAR(255),
    products JSONB DEFAULT '[]',
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE customer_churn_risks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id VARCHAR(100) NOT NULL,
    customer_name VARCHAR(255),
    churn_score FLOAT NOT NULL,
    risk_level VARCHAR(20),
    risk_factors JSONB DEFAULT '[]',
    retention_actions JSONB DEFAULT '[]',
    predicted_churn_date DATE,
    annual_revenue_at_risk DECIMAL(15,2),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sales_targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    rep_name VARCHAR(255),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    target_amount DECIMAL(15,2),
    achieved_amount DECIMAL(15,2) DEFAULT 0,
    attainment_pct FLOAT,
    product_targets JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE customer_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id VARCHAR(100),
    customer_name VARCHAR(255),
    feedback_date DATE NOT NULL,
    channel VARCHAR(50),
    rating INTEGER CHECK (rating BETWEEN 1 AND 10),
    sentiment VARCHAR(20),
    sentiment_score FLOAT,
    themes JSONB DEFAULT '[]',
    raw_feedback TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SUPPORT MODULE
-- ============================================================

CREATE TABLE support_tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id VARCHAR(100),
    customer_name VARCHAR(255),
    subject VARCHAR(500),
    description TEXT,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'open',
    assigned_to VARCHAR(255),
    channel VARCHAR(50),
    sentiment VARCHAR(20),
    sentiment_score FLOAT,
    resolution TEXT,
    csat_score INTEGER,
    first_response_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE knowledge_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    tags JSONB DEFAULT '[]',
    embedding vector(1536),
    view_count INTEGER DEFAULT 0,
    helpful_votes INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'draft',
    author VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ticket_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID REFERENCES support_tickets(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    responder_type VARCHAR(50) DEFAULT 'agent',
    responder_name VARCHAR(255),
    content TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT FALSE,
    knowledge_articles_used JSONB DEFAULT '[]',
    quality_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE quality_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    ticket_id UUID REFERENCES support_tickets(id) ON DELETE CASCADE,
    agent_name VARCHAR(255),
    dimension VARCHAR(100),
    score FLOAT NOT NULL,
    feedback TEXT,
    evaluated_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX idx_agent_conversations_session ON agent_conversations(session_id);
CREATE INDEX idx_agent_conversations_tenant ON agent_conversations(tenant_id);
CREATE INDEX idx_agent_conversations_created ON agent_conversations(created_at DESC);
CREATE INDEX idx_agent_memory_tenant_agent ON agent_memory_long_term(tenant_id, agent_name);
CREATE INDEX idx_knowledge_articles_tenant ON knowledge_articles(tenant_id);
CREATE INDEX idx_support_tickets_tenant ON support_tickets(tenant_id);
CREATE INDEX idx_support_tickets_status ON support_tickets(status);
CREATE INDEX idx_financial_transactions_tenant ON financial_transactions(tenant_id);
CREATE INDEX idx_financial_transactions_date ON financial_transactions(transaction_date DESC);
CREATE INDEX idx_employees_tenant ON employees(tenant_id);
CREATE INDEX idx_deals_tenant ON deals(tenant_id);
CREATE INDEX idx_inventory_items_tenant ON inventory_items(tenant_id);

-- Vector indexes for semantic search
CREATE INDEX idx_agent_memory_embedding ON agent_memory_long_term USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_knowledge_articles_embedding ON knowledge_articles USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================
-- SEED: Register built-in agents
-- ============================================================

INSERT INTO agents (name, display_name, module, description, capabilities, tools) VALUES
  ('forecaster_agent', 'Financial Forecaster', 'finance', 'Cash flow, revenue, and expense forecasting with confidence intervals', '["cash_flow_forecast","revenue_forecast","expense_forecast","trend_analysis"]', '["sql_tool","calculation_tool","rag_tool","api_tool"]'),
  ('detector_agent', 'Anomaly Detector', 'finance', 'Real-time anomaly and fraud detection across financial transactions', '["anomaly_detection","fraud_detection","pattern_analysis","alert_generation"]', '["sql_tool","calculation_tool","rag_tool","webhook_tool"]'),
  ('advisor_agent', 'Budget Advisor', 'finance', 'Budget optimization and cost reduction recommendations', '["budget_analysis","cost_optimization","scenario_planning","roi_analysis"]', '["sql_tool","calculation_tool","rag_tool","document_tool"]'),
  ('reporter_agent', 'Financial Reporter', 'finance', 'Automated financial narrative generation and executive reporting', '["report_generation","narrative_creation","dashboard_data","executive_summary"]', '["sql_tool","rag_tool","document_tool","email_tool"]'),
  ('talent_scout_agent', 'Talent Scout', 'hr', 'AI-powered candidate screening and recruitment optimization', '["candidate_screening","job_description_optimization","culture_fit_analysis","pipeline_management"]', '["sql_tool","document_tool","rag_tool","api_tool"]'),
  ('retention_guard_agent', 'Retention Guard', 'hr', 'Predictive attrition modeling and retention strategy generation', '["attrition_prediction","retention_planning","risk_scoring","manager_alerts"]', '["sql_tool","calculation_tool","rag_tool","webhook_tool"]'),
  ('growth_coach_agent', 'Growth Coach', 'hr', 'Personalized career development and skill gap analysis', '["skill_gap_analysis","career_path_planning","training_recommendations","progress_tracking"]', '["sql_tool","rag_tool","document_tool","email_tool"]'),
  ('culture_builder_agent', 'Culture Builder', 'hr', 'Employee sentiment analysis and engagement insights', '["sentiment_analysis","engagement_scoring","culture_assessment","initiative_planning"]', '["sql_tool","rag_tool","api_tool","document_tool"]'),
  ('demand_planner_agent', 'Demand Planner', 'operations', 'Demand forecasting and inventory optimization', '["demand_forecasting","inventory_optimization","replenishment_planning","seasonal_analysis"]', '["sql_tool","calculation_tool","rag_tool","api_tool"]'),
  ('supply_optimizer_agent', 'Supply Optimizer', 'operations', 'Procurement optimization and supplier performance analysis', '["supplier_scoring","procurement_optimization","cost_reduction","risk_assessment"]', '["sql_tool","calculation_tool","rag_tool","webhook_tool"]'),
  ('logistics_coordinator_agent', 'Logistics Coordinator', 'operations', 'Route optimization and delivery planning', '["route_optimization","carrier_selection","delivery_scheduling","cost_minimization"]', '["sql_tool","calculation_tool","api_tool","rag_tool"]'),
  ('quality_guardian_agent', 'Quality Guardian', 'operations', 'Quality monitoring and defect analysis', '["defect_analysis","quality_reporting","corrective_actions","supplier_quality"]', '["sql_tool","calculation_tool","document_tool","rag_tool"]'),
  ('revenue_forecaster_agent', 'Revenue Forecaster', 'sales', 'Revenue predictions and pipeline analysis', '["revenue_forecasting","pipeline_analysis","quota_attainment","trend_analysis"]', '["sql_tool","calculation_tool","api_tool","rag_tool"]'),
  ('churn_guardian_agent', 'Churn Guardian', 'sales', 'Customer churn prediction and retention strategies', '["churn_prediction","retention_planning","customer_health_scoring","at_risk_alerts"]', '["sql_tool","calculation_tool","rag_tool","webhook_tool"]'),
  ('deal_strategist_agent', 'Deal Strategist', 'sales', 'Deal strategy, pricing optimization and proposal creation', '["deal_coaching","pricing_optimization","competitive_analysis","proposal_generation"]', '["sql_tool","calculation_tool","rag_tool","document_tool"]'),
  ('sales_coach_agent', 'Sales Coach', 'sales', 'Rep performance analysis and personalized coaching', '["performance_analysis","coaching_plans","skill_development","win_loss_analysis"]', '["sql_tool","calculation_tool","rag_tool","api_tool"]'),
  ('ticket_resolver_agent', 'Ticket Resolver', 'support', 'Intelligent ticket triage and automated response drafting', '["ticket_classification","auto_response","escalation_routing","resolution_suggestion"]', '["sql_tool","rag_tool","api_tool","email_tool"]'),
  ('sentiment_analyst_agent', 'Sentiment Analyst', 'support', 'Real-time customer sentiment tracking and at-risk identification', '["sentiment_scoring","emotion_detection","trend_analysis","alert_generation"]', '["sql_tool","api_tool","rag_tool","webhook_tool"]'),
  ('knowledge_curator_agent', 'Knowledge Curator', 'support', 'Knowledge base management and article generation', '["article_generation","gap_analysis","content_optimization","faq_creation"]', '["sql_tool","document_tool","rag_tool","api_tool"]'),
  ('quality_analyst_agent', 'Quality Analyst', 'support', 'Support quality monitoring and agent coaching', '["quality_scoring","performance_monitoring","coaching_feedback","trend_reporting"]', '["sql_tool","calculation_tool","rag_tool","email_tool"]');
