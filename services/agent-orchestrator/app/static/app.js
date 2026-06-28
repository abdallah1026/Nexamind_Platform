/* app.js - NexaMind AI Platform Frontend Logic */

// Configurations & State
let config = {
    orchestratorUrl: window.location.origin,
    authUrl: window.location.origin,  // proxied through orchestrator to avoid CORS
    ragUrl: localStorage.getItem('setting_rag_url') || 'http://localhost:8003'
};

let state = {
    tenantId: localStorage.getItem('tenant_id') || '',
    tenantSlug: localStorage.getItem('tenant_slug') || '',
    tenantName: localStorage.getItem('tenant_name') || '',
    accessToken: localStorage.getItem('access_token') || '',
    activeView: 'dashboard',
    activeModule: 'all',
    selectedAgent: '',
    agents: [],
    uploadedDocs: JSON.parse(localStorage.getItem('uploaded_docs') || '[]')
};

// Static data mapping for agent details (to make the UI look rich and professional)
const AGENT_DETAILS = {
    // Finance
    "forecaster_agent": { displayName: "Revenue Forecaster", icon: "💵", tools: ["SQL Database", "Calculator", "ChromaDB RAG"], desc: "Analyzes historical transactions and predicts cash flows, revenue trends, and financial trends for the next 30/60/90 days." },
    "detector_agent": { displayName: "Anomaly Detector", icon: "⚠️", tools: ["SQL Database", "Isolation Forest", "Calculator"], desc: "Scans invoices, payments, and financial ledgers to flag outlier transactions and suspicious patterns." },
    "advisor_agent": { displayName: "Budget Advisor", icon: "💡", tools: ["SQL Database", "Calculator", "ChromaDB RAG"], desc: "Provides budget recommendation plans, expense savings strategies, and optimizations based on monthly burn rates." },
    "reporter_agent": { displayName: "Financial Reporter", icon: "📊", tools: ["SQL Database", "Excel Exporter"], desc: "Generates official balance sheets, income statements, and cash flow reports for audits and executive reviews." },
    
    // HR
    "talent_scout_agent": { displayName: "Talent Scout", icon: "🔍", tools: ["ChromaDB RAG", "Web Search", "SQL Database"], desc: "Screens candidate profiles, optimizes job descriptions, and matches skills with active open positions." },
    "retention_guard_agent": { displayName: "Retention Guard", icon: "🛡️", tools: ["SQL Database", "Attrition Model", "Calculator"], desc: "Identifies employees at high attrition risk using metrics like overtime, last promotion date, and manager feedback." },
    "growth_coach_agent": { displayName: "Growth Coach", icon: "🌱", tools: ["SQL Database", "ChromaDB RAG"], desc: "Generates personalized career development pathways, training schedules, and skill targets for employees." },
    "culture_builder_agent": { displayName: "Culture Builder", icon: "🤝", tools: ["SQL Database", "ChromaDB RAG"], desc: "Analyzes employee surveys, engagement metrics, and feedback to propose team building and workplace improvement activities." },

    // Operations
    "demand_planner_agent": { displayName: "Demand Planner", icon: "📦", tools: ["SQL Database", "Time Series Model", "Calculator"], desc: "Forecasts inventory demand levels, reducing holding costs and preventing stockouts." },
    "supply_optimizer_agent": { displayName: "Supply Optimizer", icon: "⛓️", tools: ["SQL Database", "Calculator", "ChromaDB RAG"], desc: "Analyzes supplier performance, lead times, and rates to optimize procurement decisions." },
    "logistics_coordinator_agent": { displayName: "Logistics Coordinator", icon: "🚚", tools: ["SQL Database", "Routing API", "Calculator"], desc: "Optimizes distribution routes, shipping schedules, and delivery pipelines to reduce transit overhead." },
    "quality_guardian_agent": { displayName: "Quality Guardian", icon: "🎖️", tools: ["SQL Database", "ChromaDB RAG"], desc: "Tracks manufacturing metrics, defect rates, and returns to identify quality control issues." },

    // Sales
    "revenue_forecaster_agent": { displayName: "Sales Forecaster", icon: "📈", tools: ["SQL Database", "Pipeline Model", "Calculator"], desc: "Forecasts sales pipelines, deal closures, and quota achievements per sales representative." },
    "churn_guardian_agent": { displayName: "Churn Guardian", icon: "🚨", tools: ["SQL Database", "Churn Classifier", "Calculator"], desc: "Analyzes customer interaction frequency, contract values, and usage behavior to flag churn warning signs." },
    "deal_strategist_agent": { displayName: "Deal Strategist", icon: "🎯", tools: ["SQL Database", "ChromaDB RAG"], desc: "Provides pricing optimization plans, competitor counter-arguments, and negotiation frameworks." },
    "sales_coach_agent": { displayName: "Sales Coach", icon: "🎓", tools: ["SQL Database", "ChromaDB RAG"], desc: "Analyzes closed deals to coach sales reps on effective strategies and pipeline hygiene." },

    // Support
    "ticket_resolver_agent": { displayName: "Ticket Resolver", icon: "🎫", tools: ["SQL Database", "ChromaDB RAG", "Email Client"], desc: "Provides automated drafts and draft responses for support tickets based on internal knowledge articles." },
    "sentiment_analyst_agent": { displayName: "Sentiment Analyst", icon: "🎭", tools: ["SQL Database", "NLP Classifier"], desc: "Tracks real-time customer sentiment trends on open support tickets and escalates frustrated users." },
    "knowledge_curator_agent": { displayName: "Knowledge Curator", icon: "📚", tools: ["ChromaDB RAG", "SQL Database"], desc: "Scours solved tickets to draft new internal documentation articles and Q&A entries." },
    "quality_analyst_agent": { displayName: "Quality Analyst", icon: "🔍", tools: ["SQL Database", "Calculator"], desc: "Audits support chat transcripts and agent response times to flag SLA violations." }
};

