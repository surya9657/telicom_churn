"""
predictor.py

Converts a validated customer profile into the exact feature schema the
model was trained on (see ml/preprocess.py), then calls model.predict() and
model.predict_proba(). This is the ONLY place in the API that talks to the
ML model, keeping prediction logic isolated from FastAPI routing concerns.
"""

from dataclasses import dataclass

import pandas as pd

from app.core.config import get_settings
from app.ml.model_loader import get_model

settings = get_settings()

# Maps our API's snake_case customer fields to the exact PascalCase column
# names the model was trained on (ml/preprocess.py -> ALL_FEATURES). Keeping
# this mapping explicit prevents silent feature-name drift between training
# and inference.
FEATURE_COLUMN_MAP = {
    "gender": "gender",
    "senior_citizen": "SeniorCitizen",
    "partner": "Partner",
    "dependents": "Dependents",
    "tenure": "tenure",
    "phone_service": "PhoneService",
    "multiple_lines": "MultipleLines",
    "internet_service": "InternetService",
    "online_security": "OnlineSecurity",
    "online_backup": "OnlineBackup",
    "device_protection": "DeviceProtection",
    "tech_support": "TechSupport",
    "streaming_tv": "StreamingTV",
    "streaming_movies": "StreamingMovies",
    "contract": "Contract",
    "paperless_billing": "PaperlessBilling",
    "payment_method": "PaymentMethod",
    "monthly_charges": "MonthlyCharges",
    "total_charges": "TotalCharges",
}


@dataclass
class ChurnPredictionResult:
    churn_probability: float
    prediction: int
    risk_level: str
    model_used: str


def _to_model_dataframe(customer_data: dict) -> pd.DataFrame:
    """Builds a single-row DataFrame with the exact columns/order the model expects."""
    row = {}
    for api_field, model_column in FEATURE_COLUMN_MAP.items():
        value = customer_data[api_field]
        # Enum values (e.g. Gender.male) -> their string value
        value = getattr(value, "value", value)
        row[model_column] = value
    return pd.DataFrame([row])


def classify_risk(probability: float) -> str:
    """
    Maps a churn probability to a risk bucket using thresholds defined in
    ONE place (app/core/config.py) rather than scattered magic numbers.
    """
    if probability < settings.RISK_LOW_MAX:
        return "Low"
    if probability < settings.RISK_MEDIUM_MAX:
        return "Medium"
    return "High"


def predict_churn(customer_data: dict) -> ChurnPredictionResult:
    """
    Runs the trained Random Forest pipeline on a single customer profile.
    Applies the SAME preprocessing pipeline used during training (it is
    embedded inside the saved model as step 1 of the sklearn Pipeline), so
    training and inference can never diverge.
    """
    model = get_model()
    X = _to_model_dataframe(customer_data)

    probability = float(model.predict_proba(X)[0][1])
    prediction = int(model.predict(X)[0])
    risk_level = classify_risk(probability)

    return ChurnPredictionResult(
        churn_probability=round(probability, 4),
        prediction=prediction,
        risk_level=risk_level,
        model_used="RandomForestClassifier",
    )
