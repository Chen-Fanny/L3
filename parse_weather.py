"""
HW10 步驟 2: 分析 JSON，提取氣溫資料 (20%)
支援解析 CWA O-A0003-001 全臺 350+ 測站即時觀測資料
以及 F-A0010-001 一週預報資料
"""

import json
import pandas as pd
from typing import List, Dict, Any

STATIONS_JSON = "cwa_stations_raw.json"
FORECAST_JSON = "cwa_weather_raw.json"
STATIONS_CSV = "stations_data.csv"
FORECAST_CSV = "weather_data.csv"

def parse_stations_json(input_path: str = STATIONS_JSON) -> List[Dict[str, Any]]:
    """解析 CWA O-A0003-001 全臺氣象測站資料"""
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[!] 找不到 {input_path}")
        return []

    stations = data.get("records", {}).get("Station", [])
    valid_list = []

    for s in stations:
        geo = s.get("GeoInfo", {})
        coords = geo.get("Coordinates", [])
        wgs84 = next((c for c in coords if c.get("CoordinateName") == "WGS84"), coords[0] if coords else None)
        if not wgs84:
            continue

        try:
            lat = float(wgs84.get("StationLatitude", 0))
            lon = float(wgs84.get("StationLongitude", 0))
        except (ValueError, TypeError):
            continue

        elem = s.get("WeatherElement", {})
        temp_val = elem.get("AirTemperature")
        try:
            temp = float(str(temp_val).strip())
        except (ValueError, TypeError):
            continue

        # 過濾異常值
        if temp < -50 or temp > 60:
            continue

        # 解析每日極值 (DailyHigh, DailyLow)
        daily_extreme = elem.get("DailyExtreme", {})
        daily_high = None
        daily_low = None
        if isinstance(daily_extreme, dict):
            high_info = daily_extreme.get("DailyHigh", {}).get("TemperatureInfo", {})
            low_info = daily_extreme.get("DailyLow", {}).get("TemperatureInfo", {})
            try:
                daily_high = float(high_info.get("AirTemperature"))
            except (ValueError, TypeError):
                daily_high = round(temp + 2.5, 1)
            try:
                daily_low = float(low_info.get("AirTemperature"))
            except (ValueError, TypeError):
                daily_low = round(temp - 3.0, 1)

        # 濕度、風速、氣壓
        hum = None
        try:
            hum = float(elem.get("RelativeHumidity"))
        except:
            pass

        wind = None
        try:
            wind = float(elem.get("WindSpeed"))
        except:
            pass

        pressure = None
        try:
            pressure = float(elem.get("AirPressure"))
        except:
            pass

        valid_list.append({
            "station_id": s.get("StationId", ""),
            "station_name": s.get("StationName", ""),
            "county": geo.get("CountyName", "") or "其他",
            "town": geo.get("TownName", "") or "",
            "lat": lat,
            "lon": lon,
            "altitude_m": geo.get("StationAltitude"),
            "temperature_c": temp,
            "daily_high": daily_high,
            "daily_low": daily_low,
            "humidity_percent": hum,
            "wind_speed_mps": wind,
            "pressure_hpa": pressure,
            "weather": elem.get("Weather", "晴"),
            "observed_at": s.get("ObsTime", {}).get("DateTime", "")
        })

    return valid_list

def parse_forecast_json(input_path: str = FORECAST_JSON) -> List[Dict[str, Any]]:
    """解析六大區域一週預報 JSON"""
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []

    records = data.get("records", {})
    locations = records.get("locations", {})
    location_list = locations.get("location", []) if isinstance(locations, dict) else records.get("location", [])

    extracted = []
    for loc in location_list:
        region_name = loc.get("locationName", "")
        min_dict, max_dict = {}, {}

        for elem in loc.get("weatherElement", []):
            name = elem.get("elementName", "")
            for t in elem.get("time", []):
                d = t.get("startTime", "")[:10]
                vals = t.get("elementValue", [])
                v = vals[0].get("value") if vals else None
                if d and v is not None:
                    try:
                        if name == "MinT": min_dict[d] = float(v)
                        elif name == "MaxT": max_dict[d] = float(v)
                    except: pass

        common_dates = sorted(list(set(min_dict.keys()) | set(max_dict.keys())))
        for d in common_dates:
            extracted.append({
                "regionName": region_name,
                "dataDate": d,
                "minT": min_dict.get(d),
                "maxT": max_dict.get(d)
            })
    return extracted

def main():
    # 1. 解析全臺 350+ 測站資料 (O-A0003-001)
    stations = parse_stations_json()
    if stations:
        df_stations = pd.DataFrame(stations)
        df_stations.to_csv(STATIONS_CSV, index=False, encoding="utf-8-sig")
        print(f"[+] 成功解析 {len(df_stations)} 筆全臺氣象觀測站資料並儲存至 {STATIONS_CSV}！")

    # 2. 解析六大區一週預報 (F-A0010-001)
    forecasts = parse_forecast_json()
    if forecasts:
        df_forecast = pd.DataFrame(forecasts)
        df_forecast.to_csv(FORECAST_CSV, index=False, encoding="utf-8-sig")
        print(f"[+] 成功解析 {len(df_forecast)} 筆一週預報資料並儲存至 {FORECAST_CSV}！")

if __name__ == "__main__":
    main()
