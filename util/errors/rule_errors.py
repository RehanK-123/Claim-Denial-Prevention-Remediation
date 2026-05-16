from util.errors.base import AppError

class RuleEngineValidationException(AppError):

    def __init__(self, code, message, details=None):

        self.code = code
        self.message = message
        self.details = details or {}

        super().__init__(self.code, self.message, self.details)

    def __str__(self):

        return (
            f"[{self.code}] {self.message} "
            f"| Details: {self.details}"
        )


class MissingFieldException(RuleEngineValidationException):

    def __init__(self, field_name):

        super().__init__(
            code="CLM-RULE-001",
            message="Required field is missing",
            details={
                "field_name": field_name
            }
        )


class InvalidDatatypeException(RuleEngineValidationException):

    def __init__(self, field_name, expected_type, actual_value):

        super().__init__(
            code="CLM-RULE-002",
            message="Invalid datatype detected",
            details={
                "field_name": field_name,
                "expected_type": expected_type,
                "actual_value": actual_value
            }
        )


class InvalidDateFormatException(RuleEngineValidationException):

    def __init__(self, field_name, actual_value):

        super().__init__(
            code="CLM-RULE-003",
            message="Invalid date format detected",
            details={
                "field_name": field_name,
                "expected_format": "YYYY-MM-DD",
                "actual_value": actual_value
            }
        )

class InvalidProcedureDiagnosisMappingException(
    RuleEngineValidationException
):
    def __init__(self, diagnosis_code, procedure_code):

        super().__init__(
            code="CLM-RULE-004",
            message="Invalid procedure-diagnosis mapping detected",
            details={
            f"Procedure code '{procedure_code}' "
            f"is not valid for diagnosis '{diagnosis_code}'"
            }
        )

class InvalidCodeFormatException(
    RuleEngineValidationException
):
    def __init__(self, field_name, actual_value):

        super().__init__(
            code="CLM-RULE-005",
            message="Invalid code format detected",
            details={
                "field_name": field_name,
                "actual_value": actual_value
            }
        )