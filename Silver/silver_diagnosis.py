from util.utils import spark, logger
from util.dao import DAO
from util.errors.dao_errors import TableCreationError, DataTransformationError
from pyspark.sql.functions import *
from pyspark.sql.window import Window

def standardize_diagnosis():
    df = spark.table("newcatalog.bronze.bronze_diagnosis")

    return df.selectExpr(
        "CAST(diagnosis_code AS STRING) as diagnosis_code",
        "category",
        "severity"
    )

def clean_diagnosis(df):
    try:
        df = df.withColumn("category", coalesce(col("category"), lit("UNKNOWN"))) \
               .withColumn("severity", coalesce(col("severity"), lit("UNKNOWN")))

        window = Window.partitionBy("diagnosis_code").orderBy(col("diagnosis_code"))

        df = df.withColumn("rn", row_number().over(window)) \
               .filter(col("rn") == 1) \
               .drop("rn")

        return df

    except Exception as e:
        raise DataTransformationError("clean_diagnosis") from e

if __name__ == "__main__":
    df = standardize_diagnosis()
    silver_diagnosis_df = clean_diagnosis(df)


    conn = DAO(spark, "newcatalog", "silver")
    conn.create_table("standardized_diagnosis", silver_diagnosis_df)
    