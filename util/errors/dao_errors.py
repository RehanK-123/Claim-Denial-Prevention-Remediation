from .base import AppError

class TableNotFoundError(AppError):
    def __init__(self, table_name):
        super().__init__(
            code="CLM-DAO-001",
            message=f"Table not found: {table_name}",
            details={"table": table_name}
        )

class DataWriteError(AppError):
    def __init__(self, table_name):
        super().__init__(
            code="CLM-DAO-002",
            message="Failed to write data",
            details={"table": table_name}
        )

class DataReadError(AppError):
    def __init__(self, file_path):
        super().__init__(
            code="CLM-DAO-003",
            message="Failed to read input data",
            details={"file_path": file_path}
        )


class TableCreationError(AppError):
    def __init__(self, table_name):
        super().__init__(
            code="CLM-DAO-004",
            message="Failed to create table",
            details={"table_name": table_name}
        )


class SchemaConnectionError(AppError):
    def __init__(self, schema):
        super().__init__(
            code="CLM-DAO-005",
            message="Failed to connect or create schema",
            details={"schema": schema}
        )


class DuplicateDataError(AppError):
    def __init__(self, column):
        super().__init__(
            code="CLM-DAO-006",
            message="Duplicate records found",
            details={"column": column}
        )


class DataTransformationError(AppError):
    def __init__(self, step):
        super().__init__(
            code="CLM-DAO-007",
            message="Error during data transformation",
            details={"step": step}
        )