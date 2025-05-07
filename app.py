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

# ─── 스타일 개선 ─────────────────────────────────────────
st.markdown("""
    <style>
    .sidebar .sidebar-content {
        background-color: #f4f4f4;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 8px 16px;
        margin: 5px 0;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stTextInput>div>input {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 6px;
    }
    .stSelectbox>div>div {
        border: 1px solid #ccc;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# ─── 레이아웃: 사이드바 메뉴 ────────────────────────────
st.sidebar.header("📌 메뉴")
page = st.sidebar.radio(
    "이동할 페이지를 선택하세요",
    ["소개", "건강지원센터 지도", "프로그램 신청"]
)

# ─── 소개 페이지 ──────────────────────────────────────────
if page == "소개":
    st.title("🏥 건강지원센터 소개")
    st.markdown(
        """
        **1. 동대문구 각 동별 건강지원센터 설립**  
        - 병원 인프라가 약한 상위 3개 동 우선  
        **2. 병원 연계 사후관리**  
        - 진료 환자 사후관리, 미진료 주민 기초 검사·상담  
        **3. 1:1 맞춤 건강증진 프로그램 & 병원 추천**  
        **4. 건강동아리 구성**  
        - 보건소·학교·복지관 협약, 주민 설문 기반 체험·교육  

        ### 🎯 목적
        1. 만성질환 조기 예방  
        2. 건강생활습관 개선 프로그램 제공
        """
    )
    st.image("https://source.unsplash.com/1600x400/?health,clinic")

# ─── 건강지원센터 지도 페이지 ──────────────────────────────
elif page == "건강지원센터 지도":
    st.title("📍 건강지원센터 위치 지도")

    # ── 필터 바 ──────────────────────────────────
    st.markdown("### 🔍 센터 필터")
    col1, col2, col3 = st.columns([2, 3, 3])
    with col1:
        selected_dong = st.selectbox(
            "행정동",
            options=["전체"] + sorted(centers["dong"].unique().tolist()),
            key="filter_dong"
        )
    with col2:
        name_query = st.text_input(
            "센터명 검색",
            placeholder="예) 회기, 주민",
            key="filter_name"
        )
    with col3:
        all_cats = sorted({c for subs in centers["categories"].dropna() for c in subs.split(";")})
        selected_cats = st.multiselect(
            "대상군",
            options=all_cats,
            key="filter_cats"
        )

    # ── 필터 적용 ──────────────────────────────────
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
    st.caption(f"표시된 센터: {len(filtered)}개")

    # ── 지도 표시 ──────────────────────────────────
    if not filtered.empty:
        center_lat = filtered["lat"].mean()
        center_lng = filtered["lng"].mean()
        zoom_start = 14 if selected_dong == "전체" else 16
    else:
        center_lat, center_lng = 37.574360, 127.039530
        zoom_start = 13

    m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom_start)

    # 센터 마커
    for _, r in filtered.iterrows():
        name = r["name"]
        popup_html = (
            f"<strong>{name}</strong><br>"
            f"기능: {r['feature']}<br>"
            f"행사: {r.get('events', '-')}<br>"
            f"프로그램: {r.get('programs', '-')}<br>"
            f"대상: {r['categories']}"
        )
        folium.Marker(
            location=[r["lat"], r["lng"]],
            popup=popup_html,
            tooltip=name,
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    # 지도 출력
    st_folium(m, width="100%", height=600)

# ─── 프로그램 신청 페이지 ──────────────────────────────
elif page == "프로그램 신청":
    st.title("📝 프로그램 신청")
    st.markdown("### 💡 원하는 프로그램을 선택하여 신청하세요.")

    program_name = st.text_input("프로그램 이름", placeholder="예: 건강 체조")
    participant_name = st.text_input("신청자 이름")
    contact = st.text_input("연락처", placeholder="010-1234-5678")

    if st.button("신청하기"):
        if program_name and participant_name and contact:
            st.success(f"✅ {program_name} 신청이 완료되었습니다!")
        else:
            st.error("❗ 모든 정보를 입력해주세요.")
