from util.utils import spark, logger
from util.dao import DAO
from util.errors.dao_errors import TableCreationError, DataTransformationError
from pyspark.sql.functions import *
from pyspark.sql.window import Window

def standardize_providers():
    df = spark.table("newcatalog.bronze.bronze_providers")

    return df.selectExpr(
        "CAST(provider_id AS STRING) as provider_id",
        "doctor_name",
        "specialty",
        "location as region"
    )


def clean_providers(df):
    try:
        # Fill nulls
        df = df.withColumn("region", coalesce(col("region"), lit("UNKNOWN"))) \
               .withColumn("specialty", coalesce(col("specialty"), lit("UNKNOWN")))

        # Deduplicate (deterministic)
        window = Window.partitionBy("provider_id").orderBy(col("provider_id"))

        df = df.withColumn("rn", row_number().over(window)) \
               .filter(col("rn") == 1) \
               .drop("rn")

        return df

    except Exception as e:
        raise DataTransformationError("clean_providers") from e

if __name__ == "__main__":
    df = standardize_providers()
    silver_providers_df = clean_providers(df)


    conn = DAO(spark, "newcatalog", "silver")
    conn.create_table("standardized_providers", silver_providers_df)
    