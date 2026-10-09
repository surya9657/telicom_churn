from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.prediction import (
    HighRiskCustomer,
    PredictionHistoryItem,
    PredictionRequest,
    PredictionResponse,
)
from app.services import prediction_service

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])


@router.post("", response_model=PredictionResponse)
def create_prediction(
    data: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prediction = prediction_service.run_prediction(db, data)
    return PredictionResponse(
        customer_id=prediction.customer_id,
        churn_probability=prediction.churn_probability,
        prediction=prediction.prediction,
        risk_level=prediction.risk_level,
        model_used=prediction.model_name,
        predicted_at=prediction.created_at,
    )


@router.get("", response_model=dict)
def list_predictions(
    risk_level: Optional[str] = Query(None, description="Low, Medium, or High"),
    prediction_result: Optional[int] = Query(None, ge=0, le=1),
    customer_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    predictions, total = prediction_service.list_predictions(
        db,
        risk_level=risk_level,
        prediction_result=prediction_result,
        customer_id=customer_id,
        skip=skip,
        limit=limit,
    )
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [PredictionHistoryItem.model_validate(p) for p in predictions],
    }


@router.get("/high-risk", response_model=list[HighRiskCustomer])
def high_risk_customers(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    predictions = prediction_service.get_high_risk_customers(db, limit=limit)
    return [
        HighRiskCustomer(
            customer_id=p.customer_id,
            tenure=p.customer.tenure,
            contract=p.customer.contract,
            monthly_charges=p.customer.monthly_charges,
            churn_probability=p.churn_probability,
            risk_level=p.risk_level,
            last_prediction_date=p.created_at,
        )
        for p in predictions
    ]


@router.get("/customer/{customer_id}", response_model=list[PredictionHistoryItem])
def customer_prediction_history(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    history = prediction_service.get_customer_prediction_history(db, customer_id)
    return [PredictionHistoryItem.model_validate(p) for p in history]


@router.get("/{prediction_id}", response_model=PredictionHistoryItem)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prediction = prediction_service.get_prediction(db, prediction_id)
    return prediction
