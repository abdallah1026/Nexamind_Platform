#!/usr/bin/env python3
"""
Seed synthetic data for NexaMind AI Platform
Usage: python seed_synthetic_data.py --tenant-id <uuid> --db-url <url>
"""
import asyncio
import random
import uuid
from datetime import datetime, timedelta, date
from decimal import Decimal
import argparse
import sys

try:
    import asyncpg
except ImportError:
    print("Install asyncpg: pip install asyncpg")
    sys.exit(1)

FINANCE_CATEGORIES = ["Revenue", "SaaS", "Professional Services", "Hardware",
                       "Marketing", "Engineering", "Sales", "G&A", "R&D", "COGS"]
DEPARTMENTS = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations", "Product", "Support"]
TICKET_CATEGORIES = ["Technical Issue", "Billing", "Feature Request", "Account Access", "Performance", "Integration"]
COUNTERPARTIES = ["Acme Corp", "TechVision Ltd", "GlobalSys Inc", "DataPro LLC", "CloudServ", "NetBridge"]

async def seed_data(conn, tenant_id: str):
    print(f"Seeding data for tenant: {tenant_id}")
    
    # ---- Financial Transactions ----
    print("  Seeding financial transactions...")
    txns = []
    base_date = date.today() - timedelta(days=365)
    for i in range(500):
        txn_date = base_date + timedelta(days=random.randint(0, 365))
        is_revenue = random.random() > 0.4
        amount = random.uniform(500, 50000) if is_revenue else -random.uniform(100, 20000)
        txns.append((
            str(uuid.uuid4()), tenant_id, txn_date, round(amount, 2),
            "USD", random.choice(FINANCE_CATEGORIES),
            f"Transaction {i+1}", random.choice(COUNTERPARTIES)
        ))
    
    await conn.executemany(
        """INSERT INTO financial_transactions 
           (id, tenant_id, transaction_date, amount, currency, category, description, counterparty)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8)""",
        txns
    )
    print(f"  ✓ {len(txns)} transactions")

    # ---- Employees ----
    print("  Seeding employees...")
    employees = []
    for i in range(50):
        hire_date = date.today() - timedelta(days=random.randint(90, 1800))
        employees.append((
            str(uuid.uuid4()), tenant_id, f"EMP{1000+i}",
            f"Employee {i+1}", f"emp{i+1}@company.com",
            random.choice(DEPARTMENTS), f"{'Senior ' if i % 3 == 0 else ''}{'Engineer' if i % 2 == 0 else 'Manager'}",
            round(random.uniform(60000, 180000), 2),
            round(random.uniform(2.5, 5.0), 1), round(random.uniform(3.0, 5.0), 1),
            hire_date
        ))
    
    await conn.executemany(
        """INSERT INTO employees 
           (id, tenant_id, employee_id, full_name, email, department, job_title, 
            salary, performance_score, engagement_score, hire_date)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
           ON CONFLICT DO NOTHING""",
        employees
    )
    emp_ids = [e[0] for e in employees]
    print(f"  ✓ {len(employees)} employees")

    # ---- Attrition Risks ----
    print("  Seeding attrition risks...")
    risks = []
    for emp_id in random.sample(emp_ids, min(15, len(emp_ids))):
        score = random.uniform(30, 95)
        risks.append((
            str(uuid.uuid4()), tenant_id, emp_id, round(score, 1),
            "high" if score > 70 else "medium" if score > 50 else "low"
        ))
    await conn.executemany(
        "INSERT INTO attrition_risks (id, tenant_id, employee_id, risk_score, risk_level) VALUES ($1,$2,$3,$4,$5)",
        risks
    )
    print(f"  ✓ {len(risks)} attrition risk records")

    # ---- Inventory Items ----
    print("  Seeding inventory...")
    skus = []
    for i in range(30):
        skus.append((
            str(uuid.uuid4()), tenant_id, f"SKU-{1000+i}",
            f"Product {i+1}", random.choice(["Electronics", "Software", "Hardware", "Services"]),
            round(random.uniform(10, 500), 2),
            random.randint(50, 500), random.randint(20, 100),
            random.randint(5, 30)
        ))
    await conn.executemany(
        """INSERT INTO inventory_items 
           (id, tenant_id, sku, name, category, unit_cost, current_stock, reorder_point, lead_time_days)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
           ON CONFLICT DO NOTHING""",
        skus
    )
    print(f"  ✓ {len(skus)} inventory items")

    # ---- Suppliers ----
    print("  Seeding suppliers...")
    suppliers = []
    for i, name in enumerate(["Alpha Supplies", "Beta Components", "Gamma Tech", "Delta Materials", "Epsilon Systems"]):
        suppliers.append((
            str(uuid.uuid4()), tenant_id, name,
            f"contact@supplier{i+1}.com",
            round(random.uniform(0.6, 0.98), 2),
            random.randint(7, 45), "Net 30"
        ))
    await conn.executemany(
        """INSERT INTO suppliers 
           (id, tenant_id, name, contact_email, reliability_score, lead_time_days, payment_terms)
           VALUES ($1,$2,$3,$4,$5,$6,$7)""",
        suppliers
    )
    print(f"  ✓ {len(suppliers)} suppliers")

    # ---- Sales Deals ----
    print("  Seeding sales pipeline...")
    stages = ["Prospecting", "Qualification", "Demo", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
    reps = ["Alice Smith", "Bob Johnson", "Carol Davis", "David Wilson", "Emma Brown"]
    deals = []
    for i in range(40):
        stage = random.choice(stages)
        prob = {"Prospecting": 10, "Qualification": 25, "Demo": 40, "Proposal": 60,
                "Negotiation": 75, "Closed Won": 100, "Closed Lost": 0}.get(stage, 50)
        deals.append((
            str(uuid.uuid4()), tenant_id, f"Deal-{2024000+i}",
            random.choice(COUNTERPARTIES), stage,
            round(random.uniform(10000, 250000), 2), prob,
            date.today() + timedelta(days=random.randint(0, 120)),
            random.choice(reps),
            "open" if stage not in ["Closed Won", "Closed Lost"] else stage.lower().replace(" ", "_")
        ))
    await conn.executemany(
        """INSERT INTO deals 
           (id, tenant_id, deal_name, customer_name, stage, amount, probability,
            expected_close_date, owner, status)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)""",
        deals
    )
    print(f"  ✓ {len(deals)} deals")

    # ---- Customer Churn Risks ----
    print("  Seeding churn risks...")
    churn_risks = []
    customers = [f"Customer {i}" for i in range(1, 16)]
    for customer in customers:
        score = random.uniform(10, 90)
        churn_risks.append((
            str(uuid.uuid4()), tenant_id, f"CUST-{random.randint(1000,9999)}",
            customer, round(score, 1),
            "critical" if score > 75 else "high" if score > 50 else "medium",
            round(random.uniform(10000, 200000), 2)
        ))
    await conn.executemany(
        """INSERT INTO customer_churn_risks 
           (id, tenant_id, customer_id, customer_name, churn_score, risk_level, annual_revenue_at_risk)
           VALUES ($1,$2,$3,$4,$5,$6,$7)""",
        churn_risks
    )
    print(f"  ✓ {len(churn_risks)} churn risk records")

    # ---- Support Tickets ----
    print("  Seeding support tickets...")
    priorities = ["P1", "P2", "P3", "P4"]
    statuses = ["open", "in_progress", "resolved", "closed"]
    sentiments = ["positive", "neutral", "negative"]
    tickets = []
    for i in range(60):
        created = datetime.now() - timedelta(days=random.randint(0, 90))
        tickets.append((
            str(uuid.uuid4()), tenant_id, f"TKT-{20240000+i}",
            random.choice(COUNTERPARTIES), f"Issue with {random.choice(TICKET_CATEGORIES)}",
            f"Customer reported issue with {random.choice(TICKET_CATEGORIES).lower()}. Requires investigation.",
            random.choice(TICKET_CATEGORIES), random.choice(priorities),
            random.choice(statuses), random.choice(sentiments),
            round(random.uniform(0.1, 1.0), 2), created
        ))
    await conn.executemany(
        """INSERT INTO support_tickets 
           (id, tenant_id, ticket_number, customer_name, subject, description, 
            category, priority, status, sentiment, sentiment_score, created_at)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
           ON CONFLICT (ticket_number) DO NOTHING""",
        tickets
    )
    print(f"  ✓ {len(tickets)} support tickets")

    # ---- Engagement Surveys ----
    print("  Seeding engagement surveys...")
    surveys = []
    for emp_id in random.sample(emp_ids, min(30, len(emp_ids))):
        surveys.append((
            str(uuid.uuid4()), tenant_id, emp_id,
            date.today() - timedelta(days=random.randint(0, 90)),
            round(random.uniform(2.5, 5.0), 1),
            random.choice(sentiments)
        ))
    await conn.executemany(
        "INSERT INTO engagement_surveys (id, tenant_id, employee_id, survey_date, overall_score, sentiment) VALUES ($1,$2,$3,$4,$5,$6)",
        surveys
    )
    print(f"  ✓ {len(surveys)} engagement surveys")

    print("\n✅ Synthetic data seeding complete!")

async def main():
    parser = argparse.ArgumentParser(description="Seed NexaMind with synthetic data")
    parser.add_argument("--tenant-id", required=True, help="Tenant UUID")
    parser.add_argument("--db-url", default="postgresql://nexamind:nexamind_secret@localhost:5432/nexamind")
    args = parser.parse_args()
    
    conn = await asyncpg.connect(args.db_url)
    try:
        await seed_data(conn, args.tenant_id)
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
