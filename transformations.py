from util.utils import spark
from util.dao import DAO
from pyspark.sql.functions import (
    col,
    avg,
    count,
    lag,
    min,
    max,
    datediff,
    when,
    sum
)
from pyspark.sql.window import Window
from util.errors.transformation_errors import (
    ProviderNotFoundException,
    DiagnosisNotFoundException,
    CostNotFoundException
)

# ---------------------------------------------------
# LOAD GOLD CLAIMS
# ---------------------------------------------------

gold_conn = DAO(
    spark,
    "newcatalog",
    "gold"
)

gold_claims_df = gold_conn.read_table(
    "gold_claims"
)

silver_conn = DAO(
    spark,
    "newcatalog",
    "silver"
)

providers_df = silver_conn.read_table(
    "standardized_providers"
)

diagnosis_df = silver_conn.read_table(
    "standardized_diagnosis"
)

costs_df = silver_conn.read_table(
    "standardized_costs"
)

silver_claims_df = silver_conn.read_table(
    "silver_claims"
)

# ---------------------------------------------------
# BUILD LOOKUP TABLES
# ---------------------------------------------------

provider_avg_df = gold_claims_df.groupBy(
    "provider_id"
).agg(
    avg("billed_amount").alias(
        "provider_avg_billed"
    )
)

diagnosis_avg_df = gold_claims_df.groupBy(
    "diagnosis_code"
).agg(
    avg("billed_amount").alias(
        "diagnosis_avg_billed"
    )
)


# ---------------------------------------------------
# PATIENT BURST FEATURE
# ---------------------------------------------------

patient_window = Window.partitionBy(
    "patient_id"
).orderBy(
    "date"
)

burst_temp_df = silver_claims_df.withColumn(
    "prev_date",
    lag("date").over(patient_window)
).withColumn(
    "gap_days",
    datediff(
        col("date"),
        col("prev_date")
    )
).withColumn(
    "new_cluster",
    when(
        (col("gap_days").isNull()) |
        (col("gap_days") > 7),
        1
    ).otherwise(0)
).withColumn(
    "cluster_id",
    sum("new_cluster").over(patient_window)
)

cluster_df = burst_temp_df.groupBy(
    "patient_id",
    "cluster_id"
).agg(
    count("*").alias("cluster_size"),
    min("date").alias("cluster_start"),
    max("date").alias("cluster_end")
)

cluster_window = Window.partitionBy(
    "patient_id"
).orderBy(
    "cluster_start"
)

cluster_df = cluster_df.withColumn(
    "prev_cluster_end",
    lag("cluster_end").over(cluster_window)
).withColumn(
    "inter_gap",
    datediff(
        col("cluster_start"),
        col("prev_cluster_end")
    )
)

cluster_df = cluster_df.withColumn(
    "burst_freq",
    col("cluster_size") / when(
        col("inter_gap") <= 0,
        None
    ).otherwise(
        col("inter_gap")
    )
)

patient_burst_df = cluster_df.groupBy(
    "patient_id"
).agg(
    avg("burst_freq").alias(
        "avg_claim_burst_freq"
    )
)


# ---------------------------------------------------
# ENRICHMENT FUNCTION
# ---------------------------------------------------

