from util.utils import read_csv, INPUT_DIR, logger
from util.dao import DAO

def diagnosis_bronze():
    """Ingests diagnosis data from a CSV file and stores it in a SQLite database."""

    schema = """
    diagnosis_code TEXT,
    category TEXT,
    severity TEXT
    """
    logger_instance = logger("logs/bronze_diagnosis.log")
    try:
        read_path = f"{INPUT_DIR}/diagnosis.csv"
        df = read_csv(read_path)
    except Exception as e:
        logger_instance.error(f"Error occurred while reading diagnosis data: {e}")
        return 

    try:
        conn = DAO("bronze.db")
        conn.create_table("bronze_diagnosis", schema)
        conn.write("bronze_diagnosis", df.values.tolist())
    except Exception as e:
        logger_instance.error(f"Error occurred while writing diagnosis data to database: {e}")
        return 
    
if __name__ == "__main__":
    diagnosis_bronze()

