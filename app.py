import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

# 1) 데이터 로드
df = pd.read_csv("centers.csv", encoding="utf-8-sig")

# 2) 사이드바: 검색 + 카테고리 필터
st.sidebar.header("🔍 필터")
search = st.sidebar.text_input("센터명 검색", "")

# categories 칼럼에 ';' 구분자로 여러 대상이 있을 수 있음
all_cats = sorted({c for subs in df["categories"].str.split(";") for c in subs})
selected = st.sidebar.multiselect("대상군 선택", options=all_cats)

# 3) 필터링
mask = pd.Series(True, index=df.index)
if search:
    mask &= df["name"].str.contains(search, case=False, na=False)
if selected:
    mask &= df["categories"].apply(lambda s: any(c in s.split(";") for c in selected))
filtered = df[mask]

st.sidebar.markdown(f"표시된 센터 수: **{len(filtered)}개**")

# 4) 지도 생성
if len(filtered)==0:
    st.warning("조건에 맞는 센터가 없습니다.")
    st.stop()

# 중심 좌표: 평균
center_lat = filtered["lat"].mean()
center_lng = filtered["lng"].mean()

m = folium.Map(location=[center_lat, center_lng], zoom_start=14)

# 카테고리별 색상 매핑 (예시)
color_map = {
    "어린이": "blue",
    "노약자": "green",
    "임산부": "pink",
    "기타": "gray",
}

# 5) 마커 추가
for _, row in filtered.iterrows():
    cats = row["categories"].split(";")
    # 첫 번째 카테고리 색상 사용
    icon_color = color_map.get(cats[0], "cadetblue")
    popup_html = f"""
      <b>{row['name']}</b><br>
      <em>Feature:</em> {row['feature']}<br>
      <em>Events:</em> {row.get('events','-')}<br>
      <em>Programs:</em> {row.get('programs','-')}<br>
      <em>Categories:</em> {row['categories']}
    """
    folium.Marker(
        [row["lat"], row["lng"]],
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color=icon_color, icon="info-sign"),
    ).add_to(m)

# 6) Streamlit에 렌더링
st.markdown("## 동대문구 돌봄센터 지도")
st_folium(m, width=800, height=600)
