from mlflow.models import infer_signature

from util.utils import spark, logger
from util.errors.ml_errors import (
    SHAPExplainerException,
    SHAPValueGenerationException,
    ClaimExplanationGenerationException,
    ModelLoadingException,
    IntensityMappingException,
    SHAPPipelineException
)

import shap
import mlflow.xgboost
import mlflow
import os
import pandas as pd
import numpy as np
from .xgboost_model import X_test

logger_exp = logger("logs/explainability.log")
# --------------------------------------------- #
# Environment + MLFlow Setup
# --------------------------------------------- #
try:
    os.environ["DATABRICKS_TOKEN"] = os.getenv("DATABRICKS_TOKEN_ID")

    mlflow.set_tracking_uri("databricks")

    model_name = "xgboost_v1"
    model_version = "latest"

    # Load model from registry
    model_uri = "models:/xgboost_v1/1"
    model = mlflow.xgboost.load_model(model_uri)

    logger_exp.info("XGBoost model loaded successfully from MLFlow registry.")

except Exception as e:
    logger_exp.exception("Failed to load ML model.")
    raise ModelLoadingException(
    model_uri=model_uri,
    reason=e
) from e

# --------------------------------------------- #
# SHAP Value Generation
# --------------------------------------------- #
def get_shapley_values(data=X_test):

    try:
        logger_exp.info("Initializing SHAP TreeExplainer.")

       
        explainer = shap.TreeExplainer(model)

        # explainer_uri = "models:/shap_explainer_v1/1"
        # explainer = mlflow.shap.load_explainer(explainer_uri)
    except Exception as e:
        logger_exp.exception("Failed to initialize SHAP explainer.")
        raise SHAPExplainerException(
            model_name=model_name,
            reason=e
        ) from e

    try:
        logger_exp.info("Generating SHAP values.")

        shap_values = explainer.shap_values(data)

        logger_exp.info("SHAP values generated successfully.")


        # Convert inputs to standard DataFrame format and SHAP values to pure floats/arrays
        # input_data = pd.DataFrame([X_test.iloc[0]])

        # # Ensure shap_values are standard floats or cast to a pure list/array
        # clean_shap_values = np.array(shap_values).astype(float) 
        # with mlflow.start_run():
        #     mlflow.shap.log_explainer(explainer, name= "explainer", registered_model_name="shap_explainer_v1", signature= infer_signature(input_data, clean_shap_values))
        
        
        return shap_values

    except Exception as e:
        logger_exp.exception("Failed to generate SHAP values.")
        raise SHAPValueGenerationException(
            dataset_name="X_test",
            reason=e
        ) from e


# --------------------------------------------- #
# Explanation Mapping
# --------------------------------------------- #
explanation_dict = {
    "cost_ratio": "Claim cost is significantly higher than expected.",
    "diagnosis_cost_ratio": "Diagnosis-related billing appears unusually expensive.",
    "provider_cost_ratio": "Provider billing behavior deviates from normal patterns.",
    "severity": "Claim severity does not align with expected billing behavior.",
    "regional_cost_deviation": "Claim cost deviates from regional averages.",
    "billed_amount": "Total billed amount is unusually high.",
    "cost_alignment_ratio": "Claim cost is poorly aligned with expected treatment cost.",
    "diag_missing": "Important diagnosis information is missing.",
    "avg_claim_burst_freq": "Provider is submitting claims at unusually high frequency.",
    "average_cost": "Average claim cost pattern appears abnormal.",
    "diagnosis_avg_billed": "Diagnosis category has elevated historical billing trends.",
    "completeness_score": "Claim documentation appears incomplete.",
    "expected_cost": "Claim cost differs from expected benchmark.",
    "procedure_code": "Procedure pattern appears associated with elevated denial risk.",
    "provider_region": "Provider region shows elevated denial behavior patterns.",
    "provider_avg_billed": "Provider historically bills above average.",
    "provider_missing": "Provider-related information is incomplete.",
    "proc_missing": "Procedure information is missing."
}


# --------------------------------------------- #
# SHAP Intensity Mapping
# --------------------------------------------- #
def get_intensity(shap_value_abs):

    try:
        if shap_value_abs >= 1.5:
            return "VERY HIGH"

        elif shap_value_abs >= 1.0:
            return "HIGH"

        elif shap_value_abs >= 0.5:
            return "MEDIUM"

        else:
            return "LOW"

    except Exception as e:
        logger_exp.exception("Failed during SHAP intensity mapping.")

        raise IntensityMappingException(
            shap_value=shap_value_abs,
            reason=e   
        ) from e


# --------------------------------------------- #
# Claim Explanation Generator
# --------------------------------------------- #
def generate_claim_explanations(
    shap_values_row,
    feature_names,
    claim_row_data,
    threshold=0.3
):

    try:

        if shap_values_row is None:
            raise ValueError("shap_values_row cannot be None")

        if feature_names is None:
            raise ValueError("feature_names cannot be None")

        if claim_row_data is None:
            raise ValueError("claim_row_data cannot be None")

        explanations = []

        logger_exp.info("Generating claim explanations.")

        for feature, shap_val, raw_value in zip(
            feature_names,
            shap_values_row,
            claim_row_data
        ):

            contribution = abs(shap_val)

            # Skip weak contributions
            if contribution < threshold:
                continue

            base_explanation = explanation_dict.get(
                feature,
                f"{feature} contributed to the prediction."
            )

            # Format values safely
            try:
                display_value = (
                    round(float(raw_value), 2)
                    if isinstance(raw_value, (int, float, np.number))
                    else raw_value
                )

            except Exception:
                display_value = str(raw_value)

            direction = (
                "Increased denial risk"
                if shap_val > 0
                else "Reduced denial risk"
            )

            explanations.append({
                "feature": feature,
                "current_value": display_value,
                "intensity": get_intensity(contribution),
                "impact": direction,
                "shap_value": round(float(shap_val), 3),
                "explanation": (
                    f"{base_explanation} "
                    f"(Current Value: {display_value})"
                )
            })

        explanations = sorted(
            explanations,
            key=lambda x: abs(x["shap_value"]),
            reverse=True
        )

        logger_exp.info(
            f"Successfully generated {len(explanations)} explanations."
        )

        return explanations

    except Exception as e:

        logger_exp.exception("Failed to generate claim explanations.")

        raise ClaimExplanationGenerationException(
            feature_name=feature,
            reason=e
        ) from e


# --------------------------------------------- #
# Main Execution
# --------------------------------------------- #
if __name__ == "__main__":

    try:

        # Generate SHAP values
        shap_values = get_shapley_values()

        row_index = 0

        claim_shap = shap_values[row_index]

        claim_raw_data = X_test.iloc[row_index].values

        feature_names = list(X_test.columns)

        # Generate explanations
        final_explanations = generate_claim_explanations(
            claim_shap,
            feature_names,
            claim_raw_data,
            threshold=0.3
        )

        for item in final_explanations:

            print(
                f"[{item['intensity']}] "
                f"{item['explanation']} "
                f"| Impact: {item['impact']}"
            )

    except Exception as e:
        logger_exp.exception("Pipeline execution failed.")
        raise SHAPPipelineException(
            pipeline_stage="Explanation Generation",
            reason=e
        ) from e