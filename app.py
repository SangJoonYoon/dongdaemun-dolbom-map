import os
import streamlit as st
import pandas as pd
import requests
import json
import streamlit.components.v1 as components

# ─── 페이지 설정 ─────────────────────────────────────────
st.set_page_config(
    page_title="동대문구 건강지원센터",
    page_icon="🏥",
    layout="wide"
)

# ─── 1️⃣ 환경변수(Kakao JS Key) 로드 ─────────────────────────────────
# Streamlit Cloud Settings → Secrets에 아래 한 줄을 정확히 적어 둡니다.
# KAKAO_JS_KEY="발급받은_JavaScript_Key_문자열"
KAKAO_JS_KEY = os.environ.get("KAKAO_JS_KEY")
if not KAKAO_JS_KEY:
    st.error(
        "❗ Kakao JavaScript Key가 설정되지 않았습니다.\n"
        "Streamlit Cloud Settings → Secrets에 다음과 같이 한 줄로 입력해주세요:\n\n"
        'KAKAO_JS_KEY="여기에_발급받은_JavaScript_Key를_붙여넣기"'
    )
    st.stop()

# ─── 2️⃣ centers.csv 로드 & 검증 ───────────────────────────────────
try:
    centers = pd.read_csv("centers.csv", encoding="utf-8-sig")
except FileNotFoundError:
    st.error("❗ centers.csv 파일이 없습니다. 프로젝트 루트에 centers.csv를 두세요.")
    st.stop()

required_cols = {"name", "feature", "dong", "programs", "categories", "lat", "lng"}
if not required_cols.issubset(centers.columns):
    missing = required_cols - set(centers.columns)
    st.error(f"❗ centers.csv에 다음 컬럼이 반드시 있어야 합니다: {', '.join(missing)}")
    st.stop()

# ─── 3️⃣ 사이드바 메뉴 ───────────────────────────────────────
st.sidebar.header("📌 메뉴")
page = st.sidebar.radio("", ["소개", "건강지원센터지도", "프로그램 목록", "프로그램 신청"])


# ─── 4️⃣ 1) 소개 페이지 ─────────────────────────────────────────
if page == "소개":
    st.title("🏥 동대문구 건강지원센터 소개")
    st.markdown(
        """
        **1. 동대문구 세 개 동(휘경2동·이문2동·답십리2동)별 건강지원센터 설립**  
        - 병원 인프라가 상대적으로 취약한 동 위주로 서비스 집중  
        - 공공데이터(동별 인구 및 의료기관 수) 분석을 통해 우선 설치  

        **2. 병원 연계 사후관리**  
        - 진료 환자 사후관리: 각 동별 병원과 협업하여 진료 후 Follow-up 제공  
        - 미진료 주민: 기초 건강검진(혈압측정·혈당측정·체성분검사) 후 간단한 상담 제공  

        **3. 맞춤 건강증진 프로그램 & 병원 추천**  
        - 주민 연령·건강 상태에 맞춘 운동·영양·건강교육 프로그램 운영  
        - 의료기관 불균형 지수 기반 추천(예: 병원 접근성이 낮은 동 우선 지원)  

        **4. 건강동아리 구성**  
        - 보건소·학교·복지관 등과 지역 협약(활동 장소 제공)  
        - 독거노인·청소년 등 대상자별 건강 소모임 활동(주기적 건강체크, 운동, 레크레이션)  

        ### 🎯 목적  
        1. 고령층·취약계층 만성질환 조기 예방  
        2. 주민의 건강생활습관 개선 및 정신건강 증진  
        3. 동대문구 의료 사각지대 해소 및 지역 공동체 강화  
        """
    )
    st.image("https://source.unsplash.com/1600x400/?health,clinic")


