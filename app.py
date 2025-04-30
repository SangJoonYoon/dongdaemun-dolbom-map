import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 페이지 설정
st.set_page_config(page_title="동대문구 돌봄센터 지도", layout="wide")

# 1) 데이터 로드
df = pd.read_csv("centers.csv", encoding="utf-8-sig")

# 2) 사이드바 필터
st.sidebar.header("🔍 필터")
search = st.sidebar.text_input("센터명 검색")

# categories 분리 후 고유 대상군
all_cats = sorted({c for subs in df["categories"].dropna() for c in subs.split(";")})
selected_cats = st.sidebar.multiselect("대상군 선택", all_cats)

# 필터링
mask = pd.Series(True, index=df.index)
if search:
    mask &= df["name"].str.contains(search, case=False, na=False)
if selected_cats:
    mask &= df["categories"].apply(lambda s: any(c in s.split(";") for c in selected_cats))
filtered = df[mask]

st.sidebar.markdown(f"표시된 센터 수: **{len(filtered)}개**")

# 3) 지도 생성
if filtered.empty:
    st.warning("조건에 맞는 센터가 없습니다.")
    st.stop()

# 중심 좌표는 평균값
center_lat = filtered["lat"].mean()
center_lng = filtered["lng"].mean()

m = folium.Map(location=[center_lat, center_lng], zoom_start=14)

# 카테고리별 색상 맵핑 예시
color_map = {
    "어린이": "blue",
    "노약자": "green",
    "임산부": "pink",
    "기타": "gray"
}

# 마커 추가
for _, row in filtered.iterrows():
    cats = row["categories"].split(";")
    color = color_map.get(cats[0], "cadetblue")
    popup = (
        f"<b>{row['name']}</b><br>"
        f"Feature: {row['feature']}<br>"
        f"Events: {row.get('events','-')}<br>"
        f"Programs: {row.get('programs','-')}<br>"
        f"Categories: {row['categories']}"
    )
    folium.Marker(
        location=[row["lat"], row["lng"]],
        popup=popup,
        icon=folium.Icon(color=color, icon="info-sign")
    ).add_to(m)

# 4) Streamlit에 렌더링
st.title("동대문구 돌봄센터 지도")
st_folium(m, width="100%", height=600)
