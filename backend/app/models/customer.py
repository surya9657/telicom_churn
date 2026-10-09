from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    # Demographic fields
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    senior_citizen: Mapped[int] = mapped_column(Integer, default=0)
    partner: Mapped[str] = mapped_column(String(5), nullable=False)
    dependents: Mapped[str] = mapped_column(String(5), nullable=False)
    tenure: Mapped[int] = mapped_column(Integer, nullable=False)

    # Service fields
    phone_service: Mapped[str] = mapped_column(String(5), nullable=False)
    multiple_lines: Mapped[str] = mapped_column(String(20), nullable=False)
    internet_service: Mapped[str] = mapped_column(String(20), nullable=False)
    online_security: Mapped[str] = mapped_column(String(25), nullable=False)
    online_backup: Mapped[str] = mapped_column(String(25), nullable=False)
    device_protection: Mapped[str] = mapped_column(String(25), nullable=False)
    tech_support: Mapped[str] = mapped_column(String(25), nullable=False)
    streaming_tv: Mapped[str] = mapped_column(String(25), nullable=False)
    streaming_movies: Mapped[str] = mapped_column(String(25), nullable=False)

    # Contract / billing fields
    contract: Mapped[str] = mapped_column(String(20), nullable=False)
    paperless_billing: Mapped[str] = mapped_column(String(5), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(35), nullable=False)
    monthly_charges: Mapped[float] = mapped_column(Float, nullable=False)
    total_charges: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    predictions = relationship(
        "Prediction", back_populates="customer", cascade="all, delete-orphan", order_by="desc(Prediction.created_at)"
    )
