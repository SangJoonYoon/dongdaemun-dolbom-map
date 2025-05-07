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

# 2) 사이드바: 표시할 센터 수만
st.sidebar.header("🗺️ 현재 표시된 센터")
# (동 선택은 아래 배너에서)
st.sidebar.markdown(f"- 전체 센터: **{len(centers)}개**")

# 3) 상단 배너: 동 선택 버튼 바
st.title("📍 동대문구 돌봄센터 지도")

dongs = sorted(centers["dong"].unique())
all_buttons = ["전체"] + dongs
cols = st.columns(len(all_buttons))
sel = st.session_state.get("selected_dong", "전체")

for idx, dong in enumerate(all_buttons):
    # 선택된 동 앞에 ▶ 표시
    label = f"▶ {dong}" if sel == dong else dong
    if cols[idx].button(label, key=f"btn_{dong}"):
        sel = dong
        st.session_state["selected_dong"] = dong


# 4) 선택된 동 기준 필터링
if sel != "전체":
    df = centers[centers["dong"] == sel]
else:
    df = centers.copy()

# 사이드바에도 갱신된 개수 표시
st.sidebar.markdown(f"- 선택된 센터: **{len(df)}개**")

# 5) Folium 지도 초기화
if not df.empty:
    center = [df["lat"].mean(), df["lng"].mean()]
    zoom  = 14 if sel=="전체" else 16
else:
    center = [37.574360, 127.039530]
    zoom   = 13

m = folium.Map(location=center, zoom_start=zoom)

# 6) 센터 마커
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
        [r["lat"], r["lng"]],
        tooltip=r["name"],
        popup=popup,
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

# 7) GeoJSON 불러와서 선택된 동만 하이라이트
GEOJSON_URL = (
    "https://raw.githubusercontent.com/"
    "raqoon886/Local_HangJeongDong/master/"
    "hangjeongdong_서울특별시.geojson"
)
res = requests.get(GEOJSON_URL)
try:
    res.raise_for_status()
    geojson = res.json()
    def style_fn(feat):
        name = feat["properties"].get("adm_nm","")
        is_sel = (sel!="전체" and sel in name)
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
except requests.exceptions.HTTPError:
    st.warning("⚠️ 경계 데이터 로드에 실패했습니다.")

# 8) 스트림릿에 맵 렌더링
st_folium(m, width=700, height=500)
