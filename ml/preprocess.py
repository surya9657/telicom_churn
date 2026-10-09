"""
preprocess.py

Defines the feature lists and the scikit-learn preprocessing pipeline
(ColumnTransformer) shared by training (train.py) and inference
(backend/app/ml/predictor.py). Keeping this logic in ONE place guarantees
training and prediction never drift apart.
"""

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Columns that are not predictive and must be dropped before modeling.
ID_COLUMNS = ["customerID"]
TARGET_COLUMN = "Churn"

NUMERIC_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]

CATEGORICAL_FEATURES = [
    "gender",
    "Partner",
    "Dependents",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
]

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def clean_raw_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleaning steps applied to the RAW dataset before it ever reaches the
    ColumnTransformer. This mirrors the well-known data-quality issues in the
    IBM Telco dataset (TotalCharges shipped as a string with blank values for
    brand-new customers).
    """
    df = df.copy()

    # TotalCharges arrives as an object/string column with blank entries for
    # customers with 0 tenure - coerce to numeric and fill sensibly.
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["TotalCharges"] = df["TotalCharges"].fillna(df["MonthlyCharges"] * df["tenure"])
    df["TotalCharges"] = df["TotalCharges"].fillna(0)

    df["SeniorCitizen"] = df["SeniorCitizen"].astype(int)

    # Drop exact duplicate rows and rows missing the target during training.
    df = df.drop_duplicates()

    return df


def build_preprocessing_pipeline() -> ColumnTransformer:
    """
    Returns a ColumnTransformer that:
      - imputes + scales numeric features
      - imputes + one-hot encodes categorical features
    This object is fit ONLY on training data and then reused (via pickle)
    for every future prediction, so training and serving preprocessing can
    never diverge.
    """
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )
    return preprocessor


def encode_target(series: pd.Series) -> pd.Series:
    """Map the Yes/No churn label to 1/0."""
    return series.map({"Yes": 1, "No": 0}).astype(int)
