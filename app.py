import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# ─── 페이지 설정 ───
st.set_page_config(page_title="동대문구 돌봄센터 지도", layout="wide")

# ─── 1) 데이터 로드 ───
df = pd.read_csv("centers.csv", encoding="utf-8-sig")

# ─── 2) 사이드바 필터 ───
st.sidebar.header("🔍 필터")
search = st.sidebar.text_input("센터명 검색")
all_cats = sorted({c for subs in df["categories"].dropna() for c in subs.split(";")})
selected_cats = st.sidebar.multiselect("대상군 선택", all_cats)

mask = pd.Series(True, index=df.index)
if search:
    mask &= df["name"].str.contains(search, case=False, na=False)
if selected_cats:
    mask &= df["categories"].apply(lambda s: any(c in s.split(";") for c in selected_cats))
filtered = df[mask]
st.sidebar.markdown(f"표시된 센터 수: **{len(filtered)}개**")

if filtered.empty:
    st.warning("조건에 맞는 센터가 없습니다.")
    st.stop()

# ─── 3) 지도 생성 ───
center_lat = float(filtered["lat"].mean())
center_lng = float(filtered["lng"].mean())
m = folium.Map(location=[center_lat, center_lng], zoom_start=14)

# ─── 4) 마커 클러스터 적용 ───
cluster = MarkerCluster().add_to(m)

# ─── 5) 마커 & 깔끔한 팝업 추가 ───
for _, row in filtered.iterrows():
    # HTML table 팝업
    popup_html = f"""
      <div style="font-family:Arial, sans-serif; font-size:13px; line-height:1.4;">
        <h4 style="margin:0 0 5px 0;">{row['name']}</h4>
        <table style="border-collapse:collapse;">
          <tr>
            <th style="text-align:left; padding:2px 8px 2px 0;">구분</th>
            <td style="padding:2px 0;">{row['feature']}</td>
          </tr>
          <tr>
            <th style="text-align:left; padding:2px 8px 2px 0;">이벤트</th>
            <td style="padding:2px 0;">{row.get('events','-')}</td>
          </tr>
          <tr>
            <th style="text-align:left; padding:2px 8px 2px 0;">프로그램</th>
            <td style="padding:2px 0;">{row.get('programs','-')}</td>
          </tr>
          <tr>
            <th style="text-align:left; padding:2px 8px 2px 0;">대상군</th>
            <td style="padding:2px 0;">{row['categories']}</td>
          </tr>
        </table>
      </div>
    """
    folium.Marker(
        location=[row["lat"], row["lng"]],
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color="cadetblue", icon="info-sign")
    ).add_to(cluster)

# ─── 6) Streamlit 렌더링 ───
st.title("동대문구 돌봄센터 지도")
st_folium(m, width="100%", height=650)
