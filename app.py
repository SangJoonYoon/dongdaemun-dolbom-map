import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(page_title="동대문구 돌봄센터 지도", layout="wide")

# 1) 데이터 로드
df = pd.read_csv("centers.csv", encoding="utf-8-sig")

# 2) 좌측 사이드바 필터 (기존 검색·카테고리)
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

# 3) 상단에 ‘동’ 선택 버튼 바
st.markdown("### 🔘 동 선택")
dongs = sorted(filtered_base["dong"].unique())
# 한 줄에 너무 많으면 wrap 되도록 st.columns 로만듭니다.
cols = st.columns(len(dongs))
selected_dong = st.session_state.get("selected_dong", None)

for col, dong in zip(cols, dongs):
    # 선택된 동을 강조 색깔로 표시
    if col.button(dong, key=dong, 
                  help=f"{dong}만 보기"):
        selected_dong = dong
        st.session_state["selected_dong"] = dong

# 전체 보기 버튼
if st.button("전체 보기"):
    selected_dong = None
    st.session_state["selected_dong"] = None

# 4) 선택된 동 기준으로 최종 필터
if selected_dong:
    filtered = filtered_base[filtered_base["dong"] == selected_dong]
    st.markdown(f"**선택된 동:** {selected_dong} (총 {len(filtered)}개)")
else:
    filtered = filtered_base
    st.markdown(f"**전체 센터 표시:** {len(filtered)}개")

if filtered.empty:
    st.warning("조건에 맞는 센터가 없습니다.")
    st.stop()

# 5) 지도 생성 & 마커 클러스터
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

# 6) Streamlit에 렌더링
st.title("동대문구 돌봄센터 지도")
st_folium(m, width="100%", height=650)
