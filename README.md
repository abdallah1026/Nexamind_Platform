# NexaMind AI Platform

Graduation project for college! This is a multi-agent AI system we built for business stuff.

> Check out `docs/GRADUATION_PROJECT_REPORT.md` if u want to see the full report, it has all our database schemas and sequence diagrams and stuff for the thesis defense.

## What is this?
Basically you just type a question like "who is going to quit our company?" and the system picks the right AI agent to look into our database and answer it. 

We made 20 different agents:
- Finance agents (forecasting, budgets)
- HR agents (retention, culture)
- Ops agents (supply chain, logistics)
- Sales agents (revenue, churn)
- Support agents (tickets)

## Architecture stuff
It works like this:
User -> Orchestrator -> Router (picks the agent) -> Agent -> LLM Gateway -> Groq
Everything is saved in PostgreSQL and we use Redis for cache.
**Note:** We use Groq for the LLMs because it's fast! We don't use Anthropic or OpenAI. 

## How to run the project
You just need Docker installed and a Groq API key.

1. First copy the env file so u can add ur keys
```bash
cp .env.example .env
```
Open `.env` and put your Groq API key in there (ignore the anthropic/openai stuff if its still there).

2. Build it using docker
```bash
docker compose -f docker/docker-compose.yml up --build -d
```

3. Make sure everything started up ok:
```bash
bash scripts/health_check.sh
```

4. Create a test company so u can login:
```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "slug": "testco",
    "admin_email": "admin@test.com",
    "admin_password": "Password123!",
    "admin_full_name": "Admin"
  }'
```

5. Grab the tenant id from the response above and put it in your terminal, then run the python scripts to fill the database with fake data so the agents have something to work with:
```bash
export TENANT_ID=<paste-the-id-here>
python3 scripts/seed_synthetic_data.py --tenant-id $TENANT_ID
python3 scripts/seed_prompts.py --tenant-id $TENANT_ID
```

6. Ask a question!
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: $TENANT_ID" \
  -d '{"message": "what are our biggest expenses?"}'
```

## Stuff we used
- FastAPI
- PostgreSQL
- ChromaDB
- Redis
- Groq (again, no openai or anthropic lol)
- Docker

## Bugs/Issues we know about
- routing sometimes gets confused if u ask weird questions
- no real logging, mostly print statements haha
- tests arent fully done yet

This was a fun grad project to work on! Hope it works on your machine.
