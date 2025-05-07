import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# ─── 페이지 설정 ───
st.set_page_config(page_title="동대문구 돌봄센터 지도", layout="wide")

# ─── 1) 데이터 로드 & dong 컬럼 생성 ───
df = pd.read_csv("centers.csv", encoding="utf-8-sig")

# name 컬럼에서 “○○동” 부분만 뽑아서 dong 컬럼으로
#   예: "회기동 주민센터" → "회기동"
df["dong"] = df["name"].str.extract(r"^(.+?동)")

# ─── 2) 사이드바: 기본 검색·카테고리 필터 ───
st.sidebar.header("🔍 기본 필터")
search = st.sidebar.text_input("센터명 검색")
all_cats = sorted({c for subs in df["categories"].dropna() for c in subs.split(";")})
selected_cats = st.sidebar.multiselect("대상군 선택", all_cats)

mask = pd.Series(True, index=df.index)
if search:
    mask &= df["name"].str.contains(search, case=False, na=False)
if selected_cats:
    mask &= df["categories"].apply(lambda s: any(c in s.split(";") for c in selected_cats))
filtered_base = df[mask]

# ─── 3) 상단 동 선택 버튼 바 ───
st.markdown("### 🔘 동 선택")
dongs = sorted(filtered_base["dong"].dropna().unique())
# 버튼을 한 줄에 모두 담기 위해 st.columns 사용
cols = st.columns(len(dongs))
# session_state 에 저장된 값 읽기
sel = st.session_state.get("selected_dong", None)

for col, dong in zip(cols, dongs):
    if col.button(dong, key=dong):
        sel = dong
        st.session_state["selected_dong"] = dong

if st.button("전체 보기"):
    sel = None
    st.session_state["selected_dong"] = None

# ─── 4) 동 기준 최종 필터 ───
if sel:
    filtered = filtered_base[filtered_base["dong"] == sel]
    st.markdown(f"**선택된 동:** {sel} (총 {len(filtered)}개)")
else:
    filtered = filtered_base
    st.markdown(f"**전체 센터 표시:** {len(filtered)}개")

if filtered.empty:
    st.warning("조건에 맞는 센터가 없습니다.")
    st.stop()

# ─── 5) Folium 지도 & MarkerCluster ───
center_lat = float(filtered["lat"].mean())
center_lng = float(filtered["lng"].mean())
m = folium.Map(location=[center_lat, center_lng], zoom_start=14)
cluster = MarkerCluster().add_to(m)

for _, row in filtered.iterrows():
    popup_html = f"""
    <div style="font-family:Arial; font-size:13px;">
      <strong>{row['name']}</strong><br/>
      <table style="border:none; font-size:12px;">
        <tr><th align="left">구분:</th><td>{row['feature']}</td></tr>
        <tr><th align="left">이벤트:</th><td>{row.get('events','-')}</td></tr>
        <tr><th align="left">프로그램:</th><td>{row.get('programs','-')}</td></tr>
        <tr><th align="left">대상군:</th><td>{row['categories']}</td></tr>
      </table>
    </div>
    """
    folium.Marker(
        location=(row["lat"], row["lng"]),
        popup=folium.Popup(popup_html, max_width=280),
        icon=folium.Icon(color="darkblue", icon="info-sign")
    ).add_to(cluster)

# ─── 6) Streamlit 렌더링 ───
st.title("동대문구 돌봄센터 지도")
st_folium(m, width="100%", height=650)
