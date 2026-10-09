"""
main.py

FastAPI application entrypoint. Wires together the database, routers, CORS,
and global error handling. Run with:

    uvicorn app.main:app --reload
"""

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models import customer, prediction, user  # noqa: F401  (ensures models are registered)
from app.models.user import User
from app.routers import auth, customers, dashboard, model, predictions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("churn_app")

settings = get_settings()

app = FastAPI(
    title="Customer Churn Prediction System",
    description="Full-stack ML-powered customer churn analytics platform.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(predictions.router)
app.include_router(dashboard.router)
app.include_router(model.router)


@app.on_event("startup")
def on_startup():
    """Creates database tables and a default admin user if none exists."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            admin = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
            )
            db.add(admin)
            db.commit()
            logger.info("Created default admin user '%s'", settings.DEFAULT_ADMIN_USERNAME)
    finally:
        db.close()


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


# ---- Global error handlers: never leak internal stack traces to the client ----


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request data", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error while processing %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred. Please try again later."},
    )
