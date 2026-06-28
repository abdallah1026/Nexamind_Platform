import asyncio
import random
import uuid
from datetime import datetime, timedelta, date
import argparse
import sys

try:
    import asyncpg
except ImportError:
    print("Install asyncpg: pip install asyncpg")
    sys.exit(1)

FINANCE_CATEGORIES = [
    "Automotive Sales",
    "Energy Generation & Storage",
    "FSD Subscriptions",
    "R&D - Autopilot",
    "R&D - Tesla Bot",
    "SG&A - Supercharger Network",
    "CapEx - Giga Texas Expansion",
    "Professional Services"
]
DEPARTMENTS = ["Autopilot", "Optimus", "Energy Storage", "Vehicle Engineering", "Finance", "HR", "Sales", "Customer Support"]
TICKET_CATEGORIES = ["Technical Issue", "Billing", "Installation Delay", "Warranty Claim", "Performance Degradation", "Integration"]
COUNTERPARTIES = ["Panasonic Energy", "CATL Co.", "Nvidia Corp", "Brembo SpA", "Steel Dynamics", "Hertz Rental", "PepsiCo", "ERCOT"]

async def seed_data(conn, tenant_id: str):
    print(f"Seeding Tesla, Inc. data for tenant: {tenant_id}")

    print("  Seeding financial transactions...")
    txns = []
    base_date = date.today() - timedelta(days=365)

    for i in range(200):
        txn_date = base_date + timedelta(days=random.randint(0, 360))
        is_revenue = random.random() > 0.45
        category = random.choice(FINANCE_CATEGORIES)

        if "Sales" in category or "Revenue" in category or "Subscription" in category:
            amount = random.uniform(100000, 1500000) if is_revenue else -random.uniform(5000, 50000)
            counterparty = random.choice(["Hertz Rental", "PepsiCo", "ERCOT", "Direct Customer"])
        else:
            amount = -random.uniform(10000, 250000)
            counterparty = random.choice(["Panasonic Energy", "CATL Co.", "Nvidia Corp", "Brembo SpA", "Steel Dynamics"])
            
        txns.append((
            str(uuid.uuid4()), tenant_id, txn_date, round(amount, 2),
            "USD", category, f"Standard transaction for {category.lower()}", counterparty
        ))

    recent_date_1 = date.today() - timedelta(days=2)
    recent_date_2 = date.today() - timedelta(days=5)

    capex_anomaly_id = str(uuid.uuid4())
    txns.append((
        capex_anomaly_id, tenant_id, recent_date_1, -9500000.00,
        "USD", "CapEx - Giga Texas Expansion",
        "Emergency payment for Giga Texas steel delivery without purchase order",
        "Steel Dynamics"
    ))

    txns.append((
        str(uuid.uuid4()), tenant_id, recent_date_2, -125000.00,
        "USD", "SG&A - Supercharger Network",
        "Wiring audit double charge", "Acme Wiring"
    ))
    txns.append((
        str(uuid.uuid4()), tenant_id, recent_date_2, -125000.00,
        "USD", "SG&A - Supercharger Network",
        "Wiring audit double charge", "Acme Wiring"
    ))

    await conn.executemany(
        """INSERT INTO financial_transactions 
           (id, tenant_id, transaction_date, amount, currency, category, description, counterparty)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8)""",
        txns
    )
    print(f"  ✓ {len(txns)} transactions seeded (including custom anomalies)")

    print("  Seeding employees...")
    employees = [
        
        (str(uuid.uuid4()), tenant_id, "EMP-001", "Elon Musk", "elon@tesla.com", "Executive", "Chief Executive Officer", 500000.00, 4.8, 4.5, date.today() - timedelta(days=3000)),
        (str(uuid.uuid4()), tenant_id, "EMP-002", "Vaibhav Taneja", "vaibhav@tesla.com", "Finance", "Chief Financial Officer", 350000.00, 4.9, 4.7, date.today() - timedelta(days=1200)),
        (str(uuid.uuid4()), tenant_id, "EMP-003", "Lars Moravy", "lars@tesla.com", "Vehicle Engineering", "VP Vehicle Engineering", 320000.00, 4.7, 4.6, date.today() - timedelta(days=2000)),
        (str(uuid.uuid4()), tenant_id, "EMP-004", "Franz von Holzhausen", "franz@tesla.com", "Vehicle Engineering", "Chief Designer", 340000.00, 4.9, 4.8, date.today() - timedelta(days=2500)),

        (str(uuid.uuid4()), tenant_id, "EMP-005", "Ashok Elluswamy", "ashok@tesla.com", "Autopilot", "Director of Autopilot Software", 280000.00, 4.9, 4.2, date.today() - timedelta(days=1500)),
        (str(uuid.uuid4()), tenant_id, "EMP-006", "John Doe", "johndoe@tesla.com", "Autopilot", "Senior Autopilot Architect", 210000.00, 4.8, 2.8, date.today() - timedelta(days=800)),
        (str(uuid.uuid4()), tenant_id, "EMP-007", "Jane Smith", "janesmith@tesla.com", "Autopilot", "ML Infrastructure Engineer", 170000.00, 4.5, 4.1, date.today() - timedelta(days=400)),
    ]

    for i in range(8, 41):
        hire_date = date.today() - timedelta(days=random.randint(60, 1500))
        dept = random.choice(DEPARTMENTS)
        title = "Staff Specialist" if i % 4 == 0 else "Senior Engineer" if i % 2 == 0 else "Associate"
        salary = round(random.uniform(70000, 190000), 2)
        performance = round(random.uniform(3.0, 5.0), 1)
        engagement = round(random.uniform(2.5, 5.0), 1)
        employees.append((
            str(uuid.uuid4()), tenant_id, f"EMP-{100+i}",
            f"Employee {i}", f"employee{i}@tesla.com",
            dept, f"{dept} {title}", salary, performance, engagement, hire_date
        ))
        
    await conn.executemany(
        """INSERT INTO employees 
           (id, tenant_id, employee_id, full_name, email, department, job_title, 
            salary, performance_score, engagement_score, hire_date)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)""",
        employees
    )
    print(f"  ✓ {len(employees)} employees seeded")

    emp_map = {e[3]: e[0] for e in employees}

    print("  Seeding attrition risks...")
    
    risks = [
        (str(uuid.uuid4()), tenant_id, emp_map["John Doe"], 88.5, "high"),
        (str(uuid.uuid4()), tenant_id, emp_map["Ashok Elluswamy"], 35.0, "low"),
    ]
    
    random_employees = random.sample([name for name in emp_map.keys() if name not in ["John Doe", "Ashok Elluswamy", "Elon Musk"]], 5)
    for name in random_employees:
        score = random.uniform(20, 68)
        risks.append((
            str(uuid.uuid4()), tenant_id, emp_map[name], round(score, 1),
            "high" if score > 70 else "medium" if score > 50 else "low"
        ))
        
    await conn.executemany(
        "INSERT INTO attrition_risks (id, tenant_id, employee_id, risk_score, risk_level) VALUES ($1,$2,$3,$4,$5)",
        risks
    )
    print(f"  ✓ {len(risks)} attrition risk records seeded")

    print("  Seeding inventory items...")
    skus = [
        (str(uuid.uuid4()), tenant_id, "SKU-MY-LR", "Model Y Long Range", "Vehicle", 35000.00, 1200, 200, 14),
        (str(uuid.uuid4()), tenant_id, "SKU-M3-SR", "Model 3 Standard Range", "Vehicle", 28000.00, 850, 150, 14),
        (str(uuid.uuid4()), tenant_id, "SKU-CT-AWD", "Cybertruck AWD", "Vehicle", 62000.00, 150, 50, 30),
        (str(uuid.uuid4()), tenant_id, "SKU-MP-2XL", "Megapack 2XL", "Energy", 980000.00, 45, 10, 45),
        (str(uuid.uuid4()), tenant_id, "SKU-PW-3", "Powerwall 3", "Energy", 5200.00, 3400, 500, 21),
    ]
    await conn.executemany(
        """INSERT INTO inventory_items 
           (id, tenant_id, sku, name, category, unit_cost, current_stock, reorder_point, lead_time_days)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)""",
        skus
    )
    print(f"  ✓ {len(skus)} inventory items seeded")

    print("  Seeding suppliers...")
    suppliers = [
        (str(uuid.uuid4()), tenant_id, "Panasonic Energy", "ops@panasonic.com", 0.96, 14, "Net 30"),
        (str(uuid.uuid4()), tenant_id, "CATL Co.", "shipping@catl.com", 0.94, 21, "Net 60"),
        (str(uuid.uuid4()), tenant_id, "Nvidia Corp", "sales@nvidia.com", 0.99, 30, "Net 30"),
        (str(uuid.uuid4()), tenant_id, "Brembo SpA", "brakes@brembo.it", 0.91, 28, "Net 45"),
        (str(uuid.uuid4()), tenant_id, "Steel Dynamics", "orders@steeldynamics.com", 0.85, 10, "Net 15"),
    ]
    await conn.executemany(
        """INSERT INTO suppliers 
           (id, tenant_id, name, contact_email, reliability_score, lead_time_days, payment_terms)
           VALUES ($1,$2,$3,$4,$5,$6,$7)""",
        suppliers
    )
    print(f"  ✓ {len(suppliers)} suppliers seeded")

    print("  Seeding deals...")
    deals = [
        (str(uuid.uuid4()), tenant_id, "Hertz Fleet Purchase 2026", "Hertz Rental", "Closed Won", 450000000.00, 100, date.today() - timedelta(days=20), "Emma Brown", "closed_won"),
        (str(uuid.uuid4()), tenant_id, "PepsiCo Semi Delivery Phase 2", "PepsiCo", "Negotiation", 20000000.00, 75, date.today() + timedelta(days=45), "Alice Smith", "open"),
        (str(uuid.uuid4()), tenant_id, "ERCOT Megapack Deployment", "ERCOT", "Proposal", 95000000.00, 60, date.today() + timedelta(days=90), "Bob Johnson", "open"),
        (str(uuid.uuid4()), tenant_id, "Walmart Semi Fleet Pilot", "Walmart", "Qualification", 2500000.00, 25, date.today() + timedelta(days=120), "Carol Davis", "open"),
    ]
    await conn.executemany(
        """INSERT INTO deals 
           (id, tenant_id, deal_name, customer_name, stage, amount, probability, expected_close_date, owner, status)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)""",
        deals
    )
    print(f"  ✓ {len(deals)} sales deals seeded")

    print("  Seeding customer churn risks...")
    churn_risks = [
        (str(uuid.uuid4()), tenant_id, "CUST-HERTZ", "Hertz Rental", 65.4, "high", 150000000.00),
        (str(uuid.uuid4()), tenant_id, "CUST-PEPSI", "PepsiCo", 22.0, "low", 20000000.00),
    ]
    await conn.executemany(
        """INSERT INTO customer_churn_risks 
           (id, tenant_id, customer_id, customer_name, churn_score, risk_level, annual_revenue_at_risk)
           VALUES ($1,$2,$3,$4,$5,$6,$7)""",
        churn_risks
    )
    print(f"  ✓ {len(churn_risks)} churn risk records seeded")

    print("  Seeding support tickets...")
    tickets = [
        (str(uuid.uuid4()), tenant_id, "TKT-MY-101", "David Vance", "Autopilot phantom braking on highway", 
         "Autopilot suddenly slammed brakes on I-5 at 70mph with no vehicles ahead. Highly dangerous.", 
         "Technical Issue", "P1", "open", "negative", 0.12, datetime.now() - timedelta(hours=6)),
        (str(uuid.uuid4()), tenant_id, "TKT-CT-102", "Tech Geeks Inc", "Cybertruck steering squeak and alignment", 
         "Cybertruck steer-by-wire system squeaking when turning left. Vehicle pulling slightly to right.", 
         "Technical Issue", "P2", "in_progress", "neutral", 0.45, datetime.now() - timedelta(days=1)),
        (str(uuid.uuid4()), tenant_id, "TKT-PW-103", "Sunny Side Solar", "Megapack installation delay Giga Texas", 
         "Megapack deployment delayed by 3 weeks due to missing wiring harness. Project schedule at risk.", 
         "Installation Delay", "P2", "open", "negative", 0.23, datetime.now() - timedelta(days=2)),
        (str(uuid.uuid4()), tenant_id, "TKT-M3-104", "Mary S.", "Model 3 panel gaps on delivery", 
         "Trunk alignment is off by 5mm, causing water leaks during heavy rain. Requesting immediate repair under warranty.", 
         "Warranty Claim", "P3", "resolved", "negative", 0.35, datetime.now() - timedelta(days=5)),
    ]
    await conn.executemany(
        """INSERT INTO support_tickets 
           (id, tenant_id, ticket_number, customer_name, subject, description, 
            category, priority, status, sentiment, sentiment_score, created_at)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
           ON CONFLICT (ticket_number) DO NOTHING""",
        tickets
    )
    print(f"  ✓ {len(tickets)} support tickets seeded")

    print("  Seeding engagement surveys...")
    surveys = []
    
    for name, emp_uuid in emp_map.items():
        score = 2.8 if name == "John Doe" else random.uniform(3.5, 5.0)
        sentiment = "negative" if score < 3.0 else "neutral" if score < 4.0 else "positive"
        surveys.append((
            str(uuid.uuid4()), tenant_id, emp_uuid,
            date.today() - timedelta(days=random.randint(5, 60)),
            round(score, 1), sentiment
        ))
    await conn.executemany(
        "INSERT INTO engagement_surveys (id, tenant_id, employee_id, survey_date, overall_score, sentiment) VALUES ($1,$2,$3,$4,$5,$6)",
        surveys
    )
    print(f"  ✓ {len(surveys)} engagement surveys seeded")

    print("\nTesla, Inc. custom database seeding complete!")

async def main():
    parser = argparse.ArgumentParser(description="Seed Tesla database tables")
    parser.add_argument("--tenant-id", required=True, help="Tenant UUID")
    parser.add_argument("--db-url", default="postgresql://postgres:postgres@localhost:5433/app")
    args = parser.parse_args()
    
    conn = await asyncpg.connect(args.db_url)
    try:
        await seed_data(conn, args.tenant_id)
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
