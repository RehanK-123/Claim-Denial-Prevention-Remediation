import os
from ML.xgboost_model import X_test
from util.utils import logger
import numpy as np

from util.errors.ml_errors import (
    PromptConstructionException,
    LLMExplanationGenerationException
)

from RAG.retrieve_policy import get_explanation_for_claim, retrieve_policies_for_claim
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
import os 


os.environ["DATABRICKS_TOKEN"] = os.getenv("DATABRICKS_TOKEN_ID")
logger_instance = logger("logs/human_explain.log")


# ------------------------------------------------ #
# PROMPT BUILDER
# ------------------------------------------------ #
def build_claim_explanation_prompt(
    claim_id,
    prediction,
    denial_probability,
    parsed_explanations,
    policy_chunks="N/A"
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

Your task is to generate a professional claim review summary using the provided feature contribution explanations.

----------------------------------------
OBJECTIVE
----------------------------------------
Generate a concise human-readable explanation describing WHY the claim was predicted as either APPROVED or DENIED.

----------------------------------------
STRICT INSTRUCTIONS
----------------------------------------
1. Write in formal professional English.
2. Keep the response between 120-180 words.
3. Summarize the strongest contributing factors first.
4. Explain whether the claim appears financially normal or suspicious.
5. Mention provider behavior abnormalities where relevant.
6. Mention diagnosis or documentation concerns where relevant.
7. NEVER mention:
   - SHAP
   - AI
   - Machine Learning
   - Model
   - Feature importance
   - Numerical contribution scores
8. Do not repeat the raw bullet explanations verbatim.
9. Write naturally like an insurance claim investigator.
10. Return ONLY the final explanation paragraph.

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
POLICY CONTEXT
----------------------------------------
{policy_chunks}
----------------------------------------
EXPECTED STYLE
----------------------------------------
Example:

"The claim demonstrates relatively consistent billing behavior across several financial indicators, including diagnosis-related cost alignment and provider billing trends. Regional expenditure patterns also appear stable when compared against historical benchmarks. While the billed amount is moderately elevated, the overall documentation and treatment characteristics remain aligned with expected claim behavior, reducing the likelihood of denial concerns."

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
    policy_chunks="N/A",
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
            policy_chunks=policy_chunks,
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
        policy_chunks = retrieve_policies_for_claim(
            shap_output_lines
        )   

        explanation = generate_human_readable_explanation(
            claim_id="C0002",
            prediction="APPROVED",
            denial_probability=0.12,
            policy_chunks= policy_chunks,
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