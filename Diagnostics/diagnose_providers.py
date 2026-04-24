from util.utils import diagnose_data
from util.dao import DAO
import pandas as pd

def diagnose_providers():
    """Diagnoses the attributes and details for the provideres data"""
    logger_instance = logger("logs/diagnose_providers.log")
    
    try:
        conn = DAO("bronze.db")
        data = conn.read("bronze_providers")
        df = pd.DataFrame(data, columns=["provider_id", "doctor_name", "specialty", "location"])
        diagnostics = diagnose_data(df)
    except Exception as e:
        logger_instance.error(f"Error diagnosing providers data {e}")
        return 

        
    return diagnostics

if __name__ == "__main__":
    diagnostics = diagnose_providers()
    for diag, desc in diagnostics.items():
        print(f"{diag}: {desc}")
