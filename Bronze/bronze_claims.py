from util.utils import read_csv, INPUT_DIR, logger, spark
from util.errors.dao_errors import DataReadError, TableCreationError, SchemaConnectionError
from util.dao import DAO


def claim_bronze():
    """Ingests claims data from a CSV file and stores it in a SQLite database."""
    logger_instance = logger("logs/bronze_claims.log") # Set up logger for this function
    try:
        read_path = f"{INPUT_DIR}/claims.csv" # Define the path to the claims CSV file
        df = read_csv(spark, read_path) # Read claims data from CSV file
    except Exception as e:
        err = DataReadError(read_path)
        logger_instance.error(err.to_dict())
        return
    try:
        conn = DAO(spark, "newcatalog", "bronze") # Create a connection to the SQLite database
        conn.create_table("bronze_claims", df) # Create the bronze_claims table
    except (SchemaConnectionError, TableCreationError) as e:
        logger_instance.error(e.to_dict())
        return  

if __name__ == "__main__":
    claim_bronze()
