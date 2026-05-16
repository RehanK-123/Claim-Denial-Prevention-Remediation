from util.utils import logger
import mlflow.xgboost
import mlflow
import os
import pandas as pd 
from sklearn.preprocessing import LabelEncoder
from .xgboost_model import X_test
from util.errors.ml_errors import (
    DataPreprocessingException,
    ModelLoadingException,
    PredictionException
)
from transformations import enrich_claim_features
import joblib

def encode_categorical_features(claim_df):
    categorical_cols = [
        col for col in claim_df.select_dtypes(include=["object"]).columns
        if col != "label"
    ]

    for col in categorical_cols:

        try:

            le = LabelEncoder()

            claim_df[col] = le.fit_transform(
                claim_df[col].astype(str)
            )

        except Exception as col_error:

            raise DataPreprocessingException(
                column_name=col,
                reason=col_error
            ) from col_error

    return claim_df

def predict_claim_denial(claim_data):
    
    logger_pred = logger("logs/predict_claim_denial.log")

    try:
        os.environ["DATABRICKS_TOKEN"] = os.getenv("DATABRICKS_TOKEN_ID")

        mlflow.set_tracking_uri("databricks")

        model_name = "xgboost_v1"
        model_version = "latest"

        # Load model from registry
        model_uri = "models:/workspace.default.xgboost_v1/1"
        model = mlflow.xgboost.load_model(model_uri)
        joblib.dump(
            model,
            "artifacts/xgb_model.pkl"
        )

        logger_pred.info("XGBoost model loaded successfully from MLFlow registry.")

    except Exception as e:
        logger_pred.exception("Failed to load ML model.")
        raise ModelLoadingException(
            model_uri=model_uri,
            reason=e
        ) from e

    try:
        # Ensure claim_data is in the correct format for prediction
        claim_df = pd.DataFrame([claim_data])  # Convert dict to DataFrame
        claim_df = claim_df[X_test.columns]  # Ensure same feature order

        # Make prediction
        pred_proba = model.predict_proba(claim_df)[:, 1][0]  # Probability of denial
        pred_label = model.predict(claim_df)[0]  # Predicted class label

        logger_pred.info(f"Prediction made successfully. Denial probability: {pred_proba}, Predicted label: {pred_label}")

    except Exception as e:
        logger_pred.exception("Failed to make prediction.")
        raise PredictionException(
            claim_id=claim_data.get("claim_id", "unknown"),
            reason=e
        ) from e

    return pred_proba, pred_label

if __name__ == "__main__":
    # Sample claim data for testing
    sample_claim = {
        "claim_id": "C0002",
        "patient_id": "P177",
        "provider_id": "PR105",
        "diagnosis_code": "D10",
        "procedure_code": "PROC3",
        "billed_amount": 28733.0,
        "date": "2024-02-22"
        # Add other necessary features as required by the model
    }

    transformed_claim = enrich_claim_features(sample_claim)  # Ensure claim is transformed before prediction
    df = pd.DataFrame([transformed_claim])  # Convert to DataFrame for preprocessing
    df.drop(columns=["claim_id", "patient_id", "date"], inplace=True)  # Drop non-feature columns
    df = encode_categorical_features(df)
    print(df.head())

    pred_proba, pred_label = predict_claim_denial(df.iloc[0].to_dict())
    print(f"Denial Probability: {pred_proba}, Predicted Label: {pred_label}")
