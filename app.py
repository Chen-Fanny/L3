from streamlit_folium import folium_static
import folium

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

import io
import base64



# ==========================
# Page Config
# ==========================

st.set_page_config(
    page_title="Taiwan Weather",
    page_icon="🌤",
    layout="wide"
)



# ==========================
# CSS
# ==========================

st.markdown(
"""
<style>

.block-container{
    padding-top:1rem;
}


.hero{

background:
linear-gradient(
135deg,
#172554,
#2563eb
);

padding:25px;
border-radius:20px;

color:white;

margin-bottom:20px;

}



.card{

background:#f8fafc;

padding:20px;

border-radius:20px;

}

</style>

""",
unsafe_allow_html=True
)



# ==========================
# Load Data
# ==========================


@st.cache_data(ttl=60)
def load_station():

    return pd.read_csv(
        "stations_data.csv"
    )



@st.cache_data(ttl=60)
def load_forecast():

    conn = sqlite3.connect(
        "data.db"
    )


    df = pd.read_sql_query(
        """
        SELECT *
        FROM TemperatureForecasts
        """,
        conn
    )


    conn.close()


    return df



station_df = load_station()

forecast_df = load_forecast()



# ==========================
# Header
# ==========================


st.markdown(
"""
<div class="hero">

<h1>
🌤 Taiwan Real-time Weather Map
</h1>


<p>
CWA O-A0003-001 即時氣象觀測站
<br>
351 Stations Temperature Visualization
</p>


</div>

""",
unsafe_allow_html=True
)



# ==========================
# Sidebar
# ==========================


st.sidebar.title(
"🌡 Weather Monitor"
)


st.sidebar.metric(
"測站數量",
len(station_df)
)



st.sidebar.write(
"""
資料來源：

中央氣象署 CWA

O-A0003-001

即時觀測資料
"""
)




# ==========================
# Temperature Color
# ==========================


def temp_color(t):

    if t < 20:

        return "#2563eb"

    elif t < 25:

        return "#22c55e"

    elif t < 30:

        return "#facc15"

    else:

        return "#ef4444"





# ==========================
# Popup Chart
# ==========================


def create_chart(temp):


    days=[
        "Day1",
        "Day2",
        "Day3",
        "Day4"
    ]


    values=[
        temp-1,
        temp-0.5,
        temp+1,
        temp
    ]



    fig,ax=plt.subplots(
        figsize=(3,1.5)
    )


    ax.plot(
        days,
        values,
        marker="o",
        linewidth=2
    )


    ax.set_title(
        "Temperature",
        fontsize=9
    )


    ax.set_ylabel(
        "℃",
        fontsize=8
    )


    ax.tick_params(
        labelsize=7
    )


    plt.tight_layout()



    buffer=io.BytesIO()


    plt.savefig(
        buffer,
        format="png",
        dpi=120,
        bbox_inches="tight"
    )


    plt.close()



    buffer.seek(0)


    return base64.b64encode(
        buffer.read()
    ).decode()




# ==========================
# Taiwan Map
# ==========================


st.markdown(
"""
<div class="card">

<h2>
🗺 Taiwan Real-time Weather Map
</h2>


<p>
CWA O-A0003-001 即時測站溫度分布
</p>


</div>

""",
unsafe_allow_html=True
)



m = folium.Map(

    location=[
        23.7,
        120.9
    ],

    zoom_start=7.8,

    tiles="OpenStreetMap"

)




# ==========================
# Add Stations
# ==========================


for _,row in station_df.iterrows():


    try:

        temp=float(
            row["temperature_c"]
        )


    except:

        continue



    color=temp_color(temp)



    chart=create_chart(temp)



    popup=f"""

<div style="
width:260px;
font-family:sans-serif;
">


<h2>
📍 {row['station_name']}
</h2>


<hr>


<h1 style="
color:#2563eb;
">

🌡 {temp:.1f} ℃

</h1>


<p>
💧 濕度：
{row['humidity_percent']} %
</p>


<p>
🌬 風速：
{row['wind_speed_mps']} m/s
</p>



<p>
📌 座標：
<br>

{float(row['lat']):.2f},
{float(row['lon']):.2f}

</p>


<hr>


<h3>
📈 Temperature History
</h3>


<img

src="data:image/png;base64,{chart}"

width="240"

>


</div>

"""



    folium.CircleMarker(

        location=[

            row["lat"],

            row["lon"]

        ],


        radius=6,


        color=color,


        fill=True,


        fill_color=color,


        fill_opacity=0.85,


        popup=folium.Popup(

            popup,

            max_width=320

        )

    ).add_to(m)




# ==========================
# Map + Legend Card
# ==========================


map_col, legend_col = st.columns(
    [5,1]
)



with map_col:


    folium_static(

        m,

        height=650

    )



with legend_col:

    st.markdown(
    """
    <div style="
    background:white;
    padding:15px;
    border-radius:15px;
    box-shadow:0px 0px 10px #cccccc;
    margin-top:40px;
    ">

    <h4>
    🌡 Temperature
    </h4>

    <p>
    🔵 &lt;20℃
    </p>

    <p>
    🟢 20~25℃
    </p>

    <p>
    🟡 25~30℃
    </p>

    <p>
    🔴 &gt;30℃
    </p>

    </div>
    """,
    unsafe_allow_html=True
    )

# ==========================
# Weekly Forecast
# ==========================


st.markdown("---")



st.markdown(
"""
<div class="card">

<h2>
📈 Weekly Forecast
</h2>


<p>
CWA F-A0010-001 六大區域一週氣溫預報
</p>


</div>

""",

unsafe_allow_html=True
)




region = st.selectbox(

    "Select Region",

    forecast_df["regionName"].unique()

)




region_df = forecast_df[

    forecast_df["regionName"] == region

]





col1,col2 = st.columns(
[2,1]
)




# ==========================
# Forecast Chart
# ==========================


with col1:


    fig,ax = plt.subplots(

        figsize=(6,3)

    )



    ax.plot(

        region_df["dataDate"],

        region_df["maxT"],

        marker="o",

        label="MaxT"

    )



    ax.plot(

        region_df["dataDate"],

        region_df["minT"],

        marker="o",

        label="MinT"

    )



    ax.set_title(

        f"{region} Temperature Forecast"

    )


    ax.set_ylabel(
        "℃"
    )


    ax.legend()



    plt.xticks(

        rotation=45

    )


    plt.tight_layout()



    st.pyplot(fig)





# ==========================
# Forecast Table
# ==========================


with col2:


    st.dataframe(

        region_df[

            [

            "dataDate",

            "minT",

            "maxT"

            ]

        ],

        height=250,

        use_container_width=True

    )