from util.utils import read_csv, INPUT_DIR, logger
from util.dao import DAO

def cost_bronze():
    """Ingests costs data from a CSV file and stores it in a SQLite database."""

    schema = """
    procedure_code TEXT,
    average_cost REAL,  
    expected_cost REAL,
    region TEXT
    """
    logger_instance = logger("logs/bronze_cost.log") # Set up logger for this function
    try:
        read_path = f"{INPUT_DIR}/cost.csv" 
        df = read_csv(read_path)
    except Exception as e:
        logger_instance.error(f"Error occurred while reading costs data: {e}") 
        return
    try: 
        conn = DAO("bronze.db")
        conn.create_table("bronze_cost", schema)
        conn.write("bronze_cost", df.values.tolist())
    except Exception as e:
        logger_instance.error(f"Error occurred while writing costs data to database: {e}")
        return  

if __name__ == "__main__":
    cost_bronze()

#comment and description 
#log exceptions 
#create architecture flow - hld lld 
#hipaa compliance 