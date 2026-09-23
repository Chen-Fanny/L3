# HW10 Taiwan Weather Forecast 從氣象資料到互動式天氣預報應用程式
> **CWA API × JSON × Python × SQLite × Streamlit × 台灣即時氣象地圖 (類 Windy 風格)**

本專案完全滿足 **HW10 作業五大評分標準（100% + 進階加分）**，並對齊成果範本 [台灣即時氣象地圖 (taiwan-weather-map.vercel.app)](https://taiwan-weather-map.vercel.app/) 的暗黑高質感氣候視覺化體驗！

---

## 🎯 作業五大步驟與評分項目對應

| 步驟 | 權重 | 檔案名稱 | 功能說明 | 實作重點 |
|:---:|:---:|:---|:---|:---|
| **1** | **20%** | [`fetch_weather.py`](file:///c:/L3/fetch_weather.py) | **取得 CWA API 資料** | 使用 `requests` 呼叫 CWA API (`F-A0010-001`)，並透過 `json.dumps(..., indent=2, ensure_ascii=False)` 格式化檢視與存成 `cwa_weather_raw.json` |
| **2** | **20%** | [`parse_weather.py`](file:///c:/L3/parse_weather.py) | **分析 JSON，提取氣溫資料** | 解析六大區域（北部、東北部、中部、東部、南部、東南部）每日最低溫 `MinT` 與最高溫 `MaxT`，存成 `weather_data.csv` |
| **3** | **20%** | [`database.py`](file:///c:/L3/database.py) | **存入 SQLite 資料庫** | 建立 `data.db` 與 `TemperatureForecasts` 表，並執行驗證查詢（列出所有地區、查詢中部地區） |
| **4** | **40%** | [`app.py`](file:///c:/L3/app.py) | **Streamlit 氣溫預報 Web App** | 提供下拉選單選擇地區、使用 SQL 從 SQLite 查詢資料、繪製最高/最低溫折線圖、顯示一週表格 |
| **5** | **進階加分** | [`app.py`](file:///c:/L3/app.py) | **臺灣地圖視覺化 (成果對齊)** | 採用 `folium` 暗黑底圖 (CartoDB dark_matter)，六大區依平均溫標記色彩（藍/綠/黃/紅），附右下角連續漸層溫度圖例 |

---

## 📂 專案檔案架構

```text
.
├── fetch_weather.py     # 步驟 1: 呼叫 CWA API 取得六大區一週天氣預報 (JSON)
├── parse_weather.py     # 步驟 2: 解析 JSON 提取每日 MinT / MaxT 氣溫
├── database.py          # 步驟 3: 存入 SQLite (data.db) 並執行 SQL 驗證查詢
├── app.py               # 步驟 4 & 5: Streamlit Web App (折線圖、表格、暗黑地圖)
├── data.db              # SQLite 資料庫檔案 (含 TemperatureForecasts 資料表)
├── weather_data.csv     # (中介產物) 解析完成之氣溫 CSV
├── cwa_weather_raw.json # CWA 原始回傳之 JSON 資料備份
├── requirements.txt     # 作業所需 Python 套件清單
├── README.md            # 作業繳交說明文件
│
├── backend/             # (進階架構) FastAPI 後端氣溫服務
└── frontend/            # (進階架構) Leaflet + Windy Map 前端儀表板
```

---

## 🚀 快速執行步驟

### 1. 安裝所需套件
```bash
pip install -r requirements.txt
```

### 2. 依序執行資料處理流程（一次即可）
```bash
# 步驟 1: 取得氣象資料
python fetch_weather.py

# 步驟 2: 分析 JSON 並提取氣溫
python parse_weather.py

# 步驟 3: 儲存至 SQLite 資料庫並驗證
python database.py
```

### 3. 啟動 Streamlit 互動式 Web App
```bash
streamlit run app.py
```
啟動後瀏覽器會自動開啟 [http://localhost:8501](http://localhost:8501)。

---

## 📊 資料庫結構 (SQLite Schema)

```sql
CREATE TABLE IF NOT EXISTS TemperatureForecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regionName TEXT,
    dataDate TEXT,
    minT REAL,
    maxT REAL
);
```

### 驗證查詢範例：
1. **列出所有地區名稱**：
   ```sql
   SELECT DISTINCT regionName FROM TemperatureForecasts;
   ```
2. **查詢中部地區資料**：
   ```sql
   SELECT * FROM TemperatureForecasts WHERE regionName = '中部地區';
   ```

---

## 🎨 地圖視覺化溫度色彩分級

依據作業評分標準規範：
- 🔵 **`< 20°C` (藍色 `#2c7bb6`)**：寒冷低溫
- 🟢 **`20 - 25°C` (綠色 `#7fcdbb`)**：舒適宜人
- 🟡 **`25 - 30°C` (黃色 `#fee08b`)**：溫暖微熱
- 🔴 **`> 30°C` (紅色 `#d73027`)**：高溫炎熱
