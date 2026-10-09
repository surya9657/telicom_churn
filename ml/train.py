"""
train.py

End-to-end training pipeline for the Customer Churn Prediction System.

Steps:
  1. Load dataset
  2. Inspect dataset
  3. Clean missing values
  4. Remove unnecessary columns
  5. Convert categorical variables (handled inside the sklearn Pipeline)
  6. Separate features and target
  7. Split into training and testing data
  8. Preprocess numerical and categorical features (ColumnTransformer)
  9. Train Random Forest Classifier
 10. Evaluate model (+ optional Logistic Regression comparison)
 11. Save model
 12. Save preprocessing pipeline
 13. Save evaluation metrics (consumed by the /api/model/metrics endpoint)

Run:
    python train.py
"""

import json
import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from evaluate import evaluate_model
from preprocess import (
    ALL_FEATURES,
    TARGET_COLUMN,
    build_preprocessing_pipeline,
    clean_raw_dataframe,
    encode_target,
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "telco_churn.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")
RANDOM_STATE = 42


def load_dataset(path: str) -> pd.DataFrame:
    print(f"[1/13] Loading dataset from {path} ...")
    df = pd.read_csv(path)
    print(f"       Loaded {len(df)} rows, {len(df.columns)} columns")
    return df


def inspect_dataset(df: pd.DataFrame) -> None:
    print("[2/13] Inspecting dataset ...")
    print(f"       Missing values per column:\n{df.isna().sum()[df.isna().sum() > 0]}")
    print(f"       Churn distribution:\n{df[TARGET_COLUMN].value_counts()}")


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    # 1-2. Load + inspect
    df = load_dataset(DATA_PATH)
    inspect_dataset(df)

    # 3-4. Clean missing values / drop unnecessary columns
    print("[3/13] Cleaning missing values ...")
    df = clean_raw_dataframe(df)
    print(f"       {len(df)} rows remain after cleaning")

    print("[4/13] Removing unnecessary columns (customerID is kept aside, not modeled) ...")
    # customerID is not a predictive feature - it is excluded from X below.

    # 5-6. Convert categorical variables happens inside the sklearn Pipeline;
    # here we just separate features/target.
    print("[5/13] Categorical conversion will be handled by the ColumnTransformer")
    print("[6/13] Separating features and target ...")
    X = df[ALL_FEATURES]
    y = encode_target(df[TARGET_COLUMN])

    # 7. Train/test split (stratified because churn is imbalanced)
    print("[7/13] Splitting into train/test sets ...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    print(f"       Train: {len(X_train)}  Test: {len(X_test)}")

    # 8. Build the shared preprocessing ColumnTransformer
    print("[8/13] Building preprocessing pipeline ...")
    preprocessor = build_preprocessing_pipeline()

    # 9. Train Random Forest Classifier (primary model)
    print("[9/13] Training Random Forest Classifier ...")
    rf_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=10,
                    min_samples_leaf=5,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    rf_pipeline.fit(X_train, y_train)

    # Optional comparison model: Logistic Regression, same preprocessor/split
    print("       Training Logistic Regression (comparison model) ...")
    lr_pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessing_pipeline()),
            (
                "classifier",
                LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE),
            ),
        ]
    )
    lr_pipeline.fit(X_train, y_train)

    # 10. Evaluate both models on the SAME test set
    print("[10/13] Evaluating models ...")
    rf_metrics = evaluate_model(rf_pipeline, X_test, y_test, model_name="RandomForest")
    lr_metrics = evaluate_model(lr_pipeline, X_test, y_test, model_name="LogisticRegression")

    print("       Random Forest metrics:", json.dumps(rf_metrics, indent=2))
    print("       Logistic Regression metrics:", json.dumps(lr_metrics, indent=2))

    # 11-12. Save model + preprocessing pipeline.
    # We persist the FULL pipeline (preprocessor + classifier) as a single
    # object so prediction code applies IDENTICAL preprocessing to training.
    model_path = os.path.join(MODEL_DIR, "churn_model.pkl")
    preprocessing_path = os.path.join(MODEL_DIR, "preprocessing_pipeline.pkl")
    lr_model_path = os.path.join(MODEL_DIR, "churn_model_logreg.pkl")

    print(f"[11/13] Saving Random Forest model to {model_path} ...")
    joblib.dump(rf_pipeline, model_path)

    print(f"[12/13] Saving preprocessing pipeline reference to {preprocessing_path} ...")
    # The preprocessor is embedded inside the saved pipeline above; we ALSO
    # save it standalone (fit on the same training data) so it can be reused
    # independently if a future model swap is needed without retraining
    # preprocessing from scratch.
    joblib.dump(rf_pipeline.named_steps["preprocessor"], preprocessing_path)

    print(f"        Saving Logistic Regression model to {lr_model_path} (comparison only) ...")
    joblib.dump(lr_pipeline, lr_model_path)

    # 13. Save evaluation metrics for the /api/model/metrics endpoint
    metrics_path = os.path.join(MODEL_DIR, "metrics.json")
    print(f"[13/13] Saving evaluation metrics to {metrics_path} ...")
    all_metrics = {
        "random_forest": rf_metrics,
        "logistic_regression": lr_metrics,
        "training_rows": len(X_train),
        "test_rows": len(X_test),
        "features": ALL_FEATURES,
        "random_state": RANDOM_STATE,
    }
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)

    print("\nTraining complete. Artifacts saved in ml/model/")


if __name__ == "__main__":
    main()
