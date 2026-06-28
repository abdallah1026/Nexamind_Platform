

import os
import joblib
import pandas as pd
from typing import Any, Dict
from ..base_agent import BaseAgent

class DetectorAgent(BaseAgent):
    name = "detector_agent"
    module = "finance"
    description = "finds weird transactions / possible fraud"
    tools = ["sql_tool", "calculation_tool", "rag_tool", "webhook_tool"]

    def _get_model_path(self) -> str:
        
        base_dir = os.path.dirname(__file__)
        
        return os.path.abspath(os.path.join(base_dir, "..", "..", "models", "anomaly_models", f"detector_{self.tenant_id}.joblib"))

    def get_system_prompt(self) -> str:
        return """You are a fraud and anomaly detection assistant for financial data.

Look at the transactions and find anything suspicious like:
- unusually large amounts compared to normal
- duplicate transactions (same amount, same vendor, close dates)
- transactions at weird times
- round numbers (often sign of fraud apparently)
- ML-flagged anomalies (from an IsolationForest model)

for each anomaly you find say:
1. what it is
2. how serious (low/medium/high)  
3. what to do about it

be specific, dont say "this might be suspicious" actually explain why"""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        calc = self.get_tool("calculation_tool")

        result = await sql.execute(
            """SELECT id, transaction_date, amount, category, counterparty, description
            FROM financial_transactions
            WHERE tenant_id = :tenant_id
              AND transaction_date >= NOW() - INTERVAL '30 days'
            ORDER BY transaction_date DESC
            LIMIT 500""",
            {"tenant_id": self.tenant_id}
        )
        txns = result.get("rows", [])

        amounts = [float(r["amount"]) for r in txns if r.get("amount")]
        
        stdev_result = {"result": 0}
        mean_result = {"result": 0}
        if len(amounts) > 1:
            stdev_result = await calc.execute("stdev", amounts)
            mean_result = await calc.execute("mean", amounts)

        ml_anomalies = []
        model_loaded = False
        model_path = self._get_model_path()
        
        if os.path.exists(model_path):
            try:
                model = joblib.load(model_path)
                df = pd.DataFrame(txns)
                if not df.empty:
                    
                    df['amount'] = df['amount'].astype(float)
                    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
                    df['hour'] = df['transaction_date'].dt.hour
                    df['dow'] = df['transaction_date'].dt.dayofweek

                    preds = model.predict(df[["amount", "category", "counterparty", "hour", "dow"]])
                    
                    for i, pred in enumerate(preds):
                        if pred == -1:
                            ml_anomalies.append(txns[i])
                    model_loaded = True
            except Exception as e:
                print(f"Error loading/using ML model: {e}")

        prompt_data = f"""
user request: {user_input}

transactions from last 30 days (total: {len(amounts)}):
{txns[:20]} ... (showing first 20)

statistics (Z-score approach):
- mean amount: {mean_result.get('result', 'N/A')}
- standard deviation: {stdev_result.get('result', 'N/A')}
"""

        if model_loaded:
            prompt_data += f"\nML model flagged {len(ml_anomalies)} potential anomalies using IsolationForest:\n{ml_anomalies[:10]}"
        else:
            prompt_data += "\nNote: Machine learning model not found or failed to load. Using statistical fallback only."

        messages = [{"role": "user", "content": f"""
{prompt_data}

anything more than 2 standard deviations from mean is suspicious.
please analyze and report anomalies"""}]
        
        response = await self.call_llm(
            messages, 
            system=self.get_system_prompt(), 
            temperature=0.1
        )
        
        return {
            "response": response, 
            "transactions_analyzed": len(amounts),
            "ml_model_used": model_loaded,
            "ml_anomalies_found": len(ml_anomalies)
        }
