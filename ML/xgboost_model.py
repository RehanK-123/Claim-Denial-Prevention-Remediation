import mlflow
import xgboost as xgb
import pandas as pd
import os
import optuna

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    roc_auc_score,
    accuracy_score,
    classification_report
)
from sklearn.model_selection import StratifiedKFold

from util.utils import spark, logger
from util.dao import DAO

from util.errors.ml_errors import (
    DataLoadingException,
    DataPreprocessingException,
    DataSplitException,
    OptunaOptimizationException,
    ModelTrainingException,
    ModelEvaluationException,
    MLflowLoggingException,
    ModelPipelineException
)

logger_xg = logger("logs/xgboost_model.log")
# ---------------- CONFIG ---------------- #
try:

    os.environ["DATABRICKS_TOKEN"] = os.getenv("DATABRICKS_TOKEN_ID")

    EXPERIMENT_NAME = (
        "/Users/rehansk123.rk@gmail.com/"
        "Claim_Denial_Prevention"
    )

    mlflow.set_tracking_uri("databricks")
    mlflow.set_experiment(EXPERIMENT_NAME)

    logger_xg.info("MLFlow configuration initialized successfully.")

except Exception as e:

    logger_xg.exception("Failed during MLFlow configuration.")

    raise MLflowLoggingException(
        artifact_type="experiment_configuration",
        reason=e
    ) from e


# ---------------- LOAD DATA ---------------- #
try:

    conn = DAO(spark, "newcatalog", "gold")

    df = conn.read_table("gold_claims").toPandas()

    logger_xg.info(
        f"Successfully loaded dataset with shape: {df.shape}"
    )

except Exception as e:

    logger_xg.exception("Failed to load dataset.")

    raise DataLoadingException(
        table_name="gold_claims",
        reason=e
    ) from e


# ---------------- PREPROCESS ---------------- #
try:

    categorical_cols = [
        col for col in df.select_dtypes(include=["object"]).columns
        if col != "label"
    ]

    for col in categorical_cols:

        try:

            le = LabelEncoder()

            df[col] = le.fit_transform(
                df[col].astype(str)
            )

        except Exception as col_error:

            logger_xg.exception(
                f"Encoding failed for column: {col}"
            )

            raise DataPreprocessingException(
                column_name=col,
                reason=col_error
            ) from col_error

    # Encode target
    df["label"] = df["label"].map({
        "APPROVED": 0,
        "DENIED": 1
    })

    X = df.drop(columns=["label"])

    y = df["label"]

    logger_xg.info("Data preprocessing completed successfully.")

except Exception as e:

    logger_xg.exception("Data preprocessing failed.")

    raise DataPreprocessingException(
        column_name="dataset",
        reason=e
    ) from e


# ---------------- TRAIN TEST SPLIT ---------------- #
try:

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    logger_xg.info("Train-test split completed successfully.")

except Exception as e:

    logger_xg.exception("Train-test split failed.")

    raise DataSplitException(
        reason=e
    ) from e


