"""
HW10 步驟 2: 分析 JSON，提取氣溫資料 (20%)
目標：分析 JSON 結構，找出並提取每日最高與最低氣溫 (Region 在資料中通常以 Location 表示)
"""

import json
import pandas as pd
from typing import List, Dict, Any

INPUT_FILE = "cwa_weather_raw.json"
OUTPUT_CSV = "weather_data.csv"

def parse_weather_json(input_path: str = INPUT_FILE) -> List[Dict[str, Any]]:
    """分析 JSON 結構並提取各區域每日最高溫與最低溫"""
    print(f"[*] 讀取檔案: {input_path} ...")
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = data.get("records", {})
    # 支援 locations.location 或直接 location 結構
    locations = records.get("locations", {})
    if isinstance(locations, dict) and "location" in locations:
        location_list = locations["location"]
    elif "location" in records:
        location_list = records["location"]
    else:
        raise ValueError("無法在 JSON 中找到 location 清單！")

    extracted_records = []

    for loc in location_list:
        region_name = loc.get("locationName", "")
        weather_elements = loc.get("weatherElement", [])

        # 分別抓取 MinT 與 MaxT
        min_dict = {}
        max_dict = {}

        for elem in weather_elements:
            elem_name = elem.get("elementName", "")
            times = elem.get("time", [])

            if elem_name == "MinT":
                for t in times:
                    # 擷取日期 (例如 2026-04-14)
                    date_str = t.get("startTime", "")[:10]
                    vals = t.get("elementValue", [])
                    val = vals[0].get("value") if vals else None
                    if date_str and val is not None:
                        try:
                            min_dict[date_str] = float(val)
                        except ValueError:
                            pass

            elif elem_name == "MaxT":
                for t in times:
                    date_str = t.get("startTime", "")[:10]
                    vals = t.get("elementValue", [])
                    val = vals[0].get("value") if vals else None
                    if date_str and val is not None:
                        try:
                            max_dict[date_str] = float(val)
                        except ValueError:
                            pass

        # 合併同日期的 MinT 與 MaxT
        common_dates = sorted(list(set(min_dict.keys()).intersection(set(max_dict.keys()))))
        if not common_dates:
            common_dates = sorted(list(set(min_dict.keys()) | set(max_dict.keys())))

        for d in common_dates:
            extracted_records.append({
                "regionName": region_name,
                "dataDate": d,
                "minT": min_dict.get(d),
                "maxT": max_dict.get(d)
            })

    return extracted_records

def main():
    records = parse_weather_json()
    df = pd.DataFrame(records)

    print(f"\n[+] 成功解析 {len(df)} 筆氣溫預報資料！")
    print(f"[*] 涵蓋區域: {df['regionName'].unique().tolist()}")
    print("\n--- 提取結果範例 (前 10 筆) ---")
    print(df.head(10).to_string(index=False))

    # 儲存為 CSV
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n[+] 已成功儲存至: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