// Module Suggestions
const MODULE_SUGGESTIONS = {
    all: [
        "what are our biggest expenses and where can we save money?",
        "which employees are at risk of leaving?",
        "forecast our revenue for next quarter",
        "show me a list of outstanding support tickets with negative sentiment"
    ],
    finance: [
        "what are our biggest expenses and where can we save money?",
        "forecast our cash flow for the next 90 days",
        "show any recent budget anomalies or weird transactions",
        "generate a brief balance sheet report for this quarter"
    ],
    hr: [
        "which employees are at risk of leaving?",
        "recommend a skill growth pathway for a junior software engineer",
        "summarize our employee survey feedback and team sentiment",
        "find candidate resumes matching our open python developer position"
    ],
    operations: [
        "summarize our supply chain status and list potential bottlenecks",
        "which inventory items are at risk of stockouts next month?",
        "how can we optimize shipping routes for our west region distribution?",
        "calculate our overall defect rate for last week's production batch"
    ],
    sales: [
        "forecast our revenue for next quarter",
        "which of our premium accounts are showing churn risk signs?",
        "give me a negotiation plan for closing the ACME deal",
        "who are our top performing sales representatives this month?"
    ],
    support: [
        "show recent sentiment analysis of support tickets",
        "generate draft responses for ticket #1024",
        "what are our most common customer issues based on solved tickets?",
        "calculate our average SLA response time of support agents"
    ]
};

// Initialize Page
document.addEventListener("DOMContentLoaded", () => {
    initElements();
    bindEvents();
    checkAuth();
    loadSettingsInputs();
});

// Element References
let el = {};
function initElements() {
    el.authGateway = document.getElementById("auth-gateway");
    el.appWorkspace = document.getElementById("app-workspace");
    el.authStatus = document.getElementById("auth-status");
    
    // Forms
    el.formLogin = document.getElementById("form-login");
    el.formRegister = document.getElementById("form-register");
    el.formBypass = document.getElementById("form-bypass");
    el.authTabs = document.querySelectorAll(".auth-tab");
    
    // Sidebar details
    el.displayTenantName = document.getElementById("display-tenant-name");
    el.displayTenantId = document.getElementById("display-tenant-id");
    el.btnLogout = document.getElementById("btn-logout");
    el.navItems = document.querySelectorAll(".nav-item");
    el.contentViews = document.querySelectorAll(".content-view");
    
    // Dashboard
    el.dashboardActiveModule = document.getElementById("dashboard-active-module");
    el.servicesHealthDot = document.getElementById("services-health-dot");
    el.servicesHealthText = document.getElementById("services-health-text");
    el.servicesHealthDesc = document.getElementById("services-health-desc");
    el.seedHintId = document.getElementById("seed-hint-id");
    el.seedHintId2 = document.getElementById("seed-hint-id-2");
    
    // Chat
    el.moduleSelectors = document.querySelectorAll(".module-selector");
    el.chatAgentOverride = document.getElementById("chat-agent-override");
    el.chatActiveTitle = document.getElementById("chat-active-title");
    el.chatActiveDesc = document.getElementById("chat-active-desc");
    el.chatMessages = document.getElementById("chat-messages-container");
    el.chatSuggestions = document.getElementById("chat-suggestions-chips");
    el.chatTypingIndicator = document.getElementById("chat-typing-indicator");
    el.typingIndicatorText = document.getElementById("typing-indicator-text");
    el.chatInput = document.getElementById("chat-input");
    el.btnSendMessage = document.getElementById("btn-send-message");
    el.btnClearChat = document.getElementById("btn-clear-chat");
    
    // RAG
    el.ragDropZone = document.getElementById("rag-drop-zone");
    el.ragFileInput = document.getElementById("rag-file-input");
    el.ragCollection = document.getElementById("rag-collection");
    el.uploadProgressContainer = document.getElementById("upload-progress-container");
    el.uploadFilename = document.getElementById("upload-filename");
    el.uploadStatusBadge = document.getElementById("upload-status-badge");
    el.uploadProgressBar = document.getElementById("upload-progress-bar");
    el.uploadHistoryList = document.getElementById("upload-history-list");
    el.ragQueryInput = document.getElementById("rag-query-input");
    el.ragHybridSearch = document.getElementById("rag-hybrid-search");
    el.ragResultsCount = document.getElementById("rag-results-count");
    el.btnSearchRag = document.getElementById("btn-search-rag");
    el.searchResultsList = document.getElementById("search-results-list");
    
    // Registry
    el.agentsRegistryGrid = document.getElementById("agents-registry-grid");
    el.registryFilters = document.querySelectorAll(".registry-filter");
    
    // Settings
    el.settingOrchestratorUrl = document.getElementById("setting-orchestrator-url");
    el.settingAuthUrl = document.getElementById("setting-auth-url");
    el.settingRagUrl = document.getElementById("setting-rag-url");
    el.btnSaveSettings = document.getElementById("btn-save-settings");
    el.btnRunDiagnostics = document.getElementById("btn-run-diagnostics");
    el.diagOrchestrator = document.getElementById("diag-orchestrator");
    el.diagAuth = document.getElementById("diag-auth");
    el.diagRag = document.getElementById("diag-rag");
}

