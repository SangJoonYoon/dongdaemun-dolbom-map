import streamlit as st
import pandas as pd
import folium
import requests
from streamlit_folium import st_folium

# 페이지 설정
st.set_page_config(page_title="동대문구 건강지원센터", layout="wide")

# 스타일
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

# 데이터 로드
try:
    centers = pd.read_csv("centers.csv", encoding="utf-8-sig")
except FileNotFoundError:
    st.error("❗ centers.csv 파일을 찾을 수 없습니다.")
    st.stop()

# 필수 컬럼 검증
required = {"name","feature","dong","programs","categories","lat","lng"}
if not required.issubset(centers.columns):
    st.error(f"❗ centers.csv에 다음 컬럼이 필요합니다: {', '.join(sorted(required))}")
    st.stop()

# 탭 메뉴
tab1, tab2, tab3, tab4 = st.tabs(["소개","건강지원센터지도","프로그램 목록","프로그램 신청"])

# 1) 소개
with tab1:
    st.header("🏥 동대문구 건강지원센터 소개")
    st.write("...앱 소개 텍스트...")

# 2) 지도
with tab2:
    st.header("📍 건강지원센터 위치 지도")
    # 초기엔 전체 동대문구 지도
    m = folium.Map(location=[37.58200,127.06400], zoom_start=13)
    # 마커 추가 (단, 데이터는 centers.csv 세 동만)
    for _, r in centers.iterrows():
        tags = " ".join(f'<span class="badge">{t}</span>' 
                        for t in r["categories"].split(";"))
        popup = folium.Popup(f"<b>{r['name']}</b><br>{tags}", max_width=300)
        folium.Marker([r["lat"],r["lng"]], popup=popup).add_to(m)
    st_folium(m, width="100%", height=600)

# 3) 프로그램 목록
with tab3:
    st.header("📋 프로그램 목록")
    # 그룹핑: 프로그램별 센터
    dfp = centers[["programs","name","categories"]].dropna()
    grouped = dfp.groupby("programs")
    for prog, grp in grouped:
        # 태그: 대상 & 목적
        tgt = grp["categories"].iloc[0]
        # 목적 태그는 프로그램명에 따라 간단 추출
        purpose = []
        if any(w in prog for w in ["예방","검진","금연"]): purpose.append("예방")
        if any(w in prog for w in ["정신","우울","스트레스"]): purpose.append("정신")
        if any(w in prog for w in ["운동","요가","체조","재활"]): purpose.append("운동")
        tags = " ".join(f'<span class="badge">#{t}</span>' for t in [tgt]+purpose)
        centers_list = ", ".join(grp["name"].unique())
        st.markdown(f"**{prog}** {tags}<br>"
                    f"<span style='color:gray;'>제공 센터: {centers_list}</span>",
                    unsafe_allow_html=True)

# 4) 신청
with tab4:
    st.header("📝 프로그램 신청")
    progs = sorted(centers["programs"].unique())
    sel = st.selectbox("프로그램 선택", progs)
    name = st.text_input("이름")
    contact = st.text_input("연락처")
    if st.button("신청하기"):
        if sel and name and contact:
            st.success(f"✅ {name} 님, '{sel}' 신청 완료!")
        else:
            st.error("❗ 모든 항목을 입력해주세요.")
