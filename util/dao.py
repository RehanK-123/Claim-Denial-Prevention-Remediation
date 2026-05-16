from util.errors.dao_errors import TableNotFoundError, SchemaConnectionError, TableCreationError

class DAO:
    def __init__(self, spark, catalog: str, schema: str):
        self.spark = spark
        self.catalog = catalog
        self.schema = schema
        self.full_schema = f"{catalog}.{schema}"
        
        self._ensure_schema_exists()

    def _ensure_schema_exists(self):
        """
        Create schema if it does not exist
        """
        try:
            self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.full_schema}")
        
        except Exception as e:
            raise SchemaConnectionError(self.full_schema) from e 

    def create_table(self, table_name: str, df, mode: str = "overwrite"):
        """
        Create or overwrite a table

        mode options:
        - 'error' (default): fail if exists
        - 'overwrite': replace table
        - 'append': add data
        """
        full_table_name = f"{self.full_schema}.{table_name}"

        try:
            df.write.mode(mode).saveAsTable(full_table_name)
        
        except Exception as e:
            raise TableCreationError(table_name) from e 

    def read_table(self, table_name: str):
        """
        Read a table from schema
        """
        full_table_name = f"{self.full_schema}.{table_name}"

        if not self.table_exists(table_name):
            raise TableNotFoundError(full_table_name)

        return self.spark.table(full_table_name)

    def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists
        """
        full_table_name = f"{self.full_schema}.{table_name}"
        return self.spark.catalog.tableExists(full_table_name)