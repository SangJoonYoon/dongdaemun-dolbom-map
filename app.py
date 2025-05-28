import streamlit as st
import pandas as pd
import folium
import requests
from streamlit_folium import st_folium

# ─── 페이지 설정 ─────────────────────────────────────────
st.set_page_config(
    page_title="동대문구 건강지원센터",
    page_icon="🏥",
    layout="wide"
)

# ─── CSS (배지 스타일) ────────────────────────────────────
st.markdown("""
<style>
.badge {
  display:inline-block;
  background:#3498db;
  color:white;
  padding:2px 6px;
  margin:0 2px;
  border-radius:4px;
  font-size:0.85em;
}
</style>
""", unsafe_allow_html=True)

# ─── 데이터 로드 & 검증 ───────────────────────────────────
try:
    centers = pd.read_csv("centers.csv", encoding="utf-8-sig")
except FileNotFoundError:
    st.error("❗ centers.csv 파일을 찾을 수 없습니다.")
    st.stop()

required = {"name","feature","dong","programs","categories","lat","lng"}
if not required.issubset(centers.columns):
    st.error(f"❗ centers.csv에 다음 컬럼이 필요합니다: {', '.join(sorted(required))}")
    st.stop()

# ─── 사이드바 메뉴 ───────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["소개","건강지원센터지도","프로그램 목록","프로그램 신청"])

# 1️⃣ 소개
with tab1:
    st.header("🏥 동대문구 건강지원센터 소개")
    st.write("동대문구 내 건강지원센터 위치와 프로그램 정보를 한눈에 확인하고, "
             "원하는 프로그램에 바로 신청할 수 있습니다.")

# 2️⃣ 건강지원센터지도
with tab2:
    st.header("📍 건강지원센터 위치 지도")
    st.write("지도 위 마커를 클릭하면 해당 센터의 **모든 프로그램**과 **태그**를 확인할 수 있습니다.")
    
    # Folium 지도 생성 (동대문구 중심)
    m = folium.Map(location=[37.582, 127.064], zoom_start=13, tiles="cartodbpositron")

    # 마커: 센터별로 그룹핑하여 프로그램 리스트와 태그 생성
    for center_name, group in centers.groupby("name"):
        lat = group["lat"].iloc[0]
        lng = group["lng"].iloc[0]

        # 프로그램별 태그 생성 함수
        def make_tags(prog, cat):
            tags = []
            # 대상자 태그
            tags.append(f"#{cat}")
            # 목적 태그
            if any(w in prog for w in ["예방","검진","금연"]):
                tags.append("#예방")
            if any(w in prog for w in ["정신","우울","스트레스"]):
                tags.append("#정신건강")
            if any(w in prog for w in ["운동","요가","체조","재활"]):
                tags.append("#운동")
            if "영양" in prog:
                tags.append("#영양")
            if "상담" in prog:
                tags.append("#상담")
            if "치매" in prog:
                tags.append("#치매")
            return "".join(f'<span class="badge">{t}</span>' for t in sorted(set(tags)))

        # 팝업 HTML: 프로그램명 + 태그 리스트
        popup_items = []
        for _, row in group.iterrows():
            prog = row["programs"]
            cat  = row["categories"]
            badges = make_tags(prog, cat)
            popup_items.append(f"<li><strong>{prog}</strong> {badges}</li>")
        popup_html = (
            f"<div style='max-width:300px;'>"
            f"<h4 style='margin:0 0 4px;'>{center_name}</h4>"
            f"<ul style='padding-left:16px; margin:4px 0;'>{''.join(popup_items)}</ul>"
            f"</div>"
        )

        folium.Marker(
            [lat, lng],
            tooltip=center_name,
            popup=folium.Popup(popup_html, max_width=350)
        ).add_to(m)

    # 지도 렌더링
    st_folium(m, width="100%", height=600)

# 3️⃣ 프로그램 목록
with tab3:
    st.header("📋 프로그램 목록")
    dfp = centers[["name","programs","categories"]].dropna()
    for prog, grp in dfp.groupby("programs"):
        cat = grp["categories"].iloc[0]
        # 태그 생성 (동일 로직)
        tags = []
        tags.append(f"#{cat}")
        if any(w in prog for w in ["예방","검진","금연"]): tags.append("#예방")
        if any(w in prog for w in ["정신","우울","스트레스"]): tags.append("#정신건강")
        if any(w in prog for w in ["운동","요가","체조","재활"]): tags.append("#운동")
        if "영양" in prog: tags.append("#영양")
        if "상담" in prog: tags.append("#상담")
        if "치매" in prog: tags.append("#치매")
        badges = "".join(f'<span class="badge">{t}</span>' for t in sorted(set(tags)))

        centers_list = ", ".join(grp["name"].unique())
        st.markdown(f"**{prog}** {badges}<br>"
                    f"<span style='color:gray;'>제공 센터: {centers_list}</span>",
                    unsafe_allow_html=True)

# 4️⃣ 프로그램 신청
with tab4:
    st.header("📝 프로그램 신청")
    programs = sorted(centers["programs"].unique())
    sel_prog  = st.selectbox("프로그램 선택", programs)
    user_name = st.text_input("이름")
    contact   = st.text_input("연락처", placeholder="010-1234-5678")
    if st.button("신청하기"):
        if sel_prog and user_name and contact:
            st.success(f"✅ '{sel_prog}' 신청이 완료되었습니다!")
        else:
            st.error("❗ 모든 항목을 입력해주세요.")
