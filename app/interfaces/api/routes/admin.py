from fastapi import APIRouter, HTTPException

from app.application.use_cases.retrain_model import RetrainModelUseCase
from app.interfaces.api.schemas.admin_schemas import RetrainResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/retrain", response_model=RetrainResponse)
def retrain_model() -> RetrainResponse:
    use_case = RetrainModelUseCase()

    try:
        model_path = use_case.execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return RetrainResponse(
        status="success",
        message="Model retrained successfully.",
        model_path=str(model_path),
    )
