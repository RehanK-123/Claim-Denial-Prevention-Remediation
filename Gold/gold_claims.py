from util.utils import spark, logger
from util.dao import DAO
from util.errors.dao_errors import TableCreationError, DataTransformationError
from pyspark.sql.functions import *
from pyspark.sql.window import Window 


def build_gold_claims(df):

    provider_avg = df.groupBy("provider_id").agg(
        avg("billed_amount").alias("provider_avg_billed")
    )

    diagnosis_avg = df.groupBy("diagnosis_code").agg(
        avg("billed_amount").alias("diagnosis_avg_billed")
    )

    df = df.join(provider_avg, on="provider_id", how="left")
    df = df.join(diagnosis_avg, on="diagnosis_code", how="left")

    df = df.withColumn(
        "cost_ratio",
        when(col("expected_cost").isNull() | (col("expected_cost") == 0), None)
        .otherwise(col("billed_amount") / col("expected_cost"))
    ).withColumn(
        "completeness_score",
        1 - (col("proc_missing") + col("diag_missing") + col("provider_missing")) / 3
    ).withColumn(
        "regional_cost_deviation",
        when(col("average_cost").isNull() | (col("average_cost") == 0), None)
        .otherwise((col("billed_amount") - col("average_cost")) / col("average_cost"))
    ).withColumn(
        "cost_alignment_ratio",
        when(col("average_cost").isNull() | (col("average_cost") == 0), None)
        .otherwise(col("billed_amount") / col("average_cost"))
    # ).withColumn(
    #     "late_submission_flag",
    #     (datediff(current_date(), col("date")) > 180).cast("int")
    ).withColumn(
        "provider_cost_ratio",
        when(col("provider_avg_billed") == 0, None)
        .otherwise(col("billed_amount") / col("provider_avg_billed"))
    ).withColumn(
        "diagnosis_cost_ratio",
        when(col("diagnosis_avg_billed") == 0, None)
        .otherwise(col("billed_amount") / col("diagnosis_avg_billed"))
    )

# --------- BURST CLAIM LOGIC ------------ #
    # Step 1: patient window
    w = Window.partitionBy("patient_id").orderBy("date")

    # Step 2–4: inline cluster creation
    df_temp = df.withColumn("prev_date", lag("date").over(w)) \
        .withColumn("gap_days", datediff(col("date"), col("prev_date"))) \
        .withColumn("new_cluster", when((col("gap_days").isNull()) | (col("gap_days") > 7), 1).otherwise(0)) \
        .withColumn("cluster_id", sum("new_cluster").over(w))

    # Step 5: cluster stats
    cluster_df = df_temp.groupBy("patient_id", "cluster_id").agg(
        count("*").alias("cluster_size"),
        min("date").alias("cluster_start"),
        max("date").alias("cluster_end")
    )

    # Step 6: inter-cluster gap
    w2 = Window.partitionBy("patient_id").orderBy("cluster_start")

    cluster_df = cluster_df.withColumn(
        "prev_cluster_end",
        lag("cluster_end").over(w2)
    ).withColumn(
        "inter_gap",
        datediff(col("cluster_start"), col("prev_cluster_end"))
    )

    # Step 7: burst frequency
    cluster_df = cluster_df.withColumn(
        "burst_freq",
        col("cluster_size") / when(col("inter_gap") <= 0, None).otherwise(col("inter_gap"))
    )

    # Step 8: final patient-level feature ONLY
    patient_burst = cluster_df.groupBy("patient_id").agg(
        avg("burst_freq").alias("avg_claim_burst_freq")
    )

    # Step 9: join back (only 1 column added)
    df = df.join(patient_burst, on="patient_id", how="left")
    
    cols_to_drop = ["patient_id", "claim_id", "date"]

    df = df.drop(*[c for c in cols_to_drop if c in df.columns])
    
    return df 



def generate_labels(df):
    # ---------------- COST RULES ---------------- #
    df_temp = df.withColumn(
        "cost_risk",
        when(col("cost_ratio") > 2.0, 1.0)
        .when(col("cost_ratio") > 1.5, 0.7)
        .when(col("cost_ratio") > 1.2, 0.4)
        .otherwise(0.0)
    ).withColumn(
        "regional_risk",
        when(col("regional_cost_deviation") > 0.5, 1.0)
        .when(col("regional_cost_deviation") > 0.3, 0.6)
        .otherwise(0.0)
    ).withColumn(
        "alignment_risk",
        when(col("cost_alignment_ratio") > 1.8, 1.0)
        .when(col("cost_alignment_ratio") > 1.4, 0.6)
        .otherwise(0.0)
    ).withColumn(
        "provider_risk",
        when(col("provider_cost_ratio") > 1.8, 1.0)
        .when(col("provider_cost_ratio") > 1.4, 0.6)
        .otherwise(0.0)
    ).withColumn(
        "diagnosis_risk",
        when(col("diagnosis_cost_ratio") > 1.8, 1.0)
        .when(col("diagnosis_cost_ratio") > 1.4, 0.6)
        .otherwise(0.0)
    ).withColumn(
        "data_quality_risk",
        when(col("completeness_score") < 0.5, 1.0)
        .when(col("completeness_score") < 0.7, 0.6)
        .otherwise(0.0)
    ).withColumn(
        "severity_risk",
        when(
            (col("severity") == "low") & (col("cost_ratio") > 1.5),
            1.0
        ).when(
            (col("severity") == "medium") & (col("cost_ratio") > 2.0),
            0.7
        ).otherwise(0.0)
    ).withColumn(
        "burst_risk",
        when(col("avg_claim_burst_freq") > 1.5, 1.0)
        .when(col("avg_claim_burst_freq") > 1.0, 0.6)
        .otherwise(0.0)
    )

    # ---------------- FINAL WEIGHTED SCORE ---------------- #
    risk_score_df = df_temp.withColumn(
        "risk_score",
        0.25 * col("cost_risk") +
        0.15 * col("regional_risk") +
        0.15 * col("alignment_risk") +
        0.15 * col("provider_risk") +
        0.10 * col("diagnosis_risk") +
        0.10 * col("data_quality_risk") +
        0.05 * col("severity_risk") +
        0.05 * col("burst_risk")
    ).withColumn(
        "label",
        when(col("risk_score") >= 0.6, "DENIED")
        .otherwise("APPROVED")
    )

    final_df = risk_score_df.select(*df.columns, "label") #getting relevant labels
    return final_df



if __name__ == "__main__":
    conn = DAO(spark, "newcatalog", "silver")
    df = conn.read_table("silver_claims")

    claims_df = build_gold_claims(df)
    claims_labelled_df = generate_labels(claims_df)

    gold_conn = DAO(spark, "newcatalog", "gold")
    gold_conn.create_table("gold_claims", claims_labelled_df)