def enrich_claim_features(claim_input):

    enriched_claim = claim_input.copy()

    provider_id = enriched_claim["provider_id"]
    diagnosis_code = enriched_claim["diagnosis_code"]
    procedure_code = enriched_claim["procedure_code"]
    patient_id = enriched_claim["patient_id"]

    # ---------------------------------------------------
    # PROVIDER AVG
    # ---------------------------------------------------

    provider_record = provider_avg_df.filter(
        col("provider_id") == provider_id
    ).first()

    if provider_record:

        enriched_claim["provider_avg_billed"] = float(
            provider_record["provider_avg_billed"]
        )

        enriched_claim["provider_missing"] = 0

    else:

        enriched_claim["provider_avg_billed"] = 0.0
        enriched_claim["provider_missing"] = 1

    # ---------------------------------------------------
    # DIAGNOSIS AVG
    # ---------------------------------------------------

    diagnosis_record = diagnosis_avg_df.filter(
        col("diagnosis_code") == diagnosis_code
    ).first()

    if diagnosis_record:

        enriched_claim["diagnosis_avg_billed"] = float(
            diagnosis_record["diagnosis_avg_billed"]
        )

        enriched_claim["diag_missing"] = 0

    else:

        enriched_claim["diagnosis_avg_billed"] = 0.0
        enriched_claim["diag_missing"] = 1

    # ---------------------------------------------------
    # PROCEDURE MISSING
    # ---------------------------------------------------

    if (
        enriched_claim["procedure_code"] is None
        or str(
            enriched_claim["procedure_code"]
        ).strip() == ""
    ):

        enriched_claim["proc_missing"] = 1

    else:

        enriched_claim["proc_missing"] = 0

    # ---------------------------------------------------
    # PATIENT BURST FEATURE
    # ---------------------------------------------------

    patient_record = patient_burst_df.filter(
        col("patient_id") == patient_id
    ).first()

    if patient_record:

        enriched_claim["avg_claim_burst_freq"] = float(
            patient_record["avg_claim_burst_freq"]
        )

    else:

        enriched_claim["avg_claim_burst_freq"] = 0.0

     # ---------------------------------------------------
    # PROVIDER LOOKUP
    # ---------------------------------------------------

    provider_record = providers_df.filter(
        col("provider_id") == provider_id
    ).select(
        "region"
    ).first()

    if provider_record is None:

        raise ProviderNotFoundException(
            provider_id
        )

    enriched_claim["provider_region"] = (
        provider_record["region"]
    )

    # ---------------------------------------------------
    # DIAGNOSIS LOOKUP
    # ---------------------------------------------------

    diagnosis_record = diagnosis_df.filter(
        col("diagnosis_code") == diagnosis_code
    ).select(
        "severity"
    ).first()

    if diagnosis_record is None:

        raise DiagnosisNotFoundException(
            diagnosis_code
        )

    enriched_claim["severity"] = (
        diagnosis_record["severity"]
    )

    # ---------------------------------------------------
    # COST LOOKUP
    # ---------------------------------------------------

    cost_record = costs_df.filter(
        col("procedure_code") == procedure_code
    ).select(
        "average_cost",
        "expected_cost",
        "region"
    ).first()

    if cost_record is None:

        raise CostNotFoundException(
            procedure_code
        )

    enriched_claim["average_cost"] = (
        cost_record["average_cost"]
    )

    enriched_claim["expected_cost"] = (
        cost_record["expected_cost"]
    )

    enriched_claim["cost_region"] = (
        cost_record["region"]
    )

    # ---------------------------------------------------
    # COST RATIO    
    # ---------------------------------------------------

    if enriched_claim["expected_cost"] != 0:

        enriched_claim["cost_ratio"] = (
            enriched_claim["billed_amount"] /
            enriched_claim["expected_cost"]
        )

    else:

        enriched_claim["cost_ratio"] = None


    # ---------------------------------------------------
    # REGIONAL COST DEVIATION
    # ---------------------------------------------------

    if enriched_claim["average_cost"] != 0:

        enriched_claim["regional_cost_deviation"] = abs(
            enriched_claim["billed_amount"] -
            enriched_claim["average_cost"]
        ) / enriched_claim["average_cost"]

    else:

        enriched_claim["regional_cost_deviation"] = None


    # ---------------------------------------------------
    # COST ALIGNMENT RATIO
    # ---------------------------------------------------

    if enriched_claim["expected_cost"] != 0:

        enriched_claim["cost_alignment_ratio"] = (
            enriched_claim["billed_amount"] /
            enriched_claim["expected_cost"]
        )

    else:

        enriched_claim["cost_alignment_ratio"] = None


    # ---------------------------------------------------
    # PROVIDER COST RATIO
    # ---------------------------------------------------

    if enriched_claim["provider_avg_billed"] != 0:

        enriched_claim["provider_cost_ratio"] = (
            enriched_claim["billed_amount"] /
            enriched_claim["provider_avg_billed"]
        )

    else:

        enriched_claim["provider_cost_ratio"] = None


    # ---------------------------------------------------
    # DIAGNOSIS COST RATIO
    # ---------------------------------------------------

    if enriched_claim["diagnosis_avg_billed"] != 0:

        enriched_claim["diagnosis_cost_ratio"] = (
            enriched_claim["billed_amount"] /
            enriched_claim["diagnosis_avg_billed"]
        )

    else:

        enriched_claim["diagnosis_cost_ratio"] = None


    # ---------------------------------------------------
    # COMPLETENESS SCORE
    # ---------------------------------------------------

    enriched_claim["completeness_score"] = 1.0 - (
        (
            enriched_claim["proc_missing"] +
            enriched_claim["diag_missing"] +
            enriched_claim["provider_missing"]
        ) / 3.0
    )
    
    return enriched_claim



# ---------------------------------------------------
# TEST
# ---------------------------------------------------

if __name__ == "__main__":

    sample_claim = {
        "claim_id": "C9999",
        "patient_id": "P177",
        "provider_id": "PR105",
        "diagnosis_code": "D10",
        "procedure_code": "PROC3",
        "billed_amount": 32000.0,
        "date": "2024-05-01"
    }

    enriched_claim = enrich_claim_features(
        sample_claim
    )
    
    enriched_claim.pop("claim_id")  # Remove claim_id for cleaner output
    enriched_claim.pop("patient_id")  # Remove patient_id for cleaner output
    enriched_claim.pop("date")  # Remove date for cleaner output

    print(enriched_claim, len(enriched_claim))




# 'diagnosis_code',1
#  'provider_id',2
#  'procedure_code',3
#  'billed_amount',4
#  'provider_region',5
#  'cost_region',6
#  'severity',7
#  'expected_cost',8
#  'average_cost',9
#  'proc_missing',10
#  'diag_missing',11
#  'provider_missing',12
#  'provider_avg_billed',
#  'diagnosis_avg_billed',
#  'cost_ratio',
#  'completeness_score',
#  'regional_cost_deviation',
#  'cost_alignment_ratio',
#  'provider_cost_ratio',
#  'diagnosis_cost_ratio',
#  'avg_claim_burst_freq',