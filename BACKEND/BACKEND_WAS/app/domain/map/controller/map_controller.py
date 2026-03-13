from fastapi import APIRouter, HTTPException
from ..service.map_service import PointService
from ..models.map_models import PointsData

router = APIRouter()

@router.get("/map", response_model=PointsData)
async def get_points():
    return await PointService.get_points()

@router.put("/map")
async def update_points(data: PointsData):
    try:
        return await PointService.update_points(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))