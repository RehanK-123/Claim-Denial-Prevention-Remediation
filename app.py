import config

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any

import joblib
import numpy as np
import pandas as pd 
from ML.xgboost_model import X_test
import os 
from Rule_Engine.rule_validation import RuleEngine
from RAG.retrieve_policy import retrieve_policies_for_claim, get_explanation_for_claim
from RAG.retrieve_remediation import retrieve_remediations_for_claim
from util.errors.rule_errors import (
    RuleEngineValidationException
)

app = FastAPI()

origins = [
    "http://localhost:3000",  # Default Create-React-App port
    "http://localhost:5173",  # Default Vite server port\
    "http://localhost:5174",  # FastAPI backend port
    "http://127.0.0.1:5174"
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Matches the incoming port
    allow_credentials=True,
    allow_methods=["*"],          # Permits your POST method
    allow_headers=["*"],          # Permits Content-Type configuration
)
engine = RuleEngine()


# ---------------------------------------------------
# REQUEST MODEL
# ---------------------------------------------------

class ClaimInput(BaseModel):

    claim_id: str
    patient_id: str
    provider_id: str
    diagnosis_code: str
    procedure_code: str
    billed_amount: float
    date: str

class PSearchResultItem(BaseModel):
    policy_id: str
    chunk_id: str
    chunk_text: str
    score: float

class RSearchResultItem(BaseModel):
    fix_id: str
    chunk_id: str
    chunk_text: str
    score: float = None  # Optional score field for remediation results, if available   


# ---------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------

@app.get("/health")
def health_check():

    return {
        "status": "UP"
    }


# ---------------------------------------------------
# CLAIM VALIDATION ENDPOINT
# ---------------------------------------------------
@app.post("/validate-claim")

def validate_claim(
    claim: ClaimInput
) -> dict[str, Any]:

    try:

        claim_dict = claim.dict()

        validation_result = engine.validate_claim(
            claim_dict
        )

        return {
            "status": validation_result["status"],
            "message": validation_result["message"]
        }

    except RuleEngineValidationException as e:

        return {
            "status": "FAILED",
            "message": str(e),
            "action_required": (
                "Please correct the claim input "
                "and submit again."
            )
        }

    except Exception as e:

        return {
            "status": "ERROR",
            "message": str(e)
        }


@app.post("/predict")
def predict_claim(
    claim: ClaimInput
) -> dict[str, Any]:

    from transformations import (
        enrich_claim_features
    )

    from ML.predict import (
        predict_claim_denial, encode_categorical_features
    )

    from LLM.denial_reasons import (
        generate_human_readable_explanation as generate_denial_explanation
    )

    from LLM.remediations import (
        generate_human_readable_explanation as generate_remediation_explanation
    )

    try:

        # ---------------------------------------------------
        # RAW INPUT
        # ---------------------------------------------------

        claim_dict = claim.dict()

        # ---------------------------------------------------
        # FEATURE ENRICHMENT
        # ---------------------------------------------------

        enriched_claim = enrich_claim_features(
            claim_dict
        )

        # ---------------------------------------------------
        # REMOVE NON-ML COLUMNS
        # ---------------------------------------------------

        ml_input = enriched_claim.copy()
        # ---------------------------------------------------
        # ML PREDICTION
        # ---------------------------------------------------

        ml_input = encode_categorical_features(
            pd.DataFrame([ml_input])
        )

        probability, prediction = predict_claim_denial(
            ml_input.iloc[0].to_dict())
        
        # ---------------------------------------------------
        # EXPLAINABILITY
        # ---------------------------------------------------
        if prediction == 0:  # If claim is predicted to be approved, we can skip explanation and retrieval steps
            return {
                "status": "SUCCESS",
                "raw_claim": claim_dict,
                "prediction": int(prediction),
                "probability": 1 - float(probability)
            }
        else:
            ml_input = ml_input.drop(columns=["claim_id", "patient_id", "date"], errors="ignore")
            explanations = get_explanation_for_claim(np.array(ml_input.iloc[0]))
            explanations_out = [str(exp["explanation"]) for exp in explanations]
            # ---------------------------------------------------
            # FINAL RESPONSE
            # ---------------------------------------------------
        
            policies = retrieve_policies_for_claim(explanations)

        #     llm_exp = generate_denial_explanation(
        #     claim_id=claim.claim_id,
        #     prediction="APPROVED" if prediction == 0 else "DENIED",
        #     denial_probability=probability,
        #     policy_chunks= policies,
        #     shap_output_lines= explanations,
        # )

            cleaned_policies = [
                PSearchResultItem(
                    policy_id=str(row[0]),
                    chunk_id=str(row[1]),
                    chunk_text=str(row[2]),
                    score= float(row[3])
                )
                for row in policies
                ]

            remediation = retrieve_remediations_for_claim(explanations)
            cleaned_remediation = [
                RSearchResultItem(
                    fix_id=str(row[0]),
                    chunk_id=str(row[1]),
                    chunk_text=str(row[2]),
                    score= float(row[3]) if len(row) > 3 else None
                )
                for row in remediation
            ]

            return {

                "status": "SUCCESS",

                "raw_claim": claim_dict,

                "transformed_claim": ml_input.to_dict(orient="records")[0],

                "prediction": int(prediction),

                "explanations": explanations_out,

                # "llm_explanations": llm_exp, 

                "relevant_policies": cleaned_policies,

                "recommended_remediation": cleaned_remediation 
            }

    except Exception as e:

        return {

            "status": "ERROR",

            "message": str(e)
        }