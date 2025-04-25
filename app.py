import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json

# 1) 데이터 로드
df = pd.read_csv("centers.csv", encoding="utf-8-sig")

# 2) 사이드바: 검색 + 카테고리 필터
st.sidebar.header("🔍 필터")
search = st.sidebar.text_input("센터명 검색")
all_cats = sorted({cat for subs in df["categories"].str.split(";") for cat in subs})
selected_cats = st.sidebar.multiselect("대상군 선택", all_cats)

# 3) 필터링
mask = pd.Series(True, index=df.index)
if search:
    mask &= df["name"].str.contains(search)
if selected_cats:
    mask &= df["categories"].apply(
        lambda s: any(cat in s.split(";") for cat in selected_cats)
    )
filtered = df[mask]

st.markdown(f"### 표시된 센터 수: {len(filtered)}개")

# 4) 지도용 JSON
centers_list = filtered.to_dict(orient="records")
json_data = json.dumps(centers_list, ensure_ascii=False)

# 5) HTML + Kakao SDK + marker 코드
html = f"""
<div id="map" style="width:100%;height:650px;"></div>
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=49a701f08a231a6895dca5db6de5869a&libraries=services"></script>
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
    const info = `
      <div style="padding:5px;max-width:250px;">
        <strong>${{item.name}}</strong><br/>
        <em>Feature:</em> ${{item.feature}}<br/>
        <em>이벤트:</em> ${{item.events.join(", ")}}<br/>
        <em>프로그램:</em> ${{item.programs.join(", ")}}<br/>
        <em>대상:</em> ${{item.categories}}
      </div>`;
    const infowindow = new kakao.maps.InfoWindow({{ content: info }});
    kakao.maps.event.addListener(marker, 'click', () => {{
      infowindow.open(map, marker);
    }});
  }});
</script>
"""

# 6) sandbox 옵션으로 스크립트·동일출처 허용
components.html(
    html,
    height=700,
    scrolling=False,
    sandbox="allow-scripts allow-same-origin"
)
