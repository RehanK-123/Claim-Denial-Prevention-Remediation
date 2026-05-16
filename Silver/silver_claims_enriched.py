from util.utils import spark, logger
from util.dao import DAO
from util.errors.dao_errors import TableCreationError, DataTransformationError
from pyspark.sql.functions import *
from pyspark.sql.window import Window



def build_enriched():
    claims = conn.read_table("standardized_claims")
    providers = conn.read_table("standardized_providers")
    diagnosis = conn.read_table("standardized_diagnosis")
    costs = conn.read_table("standardized_costs")

    df = claims \
        .join(providers, "provider_id", "left") \
        .join(diagnosis, "diagnosis_code", "left") \
        .join(costs, "procedure_code", "left").select(
        "claim_id",
        "patient_id",
        "provider_id",
        "diagnosis_code",
        "procedure_code",
        "billed_amount",
        "date",
        col("standardized_providers.region").alias("provider_region"),
        col("standardized_costs.region").alias("cost_region"),
        "severity",
        "expected_cost",
        "average_cost"
    )

    df = df.withColumn(
        "proc_missing",
        when(col("procedure_code") == "UNKNOWN", 1).otherwise(0)
    ).withColumn(
        "diag_missing",
        when(col("diagnosis_code") == "UNKNOWN", 1).otherwise(0)
    ).withColumn(
        "provider_missing",
        when(col("provider_id") == "UNKNOWN", 1).otherwise(0)
    )
    return df


if __name__ == "__main__":
    conn = DAO(spark, "newcatalog", "silver") #connect to Databricks 

    enriched_claims_df = build_enriched()

    conn.create_table("silver_claims", enriched_claims_df)
