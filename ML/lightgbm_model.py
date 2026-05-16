import mlflow
import lightgbm as lgb
import pandas as pd
import os
import optuna

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score, accuracy_score, classification_report

from util.utils import spark, logger
from util.dao import DAO

# ---------------- CONFIG ---------------- #
os.environ['DATABRICKS_TOKEN'] = os.getenv('DATABRICKS_TOKEN_ID')
EXPERIMENT_NAME = "/Users/rehansk123.rk@gmail.com/Claim_Denial_Prevention"

mlflow.set_tracking_uri("databricks")
mlflow.set_experiment(EXPERIMENT_NAME)

# ---------------- LOAD DATA ---------------- #
conn = DAO(spark, "newcatalog", "gold")
silver_conn = DAO(spark, "newcatalog", "silver")

df = silver_conn.read_table("silver_claims").toPandas()
label_df = conn.read_table("gold_claims").toPandas()

# ---------------- PREPROCESS ---------------- #
categorical_cols = df.select_dtypes(include=['object']).columns

for col in categorical_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))

label_df["label"] = label_df["label"].map({"APPROVED": 0, "DENIED": 1})

X = df
y = label_df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# ---------------- OPTUNA OBJECTIVE ---------------- #
def objective(trial):

    params = {
        "num_leaves": trial.suggest_int("num_leaves", 20, 100),
        "max_depth": trial.suggest_int("max_depth", 3, 8),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1),
        "n_estimators": trial.suggest_int("n_estimators", 100, 300),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 0, 1),
        "reg_lambda": trial.suggest_float("reg_lambda", 0, 2),
        "objective": "binary"
    }

    model = lgb.LGBMClassifier(**params)

    kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    auc_scores = []

    for train_idx, val_idx in kf.split(X_train, y_train):
        X_train_fold, X_val_fold = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_train_fold, y_val_fold = y_train.iloc[train_idx], y_train.iloc[val_idx]

        model.fit(X_train_fold, y_train_fold)

        probs = model.predict_proba(X_val_fold)[:, 1]
        auc = roc_auc_score(y_val_fold, probs)

        auc_scores.append(auc)

    return sum(auc_scores) / len(auc_scores)

if __name__ == "__main__":
    # ---------------- RUN OPTUNA ---------------- #
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=30)

    best_params = study.best_params
    print("Best Params:", best_params)

    # ---------------- FINAL MODEL + MLFLOW ---------------- #
    with mlflow.start_run():

        model = lgb.LGBMClassifier(**best_params)

        model.fit(X_train, y_train)

        probs = model.predict_proba(X_test)[:, 1] #gets denial probability 
        preds = (probs >= 0.5).astype(int)

        auc = roc_auc_score(y_test, probs)
        accuracy = accuracy_score(y_test, preds)
        class_sum = classification_report(y_test, preds)

        mlflow.log_params(best_params)
        mlflow.log_metric("auc", auc)
        mlflow.log_metric("accuracy", accuracy)

        mlflow.lightgbm.log_model(model, "model")

        # print(f"Final AUC: {auc}")
        # print(f"Accuracy Score: {accuracy}")
        # print(f"Classification Report:\n{class_sum}")