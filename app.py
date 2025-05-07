import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# --- 1) 데이터 로드 ---------------------------------------------------------
centers = pd.read_csv("centers.csv")

# --- 2) 사이드바 UI : 동 선택 -----------------------------------------------
st.sidebar.header("🗺️ 동 선택")
all_dongs = sorted(centers["dong"].unique().tolist())
selected_dong = st.sidebar.selectbox("행정동 선택", ["전체"] + all_dongs)

# 센터 필터링
if selected_dong != "전체":
    df = centers[centers["dong"] == selected_dong]
else:
    df = centers.copy()

st.sidebar.markdown(f"표시된 센터: **{len(df)}개**")

# --- 3) Folium 지도 생성 ---------------------------------------------------
# 지도의 초기 중심: 필터된 센터의 평균 좌표
if len(df) > 0:
    center_lat = df["lat"].mean()
    center_lng = df["lng"].mean()
else:
    # 센터가 없으면 동대문구 대략 중앙
    center_lat, center_lng = 37.57436, 127.03953

m = folium.Map(location=[center_lat, center_lng], zoom_start=13)

# 3-1) 센터 마커 찍기
for _, row in df.iterrows():
    popup = folium.Popup(
        f"<strong>{row['name']}</strong><br>"
        f"기능: {row['feature']}<br>"
        f"행사: {row['events']}<br>"
        f"프로그램: {row['programs']}<br>"
        f"대상: {row['categories']}",
        max_width=300
    )
    folium.Marker(
        [row["lat"], row["lng"]],
        tooltip=row["name"],
        popup=popup,
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

# 3-2) 동대문구 GeoJSON 불러와서 폴리곤 그리기
GEOJSON_URL = (
    "https://raw.githubusercontent.com/"
    "vuski/admdongkor/main/geojson/행정동_시군구별/서울특별시.geojson"
)
geojson = requests.get(GEOJSON_URL).json()

def style_fn(feature):
    # 'properties.adm_nm' 예: "서울특별시 동대문구 회기동"
    name = feature["properties"].get("adm_nm", "")
    is_this = selected_dong in name  # e.g. "회기동" in "서울특별시 동대문구 회기동"
    return {
        "fillColor": "#0055FF" if is_this else "#ffffff",
        "color": "#0055FF" if is_this else "#999999",
        "weight": 2 if is_this else 1,
        "fillOpacity": 0.3 if is_this else 0.0,
    }

# 서울시 전체 -> 동대문구만 필터링 & 적용
# 여기서는 지오JSON 전체를 추가하되 style_fn 으로 동대문구만 하이라이트
folium.GeoJson(
    geojson,
    name="행정동경계",
    style_function=style_fn,
    tooltip=folium.GeoJsonTooltip(fields=["adm_nm"], aliases=["행정동"])
).add_to(m)

# --- 4) Streamlit에 렌더링 --------------------------------------------------
st.title("📍 동대문구 돌봄센터 & 행정동 하이라이트")
st.markdown("사이드바에서 행정동을 선택하면 해당 동 경계가 반투명으로 강조됩니다.")

# folium 으로 그린 지도 표시
st_data = st_folium(m, width=700, height=500)
