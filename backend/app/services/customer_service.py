"""
customer_service.py

Business logic for customer management: create, list (with search/filter),
retrieve, delete, and bulk CSV import. Keeping this logic out of the router
layer makes it independently testable and reusable.
"""

import csv
import io
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerImportSummary

# Columns expected in an import CSV, mirroring CustomerCreate fields.
REQUIRED_CSV_COLUMNS = [
    "customer_id",
    "gender",
    "senior_citizen",
    "partner",
    "dependents",
    "tenure",
    "phone_service",
    "multiple_lines",
    "internet_service",
    "online_security",
    "online_backup",
    "device_protection",
    "tech_support",
    "streaming_tv",
    "streaming_movies",
    "contract",
    "paperless_billing",
    "payment_method",
    "monthly_charges",
    "total_charges",
]


def create_customer(db: Session, customer_in: CustomerCreate) -> Customer:
    existing = db.query(Customer).filter(Customer.customer_id == customer_in.customer_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Customer with customer_id '{customer_in.customer_id}' already exists",
        )

    customer = Customer(
        customer_id=customer_in.customer_id,
        gender=customer_in.gender.value,
        senior_citizen=customer_in.senior_citizen,
        partner=customer_in.partner.value,
        dependents=customer_in.dependents.value,
        tenure=customer_in.tenure,
        phone_service=customer_in.phone_service.value,
        multiple_lines=customer_in.multiple_lines.value,
        internet_service=customer_in.internet_service.value,
        online_security=customer_in.online_security.value,
        online_backup=customer_in.online_backup.value,
        device_protection=customer_in.device_protection.value,
        tech_support=customer_in.tech_support.value,
        streaming_tv=customer_in.streaming_tv.value,
        streaming_movies=customer_in.streaming_movies.value,
        contract=customer_in.contract.value,
        paperless_billing=customer_in.paperless_billing.value,
        payment_method=customer_in.payment_method.value,
        monthly_charges=customer_in.monthly_charges,
        total_charges=customer_in.total_charges,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_customer_by_customer_id(db: Session, customer_id: str) -> Customer:
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Customer '{customer_id}' not found")
    return customer


def list_customers(
    db: Session,
    search: Optional[str] = None,
    contract: Optional[str] = None,
    internet_service: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    query = db.query(Customer)

    if search:
        like_term = f"%{search}%"
        query = query.filter(or_(Customer.customer_id.ilike(like_term), Customer.gender.ilike(like_term)))
    if contract:
        query = query.filter(Customer.contract == contract)
    if internet_service:
        query = query.filter(Customer.internet_service == internet_service)

    total = query.count()
    customers = query.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()
    return customers, total


def delete_customer(db: Session, customer_id: str) -> None:
    customer = get_customer_by_customer_id(db, customer_id)
    db.delete(customer)
    db.commit()


def import_customers_from_csv(db: Session, file_bytes: bytes) -> CustomerImportSummary:
    """
    Parses an uploaded CSV, validates every row with CustomerCreate, and
    inserts valid, non-duplicate rows. Every failure is recorded rather than
    silently skipped, per spec.
    """
    text = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    missing_columns = [c for c in REQUIRED_CSV_COLUMNS if c not in (reader.fieldnames or [])]
    if missing_columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV is missing required columns: {', '.join(missing_columns)}",
        )

    total = 0
    imported = 0
    failed = 0
    duplicates = 0
    errors: list[str] = []
    seen_ids_in_file: set[str] = set()

    for row_number, row in enumerate(reader, start=2):  # header is line 1
        total += 1
        customer_id = (row.get("customer_id") or "").strip()

        try:
            if customer_id in seen_ids_in_file:
                duplicates += 1
                errors.append(f"Row {row_number}: duplicate customer_id '{customer_id}' within file")
                continue
            seen_ids_in_file.add(customer_id)

            existing = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            if existing:
                duplicates += 1
                errors.append(f"Row {row_number}: customer_id '{customer_id}' already exists in database")
                continue

            customer_in = CustomerCreate(
                customer_id=customer_id,
                gender=row["gender"].strip(),
                senior_citizen=int(row["senior_citizen"]),
                partner=row["partner"].strip(),
                dependents=row["dependents"].strip(),
                tenure=int(row["tenure"]),
                phone_service=row["phone_service"].strip(),
                multiple_lines=row["multiple_lines"].strip(),
                internet_service=row["internet_service"].strip(),
                online_security=row["online_security"].strip(),
                online_backup=row["online_backup"].strip(),
                device_protection=row["device_protection"].strip(),
                tech_support=row["tech_support"].strip(),
                streaming_tv=row["streaming_tv"].strip(),
                streaming_movies=row["streaming_movies"].strip(),
                contract=row["contract"].strip(),
                paperless_billing=row["paperless_billing"].strip(),
                payment_method=row["payment_method"].strip(),
                monthly_charges=float(row["monthly_charges"]),
                total_charges=float(row["total_charges"]),
            )
            create_customer(db, customer_in)
            imported += 1

        except HTTPException as exc:
            failed += 1
            errors.append(f"Row {row_number} ({customer_id}): {exc.detail}")
        except (ValueError, KeyError) as exc:
            failed += 1
            errors.append(f"Row {row_number} ({customer_id}): invalid data - {exc}")

    return CustomerImportSummary(
        total_records=total,
        imported=imported,
        failed=failed,
        duplicates=duplicates,
        errors=errors[:100],  # cap so a huge bad file doesn't blow up the response
    )
