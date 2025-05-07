import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from shapely.geometry import Polygon
import geopandas as gpd

# 페이지 설정
st.set_page_config(page_title="동대문구 건강지원센터", page_icon="🏥", layout="wide")

# 데이터 로드
centers_df = pd.read_csv("centers.csv")

# 행정동 목록
dongs = sorted(centers_df['dong'].unique())

# 좌표 중심 설정
center_lat, center_lon = 37.574360, 127.039530

# 스타일 정의
main_color = "#4CAF50"
sidebar_color = "#F0F0F0"

# ---- UI 구성 ----
st.sidebar.header("📌 메뉴")
page = st.sidebar.radio("페이지 선택", ["소개", "건강지원센터 지도", "프로그램 신청"])

# 1️⃣ 소개 페이지
if page == "소개":
    st.title("💡 동대문구 건강지원센터")
    st.markdown(
        """
        동대문구 건강지원센터는 지역 주민들의 건강 증진과 복지 향상을 위한 종합 지원 센터입니다.
        주요 서비스는 다음과 같습니다:
        - **건강 상담 및 예방 서비스**
        - **노인, 임산부, 어린이 대상 프로그램**
        - **지역사회 건강 연계 프로그램**
        """
    )
    st.image("https://source.unsplash.com/1600x400/?health,clinic")

# 2️⃣ 건강지원센터 지도 페이지
elif page == "건강지원센터 지도":
    st.title("📍 동대문구 건강지원센터 지도")
    
    # --- 사이드바 필터 ---
    st.sidebar.subheader("🔎 필터링")
    selected_dong = st.sidebar.selectbox("행정동 선택", ["전체"] + dongs)
    search_keyword = st.sidebar.text_input("센터명 검색", placeholder="센터명 입력")
    
    # --- 필터링 로직 ---
    filtered = centers_df.copy()
    if selected_dong != "전체":
        filtered = filtered[filtered['dong'] == selected_dong]
    if search_keyword:
        filtered = filtered[filtered['name'].str.contains(search_keyword, case=False, na=False)]
    
    # --- 지도 생성 ---
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="cartodbpositron")
    
    # --- 행정동 경계 표시 ---
    if selected_dong != "전체":
        geojson_url = f"https://github.com/your_github_repo/{selected_dong}.geojson"
        folium.GeoJson(
            geojson_url,
            name=selected_dong,
            style_function=lambda x: {
                'fillColor': '#3186cc',
                'color': '#3186cc',
                'weight': 2,
                'fillOpacity': 0.3
            }
        ).add_to(m)
    
    # --- 마커 표시 ---
    for _, row in filtered.iterrows():
        folium.Marker(
            location=[row['lat'], row['lng']],
            popup=f"{row['name']}<br>{row['feature']}<br>{row['events']}<br>{row['programs']}",
            tooltip=row['name']
        ).add_to(m)

    # --- 지도 출력 ---
    st_folium(m, height=500, width=700)

# 3️⃣ 프로그램 신청 페이지
elif page == "프로그램 신청":
    st.title("📝 프로그램 신청")
    st.markdown("추후 프로그램 신청 기능이 업데이트될 예정입니다.")
