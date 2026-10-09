from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerImportSummary, CustomerListItem, CustomerResponse
from app.services import customer_service

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.get("", response_model=dict)
def list_customers(
    search: Optional[str] = Query(None, description="Search by customer ID or gender"),
    contract: Optional[str] = Query(None),
    internet_service: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customers, total = customer_service.list_customers(
        db, search=search, contract=contract, internet_service=internet_service, skip=skip, limit=limit
    )
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [CustomerListItem.model_validate(c) for c in customers],
    }


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = customer_service.create_customer(db, customer_in)
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return customer_service.get_customer_by_customer_id(db, customer_id)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer_service.delete_customer(db, customer_id)
    return None


@router.post("/import", response_model=CustomerImportSummary)
async def import_customers(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_bytes = await file.read()
    return customer_service.import_customers_from_csv(db, file_bytes)