# ---------------- OPTUNA OBJECTIVE ---------------- #
def objective(trial):

    try:

        params = {
            "max_depth": trial.suggest_int(
                "max_depth", 3, 6
            ),
            "learning_rate": trial.suggest_float(
                "learning_rate", 0.01, 0.1
            ),
            "n_estimators": trial.suggest_int(
                "n_estimators", 100, 300
            ),
            "subsample": trial.suggest_float(
                "subsample", 0.6, 1.0
            ),
            "colsample_bytree": trial.suggest_float(
                "colsample_bytree", 0.6, 1.0
            ),
            "reg_alpha": trial.suggest_float(
                "reg_alpha", 0, 1
            ),
            "reg_lambda": trial.suggest_float(
                "reg_lambda", 0.5, 2
            ),
            "eval_metric": "logloss",
            "use_label_encoder": False
        }

        model = xgb.XGBClassifier(**params)

        kf = StratifiedKFold(
            n_splits=5,
            shuffle=True,
            random_state=42
        )

        auc_scores = []

        for train_idx, val_idx in kf.split(X, y):

            X_train_fold = X.iloc[train_idx]
            X_val_fold = X.iloc[val_idx]

            y_train_fold = y.iloc[train_idx]
            y_val_fold = y.iloc[val_idx]

            model.fit(
                X_train_fold,
                y_train_fold
            )

            probs = model.predict_proba(
                X_val_fold
            )[:, 1]

            auc = roc_auc_score(
                y_val_fold,
                probs
            )

            auc_scores.append(auc)

        mean_auc = sum(auc_scores) / len(auc_scores)

        logger_xg.info(
            f"Trial {trial.number} completed "
            f"with AUC: {mean_auc}"
        )

        return mean_auc

    except Exception as e:

        logger_xg.exception(
            f"Optuna trial {trial.number} failed."
        )

        raise OptunaOptimizationException(
            trial_number=trial.number,
            reason=e
        ) from e


# ---------------- MAIN PIPELINE ---------------- #
if __name__ == "__main__":

    try:

        # ---------------- RUN OPTUNA ---------------- #
        try:

            study = optuna.create_study(
                direction="maximize"
            )

            study.optimize(
                objective,
                n_trials=30
            )

            best_params = study.best_params

            logger_xg.info(
                f"Best parameters found: {best_params}"
            )

        except Exception as e:

            logger_xg.exception(
                "Optuna optimization failed."
            )

            raise OptunaOptimizationException(
                trial_number="study_level",
                reason=e
            ) from e

        # ---------------- MODEL TRAINING ---------------- #
        try:

            model = xgb.XGBClassifier(
                **best_params
            )

            model.fit(
                X_train,
                y_train
            )

            logger_xg.info(
                "Final model training completed."
            )

        except Exception as e:

            logger_xg.exception(
                "Final model training failed."
            )

            raise ModelTrainingException(
                model_name="XGBClassifier",
                reason=e
            ) from e

        # ---------------- MODEL EVALUATION ---------------- #
        try:

            preds = model.predict(X_test)

            probs = model.predict_proba(
                X_test
            )[:, 1]

            auc = roc_auc_score(
                y_test,
                probs
            )

            accuracy = accuracy_score(
                y_test,
                preds
            )

            class_sum = classification_report(
                y_test,
                preds
            )

            logger_xg.info(
                f"Evaluation completed. "
                f"AUC={auc}, Accuracy={accuracy}"
            )

        except Exception as e:

            logger_xg.exception(
                "Model evaluation failed."
            )

            raise ModelEvaluationException(
                metric_name="auc_accuracy_classification_report",
                reason=e
            ) from e

        # ---------------- MLFlow LOGGING ---------------- #
        try:

            with mlflow.start_run():

                mlflow.log_params(best_params)

                mlflow.log_metric(
                    "auc",
                    auc
                )

                mlflow.log_metric(
                    "accuracy",
                    accuracy
                )

                mlflow.xgboost.log_model(
                    model,
                    name="model",
                    input_example=X_train.iloc[[0]],
                    registered_model_name="xgboost_v1"
                )

            logger_xg.info(
                "MLFlow logging completed successfully."
            )

        except Exception as e:

            logger_xg.exception(
                "MLFlow logging failed."
            )

            raise MLflowLoggingException(
                artifact_type="model_metrics_registration",
                reason=e
            ) from e

        # ---------------- OUTPUT ---------------- #
        print(f"Final AUC: {auc}")

        print(f"Accuracy Score: {accuracy}")

        print(
            f"Classification Report: {class_sum}"
        )

    except Exception as e:

        logger_xg.exception(
            "ML pipeline execution failed."
        )

        raise ModelPipelineException(
            pipeline_stage="main_execution",
            reason=e
        ) from e