# ─── 5️⃣ 2) 건강지원센터 지도 페이지 ─────────────────────────────────
elif page == "건강지원센터지도":
    st.title("📍 건강지원센터 위치 지도")

    # --- 2-1) “동 선택” 전용 버튼(휘경2동, 이문2동, 답십리2동) ---
    st.markdown("**행정동별 보기 (세 개 동만 선택 가능)**")
    sel_dong = st.radio(
        "",
        options=["전체", "휘경2동", "이문2동", "답십리2동"],
        index=0,
        horizontal=True
    )

    # --- 2-2) 동 선택에 따른 필터링 ---
    if sel_dong == "전체":
        df = centers[centers["dong"].isin(["휘경2동", "이문2동", "답십리2동"])].copy()
    else:
        df = centers[centers["dong"] == sel_dong].copy()

    st.caption(f"표시된 센터: {len(df)}개")

    # --- 2-3) Kakao Map HTML 생성 및 렌더링 ---
    # 1) centers 데이터프레임을 JSON으로 변환
    centers_json = df.to_dict(orient="records")
    json_data = json.dumps(centers_json, ensure_ascii=False)

    # 2) 지도의 중심좌표 및 줌레벨 설정
    if sel_dong == "전체":
        # 세 개 동의 평균 위치
        lat_center = df["lat"].mean()
        lng_center = df["lng"].mean()
        zoom_level = 13
    else:
        lat_center = float(df.iloc[0]["lat"])
        lng_center = float(df.iloc[0]["lng"])
        zoom_level = 16

    # 3) HTML + JavaScript 코드 (components.html 로 삽입)
    html_map = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <!-- Kakao JavaScript SDK: 반드시 appkey 파라미터에 환경변수값을 넣어야 합니다 -->
      <script type="text/javascript"
              src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&libraries=services,clusterer"></script>
    </head>
    <body>
      <div id="map" style="width:100%;height:600px;"></div>
      <script>
        // 1) 맵 객체 생성
        var mapContainer = document.getElementById('map');
        var mapOption = {{
            center: new kakao.maps.LatLng({lat_center}, {lng_center}),
            level: {zoom_level}
        }};
        var map = new kakao.maps.Map(mapContainer, mapOption);

        // 2) GeoJSON으로 동 경계 하이라이트
        fetch("https://raw.githubusercontent.com/raqoon886/Local_HangJeongDong/master/hangjeongdong_서울특별시.geojson")
          .then(response => response.json())
          .then(geojsonData => {{
            var geojson = new kakao.maps.GeoJSON({{
              map: map,
              geojson: geojsonData,
              style: function(feature) {{
                var name = feature.properties.adm_nm;
                var isSelected = ( "{sel_dong}" !== "전체" ) && name.indexOf("{sel_dong}") !== -1;
                return {{
                  fillColor: isSelected ? "#0055FF" : "#ffffff",
                  color: isSelected ? "#0055FF" : "#999999",
                  weight: isSelected ? 3 : 1,
                  fillOpacity: isSelected ? 0.3 : 0.0
                }};
              }},
              tooltip: function(feature) {{
                return feature.properties.adm_nm;
              }}
            }});
          }})
          .catch(err => console.error("경계 로드 실패:", err));

        // 3) 마커 & 인포윈도우 생성 (클러스터러 사용)
        var markers = [];
        var data = {json_data};

        data.forEach(item => {{
          var position = new kakao.maps.LatLng(item.lat, item.lng);
          var marker = new kakao.maps.Marker({{
            map: map,
            position: position,
            title: item.name
          }});
          // InfoWindow 내용: 센터명 + 프로그램 + 태그(카테고리)
          var content = `
            <div style="font-family:Arial, sans-serif; max-width:220px; padding:8px;">
              <h4 style="margin:0 0 6px;">${{item.name}}</h4>
              <p style="margin:0;font-weight:600;">프로그램:</p>
              <ul style="margin:4px 0 0 16px;padding:0;list-style:disc;">
                ${{ item.programs.split(";").map(p => `<li>${{p}}</li>`).join('') }}
              </ul>
              <p style="margin:6px 0 0 0;font-weight:600;">태그:</p>
              <div style="margin-top:4px;">
                ${{ item.categories.split(";").map(c => `<span style="display:inline-block;
                                                              background:#E3F2FD;
                                                              color:#0D47A1;
                                                              padding:2px 6px;
                                                              margin:2px;
                                                              border-radius:4px;
                                                              font-size:12px;">
                                                            #${{c}}
                                                          </span>`).join('') }}
              </div>
            </div>
          `;
          var infowindow = new kakao.maps.InfoWindow({{ content: content }});
          kakao.maps.event.addListener(marker, 'click', function() {{
            infowindow.open(map, marker);
          }});
          markers.push(marker);
        }});

        // 4) 클러스터러 생성 (마커가 겹쳐지지 않도록)
        new kakao.maps.MarkerClusterer({{
          map: map,
          averageCenter: true,
          minLevel: 5,
          markers: markers
        }});
      </script>
    </body>
    </html>
    """

    # 4) Streamlit 에 HTML 전달
    components.html(html_map, height=650, scrolling=False)


# ─── 6️⃣ 3) 프로그램 목록 페이지 ───────────────────────────────────
elif page == "프로그램 목록":
    st.title("📋 현재 운영중인 프로그램")

    # “programs” 컬럼을 explode 처리해서 프로그램별로 센터 리스트 보여주기
    dfp = centers[["name", "programs", "categories"]].copy().fillna("")
    dfp["programs"] = dfp["programs"].str.split(";")
    dfp = dfp.explode("programs")
    dfp["programs"] = dfp["programs"].str.strip()
    dfp = dfp[dfp["programs"] != ""]

    # “프로그램 → 센터 이름” 형태로 그룹핑
    for prog_name, grp in dfp.groupby("programs"):
        # 카테고리 태그(예: #노인, #일반 등) 도 함께 표시
        cats = set()
        grp["categories"].str.split(";").apply(lambda arr: cats.update(arr))
        cat_tags = " ".join([f"`#{c}`" for c in sorted(cats) if c != ""])
        with st.expander(f"{prog_name} ({len(grp)})  {cat_tags}"):
            for _, row in grp.iterrows():
                st.write(f"- {row['name']} ({row['dong']})")


# ─── 7️⃣ 4) 프로그램 신청 페이지 ─────────────────────────────────
else:  # 프로그램 신청
    st.title("📝 프로그램 신청")

    dfp = centers[["programs"]].copy().fillna("")
    dfp["programs"] = dfp["programs"].str.split(";")
    dfp = dfp.explode("programs")
    dfp["programs"] = dfp["programs"].str.strip()
    programs = sorted(dfp[dfp["programs"] != ""].programs.unique())

    if not programs:
        st.info("등록된 프로그램이 없습니다.")
        st.stop()

    sel_prog = st.selectbox("프로그램 선택", programs)
    user_name = st.text_input("이름")
    contact = st.text_input("연락처", placeholder="010-1234-5678")

    if st.button("신청하기"):
        if sel_prog and user_name and contact:
            st.success(f"✅ '{sel_prog}' 신청이 완료되었습니다!")
        else:
            st.error("❗ 모든 항목을 입력해주세요.")
