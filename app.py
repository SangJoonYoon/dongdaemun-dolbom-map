import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# ─── 페이지 설정 ─────────────────────────────────────────
st.set_page_config(
    page_title="동대문구 건강지원센터",
    page_icon="🏥",
    layout="wide"
)

# ─── 데이터 로드 & 검증 ───────────────────────────────────
try:
    centers = pd.read_csv("centers.csv", encoding="utf-8-sig")
except FileNotFoundError:
    st.error("❗ centers.csv 파일을 찾을 수 없습니다.")
    st.stop()
if "dong" not in centers.columns:
    st.error("❗ centers.csv에 'dong' 컬럼이 없습니다.")
    st.stop()

# ─── 더미 프로그램 데이터 ─────────────────────────────────
programs_data = [
    {"카테고리": "건강생활", "프로그램명": "생활체육 요가 교실", "기간": "5/1~6/30", "대상": "성인", "장소": "구민체육센터"},
    {"카테고리": "정신건강", "프로그램명": "마음건강 상담 챗봇", "기간": "상시", "대상": "전체", "장소": "온라인"},
    {"카테고리": "가족지원", "프로그램명": "부모-자녀 워크숍", "기간": "7/15", "대상": "부모·자녀", "장소": "건강가정지원센터"}
]
programs_df = pd.DataFrame(programs_data)

# ─── 사이드바 메뉴 ───────────────────────────────────────
st.sidebar.header("📌 메뉴")
page = st.sidebar.radio("", ["소개", 
                             "건강지원센터지도", 
                             "프로그램 목록", 
                             "프로그램 신청"])

# ─── 소개 페이지 ─────────────────────────────────────────
if page == "소개":
    st.title("🏥 건강지원센터 소개")
    st.markdown(
        """
        **1. 동대문구 각 동별 건강지원센터 설립**  
        **2. 병원 연계 사후관리**  
        **3. 1:1 맞춤 건강증진 프로그램 & 병원 추천**  
        **4. 건강동아리 구성**  

        ### 🎯 목적
        - 만성질환 조기 예방  
        - 건강생활습관 개선 프로그램 제공
        """
    )
    st.image("https://source.unsplash.com/1600x400/?health,clinic")

# ─── 지도 페이지 ─────────────────────────────────────────
elif page == "건강지원센터지도":
    st.title("📍 건강지원센터 위치 지도")

    # 필터 UI
    f1, f2, f3 = st.columns([2,3,3])
    with f1:
        selected_dong = st.selectbox("행정동", ["전체"] + sorted(centers["dong"].unique()))
    with f2:
        name_q = st.text_input("센터명 검색", placeholder="예) 회기센터")
    with f3:
        cats = sorted({c for subs in centers["categories"].dropna() for c in subs.split(";")})
        selected_cats = st.multiselect("대상군", cats)

    # 필터링
    mask = pd.Series(True, index=centers.index)
    if selected_dong!="전체":
        mask &= centers["dong"]==selected_dong
    if name_q:
        mask &= centers["name"].str.contains(name_q, case=False)
    if selected_cats:
        mask &= centers["categories"].apply(lambda s: any(c in s.split(";") for c in selected_cats))
    df = centers[mask]
    st.caption(f"표시된 센터: {len(df)}개")

    # 지도 생성
    if not df.empty:
        lat, lng = df["lat"].mean(), df["lng"].mean()
        zoom = 14 if selected_dong=="전체" else 16
    else:
        lat, lng, zoom = 37.57436,127.03953,13
    m = folium.Map(location=[lat,lng], zoom_start=zoom)

    # 동 하이라이트
    GEO = "https://raw.githubusercontent.com/raqoon886/Local_HangJeongDong/master/hangjeongdong_서울특별시.geojson"
    geo = requests.get(GEO).json()
    def style_fn(feat):
        name=feat["properties"]["adm_nm"]
        sel = (selected_dong!="전체" and selected_dong in name)
        return {
            "fillColor":"#0055FF" if sel else "#ffffff",
            "color":"#0055FF" if sel else "#999999",
            "weight":2 if sel else 1,
            "fillOpacity":0.3 if sel else 0.0
        }
    folium.GeoJson(geo, style_function=style_fn,
                   tooltip=folium.GeoJsonTooltip(fields=["adm_nm"],aliases=["행정동"])
    ).add_to(m)

    # 마커
    for _,r in df.iterrows():
        folium.Marker(
            [r.lat,r.lng],
            tooltip=r.name,
            popup=f"<b>{r.name}</b><br>{r.feature}",
            icon=folium.Icon(color="green")
        ).add_to(m)

    st_folium(m, height=600, width="100%")

# ─── 프로그램 목록 페이지 ─────────────────────────────────
elif page == "프로그램 목록":
    st.title("📋 프로그램 목록")
    for _, p in programs_df.iterrows():
        with st.expander(f"{p['프로그램명']} ({p['카테고리']})"):
            st.write(f"- 기간: {p['기간']}")
            st.write(f"- 대상: {p['대상']}")
            st.write(f"- 장소: {p['장소']}")

# ─── 프로그램 신청 페이지 ─────────────────────────────────
else:  # 프로그램 신청
    st.title("📝 프로그램 신청")
    prog = st.selectbox("프로그램 선택", programs_df["프로그램명"])
    name = st.text_input("이름")
    contact = st.text_input("연락처")
    if st.button("신청하기"):
        if prog and name and contact:
            st.success(f"✅ '{prog}' 신청이 완료되었습니다!")
        else:
            st.error("❗ 모든 항목을 입력해 주세요.")
