import streamlit as st
import pandas as pd
import requests

st.set_page_config("동대문구 돌봄센터 Static Map", layout="wide")

# 1) 데이터 로드
df = pd.read_csv("centers.csv", encoding="utf-8-sig")

# 2) 사이드바 필터
st.sidebar.header("🔍 필터")
search = st.sidebar.text_input("센터명 검색")
cats = sorted({c for subs in df["categories"].str.split(";") for c in subs})
sel = st.sidebar.multiselect("대상군 선택", cats)

mask = pd.Series(True, index=df.index)
if search:
    mask &= df["name"].str.contains(search, na=False)
if sel:
    mask &= df["categories"].apply(lambda s: any(c in s for c in sel))
filtered = df[mask]

# 선택 박스(팝업 대체)
selected = st.sidebar.selectbox("상세 정보 보기", [""] + filtered["name"].tolist())
if selected:
    info = filtered[filtered["name"] == selected].iloc[0]
    st.sidebar.markdown(f"**{info.name}**")
    st.sidebar.markdown(f"- Feature: {info.feature}")
    st.sidebar.markdown(f"- Events: {info.events}")
    st.sidebar.markdown(f"- Programs: {info.programs}")
    st.sidebar.markdown(f"- Categories: {info.categories}")

# 3) Static Map URL 생성
if not filtered.empty:
    # center: 경도,위도 (DataFrame 열순: name,lat,lng)
    cen_lat = filtered.iloc[0]["lat"]
    cen_lng = filtered.iloc[0]["lng"]
else:
    cen_lat, cen_lng = 37.574360, 127.039530

# size 최대 640x640
size = "640x640"

# markers: 각 마커마다 위도,경도 순서로 나열
marker_list = []
for _, row in filtered.iterrows():
    # type: marker 을 명시해도 되고, 생략해도 기본 마커가 찍힙니다
    marker_list.append(f"{row.lat},{row.lng}")

markers_param = "|".join(marker_list)

static_url = (
    "https://dapi.kakao.com/v2/maps/staticmap"
    f"?center={cen_lng},{cen_lat}"
    f"&level=4"
    f"&size={size}"
    f"&markers={markers_param}"
)

# 4) REST API 호출
REST_KEY = "a744cda0e04fc0979044ffbf0904c193"
headers = {"Authorization": f"KakaoAK {REST_KEY}"}
resp = requests.get(static_url, headers=headers)

if resp.status_code == 200:
    st.image(resp.content, caption="동대문구 돌봄센터 분포도")
else:
    st.error(f"지도 이미지 로드 실패: status_code={resp.status_code}")

st.markdown(f"### 표시된 센터 수: {len(filtered)}개")
