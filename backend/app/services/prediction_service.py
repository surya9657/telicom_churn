"""
prediction_service.py

Orchestrates the prediction workflow described in the spec:
  validate input -> feature preprocessing -> trained model -> probability
  -> risk classification -> store in PostgreSQL -> return result.

Feature preprocessing + model inference live in app/ml/predictor.py; this
service is responsible for the surrounding business logic (upserting the
customer profile and persisting the prediction record).
"""

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ml.predictor import predict_churn
from app.models.customer import Customer
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionRequest

settings = get_settings()


def _upsert_customer_profile(db: Session, data: PredictionRequest) -> Customer:
    """Creates the customer if new, or refreshes their profile if they already exist."""
    customer = db.query(Customer).filter(Customer.customer_id == data.customer_id).first()

    field_values = dict(
        gender=data.gender.value,
        senior_citizen=data.senior_citizen,
        partner=data.partner.value,
        dependents=data.dependents.value,
        tenure=data.tenure,
        phone_service=data.phone_service.value,
        multiple_lines=data.multiple_lines.value,
        internet_service=data.internet_service.value,
        online_security=data.online_security.value,
        online_backup=data.online_backup.value,
        device_protection=data.device_protection.value,
        tech_support=data.tech_support.value,
        streaming_tv=data.streaming_tv.value,
        streaming_movies=data.streaming_movies.value,
        contract=data.contract.value,
        paperless_billing=data.paperless_billing.value,
        payment_method=data.payment_method.value,
        monthly_charges=data.monthly_charges,
        total_charges=data.total_charges,
    )

    if customer:
        for field, value in field_values.items():
            setattr(customer, field, value)
    else:
        customer = Customer(customer_id=data.customer_id, **field_values)
        db.add(customer)

    db.commit()
    db.refresh(customer)
    return customer


def run_prediction(db: Session, data: PredictionRequest) -> Prediction:
    """
    Full prediction pipeline: upsert customer -> run ML model -> classify
    risk -> persist prediction row -> return it.
    """
    customer = _upsert_customer_profile(db, data)

    try:
        result = predict_churn(data.model_dump())
    except Exception as exc:  # ML errors are surfaced as a clean 500, no stack trace to the client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: the ML model could not score this customer ({type(exc).__name__})",
        )

    prediction = Prediction(
        customer_pk=customer.id,
        customer_id=customer.customer_id,
        churn_probability=result.churn_probability,
        prediction=result.prediction,
        risk_level=result.risk_level,
        model_name=result.model_used,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def list_predictions(
    db: Session,
    risk_level: Optional[str] = None,
    prediction_result: Optional[int] = None,
    customer_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    query = db.query(Prediction)
    if risk_level:
        query = query.filter(Prediction.risk_level == risk_level)
    if prediction_result is not None:
        query = query.filter(Prediction.prediction == prediction_result)
    if customer_id:
        query = query.filter(Prediction.customer_id == customer_id)

    total = query.count()
    predictions = query.order_by(Prediction.created_at.desc()).offset(skip).limit(limit).all()
    return predictions, total


def get_prediction(db: Session, prediction_id: int) -> Prediction:
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prediction {prediction_id} not found")
    return prediction


def get_customer_prediction_history(db: Session, customer_id: str) -> List[Prediction]:
    return (
        db.query(Prediction)
        .filter(Prediction.customer_id == customer_id)
        .order_by(Prediction.created_at.desc())
        .all()
    )


def get_high_risk_customers(db: Session, limit: int = 100):
    """
    Returns each customer's MOST RECENT prediction, filtered to High risk,
    sorted by churn probability descending, joined with current customer info.
    """
    from sqlalchemy import func

    latest_ids_subq = (
        db.query(
            Prediction.customer_id,
            func.max(Prediction.created_at).label("latest_created_at"),
        )
        .group_by(Prediction.customer_id)
        .subquery()
    )

    latest_predictions = (
        db.query(Prediction)
        .join(
            latest_ids_subq,
            (Prediction.customer_id == latest_ids_subq.c.customer_id)
            & (Prediction.created_at == latest_ids_subq.c.latest_created_at),
        )
        .filter(Prediction.risk_level == "High")
        .order_by(Prediction.churn_probability.desc())
        .limit(limit)
        .all()
    )
    return latest_predictions
