from util.utils import read_csv, INPUT_DIR, logger
from util.dao import DAO

def providers_bronze():
    """Ingests providers data from a CSV file and stores it in a SQLite database."""

    schema = """
    provider_id TEXT,
    doctor_name TEXT,
    specialty TEXT,
    location TEXT
    """
    logger_instance = logger("logs/bronze_providers.log")
    try:
        read_path = f"{INPUT_DIR}/providers.csv"
        df = read_csv(read_path)
    except Exception as e:
        logger_instance.error(f"Error occurred while reading providers data: {e}")
    
    try:
        conn = DAO("bronze.db")
        conn.create_table("bronze_providers", schema)
        conn.write("bronze_providers", df.values.tolist())
    except Exception as e:
        logger_instance.error(f"Error occurred while writing providers data to database: {e}")
        return

if __name__ == "__main__":
    providers_bronze()

