# app.py
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json

# ─── 페이지 설정 ───
st.set_page_config(
    page_title="동대문구 돌봄센터 위치 지도",
    layout="wide"
)

# ─── 1) 데이터 로드 ───
df = pd.read_csv("centers.csv", encoding="utf-8-sig")

# ─── 2) 사이드바 필터 ───
st.sidebar.header("🔍 필터")
search = st.sidebar.text_input("센터명 검색")

# 고유 대상군 추출
all_cats = sorted({
    cat
    for subcats in df["categories"].str.split(";")
    for cat in subcats
})
selected_cats = st.sidebar.multiselect("대상군 선택", all_cats)

# ─── 3) DataFrame 필터링 ───
mask = pd.Series(True, index=df.index)
if search:
    mask &= df["name"].str.contains(search, na=False)
if selected_cats:
    mask &= df["categories"].apply(
        lambda s: any(cat in s.split(";") for cat in selected_cats)
    )
filtered = df[mask]

st.markdown(f"### 표시된 센터 수: {len(filtered)}개")

# ─── 4) 지도 렌더링용 HTML/JS 생성 ───
centers_list = filtered.to_dict(orient="records")
# 한글 깨짐 방지
json_data = json.dumps(centers_list, ensure_ascii=False)

html = """
<div id="map" style="width:100%;height:650px;"></div>
<script src="https://dapi.kakao.com/v2/maps/sdk.js?
  appkey=49a701f08a231a6895dca5db6de5869a&libraries=services">
</script>
<script>
  // 1) 지도 생성
  const map = new kakao.maps.Map(
    document.getElementById('map'),
    { center: new kakao.maps.LatLng(37.574360, 127.039530), level: 4 }
  );

  // 2) Python에서 넘긴 데이터 파싱
  const data = %s;

  // 3) 마커 + InfoWindow
  data.forEach(item => {
    const marker = new kakao.maps.Marker({
      map: map,
      position: new kakao.maps.LatLng(item.lat, item.lng),
      title: item.name
    });

    const content = 
      '<div style="padding:5px;max-width:250px;">' +
        '<strong>' + item.name + '</strong><br/>' +
        '<em>Feature:</em> ' + item.feature + '<br/>' +
        '<em>Events:</em> ' + item.events.join(', ') + '<br/>' +
        '<em>Programs:</em> ' + item.programs.join(', ') + '<br/>' +
        '<em>Categories:</em> ' + item.categories +
      '</div>';

    const infowindow = new kakao.maps.InfoWindow({ content });
    kakao.maps.event.addListener(marker, 'click', () => {
      infowindow.open(map, marker);
    });
  });
</script>
""" % json_data

# ─── 5) Components로 HTML/JS 실행 ───
components.html(html, height=700, scrolling=False)
