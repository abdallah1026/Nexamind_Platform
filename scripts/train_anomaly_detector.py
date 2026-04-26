#!/usr/bin/env python3
"""
Train Anomaly Detector for NexaMind AI Platform
Usage: python train_anomaly_detector.py --tenant-id <uuid> --db-url <url>
"""
import asyncio
import argparse
import sys
import os
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib

try:
    import asyncpg
except ImportError:
    print("Install asyncpg: pip install asyncpg")
    sys.exit(1)

# Default model path
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "services", "agent-orchestrator", "app", "models", "anomaly_models")

async def fetch_data(conn, tenant_id: str):
    print(f"Fetching data for tenant: {tenant_id}")
    query = """
        SELECT amount, category, counterparty, EXTRACT(HOUR FROM transaction_date::timestamp) as hour,
               EXTRACT(DOW FROM transaction_date) as dow
        FROM financial_transactions
        WHERE tenant_id = $1
    """
    rows = await conn.fetch(query, tenant_id)
    if not rows:
        print(f"No transactions found for tenant {tenant_id}")
        return None
    
    return pd.DataFrame([dict(r) for r in rows])

def train_model(df):
    print(f"Training IsolationForest on {len(df)} transactions...")
    
    # Define features
    numeric_features = ["amount", "hour", "dow"]
    categorical_features = ["category", "counterparty"]
    
    # Preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
        ]
    )
    
    # Isolation Forest Model
    model = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("clf", IsolationForest(contamination=0.05, random_state=42))
    ])
    
    # Fit model
    # IsolationForest.fit expects data where -1 is anomaly, 1 is normal
    model.fit(df)
    
    return model

async def main():
    parser = argparse.ArgumentParser(description="Train NexaMind Anomaly Detector model")
    parser.add_argument("--tenant-id", required=True, help="Tenant UUID")
    parser.add_argument("--db-url", default="postgresql://nexamind:nexamind_secret@localhost:5432/nexamind")
    parser.add_argument("--output-dir", help="Directory to save the model", default=MODEL_DIR)
    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        print(f"Created directory: {args.output_dir}")

    try:
        conn = await asyncpg.connect(args.db_url)
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        sys.exit(1)

    try:
        df = await fetch_data(conn, args.tenant_id)
        if df is not None and not df.empty:
            model = train_model(df)
            model_path = os.path.join(args.output_dir, f"detector_{args.tenant_id}.joblib")
            joblib.dump(model, model_path)
            print(f"✅ Model saved to: {model_path}")
        else:
            print("❌ Training skipped due to lack of data.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
