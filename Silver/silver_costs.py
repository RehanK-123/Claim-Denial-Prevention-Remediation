from util.utils import spark, logger
from util.dao import DAO
from util.errors.dao_errors import TableCreationError, DataTransformationError
from pyspark.sql.functions import *
from pyspark.sql.window import Window

def standardize_costs():
    df = spark.table("newcatalog.bronze.bronze_cost")

    return df.selectExpr(
        "CAST(procedure_code AS STRING) as procedure_code",
        "CAST(average_cost AS DOUBLE) as average_cost",
        "CAST(expected_cost AS DOUBLE) as expected_cost",
        "region"
    )

def clean_costs(df):
    try:
        df = df.withColumn("region", coalesce(col("region"), lit("UNKNOWN")))

        window = Window.partitionBy("procedure_code").orderBy(col("procedure_code"))

        df = df.withColumn("rn", row_number().over(window)) \
               .filter(col("rn") == 1) \
               .drop("rn")

        return df

    except Exception as e:
        raise DataTransformationError("clean_costs") from e



if __name__ == "__main__":
    df = standardize_costs()
    silver_costs_df = clean_costs(df)

    conn = DAO(spark, "newcatalog", "silver")
    conn.create_table("standardized_costs", silver_costs_df)


