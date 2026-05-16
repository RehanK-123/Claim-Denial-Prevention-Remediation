import pandas as pd 
import logging
from databricks.connect import DatabricksSession
from pyspark.sql import functions as F
import os 


DATABRICKS_TOKEN_ID = os.getenv("DATABRICKS_TOKEN_ID")
DATABRICKS_HOST_URL = os.getenv("DATABRICKS_HOST_URL")

INPUT_DIR = "/Volumes/newcatalog/newschema/input/"

def getSparkSession():
    try:
        spark = DatabricksSession.builder.remote(host = DATABRICKS_HOST_URL,
        serverless= True,
token= DATABRICKS_TOKEN_ID).getOrCreate() #getting or creating the spark session for the databricks workspace session 
    except:
        raise ValueError("No active SparkSession found.")
    return spark

spark = getSparkSession()

def read_csv(spark, file_path):
    """
    Reads a CSV file and returns a pandas DataFrame.

    Parameters:
    file_path (str): The path to the CSV file.

    Returns:
    pd.DataFrame: A DataFrame containing the data from the CSV file.
    """
    try:
        return spark.read.csv(file_path, header=True, inferSchema=True)
    except Exception as e:
        raise IOError(f"Error reading the CSV file: {e}")
    

def diagnose_data(df):
    """
    Diagnoses the DataFrame for missing values and data types.

    Parameters:
    df (pd.DataFrame): The DataFrame to diagnose.

    Returns:
    dict: A dictionary containing the diagnosis results.
    """
    
    diagnosis = {
        'missing_values': df.select([F.count(F.when(F.col(c).isNull(), c)).alias(c) for c in df.columns]),
        'data_types': df.dtypes,
        'shape': (df.count(), len(df.columns)),
        'columns': df.columns,
        'description': df.describe()
    }

    return diagnosis

def logger(log_file, lvl=logging.INFO):
    """
    Sets up a logger to log messages to a specified file.

    Parameters:
    log_file (str): The path to the log file.

    Returns:
    logging.Logger: A configured logger instance.
    """
    logging.basicConfig(filename=log_file, level=lvl,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger()
