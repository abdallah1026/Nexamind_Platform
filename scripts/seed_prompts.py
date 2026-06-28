
"""Seed knowledge base with initial prompt documentation"""
import asyncio
import asyncpg
import argparse

KB_ARTICLES = [
    {"title": "Financial Forecasting Best Practices", "category": "Finance", "content": """
# Financial Forecasting Best Practices

## Methodology Selection
- **Short-term (< 3 months)**: Exponential smoothing (ARIMA), weighted moving average
- **Medium-term (3-12 months)**: Regression with seasonal decomposition
- **Long-term (> 12 months)**: Scenario planning with Monte Carlo simulation

## Data Requirements
Minimum 24 months of historical data for reliable seasonality detection.
Identify and exclude one-time events (M&A, disasters, COVID) from baseline.

## Confidence Intervals
- 80% CI: Normal business planning
- 95% CI: Risk management and stress testing
- Always show point estimate + range, never just a single number

## Common Pitfalls
1. Anchoring bias: Don't start from last year's number
2. Hockey stick bias: Growth cannot exceed market size
3. Ignoring lead times: Cash lags revenue by 30-90 days
"""},
    {"title": "HR Attrition Risk Framework", "category": "HR", "content": """
# Employee Attrition Risk Framework

## Risk Factor Weighting
| Factor | Weight | High Risk Signal |
|--------|--------|-----------------|
| Below-market compensation | 25% | < 85th percentile |
| Tenure milestone approaching | 20% | 1yr, 2yr, 5yr anniversaries |
| Manager change in past 6 months | 15% | Especially downward change |
| Promotion velocity | 15% | < 1 promotion per 3 years |
| Engagement score | 15% | < 3.5/5.0 |
| Peer network dissolution | 10% | > 30% of close peers departed |

## Intervention Playbook
**Score 61-80 (High)**: Manager 1:1, compensation review, development plan
**Score 81-100 (Critical)**: Skip-level meeting within 1 week, retention package consideration
"""},
    {"title": "Demand Planning Methodology", "category": "Operations", "content": """
# Demand Planning Methodology

## Forecasting Hierarchy
1. Statistical baseline (bottom-up by SKU)
2. Commercial adjustment (sales team input)
3. Market intelligence adjustment
4. Final consensus forecast

## Safety Stock Formula
SS = Z × σ_demand × √(lead_time)
- Z = 1.65 for 95% service level
- Z = 2.05 for 98% service level

## Reorder Point Formula
ROP = Average_Daily_Demand × Lead_Time + Safety_Stock

## ABC-XYZ Classification
- A items: Top 20% by value — weekly review
- B items: Next 30% — bi-weekly review  
- C items: Bottom 50% — monthly review
"""},
    {"title": "Customer Churn Prevention Playbook", "category": "Sales", "content": """
# Customer Churn Prevention Playbook

## Early Warning System
Monitor weekly: login frequency, feature adoption, support ticket volume, NPS trend

## Intervention Tiers
**Score 51-75 (At Risk)**:
- CS check-in call within 1 week
- Usage review and QBR scheduling
- Product adoption workshop offer

**Score 76-100 (Critical)**:
- Executive escalation within 24 hours
- Executive sponsor mapping and outreach
- Custom success plan with 30/60/90 milestones
- Consider commercial flexibility (multi-year discount)

## Revenue Recovery Formula
Expected_Retention_Value = Annual_Revenue × (1 - Churn_Probability) × Avg_Customer_Lifetime
"""},
    {"title": "Support Ticket Triage Guide", "category": "Support", "content": """
# Support Ticket Triage Guide

## Priority Matrix
| Impact | Urgency | Priority |
|--------|---------|----------|
| Production down | Immediate | P1 - 1hr SLA |
| Core feature broken | High | P2 - 4hr SLA |
| Feature degraded | Medium | P3 - 24hr SLA |
| Question/Enhancement | Low | P4 - 72hr SLA |

## First Response Template
1. Acknowledge the specific issue (don't be generic)
2. Set clear expectations for timeline
3. Provide immediate workaround if available
4. Assign ticket owner and escalation path

## Escalation Triggers
- Customer mentions legal/SLA breach
- Issue affects > 10 users
- Revenue impact > $10K/day
- VIP/Enterprise customer
"""},
]

async def seed_articles(conn, tenant_id: str):
    for article in KB_ARTICLES:
        await conn.execute(
            """INSERT INTO knowledge_articles (id, tenant_id, title, content, category, status, author)
               VALUES (gen_random_uuid(), $1, $2, $3, $4, 'published', 'NexaMind System')
               ON CONFLICT DO NOTHING""",
            tenant_id, article["title"], article["content"], article["category"]
        )
    print(f"✅ Seeded {len(KB_ARTICLES)} knowledge base articles")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--db-url", default="postgresql://nexamind:nexamind_secret@localhost:5432/nexamind")
    args = parser.parse_args()
    
    conn = await asyncpg.connect(args.db_url)
    try:
        await seed_articles(conn, args.tenant_id)
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
