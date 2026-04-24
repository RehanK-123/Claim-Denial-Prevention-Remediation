import pandas as pd 
import logging

INPUT_DIR = "Input/"

def read_csv(file_path):
    """
    Reads a CSV file and returns a pandas DataFrame.

    Parameters:
    file_path (str): The path to the CSV file.

    Returns:
    pd.DataFrame: A DataFrame containing the data from the CSV file.
    """
    try:
        df = pd.read_csv(file_path)
        return df
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
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame.")
    
    diagnosis = {
        'missing_values': df.isnull().sum(),
        'data_types': df.dtypes,
        'shape': df.shape,
        'columns': df.columns.tolist(),
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
