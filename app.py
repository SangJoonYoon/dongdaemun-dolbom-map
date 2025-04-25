import streamlit as st
import pandas as pd
import requests
from io import BytesIO

#
# 1) 카카오 REST API 키 (환경변수 또는 .env 파일 활용)
#
# .env 파일에
# KAKAO_REST_API_KEY="a744cda0e04fc0979044ffbf0904c193"
# 이렇게 적어두고,
# python-dotenv로 로드해도 됩니다.
#
from dotenv import load_dotenv
import os
load_dotenv()
REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
if not REST_API_KEY:
    st.error("카카오 REST API 키를 설정해 주세요.")
    st.stop()

#
# 2) 데이터 로드
#
centers = pd.read_csv("centers.csv", encoding="utf-8-sig")

#
# 3) 사이드바 UI: 검색·필터
#
st.sidebar.header("🔍 필터")

name_filter = st.sidebar.text_input("센터명 검색")
target_filter = st.sidebar.selectbox(
    "대상군 선택",
    options=["전체"] + sorted(centers["categories"].unique().tolist())
)

# 필터링
df = centers.copy()
if name_filter:
    df = df[df["name"].str.contains(name_filter, case=False, na=False)]
if target_filter != "전체":
    df = df[df["categories"] == target_filter]

st.sidebar.markdown(f"표시된 센터 수: **{len(df)}개**")

#
# 4) 본문: Static Map 요청
#
st.title("동대문구 돌봄센터 위치 지도")
st.write(f"총 {len(df)}개 센터를 지도에 표시합니다.")

if len(df)==0:
    st.info("조건에 맞는 센터가 없습니다.")
    st.stop()

# 중간 중심점: 첫 번째 센터를 중심으로 잡거나, 평균 좌표
center_lat = df["lat"].mean()
center_lng = df["lng"].mean()

# 마커 문자열: "lat,lng|lat2,lng2|..."
markers = "|".join(f"{row.lat},{row.lng}" for row in df.itertuples())

# Static Map 파라미터
level = 4   # 고정 줌 레벨, 필요에 따라 UI로 노출 가능
size = "640x640"

static_url = (
    "https://dapi.kakao.com/v2/maps/staticmap"
    f"?center={center_lat},{center_lng}"
    f"&level={level}"
    f"&size={size}"
    f"&markers={markers}"
)

# 요청
headers = {"Authorization": f"KakaoAK {REST_API_KEY}"}
resp = requests.get(static_url, headers=headers)

if resp.status_code != 200:
    st.error(f"지도 이미지 로드 실패: status_code={resp.status_code}")
else:
    # 이미지 표시
    st.image(resp.content, use_column_width=True)

#
# 5) 상세 정보 보기
#
st.markdown("---")
st.subheader("상세 정보 보기")
choose = st.selectbox("상세 정보 열기", ["선택하세요"] + df["name"].tolist())
if choose != "선택하세요":
    row = df[df["name"] == choose].iloc[0]
    st.markdown(f"**센터명:** {row.name}")
    st.markdown(f"**위치:** {row.lat}, {row.lng}")
    st.markdown(f"**기능:** {row.feature}")
    st.markdown(f"**대상군:** {row.categories}")
