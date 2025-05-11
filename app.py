import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 데이터 불러오기 (centers.csv는 UTF-8-sig 인코딩)
df = pd.read_csv("centers.csv", encoding="utf-8-sig")

# 페이지 기본 설정
st.set_page_config(page_title="동대문구 건강지원센터", layout="wide")

# 제목
st.title("동대문구 건강지원센터 프로그램 지도")

# 사이드바 필터 UI
st.sidebar.header("필터")
# 동 선택 멀티셀렉트 (기본값으로 휘경2동, 이문2동, 답십리2동 모두 선택)
all_centers = df["name"].unique().tolist()
selected_centers = st.sidebar.multiselect("동 선택", all_centers, default=all_centers)
# 카테고리 선택 멀티셀렉트 (기본값으로 모든 카테고리 선택)
all_categories = df["category"].unique().tolist()
selected_categories = st.sidebar.multiselect("카테고리 선택", all_categories, default=all_categories)

# 탭 구성: 지도 보기 / 프로그램 검색
tab_map, tab_search = st.tabs(["지도 보기", "프로그램 검색"])

# **지도 보기 탭**
with tab_map:
    # 선택된 동/카테고리에 맞게 데이터 필터링
    map_df = df[df["name"].isin(selected_centers) & df["category"].isin(selected_categories)]
    if map_df.empty:
        st.warning("선택된 필터에 해당하는 프로그램이 없습니다.")
    else:
        # 동대문구 전체가 보이도록 지도 중앙과 확대 수준 설정
        center_lat = map_df["latitude"].mean()
        center_lon = map_df["longitude"].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
        # 필터된 각 동 주민센터마다 하나의 마커 표시
        for center_name, group in map_df.groupby("name"):
            lat = group["latitude"].iloc[0]
            lon = group["longitude"].iloc[0]
            # 해당 주민센터의 프로그램 목록을 팝업에 표시 (프로그램명 및 카테고리)
            program_list = [f"{row.program} ({row.category})" for row in group.itertuples()]
            popup_html = "<br>".join(program_list)
            folium.Marker([lat, lon], tooltip=center_name, popup=popup_html).add_to(m)
        # 스트림릿에 Folium 지도 렌더링
        st_folium(m, width=700, height=500)

# **프로그램 검색 탭**
with tab_search:
    # 검색어 입력
    search_term = st.text_input("프로그램명 검색")
    # 선택된 동/카테고리에 따라 프로그램 목록 필터링
    list_df = df[df["name"].isin(selected_centers) & df["category"].isin(selected_categories)]
    if search_term:
        # 프로그램명에 검색어가 포함된 항목만 필터
        list_df = list_df[list_df["program"].str.contains(search_term)]
    if list_df.empty:
        st.info("검색 결과가 없습니다.")
    else:
        # 필터된 프로그램 수 표시
        st.caption(f"총 {len(list_df)}개의 프로그램이 검색되었습니다.")
        # 프로그램 리스트 출력 (동, 카테고리, 프로그램명 및 신청 버튼)
        for idx, row in list_df.iterrows():
            cols = st.columns([2, 2, 4, 1])
            cols[0].write(row["name"])         # 동 주민센터 이름
            cols[1].write(row["category"])     # 프로그램 카테고리
            cols[2].write(row["program"])      # 프로그램 명
            # 신청 버튼 (각 행별로 고유 키를 부여)
            if cols[3].button("신청", key=f"apply_{idx}"):
                cols[3].success("신청 완료")   # 버튼 누르면 해당 위치에 완료 표시
