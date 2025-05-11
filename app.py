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

# 필수 컬럼 체크
required = {"name","lat","lng","feature","programs","categories","dong"}
if not required.issubset(centers.columns):
    st.error(f"❗ centers.csv에 다음 컬럼이 필요합니다: {', '.join(required)}")
    st.stop()

# ─── 사이드바 메뉴 ───────────────────────────────────────
st.sidebar.header("📌 메뉴")
page = st.sidebar.radio("", ["소개","건강지원센터지도","프로그램 목록","프로그램 신청"])

# ─── 1️⃣ 소개 페이지 ─────────────────────────────────────────
if page=="소개":
    st.title("🏥 동대문구 건강지원센터 소개")
    st.markdown("""
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
    """)
    st.image("https://source.unsplash.com/1600x400/?health,clinic")

# ─── 2️⃣ 건강지원센터 지도 페이지 ─────────────────────────────────
elif page=="건강지원센터지도":
    st.title("📍 건강지원센터 위치 지도")
    # 필터 UI
    c1,c2,c3 = st.columns([2,3,3])
    with c1:
        sel_dong = st.selectbox("행정동", ["전체"] + sorted(centers["dong"].unique()))
    with c2:
        kw = st.text_input("센터명 검색", placeholder="예) 회기센터")
    with c3:
        cats = sorted({x for subs in centers["categories"].dropna() for x in subs.split(";")})
        sel_cats = st.multiselect("대상군", cats)

    # 필터링
    mask = pd.Series(True, index=centers.index)
    if sel_dong!="전체":
        mask &= centers["dong"]==sel_dong
    if kw:
        mask &= centers["name"].str.contains(kw, case=False, na=False)
    if sel_cats:
        mask &= centers["categories"].apply(lambda s: any(c in s.split(";") for c in sel_cats))
    df = centers[mask]
    st.caption(f"표시된 센터: {len(df)}개")

    # Folium 지도
    if not df.empty:
        lat,lng = df["lat"].mean(), df["lng"].mean()
        zoom = 14 if sel_dong=="전체" else 16
    else:
        lat,lng,zoom = 37.57436,127.03953,13
    m = folium.Map([lat,lng], zoom_start=zoom, tiles="cartodbpositron")

    # GeoJSON 하이라이트
    GEO = ("https://raw.githubusercontent.com/"
           "raqoon886/Local_HangJeongDong/master/"
           "hangjeongdong_서울특별시.geojson")
    gj = requests.get(GEO).json()
    def style_fn(feat):
        nm = feat["properties"].get("adm_nm","")
        sel = sel_dong!="전체" and sel_dong in nm
        return {
            "fillColor":"#0055FF" if sel else "#ffffff",
            "color":"#0055FF" if sel else "#999999",
            "weight":2 if sel else 1,
            "fillOpacity":0.3 if sel else 0.0
        }
    folium.GeoJson(gj, style_function=style_fn,
                   tooltip=folium.GeoJsonTooltip(fields=["adm_nm"],aliases=["행정동"])
    ).add_to(m)

    # 센터 마커 (팝업에 프로그램 표시)
    for _,r in df.iterrows():
        display = r["name"].replace("돌봄센터","건강지원센터")
        popup = folium.Popup(f"<strong>{display}</strong><br>{r['programs']}", max_width=300)
        folium.Marker([r["lat"],r["lng"]],
                      tooltip=display,
                      popup=popup,
                      icon=folium.Icon(color="green",icon="plus-sign")
        ).add_to(m)

    st_folium(m, width="100%", height=650)

# ─── 3️⃣ 프로그램 목록 페이지 ───────────────────────────────────
elif page=="프로그램 목록":
    st.title("📋 현재 운영중인 프로그램")
    # explode 후 unique
    dfp = centers[["name","programs"]].fillna("").copy()
    dfp["programs"]=dfp["programs"].str.split(";")
    dfp=dfp.explode("programs")
    dfp["programs"]=dfp["programs"].str.strip()
    dfp=dfp[dfp["programs"]!=""]
    # 프로그램별 센터 나열
    for prog,grp in dfp.groupby("programs"):
        names = grp["name"].tolist()
        st.expander(f"{prog} ({len(names)}개 센터)").write(
            "\n".join(f"- {n}" for n in names)
        )

# ─── 4️⃣ 프로그램 신청 페이지 ─────────────────────────────────
else:
    st.title("📝 프로그램 신청")
    # 신청 가능한 프로그램 리스트
    dfp = centers[["programs"]].fillna("").copy()
    dfp["programs"]=dfp["programs"].str.split(";")
    dfp=dfp.explode("programs")
    dfp["programs"]=dfp["programs"].str.strip()
    programs = sorted(dfp[dfp["programs"]!=""]["programs"].unique())

    sel_prog = st.selectbox("프로그램 선택", programs)
    user    = st.text_input("이름")
    contact = st.text_input("연락처",placeholder="010-1234-5678")
    if st.button("신청하기"):
        if sel_prog and user and contact:
            st.success(f"✅ '{sel_prog}' 신청이 완료되었습니다!")
        else:
            st.error("❗ 모든 항목을 입력해주세요.")
