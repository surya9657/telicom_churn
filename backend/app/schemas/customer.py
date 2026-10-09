from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class YesNo(str, Enum):
    yes = "Yes"
    no = "No"


class Gender(str, Enum):
    male = "Male"
    female = "Female"


class MultipleLines(str, Enum):
    yes = "Yes"
    no = "No"
    no_phone_service = "No phone service"


class InternetService(str, Enum):
    dsl = "DSL"
    fiber_optic = "Fiber optic"
    none_ = "No"


class InternetDependentFeature(str, Enum):
    yes = "Yes"
    no = "No"
    no_internet_service = "No internet service"


class Contract(str, Enum):
    month_to_month = "Month-to-month"
    one_year = "One year"
    two_year = "Two year"


class PaymentMethod(str, Enum):
    electronic_check = "Electronic check"
    mailed_check = "Mailed check"
    bank_transfer = "Bank transfer (automatic)"
    credit_card = "Credit card (automatic)"


class CustomerBase(BaseModel):
    customer_id: str = Field(..., min_length=3, max_length=50, description="Unique business customer identifier")
    gender: Gender
    senior_citizen: int = Field(..., ge=0, le=1, description="0 = No, 1 = Yes")
    partner: YesNo
    dependents: YesNo
    tenure: int = Field(..., ge=0, le=100, description="Months with the company")

    phone_service: YesNo
    multiple_lines: MultipleLines
    internet_service: InternetService
    online_security: InternetDependentFeature
    online_backup: InternetDependentFeature
    device_protection: InternetDependentFeature
    tech_support: InternetDependentFeature
    streaming_tv: InternetDependentFeature
    streaming_movies: InternetDependentFeature

    contract: Contract
    paperless_billing: YesNo
    payment_method: PaymentMethod
    monthly_charges: float = Field(..., ge=0, le=1000)
    total_charges: float = Field(..., ge=0, le=100000)

    @field_validator(
        "multiple_lines",
        mode="after",
    )
    @classmethod
    def validate_multiple_lines_consistency(cls, value, info):
        phone_service = info.data.get("phone_service")
        if phone_service == YesNo.no and value != MultipleLines.no_phone_service:
            raise ValueError("multiple_lines must be 'No phone service' when phone_service is 'No'")
        return value


class CustomerCreate(CustomerBase):
    pass


class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerListItem(BaseModel):
    id: int
    customer_id: str
    gender: str
    tenure: int
    contract: str
    monthly_charges: float
    internet_service: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerImportSummary(BaseModel):
    total_records: int
    imported: int
    failed: int
    duplicates: int
    errors: list[str] = []
