#!/bin/bash
set -e

echo "=== NexaMind Platform Health Check ==="
echo ""

check_service() {
  local name=$1
  local url=$2
  local status
  status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
  if [ "$status" = "200" ]; then
    echo " $name: HEALTHY ($url)"
  else
    echo " $name: UNHEALTHY [$status] ($url)"
  fi
}

check_service "Agent Orchestrator"  "http://localhost:8000/health"
check_service "Auth Service"        "http://localhost:8001/health"
check_service "LLM Gateway"         "http://localhost:8002/api/v1/health"
check_service "RAG Service"         "http://localhost:8003/health"
check_service "ChromaDB"            "http://localhost:8010/api/v1/heartbeat"

echo ""
echo "=== Database & Redis ==="
pg_isready -h localhost -p 5432 -U nexamind && echo " PostgreSQL: HEALTHY" || echo " PostgreSQL: UNHEALTHY"
redis-cli -p 6379 ping > /dev/null 2>&1 && echo " Redis: HEALTHY" || echo " Redis: UNHEALTHY"
