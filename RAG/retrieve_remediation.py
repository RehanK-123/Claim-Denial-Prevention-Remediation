from databricks.vector_search.client import VectorSearchClient
from ML.explainability import get_shapley_values, generate_claim_explanations
from ML.xgboost_model import X_test
import numpy as np 
import os 

DATABRICKS_TOKEN_ID = os.getenv("DATABRICKS_TOKEN_ID")
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")

#------------CONFIG---------------- #
# Connect using Personal Access Token (PAT)
vsc = VectorSearchClient(
    workspace_url= DATABRICKS_HOST,
    personal_access_token= DATABRICKS_TOKEN_ID
)

index = vsc.get_index(index_name="newcatalog.gold.remediation_embeddings")

def get_explanation_for_claim(data):
    data_reshaped = data.reshape(1, -1)
    claim_shap = get_shapley_values(data_reshaped) if data_reshaped is not None else get_shapley_values() 

    claim_raw_data = data.values if hasattr(data, "values") else data_reshaped.flatten().tolist()
    feature_names = list(X_test.columns)
    explanations = generate_claim_explanations(claim_shap[0], feature_names, claim_raw_data)
    return explanations

def retrieve_remediations_for_claim(final_explanations):
   # Create a clean, comma-separated list of attributes
    explanation_terms = [exp["explanation"] for exp in final_explanations]
    attributes_str = ", ".join(explanation_terms)

    # Standardized template
    retrieval_query = f"Remediation search for insurance claims with features: {attributes_str}."


    results = index.similarity_search(
        query_text= retrieval_query,
        # query_vector= "Add custom calculated query embedding for similarity search or relevant retrieval"
        columns=["fix_id", "chunk_id", "chunk_text"],
        num_results=3 
    )
    
    return results["result"]["data_array"]

if __name__ == "__main__":
    claim_data = np.array(X_test.iloc[0]) #get data for first claim in X_test
    final_explanations = get_explanation_for_claim(claim_data)
    remediations = retrieve_remediations_for_claim(final_explanations)

    print("Relevant remediations retrieved for the claim:" \
    "" \
    "" \
    "" \
    "")
    print(remediations)

