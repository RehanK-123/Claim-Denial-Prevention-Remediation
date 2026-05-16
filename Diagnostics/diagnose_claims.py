from util.utils import diagnose_data, logger, spark
from util.errors.validation_errors import InvalidClaimError
from util.dao import DAO
import pandas as pd

def diagnose_claims():
    """Diagnoses the attributes and details for the claims data"""
    logger_instance = logger("logs/diagnose_claims.log")

    try: 
        conn = DAO(spark, "newcatalog", "bronze")
        df = conn.read_table("bronze_claims")
        diagnostics = diagnose_data(df)
    except Exception as e:
        err = InvalidClaimError(e)
        logger_instance.error(err.to_dict())
        return

    return diagnostics

if __name__ == "__main__":
    diagnostics = diagnose_claims()
    for diag, desc in diagnostics.items():
        print(f"{diag}: {desc}")



# constant error
# error code for log traceability - make error code standardized 
# make dashboard for analytics of data 
# silver layer for business validation and cleaning 
