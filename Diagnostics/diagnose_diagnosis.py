from util.utils import diagnose_data
from util.dao import DAO
import pandas as pd

def diagnose_diagnosis():
    """Diagnoses the attributes and details for the diagnosis data"""
    logger_instance = logger("logs/diagnose_diagnosis.log")

    try:
        conn = DAO("bronze.db")
        data = conn.read("bronze_diagnosis")
        df = pd.DataFrame(data, columns=["diagnosis_code", "category", "severity"])
        diagnostics = diagnose_data(df)
    except Exception as e:
        logger_instance.error(f"Error diagnosing diagnosis data {e}")
        return

        
    return diagnostics

if __name__ == "__main__":
    diagnostics = diagnose_diagnosis()
    for diag, desc in diagnostics.items():
        print(f"{diag}: {desc}")