from util.errors.registry import ERROR_CODES

class AppError(Exception):
    def __init__(self, code: str, message: str, details: dict=None):
        if code not in ERROR_CODES:
            raise ValueError(f"Invalid error code: {code}")

        self.code = code
        self.message = message
        self.details = details or {}

        super().__init__(f"[{code}] {message}")

    def to_dict(self):
        return {
            "error_code": self.code,
            "message": self.message,
            "details": self.details
        }