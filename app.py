import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# ─── 페이지 설정 ──────────────────────────────────────
st.set_page_config(
    page_title="동대문구 건강지원센터 지도",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── 0) 첫 방문 안내 팝업 ──────────────────────────────
if 'show_intro' not in st.session_state:
    st.session_state.show_intro = True

if st.session_state.show_intro:
    col_text, col_close = st.columns([9,1])
    with col_text:
        st.markdown(
            """
            ## 📢 건강지원센터 운영 방식
            1. 동대문구 각 동별 1개 건강지원센터 설립  
               혹은 병원 인프라가 부족한 상위 3개 동에 우선 설립  
            2. 병원 연계 센터  
               진료 받은 환자는 사후관리,  
               미진료 주민도 기초 건강측정·등록·상담  
            3. 1:1 맞춤 건강증진 프로그램 제공 및 병원 추천  
            4. 건강동아리 구성  
               보건소·학교·복지관 협약, 설문 기반 체험·교육  
            
            ### 🎯 목적
            1. 만성질환 조기 예방  
            2. 건강생활습관 개선 프로그램 제공  
            """
        )
    with col_close:
        if st.button("X"):
            st.session_state.show_intro = False
    st.markdown("---")

# ─── 1) 데이터 로드 & 검증 ─────────────────────────────
try:
    centers = pd.read_csv("centers.csv", encoding="utf-8-sig")
except FileNotFoundError:
    st.sidebar.error("❗ centers.csv 파일을 찾을 수 없습니다.")
    st.stop()

if "dong" not in centers.columns:
    st.sidebar.error("❗ centers.csv에 'dong' 컬럼이 없습니다.")
    st.stop()

# ─── 2) 사이드바: 필터 ─────────────────────────────────
with st.sidebar:
    st.title("🔎 필터")

    with st.expander("1. 행정동 선택", expanded=True):
        all_dongs = sorted(centers["dong"].unique())
        selected_dong = st.radio(
            "동", ["전체"] + all_dongs, index=0
        )

    with st.expander("2. 센터명 검색"):
        name_query = st.text_input(
            "건강지원센터명 포함 키워드",
            placeholder="예) 회기, 주민"
        )

    with st.expander("3. 대상군 선택"):
        cats = sorted({c for subs in centers["categories"].dropna() for c in subs.split(";")})
        selected_cats = st.multiselect("대상군", cats)

    # 필터 적용
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

# ─── 3) 지도 생성 ──────────────────────────────────────
# 중심 좌표 & 줌
if not filtered.empty:
    center_lat = filtered["lat"].mean()
    center_lng = filtered["lng"].mean()
    zoom_start = 14 if selected_dong=="전체" else 16
else:
    center_lat, center_lng = 37.574360, 127.039530
    zoom_start = 13

m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom_start)

# 3-1) 건강지원센터 마커 추가
for _, r in filtered.iterrows():
    display_name = r["name"].replace("돌봄센터", "건강지원센터")
    popup_html = (
        f"<strong>{display_name}</strong><br>"
        f"<em>기능:</em> {r['feature']}<br>"
        f"<em>행사:</em> {r.get('events','-')}<br>"
        f"<em>프로그램:</em> {r.get('programs','-')}<br>"
        f"<em>대상:</em> {r['categories']}"
    )
    folium.Marker(
        location=[r["lat"], r["lng"]],
        tooltip=display_name,
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color="green", icon="plus-sign")
    ).add_to(m)

# 3-2) GeoJSON으로 행정동 경계 하이라이트
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
        nm = feat["properties"].get("adm_nm","")
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
    st.sidebar.warning("⚠️ 행정동 경계 데이터 로드 실패")

# ─── 4) 지도 렌더링 ───────────────────────────────────
st.header("동대문구 건강지원센터 위치 지도")
st_folium(m, width="100%", height=650)
