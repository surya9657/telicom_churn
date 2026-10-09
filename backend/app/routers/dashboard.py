from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_current_user
from app.database import get_db
from app.models.customer import Customer
from app.models.prediction import Prediction
from app.models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
settings = get_settings()


def _latest_prediction_per_customer(db: Session):
    """Subquery-free helper: returns {customer_id: latest Prediction}."""
    predictions = db.query(Prediction).order_by(Prediction.created_at.desc()).all()
    latest = {}
    for p in predictions:
        if p.customer_id not in latest:
            latest[p.customer_id] = p
    return latest


@router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_customers = db.query(func.count(Customer.id)).scalar() or 0
    total_predictions = db.query(func.count(Prediction.id)).scalar() or 0

    latest = _latest_prediction_per_customer(db)
    risk_counts = {"High": 0, "Medium": 0, "Low": 0}
    churned_count = 0
    probabilities = []

    for p in latest.values():
        risk_counts[p.risk_level] = risk_counts.get(p.risk_level, 0) + 1
        churned_count += p.prediction
        probabilities.append(p.churn_probability)

    churn_rate = round(churned_count / len(latest), 4) if latest else 0.0
    avg_probability = round(sum(probabilities) / len(probabilities), 4) if probabilities else 0.0

    return {
        "total_customers": total_customers,
        "total_predictions": total_predictions,
        "high_risk_customers": risk_counts["High"],
        "medium_risk_customers": risk_counts["Medium"],
        "low_risk_customers": risk_counts["Low"],
        "overall_churn_rate": churn_rate,
        "average_churn_probability": avg_probability,
    }


@router.get("/churn-distribution")
def churn_distribution(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    latest = _latest_prediction_per_customer(db)
    churned = sum(1 for p in latest.values() if p.prediction == 1)
    not_churned = len(latest) - churned
    return {"churned": churned, "not_churned": not_churned}


@router.get("/risk-distribution")
def risk_distribution(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    latest = _latest_prediction_per_customer(db)
    counts = {"High": 0, "Medium": 0, "Low": 0}
    for p in latest.values():
        counts[p.risk_level] = counts.get(p.risk_level, 0) + 1
    return {"high": counts["High"], "medium": counts["Medium"], "low": counts["Low"]}


@router.get("/trends")
def monthly_prediction_trend(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Groups predictions by calendar month. Grouping is done in Python rather
    than with a Postgres-only date-formatting function so the same code path
    works against any SQLAlchemy-supported database.
    """
    predictions = db.query(Prediction.created_at, Prediction.prediction).all()

    monthly = defaultdict(lambda: {"total_predictions": 0, "predicted_churn": 0})
    for created_at, predicted in predictions:
        key = created_at.strftime("%Y-%m")
        monthly[key]["total_predictions"] += 1
        monthly[key]["predicted_churn"] += predicted

    return [
        {"month": month, **counts}
        for month, counts in sorted(monthly.items())
    ]


@router.get("/segmentation")
def customer_segmentation(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    customers = db.query(Customer).all()

    def bucket_tenure(tenure: int) -> str:
        if tenure <= 12:
            return "0-12 months"
        if tenure <= 24:
            return "13-24 months"
        if tenure <= 48:
            return "25-48 months"
        return "49+ months"

    contract_counts = defaultdict(int)
    payment_counts = defaultdict(int)
    internet_counts = defaultdict(int)
    tenure_counts = defaultdict(int)

    for c in customers:
        contract_counts[c.contract] += 1
        payment_counts[c.payment_method] += 1
        internet_counts[c.internet_service] += 1
        tenure_counts[bucket_tenure(c.tenure)] += 1

    return {
        "by_contract": dict(contract_counts),
        "by_payment_method": dict(payment_counts),
        "by_internet_service": dict(internet_counts),
        "by_tenure_group": dict(tenure_counts),
    }
