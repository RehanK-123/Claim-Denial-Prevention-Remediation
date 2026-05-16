from util.utils import diagnose_data, spark, logger
from util.errors.validation_errors import InvalidClaimError
from util.dao import DAO
import pandas as pd

def diagnose_cost():
    """Diagnoses the attributes and details for the costs data"""
    logger_instance = logger("logs/diagnose_costs.log")

    try:
        conn = DAO(spark, "newcatalog", "bronze")
        df = conn.read_table("bronze_cost")
        diagnostics = diagnose_data(df)
    except Exception as e:
        err = InvalidClaimError(e)
        logger_instance.error(err.to_dict())
        return

    return diagnostics

if __name__ == "__main__":
    diagnostics = diagnose_cost()
    for diag, desc in diagnostics.items():
        print(f"{diag}: {desc}")