// Event Listeners
function bindEvents() {
    // Auth Tab toggling
    el.authTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            el.authTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            
            document.querySelectorAll(".auth-form").forEach(f => f.classList.remove("active"));
            document.getElementById(`form-${tab.dataset.tab}`).classList.add("active");
            el.authStatus.style.display = "none";
        });
    });

    // Form submits
    el.formLogin.addEventListener("submit", handleLogin);
    el.formRegister.addEventListener("submit", handleRegister);
    el.formBypass.addEventListener("submit", handleBypass);
    el.btnLogout.addEventListener("click", handleLogout);

    // Sidebar navigation
    el.navItems.forEach(item => {
        item.addEventListener("click", () => {
            el.navItems.forEach(i => i.classList.remove("active"));
            item.classList.add("active");
            switchView(item.dataset.view);
        });
    });

    // Tenant ID Copy
    el.displayTenantId.addEventListener("click", () => {
        navigator.clipboard.writeText(state.tenantId);
        const originalText = el.displayTenantId.innerText;
        el.displayTenantId.innerText = "COPIED!";
        setTimeout(() => {
            el.displayTenantId.innerText = originalText;
        }, 1500);
    });

    // Dashboard Quick Cards
    document.querySelectorAll(".clickable-card").forEach(card => {
        card.addEventListener("click", () => {
            const module = card.dataset.module;
            const prompt = card.dataset.prompt;
            
            // Switch to chat view
            el.navItems.forEach(i => i.classList.remove("active"));
            document.querySelector(".nav-item[data-view='chat']").classList.add("active");
            switchView("chat");
            
            // Activate module
            activateChatModule(module);
            
            // Fill prompt and submit
            el.chatInput.value = prompt;
            el.chatInput.focus();
        });
    });

    // Chat navigation and select overrides
    el.moduleSelectors.forEach(selector => {
        selector.addEventListener("click", () => {
            el.moduleSelectors.forEach(s => s.classList.remove("active"));
            selector.classList.add("active");
            activateChatModule(selector.dataset.module);
        });
    });

    el.chatAgentOverride.addEventListener("change", (e) => {
        state.selectedAgent = e.target.value;
    });

    // Send chat message
    el.btnSendMessage.addEventListener("click", sendChatMessage);
    el.chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    el.btnClearChat.addEventListener("click", () => {
        el.chatMessages.innerHTML = `
            <div class="message system-msg">
                <div class="msg-bubble">
                    Conversation cleared. Send a message to start a new analytical routing.
                </div>
            </div>`;
    });

    // RAG Drag & Drop
    el.ragDropZone.addEventListener("click", () => el.ragFileInput.click());
    el.ragFileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            uploadRagFile(e.target.files[0]);
        }
    });
    
    el.ragDropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        el.ragDropZone.classList.add("dragover");
    });
    el.ragDropZone.addEventListener("dragleave", () => {
        el.ragDropZone.classList.remove("dragover");
    });
    el.ragDropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        el.ragDropZone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            uploadRagFile(e.dataTransfer.files[0]);
        }
    });

    // RAG Search
    el.btnSearchRag.addEventListener("click", runRagSearch);
    el.ragQueryInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            runRagSearch();
        }
    });

    // Registry Filter
    el.registryFilters.forEach(filter => {
        filter.addEventListener("click", () => {
            el.registryFilters.forEach(f => f.classList.remove("active"));
            filter.classList.add("active");
            renderAgentsRegistry(filter.dataset.filter);
        });
    });

    // Settings save
    el.btnSaveSettings.addEventListener("click", () => {
        const oUrl = el.settingOrchestratorUrl.value.trim() || window.location.origin;
        const aUrl = el.settingAuthUrl.value.trim() || 'http://localhost:8001';
        const rUrl = el.settingRagUrl.value.trim() || 'http://localhost:8003';
        
        config.orchestratorUrl = oUrl;
        config.authUrl = aUrl;
        config.ragUrl = rUrl;
        
        localStorage.setItem('setting_auth_url', aUrl);
        localStorage.setItem('setting_rag_url', rUrl);
        
        showSettingsStatus("Settings saved successfully!", "success");
        runMicroservicesHealthCheck();
    });

    el.btnRunDiagnostics.addEventListener("click", runMicroservicesHealthCheck);
}

