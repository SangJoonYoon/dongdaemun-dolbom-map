import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# ─── 설정 ─────────────────────────────────────────
st.set_page_config(page_title="동대문구 건강지원센터", page_icon="🏥", layout="wide")

# ─── 데이터 로드 ───────────────────────────────────
centers = pd.read_csv("centers.csv", encoding="utf-8-sig")

# ─── 메뉴 ─────────────────────────────────────────
st.sidebar.header("📌 메뉴")
page = st.sidebar.radio("", ["소개","건강지원센터지도","프로그램 목록","프로그램 신청"])

# ─── 1️⃣ 소개 ────────────────────────────────────────
if page=="소개":
    st.title("🏥 동대문구 건강지원센터 소개")
    st.markdown("""
    **1. 동대문구 각 동별 건강지원센터 설립**  
    **2. 병원 연계 사후관리**  
    **3. 1:1 맞춤 건강증진 프로그램 & 병원 추천**  
    **4. 건강동아리 구성**  
    """)
    st.image("https://source.unsplash.com/1600x400/?health,clinic")

# ─── 2️⃣ 지도 ────────────────────────────────────────
elif page=="건강지원센터지도":
    st.title("📍 건강지원센터 위치 지도")
    # 필터
    c1,c2,c3=st.columns([2,3,3])
    sel_dong = c1.selectbox("행정동", ["전체"]+sorted(centers.dong.unique()))
    kw       = c2.text_input("센터명 검색")
    cats     = sorted({x for subs in centers.categories.dropna() for x in subs.split(";")})
    sel_cats = c3.multiselect("대상군", cats)
    # 필터링
    mask = pd.Series(True, index=centers.index)
    if sel_dong!="전체": mask &= centers.dong==sel_dong
    if kw:               mask &= centers.name.str.contains(kw, case=False)
    if sel_cats:         mask &= centers.categories.apply(lambda s: any(c in s.split(";") for c in sel_cats))
    df=centers[mask]
    st.caption(f"표시된 센터: {len(df)}개")
    # 지도
    if not df.empty:
        lat,lon=df.lat.mean(), df.lng.mean(); zoom=14 if sel_dong=="전체" else 16
    else:
        lat,lon,zoom=37.57436,127.03953,13
    m=folium.Map([lat,lon], zoom_start=zoom, tiles="cartodbpositron")
    # GeoJSON 하이라이트
    GEO="https://raw.githubusercontent.com/raqoon886/Local_HangJeongDong/master/hangjeongdong_서울특별시.geojson"
    gj=requests.get(GEO).json()
    def style_fn(feat):
        nm=feat["properties"].get("adm_nm","")
        sel=sel_dong!="전체" and sel_dong in nm
        return {"fillColor":"#0055FF" if sel else "#ffffff",
                "color":"#0055FF" if sel else "#999999",
                "weight":2 if sel else 1,
                "fillOpacity":0.3 if sel else 0.0}
    folium.GeoJson(gj, style_function=style_fn,
                   tooltip=folium.GeoJsonTooltip(fields=["adm_nm"],aliases=["행정동"])
    ).add_to(m)
    # 마커 (중복 제거)
    for _,r in df.drop_duplicates(subset=["name"]).iterrows():
        title=r.name.replace("돌봄센터","건강지원센터")
        popup_html=f"""
          <div style="max-width:250px;font-family:Arial;">
            <h4 style="margin:0 0 6px;">{title}</h4>
            <p style="margin:0;font-weight:600;">프로그램:</p>
            <ul style="margin:4px 0 0 16px 16px;padding:0;list-style:disc;">
              <li>{r.programs}</li>
            </ul>
          </div>
        """
        folium.Marker([r.lat,r.lng],
                      tooltip=title,
                      popup=folium.Popup(popup_html,max_width=300),
                      icon=folium.Icon(color="green",icon="plus-sign")
        ).add_to(m)
    st_folium(m, width="100%", height=650)

# ─── 3️⃣ 프로그램 목록 ───────────────────────────────────
elif page=="프로그램 목록":
    st.title("📋 현재 운영중인 프로그램")
    dfp=centers[["name","programs"]].fillna("").copy()
    dfp.programs=dfp.programs.str.split(";"); dfp=dfp.explode("programs")
    dfp.programs=dfp.programs.str.strip(); dfp=dfp[dfp.programs!=""]
    for prog,grp in dfp.groupby("programs"):
        names=grp["name"].tolist()
        with st.expander(f"{prog} ({len(names)}개 센터)"):
            for nm in names:
                st.write(f"- {nm}")

# ─── 4️⃣ 프로그램 신청 ───────────────────────────────────
else:
    st.title("📝 프로그램 신청")
    dfp=centers[["programs"]].fillna("").copy()
    dfp.programs=dfp.programs.str.split(";"); dfp=dfp.explode("programs")
    dfp.programs=dfp.programs.str.strip(); programs=sorted(dfp[dfp.programs!=""].programs.unique())
    sel=st.selectbox("프로그램 선택", programs)
    user=st.text_input("이름"); contact=st.text_input("연락처")
    if st.button("신청하기"):
        if sel and user and contact:
            st.success(f"✅ '{sel}' 신청이 완료되었습니다!")
        else:
            st.error("❗ 정보를 모두 입력해주세요.")
