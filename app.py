import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import requests
from io import StringIO

# ─── 0) 페이지 설정 ─────────────────────────
st.set_page_config(
    page_title="동대문구 돌봄센터 지도",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── 1) 돌봄센터 데이터 로드 ─────────────────
df = pd.read_csv("centers.csv", encoding="utf-8-sig")
df["dong"] = df["name"].str.extract(r"^(.+?동)")

# ─── 2) GeoJSON 실시간 로드 ─────────────────
# South Korea level3(읍·면·동) 경계를 담은 GeoJSON
GEO_URL = (
    "https://raw.githubusercontent.com/southkorea/southkorea-maps"
    "/master/kostat/2013/json/skorea_submunicipalities_geo_simple.json"
)
resp = requests.get(GEO_URL)
gdf = gpd.read_file(StringIO(resp.text), encoding="utf-8")

# “동대문구” 필터, 동 이름 컬럼 추출
gdf_ddm = gdf[gdf["SIG_KOR_NM"] == "동대문구"].copy()
gdf_ddm["dong"] = gdf_ddm["EMD_KOR_NM"]

# ─── 3) 사이드바 필터 ───────────────────────
with st.sidebar:
    st.header("🔍 필터")
    search = st.text_input("센터명 검색")
    cats = sorted({c for subs in df["categories"].dropna() for c in subs.split(";")})
    selected_cats = st.multiselect("대상군 선택", cats)

    mask = pd.Series(True, index=df.index)
    if search:
        mask &= df["name"].str.contains(search, case=False, na=False)
    if selected_cats:
        mask &= df["categories"].apply(
            lambda s: any(c in s.split(";") for c in selected_cats)
        )
    filtered_base = df[mask]
    st.markdown(f"**총 센터 수:** {len(filtered_base)}개")

# ─── 4) 상단 동 선택 버튼 바 ─────────────────
st.markdown("## 🔘 동 선택")
dongs = sorted(filtered_base["dong"].dropna().unique())
cols = st.columns(min(6, len(dongs)))  # 한 줄에 최대 6개

sel = st.session_state.get("selected_dong", None)
for i, dong in enumerate(dongs):
    if cols[i % len(cols)].button(dong, key=dong):
        sel = dong
        st.session_state["selected_dong"] = dong

if st.button("전체 보기"):
    sel = None
    st.session_state["selected_dong"] = None

# ─── 5) 최종 필터링 ────────────────────────
if sel:
    filtered = filtered_base[filtered_base["dong"] == sel]
    st.markdown(f"### 선택된 동: **{sel}** (총 {len(filtered)}개)")
else:
    filtered = filtered_base
    st.markdown(f"### 전체 센터 표시 (총 {len(filtered)}개)")

if filtered.empty:
    st.warning("조건에 맞는 센터가 없습니다.")
    st.stop()

# ─── 6) Folium 지도 생성 & 마커 클러스터 ────
# 중심 좌표 & 줌 레벨
if sel:
    zoom = 16
else:
    zoom = 14
center_lat = float(filtered["lat"].mean())
center_lng = float(filtered["lng"].mean())

m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom)
cluster = MarkerCluster().add_to(m)

# 6-1) 동대문구 GeoJSON 중, 선택된 동만 하이라이트
if sel:
    sel_geo = gdf_ddm[gdf_ddm["dong"] == sel]
    folium.GeoJson(
        sel_geo,
        style_function=lambda feat: {
            "fillColor": "#4287f5",
            "color": "#1f3b82",
            "weight": 2,
            "fillOpacity": 0.2
        },
        name="selected_dong"
    ).add_to(m)

# 6-2) 돌봄센터 마커 & 팝업
for _, row in filtered.iterrows():
    popup = folium.Popup(f"""
      <div style="font-family:Arial; font-size:13px;">
        <strong>{row['name']}</strong><br/>
        <table style="border:none; font-size:12px;">
          <tr><th align="left">구분:</th><td>{row['feature']}</td></tr>
          <tr><th align="left">이벤트:</th><td>{row.get('events','-')}</td></tr>
          <tr><th align="left">프로그램:</th><td>{row.get('programs','-')}</td></tr>
          <tr><th align="left">대상군:</th><td>{row['categories']}</td></tr>
        </table>
      </div>
    """, max_width=300)
    folium.Marker(
        location=(row["lat"], row["lng"]),
        popup=popup,
        icon=folium.Icon(color="darkblue", icon="info-sign")
    ).add_to(cluster)

# ─── 7) Streamlit에 렌더링 ─────────────────
st.title("동대문구 돌봄센터 지도")
st_folium(m, width="100%", height=650)
