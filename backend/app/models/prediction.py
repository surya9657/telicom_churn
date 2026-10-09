from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign key to customers.id (avoids duplicating customer data here)
    customer_pk: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    customer_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)

    churn_probability: Mapped[float] = mapped_column(Float, nullable=False)
    prediction: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 = churn, 0 = no churn
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False)  # Low / Medium / High
    model_name: Mapped[str] = mapped_column(String(50), default="RandomForestClassifier")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    customer = relationship("Customer", back_populates="predictions")
