import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import math

# ─── 유틸: 두 위경도 사이 거리 계산 (m) ─────────────────
def haversine(lat1, lng1, lat2, lng2):
    R = 6371000  # 지구 반경(m)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ─── 1) 데이터 로드 & dong 추출 ────────────────────────
df = pd.read_csv("centers.csv", encoding="utf-8-sig")
df["dong"] = df["name"].str.extract(r"^(.+?동)")

# ─── 2) 사이드바 필터 ────────────────────────────────
st.sidebar.header("🔍 필터")
search = st.sidebar.text_input("센터명 검색")
cats = sorted({c for subs in df["categories"].dropna() for c in subs.split(";")})
sel_cats = st.sidebar.multiselect("대상군 선택", cats)

mask = pd.Series(True, index=df.index)
if search:
    mask &= df["name"].str.contains(search, case=False, na=False)
if sel_cats:
    mask &= df["categories"].apply(lambda s: any(c in s.split(";") for c in sel_cats))
base = df[mask]
st.sidebar.markdown(f"**총 센터:** {len(base)}개")

# ─── 3) 상단 “동 선택” 버튼 바 ─────────────────────────
st.markdown("### 🔘 동 선택")
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

# ─── 4) 최종 필터링 ────────────────────────────────
if sel:
    df2 = base[base["dong"] == sel]
    st.markdown(f"### 선택된 동: **{sel}** ({len(df2)}개)")
else:
    df2 = base
    st.markdown(f"### 전체 센터 표시 ({len(df2)}개)")

if df2.empty:
    st.warning("조건에 맞는 센터가 없습니다.")
    st.stop()

# ─── 5) Folium 지도 & 마커 클러스터 ───────────────────
# 중심 계산
center_lat = float(df2["lat"].mean())
center_lng = float(df2["lng"].mean())
zoom = 16 if sel else 14

m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom)
cluster = MarkerCluster().add_to(m)

# 5-1) 동 하이라이트: 돌봄센터들의 최대 거리 기준 원 그리기
if sel:
    # 각 센터와 중심까지 거리 계산
    distances = df2.apply(lambda r: haversine(center_lat, center_lng, r.lat, r.lng), axis=1)
    radius = distances.max() * 1.2  # 최대 반경의 1.2배 여유폭
    folium.Circle(
        location=[center_lat, center_lng],
        radius=radius,
        color="#4287f5",
        fill=True,
        fill_color="#4287f5",
        fill_opacity=0.1,
        weight=2
    ).add_to(m)

# 5-2) 마커 & 깔끔한 팝업
for _, r in df2.iterrows():
    popup = folium.Popup(f"""
      <div style="font-family:Arial; font-size:13px;">
        <strong>{r['name']}</strong><br/>
        <table style="border:none; font-size:12px;">
          <tr><th align="left">구분:</th><td>{r['feature']}</td></tr>
          <tr><th align="left">이벤트:</th><td>{r.get('events','-')}</td></tr>
          <tr><th align="left">프로그램:</th><td>{r.get('programs','-')}</td></tr>
          <tr><th align="left">대상군:</th><td>{r['categories']}</td></tr>
        </table>
      </div>
    """, max_width=300)
    folium.Marker(
        location=(r["lat"], r["lng"]),
        popup=popup,
        icon=folium.Icon(color="darkblue", icon="info-sign"),
    ).add_to(cluster)

# ─── 6) Streamlit 렌더링 ────────────────────────────
st.title("동대문구 돌봄센터 지도")
st_folium(m, width="100%", height=650)
