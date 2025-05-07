import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# --- 0) 페이지 설정 --------------------------------------------------------
st.set_page_config(
    page_title="동대문구 돌봄센터 지도",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1) 데이터 로드 & 검증 ------------------------------------------------
try:
    centers = pd.read_csv("centers.csv", encoding="utf-8-sig")
except FileNotFoundError:
    st.sidebar.error("❗ centers.csv 파일을 찾을 수 없습니다.")
    st.stop()

if "dong" not in centers.columns:
    st.sidebar.error("❗ centers.csv에 'dong' 컬럼이 없습니다.")
    st.stop()

# --- 2) 사이드바: 필터 ----------------------------------------------------
with st.sidebar:
    st.title("🔎 필터")

    with st.expander("1. 행정동 선택", expanded=True):
        all_dongs = sorted(centers["dong"].unique())
        selected_dong = st.radio(
            label="동",
            options=["전체"] + all_dongs,
            index=0
        )

    with st.expander("2. 센터명 검색"):
        name_query = st.text_input(
            label="센터명 포함 키워드",
            placeholder="예) 회기, 주민센터"
        )

    with st.expander("3. 대상군 선택"):
        all_cats = sorted({c for subs in centers["categories"].dropna() for c in subs.split(";")})
        selected_cats = st.multiselect(
            label="대상군",
            options=all_cats
        )

    # 필터 적용 후 개수 표시
    mask = pd.Series(True, index=centers.index)
    if selected_dong != "전체":
        mask &= centers["dong"] == selected_dong
    if name_query:
        mask &= centers["name"].str.contains(name_query, case=False, na=False)
    if selected_cats:
        mask &= centers["categories"].apply(
            lambda s: any(c in s.split(";") for c in selected_cats)
        )
    filtered = centers[mask]
    st.markdown(f"---\n**표시된 센터:** {len(filtered)}개")

# --- 3) 지도 생성 --------------------------------------------------------
# 초기 중심과 줌
if not filtered.empty:
    center_lat = filtered["lat"].mean()
    center_lng = filtered["lng"].mean()
    zoom_start = 14 if selected_dong=="전체" else 16
else:
    center_lat, center_lng = 37.574360, 127.039530
    zoom_start = 13

m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom_start)

# 3-1) 센터 마커 추가
for _, r in filtered.iterrows():
    popup_html = (
        f"<strong>{r['name']}</strong><br>"
        f"기능: {r['feature']}<br>"
        f"행사: {r.get('events','-')}<br>"
        f"프로그램: {r.get('programs','-')}<br>"
        f"대상: {r['categories']}"
    )
    folium.Marker(
        location=[r["lat"], r["lng"]],
        tooltip=r["name"],
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

# 3-2) 행정동 GeoJSON 하이라이트
GEOJSON_URL = (
    "https://raw.githubusercontent.com/"
    "raqoon886/Local_HangJeongDong/master/"
    "hangjeongdong_서울특별시.geojson"
)
try:
    res = requests.get(GEOJSON_URL)
    res.raise_for_status()
    gj = res.json()
    def style_fn(feat):
        nm = feat["properties"].get("adm_nm", "")
        is_sel = (selected_dong!="전체" and selected_dong in nm)
        return {
            "fillColor": "#0055FF" if is_sel else "#ffffff",
            "color":     "#0055FF" if is_sel else "#999999",
            "weight":    2 if is_sel else 1,
            "fillOpacity": 0.3 if is_sel else 0.0,
        }
    folium.GeoJson(
        gj,
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(fields=["adm_nm"], aliases=["행정동"])
    ).add_to(m)
except requests.exceptions.RequestException:
    st.sidebar.warning("⚠️ 행정동 경계 데이터 로드에 실패했습니다.")

# --- 4) 메인: 지도 렌더링 -----------------------------------------------
st.header("동대문구 돌봄센터 위치 지도")
st_folium(m, width="100%", height=650)