// Authentication Check
function checkAuth() {
    if (state.tenantId) {
        showAppWorkspace();
    } else {
        showAuthGateway();
    }
}

function showAuthGateway() {
    el.authGateway.classList.remove("hidden");
    el.appWorkspace.classList.add("hidden");
}

function showAppWorkspace() {
    el.authGateway.classList.add("hidden");
    el.appWorkspace.classList.remove("hidden");
    
    // Fill in tenant info
    el.displayTenantName.innerText = state.tenantName || state.tenantSlug || "Seeded Tenant";
    el.displayTenantId.innerText = state.tenantId;
    
    if (el.seedHintId) el.seedHintId.innerText = state.tenantId;
    if (el.seedHintId2) el.seedHintId2.innerText = state.tenantId;
    
    // Pre-load data from services
    fetchAgentsList();
    runMicroservicesHealthCheck();
    renderUploadedDocs();
    updateChatSuggestions();
}

function loadSettingsInputs() {
    el.settingOrchestratorUrl.value = config.orchestratorUrl;
    el.settingAuthUrl.value = config.authUrl;
    el.settingRagUrl.value = config.ragUrl;
}

// JWT Token Decoder
function decodeJwt(token) {
    try {
        const parts = token.split('.');
        if (parts.length !== 3) return null;
        const payloadDecoded = atob(parts[1]);
        return JSON.parse(payloadDecoded);
    } catch (e) {
        console.error("JWT decoding failed:", e);
        return null;
    }
}

// Auth Handlers
async function handleLogin(e) {
    e.preventDefault();
    showAuthStatus("Connecting...", "success");
    
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
    
    try {
        const res = await fetch(`${config.authUrl}/api/v1/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Authentication failed");
        }
        
        const data = await res.json();
        state.accessToken = data.access_token;
        
        // Decode token to extract tenant_id
        const decoded = decodeJwt(data.access_token);
        if (!decoded || !decoded.tenant_id) {
            throw new Error("Unable to read tenant ID from access token");
        }
        
        state.tenantId = decoded.tenant_id;
        state.tenantSlug = decoded.email.split('@')[1] || "company";
        state.tenantName = "Active Tenant";
        
        // Save state
        localStorage.setItem("access_token", state.accessToken);
        localStorage.setItem("tenant_id", state.tenantId);
        localStorage.setItem("tenant_slug", state.tenantSlug);
        localStorage.setItem("tenant_name", state.tenantName);
        
        showAuthStatus("Authentication successful! Loading workspace...", "success");
        setTimeout(showAppWorkspace, 1000);
        
    } catch (err) {
        showAuthStatus(err.message, "error");
    }
}

async function handleRegister(e) {
    e.preventDefault();
    showAuthStatus("Creating tenant workspace...", "success");
    
    const company = document.getElementById("reg-company").value;
    const slug = document.getElementById("reg-slug").value;
    const name = document.getElementById("reg-name").value;
    const email = document.getElementById("reg-email").value;
    const password = document.getElementById("reg-password").value;
    
    try {
        const res = await fetch(`${config.authUrl}/api/v1/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: company,
                slug: slug,
                admin_email: email,
                admin_password: password,
                admin_full_name: name
            })
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Registration failed");
        }
        
        const data = await res.json();
        
        state.accessToken = data.access_token;
        state.tenantId = data.tenant.id;
        state.tenantSlug = data.tenant.slug;
        state.tenantName = data.tenant.name;
        
        // Save
        localStorage.setItem("access_token", state.accessToken);
        localStorage.setItem("tenant_id", state.tenantId);
        localStorage.setItem("tenant_slug", state.tenantSlug);
        localStorage.setItem("tenant_name", state.tenantName);
        
        showAuthStatus("Tenant registered! Workspace ready.", "success");
        setTimeout(showAppWorkspace, 1200);
        
    } catch (err) {
        // Pydantic returns [{msg, loc, ...}] — parse into a readable string
        let errMsg = err.message;
        try {
            const parsed = JSON.parse(err.message);
            if (Array.isArray(parsed)) {
                errMsg = parsed.map(e => `${e.loc ? e.loc.join('.') + ': ' : ''}${e.msg}`).join(' | ');
            }
        } catch (_) {}
        showAuthStatus(errMsg, "error");
    }
}

