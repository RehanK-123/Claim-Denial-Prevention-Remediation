from util.utils import diagnose_data
from util.dao import DAO
import pandas as pd

def diagnose_cost():
    """Diagnoses the attributes and details for the costs data"""
    logger_instance = logger("logs/diagnose_costs.log")

    try:
        conn = DAO("bronze.db")
        data = conn.read("bronze_cost")
        df = pd.DataFrame(data, columns=["procedure_code", "average_cost", "expected_cost", "region"])
        diagnostics = diagnose_data(df)
    except Exception as e:
        logger_instance.error(f"Error diagnosing cost data {e}")
        return

    return diagnostics

if __name__ == "__main__":
    diagnostics = diagnose_cost()
    for diag, desc in diagnostics.items():
        print(f"{diag}: {desc}")

