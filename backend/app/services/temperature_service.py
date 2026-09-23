import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from app.services.cache_service import cache_service
from app.services.cwa_client import cwa_client
from app.schemas.temperature import (
    StationTemperature,
    TemperatureResponse,
    GeoJSONFeatureCollection,
    GeoJSONFeature,
    GeoJSONGeometry,
    HealthResponse
)

logger = logging.getLogger(__name__)

class TemperatureService:
    async def get_latest_observations(self, force_refresh: bool = False) -> TemperatureResponse:
        cached = cache_service.get()
        if not force_refresh and cache_service.is_fresh() and cached:
            return TemperatureResponse(**cached)

        # Refresh
        stations = await cwa_client.fetch_cwa_observations()
        now_iso = datetime.now(timezone(timedelta(hours=8))).isoformat()
        if stations:
            now_iso = stations[0].observed_at

        response_data = {
            "source": "CWA OpenData" if cwa_client.api_key else "CWA (Fallback Demo)",
            "status": "ok",
            "updated_at": now_iso,
            "count": len(stations),
            "stations": [s.model_dump() for s in stations]
        }

        cache_service.set(response_data)
        return TemperatureResponse(**response_data)

    async def get_geojson(self, force_refresh: bool = False) -> GeoJSONFeatureCollection:
        data = await self.get_latest_observations(force_refresh=force_refresh)
        features: List[GeoJSONFeature] = []

        for s in data.stations:
            feature = GeoJSONFeature(
                geometry=GeoJSONGeometry(coordinates=[s.lon, s.lat]),
                properties={
                    "station_id": s.station_id,
                    "station_name": s.station_name,
                    "county": s.county,
                    "town": s.town,
                    "temperature_c": s.temperature_c,
                    "humidity_percent": s.humidity_percent,
                    "wind_speed_mps": s.wind_speed_mps,
                    "weather": s.weather,
                    "observed_at": s.observed_at
                }
            )
            features.append(feature)

        return GeoJSONFeatureCollection(features=features)

    async def get_station_by_id(self, station_id: str) -> Optional[StationTemperature]:
        data = await self.get_latest_observations()
        for s in data.stations:
            if s.station_id.lower() == station_id.lower():
                return s
        return None

    def get_health(self) -> HealthResponse:
        cached = cache_service.get()
        return HealthResponse(
            status="ok",
            cwa_cache_status=cache_service.status(),
            latest_cwa_time=cached.get("updated_at") if cached else None,
            station_count=cached.get("count", 0) if cached else 0
        )

temperature_service = TemperatureService()
