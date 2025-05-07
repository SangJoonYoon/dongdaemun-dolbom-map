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
    st.error("❗ centers.csv 파일을 찾을 수 없습니다.")
    st.stop()

if "dong" not in centers.columns:
    st.error("❗ centers.csv에 'dong' 컬럼이 없습니다.")
    st.stop()

# 2) 사이드바: 동 선택
st.sidebar.header("🗺️ 행정동 선택")
dongs = sorted(centers["dong"].unique())
sel = st.sidebar.selectbox("동을 선택하세요", ["전체"] + dongs)

df = centers if sel == "전체" else centers[centers["dong"] == sel]
st.sidebar.markdown(f"- 표시 대상 센터: **{len(df)}개**")

# 3) Folium 지도 준비
if not df.empty:
    center = [df["lat"].mean(), df["lng"].mean()]
else:
    center = [37.574360, 127.039530]
m = folium.Map(location=center, zoom_start=13)

# 4) 센터 마커
for _, r in df.iterrows():
    popup = folium.Popup(
        f"<b>{r['name']}</b><br>"
        f"기능: {r['feature']}<br>"
        f"행사: {r.get('events','-')}<br>"
        f"프로그램: {r.get('programs','-')}<br>"
        f"대상: {r['categories']}", max_width=300
    )
    folium.Marker(
        [r["lat"], r["lng"]],
        tooltip=r["name"],
        popup=popup,
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

# 5) 행정동 GeoJSON (서울특별시) 불러와서 하이라이트
#    ※ Local_HangJeongDong 레포의 서울특별시 파일 사용
GEOJSON_URL = (
    "https://raw.githubusercontent.com/"
    "raqoon886/Local_HangJeongDong/master/"
    "hangjeongdong_서울특별시.geojson"
)
res = requests.get(GEOJSON_URL)
try:
    res.raise_for_status()
except requests.exceptions.HTTPError:
    st.error(f"경계 데이터 로드 실패: {res.status_code}")
    st.stop()

geojson = res.json()

def style_fn(feat):
    nm = feat["properties"].get("adm_nm", "")
    is_sel = (sel != "전체" and sel in nm)
    return {
        "fillColor": "#0055FF" if is_sel else "#ffffff",
        "color":     "#0055FF" if is_sel else "#999999",
        "weight":    2 if is_sel else 1,
        "fillOpacity": 0.3 if is_sel else 0.0,
    }

folium.GeoJson(
    geojson,
    name="행정동경계",
    style_function=style_fn,
    tooltip=folium.GeoJsonTooltip(fields=["adm_nm"], aliases=["행정동"])
).add_to(m)

# 6) 렌더링
st.title("📍 동대문구 돌봄센터 & 행정동 하이라이트")
st.markdown("사이드바에서 동을 선택하면 해당 동 경계가 반투명 파란색으로 강조됩니다.")
st_folium(m, width=700, height=500)
