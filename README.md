# 🌤 HW1 Taiwan Weather Forecast Dashboard

> CWA API × JSON × Python × SQLite × Streamlit × Interactive Taiwan Weather Map


## 🚀 Live Demo

### Taiwan Weather Dashboard

🔗 Demo URL:https://qgouzxx9hch7x3j5xqnkwh.streamlit.app/
🔗 github : https://github.com/Chen-Fanny/L3

## 📸 Preview

![Dashboard](demo(1).jpg)

![Dashboard](demo%20(2).jpg)

---

# ✨ Features


## 🗺 Taiwan Weather Map

- Display CWA weather stations
- Interactive Taiwan map visualization
- Temperature color classification

Temperature levels:

🔵 <20°C

🟢 20~25°C

🟡 25~30°C

🔴 >30°C


Each station provides:

- Temperature
- Humidity
- Wind speed
- Location
- Temperature history chart


---

## 📈 Weekly Forecast

- Select weather region
- Display 7-day forecast
- Maximum / Minimum temperature chart
- Forecast table


---

# ✨ Features

- Retrieve weather data from Central Weather Administration (CWA) API
- Parse JSON weather forecast data using Python
- Store forecast information into SQLite database
- Build interactive Streamlit weather dashboard
- Visualize Taiwan weather station temperature distribution
- Display weekly temperature forecast with charts and tables
- Interactive Taiwan map using Folium


---

# 📂 Project Structure

```text
L3
│
├── app.py                  # Streamlit Web Dashboard
├── fetch_weather.py        # Fetch CWA API weather data
├── parse_weather.py        # Parse JSON and extract temperature data
├── database.py             # Create SQLite database and store data
│
├── data.db                 # SQLite database
├── weather_data.csv        # Parsed forecast data
├── stations_data.csv       # Weather station observation data
│
├── cwa_weather_raw.json    # Original CWA API response
├── cwa_stations_raw.json   # Raw station data
│
├── requirements.txt        # Python dependencies
├── README.md
│
└── demo images
    ├── demo1.jpg
    └── demo2.jpg

