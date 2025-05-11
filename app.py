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

required = {"name","lat","lng","feature","programs","categories","dong"}
if not required.issubset(centers.columns):
    st.error(f"❗ centers.csv에 다음 컬럼이 필요합니다: {', '.join(required)}")
    st.stop()

# ─── 사이드바 메뉴 ───────────────────────────────────────
st.sidebar.header("📌 메뉴")
page = st.sidebar.radio("", ["소개", "건강지원센터지도", "프로그램 목록", "프로그램 신청"])

# ─── 1️⃣ 소개 페이지 ─────────────────────────────────────────
if page == "소개":
    st.title("🏥 동대문구 건강지원센터 소개")
    st.markdown("""
    소개 
1. 동대문구 동별 건강지원센터 설립
-병원 인프라가 부족한 상위 3개 동 우선 선정

-공공데이터(동별 인구수, 병·의원 수)를 분석해 인구 대비 의료기관 수, 65세 이상 인구 대비 의료기관 수를 산출하여 위치 선정

-해당 지역에 건강지원센터 설치


2. 병원 연계 사후관리

-진료 환자 사후관리 및 미진료 주민 대상 기초검진·상담 제공

-병원과의 협약을 통해 환자 맞춤형 사후관리 시스템 운영


3. 맞춤 건강증진 프로그램 & 병원 추천

-지역별 만성질환 의료수요에 맞춘 맞춤형 프로그램 구성

-개인별 건강 상태에 따라 병원·건강지원센터 추천


4. 건강동아리 구성

-보건소·학교·복지관 협력, 주민 설문 기반 체험·교육 프로그램 운영

-독거노인을 위한 건강동아리 개설해서 정기 건강체크, 운동 모임, 정서적 지지 활동으로 건강 소외계층 돌봄 기능 강화


목적

1. 만성질환 조기 예방

-고혈압, 당뇨, 심뇌혈관질환 등 조기 발견 및 지속적인 관리


2. 건강생활습관 개선 프로그램 제공

-맞춤형 운동, 영양, 금연, 스트레스 관리 프로그램 운영


3. 주민 건강정보 접근성 강화

-건강지원센터 웹사이트를 통해 동대문구에서 진행되는 건강 프로그램을 한눈에 확인하고, 바로 신청 가능

-가까운 병원과 센터 정보 제공


4. 의료 사각지대 해소 및 건강 공동체 조성

-의료 인프라 취약 지역 주민 건강관리 체계 마련

-건강동아리, 체험행사, 교육 프로그램을 통해 지역 공동체 결속력 강화  

    """)
    st.image("https://source.unsplash.com/1600x400/?health,clinic")

# ─── 2️⃣ 건강지원센터 지도 페이지 ─────────────────────────────────
elif page == "프로그램 장소":
    st.title("📍 건강지원센터 지도")

    # 필터 UI
    c1, c2, c3 = st.columns([2, 3, 3])
    with c1:
        sel_dong = st.selectbox("행정동", ["전체"] + sorted(centers["dong"].unique()))
    with c2:
        kw = st.text_input("센터명 검색", placeholder="예) 회기센터")
    with c3:
        cats = sorted({c for subs in centers["categories"].dropna() for c in subs.split(";")})
        sel_cats = st.multiselect("대상군", cats)

    # 필터링
    mask = pd.Series(True, index=centers.index)
    if sel_dong != "전체":
        mask &= centers["dong"] == sel_dong
    if kw:
        mask &= centers["name"].str.contains(kw, case=False, na=False)
    if sel_cats:
        mask &= centers["categories"].apply(lambda s: any(c in s.split(";") for c in sel_cats))
    df = centers[mask]
    st.caption(f"표시된 센터: {len(df)}개")

    # Folium 지도 생성
    if not df.empty:
        center_lat = df["lat"].mean()
        center_lng = df["lng"].mean()
        zoom_start = 14 if sel_dong == "전체" else 16
    else:
        center_lat, center_lng, zoom_start = 37.57436, 127.03953, 13

    m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom_start, tiles="cartodbpositron")

    # 행정동 GeoJSON 하이라이트
    GEO_URL = (
        "https://raw.githubusercontent.com/"
        "raqoon886/Local_HangJeongDong/master/"
        "hangjeongdong_서울특별시.geojson"
    )
    gj = requests.get(GEO_URL).json()
    def style_fn(feat):
        nm = feat["properties"].get("adm_nm", "")
        sel = (sel_dong != "전체" and sel_dong in nm)
        return {
            "fillColor": "#0055FF" if sel else "#ffffff",
            "color":     "#0055FF" if sel else "#999999",
            "weight":    2 if sel else 1,
            "fillOpacity": 0.3 if sel else 0.0,
        }
    folium.GeoJson(
        gj,
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(fields=["adm_nm"], aliases=["행정동"])
    ).add_to(m)

    # 센터 마커 (중복된 이름 한 번씩만 표시)
    for _, r in df.drop_duplicates(subset=["name"]).iterrows():
        title = r["name"].replace("돌봄센터", "건강지원센터")
        popup_html = f"""
          <div style="max-width:250px;font-family:Arial, sans-serif;">
            <h4 style="margin:0 0 6px;">{title}</h4>
            <p style="margin:0;font-weight:600;">프로그램:</p>
            <ul style="margin:4px 0 0 16px 16px;padding:0;list-style:disc;">
              <li>{r['programs']}</li>
            </ul>
          </div>
        """
        folium.Marker(
            [r["lat"], r["lng"]],
            tooltip=title,
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color="green", icon="plus-sign")
        ).add_to(m)

    st_folium(m, width="100%", height=650)

# ─── 3️⃣ 프로그램 목록 페이지 ───────────────────────────────────
elif page == "프로그램 목록":
    st.title("📋 현재 운영중인 프로그램")

    dfp = centers[["name", "programs"]].fillna("").copy()
    dfp["programs"] = dfp["programs"].str.split(";")
    dfp = dfp.explode("programs")
    dfp["programs"] = dfp["programs"].str.strip()
    dfp = dfp[dfp["programs"] != ""]

    for prog, grp in dfp.groupby("programs"):
        names = grp["name"].tolist()
        with st.expander(f"{prog} ({len(names)}개 센터)"):
            for nm in names:
                st.write(f"- {nm}")

# ─── 4️⃣ 프로그램 신청 페이지 ─────────────────────────────────
else:  # 프로그램 신청
    st.title("📝 프로그램 신청")

    dfp = centers[["programs"]].fillna("").copy()
    dfp["programs"] = dfp["programs"].str.split(";")
    dfp = dfp.explode("programs")
    dfp["programs"] = dfp["programs"].str.strip()
    programs = sorted(dfp[dfp["programs"] != ""].programs.unique())

    if not programs:
        st.info("등록된 프로그램이 없습니다.")
        st.stop()

    sel_prog  = st.selectbox("프로그램 선택", programs)
    user_name = st.text_input("이름")
    contact   = st.text_input("연락처", placeholder="010-1234-5678")

    if st.button("신청하기"):
        if sel_prog and user_name and contact:
            st.success(f"✅ '{sel_prog}' 신청이 완료되었습니다!")
        else:
            st.error("❗ 모든 항목을 입력해주세요.")
