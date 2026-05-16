from util.errors.base import AppError


class ModelLoadingException(AppError):

    def __init__(self, model_uri, reason=None):

        super().__init__(
            code="CLM-ML-001",
            message="Failed to load ML model",
            details={
                "model_uri": model_uri,
                "reason": str(reason) if reason else None
            }
        )


class SHAPExplainerException(AppError):

    def __init__(self, model_name, reason=None):

        super().__init__(
            code="CLM-ML-002",
            message="Failed to initialize SHAP explainer",
            details={
                "model_name": model_name,
                "reason": str(reason) if reason else None
            }
        )


class SHAPValueGenerationException(AppError):

    def __init__(self, dataset_name=None, reason=None):

        super().__init__(
            code="CLM-ML-003",
            message="Failed to generate SHAP values",
            details={
                "dataset_name": dataset_name,
                "reason": str(reason) if reason else None
            }
        )


class IntensityMappingException(AppError):

    def __init__(self, shap_value=None, reason=None):

        super().__init__(
            code="CLM-ML-004",
            message="Failed during SHAP intensity mapping",
            details={
                "shap_value": shap_value,
                "reason": str(reason) if reason else None
            }
        )


class ClaimExplanationGenerationException(AppError):

    def __init__(self, feature_name=None, reason=None):

        super().__init__(
            code="CLM-ML-005",
            message="Failed to generate claim explanations",
            details={
                "feature_name": feature_name,
                "reason": str(reason) if reason else None
            }
        )


class SHAPPipelineException(AppError):

    def __init__(self, pipeline_stage=None, reason=None):

        super().__init__(
            code="CLM-ML-006",
            message="SHAP explanation pipeline execution failed",
            details={
                "pipeline_stage": pipeline_stage,
                "reason": str(reason) if reason else None
            }
        )

class DataLoadingException(AppError):

    def __init__(self, table_name=None, reason=None):

        super().__init__(
            code="CLM-ML-007",
            message="Failed to load training dataset",
            details={
                "table_name": table_name,
                "reason": str(reason) if reason else None
            }
        )


class DataPreprocessingException(AppError):

    def __init__(self, column_name=None, reason=None):

        super().__init__(
            code="CLM-ML-008",
            message="Failed during data preprocessing",
            details={
                "column_name": column_name,
                "reason": str(reason) if reason else None
            }
        )


class DataSplitException(AppError):

    def __init__(self, reason=None):

        super().__init__(
            code="CLM-ML-009",
            message="Failed during train-test split",
            details={
                "reason": str(reason) if reason else None
            }
        )


class OptunaOptimizationException(AppError):

    def __init__(self, trial_number=None, reason=None):

        super().__init__(
            code="CLM-ML-010",
            message="Optuna hyperparameter optimization failed",
            details={
                "trial_number": trial_number,
                "reason": str(reason) if reason else None
            }
        )


class ModelTrainingException(AppError):

    def __init__(self, model_name=None, reason=None):

        super().__init__(
            code="CLM-ML-011",
            message="Model training failed",
            details={
                "model_name": model_name,
                "reason": str(reason) if reason else None
            }
        )


class ModelEvaluationException(AppError):

    def __init__(self, metric_name=None, reason=None):

        super().__init__(
            code="CLM-ML-012",
            message="Model evaluation failed",
            details={
                "metric_name": metric_name,
                "reason": str(reason) if reason else None
            }
        )


class MLflowLoggingException(AppError):

    def __init__(self, artifact_type=None, reason=None):

        super().__init__(
            code="CLM-ML-013",
            message="MLFlow logging failed",
            details={
                "artifact_type": artifact_type,
                "reason": str(reason) if reason else None
            }
        )


class ModelPipelineException(AppError):

    def __init__(self, pipeline_stage=None, reason=None):

        super().__init__(
            code="CLM-ML-014",
            message="ML training pipeline execution failed",
            details={
                "pipeline_stage": pipeline_stage,
                "reason": str(reason) if reason else None
            }
        )

class LLMExplanationGenerationException(AppError):

    def __init__(self, claim_id=None, reason=None):

        super().__init__(
            code="CLM-LLM-001",
            message="Failed to generate human-readable claim explanation",
            details={
                "claim_id": claim_id,
                "reason": str(reason) if reason else None
            }
        )


class PromptConstructionException(AppError):

    def __init__(self, reason=None):

        super().__init__(
            code="CLM-LLM-002",
            message="Failed to construct LLM prompt",
            details={
                "reason": str(reason) if reason else None
            }
        )


class SHAPParsingException(AppError):

    def __init__(self, raw_line=None, reason=None):

        super().__init__(
            code="CLM-LLM-003",
            message="Failed to parse SHAP explanation output",
            details={
                "raw_line": raw_line,
                "reason": str(reason) if reason else None
            }
        )

class PredictionException(AppError):

    def __init__(self, claim_id=None, reason=None):

        super().__init__(
            code="CLM-ML-015",
            message="Failed to predict claim denial risk",
            details={
                "claim_id": claim_id,
                "reason": str(reason) if reason else None
            }
        )