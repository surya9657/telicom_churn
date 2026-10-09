from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.customer import CustomerBase


class PredictionRequest(CustomerBase):
    """
    Prediction accepts the full customer profile (same fields used for
    customer creation) so an admin can either predict for an existing
    customer or run an ad-hoc "what-if" prediction. If a customer with this
    customer_id already exists, their profile is refreshed with these values.
    """

    pass


class PredictionResponse(BaseModel):
    customer_id: str
    churn_probability: float
    prediction: int
    risk_level: str
    model_used: str
    predicted_at: datetime


class PredictionHistoryItem(BaseModel):
    id: int
    customer_id: str
    churn_probability: float
    prediction: int
    risk_level: str
    model_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class HighRiskCustomer(BaseModel):
    customer_id: str
    tenure: int
    contract: str
    monthly_charges: float
    churn_probability: float
    risk_level: str
    last_prediction_date: datetime
