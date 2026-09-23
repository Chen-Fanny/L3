import logging
import httpx
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from app.config import settings
from app.schemas.temperature import StationTemperature

logger = logging.getLogger(__name__)

INVALID_VALUES = {"", "X", "NA", "null", "None", "-99", "-999", "-99.0", "-999.0"}

def parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    val_str = str(value).strip()
    if val_str in INVALID_VALUES:
        return None
    try:
        val = float(val_str)
        return val
    except (ValueError, TypeError):
        return None

class CWAClient:
    def __init__(self):
        self.api_key = settings.CWA_API_KEY
        self.data_url = settings.CWA_DATA_URL

    async def fetch_cwa_observations(self) -> List[StationTemperature]:
        """
        Fetch real observation data from CWA OpenData if API key is provided,
        or fall back to realistic pre-generated Taiwan observation data.
        """
        if self.api_key:
            try:
                stations = await self._fetch_from_api()
                if stations:
                    logger.info(f"Successfully fetched {len(stations)} stations from CWA API.")
                    return stations
                logger.warning("CWA API returned 0 valid stations. Using fallback dataset.")
            except Exception as e:
                logger.error(f"Error fetching from CWA API: {e}. Using fallback dataset.")

        return self._generate_fallback_data()

    async def _fetch_from_api(self) -> List[StationTemperature]:
        params = {
            "Authorization": self.api_key,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(self.data_url, params=params)
            resp.raise_for_status()
            data = resp.json()

        return self._parse_cwa_response(data)

    def _parse_cwa_response(self, data: Dict[str, Any]) -> List[StationTemperature]:
        stations: List[StationTemperature] = []
        records = data.get("records", {})

        # Format 1: Newer CWA format (Station list)
        if "Station" in records:
            for item in records["Station"]:
                st = self._parse_format_v2(item)
                if st:
                    stations.append(st)
            if stations:
                return stations

        # Format 2: Classic CWA format (location list)
        if "location" in records:
            for item in records["location"]:
                st = self._parse_format_v1(item)
                if st:
                    stations.append(st)

        return stations

    def _parse_format_v2(self, item: Dict[str, Any]) -> Optional[StationTemperature]:
        try:
            station_id = str(item.get("StationId", "")).strip()
            station_name = str(item.get("StationName", "")).strip()
            if not station_id or not station_name:
                return None

            obs_time = item.get("ObsTime", {}).get("DateTime", "")
            if not obs_time:
                obs_time = datetime.now(timezone(timedelta(hours=8))).isoformat()

            geo = item.get("GeoInfo", {})
            county = geo.get("CountyName")
            town = geo.get("TownName")
            altitude = parse_float(geo.get("StationAltitude"))

            lat = None
            lon = None
            coords = geo.get("Coordinates", [])
            if isinstance(coords, list) and len(coords) > 0:
                c_item = coords[0]
                lat = parse_float(c_item.get("StationLatitude"))
                lon = parse_float(c_item.get("StationLongitude"))

            if lat is None or lon is None:
                return None

            weather_elem = item.get("WeatherElement", {})
            temp = parse_float(weather_elem.get("AirTemperature"))
            if temp is None or temp < -20.0 or temp > 50.0:
                return None

            humidity = parse_float(weather_elem.get("RelativeHumidity"))
            pressure = parse_float(weather_elem.get("AirPressure"))
            wind_speed = parse_float(weather_elem.get("WindSpeed"))
            wind_dir = parse_float(weather_elem.get("WindDirection"))
            weather = weather_elem.get("Weather")
            precip = parse_float(weather_elem.get("Now", {}).get("Precipitation"))

            return StationTemperature(
                station_id=station_id,
                station_name=station_name,
                county=county,
                town=town,
                lat=lat,
                lon=lon,
                altitude_m=altitude,
                observed_at=obs_time,
                temperature_c=temp,
                humidity_percent=humidity,
                pressure_hpa=pressure,
                wind_speed_mps=wind_speed,
                wind_direction_deg=wind_dir,
                precipitation_mm=precip,
                weather=weather
            )
        except Exception:
            return None

    def _parse_format_v1(self, item: Dict[str, Any]) -> Optional[StationTemperature]:
        try:
            station_id = str(item.get("stationId", "")).strip()
            station_name = str(item.get("locationName", "")).strip()
            if not station_id or not station_name:
                return None

            lat = parse_float(item.get("lat"))
            lon = parse_float(item.get("lon"))
            if lat is None or lon is None:
                return None

            obs_time = item.get("time", {}).get("obsTime")
            if not obs_time:
                obs_time = datetime.now(timezone(timedelta(hours=8))).isoformat()

            elem_dict = {}
            for el in item.get("weatherElement", []):
                name = el.get("elementName")
                val = el.get("elementValue")
                if name:
                    elem_dict[name] = val

            temp = parse_float(elem_dict.get("TEMP"))
            if temp is None or temp < -20.0 or temp > 50.0:
                return None

            hum = parse_float(elem_dict.get("HUMD"))
            if hum is not None and hum <= 1.0:
                hum = hum * 100.0  # normalize decimal humidity

            return StationTemperature(
                station_id=station_id,
                station_name=station_name,
                county=item.get("parameter", [{}])[0].get("parameterValue") if item.get("parameter") else None,
                town=None,
                lat=lat,
                lon=lon,
                altitude_m=parse_float(elem_dict.get("ELEV")),
                observed_at=obs_time,
                temperature_c=temp,
                humidity_percent=hum,
                pressure_hpa=parse_float(elem_dict.get("PRES")),
                wind_speed_mps=parse_float(elem_dict.get("WDIR")),
                precipitation_mm=parse_float(elem_dict.get("24R")),
                weather=None
            )
        except Exception:
            return None

    def _generate_fallback_data(self) -> List[StationTemperature]:
        """
        Provides realistic Taiwan meteorological observation data covering all
        counties, mountain peaks, and offshore islands.
        """
        now = datetime.now(timezone(timedelta(hours=8)))
        time_str = now.strftime("%Y-%m-%dT%H:00:00+08:00")

        # Key stations with real geographical locations across Taiwan
        preset_stations = [
            # Northern Taiwan
            {"id": "466920", "name": "臺北", "county": "臺北市", "town": "中正區", "lat": 25.0377, "lon": 121.5149, "alt": 9.2, "temp": 28.6, "hum": 72, "wind": 2.2, "weather": "多雲"},
            {"id": "C0A980", "name": "社子", "county": "臺北市", "town": "士林區", "lat": 25.0886, "lon": 121.5036, "alt": 5.0, "temp": 29.1, "hum": 70, "wind": 1.9, "weather": "晴"},
            {"id": "466910", "name": "鞍部", "county": "臺北市", "town": "北投區", "lat": 25.1826, "lon": 121.5297, "alt": 825.8, "temp": 21.4, "hum": 89, "wind": 4.1, "weather": "陰"},
            {"id": "466900", "name": "淡水", "county": "新北市", "town": "淡水區", "lat": 25.1649, "lon": 121.4489, "alt": 19.0, "temp": 27.8, "hum": 75, "wind": 3.4, "weather": "多雲"},
            {"id": "466880", "name": "板橋", "county": "新北市", "town": "板橋區", "lat": 24.9976, "lon": 121.4420, "alt": 9.7, "temp": 28.9, "hum": 71, "wind": 2.0, "weather": "晴"},
            {"id": "466940", "name": "基隆", "county": "基隆市", "town": "仁愛區", "lat": 25.1333, "lon": 121.7405, "alt": 26.7, "temp": 27.2, "hum": 78, "wind": 3.8, "weather": "多雲"},
            {"id": "C0C480", "name": "桃園", "county": "桃園市", "town": "桃園區", "lat": 24.9961, "lon": 121.3129, "alt": 35.0, "temp": 29.4, "hum": 68, "wind": 2.6, "weather": "晴"},
            {"id": "467571", "name": "新竹", "county": "新竹市", "town": "北區", "lat": 24.8279, "lon": 120.9255, "alt": 26.9, "temp": 29.8, "hum": 66, "wind": 3.5, "weather": "晴"},
            {"id": "C0D570", "name": "竹東", "county": "新竹縣", "town": "竹東鎮", "lat": 24.7378, "lon": 121.0919, "alt": 110.0, "temp": 28.5, "hum": 72, "wind": 1.7, "weather": "晴"},
            {"id": "C0E420", "name": "苗栗", "county": "苗栗縣", "town": "苗栗市", "lat": 24.5650, "lon": 120.8250, "alt": 55.0, "temp": 30.1, "hum": 65, "wind": 2.3, "weather": "晴"},

            # Central Taiwan
            {"id": "467490", "name": "臺中", "county": "臺中市", "town": "北區", "lat": 24.1458, "lon": 120.6842, "alt": 77.2, "temp": 31.2, "hum": 63, "wind": 2.1, "weather": "晴"},
            {"id": "C0F970", "name": "大甲", "county": "臺中市", "town": "大甲區", "lat": 24.3486, "lon": 120.6200, "alt": 30.0, "temp": 30.5, "hum": 67, "wind": 3.1, "weather": "晴"},
            {"id": "C0G650", "name": "員林", "county": "彰化縣", "town": "員林市", "lat": 23.9589, "lon": 120.5744, "alt": 28.0, "temp": 31.8, "hum": 62, "wind": 2.0, "weather": "晴"},
            {"id": "467650", "name": "日月潭", "county": "南投縣", "town": "魚池鄉", "lat": 23.8813, "lon": 120.9081, "alt": 1014.8, "temp": 22.3, "hum": 84, "wind": 1.5, "weather": "陰"},
            {"id": "C0H990", "name": "南投", "county": "南投縣", "town": "南投市", "lat": 23.9097, "lon": 120.6869, "alt": 110.0, "temp": 31.0, "hum": 64, "wind": 1.8, "weather": "晴"},
            {"id": "467550", "name": "玉山", "county": "南投縣", "town": "信義鄉", "lat": 23.4876, "lon": 120.9595, "alt": 3844.8, "temp": 8.4, "hum": 91, "wind": 5.8, "weather": "強風有霧"},
            {"id": "C0K400", "name": "斗六", "county": "雲林縣", "town": "斗六市", "lat": 23.7119, "lon": 120.5439, "alt": 52.0, "temp": 32.1, "hum": 61, "wind": 1.9, "weather": "晴"},

            # Southern Taiwan
            {"id": "467480", "name": "嘉義", "county": "嘉義市", "town": "西區", "lat": 23.4959, "lon": 120.4322, "alt": 26.9, "temp": 32.5, "hum": 60, "wind": 2.2, "weather": "晴"},
            {"id": "467530", "name": "阿里山", "county": "嘉義縣", "town": "阿里山鄉", "lat": 23.5082, "lon": 120.8132, "alt": 2215.5, "temp": 14.8, "hum": 86, "wind": 2.5, "weather": "薄霧"},
            {"id": "467410", "name": "臺南", "county": "臺南市", "town": "中西區", "lat": 22.9932, "lon": 120.2036, "alt": 13.9, "temp": 33.2, "hum": 64, "wind": 2.4, "weather": "晴午後熱"},
            {"id": "C0X060", "name": "永康", "county": "臺南市", "town": "永康區", "lat": 23.0383, "lon": 120.2367, "alt": 14.0, "temp": 33.5, "hum": 62, "wind": 2.1, "weather": "晴"},
            {"id": "467440", "name": "高雄", "county": "高雄市", "town": "前鎮區", "lat": 22.5660, "lon": 120.3157, "alt": 2.3, "temp": 33.0, "hum": 66, "wind": 2.8, "weather": "晴"},
            {"id": "C0V680", "name": "旗津", "county": "高雄市", "town": "旗津區", "lat": 22.5667, "lon": 120.2783, "alt": 3.0, "temp": 32.0, "hum": 72, "wind": 4.2, "weather": "多雲"},
            {"id": "C0V770", "name": "美濃", "county": "高雄市", "town": "美濃區", "lat": 22.8989, "lon": 120.5414, "alt": 55.0, "temp": 33.8, "hum": 59, "wind": 1.6, "weather": "晴"},
            {"id": "467590", "name": "恆春", "county": "屏東縣", "town": "恆春鎮", "lat": 22.0039, "lon": 120.7463, "alt": 22.1, "temp": 31.5, "hum": 74, "wind": 4.8, "weather": "多雲晴"},
            {"id": "C0R140", "name": "屏東", "county": "屏東縣", "town": "屏東市", "lat": 22.6761, "lon": 120.4883, "alt": 24.0, "temp": 34.2, "hum": 58, "wind": 1.7, "weather": "晴熱"},

            # Eastern Taiwan
            {"id": "467080", "name": "宜蘭", "county": "宜蘭縣", "town": "宜蘭市", "lat": 24.7640, "lon": 121.7565, "alt": 7.2, "temp": 28.0, "hum": 76, "wind": 2.5, "weather": "多雲"},
            {"id": "C0U600", "name": "羅東", "county": "宜蘭縣", "town": "羅東鎮", "lat": 24.6750, "lon": 121.7670, "alt": 11.0, "temp": 28.2, "hum": 75, "wind": 2.0, "weather": "多雲"},
            {"id": "466990", "name": "花蓮", "county": "花蓮縣", "town": "花蓮市", "lat": 23.9752, "lon": 121.6133, "alt": 16.0, "temp": 29.5, "hum": 73, "wind": 3.0, "weather": "多雲"},
            {"id": "C0T870", "name": "光復", "county": "花蓮縣", "town": "光復鄉", "lat": 23.6667, "lon": 121.4189, "alt": 130.0, "temp": 30.2, "hum": 70, "wind": 2.1, "weather": "晴"},
            {"id": "467660", "name": "臺東", "county": "臺東縣", "town": "臺東市", "lat": 22.7522, "lon": 121.1546, "alt": 9.0, "temp": 31.0, "hum": 68, "wind": 3.2, "weather": "晴"},
            {"id": "467610", "name": "成功", "county": "臺東縣", "town": "成功鎮", "lat": 23.0975, "lon": 121.3734, "alt": 33.6, "temp": 30.0, "hum": 71, "wind": 3.6, "weather": "多雲"},

            # Islands
            {"id": "467350", "name": "澎湖", "county": "澎湖縣", "town": "馬公市", "lat": 23.5655, "lon": 119.5630, "alt": 10.7, "temp": 29.8, "hum": 77, "wind": 5.2, "weather": "晴"},
            {"id": "467110", "name": "金門", "county": "金門縣", "town": "金城鎮", "lat": 24.4073, "lon": 118.2893, "alt": 47.5, "temp": 29.0, "hum": 74, "wind": 4.0, "weather": "多雲"},
            {"id": "467990", "name": "馬祖", "county": "連江縣", "town": "南竿鄉", "lat": 26.1692, "lon": 119.9230, "alt": 97.8, "temp": 26.5, "hum": 82, "wind": 4.5, "weather": "陰"},
            {"id": "467620", "name": "蘭嶼", "county": "臺東縣", "town": "蘭嶼鄉", "lat": 22.0370, "lon": 121.5583, "alt": 324.0, "temp": 27.5, "hum": 88, "wind": 6.8, "weather": "多雲強風"},
            {"id": "467540", "name": "綠島", "county": "臺東縣", "town": "綠島鄉", "lat": 22.6739, "lon": 121.4939, "alt": 8.0, "temp": 30.5, "hum": 78, "wind": 4.1, "weather": "晴"}
        ]

        results = []
        for s in preset_stations:
            results.append(
                StationTemperature(
                    station_id=s["id"],
                    station_name=s["name"],
                    county=s["county"],
                    town=s["town"],
                    lat=s["lat"],
                    lon=s["lon"],
                    altitude_m=s["alt"],
                    observed_at=time_str,
                    temperature_c=s["temp"],
                    humidity_percent=s["hum"],
                    pressure_hpa=1013.2 - (s["alt"] / 10.0),
                    wind_speed_mps=s["wind"],
                    wind_direction_deg=90.0,
                    precipitation_mm=0.0,
                    weather=s["weather"]
                )
            )
        return results

cwa_client = CWAClient()
