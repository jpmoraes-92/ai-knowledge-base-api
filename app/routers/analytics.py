from fastapi import APIRouter, status
from app.models.schemas import AnalyticsResponse
from app.services.mongo_service import mongo_service

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics & BI"])

@router.get("/documents", response_model=AnalyticsResponse, status_code=status.HTTP_200_OK)
async def get_analytics():
    data = await mongo_service.get_document_analytics()
    return {"results": data}