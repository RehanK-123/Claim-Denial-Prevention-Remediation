from util.utils import diagnose_data, spark, logger
from util.errors.validation_errors import InvalidClaimError
from util.dao import DAO
import pandas as pd

def diagnose_diagnosis():
    """Diagnoses the attributes and details for the diagnosis data"""
    logger_instance = logger("logs/diagnose_diagnosis.log")

    try:
        conn = DAO(spark, "newcatalog", "bronze")
        df = conn.read_table("bronze_diagnosis")
        diagnostics = diagnose_data(df)
    except Exception as e:
        err = InvalidClaimError(e)
        logger_instance.error(err.to_dict())
        return


    return diagnostics

if __name__ == "__main__":
    diagnostics = diagnose_diagnosis()
    for diag, desc in diagnostics.items():
        print(f"{diag}: {desc}")