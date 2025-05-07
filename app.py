import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 페이지 설정
st.set_page_config(page_title="동대문구 건강지원센터", page_icon="🏥", layout="wide")

# 데이터 로드 (데모 데이터)
centers_data = [
    {"센터명": "동대문구 치매안심센터", "행정동": "용신동", "대상": "어르신", "위도": 37.574, "경도": 127.039, "소개": "치매 예방·상담 및 가족 지원 서비스 제공"},
    {"센터명": "동대문구 정신건강복지센터", "행정동": "회기동", "대상": "전체", "위도": 37.592, "경도": 127.055, "소개": "정신건강 상담, 재활 및 자살예방 서비스"},
    {"센터명": "동대문구 건강가정지원센터", "행정동": "답십리동", "대상": "가족", "위도": 37.569, "경도": 127.067, "소개": "가족 교육, 돌봄 나눔 및 다문화가족 지원 프로그램 운영"}
]
centers_df = pd.DataFrame(centers_data)

programs_data = [
    {"카테고리": "건강생활", "프로그램명": "생활체육 요가 교실", "기간": "2025-05-01 ~ 2025-06-30", "대상": "성인 주민", "장소": "구민체육센터", "문의": "02-000-0000"},
    {"카테고리": "정신건강", "프로그램명": "마음건강 상담 챗봇", "기간": "상시 운영", "대상": "전체", "장소": "온라인 (웹/앱)", "문의": "02-111-1111"},
    {"카테고리": "가족지원", "프로그램명": "부모-자녀 관계 개선 워크숍", "기간": "2025-07-15 ~ 2025-07-15", "대상": "부모 및 자녀", "장소": "동대문구 건강가정지원센터", "문의": "02-222-2222"}
]
programs_df = pd.DataFrame(programs_data)

# 사이드바 메뉴
st.sidebar.title("📌 메뉴")
page = st.sidebar.radio("페이지 이동", ["소개", "센터 지도", "프로그램 신청"])

# 1️⃣ 소개 페이지
if page == "소개":
    st.header("동대문구 건강지원센터 소개")
    st.markdown("동대문구 건강지원센터는 지역주민의 건강증진과 복지향상을 위해 다양한 서비스를 제공하는 종합 지원 기관입니다.")
    st.subheader("운영 방식 및 목표")
    st.markdown("✅ **찾아가는 서비스:** 거동이 불편한 주민을 직접 찾아뵙는 방문 건강관리 제공")
    st.markdown("✅ **통합 상담:** 의료, 심리, 복지 등 분야별 전문가 상담을 한 곳에서 지원")
    st.markdown("💡 **목적:** 주민 모두가 :blue[건강한 삶]을 누리도록 예방부터 관리까지 돕는 것")
    st.markdown("💡 **비전:** 함께 돌보고 함께 나누는 지역사회 구현")
    st.subheader("주요 서비스 분야")
    st.markdown("- 🩺 **건강 검진 및 상담**: 기초 건강검진, 만성질환 관리 상담")
    st.markdown("- 🧠 **정신건강 지원**: 우울증, 치매 등 정신건강 예방 프로그램")
    st.markdown("- 🤸 **건강생활 실천**: 운동 교실, 영양 관리 교육 등 생활습관 개선")
    st.markdown("- 🤝 **가족 및 돌봄 지원**: 육아 나눔터 운영, 치매가족 쉼터 지원")
    st.info("※ 각 분야별 상세 프로그램은 '프로그램 신청' 탭에서 확인 가능합니다.")

# 2️⃣ 센터 지도 페이지
elif page == "센터 지도":
    st.header("📍 동대문구 건강지원센터 지도")
    
    # 필터
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        dong_options = ["전체"] + sorted(centers_df["행정동"].unique())
        sel_dong = st.selectbox("행정동", dong_options, index=0)
    with col2:
        keyword = st.text_input("검색", placeholder="센터 이름 검색")
    with col3:
        target_options = ["전체"] + sorted(centers_df["대상"].unique())
        sel_target = st.selectbox("대상군", target_options, index=0)
    
    # 필터링 로직
    filtered = centers_df.copy()
    if sel_dong != "전체":
        filtered = filtered[filtered["행정동"] == sel_dong]
    if sel_target != "전체":
        filtered = filtered[filtered["대상"] == sel_target]
    if keyword:
        filtered = filtered[filtered["센터명"].str.contains(keyword, case=False)]

    # 지도 생성
    center_lat, center_lon = 37.57, 127.04
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="cartodbpositron")
    for _, row in filtered.iterrows():
        folium.Marker([row["위도"], row["경도"]],
                      popup=f"{row['센터명']}<br>{row['행정동']}<br>{row['소개']}",
                      tooltip=row["센터명"]).add_to(m)
    st_folium(m, height=500, width=None)

# 3️⃣ 프로그램 신청 페이지
elif page == "프로그램 신청":
    st.header("📝 건강지원센터 프로그램 신청")
    categories = programs_df["카테고리"].unique()
    for cat in categories:
        cat_programs = programs_df[programs_df["카테고리"] == cat]
        st.subheader(f"▶ {cat}")
        for _, prog in cat_programs.iterrows():
            with st.container():
                st.markdown(f"**{prog['프로그램명']}**  \n기간: {prog['기간']} | 대상: {prog['대상']} | 장소: {prog['장소']}")
                st.caption(f"문의: {prog['문의']}")
                with st.expander("프로그램 신청하기"):
                    with st.form(key=f"form_{prog['프로그램명']}"):
                        st.text_input("이름", placeholder="이름을 입력하세요")
                        st.text_input("연락처", placeholder="연락처를 입력하세요")
                        st.text_area("하고싶은 말", placeholder="문의사항 또는 요청사항 (선택)")
                        if st.form_submit_button("제출"):
                            st.success(f"✅ {prog['프로그램명']} 신청이 완료되었습니다!")
