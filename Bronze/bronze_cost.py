from util.utils import read_csv, INPUT_DIR, logger, spark
from util.errors.dao_errors import DataReadError, TableCreationError, SchemaConnectionError
from util.dao import DAO

def cost_bronze():
    """Ingests costs data from a CSV file and stores it in a SQLite database."""

    logger_instance = logger("logs/bronze_cost.log") # Set up logger for this function
    try:
        read_path = f"{INPUT_DIR}/cost.csv" 
        df = read_csv(spark, read_path)
    except Exception as e:
        err = DataReadError(read_path)
        logger_instance.error(err.to_dict()) 
        return
    try: 
        conn = DAO(spark, "newcatalog", "bronze")
        conn.create_table("bronze_cost", df)
    except (SchemaConnectionError, TableCreationError) as e:
        logger_instance.error(e.to_dict())
        return  

if __name__ == "__main__":
    cost_bronze()

#comment and description 
#log exceptions 
#create architecture flow - hld lld 
#hipaa compliance 