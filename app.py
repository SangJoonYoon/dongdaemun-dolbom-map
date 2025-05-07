import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# --- 1) 데이터 로드 ---------------------------------------------------------
try:
    centers = pd.read_csv("centers.csv")
except FileNotFoundError:
    st.error("❗ centers.csv 파일을 찾을 수 없습니다. 같은 폴더에 파일이 있는지 확인하세요.")
    st.stop()

if "dong" not in centers.columns:
    st.error("❗ centers.csv에 'dong' 컬럼이 없습니다.\nCSV를 아래 예시처럼 업데이트해 주세요.")
    st.markdown(
        """```csv
name,lat,lng,feature,events,programs,categories,dong
청량리돌봄센터,37.582865,127.036583,노인복지·교육,건강검진 지원,어르신 요가;스트레칭,노약자,청량리동
...  
```"""
    )
    st.stop()

# --- 2) 사이드바 UI : 동 선택 -----------------------------------------------
st.sidebar.header("🗺️ 동 선택")
all_dongs = sorted(centers["dong"].unique().tolist())
selected_dong = st.sidebar.selectbox("행정동 선택", ["전체"] + all_dongs)

# 필터링
if selected_dong != "전체":
    df = centers[centers["dong"] == selected_dong]
else:
    df = centers.copy()

st.sidebar.markdown(f"표시된 센터: **{len(df)}개**")

# --- 3) Folium 지도 생성 ---------------------------------------------------
# (이하는 이전에 드린 Folium 코드와 동일)
if len(df) > 0:
    center_lat = df["lat"].mean()
    center_lng = df["lng"].mean()
else:
    center_lat, center_lng = 37.57436, 127.03953

m = folium.Map(location=[center_lat, center_lng], zoom_start=13)
for _, row in df.iterrows():
    popup = folium.Popup(
        f"<strong>{row['name']}</strong><br>"
        f"기능: {row['feature']}<br>"
        f"행사: {row['events']}<br>"
        f"프로그램: {row['programs']}<br>"
        f"대상: {row['categories']}", max_width=300
    )
    folium.Marker(
        [row["lat"], row["lng"]],
        tooltip=row["name"],
        popup=popup,
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

# GeoJSON 하이라이트 (동대문구 전체 / 선택된 동 강조)
GEOJSON_URL = (
    "https://raw.githubusercontent.com/"
    "vuski/admdongkor/main/geojson/행정동_시군구별/서울특별시.geojson"
)
geojson = requests.get(GEOJSON_URL).json()

def style_fn(feature):
    name = feature["properties"].get("adm_nm", "")
    is_this = selected_dong in name
    return {
        "fillColor": "#0055FF" if is_this else "#ffffff",
        "color": "#0055FF" if is_this else "#999999",
        "weight": 2 if is_this else 1,
        "fillOpacity": 0.3 if is_this else 0.0,
    }

folium.GeoJson(
    geojson,
    name="행정동경계",
    style_function=style_fn,
    tooltip=folium.GeoJsonTooltip(fields=["adm_nm"], aliases=["행정동"])
).add_to(m)

# --- 4) Streamlit에 렌더링 --------------------------------------------------
st.title("📍 동대문구 돌봄센터 & 행정동 하이라이트")
st.markdown("사이드바에서 행정동을 선택하면 해당 동 경계가 반투명으로 강조됩니다.")
st_folium(m, width=700, height=500)
