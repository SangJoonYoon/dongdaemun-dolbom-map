import streamlit as st
import pandas as pd
import geopandas as gpd
import requests
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from io import StringIO

st.set_page_config(page_title="동대문구 돌봄센터 지도", layout="wide")

# 1) 돌봄센터 데이터
df = pd.read_csv("centers.csv", encoding="utf-8-sig")
df["dong"] = df["name"].str.extract(r"^(.+?동)")

# 2) 행정경계 GeoJSON 로드 (GitHub RAW)
GEO_URL = (
    "https://raw.githubusercontent.com/southkorea/southkorea-maps"
    "/master/kostat/2013/json/skorea_submunicipalities_geo_simple.json"
)
gdf = gpd.read_file(StringIO(requests.get(GEO_URL).text))
gdf_ddm = gdf[gdf["SIG_KOR_NM"] == "동대문구"].copy()
gdf_ddm["dong"] = gdf_ddm["EMD_KOR_NM"]

# 3) 사이드바 필터
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
    base = df[mask]
    st.markdown(f"**총 센터:** {len(base)}개")

# 4) 동 선택
st.markdown("## 🔘 동 선택")
dongs = sorted(base["dong"].dropna().unique())
cols = st.columns(min(6, len(dongs)))
sel = st.session_state.get("selected_dong", None)
for i, dong in enumerate(dongs):
    if cols[i % len(cols)].button(dong, key=dong):
        sel = dong
        st.session_state["selected_dong"] = dong
if st.button("전체 보기"):
    sel = None
    st.session_state["selected_dong"] = None

# 5) 카카오 키워드 검색으로 정확한 동 이름(Region_3depth) 가져오기
region_name = sel
if sel:
    kakao_url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers   = {"Authorization": "KakaoAK a744cda0e04fc0979044ffbf0904c193"}
    params    = {"query": f"{sel} 동대문구", "size":1}
    docs      = requests.get(kakao_url, headers=headers, params=params).json().get("documents")
    if docs:
        region_name = docs[0]["address"]["region_3depth_name"]

# 6) 최종 필터링
if sel:
    filtered = base[base["dong"] == sel]
    st.markdown(f"### 선택된 동: **{sel}** ({len(filtered)}개)")
else:
    filtered = base
    st.markdown(f"### 전체 센터 표시 ({len(filtered)}개)")

if filtered.empty:
    st.warning("조건에 맞는 센터가 없습니다.")
    st.stop()

# 7) Folium 지도
center_lat = float(filtered["lat"].mean())
center_lng = float(filtered["lng"].mean())
zoom       = 16 if sel else 14
m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom)
cluster = MarkerCluster().add_to(m)

# 7-1) GeoJSON 하이라이트 (region_name 으로 매칭)
if region_name:
    sel_geo = gdf_ddm[gdf_ddm["dong"] == region_name]
    if not sel_geo.empty:
        folium.GeoJson(
            sel_geo,
            style_function=lambda feat: {
                "fillColor": "#4287f5",
                "color": "#1f3b82",
                "weight": 2,
                "fillOpacity": 0.2
            }
        ).add_to(m)

# 7-2) 돌봄센터 마커
for _, r in filtered.iterrows():
    popup = folium.Popup(f"""
      <div style="font-family:Arial; font-size:13px;">
        <strong>{r['name']}</strong><br/>
        <em>Feature:</em> {r['feature']}<br/>
        <em>Events:</em> {r.get('events','-')}<br/>
        <em>Programs:</em> {r.get('programs','-')}<br/>
        <em>Categories:</em> {r['categories']}
      </div>
    """, max_width=300)
    folium.Marker(
        location=(r["lat"], r["lng"]),
        popup=popup,
        icon=folium.Icon(color="darkblue", icon="info-sign")
    ).add_to(cluster)

# 8) 렌더링
st.title("동대문구 돌봄센터 지도")
st_folium(m, width="100%", height=650)
