import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json

st.set_page_config("동대문구 돌봄센터 위치 지도", layout="wide")

# 1) 데이터
df = pd.read_csv("centers.csv", encoding="utf-8-sig")

# 2) 필터 UI
st.sidebar.header("🔍 필터")
search = st.sidebar.text_input("센터명 검색")
cats = sorted({c for subs in df["categories"].str.split(";") for c in subs})
sel = st.sidebar.multiselect("대상군", cats)

mask = pd.Series(True, index=df.index)
if search:
    mask &= df["name"].str.contains(search, na=False)
if sel:
    mask &= df["categories"].apply(lambda s: any(c in s.split(";") for c in sel))
filtered = df[mask]
st.markdown(f"### 표시된 센터: {len(filtered)}개")

# 3) JSON 직렬화
data = filtered.to_dict(orient="records")
json_data = json.dumps(data, ensure_ascii=False)

# 4) HTML + Kakao SDK + 마커 스크립트
html = f'''<div id="map" style="width:100%;height:650px;"></div>
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=49a701f08a231a6895dca5db6de5869a&libraries=services"></script>
<script>
  const map = new kakao.maps.Map(
    document.getElementById('map'),
    {{ center: new kakao.maps.LatLng(37.574360,127.039530), level:4 }}
  );
  const list = {json_data};
  list.forEach(item => {{
    const marker = new kakao.maps.Marker({{
      map, 
      position: new kakao.maps.LatLng(item.lat,item.lng),
      title: item.name
    }});
    const content = 
      '<div style="padding:5px;max-width:250px;">' +
        '<strong>'+item.name+'</strong><br/>' +
        '<em>Feature:</em> '+item.feature+'<br/>' +
        '<em>이벤트:</em> '+item.events.join(', ')+'<br/>' +
        '<em>프로그램:</em> '+item.programs.join(', ')+'<br/>' +
        '<em>대상:</em> '+item.categories +
      '</div>';
    const iw = new kakao.maps.InfoWindow({{ content }});
    kakao.maps.event.addListener(marker,'click',()=>iw.open(map, marker));
  }});
</script>'''

# 5) 실제 스크립트 실행
components.html(html, height=700, scrolling=False)
