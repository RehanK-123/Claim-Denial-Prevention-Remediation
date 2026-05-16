from .base import AppError

class InvalidClaimError(AppError):
    def __init__(self, reason):
        super().__init__(
            code="CLM-VAL-001",
            message="Invalid claim data",
            details={"reason": reason}
        )