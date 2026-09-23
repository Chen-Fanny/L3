from fastapi import APIRouter
from app.schemas.temperature import HealthResponse
from app.services.temperature_service import temperature_service

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return temperature_service.get_health()
