"""
HW10 步驟 4: Streamlit 氣溫預報 Web App (40%)
HW10 步驟 5: 進階：台灣地圖視覺化 (Optional，對齊臺灣即時氣象地圖風格)
"""

import sqlite3
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import folium_static
import branca.colormap as cm

# ==============================================================================
# 頁面配置與現代深色風格 CSS
# ==============================================================================
st.set_page_config(
    page_title="Taiwan Weather Forecast | 臺灣即時氣溫預報",
    page_icon="⛅",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    /* 全域字體與深色主題優化 */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
    }
    
    /* 頂部標題 Hero 區域 */
    .hero-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    }
    .hero-title {
        font-size: 1.8rem;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-top: 4px;
    }
    
    /* 統計卡片 */
    .metric-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        border-color: rgba(56, 189, 248, 0.4);
        transform: translateY(-2px);
    }
    .metric-val {
        font-family: 'Outfit', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        margin: 4px 0;
    }
    .metric-label {
        font-size: 0.78rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* 臺灣即時氣象地圖漸層色階標記 (Bottom-Right Legend) */
    .map-legend-box {
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 8px;
        padding: 10px 14px;
        color: #f1f5f9;
        font-size: 0.78rem;
        margin-top: 10px;
    }
    .legend-bar {
        height: 10px;
        border-radius: 9999px;
        background: linear-gradient(to right, #2c7bb6, #5aa2cf, #abd9e9, #7fcdbb, #d9ef8b, #fee08b, #fdae61, #f46d43, #d73027);
        margin: 6px 0;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==============================================================================
# 資料庫連線與查詢核心函式
# ==============================================================================
DB_PATH = "data.db"

@st.cache_data(ttl=60)
def get_all_regions():
    """從 SQLite 查詢所有可選地區名稱"""
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY id ASC;"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df["regionName"].tolist()

def get_forecast_by_region(region_name: str) -> pd.DataFrame:
    """使用 SQL 從 SQLite 查詢指定地區的一週氣溫預報"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT dataDate, minT, maxT, 
           ROUND((minT + maxT) / 2.0, 1) AS avgT
    FROM TemperatureForecasts 
    WHERE regionName = ? 
    ORDER BY dataDate ASC;
    """
    df = pd.read_sql_query(query, conn, params=(region_name,))
    conn.close()
    return df

def get_all_forecasts_for_map() -> pd.DataFrame:
    """查詢所有區域最新一日氣溫用於地圖視覺化"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT regionName, dataDate, minT, maxT,
           ROUND((minT + maxT) / 2.0, 1) AS avgT
    FROM TemperatureForecasts
    GROUP BY regionName
    HAVING dataDate = MIN(dataDate);
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# 各區域經緯度代表點 (台灣六大區)
REGION_COORDINATES = {
    "北部地區": {"lat": 25.04, "lon": 121.53, "desc": "包含臺北、新北、基隆、桃園、新竹"},
    "東北部地區": {"lat": 24.75, "lon": 121.75, "desc": "包含宜蘭地區"},
    "中部地區": {"lat": 24.15, "lon": 120.68, "desc": "包含苗栗、臺中、彰化、南投、雲林"},
    "東部地區": {"lat": 23.98, "lon": 121.60, "desc": "包含花蓮地區"},
    "南部地區": {"lat": 22.63, "lon": 120.30, "desc": "包含嘉義、臺南、高雄、屏東"},
    "東南部地區": {"lat": 22.76, "lon": 121.15, "desc": "包含臺東地區"}
}

def get_temperature_color(avg_temp: float) -> str:
    """依作業規範設定氣溫標記顏色"""
    if avg_temp < 20.0:
        return "#2c7bb6"  # 藍色 (< 20°C)
    elif avg_temp < 25.0:
        return "#7fcdbb"  # 綠色 (20 - 25°C)
    elif avg_temp < 30.0:
        return "#fee08b"  # 黃色 (25 - 30°C)
    else:
        return "#d73027"  # 紅色 (> 30°C)

# ==============================================================================
# UI 介面呈現
# ==============================================================================

# 頂部標題看板
st.markdown("""
<div class="hero-container">
    <h1 class="hero-title">🌤️ HW10 Taiwan Weather Forecast</h1>
    <div class="hero-subtitle">
        從氣象資料到互動式天氣預報應用程式 · CWA API × JSON × Python × SQLite × Streamlit
    </div>
</div>
""", unsafe_allow_html=True)

# 側邊欄控制項 (功能 1: 下拉選單選擇地區)
st.sidebar.title("⚙️ 預報控制面板")

regions = get_all_regions()
if not regions:
    st.error("⚠️ 資料庫中尚無資料，請先執行 database.py！")
    st.stop()

selected_region = st.sidebar.selectbox(
    "📍 選擇預報地區 (Select Region)",
    options=regions,
    index=regions.index("中部地區") if "中部地區" in regions else 0,
    help="從 SQLite 資料庫中查詢對應區域一週預報"
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**目前選擇**：`{selected_region}`")
if selected_region in REGION_COORDINATES:
    st.sidebar.caption(REGION_COORDINATES[selected_region]["desc"])

# 手動重新載入
if st.sidebar.button("🔄 重新載入 SQLite 資料"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("中央氣象署 CWA OpenData · F-A0010-001")

# 主分頁規劃
tab_chart, tab_map, tab_sql = st.tabs([
    "📈 一週氣溫折線圖與表格 (作業 40%)",
    "🗺️ 臺灣即時氣象地圖 (進階地圖視覺化 · 類 Windy 風格)",
    "🔍 SQLite 即時資料庫查詢"
])

# ==============================================================================
# Tab 1: 一週氣溫折線圖與表格 (HW10 核心需求 40%)
# ==============================================================================
with tab_chart:
    # 執行 SQL 查詢
    df_region = get_forecast_by_region(selected_region)
    
    if df_region.empty:
        st.warning(f"目前無 {selected_region} 的資料。")
    else:
        # 統計資訊小卡
        today_data = df_region.iloc[0]
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">預報區域</div>
                <div class="metric-val" style="color: #38bdf8;">{selected_region}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">今日最低溫 (MinT)</div>
                <div class="metric-val" style="color: #60a5fa;">{today_data['minT']}°C</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">今日最高溫 (MaxT)</div>
                <div class="metric-val" style="color: #f87171;">{today_data['maxT']}°C</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">日平均溫 (AvgT)</div>
                <div class="metric-val" style="color: #34d399;">{today_data['avgT']}°C</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 顯示最高 / 最低溫折線圖 (功能 3)
        st.subheader(f"📊 Temperature Forecast - {selected_region}")
        
        # 整理圖表資料格式
        chart_data = df_region.copy()
        chart_data["Date"] = pd.to_datetime(chart_data["dataDate"]).dt.strftime("%m/%d")
        chart_data = chart_data.rename(columns={"maxT": "MaxT (最高溫)", "minT": "MinT (最低溫)"})
        chart_data = chart_data.set_index("Date")[["MaxT (最高溫)", "MinT (最低溫)"]]
        
        # 使用 Streamlit 內建折線圖繪製雙溫折線
        st.line_chart(chart_data, color=["#ef4444", "#3b82f6"], height=360)

        # 顯示一週資料表格 (功能 4)
        st.subheader("📋 一週氣溫預報資料明細")
        
        display_df = df_region.copy()
        display_df = display_df.rename(columns={
            "dataDate": "預報日期 (Date)",
            "minT": "最低溫 (°C)",
            "maxT": "最高溫 (°C)",
            "avgT": "平均溫 (°C)"
        })
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

# ==============================================================================
# Tab 2: 進階：台灣地圖視覺化 (HW10 步驟 5 + 對齊成果範本風格)
# ==============================================================================
with tab_map:
    st.subheader("🗺️ 臺灣六大區域日平均氣溫地圖 (類 Windy / 暗黑地圖風格)")
    st.caption("點擊各區彩色圓點標記可查看詳細預報，右下角附有標準 CWA 氣溫連續色階圖例。")

    df_map = get_all_forecasts_for_map()

    # 建立 Folium 地圖，預設中心台灣本島 [23.7, 120.95]
    m = folium.Map(
        location=[23.75, 120.95],
        zoom_start=7,
        tiles="CartoDB dark_matter",  # 深色暗黑底圖，對齊成果範本風格
        control_scale=True
    )

    # 在地圖上為六大區域繪製氣溫圓點標記
    for _, row in df_map.iterrows():
        reg_name = row["regionName"]
        if reg_name not in REGION_COORDINATES:
            continue
            
        coord = REGION_COORDINATES[reg_name]
        avg_temp = row["avgT"]
        min_temp = row["minT"]
        max_temp = row["maxT"]
        date_str = row["dataDate"]
        color = get_temperature_color(avg_temp)

        # 彈窗內容 (符合作業規格 + 成果卡片)
        popup_html = f"""
        <div style="font-family: sans-serif; min-width: 160px; line-height: 1.5; color: #1e293b;">
            <h4 style="margin: 0 0 6px 0; color: #0f172a; border-bottom: 2px solid {color}; padding-bottom: 4px;">
                📍 {reg_name}
            </h4>
            <div style="font-size: 0.82rem;"><b>預報日期:</b> {date_str}</div>
            <div style="font-size: 0.82rem;"><b>日最低溫:</b> <span style="color:#2563eb;">{min_temp}°C</span></div>
            <div style="font-size: 0.82rem;"><b>日最高溫:</b> <span style="color:#dc2626;">{max_temp}°C</span></div>
            <div style="font-size: 0.88rem; font-weight: bold; margin-top: 4px; color: {color};">
                日平均溫: {avg_temp}°C
            </div>
        </div>
        """

        # 外圈光暈與主要氣溫圓點
        folium.CircleMarker(
            location=[coord["lat"], coord["lon"]],
            radius=16,
            color=color,
            weight=3,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"{reg_name}: {avg_temp}°C"
        ).addTo(m)

        # 測站文字標籤
        folium.map.Marker(
            [coord["lat"], coord["lon"]],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    font-family: sans-serif;
                    font-weight: 700;
                    font-size: 11px;
                    color: #ffffff;
                    text-shadow: 0 1px 4px rgba(0,0,0,0.9);
                    white-space: nowrap;
                    transform: translate(-50%, -30px);
                    background: rgba(15, 23, 42, 0.85);
                    padding: 2px 6px;
                    border-radius: 4px;
                    border: 1px solid rgba(255,255,255,0.2);
                ">
                    {reg_name} {avg_temp}°C
                </div>
                """
            )
        ).addTo(m)

    # 渲染 Folium 地圖
    folium_static(m, width=1050, height=520)

    # 圖例區 (對齊成果範本 taiwan-weather-map.vercel.app 漸層色階與規範)
    col_l1, col_l2 = st.columns([2, 1])
    with col_l1:
        st.markdown("""
        <div class="map-legend-box">
            <div style="display: flex; justify-content: space-between; font-weight: 600;">
                <span>🌡️ 氣溫視覺化色階 (°C)</span>
                <span>依平均溫度設定顏色</span>
            </div>
            <div class="legend-bar"></div>
            <div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: #94a3b8;">
                <span>5°C</span>
                <span>10°C</span>
                <span>15°C</span>
                <span>20°C</span>
                <span>25°C</span>
                <span>30°C</span>
                <span>35°C+</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_l2:
        st.markdown("""
        <div class="map-legend-box">
            <b>作業色彩分級規範：</b><br>
            🔵 <code>&lt; 20°C</code>：寒冷低溫<br>
            🟢 <code>20 - 25°C</code>：舒適宜人<br>
            🟡 <code>25 - 30°C</code>：溫暖微熱<br>
            🔴 <code>&gt; 30°C</code>：高溫炎熱
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# Tab 3: SQLite 即時資料庫查詢器
# ==============================================================================
with tab_sql:
    st.subheader("🔍 SQLite 直接查詢驗證")
    st.caption("支援在網頁上直接執行 SQL 查詢，驗證資料庫內部存儲之 TemperatureForecasts 資料。")

    default_query = "SELECT * FROM TemperatureForecasts LIMIT 15;"
    user_query = st.text_area("SQL 查詢陳述式", value=default_query, height=80)
    
    if st.button("執行查詢 (Run Query)"):
        try:
            conn = sqlite3.connect(DB_PATH)
            sql_res = pd.read_sql_query(user_query, conn)
            conn.close()
            st.success(f"查詢成功！共返回 {len(sql_res)} 筆資料。")
            st.dataframe(sql_res, use_container_width=True)
        except Exception as err:
            st.error(f"SQL 執行失敗: {err}")
