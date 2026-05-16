from util.utils import read_csv, INPUT_DIR, logger, spark
from util.errors.dao_errors import DataReadError, TableCreationError, SchemaConnectionError
from util.dao import DAO

def diagnosis_bronze():
    """Ingests diagnosis data from a CSV file and stores it in a SQLite database."""

    logger_instance = logger("logs/bronze_diagnosis.log")
    try:
        read_path = f"{INPUT_DIR}/diagnosis.csv"
        df = read_csv(spark, read_path)
    except Exception as e:
        err = DataReadError(read_path)
        logger_instance.error(err.to_dict())
        return 

    try:
        conn = DAO(spark, "newcatalog", "bronze")
        conn.create_table("bronze_diagnosis", df)
    except (SchemaConnectionError, TableCreationError) as e:
        logger_instance.error(e.to_dict())
        return 
    
if __name__ == "__main__":
    diagnosis_bronze()

