import streamlit as st
import pandas as pd
import requests

# ─── 페이지 설정 ───
st.set_page_config(
    page_title="동대문구 돌봄센터 Static Map",
    layout="wide"
)

# ─── 1) 데이터 로드 ───
# centers.csv 파일이 같은 폴더에 존재해야 합니다.
# 컬럼: name, lat, lng, feature, events, programs, categories
df = pd.read_csv("centers.csv", encoding="utf-8-sig")

# ─── 2) 사이드바: 검색 + 대상군 필터 + 상세 선택 ───
st.sidebar.header("🔍 필터 & 상세보기")

search = st.sidebar.text_input("센터명 검색")

# categories 컬럼에서 고유 대상군 목록 뽑기
all_cats = sorted({c for subs in df["categories"].str.split(";") for c in subs})
sel_cats = st.sidebar.multiselect("대상군 선택", all_cats)

# DataFrame 필터링
mask = pd.Series(True, index=df.index)
if search:
    mask &= df["name"].str.contains(search, na=False)
if sel_cats:
    mask &= df["categories"].apply(lambda s: any(c in s for c in sel_cats))

filtered = df[mask]

# 상세보기용 selectbox
selected = st.sidebar.selectbox("상세 정보 보기", [""] + filtered["name"].tolist())
if selected:
    info = filtered[filtered["name"] == selected].iloc[0]
    st.sidebar.markdown(f"## {info.name}")
    st.sidebar.markdown(f"- **Feature:** {info.feature}")
    st.sidebar.markdown(f"- **Events:** {info.events}")
    st.sidebar.markdown(f"- **Programs:** {info.programs}")
    st.sidebar.markdown(f"- **Categories:** {info.categories}")

# ─── 3) Static Map API URL 생성 ───
if not filtered.empty:
    cen_lat = filtered.iloc[0]["lat"]
    cen_lng = filtered.iloc[0]["lng"]
else:
    # 기본 센터 위치 (동대문구청)
    cen_lat, cen_lng = 37.574360, 127.039530

# Static Map 최대 size는 640x640
size = "640x640"

# markers 파라미터는 "lng,lat|lng,lat|..."
marker_list = [f"{row.lng},{row.lat}" for _, row in filtered.iterrows()]
markers_param = "|".join(marker_list)

static_url = (
    "https://dapi.kakao.com/v2/maps/staticmap"
    f"?center={cen_lng},{cen_lat}"
    f"&level=4"
    f"&size={size}"
    f"&markers={markers_param}"
)

# ─── 4) 디버그: 호출 URL 출력 ───
st.code(static_url)

# ─── 5) 지도 이미지 요청 ───
REST_KEY = "a744cda0e04fc0979044ffbf0904c193"  # 본인의 REST API 키
headers = {"Authorization": f"KakaoAK {REST_KEY}"}
resp = requests.get(static_url, headers=headers)

if resp.status_code == 200:
    st.image(resp.content, caption="동대문구 돌봄센터 분포도")
else:
    st.error(f"지도 이미지 로드 실패: status_code={resp.status_code}")

# ─── 6) 하단에 표시된 센터 개수 ───
st.markdown(f"### 표시된 센터 수: {len(filtered)}개")