function handleBypass(e) {
    e.preventDefault();
    const bypassId = document.getElementById("bypass-tenant-id").value.trim();
    if (!bypassId) {
        showAuthStatus("Please enter a valid Tenant UUID", "error");
        return;
    }
    
    state.tenantId = bypassId;
    state.tenantSlug = "bypassed";
    state.tenantName = "Developer Workspace";
    state.accessToken = "bypass-token";
    
    localStorage.setItem("tenant_id", state.tenantId);
    localStorage.setItem("tenant_slug", state.tenantSlug);
    localStorage.setItem("tenant_name", state.tenantName);
    localStorage.setItem("access_token", state.accessToken);
    
    showAuthStatus("Access granted. Loading seeded environment...", "success");
    setTimeout(showAppWorkspace, 1000);
}

function handleLogout() {
    state.tenantId = '';
    state.tenantSlug = '';
    state.tenantName = '';
    state.accessToken = '';
    
    localStorage.removeItem("tenant_id");
    localStorage.removeItem("tenant_slug");
    localStorage.removeItem("tenant_name");
    localStorage.removeItem("access_token");
    
    showAuthGateway();
}

function showAuthStatus(msg, type) {
    el.authStatus.innerText = msg;
    el.authStatus.className = `auth-status-msg ${type}`;
}

// Switch Tab View
function switchView(viewId) {
    state.activeView = viewId;
    el.contentViews.forEach(view => {
        view.classList.remove("active");
    });
    document.getElementById(`view-${viewId}`).classList.add("active");
    
    // Side effects on switching views
    if (viewId === 'dashboard') {
        el.dashboardActiveModule.innerText = state.activeModule === 'all' ? 'All-Router' : state.activeModule.toUpperCase();
    } else if (viewId === 'chat') {
        updateChatSuggestions();
        el.chatInput.focus();
    } else if (viewId === 'agents') {
        renderAgentsRegistry("all");
    }
}

// Fetch Agents List
async function fetchAgentsList() {
    try {
        const res = await fetch(`${config.orchestratorUrl}/api/v1/agents`);
        if (!res.ok) throw new Error("Could not retrieve agent metadata");
        const data = await res.json();
        
        state.agents = data.agents || [];
        populateOverrideDropdown();
        renderAgentsRegistry("all");
    } catch (e) {
        console.error("Agents fetch error:", e);
    }
}

// Chat UI Controls
function activateChatModule(moduleCode) {
    state.activeModule = moduleCode;
    
    // UI titles and descriptors
    if (moduleCode === 'all') {
        el.chatActiveTitle.innerText = "General Orchestrator Router";
        el.chatActiveDesc.innerText = "Questions are automatically classified and routed to the corresponding department agent.";
    } else {
        el.chatActiveTitle.innerText = `${moduleCode.toUpperCase()} Department Agent Hub`;
        el.chatActiveDesc.innerText = `Queries are locked to the ${moduleCode} department module.`;
    }
    
    populateOverrideDropdown();
    updateChatSuggestions();
}

function populateOverrideDropdown() {
    // Clear select
    el.chatAgentOverride.innerHTML = `<option value="">Auto-Route (Router Agent)</option>`;
    
    // Filter agents by active module
    const filtered = state.agents.filter(agent => {
        return state.activeModule === 'all' || agent.module === state.activeModule;
    });
    
    filtered.forEach(agent => {
        const staticDetails = AGENT_DETAILS[agent.name] || { displayName: agent.name };
        const option = document.createElement("option");
        option.value = agent.name;
        option.innerText = staticDetails.displayName;
        el.chatAgentOverride.appendChild(option);
    });
    
    state.selectedAgent = '';
}

function updateChatSuggestions() {
    el.chatSuggestions.innerHTML = '';
    const prompts = MODULE_SUGGESTIONS[state.activeModule] || MODULE_SUGGESTIONS.all;
    
    prompts.forEach(p => {
        const chip = document.createElement("div");
        chip.className = "suggestion-chip";
        chip.innerText = p;
        chip.addEventListener("click", () => {
            el.chatInput.value = p;
            el.chatInput.focus();
        });
        el.chatSuggestions.appendChild(chip);
    });
}

