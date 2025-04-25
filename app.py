import streamlit as st
import pandas as pd
import requests

# ─── 페이지 기본 설정 ───
st.set_page_config(
    page_title="동대문구 돌봄센터 Static Map",
    layout="wide"
)

# ─── 1) 데이터 로드 ───
# 같은 폴더에 centers.csv 파일이 있어야 합니다.
# CSV 컬럼: name, lat, lng, feature, events, programs, categories
df = pd.read_csv("centers.csv", encoding="utf-8-sig")

# ─── 2) 사이드바: 검색 · 대상군 필터 · 상세보기 ───
st.sidebar.header("🔍 필터 & 상세 정보")

# 센터명 검색
search = st.sidebar.text_input("센터명 검색")

# categories 컬럼(예: "어린이;노약자;임산부")에서 고유 대상군 목록 추출
all_cats = sorted(
    set(
        sum(
            [cat.split(";") for cat in df["categories"].dropna().tolist()],
            []
        )
    )
)
sel_cats = st.sidebar.multiselect("대상군 선택", all_cats)

# 필터링
mask = pd.Series(True, index=df.index)
if search:
    mask &= df["name"].str.contains(search, na=False)
if sel_cats:
    mask &= df["categories"].apply(
        lambda s: any(c in s.split(";") for c in sel_cats)
    )
filtered = df[mask]

# 상세보기 selectbox
detail = st.sidebar.selectbox(
    "상세 정보 보기",
    [""] + filtered["name"].tolist()
)
if detail:
    row = filtered[filtered["name"] == detail].iloc[0]
    st.sidebar.markdown(f"## {row.name}")
    st.sidebar.markdown(f"- **Feature:** {row.feature}")
    st.sidebar.markdown(f"- **Events:** {row.events}")
    st.sidebar.markdown(f"- **Programs:** {row.programs}")
    st.sidebar.markdown(f"- **Categories:** {row.categories}")

# ─── 3) Static Map URL 조립 ───
# 중심은 첫 번째 필터된 센터, 없으면 동대문구청 좌표
if not filtered.empty:
    cen_lat = filtered.iloc[0]["lat"]
    cen_lng = filtered.iloc[0]["lng"]
else:
    cen_lat, cen_lng = 37.574360, 127.039530

# 최대 640x640 픽셀
size = "640x640"

# markers 파라미터: "lng,lat|lng,lat|..."
markers_param = "|".join(
    f"{row.lng},{row.lat}" for _, row in filtered.iterrows()
)

static_url = (
    "https://dapi.kakao.com/v2/maps/staticmap"
    f"?center={cen_lng},{cen_lat}"
    f"&level=4"
    f"&size={size}"
    f"&markers={markers_param}"
)

# ─── 4) 디버그: 호출될 URL 출력 ───
st.code("▶ Kakao Static Map URL:\n" + static_url)

# ─── 5) 지도 이미지 요청 ───
REST_KEY = "a744cda0e04fc0979044ffbf0904c193"  # 본인의 REST API 키
headers = {"Authorization": f"KakaoAK {REST_KEY}"}
resp = requests.get(static_url, headers=headers)

if resp.status_code == 200:
    st.image(resp.content, caption="동대문구 돌봄센터 분포도")
else:
    st.error(f"지도 이미지 로드 실패: status_code={resp.status_code}")

# ─── 6) 하단에 필터된 센터 개수 표시 ───
st.markdown(f"### 표시된 센터 수: {len(filtered)}개")
