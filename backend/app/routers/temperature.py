from fastapi import APIRouter, HTTPException, Query
from app.schemas.temperature import TemperatureResponse, GeoJSONFeatureCollection, StationTemperature
from app.services.temperature_service import temperature_service

router = APIRouter(prefix="/api/temperature", tags=["temperature"])

@router.get("/latest", response_model=TemperatureResponse)
async def get_latest_temperature(force_refresh: bool = Query(False, description="Bypass cache and force refresh from source")):
    return await temperature_service.get_latest_observations(force_refresh=force_refresh)

@router.get("/geojson", response_model=GeoJSONFeatureCollection)
async def get_temperature_geojson(force_refresh: bool = Query(False, description="Bypass cache and force refresh")):
    return await temperature_service.get_geojson(force_refresh=force_refresh)

@router.get("/stations/{station_id}", response_model=StationTemperature)
async def get_station_detail(station_id: str):
    station = await temperature_service.get_station_by_id(station_id)
    if not station:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found")
    return station
