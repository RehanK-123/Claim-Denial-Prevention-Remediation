import databricks.vector_search
import os
from google.cloud import secretmanager

def _get_gcp_secret(secret_id: str, version_id: str = "latest") -> str:
    """Internal helper to safely fetch a secret once from GCP."""
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        project_id = "your-gcp-project-id" 

    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"⚠️ Warning: Could not load secret [{secret_id}]: {e}")
        return ""

# --- Global Injection into Environment Variables ---
# We map the GCP Secret names to the standard OS variables Databricks expects
# os.environ["DATABRICKS_HOST"]       = _get_gcp_secret("databricks-host")
# os.environ["DATABRICKS_TOKEN"]      = _get_gcp_secret("databricks-token")
# os.environ["DATABRICKS_CLUSTER_ID"] = _get_gcp_secret("databricks-cluster-id")
# os.environ["COGNITO_CLIENT_SECRET"] = _get_gcp_secret("cognito-client-secret")

def setup_environment():
    """Call this function at the start of your application to set up environment variables."""
    os.environ["DATABRICKS_HOST_URL"] = "https://dbc-19cd72a7-6a95.cloud.databricks.com/?o=7474651951534513"
    os.environ["DATABRICKS_TOKEN_ID"] = "dapic3729e20cb7a2f401d58b3254c80afee"
    os.environ["DATABRICKS_HOST"] = "https://dbc-19cd72a7-6a95.cloud.databricks.com"