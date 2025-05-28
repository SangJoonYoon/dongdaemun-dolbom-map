import os
import json
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import streamlit.components.v1 as components

load_dotenv()
KAKAO_JS_KEY = os.getenv("49a701f08a231a6895dca5db6de5869a")
if not KAKAO_JS_KEY:
    st.error("❗ Kakao JavaScript 키를 환경변수 `KAKAO_JS_KEY` 에 설정해주세요.")
    st.stop()

# 페이지 설정
st.set_page_config(page_title="동대문구 건강지원센터", layout="wide")

# 데이터 불러오기
centers = pd.read_csv("centers.csv", encoding="utf-8-sig")

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["소개", "건강지원센터지도", "프로그램 목록", "프로그램 신청"])

# ─── 1️⃣ 소개 ─────────────────────────────────────────────
with tab1:
    st.header("🏥 동대문구 건강지원센터 소개")
    st.write("동대문구 내 건강지원센터 위치와 프로그램 정보를 한눈에 확인할 수 있습니다.")

# ─── 2️⃣ 건강지원센터지도 ─────────────────────────────────
with tab2:
    st.header("📍 건강지원센터 위치 지도")
    st.write("아래 버튼을 눌러 관심 있는 동으로 바로 이동・하이라이트할 수 있습니다.")

    # session_state 초기화
    if "sel_dong" not in st.session_state:
        st.session_state.sel_dong = "전체"

    # 동 선택 버튼
    c_all, c_wi, c_im, c_da = st.columns(4)
    if c_all.button("전체"):
        st.session_state.sel_dong = "전체"
    if c_wi.button("휘경2동"):
        st.session_state.sel_dong = "휘경2동"
    if c_im.button("이문2동"):
        st.session_state.sel_dong = "이문2동"
    if c_da.button("답십리2동"):
        st.session_state.sel_dong = "답십리2동"

    # 클라이언트로 보낼 센터 데이터 JSON
    centers_js = centers.to_dict(orient="records")
    centers_json = json.dumps(centers_js, ensure_ascii=False)

    # Python에서 중심 좌표와 줌레벨 계산
    if st.session_state.sel_dong == "전체":
        center_lat, center_lng, zoom = 37.582, 127.064, 13
    else:
        df_d = centers[centers["dong"] == st.session_state.sel_dong]
        center_lat, center_lng = df_d[["lat","lng"]].mean()
        zoom = 16

    # Kakao Map HTML + JS
    html = f"""
    <div id="map" style="width:100%;height:600px;"></div>
    <script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&libraries=services"></script>
    <script>
      kakao.maps.load(function() {{
        // 1) 지도 생성
        var map = new kakao.maps.Map(document.getElementById('map'), {{
          center: new kakao.maps.LatLng({center_lat}, {center_lng}),
          level: {zoom}
        }});

        // 2) 동별 경계 GeoJSON 불러오기
        fetch("https://raw.githubusercontent.com/raqoon886/Local_HangJeongDong/master/hangjeongdong_서울특별시.geojson")
          .then(res => res.json())
          .then(geojson => {{
            geojson.features.forEach(function(feat) {{
              // 좌표 배열 변환 (한 feature당 가장 첫번째 폴리곤만 사용)
              var coords = feat.geometry.coordinates[0].map(c => new kakao.maps.LatLng(c[1], c[0]));
              var polygon = new kakao.maps.Polygon({{
                map: map,
                paths: coords,
                strokeWeight: 1,
                strokeColor: "#999",
                fillColor: "#fff",
                fillOpacity: 0.0
              }});
              // 클릭된 동만 하이라이트
              var adm = feat.properties.adm_nm;
              if (adm.includes("{st.session_state.sel_dong}")) {{
                polygon.setOptions({{
                  strokeWeight: 3,
                  strokeColor: "#0055FF",
                  fillColor: "#0055FF",
                  fillOpacity: 0.3
                }});
              }}
            }});
          }});

        // 3) 센터 마커 추가
        var centers = {centers_json};
        centers.forEach(function(c) {{
          // 전체 혹은 해당 동만 표시
          if ("{st.session_state.sel_dong}" === "전체" || c.dong === "{st.session_state.sel_dong}") {{
            var marker = new kakao.maps.Marker({{
              map: map,
              position: new kakao.maps.LatLng(c.lat, c.lng),
              title: c.name
            }});
            // 팝업 내용: 센터명 + 프로그램 목록
            var progs = c.programs.split(";").map(p => p.trim());
            var html = "<div style='padding:8px;max-width:280px;'><strong>" + c.name + "</strong><ul>";
            progs.forEach(function(p) {{
              html += "<li>" + p + "</li>";
            }});
            html += "</ul></div>";
            var infowindow = new kakao.maps.InfoWindow({{ content: html }});
            kakao.maps.event.addListener(marker, 'click', function() {{
              infowindow.open(map, marker);
            }});
          }}
        }});
      }});
    </script>
    """

    components.html(html, height=650, scrolling=False)

# ─── 3️⃣ 프로그램 목록 페이지 ───────────────────────────────────
with tab3:
    st.header("📋 프로그램 목록")
    # ... (기존 태그 표시 로직 유지) ...

# ─── 4️⃣ 프로그램 신청 페이지 ─────────────────────────────────
with tab4:
    st.header("📝 프로그램 신청")
    # ... (기존 신청 폼 로직 유지) ...
