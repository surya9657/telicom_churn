from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.ml.model_loader import ModelNotFoundError, get_model_metrics
from app.models.user import User

router = APIRouter(prefix="/api/model", tags=["Model"])


@router.get("/metrics")
def model_metrics(current_user: User = Depends(get_current_user)):
    try:
        return get_model_metrics()
    except ModelNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
