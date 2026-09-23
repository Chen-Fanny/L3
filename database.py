"""
HW10 步驟 3: 存入 SQLite 資料庫 (20%)
目標：將氣溫資料儲存到 SQLite 資料庫 (data.db)，並執行驗證查詢。
"""

import sqlite3
import pandas as pd
from typing import List, Dict, Any
from parse_weather import parse_weather_json

DB_FILE = "data.db"
CSV_FILE = "weather_data.csv"

def init_database(db_path: str = DB_FILE):
    """初始化資料庫並建立 TemperatureForecasts 資料表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 依作業規格建立資料表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TemperatureForecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        regionName TEXT,
        dataDate TEXT,
        minT REAL,
        maxT REAL
    );
    """)

    conn.commit()
    conn.close()
    print(f"[+] 資料庫 {db_path} 初始化完成，已確認 TemperatureForecasts 資料表結構！")

def insert_forecast_data(records: List[Dict[str, Any]], db_path: str = DB_FILE):
    """將解析後的氣溫資料存入 SQLite 資料表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 先清空舊資料避免重複
    cursor.execute("DELETE FROM TemperatureForecasts;")

    sql = """
    INSERT INTO TemperatureForecasts (regionName, dataDate, minT, maxT)
    VALUES (?, ?, ?, ?);
    """

    data_to_insert = [
        (r["regionName"], r["dataDate"], r["minT"], r["maxT"])
        for r in records
    ]

    cursor.executemany(sql, data_to_insert)
    conn.commit()
    count = cursor.rowcount
    conn.close()
    print(f"[+] 成功存入 {len(data_to_insert)} 筆預報資料至 {db_path}！")

def run_verification_queries(db_path: str = DB_FILE):
    """執行評分標準所要求的驗證查詢"""
    conn = sqlite3.connect(db_path)

    print("\n" + "=" * 50)
    print("【驗證查詢 1】列出所有地區名稱")
    print("SQL: SELECT DISTINCT regionName FROM TemperatureForecasts;")
    print("-" * 50)
    df_regions = pd.read_sql_query("SELECT DISTINCT regionName FROM TemperatureForecasts;", conn)
    print(df_regions.to_string(index=False))

    print("\n" + "=" * 50)
    print("【驗證查詢 2】查詢中部地區資料")
    print("SQL: SELECT * FROM TemperatureForecasts WHERE regionName = '中部地區';")
    print("-" * 50)
    df_central = pd.read_sql_query("SELECT * FROM TemperatureForecasts WHERE regionName = '中部地區';", conn)
    print(df_central.to_string(index=False))
    print("=" * 50 + "\n")

    conn.close()

def main():
    # 1. 初始化資料庫結構
    init_database()

    # 2. 取得解析資料 (優先讀取 CSV 或即時解析)
    try:
        df = pd.read_csv(CSV_FILE)
        records = df.to_dict(orient="records")
    except Exception:
        records = parse_weather_json()

    # 3. 寫入 SQLite
    insert_forecast_data(records)

    # 4. 執行驗證查詢
    run_verification_queries()

if __name__ == "__main__":
    main()
