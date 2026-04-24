from util.utils import read_csv, INPUT_DIR, logger
from util.dao import DAO


def claim_bronze():
    """Ingests claims data from a CSV file and stores it in a SQLite database."""
    schema = """
    claim_id TEXT,
    patient_id TEXT,
    provider_id TEXT,
    diagnosis_code TEXT,
    procedure_code TEXT,
    billed_amount REAL,
    date TEXT
    """
    logger_instance = logger("logs/bronze_claims.log") # Set up logger for this function
    try:
        read_path = f"{INPUT_DIR}/claims.csv" # Define the path to the claims CSV file
        df = read_csv(read_path) # Read claims data from CSV file
    except Exception as e:
        logger_instance.error(f"Error occurred while reading claims data: {e}") 
        return
    try:
        conn = DAO("bronze.db") # Create a connection to the SQLite database
        conn.create_table("bronze_claims", schema) # Create the bronze_claims table with the defined schema
        conn.write("bronze_claims", df.values.tolist()) # Write the claims data to the bronze_claims table
    except Exception as e:
        logger_instance.error(f"Error occurred while writing claims data to database: {e}")
        return  

if __name__ == "__main__":
    claim_bronze()

