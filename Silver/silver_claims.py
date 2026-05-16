from util.utils import spark, logger
from util.dao import DAO
from util.errors.dao_errors import TableCreationError, DataTransformationError
from pyspark.sql.functions import *
from pyspark.sql.window import Window


def standardize_claims():
    df = spark.table("newcatalog.bronze.bronze_claims")

    return df.selectExpr(
        "CAST(claim_id AS STRING) as claim_id",
        "CAST(patient_id AS STRING) as patient_id",
        "CAST(provider_id AS STRING) as provider_id",
        "CAST(diagnosis_code AS STRING) as diagnosis_code",
        "CAST(procedure_code AS STRING) as procedure_code",
        "CAST(billed_amount AS DOUBLE) as billed_amount",
        "CAST(date AS DATE) as date"
    )

def clean_silver_claims(df):
    try:
        # Deterministic dedup
        window = Window.partitionBy("claim_id").orderBy(col("date").desc())

        df = df.withColumn("rn", row_number().over(window)) \
               .filter("rn = 1") \
               .drop("rn")

        # Fill categorical nulls
        df = df.fillna({
            "diagnosis_code": "UNKNOWN",
            "procedure_code": "UNKNOWN",
            "billed_amount": int(df.select("billed_amount").toPandas().median().iloc[0]) #because data is right skewed - impute with median 
        })

        # Filter invalid billed_amount
        df = df.filter(col("billed_amount").isNotNull() & (col("billed_amount") > 0))

        return df

    except Exception as e:
        raise DataTransformationError("clean_silver_claims") from e

if __name__ == "__main__":
    df = standardize_claims()
    silver_claims_df = clean_silver_claims(df)

    conn = DAO(spark, "newcatalog", "silver")
    conn.create_table("standardized_claims", silver_claims_df)