from util.utils import diagnose_data, logger
from util.dao import DAO
import pandas as pd

def diagnose_claims():
    """Diagnoses the attributes and details for the claims data"""
    logger_instance = logger("logs/diagnose_claims.log")
    
    try: 
        conn = DAO("bronze.db")
        data = conn.read("bronze_claims")
        df = pd.DataFrame(data, columns=["claim_id", "patient_id", "provider_id", "diagnosis_code", "procedure_code", "billed_amount", "date"])
        diagnostics = diagnose_data(df)
    except Exception as e:
        logger_instance.error(f"Error diagnosing claims data {e}")
        return

    return diagnostics

if __name__ == "__main__":
    diagnostics = diagnose_claims()
    for diag, desc in diagnostics.items():
        print(f"{diag}: {desc}")