import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json

# 1) 데이터 로드
df = pd.read_csv("centers.csv")

# 2) 사이드바: 검색 + 카테고리 필터
st.sidebar.header("🔍 필터")
search = st.sidebar.text_input("센터명 검색")

# 고유 카테고리 목록 추출
all_cats = sorted({cat for subs in df["categories"].str.split(";") for cat in subs})
selected_cats = st.sidebar.multiselect("대상군 선택", all_cats)

# 3) DataFrame 필터링
mask = pd.Series(True, index=df.index)
if search:
    mask &= df["name"].str.contains(search)
if selected_cats:
    mask &= df["categories"].apply(
        lambda s: any(cat in s.split(";") for cat in selected_cats)
    )
filtered = df[mask]

# 4) 헤드라인
st.markdown(f"### 표시된 센터 수: {len(filtered)}개")

# 5) Kakao Map HTML 생성
#    JSON으로 변환 (ensure_ascii=False 로 한글 유지)
centers_list = filtered.to_dict(orient="records")
json_data = json.dumps(centers_list, ensure_ascii=False)

html = f"""
<div id="map" style="width:100%;height:600px;"></div>
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=49a701f08a231a6895dca5db6de5869a"></script>
<script>
  const map = new kakao.maps.Map(
    document.getElementById('map'),
    {{ center: new kakao.maps.LatLng(37.574360, 127.039530), level: 4 }}
  );
  const data = {json_data};
  data.forEach(item => {{
    const marker = new kakao.maps.Marker({{
      map: map,
      position: new kakao.maps.LatLng(item.lat, item.lng),
      title: item.name
    }});
    const infoContent = `
      <div style="padding:5px;max-width:250px;">
        <strong>${{item.name}}</strong><br/>
        <em>Feature:</em> ${{item.feature}}<br/>
        <em>Programs:</em> ${{item.events}};<br/>
        <em>Activities:</em> ${{item.programs}}<br/>
        <em>Categories:</em> ${{item.categories}}
      </div>
    `;
    const infowindow = new kakao.maps.InfoWindow({{ content: infoContent }});
    kakao.maps.event.addListener(marker, 'click', () => {{ infowindow.open(map, marker); }});
  }});
</script>
"""

# 6) 지도 렌더링
components.html(html, height=650, scrolling=False)
