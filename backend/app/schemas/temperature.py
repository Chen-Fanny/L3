from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class StationTemperature(BaseModel):
    station_id: str
    station_name: str
    county: Optional[str] = None
    town: Optional[str] = None

    lat: float
    lon: float
    altitude_m: Optional[float] = None

    observed_at: str
    temperature_c: float

    humidity_percent: Optional[float] = None
    pressure_hpa: Optional[float] = None
    wind_speed_mps: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    precipitation_mm: Optional[float] = None
    weather: Optional[str] = None

class TemperatureResponse(BaseModel):
    source: str = "CWA"
    status: str = "ok"
    updated_at: str
    count: int
    stations: List[StationTemperature]

class GeoJSONGeometry(BaseModel):
    type: str = "Point"
    coordinates: List[float] # [lon, lat]

class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: Dict[str, Any]

class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]

class HealthResponse(BaseModel):
    status: str = "ok"
    cwa_cache_status: str
    latest_cwa_time: Optional[str] = None
    station_count: int = 0
