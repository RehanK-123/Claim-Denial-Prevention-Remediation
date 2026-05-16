from .base import AppError  


# ---------------------------------------------------
# CUSTOM ERRORS
# ---------------------------------------------------

class ProviderNotFoundException(AppError):

    def __init__(self, provider_id):

        super().__init__(
            code="CLM-TRF-001",
            message="Provider not found",
            details={"provider_id": provider_id}
        )


class DiagnosisNotFoundException(AppError):

    def __init__(self, diagnosis_code):

        super().__init__(
            code="CLM-TRF-002",
            message="Diagnosis not found",
            details={"diagnosis_code": diagnosis_code}
        )


class CostNotFoundException(AppError):

    def __init__(self, procedure_code):

        super().__init__(
            code="CLM-TRF-003",
            message="Cost benchmark not found",
            details={"procedure_code": procedure_code}
        )