// Send Chat Message
async function sendChatMessage() {
    const text = el.chatInput.value.trim();
    if (!text) return;
    
    // User message bubble
    appendMessage(text, "user");
    el.chatInput.value = '';
    el.chatInput.style.height = 'auto'; // Reset grow
    
    // Set loading indicator
    el.chatTypingIndicator.classList.remove("hidden");
    if (state.selectedAgent) {
        const agentName = AGENT_DETAILS[state.selectedAgent]?.displayName || state.selectedAgent;
        el.typingIndicatorText.innerText = `Calling specialized ${agentName}...`;
    } else {
        el.typingIndicatorText.innerText = "Orchestrator routing message to correct agent...";
    }
    
    scrollToBottom(el.chatMessages);
    
    try {
        const body = {
            message: text,
            agent: state.selectedAgent || null,
            module: state.activeModule === 'all' ? null : state.activeModule
        };
        
        const res = await fetch(`${config.orchestratorUrl}/api/v1/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Tenant-Id": state.tenantId
            },
            body: JSON.stringify(body)
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Error communicating with agent orchestrator");
        }
        
        const data = await res.json();
        
        // Remove typing indicator and render agent reply
        el.chatTypingIndicator.classList.add("hidden");
        appendMessage(data.response, "agent", data.agent, data.module, data.metadata);
        
    } catch (err) {
        el.chatTypingIndicator.classList.add("hidden");
        appendMessage(`System Error: ${err.message}. Make sure the orchestrator service is running and database is seeded.`, "system");
    }
    
    scrollToBottom(el.chatMessages);
}

function appendMessage(text, type, agentName = '', moduleName = '', metadata = null) {
    const msg = document.createElement("div");
    msg.className = `message ${type}-msg`;
    
    if (type === 'agent') {
        const details = AGENT_DETAILS[agentName] || { displayName: agentName, icon: "🤖" };
        const displayMod = moduleName ? moduleName.toUpperCase() : "AGENT";
        
        msg.innerHTML = `
            <div class="msg-header">
                <span>${details.icon} ${details.displayName}</span>
                <span class="badge badge-primary">${displayMod}</span>
            </div>
            <div class="msg-bubble">${text}</div>
        `;
        
        // If metadata returned, append execution summary card
        if (metadata && Object.keys(metadata).length > 0) {
            const metaCard = document.createElement("div");
            metaCard.className = "metadata-card";
            
            const cardId = 'meta_' + Math.random().toString(36).substr(2, 9);
            
            let gridRows = '';
            for (const [key, val] of Object.entries(metadata)) {
                let formattedVal = typeof val === 'object' ? JSON.stringify(val) : val;
                gridRows += `
                    <div class="meta-label">${key}:</div>
                    <div class="meta-val">${formattedVal}</div>
                `;
            }
            
            metaCard.innerHTML = `
                <button class="metadata-toggle" onclick="toggleMetadata('${cardId}')">
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points='6 9 12 15 18 9'></polyline></svg>
                    <span>Execution Metadata</span>
                </button>
                <div id="${cardId}" class="metadata-content">
                    <div class="metadata-grid">
                        ${gridRows}
                    </div>
                </div>
            `;
            msg.appendChild(metaCard);
        }
        
    } else if (type === 'user') {
        msg.innerHTML = `
            <div class="msg-header">You</div>
            <div class="msg-bubble">${text}</div>
        `;
    } else {
        // System / error message
        msg.innerHTML = `<div class="msg-bubble">${text}</div>`;
    }
    
    el.chatMessages.appendChild(msg);
}

// Global function to toggle metadata panel
window.toggleMetadata = function(id) {
    const elMeta = document.getElementById(id);
    if (elMeta) {
        elMeta.classList.toggle("active");
    }
};

// RAG Handlers
async function uploadRagFile(file) {
    el.uploadProgressContainer.classList.remove("hidden");
    el.uploadFilename.innerText = file.name;
    el.uploadStatusBadge.innerText = "Uploading...";
    el.uploadStatusBadge.className = "badge badge-warning";
    el.uploadProgressBar.style.width = "20%";
    
    const collection = el.ragCollection.value.trim() || "default";
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        el.uploadProgressBar.style.width = "50%";
        el.uploadStatusBadge.innerText = "Indexing in ChromaDB...";
        
        const res = await fetch(`${config.ragUrl}/api/v1/documents/upload?collection=${collection}`, {
            method: "POST",
            headers: {
                "X-Tenant-Id": state.tenantId
            },
            body: formData
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "RAG upload failed");
        }
        
        const data = await res.json();
        el.uploadProgressBar.style.width = "100%";
        el.uploadStatusBadge.innerText = "SUCCESS";
        el.uploadStatusBadge.className = "badge badge-success";
        
        // Add to history
        state.uploadedDocs.unshift({
            id: data.doc_id,
            filename: data.filename,
            chunks: data.chunks,
            collection: data.collection,
            timestamp: new Date().toLocaleTimeString()
        });
        localStorage.setItem('uploaded_docs', JSON.stringify(state.uploadedDocs));
        renderUploadedDocs();
        
        setTimeout(() => {
            el.uploadProgressContainer.classList.add("hidden");
        }, 3000);
        
    } catch (e) {
        el.uploadProgressBar.style.width = "100%";
        el.uploadProgressBar.style.backgroundColor = "var(--color-danger)";
        el.uploadStatusBadge.innerText = "FAILED";
        el.uploadStatusBadge.className = "badge badge-danger";
        console.error("RAG upload error:", e);
    }
}

function renderUploadedDocs() {
    el.uploadHistoryList.innerHTML = '';
    if (state.uploadedDocs.length === 0) {
        el.uploadHistoryList.innerHTML = `<div class="no-data">No documents indexed in this session.</div>`;
        return;
    }
    
    state.uploadedDocs.forEach((doc, idx) => {
        const item = document.createElement("div");
        item.className = "history-item";
        item.innerHTML = `
            <div class="history-item-details">
                <span class="doc-name">${doc.filename}</span>
                <span class="doc-meta">${doc.chunks} chunks • Collection: ${doc.collection}</span>
            </div>
            <button class="btn-delete-doc" onclick="deleteIndexedDocument('${doc.id}', ${idx})" title="Delete index">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
        `;
        el.uploadHistoryList.appendChild(item);
    });
}

window.deleteIndexedDocument = async function(docId, idx) {
    if (!confirm("Are you sure you want to remove this document index from ChromaDB?")) return;
    
    try {
        const res = await fetch(`${config.ragUrl}/api/v1/documents/${docId}`, {
            method: "DELETE",
            headers: {
                "X-Tenant-Id": state.tenantId
            }
        });
        
        if (!res.ok) throw new Error("Could not delete from vector store");
        
        state.uploadedDocs.splice(idx, 1);
        localStorage.setItem('uploaded_docs', JSON.stringify(state.uploadedDocs));
        renderUploadedDocs();
    } catch (e) {
        alert("Delete error: " + e.message);
    }
};

async function runRagSearch() {
    const query = el.ragQueryInput.value.trim();
    if (!query) return;
    
    el.searchResultsList.innerHTML = `<div class="typing-indicator"><div class="dot"></div><div class="dot"></div><div class="dot"></div><span>Querying local embeddings...</span></div>`;
    
    try {
        const body = {
            query: query,
            collection: el.ragCollection.value.trim() || "default",
            n_results: parseInt(el.ragResultsCount.value) || 3,
            use_hybrid: el.ragHybridSearch.checked
        };
        
        const res = await fetch(`${config.ragUrl}/api/v1/search`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Tenant-Id": state.tenantId
            },
            body: JSON.stringify(body)
        });
        
        if (!res.ok) throw new Error("Vector search query failed");
        const results = await res.json();
        
        el.searchResultsList.innerHTML = '';
        if (results.length === 0) {
            el.searchResultsList.innerHTML = `<div class="no-data">No relevant matches found in vector storage.</div>`;
            return;
        }
        
        results.forEach(match => {
            const pct = Math.round((match.score || 0) * 100);
            const card = document.createElement("div");
            card.className = "result-card";
            card.innerHTML = `
                <div class="result-header">
                    <span>Source: ${match.metadata.filename || 'Unknown'} (Chunk ${match.metadata.chunk_index || 0})</span>
                    <span class="result-score badge badge-success">${pct}% Match</span>
                </div>
                <div class="result-text">${match.content}</div>
            `;
            el.searchResultsList.appendChild(card);
        });
        
    } catch (e) {
        el.searchResultsList.innerHTML = `<div class="no-data" style="color: var(--color-danger)">Search Error: ${e.message}</div>`;
    }
}

// Render Agents Grid Registry
function renderAgentsRegistry(filterModule) {
    if (!el.agentsRegistryGrid) return;
    el.agentsRegistryGrid.innerHTML = '';
    
    // If no agents loaded, render a loading alert
    if (state.agents.length === 0) {
        el.agentsRegistryGrid.innerHTML = `<div class="no-data" style="grid-column: 1 / -1">No agents meta loaded yet. Please verify that the agent orchestrator is running and check settings.</div>`;
        return;
    }
    
    const filtered = state.agents.filter(agent => {
        return filterModule === 'all' || agent.module === filterModule;
    });
    
    filtered.forEach(agent => {
        const details = AGENT_DETAILS[agent.name] || {
            displayName: agent.name,
            icon: "🤖",
            desc: "Custom department agent for multi-agent calculations.",
            tools: ["SQL Database"]
        };
        
        const card = document.createElement("div");
        card.className = `agent-card glass-panel ${agent.module}-agent`;
        
        let toolsHTML = '';
        details.tools.forEach(t => {
            toolsHTML += `<span class="tool-badge">${t}</span>`;
        });
        
        card.innerHTML = `
            <div class="agent-card-header">
                <div class="agent-card-icon">${details.icon}</div>
                <div class="agent-card-title">
                    <h3>${details.displayName}</h3>
                    <span class="agent-module">${agent.module}</span>
                </div>
            </div>
            <p class="agent-card-desc">${details.desc}</p>
            <div class="agent-card-tools">
                <span>Tools Available:</span>
                <div class="tools-list">${toolsHTML}</div>
            </div>
            <div class="agent-card-footer">
                <span class="badge badge-success">ACTIVE</span>
                <button class="btn btn-primary btn-sm" onclick="quickInvokeAgent('${agent.name}', '${agent.module}')">Invoke</button>
            </div>
        `;
        el.agentsRegistryGrid.appendChild(card);
    });
}

window.quickInvokeAgent = function(agentName, agentModule) {
    // Navigate to Chat
    el.navItems.forEach(i => i.classList.remove("active"));
    document.querySelector(".nav-item[data-view='chat']").classList.add("active");
    switchView("chat");
    
    // Choose module
    activateChatModule(agentModule);
    
    // Select agent override
    el.chatAgentOverride.value = agentName;
    state.selectedAgent = agentName;
    
    // Fill chat prompt suggestion based on agent name if it exists in prompts
    const suggestions = MODULE_SUGGESTIONS[agentModule] || [];
    el.chatInput.value = suggestions[0] || '';
    el.chatInput.focus();
};

// Health Check Diagnostics
async function runMicroservicesHealthCheck() {
    let orchestratorOk = false;
    let authOk = false;
    let ragOk = false;
    
    // Orchestrator
    try {
        const res = await fetch(`${config.orchestratorUrl}/health`);
        const data = await res.json();
        if (data.status === 'ok') orchestratorOk = true;
    } catch (e) {}
    updateDiagState(el.diagOrchestrator, orchestratorOk);
    
    // Auth
    try {
        const res = await fetch(`${config.authUrl}/health`);
        const data = await res.json();
        if (data.status === 'healthy') authOk = true;
    } catch (e) {}
    updateDiagState(el.diagAuth, authOk);
    
    // RAG
    try {
        const res = await fetch(`${config.ragUrl}/health`);
        const data = await res.json();
        if (data.status === 'healthy') ragOk = true;
    } catch (e) {}
    updateDiagState(el.diagRag, ragOk);
    
    // Update dashboard indicator
    if (orchestratorOk && authOk && ragOk) {
        el.servicesHealthDot.className = "pulse-indicator online";
        el.servicesHealthText.innerText = "Online";
        el.servicesHealthDesc.innerText = "All backend services healthy";
    } else {
        el.servicesHealthDot.className = "pulse-indicator offline";
        el.servicesHealthText.innerText = "Degraded";
        el.servicesHealthDesc.innerText = "Some services could not be reached";
    }
}

function updateDiagState(element, isOk) {
    if (!element) return;
    if (isOk) {
        element.innerText = "HEALTHY";
        element.className = "diag-status status-online";
    } else {
        element.innerText = "UNREACHABLE";
        element.className = "diag-status status-offline";
    }
}

function showSettingsStatus(msg, type) {
    const statusDiv = document.createElement("div");
    statusDiv.style.marginTop = "15px";
    statusDiv.className = `auth-status-msg ${type}`;
    statusDiv.innerText = msg;
    statusDiv.style.display = "block";
    
    const settingsCard = el.btnSaveSettings.parentElement;
    const existingStatus = settingsCard.querySelector(".auth-status-msg");
    if (existingStatus) settingsCard.removeChild(existingStatus);
    
    settingsCard.appendChild(statusDiv);
    
    setTimeout(() => {
        statusDiv.style.display = "none";
        settingsCard.removeChild(statusDiv);
    }, 3000);
}

// Helpers
function scrollToBottom(container) {
    container.scrollTop = container.scrollHeight;
}

// Textarea auto grow
if (el.chatInput) {
    el.chatInput.addEventListener("input", function() {
        this.style.height = "auto";
        this.style.height = (this.scrollHeight) + "px";
    });
}
