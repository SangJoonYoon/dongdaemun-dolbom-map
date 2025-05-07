# app.py
import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# 1) CSV 로드
try:
    centers = pd.read_csv("centers.csv", encoding="utf-8-sig")
except FileNotFoundError:
    st.error("❗ centers.csv 가 없습니다.")
    st.stop()

if "dong" not in centers.columns:
    st.error("❗ centers.csv 에 ‘dong’ 컬럼이 반드시 있어야 합니다.")
    st.stop()

# 2) 사이드바: 동 선택
st.sidebar.header("🗺️ 행정동 선택")
dongs = sorted(centers["dong"].unique())
sel = st.sidebar.selectbox("동을 선택하세요", ["전체"] + dongs)

df = centers if sel=="전체" else centers[centers["dong"]==sel]
st.sidebar.markdown(f"- 표시 대상 센터: **{len(df)}개**")

# 3) 지도 초기화 (서울 동대문구 중심)
if not df.empty:
    map_center = [df["lat"].mean(), df["lng"].mean()]
else:
    map_center = [37.574360, 127.039530]

m = folium.Map(location=map_center, zoom_start=13)

# 4) 센터 마커 찍기
for _, r in df.iterrows():
    popup = folium.Popup(
        f"<b>{r['name']}</b><br>"
        f"기능: {r['feature']}<br>"
        f"행사: {r.get('events','-')}<br>"
        f"프로그램: {r.get('programs','-')}<br>"
        f"대상: {r['categories']}",
        max_width=300
    )
    folium.Marker(
        location=[r["lat"], r["lng"]],
        tooltip=r["name"],
        popup=popup,
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

# 5) 행정동 GeoJSON 가져오기 & 하이라이트
GEOJSON_URL = (
    "https://raw.githubusercontent.com/"
    "vuski/admdongkor/main/geojson/행정동_시군구별/서울특별시.geojson"
)
res = requests.get(GEOJSON_URL)
res.raise_for_status()
geojson = res.json()

def style_fn(feat):
    name = feat["properties"].get("adm_nm","")
    return {
        "fillColor": "#0055FF" if sel in name else "#ffffff",
        "color": "#0055FF" if sel in name else "#999999",
        "weight": 2 if sel in name else 1,
        "fillOpacity": 0.3 if sel in name and sel!="전체" else 0.0,
    }

folium.GeoJson(
    geojson,
    style_function=style_fn,
    tooltip=folium.GeoJsonTooltip(fields=["adm_nm"], aliases=["행정동"])
).add_to(m)

# 6) 렌더링
st.title("📍 동대문구 돌봄센터 & 행정동 하이라이트")
st.markdown("사이드바에서 동을 선택하면 해당 동 경계가 반투명 파란색으로 강조됩니다.")
st_folium(m, width=700, height=500)
