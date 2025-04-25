import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# 데이터 로드
df = pd.read_csv('centers.csv')  # name, lat, lng, feature 컬럼 필수

# 페이지 설정
st.set_page_config(page_title='돌봄센터 위치 표시', layout='wide')
st.title('동대문구 돌봄센터 위치 지도')

# 사이드바 검색·필터
search = st.sidebar.text_input('센터명 검색')
features = st.sidebar.multiselect('특성으로 필터', df['feature'].unique().tolist())

# 데이터 필터링
df2 = df.copy()
if search:
    df2 = df2[df2['name'].str.contains(search)]
if features:
    df2 = df2[df2['feature'].isin(features)]

# 결과 표시
if df2.empty:
    st.warning('조건에 맞는 센터가 없습니다.')
else:
    # 선택 박스
    choice = st.sidebar.selectbox('센터 선택', df2['name'])
    sel = df2[df2['name'] == choice].iloc[0]
    lat, lng, name, feature = sel['lat'], sel['lng'], sel['name'], sel['feature']

    # Kakao Link Map 임베드
    iframe = f'''
<iframe
  src="https://map.kakao.com/link/map/{name},{lat},{lng}"
  width="100%" height="650" frameborder="0" allowfullscreen>
</iframe>
'''
    components.html(iframe, height=650)

    # 상세 정보
    st.markdown(f'**센터명:** {name}')
    st.markdown(f'**위치:** {lat}, {lng}')
    st.markdown(f'**특성:** {feature}')
