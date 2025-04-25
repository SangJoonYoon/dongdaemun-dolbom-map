import streamlit as st
import pandas as pd
import requests

# ─── 페이지 셋업 ───
st.set_page_config("동대문구 돌봄센터 Static Map", layout="wide")

# ─── 1) 데이터 로드 ───
df = pd.read_csv("centers.csv", encoding="utf-8-sig")

# ─── 2) 사이드바: 검색 + 필터 + 선택 ───
st.sidebar.header("🔍 필터 & 선택")
search = st.sidebar.text_input("센터명 검색")
cats = sorted({c for subs in df["categories"].str.split(";") for c in subs})
sel_cats = st.sidebar.multiselect("대상군 선택", cats)

#  필터 적용
mask = pd.Series(True, index=df.index)
if search:
    mask &= df["name"].str.contains(search, na=False)
if sel_cats:
    mask &= df["categories"].apply(lambda s: any(c in s for c in sel_cats))
filtered = df[mask]

# 선택 리스트 (팝업 대신)
center_names = filtered["name"].tolist()
selected_name = st.sidebar.selectbox("상세 보기 (선택)", [""] + center_names)

st.sidebar.markdown("---")
if selected_name:
    info = filtered[filtered["name"] == selected_name].iloc[0]
    st.sidebar.markdown(f"**{info.name}**")
    st.sidebar.markdown(f"- Feature: {info.feature}")
    st.sidebar.markdown(f"- Events: {info.events}")
    st.sidebar.markdown(f"- Programs: {info.programs}")
    st.sidebar.markdown(f"- Categories: {info.categories}")

# ─── 3) Static Map 이미지 URL 생성 ───
# center 파라미터는 "lng,lat"
if not filtered.empty:
    # 맵 중심: 첫 번째 필터된 센터
    center_lng = filtered.iloc[0]["lng"]
    center_lat = filtered.iloc[0]["lat"]
else:
    center_lng, center_lat = 127.039530, 37.574360

# 마커 파라미터: markerType:blue|lat,lng (여러 개는 '|' 로 구분)
markers = "|".join(
    f"markerType:blue|{row.lat},{row.lng}"
    for _, row in filtered.iterrows()
)

static_url = (
    "https://dapi.kakao.com/v2/maps/staticmap"
    f"?center={center_lng},{center_lat}"
    f"&level=4&size=800x600"
    f"&markers={markers}"
)

# ─── 4) REST API 호출 ───
# Kakao REST API 키 (환경변수로 설정해 두시거나, 직접 넣으셔도 됩니다)
REST_KEY = "a744cda0e04fc0979044ffbf0904c193"
headers = {"Authorization": f"KakaoAK {REST_KEY}"}

resp = requests.get(static_url, headers=headers)
if resp.status_code == 200:
    st.image(resp.content, caption="동대문구 돌봄센터 분포도")
else:
    st.error(f"지도 이미지 로드 실패: status_code={resp.status_code}")

# ─── 5) 표시된 센터 개수 ───
st.markdown(f"### 표시된 센터 수: {len(filtered)}개")
