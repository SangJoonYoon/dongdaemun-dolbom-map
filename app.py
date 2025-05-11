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
    1. 동대문구 동별 건강지원센터 설립  
    2. 병원 연계 사후관리  
    3. 1:1 맞춤 건강증진 프로그램 & 병원 추천  
    4. 건강동아리 구성  

    🎯 목적  
    - 만성질환 조기 예방  
    - 건강생활습관 개선  
    """)
    st.image("https://source.unsplash.com/1600x400/?health,clinic")

# ─── 2️⃣ 건강지원센터 지도 페이지 ─────────────────────────────────
elif page == "건강지원센터지도":
    st.title("📍 건강지원센터 위치 지도")
    st.markdown("**휘경2동 · 이문2동 · 답십리2동** 세 곳만 표시합니다.")

    # 이 세 동만 필터링
    target_dongs = ["답십리2동", "이문2동", "휘경2동"]
    df = centers[centers["dong"].isin(target_dongs)]

    # 지도 중심점: 세 곳 평균
    lat = df["lat"].mean()
    lng = df["lng"].mean()

    m = folium.Map(location=[lat, lng], zoom_start=15, tiles="cartodbpositron")

    # GeoJSON 하이라이트 (세 동만 강조)
    GEO_URL = (
        "https://raw.githubusercontent.com/"
        "raqoon886/Local_HangJeongDong/master/"
        "hangjeongdong_서울특별시.geojson"
    )
    gj = requests.get(GEO_URL).json()
    def style_fn(feat):
        nm = feat["properties"].get("adm_nm", "")
        sel = any(d in nm for d in target_dongs)
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

    # 마커 & 팝업
    for _, r in df.iterrows():
        title = r["name"]  # ex) "답십리2동 주민센터"
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
    dfp = centers[["name","programs"]].dropna().copy()
    dfp["programs"] = dfp["programs"].str.split(";")
    dfp = dfp.explode("programs").reset_index(drop=True)
    dfp["programs"] = dfp["programs"].str.strip()

    for prog, grp in dfp.groupby("programs"):
        names = grp["name"].tolist()
        with st.expander(f"{prog} ({len(names)}개 기관)"):
            for nm in names:
                st.write(f"- {nm}")

# ─── 4️⃣ 프로그램 신청 페이지 ─────────────────────────────────
else:  # 프로그램 신청
    st.title("📝 프로그램 신청")
    dfp = centers[["programs"]].dropna().copy()
    dfp["programs"] = dfp["programs"].str.split(";")
    dfp = dfp.explode("programs").reset_index(drop=True)
    dfp["programs"] = dfp["programs"].str.strip()
    programs = sorted(dfp["programs"].unique())

    sel_prog  = st.selectbox("프로그램 선택", programs)
    user_name = st.text_input("이름")
    contact   = st.text_input("연락처", placeholder="010-1234-5678")

    if st.button("신청하기"):
        if sel_prog and user_name and contact:
            st.success(f"✅ '{sel_prog}' 신청이 완료되었습니다!")
        else:
            st.error("❗ 모든 항목을 입력해주세요.")
