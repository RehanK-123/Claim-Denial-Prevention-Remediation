from datetime import datetime
import re
from util.errors.rule_errors import (
    InvalidCodeFormatException,
    MissingFieldException,
    InvalidDatatypeException,
    InvalidDateFormatException,
    RuleEngineValidationException,
    InvalidProcedureDiagnosisMappingException
)


CODE_PATTERNS = {
    "claim_id": r"^C\d{4}$",
    "patient_id": r"^P\d{3}$",
    "provider_id": r"^PR\d{3}$",
    "diagnosis_code": r"^[A-Z]\d{2,4}$",
    "procedure_code": r"^PROC\d{1,4}$"
}

class RuleEngine:

    REQUIRED_SCHEMA = {
        "claim_id": str,
        "patient_id": str,
        "provider_id": str,
        "diagnosis_code": str,
        "procedure_code": str,
        "billed_amount": float,
        "date": "date"
    }

    ICD_CPT_MAPPING = {
        "D50": ["PROC1", "PROC2","PROC6"],
        "I10": ["PROC3"],
        "E11": ["PROC4", "PROC5"]
    }

    def validate_required_fields(self, claim_record):

        for field in self.REQUIRED_SCHEMA.keys():

            if (
                field not in claim_record
                or claim_record[field] is None
                or str(claim_record[field]).strip() == ""
            ):

                raise MissingFieldException(field)
            
    def validate_field_patterns(self, claim_record):

        for field, pattern in CODE_PATTERNS.items():

            value = claim_record[field]

            if not re.match(pattern, str(value)):

                raise InvalidCodeFormatException(
                    field_name=field,
                    actual_value=value
                )

    def validate_datatypes(self, claim_record):

        for field, expected_type in self.REQUIRED_SCHEMA.items():

            value = claim_record[field]

            # DATE VALIDATION
            if expected_type == "date":

                try:

                    datetime.strptime(
                        value,
                        "%Y-%m-%d"
                    )

                except Exception:

                    raise InvalidDateFormatException(
                        field_name=field,
                        actual_value=value
                    )

            # FLOAT VALIDATION
            elif expected_type == float:

                try:

                    float(value)

                except Exception:

                    raise InvalidDatatypeException(
                        field_name=field,
                        expected_type="float",
                        actual_value=value
                    )

            # STRING VALIDATION
            elif expected_type == str:

                if not isinstance(value, str):

                    raise InvalidDatatypeException(
                        field_name=field,
                        expected_type="string",
                        actual_value=value
                    )

    def validate_icd_cpt_mapping(self, claim_record):

        diagnosis_code = claim_record["diagnosis_code"]
        procedure_code = claim_record["procedure_code"]

        allowed_procedures = self.ICD_CPT_MAPPING.get(
            diagnosis_code,
            []
        )

        if procedure_code not in allowed_procedures:

            raise InvalidProcedureDiagnosisMappingException(
                diagnosis_code=diagnosis_code,
                procedure_code=procedure_code
            )

    def validate_claim(self, claim_record):

        self.validate_field_patterns(
            claim_record
        )

        self.validate_required_fields(
            claim_record
        )

        self.validate_datatypes(
            claim_record
        )

        self.validate_icd_cpt_mapping(
            claim_record
        )

        return {
            "status": "SUCCESS",
            "message": "Claim validation passed"
        }


if __name__ == "__main__":

    sample_claim = {
        "claim_id": "C0002",
        "patient_id": "P177",
        "provider_id": "PR105",
        "diagnosis_code": "I10",
        "procedure_code": "PROC3",
        "billed_amount": 28733.0,
        "date": "2024-02-22"
    }

    engine = RuleEngine()

    try:

        result = engine.validate_claim(
            sample_claim
        )

        print(result)

    except RuleEngineValidationException as e:

        print(str(e))