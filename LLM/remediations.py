import os
from ML.xgboost_model import X_test
from RAG.retrieve_policy import retrieve_policies_for_claim
from util.utils import logger
import numpy as np

from util.errors.ml_errors import (
    PromptConstructionException,
    LLMExplanationGenerationException
)

from RAG.retrieve_remediation import get_explanation_for_claim, retrieve_remediations_for_claim
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
import os 


os.environ["DATABRICKS_TOKEN"] = os.getenv("DATABRICKS_TOKEN_ID")
logger_instance = logger("logs/remediations.log")


# ------------------------------------------------ #
# PROMPT BUILDER
# ------------------------------------------------ #
def build_claim_explanation_prompt(
    claim_id,
    prediction,
    denial_probability,
    parsed_explanations,
    remediation_chunks="N/A"
):

    try:

        formatted_explanations = "\n".join([
            (
                f"- Intensity: {item['intensity']}\n"
                f"  Explanation: {item['explanation']}\n"
                f"  Current Value: {item['current_value']}\n"
            )
            for item in parsed_explanations
        ])

        prompt = f"""
You are an expert healthcare insurance claims investigator.

Your task is to generate a professional reasons for remediations using the provided remediation information.

----------------------------------------
OBJECTIVE
----------------------------------------
Generate a concise human-readable description of HOW the claim can be remediated to APPROVED.

----------------------------------------
STRICT INSTRUCTIONS
----------------------------------------
1. Write in formal professional English.
2. Keep the response between 120-180 words.
3. Summarize the strongest remediation factors first.
4. Explain whether the remediation appears straightforward or complex.
5. Remember to consider the remediation context when suggesting remediations.
6. Write naturally like an insurance claim investigator.
7. Return ONLY the final remediation explanation paragraph.
8. NEVER mention:
   - SHAP
   - AI
   - Machine Learning
   - Model
   - Feature importance
   - Numerical contribution scores
9. Do not repeat the raw bullet explanations verbatim.
10. Write naturally like an insurance claim investigator.
11. Return ONLY the final explanation paragraph.

----------------------------------------
CLAIM INFORMATION
----------------------------------------
Claim ID: {claim_id}

Predicted Outcome: {prediction}

Denial Probability: {round(denial_probability, 4)}

----------------------------------------
CLAIM CONTRIBUTION SIGNALS
----------------------------------------
{formatted_explanations}

----------------------------------------
REMEDIATION CONTEXT
----------------------------------------
{remediation_chunks}
----------------------------------------
EXPECTED STYLE
----------------------------------------
Example:

"To remediate the identified risks, the claim should undergo targeted correction and validation before submission. 
    Recommended remediation actions include:
        * Review and normalize billed amounts against historical reimbursement benchmarks and payer fee schedules.
        * Validate diagnosis specificity and ensure clinical documentation adequately supports treatment complexity and medical necessity.
        * Confirm that all required CPT/HCPCS modifiers, provider identifiers, and supporting encounter documentation are complete and correctly mapped.
        * Audit provider billing patterns and verify that no duplicate or excessive utilization indicators are present.
        * Attach supplemental physician notes, operative reports, or medical necessity documentation where applicable.
        * Re-evaluate the claim through the rules engine and denial prediction pipeline after corrections are completed.
Following remediation, the claims denial probability is expected to decrease substantially, provided that coding accuracy, documentation completeness, and reimbursement alignment are successfully validated prior to final submission."

Generate the final explanation now.
"""

        return prompt

    except Exception as e:

        logger_instance.exception(
            "Prompt construction failed."
        )

        raise PromptConstructionException(
            reason=e
        ) from e


# ------------------------------------------------ #
# LLM EXPLANATION GENERATOR
# ------------------------------------------------ #
def generate_human_readable_explanation(
    claim_id,
    prediction,
    denial_probability,
    shap_output_lines,
    remediation_chunks="N/A",
    model_name="gpt-4o-mini"
):

    try:

        logger_instance.info(
            f"Generating explanation for claim: {claim_id}"
        )

        prompt = build_claim_explanation_prompt(
            claim_id=claim_id,
            prediction=prediction,
            denial_probability=denial_probability,
            remediation_chunks=remediation_chunks,
            parsed_explanations=shap_output_lines
        )

        w = WorkspaceClient()

        response = w.serving_endpoints.query(
            name="claims_llm",
            messages=[
            ChatMessage(role=ChatMessageRole.SYSTEM, content="You are a senior healthcare claims review specialist."),
            ChatMessage(role=ChatMessageRole.USER, content=prompt)
            ]
        )

        final_explanation = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        logger_instance.info(
            f"Explanation generated successfully "
            f"for claim: {claim_id}"
        )

        return final_explanation

    except Exception as e:

        logger_instance.exception(
            "LLM explanation generation failed."
        )

        raise LLMExplanationGenerationException(
            claim_id=claim_id,
            reason=e
        ) from e


# ------------------------------------------------ #
# SAMPLE EXECUTION
# ------------------------------------------------ #
if __name__ == "__main__":

    # Sample SHAP output lines for a claim
    claim_data = np.array(X_test.iloc[0]) #get data for first claim in X_test
    shap_output_lines = get_explanation_for_claim(claim_data)
    try:
        remediation_chunks = retrieve_remediations_for_claim(
            shap_output_lines
        )   

        explanation = generate_human_readable_explanation(
            claim_id="C0002",
            prediction="APPROVED",
            denial_probability=0.12,
            remediation_chunks= remediation_chunks,
            shap_output_lines=shap_output_lines
        )

        print("\n")
        print("FINAL CLAIM SUMMARY")
        print("---------------------------")
        print(explanation)

    except Exception as e:

        logger_instance.exception(
            "Execution failed."
        )

        print(str(e))